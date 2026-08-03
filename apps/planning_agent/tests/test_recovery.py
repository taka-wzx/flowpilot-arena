import asyncio
import hashlib
import json
from typing import cast

from flowpilot_planning_agent.budget import TotalBudgetLedger
from flowpilot_planning_agent.client import BrowserWorkerClient
from flowpilot_planning_agent.dag import step_by_id
from flowpilot_planning_agent.planner import DeterministicPlanner
from flowpilot_planning_agent.recovery import RecoveryCoordinator, RecoveryRunState
from flowpilot_planning_agent.recovery_schemas import (
    Checkpoint,
    DurableUsage,
    PlanningActivityResult,
    PlanningRecoveryActivity,
    ReceiptRecord,
)
from flowpilot_planning_agent.schemas import (
    LeaverSuppliedValues,
    MoverSuppliedValues,
    PlanRequest,
    TotalBudget,
)
from flowpilot_planning_agent.worker_schemas import HybridDomObservation


def _start_activity(run_id: str) -> PlanningRecoveryActivity:
    return PlanningRecoveryActivity.model_validate(
        {
            "command": "start",
            "workflow_id": f"workflow_{run_id}",
            "run_id": run_id,
            "task_id": "w7-jml-leaver-001-v1",
            "process": "leaver",
            "category": "standard_leaver",
            "human_brief": "Synthetic bounded brief",
            "supplied_values": {"process": "leaver", "employee_id": 101},
            "fault_scenario": "none",
            "checkpoint": None,
            "step_id": None,
            "session_epoch": 1,
            "revision": 1,
        }
    )


