"""Authenticated W10 API, RBAC, isolation, and HTTP locking matrix."""

from datetime import UTC, datetime

import pytest
from conftest import TokenFactory
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from flowpilot_control_api.etag import strong_etag
from flowpilot_control_api.models import (
    Membership,
    OidcIdentity,
    Organization,
    OrganizationMemory,
    User,
)
from flowpilot_control_api.schemas import ResourceKind

ALPHA = "org_syn_alpha_0001"
BETA = "org_syn_beta_0001"
ALPHA_ADMIN = "usr_syn_alpha_admin_0001"
ALPHA_AUDITOR = "usr_syn_alpha_auditor_0001"
ALPHA_AUDITOR_MEMBERSHIP = "mbr_syn_alpha_auditor_0001"
BETA_ADMIN = "usr_syn_beta_admin_0001"
BETA_ADMIN_MEMBERSHIP = "mbr_syn_beta_admin_0001"


def _headers(token_factory: TokenFactory, *, subject: str, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_factory.issue(subject=subject, role=role)}"}


def test_authentication_required_transport_and_current_identity(
    client: TestClient, token_factory: TokenFactory, admin_headers: dict[str, str]
) -> None:
    missing = client.get("/api/v1/identity/me")
    malformed = client.get("/api/v1/identity/me", headers={"Authorization": "bearer malformed"})
    query = client.get("/api/v1/identity/me?access_token=raw", headers=admin_headers)
    valid = client.get("/api/v1/identity/me", headers=admin_headers)

    assert missing.status_code == 401
    assert malformed.status_code == 401
    assert query.status_code == 401
    assert missing.json()["code"] == "authentication_required"
    assert malformed.json()["code"] == "invalid_authentication"
    assert valid.status_code == 200
    assert valid.json()["organization_id"] == ALPHA
    assert valid.json()["role"] == "organization_admin"
    assert "token" not in valid.text.lower()
    assert "10000000-0000" not in valid.text

    mismatch = client.get(
        "/api/v1/identity/me",
        headers=_headers(
            token_factory,
            subject="10000000-0000-0000-0000-000000000001",
            role="operator",
        ),
    )
    assert mismatch.status_code == 403


def test_role_allow_and_deny_routes(client: TestClient, token_factory: TokenFactory) -> None:
    operator = _headers(
        token_factory,
        subject="10000000-0000-0000-0000-000000000002",
        role="operator",
    )
    auditor = _headers(
        token_factory,
        subject="10000000-0000-0000-0000-000000000003",
        role="auditor",
    )
    memory_payload = {
        "field": "department",
        "safe_value": "synthetic_operations",
        "valid_from": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }

    assert client.get(f"/api/v1/organizations/{ALPHA}/users", headers=operator).status_code == 200
    assert (
        client.get(f"/api/v1/organizations/{ALPHA}/memberships", headers=operator).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/organizations/{ALPHA}/memories",
            headers=operator,
            json=memory_payload,
        ).status_code
        == 201
    )
    assert (
        client.get(f"/api/v1/organizations/{ALPHA}/memberships", headers=auditor).status_code == 200
    )
    assert (
        client.post(
            f"/api/v1/organizations/{ALPHA}/memories",
            headers=auditor,
            json=memory_payload,
        ).status_code
        == 403
    )


