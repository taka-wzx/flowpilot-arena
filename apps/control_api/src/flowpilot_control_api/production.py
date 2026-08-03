"""W12 organization-qualified durable production admission."""

import math
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot_control_api.approval import REQUEST_TTL, TrustedGrantVault, claim_grant
from flowpilot_control_api.audit import append_audit_event
from flowpilot_control_api.config import ProductionPolicy, TokenBucketPolicy
from flowpilot_control_api.etag import PreconditionFailed
from flowpilot_control_api.models import (
    ApprovalGrant,
    ApprovalRequest,
    DispatchOutbox,
    IdempotencyRecord,
    Membership,
    ProductionRun,
    RateLimitBucket,
    SchedulerPartition,
    User,
)
from flowpilot_control_api.repository import ResourceNotFound
from flowpilot_control_api.risk import RiskEvaluation, RiskFacts, evaluate_risk
from flowpilot_control_api.schemas import (
    ActorContext,
    ApprovalRequestStatus,
    AuditEventType,
    GrantClaimRequest,
    GrantStatus,
    ProductionCategory,
    ProductionProcess,
    ProductionRouteClass,
    ProductionRunClaim,
    ProductionRunCreate,
    ProductionRunRead,
    ProductionRunStatus,
    ProductionTerminalReason,
    RiskLevel,
    Role,
    stable_hash,
)

MICROTOKEN = 1_000_000


class IdempotencyConflict(RuntimeError):
    pass


class ProductionStateConflict(RuntimeError):
    pass


class RateLimitExceeded(RuntimeError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("rate_limited")
        self.retry_after = retry_after


class BackpressureExceeded(RuntimeError):
    def __init__(self, retry_after: int = 1) -> None:
        super().__init__("backpressure")
        self.retry_after = retry_after


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _opaque_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(16)}"


def _require_actor_organization(actor: ActorContext, organization_id: str) -> None:
    if actor.organization_id != organization_id:
        raise ResourceNotFound("resource_not_found")


def _workflow_identity(organization_id: str, run_id: str) -> tuple[str, str]:
    workflow_hash = stable_hash(
        {
            "schema_version": "w12-workflow-identity/1.0",
            "organization_id": organization_id,
            "run_id": run_id,
        }
    )
    return f"w12-{workflow_hash[:48]}", workflow_hash


def run_read(record: ProductionRun) -> ProductionRunRead:
    return ProductionRunRead(
        run_id=record.run_id,
        organization_id=record.organization_id,
        requester_user_id=record.requester_user_id,
        executor_user_id=record.executor_user_id,
        task_id=record.task_id,  # type: ignore[arg-type]
        process=ProductionProcess(record.process),
        category=ProductionCategory(record.category),
        approval_request_id=record.approval_request_id,
        grant_id=record.grant_id,
        execution_id=record.execution_id,
        action_type=record.action_type,
        parameter_hash=record.parameter_hash,
        authorization_hash=record.authorization_hash,
        approval_set_hash=record.approval_set_hash,
        payload_hash=record.payload_hash,
        status=ProductionRunStatus(record.status),
        version=record.version,
        workflow_hash=record.workflow_hash,
        fencing_token=record.fencing_token,
        accepted_at=record.accepted_at,
        queued_at=record.queued_at,
        started_at=record.started_at,
        finished_at=record.finished_at,
        terminal_reason=(
            ProductionTerminalReason(record.terminal_reason)
            if record.terminal_reason is not None
            else None
        ),
        receipt_reference=record.receipt_reference,
        audit_sequence=record.audit_sequence,
    )


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
            (User.organization_id == Membership.organization_id)
            & (User.user_id == Membership.user_id),
        )
        .where(
            Membership.organization_id == organization_id,
            Membership.user_id == target_user_id,
            Membership.status == "active",
            User.organization_id == organization_id,
            User.status == "active",
        )
    )
    return RiskFacts(target_is_organization_administrator=role == Role.ORGANIZATION_ADMIN.value)


def _evaluate_production_risk(
    session: Session,
    organization_id: str,
    action_type: str,
    parameters: dict[str, object],
) -> RiskEvaluation:
    validated = evaluate_risk(action_type, parameters)
    if not validated.known_action or action_type != "create_account":
        return validated
    return evaluate_risk(
        action_type,
        validated.validated_parameters,
        _risk_facts(
            session,
            organization_id,
            action_type,
            validated.validated_parameters,
        ),
    )


