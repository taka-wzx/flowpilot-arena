"""Local-only W10 OIDC, RBAC, tenant, and optimistic-lock Compose smoke."""

import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

CONTROL_API = os.environ.get("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
TOKEN_URL = os.environ.get(
    "KEYCLOAK_TOKEN_URL",
    "http://keycloak:8080/realms/flowpilot/protocol/openid-connect/token",
)
SYNTHETIC_PASSWORD = os.environ.get("W10_SYNTHETIC_PASSWORD", "")
ALPHA = "org_syn_alpha_0001"
BETA = "org_syn_beta_0001"
BETA_ADMIN = "usr_syn_beta_admin_0001"
BETA_ADMIN_MEMBERSHIP = "mbr_syn_beta_admin_0001"
ALPHA_AUDITOR_MEMBERSHIP = "mbr_syn_alpha_auditor_0001"


def _validate_origins() -> None:
    control = urlsplit(CONTROL_API)
    token = urlsplit(TOKEN_URL)
    assert control.scheme == "http" and control.hostname == "control-api"
    assert control.path in {"", "/"} and not control.query and not control.fragment
    assert token.scheme == "http" and token.hostname == "keycloak"
    assert token.path == "/realms/flowpilot/protocol/openid-connect/token"
    assert not token.query and not token.fragment
    assert SYNTHETIC_PASSWORD


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
    request = Request(
        f"{CONTROL_API}{path}", data=data, headers=request_headers, method=method
    )
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


def _etag(kind: str, organization_id: str, resource_id: str, version: int) -> str:
    fingerprint = hashlib.sha256(
        f"{kind}|{organization_id}|{resource_id}".encode()
    ).hexdigest()[:24]
    return f'"w10-{kind}-{fingerprint}-v{version}"'


def main() -> None:
    _validate_origins()
    tokens = {
        "admin": _token("syn-alpha-admin"),
        "operator": _token("syn-alpha-operator"),
        "auditor": _token("syn-alpha-auditor"),
        "beta_admin": _token("syn-beta-admin"),
    }
    roles = {
        "admin": "organization_admin",
        "operator": "operator",
        "auditor": "auditor",
        "beta_admin": "organization_admin",
    }
    for name, token in tokens.items():
        code, _, payload = _json_request("GET", "/api/v1/identity/me", token=token)
        assert code == 200 and payload["role"] == roles[name]
    missing, _, missing_body = _json_request("GET", "/api/v1/identity/me")
    assert missing == 401 and missing_body["code"] == "authentication_required"

    operator_memberships, _, _ = _json_request(
        "GET", f"/api/v1/organizations/{ALPHA}/memberships", token=tokens["operator"]
    )
    auditor_write, _, _ = _json_request(
        "POST",
        f"/api/v1/organizations/{ALPHA}/memories",
        token=tokens["auditor"],
        body={
            "field": "department",
            "safe_value": "must_not_write",
            "valid_from": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
    )
    assert operator_memberships == 403 and auditor_write == 403

    beta_user_etag = _etag("user", BETA, BETA_ADMIN, 1)
    beta_membership_etag = _etag("membership", BETA, BETA_ADMIN_MEMBERSHIP, 1)
    beta_collection_etag = _etag("memory-collection", BETA, BETA, 1)
    cross_statuses = (
        _json_request("GET", f"/api/v1/organizations/{BETA}", token=tokens["admin"])[0],
        _json_request(
            "GET", f"/api/v1/organizations/{BETA}/users", token=tokens["admin"]
        )[0],
        _json_request(
            "GET", f"/api/v1/organizations/{BETA}/users/count", token=tokens["admin"]
        )[0],
        _json_request(
            "PATCH",
            f"/api/v1/organizations/{BETA}/users/{BETA_ADMIN}",
            token=tokens["admin"],
            headers={"If-Match": beta_user_etag},
            body={"profile_code": "cross_org_update"},
        )[0],
        _json_request(
            "PATCH",
            f"/api/v1/organizations/{BETA}/memberships/{BETA_ADMIN_MEMBERSHIP}",
            token=tokens["admin"],
            headers={"If-Match": beta_membership_etag},
            body={"role": "auditor"},
        )[0],
        _json_request(
            "POST",
            f"/api/v1/organizations/{BETA}/memories/reset",
            token=tokens["admin"],
            headers={"If-Match": beta_collection_etag},
        )[0],
        _json_request(
            "GET",
            f"/api/v1/organizations/{BETA}/context-projection",
            token=tokens["admin"],
        )[0],
    )
    assert cross_statuses == (404,) * len(cross_statuses)

    created_code, created_headers, created = _json_request(
        "POST",
        f"/api/v1/organizations/{ALPHA}/memories",
        token=tokens["admin"],
        body={
            "field": "location",
            "safe_value": "synthetic_location_a",
            "valid_from": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
    )
    assert created_code == 201 and created["version"] == 1
    memory_id = created["memory_id"]
    etag = created_headers["etag"]

    def write(value: str) -> int:
        return _json_request(
            "PATCH",
            f"/api/v1/organizations/{ALPHA}/memories/{memory_id}",
            token=tokens["admin"],
            headers={"If-Match": etag},
            body={
                "safe_value": value,
                "valid_from": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            },
        )[0]

    with ThreadPoolExecutor(max_workers=2) as executor:
        concurrent = tuple(
            executor.map(write, ("synthetic_location_b", "synthetic_location_c"))
        )
    assert sorted(concurrent) == [200, 412]

    projection_status, _, projection = _json_request(
        "GET",
        f"/api/v1/organizations/{ALPHA}/context-projection",
        token=tokens["admin"],
    )
    assert projection_status == 200 and len(projection["memory_items"]) == 1
    serialized_projection = json.dumps(projection, sort_keys=True)
    assert (
        "access_token" not in serialized_projection
        and "10000000-" not in serialized_projection
    )

    membership_status, membership_headers, _ = _json_request(
        "GET",
        f"/api/v1/organizations/{ALPHA}/memberships/{ALPHA_AUDITOR_MEMBERSHIP}",
        token=tokens["admin"],
    )
    assert membership_status == 200
    disabled_status, _, disabled = _json_request(
        "DELETE",
        f"/api/v1/organizations/{ALPHA}/memberships/{ALPHA_AUDITOR_MEMBERSHIP}",
        token=tokens["admin"],
        headers={"If-Match": membership_headers["etag"]},
    )
    assert disabled_status == 200 and disabled["status"] == "disabled"
    revoked_status, _, _ = _json_request(
        "GET", "/api/v1/identity/me", token=tokens["auditor"]
    )
    assert revoked_status == 403

    summary = {
        "schema_version": "w10-compose-smoke/1.0",
        "local_oidc_calls": 4,
        "authn_allow": 4,
        "authn_reject": 1,
        "authz_allow": 5,
        "authz_reject": 3,
        "cross_organization_reject": len(cross_statuses),
        "optimistic_success": 1,
        "optimistic_stale": 1,
        "concurrent_exactly_one_winner": True,
        "context_projection_items": 1,
        "real_identity_provider_calls": 0,
        "real_model_provider_calls": 0,
        "cost": 0,
        "validation_run": False,
        "reporting_executed": False,
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
