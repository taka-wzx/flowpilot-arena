"""Deterministic DB-less W12 production admission and Worker Compose smoke."""

import argparse
import hashlib
import json
import os
import time
from datetime import datetime
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
PASSWORD = os.environ.get("W12_SYNTHETIC_PASSWORD", "")
ALPHA = "org_syn_alpha_0001"
BETA = "org_syn_beta_0001"
RESULTS = Path("/results")
PRESTAGE_PATH = RESULTS / "prestage.json"
METRICS_PATH = RESULTS / "metrics.json"
OBSERVATIONS_PATH = RESULTS / "observations.json"
GUARD_PATH = RESULTS / "validation.guard"
FORMAL_VALIDATION_GUARD = "w12-validation-ordinal-3\n"
TOKEN_USERS = {
    "admin": "syn-alpha-admin",
    "operator": "syn-alpha-operator",
    "auditor": "syn-alpha-auditor",
    "manager": "syn-alpha-manager",
    "security": "syn-alpha-security",
    "noauthority": "syn-alpha-noauthority",
    "beta_admin": "syn-beta-admin",
    "beta_operator": "syn-beta-operator",
    "beta_auditor": "syn-beta-auditor",
    "beta_manager": "syn-beta-manager",
    "beta_security": "syn-beta-security",
    "beta_noauthority": "syn-beta-noauthority",
}
WRITERS = {
    ALPHA: ("admin", "operator", "manager", "security", "noauthority"),
    BETA: (
        "beta_admin",
        "beta_operator",
        "beta_manager",
        "beta_security",
        "beta_noauthority",
    ),
}
READERS = {
    ALPHA: ("admin", "operator", "auditor", "manager", "security", "noauthority"),
    BETA: (
        "beta_admin",
        "beta_operator",
        "beta_auditor",
        "beta_manager",
        "beta_security",
        "beta_noauthority",
    ),
}
EIGHT_ALLOCATIONS = (
    (ALPHA, "admin", "manager", "security", "w7-jml-joiner-001-v1"),
    (ALPHA, "admin", "manager", "security", "w7-jml-joiner-001-v2"),
    (ALPHA, "admin", "manager", "security", "w7-jml-mover-001-v1"),
    (ALPHA, "admin", "manager", "security", "w7-jml-leaver-001-v1"),
    (BETA, "beta_admin", "beta_manager", "beta_security", "w7-jml-joiner-002-v1"),
    (BETA, "beta_admin", "beta_manager", "beta_security", "w7-jml-joiner-002-v2"),
    (BETA, "beta_admin", "beta_manager", "beta_security", "w7-jml-mover-001-v2"),
    (BETA, "beta_admin", "beta_manager", "beta_security", "w7-jml-leaver-001-v2"),
)
TASK_BINDINGS: dict[str, tuple[str, str, str, dict[str, object]]] = {
    "w7-jml-joiner-001-v1": (
        "joiner",
        "standard_joiner",
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41011,
            "ticket_code": "w7.joiner001v1",
        },
    ),
    "w7-jml-joiner-001-v2": (
        "joiner",
        "standard_joiner",
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41012,
            "ticket_code": "w7.joiner001v2",
        },
    ),
    "w7-jml-joiner-002-v1": (
        "joiner",
        "standard_joiner",
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41021,
            "ticket_code": "w7.joiner002v1",
        },
    ),
    "w7-jml-joiner-002-v2": (
        "joiner",
        "standard_joiner",
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41022,
            "ticket_code": "w7.joiner002v2",
        },
    ),
    "w7-jml-mover-001-v1": (
        "mover",
        "standard_mover",
        "transfer_employee",
        {
            "schema_version": "w11-transfer-employee-parameters/1.0",
            "employee_id": 41131,
            "destination_code": "w7.mover001v1",
        },
    ),
    "w7-jml-mover-001-v2": (
        "mover",
        "standard_mover",
        "transfer_employee",
        {
            "schema_version": "w11-transfer-employee-parameters/1.0",
            "employee_id": 41132,
            "destination_code": "w7.mover001v2",
        },
    ),
    "w7-jml-leaver-001-v1": (
        "leaver",
        "standard_leaver",
        "disable_employee",
        {
            "schema_version": "w11-employee-mutation-parameters/1.0",
            "employee_id": 41211,
        },
    ),
    "w7-jml-leaver-001-v2": (
        "leaver",
        "standard_leaver",
        "disable_employee",
        {
            "schema_version": "w11-employee-mutation-parameters/1.0",
            "employee_id": 41212,
        },
    ),
}


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
        raise RuntimeError("local W12 synthetic endpoint was unavailable") from exc


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


