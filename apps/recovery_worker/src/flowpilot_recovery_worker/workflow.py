from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, CancelledError

with workflow.unsafe.imports_passed_through():
    from flowpilot_recovery_worker.schemas import (
        ActivityRequest,
        ActivityResult,
        Checkpoint,
        DurableUsage,
        TerminalReason,
        WorkflowResult,
        WorkflowStart,
        WorkflowTerminalStatus,
        build_checkpoint,
        validate_checkpoint,
    )

GENESIS_HASH = "0" * 64


def _charge(usage: DurableUsage, result: ActivityResult, *, fault: bool = False) -> DurableUsage:
    update: dict[str, object] = {
        "activity_attempts": usage.activity_attempts + result.activity_attempt,
        "retries": usage.retries + max(0, result.activity_attempt - 1),
        "faults": usage.faults + (1 if fault else 0),
        "receipt_creates": usage.receipt_creates,
        "receipt_replays": usage.receipt_replays,
        "receipt_mismatches": usage.receipt_mismatches,
    }
    if result.receipt is not None:
        if result.receipt.state == "created":
            update["receipt_creates"] = usage.receipt_creates + 1
        elif result.receipt.state == "replayed":
            update["receipt_replays"] = usage.receipt_replays + 1
        elif result.receipt.state == "mismatch":
            update["receipt_mismatches"] = usage.receipt_mismatches + 1
    if result.planning_usage is not None:
        current = usage.planning_usage.model_dump()
        incoming = result.planning_usage.model_dump()
        if any(incoming[field] < current[field] for field in current):
            raise ValueError("Planning usage counters cannot reset")
        update["planning_usage"] = result.planning_usage
    return usage.model_copy(update=update)


def _charge_recoverable_activity_error(usage: DurableUsage, *, attempts: int) -> DurableUsage:
    return usage.model_copy(
        update={
            "activity_attempts": usage.activity_attempts + attempts,
            "retries": usage.retries + max(0, attempts - 1),
            "faults": usage.faults + 1,
        }
    )


def _activity_error_type(exc: ActivityError) -> str | None:
    cause = getattr(exc, "cause", None)
    value = getattr(cause, "type", None)
    return value if isinstance(value, str) else None


def _is_recoverable_step_activity_error(exc: ActivityError) -> bool:
    return _activity_error_type(exc) == "ReadTimeout"


