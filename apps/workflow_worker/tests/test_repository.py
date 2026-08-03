"""Organization fairness, fencing, terminal mapping, and four-slot tests."""

import asyncio
from datetime import datetime, timedelta

import pytest
from conftest import NOW, Seeder
from sqlalchemy import func, insert, select, update
from sqlalchemy.engine import Engine

import flowpilot_workflow_worker.main as worker_main
from flowpilot_workflow_worker.config import WorkerSettings
from flowpilot_workflow_worker.main import Dispatcher
from flowpilot_workflow_worker.repository import (
    AUDIT_EVENTS,
    AUTHORITIES,
    DECISIONS,
    GRANTS,
    LEASES,
    MEMBERSHIPS,
    OUTBOX,
    PARTITIONS,
    REQUESTS,
    RUNS,
    USERS,
    WorkflowRepository,
)
from flowpilot_workflow_worker.schemas import (
    TemporalOutcome,
    WorkflowResult,
    WorkItem,
    stable_hash,
)


def _outcome(item: WorkItem) -> TemporalOutcome:
    return TemporalOutcome(
        result=WorkflowResult(
            workflow_id=item.workflow_id,
            run_id=item.run_id,
            task_id=item.task_id,
            status="finished_ungraded",
            terminal_reason="workflow_finished_ungraded",
            plan_hash=None,
            revision=1,
            session_epoch=1,
            completed_step_ids=(),
            checkpoint_count=0,
            latest_checkpoint_hash=None,
            usage={},
        ),
        deduplicated_start=False,
    )


def test_organization_fair_claim_order(
    repository: WorkflowRepository,
    seeder: Seeder,
) -> None:
    seeder.organization("alpha", last_selected_at=NOW - timedelta(seconds=20))
    seeder.organization("beta", last_selected_at=NOW - timedelta(seconds=10))
    seeder.run("alpha")
    seeder.run("beta")

    first = repository.claim_next(now=NOW)
    second = repository.claim_next(now=NOW + timedelta(microseconds=1))
    assert first is not None and first.organization_id == "org_alpha_0001"
    assert second is not None and second.organization_id == "org_beta_0001"


def test_lease_expiry_reclaim_stale_fence_and_finished_ungraded(
    repository: WorkflowRepository,
    seeder: Seeder,
    engine: Engine,
) -> None:
    seeder.organization("fence")
    seeded = seeder.run("fence")
    first = repository.claim_next(now=NOW)
    assert first is not None
    assert first.fencing_token == 1
    assert repository.claim_next(now=NOW + timedelta(seconds=1)) is None
    with engine.connect() as connection:
        partition = (
            connection.execute(
                select(PARTITIONS).where(
                    PARTITIONS.c.organization_id == seeded.organization_id,
                )
            )
            .mappings()
            .one()
        )
        assert partition["status"] == "ready"

    reclaimed = repository.claim_next(now=NOW + timedelta(seconds=31))
    assert reclaimed is not None
    assert reclaimed.run_id == first.run_id
    assert reclaimed.workflow_id == first.workflow_id
    assert reclaimed.fencing_token == 2
    assert reclaimed.attempt_count == 2

    assert repository.heartbeat(first, now=NOW + timedelta(seconds=32)) is False
    assert repository.heartbeat(reclaimed, now=NOW + timedelta(seconds=32)) is True
    assert repository.mark_started(first, now=NOW + timedelta(seconds=33)) is False
    assert repository.mark_started(reclaimed, now=NOW + timedelta(seconds=33)) is True
    assert repository.complete(
        reclaimed,
        _outcome(reclaimed),
        now=NOW + timedelta(seconds=34),
    )

    with engine.connect() as connection:
        run = (
            connection.execute(
                select(RUNS).where(
                    RUNS.c.organization_id == seeded.organization_id,
                    RUNS.c.run_id == seeded.run_id,
                )
            )
            .mappings()
            .one()
        )
        outbox = (
            connection.execute(
                select(OUTBOX).where(
                    OUTBOX.c.organization_id == seeded.organization_id,
                    OUTBOX.c.outbox_id == seeded.outbox_id,
                )
            )
            .mappings()
            .one()
        )
        lease_statuses = list(
            connection.scalars(
                select(LEASES.c.status)
                .where(LEASES.c.organization_id == seeded.organization_id)
                .order_by(LEASES.c.closed_at)
            )
        )
        event_types = list(
            connection.scalars(
                select(AUDIT_EVENTS.c.event_type)
                .where(AUDIT_EVENTS.c.organization_id == seeded.organization_id)
                .order_by(AUDIT_EVENTS.c.sequence)
            )
        )
        assert run["status"] == "finished_ungraded"
        assert run["terminal_reason"] == "agent_finished"
        assert run["receipt_reference"] is not None
        assert outbox["status"] == "closed"
        assert lease_statuses == ["expired", "completed"]
        assert event_types.count("stale_fence_rejected") == 2
        assert "run_recovered" in event_types
        assert event_types[-3:] == [
            "run_verifying",
            "run_finished_ungraded",
            "execution_succeeded",
        ]
        assert (
            connection.scalar(
                select(PARTITIONS.c.ready_count).where(
                    PARTITIONS.c.organization_id == seeded.organization_id
                )
            )
            == 0
        )

    terminal_version = int(run["version"])
    assert (
        repository.complete(
            reclaimed,
            _outcome(reclaimed),
            now=NOW + timedelta(seconds=35),
        )
        is False
    )
    with engine.connect() as connection:
        assert (
            connection.scalar(
                select(RUNS.c.version).where(
                    RUNS.c.organization_id == seeded.organization_id,
                    RUNS.c.run_id == seeded.run_id,
                )
            )
            == terminal_version
        )


