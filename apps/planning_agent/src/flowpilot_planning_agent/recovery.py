import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
from typing import cast

import httpx

from flowpilot_planning_agent.budget import BudgetExceeded, TotalBudgetLedger
from flowpilot_planning_agent.client import BrowserWorkerClient
from flowpilot_planning_agent.dag import step_by_id, validate_dag
from flowpilot_planning_agent.executor import ExecutionFailure, PlanningExecutor, _Instruction
from flowpilot_planning_agent.planner import DeterministicPlanner
from flowpilot_planning_agent.receipts import build_binding
from flowpilot_planning_agent.recovery_schemas import (
    ActivityOutcome,
    PlanningActivityResult,
    PlanningRecoveryActivity,
    ReceiptRecord,
    validate_checkpoint,
)
from flowpilot_planning_agent.replan import partial_replan
from flowpilot_planning_agent.schemas import (
    PlanningDag,
    PlanRequest,
    PlanStep,
    TotalBudget,
    VerifierRequest,
)
from flowpilot_planning_agent.verifier import DeterministicStepVerifier
from flowpilot_planning_agent.worker_schemas import (
    DomAction,
    DomClickAction,
    DomFillAction,
    DomNavigateAction,
    DomReadAction,
    HybridDomObservation,
    RecoveryDomActionEnvelope,
    RecoveryIdempotencyBinding,
    SandboxPath,
)


@dataclass(slots=True)
class RecoveryRunState:
    request_identity: tuple[str, str, str]
    dag: PlanningDag
    plan_hash: str
    topology: tuple[str, ...]
    session_id: str
    session_epoch: int
    observation: HybridDomObservation
    ledger: TotalBudgetLedger
    completed: set[str] = field(default_factory=set)
    injected_faults: set[str] = field(default_factory=set)
    action_number: int = 0


