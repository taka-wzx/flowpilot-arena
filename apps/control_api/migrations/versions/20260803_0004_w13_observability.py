"""Add W13 append-only observability events.

Revision ID: 20260803_0004
Revises: 20260801_0003
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260803_0004"
down_revision: str | None = "20260801_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "w13_observability_events",
        sa.Column("event_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("run_id", sa.String(length=68), nullable=False),
        sa.Column("event_sequence", sa.Integer(), nullable=False),
        sa.Column("trace_id", sa.String(length=32), nullable=False),
        sa.Column("span_id", sa.String(length=16), nullable=False),
        sa.Column("parent_span_id", sa.String(length=16), nullable=True),
        sa.Column("phase", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("failure_category", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("attributes_json", sa.Text(), nullable=False),
        sa.Column("attributes_hash", sa.String(length=64), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id", "run_id"],
            ["w12_production_runs.organization_id", "w12_production_runs.run_id"],
            name="fk_w13_event_org_run",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("event_id", name="pk_w13_observability_events"),
        sa.UniqueConstraint("organization_id", "event_id", name="uq_w13_event_owner"),
        sa.UniqueConstraint(
            "organization_id",
            "run_id",
            "event_sequence",
            name="uq_w13_event_run_sequence",
        ),
        sa.CheckConstraint("event_sequence BETWEEN 1 AND 256", name="ck_w13_event_sequence"),
        sa.CheckConstraint("length(trace_id) = 32", name="ck_w13_trace_id"),
        sa.CheckConstraint("length(span_id) = 16", name="ck_w13_span_id"),
        sa.CheckConstraint(
            "parent_span_id IS NULL OR length(parent_span_id) = 16",
            name="ck_w13_parent_span_id",
        ),
        sa.CheckConstraint(
            "phase IN ('admission', 'approval', 'outbox', 'lease', 'dispatch', "
            "'workflow', 'recovery', 'planning', 'browser', 'receipt', 'grader', "
            "'audit', 'cost', 'terminal', 'replay', 'dashboard')",
            name="ck_w13_phase",
        ),
        sa.CheckConstraint(
            "status IN ('accepted', 'waiting', 'queued', 'leased', 'running', "
            "'recovered', 'released', 'succeeded', 'failed', 'rejected', "
            "'cancelled', 'pending', 'exported')",
            name="ck_w13_status",
        ),
        sa.CheckConstraint(
            "failure_category IN ('none', 'authn', 'authz', 'approval', 'schema', "
            "'rate_limit', 'backpressure', 'queue_expiry', 'lease_fence', "
            "'workflow_rejected', 'dependency_unavailable', 'browser_timeout', "
            "'browser_error', 'planning_failure', 'recovery_failure', "
            "'receipt_invalid', 'grader_verification', 'audit_verification')",
            name="ck_w13_failure_category",
        ),
        sa.CheckConstraint(
            "reason IN ('admitted_queued', 'admitted_waiting_approval', "
            "'approval_handoff', 'outbox_ready', 'lease_claimed', "
            "'lease_recovered', 'lease_heartbeat', 'lease_released', "
            "'stale_fence_rejected', 'worker_dispatched', 'temporal_reference', "
            "'temporal_deduplicated', 'recovery_summary', 'planning_summary', "
            "'browser_step', 'browser_summary', 'receipt_recorded', "
            "'grader_pending', 'audit_reference', 'fake_cost_accounted', "
            "'run_finished_ungraded', 'run_failed', 'run_cancelled', "
            "'run_expired', 'replay_exported', 'dashboard_exported')",
            name="ck_w13_reason",
        ),
        sa.CheckConstraint("length(attributes_json) <= 2048", name="ck_w13_attributes_size"),
        sa.CheckConstraint("length(attributes_hash) = 64", name="ck_w13_attributes_hash"),
        sa.CheckConstraint("length(event_hash) = 64", name="ck_w13_event_hash"),
    )
    op.create_index(
        "ix_w13_events_org_run_sequence",
        "w13_observability_events",
        ["organization_id", "run_id", "event_sequence"],
    )
    op.create_index(
        "ix_w13_events_org_phase_status",
        "w13_observability_events",
        ["organization_id", "phase", "status"],
    )
    _create_immutable_triggers()


def _create_immutable_triggers() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION w13_reject_observability_change() RETURNS trigger AS $$
            BEGIN
              RAISE EXCEPTION 'w13 immutable row';
            END;
            $$ LANGUAGE plpgsql
            """
        )
        op.execute(
            "CREATE TRIGGER trg_w13_observability_events_immutable "
            "BEFORE UPDATE OR DELETE ON w13_observability_events "
            "FOR EACH ROW EXECUTE FUNCTION w13_reject_observability_change()"
        )
    elif bind.dialect.name == "sqlite":
        op.execute(
            "CREATE TRIGGER trg_w13_observability_events_update "
            "BEFORE UPDATE ON w13_observability_events "
            "BEGIN SELECT RAISE(ABORT, 'w13 immutable row'); END"
        )
        op.execute(
            "CREATE TRIGGER trg_w13_observability_events_delete "
            "BEFORE DELETE ON w13_observability_events "
            "BEGIN SELECT RAISE(ABORT, 'w13 immutable row'); END"
        )


def _drop_immutable_triggers() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS trg_w13_observability_events_immutable ON "
            "w13_observability_events"
        )
        op.execute("DROP FUNCTION IF EXISTS w13_reject_observability_change()")
    elif bind.dialect.name == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS trg_w13_observability_events_update")
        op.execute("DROP TRIGGER IF EXISTS trg_w13_observability_events_delete")


def downgrade() -> None:
    _drop_immutable_triggers()
    op.drop_index("ix_w13_events_org_phase_status", table_name="w13_observability_events")
    op.drop_index("ix_w13_events_org_run_sequence", table_name="w13_observability_events")
    op.drop_table("w13_observability_events")
