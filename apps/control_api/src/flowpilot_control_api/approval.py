"""W11 organization-qualified approval state and one-time execution grants."""

import hashlib
import secrets
import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot_control_api.audit import append_audit_event
from flowpilot_control_api.etag import PreconditionFailed
from flowpilot_control_api.models import (
    ApprovalAuthority,
    ApprovalDecision,
    ApprovalGrant,
    ApprovalRequest,
    Membership,
    Organization,
    ProductionRun,
    User,
)
from flowpilot_control_api.rbac import AuthorizationDenied
from flowpilot_control_api.repository import ResourceConflict, ResourceNotFound
from flowpilot_control_api.risk import RiskFacts, RiskSchemaRejected, evaluate_risk
from flowpilot_control_api.schemas import (
    ActorContext,
    ApprovalAuthorityCreate,
    ApprovalAuthorityRead,
    ApprovalAuthorityStatus,
    ApprovalDecisionCreate,
    ApprovalDecisionRead,
    ApprovalDecisionResult,
    ApprovalDecisionValue,
    ApprovalReason,
    ApprovalRequestRead,
    ApprovalRequestStatus,
    ApprovalRole,
    AuditEventType,
    ExecutionClaimRead,
    ExecutionGateRequest,
    ExecutionGateResponse,
    ExecutionGateStatus,
    GrantClaimRequest,
    GrantStatus,
    RiskLevel,
    Role,
    canonical_json_bytes,
    stable_hash,
)

REQUEST_TTL = timedelta(minutes=10)
GRANT_TTL = timedelta(minutes=2)


class ApprovalStateConflict(RuntimeError):
    pass


class RiskDenied(RuntimeError):
    pass


class GrantRejected(RuntimeError):
    pass


class TrustedGrantVault:
    """Bounded process-memory handoff; raw values never cross the Web API."""

    def __init__(self, capacity: int = 64) -> None:
        if not 1 <= capacity <= 256:
            raise ValueError("trusted grant vault capacity is outside the W11 bound")
        self._capacity = capacity
        self._values: dict[str, str] = {}
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return f"TrustedGrantVault(capacity={self._capacity}, entries={self.size})"

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._values)

    def put(self, grant_id: str, credential: str) -> None:
        with self._lock:
            if grant_id in self._values or len(self._values) >= self._capacity:
                raise ApprovalStateConflict("trusted grant vault is unavailable")
            self._values[grant_id] = credential

    def take(self, grant_id: str) -> str | None:
        with self._lock:
            return self._values.pop(grant_id, None)

    def peek(self, grant_id: str) -> str | None:
        with self._lock:
            return self._values.get(grant_id)

    def discard(self, grant_id: str) -> None:
        with self._lock:
            self._values.pop(grant_id, None)


def _opaque_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(16)}"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_actor_organization(actor: ActorContext, organization_id: str) -> None:
    if actor.organization_id != organization_id:
        raise ResourceNotFound("resource_not_found")