class RecoveryCoordinator:
    def __init__(self, browser: BrowserWorkerClient) -> None:
        self._browser = browser
        self._planner = DeterministicPlanner()
        self._verifier = DeterministicStepVerifier()
        self._runs: dict[str, RecoveryRunState] = {}
        self._lock = asyncio.Lock()

    async def invoke(self, request: PlanningRecoveryActivity) -> PlanningActivityResult:
        async with self._lock:
            if request.command == "start":
                return await self._start(request)
            state = self._require_state(request)
            if request.command == "cleanup":
                return await self._cleanup(request, state)
            self._validate_checkpoint(request, state)
            if request.command == "refresh":
                return await self._refresh(request, state)
            if request.command == "recover":
                return await self._recover(request, state)
            if request.command == "replan":
                return self._replan(request, state)
            return await self._step(request, state)

    async def _start(self, request: PlanningRecoveryActivity) -> PlanningActivityResult:
        if request.run_id in self._runs:
            state = self._runs[request.run_id]
            return self._result(request, state, "started", "existing recovery run resumed")
        plan = self._planner.generate(
            PlanRequest(
                process=request.process,
                category=request.category,
                human_brief=request.human_brief,
                supplied_values=request.supplied_values,
            )
        )
        validation = validate_dag(plan.dag)
        if not validation.valid or validation.plan_id is None:
            return PlanningActivityResult(
                outcome="permanent_failure",
                safe_reason="deterministic plan validation failed",
                session_epoch=request.session_epoch,
                revision=request.revision,
            )
        ledger = TotalBudgetLedger(TotalBudget())
        ledger.charge_plan(
            nodes=validation.node_count,
            edges=validation.edge_count,
            depth=validation.depth,
            serialized_bytes=validation.serialized_bytes,
        )
        created = await self._browser.create_recovery_session(request.session_epoch)
        ledger.charge_dom_observation(created.observation.route_signals.dom_observation_bytes)
        state = RecoveryRunState(
            request_identity=(request.workflow_id, request.run_id, request.task_id),
            dag=plan.dag,
            plan_hash=validation.plan_id,
            topology=validation.topology,
            session_id=created.session_id,
            session_epoch=request.session_epoch,
            observation=created.observation,
            ledger=ledger,
        )
        self._runs[request.run_id] = state
        return self._result(request, state, "started", "recovery run initialized")

    async def _step(
        self, request: PlanningRecoveryActivity, state: RecoveryRunState
    ) -> PlanningActivityResult:
        if request.step_id is None or request.step_id not in state.topology:
            return self._result(
                request, state, "permanent_failure", "step is outside current revision"
            )
        if (
            request.fault_scenario == "permanent_failure"
            and "permanent_failure" not in state.injected_faults
        ):
            state.injected_faults.add("permanent_failure")
            return self._result(request, state, "permanent_failure", "trusted permanent fault")
        if request.fault_scenario in {"browser_session_lost_once", "browser_worker_restart_once"}:
            key = request.fault_scenario
            if key not in state.injected_faults:
                state.injected_faults.add(key)
                with suppress(Exception):
                    await self._browser.close_recovery_session(state.session_id)
                return self._result(
                    request, state, "session_lost", "current browser epoch was lost"
                )
        if (
            request.fault_scenario in {"replan_eligible_once", "replan_disallowed"}
            and state.completed
            and request.fault_scenario not in state.injected_faults
        ):
            state.injected_faults.add(request.fault_scenario)
            return self._result(
                request, state, "replan_eligible", "failed subgraph is replan eligible"
            )

        step = step_by_id(state.dag, request.step_id)
        if any(dependency not in state.completed for dependency in step.dependencies):
            return self._result(
                request, state, "permanent_failure", "step dependencies are not verified"
            )
        try:
            state.ledger.charge_step()
            observation = state.observation
            action_success = False
            receipt: ReceiptRecord | None = None
            for instruction in PlanningExecutor._instructions(step, request.supplied_values):
                state.ledger.charge_action()
                envelope, binding = self._envelope(request, state, step, observation, instruction)
                result = await self._browser.execute_recovery_action(state.session_id, envelope)
                if result.terminal or result.observation is None:
                    return self._result(
                        request, state, "session_lost", "recovery action lost session"
                    )
                observation = result.observation
                state.observation = observation
                state.ledger.charge_dom_observation(observation.route_signals.dom_observation_bytes)
                action_success = result.success
                if result.receipt is not None and binding is not None:
                    result_hash = result.receipt.result_hash or "0" * 64
                    receipt = ReceiptRecord(
                        idempotency_key=binding.idempotency_key,
                        request_hash=binding.request_hash,
                        result_hash=result_hash,
                        state=result.receipt.state,
                    )
                    if result.receipt.state == "mismatch":
                        return self._result(
                            request,
                            state,
                            "idempotency_mismatch",
                            "Sandbox rejected changed-hash replay",
                            receipt=receipt,
                        )
                if not result.success:
                    break
            verification = self._verifier.verify(
                VerifierRequest(
                    step_id=step.step_id,
                    expected_page=step.expected_page,
                    current_page=PlanningExecutor._page(observation),
                    observation_generation=observation.generation,
                    action_success=action_success,
                    postconditions=step.postconditions,
                ),
                state.ledger,
                probe=False,
            )
            if verification.status != "verified":
                return self._result(
                    request, state, "permanent_failure", "runtime Verifier did not verify step"
                )
            state.completed.add(request.step_id)
            return self._result(
                request,
                state,
                "verified",
                "step verified from current safe evidence",
                receipt=receipt,
            )
        except (BudgetExceeded, ExecutionFailure):
            return self._result(
                request, state, "permanent_failure", "total ledger or tool limit reached"
            )
        except httpx.HTTPError:
            return self._result(
                request, state, "session_lost", "Browser Worker session unavailable"
            )

    async def _refresh(
        self, request: PlanningRecoveryActivity, state: RecoveryRunState
    ) -> PlanningActivityResult:
        try:
            observation = await self._browser.request_recovery_observation(
                state.session_id, state.session_epoch
            )
        except httpx.HTTPError:
            return self._result(request, state, "session_lost", "current epoch is unavailable")
        state.observation = observation
        state.ledger.charge_dom_observation(observation.route_signals.dom_observation_bytes)
        return self._result(request, state, "started", "current observation refreshed")

    async def _recover(
        self, request: PlanningRecoveryActivity, state: RecoveryRunState
    ) -> PlanningActivityResult:
        if request.session_epoch != state.session_epoch + 1 or request.session_epoch > 3:
            return self._result(
                request, state, "permanent_failure", "session epoch transition rejected"
            )
        with suppress(Exception):
            await self._browser.close_recovery_session(state.session_id)
        created = await self._browser.create_recovery_session(request.session_epoch)
        state.session_id = created.session_id
        state.session_epoch = request.session_epoch
        state.observation = created.observation
        state.ledger.charge_dom_observation(created.observation.route_signals.dom_observation_bytes)
        return self._result(request, state, "started", "fresh browser epoch created")

    def _replan(
        self, request: PlanningRecoveryActivity, state: RecoveryRunState
    ) -> PlanningActivityResult:
        if request.step_id is None or request.revision != 2:
            return self._result(request, state, "permanent_failure", "revision transition rejected")
        revised, replaced = partial_replan(state.dag, request.step_id, frozenset(state.completed))
        validation = validate_dag(revised)
        if not validation.valid or validation.plan_id is None:
            return self._result(request, state, "permanent_failure", "replacement DAG rejected")
        state.dag = revised
        state.plan_hash = validation.plan_id
        state.topology = validation.topology
        return self._result(
            request,
            state,
            "started",
            "bounded partial revision created",
            replaced_step_ids=replaced,
        )

    async def _cleanup(
        self, request: PlanningRecoveryActivity, state: RecoveryRunState
    ) -> PlanningActivityResult:
        with suppress(Exception):
            await self._browser.close_recovery_session(state.session_id)
        del self._runs[request.run_id]
        return PlanningActivityResult(
            outcome="cleaned",
            safe_reason="task-local recovery state cleared",
            plan_hash=state.plan_hash,
            topology=state.topology,
            session_epoch=state.session_epoch,
            revision=request.revision,
        )

    def _require_state(self, request: PlanningRecoveryActivity) -> RecoveryRunState:
        state = self._runs.get(request.run_id)
        if state is None or state.request_identity != (
            request.workflow_id,
            request.run_id,
            request.task_id,
        ):
            raise ValueError("recovery run identity not found")
        return state

    @staticmethod
    def _validate_checkpoint(request: PlanningRecoveryActivity, state: RecoveryRunState) -> None:
        if request.checkpoint is None:
            raise ValueError("durable command requires a Checkpoint")
        validate_checkpoint(request.checkpoint)
        revision_valid = (
            request.checkpoint.revision + 1 == request.revision
            if request.command == "replan"
            else request.checkpoint.revision == request.revision
        )
        if (
            request.checkpoint.plan_hash != state.plan_hash
            or not revision_valid
            or request.checkpoint.session_epoch != state.session_epoch
            or request.checkpoint.task_id != request.task_id
        ):
            raise ValueError("Checkpoint does not bind current recovery state")

    @staticmethod
    def _result(
        request: PlanningRecoveryActivity,
        state: RecoveryRunState,
        outcome: ActivityOutcome,
        reason: str,
        *,
        receipt: ReceiptRecord | None = None,
        replaced_step_ids: tuple[str, ...] = (),
    ) -> PlanningActivityResult:
        return PlanningActivityResult(
            outcome=outcome,
            safe_reason=reason,
            plan_hash=state.plan_hash,
            topology=state.topology,
            step_id=request.step_id,
            session_epoch=state.session_epoch,
            revision=request.revision,
            receipt=receipt,
            replaced_step_ids=replaced_step_ids,
            planning_usage=state.ledger.snapshot(),
        )

    def _envelope(
        self,
        request: PlanningRecoveryActivity,
        state: RecoveryRunState,
        step: PlanStep,
        observation: HybridDomObservation,
        instruction: _Instruction,
    ) -> tuple[RecoveryDomActionEnvelope, RecoveryIdempotencyBinding | None]:
        action_kind = instruction.action
        label = instruction.label
        value = instruction.value
        state.action_number += 1
        action_id = f"act_w8_{state.action_number}"
        if action_kind == "navigate":
            action: DomAction = DomNavigateAction(action_id=action_id, url=cast(SandboxPath, value))
        elif action_kind == "fill":
            element = PlanningExecutor._element(observation, "fill", label)
            action = DomFillAction(
                action_id=action_id,
                observation_id=observation.observation.observation_id,
                element_ref=element.element_ref,
                text=value or "",
            )
        elif action_kind == "click":
            element = PlanningExecutor._element(observation, "click", label)
            action = DomClickAction(
                action_id=action_id,
                observation_id=observation.observation.observation_id,
                element_ref=element.element_ref,
            )
        elif action_kind == "read":
            element = PlanningExecutor._element(observation, "read", label)
            action = DomReadAction(
                action_id=action_id,
                observation_id=observation.observation.observation_id,
                element_ref=element.element_ref,
            )
        else:
            raise ExecutionFailure("unsupported recovery instruction")
        binding = None
        if action_kind == "click" and label != "Show transitions":
            binding = build_binding(request, step.operation)
            if (
                request.fault_scenario == "idempotency_mismatch"
                and "idempotency_mismatch" not in state.injected_faults
            ):
                state.injected_faults.add("idempotency_mismatch")
                binding = binding.model_copy(update={"request_hash": "f" * 64})
        return (
            RecoveryDomActionEnvelope(
                session_id=state.session_id,
                session_epoch=state.session_epoch,
                generation=observation.generation,
                action=action,
                idempotency=binding,
            ),
            binding,
        )

    async def close_all(self) -> None:
        async with self._lock:
            states = list(self._runs.values())
            self._runs.clear()
        for state in states:
            with suppress(Exception):
                await self._browser.close_recovery_session(state.session_id)
