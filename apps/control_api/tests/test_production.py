"""W12 durable admission, limiter, approval handoff, and ETag tests."""

import hashlib
import threading
from datetime import UTC, datetime

import pytest
from conftest import TokenFactory
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from flowpilot_control_api.auth import OidcVerifier, VerifiedIdentity
from flowpilot_control_api.config import OidcPolicy, ProductionPolicy
from flowpilot_control_api.models import (
    ApprovalGrant,
    ApprovalRequest,
    AuditEvent,
    DispatchOutbox,
    ProductionRun,
    SchedulerPartition,
)
from flowpilot_control_api.production import (
    RateLimitExceeded,
    _consume_rate_limit_or_audit,
    consume_rate_limit,
)
from flowpilot_control_api.repository import resolve_actor
from flowpilot_control_api.schemas import ProductionRouteClass, Role

ALPHA_ORG = "org_syn_alpha_0001"
BETA_ORG = "org_syn_beta_0001"


def test_identity_database_resolution_runs_off_event_loop(
    client: TestClient,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from flowpilot_control_api import main as main_module

    thread_ids: dict[str, int] = {}
    verifier_type = type(client.app.state.oidc_verifier)
    original_verify = verifier_type.verify
    original_resolve_actor = main_module.resolve_actor

    async def recorded_verify(self: OidcVerifier, token: str) -> VerifiedIdentity:
        thread_ids["event_loop"] = threading.get_ident()
        return await original_verify(self, token)

    def recorded_resolve_actor(session: Session, verified: VerifiedIdentity) -> object:
        thread_ids["database"] = threading.get_ident()
        return original_resolve_actor(session, verified)

    monkeypatch.setattr(verifier_type, "verify", recorded_verify)
    monkeypatch.setattr(main_module, "resolve_actor", recorded_resolve_actor)

    response = client.get("/api/v1/identity/me", headers=admin_headers)

    assert response.status_code == 200
    assert thread_ids["database"] != thread_ids["event_loop"]


def _headers(token_factory: TokenFactory, subject: str, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_factory.issue(subject=subject, role=role)}"}


def _run_body(
    *,
    action_type: str = "generate_plan",
    parameters: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "w12-production-run-create/1.0",
        "task_id": "w7-jml-joiner-001-v1",
        "process": "joiner",
        "category": "standard_joiner",
        "action_type": action_type,
        "parameters": parameters
        or {
            "schema_version": "w11-task-parameters/1.0",
            "task_reference": "w7-jml-joiner-001-v1",
        },
    }


def _verified(policy: OidcPolicy) -> VerifiedIdentity:
    return VerifiedIdentity(
        issuer_id=policy.issuer_id,
        issuer_hash=hashlib.sha256(policy.issuer.encode()).hexdigest(),
        subject_hash=hashlib.sha256(b"10000000-0000-0000-0000-000000000001").hexdigest(),
        claimed_role=Role.ORGANIZATION_ADMIN,
    )


def test_submit_replay_mismatch_cross_tenant_and_cancel(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    headers = {**admin_headers, "Idempotency-Key": "w12-aaaaaaaaaaaa-0001"}
    created = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers=headers,
        json=_run_body(),
    )
    assert created.status_code == 202
    assert created.json()["status"] == "queued"
    assert created.json()["version"] == 1
    run_id = created.json()["run_id"]
    etag = created.headers["etag"]

    replay = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers=headers,
        json=_run_body(),
    )
    assert replay.status_code == 202
    assert replay.json()["run_id"] == run_id
    assert replay.headers["etag"] == etag

    mismatch = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers=headers,
        json=_run_body(action_type="create_draft"),
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["code"] == "conflict"

    cross_tenant = client.get(
        f"/api/v1/organizations/{BETA_ORG}/production-runs/{run_id}",
        headers=admin_headers,
    )
    missing = client.get(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/run_missing_0001",
        headers=admin_headers,
    )
    assert cross_tenant.status_code == missing.status_code == 404
    assert cross_tenant.json() == missing.json()

    no_precondition = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/{run_id}/cancel",
        headers=admin_headers,
    )
    assert no_precondition.status_code == 428
    cancelled = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/{run_id}/cancel",
        headers={**admin_headers, "If-Match": etag},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["version"] == 2
    stale = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/{run_id}/cancel",
        headers={**admin_headers, "If-Match": etag},
    )
    assert stale.status_code == 412