def ensure_scheduler_partitions(session: Session, *, now: datetime) -> None:
    """Verify scheduler metadata availability without globally reading tenant rows."""
    del now
    session.scalar(select(func.count()).select_from(SchedulerPartition))
    session.commit()


def _ensure_partition(
    session: Session,
    organization_id: str,
    now: datetime,
    *,
    lock: bool = True,
) -> SchedulerPartition:
    values = {
        "organization_id": organization_id,
        "partition_id": f"prt_{stable_hash(organization_id)[:32]}",
        "ready_count": 0,
        "status": "empty",
        "cursor_version": 1,
        "last_selected_at": None,
        "updated_at": now,
    }
    bind = session.get_bind()
    if bind.dialect.name == "postgresql":
        session.execute(
            postgresql_insert(SchedulerPartition)
            .values(**values)
            .on_conflict_do_nothing(index_elements=["organization_id"])
        )
    elif bind.dialect.name == "sqlite":
        session.execute(
            sqlite_insert(SchedulerPartition)
            .values(**values)
            .on_conflict_do_nothing(index_elements=["organization_id"])
        )
    else:
        raise BackpressureExceeded()
    query = select(SchedulerPartition).where(SchedulerPartition.organization_id == organization_id)
    if lock:
        query = query.with_for_update()
    partition = session.scalar(query)
    if partition is None:
        raise BackpressureExceeded()
    return partition


