"""Closed SQL repository for W12 fair claim, authorization recheck, and fencing."""

import secrets
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    and_,
    create_engine,
    func,
    insert,
    or_,
    select,
    update,
)
from sqlalchemy.engine import Connection, Engine, RowMapping

from flowpilot_workflow_worker.config import WorkerSettings
from flowpilot_workflow_worker.schemas import (
    TemporalOutcome,
    WorkItem,
    canonical_json_bytes,
    stable_hash,
)

METADATA = MetaData()

ORGANIZATIONS = Table(
    "w10_organizations",
    METADATA,
    Column("organization_id", String(68), primary_key=True),
    Column("status", String(16), nullable=False),
    Column("version", Integer, nullable=False),
)
USERS = Table(
    "w10_users",
    METADATA,
    Column("user_id", String(68), primary_key=True),
    Column("organization_id", String(68), nullable=False),
    Column("status", String(16), nullable=False),
    Column("version", Integer, nullable=False),
)
IDENTITIES = Table(
    "w10_oidc_identities",
    METADATA,
    Column("identity_id", String(68), primary_key=True),
    Column("organization_id", String(68), nullable=False),
    Column("user_id", String(68), nullable=False),
    Column("status", String(16), nullable=False),
    Column("version", Integer, nullable=False),
)
MEMBERSHIPS = Table(
    "w10_memberships",
    METADATA,
    Column("membership_id", String(68), primary_key=True),
    Column("organization_id", String(68), nullable=False),
    Column("user_id", String(68), nullable=False),
    Column("role", String(32), nullable=False),
    Column("status", String(16), nullable=False),
    Column("version", Integer, nullable=False),
)
AUTHORITIES = Table(
    "w11_approval_authorities",
    METADATA,
    Column("authority_id", String(68), primary_key=True),
    Column("organization_id", String(68), nullable=False),
    Column("user_id", String(68), nullable=False),
    Column("role", String(16), nullable=False),
    Column("status", String(16), nullable=False),
    Column("version", Integer, nullable=False),
)
REQUESTS = Table(
    "w11_approval_requests",
    METADATA,
    Column("request_id", String(68), primary_key=True),
    Column("organization_id", String(68), nullable=False),
    Column("task_id", String(80), nullable=False),
    Column("step_id", String(40), nullable=False),
    Column("action_type", String(64), nullable=False),
    Column("parameter_hash", String(64), nullable=False),
    Column("risk_level", String(2), nullable=False),
    Column("executor_user_id", String(68), nullable=False),
    Column("required_roles", String(32), nullable=False),
    Column("status", String(16), nullable=False),
    Column("version", Integer, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
DECISIONS = Table(
    "w11_approval_decisions",
    METADATA,
    Column("decision_id", String(68), primary_key=True),
    Column("organization_id", String(68), nullable=False),
    Column("request_id", String(68), nullable=False),
    Column("decision", String(16), nullable=False),
    Column("approver_user_id", String(68), nullable=False),
    Column("authority_id", String(68), nullable=False),
    Column("approval_role", String(16), nullable=False),
)
GRANTS = Table(
    "w11_approval_grants",
    METADATA,
    Column("grant_id", String(68), primary_key=True),
    Column("organization_id", String(68), nullable=False),
    Column("request_id", String(68), nullable=False),
    Column("task_id", String(80), nullable=False),
    Column("step_id", String(40), nullable=False),
    Column("action_type", String(64), nullable=False),
    Column("parameter_hash", String(64), nullable=False),
    Column("approval_set_hash", String(64), nullable=False),
    Column("executor_user_id", String(68), nullable=False),
    Column("status", String(16), nullable=False),
    Column("version", Integer, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("execution_id", String(68)),
    Column("authorization_hash", String(64)),
    Column("receipt_reference", String(80)),
    Column("consumed_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
AUDIT_HEADS = Table(
    "w11_audit_chain_heads",
    METADATA,
    Column("organization_id", String(68), primary_key=True),
    Column("head_sequence", Integer, nullable=False),
    Column("head_hash", String(64), nullable=False),
    Column("version", Integer, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
AUDIT_EVENTS = Table(
    "w11_audit_events",
    METADATA,
    Column("organization_id", String(68), primary_key=True),
    Column("sequence", Integer, primary_key=True),
    Column("event_id", String(68), nullable=False),
    Column("event_type", String(40), nullable=False),
    Column("actor_reference", String(64), nullable=False),
    Column("subject_reference", String(68), nullable=False),
    Column("payload_json", Text, nullable=False),
    Column("payload_hash", String(64), nullable=False),
    Column("previous_hash", String(64), nullable=False),
    Column("event_hash", String(64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
RUNS = Table(
    "w12_production_runs",
    METADATA,
    Column("run_id", String(68), primary_key=True),
    Column("organization_id", String(68), nullable=False),
    Column("requester_user_id", String(68), nullable=False),
    Column("executor_user_id", String(68), nullable=False),
    Column("task_id", String(40), nullable=False),
    Column("process", String(16), nullable=False),
    Column("category", String(24), nullable=False),
    Column("approval_request_id", String(68)),
    Column("grant_id", String(68)),
    Column("execution_id", String(68)),
    Column("action_type", String(64), nullable=False),
    Column("parameter_hash", String(64), nullable=False),
    Column("authorization_hash", String(64), nullable=False),
    Column("approval_set_hash", String(64)),
    Column("payload_reference", String(80), nullable=False),
    Column("payload_hash", String(64), nullable=False),
    Column("status", String(24), nullable=False),
    Column("version", Integer, nullable=False),
    Column("workflow_id", String(64), nullable=False),
    Column("workflow_hash", String(64), nullable=False),
    Column("lease_owner_hash", String(64)),
    Column("fencing_token", Integer, nullable=False),
    Column("lease_expires_at", DateTime(timezone=True)),
    Column("started_at", DateTime(timezone=True)),
    Column("finished_at", DateTime(timezone=True)),
    Column("terminal_reason", String(32)),
    Column("receipt_reference", String(80)),
    Column("audit_sequence", Integer, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
OUTBOX = Table(
    "w12_dispatch_outbox",
    METADATA,
    Column("outbox_id", String(68), primary_key=True),
    Column("organization_id", String(68), nullable=False),
    Column("run_id", String(68), nullable=False),
    Column("status", String(16), nullable=False),
    Column("attempt_count", Integer, nullable=False),
    Column("fencing_token", Integer, nullable=False),
    Column("lease_owner_hash", String(64)),
    Column("lease_version", Integer, nullable=False),
    Column("leased_at", DateTime(timezone=True)),
    Column("lease_expires_at", DateTime(timezone=True)),
    Column("heartbeat_at", DateTime(timezone=True)),
    Column("available_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
LEASES = Table(
    "w12_worker_leases",
    METADATA,
    Column("lease_id", String(68), primary_key=True),
    Column("organization_id", String(68), nullable=False),
    Column("outbox_id", String(68), nullable=False),
    Column("run_id", String(68), nullable=False),
    Column("worker_owner_hash", String(64), nullable=False),
    Column("lease_version", Integer, nullable=False),
    Column("fencing_token", Integer, nullable=False),
    Column("leased_at", DateTime(timezone=True), nullable=False),
    Column("lease_expires_at", DateTime(timezone=True), nullable=False),
    Column("heartbeat_at", DateTime(timezone=True), nullable=False),
    Column("attempt_count", Integer, nullable=False),
    Column("status", String(16), nullable=False),
    Column("closed_at", DateTime(timezone=True)),
)
PARTITIONS = Table(
    "w12_scheduler_partitions",
    METADATA,
    Column("organization_id", String(68), primary_key=True),
    Column("partition_id", String(68), nullable=False),
    Column("ready_count", Integer, nullable=False),
    Column("status", String(16), nullable=False),
    Column("cursor_version", Integer, nullable=False),
    Column("last_selected_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _opaque_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(16)}"


def _as_datetime(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("database timestamp is invalid")
    return _utc(value)


def _as_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("database integer is invalid")
    return value


def _append_audit(
    connection: Connection,
    *,
    organization_id: str,
    event_type: str,
    actor_reference: str,
    subject_reference: str,
    payload: dict[str, object],
    now: datetime,
) -> int:
    organization = connection.scalar(
        select(ORGANIZATIONS.c.organization_id)
        .where(ORGANIZATIONS.c.organization_id == organization_id)
        .with_for_update(read=True, key_share=True)
    )
    if organization is None:
        raise RuntimeError("organization audit owner is unavailable")
    head = (
        connection.execute(
            select(AUDIT_HEADS)
            .where(AUDIT_HEADS.c.organization_id == organization_id)
            .with_for_update()
        )
        .mappings()
        .one()
    )
    sequence = int(head["head_sequence"]) + 1
    previous_hash = str(head["head_hash"])
    event_id = _opaque_id("aud")
    payload_json = canonical_json_bytes(payload).decode("utf-8")
    payload_hash = stable_hash(payload)
    fields: dict[str, object] = {
        "schema_version": "w11-audit-event/1.0",
        "event_id": event_id,
        "organization_id": organization_id,
        "sequence": sequence,
        "event_type": event_type,
        "actor_reference": actor_reference,
        "subject_reference": subject_reference,
        "payload": payload,
        "previous_hash": previous_hash,
        "created_at": now,
    }
    event_hash = stable_hash(fields)
    connection.execute(
        insert(AUDIT_EVENTS).values(
            organization_id=organization_id,
            sequence=sequence,
            event_id=event_id,
            event_type=event_type,
            actor_reference=actor_reference,
            subject_reference=subject_reference,
            payload_json=payload_json,
            payload_hash=payload_hash,
            previous_hash=previous_hash,
            event_hash=event_hash,
            created_at=now,
        )
    )
    connection.execute(
        update(AUDIT_HEADS)
        .where(AUDIT_HEADS.c.organization_id == organization_id)
        .values(
            head_sequence=sequence,
            head_hash=event_hash,
            version=AUDIT_HEADS.c.version + 1,
            updated_at=now,
        )
    )
    return sequence


def _authorization_hash(
    connection: Connection,
    organization_id: str,
    user_id: str,
    *,
    lock: bool,
) -> str | None:
    organization_query = select(ORGANIZATIONS).where(
        ORGANIZATIONS.c.organization_id == organization_id,
        ORGANIZATIONS.c.status == "active",
    )
    user_query = select(USERS).where(
        USERS.c.organization_id == organization_id,
        USERS.c.user_id == user_id,
        USERS.c.status == "active",
    )
    membership_query = select(MEMBERSHIPS).where(
        MEMBERSHIPS.c.organization_id == organization_id,
        MEMBERSHIPS.c.user_id == user_id,
        MEMBERSHIPS.c.status == "active",
    )
    identities_query = select(IDENTITIES).where(
        IDENTITIES.c.organization_id == organization_id,
        IDENTITIES.c.user_id == user_id,
        IDENTITIES.c.status == "active",
    )
    authorities_query = (
        select(AUTHORITIES)
        .where(
            AUTHORITIES.c.organization_id == organization_id,
            AUTHORITIES.c.user_id == user_id,
            AUTHORITIES.c.status == "active",
        )
        .order_by(AUTHORITIES.c.role, AUTHORITIES.c.authority_id)
    )
    if lock:
        organization_query = organization_query.with_for_update()
        user_query = user_query.with_for_update()
        membership_query = membership_query.with_for_update()
        identities_query = identities_query.with_for_update()
        authorities_query = authorities_query.with_for_update()
    organization = connection.execute(organization_query).mappings().one_or_none()
    user = connection.execute(user_query).mappings().one_or_none()
    membership = connection.execute(membership_query).mappings().one_or_none()
    identities = list(connection.execute(identities_query).mappings())
    if organization is None or user is None or membership is None or len(identities) != 1:
        return None
    authorities = list(connection.execute(authorities_query).mappings())
    identity = identities[0]
    return stable_hash(
        {
            "schema_version": "w10-authorization-fact/1.0",
            "identity_id": identity["identity_id"],
            "identity_version": identity["version"],
            "organization_id": organization["organization_id"],
            "organization_version": organization["version"],
            "user_id": user["user_id"],
            "user_version": user["version"],
            "membership_id": membership["membership_id"],
            "membership_version": membership["version"],
            "role": membership["role"],
            "approval_authorities": [
                {
                    "authority_id": authority["authority_id"],
                    "role": authority["role"],
                    "version": authority["version"],
                }
                for authority in authorities
            ],
        }
    )


def _approval_set_hash(
    connection: Connection,
    organization_id: str,
    request_id: str,
    *,
    lock: bool,
) -> str | None:
    decisions = list(
        connection.execute(
            select(DECISIONS)
            .where(
                DECISIONS.c.organization_id == organization_id,
                DECISIONS.c.request_id == request_id,
                DECISIONS.c.decision == "approved",
            )
            .order_by(DECISIONS.c.approval_role, DECISIONS.c.decision_id)
        ).mappings()
    )
    approvals: list[dict[str, object]] = []
    for decision in decisions:
        authority_query = select(AUTHORITIES).where(
            AUTHORITIES.c.organization_id == organization_id,
            AUTHORITIES.c.authority_id == decision["authority_id"],
            AUTHORITIES.c.user_id == decision["approver_user_id"],
            AUTHORITIES.c.role == decision["approval_role"],
            AUTHORITIES.c.status == "active",
        )
        approver_query = (
            select(USERS.c.user_id)
            .join(
                MEMBERSHIPS,
                and_(
                    MEMBERSHIPS.c.organization_id == USERS.c.organization_id,
                    MEMBERSHIPS.c.user_id == USERS.c.user_id,
                ),
            )
            .where(
                USERS.c.organization_id == organization_id,
                USERS.c.user_id == decision["approver_user_id"],
                USERS.c.status == "active",
                MEMBERSHIPS.c.organization_id == organization_id,
                MEMBERSHIPS.c.status == "active",
                MEMBERSHIPS.c.role != "auditor",
            )
        )
        if lock:
            authority_query = authority_query.with_for_update()
            approver_query = approver_query.with_for_update()
        authority = connection.execute(authority_query).mappings().one_or_none()
        approver = connection.execute(approver_query).scalar_one_or_none()
        if authority is None or approver is None:
            return None
        approvals.append(
            {
                "decision_id": decision["decision_id"],
                "approver_user_id": decision["approver_user_id"],
                "authority_id": decision["authority_id"],
                "approval_role": decision["approval_role"],
                "authority_version": authority["version"],
            }
        )
    return stable_hash(
        {
            "schema_version": "w11-required-approval-set/1.0",
            "approvals": sorted(approvals, key=lambda item: str(item["approval_role"])),
        }
    )


def _binding_valid(
    connection: Connection,
    item: WorkItem,
    now: datetime,
    *,
    check_expiry: bool,
    lock: bool,
) -> bool:
    current_hash = _authorization_hash(
        connection,
        item.organization_id,
        item.executor_user_id,
        lock=lock,
    )
    if current_hash != item.authorization_hash:
        return False
    if item.approval_request_id is None:
        return item.grant_id is None and item.execution_id is None
    request_query = select(REQUESTS).where(
        REQUESTS.c.organization_id == item.organization_id,
        REQUESTS.c.request_id == item.approval_request_id,
    )
    grant_query = select(GRANTS).where(
        GRANTS.c.organization_id == item.organization_id,
        GRANTS.c.grant_id == item.grant_id,
        GRANTS.c.request_id == item.approval_request_id,
        GRANTS.c.execution_id == item.execution_id,
    )
    if lock:
        request_query = request_query.with_for_update()
        grant_query = grant_query.with_for_update()
    request = connection.execute(request_query).mappings().one_or_none()
    grant = connection.execute(grant_query).mappings().one_or_none()
    if request is None or grant is None:
        return False
    request_expiry = _as_datetime(request["expires_at"])
    grant_expiry = _as_datetime(grant["expires_at"])
    if check_expiry and (request_expiry <= now or grant_expiry <= now):
        return False
    if (
        request["status"] != "claimed"
        or grant["status"] != "claimed"
        or request["task_id"] != item.task_id
        or request["step_id"] != "production_run"
        or request["action_type"] != item.action_type
        or request["parameter_hash"] != item.parameter_hash
        or request["executor_user_id"] != item.executor_user_id
        or grant["task_id"] != item.task_id
        or grant["step_id"] != "production_run"
        or grant["action_type"] != item.action_type
        or grant["parameter_hash"] != item.parameter_hash
        or grant["executor_user_id"] != item.executor_user_id
        or grant["authorization_hash"] != item.authorization_hash
        or grant["approval_set_hash"] != item.approval_set_hash
    ):
        return False
    required_roles = str(request["required_roles"]).split(",")
    approval_hash = _approval_set_hash(
        connection,
        item.organization_id,
        item.approval_request_id,
        lock=lock,
    )
    decision_count = connection.scalar(
        select(func.count())
        .select_from(DECISIONS)
        .where(
            DECISIONS.c.organization_id == item.organization_id,
            DECISIONS.c.request_id == item.approval_request_id,
            DECISIONS.c.decision == "approved",
        )
    )
    return approval_hash == item.approval_set_hash and decision_count == len(required_roles)


def _work_item(run: RowMapping, outbox: Mapping[str, object], owner_hash: str) -> WorkItem:
    return WorkItem(
        organization_id=str(run["organization_id"]),
        outbox_id=str(outbox["outbox_id"]),
        run_id=str(run["run_id"]),
        executor_user_id=str(run["executor_user_id"]),
        task_id=str(run["task_id"]),  # type: ignore[arg-type]
        process=str(run["process"]),  # type: ignore[arg-type]
        category=str(run["category"]),  # type: ignore[arg-type]
        action_type=str(run["action_type"]),
        parameter_hash=str(run["parameter_hash"]),
        authorization_hash=str(run["authorization_hash"]),
        approval_request_id=run["approval_request_id"],
        grant_id=run["grant_id"],
        execution_id=run["execution_id"],
        approval_set_hash=run["approval_set_hash"],
        payload_reference=str(run["payload_reference"]),
        payload_hash=str(run["payload_hash"]),
        workflow_id=str(run["workflow_id"]),
        workflow_hash=str(run["workflow_hash"]),
        worker_owner_hash=owner_hash,
        fencing_token=_as_int(outbox["fencing_token"]),
        lease_version=_as_int(outbox["lease_version"]),
        attempt_count=_as_int(outbox["attempt_count"]),
        leased_at=_as_datetime(outbox["leased_at"]),
        lease_expires_at=_as_datetime(outbox["lease_expires_at"]),
    )


class WorkflowRepository:
    def __init__(self, engine: Engine, settings: WorkerSettings) -> None:
        self._engine = engine
        self._settings = settings
        self.owner_hash = stable_hash(settings.worker_instance_id)

    @classmethod
    def connect(cls, settings: WorkerSettings) -> "WorkflowRepository":
        connect_args = (
            {"check_same_thread": False}
            if settings.database_url.startswith("sqlite+pysqlite://")
            else {}
        )
        return cls(
            create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args),
            settings,
        )

    def close(self) -> None:
        self._engine.dispose()

    def ping(self) -> bool:
        with self._engine.connect() as connection:
            return connection.scalar(select(func.count()).select_from(PARTITIONS)) is not None

    def _lease_history(
        self,
        connection: Connection,
        outbox: RowMapping,
        *,
        status: str,
        now: datetime,
    ) -> None:
        if int(outbox["fencing_token"]) < 1 or outbox["leased_at"] is None:
            return
        connection.execute(
            insert(LEASES).values(
                lease_id=_opaque_id("lse"),
                organization_id=outbox["organization_id"],
                outbox_id=outbox["outbox_id"],
                run_id=outbox["run_id"],
                worker_owner_hash=outbox["lease_owner_hash"],
                lease_version=outbox["lease_version"],
                fencing_token=outbox["fencing_token"],
                leased_at=outbox["leased_at"],
                lease_expires_at=outbox["lease_expires_at"],
                heartbeat_at=outbox["heartbeat_at"] or outbox["leased_at"],
                attempt_count=outbox["attempt_count"],
                status=status,
                closed_at=now,
            )
        )

    def _record_stale_fence(
        self,
        connection: Connection,
        item: WorkItem,
        *,
        now: datetime,
    ) -> None:
        current = (
            connection.execute(
                select(OUTBOX)
                .where(
                    OUTBOX.c.organization_id == item.organization_id,
                    OUTBOX.c.outbox_id == item.outbox_id,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if current is None:
            return
        _append_audit(
            connection,
            organization_id=item.organization_id,
            event_type="stale_fence_rejected",
            actor_reference=item.worker_owner_hash,
            subject_reference=str(current["run_id"]),
            payload={
                "schema_version": "w12-audit-payload/1.0",
                "run_id": current["run_id"],
                "outbox_id": current["outbox_id"],
                "outbox_status": current["status"],
                "fencing_token": current["fencing_token"],
                "reason": "stale_fence",
            },
            now=now,
        )

    def claim_next(self, *, now: datetime) -> WorkItem | None:
        now = _utc(now)
        with self._engine.begin() as connection:
            partition = (
                connection.execute(
                    select(PARTITIONS)
                    .where(PARTITIONS.c.status == "ready", PARTITIONS.c.ready_count > 0)
                    .order_by(
                        PARTITIONS.c.last_selected_at.asc().nullsfirst(),
                        PARTITIONS.c.partition_id,
                    )
                    .limit(1)
                    .with_for_update(skip_locked=True)
                )
                .mappings()
                .one_or_none()
            )
            if partition is None:
                return None
            organization_id = str(partition["organization_id"])
            outbox = (
                connection.execute(
                    select(OUTBOX)
                    .where(
                        OUTBOX.c.organization_id == organization_id,
                        or_(
                            and_(OUTBOX.c.status == "ready", OUTBOX.c.available_at <= now),
                            and_(
                                OUTBOX.c.status.in_(("leased", "dispatched")),
                                OUTBOX.c.lease_expires_at <= now,
                            ),
                        ),
                    )
                    .order_by(OUTBOX.c.available_at, OUTBOX.c.outbox_id)
                    .limit(1)
                    .with_for_update(skip_locked=True)
                )
                .mappings()
                .one_or_none()
            )
            if outbox is None:
                connection.execute(
                    update(PARTITIONS)
                    .where(PARTITIONS.c.organization_id == organization_id)
                    .values(
                        status="ready",
                        last_selected_at=now,
                        cursor_version=PARTITIONS.c.cursor_version + 1,
                        updated_at=now,
                    )
                )
                return None
            run = (
                connection.execute(
                    select(RUNS)
                    .where(
                        RUNS.c.organization_id == organization_id,
                        RUNS.c.run_id == outbox["run_id"],
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if run is None:
                return None
            if _as_datetime(outbox["expires_at"]) <= now:
                self._lease_history(connection, outbox, status="expired", now=now)
                connection.execute(
                    update(OUTBOX)
                    .where(
                        OUTBOX.c.organization_id == organization_id,
                        OUTBOX.c.outbox_id == outbox["outbox_id"],
                    )
                    .values(status="expired", updated_at=now)
                )
                connection.execute(
                    update(RUNS)
                    .where(
                        RUNS.c.organization_id == organization_id,
                        RUNS.c.run_id == run["run_id"],
                    )
                    .values(
                        status="expired",
                        version=RUNS.c.version + 1,
                        finished_at=now,
                        terminal_reason="queue_expired",
                        updated_at=now,
                    )
                )
                connection.execute(
                    update(PARTITIONS)
                    .where(PARTITIONS.c.organization_id == organization_id)
                    .values(
                        ready_count=PARTITIONS.c.ready_count - 1,
                        cursor_version=PARTITIONS.c.cursor_version + 1,
                        updated_at=now,
                    )
                )
                sequence = _append_audit(
                    connection,
                    organization_id=organization_id,
                    event_type="run_expired",
                    actor_reference=self.owner_hash,
                    subject_reference=str(run["run_id"]),
                    payload={
                        "schema_version": "w12-audit-payload/1.0",
                        "run_id": run["run_id"],
                        "run_status": "expired",
                        "reason": "queue_expired",
                        "version": int(run["version"]) + 1,
                    },
                    now=now,
                )
                connection.execute(
                    update(RUNS)
                    .where(
                        RUNS.c.organization_id == organization_id,
                        RUNS.c.run_id == run["run_id"],
                    )
                    .values(audit_sequence=sequence)
                )
                return None
            if int(outbox["attempt_count"]) >= self._settings.maximum_attempts:
                self._fail_locked(
                    connection,
                    run,
                    outbox,
                    reason="lease_exhausted",
                    now=now,
                )
                return None
            reclaimed = str(outbox["status"]) != "ready"
            if reclaimed:
                self._lease_history(connection, outbox, status="expired", now=now)
            fence = int(outbox["fencing_token"]) + 1
            lease_version = int(outbox["lease_version"]) + 1
            attempt = int(outbox["attempt_count"]) + 1
            expires = now + timedelta(seconds=self._settings.lease_ttl_seconds)
            claim_result = connection.execute(
                update(OUTBOX)
                .where(
                    OUTBOX.c.organization_id == organization_id,
                    OUTBOX.c.outbox_id == outbox["outbox_id"],
                    OUTBOX.c.status == outbox["status"],
                    OUTBOX.c.fencing_token == outbox["fencing_token"],
                    OUTBOX.c.lease_version == outbox["lease_version"],
                )
                .values(
                    status="leased",
                    attempt_count=attempt,
                    fencing_token=fence,
                    lease_owner_hash=self.owner_hash,
                    lease_version=lease_version,
                    leased_at=now,
                    lease_expires_at=expires,
                    heartbeat_at=now,
                    updated_at=now,
                )
            )
            if claim_result.rowcount != 1:
                return None
            next_status = "recovering" if reclaimed else "leased"
            run_result = connection.execute(
                update(RUNS)
                .where(
                    RUNS.c.organization_id == organization_id,
                    RUNS.c.run_id == run["run_id"],
                    RUNS.c.status == run["status"],
                    RUNS.c.version == run["version"],
                    RUNS.c.fencing_token == run["fencing_token"],
                )
                .values(
                    status=next_status,
                    version=RUNS.c.version + 1,
                    lease_owner_hash=self.owner_hash,
                    fencing_token=fence,
                    lease_expires_at=expires,
                    updated_at=now,
                )
            )
            if run_result.rowcount != 1:
                raise RuntimeError("production run fence changed during claim")
            connection.execute(
                update(PARTITIONS)
                .where(PARTITIONS.c.organization_id == organization_id)
                .values(
                    status="ready",
                    last_selected_at=now,
                    cursor_version=PARTITIONS.c.cursor_version + 1,
                    updated_at=now,
                )
            )
            event_type = "run_recovered" if reclaimed else "run_leased"
            sequence = _append_audit(
                connection,
                organization_id=organization_id,
                event_type=event_type,
                actor_reference=self.owner_hash,
                subject_reference=str(run["run_id"]),
                payload={
                    "schema_version": "w12-audit-payload/1.0",
                    "run_id": run["run_id"],
                    "outbox_id": outbox["outbox_id"],
                    "run_status": next_status,
                    "fencing_token": fence,
                    "attempt_count": attempt,
                    "version": int(run["version"]) + 1,
                },
                now=now,
            )
            connection.execute(
                update(RUNS)
                .where(
                    RUNS.c.organization_id == organization_id,
                    RUNS.c.run_id == run["run_id"],
                    RUNS.c.fencing_token == fence,
                )
                .values(audit_sequence=sequence)
            )
            claimed_outbox = dict(outbox)
            claimed_outbox.update(
                fencing_token=fence,
                lease_version=lease_version,
                attempt_count=attempt,
                leased_at=now,
                lease_expires_at=expires,
            )
            return _work_item(run, claimed_outbox, self.owner_hash)

    def binding_valid(self, item: WorkItem, *, now: datetime) -> bool:
        with self._engine.connect() as connection:
            return _binding_valid(
                connection,
                item,
                _utc(now),
                check_expiry=False,
                lock=False,
            )

    def mark_started(self, item: WorkItem, *, now: datetime) -> bool:
        now = _utc(now)
        with self._engine.begin() as connection:
            outbox = (
                connection.execute(
                    select(OUTBOX)
                    .where(
                        OUTBOX.c.organization_id == item.organization_id,
                        OUTBOX.c.outbox_id == item.outbox_id,
                        OUTBOX.c.status == "leased",
                        OUTBOX.c.lease_owner_hash == item.worker_owner_hash,
                        OUTBOX.c.fencing_token == item.fencing_token,
                        OUTBOX.c.lease_expires_at > now,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if outbox is None:
                self._record_stale_fence(connection, item, now=now)
                return False
            run = (
                connection.execute(
                    select(RUNS)
                    .where(
                        RUNS.c.organization_id == item.organization_id,
                        RUNS.c.run_id == item.run_id,
                        RUNS.c.status.in_(("leased", "recovering")),
                        RUNS.c.lease_owner_hash == item.worker_owner_hash,
                        RUNS.c.fencing_token == item.fencing_token,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if run is None:
                self._record_stale_fence(connection, item, now=now)
                return False
            if not _binding_valid(
                connection,
                item,
                now,
                check_expiry=False,
                lock=True,
            ):
                self._fail_locked(
                    connection,
                    run,
                    outbox,
                    reason="authorization_invalid",
                    now=now,
                )
                return False
            connection.execute(
                update(OUTBOX)
                .where(
                    OUTBOX.c.organization_id == item.organization_id,
                    OUTBOX.c.outbox_id == item.outbox_id,
                    OUTBOX.c.fencing_token == item.fencing_token,
                )
                .values(status="dispatched", updated_at=now)
            )
            connection.execute(
                update(RUNS)
                .where(
                    RUNS.c.organization_id == item.organization_id,
                    RUNS.c.run_id == item.run_id,
                    RUNS.c.fencing_token == item.fencing_token,
                )
                .values(
                    status="running",
                    version=RUNS.c.version + 1,
                    started_at=func.coalesce(RUNS.c.started_at, now),
                    updated_at=now,
                )
            )
            sequence = _append_audit(
                connection,
                organization_id=item.organization_id,
                event_type="run_started",
                actor_reference=item.worker_owner_hash,
                subject_reference=item.run_id,
                payload={
                    "schema_version": "w12-audit-payload/1.0",
                    "run_id": item.run_id,
                    "outbox_id": item.outbox_id,
                    "run_status": "running",
                    "fencing_token": item.fencing_token,
                    "version": int(run["version"]) + 1,
                },
                now=now,
            )
            connection.execute(
                update(RUNS)
                .where(
                    RUNS.c.organization_id == item.organization_id,
                    RUNS.c.run_id == item.run_id,
                    RUNS.c.fencing_token == item.fencing_token,
                )
                .values(audit_sequence=sequence)
            )
            return True

    def heartbeat(self, item: WorkItem, *, now: datetime) -> bool:
        now = _utc(now)
        expires = now + timedelta(seconds=self._settings.lease_ttl_seconds)
        with self._engine.begin() as connection:
            result = connection.execute(
                update(OUTBOX)
                .where(
                    OUTBOX.c.organization_id == item.organization_id,
                    OUTBOX.c.outbox_id == item.outbox_id,
                    OUTBOX.c.status.in_(("leased", "dispatched")),
                    OUTBOX.c.lease_owner_hash == item.worker_owner_hash,
                    OUTBOX.c.fencing_token == item.fencing_token,
                    OUTBOX.c.lease_version == item.lease_version,
                    OUTBOX.c.lease_expires_at > now,
                )
                .values(heartbeat_at=now, lease_expires_at=expires, updated_at=now)
            )
            if result.rowcount != 1:
                self._record_stale_fence(connection, item, now=now)
                return False
            connection.execute(
                update(RUNS)
                .where(
                    RUNS.c.organization_id == item.organization_id,
                    RUNS.c.run_id == item.run_id,
                    RUNS.c.lease_owner_hash == item.worker_owner_hash,
                    RUNS.c.fencing_token == item.fencing_token,
                )
                .values(lease_expires_at=expires, updated_at=now)
            )
            _append_audit(
                connection,
                organization_id=item.organization_id,
                event_type="lease_heartbeat",
                actor_reference=item.worker_owner_hash,
                subject_reference=item.run_id,
                payload={
                    "schema_version": "w12-audit-payload/1.0",
                    "run_id": item.run_id,
                    "outbox_id": item.outbox_id,
                    "fencing_token": item.fencing_token,
                },
                now=now,
            )
            return True

    def record_deduplicated(self, item: WorkItem, *, now: datetime) -> bool:
        with self._engine.begin() as connection:
            current = connection.scalar(
                select(func.count())
                .select_from(OUTBOX)
                .where(
                    OUTBOX.c.organization_id == item.organization_id,
                    OUTBOX.c.outbox_id == item.outbox_id,
                    OUTBOX.c.lease_owner_hash == item.worker_owner_hash,
                    OUTBOX.c.fencing_token == item.fencing_token,
                )
            )
            if current != 1:
                self._record_stale_fence(connection, item, now=_utc(now))
                return False
            _append_audit(
                connection,
                organization_id=item.organization_id,
                event_type="workflow_deduplicated",
                actor_reference=item.worker_owner_hash,
                subject_reference=item.run_id,
                payload={
                    "schema_version": "w12-audit-payload/1.0",
                    "run_id": item.run_id,
                    "workflow_hash": item.workflow_hash,
                    "fencing_token": item.fencing_token,
                },
                now=_utc(now),
            )
            return True

    def _fail_locked(
        self,
        connection: Connection,
        run: RowMapping,
        outbox: RowMapping,
        *,
        reason: str,
        now: datetime,
    ) -> bool:
        self._lease_history(connection, outbox, status="failed", now=now)
        connection.execute(
            update(OUTBOX)
            .where(
                OUTBOX.c.organization_id == run["organization_id"],
                OUTBOX.c.outbox_id == outbox["outbox_id"],
            )
            .values(status="failed", updated_at=now)
        )
        connection.execute(
            update(RUNS)
            .where(
                RUNS.c.organization_id == run["organization_id"],
                RUNS.c.run_id == run["run_id"],
            )
            .values(
                status="failed",
                version=RUNS.c.version + 1,
                finished_at=now,
                terminal_reason=reason,
                updated_at=now,
            )
        )
        connection.execute(
            update(PARTITIONS)
            .where(PARTITIONS.c.organization_id == run["organization_id"])
            .values(
                ready_count=PARTITIONS.c.ready_count - 1,
                cursor_version=PARTITIONS.c.cursor_version + 1,
                updated_at=now,
            )
        )
        sequence = _append_audit(
            connection,
            organization_id=str(run["organization_id"]),
            event_type="run_failed",
            actor_reference=self.owner_hash,
            subject_reference=str(run["run_id"]),
            payload={
                "schema_version": "w12-audit-payload/1.0",
                "run_id": run["run_id"],
                "run_status": "failed",
                "reason": reason,
                "fencing_token": outbox["fencing_token"],
                "version": int(run["version"]) + 1,
            },
            now=now,
        )
        connection.execute(
            update(RUNS)
            .where(
                RUNS.c.organization_id == run["organization_id"],
                RUNS.c.run_id == run["run_id"],
            )
            .values(audit_sequence=sequence)
        )
        request_id = run["approval_request_id"]
        grant_id = run["grant_id"]
        execution_id = run["execution_id"]
        if request_id is not None and grant_id is not None and execution_id is not None:
            request = (
                connection.execute(
                    select(REQUESTS)
                    .where(
                        REQUESTS.c.organization_id == run["organization_id"],
                        REQUESTS.c.request_id == request_id,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            grant = (
                connection.execute(
                    select(GRANTS)
                    .where(
                        GRANTS.c.organization_id == run["organization_id"],
                        GRANTS.c.grant_id == grant_id,
                        GRANTS.c.request_id == request_id,
                        GRANTS.c.execution_id == execution_id,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if (
                request is not None
                and grant is not None
                and request["status"] == "claimed"
                and grant["status"] == "claimed"
            ):
                connection.execute(
                    update(REQUESTS)
                    .where(
                        REQUESTS.c.organization_id == run["organization_id"],
                        REQUESTS.c.request_id == request_id,
                        REQUESTS.c.status == "claimed",
                    )
                    .values(
                        status="failed",
                        version=REQUESTS.c.version + 1,
                        updated_at=now,
                    )
                )
                connection.execute(
                    update(GRANTS)
                    .where(
                        GRANTS.c.organization_id == run["organization_id"],
                        GRANTS.c.grant_id == grant_id,
                        GRANTS.c.execution_id == execution_id,
                        GRANTS.c.status == "claimed",
                    )
                    .values(
                        status="failed",
                        version=GRANTS.c.version + 1,
                        updated_at=now,
                    )
                )
                _append_audit(
                    connection,
                    organization_id=str(run["organization_id"]),
                    event_type="execution_failed",
                    actor_reference=self.owner_hash,
                    subject_reference=str(grant_id),
                    payload={
                        "schema_version": "w11-audit-payload/1.0",
                        "request_id": request_id,
                        "grant_id": grant_id,
                        "grant_status": "failed",
                        "execution_id": execution_id,
                        "reason": reason,
                    },
                    now=now,
                )
        return True

    def fail(self, item: WorkItem, *, reason: str, now: datetime) -> bool:
        now = _utc(now)
        with self._engine.begin() as connection:
            outbox = (
                connection.execute(
                    select(OUTBOX)
                    .where(
                        OUTBOX.c.organization_id == item.organization_id,
                        OUTBOX.c.outbox_id == item.outbox_id,
                        OUTBOX.c.status.in_(("leased", "dispatched")),
                        OUTBOX.c.lease_owner_hash == item.worker_owner_hash,
                        OUTBOX.c.fencing_token == item.fencing_token,
                        OUTBOX.c.lease_version == item.lease_version,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            run = (
                connection.execute(
                    select(RUNS)
                    .where(
                        RUNS.c.organization_id == item.organization_id,
                        RUNS.c.run_id == item.run_id,
                        RUNS.c.status.in_(("leased", "recovering", "running")),
                        RUNS.c.lease_owner_hash == item.worker_owner_hash,
                        RUNS.c.fencing_token == item.fencing_token,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if outbox is None or run is None:
                self._record_stale_fence(connection, item, now=now)
                return False
            return self._fail_locked(connection, run, outbox, reason=reason, now=now)

    def complete(self, item: WorkItem, outcome: TemporalOutcome, *, now: datetime) -> bool:
        now = _utc(now)
        with self._engine.begin() as connection:
            outbox = (
                connection.execute(
                    select(OUTBOX)
                    .where(
                        OUTBOX.c.organization_id == item.organization_id,
                        OUTBOX.c.outbox_id == item.outbox_id,
                        OUTBOX.c.status == "dispatched",
                        OUTBOX.c.lease_owner_hash == item.worker_owner_hash,
                        OUTBOX.c.fencing_token == item.fencing_token,
                        OUTBOX.c.lease_version == item.lease_version,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            run = (
                connection.execute(
                    select(RUNS)
                    .where(
                        RUNS.c.organization_id == item.organization_id,
                        RUNS.c.run_id == item.run_id,
                        RUNS.c.status == "running",
                        RUNS.c.lease_owner_hash == item.worker_owner_hash,
                        RUNS.c.fencing_token == item.fencing_token,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if outbox is None or run is None:
                self._record_stale_fence(connection, item, now=now)
                return False
            if not _binding_valid(
                connection,
                item,
                now,
                check_expiry=False,
                lock=True,
            ):
                return self._fail_locked(
                    connection,
                    run,
                    outbox,
                    reason="authorization_invalid",
                    now=now,
                )
            receipt_reference = outcome.result.latest_checkpoint_hash or stable_hash(outcome.result)
            successful = outcome.result.status == "finished_ungraded"
            if successful:
                connection.execute(
                    update(RUNS)
                    .where(
                        RUNS.c.organization_id == item.organization_id,
                        RUNS.c.run_id == item.run_id,
                        RUNS.c.fencing_token == item.fencing_token,
                    )
                    .values(status="verifying", version=RUNS.c.version + 1, updated_at=now)
                )
                _append_audit(
                    connection,
                    organization_id=item.organization_id,
                    event_type="run_verifying",
                    actor_reference=item.worker_owner_hash,
                    subject_reference=item.run_id,
                    payload={
                        "schema_version": "w12-audit-payload/1.0",
                        "run_id": item.run_id,
                        "run_status": "verifying",
                        "receipt_reference": receipt_reference,
                        "fencing_token": item.fencing_token,
                        "version": int(run["version"]) + 1,
                    },
                    now=now,
                )
                terminal_status = "finished_ungraded"
                terminal_reason = "agent_finished"
                lease_status = "completed"
                event_type = "run_finished_ungraded"
            else:
                terminal_status = "failed"
                terminal_reason = "agent_failed"
                lease_status = "failed"
                event_type = "run_failed"
            self._lease_history(connection, outbox, status=lease_status, now=now)
            connection.execute(
                update(OUTBOX)
                .where(
                    OUTBOX.c.organization_id == item.organization_id,
                    OUTBOX.c.outbox_id == item.outbox_id,
                    OUTBOX.c.fencing_token == item.fencing_token,
                )
                .values(status="closed" if successful else "failed", updated_at=now)
            )
            terminal_version = int(run["version"]) + (2 if successful else 1)
            connection.execute(
                update(RUNS)
                .where(
                    RUNS.c.organization_id == item.organization_id,
                    RUNS.c.run_id == item.run_id,
                    RUNS.c.fencing_token == item.fencing_token,
                )
                .values(
                    status=terminal_status,
                    version=terminal_version,
                    finished_at=now,
                    terminal_reason=terminal_reason,
                    receipt_reference=receipt_reference,
                    updated_at=now,
                )
            )
            connection.execute(
                update(PARTITIONS)
                .where(PARTITIONS.c.organization_id == item.organization_id)
                .values(
                    ready_count=PARTITIONS.c.ready_count - 1,
                    cursor_version=PARTITIONS.c.cursor_version + 1,
                    updated_at=now,
                )
            )
            sequence = _append_audit(
                connection,
                organization_id=item.organization_id,
                event_type=event_type,
                actor_reference=item.worker_owner_hash,
                subject_reference=item.run_id,
                payload={
                    "schema_version": "w12-audit-payload/1.0",
                    "run_id": item.run_id,
                    "run_status": terminal_status,
                    "reason": terminal_reason,
                    "receipt_reference": receipt_reference,
                    "fencing_token": item.fencing_token,
                    "version": terminal_version,
                },
                now=now,
            )
            connection.execute(
                update(RUNS)
                .where(
                    RUNS.c.organization_id == item.organization_id,
                    RUNS.c.run_id == item.run_id,
                    RUNS.c.fencing_token == item.fencing_token,
                )
                .values(audit_sequence=sequence)
            )
            if item.grant_id is not None and item.approval_request_id is not None:
                grant_status = "consumed" if successful else "failed"
                request_status = "consumed" if successful else "failed"
                grant_result = connection.execute(
                    update(GRANTS)
                    .where(
                        GRANTS.c.organization_id == item.organization_id,
                        GRANTS.c.grant_id == item.grant_id,
                        GRANTS.c.execution_id == item.execution_id,
                        GRANTS.c.status == "claimed",
                    )
                    .values(
                        status=grant_status,
                        version=GRANTS.c.version + 1,
                        receipt_reference=receipt_reference,
                        consumed_at=now if successful else None,
                        updated_at=now,
                    )
                )
                request_result = connection.execute(
                    update(REQUESTS)
                    .where(
                        REQUESTS.c.organization_id == item.organization_id,
                        REQUESTS.c.request_id == item.approval_request_id,
                        REQUESTS.c.status == "claimed",
                    )
                    .values(
                        status=request_status,
                        version=REQUESTS.c.version + 1,
                        updated_at=now,
                    )
                )
                if grant_result.rowcount != 1 or request_result.rowcount != 1:
                    raise RuntimeError("approval completion binding changed")
                _append_audit(
                    connection,
                    organization_id=item.organization_id,
                    event_type="grant_consumed" if successful else "execution_failed",
                    actor_reference=item.worker_owner_hash,
                    subject_reference=item.grant_id,
                    payload={
                        "schema_version": "w11-audit-payload/1.0",
                        "request_id": item.approval_request_id,
                        "grant_id": item.grant_id,
                        "grant_status": grant_status,
                        "execution_id": item.execution_id,
                        "receipt_reference": receipt_reference,
                    },
                    now=now,
                )
            else:
                _append_audit(
                    connection,
                    organization_id=item.organization_id,
                    event_type="execution_succeeded" if successful else "execution_failed",
                    actor_reference=item.worker_owner_hash,
                    subject_reference=item.run_id,
                    payload={
                        "schema_version": "w11-audit-payload/1.0",
                        "action_type": item.action_type,
                        "parameter_hash": item.parameter_hash,
                        "receipt_reference": receipt_reference,
                    },
                    now=now,
                )
            return True

    def release(self, item: WorkItem, *, now: datetime) -> bool:
        now = _utc(now)
        with self._engine.begin() as connection:
            outbox = (
                connection.execute(
                    select(OUTBOX)
                    .where(
                        OUTBOX.c.organization_id == item.organization_id,
                        OUTBOX.c.outbox_id == item.outbox_id,
                        OUTBOX.c.status.in_(("leased", "dispatched")),
                        OUTBOX.c.lease_owner_hash == item.worker_owner_hash,
                        OUTBOX.c.fencing_token == item.fencing_token,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if outbox is None:
                self._record_stale_fence(connection, item, now=now)
                return False
            self._lease_history(connection, outbox, status="released", now=now)
            connection.execute(
                update(OUTBOX)
                .where(
                    OUTBOX.c.organization_id == item.organization_id,
                    OUTBOX.c.outbox_id == item.outbox_id,
                    OUTBOX.c.fencing_token == item.fencing_token,
                )
                .values(
                    status="ready",
                    lease_owner_hash=None,
                    lease_expires_at=None,
                    heartbeat_at=None,
                    updated_at=now,
                )
            )
            connection.execute(
                update(RUNS)
                .where(
                    RUNS.c.organization_id == item.organization_id,
                    RUNS.c.run_id == item.run_id,
                    RUNS.c.fencing_token == item.fencing_token,
                )
                .values(
                    status="queued",
                    version=RUNS.c.version + 1,
                    lease_owner_hash=None,
                    lease_expires_at=None,
                    updated_at=now,
                )
            )
            _append_audit(
                connection,
                organization_id=item.organization_id,
                event_type="lease_released",
                actor_reference=item.worker_owner_hash,
                subject_reference=item.run_id,
                payload={
                    "schema_version": "w12-audit-payload/1.0",
                    "run_id": item.run_id,
                    "outbox_id": item.outbox_id,
                    "run_status": "queued",
                    "fencing_token": item.fencing_token,
                    "reason": "worker_drained",
                },
                now=now,
            )
            return True
