import asyncio
from contextlib import suppress
from dataclasses import dataclass
from typing import cast
from urllib.parse import urlsplit

from flowpilot_planning_agent.budget import BudgetExceeded, TotalBudgetLedger
from flowpilot_planning_agent.client import BrowserWorkerClient
from flowpilot_planning_agent.dag import (
    DependencyBlocked,
    StepStateMachine,
    step_by_id,
    validate_dag,
)
from flowpilot_planning_agent.planner import DeterministicPlanner
from flowpilot_planning_agent.schemas import (
    AllowedAction,
    JoinerSuppliedValues,
    LeaverSuppliedValues,
    MoverSuppliedValues,
    Page,
    PlanningRunRequest,
    PlanningRunResult,
    PlanningRunStatus,
    PlanRequest,
    PlanStep,
    StepExecutionResult,
    StepState,
    SuppliedValues,
    ToolRejectionReason,
    VerifierRequest,
)
from flowpilot_planning_agent.tools import GLOBAL_TOOLS, DeterministicToolMatcher
from flowpilot_planning_agent.verifier import DeterministicStepVerifier
from flowpilot_planning_agent.worker_schemas import (
    DomAction,
    DomClickAction,
    DomFillAction,
    DomFinishAction,
    DomNavigateAction,
    DomReadAction,
    HybridActionResult,
    HybridDomActionEnvelope,
    HybridDomObservation,
    InteractiveElement,
    SandboxPath,
)

PAGE_PATH: dict[Page, SandboxPath] = {
    "hris": "/hris",
    "itsm": "/itsm",
    "iam": "/iam",
    "assets": "/assets",
    "mail": "/mail",
}
PATH_PAGE = {path: page for page, path in PAGE_PATH.items()}


@dataclass(frozen=True, slots=True)
class _Instruction:
    action: AllowedAction
    label: str | None = None
    value: str | None = None


class ExecutionFailure(RuntimeError):
    def __init__(self, safe_reason: str, rejection: ToolRejectionReason | None = None) -> None:
        super().__init__(safe_reason)
        self.safe_reason = safe_reason
        self.rejection = rejection


