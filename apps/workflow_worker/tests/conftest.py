"""Deterministic isolated database fixtures for the W12 Workflow Worker."""

import base64
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, insert, update
from sqlalchemy.engine import Engine

from flowpilot_workflow_worker.config import WorkerSettings
from flowpilot_workflow_worker.repository import (
    AUDIT_HEADS,
    IDENTITIES,
    MEMBERSHIPS,
    METADATA,
    ORGANIZATIONS,
    OUTBOX,
    PARTITIONS,
    RUNS,
    USERS,
    WorkflowRepository,
)
from flowpilot_workflow_worker.schemas import stable_hash

NOW = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)


@pytest.fixture
def settings(tmp_path: Path) -> WorkerSettings:
    database_path = tmp_path / "control.db"
    value = WorkerSettings(
        database_url=f"sqlite+pysqlite:///{database_path}",
        envelope_key=base64.urlsafe_b64encode(b"w" * 32).decode("ascii"),
        worker_instance_id="worker_test_instance_0001",
    )
    value.validate()
    return value


@pytest.fixture
def engine(settings: WorkerSettings) -> Engine:
    value = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    METADATA.create_all(value)
    try:
        yield value
    finally:
        value.dispose()


@pytest.fixture
def repository(engine: Engine, settings: WorkerSettings) -> WorkflowRepository:
    return WorkflowRepository(engine, settings)


@dataclass(frozen=True, slots=True)
class SeededRun:
    organization_id: str
    user_id: str
    run_id: str
    outbox_id: str
    authorization_hash: str
    parameter_hash: str
    payload_hash: str


class Seeder:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def organization(self, suffix: str, *, last_selected_at: datetime | None = None) -> None:
        organization_id = f"org_{suffix}_0001"
        user_id = f"usr_{suffix}_0001"
        with self.engine.begin() as connection:
            connection.execute(
                insert(ORGANIZATIONS).values(
                    organization_id=organization_id,
                    status="active",
                    version=1,
                )
            )
            connection.execute(
                insert(USERS).values(
                    user_id=user_id,
                    organization_id=organization_id,
                    status="active",
                    version=1,
                )
            )
            connection.execute(
                insert(IDENTITIES).values(
                    identity_id=f"idn_{suffix}_0001",
                    organization_id=organization_id,
                    user_id=user_id,
                    status="active",
                    version=1,
                )
            )
            connection.execute(
                insert(MEMBERSHIPS).values(
                    membership_id=f"mem_{suffix}_0001",
                    organization_id=organization_id,
                    user_id=user_id,
                    role="organization_admin",
                    status="active",
                    version=1,
                )
            )
            connection.execute(
                insert(AUDIT_HEADS).values(
                    organization_id=organization_id,
                    head_sequence=0,
                    head_hash="0" * 64,
                    version=1,
                    updated_at=NOW,
                )
            )
            connection.execute(
                insert(PARTITIONS).values(
                    organization_id=organization_id,
                    partition_id=f"part_{suffix}_0001",
                    ready_count=0,
                    status="empty",
                    cursor_version=1,
                    last_selected_at=last_selected_at,
                    updated_at=NOW,
                )
            )

    def run(
        self,
        suffix: str,
        *,
        ordinal: int = 1,
        available_at: datetime = NOW,
        expires_at: datetime = NOW + timedelta(seconds=300),
    ) -> SeededRun:
        organization_id = f"org_{suffix}_0001"
        user_id = f"usr_{suffix}_0001"
        run_id = f"run_{suffix}_{ordinal:04d}"
        outbox_id = f"out_{suffix}_{ordinal:04d}"
        authorization_hash = stable_hash(
            {
                "schema_version": "w10-authorization-fact/1.0",
                "identity_id": f"idn_{suffix}_0001",
                "identity_version": 1,
                "organization_id": organization_id,
                "organization_version": 1,
                "user_id": user_id,
                "user_version": 1,
                "membership_id": f"mem_{suffix}_0001",
                "membership_version": 1,
                "role": "organization_admin",
                "approval_authorities": [],
            }
        )
        parameter_hash = stable_hash(
            {
                "schema_version": "w11-action-binding/1.0",
                "action_type": "create_ticket",
                "parameters": {
                    "schema_version": "w11-create-ticket-parameters/1.0",
                    "employee_id": 41011,
                    "ticket_code": "w7.joiner001v1",
                },
            }
        )
        payload_hash = stable_hash(
            {
                "schema_version": "w12-trusted-task-reference/1.0",
                "task_id": "w7-jml-joiner-001-v1",
                "process": "joiner",
                "category": "standard_joiner",
            }
        )
        with self.engine.begin() as connection:
            connection.execute(
                insert(RUNS).values(
                    run_id=run_id,
                    organization_id=organization_id,
                    requester_user_id=user_id,
                    executor_user_id=user_id,
                    task_id="w7-jml-joiner-001-v1",
                    process="joiner",
                    category="standard_joiner",
                    approval_request_id=None,
                    grant_id=None,
                    execution_id=None,
                    action_type="create_ticket",
                    parameter_hash=parameter_hash,
                    authorization_hash=authorization_hash,
                    approval_set_hash=None,
                    payload_reference=f"taskref_{suffix}_{ordinal:04d}",
                    payload_hash=payload_hash,
                    status="queued",
                    version=1,
                    workflow_id=f"workflow_{suffix}_{ordinal:04d}",
                    workflow_hash=stable_hash(f"workflow_{suffix}_{ordinal:04d}"),
                    lease_owner_hash=None,
                    fencing_token=0,
                    lease_expires_at=None,
                    started_at=None,
                    finished_at=None,
                    terminal_reason=None,
                    receipt_reference=None,
                    audit_sequence=1,
                    updated_at=NOW,
                )
            )
            connection.execute(
                insert(OUTBOX).values(
                    outbox_id=outbox_id,
                    organization_id=organization_id,
                    run_id=run_id,
                    status="ready",
                    attempt_count=0,
                    fencing_token=0,
                    lease_owner_hash=None,
                    lease_version=0,
                    leased_at=None,
                    lease_expires_at=None,
                    heartbeat_at=None,
                    available_at=available_at,
                    expires_at=expires_at,
                    updated_at=NOW,
                )
            )
            connection.execute(
                update(PARTITIONS)
                .where(PARTITIONS.c.organization_id == organization_id)
                .values(
                    ready_count=PARTITIONS.c.ready_count + 1,
                    status="ready",
                    cursor_version=PARTITIONS.c.cursor_version + 1,
                )
            )
        return SeededRun(
            organization_id=organization_id,
            user_id=user_id,
            run_id=run_id,
            outbox_id=outbox_id,
            authorization_hash=authorization_hash,
            parameter_hash=parameter_hash,
            payload_hash=payload_hash,
        )


@pytest.fixture
def seeder(engine: Engine) -> Seeder:
    return Seeder(engine)
