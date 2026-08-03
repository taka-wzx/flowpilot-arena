"""Deterministic W13 single-run observability and replay Compose smoke."""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

CONTROL_API = os.environ.get("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
SANDBOX_API = os.environ.get("SANDBOX_API_URL", "http://sandbox-api:8001").rstrip("/")
TOKEN_URL = os.environ.get(
    "KEYCLOAK_TOKEN_URL",
    "http://keycloak:8080/realms/flowpilot/protocol/openid-connect/token",
)
PASSWORD = os.environ.get("W13_SYNTHETIC_PASSWORD", "")
RESULTS = Path("/results")
REPORT_PATH = RESULTS / "w13-observability-report.json"
ALPHA = "org_syn_alpha_0001"
TASK_ID = "w7-jml-joiner-001-v1"


def _validate_origins() -> None:
    control = urlsplit(CONTROL_API)
    sandbox = urlsplit(SANDBOX_API)
    token = urlsplit(TOKEN_URL)
    assert control.scheme == "http" and control.hostname == "control-api"
    assert sandbox.scheme == "http" and sandbox.hostname == "sandbox-api"
    assert token.scheme == "http" and token.hostname == "keycloak"
    assert control.path in {"", "/"} and sandbox.path in {"", "/"}
    assert token.path == "/realms/flowpilot/protocol/openid-connect/token"
    assert not any((control.query, control.fragment, sandbox.query, sandbox.fragment))
    assert not token.query and not token.fragment and PASSWORD


def _request(
    method: str,
    base: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], dict[str, Any]]:
    request_headers = {"Accept": "application/json"}
    if token is not None:
        request_headers["Authorization"] = f"Bearer {token}"
    if headers:
        request_headers.update(headers)
    data = None
    if body is not None:
        request_headers["Content-Type"] = "application/json"
        data = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    request = Request(
        f"{base}{path}", data=data, headers=request_headers, method=method
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read())
            return (
                response.status,
                {key.lower(): value for key, value in response.headers.items()},
                payload,
            )
    except HTTPError as exc:
        payload = json.loads(exc.read())
        return (
            exc.code,
            {key.lower(): value for key, value in exc.headers.items()},
            payload,
        )
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("local W13 synthetic endpoint was unavailable") from exc


