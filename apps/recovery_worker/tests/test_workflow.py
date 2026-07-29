import pytest

from flowpilot_recovery_worker.schemas import (
    ActivityResult,
    DurableUsage,
    PlanningUsage,
    ReceiptRecord,
)
from flowpilot_recovery_worker.workflow import _charge


def test_activity_attempt_and_receipt_usage_never_reset() -> None:
    first = _charge(
        DurableUsage(activity_attempts=3, retries=1),
        ActivityResult(
            outcome="verified",
            safe_reason="receipt replayed",
            session_epoch=1,
            revision=1,
            activity_attempt=2,
            receipt=ReceiptRecord(
                idempotency_key="op_" + "1" * 64,
                request_hash="2" * 64,
                result_hash="3" * 64,
                state="replayed",
            ),
        ),
        fault=True,
    )
    assert first.activity_attempts == 5
    assert first.retries == 2
    assert first.receipt_replays == 1
    assert first.faults == 1


def test_planning_usage_high_water_cannot_reset() -> None:
    usage = DurableUsage(planning_usage=PlanningUsage(worker_actions=4, verifier_calls=1))
    with pytest.raises(ValueError, match="cannot reset"):
        _charge(
            usage,
            ActivityResult(
                outcome="verified",
                safe_reason="invalid lower ledger",
                session_epoch=1,
                revision=1,
                planning_usage=PlanningUsage(worker_actions=3, verifier_calls=1),
            ),
        )