def authority_read(record: ApprovalAuthority) -> ApprovalAuthorityRead:
    return ApprovalAuthorityRead(
        authority_id=record.authority_id,
        organization_id=record.organization_id,
        user_id=record.user_id,
        role=ApprovalRole(record.role),
        status=ApprovalAuthorityStatus(record.status),
        version=record.version,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def request_read(record: ApprovalRequest) -> ApprovalRequestRead:
    return ApprovalRequestRead(
        request_id=record.request_id,
        organization_id=record.organization_id,
        task_id=record.task_id,
        step_id=record.step_id,
        action_type=record.action_type,
        parameter_hash=record.parameter_hash,
        risk_level=RiskLevel(record.risk_level),
        requester_user_id=record.requester_user_id,
        executor_user_id=record.executor_user_id,
        required_roles=tuple(ApprovalRole(item) for item in record.required_roles.split(",")),
        status=ApprovalRequestStatus(record.status),
        version=record.version,
        expires_at=record.expires_at,
        closed_reason=ApprovalReason(record.closed_reason) if record.closed_reason else None,
        audit_sequence=record.audit_sequence,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def decision_read(record: ApprovalDecision) -> ApprovalDecisionRead:
    return ApprovalDecisionRead(
        decision_id=record.decision_id,
        organization_id=record.organization_id,
        request_id=record.request_id,
        decision=ApprovalDecisionValue(record.decision),
        approver_user_id=record.approver_user_id,
        authority_id=record.authority_id,
        approval_role=ApprovalRole(record.approval_role),
        request_version=record.request_version,
        action_type=record.action_type,
        parameter_hash=record.parameter_hash,
        reason=ApprovalReason(record.reason),
        audit_sequence=record.audit_sequence,
        created_at=record.created_at,
    )


def list_authorities(
    session: Session, actor: ActorContext, organization_id: str
) -> list[ApprovalAuthority]:
    _require_actor_organization(actor, organization_id)
    return list(
        session.scalars(
            select(ApprovalAuthority)
            .where(ApprovalAuthority.organization_id == organization_id)
            .order_by(ApprovalAuthority.role, ApprovalAuthority.authority_id)
            .limit(100)
        )
    )


def get_authority(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    authority_id: str,
) -> ApprovalAuthority:
    _require_actor_organization(actor, organization_id)
    record = session.scalar(
        select(ApprovalAuthority).where(
            ApprovalAuthority.organization_id == organization_id,
            ApprovalAuthority.authority_id == authority_id,
        )
    )
    if record is None:
        raise ResourceNotFound("resource_not_found")
    return record


def create_authority(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    payload: ApprovalAuthorityCreate,
) -> ApprovalAuthority:
    _require_actor_organization(actor, organization_id)
    user = session.scalar(
        select(User).where(
            User.organization_id == organization_id,
            User.user_id == payload.user_id,
        )
    )
    if user is None:
        raise ResourceNotFound("resource_not_found")
    record = ApprovalAuthority(
        authority_id=_opaque_id("aut"),
        organization_id=organization_id,
        user_id=payload.user_id,
        role=payload.role.value,
        status="active",
        version=1,
    )
    session.add(record)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ResourceConflict("conflict") from exc
    session.refresh(record)
    return record


def disable_authority(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    authority_id: str,
    expected_version: int,
    *,
    now: datetime,
    vault: TrustedGrantVault,
) -> ApprovalAuthority:
    _require_actor_organization(actor, organization_id)
    now = _utc(now)
    exists = session.scalar(
        select(ApprovalAuthority.authority_id).where(
            ApprovalAuthority.organization_id == organization_id,
            ApprovalAuthority.authority_id == authority_id,
        )
    )
    if exists is None:
        raise ResourceNotFound("resource_not_found")
    record = session.scalars(
        update(ApprovalAuthority)
        .where(
            ApprovalAuthority.organization_id == organization_id,
            ApprovalAuthority.authority_id == authority_id,
            ApprovalAuthority.version == expected_version,
            ApprovalAuthority.status == "active",
        )
        .values(status="disabled", version=ApprovalAuthority.version + 1, updated_at=now)
        .returning(ApprovalAuthority)
        .execution_options(synchronize_session=False)
    ).one_or_none()
    if record is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    affected = list(
        session.scalars(
            select(ApprovalGrant)
            .join(
                ApprovalDecision,
                and_(
                    ApprovalDecision.organization_id == ApprovalGrant.organization_id,
                    ApprovalDecision.request_id == ApprovalGrant.request_id,
                ),
            )
            .where(
                ApprovalGrant.organization_id == organization_id,
                ApprovalGrant.status == "issued",
                ApprovalDecision.authority_id == authority_id,
            )
            .with_for_update()
        )
    )
    for grant in affected:
        grant.status = "revoked"
        grant.version += 1
        grant.updated_at = now
        request = session.scalar(
            select(ApprovalRequest).where(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.request_id == grant.request_id,
            )
        )
        if request is not None and request.status == "approved":
            request.status = "invalidated"
            request.closed_reason = ApprovalReason.AUTHORITY_INACTIVE.value
            request.version += 1
            request.updated_at = now
            event = append_audit_event(
                session,
                organization_id=organization_id,
                event_type=AuditEventType.REQUEST_INVALIDATED,
                actor_reference=actor.authorization_hash,
                subject_reference=request.request_id,
                payload={
                    "schema_version": "w11-audit-payload/1.0",
                    "request_id": request.request_id,
                    "request_status": request.status,
                    "reason": ApprovalReason.AUTHORITY_INACTIVE.value,
                    "version": request.version,
                },
                now=now,
            )
            request.audit_sequence = event.sequence
    append_audit_event(
        session,
        organization_id=organization_id,
        event_type=AuditEventType.AUTHORITY_DISABLED,
        actor_reference=actor.authorization_hash,
        subject_reference=authority_id,
        payload={
            "schema_version": "w11-audit-payload/1.0",
            "authority_id": authority_id,
            "approval_role": record.role,
            "version": record.version,
        },
        now=now,
    )
    session.commit()
    for grant in affected:
        vault.discard(grant.grant_id)
    return record


def _risk_facts(
    session: Session,
    organization_id: str,
    action_type: str,
    parameters: dict[str, object],
) -> RiskFacts:
    if action_type != "create_account":
        return RiskFacts()
    target_user_id = parameters.get("target_user_id")
    if not isinstance(target_user_id, str):
        return RiskFacts()
    role = session.scalar(
        select(Membership.role)
        .join(
            User,
            and_(
                User.organization_id == Membership.organization_id,
                User.user_id == Membership.user_id,
            ),
        )
        .where(
            Membership.organization_id == organization_id,
            Membership.user_id == target_user_id,
            Membership.status == "active",
            User.status == "active",
        )
    )
    return RiskFacts(target_is_organization_administrator=role == Role.ORGANIZATION_ADMIN.value)


def create_execution_gate(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    payload: ExecutionGateRequest,
    *,
    now: datetime,
) -> ExecutionGateResponse:
    _require_actor_organization(actor, organization_id)
    now = _utc(now)
    evaluation = evaluate_risk(
        payload.action_type,
        payload.parameters,
        _risk_facts(session, organization_id, payload.action_type, payload.parameters),
    )
    append_audit_event(
        session,
        organization_id=organization_id,
        event_type=AuditEventType.RISK_CLASSIFIED,
        actor_reference=actor.authorization_hash,
        subject_reference=payload.action_type,
        payload={
            "schema_version": "w11-audit-payload/1.0",
            "action_type": payload.action_type,
            "risk_level": evaluation.risk_level.value,
            "parameter_hash": evaluation.parameter_hash,
        },
        now=now,
    )
    if evaluation.risk_level == RiskLevel.L4:
        append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.L4_DENIED,
            actor_reference=actor.authorization_hash,
            subject_reference=payload.action_type,
            payload={
                "schema_version": "w11-audit-payload/1.0",
                "action_type": payload.action_type,
                "risk_level": RiskLevel.L4.value,
                "parameter_hash": evaluation.parameter_hash,
                "reason": "permanently_denied",
                "http_status": 403,
            },
            now=now,
        )
        session.commit()
        raise RiskDenied("risk_denied")
    if evaluation.risk_level in {RiskLevel.L0, RiskLevel.L1}:
        append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.EXECUTION_STARTED,
            actor_reference=actor.authorization_hash,
            subject_reference=payload.action_type,
            payload={
                "schema_version": "w11-audit-payload/1.0",
                "action_type": payload.action_type,
                "risk_level": evaluation.risk_level.value,
                "parameter_hash": evaluation.parameter_hash,
            },
            now=now,
        )
        completed = append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.EXECUTION_SUCCEEDED,
            actor_reference=actor.authorization_hash,
            subject_reference=payload.action_type,
            payload={
                "schema_version": "w11-audit-payload/1.0",
                "action_type": payload.action_type,
                "risk_level": evaluation.risk_level.value,
                "parameter_hash": evaluation.parameter_hash,
            },
            now=now,
        )
        session.commit()
        return ExecutionGateResponse(
            status=ExecutionGateStatus.AUTOMATIC,
            risk_level=evaluation.risk_level,
            action_type=payload.action_type,
            parameter_hash=evaluation.parameter_hash,
            audit_sequence=completed.sequence,
        )
    request_id = _opaque_id("apr")
    requested = append_audit_event(
        session,
        organization_id=organization_id,
        event_type=AuditEventType.APPROVAL_REQUESTED,
        actor_reference=actor.authorization_hash,
        subject_reference=request_id,
        payload={
            "schema_version": "w11-audit-payload/1.0",
            "action_type": payload.action_type,
            "risk_level": evaluation.risk_level.value,
            "parameter_hash": evaluation.parameter_hash,
            "request_id": request_id,
            "request_status": ApprovalRequestStatus.PENDING.value,
            "version": 1,
        },
        now=now,
    )
    request = ApprovalRequest(
        request_id=request_id,
        organization_id=organization_id,
        task_id=payload.task_id,
        step_id=payload.step_id,
        action_type=payload.action_type,
        parameter_hash=evaluation.parameter_hash,
        risk_level=evaluation.risk_level.value,
        requester_user_id=actor.user_id,
        executor_user_id=actor.user_id,
        required_roles=",".join(role.value for role in evaluation.required_roles),
        status=ApprovalRequestStatus.PENDING.value,
        version=1,
        expires_at=now + REQUEST_TTL,
        closed_reason=None,
        audit_sequence=requested.sequence,
        created_at=now,
        updated_at=now,
    )
    session.add(request)
    session.commit()
    session.refresh(request)
    return ExecutionGateResponse(
        status=ExecutionGateStatus.WAITING_APPROVAL,
        risk_level=evaluation.risk_level,
        action_type=payload.action_type,
        parameter_hash=evaluation.parameter_hash,
        request=request_read(request),
        audit_sequence=requested.sequence,
    )