def test_effect_boundary_rechecks_current_authorization(
    repository: WorkflowRepository,
    seeder: Seeder,
    engine: Engine,
) -> None:
    seeder.organization("disabled")
    seeded = seeder.run("disabled")
    item = repository.claim_next(now=NOW)
    assert item is not None
    with engine.begin() as connection:
        connection.execute(
            update(USERS)
            .where(
                USERS.c.organization_id == seeded.organization_id,
                USERS.c.user_id == seeded.user_id,
            )
            .values(status="disabled", version=USERS.c.version + 1)
        )
    assert repository.binding_valid(item, now=NOW + timedelta(seconds=1)) is False
    assert repository.mark_started(item, now=NOW + timedelta(seconds=1)) is False
    with engine.connect() as connection:
        run = (
            connection.execute(
                select(RUNS).where(
                    RUNS.c.organization_id == seeded.organization_id,
                    RUNS.c.run_id == seeded.run_id,
                )
            )
            .mappings()
            .one()
        )
        assert run["status"] == "failed"
        assert run["terminal_reason"] == "authorization_invalid"


def test_claimed_grant_expiry_does_not_cancel_durable_queued_run(
    repository: WorkflowRepository,
    seeder: Seeder,
    engine: Engine,
) -> None:
    seeder.organization("claimed")
    seeded = seeder.run("claimed")
    request_id = "apr_claimed_0001"
    grant_id = "grt_claimed_0001"
    execution_id = "exe_claimed_0001"
    approver_user_id = "usr_claimed_manager_0001"
    authority_id = "auth_claimed_manager_0001"
    decision_id = "dec_claimed_manager_0001"
    approval_set_hash = stable_hash(
        {
            "schema_version": "w11-required-approval-set/1.0",
            "approvals": [
                {
                    "decision_id": decision_id,
                    "approver_user_id": approver_user_id,
                    "authority_id": authority_id,
                    "approval_role": "manager",
                    "authority_version": 1,
                }
            ],
        }
    )
    with engine.begin() as connection:
        connection.execute(
            insert(USERS).values(
                user_id=approver_user_id,
                organization_id=seeded.organization_id,
                status="active",
                version=1,
            )
        )
        connection.execute(
            insert(MEMBERSHIPS).values(
                membership_id="mem_claimed_manager_0001",
                organization_id=seeded.organization_id,
                user_id=approver_user_id,
                role="organization_operator",
                status="active",
                version=1,
            )
        )
        connection.execute(
            insert(AUTHORITIES).values(
                authority_id=authority_id,
                organization_id=seeded.organization_id,
                user_id=approver_user_id,
                role="manager",
                status="active",
                version=1,
            )
        )
        connection.execute(
            insert(REQUESTS).values(
                request_id=request_id,
                organization_id=seeded.organization_id,
                task_id="w7-jml-joiner-001-v1",
                step_id="production_run",
                action_type="create_ticket",
                parameter_hash=seeded.parameter_hash,
                risk_level="L2",
                executor_user_id=seeded.user_id,
                required_roles="manager",
                status="claimed",
                version=2,
                expires_at=NOW + timedelta(minutes=10),
                updated_at=NOW,
            )
        )
        connection.execute(
            insert(DECISIONS).values(
                decision_id=decision_id,
                organization_id=seeded.organization_id,
                request_id=request_id,
                decision="approved",
                approver_user_id=approver_user_id,
                authority_id=authority_id,
                approval_role="manager",
            )
        )
        connection.execute(
            insert(GRANTS).values(
                grant_id=grant_id,
                organization_id=seeded.organization_id,
                request_id=request_id,
                task_id="w7-jml-joiner-001-v1",
                step_id="production_run",
                action_type="create_ticket",
                parameter_hash=seeded.parameter_hash,
                approval_set_hash=approval_set_hash,
                executor_user_id=seeded.user_id,
                status="claimed",
                version=2,
                expires_at=NOW + timedelta(minutes=2),
                execution_id=execution_id,
                authorization_hash=seeded.authorization_hash,
                receipt_reference=None,
                consumed_at=None,
                updated_at=NOW,
            )
        )
        connection.execute(
            update(RUNS)
            .where(
                RUNS.c.organization_id == seeded.organization_id,
                RUNS.c.run_id == seeded.run_id,
            )
            .values(
                approval_request_id=request_id,
                grant_id=grant_id,
                execution_id=execution_id,
                approval_set_hash=approval_set_hash,
            )
        )

    after_grant_ttl = NOW + timedelta(seconds=121)
    item = repository.claim_next(now=after_grant_ttl)
    assert item is not None
    assert repository.binding_valid(item, now=after_grant_ttl) is True
    assert repository.mark_started(item, now=after_grant_ttl + timedelta(seconds=1)) is True
    assert repository.complete(
        item,
        _outcome(item),
        now=after_grant_ttl + timedelta(seconds=2),
    )

    with engine.connect() as connection:
        run = (
            connection.execute(
                select(RUNS).where(
                    RUNS.c.organization_id == seeded.organization_id,
                    RUNS.c.run_id == seeded.run_id,
                )
            )
            .mappings()
            .one()
        )
        assert run["status"] == "finished_ungraded"
        assert run["terminal_reason"] == "agent_finished"


