"""Add W3 Arena task ownership and human baseline records.

Revision ID: 20260726_0002
Revises: 20260726_0001
Create Date: 2026-07-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260726_0002"
down_revision: str | None = "20260726_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TASK_OWNED_TABLES = (
    "employees",
    "onboarding_tickets",
    "iam_accounts",
    "asset_assignments",
    "mailboxes",
)


def upgrade() -> None:
    for table_name in TASK_OWNED_TABLES:
        op.add_column(table_name, sa.Column("arena_task_id", sa.String(length=32), nullable=True))
        op.create_index(f"ix_{table_name}_arena_task_id", table_name, ["arena_task_id"])

    op.create_table(
        "human_baseline_records",
        sa.Column("record_id", sa.String(length=80), primary_key=True),
        sa.Column("task_id", sa.String(length=32), nullable=False),
        sa.Column("operator_alias", sa.String(length=80), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("action_count", sa.Integer(), nullable=False),
        sa.Column("final_score", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("duration_seconds >= 0", name="ck_baseline_duration_nonnegative"),
        sa.CheckConstraint("action_count >= 0", name="ck_baseline_actions_nonnegative"),
        sa.CheckConstraint(
            "final_score >= 0 AND final_score <= 100", name="ck_baseline_score_range"
        ),
    )
    op.create_index("ix_human_baseline_records_task_id", "human_baseline_records", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_human_baseline_records_task_id", table_name="human_baseline_records")
    op.drop_table("human_baseline_records")
    for table_name in reversed(TASK_OWNED_TABLES):
        op.drop_index(f"ix_{table_name}_arena_task_id", table_name=table_name)
        op.drop_column(table_name, "arena_task_id")