def list_requests(
    session: Session, actor: ActorContext, organization_id: str
) -> list[ApprovalRequest]:
    _require_actor_organization(actor, organization_id)
    return list(
        session.scalars(
            select(ApprovalRequest)
            .where(ApprovalRequest.organization_id == organization_id)
            .order_by(ApprovalRequest.created_at, ApprovalRequest.request_id)
            .limit(100)
        )
    )


def get_request(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    request_id: str,
) -> ApprovalRequest:
    _require_actor_organization(actor, organization_id)
    record = session.scalar(
        select(ApprovalRequest).where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.request_id == request_id,
        )
    )
    if record is None:
        raise ResourceNotFound("resource_not_found")
    return record


def _current_actor_authorities(
    session: Session,
    actor: ActorContext,
    required: set[ApprovalRole],
) -> list[ApprovalAuthority]:
    if actor.role == Role.AUDITOR:
        return []
    return list(
        session.scalars(
            select(ApprovalAuthority)
            .join(
                User,
                and_(
                    User.organization_id == ApprovalAuthority.organization_id,
                    User.user_id == ApprovalAuthority.user_id,
                ),
            )
            .join(
                Membership,
                and_(
                    Membership.organization_id == User.organization_id,
                    Membership.user_id == User.user_id,
                ),
            )
            .join(Organization, Organization.organization_id == User.organization_id)
            .where(
                ApprovalAuthority.organization_id == actor.organization_id,
                ApprovalAuthority.user_id == actor.user_id,
                ApprovalAuthority.status == "active",
                ApprovalAuthority.role.in_(role.value for role in required),
                User.status == "active",
                Membership.status == "active",
                Membership.role != Role.AUDITOR.value,
                Organization.status == "active",
            )
            .order_by(ApprovalAuthority.role, ApprovalAuthority.authority_id)
        )
    )