def test_organization_user_and_membership_versions_use_strong_preconditions(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    organization = client.get(f"/api/v1/organizations/{ALPHA}", headers=admin_headers)
    assert organization.status_code == 200
    assert organization.headers["etag"].startswith('"w10-organization-')
    missing = client.patch(
        f"/api/v1/organizations/{ALPHA}",
        headers=admin_headers,
        json={"profile_code": "synthetic_alpha_updated"},
    )
    assert missing.status_code == 428
    updated = client.patch(
        f"/api/v1/organizations/{ALPHA}",
        headers={**admin_headers, "If-Match": organization.headers["etag"]},
        json={"profile_code": "synthetic_alpha_updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == organization.json()["version"] + 1
    assert (
        client.patch(
            f"/api/v1/organizations/{ALPHA}",
            headers={**admin_headers, "If-Match": organization.headers["etag"]},
            json={"profile_code": "stale_change"},
        ).status_code
        == 412
    )

    user = client.get(f"/api/v1/organizations/{ALPHA}/users/{ALPHA_AUDITOR}", headers=admin_headers)
    patched_user = client.patch(
        f"/api/v1/organizations/{ALPHA}/users/{ALPHA_AUDITOR}",
        headers={**admin_headers, "If-Match": user.headers["etag"]},
        json={"profile_code": "synthetic_auditor_updated"},
    )
    assert patched_user.status_code == 200
    assert patched_user.json()["version"] == 2

    membership = client.get(
        f"/api/v1/organizations/{ALPHA}/memberships/{ALPHA_AUDITOR_MEMBERSHIP}",
        headers=admin_headers,
    )
    patched_membership = client.patch(
        f"/api/v1/organizations/{ALPHA}/memberships/{ALPHA_AUDITOR_MEMBERSHIP}",
        headers={**admin_headers, "If-Match": membership.headers["etag"]},
        json={"role": "operator"},
    )
    assert patched_membership.status_code == 200
    assert patched_membership.json()["version"] == 2


def test_memory_etag_stale_replay_tombstone_and_reset(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    created = client.post(
        f"/api/v1/organizations/{ALPHA}/memories",
        headers=admin_headers,
        json={"field": "location", "safe_value": "location_one", "valid_from": now},
    )
    assert created.status_code == 201
    assert created.json()["version"] == 1
    memory_id = created.json()["memory_id"]
    original_etag = created.headers["etag"]

    assert (
        client.patch(
            f"/api/v1/organizations/{ALPHA}/memories/{memory_id}",
            headers={**admin_headers, "If-Match": 'W/"invalid"'},
            json={"safe_value": "location_two", "valid_from": now},
        ).status_code
        == 412
    )
    updated = client.patch(
        f"/api/v1/organizations/{ALPHA}/memories/{memory_id}",
        headers={**admin_headers, "If-Match": original_etag},
        json={"safe_value": "location_two", "valid_from": now},
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    stale = client.patch(
        f"/api/v1/organizations/{ALPHA}/memories/{memory_id}",
        headers={**admin_headers, "If-Match": original_etag},
        json={"safe_value": "stale_value", "valid_from": now},
    )
    assert stale.status_code == 412
    unchanged = client.get(
        f"/api/v1/organizations/{ALPHA}/memories/{memory_id}", headers=admin_headers
    )
    assert unchanged.json()["safe_value"] == "location_two"
    assert unchanged.json()["version"] == 2

    tombstone = client.delete(
        f"/api/v1/organizations/{ALPHA}/memories/{memory_id}",
        headers={**admin_headers, "If-Match": updated.headers["etag"]},
    )
    assert tombstone.status_code == 200
    assert tombstone.json()["status"] == "tombstone"
    assert tombstone.json()["version"] == 3

    collection = client.get(f"/api/v1/organizations/{ALPHA}/memories", headers=admin_headers)
    reset = client.post(
        f"/api/v1/organizations/{ALPHA}/memories/reset",
        headers={**admin_headers, "If-Match": collection.headers["etag"]},
    )
    assert reset.status_code == 200
    assert reset.json()["changed_count"] == 0
    assert reset.json()["memory_version"] == collection.json()["collection_version"] + 1


def test_cross_organization_matrix_is_uniform_and_side_effect_free(
    client: TestClient,
    database_engine: Engine,
    admin_headers: dict[str, str],
) -> None:
    with Session(database_engine) as session:
        before = {
            "users": session.scalar(select(func.count()).select_from(User)),
            "memberships": session.scalar(select(func.count()).select_from(Membership)),
            "memories": session.scalar(select(func.count()).select_from(OrganizationMemory)),
            "beta_status": session.scalar(select(User.status).where(User.user_id == BETA_ADMIN)),
        }
    beta_user_etag = strong_etag(ResourceKind.USER, BETA, BETA_ADMIN, 1)
    beta_membership_etag = strong_etag(ResourceKind.MEMBERSHIP, BETA, BETA_ADMIN_MEMBERSHIP, 1)
    beta_collection_etag = strong_etag(ResourceKind.MEMORY_COLLECTION, BETA, BETA, 1)
    requests = (
        client.get(f"/api/v1/organizations/{BETA}", headers=admin_headers),
        client.get(f"/api/v1/organizations/{BETA}/users", headers=admin_headers),
        client.get(f"/api/v1/organizations/{BETA}/users/count", headers=admin_headers),
        client.post(
            f"/api/v1/organizations/{BETA}/users",
            headers=admin_headers,
            json={"profile_code": "cross_org_create"},
        ),
        client.patch(
            f"/api/v1/organizations/{BETA}/users/{BETA_ADMIN}",
            headers={**admin_headers, "If-Match": beta_user_etag},
            json={"profile_code": "cross_org_update"},
        ),
        client.delete(
            f"/api/v1/organizations/{BETA}/users/{BETA_ADMIN}",
            headers={**admin_headers, "If-Match": beta_user_etag},
        ),
        client.patch(
            f"/api/v1/organizations/{BETA}/memberships/{BETA_ADMIN_MEMBERSHIP}",
            headers={**admin_headers, "If-Match": beta_membership_etag},
            json={"role": "auditor"},
        ),
        client.get(f"/api/v1/organizations/{BETA}/memories", headers=admin_headers),
        client.get(f"/api/v1/organizations/{BETA}/memories/count", headers=admin_headers),
        client.post(
            f"/api/v1/organizations/{BETA}/memories/reset",
            headers={**admin_headers, "If-Match": beta_collection_etag},
        ),
        client.get(f"/api/v1/organizations/{BETA}/context-projection", headers=admin_headers),
    )
    nonexistent = client.get(
        f"/api/v1/organizations/{ALPHA}/users/usr_nonexistent_0001",
        headers=admin_headers,
    )

    assert all(response.status_code == 404 for response in requests)
    assert all(response.json() == nonexistent.json() for response in requests)
    with Session(database_engine) as session:
        after = {
            "users": session.scalar(select(func.count()).select_from(User)),
            "memberships": session.scalar(select(func.count()).select_from(Membership)),
            "memories": session.scalar(select(func.count()).select_from(OrganizationMemory)),
            "beta_status": session.scalar(select(User.status).where(User.user_id == BETA_ADMIN)),
        }
    assert after == before

    owner_injection = client.post(
        f"/api/v1/organizations/{ALPHA}/memories",
        headers=admin_headers,
        json={
            "field": "role",
            "safe_value": "operator",
            "valid_from": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "organization_id": BETA,
            "owner_user_id": BETA_ADMIN,
        },
    )
    assert owner_injection.status_code == 422


@pytest.mark.parametrize("disabled", ("identity", "user", "membership", "organization"))
def test_disabled_authorization_fact_takes_effect_immediately(
    client: TestClient,
    database_engine: Engine,
    admin_headers: dict[str, str],
    disabled: str,
) -> None:
    statements = {
        "identity": update(OidcIdentity)
        .where(OidcIdentity.identity_id == "idn_syn_alpha_admin_0001")
        .values(status="disabled", version=OidcIdentity.version + 1),
        "user": update(User)
        .where(User.user_id == ALPHA_ADMIN)
        .values(status="disabled", version=User.version + 1),
        "membership": update(Membership)
        .where(Membership.membership_id == "mbr_syn_alpha_admin_0001")
        .values(status="disabled", version=Membership.version + 1),
        "organization": update(Organization)
        .where(Organization.organization_id == ALPHA)
        .values(status="disabled", version=Organization.version + 1),
    }
    with Session(database_engine) as session:
        session.execute(statements[disabled])
        session.commit()

    response = client.get("/api/v1/identity/me", headers=admin_headers)

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_w11_authenticated_approval_web_contract_and_one_time_claim(
    client: TestClient,
    token_factory: TokenFactory,
) -> None:
    operator = _headers(
        token_factory,
        subject="10000000-0000-0000-0000-000000000002",
        role="operator",
    )
    manager = _headers(
        token_factory,
        subject="10000000-0000-0000-0000-000000000004",
        role="operator",
    )
    admin = _headers(
        token_factory,
        subject="10000000-0000-0000-0000-000000000001",
        role="organization_admin",
    )
    current = client.get("/api/v1/approval-authorities/me", headers=manager)
    assert current.status_code == 200
    assert current.json()["roles"] == ["manager"]

    automatic = client.post(
        f"/api/v1/organizations/{ALPHA}/execution-gates",
        headers=operator,
        json={
            "task_id": "task_syn_alpha_0001",
            "step_id": "inspect_task",
            "action_type": "inspect_task",
            "parameters": {"task_reference": "task_syn_alpha_0001"},
        },
    )
    assert automatic.status_code == 200
    assert automatic.json()["status"] == "automatic"
    denied = client.post(
        f"/api/v1/organizations/{ALPHA}/execution-gates",
        headers=operator,
        json={
            "task_id": "task_syn_alpha_0001",
            "step_id": "blocked_action",
            "action_type": "unknown_action",
            "parameters": {"model_risk": "L0"},
        },
    )
    assert denied.status_code == 403 and denied.json()["code"] == "risk_denied"

    gate_body = {
        "task_id": "task_syn_alpha_0001",
        "step_id": "assign_asset",
        "action_type": "assign_asset",
        "parameters": {"employee_id": 41001, "asset_code": "asset.standard"},
    }
    waiting = client.post(
        f"/api/v1/organizations/{ALPHA}/execution-gates",
        headers=operator,
        json=gate_body,
    )
    assert waiting.status_code == 200
    assert waiting.json()["status"] == "waiting_approval"
    request_id = waiting.json()["request"]["request_id"]
    etag = waiting.headers["etag"]
    assert etag.startswith('"w11-approval-request-')

    missing = client.post(
        f"/api/v1/organizations/{ALPHA}/approval-requests/{request_id}/decisions",
        headers=manager,
        json={"decision": "approved", "reason": "policy_satisfied"},
    )
    assert missing.status_code == 428
    admin_without_authority = client.post(
        f"/api/v1/organizations/{ALPHA}/approval-requests/{request_id}/decisions",
        headers={**admin, "If-Match": etag},
        json={"decision": "approved", "reason": "policy_satisfied"},
    )
    assert admin_without_authority.status_code == 403
    approved = client.post(
        f"/api/v1/organizations/{ALPHA}/approval-requests/{request_id}/decisions",
        headers={**manager, "If-Match": etag},
        json={"decision": "approved", "reason": "policy_satisfied"},
    )
    assert approved.status_code == 200 and approved.json()["grant_issued"] is True
    assert "credential" not in approved.text.lower()
    assert "nonce" not in approved.text.lower()
    stale = client.post(
        f"/api/v1/organizations/{ALPHA}/approval-requests/{request_id}/decisions",
        headers={**manager, "If-Match": etag},
        json={"decision": "approved", "reason": "policy_satisfied"},
    )
    assert stale.status_code == 412

    claimed = client.post(
        f"/api/v1/organizations/{ALPHA}/approval-requests/{request_id}/claim",
        headers=operator,
        json=gate_body,
    )
    assert claimed.status_code == 200
    assert claimed.json()["grant_status"] == "claimed"
    replay = client.post(
        f"/api/v1/organizations/{ALPHA}/approval-requests/{request_id}/claim",
        headers=operator,
        json=gate_body,
    )
    assert replay.status_code == 409 and replay.json()["code"] == "grant_rejected"

    audit = client.get(f"/api/v1/organizations/{ALPHA}/audit-events", headers=admin)
    assert audit.status_code == 200 and audit.json()["count"] >= 9
    verified = client.post(f"/api/v1/organizations/{ALPHA}/audit-events/verify", headers=admin)
    assert verified.status_code == 200 and verified.json()["valid"] is True
    cross = client.get("/api/v1/organizations/org_syn_beta_0001/audit-events", headers=admin)
    assert cross.status_code == 404
