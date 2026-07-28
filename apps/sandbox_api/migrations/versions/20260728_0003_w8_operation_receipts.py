"""Add task-owned W8 operation receipts.

Revision ID: 20260728_0003
Revises: 20260726_0002
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260728_0003"
down_revision: str | None = "20260726_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "w8_operation_receipts",
        sa.Column("task_id", sa.String(length=40), nullable=False),
        sa.Column("idempotency_key", sa.String(length=67), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("plan_revision", sa.SmallInteger(), nullable=False),
        sa.Column("step_id", sa.String(length=40), nullable=False),
        sa.Column("operation", sa.String(length=40), nullable=False),
        sa.Column("outcome_code", sa.String(length=32), nullable=False),
        sa.Column("result_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("task_id", "idempotency_key", name="pk_w8_operation_receipts"),
        sa.CheckConstraint("length(idempotency_key) = 67", name="ck_w8_receipt_key_length"),
        sa.CheckConstraint("length(request_hash) = 64", name="ck_w8_receipt_request_hash_length"),
        sa.CheckConstraint("length(result_hash) = 64", name="ck_w8_receipt_result_hash_length"),
        sa.CheckConstraint("plan_revision >= 1 AND plan_revision <= 2", name="ck_w8_revision"),
        sa.CheckConstraint("outcome_code = 'committed'", name="ck_w8_outcome"),
    )
    op.create_index("ix_w8_operation_receipts_task_id", "w8_operation_receipts", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_w8_operation_receipts_task_id", table_name="w8_operation_receipts")
    op.drop_table("w8_operation_receipts")