def _approved_decisions(
    session: Session, organization_id: str, request_id: str
) -> list[ApprovalDecision]:
    return list(
        session.scalars(
            select(ApprovalDecision)
            .where(
                ApprovalDecision.organization_id == organization_id,
                ApprovalDecision.request_id == request_id,
                ApprovalDecision.decision == ApprovalDecisionValue.APPROVED.value,
            )
            .order_by(ApprovalDecision.approval_role, ApprovalDecision.decision_id)
        )
    )


def _approval_set_hash(
    session: Session, organization_id: str, decisions: list[ApprovalDecision]
) -> str:
    items: list[dict[str, object]] = []
    for decision in decisions:
        authority = session.scalar(
            select(ApprovalAuthority).where(
                ApprovalAuthority.organization_id == organization_id,
                ApprovalAuthority.authority_id == decision.authority_id,
            )
        )
        if authority is None:
            raise ApprovalStateConflict("approval authority disappeared")
        items.append(
            {
                "decision_id": decision.decision_id,
                "approver_user_id": decision.approver_user_id,
                "authority_id": decision.authority_id,
                "approval_role": decision.approval_role,
                "authority_version": authority.version,
            }
        )
    return stable_hash(
        {
            "schema_version": "w11-required-approval-set/1.0",
            "approvals": sorted(items, key=lambda item: str(item["approval_role"])),
        }
    )


def _new_credential() -> tuple[str, str, str]:
    token = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(18)
    return (
        f"w11.{token}.{nonce}",
        hashlib.sha256(token.encode()).hexdigest(),
        hashlib.sha256(nonce.encode()).hexdigest(),
    )