def _ensure_bucket(
    session: Session,
    *,
    organization_id: str,
    bucket_key_hash: str,
    scope_kind: str,
    route_class: ProductionRouteClass,
    burst: int,
    now: datetime,
) -> RateLimitBucket:
    values = {
        "organization_id": organization_id,
        "bucket_key_hash": bucket_key_hash,
        "scope_kind": scope_kind,
        "route_class": route_class.value,
        "tokens_micro": burst * MICROTOKEN,
        "last_refill_at": now,
        "status": "active",
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    bind = session.get_bind()
    if bind.dialect.name == "postgresql":
        session.execute(
            postgresql_insert(RateLimitBucket)
            .values(**values)
            .on_conflict_do_nothing(
                index_elements=["organization_id", "bucket_key_hash", "route_class"]
            )
        )
    elif bind.dialect.name == "sqlite":
        session.execute(
            sqlite_insert(RateLimitBucket)
            .values(**values)
            .on_conflict_do_nothing(
                index_elements=["organization_id", "bucket_key_hash", "route_class"]
            )
        )
    else:
        raise BackpressureExceeded()
    bucket = session.scalar(
        select(RateLimitBucket)
        .where(
            RateLimitBucket.organization_id == organization_id,
            RateLimitBucket.bucket_key_hash == bucket_key_hash,
            RateLimitBucket.route_class == route_class.value,
            RateLimitBucket.scope_kind == scope_kind,
            RateLimitBucket.status == "active",
        )
        .with_for_update()
    )
    if bucket is None:
        raise BackpressureExceeded()
    return bucket


def _refill(bucket: RateLimitBucket, rate: int, burst: int, now: datetime) -> int:
    last = _utc(bucket.last_refill_at)
    elapsed = now - last
    elapsed_us = max(
        0,
        elapsed.days * 86_400 * MICROTOKEN + elapsed.seconds * MICROTOKEN + elapsed.microseconds,
    )
    return min(burst * MICROTOKEN, bucket.tokens_micro + elapsed_us * rate)


def consume_rate_limit(
    session: Session,
    actor: ActorContext,
    route_class: ProductionRouteClass,
    policy: ProductionPolicy,
    *,
    now: datetime,
) -> None:
    now = _utc(now)
    limits: TokenBucketPolicy = policy.bucket(route_class)
    actor_bucket = _ensure_bucket(
        session,
        organization_id=actor.organization_id,
        bucket_key_hash=stable_hash(actor.user_id),
        scope_kind="actor",
        route_class=route_class,
        burst=limits.actor_burst,
        now=now,
    )
    organization_bucket = _ensure_bucket(
        session,
        organization_id=actor.organization_id,
        bucket_key_hash=stable_hash(actor.organization_id),
        scope_kind="organization",
        route_class=route_class,
        burst=limits.organization_burst,
        now=now,
    )
    actor_tokens = _refill(actor_bucket, limits.actor_rate, limits.actor_burst, now)
    organization_tokens = _refill(
        organization_bucket,
        limits.organization_rate,
        limits.organization_burst,
        now,
    )
    actor_deficit = max(0, MICROTOKEN - actor_tokens)
    organization_deficit = max(0, MICROTOKEN - organization_tokens)
    for bucket, tokens in (
        (actor_bucket, actor_tokens),
        (organization_bucket, organization_tokens),
    ):
        bucket.tokens_micro = tokens
        bucket.last_refill_at = now
        bucket.updated_at = now
        bucket.version += 1
    if actor_deficit or organization_deficit:
        actor_wait = actor_deficit / (limits.actor_rate * MICROTOKEN)
        organization_wait = organization_deficit / (limits.organization_rate * MICROTOKEN)
        retry_after = max(1, math.ceil(max(actor_wait, organization_wait)))
        raise RateLimitExceeded(min(policy.retry_after_max_seconds, retry_after))
    actor_bucket.tokens_micro -= MICROTOKEN
    organization_bucket.tokens_micro -= MICROTOKEN


def _consume_rate_limit_or_audit(
    session: Session,
    actor: ActorContext,
    route_class: ProductionRouteClass,
    policy: ProductionPolicy,
    *,
    subject_reference: str,
    now: datetime,
) -> None:
    try:
        consume_rate_limit(session, actor, route_class, policy, now=now)
    except RateLimitExceeded as exc:
        append_audit_event(
            session,
            organization_id=actor.organization_id,
            event_type=AuditEventType.RATE_LIMITED,
            actor_reference=actor.authorization_hash,
            subject_reference=subject_reference,
            payload={
                "schema_version": "w12-audit-payload/1.0",
                "reason": "rate_limited",
                "http_status": 429,
                "retry_after": exc.retry_after,
            },
            now=now,
        )
        session.commit()
        raise


def _lock_capacity(
    session: Session,
    organization_id: str,
    policy: ProductionPolicy,
    *,
    now: datetime,
) -> SchedulerPartition:
    # Capacity writers must not pre-lock different current partitions before
    # taking the same global partition order.
    _ensure_partition(session, organization_id, now, lock=False)
    partitions = list(
        session.scalars(
            select(SchedulerPartition).order_by(SchedulerPartition.partition_id).with_for_update()
        )
    )
    current = next((item for item in partitions if item.organization_id == organization_id), None)
    if current is None:
        raise BackpressureExceeded()
    if (
        sum(item.ready_count for item in partitions) >= policy.queue_total_capacity
        or current.ready_count >= policy.queue_organization_capacity
    ):
        raise BackpressureExceeded()
    return current


def _new_outbox(
    *,
    organization_id: str,
    run_id: str,
    now: datetime,
    policy: ProductionPolicy,
) -> DispatchOutbox:
    return DispatchOutbox(
        outbox_id=_opaque_id("out"),
        organization_id=organization_id,
        run_id=run_id,
        status="ready",
        attempt_count=0,
        fencing_token=0,
        lease_owner_hash=None,
        lease_version=0,
        leased_at=None,
        lease_expires_at=None,
        heartbeat_at=None,
        available_at=now,
        expires_at=now + timedelta(seconds=policy.queue_ttl_seconds),
        created_at=now,
        updated_at=now,
    )


def _existing_idempotent_run(
    session: Session,
    actor: ActorContext,
    key_hash: str,
    body_hash: str,
) -> ProductionRun | None:
    record = session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.organization_id == actor.organization_id,
            IdempotencyRecord.actor_user_id == actor.user_id,
            IdempotencyRecord.key_hash == key_hash,
        )
    )
    if record is None:
        return None
    if record.body_hash != body_hash:
        raise IdempotencyConflict("idempotency_mismatch")
    run = session.scalar(
        select(ProductionRun).where(
            ProductionRun.organization_id == actor.organization_id,
            ProductionRun.run_id == record.run_id,
        )
    )
    if run is None:
        raise ProductionStateConflict("idempotency_run_missing")
    return run


