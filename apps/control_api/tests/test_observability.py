"""W13 trace schema, replay, redaction, taxonomy, and tenant isolation."""

import json
from datetime import UTC, datetime

import pytest
from conftest import TokenFactory
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from flowpilot_control_api.models import ObservabilityEvent
from flowpilot_control_api.observability import (
    ObservabilityPayloadRejected,
    append_observability_event,
)
from flowpilot_control_api.schemas import (
    FailureCategory,
    ObservabilityPhase,
    ObservabilityStatus,
    TraceReason,
    stable_hash,
)

ALPHA_ORG = "org_syn_alpha_0001"
BETA_ORG = "org_syn_beta_0001"


def _headers(token_factory: TokenFactory, subject: str, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_factory.issue(subject=subject, role=role)}"}


def _run_body() -> dict[str, object]:
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


def test_trace_export_orders_replay_redacts_and_blocks_cross_tenant(
    client: TestClient,
    token_factory: TokenFactory,
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
    submitted = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers={**admin, "Idempotency-Key": "w13-trace-create-0001"},
        json=_run_body(),
    )
    assert submitted.status_code == 202
    run = submitted.json()
    run_id = run["run_id"]

    request = client.get(
        f"/api/v1/organizations/{ALPHA_ORG}/approval-requests/{run['approval_request_id']}",
        headers=manager,
    )
    assert request.status_code == 200
    approved = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/approval-requests/{run['approval_request_id']}/decisions",
        headers={**manager, "If-Match": request.headers["etag"]},
        json={
            "schema_version": "w11-approval-decision-create/1.0",
            "decision": "approved",
            "reason": "policy_satisfied",
        },
    )
    assert approved.status_code == 200
    claimed = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/{run_id}/claim",
        headers={**admin, "If-Match": submitted.headers["etag"]},
        json={
            "schema_version": "w12-production-run-claim/1.0",
            "action_type": _run_body()["action_type"],
            "parameters": _run_body()["parameters"],
        },
    )
    assert claimed.status_code == 202

    trace = client.get(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/{run_id}/trace",
        headers=admin,
    )
    assert trace.status_code == 200
    payload = trace.json()
    assert payload["schema_version"] == "w13-run-trace-export/1.0"
    assert payload["run"]["run_id"] == run_id
    assert [event["event_sequence"] for event in payload["events"]] == [1, 2, 3]
    assert [step["ordinal"] for step in payload["replay_steps"]] == [1, 2, 3]
    assert [event["phase"] for event in payload["events"]] == [
        "admission",
        "approval",
        "outbox",
    ]
    assert payload["events"][0]["parent_span_id"] is None
    assert payload["events"][1]["parent_span_id"] == payload["events"][0]["span_id"]
    assert payload["cost"] == {
        "schema_version": "w13-cost-summary/1.0",
        "model_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "fake_cost_microusd": 0,
        "real_cost_microusd": 0,
    }
    expected_export_hash = stable_hash(
        {key: value for key, value in payload.items() if key != "export_hash"}
    )
    assert payload["export_hash"] == expected_export_hash
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).lower()
    assert not any(
        forbidden in serialized
        for forbidden in (
            "bearer ",
            "access_token",
            "credential",
            "nonce",
            "cookie",
            "password",
            "private_key",
            "10000000-0000",
        )
    )

    cross = client.get(
        f"/api/v1/organizations/{BETA_ORG}/production-runs/{run_id}/trace",
        headers=admin,
    )
    missing = client.get(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs/run_missing_0001/trace",
        headers=admin,
    )
    assert cross.status_code == missing.status_code == 404
    assert cross.json() == missing.json()


def test_trace_append_rejects_forbidden_fields_and_preserves_closed_taxonomy(
    client: TestClient,
    admin_headers: dict[str, str],
    database_engine: object,
) -> None:
    created = client.post(
        f"/api/v1/organizations/{ALPHA_ORG}/production-runs",
        headers={**admin_headers, "Idempotency-Key": "w13-trace-create-0002"},
        json={
            "schema_version": "w12-production-run-create/1.0",
            "task_id": "w7-jml-joiner-001-v1",
            "process": "joiner",
            "category": "standard_joiner",
            "action_type": "generate_plan",
            "parameters": {
                "schema_version": "w11-task-parameters/1.0",
                "task_reference": "w7-jml-joiner-001-v1",
            },
        },
    )
    assert created.status_code == 202
    run_id = created.json()["run_id"]
    required = {
        "authn",
        "authz",
        "approval",
        "schema",
        "rate_limit",
        "backpressure",
        "queue_expiry",
        "lease_fence",
        "workflow_rejected",
        "dependency_unavailable",
        "browser_timeout",
        "browser_error",
        "planning_failure",
        "recovery_failure",
        "receipt_invalid",
        "grader_verification",
        "audit_verification",
    }
    assert required <= {item.value for item in FailureCategory}

    with Session(database_engine) as session:
        with pytest.raises(ObservabilityPayloadRejected):
            append_observability_event(
                session,
                organization_id=ALPHA_ORG,
                run_id=run_id,
                phase=ObservabilityPhase.BROWSER,
                status=ObservabilityStatus.FAILED,
                reason=TraceReason.BROWSER_SUMMARY,
                failure_category=FailureCategory.BROWSER_TIMEOUT,
                attributes={"token": "Bearer unsafe"},
                now=datetime(2026, 8, 3, tzinfo=UTC),
            )
        event = append_observability_event(
            session,
            organization_id=ALPHA_ORG,
            run_id=run_id,
            phase=ObservabilityPhase.BROWSER,
            status=ObservabilityStatus.FAILED,
            reason=TraceReason.BROWSER_SUMMARY,
            failure_category=FailureCategory.BROWSER_TIMEOUT,
            attributes={
                "run_status": "queued",
                "latency_ms": 250,
                "real_cost_microusd": 0,
                "sensitive_fields_present": False,
            },
            now=datetime(2026, 8, 3, tzinfo=UTC),
        )
        session.commit()
        stored = session.get(ObservabilityEvent, event.event_id)
        assert stored is not None
        attributes = json.loads(stored.attributes_json)
        assert stored.attributes_hash == stable_hash(attributes)
        assert stored.failure_category == "browser_timeout"
