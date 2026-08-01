"""Add W11 approval, grant, execution-claim, and audit-chain state.

Revision ID: 20260729_0002
Revises: 20260729_0001
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0002"
down_revision: str | None = "20260729_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "w11_approval_authorities",
        sa.Column("authority_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("user_id", sa.String(length=68), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
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
            name="fk_w11_authority_org_user",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("authority_id", name="pk_w11_approval_authorities"),
        sa.UniqueConstraint("organization_id", "authority_id", name="uq_w11_authority_owner"),
        sa.UniqueConstraint(
            "organization_id",
            "authority_id",
            "user_id",
            "role",
            name="uq_w11_authority_decision_binding",
        ),
        sa.UniqueConstraint(
            "organization_id", "user_id", "role", name="uq_w11_authority_user_role"
        ),
        sa.CheckConstraint("role IN ('manager', 'security')", name="ck_w11_authority_role"),
        sa.CheckConstraint(
            "status IN ('active', 'disabled', 'tombstone')",
            name="ck_w11_authority_status",
        ),
        sa.CheckConstraint("version >= 1", name="ck_w11_authority_version"),
    )
    op.create_index(
        "ix_w11_authorities_org_status_role_user",
        "w11_approval_authorities",
        ["organization_id", "status", "role", "user_id"],
    )

    op.create_table(
        "w11_approval_requests",
        sa.Column("request_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("task_id", sa.String(length=80), nullable=False),
        sa.Column("step_id", sa.String(length=40), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("parameter_hash", sa.String(length=64), nullable=False),
        sa.Column("risk_level", sa.String(length=2), nullable=False),
        sa.Column("requester_user_id", sa.String(length=68), nullable=False),
        sa.Column("executor_user_id", sa.String(length=68), nullable=False),
        sa.Column("required_roles", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_reason", sa.String(length=32), nullable=True),
        sa.Column("audit_sequence", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "requester_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            name="fk_w11_request_org_requester",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "executor_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            name="fk_w11_request_org_executor",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("request_id", name="pk_w11_approval_requests"),
        sa.UniqueConstraint("organization_id", "request_id", name="uq_w11_request_owner"),
        sa.UniqueConstraint(
            "organization_id",
            "request_id",
            "action_type",
            "parameter_hash",
            name="uq_w11_request_decision_binding",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "request_id",
            "action_type",
            "parameter_hash",
            "risk_level",
            "executor_user_id",
            name="uq_w11_request_grant_binding",
        ),
        sa.CheckConstraint("risk_level IN ('L2', 'L3')", name="ck_w11_request_approval_risk"),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled', 'expired', "
            "'invalidated', 'claimed', 'consumed', 'failed')",
            name="ck_w11_request_status",
        ),
        sa.CheckConstraint(
            "required_roles IN ('manager', 'manager,security')",
            name="ck_w11_request_required_roles",
        ),
        sa.CheckConstraint(
            "action_type IN ('create_ticket', 'create_account', 'assign_asset', "
            "'create_mailbox', 'transfer_employee', 'close_ticket', 'release_asset', "
            "'grant_admin_privilege', 'revoke_account', 'disable_employee', "
            "'disable_mailbox', 'transfer_file_ownership')",
            name="ck_w11_request_action",
        ),
        sa.CheckConstraint(
            "((risk_level = 'L2' AND required_roles = 'manager' AND action_type IN "
            "('create_ticket', 'create_account', 'assign_asset', 'create_mailbox', "
            "'transfer_employee', 'close_ticket', 'release_asset')) OR "
            "(risk_level = 'L3' AND required_roles = 'manager,security' AND action_type IN "
            "('create_account', 'grant_admin_privilege', 'revoke_account', "
            "'disable_employee', 'disable_mailbox', 'transfer_file_ownership')))",
            name="ck_w11_request_risk_roles_action",
        ),
        sa.CheckConstraint(
            "closed_reason IS NULL OR closed_reason IN ('policy_rejected', "
            "'requester_cancelled', 'parameters_changed', 'authority_inactive', "
            "'request_expired')",
            name="ck_w11_request_closed_reason",
        ),
        sa.CheckConstraint("length(parameter_hash) = 64", name="ck_w11_request_parameter_hash"),
        sa.CheckConstraint("version >= 1", name="ck_w11_request_version"),
        sa.CheckConstraint("audit_sequence >= 1", name="ck_w11_request_audit_sequence"),
    )
    op.create_index(
        "ix_w11_requests_org_status_expiry_id",
        "w11_approval_requests",
        ["organization_id", "status", "expires_at", "request_id"],
    )
    op.create_index(
        "ix_w11_requests_org_executor_status",
        "w11_approval_requests",
        ["organization_id", "executor_user_id", "status"],
    )

    op.create_table(
        "w11_approval_decisions",
        sa.Column("decision_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("request_id", sa.String(length=68), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("approver_user_id", sa.String(length=68), nullable=False),
        sa.Column("authority_id", sa.String(length=68), nullable=False),
        sa.Column("approval_role", sa.String(length=16), nullable=False),
        sa.Column("request_version", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("parameter_hash", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("audit_sequence", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "request_id", "action_type", "parameter_hash"],
            [
                "w11_approval_requests.organization_id",
                "w11_approval_requests.request_id",
                "w11_approval_requests.action_type",
                "w11_approval_requests.parameter_hash",
            ],
            name="fk_w11_decision_org_request_binding",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "approver_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            name="fk_w11_decision_org_approver",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "authority_id", "approver_user_id", "approval_role"],
            [
                "w11_approval_authorities.organization_id",
                "w11_approval_authorities.authority_id",
                "w11_approval_authorities.user_id",
                "w11_approval_authorities.role",
            ],
            name="fk_w11_decision_org_authority_binding",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("decision_id", name="pk_w11_approval_decisions"),
        sa.UniqueConstraint("organization_id", "decision_id", name="uq_w11_decision_owner"),
        sa.UniqueConstraint(
            "organization_id",
            "request_id",
            "approver_user_id",
            name="uq_w11_decision_request_approver",
        ),
        sa.UniqueConstraint(
            "organization_id", "request_id", "approval_role", name="uq_w11_decision_role"
        ),
        sa.CheckConstraint("decision IN ('approved', 'rejected')", name="ck_w11_decision_value"),
        sa.CheckConstraint(
            "((decision = 'approved' AND reason = 'policy_satisfied') OR "
            "(decision = 'rejected' AND reason = 'policy_rejected'))",
            name="ck_w11_decision_reason",
        ),
        sa.CheckConstraint("approval_role IN ('manager', 'security')", name="ck_w11_decision_role"),
        sa.CheckConstraint("length(parameter_hash) = 64", name="ck_w11_decision_parameter_hash"),
        sa.CheckConstraint("request_version >= 1", name="ck_w11_decision_request_version"),
        sa.CheckConstraint("audit_sequence >= 1", name="ck_w11_decision_audit_sequence"),
    )
    op.create_index(
        "ix_w11_decisions_org_request_role",
        "w11_approval_decisions",
        ["organization_id", "request_id", "approval_role"],
    )

    op.create_table(
        "w11_approval_grants",
        sa.Column("grant_id", sa.String(length=68), nullable=False),
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("request_id", sa.String(length=68), nullable=False),
        sa.Column("task_id", sa.String(length=80), nullable=False),
        sa.Column("step_id", sa.String(length=40), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("parameter_hash", sa.String(length=64), nullable=False),
        sa.Column("risk_level", sa.String(length=2), nullable=False),
        sa.Column("approval_set_hash", sa.String(length=64), nullable=False),
        sa.Column("executor_user_id", sa.String(length=68), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("nonce_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("execution_id", sa.String(length=68), nullable=True),
        sa.Column("authorization_hash", sa.String(length=64), nullable=True),
        sa.Column("receipt_reference", sa.String(length=80), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            [
                "organization_id",
                "request_id",
                "action_type",
                "parameter_hash",
                "risk_level",
                "executor_user_id",
            ],
            [
                "w11_approval_requests.organization_id",
                "w11_approval_requests.request_id",
                "w11_approval_requests.action_type",
                "w11_approval_requests.parameter_hash",
                "w11_approval_requests.risk_level",
                "w11_approval_requests.executor_user_id",
            ],
            name="fk_w11_grant_org_request_binding",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "executor_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            name="fk_w11_grant_org_executor",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("grant_id", name="pk_w11_approval_grants"),
        sa.UniqueConstraint("organization_id", "grant_id", name="uq_w11_grant_owner"),
        sa.UniqueConstraint("organization_id", "request_id", name="uq_w11_grant_request"),
        sa.UniqueConstraint("organization_id", "execution_id", name="uq_w11_grant_execution"),
        sa.CheckConstraint("risk_level IN ('L2', 'L3')", name="ck_w11_grant_risk"),
        sa.CheckConstraint(
            "((risk_level = 'L2' AND action_type IN ('create_ticket', 'create_account', "
            "'assign_asset', 'create_mailbox', 'transfer_employee', 'close_ticket', "
            "'release_asset')) OR (risk_level = 'L3' AND action_type IN "
            "('create_account', 'grant_admin_privilege', 'revoke_account', "
            "'disable_employee', 'disable_mailbox', 'transfer_file_ownership')))",
            name="ck_w11_grant_risk_action",
        ),
        sa.CheckConstraint(
            "status IN ('issued', 'claimed', 'consumed', 'revoked', 'expired', 'failed')",
            name="ck_w11_grant_status",
        ),
        sa.CheckConstraint("length(parameter_hash) = 64", name="ck_w11_grant_parameter_hash"),
        sa.CheckConstraint("length(approval_set_hash) = 64", name="ck_w11_grant_set_hash"),
        sa.CheckConstraint("length(token_hash) = 64", name="ck_w11_grant_token_hash"),
        sa.CheckConstraint("length(nonce_hash) = 64", name="ck_w11_grant_nonce_hash"),
        sa.CheckConstraint(
            "authorization_hash IS NULL OR length(authorization_hash) = 64",
            name="ck_w11_grant_authorization_hash",
        ),
        sa.CheckConstraint("version >= 1", name="ck_w11_grant_version"),
    )
    op.create_index(
        "ix_w11_grants_org_status_expiry_id",
        "w11_approval_grants",
        ["organization_id", "status", "expires_at", "grant_id"],
    )

    op.create_table(
        "w11_audit_chain_heads",
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("head_sequence", sa.Integer(), nullable=False),
        sa.Column("head_hash", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["w10_organizations.organization_id"],
            name="fk_w11_audit_head_organization",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("organization_id", name="pk_w11_audit_chain_heads"),
        sa.CheckConstraint("head_sequence >= 0", name="ck_w11_audit_head_sequence"),
        sa.CheckConstraint("length(head_hash) = 64", name="ck_w11_audit_head_hash"),
        sa.CheckConstraint("version >= 1", name="ck_w11_audit_head_version"),
    )

    op.create_table(
        "w11_audit_events",
        sa.Column("organization_id", sa.String(length=68), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=68), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("actor_reference", sa.String(length=64), nullable=False),
        sa.Column("subject_reference", sa.String(length=68), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["w10_organizations.organization_id"],
            name="fk_w11_audit_event_organization",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("organization_id", "sequence", name="pk_w11_audit_events"),
        sa.UniqueConstraint("organization_id", "event_id", name="uq_w11_audit_event_owner"),
        sa.CheckConstraint(
            "event_type IN ('risk_classified', 'l4_denied', 'approval_requested', "
            "'approval_approved', 'approval_rejected', 'request_cancelled', "
            "'request_expired', 'request_invalidated', 'grant_issued', 'grant_claimed', "
            "'grant_consumed', 'grant_rejected', 'execution_started', "
            "'execution_succeeded', 'execution_failed', 'recovery_resumed', "
            "'authority_disabled', 'audit_verified')",
            name="ck_w11_audit_event_type",
        ),
        sa.CheckConstraint("sequence >= 1", name="ck_w11_audit_sequence"),
        sa.CheckConstraint("length(previous_hash) = 64", name="ck_w11_audit_previous_hash"),
        sa.CheckConstraint("length(actor_reference) = 64", name="ck_w11_audit_actor_reference"),
        sa.CheckConstraint(
            "length(subject_reference) BETWEEN 1 AND 68",
            name="ck_w11_audit_subject_reference",
        ),
        sa.CheckConstraint("length(payload_json) <= 2048", name="ck_w11_audit_payload_size"),
        sa.CheckConstraint("length(payload_hash) = 64", name="ck_w11_audit_payload_hash"),
        sa.CheckConstraint("length(event_hash) = 64", name="ck_w11_audit_event_hash"),
    )
    op.create_index(
        "ix_w11_audit_org_type_sequence",
        "w11_audit_events",
        ["organization_id", "event_type", "sequence"],
    )
    _create_immutable_triggers()


def _create_immutable_triggers() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION w11_reject_immutable_change() RETURNS trigger AS $$
            BEGIN
              RAISE EXCEPTION 'w11 immutable row';
            END;
            $$ LANGUAGE plpgsql
            """
        )
        for table in ("w11_approval_decisions", "w11_audit_events"):
            op.execute(
                f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE OR DELETE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION w11_reject_immutable_change()"
            )
    elif bind.dialect.name == "sqlite":
        for table in ("w11_approval_decisions", "w11_audit_events"):
            op.execute(
                f"CREATE TRIGGER trg_{table}_update BEFORE UPDATE ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'w11 immutable row'); END"
            )
            op.execute(
                f"CREATE TRIGGER trg_{table}_delete BEFORE DELETE ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'w11 immutable row'); END"
            )