def admit_production_run(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    idempotency_key: str,
    payload: ProductionRunCreate,
    policy: ProductionPolicy,
    *,
    now: datetime,
) -> ProductionRun:
    _require_actor_organization(actor, organization_id)
    now = _utc(now)
    key_hash = stable_hash(idempotency_key)
    body_hash = stable_hash(payload)
    existing = _existing_idempotent_run(session, actor, key_hash, body_hash)
    if existing is not None:
        return existing
    evaluation = _evaluate_production_risk(
        session,
        organization_id,
        payload.action_type,
        payload.parameters,
    )
    if evaluation.risk_level == RiskLevel.L4:
        append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.ADMISSION_REJECTED,
            actor_reference=actor.authorization_hash,
            subject_reference=payload.action_type,
            payload={
                "schema_version": "w12-audit-payload/1.0",
                "action_type": payload.action_type,
                "risk_level": RiskLevel.L4.value,
                "parameter_hash": evaluation.parameter_hash,
                "reason": "risk_denied",
                "http_status": 403,
            },
            now=now,
        )
        session.commit()
        from flowpilot_control_api.approval import RiskDenied

        raise RiskDenied("risk_denied")
    _consume_rate_limit_or_audit(
        session,
        actor,
        ProductionRouteClass.SUBMIT,
        policy,
        subject_reference=payload.action_type,
        now=now,
    )
    status = (
        ProductionRunStatus.WAITING_APPROVAL
        if evaluation.risk_level in {RiskLevel.L2, RiskLevel.L3}
        else ProductionRunStatus.QUEUED
    )
    partition: SchedulerPartition | None = None
    if status == ProductionRunStatus.QUEUED:
        try:
            partition = _lock_capacity(session, organization_id, policy, now=now)
        except BackpressureExceeded as exc:
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
            append_audit_event(
                session,
                organization_id=organization_id,
                event_type=AuditEventType.BACKPRESSURE_REJECTED,
                actor_reference=actor.authorization_hash,
                subject_reference=payload.action_type,
                payload={
                    "schema_version": "w12-audit-payload/1.0",
                    "reason": "backpressure",
                    "http_status": 503,
                    "retry_after": exc.retry_after,
                },
                now=now,
            )
            session.commit()
            raise
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
    run_id = _opaque_id("run")
    workflow_id, workflow_hash = _workflow_identity(organization_id, run_id)
    payload_reference = f"taskref_{stable_hash(payload.task_id)[:32]}"
    payload_hash = stable_hash(
        {
            "schema_version": "w12-trusted-task-reference/1.0",
            "task_id": payload.task_id,
            "process": payload.process.value,
            "category": payload.category.value,
        }
    )
    request_id: str | None = None
    if status == ProductionRunStatus.WAITING_APPROVAL:
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
        session.add(
            ApprovalRequest(
                request_id=request_id,
                organization_id=organization_id,
                task_id=payload.task_id,
                step_id="production_run",
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
        )
    event_type = (
        AuditEventType.RUN_WAITING_APPROVAL
        if status == ProductionRunStatus.WAITING_APPROVAL
        else AuditEventType.RUN_QUEUED
    )
    accepted_event = append_audit_event(
        session,
        organization_id=organization_id,
        event_type=event_type,
        actor_reference=actor.authorization_hash,
        subject_reference=run_id,
        payload={
            "schema_version": "w12-audit-payload/1.0",
            "run_id": run_id,
            "request_id": request_id,
            "run_status": status.value,
            "action_type": payload.action_type,
            "parameter_hash": evaluation.parameter_hash,
            "version": 1,
        },
        now=now,
    )
    run = ProductionRun(
        run_id=run_id,
        organization_id=organization_id,
        requester_user_id=actor.user_id,
        executor_user_id=actor.user_id,
        task_id=payload.task_id,
        process=payload.process.value,
        category=payload.category.value,
        approval_request_id=request_id,
        grant_id=None,
        execution_id=None,
        action_type=payload.action_type,
        parameter_hash=evaluation.parameter_hash,
        authorization_hash=actor.authorization_hash,
        approval_set_hash=None,
        payload_reference=payload_reference,
        payload_hash=payload_hash,
        status=status.value,
        version=1,
        idempotency_hash=key_hash,
        body_hash=body_hash,
        workflow_id=workflow_id,
        workflow_hash=workflow_hash,
        lease_owner_hash=None,
        fencing_token=0,
        lease_expires_at=None,
        accepted_at=now,
        queued_at=now if status == ProductionRunStatus.QUEUED else None,
        started_at=None,
        finished_at=None,
        terminal_reason=None,
        receipt_reference=None,
        audit_sequence=accepted_event.sequence,
        created_at=now,
        updated_at=now,
    )
    session.add(run)
    session.flush()
    session.add(
        IdempotencyRecord(
            idempotency_id=_opaque_id("idm"),
            organization_id=organization_id,
            actor_user_id=actor.user_id,
            key_hash=key_hash,
            body_hash=body_hash,
            run_id=run_id,
            created_at=now,
        )
    )
    if status == ProductionRunStatus.QUEUED:
        assert partition is not None
        session.add(
            _new_outbox(
                organization_id=organization_id,
                run_id=run_id,
                now=now,
                policy=policy,
            )
        )
        partition.ready_count += 1
        partition.status = "ready"
        partition.cursor_version += 1
        partition.updated_at = now
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        winner = _existing_idempotent_run(session, actor, key_hash, body_hash)
        if winner is None:
            raise IdempotencyConflict("idempotency_conflict") from None
        return winner
    session.refresh(run)
    return run


def get_production_run(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    run_id: str,
    policy: ProductionPolicy,
    *,
    now: datetime,
    charge_rate: bool = True,
) -> ProductionRun:
    _require_actor_organization(actor, organization_id)
    if charge_rate:
        _consume_rate_limit_or_audit(
            session,
            actor,
            ProductionRouteClass.READ,
            policy,
            subject_reference=run_id,
            now=_utc(now),
        )
    record = session.scalar(
        select(ProductionRun).where(
            ProductionRun.organization_id == organization_id,
            ProductionRun.run_id == run_id,
        )
    )
    if record is None:
        if charge_rate:
            session.commit()
        else:
            session.rollback()
        raise ResourceNotFound("resource_not_found")
    if charge_rate:
        session.commit()
    return record


def list_production_runs(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    policy: ProductionPolicy,
    *,
    now: datetime,
) -> list[ProductionRun]:
    _require_actor_organization(actor, organization_id)
    _consume_rate_limit_or_audit(
        session,
        actor,
        ProductionRouteClass.READ,
        policy,
        subject_reference=organization_id,
        now=_utc(now),
    )
    records = list(
        session.scalars(
            select(ProductionRun)
            .where(ProductionRun.organization_id == organization_id)
            .order_by(ProductionRun.accepted_at, ProductionRun.run_id)
            .limit(100)
        )
    )
    session.commit()
    return records


def claim_production_run(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    run_id: str,
    expected_version: int,
    payload: ProductionRunClaim,
    policy: ProductionPolicy,
    *,
    now: datetime,
    vault: TrustedGrantVault,
) -> ProductionRun:
    _require_actor_organization(actor, organization_id)
    now = _utc(now)
    _consume_rate_limit_or_audit(
        session,
        actor,
        ProductionRouteClass.MUTATE,
        policy,
        subject_reference=run_id,
        now=now,
    )
    run = session.scalar(
        select(ProductionRun).where(
            ProductionRun.organization_id == organization_id,
            ProductionRun.run_id == run_id,
            ProductionRun.status == ProductionRunStatus.WAITING_APPROVAL.value,
        )
    )
    if run is None or run.approval_request_id is None:
        raise ProductionStateConflict("production_claim_rejected")
    if run.version != expected_version:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    try:
        partition = _lock_capacity(session, organization_id, policy, now=now)
    except BackpressureExceeded as exc:
        append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.BACKPRESSURE_REJECTED,
            actor_reference=actor.authorization_hash,
            subject_reference=run_id,
            payload={
                "schema_version": "w12-audit-payload/1.0",
                "run_id": run_id,
                "reason": "backpressure",
                "http_status": 503,
                "retry_after": exc.retry_after,
            },
            now=now,
        )
        session.commit()
        raise

    def on_claim(
        request: ApprovalRequest,
        grant: ApprovalGrant,
        claim: object,
    ) -> None:
        from flowpilot_control_api.schemas import ExecutionClaimRead

        if not isinstance(claim, ExecutionClaimRead):
            raise ProductionStateConflict("production_claim_rejected")
        locked_run = session.scalar(
            select(ProductionRun)
            .where(
                ProductionRun.organization_id == organization_id,
                ProductionRun.run_id == run_id,
                ProductionRun.status == ProductionRunStatus.WAITING_APPROVAL.value,
                ProductionRun.approval_request_id == request.request_id,
                ProductionRun.parameter_hash == request.parameter_hash,
                ProductionRun.action_type == request.action_type,
            )
            .with_for_update()
        )
        if locked_run is None:
            raise ProductionStateConflict("production_claim_rejected")
        locked_run.grant_id = grant.grant_id
        locked_run.execution_id = claim.execution_id
        locked_run.authorization_hash = claim.authorization_hash
        locked_run.approval_set_hash = grant.approval_set_hash
        locked_run.status = ProductionRunStatus.QUEUED.value
        locked_run.version += 1
        locked_run.queued_at = now
        locked_run.updated_at = now
        session.add(
            _new_outbox(
                organization_id=organization_id,
                run_id=run_id,
                now=now,
                policy=policy,
            )
        )
        partition.ready_count += 1
        partition.status = "ready"
        partition.cursor_version += 1
        partition.updated_at = now
        queued = append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.RUN_QUEUED,
            actor_reference=actor.authorization_hash,
            subject_reference=run_id,
            payload={
                "schema_version": "w12-audit-payload/1.0",
                "run_id": run_id,
                "request_id": request.request_id,
                "grant_id": grant.grant_id,
                "execution_id": claim.execution_id,
                "run_status": ProductionRunStatus.QUEUED.value,
                "parameter_hash": request.parameter_hash,
                "version": locked_run.version,
            },
            now=now,
        )
        locked_run.audit_sequence = queued.sequence

    claim_grant(
        session,
        actor,
        organization_id,
        run.approval_request_id,
        GrantClaimRequest(
            task_id=run.task_id,
            step_id="production_run",
            action_type=payload.action_type,
            parameters=payload.parameters,
        ),
        now=now,
        vault=vault,
        on_claim=on_claim,
    )
    refreshed = session.scalar(
        select(ProductionRun).where(
            ProductionRun.organization_id == organization_id,
            ProductionRun.run_id == run_id,
        )
    )
    if refreshed is None:
        raise ProductionStateConflict("production_claim_rejected")
    return refreshed