def _checkpoint(
    *,
    workflow_id: str,
    run_id: str,
    task_id: str,
    plan_hash: str,
    topology: tuple[str, ...],
    completed: tuple[str, ...],
    remaining: tuple[str, ...],
    usage: DurableUsage,
) -> Checkpoint:
    payload = {
        "schema_version": "w8-checkpoint/1.0",
        "workflow_id": workflow_id,
        "run_id": run_id,
        "task_id": task_id,
        "plan_hash": plan_hash,
        "revision": 1,
        "topology": topology,
        "completed_step_ids": completed,
        "remaining_step_ids": remaining,
        "session_epoch": 1,
        "absolute_deadline_ms": 1,
        "usage": usage.model_dump(mode="json"),
        "receipt_hashes": (),
        "closed_reason": "planning_complete",
        "parent_checkpoint_hash": "0" * 64,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return Checkpoint.model_validate(
        {**payload, "checkpoint_hash": hashlib.sha256(canonical).hexdigest()}
    )


class _ConcurrencyProbeCoordinator(RecoveryCoordinator):
    def __init__(self) -> None:
        super().__init__(cast(BrowserWorkerClient, None))
        self.entered: list[str] = []
        self.release = asyncio.Event()

    async def _start(self, request: PlanningRecoveryActivity) -> PlanningActivityResult:
        self.entered.append(request.run_id)
        if len(self.entered) == 2:
            self.release.set()
        await asyncio.wait_for(self.release.wait(), timeout=1)
        return PlanningActivityResult(
            outcome="cleaned",
            safe_reason="concurrency probe",
            session_epoch=request.session_epoch,
            revision=request.revision,
        )


def test_recovery_activity_locks_are_scoped_per_run() -> None:
    async def exercise() -> None:
        coordinator = _ConcurrencyProbeCoordinator()
        await asyncio.gather(
            coordinator.invoke(_start_activity("run_w8_parallel_a")),
            coordinator.invoke(_start_activity("run_w8_parallel_b")),
        )
        assert coordinator.entered == ["run_w8_parallel_a", "run_w8_parallel_b"]

    asyncio.run(exercise())


def test_recovery_step_retry_replays_completed_result_without_browser_action() -> None:
    async def exercise() -> None:
        coordinator = RecoveryCoordinator(cast(BrowserWorkerClient, None))
        workflow_id = "workflow_replay_0001"
        run_id = "run_replay_0001"
        task_id = "w7-jml-mover-001-v1"
        supplied_values = MoverSuppliedValues(
            process="mover",
            employee_id=41131,
            new_department="Synthetic Transfer Department 1",
            new_job_title="Synthetic Transfer Lead 1",
            new_location="Synthetic Transfer Location 1",
        )
        plan = DeterministicPlanner().generate(
            PlanRequest(
                process="mover",
                category="standard_mover",
                human_brief="Synthetic bounded brief",
                supplied_values=supplied_values,
            )
        )
        topology = ("s10_transfer", "s20_close", "s90_finalize")
        ledger = TotalBudgetLedger(TotalBudget())
        usage = DurableUsage(planning_usage=ledger.snapshot())
        receipt = ReceiptRecord(
            idempotency_key=f"op_{'a' * 64}",
            request_hash="b" * 64,
            result_hash="c" * 64,
            state="created",
        )
        cached = PlanningActivityResult(
            outcome="verified",
            safe_reason="step verified from current safe evidence",
            plan_hash=plan.plan_id,
            topology=topology,
            step_id="s10_transfer",
            session_epoch=1,
            revision=1,
            receipt=receipt,
            planning_usage=ledger.snapshot(),
        )
        state = RecoveryRunState(
            request_identity=(workflow_id, run_id, task_id),
            dag=plan.dag,
            plan_hash=plan.plan_id,
            topology=topology,
            session_id="bw_replay_0001",
            session_epoch=1,
            observation=cast(HybridDomObservation, None),
            ledger=ledger,
            completed={"s10_transfer"},
            completed_results={"s10_transfer": cached},
            action_number=6,
        )
        coordinator._runs[run_id] = state

        replay = await coordinator.invoke(
            PlanningRecoveryActivity(
                command="step",
                workflow_id=workflow_id,
                run_id=run_id,
                task_id=task_id,
                process="mover",
                category="standard_mover",
                human_brief="Synthetic bounded brief",
                supplied_values=supplied_values,
                fault_scenario="none",
                checkpoint=_checkpoint(
                    workflow_id=workflow_id,
                    run_id=run_id,
                    task_id=task_id,
                    plan_hash=plan.plan_id,
                    topology=topology,
                    completed=(),
                    remaining=topology,
                    usage=usage,
                ),
                step_id="s10_transfer",
                session_epoch=1,
                revision=1,
            )
        )

        assert replay == cached
        assert state.action_number == 6

    asyncio.run(exercise())


def test_recovery_activity_requires_step_for_step_commands() -> None:
    base = {
        "command": "step",
        "workflow_id": "workflow_w8_schema",
        "run_id": "run_w8_schema",
        "task_id": "w7-jml-leaver-001-v1",
        "process": "leaver",
        "category": "standard_leaver",
        "human_brief": "Synthetic bounded brief",
        "supplied_values": {"process": "leaver", "employee_id": 101},
        "fault_scenario": "none",
        "checkpoint": None,
        "step_id": None,
        "session_epoch": 1,
        "revision": 1,
    }
    try:
        PlanningRecoveryActivity.model_validate(base)
    except ValueError:
        pass
    else:
        raise AssertionError("step command without step_id was accepted")


def test_recovery_finalization_reuses_navigation_observation() -> None:
    plan = DeterministicPlanner().generate(
        PlanRequest(
            process="leaver",
            category="standard_leaver",
            human_brief="Synthetic bounded brief",
            supplied_values=LeaverSuppliedValues(process="leaver", employee_id=101),
        )
    )
    final_step = step_by_id(plan.dag, "s90_finalize")

    instructions = RecoveryCoordinator._instructions_for_step(
        final_step,
        LeaverSuppliedValues(process="leaver", employee_id=101),
        current_page="mail",
    )

    assert tuple(instruction.action for instruction in instructions) == ("navigate",)


def test_recovery_reuses_matching_initial_page_observation() -> None:
    plan = DeterministicPlanner().generate(
        PlanRequest(
            process="leaver",
            category="standard_leaver",
            human_brief="Synthetic bounded brief",
            supplied_values=LeaverSuppliedValues(process="leaver", employee_id=101),
        )
    )
    first_step = step_by_id(plan.dag, "s10_disable_employee")

    instructions = RecoveryCoordinator._instructions_for_step(
        first_step,
        LeaverSuppliedValues(process="leaver", employee_id=101),
        current_page="hris",
    )

    assert tuple(instruction.action for instruction in instructions) == ("click", "fill", "click")


def test_recovery_classifies_only_transient_browser_errors_as_session_loss() -> None:
    assert RecoveryCoordinator._is_recoverable_browser_failure(False, "browser_timeout")
    assert RecoveryCoordinator._is_recoverable_browser_failure(False, "browser_error")
    assert not RecoveryCoordinator._is_recoverable_browser_failure(False, "input_rejected")
    assert not RecoveryCoordinator._is_recoverable_browser_failure(False, "stale_hybrid_ref")
    assert not RecoveryCoordinator._is_recoverable_browser_failure(True, "browser_timeout")
