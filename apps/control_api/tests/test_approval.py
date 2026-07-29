"""W11 authority, request, decision, grant, and recovery boundary tests."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from flowpilot_control_api.approval import (
    GrantRejected,
    TrustedGrantVault,
    claim_grant,
    complete_execution_claim,
    create_execution_gate,
    credential_plaintext_present,
    decide_request,
    disable_authority,
    get_request,
    resume_execution_claim,
)
from flowpilot_control_api.auth import VerifiedIdentity
from flowpilot_control_api.config import OidcPolicy
from flowpilot_control_api.models import (
    ApprovalDecision,
    ApprovalGrant,
    ApprovalRequest,
    AuditEvent,
)
from flowpilot_control_api.rbac import AuthorizationDenied
from flowpilot_control_api.repository import ResourceNotFound, resolve_actor
from flowpilot_control_api.schemas import (
    ApprovalDecisionCreate,
    ApprovalDecisionValue,
    ApprovalReason,
    ApprovalRequestStatus,
    ExecutionGateRequest,
    GrantClaimRequest,
    GrantStatus,
    Role,
)

ALPHA = "org_syn_alpha_0001"
NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)


def _actor(session: Session, policy: OidcPolicy, subject_suffix: int, role: Role):
    subject = f"10000000-0000-0000-0000-{subject_suffix:012d}"
    return resolve_actor(
        session,
        VerifiedIdentity(
            issuer_id=policy.issuer_id,
            issuer_hash=hashlib.sha256(policy.issuer.encode()).hexdigest(),
            subject_hash=hashlib.sha256(subject.encode()).hexdigest(),
            claimed_role=role,
        ),
    )


def _gate(action: str = "assign_asset", parameters: dict[str, object] | None = None):
    return ExecutionGateRequest(
        task_id="task_syn_alpha_0001",
        step_id="assign_asset",
        action_type=action,
        parameters=parameters or {"employee_id": 41001, "asset_code": "asset.standard"},
    )


def _claim(gate: ExecutionGateRequest) -> GrantClaimRequest:
    return GrantClaimRequest(
        task_id=gate.task_id,
        step_id=gate.step_id,
        action_type=gate.action_type,
        parameters=gate.parameters,
    )


def _approve_l2(
    engine: Engine,
    policy: OidcPolicy,
    vault: TrustedGrantVault,
    gate: ExecutionGateRequest | None = None,
) -> str:
    gate = gate or _gate()
    with Session(engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        created = create_execution_gate(session, requester, ALPHA, gate, now=NOW)
        assert created.request is not None
        request_id = created.request.request_id
    with Session(engine) as session:
        manager = _actor(session, policy, 4, Role.OPERATOR)
        result = decide_request(
            session,
            manager,
            ALPHA,
            request_id,
            1,
            ApprovalDecisionCreate(
                decision=ApprovalDecisionValue.APPROVED,
                reason=ApprovalReason.POLICY_SATISFIED,
            ),
            now=NOW,
            vault=vault,
        )
        assert result.grant_issued
        assert result.request.status == ApprovalRequestStatus.APPROVED
    return request_id


def test_l2_self_approval_denied_then_manager_grant_claim_consume_and_recovery(
    database_engine: Engine, policy: OidcPolicy, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = TrustedGrantVault()
    gate = _gate()
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        created = create_execution_gate(session, requester, ALPHA, gate, now=NOW)
        assert created.request is not None
        request_id = created.request.request_id
        with pytest.raises(AuthorizationDenied, match="self_approval"):
            decide_request(
                session,
                requester,
                ALPHA,
                request_id,
                1,
                ApprovalDecisionCreate(
                    decision=ApprovalDecisionValue.APPROVED,
                    reason=ApprovalReason.POLICY_SATISFIED,
                ),
                now=NOW,
                vault=vault,
            )

    raw_parts = iter(("runtime-token-material", "runtime-nonce-material"))
    monkeypatch.setattr(
        "flowpilot_control_api.approval.secrets.token_urlsafe",
        lambda _: next(raw_parts),
    )
    with Session(database_engine) as session:
        manager = _actor(session, policy, 4, Role.OPERATOR)
        decided = decide_request(
            session,
            manager,
            ALPHA,
            request_id,
            1,
            ApprovalDecisionCreate(
                decision=ApprovalDecisionValue.APPROVED,
                reason=ApprovalReason.POLICY_SATISFIED,
            ),
            now=NOW,
            vault=vault,
        )
        assert decided.grant_issued and vault.size == 1
        raw = "w11.runtime-token-material.runtime-nonce-material"
        assert not credential_plaintext_present(session, raw)
        grant = session.scalar(select(ApprovalGrant).where(ApprovalGrant.request_id == request_id))
        assert grant is not None
        assert grant.token_hash == hashlib.sha256(b"runtime-token-material").hexdigest()
        assert grant.nonce_hash == hashlib.sha256(b"runtime-nonce-material").hexdigest()

    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        claim = claim_grant(
            session,
            requester,
            ALPHA,
            request_id,
            _claim(gate),
            now=NOW,
            vault=vault,
        )
        assert claim.grant_status == GrantStatus.CLAIMED
        assert vault.size == 0

    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        resumed = resume_execution_claim(
            session,
            requester,
            ALPHA,
            claim.execution_id,
            parameter_hash=claim.parameter_hash,
            authorization_hash=claim.authorization_hash,
            now=NOW,
        )
        assert resumed.execution_id == claim.execution_id
        complete_execution_claim(
            session,
            requester,
            ALPHA,
            claim.execution_id,
            receipt_reference="rcp_synthetic_0001",
            now=NOW,
        )
    with Session(database_engine) as session:
        grant = session.scalar(select(ApprovalGrant).where(ApprovalGrant.request_id == request_id))
        request = session.scalar(
            select(ApprovalRequest).where(ApprovalRequest.request_id == request_id)
        )
        assert grant is not None and grant.status == "consumed" and grant.version == 3
        assert request is not None and request.status == "consumed"
        assert session.scalar(select(func.count()).select_from(ApprovalDecision)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) >= 9


def test_l3_requires_distinct_manager_and_security_and_disabled_authority_denies(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    vault = TrustedGrantVault()
    gate = _gate("disable_employee", {"employee_id": 41001}).model_copy(
        update={"step_id": "disable_employee"}
    )
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        created = create_execution_gate(session, requester, ALPHA, gate, now=NOW)
        assert created.request is not None
        request_id = created.request.request_id
    with Session(database_engine) as session:
        manager = _actor(session, policy, 4, Role.OPERATOR)
        first = decide_request(
            session,
            manager,
            ALPHA,
            request_id,
            1,
            ApprovalDecisionCreate(
                decision=ApprovalDecisionValue.APPROVED,
                reason=ApprovalReason.POLICY_SATISFIED,
            ),
            now=NOW,
            vault=vault,
        )
        assert not first.grant_issued and first.request.status == ApprovalRequestStatus.PENDING
    with Session(database_engine) as session:
        security = _actor(session, policy, 5, Role.OPERATOR)
        second = decide_request(
            session,
            security,
            ALPHA,
            request_id,
            2,
            ApprovalDecisionCreate(
                decision=ApprovalDecisionValue.APPROVED,
                reason=ApprovalReason.POLICY_SATISFIED,
            ),
            now=NOW,
            vault=vault,
        )
        assert second.grant_issued and vault.size == 1

    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        denied_request = create_execution_gate(session, requester, ALPHA, gate, now=NOW)
        assert denied_request.request is not None
        denied_request_id = denied_request.request.request_id
    with Session(database_engine) as session:
        disabled_security = _actor(session, policy, 7, Role.OPERATOR)
        assert disabled_security.approval_authorities == ()
        with pytest.raises(AuthorizationDenied, match="approval_authority"):
            decide_request(
                session,
                disabled_security,
                ALPHA,
                denied_request_id,
                1,
                ApprovalDecisionCreate(
                    decision=ApprovalDecisionValue.APPROVED,
                    reason=ApprovalReason.POLICY_SATISFIED,
                ),
                now=NOW,
                vault=vault,
            )
        with pytest.raises(AuthorizationDenied, match="inactive_or_unknown"):
            _actor(session, policy, 6, Role.OPERATOR)


def test_parameter_change_has_no_version_or_business_side_effect_and_replay_rejects(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    vault = TrustedGrantVault()
    request_id = _approve_l2(database_engine, policy, vault)
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        with pytest.raises(GrantRejected):
            claim_grant(
                session,
                requester,
                ALPHA,
                request_id,
                _claim(_gate(parameters={"employee_id": 41001, "asset_code": "asset.changed"})),
                now=NOW,
                vault=vault,
            )
    with Session(database_engine) as session:
        grant = session.scalar(select(ApprovalGrant).where(ApprovalGrant.request_id == request_id))
        request = get_request(session, _actor(session, policy, 2, Role.OPERATOR), ALPHA, request_id)
        assert grant is not None and grant.status == "issued" and grant.version == 1
        assert request.status == "approved" and request.version == 2
        assert grant.receipt_reference is None
        with pytest.raises(GrantRejected):
            claim_grant(
                session,
                _actor(session, policy, 2, Role.OPERATOR),
                ALPHA,
                request_id,
                _claim(_gate()),
                now=NOW,
                vault=vault,
            )


def test_missing_grant_rejection_is_audited_without_business_side_effect(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    vault = TrustedGrantVault()
    gate = _gate("create_ticket", {"employee_id": 41001, "ticket_code": "ticket.standard"})
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        created = create_execution_gate(session, requester, ALPHA, gate, now=NOW)
        assert created.request is not None
        request_id = created.request.request_id
        before = session.scalar(select(func.count()).select_from(AuditEvent))
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        with pytest.raises(GrantRejected):
            claim_grant(
                session,
                requester,
                ALPHA,
                request_id,
                _claim(gate),
                now=NOW,
                vault=vault,
            )
    with Session(database_engine) as session:
        request = session.scalar(
            select(ApprovalRequest).where(ApprovalRequest.request_id == request_id)
        )
        assert request is not None and request.status == "pending" and request.version == 1
        assert session.scalar(select(func.count()).select_from(ApprovalGrant)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == before + 1


def test_waiting_request_survives_browser_and_recovery_process_loss(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    gate = _gate()
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        created = create_execution_gate(session, requester, ALPHA, gate, now=NOW)
        assert created.request is not None
        request_id = created.request.request_id

    for _simulated_process_loss in ("browser_worker", "recovery_worker"):
        with Session(database_engine) as session:
            requester = _actor(session, policy, 2, Role.OPERATOR)
            request = get_request(session, requester, ALPHA, request_id)
            assert request.status == "pending" and request.version == 1
            assert session.scalar(select(func.count()).select_from(ApprovalDecision)) == 0
            assert session.scalar(select(func.count()).select_from(ApprovalGrant)) == 0


def test_preclaim_vault_loss_fails_closed_without_receipt_or_version_change(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    request_id = _approve_l2(database_engine, policy, TrustedGrantVault())
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        with pytest.raises(GrantRejected):
            claim_grant(
                session,
                requester,
                ALPHA,
                request_id,
                _claim(_gate()),
                now=NOW,
                vault=TrustedGrantVault(),
            )
    with Session(database_engine) as session:
        grant = session.scalar(select(ApprovalGrant).where(ApprovalGrant.request_id == request_id))
        request = session.scalar(
            select(ApprovalRequest).where(ApprovalRequest.request_id == request_id)
        )
        assert grant is not None and grant.status == "issued" and grant.version == 1
        assert grant.receipt_reference is None
        assert request is not None and request.status == "approved" and request.version == 2


def test_claimed_recovery_rechecks_parameter_authority_and_receipt_replay(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    receipt_vault = TrustedGrantVault()
    receipt_request = _approve_l2(database_engine, policy, receipt_vault)
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        receipt_claim = claim_grant(
            session,
            requester,
            ALPHA,
            receipt_request,
            _claim(_gate()),
            now=NOW,
            vault=receipt_vault,
        )
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        with pytest.raises(GrantRejected):
            resume_execution_claim(
                session,
                requester,
                ALPHA,
                receipt_claim.execution_id,
                parameter_hash="f" * 64,
                authorization_hash=receipt_claim.authorization_hash,
                now=NOW,
            )
        resumed = resume_execution_claim(
            session,
            requester,
            ALPHA,
            receipt_claim.execution_id,
            parameter_hash=receipt_claim.parameter_hash,
            authorization_hash=receipt_claim.authorization_hash,
            now=NOW,
        )
        assert resumed.execution_id == receipt_claim.execution_id
        complete_execution_claim(
            session,
            requester,
            ALPHA,
            receipt_claim.execution_id,
            receipt_reference="rcp_recovery_0001",
            now=NOW,
        )
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        with pytest.raises(GrantRejected):
            complete_execution_claim(
                session,
                requester,
                ALPHA,
                receipt_claim.execution_id,
                receipt_reference="rcp_recovery_0001",
                now=NOW,
            )
        grant = session.scalar(
            select(ApprovalGrant).where(ApprovalGrant.request_id == receipt_request)
        )
        assert grant is not None and grant.status == "consumed" and grant.version == 3
        assert grant.receipt_reference == "rcp_recovery_0001"

    revoke_vault = TrustedGrantVault()
    revoke_request = _approve_l2(database_engine, policy, revoke_vault)
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        revoke_claim = claim_grant(
            session,
            requester,
            ALPHA,
            revoke_request,
            _claim(_gate()),
            now=NOW,
            vault=revoke_vault,
        )
    with Session(database_engine) as session:
        admin = _actor(session, policy, 1, Role.ORGANIZATION_ADMIN)
        disable_authority(
            session,
            admin,
            ALPHA,
            "aut_syn_alpha_manager_0001",
            1,
            now=NOW,
            vault=revoke_vault,
        )
    with Session(database_engine) as session:
        requester = _actor(session, policy, 2, Role.OPERATOR)
        with pytest.raises(GrantRejected):
            resume_execution_claim(
                session,
                requester,
                ALPHA,
                revoke_claim.execution_id,
                parameter_hash=revoke_claim.parameter_hash,
                authorization_hash=revoke_claim.authorization_hash,
                now=NOW,
            )


def test_concurrent_claim_has_exactly_one_winner_and_authority_disable_revokes(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    vault = TrustedGrantVault()
    request_id = _approve_l2(database_engine, policy, vault)

    def contender(_: int) -> str:
        with Session(database_engine) as session:
            actor = _actor(session, policy, 2, Role.OPERATOR)
            try:
                claim_grant(
                    session,
                    actor,
                    ALPHA,
                    request_id,
                    _claim(_gate()),
                    now=NOW,
                    vault=vault,
                )
            except GrantRejected:
                return "rejected"
            return "claimed"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = tuple(executor.map(contender, (1, 2)))
    assert sorted(outcomes) == ["claimed", "rejected"]

    second_vault = TrustedGrantVault()
    second_request = _approve_l2(database_engine, policy, second_vault)
    with Session(database_engine) as session:
        admin = _actor(session, policy, 1, Role.ORGANIZATION_ADMIN)
        authority = disable_authority(
            session,
            admin,
            ALPHA,
            "aut_syn_alpha_manager_0001",
            1,
            now=NOW,
            vault=second_vault,
        )
        assert authority.status == "disabled" and second_vault.size == 0
    with Session(database_engine) as session:
        grant = session.scalar(
            select(ApprovalGrant).where(ApprovalGrant.request_id == second_request)
        )
        request = session.scalar(
            select(ApprovalRequest).where(ApprovalRequest.request_id == second_request)
        )
        assert grant is not None and grant.status == "revoked"
        assert request is not None and request.status == "invalidated"
        with pytest.raises(ResourceNotFound):
            get_request(
                session,
                _actor(session, policy, 2, Role.OPERATOR),
                "org_syn_beta_0001",
                second_request,
            )