def cancel_production_run(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    run_id: str,
    expected_version: int,
    policy: ProductionPolicy,
    *,
    now: datetime,
    vault: TrustedGrantVault,
) -> ProductionRun:
    _require_actor_organization(actor, organization_id)
    now = _utc(now)
    _consume_rate_limit_or_audit(
        session,
        actor,
        ProductionRouteClass.MUTATE,
        policy,
        subject_reference=run_id,
        now=now,
    )
    current = session.scalar(
        select(ProductionRun).where(
            ProductionRun.organization_id == organization_id,
            ProductionRun.run_id == run_id,
        )
    )
    if current is None:
        session.rollback()
        raise ResourceNotFound("resource_not_found")
    if current.version != expected_version:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    if current.status not in {
        ProductionRunStatus.WAITING_APPROVAL.value,
        ProductionRunStatus.QUEUED.value,
        ProductionRunStatus.LEASED.value,
    }:
        session.rollback()
        raise ProductionStateConflict("illegal_transition")
    outbox: DispatchOutbox | None = None
    partition: SchedulerPartition | None = None
    if current.status == ProductionRunStatus.WAITING_APPROVAL.value:
        run = session.scalar(
            select(ProductionRun)
            .where(
                ProductionRun.organization_id == organization_id,
                ProductionRun.run_id == run_id,
                ProductionRun.version == expected_version,
                ProductionRun.status == ProductionRunStatus.WAITING_APPROVAL.value,
            )
            .with_for_update()
        )
    else:
        partition = _ensure_partition(session, organization_id, now)
        outbox = session.scalar(
            select(DispatchOutbox)
            .where(
                DispatchOutbox.organization_id == organization_id,
                DispatchOutbox.run_id == run_id,
                DispatchOutbox.status.in_(("ready", "leased", "dispatched")),
            )
            .with_for_update()
        )
        run = session.scalar(
            select(ProductionRun)
            .where(
                ProductionRun.organization_id == organization_id,
                ProductionRun.run_id == run_id,
                ProductionRun.version == expected_version,
                ProductionRun.status.in_(
                    (
                        ProductionRunStatus.QUEUED.value,
                        ProductionRunStatus.LEASED.value,
                    )
                ),
            )
            .with_for_update()
        )
    if run is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    if run.status in {ProductionRunStatus.QUEUED.value, ProductionRunStatus.LEASED.value}:
        if outbox is None or partition is None:
            session.rollback()
            raise ProductionStateConflict("illegal_transition")
        outbox.status = "cancelled"
        outbox.updated_at = now
        partition.ready_count = max(0, partition.ready_count - 1)
        partition.status = "ready" if partition.ready_count else "empty"
        partition.cursor_version += 1
        partition.updated_at = now
    grant_id: str | None = None
    if run.approval_request_id is not None:
        request = session.scalar(
            select(ApprovalRequest)
            .where(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.request_id == run.approval_request_id,
            )
            .with_for_update()
        )
        if request is not None and request.status in {
            ApprovalRequestStatus.PENDING.value,
            ApprovalRequestStatus.APPROVED.value,
            ApprovalRequestStatus.CLAIMED.value,
        }:
            request.status = ApprovalRequestStatus.CANCELLED.value
            request.closed_reason = "requester_cancelled"
            request.version += 1
            request.updated_at = now
            request_event = append_audit_event(
                session,
                organization_id=organization_id,
                event_type=AuditEventType.REQUEST_CANCELLED,
                actor_reference=actor.authorization_hash,
                subject_reference=request.request_id,
                payload={
                    "schema_version": "w11-audit-payload/1.0",
                    "request_id": request.request_id,
                    "request_status": request.status,
                    "reason": "requester_cancelled",
                    "version": request.version,
                },
                now=now,
            )
            request.audit_sequence = request_event.sequence
        grant = session.scalar(
            select(ApprovalGrant)
            .where(
                ApprovalGrant.organization_id == organization_id,
                ApprovalGrant.request_id == run.approval_request_id,
            )
            .with_for_update()
        )
        if grant is not None and grant.status in {
            GrantStatus.ISSUED.value,
            GrantStatus.CLAIMED.value,
        }:
            was_claimed = grant.status == GrantStatus.CLAIMED.value
            grant.status = GrantStatus.FAILED.value if was_claimed else GrantStatus.REVOKED.value
            grant.version += 1
            grant.updated_at = now
            grant_id = grant.grant_id
            if was_claimed:
                append_audit_event(
                    session,
                    organization_id=organization_id,
                    event_type=AuditEventType.EXECUTION_FAILED,
                    actor_reference=actor.authorization_hash,
                    subject_reference=grant.execution_id or grant.grant_id,
                    payload={
                        "schema_version": "w11-audit-payload/1.0",
                        "request_id": run.approval_request_id,
                        "grant_id": grant.grant_id,
                        "grant_status": grant.status,
                        "execution_id": grant.execution_id,
                        "reason": "requester_cancelled",
                    },
                    now=now,
                )
    run.status = ProductionRunStatus.CANCELLED.value
    run.version += 1
    run.finished_at = now
    run.terminal_reason = ProductionTerminalReason.CANCELLED_BY_ACTOR.value
    run.updated_at = now
    event = append_audit_event(
        session,
        organization_id=organization_id,
        event_type=AuditEventType.RUN_CANCELLED,
        actor_reference=actor.authorization_hash,
        subject_reference=run_id,
        payload={
            "schema_version": "w12-audit-payload/1.0",
            "run_id": run_id,
            "run_status": ProductionRunStatus.CANCELLED.value,
            "reason": ProductionTerminalReason.CANCELLED_BY_ACTOR.value,
            "version": run.version,
        },
        now=now,
    )
    run.audit_sequence = event.sequence
    session.commit()
    if grant_id is not None:
        vault.discard(grant_id)
    session.refresh(run)
    return run