def _token(username: str) -> str:
    request = Request(
        TOKEN_URL,
        data=urlencode(
            {
                "grant_type": "password",
                "client_id": "flowpilot-control-web",
                "username": username,
                "password": PASSWORD,
                "scope": "openid",
            }
        ).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("local synthetic token endpoint was unavailable") from exc
    value = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(value, str) or payload.get("token_type") != "Bearer":
        raise RuntimeError("local synthetic token response was invalid")
    return value


def _task_body() -> dict[str, object]:
    return {
        "schema_version": "w12-production-run-create/1.0",
        "task_id": TASK_ID,
        "process": "joiner",
        "category": "standard_joiner",
        "action_type": "create_ticket",
        "parameters": {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41011,
            "ticket_code": "w7.joiner001v1",
        },
    }


def _reset() -> None:
    status, _, payload = _request(
        "POST",
        SANDBOX_API,
        f"/api/arena/w7/tasks/{TASK_ID}/reset-seed",
        body={},
    )
    assert status == 200 and payload["task_id"] == TASK_ID


def _grade() -> bool:
    status, _, payload = _request(
        "POST",
        SANDBOX_API,
        f"/api/arena/w7/tasks/{TASK_ID}/grade",
        body={},
    )
    return (
        status == 200
        and payload.get("passed") is True
        and payload.get("total_score") == 100
    )


def _terminal(token: str, run_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        status, _, run = _request(
            "GET",
            CONTROL_API,
            f"/api/v1/organizations/{ALPHA}/production-runs/{run_id}",
            token=token,
        )
        assert status == 200, {"http_status": status, "code": run.get("code")}
        if run["status"] in {"finished_ungraded", "failed", "cancelled", "expired"}:
            return run
        time.sleep(1)
    raise RuntimeError("W13 production run did not become terminal")


def _hash_report(report: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def main() -> None:
    _validate_origins()
    RESULTS.mkdir(parents=True, exist_ok=True)
    _reset()
    admin = _token("syn-alpha-admin")
    manager = _token("syn-alpha-manager")
    body = _task_body()
    idempotency_key_parts = ("w13", "obs", "smoke", "01")
    idempotency_key = "-".join(idempotency_key_parts)
    status, headers, run = _request(
        "POST",
        CONTROL_API,
        f"/api/v1/organizations/{ALPHA}/production-runs",
        token=admin,
        body=body,
        headers={"Idempotency-Key": idempotency_key},
    )
    assert status == 202 and run["status"] == "waiting_approval", {
        "http_status": status,
        "code": run.get("code"),
        "run_status": run.get("status"),
    }
    request_id = str(run["approval_request_id"])
    run_id = str(run["run_id"])
    run_etag = headers["etag"]
    status, request_headers, _ = _request(
        "GET",
        CONTROL_API,
        f"/api/v1/organizations/{ALPHA}/approval-requests/{request_id}",
        token=manager,
    )
    assert status == 200
    status, _, approved = _request(
        "POST",
        CONTROL_API,
        f"/api/v1/organizations/{ALPHA}/approval-requests/{request_id}/decisions",
        token=manager,
        headers={"If-Match": request_headers["etag"]},
        body={
            "schema_version": "w11-approval-decision-create/1.0",
            "decision": "approved",
            "reason": "policy_satisfied",
        },
    )
    assert status == 200 and approved["grant_issued"] is True
    status, _, claimed = _request(
        "POST",
        CONTROL_API,
        f"/api/v1/organizations/{ALPHA}/production-runs/{run_id}/claim",
        token=admin,
        headers={"If-Match": run_etag},
        body={
            "schema_version": "w12-production-run-claim/1.0",
            "action_type": body["action_type"],
            "parameters": body["parameters"],
        },
    )
    assert status == 202 and claimed["status"] == "queued"
    terminal = _terminal(admin, run_id)
    assert terminal["status"] == "finished_ungraded"
    grader_passed = _grade()

    status, _, trace = _request(
        "GET",
        CONTROL_API,
        f"/api/v1/organizations/{ALPHA}/production-runs/{run_id}/trace",
        token=admin,
    )
    assert status == 200 and trace["schema_version"] == "w13-run-trace-export/1.0"
    phases = [str(event["phase"]) for event in trace["events"]]
    reasons = [str(event["reason"]) for event in trace["events"]]
    assert phases[0:3] == ["admission", "approval", "outbox"]
    assert "dispatch" in phases and "workflow" in phases
    assert "recovery" in phases and "planning" in phases and "browser" in phases
    assert "receipt" in phases and "cost" in phases and "terminal" in phases
    assert "run_finished_ungraded" in reasons
    assert trace["dashboard"]["terminal_status"] == "finished_ungraded"
    assert trace["dashboard"]["real_cost_microusd"] == 0
    assert trace["dashboard"]["sensitive_fields_present"] is False
    assert trace["cost"]["real_cost_microusd"] == 0
    assert len(trace["replay_steps"]) == len(trace["events"])
    serialized = json.dumps(trace, sort_keys=True, separators=(",", ":")).lower()
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
        )
    )

    report: dict[str, object] = {
        "schema_version": "w13-observability-smoke/1.0",
        "run_id": run_id,
        "trace_id": trace["trace_id"],
        "event_count": len(trace["events"]),
        "replay_step_count": len(trace["replay_steps"]),
        "terminal_status": terminal["status"],
        "terminal_reason": terminal["terminal_reason"],
        "phases": phases,
        "reasons": reasons,
        "fake_cost_microusd": int(trace["cost"]["fake_cost_microusd"]),
        "real_cost_microusd": 0,
        "dashboard_hash": trace["dashboard"]["dashboard_hash"],
        "export_hash": trace["export_hash"],
        "independent_grader_passed": grader_passed,
        "reporting_executed": False,
        "real_calls": {
            "idp": 0,
            "account_data": 0,
            "model": 0,
            "provider": 0,
            "ocr": 0,
            "vlm": 0,
            "embedding": 0,
            "egress": 0,
        },
    }
    report["result_hash"] = _hash_report(report)
    REPORT_PATH.write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