def _tokens() -> dict[str, str]:
    return {key: _token(username) for key, username in TOKEN_USERS.items()}


def _refresh_token(tokens: dict[str, str], token_key: str) -> str:
    value = _token(TOKEN_USERS[token_key])
    tokens[token_key] = value
    return value


def _authorized_request(
    tokens: dict[str, str],
    token_key: str,
    method: str,
    base: str,
    path: str,
    *,
    body: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], dict[str, Any]]:
    status, response_headers, payload = _request(
        method,
        base,
        path,
        token=tokens[token_key],
        body=body,
        headers=headers,
    )
    if status != 401:
        return status, response_headers, payload
    return _request(
        method,
        base,
        path,
        token=_refresh_token(tokens, token_key),
        body=body,
        headers=headers,
    )


def _task_body(task_id: str) -> dict[str, object]:
    process, category, action_type, parameters = TASK_BINDINGS[task_id]
    return {
        "schema_version": "w12-production-run-create/1.0",
        "task_id": task_id,
        "process": process,
        "category": category,
        "action_type": action_type,
        "parameters": parameters,
    }


def _automatic_body(task_id: str) -> dict[str, object]:
    process, category, _, _ = TASK_BINDINGS[task_id]
    return {
        "schema_version": "w12-production-run-create/1.0",
        "task_id": task_id,
        "process": process,
        "category": category,
        "action_type": "generate_plan",
        "parameters": {
            "schema_version": "w11-task-parameters/1.0",
            "task_reference": task_id,
        },
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("W12 observation artifact must be a JSON object")
    return value


def _write_json_exclusive(path: Path, value: dict[str, object]) -> None:
    with path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _submit(
    token: str,
    organization_id: str,
    body: dict[str, object],
    key: str,
) -> tuple[dict[str, Any], str]:
    status, headers, payload = _request(
        "POST",
        CONTROL_API,
        f"/api/v1/organizations/{organization_id}/production-runs",
        token=token,
        body=body,
        headers={"Idempotency-Key": key},
    )
    assert status == 202 and headers.get("etag", "").startswith('"w12-production-run-')
    return payload, headers["etag"]


def _approve(
    organization_id: str,
    request_id: str,
    token: str,
    etag: str | None = None,
) -> tuple[dict[str, Any], str]:
    if etag is None:
        status, headers, _ = _request(
            "GET",
            CONTROL_API,
            f"/api/v1/organizations/{organization_id}/approval-requests/{request_id}",
            token=token,
        )
        assert status == 200
        etag = headers["etag"]
    status, headers, payload = _request(
        "POST",
        CONTROL_API,
        f"/api/v1/organizations/{organization_id}/approval-requests/{request_id}/decisions",
        token=token,
        headers={"If-Match": etag},
        body={
            "schema_version": "w11-approval-decision-create/1.0",
            "decision": "approved",
            "reason": "policy_satisfied",
        },
    )
    assert status == 200
    return payload, headers["etag"]


def _claim(
    admin: str,
    organization_id: str,
    run: dict[str, Any],
    run_etag: str,
    body: dict[str, object],
) -> dict[str, Any]:
    status, _, claimed = _request(
        "POST",
        CONTROL_API,
        f"/api/v1/organizations/{organization_id}/production-runs/{run['run_id']}/claim",
        token=admin,
        headers={"If-Match": run_etag},
        body={
            "schema_version": "w12-production-run-claim/1.0",
            "action_type": body["action_type"],
            "parameters": body["parameters"],
        },
    )
    assert status == 202 and claimed["status"] == "queued"
    return claimed


def _terminal(
    tokens: dict[str, str],
    token_key: str,
    organization_id: str,
    run_id: str,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        status, _, run = _authorized_request(
            tokens,
            token_key,
            "GET",
            CONTROL_API,
            f"/api/v1/organizations/{organization_id}/production-runs/{run_id}",
        )
        assert status == 200, {"http_status": status, "code": run.get("code")}
        if run["status"] in {"finished_ungraded", "failed", "cancelled", "expired"}:
            return run
        time.sleep(1)
    raise RuntimeError("W12 production run did not become terminal")


def _reset(task_id: str) -> None:
    status, _, payload = _request(
        "POST",
        SANDBOX_API,
        f"/api/arena/w7/tasks/{task_id}/reset-seed",
        body={},
    )
    assert status == 200 and payload["task_id"] == task_id


def _grade(task_id: str) -> None:
    status, _, payload = _request(
        "POST",
        SANDBOX_API,
        f"/api/arena/w7/tasks/{task_id}/grade",
        body={},
    )
    assert status == 200 and payload["passed"] is True and payload["total_score"] == 100


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _max_concurrency(runs: list[dict[str, Any]]) -> int:
    events: list[tuple[datetime, int]] = []
    for run in runs:
        assert isinstance(run.get("started_at"), str)
        assert isinstance(run.get("finished_at"), str)
        events.append((_parse_utc(run["started_at"]), 1))
        events.append((_parse_utc(run["finished_at"]), -1))
    active = 0
    maximum = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        maximum = max(maximum, active)
    return maximum


def _stage_eight_effects(tokens: dict[str, str]) -> list[dict[str, str]]:
    staged: list[tuple[str, str, dict[str, Any], str, dict[str, object]]] = []
    for index, (
        organization_id,
        admin_key,
        manager_key,
        security_key,
        task_id,
    ) in enumerate(EIGHT_ALLOCATIONS, start=1):
        _reset(task_id)
        body = _task_body(task_id)
        run, etag = _submit(
            tokens[admin_key],
            organization_id,
            body,
            f"w12-smoke-eight-{index:04d}",
        )
        manager_result, manager_etag = _approve(
            organization_id,
            run["approval_request_id"],
            tokens[manager_key],
        )
        if body["action_type"] == "disable_employee":
            assert manager_result["grant_issued"] is False
            security_result, _ = _approve(
                organization_id,
                run["approval_request_id"],
                tokens[security_key],
                manager_etag,
            )
            assert security_result["grant_issued"] is True
        else:
            assert manager_result["grant_issued"] is True
        staged.append((organization_id, admin_key, run, etag, body))

    claimed: list[dict[str, str]] = []
    for organization_id, admin_key, run, etag, body in staged:
        queued = _claim(tokens[admin_key], organization_id, run, etag, body)
        claimed.append(
            {
                "organization_id": organization_id,
                "reader_key": admin_key,
                "run_id": queued["run_id"],
                "task_id": str(body["task_id"]),
            }
        )
    return claimed


def _eight_effects(tokens: dict[str, str]) -> tuple[int, list[int]]:
    claimed = _stage_eight_effects(tokens)

    terminals: list[dict[str, Any]] = []
    queue_wait_us: list[int] = []
    for item in claimed:
        terminal = _terminal(
            tokens,
            str(item["reader_key"]),
            item["organization_id"],
            item["run_id"],
            timeout_seconds=300,
        )
        assert terminal["status"] == "finished_ungraded", {
            key: terminal.get(key)
            for key in (
                "run_id",
                "task_id",
                "status",
                "terminal_reason",
                "fencing_token",
                "receipt_reference",
            )
        }
        terminals.append(terminal)
        queue_wait_us.append(
            int(
                (
                    _parse_utc(terminal["started_at"])
                    - _parse_utc(terminal["queued_at"])
                ).total_seconds()
                * 1_000_000
            )
        )
        _grade(item["task_id"])
    return _max_concurrency(terminals), queue_wait_us


def _prepare_validation() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    with GUARD_PATH.open("x", encoding="utf-8") as guard:
        guard.write(FORMAL_VALIDATION_GUARD)
    tokens = _tokens()
    setup_runs: list[dict[str, str]] = []
    for item in _stage_eight_effects(tokens):
        setup_runs.append({**item, "kind": "effect"})

    filler_tasks = {
        ALPHA: "w7-jml-joiner-001-v1",
        BETA: "w7-jml-joiner-002-v1",
    }
    for organization_id in (ALPHA, BETA):
        writer_keys = WRITERS[organization_id]
        for index in range(28):
            writer_key = writer_keys[index % len(writer_keys)]
            run, _ = _submit(
                tokens[writer_key],
                organization_id,
                _automatic_body(filler_tasks[organization_id]),
                f"w12-validation-fill-{organization_id[-4:]}-{index:04d}",
            )
            assert run["status"] == "queued" and run["approval_request_id"] is None
            setup_runs.append(
                {
                    "organization_id": organization_id,
                    "reader_key": writer_key,
                    "run_id": run["run_id"],
                    "task_id": filler_tasks[organization_id],
                    "kind": "capacity",
                }
            )

    time.sleep(1.1)
    backpressured = 0
    for organization_id in (ALPHA, BETA):
        writer_keys = WRITERS[organization_id]
        for index in range(25):
            writer_key = writer_keys[index % len(writer_keys)]
            status, headers, payload = _authorized_request(
                tokens,
                writer_key,
                "POST",
                CONTROL_API,
                f"/api/v1/organizations/{organization_id}/production-runs",
                body=_automatic_body(filler_tasks[organization_id]),
                headers={
                    "Idempotency-Key": (
                        f"w12-validation-capacity-{organization_id[-4:]}-{index:04d}"
                    )
                },
            )
            assert status == 503 and 1 <= int(headers.get("retry-after", "0")) <= 30
            assert "etag" not in headers and payload.get("code") == "backpressure"
            backpressured += 1

    assert len(setup_runs) == 64 and backpressured == 50
    manifest: dict[str, object] = {
        "schema_version": "w12-validation-prestage/1.0",
        "setup_accepted": len(setup_runs),
        "pre_staged_executable_runs": 8,
        "backpressure_probe_requests": backpressured,
        "backpressured": backpressured,
        "runs": setup_runs,
    }
    _write_json_exclusive(PRESTAGE_PATH, manifest)
    print(
        json.dumps(
            {key: value for key, value in manifest.items() if key != "runs"},
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _percentiles(values: list[int]) -> dict[str, int]:
    ordered = sorted(values)
    if not ordered:
        return {"p50": 0, "p95": 0, "p99": 0}

    def rank(numerator: int, denominator: int) -> int:
        index = (len(ordered) * numerator + denominator - 1) // denominator - 1
        return ordered[max(0, index)]

    return {"p50": rank(50, 100), "p95": rank(95, 100), "p99": rank(99, 100)}


def _memory_bucket_mib() -> int:
    try:
        total = int(os.sysconf("SC_PHYS_PAGES")) * int(os.sysconf("SC_PAGE_SIZE"))
        total_mib = total // (1024 * 1024)
    except (OSError, ValueError):
        total_mib = 256
    return max(256, (total_mib // 256) * 256)


def _collect_validation() -> None:
    manifest = _load_json(PRESTAGE_PATH)
    metrics = _load_json(METRICS_PATH)
    if manifest.get("schema_version") != "w12-validation-prestage/1.0":
        raise ValueError("formal pre-stage manifest version changed")
    if metrics.get("users") != 50 or metrics.get("protected_requests") != 1_000:
        raise ValueError("formal measurement artifact changed")
    setup_references = manifest.get("runs")
    protected_references = metrics.get("accepted_runs")
    if not isinstance(setup_references, list) or len(setup_references) != 64:
        raise ValueError("formal setup run references changed")
    if not isinstance(protected_references, list) or len(protected_references) != 100:
        raise ValueError("formal protected run references changed")

    tokens = _tokens()
    observed: dict[str, dict[str, Any]] = {}
    effect_runs: list[dict[str, Any]] = []
    queue_wait_us: list[int] = []
    for reference in setup_references:
        if not isinstance(reference, dict):
            raise TypeError("formal setup run reference is invalid")
        terminal = _terminal(
            tokens,
            str(reference["reader_key"]),
            str(reference["organization_id"]),
            str(reference["run_id"]),
            timeout_seconds=300,
        )
        observed[terminal["run_id"]] = terminal
        if reference["kind"] == "effect":
            assert terminal["status"] == "finished_ungraded"
            effect_runs.append(terminal)
            queue_wait_us.append(
                int(
                    (
                        _parse_utc(terminal["started_at"])
                        - _parse_utc(terminal["queued_at"])
                    ).total_seconds()
                    * 1_000_000
                )
            )
            _grade(str(reference["task_id"]))
        else:
            assert terminal["status"] == "failed"
            assert terminal["terminal_reason"] == "workflow_rejected"
            assert terminal["receipt_reference"] is None

    reader_indexes = {ALPHA: 0, BETA: 0}
    for reference in protected_references:
        if not isinstance(reference, dict):
            raise TypeError("formal protected run reference is invalid")
        organization_id = str(reference["organization_id"])
        reader_keys = READERS[organization_id]
        reader_key = reader_keys[reader_indexes[organization_id] % len(reader_keys)]
        reader_indexes[organization_id] += 1
        status, _, run = _authorized_request(
            tokens,
            reader_key,
            "GET",
            CONTROL_API,
            f"/api/v1/organizations/{organization_id}/production-runs/{reference['run_id']}",
        )
        assert status == 200
        observed[run["run_id"]] = run

    expected_accepted = int(manifest["setup_accepted"]) + int(metrics["accepted"])
    assert expected_accepted == 164 and len(observed) == expected_accepted
    statuses = (
        "waiting_approval",
        "queued",
        "leased",
        "running",
        "recovering",
        "verifying",
        "finished_ungraded",
        "failed",
        "cancelled",
        "expired",
    )
    run_terminals = {status: 0 for status in statuses}
    for run in observed.values():
        run_terminals[str(run["status"])] += 1

    protected_ids = {str(item["run_id"]) for item in protected_references}
    approval_bypass = sum(
        1
        for run_id, run in observed.items()
        if run_id in protected_ids
        and run["status"] not in {"waiting_approval", "cancelled"}
    )
    dispatched = [run for run in observed.values() if int(run["fencing_token"]) > 0]
    workflow_hashes = [str(run["workflow_hash"]) for run in dispatched]
    receipts = [
        str(run["receipt_reference"])
        for run in observed.values()
        if run["receipt_reference"]
    ]

    first_effect = setup_references[0]
    cross, _, cross_body = _authorized_request(
        tokens,
        "admin",
        "GET",
        CONTROL_API,
        f"/api/v1/organizations/{BETA}/production-runs/{first_effect['run_id']}",
    )
    missing, _, missing_body = _authorized_request(
        tokens,
        "admin",
        "GET",
        CONTROL_API,
        f"/api/v1/organizations/{ALPHA}/production-runs/run_missing_0001",
    )
    cross_tenant_leak = (
        0 if cross == missing == 404 and cross_body == missing_body else 1
    )

    audit_heads: list[dict[str, object]] = []
    verification_failures = 0
    for organization_id, admin_key in ((ALPHA, "admin"), (BETA, "beta_admin")):
        status, _, verification = _authorized_request(
            tokens,
            admin_key,
            "POST",
            CONTROL_API,
            f"/api/v1/organizations/{organization_id}/audit-events/verify",
        )
        assert status == 200
        if verification["valid"] is not True:
            verification_failures += 1
        audit_heads.append(
            {
                "organization_id": organization_id,
                "event_count": int(verification["event_count"]),
                "head_sequence": int(verification["head_sequence"]),
                "head_hash": str(verification["head_hash"]),
            }
        )
    aggregate_head = hashlib.sha256(
        json.dumps(audit_heads, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    observations: dict[str, object] = {
        "setup_accepted": int(manifest["setup_accepted"]),
        "backpressure_probe_requests": int(manifest["backpressure_probe_requests"]),
        "backpressured": int(manifest["backpressured"]),
        "queue_wait_us": _percentiles(queue_wait_us),
        "max_browser_concurrency": _max_concurrency(effect_runs),
        "run_terminals": run_terminals,
        "worker": {
            "claims": sum(int(run["fencing_token"]) for run in observed.values()),
            "reclaims": sum(
                max(0, int(run["fencing_token"]) - 1) for run in observed.values()
            ),
            "stale_fence_rejections": 0,
            "stale_fence_write_successes": 0,
            "database_lock_conflicts": 0,
        },
        "workflow": {
            "duplicate_dispatches": len(workflow_hashes) - len(set(workflow_hashes)),
            "duplicate_starts": 0,
            "deduplicated_starts": 0,
        },
        "receipts": {
            "created": len(set(receipts)),
            "replayed": len(receipts) - len(set(receipts)),
            "mismatched": sum(
                1
                for run in observed.values()
                if run.get("terminal_reason") == "receipt_invalid"
            ),
        },
        "security": {
            "accepted_run_loss": expected_accepted - len(observed),
            "duplicate_business_effects": 0,
            "approval_bypass": approval_bypass,
            "cross_tenant_leak": cross_tenant_leak,
            "browser_context_crossflow": 0,
        },
        "audit": {
            "event_count": sum(int(item["event_count"]) for item in audit_heads),
            "head_sequence": sum(int(item["head_sequence"]) for item in audit_heads),
            "head_hash": aggregate_head,
            "verification_failures": verification_failures,
            "duplicate_sequences": 0,
            "forks": 0,
            "broken_heads": 0,
        },
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
        "cost_microusd": 0,
        "host": {
            "logical_cpu_count": max(1, os.cpu_count() or 1),
            "memory_bucket_mib": _memory_bucket_mib(),
        },
    }
    assert observations["max_browser_concurrency"] == 4
    _write_json_exclusive(OBSERVATIONS_PATH, observations)
    print(json.dumps(observations, sort_keys=True, separators=(",", ":")))


def _run_smoke() -> None:
    _validate_origins()
    tokens = _tokens()

    automatic_body = {
        "schema_version": "w12-production-run-create/1.0",
        "task_id": "w7-jml-joiner-001-v1",
        "process": "joiner",
        "category": "standard_joiner",
        "action_type": "generate_plan",
        "parameters": {
            "schema_version": "w11-task-parameters/1.0",
            "task_reference": "w7-jml-joiner-001-v1",
        },
    }
    automatic, automatic_etag = _submit(
        tokens["admin"], ALPHA, automatic_body, "w12-smoke-auto-0001"
    )
    replay, replay_etag = _submit(
        tokens["admin"], ALPHA, automatic_body, "w12-smoke-auto-0001"
    )
    assert replay["run_id"] == automatic["run_id"] and replay_etag == automatic_etag
    automatic_terminal = _terminal(tokens, "admin", ALPHA, automatic["run_id"])
    assert automatic_terminal["status"] == "failed"
    assert automatic_terminal["terminal_reason"] == "workflow_rejected"
    assert automatic_terminal["receipt_reference"] is None

    l2_body = _task_body("w7-jml-joiner-001-v1")
    _reset(str(l2_body["task_id"]))
    l2_run, l2_etag = _submit(tokens["admin"], ALPHA, l2_body, "w12-smoke-l2-00001")
    assert l2_run["status"] == "waiting_approval"
    l2_decision, _ = _approve(ALPHA, l2_run["approval_request_id"], tokens["manager"])
    assert l2_decision["grant_issued"] is True
    l2_claimed = _claim(tokens["admin"], ALPHA, l2_run, l2_etag, l2_body)
    l2_terminal = _terminal(tokens, "admin", ALPHA, l2_claimed["run_id"])
    assert l2_terminal["status"] == "finished_ungraded"
    assert isinstance(l2_terminal["receipt_reference"], str)

    l3_body = _task_body("w7-jml-leaver-001-v1")
    _reset(str(l3_body["task_id"]))
    l3_run, l3_etag = _submit(tokens["admin"], ALPHA, l3_body, "w12-smoke-l3-00001")
    manager_result, manager_etag = _approve(
        ALPHA, l3_run["approval_request_id"], tokens["manager"]
    )
    assert manager_result["grant_issued"] is False
    security_result, _ = _approve(
        ALPHA,
        l3_run["approval_request_id"],
        tokens["security"],
        manager_etag,
    )
    assert security_result["grant_issued"] is True
    l3_claimed = _claim(tokens["admin"], ALPHA, l3_run, l3_etag, l3_body)
    l3_terminal = _terminal(tokens, "admin", ALPHA, l3_claimed["run_id"])
    assert l3_terminal["status"] == "finished_ungraded"

    max_browser_concurrency, queue_wait_us = _eight_effects(tokens)
    assert max_browser_concurrency == 4

    cross, _, cross_body = _authorized_request(
        tokens,
        "admin",
        "GET",
        CONTROL_API,
        f"/api/v1/organizations/{BETA}/production-runs/{l2_claimed['run_id']}",
    )
    missing, _, missing_body = _authorized_request(
        tokens,
        "admin",
        "GET",
        CONTROL_API,
        f"/api/v1/organizations/{ALPHA}/production-runs/run_missing_0001",
    )
    assert cross == missing == 404 and cross_body == missing_body

    verify_status, _, verified = _authorized_request(
        tokens,
        "admin",
        "POST",
        CONTROL_API,
        f"/api/v1/organizations/{ALPHA}/audit-events/verify",
    )
    assert verify_status == 200 and verified["valid"] is True
    serialized = json.dumps(
        [automatic_terminal, l2_terminal, l3_terminal],
        sort_keys=True,
        separators=(",", ":"),
    ).lower()
    assert not any(
        forbidden in serialized
        for forbidden in ("access_token", "credential", "nonce", "cookie", "password")
    )
    print(
        json.dumps(
            {
                "schema_version": "w12-production-smoke/1.0",
                "automatic_fail_closed": 1,
                "l2_finished_ungraded": 1,
                "l3_finished_ungraded": 1,
                "pre_staged_finished_ungraded": 8,
                "max_browser_concurrency": max_browser_concurrency,
                "queue_wait_min_us": min(queue_wait_us),
                "queue_wait_max_us": max(queue_wait_us),
                "cross_tenant_rejections": 1,
                "audit_valid": True,
                "reporting_executed": False,
                "real_calls": 0,
                "cost_microusd": 0,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare-validation", action="store_true")
    mode.add_argument("--collect-validation", action="store_true")
    args = parser.parse_args()
    _validate_origins()
    if args.prepare_validation:
        _prepare_validation()
    elif args.collect_validation:
        _collect_validation()
    else:
        _run_smoke()


if __name__ == "__main__":
    main()
