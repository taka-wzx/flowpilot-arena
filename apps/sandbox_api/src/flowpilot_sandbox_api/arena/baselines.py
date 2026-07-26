from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.catalog import TaskCatalog
from flowpilot_sandbox_api.arena.grader import grade_task
from flowpilot_sandbox_api.arena.schemas import ManualBaselineCreate, ManualBaselineRead
from flowpilot_sandbox_api.models import HumanBaselineRecord


class DuplicateBaselineRecordError(Exception):
    pass


def create_baseline_record(
    session: Session, catalog: TaskCatalog, payload: ManualBaselineCreate
) -> ManualBaselineRead:
    spec = catalog.get(payload.task_id)
    duration_seconds = int((payload.ended_at - payload.started_at).total_seconds())
    final_score = grade_task(session, spec).total_score
    record = HumanBaselineRecord(
        **payload.model_dump(),
        duration_seconds=duration_seconds,
        final_score=final_score,
    )
    session.add(record)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DuplicateBaselineRecordError(payload.record_id) from exc
    session.refresh(record)
    return _read_model(record)


def list_baseline_records(session: Session) -> list[ManualBaselineRead]:
    records = list(
        session.scalars(select(HumanBaselineRecord).order_by(HumanBaselineRecord.record_id))
    )
    return [_read_model(record) for record in records]


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _read_model(record: HumanBaselineRecord) -> ManualBaselineRead:
    return ManualBaselineRead(
        record_id=record.record_id,
        task_id=record.task_id,
        operator_alias=record.operator_alias,
        started_at=_utc(record.started_at),
        ended_at=_utc(record.ended_at),
        duration_seconds=record.duration_seconds,
        action_count=record.action_count,
        final_score=record.final_score,
        notes=record.notes,
        created_at=_utc(record.created_at),
    )
