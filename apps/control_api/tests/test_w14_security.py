"""W14 adversarial authority and W13 compatibility tests."""

import json

from conftest import TokenFactory
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from flowpilot_control_api.models import DispatchOutbox, ProductionRun
from flowpilot_control_api.schemas import stable_hash

ALPHA_ORG = "org_syn_alpha_0001"
BETA_ORG = "org_syn_beta_0001"


def _headers(token_factory: TokenFactory, subject: str, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_factory.issue(subject=subject, role=role)}"}


def _l2_body() -> dict[str, object]:
    return {
        "schema_version": "w12-production-run-create/1.0",
        "task_id": "w7-jml-joiner-001-v1",
        "process": "joiner",
        "category": "standard_joiner",
        "action_type": "create_ticket",
        "parameters": {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 1,
            "ticket_code": "synthetic.ticket.001",
        },
    }


def test_untrusted_body_headers_rbac_tenant_and_approval_cannot_select_authority(
    client: TestClient,
    token_factory: TokenFactory,
    database_engine: Engine,
) -> None:
    alpha_admin = _headers(
        token_factory, "10000000-0000-0000-0000-000000000001", "organization_admin"
    )
    alpha_auditor = _headers(
        token_factory,
        "10000000-0000-0000-0000-000000000003",
        "auditor",
    )
    canary = "-".join(("w14", "canary", "header", "01"))
    hostile_headers = {
        **alpha_admin,
        "X-Organization-Id": BETA_ORG,
        "X-Role": "global_administrator",
        "X-Approval": "bypass",
        "X-Forwarded-Authorization": "Bearer " + canary,
        "Idempotency-Key": "w14-security-authority-0001",
    }
    invalid_body = {
        **_l2_body(),
        "organization_id": BETA_ORG,
        "role": "global_administrator",
        "approval": "bypass",
        "success": True,
    }
    rejected_body = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers=hostile_headers,
        json=invalid_body,
    )
    assert rejected_body.status_code == 422
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(ProductionRun)) == 0
        assert session.scalar(select(func.count()).select_from(DispatchOutbox)) == 0

    denied_rbac = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers={**alpha_auditor, "Idempotency-Key": "w14-security-rbac-0001"},
        json=_l2_body(),
    )
    assert denied_rbac.status_code == 403

    submitted = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers=hostile_headers,
        json=_l2_body(),
    )
    assert submitted.status_code == 202
    run = submitted.json()
    assert run["status"] == "waiting_approval"
    run_id = run["run_id"]
    bypass = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/{run_id}/claim",
        headers={
            **hostile_headers,
            "If-Match": submitted.headers["etag"],
            "X-Approval-Nonce": canary,
        },
        json={
            "schema_version": "w12-production-run-claim/1.0",
            "action_type": _l2_body()["action_type"],
            "parameters": _l2_body()["parameters"],
        },
    )
    assert bypass.status_code == 409
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(DispatchOutbox)) == 0

    cross = client.get(
        f"/api/v1/organizations/{BETA_ORG}/production-runs/{run_id}", headers=alpha_admin
    )
    missing = client.get(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/run_missing_0001",
        headers=alpha_admin,
    )
    assert cross.status_code == missing.status_code == 404
    assert cross.json() == missing.json()

    trace_response = client.get(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/{run_id}/trace",
        headers=alpha_admin,
    )
    assert trace_response.status_code == 200
    trace = trace_response.json()
    assert trace["schema_version"] == "w13-run-trace-export/1.0"
    assert trace["export_hash"] == stable_hash(
        {key: value for key, value in trace.items() if key != "export_hash"}
    )
    serialized = json.dumps(trace, sort_keys=True, separators=(",", ":")).casefold()
    assert canary not in serialized
    forbidden_fields = ("bearer ", "cookie", "password", "approval_nonce")
    assert not any(forbidden in serialized for forbidden in forbidden_fields)
