"""Create the separate W10 Control Plane identity schema.

Revision ID: 20260729_0001
Revises:
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "w10_organizations",
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("profile_code", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("memory_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("organization_id", name="pk_w10_organizations"),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_w10_org_status"),
        sa.CheckConstraint("version >= 1", name="ck_w10_org_version"),
        sa.CheckConstraint("memory_version >= 1", name="ck_w10_org_memory_version"),
    )
    op.create_index(
        "ix_w10_organizations_status_id",
        "w10_organizations",
        ["status", "organization_id"],
    )

    op.create_table(
        "w10_users",
        sa.Column("user_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("profile_code", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["w10_organizations.organization_id"],
            name="fk_w10_users_organization",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_w10_users"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_w10_user_owner"),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_w10_user_status"),
        sa.CheckConstraint("version >= 1", name="ck_w10_user_version"),
    )
    op.create_index(
        "ix_w10_users_org_status_id",
        "w10_users",
        ["organization_id", "status", "user_id"],
    )

    op.create_table(
        "w10_oidc_identities",
        sa.Column("identity_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("user_id", sa.String(length=68), nullable=False),
        sa.Column("issuer_id", sa.String(length=32), nullable=False),
        sa.Column("issuer_hash", sa.String(length=64), nullable=False),
        sa.Column("subject_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            name="fk_w10_identity_org_user",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("identity_id", name="pk_w10_oidc_identities"),
        sa.UniqueConstraint("issuer_id", "subject_hash", name="uq_w10_issuer_subject"),
        sa.UniqueConstraint("organization_id", "identity_id", name="uq_w10_identity_owner"),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_w10_identity_status"),
        sa.CheckConstraint("version >= 1", name="ck_w10_identity_version"),
        sa.CheckConstraint("length(issuer_hash) = 64", name="ck_w10_identity_issuer_hash"),
        sa.CheckConstraint("length(subject_hash) = 64", name="ck_w10_identity_subject_hash"),
    )
    op.create_index(
        "ix_w10_identities_org_user_status",
        "w10_oidc_identities",
        ["organization_id", "user_id", "status"],
    )

    op.create_table(
        "w10_memberships",
        sa.Column("membership_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("user_id", sa.String(length=68), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            name="fk_w10_membership_org_user",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("membership_id", name="pk_w10_memberships"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_w10_membership_org_user"),
        sa.UniqueConstraint("organization_id", "membership_id", name="uq_w10_membership_owner"),
        sa.CheckConstraint(
            "role IN ('organization_admin', 'operator', 'auditor')",
            name="ck_w10_membership_role",
        ),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_w10_membership_status"),
        sa.CheckConstraint("version >= 1", name="ck_w10_membership_version"),
    )
    op.create_index(
        "ix_w10_memberships_org_status_role",
        "w10_memberships",
        ["organization_id", "status", "role"],
    )

    op.create_table(
        "w10_organization_memories",
        sa.Column("memory_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("owner_user_id", sa.String(length=68), nullable=False),
        sa.Column("field", sa.String(length=32), nullable=False),
        sa.Column("safe_value", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "owner_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            name="fk_w10_memory_org_owner",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("memory_id", name="pk_w10_organization_memories"),
        sa.UniqueConstraint("organization_id", "memory_id", name="uq_w10_memory_owner"),
        sa.CheckConstraint(
            "field IN ('department', 'role', 'location', 'device_preference', 'approval_chain')",
            name="ck_w10_memory_field",
        ),
        sa.CheckConstraint("status IN ('active', 'tombstone')", name="ck_w10_memory_status"),
        sa.CheckConstraint("version >= 1", name="ck_w10_memory_version"),
        sa.CheckConstraint("length(content_hash) = 64", name="ck_w10_memory_hash"),
    )
    op.create_index(
        "ix_w10_memories_org_status_field_id",
        "w10_organization_memories",
        ["organization_id", "status", "field", "memory_id"],
    )
    op.create_index(
        "ix_w10_memories_org_owner_status",
        "w10_organization_memories",
        ["organization_id", "owner_user_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_w10_memories_org_owner_status", table_name="w10_organization_memories")
    op.drop_index("ix_w10_memories_org_status_field_id", table_name="w10_organization_memories")
    op.drop_table("w10_organization_memories")
    op.drop_index("ix_w10_memberships_org_status_role", table_name="w10_memberships")
    op.drop_table("w10_memberships")
    op.drop_index("ix_w10_identities_org_user_status", table_name="w10_oidc_identities")
    op.drop_table("w10_oidc_identities")
    op.drop_index("ix_w10_users_org_status_id", table_name="w10_users")
    op.drop_table("w10_users")
    op.drop_index("ix_w10_organizations_status_id", table_name="w10_organizations")
    op.drop_table("w10_organizations")