def decide_request(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    request_id: str,
    expected_version: int,
    payload: ApprovalDecisionCreate,
    *,
    now: datetime,
    vault: TrustedGrantVault,
) -> ApprovalDecisionResult:
    _require_actor_organization(actor, organization_id)
    now = _utc(now)
    exists = session.scalar(
        select(ApprovalRequest.request_id).where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.request_id == request_id,
        )
    )
    if exists is None:
        raise ResourceNotFound("resource_not_found")
    request = session.scalars(
        update(ApprovalRequest)
        .where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.request_id == request_id,
            ApprovalRequest.version == expected_version,
            ApprovalRequest.status == ApprovalRequestStatus.PENDING.value,
        )
        .values(version=ApprovalRequest.version + 1, updated_at=now)
        .returning(ApprovalRequest)
        .execution_options(synchronize_session=False)
    ).one_or_none()
    if request is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    if _utc(request.expires_at) <= now:
        request.status = ApprovalRequestStatus.EXPIRED.value
        request.closed_reason = ApprovalReason.REQUEST_EXPIRED.value
        event = append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.REQUEST_EXPIRED,
            actor_reference=actor.authorization_hash,
            subject_reference=request_id,
            payload={
                "schema_version": "w11-audit-payload/1.0",
                "request_id": request_id,
                "request_status": request.status,
                "reason": request.closed_reason,
                "version": request.version,
            },
            now=now,
        )
        request.audit_sequence = event.sequence
        session.commit()
        raise ApprovalStateConflict("approval request expired")
    if actor.user_id in {request.requester_user_id, request.executor_user_id}:
        session.rollback()
        raise AuthorizationDenied("self_approval_denied")
    required = {ApprovalRole(item) for item in request.required_roles.split(",")}
    prior = list(
        session.scalars(
            select(ApprovalDecision).where(
                ApprovalDecision.organization_id == organization_id,
                ApprovalDecision.request_id == request_id,
            )
        )
    )
    if any(item.approver_user_id == actor.user_id for item in prior):
        session.rollback()
        raise ApprovalStateConflict("duplicate decision")
    decided_roles = {ApprovalRole(item.approval_role) for item in prior}
    authorities = _current_actor_authorities(session, actor, required - decided_roles)
    if len(authorities) != 1:
        session.rollback()
        raise AuthorizationDenied("approval_authority_denied")
    authority = authorities[0]
    approval_role = ApprovalRole(authority.role)
    decision_id = _opaque_id("dec")
    decision_event_type = (
        AuditEventType.APPROVAL_APPROVED
        if payload.decision == ApprovalDecisionValue.APPROVED
        else AuditEventType.APPROVAL_REJECTED
    )
    event = append_audit_event(
        session,
        organization_id=organization_id,
        event_type=decision_event_type,
        actor_reference=actor.authorization_hash,
        subject_reference=request_id,
        payload={
            "schema_version": "w11-audit-payload/1.0",
            "request_id": request_id,
            "decision_id": decision_id,
            "authority_id": authority.authority_id,
            "approval_role": approval_role.value,
            "action_type": request.action_type,
            "parameter_hash": request.parameter_hash,
            "reason": payload.reason.value,
            "version": expected_version,
        },
        now=now,
    )
    decision = ApprovalDecision(
        decision_id=decision_id,
        organization_id=organization_id,
        request_id=request_id,
        decision=payload.decision.value,
        approver_user_id=actor.user_id,
        authority_id=authority.authority_id,
        approval_role=approval_role.value,
        request_version=expected_version,
        action_type=request.action_type,
        parameter_hash=request.parameter_hash,
        reason=payload.reason.value,
        audit_sequence=event.sequence,
        created_at=now,
    )
    session.add(decision)
    request.audit_sequence = event.sequence
    grant: ApprovalGrant | None = None
    raw_credential: str | None = None
    if payload.decision == ApprovalDecisionValue.REJECTED:
        request.status = ApprovalRequestStatus.REJECTED.value
        request.closed_reason = payload.reason.value
    else:
        approved_roles = {
            ApprovalRole(item.approval_role)
            for item in prior
            if item.decision == ApprovalDecisionValue.APPROVED.value
        } | {approval_role}
        if approved_roles == required:
            request.status = ApprovalRequestStatus.APPROVED.value
            session.flush()
            decisions = _approved_decisions(session, organization_id, request_id)
            set_hash = _approval_set_hash(session, organization_id, decisions)
            raw_credential, token_hash, nonce_hash = _new_credential()
            grant = ApprovalGrant(
                grant_id=_opaque_id("grt"),
                organization_id=organization_id,
                request_id=request_id,
                task_id=request.task_id,
                step_id=request.step_id,
                action_type=request.action_type,
                parameter_hash=request.parameter_hash,
                risk_level=request.risk_level,
                approval_set_hash=set_hash,
                executor_user_id=request.executor_user_id,
                token_hash=token_hash,
                nonce_hash=nonce_hash,
                status=GrantStatus.ISSUED.value,
                version=1,
                expires_at=min(_utc(request.expires_at), now + GRANT_TTL),
                created_at=now,
                updated_at=now,
            )
            session.add(grant)
            issued = append_audit_event(
                session,
                organization_id=organization_id,
                event_type=AuditEventType.GRANT_ISSUED,
                actor_reference=actor.authorization_hash,
                subject_reference=grant.grant_id,
                payload={
                    "schema_version": "w11-audit-payload/1.0",
                    "request_id": request_id,
                    "grant_id": grant.grant_id,
                    "grant_status": grant.status,
                    "risk_level": request.risk_level,
                    "parameter_hash": request.parameter_hash,
                    "version": grant.version,
                },
                now=now,
            )
            request.audit_sequence = issued.sequence
    if grant is not None and raw_credential is not None:
        vault.put(grant.grant_id, raw_credential)
    try:
        session.commit()
    except Exception:
        session.rollback()
        if grant is not None:
            vault.discard(grant.grant_id)
        raise
    session.refresh(decision)
    session.refresh(request)
    return ApprovalDecisionResult(
        decision=decision_read(decision),
        request=request_read(request),
        grant_issued=grant is not None,
    )


def close_request(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    request_id: str,
    expected_version: int,
    *,
    reason: ApprovalReason,
    invalidate: bool,
    now: datetime,
    vault: TrustedGrantVault,
) -> ApprovalRequest:
    _require_actor_organization(actor, organization_id)
    now = _utc(now)
    current = session.scalar(
        select(ApprovalRequest).where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.request_id == request_id,
        )
    )
    if current is None:
        raise ResourceNotFound("resource_not_found")
    if (
        not invalidate
        and actor.role != Role.ORGANIZATION_ADMIN
        and (current.requester_user_id != actor.user_id)
    ):
        raise AuthorizationDenied("request_cancel_denied")
    target_status = (
        ApprovalRequestStatus.INVALIDATED if invalidate else ApprovalRequestStatus.CANCELLED
    )
    event_type = (
        AuditEventType.REQUEST_INVALIDATED if invalidate else AuditEventType.REQUEST_CANCELLED
    )
    record = session.scalars(
        update(ApprovalRequest)
        .where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.request_id == request_id,
            ApprovalRequest.version == expected_version,
            ApprovalRequest.status.in_(("pending", "approved")),
        )
        .values(
            status=target_status.value,
            closed_reason=reason.value,
            version=ApprovalRequest.version + 1,
            updated_at=now,
        )
        .returning(ApprovalRequest)
        .execution_options(synchronize_session=False)
    ).one_or_none()
    if record is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    event = append_audit_event(
        session,
        organization_id=organization_id,
        event_type=event_type,
        actor_reference=actor.authorization_hash,
        subject_reference=request_id,
        payload={
            "schema_version": "w11-audit-payload/1.0",
            "request_id": request_id,
            "request_status": record.status,
            "reason": reason.value,
            "version": record.version,
        },
        now=now,
    )
    record.audit_sequence = event.sequence
    grants = list(
        session.scalars(
            select(ApprovalGrant).where(
                ApprovalGrant.organization_id == organization_id,
                ApprovalGrant.request_id == request_id,
                ApprovalGrant.status == GrantStatus.ISSUED.value,
            )
        )
    )
    for grant in grants:
        grant.status = GrantStatus.REVOKED.value
        grant.version += 1
        grant.updated_at = now
    session.commit()
    for grant in grants:
        vault.discard(grant.grant_id)
    return record