def test_same_tenant_missing_reads_persist_rate_charge(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    path = f"/api/v1/organizations/{ALPHA_ORG}/production-runs/run_missing_0001"

    limited = None
    for _ in range(80):
        missing = client.get(path, headers=admin_headers)
        if missing.status_code == 429:
            limited = missing
            break
        assert missing.status_code == 404

    assert limited is not None
    assert limited.json()["code"] == "rate_limited"
    assert 1 <= int(limited.headers["retry-after"]) <= 30


def test_l2_approval_old_claim_is_closed_and_production_claim_enqueues(
    client: TestClient,
    token_factory: TokenFactory,
    database_engine: Engine,
) -> None:
    admin = _headers(
        token_factory,
        "10000000-0000-0000-0000-000000000001",
        "organization_admin",
    )
    manager = _headers(
        token_factory,
        "10000000-0000-0000-0000-000000000004",
        "operator",
    )
    parameters = {
        "schema_version": "w11-create-ticket-parameters/1.0",
        "employee_id": 1,
        "ticket_code": "synthetic.ticket.001",
    }
    submitted = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers={**admin, "Idempotency-Key": "w12-approval-run-0001"},
        json=_run_body(action_type="create_ticket", parameters=parameters),
    )
    assert submitted.status_code == 202
    body = submitted.json()
    assert body["status"] == "waiting_approval"
    run_id = body["run_id"]
    request_id = body["approval_request_id"]
    run_etag = submitted.headers["etag"]
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(DispatchOutbox)) == 0

    request = client.get(
        f"/api/v1/organizations/{ALPHA_ORG}/approval-requests/{request_id}",
        headers=manager,
    )
    assert request.status_code == 200
    approved = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/approval-requests/{request_id}/decisions",
        headers={**manager, "If-Match": request.headers["etag"]},
        json={
            "schema_version": "w11-approval-decision-create/1.0",
            "decision": "approved",
            "reason": "policy_satisfied",
        },
    )
    assert approved.status_code == 200
    assert approved.json()["grant_issued"] is True

    old_claim = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/approval-requests/{request_id}/claim",
        headers=admin,
        json={
            "schema_version": "w11-grant-claim-request/1.0",
            "task_id": "w7-jml-joiner-001-v1",
            "step_id": "production_run",
            "action_type": "create_ticket",
            "parameters": parameters,
        },
    )
    assert old_claim.status_code == 409

    claimed = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/{run_id}/claim",
        headers={**admin, "If-Match": run_etag},
        json={
            "schema_version": "w12-production-run-claim/1.0",
            "action_type": "create_ticket",
            "parameters": parameters,
        },
    )
    assert claimed.status_code == 202
    assert claimed.json()["status"] == "queued"
    assert claimed.json()["version"] == 2
    assert claimed.json()["execution_id"].startswith("exe_")
    assert client.app.state.grant_vault.size == 0
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(DispatchOutbox)) == 1

    cancelled = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/{run_id}/cancel",
        headers={**admin, "If-Match": claimed.headers["etag"]},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    with Session(database_engine) as session:
        request_record = session.scalar(
            select(ApprovalRequest).where(ApprovalRequest.request_id == request_id)
        )
        grant_record = session.scalar(
            select(ApprovalGrant).where(ApprovalGrant.request_id == request_id)
        )
        assert request_record is not None and request_record.status == "cancelled"
        assert grant_record is not None and grant_record.status == "failed"


