import json
import tempfile

from temporalio import activity
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.exceptions import ApplicationError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker

from flowpilot_recovery_worker.schemas import ActivityRequest, ActivityResult, WorkflowResult
from flowpilot_recovery_worker.workflow import DurableRecoveryWorkflow


@activity.defn(name="w8_start_run")
async def start_run(payload: dict[str, object]) -> dict[str, object]:
    request = ActivityRequest.model_validate(payload)
    return ActivityResult(
        outcome="started",
        safe_reason="started",
        plan_hash="a" * 64,
        topology=("s00_inspect",),
        session_epoch=request.session_epoch,
        revision=request.revision,
    ).model_dump(mode="json")


@activity.defn(name="w8_execute_step")
async def execute_step(payload: dict[str, object]) -> dict[str, object]:
    request = ActivityRequest.model_validate(payload)
    return ActivityResult(
        outcome="verified",
        safe_reason="verified",
        plan_hash="a" * 64,
        topology=("s00_inspect",),
        step_id=request.step_id,
        session_epoch=request.session_epoch,
        revision=request.revision,
    ).model_dump(mode="json")


@activity.defn(name="w8_cleanup")
async def cleanup(payload: dict[str, object]) -> dict[str, object]:
    request = ActivityRequest.model_validate(payload)
    return ActivityResult(
        outcome="cleaned",
        safe_reason="cleaned",
        plan_hash="a" * 64,
        topology=("s00_inspect",),
        session_epoch=request.session_epoch,
        revision=request.revision,
    ).model_dump(mode="json")


class TimeoutThenVerifiedActivities:
    def __init__(self) -> None:
        self.step_calls = 0

    @activity.defn(name="w8_start_run")
    async def start_run(self, payload: dict[str, object]) -> dict[str, object]:
        request = ActivityRequest.model_validate(payload)
        return ActivityResult(
            outcome="started",
            safe_reason="started",
            plan_hash="a" * 64,
            topology=("s00_inspect",),
            session_epoch=request.session_epoch,
            revision=request.revision,
        ).model_dump(mode="json")

    @activity.defn(name="w8_execute_step")
    async def execute_step(self, payload: dict[str, object]) -> dict[str, object]:
        self.step_calls += 1
        request = ActivityRequest.model_validate(payload)
        if self.step_calls <= 2:
            raise ApplicationError(
                "planning recovery read timed out",
                type="ReadTimeout",
                non_retryable=False,
            )
        return ActivityResult(
            outcome="verified",
            safe_reason="verified after lost response",
            plan_hash="a" * 64,
            topology=("s00_inspect",),
            step_id=request.step_id,
            session_epoch=request.session_epoch,
            revision=request.revision,
        ).model_dump(mode="json")

    @activity.defn(name="w8_cleanup")
    async def cleanup(self, payload: dict[str, object]) -> dict[str, object]:
        request = ActivityRequest.model_validate(payload)
        return ActivityResult(
            outcome="cleaned",
            safe_reason="cleaned",
            plan_hash="a" * 64,
            topology=("s00_inspect",),
            session_epoch=request.session_epoch,
            revision=request.revision,
        ).model_dump(mode="json")


async def test_workflow_history_replays_and_contains_no_plaintext(workflow_start) -> None:
    environment = await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter,
        download_dest_dir=tempfile.gettempdir(),
    )
    try:
        async with Worker(
            environment.client,
            task_queue="w8-replay-test",
            workflows=[DurableRecoveryWorkflow],
            activities=[start_run, execute_step, cleanup],
        ):
            handle = await environment.client.start_workflow(
                DurableRecoveryWorkflow.run,
                workflow_start.model_dump(mode="json"),
                id="workflow-w8-replay-test",
                task_queue="w8-replay-test",
            )
            result = WorkflowResult.model_validate(await handle.result())
            assert result.status == "finished_ungraded"
            assert result.checkpoint_count == 2
            history = await handle.fetch_history()

        replay = await Replayer(
            workflows=[DurableRecoveryWorkflow], data_converter=pydantic_data_converter
        ).replay_workflow(history)
        assert replay.replay_failure is None
        serialized = json.dumps(history.to_json_dict(), sort_keys=True)
        for sentinel in (
            "Synthetic secret recovery brief",
            "Synthetic secret ticket",
            "secret.user@example.invalid",
            "SYN-W8-SECRET",
        ):
            assert sentinel not in serialized
    finally:
        await environment.shutdown()


async def test_step_read_timeout_is_recoverable_lost_response(workflow_start) -> None:
    environment = await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter,
        download_dest_dir=tempfile.gettempdir(),
    )
    activities = TimeoutThenVerifiedActivities()
    try:
        async with Worker(
            environment.client,
            task_queue="w8-read-timeout-test",
            workflows=[DurableRecoveryWorkflow],
            activities=[activities.start_run, activities.execute_step, activities.cleanup],
        ):
            handle = await environment.client.start_workflow(
                DurableRecoveryWorkflow.run,
                workflow_start.model_dump(mode="json"),
                id="workflow-w8-read-timeout-test",
                task_queue="w8-read-timeout-test",
            )
            result = WorkflowResult.model_validate(await handle.result())

        assert result.status == "finished_ungraded"
        assert result.terminal_reason == "completed"
        assert result.completed_step_ids == ("s00_inspect",)
        assert result.usage.faults == 1
        assert result.usage.activity_attempts == 5
        assert result.usage.retries == 1
        assert activities.step_calls == 3
    finally:
        await environment.shutdown()
