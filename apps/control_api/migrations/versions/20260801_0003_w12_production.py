"""Add W12 durable production admission, dispatch, lease, and rate state.

Revision ID: 20260801_0003
Revises: 20260729_0002
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0003"
down_revision: str | None = "20260729_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

W11_AUDIT_EVENTS = (
    "risk_classified",
    "l4_denied",
    "approval_requested",
    "approval_approved",
    "approval_rejected",
    "request_cancelled",
    "request_expired",
    "request_invalidated",
    "grant_issued",
    "grant_claimed",
    "grant_consumed",
    "grant_rejected",
    "execution_started",
    "execution_succeeded",
    "execution_failed",
    "recovery_resumed",
    "authority_disabled",
    "audit_verified",
)
W12_AUDIT_EVENTS = (
    "run_waiting_approval",
    "run_queued",
    "run_leased",
    "run_started",
    "run_recovered",
    "run_verifying",
    "run_finished_ungraded",
    "run_failed",
    "run_cancelled",
    "run_expired",
    "admission_rejected",
    "backpressure_rejected",
    "rate_limited",
    "lease_heartbeat",
    "lease_released",
    "stale_fence_rejected",
    "workflow_deduplicated",
)


def _event_check(events: tuple[str, ...]) -> str:
    return "event_type IN (" + ", ".join(f"'{event}'" for event in events) + ")"


def _replace_audit_event_check(events: tuple[str, ...]) -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("w11_audit_events", recreate="always") as batch:
            batch.drop_constraint("ck_w11_audit_event_type", type_="check")
            batch.create_check_constraint("ck_w11_audit_event_type", _event_check(events))
        op.execute(
            "CREATE TRIGGER trg_w11_audit_events_update BEFORE UPDATE ON w11_audit_events "
            "BEGIN SELECT RAISE(ABORT, 'w11 immutable row'); END"
        )
        op.execute(
            "CREATE TRIGGER trg_w11_audit_events_delete BEFORE DELETE ON w11_audit_events "
            "BEGIN SELECT RAISE(ABORT, 'w11 immutable row'); END"
        )
    else:
        op.drop_constraint("ck_w11_audit_event_type", "w11_audit_events", type_="check")
        op.create_check_constraint(
            "ck_w11_audit_event_type",
            "w11_audit_events",
            _event_check(events),
        )


def upgrade() -> None:
    _replace_audit_event_check(W11_AUDIT_EVENTS + W12_AUDIT_EVENTS)
    op.create_table(
        "w12_production_runs",
        sa.Column("run_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("requester_user_id", sa.String(length=68), nullable=False),
        sa.Column("executor_user_id", sa.String(length=68), nullable=False),
        sa.Column("task_id", sa.String(length=40), nullable=False),
        sa.Column("process", sa.String(length=16), nullable=False),
        sa.Column("category", sa.String(length=24), nullable=False),
        sa.Column("approval_request_id", sa.String(length=68), nullable=True),
        sa.Column("grant_id", sa.String(length=68), nullable=True),
        sa.Column("execution_id", sa.String(length=68), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("parameter_hash", sa.String(length=64), nullable=False),
        sa.Column("authorization_hash", sa.String(length=64), nullable=False),
        sa.Column("approval_set_hash", sa.String(length=64), nullable=True),
        sa.Column("payload_reference", sa.String(length=80), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("idempotency_hash", sa.String(length=64), nullable=False),
        sa.Column("body_hash", sa.String(length=64), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("workflow_hash", sa.String(length=64), nullable=False),
        sa.Column("lease_owner_hash", sa.String(length=64), nullable=True),
        sa.Column("fencing_token", sa.Integer(), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("terminal_reason", sa.String(length=32), nullable=True),
        sa.Column("receipt_reference", sa.String(length=80), nullable=True),
        sa.Column("audit_sequence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id", "requester_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            name="fk_w12_run_org_requester",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "executor_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            name="fk_w12_run_org_executor",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "approval_request_id"],
            ["w11_approval_requests.organization_id", "w11_approval_requests.request_id"],
            name="fk_w12_run_org_approval_request",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "grant_id"],
            ["w11_approval_grants.organization_id", "w11_approval_grants.grant_id"],
            name="fk_w12_run_org_grant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "execution_id"],
            ["w11_approval_grants.organization_id", "w11_approval_grants.execution_id"],
            name="fk_w12_run_org_execution",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("run_id", name="pk_w12_production_runs"),
        sa.UniqueConstraint("organization_id", "run_id", name="uq_w12_run_owner"),
        sa.UniqueConstraint(
            "organization_id", "approval_request_id", name="uq_w12_run_approval_request"
        ),
        sa.UniqueConstraint("organization_id", "execution_id", name="uq_w12_run_execution"),
        sa.CheckConstraint(
            "task_id IN ('w7-jml-joiner-001-v1', 'w7-jml-joiner-001-v2', "
            "'w7-jml-joiner-002-v1', 'w7-jml-joiner-002-v2', "
            "'w7-jml-mover-001-v1', 'w7-jml-mover-001-v2', "
            "'w7-jml-leaver-001-v1', 'w7-jml-leaver-001-v2')",
            name="ck_w12_run_task",
        ),
        sa.CheckConstraint("process IN ('joiner', 'mover', 'leaver')", name="ck_w12_run_process"),
        sa.CheckConstraint(
            "category IN ('standard_joiner', 'standard_mover', 'standard_leaver')",
            name="ck_w12_run_category",
        ),
        sa.CheckConstraint(
            "((process = 'joiner' AND category = 'standard_joiner' AND task_id IN "
            "('w7-jml-joiner-001-v1', 'w7-jml-joiner-001-v2', "
            "'w7-jml-joiner-002-v1', 'w7-jml-joiner-002-v2')) OR "
            "(process = 'mover' AND category = 'standard_mover' AND "
            "task_id IN ('w7-jml-mover-001-v1', 'w7-jml-mover-001-v2')) OR "
            "(process = 'leaver' AND category = 'standard_leaver' AND "
            "task_id IN ('w7-jml-leaver-001-v1', 'w7-jml-leaver-001-v2')))",
            name="ck_w12_run_task_binding",
        ),
        sa.CheckConstraint(
            "status IN ('waiting_approval', 'queued', 'leased', 'running', 'recovering', "
            "'verifying', 'finished_ungraded', 'failed', 'cancelled', 'expired')",
            name="ck_w12_run_status",
        ),
        sa.CheckConstraint("version >= 1", name="ck_w12_run_version"),
        sa.CheckConstraint("fencing_token >= 0", name="ck_w12_run_fence"),
        sa.CheckConstraint("audit_sequence >= 1", name="ck_w12_run_audit_sequence"),
        sa.CheckConstraint("length(parameter_hash) = 64", name="ck_w12_run_parameter_hash"),
        sa.CheckConstraint("length(authorization_hash) = 64", name="ck_w12_run_auth_hash"),
        sa.CheckConstraint(
            "approval_set_hash IS NULL OR length(approval_set_hash) = 64",
            name="ck_w12_run_approval_set_hash",
        ),
        sa.CheckConstraint("length(payload_hash) = 64", name="ck_w12_run_payload_hash"),
        sa.CheckConstraint("length(idempotency_hash) = 64", name="ck_w12_run_idem_hash"),
        sa.CheckConstraint("length(body_hash) = 64", name="ck_w12_run_body_hash"),
        sa.CheckConstraint("length(workflow_hash) = 64", name="ck_w12_run_workflow_hash"),
        sa.CheckConstraint(
            "lease_owner_hash IS NULL OR length(lease_owner_hash) = 64",
            name="ck_w12_run_lease_owner_hash",
        ),
        sa.CheckConstraint(
            "terminal_reason IS NULL OR terminal_reason IN ('agent_finished', "
            "'agent_failed', 'authorization_invalid', 'queue_expired', "
            "'lease_exhausted', 'cancelled_by_actor', 'workflow_rejected', "
            "'receipt_invalid', 'worker_drained', 'dependency_unavailable')",
            name="ck_w12_run_terminal_reason",
        ),
    )
    op.create_index(
        "ix_w12_runs_org_status_accepted",
        "w12_production_runs",
        ["organization_id", "status", "accepted_at", "run_id"],
    )
    op.create_index(
        "ix_w12_runs_org_executor_status",
        "w12_production_runs",
        ["organization_id", "executor_user_id", "status"],
    )

    op.create_table(
        "w12_dispatch_outbox",
        sa.Column("outbox_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("run_id", sa.String(length=68), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("fencing_token", sa.Integer(), nullable=False),
        sa.Column("lease_owner_hash", sa.String(length=64), nullable=True),
        sa.Column("lease_version", sa.Integer(), nullable=False),
        sa.Column("leased_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id", "run_id"],
            ["w12_production_runs.organization_id", "w12_production_runs.run_id"],
            name="fk_w12_outbox_org_run",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("outbox_id", name="pk_w12_dispatch_outbox"),
        sa.UniqueConstraint("organization_id", "outbox_id", name="uq_w12_outbox_owner"),
        sa.UniqueConstraint("organization_id", "run_id", name="uq_w12_outbox_run"),
        sa.CheckConstraint(
            "status IN ('ready', 'leased', 'dispatched', 'closed', 'cancelled', "
            "'expired', 'failed')",
            name="ck_w12_outbox_status",
        ),
        sa.CheckConstraint("attempt_count BETWEEN 0 AND 3", name="ck_w12_outbox_attempts"),
        sa.CheckConstraint("fencing_token >= 0", name="ck_w12_outbox_fence"),
        sa.CheckConstraint("lease_version >= 0", name="ck_w12_outbox_lease_version"),
        sa.CheckConstraint(
            "lease_owner_hash IS NULL OR length(lease_owner_hash) = 64",
            name="ck_w12_outbox_lease_owner_hash",
        ),
    )
    op.create_index(
        "ix_w12_outbox_org_status_available",
        "w12_dispatch_outbox",
        ["organization_id", "status", "available_at", "outbox_id"],
    )
    op.create_index(
        "ix_w12_outbox_status_lease_expiry",
        "w12_dispatch_outbox",
        ["status", "lease_expires_at", "outbox_id"],
    )

    op.create_table(
        "w12_worker_leases",
        sa.Column("lease_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("outbox_id", sa.String(length=68), nullable=False),
        sa.Column("run_id", sa.String(length=68), nullable=False),
        sa.Column("worker_owner_hash", sa.String(length=64), nullable=False),
        sa.Column("lease_version", sa.Integer(), nullable=False),
        sa.Column("fencing_token", sa.Integer(), nullable=False),
        sa.Column("leased_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id", "outbox_id"],
            ["w12_dispatch_outbox.organization_id", "w12_dispatch_outbox.outbox_id"],
            name="fk_w12_lease_org_outbox",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "run_id"],
            ["w12_production_runs.organization_id", "w12_production_runs.run_id"],
            name="fk_w12_lease_org_run",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("lease_id", name="pk_w12_worker_leases"),
        sa.UniqueConstraint("organization_id", "lease_id", name="uq_w12_lease_owner"),
        sa.UniqueConstraint(
            "organization_id", "outbox_id", "fencing_token", name="uq_w12_lease_fence"
        ),
        sa.CheckConstraint("length(worker_owner_hash) = 64", name="ck_w12_lease_owner_hash"),
        sa.CheckConstraint("lease_version >= 1", name="ck_w12_lease_version"),
        sa.CheckConstraint("fencing_token >= 1", name="ck_w12_lease_fence"),
        sa.CheckConstraint("attempt_count BETWEEN 1 AND 3", name="ck_w12_lease_attempts"),
        sa.CheckConstraint(
            "status IN ('active', 'released', 'expired', 'completed', 'failed')",
            name="ck_w12_lease_status",
        ),
    )
    op.create_index(
        "ix_w12_leases_org_run_fence",
        "w12_worker_leases",
        ["organization_id", "run_id", "fencing_token"],
    )

    op.create_table(
        "w12_scheduler_partitions",
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("partition_id", sa.String(length=68), nullable=False),
        sa.Column("ready_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("cursor_version", sa.Integer(), nullable=False),
        sa.Column("last_selected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["w10_organizations.organization_id"],
            name="fk_w12_partition_organization",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("organization_id", name="pk_w12_scheduler_partitions"),
        sa.UniqueConstraint("partition_id", name="uq_w12_partition_id"),
        sa.CheckConstraint("ready_count BETWEEN 0 AND 32", name="ck_w12_partition_ready"),
        sa.CheckConstraint(
            "status IN ('ready', 'empty', 'disabled')", name="ck_w12_partition_status"
        ),
        sa.CheckConstraint("cursor_version >= 1", name="ck_w12_partition_version"),
    )
    op.create_index(
        "ix_w12_partitions_status_selected",
        "w12_scheduler_partitions",
        ["status", "last_selected_at", "partition_id"],
    )

    op.create_table(
        "w12_rate_limit_buckets",
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("bucket_key_hash", sa.String(length=64), nullable=False),
        sa.Column("scope_kind", sa.String(length=16), nullable=False),
        sa.Column("route_class", sa.String(length=24), nullable=False),
        sa.Column("tokens_micro", sa.BigInteger(), nullable=False),
        sa.Column("last_refill_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["w10_organizations.organization_id"],
            name="fk_w12_bucket_organization",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "organization_id",
            "bucket_key_hash",
            "route_class",
            name="pk_w12_rate_limit_buckets",
        ),
        sa.CheckConstraint("length(bucket_key_hash) = 64", name="ck_w12_bucket_key_hash"),
        sa.CheckConstraint("scope_kind IN ('actor', 'organization')", name="ck_w12_bucket_scope"),
        sa.CheckConstraint(
            "route_class IN ('production_submit', 'production_read', 'production_mutate')",
            name="ck_w12_bucket_route",
        ),
        sa.CheckConstraint("tokens_micro >= 0", name="ck_w12_bucket_tokens"),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_w12_bucket_status"),
        sa.CheckConstraint("version >= 1", name="ck_w12_bucket_version"),
    )
    op.create_index(
        "ix_w12_buckets_org_route_scope",
        "w12_rate_limit_buckets",
        ["organization_id", "route_class", "scope_kind"],
    )

    op.create_table(
        "w12_idempotency_records",
        sa.Column("idempotency_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("actor_user_id", sa.String(length=68), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("body_hash", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=68), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id", "actor_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            name="fk_w12_idempotency_org_actor",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "run_id"],
            ["w12_production_runs.organization_id", "w12_production_runs.run_id"],
            name="fk_w12_idempotency_org_run",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("idempotency_id", name="pk_w12_idempotency_records"),
        sa.UniqueConstraint(
            "organization_id",
            "actor_user_id",
            "key_hash",
            name="uq_w12_idempotency_actor_key",
        ),
        sa.UniqueConstraint("organization_id", "idempotency_id", name="uq_w12_idempotency_owner"),
        sa.CheckConstraint("length(key_hash) = 64", name="ck_w12_idempotency_key_hash"),
        sa.CheckConstraint("length(body_hash) = 64", name="ck_w12_idempotency_body_hash"),
    )
    op.create_index(
        "ix_w12_idempotency_org_run",
        "w12_idempotency_records",
        ["organization_id", "run_id"],
    )
    _create_immutable_triggers()


def _create_immutable_triggers() -> None:
    bind = op.get_bind()
    tables = ("w12_worker_leases", "w12_idempotency_records")
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION w12_reject_immutable_change() RETURNS trigger AS $$
            BEGIN
              RAISE EXCEPTION 'w12 immutable row';
            END;
            $$ LANGUAGE plpgsql
            """
        )
        for table in tables:
            op.execute(
                f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE OR DELETE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION w12_reject_immutable_change()"
            )
    elif bind.dialect.name == "sqlite":
        for table in tables:
            op.execute(
                f"CREATE TRIGGER trg_{table}_update BEFORE UPDATE ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'w12 immutable row'); END"
            )
            op.execute(
                f"CREATE TRIGGER trg_{table}_delete BEFORE DELETE ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'w12 immutable row'); END"
            )


