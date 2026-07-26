import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.schemas import (
    FactCounts,
    ResetSeedResult,
    SeedSummary,
    TaskSpec,
)
from flowpilot_sandbox_api.models import (
    AssetAssignment,
    Employee,
    IamAccount,
    Mailbox,
    OnboardingTicket,
)

TASK_MODELS = (Mailbox, AssetAssignment, IamAccount, OnboardingTicket, Employee)


def _stable_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def task_fact_snapshot(session: Session, task_id: str) -> dict[str, list[dict[str, Any]]]:
    employees = list(
        session.scalars(
            select(Employee).where(Employee.arena_task_id == task_id).order_by(Employee.id)
        )
    )
    tickets = list(
        session.scalars(
            select(OnboardingTicket)
            .where(OnboardingTicket.arena_task_id == task_id)
            .order_by(OnboardingTicket.id)
        )
    )
    accounts = list(
        session.scalars(
            select(IamAccount).where(IamAccount.arena_task_id == task_id).order_by(IamAccount.id)
        )
    )
    assets = list(
        session.scalars(
            select(AssetAssignment)
            .where(AssetAssignment.arena_task_id == task_id)
            .order_by(AssetAssignment.id)
        )
    )
    mailboxes = list(
        session.scalars(
            select(Mailbox).where(Mailbox.arena_task_id == task_id).order_by(Mailbox.id)
        )
    )
    return {
        "employees": [
            {
                "id": item.id,
                "first_name": item.first_name,
                "last_name": item.last_name,
                "work_email": item.work_email,
                "department": item.department,
                "job_title": item.job_title,
                "location": item.location,
                "start_date": item.start_date.isoformat(),
                "status": item.status,
                "arena_task_id": item.arena_task_id,
                "created_at": _stable_datetime(item.created_at),
            }
            for item in employees
        ],
        "tickets": [
            {
                "id": item.id,
                "employee_id": item.employee_id,
                "title": item.title,
                "status": item.status,
                "arena_task_id": item.arena_task_id,
            }
            for item in tickets
        ],
        "iam_accounts": [
            {
                "id": item.id,
                "employee_id": item.employee_id,
                "username": item.username,
                "role": item.role,
                "status": item.status,
                "arena_task_id": item.arena_task_id,
            }
            for item in accounts
        ],
        "assets": [
            {
                "id": item.id,
                "employee_id": item.employee_id,
                "asset_tag": item.asset_tag,
                "device_type": item.device_type,
                "model": item.model,
                "status": item.status,
                "arena_task_id": item.arena_task_id,
            }
            for item in assets
        ],
        "mailboxes": [
            {
                "id": item.id,
                "employee_id": item.employee_id,
                "address": item.address,
                "status": item.status,
                "arena_task_id": item.arena_task_id,
            }
            for item in mailboxes
        ],
    }


def _snapshot_checksum(snapshot: dict[str, list[dict[str, Any]]]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def reset_seed(session: Session, spec: TaskSpec) -> ResetSeedResult:
    with session.begin():
        for model in TASK_MODELS:
            session.execute(delete(model).where(model.arena_task_id == spec.task_id))
        for seed in spec.initial_state.employees:
            values = seed.model_dump(exclude={"kind"})
            session.add(Employee(**values, arena_task_id=spec.task_id))

    snapshot = task_fact_snapshot(session, spec.task_id)
    counts = FactCounts(
        employees=len(snapshot["employees"]),
        tickets=len(snapshot["tickets"]),
        iam_accounts=len(snapshot["iam_accounts"]),
        assets=len(snapshot["assets"]),
        mailboxes=len(snapshot["mailboxes"]),
    )
    return ResetSeedResult(
        task_id=spec.task_id,
        fixture_version=spec.fixture.fixture_version,
        spec_checksum=spec.canonical_checksum,
        seed_summary=SeedSummary(
            employee_ids=tuple(item["id"] for item in snapshot["employees"]),
            employee_emails=tuple(item["work_email"] for item in snapshot["employees"]),
            counts=counts,
            fact_checksum=_snapshot_checksum(snapshot),
        ),
    )
