from types import SimpleNamespace

import pytest
from temporalio.exceptions import ApplicationError

from flowpilot_recovery_worker.activities import RecoveryActivities
from flowpilot_recovery_worker.schemas import (
    ActivityRequest,
    ActivityResult,
    ReceiptRecord,
)


class StubClient:
    async def invoke(self, command, request, plain) -> ActivityResult:
        assert command == "step"
        assert plain.task_id == request.start.task_id
        return ActivityResult(
            outcome="verified",
            safe_reason="committed",
            plan_hash="a" * 64,
            topology=("s10_ticket",),
            step_id="s10_ticket",
            session_epoch=1,
            revision=1,
            receipt=ReceiptRecord(
                idempotency_key="op_" + "1" * 64,
                request_hash="2" * 64,
                result_hash="3" * 64,
                state="created",
            ),
        )


async def test_pre_dispatch_fault_is_retryable_and_does_not_call_client(
    workflow_start, envelope_key: bytes, monkeypatch
) -> None:
    called = False

    class NeverClient:
        async def invoke(self, command, request, plain):
            nonlocal called
            called = True
            raise AssertionError("client must not be called")

    monkeypatch.setattr(
        "flowpilot_recovery_worker.activities.activity.info", lambda: SimpleNamespace(attempt=1)
    )
    activities = RecoveryActivities(NeverClient(), envelope_key)  # type: ignore[arg-type]
    request = ActivityRequest(
        start=workflow_start.model_copy(update={"fault_scenario": "activity_pre_dispatch_once"}),
        step_id="s10_ticket",
    )
    with pytest.raises(ApplicationError) as captured:
        await activities.execute_step(request.model_dump(mode="json"))
    assert captured.value.non_retryable is False
    assert called is False


async def test_post_commit_fault_raises_after_safe_receipt(
    workflow_start, envelope_key: bytes, monkeypatch
) -> None:
    monkeypatch.setattr(
        "flowpilot_recovery_worker.activities.activity.info", lambda: SimpleNamespace(attempt=1)
    )
    activities = RecoveryActivities(StubClient(), envelope_key)  # type: ignore[arg-type]
    request = ActivityRequest(
        start=workflow_start.model_copy(
            update={"fault_scenario": "post_commit_pre_checkpoint_once"}
        ),
        step_id="s10_ticket",
    )
    with pytest.raises(ApplicationError) as captured:
        await activities.execute_step(request.model_dump(mode="json"))
    assert captured.value.non_retryable is False
