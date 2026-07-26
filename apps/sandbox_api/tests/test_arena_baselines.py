from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.baselines import (
    DuplicateBaselineRecordError,
    create_baseline_record,
    list_baseline_records,
)
from flowpilot_sandbox_api.arena.catalog import get_catalog
from flowpilot_sandbox_api.arena.schemas import ManualBaselineCreate


def _payload() -> ManualBaselineCreate:
    return ManualBaselineCreate(
        record_id="baseline-w3-sample-001",
        task_id="w3-joiner-001",
        operator_alias="anon-operator-01",
        started_at=datetime(2026, 7, 26, 4, 0, tzinfo=UTC),
        ended_at=datetime(2026, 7, 26, 4, 12, 30, tzinfo=UTC),
        action_count=18,
        notes="Synthetic W3 manual baseline sample",
    )


def test_records_only_declared_manual_baseline_fields(db_session: Session) -> None:
    record = create_baseline_record(db_session, get_catalog(), _payload())
    assert record.duration_seconds == 750
    assert record.final_score < 100
    assert record.operator_alias == "anon-operator-01"
    assert [item.record_id for item in list_baseline_records(db_session)] == [
        "baseline-w3-sample-001"
    ]


def test_rejects_duplicate_unknown_task_and_nonanonymous_alias(db_session: Session) -> None:
    create_baseline_record(db_session, get_catalog(), _payload())
    with pytest.raises(DuplicateBaselineRecordError):
        create_baseline_record(db_session, get_catalog(), _payload())

    unknown = _payload().model_copy(
        update={"record_id": "baseline-w3-unknown-001", "task_id": "w3-joiner-099"}
    )
    with pytest.raises(KeyError, match="Unknown Arena task"):
        create_baseline_record(db_session, get_catalog(), unknown)

    with pytest.raises(ValidationError, match="operator_alias"):
        ManualBaselineCreate.model_validate(
            {
                **_payload().model_dump(),
                "record_id": "baseline-w3-bad-alias",
                "operator_alias": "Real Person",
            }
        )


def test_rejects_reversed_or_subsecond_timestamps() -> None:
    with pytest.raises(ValidationError, match="must not precede"):
        ManualBaselineCreate.model_validate(
            {
                **_payload().model_dump(),
                "record_id": "baseline-w3-reversed",
                "ended_at": datetime(2026, 7, 26, 3, 0, tzinfo=UTC),
            }
        )
    with pytest.raises(ValidationError, match="whole seconds"):
        ManualBaselineCreate.model_validate(
            {
                **_payload().model_dump(),
                "record_id": "baseline-w3-subsecond",
                "ended_at": datetime(2026, 7, 26, 4, 12, 30, 1, tzinfo=UTC),
            }
        )