def _drop_immutable_triggers() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in ("w11_approval_decisions", "w11_audit_events"):
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON {table}")
        op.execute("DROP FUNCTION IF EXISTS w11_reject_immutable_change()")
    elif bind.dialect.name == "sqlite":
        for table in ("w11_approval_decisions", "w11_audit_events"):
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_update")
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_delete")


def downgrade() -> None:
    _drop_immutable_triggers()
    op.drop_index("ix_w11_audit_org_type_sequence", table_name="w11_audit_events")
    op.drop_table("w11_audit_events")
    op.drop_table("w11_audit_chain_heads")
    op.drop_index("ix_w11_grants_org_status_expiry_id", table_name="w11_approval_grants")
    op.drop_table("w11_approval_grants")
    op.drop_index("ix_w11_decisions_org_request_role", table_name="w11_approval_decisions")
    op.drop_table("w11_approval_decisions")
    op.drop_index("ix_w11_requests_org_executor_status", table_name="w11_approval_requests")
    op.drop_index("ix_w11_requests_org_status_expiry_id", table_name="w11_approval_requests")
    op.drop_table("w11_approval_requests")
    op.drop_index("ix_w11_authorities_org_status_role_user", table_name="w11_approval_authorities")
    op.drop_table("w11_approval_authorities")
