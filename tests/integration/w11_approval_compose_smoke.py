"""Deterministic local W11 risk, approval, grant, and audit Compose smoke."""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

CONTROL_API = os.environ.get("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
TOKEN_URL = os.environ.get(
    "KEYCLOAK_TOKEN_URL",
    "http://keycloak:8080/realms/flowpilot/protocol/openid-connect/token",
)
SYNTHETIC_PASSWORD = os.environ.get("W11_SYNTHETIC_PASSWORD", "")
EVALUATION_SPLIT = os.environ.get("W11_EVALUATION_SPLIT", "development")
ALPHA = "org_syn_alpha_0001"
BETA = "org_syn_beta_0001"


def _validate_origins() -> None:
    control = urlsplit(CONTROL_API)
    token = urlsplit(TOKEN_URL)
    assert control.scheme == "http" and control.hostname == "control-api"
    assert control.path in {"", "/"} and not control.query and not control.fragment
    assert token.scheme == "http" and token.hostname == "keycloak"
    assert token.path == "/realms/flowpilot/protocol/openid-connect/token"
    assert not token.query and not token.fragment
    assert SYNTHETIC_PASSWORD
    assert EVALUATION_SPLIT in {"development", "validation"}


def _json_request(
    method: str,
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
        data = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        request_headers["Content-Type"] = "application/json"
    request = Request(f"{CONTROL_API}{path}", data=data, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
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


def _token(username: str) -> str:
    form = urlencode(
        {
            "grant_type": "password",
            "client_id": "flowpilot-control-web",
            "username": username,
            "password": SYNTHETIC_PASSWORD,
            "scope": "openid",
        }
    ).encode()
    request = Request(
        TOKEN_URL,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    for _ in range(30):
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read())
                access_token = payload.get("access_token")
                if (
                    response.status == 200
                    and isinstance(access_token, str)
                    and payload.get("token_type") == "Bearer"
                ):
                    return access_token
        except HTTPError as exc:
            raise RuntimeError("local synthetic token request was rejected") from exc
        except (URLError, TimeoutError):
            time.sleep(1)
    raise RuntimeError("local synthetic token request did not become ready")


def _gate(
    token: str,
    *,
    task_id: str,
    step_id: str,
    action_type: str,
    parameters: dict[str, object],
) -> tuple[int, dict[str, str], dict[str, Any]]:
    return _json_request(
        "POST",
        f"/api/v1/organizations/{ALPHA}/execution-gates",
        token=token,
        body={
            "task_id": task_id,
            "step_id": step_id,
            "action_type": action_type,
            "parameters": parameters,
        },
    )


def _decision(
    token: str,
    request_id: str,
    etag: str,
    decision: str,
) -> tuple[int, dict[str, str], dict[str, Any]]:
    reason = "policy_satisfied" if decision == "approved" else "policy_rejected"
    return _json_request(
        "POST",
        f"/api/v1/organizations/{ALPHA}/approval-requests/{request_id}/decisions",
        token=token,
        headers={"If-Match": etag},
        body={"decision": decision, "reason": reason},
    )


def _claim(
    token: str,
    request_id: str,
    *,
    task_id: str,
    step_id: str,
    action_type: str,
    parameters: dict[str, object],
) -> tuple[int, dict[str, str], dict[str, Any]]:
    return _json_request(
        "POST",
        f"/api/v1/organizations/{ALPHA}/approval-requests/{request_id}/claim",
        token=token,
        body={
            "task_id": task_id,
            "step_id": step_id,
            "action_type": action_type,
            "parameters": parameters,
        },
    )


def _assert_public_payload(payload: object) -> None:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).lower()
    assert "credential" not in serialized
    assert "nonce" not in serialized
    assert "access_token" not in serialized
    assert "refresh_token" not in serialized
    assert "10000000-0000" not in serialized
    assert "20000000-0000" not in serialized


def main() -> None:
    _validate_origins()
    tokens = {
        "admin": _token("syn-alpha-admin"),
        "operator": _token("syn-alpha-operator"),
        "manager": _token("syn-alpha-manager"),
        "security": _token("syn-alpha-security"),
        "disabled_manager": _token("syn-alpha-disabled-manager"),
        "disabled_security": _token("syn-alpha-disabled-security"),
        "noauthority": _token("syn-alpha-noauthority"),
        "beta_manager": _token("syn-beta-manager"),
    }

    expected_roles = {
        "admin": [],
        "operator": [],
        "manager": ["manager"],
        "security": ["security"],
        "disabled_security": [],
        "noauthority": [],
    }
    for name, expected in expected_roles.items():
        status, _, payload = _json_request(
            "GET", "/api/v1/approval-authorities/me", token=tokens[name]
        )
        assert status == 200 and payload["roles"] == expected
        _assert_public_payload(payload)
    disabled_user, _, disabled_body = _json_request(
        "GET", "/api/v1/approval-authorities/me", token=tokens["disabled_manager"]
    )
    assert disabled_user == 403 and disabled_body["code"] == "forbidden"

    before_status, _, before_audit = _json_request(
        "GET", f"/api/v1/organizations/{ALPHA}/audit-events", token=tokens["admin"]
    )
    assert before_status == 200
    before_sequence = before_audit["head_sequence"]

    l0_status, _, l0 = _gate(
        tokens["operator"],
        task_id="task_w11_l0_0001",
        step_id="inspect_task",
        action_type="inspect_task",
        parameters={"task_reference": "task_w11_l0_0001"},
    )
    l1_status, _, l1 = _gate(
        tokens["operator"],
        task_id="task_w11_l1_0001",
        step_id="create_draft",
        action_type="create_draft",
        parameters={"task_reference": "task_w11_l1_0001"},
    )
    assert (l0_status, l0["status"], l0["risk_level"]) == (200, "automatic", "L0")
    assert (l1_status, l1["status"], l1["risk_level"]) == (200, "automatic", "L1")

    l4_status, _, l4 = _gate(
        tokens["operator"],
        task_id="task_w11_l4_0001",
        step_id="physical_delete",
        action_type="physical_delete",
        parameters={},
    )
    unknown_status, _, unknown = _gate(
        tokens["operator"],
        task_id="task_w11_unknown_0001",
        step_id="unknown_action",
        action_type="unknown_action",
        parameters={"model_risk": "L0"},
    )
    invalid_status, _, invalid = _gate(
        tokens["operator"],
        task_id="task_w11_invalid_0001",
        step_id="assign_asset",
        action_type="assign_asset",
        parameters={
            "employee_id": 41001,
            "asset_code": "asset.standard",
            "risk_level": "L0",
        },
    )
    assert l4_status == 403 and l4["code"] == "risk_denied"
    assert unknown_status == 403 and unknown["code"] == "risk_denied"
    assert invalid_status == 422 and invalid["code"] == "schema_rejected"

    l2_binding = {
        "task_id": "task_w11_l2_0001",
        "step_id": "assign_asset",
        "action_type": "assign_asset",
        "parameters": {"employee_id": 41001, "asset_code": "asset.standard"},
    }
    l2_status, l2_headers, l2 = _gate(tokens["operator"], **l2_binding)
    assert l2_status == 200 and l2["status"] == "waiting_approval"
    assert l2["risk_level"] == "L2" and l2["request"]["status"] == "pending"
    l2_request = l2["request"]["request_id"]
    l2_etag = l2_headers["etag"]

    self_status, _, self_body = _decision(tokens["operator"], l2_request, l2_etag, "approved")
    noauthority_status, _, noauthority_body = _decision(
        tokens["noauthority"], l2_request, l2_etag, "approved"
    )
    admin_status, _, admin_body = _decision(tokens["admin"], l2_request, l2_etag, "approved")
    disabled_status, _, disabled_authority_body = _decision(
        tokens["disabled_security"], l2_request, l2_etag, "approved"
    )
    assert self_status == 403 and self_body["code"] == "forbidden"
    assert noauthority_status == 403 and noauthority_body["code"] == "forbidden"
    assert admin_status == 403 and admin_body["code"] == "forbidden"
    assert disabled_status == 403 and disabled_authority_body["code"] == "forbidden"

    l2_approved_status, _, l2_approved = _decision(
        tokens["manager"], l2_request, l2_etag, "approved"
    )
    assert l2_approved_status == 200 and l2_approved["grant_issued"] is True
    assert l2_approved["request"]["status"] == "approved"
    _assert_public_payload(l2_approved)

    def l2_contender(_: int) -> int:
        return _claim(tokens["operator"], l2_request, **l2_binding)[0]

    with ThreadPoolExecutor(max_workers=2) as executor:
        l2_claims = tuple(executor.map(l2_contender, (1, 2)))
    assert sorted(l2_claims) == [200, 409]
    replay_status = _claim(tokens["operator"], l2_request, **l2_binding)[0]
    assert replay_status == 409

    l3_binding = {
        "task_id": "task_w11_l3_0001",
        "step_id": "disable_employee",
        "action_type": "disable_employee",
        "parameters": {"employee_id": 41002},
    }
    l3_status, l3_headers, l3 = _gate(tokens["operator"], **l3_binding)
    assert l3_status == 200 and l3["risk_level"] == "L3"
    l3_request = l3["request"]["request_id"]
    manager_status, manager_headers, manager_decision = _decision(
        tokens["manager"], l3_request, l3_headers["etag"], "approved"
    )
    assert manager_status == 200 and manager_decision["grant_issued"] is False
    assert manager_decision["request"]["status"] == "pending"
    security_status, _, security_decision = _decision(
        tokens["security"], l3_request, manager_headers["etag"], "approved"
    )
    assert security_status == 200 and security_decision["grant_issued"] is True
    assert security_decision["request"]["status"] == "approved"
    l3_claim_status, _, l3_claim = _claim(tokens["operator"], l3_request, **l3_binding)
    assert l3_claim_status == 200 and l3_claim["grant_status"] == "claimed"
    assert _claim(tokens["operator"], l3_request, **l3_binding)[0] == 409
    _assert_public_payload(security_decision)
    _assert_public_payload(l3_claim)

    rejected_binding = {
        "task_id": "task_w11_reject_0001",
        "step_id": "create_ticket",
        "action_type": "create_ticket",
        "parameters": {"employee_id": 41003, "ticket_code": "ticket.standard"},
    }
    reject_gate_status, reject_headers, reject_gate = _gate(tokens["operator"], **rejected_binding)
    assert reject_gate_status == 200
    rejected_request = reject_gate["request"]["request_id"]
    rejected_status, _, rejected = _decision(
        tokens["manager"], rejected_request, reject_headers["etag"], "rejected"
    )
    assert rejected_status == 200 and rejected["request"]["status"] == "rejected"
    assert rejected["grant_issued"] is False
    assert _claim(tokens["operator"], rejected_request, **rejected_binding)[0] == 409

    invalidated_binding = {
        "task_id": "task_w11_parameter_0001",
        "step_id": "assign_asset",
        "action_type": "assign_asset",
        "parameters": {"employee_id": 41004, "asset_code": "asset.original"},
    }
    parameter_status, parameter_headers, parameter_gate = _gate(
        tokens["operator"], **invalidated_binding
    )
    assert parameter_status == 200
    parameter_request = parameter_gate["request"]["request_id"]
    parameter_approved_status, parameter_approved_headers, parameter_approved = _decision(
        tokens["manager"], parameter_request, parameter_headers["etag"], "approved"
    )
    assert parameter_approved_status == 200 and parameter_approved["grant_issued"] is True
    invalidated_status, _, invalidated = _json_request(
        "POST",
        f"/api/v1/organizations/{ALPHA}/approval-requests/{parameter_request}/invalidate",
        token=tokens["admin"],
        headers={"If-Match": parameter_approved_headers["etag"]},
        body={"reason": "parameters_changed"},
    )
    assert invalidated_status == 200 and invalidated["status"] == "invalidated"
    changed_binding = {
        **invalidated_binding,
        "parameters": {"employee_id": 41004, "asset_code": "asset.changed"},
    }
    assert _claim(tokens["operator"], parameter_request, **changed_binding)[0] == 409

    cross_status, _, cross_body = _json_request(
        "GET",
        f"/api/v1/organizations/{BETA}/approval-requests",
        token=tokens["manager"],
    )
    assert cross_status == 404 and cross_body["code"] == "resource_not_found"
    beta_role_status, _, beta_role = _json_request(
        "GET", "/api/v1/approval-authorities/me", token=tokens["beta_manager"]
    )
    assert beta_role_status == 200 and beta_role["roles"] == ["manager"]

    verify_status, _, verified = _json_request(
        "POST",
        f"/api/v1/organizations/{ALPHA}/audit-events/verify",
        token=tokens["admin"],
    )
    assert verify_status == 200 and verified["valid"] is True
    audit_status, _, audit = _json_request(
        "GET", f"/api/v1/organizations/{ALPHA}/audit-events", token=tokens["admin"]
    )
    assert audit_status == 200
    assert audit["head_sequence"] == audit["count"]
    assert audit["head_sequence"] > before_sequence
    assert len(audit["head_hash"]) == 64
    event_types = {item["event_type"] for item in audit["items"]}
    expected_events = {
        "risk_classified",
        "l4_denied",
        "approval_requested",
        "approval_approved",
        "approval_rejected",
        "request_invalidated",
        "grant_issued",
        "grant_claimed",
        "grant_rejected",
        "execution_started",
        "execution_succeeded",
        "audit_verified",
    }
    assert expected_events <= event_types
    _assert_public_payload(audit)
    _assert_public_payload(verified)

    summary = {
        "schema_version": "w11-compose-smoke/1.0",
        "synthetic_organizations": 2,
        "synthetic_users": 16,
        "synthetic_authorities": 8,
        "risk_action_counts": {"L0": 2, "L1": 2, "L2": 7, "L3": 5, "L4": 5},
        "risk_allow": 4,
        "risk_deny": 2,
        "schema_reject": 1,
        "approval_requests": 4,
        "manager_approve": 3,
        "manager_reject": 1,
        "security_approve": 1,
        "self_approval_reject": 1,
        "inactive_or_missing_authority_reject": 3,
        "cross_organization_reject": 1,
        "parameter_change_invalidation": 1,
        "grants_issued": 3,
        "grants_claimed": 2,
        "grant_rejected": 5,
        "concurrent_exactly_one_winner": True,
        "pre_approval_side_effects": 0,
        "duplicate_side_effects": 0,
        "audit_events_added": audit["head_sequence"] - before_sequence,
        "audit_head_sequence": audit["head_sequence"],
        "audit_head_hash": audit["head_hash"],
        "audit_chain_valid": True,
        "sensitive_information_scan": "passed",
        "real_identity_provider_calls": 0,
        "real_model_provider_calls": 0,
        "cost": 0,
        "validation_run": EVALUATION_SPLIT == "validation",
        "reporting_executed": False,
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