def test_queue_expiry_is_terminal_and_updates_audit_reference(
    repository: WorkflowRepository,
    seeder: Seeder,
    engine: Engine,
) -> None:
    seeder.organization("expired")
    seeded = seeder.run("expired", expires_at=NOW - timedelta(microseconds=1))
    assert repository.claim_next(now=NOW) is None
    with engine.connect() as connection:
        run = (
            connection.execute(
                select(RUNS).where(
                    RUNS.c.organization_id == seeded.organization_id,
                    RUNS.c.run_id == seeded.run_id,
                )
            )
            .mappings()
            .one()
        )
        assert run["status"] == "expired"
        assert run["terminal_reason"] == "queue_expired"
        assert run["audit_sequence"] == connection.scalar(
            select(func.max(AUDIT_EVENTS.c.sequence)).where(
                AUDIT_EVENTS.c.organization_id == seeded.organization_id
            )
        )


class GateTemporal:
    def __init__(self, expected: int) -> None:
        self.expected = expected
        self.started = 0
        self.all_started = asyncio.Event()
        self.release = asyncio.Event()

    async def start_and_wait(self, item: WorkItem) -> TemporalOutcome:
        self.started += 1
        if self.started == self.expected:
            self.all_started.set()
        await self.release.wait()
        return _outcome(item)


class FrozenDispatcherDatetime(datetime):
    @classmethod
    def now(cls, tz: object = None) -> datetime:
        value = NOW + timedelta(seconds=1)
        return value if tz is not None else value.replace(tzinfo=None)


async def test_dispatcher_holds_exactly_four_slots_and_queues_fifth(
    repository: WorkflowRepository,
    seeder: Seeder,
    settings: WorkerSettings,
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(worker_main, "datetime", FrozenDispatcherDatetime)
    seeder.organization("slots")
    for ordinal in range(1, 6):
        seeder.run("slots", ordinal=ordinal)
    items = [repository.claim_next(now=NOW + timedelta(microseconds=i)) for i in range(5)]
    assert all(item is not None for item in items)
    temporal = GateTemporal(expected=4)
    dispatcher = Dispatcher(repository, temporal, settings)  # type: ignore[arg-type]
    tasks = [asyncio.create_task(dispatcher.process(item)) for item in items if item is not None]
    await asyncio.wait_for(temporal.all_started.wait(), timeout=5)
    await asyncio.sleep(0)
    assert temporal.started == 4
    assert dispatcher.max_active == 4
    temporal.release.set()
    await asyncio.gather(*tasks)
    assert temporal.started == 5
    assert dispatcher.max_active == 4
    with engine.connect() as connection:
        assert (
            connection.scalar(
                select(func.count()).select_from(RUNS).where(RUNS.c.status == "finished_ungraded")
            )
            == 5
        )


async def test_dispatcher_cancellation_releases_lease_for_drain(
    repository: WorkflowRepository,
    seeder: Seeder,
    settings: WorkerSettings,
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(worker_main, "datetime", FrozenDispatcherDatetime)
    seeder.organization("drain")
    seeded = seeder.run("drain")
    item = repository.claim_next(now=NOW)
    assert item is not None
    temporal = GateTemporal(expected=1)
    dispatcher = Dispatcher(repository, temporal, settings)  # type: ignore[arg-type]
    task = asyncio.create_task(dispatcher.process(item))
    await asyncio.wait_for(temporal.all_started.wait(), timeout=5)
    task.cancel()
    result = await asyncio.gather(task, return_exceptions=True)
    assert isinstance(result[0], asyncio.CancelledError)
    with engine.connect() as connection:
        run = (
            connection.execute(
                select(RUNS).where(
                    RUNS.c.organization_id == seeded.organization_id,
                    RUNS.c.run_id == seeded.run_id,
                )
            )
            .mappings()
            .one()
        )
        outbox = (
            connection.execute(
                select(OUTBOX).where(
                    OUTBOX.c.organization_id == seeded.organization_id,
                    OUTBOX.c.outbox_id == seeded.outbox_id,
                )
            )
            .mappings()
            .one()
        )
        assert run["status"] == "queued"
        assert outbox["status"] == "ready"
        assert (
            connection.scalar(
                select(func.count())
                .select_from(LEASES)
                .where(
                    LEASES.c.organization_id == seeded.organization_id,
                    LEASES.c.status == "released",
                )
            )
            == 1
        )