@workflow.defn(name="FlowPilotDurableRecoveryWorkflow")
class DurableRecoveryWorkflow:
    @workflow.run
    async def run(self, payload: dict[str, object]) -> dict[str, object]:
        start = WorkflowStart.model_validate(payload)
        deadline = workflow.now() + timedelta(seconds=start.budget.max_duration_seconds)
        usage = DurableUsage()
        completed: list[str] = []
        receipts: list[str] = []
        checkpoints: list[Checkpoint] = []
        plan_hash: str | None = None
        topology: tuple[str, ...] = ()
        revision = 1
        epoch = 1
        status: WorkflowTerminalStatus = "failed"
        terminal_reason: TerminalReason = "permanent_failure"

        async def invoke(
            name: str,
            request: ActivityRequest,
            *,
            retry: bool,
        ) -> ActivityResult:
            raw = await workflow.execute_activity(
                name,
                request.model_dump(mode="json"),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(milliseconds=100),
                    backoff_coefficient=1.0,
                    maximum_interval=timedelta(milliseconds=100),
                    maximum_attempts=start.budget.max_activity_attempts if retry else 1,
                    non_retryable_error_types=(
                        "schema_invalid",
                        "permission_denied",
                        "idempotency_mismatch",
                        "budget_exhausted",
                        "permanent_failure",
                    ),
                ),
                result_type=dict[str, object],
            )
            return ActivityResult.model_validate(raw)

        def request(
            *,
            step_id: str | None = None,
            checkpoint: Checkpoint | None = None,
        ) -> ActivityRequest:
            return ActivityRequest(
                start=start,
                checkpoint=checkpoint,
                step_id=step_id,
                session_epoch=epoch,
                revision=revision,
            )

        try:
            started = await invoke("w8_start_run", request(), retry=False)
            usage = _charge(usage, started)
            if started.outcome != "started" or started.plan_hash is None or not started.topology:
                raise ValueError("Planning start did not return a safe validated plan")
            plan_hash = started.plan_hash
            topology = started.topology
            initial = build_checkpoint(
                start=start,
                plan_hash=plan_hash,
                revision=revision,
                topology=topology,
                completed=(),
                remaining=topology,
                session_epoch=epoch,
                deadline=deadline,
                usage=usage,
                receipt_hashes=(),
                reason="planning_complete",
                parent_hash=GENESIS_HASH,
            )
            checkpoints.append(initial)

            while len(completed) < len(topology):
                if workflow.now() > deadline:
                    terminal_reason = "budget_exhausted"
                    break
                step_id = next(step for step in topology if step not in completed)
                latest = checkpoints[-1]
                try:
                    result = await invoke(
                        "w8_execute_step",
                        request(step_id=step_id, checkpoint=latest),
                        retry=True,
                    )
                except ActivityError as exc:
                    if _is_recoverable_step_activity_error(exc):
                        usage = _charge_recoverable_activity_error(
                            usage,
                            attempts=start.budget.max_activity_attempts,
                        )
                        if usage.faults > start.budget.max_faults:
                            terminal_reason = "budget_exhausted"
                            break
                        continue
                    terminal_reason = "permanent_failure"
                    break
                fault_used = result.activity_attempt > 1 or result.outcome in {
                    "session_lost",
                    "replan_eligible",
                    "permanent_failure",
                    "idempotency_mismatch",
                }
                usage = _charge(usage, result, fault=fault_used)
                if usage.faults > start.budget.max_faults:
                    terminal_reason = "budget_exhausted"
                    break

                if result.outcome == "verified":
                    completed.append(step_id)
                    if result.receipt is not None:
                        receipts.append(result.receipt.result_hash)
                    remaining = tuple(step for step in topology if step not in completed)
                    checkpoint = build_checkpoint(
                        start=start,
                        plan_hash=plan_hash,
                        revision=revision,
                        topology=topology,
                        completed=tuple(step for step in topology if step in completed),
                        remaining=remaining,
                        session_epoch=epoch,
                        deadline=deadline,
                        usage=usage,
                        receipt_hashes=tuple(receipts),
                        reason="step_verified",
                        parent_hash=checkpoints[-1].checkpoint_hash,
                    )
                    if start.fault_scenario == "checkpoint_hash_mismatch" and len(completed) == 1:
                        checkpoint = checkpoint.model_copy(update={"checkpoint_hash": "f" * 64})
                    if (
                        start.fault_scenario == "checkpoint_version_mismatch"
                        and len(completed) == 1
                    ):
                        terminal_reason = "checkpoint_invalid"
                        break
                    try:
                        validate_checkpoint(checkpoint)
                    except ValueError:
                        terminal_reason = "checkpoint_invalid"
                        break
                    checkpoints.append(checkpoint)
                    if len(checkpoints) > start.budget.max_checkpoints:
                        terminal_reason = "budget_exhausted"
                        break
                    continue

                if result.outcome == "session_lost":
                    refreshed = await invoke(
                        "w8_refresh", request(step_id=step_id, checkpoint=latest), retry=False
                    )
                    usage = _charge(usage, refreshed)
                    if usage.session_recoveries >= start.budget.max_session_recoveries:
                        terminal_reason = "recovery_exhausted"
                        break
                    epoch += 1
                    recovered = await invoke(
                        "w8_recover", request(step_id=step_id, checkpoint=latest), retry=False
                    )
                    usage = _charge(usage, recovered).model_copy(
                        update={"session_recoveries": usage.session_recoveries + 1}
                    )
                    if recovered.outcome != "started" or recovered.session_epoch != epoch:
                        terminal_reason = "recovery_exhausted"
                        break
                    recovery_checkpoint = build_checkpoint(
                        start=start,
                        plan_hash=plan_hash,
                        revision=revision,
                        topology=topology,
                        completed=tuple(step for step in topology if step in completed),
                        remaining=tuple(step for step in topology if step not in completed),
                        session_epoch=epoch,
                        deadline=deadline,
                        usage=usage,
                        receipt_hashes=tuple(receipts),
                        reason="session_recovered",
                        parent_hash=checkpoints[-1].checkpoint_hash,
                    )
                    validate_checkpoint(recovery_checkpoint)
                    checkpoints.append(recovery_checkpoint)
                    if len(checkpoints) > start.budget.max_checkpoints:
                        terminal_reason = "budget_exhausted"
                        break
                    continue

                if result.outcome == "replan_eligible":
                    if (
                        start.fault_scenario == "replan_disallowed"
                        or usage.replans >= start.budget.max_replans
                        or revision >= start.budget.max_revisions
                    ):
                        terminal_reason = "replan_disallowed"
                        break
                    revision += 1
                    replanned = await invoke(
                        "w8_replan", request(step_id=step_id, checkpoint=latest), retry=False
                    )
                    usage = _charge(usage, replanned).model_copy(
                        update={
                            "replans": usage.replans + 1,
                            "replaced_nodes": usage.replaced_nodes
                            + len(replanned.replaced_step_ids),
                        }
                    )
                    if replanned.plan_hash is None or not replanned.topology:
                        terminal_reason = "replan_disallowed"
                        break
                    plan_hash = replanned.plan_hash
                    topology = replanned.topology
                    if any(step not in topology for step in completed):
                        terminal_reason = "replan_disallowed"
                        break
                    replan_checkpoint = build_checkpoint(
                        start=start,
                        plan_hash=plan_hash,
                        revision=revision,
                        topology=topology,
                        completed=tuple(step for step in topology if step in completed),
                        remaining=tuple(step for step in topology if step not in completed),
                        session_epoch=epoch,
                        deadline=deadline,
                        usage=usage,
                        receipt_hashes=tuple(receipts),
                        reason="partial_replan",
                        parent_hash=checkpoints[-1].checkpoint_hash,
                    )
                    validate_checkpoint(replan_checkpoint)
                    checkpoints.append(replan_checkpoint)
                    continue

                if result.outcome == "idempotency_mismatch":
                    terminal_reason = "idempotency_mismatch"
                    break
                terminal_reason = "permanent_failure"
                break
            else:
                status = "finished_ungraded"
                terminal_reason = "completed"
        except CancelledError:
            status = "cancelled"
            terminal_reason = "cancelled"
        except (ActivityError, ValueError):
            status = "failed"
            terminal_reason = "permanent_failure"
        finally:
            try:
                cleaned = await invoke(
                    "w8_cleanup",
                    request(checkpoint=checkpoints[-1] if checkpoints else None),
                    retry=False,
                )
                usage = _charge(usage, cleaned)
            except (ActivityError, CancelledError):
                if status == "finished_ungraded":
                    status = "failed"
                    terminal_reason = "permanent_failure"

        final_result = WorkflowResult(
            workflow_id=start.workflow_id,
            run_id=start.run_id,
            task_id=start.task_id,
            status=status,
            terminal_reason=terminal_reason,
            plan_hash=plan_hash,
            revision=revision,
            session_epoch=epoch,
            completed_step_ids=tuple(step for step in topology if step in completed),
            checkpoint_count=len(checkpoints),
            latest_checkpoint_hash=(checkpoints[-1].checkpoint_hash if checkpoints else None),
            usage=usage,
        )
        return final_result.model_dump(mode="json")