def test_atomic_token_bucket_refill_and_retry_after(
    database_engine: Engine,
    policy: OidcPolicy,
) -> None:
    frozen_now = datetime(2026, 8, 1, tzinfo=UTC)
    with Session(database_engine) as session:
        actor = resolve_actor(session, _verified(policy))
        for _ in range(10):
            consume_rate_limit(
                session,
                actor,
                ProductionRouteClass.SUBMIT,
                ProductionPolicy(),
                now=frozen_now,
            )
            session.commit()
        with pytest.raises(RateLimitExceeded) as rejected:
            consume_rate_limit(
                session,
                actor,
                ProductionRouteClass.SUBMIT,
                ProductionPolicy(),
                now=frozen_now,
            )
        assert rejected.value.retry_after == 1
        session.rollback()
        consume_rate_limit(
            session,
            actor,
            ProductionRouteClass.SUBMIT,
            ProductionPolicy(),
            now=frozen_now.replace(second=1),
        )


def test_rate_rejection_persists_bucket_refill_and_safe_audit(
    database_engine: Engine,
    policy: OidcPolicy,
) -> None:
    frozen_now = datetime(2026, 8, 1, tzinfo=UTC)
    with Session(database_engine) as session:
        actor = resolve_actor(session, _verified(policy))
        for _ in range(20):
            _consume_rate_limit_or_audit(
                session,
                actor,
                ProductionRouteClass.READ,
                ProductionPolicy(),
                subject_reference=ALPHA_ORG,
                now=frozen_now,
            )
            session.commit()
        with pytest.raises(RateLimitExceeded):
            _consume_rate_limit_or_audit(
                session,
                actor,
                ProductionRouteClass.READ,
                ProductionPolicy(),
                subject_reference=ALPHA_ORG,
                now=frozen_now,
            )
        assert (
            session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(
                    AuditEvent.organization_id == ALPHA_ORG,
                    AuditEvent.event_type == "rate_limited",
                )
            )
            == 1
        )


def test_backpressure_is_503_without_a_second_run(
    client: TestClient,
    admin_headers: dict[str, str],
    database_engine: Engine,
) -> None:
    first = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers={**admin_headers, "Idempotency-Key": "w12-bbbbbbbbbbbb-0001"},
        json=_run_body(),
    )
    assert first.status_code == 202
    with Session(database_engine) as session:
        partition = session.get(SchedulerPartition, ALPHA_ORG)
        assert partition is not None
        partition.ready_count = 32
        partition.status = "ready"
        session.commit()
        before = session.scalar(select(func.count()).select_from(ProductionRun))

    rejected = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers={**admin_headers, "Idempotency-Key": "w12-cccccccccccc-0001"},
        json=_run_body(),
    )
    assert rejected.status_code == 503
    assert rejected.headers["retry-after"] == "1"
    assert rejected.json()["code"] == "backpressure"
    with Session(database_engine) as session:
        after = session.scalar(select(func.count()).select_from(ProductionRun))
        assert after == before


def test_waiting_approval_does_not_consume_or_lock_queue_capacity(
    client: TestClient,
    admin_headers: dict[str, str],
    database_engine: Engine,
) -> None:
    with Session(database_engine) as session:
        now = datetime.now(UTC)
        session.add_all(
            (
                SchedulerPartition(
                    organization_id=ALPHA_ORG,
                    partition_id="prt_alpha_capacity_test",
                    ready_count=32,
                    status="ready",
                    cursor_version=1,
                    last_selected_at=None,
                    updated_at=now,
                ),
                SchedulerPartition(
                    organization_id=BETA_ORG,
                    partition_id="prt_beta_capacity_test",
                    ready_count=32,
                    status="ready",
                    cursor_version=1,
                    last_selected_at=None,
                    updated_at=now,
                ),
            )
        )
        session.commit()

    response = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers={**admin_headers, "Idempotency-Key": "w12-dddddddddddd-0001"},
        json=_run_body(
            action_type="create_ticket",
            parameters={
                "schema_version": "w11-create-ticket-parameters/1.0",
                "employee_id": 1,
                "ticket_code": "synthetic.ticket.001",
            },
        ),
    )

    assert response.status_code == 202
    assert response.json()["status"] == "waiting_approval"
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(DispatchOutbox)) == 0
        for organization_id in (ALPHA_ORG, BETA_ORG):
            partition = session.get(SchedulerPartition, organization_id)
            assert partition is not None
            assert partition.ready_count == 32