def _drop_immutable_triggers() -> None:
    bind = op.get_bind()
    tables = ("w12_worker_leases", "w12_idempotency_records")
    if bind.dialect.name == "postgresql":
        for table in tables:
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON {table}")
        op.execute("DROP FUNCTION IF EXISTS w12_reject_immutable_change()")
    elif bind.dialect.name == "sqlite":
        for table in tables:
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_update")
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_delete")


def downgrade() -> None:
    _drop_immutable_triggers()
    op.drop_index("ix_w12_idempotency_org_run", table_name="w12_idempotency_records")
    op.drop_table("w12_idempotency_records")
    op.drop_index("ix_w12_buckets_org_route_scope", table_name="w12_rate_limit_buckets")
    op.drop_table("w12_rate_limit_buckets")
    op.drop_index("ix_w12_partitions_status_selected", table_name="w12_scheduler_partitions")
    op.drop_table("w12_scheduler_partitions")
    op.drop_index("ix_w12_leases_org_run_fence", table_name="w12_worker_leases")
    op.drop_table("w12_worker_leases")
    op.drop_index("ix_w12_outbox_status_lease_expiry", table_name="w12_dispatch_outbox")
    op.drop_index("ix_w12_outbox_org_status_available", table_name="w12_dispatch_outbox")
    op.drop_table("w12_dispatch_outbox")
    op.drop_index("ix_w12_runs_org_executor_status", table_name="w12_production_runs")
    op.drop_index("ix_w12_runs_org_status_accepted", table_name="w12_production_runs")
    op.drop_table("w12_production_runs")
    _replace_audit_event_check(W11_AUDIT_EVENTS)