def _parse_credential(credential: str) -> tuple[str, str]:
    parts = credential.split(".")
    if len(parts) != 3 or parts[0] != "w11" or not parts[1] or not parts[2]:
        raise GrantRejected("grant_rejected")
    return (
        hashlib.sha256(parts[1].encode()).hexdigest(),
        hashlib.sha256(parts[2].encode()).hexdigest(),
    )


def _active_approval_set(
    session: Session, request: ApprovalRequest
) -> tuple[list[ApprovalDecision], str]:
    decisions = _approved_decisions(session, request.organization_id, request.request_id)
    required = set(request.required_roles.split(","))
    if {item.approval_role for item in decisions} != required:
        raise GrantRejected("grant_rejected")
    if len({item.approver_user_id for item in decisions}) != len(decisions):
        raise GrantRejected("grant_rejected")
    for decision in decisions:
        active = session.scalar(
            select(ApprovalAuthority.authority_id)
            .join(
                User,
                and_(
                    User.organization_id == ApprovalAuthority.organization_id,
                    User.user_id == ApprovalAuthority.user_id,
                ),
            )
            .join(
                Membership,
                and_(
                    Membership.organization_id == User.organization_id,
                    Membership.user_id == User.user_id,
                ),
            )
            .join(Organization, Organization.organization_id == User.organization_id)
            .where(
                ApprovalAuthority.organization_id == request.organization_id,
                ApprovalAuthority.authority_id == decision.authority_id,
                ApprovalAuthority.user_id == decision.approver_user_id,
                ApprovalAuthority.role == decision.approval_role,
                ApprovalAuthority.status == "active",
                User.status == "active",
                Membership.status == "active",
                Membership.role != Role.AUDITOR.value,
                Organization.status == "active",
            )
        )
        if active is None:
            raise GrantRejected("grant_rejected")
    return decisions, _approval_set_hash(session, request.organization_id, decisions)