class PlanningExecutor:
    def __init__(
        self,
        browser: BrowserWorkerClient,
        *,
        planner: DeterministicPlanner | None = None,
        matcher: DeterministicToolMatcher | None = None,
        verifier: DeterministicStepVerifier | None = None,
    ) -> None:
        self._browser = browser
        self._planner = planner or DeterministicPlanner()
        self._matcher = matcher or DeterministicToolMatcher()
        self._verifier = verifier or DeterministicStepVerifier()
        self._action_number = 0

    async def run(self, request: PlanningRunRequest) -> PlanningRunResult:
        ledger = TotalBudgetLedger(request.budget)
        step_results: list[StepExecutionResult] = []
        rejection_reasons: list[ToolRejectionReason] = []
        plan_id: str | None = None
        topology: tuple[str, ...] = ()
        session_id: str | None = None
        try:
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
                return self._result(
                    request,
                    "invalid_plan",
                    "Planning DAG failed strict validation",
                    ledger,
                    None,
                    (),
                    step_results,
                    rejection_reasons,
                )
            plan_id = validation.plan_id
            topology = validation.topology
            ledger.charge_plan(
                nodes=validation.node_count,
                edges=validation.edge_count,
                depth=validation.depth,
                serialized_bytes=validation.serialized_bytes,
            )

            created = await self._browser.create_session()
            session_id = created.session_id
            observation = created.observation
            ledger.charge_dom_observation(observation.route_signals.dom_observation_bytes)

            if request.fake_scenario == "finish_immediately":
                result = await self._finish(session_id, observation, ledger)
                if not result.success or not result.terminal:
                    raise ExecutionFailure("Browser Worker did not accept bounded finish")
                return self._result(
                    request,
                    "finished_ungraded",
                    "Planning Agent finished immediately; independent grading is required",
                    ledger,
                    plan_id,
                    topology,
                    step_results,
                    rejection_reasons,
                )

            state_machine = StepStateMachine(plan.dag)
            if request.fake_scenario == "out_of_order_probe":
                try:
                    state_machine.start(topology[1])
                except DependencyBlocked as exc:
                    ledger.charge_step(blocked=True)
                    step_results.append(
                        StepExecutionResult(
                            step_id=topology[1],
                            state="blocked",
                            action_count=0,
                        )
                    )
                    return self._result(
                        request,
                        "dependency_blocked",
                        str(exc),
                        ledger,
                        plan_id,
                        topology,
                        step_results,
                        rejection_reasons,
                    )
                raise ExecutionFailure("Out-of-order dependency probe unexpectedly executed")
            first_step = step_by_id(plan.dag, topology[0])
            probe = self._matcher.match(
                first_step,
                "shell",
                page=self._page(observation),
                modality="dom",
                worker_allowed=GLOBAL_TOOLS,
                ledger=ledger,
            )
            if probe.rejection_reason is not None:
                rejection_reasons.append(probe.rejection_reason)
            if probe.matched:
                raise ExecutionFailure("Unknown tool probe unexpectedly matched")

            explicit_probe_remaining = True
            for step_id in topology:
                step = step_by_id(plan.dag, step_id)
                try:
                    state_machine.start(step_id)
                except DependencyBlocked as exc:
                    ledger.charge_step(blocked=True)
                    step_results.append(
                        StepExecutionResult(step_id=step_id, state="blocked", action_count=0)
                    )
                    return self._result(
                        request,
                        "dependency_blocked",
                        str(exc),
                        ledger,
                        plan_id,
                        topology,
                        step_results,
                        rejection_reasons,
                    )
                ledger.charge_step()
                observation, action_success, action_count = await self._execute_operation(
                    session_id,
                    observation,
                    step,
                    request.supplied_values,
                    ledger,
                )
                used_probe = False
                if explicit_probe_remaining:
                    observation = await self._browser.request_dom_observation(session_id)
                    ledger.charge_dom_observation(observation.route_signals.dom_observation_bytes)
                    explicit_probe_remaining = False
                    used_probe = True
                verification = self._verifier.verify(
                    VerifierRequest(
                        step_id=step.step_id,
                        expected_page=step.expected_page,
                        current_page=self._page(observation),
                        observation_generation=observation.generation,
                        action_success=action_success,
                        postconditions=step.postconditions,
                        force_inconclusive=(
                            request.fake_scenario == "verifier_inconclusive" and not step_results
                        ),
                    ),
                    ledger,
                    probe=used_probe,
                )
                if verification.status != "verified":
                    terminal_state: StepState = (
                        "escalated" if step.fallback == "escalate" else "failed"
                    )
                    state_machine.terminate(step_id, terminal_state)
                    ledger.charge_step(blocked=True)
                    step_results.append(
                        StepExecutionResult(
                            step_id=step_id,
                            state=terminal_state,
                            action_count=action_count,
                            verifier=verification,
                        )
                    )
                    status: PlanningRunStatus = (
                        "verification_inconclusive"
                        if verification.status == "inconclusive"
                        else "verification_not_verified"
                    )
                    return self._result(
                        request,
                        status,
                        "Runtime step verification did not verify the step",
                        ledger,
                        plan_id,
                        topology,
                        step_results,
                        rejection_reasons,
                    )
                state_machine.verify(step_id)
                step_results.append(
                    StepExecutionResult(
                        step_id=step_id,
                        state="verified",
                        action_count=action_count,
                        verifier=verification,
                    )
                )

            final_step = step_by_id(plan.dag, topology[-1])
            matched = self._matcher.match(
                final_step,
                "finish",
                page=self._page(observation),
                modality="dom",
                worker_allowed=GLOBAL_TOOLS,
                ledger=ledger,
            )
            if not matched.matched:
                if matched.rejection_reason is not None:
                    rejection_reasons.append(matched.rejection_reason)
                raise ExecutionFailure(
                    "Final finish tool was rejected",
                    matched.rejection_reason,
                )
            result = await self._finish(session_id, observation, ledger)
            if not result.success or not result.terminal:
                raise ExecutionFailure("Browser Worker did not accept bounded finish")
            return self._result(
                request,
                "finished_ungraded",
                "Planning Agent finished; independent database-fact grading is required",
                ledger,
                plan_id,
                topology,
                step_results,
                rejection_reasons,
            )
        except BudgetExceeded as exc:
            return self._result(
                request,
                "budget_exhausted",
                exc.reason,
                ledger,
                plan_id,
                topology,
                step_results,
                rejection_reasons,
            )
        except ExecutionFailure as exc:
            if exc.rejection is not None:
                rejection_reasons.append(exc.rejection)
            return self._result(
                request,
                "tool_rejected" if exc.rejection is not None else "failed",
                exc.safe_reason,
                ledger,
                plan_id,
                topology,
                step_results,
                rejection_reasons,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            return self._result(
                request,
                "browser_error",
                "Planning Agent could not complete the isolated Browser Worker run",
                ledger,
                plan_id,
                topology,
                step_results,
                rejection_reasons,
            )
        finally:
            if session_id is not None:
                with suppress(Exception):
                    await self._browser.close_session(session_id)

    async def _execute_operation(
        self,
        session_id: str,
        observation: HybridDomObservation,
        step: PlanStep,
        supplied_values: SuppliedValues,
        ledger: TotalBudgetLedger,
    ) -> tuple[HybridDomObservation, bool, int]:
        action_count = 0
        action_success = False
        for instruction in self._instructions(step, supplied_values):
            worker_allowed = self._worker_allowed(observation)
            match = self._matcher.match(
                step,
                instruction.action,
                page=self._page(observation),
                modality="dom",
                worker_allowed=worker_allowed,
                ledger=ledger,
            )
            if not match.matched:
                raise ExecutionFailure(
                    "Current step tool intersection rejected an action",
                    match.rejection_reason,
                )
            envelope = self._envelope(observation, instruction)
            ledger.charge_action()
            result = await self._browser.execute_action(session_id, envelope)
            action_count += 1
            action_success = result.success
            if result.terminal or result.observation is None:
                raise ExecutionFailure("A non-final Planning step terminated the Worker session")
            observation = result.observation
            ledger.charge_dom_observation(observation.route_signals.dom_observation_bytes)
            if not result.success:
                break
        return observation, action_success, action_count

    async def _finish(
        self,
        session_id: str,
        observation: HybridDomObservation,
        ledger: TotalBudgetLedger,
    ) -> HybridActionResult:
        ledger.charge_action()
        return await self._browser.execute_action(
            session_id,
            HybridDomActionEnvelope(
                session_id=session_id,
                generation=observation.generation,
                action=DomFinishAction(
                    action_id=self._next_action_id(),
                    summary="Deterministic Planning run ended; grading remains external",
                ),
            ),
        )

    def _envelope(
        self,
        observation: HybridDomObservation,
        instruction: _Instruction,
    ) -> HybridDomActionEnvelope:
        action_id = self._next_action_id()
        if instruction.action == "navigate":
            action: DomAction = DomNavigateAction(
                action_id=action_id,
                url=PAGE_PATH[self._required_page(instruction)],
            )
        elif instruction.action == "fill":
            element = self._element(observation, "fill", instruction.label)
            action = DomFillAction(
                action_id=action_id,
                observation_id=observation.observation.observation_id,
                element_ref=element.element_ref,
                text=instruction.value or "",
            )
        elif instruction.action == "click":
            element = self._element(observation, "click", instruction.label)
            action = DomClickAction(
                action_id=action_id,
                observation_id=observation.observation.observation_id,
                element_ref=element.element_ref,
            )
        elif instruction.action == "read":
            element = self._element(observation, "read", instruction.label)
            action = DomReadAction(
                action_id=action_id,
                observation_id=observation.observation.observation_id,
                element_ref=element.element_ref,
            )
        else:
            raise ExecutionFailure("Fake executor received an unsupported instruction")
        return HybridDomActionEnvelope(
            session_id=observation.session_id,
            generation=observation.generation,
            action=action,
        )

    @staticmethod
    def _required_page(instruction: _Instruction) -> Page:
        if instruction.value not in PATH_PAGE:
            raise ExecutionFailure("Navigate instruction was outside the fixed Sandbox paths")
        return PATH_PAGE[cast(SandboxPath, instruction.value)]

    @staticmethod
    def _element(
        observation: HybridDomObservation,
        action: str,
        label: str | None,
    ) -> InteractiveElement:
        candidates = [
            element
            for element in observation.observation.interactive_elements
            if action in element.allowed_actions and not element.state.disabled
        ]
        if label is not None:
            normalized = label.strip().casefold()
            candidates = [
                element for element in candidates if element.name.strip().casefold() == normalized
            ]
        if not candidates:
            raise ExecutionFailure("Current DOM observation lacked an authorized element")
        return candidates[0]

    @staticmethod
    def _page(observation: HybridDomObservation) -> Page:
        path = urlsplit(observation.observation.current_url).path.rstrip("/") or "/hris"
        try:
            return PATH_PAGE[cast(SandboxPath, path)]
        except KeyError as exc:
            raise ExecutionFailure("Worker observation was outside fixed Sandbox pages") from exc

    @staticmethod
    def _worker_allowed(observation: HybridDomObservation) -> frozenset[AllowedAction]:
        allowed: set[AllowedAction] = {"navigate", "wait", "finish", "fail"}
        for element in observation.observation.interactive_elements:
            if not element.state.disabled:
                allowed.update(element.allowed_actions)
        return frozenset(allowed)

    @staticmethod
    def _instructions(step: PlanStep, values: SuppliedValues) -> tuple[_Instruction, ...]:
        navigate = _Instruction("navigate", value=PAGE_PATH[step.expected_page])
        show_transitions = _Instruction("click", "Show transitions")
        operation = step.operation
        if operation in {"inspect_employee", "finalize"}:
            return (navigate, _Instruction("read"))
        employee_id = str(values.employee_id)
        if operation == "create_ticket" and isinstance(values, JoinerSuppliedValues):
            return (
                navigate,
                _Instruction("fill", "Employee ID", employee_id),
                _Instruction("fill", "Ticket title", values.ticket_title),
                _Instruction("click", "Create ticket"),
            )
        if operation == "create_account" and isinstance(values, JoinerSuppliedValues):
            return (
                navigate,
                _Instruction("fill", "Employee ID", employee_id),
                _Instruction("fill", "Username", values.username),
                _Instruction("click", "Create account"),
            )
        if operation == "assign_asset" and isinstance(values, JoinerSuppliedValues):
            return (
                navigate,
                _Instruction("fill", "Employee ID", employee_id),
                _Instruction("fill", "Asset tag", values.asset_tag),
                _Instruction("fill", "Model", values.laptop_model),
                _Instruction("click", "Assign laptop"),
            )
        if operation == "create_mailbox" and isinstance(values, JoinerSuppliedValues):
            return (
                navigate,
                _Instruction("fill", "Employee ID", employee_id),
                _Instruction("fill", "Mailbox address", values.mailbox),
                _Instruction("click", "Create mailbox"),
            )
        if operation == "transfer_employee" and isinstance(values, MoverSuppliedValues):
            return (
                navigate,
                show_transitions,
                _Instruction("fill", "Transfer employee ID", employee_id),
                _Instruction("fill", "New department", values.new_department),
                _Instruction("fill", "New job title", values.new_job_title),
                _Instruction("fill", "New location", values.new_location),
                _Instruction("click", "Transfer employee"),
            )
        transitions = {
            "disable_employee": ("Disable employee ID", "Disable employee"),
            "close_ticket": ("Close ticket employee ID", "Close ticket"),
            "revoke_account": ("Revoke account employee ID", "Revoke account"),
            "release_asset": ("Release asset employee ID", "Release asset"),
            "disable_mailbox": ("Disable mailbox employee ID", "Disable mailbox"),
        }
        if operation in transitions and isinstance(
            values, (MoverSuppliedValues, LeaverSuppliedValues)
        ):
            field, button = transitions[operation]
            return (
                navigate,
                show_transitions,
                _Instruction("fill", field, employee_id),
                _Instruction("click", button),
            )
        raise ExecutionFailure("Supplied values did not match the closed operation")

    def _next_action_id(self) -> str:
        self._action_number += 1
        return f"act_w7_{self._action_number}"

    @staticmethod
    def _result(
        request: PlanningRunRequest,
        status: PlanningRunStatus,
        reason: str,
        ledger: TotalBudgetLedger,
        plan_id: str | None,
        topology: tuple[str, ...],
        step_results: list[StepExecutionResult],
        rejection_reasons: list[ToolRejectionReason],
    ) -> PlanningRunResult:
        return PlanningRunResult(
            run_id=request.run_id,
            task_id=request.task_id,
            status=status,
            terminal_reason=reason[:300],
            plan_id=plan_id,
            topology=topology,
            step_results=tuple(step_results),
            tool_rejection_reasons=tuple(rejection_reasons),
            usage=ledger.snapshot(),
        )
