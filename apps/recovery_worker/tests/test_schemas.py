from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from flowpilot_recovery_worker.schemas import (
    DurableUsage,
    WorkflowStart,
    build_checkpoint,
    validate_checkpoint,
)


def test_checkpoint_hash_lineage_and_step_partition(workflow_start: WorkflowStart) -> None:
    checkpoint = build_checkpoint(
        start=workflow_start,
        plan_hash="a" * 64,
        revision=1,
        topology=("s00_inspect", "s10_ticket"),
        completed=("s00_inspect",),
        remaining=("s10_ticket",),
        session_epoch=1,
        deadline=datetime.now(UTC) + timedelta(seconds=300),
        usage=DurableUsage(),
        receipt_hashes=(),
        reason="step_verified",
        parent_hash="0" * 64,
    )
    validate_checkpoint(checkpoint)
    with pytest.raises(ValueError):
        validate_checkpoint(checkpoint.model_copy(update={"checkpoint_hash": "f" * 64}))


def test_unknown_state_version_and_limit_fail_closed(workflow_start: WorkflowStart) -> None:
    payload = workflow_start.model_dump(mode="json")
    payload["selector"] = "#unsafe"
    with pytest.raises(ValidationError):
        WorkflowStart.model_validate(payload)
    with pytest.raises(ValidationError):
        WorkflowStart.model_validate(
            {**workflow_start.model_dump(mode="json"), "fault_scenario": "page_directed"}
        )