def claim_grant(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    request_id: str,
    payload: GrantClaimRequest,
    *,
    now: datetime,
    vault: TrustedGrantVault,
    on_claim: Callable[[ApprovalRequest, ApprovalGrant, ExecutionClaimRead], None] | None = None,
) -> ExecutionClaimRead:
    _require_actor_organization(actor, organization_id)
    now = _utc(now)
    request = session.scalar(
        select(ApprovalRequest).where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.request_id == request_id,
        )
    )
    grant = session.scalar(
        select(ApprovalGrant).where(
            ApprovalGrant.organization_id == organization_id,
            ApprovalGrant.request_id == request_id,
        )
    )
    if request is None or grant is None or actor.user_id != request.executor_user_id:
        subject_reference = grant.grant_id if grant is not None else request_id
        rejection_payload: dict[str, object] = {
            "schema_version": "w11-audit-payload/1.0",
            "request_id": request_id,
            "reason": "grant_rejected",
            "http_status": 409,
        }
        if grant is not None:
            rejection_payload.update(
                {
                    "grant_id": grant.grant_id,
                    "grant_status": grant.status,
                    "parameter_hash": grant.parameter_hash,
                }
            )
        append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.GRANT_REJECTED,
            actor_reference=actor.authorization_hash,
            subject_reference=subject_reference,
            payload=rejection_payload,
            now=now,
        )
        session.commit()
        raise GrantRejected("grant_rejected")
    production_run = session.scalar(
        select(ProductionRun.run_id).where(
            ProductionRun.organization_id == organization_id,
            ProductionRun.approval_request_id == request_id,
        )
    )
    if production_run is not None and on_claim is None:
        append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.GRANT_REJECTED,
            actor_reference=actor.authorization_hash,
            subject_reference=grant.grant_id,
            payload={
                "schema_version": "w11-audit-payload/1.0",
                "request_id": request_id,
                "grant_id": grant.grant_id,
                "grant_status": grant.status,
                "parameter_hash": grant.parameter_hash,
                "reason": "grant_rejected",
                "http_status": 409,
            },
            now=now,
        )
        session.commit()
        raise GrantRejected("grant_rejected")
    try:
        credential = vault.peek(grant.grant_id)
        if credential is None:
            raise GrantRejected("grant_rejected")
        token_hash, nonce_hash = _parse_credential(credential)
        evaluation = evaluate_risk(
            payload.action_type,
            payload.parameters,
            _risk_facts(session, organization_id, payload.action_type, payload.parameters),
        )
        decisions, approval_set_hash = _active_approval_set(session, request)
        if (
            request.status != ApprovalRequestStatus.APPROVED.value
            or grant.status != GrantStatus.ISSUED.value
            or _utc(request.expires_at) <= now
            or _utc(grant.expires_at) <= now
            or payload.task_id != request.task_id
            or payload.step_id != request.step_id
            or payload.action_type != request.action_type
            or evaluation.parameter_hash != request.parameter_hash
            or evaluation.risk_level.value != request.risk_level
            or grant.task_id != request.task_id
            or grant.step_id != request.step_id
            or grant.action_type != request.action_type
            or grant.parameter_hash != request.parameter_hash
            or grant.approval_set_hash != approval_set_hash
            or grant.token_hash != token_hash
            or grant.nonce_hash != nonce_hash
            or len(decisions) != len(request.required_roles.split(","))
        ):
            raise GrantRejected("grant_rejected")
        execution_id = _opaque_id("exe")
        claimed = session.scalars(
            update(ApprovalGrant)
            .where(
                ApprovalGrant.organization_id == organization_id,
                ApprovalGrant.grant_id == grant.grant_id,
                ApprovalGrant.status == GrantStatus.ISSUED.value,
                ApprovalGrant.version == grant.version,
                ApprovalGrant.expires_at > now,
            )
            .values(
                status=GrantStatus.CLAIMED.value,
                version=ApprovalGrant.version + 1,
                execution_id=execution_id,
                authorization_hash=actor.authorization_hash,
                claimed_at=now,
                updated_at=now,
            )
            .returning(ApprovalGrant)
            .execution_options(synchronize_session=False)
        ).one_or_none()
        if claimed is None:
            raise GrantRejected("grant_rejected")
        request.status = ApprovalRequestStatus.CLAIMED.value
        request.version += 1
        request.updated_at = now
        claimed_event = append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.GRANT_CLAIMED,
            actor_reference=actor.authorization_hash,
            subject_reference=claimed.grant_id,
            payload={
                "schema_version": "w11-audit-payload/1.0",
                "request_id": request_id,
                "grant_id": claimed.grant_id,
                "grant_status": claimed.status,
                "execution_id": execution_id,
                "parameter_hash": request.parameter_hash,
                "authorization_hash": actor.authorization_hash,
                "version": claimed.version,
            },
            now=now,
        )
        append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.EXECUTION_STARTED,
            actor_reference=actor.authorization_hash,
            subject_reference=execution_id,
            payload={
                "schema_version": "w11-audit-payload/1.0",
                "request_id": request_id,
                "grant_id": claimed.grant_id,
                "execution_id": execution_id,
                "action_type": request.action_type,
                "parameter_hash": request.parameter_hash,
            },
            now=now,
        )
        request.audit_sequence = claimed_event.sequence
        claim_read = ExecutionClaimRead(
            execution_id=execution_id,
            grant_id=claimed.grant_id,
            request_id=request_id,
            organization_id=organization_id,
            task_id=request.task_id,
            step_id=request.step_id,
            action_type=request.action_type,
            parameter_hash=request.parameter_hash,
            authorization_hash=actor.authorization_hash,
            grant_status=GrantStatus.CLAIMED,
            grant_version=claimed.version,
            claimed_at=now,
        )
        if on_claim is not None:
            on_claim(request, claimed, claim_read)
        session.commit()
        vault.discard(claimed.grant_id)
        return claim_read
    except (GrantRejected, RiskSchemaRejected):
        session.rollback()
        vault.discard(grant.grant_id)
        try:
            append_audit_event(
                session,
                organization_id=organization_id,
                event_type=AuditEventType.GRANT_REJECTED,
                actor_reference=actor.authorization_hash,
                subject_reference=grant.grant_id,
                payload={
                    "schema_version": "w11-audit-payload/1.0",
                    "request_id": request_id,
                    "grant_id": grant.grant_id,
                    "grant_status": grant.status,
                    "parameter_hash": grant.parameter_hash,
                    "reason": "grant_rejected",
                    "http_status": 409,
                },
                now=now,
            )
            session.commit()
        except Exception:
            session.rollback()
        raise
    except Exception:
        session.rollback()
        raise


def resume_execution_claim(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    execution_id: str,
    *,
    parameter_hash: str,
    authorization_hash: str,
    now: datetime,
) -> ExecutionClaimRead:
    _require_actor_organization(actor, organization_id)
    grant = session.scalar(
        select(ApprovalGrant).where(
            ApprovalGrant.organization_id == organization_id,
            ApprovalGrant.execution_id == execution_id,
            ApprovalGrant.status == GrantStatus.CLAIMED.value,
        )
    )
    if (
        grant is None
        or grant.executor_user_id != actor.user_id
        or grant.parameter_hash != parameter_hash
        or grant.authorization_hash != authorization_hash
        or actor.authorization_hash != authorization_hash
        or grant.claimed_at is None
    ):
        raise GrantRejected("grant_rejected")
    request = session.scalar(
        select(ApprovalRequest).where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.request_id == grant.request_id,
            ApprovalRequest.status == ApprovalRequestStatus.CLAIMED.value,
        )
    )
    if request is None:
        raise GrantRejected("grant_rejected")
    _active_approval_set(session, request)
    now = _utc(now)
    append_audit_event(
        session,
        organization_id=organization_id,
        event_type=AuditEventType.RECOVERY_RESUMED,
        actor_reference=actor.authorization_hash,
        subject_reference=execution_id,
        payload={
            "schema_version": "w11-audit-payload/1.0",
            "request_id": request.request_id,
            "grant_id": grant.grant_id,
            "execution_id": execution_id,
            "parameter_hash": parameter_hash,
            "authorization_hash": authorization_hash,
        },
        now=now,
    )
    session.commit()
    return ExecutionClaimRead(
        execution_id=execution_id,
        grant_id=grant.grant_id,
        request_id=request.request_id,
        organization_id=organization_id,
        task_id=request.task_id,
        step_id=request.step_id,
        action_type=request.action_type,
        parameter_hash=parameter_hash,
        authorization_hash=authorization_hash,
        grant_status=GrantStatus.CLAIMED,
        grant_version=grant.version,
        claimed_at=grant.claimed_at,
    )


def complete_execution_claim(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    execution_id: str,
    *,
    receipt_reference: str,
    now: datetime,
) -> None:
    _require_actor_organization(actor, organization_id)
    if not 8 <= len(receipt_reference) <= 80 or not receipt_reference.startswith("rcp_"):
        raise GrantRejected("grant_rejected")
    now = _utc(now)
    grant = session.scalars(
        update(ApprovalGrant)
        .where(
            ApprovalGrant.organization_id == organization_id,
            ApprovalGrant.execution_id == execution_id,
            ApprovalGrant.executor_user_id == actor.user_id,
            ApprovalGrant.status == GrantStatus.CLAIMED.value,
        )
        .values(
            status=GrantStatus.CONSUMED.value,
            version=ApprovalGrant.version + 1,
            receipt_reference=receipt_reference,
            consumed_at=now,
            updated_at=now,
        )
        .returning(ApprovalGrant)
        .execution_options(synchronize_session=False)
    ).one_or_none()
    if grant is None:
        session.rollback()
        raise GrantRejected("grant_rejected")
    request = session.scalar(
        select(ApprovalRequest).where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.request_id == grant.request_id,
            ApprovalRequest.status == ApprovalRequestStatus.CLAIMED.value,
        )
    )
    if request is None:
        session.rollback()
        raise GrantRejected("grant_rejected")
    request.status = ApprovalRequestStatus.CONSUMED.value
    request.version += 1
    request.updated_at = now
    consumed = append_audit_event(
        session,
        organization_id=organization_id,
        event_type=AuditEventType.GRANT_CONSUMED,
        actor_reference=actor.authorization_hash,
        subject_reference=grant.grant_id,
        payload={
            "schema_version": "w11-audit-payload/1.0",
            "request_id": request.request_id,
            "grant_id": grant.grant_id,
            "grant_status": grant.status,
            "execution_id": execution_id,
            "receipt_reference": receipt_reference,
            "version": grant.version,
        },
        now=now,
    )
    append_audit_event(
        session,
        organization_id=organization_id,
        event_type=AuditEventType.EXECUTION_SUCCEEDED,
        actor_reference=actor.authorization_hash,
        subject_reference=execution_id,
        payload={
            "schema_version": "w11-audit-payload/1.0",
            "request_id": request.request_id,
            "grant_id": grant.grant_id,
            "execution_id": execution_id,
            "receipt_reference": receipt_reference,
            "action_type": request.action_type,
            "parameter_hash": request.parameter_hash,
        },
        now=now,
    )
    request.audit_sequence = consumed.sequence
    session.commit()


def credential_plaintext_present(session: Session, raw_credential: str) -> bool:
    """Test-only safety assertion over persisted W11 string columns."""
    if not raw_credential:
        return False
    grants = list(session.scalars(select(ApprovalGrant)))
    decisions = list(session.scalars(select(ApprovalDecision)))
    requests = list(session.scalars(select(ApprovalRequest)))
    persisted = canonical_json_bytes(
        {
            "grants": [
                {
                    "grant_id": item.grant_id,
                    "token_hash": item.token_hash,
                    "nonce_hash": item.nonce_hash,
                }
                for item in grants
            ],
            "decisions": [item.decision_id for item in decisions],
            "requests": [item.request_id for item in requests],
        }
    ).decode("utf-8")
    return raw_credential in persisted
