"""Control Plane-owned W10 identity and durable memory tables."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = "w10_organizations"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled')", name="ck_w10_org_status"),
        CheckConstraint("version >= 1", name="ck_w10_org_version"),
        CheckConstraint("memory_version >= 1", name="ck_w10_org_memory_version"),
        Index("ix_w10_organizations_status_id", "status", "organization_id"),
    )

    organization_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    profile_code: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(16), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    memory_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "w10_users"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_w10_user_owner"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_w10_user_status"),
        CheckConstraint("version >= 1", name="ck_w10_user_version"),
        Index("ix_w10_users_org_status_id", "organization_id", "status", "user_id"),
    )

    user_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("w10_organizations.organization_id", ondelete="RESTRICT"), nullable=False
    )
    profile_code: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(16), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OidcIdentity(Base):
    __tablename__ = "w10_oidc_identities"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w10_identity_org_user",
        ),
        UniqueConstraint("issuer_id", "subject_hash", name="uq_w10_issuer_subject"),
        UniqueConstraint("organization_id", "identity_id", name="uq_w10_identity_owner"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_w10_identity_status"),
        CheckConstraint("version >= 1", name="ck_w10_identity_version"),
        CheckConstraint("length(issuer_hash) = 64", name="ck_w10_identity_issuer_hash"),
        CheckConstraint("length(subject_hash) = 64", name="ck_w10_identity_subject_hash"),
        Index(
            "ix_w10_identities_org_user_status",
            "organization_id",
            "user_id",
            "status",
        ),
    )

    identity_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    issuer_id: Mapped[str] = mapped_column(String(32))
    issuer_hash: Mapped[str] = mapped_column(String(64))
    subject_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Membership(Base):
    __tablename__ = "w10_memberships"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w10_membership_org_user",
        ),
        UniqueConstraint("organization_id", "user_id", name="uq_w10_membership_org_user"),
        UniqueConstraint("organization_id", "membership_id", name="uq_w10_membership_owner"),
        CheckConstraint(
            "role IN ('organization_admin', 'operator', 'auditor')",
            name="ck_w10_membership_role",
        ),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_w10_membership_status"),
        CheckConstraint("version >= 1", name="ck_w10_membership_version"),
        Index(
            "ix_w10_memberships_org_status_role",
            "organization_id",
            "status",
            "role",
        ),
    )

    membership_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    role: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OrganizationMemory(Base):
    __tablename__ = "w10_organization_memories"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "owner_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w10_memory_org_owner",
        ),
        UniqueConstraint("organization_id", "memory_id", name="uq_w10_memory_owner"),
        CheckConstraint(
            "field IN ('department', 'role', 'location', 'device_preference', 'approval_chain')",
            name="ck_w10_memory_field",
        ),
        CheckConstraint("status IN ('active', 'tombstone')", name="ck_w10_memory_status"),
        CheckConstraint("version >= 1", name="ck_w10_memory_version"),
        CheckConstraint("length(content_hash) = 64", name="ck_w10_memory_hash"),
        Index(
            "ix_w10_memories_org_status_field_id",
            "organization_id",
            "status",
            "field",
            "memory_id",
        ),
        Index(
            "ix_w10_memories_org_owner_status",
            "organization_id",
            "owner_user_id",
            "status",
        ),
    )

    memory_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    field: Mapped[str] = mapped_column(String(32))
    safe_value: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(16), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ApprovalAuthority(Base):
    __tablename__ = "w11_approval_authorities"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w11_authority_org_user",
        ),
        UniqueConstraint("organization_id", "authority_id", name="uq_w11_authority_owner"),
        UniqueConstraint(
            "organization_id",
            "authority_id",
            "user_id",
            "role",
            name="uq_w11_authority_decision_binding",
        ),
        UniqueConstraint("organization_id", "user_id", "role", name="uq_w11_authority_user_role"),
        CheckConstraint("role IN ('manager', 'security')", name="ck_w11_authority_role"),
        CheckConstraint(
            "status IN ('active', 'disabled', 'tombstone')",
            name="ck_w11_authority_status",
        ),
        CheckConstraint("version >= 1", name="ck_w11_authority_version"),
        Index(
            "ix_w11_authorities_org_status_role_user",
            "organization_id",
            "status",
            "role",
            "user_id",
        ),
    )

    authority_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    role: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ApprovalRequest(Base):
    __tablename__ = "w11_approval_requests"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "requester_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w11_request_org_requester",
        ),
        ForeignKeyConstraint(
            ["organization_id", "executor_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w11_request_org_executor",
        ),
        UniqueConstraint("organization_id", "request_id", name="uq_w11_request_owner"),
        UniqueConstraint(
            "organization_id",
            "request_id",
            "action_type",
            "parameter_hash",
            name="uq_w11_request_decision_binding",
        ),
        UniqueConstraint(
            "organization_id",
            "request_id",
            "action_type",
            "parameter_hash",
            "risk_level",
            "executor_user_id",
            name="uq_w11_request_grant_binding",
        ),
        CheckConstraint("risk_level IN ('L2', 'L3')", name="ck_w11_request_approval_risk"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled', 'expired', "
            "'invalidated', 'claimed', 'consumed', 'failed')",
            name="ck_w11_request_status",
        ),
        CheckConstraint(
            "required_roles IN ('manager', 'manager,security')",
            name="ck_w11_request_required_roles",
        ),
        CheckConstraint(
            "action_type IN ('create_ticket', 'create_account', 'assign_asset', "
            "'create_mailbox', 'transfer_employee', 'close_ticket', 'release_asset', "
            "'grant_admin_privilege', 'revoke_account', 'disable_employee', "
            "'disable_mailbox', 'transfer_file_ownership')",
            name="ck_w11_request_action",
        ),
        CheckConstraint(
            "((risk_level = 'L2' AND required_roles = 'manager' AND action_type IN "
            "('create_ticket', 'create_account', 'assign_asset', 'create_mailbox', "
            "'transfer_employee', 'close_ticket', 'release_asset')) OR "
            "(risk_level = 'L3' AND required_roles = 'manager,security' AND action_type IN "
            "('create_account', 'grant_admin_privilege', 'revoke_account', "
            "'disable_employee', 'disable_mailbox', 'transfer_file_ownership')))",
            name="ck_w11_request_risk_roles_action",
        ),
        CheckConstraint(
            "closed_reason IS NULL OR closed_reason IN ('policy_rejected', "
            "'requester_cancelled', 'parameters_changed', 'authority_inactive', "
            "'request_expired')",
            name="ck_w11_request_closed_reason",
        ),
        CheckConstraint("length(parameter_hash) = 64", name="ck_w11_request_parameter_hash"),
        CheckConstraint("version >= 1", name="ck_w11_request_version"),
        CheckConstraint("audit_sequence >= 1", name="ck_w11_request_audit_sequence"),
        Index(
            "ix_w11_requests_org_status_expiry_id",
            "organization_id",
            "status",
            "expires_at",
            "request_id",
        ),
        Index(
            "ix_w11_requests_org_executor_status",
            "organization_id",
            "executor_user_id",
            "status",
        ),
    )

    request_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    task_id: Mapped[str] = mapped_column(String(80))
    step_id: Mapped[str] = mapped_column(String(40))
    action_type: Mapped[str] = mapped_column(String(64))
    parameter_hash: Mapped[str] = mapped_column(String(64))
    risk_level: Mapped[str] = mapped_column(String(2))
    requester_user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    executor_user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    required_roles: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    version: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_reason: Mapped[str | None] = mapped_column(String(32))
    audit_sequence: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ApprovalDecision(Base):
    __tablename__ = "w11_approval_decisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "request_id", "action_type", "parameter_hash"],
            [
                "w11_approval_requests.organization_id",
                "w11_approval_requests.request_id",
                "w11_approval_requests.action_type",
                "w11_approval_requests.parameter_hash",
            ],
            ondelete="RESTRICT",
            name="fk_w11_decision_org_request_binding",
        ),
        ForeignKeyConstraint(
            ["organization_id", "approver_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w11_decision_org_approver",
        ),
        ForeignKeyConstraint(
            ["organization_id", "authority_id", "approver_user_id", "approval_role"],
            [
                "w11_approval_authorities.organization_id",
                "w11_approval_authorities.authority_id",
                "w11_approval_authorities.user_id",
                "w11_approval_authorities.role",
            ],
            ondelete="RESTRICT",
            name="fk_w11_decision_org_authority_binding",
        ),
        UniqueConstraint("organization_id", "decision_id", name="uq_w11_decision_owner"),
        UniqueConstraint(
            "organization_id",
            "request_id",
            "approver_user_id",
            name="uq_w11_decision_request_approver",
        ),
        UniqueConstraint(
            "organization_id", "request_id", "approval_role", name="uq_w11_decision_role"
        ),
        CheckConstraint("decision IN ('approved', 'rejected')", name="ck_w11_decision_value"),
        CheckConstraint(
            "((decision = 'approved' AND reason = 'policy_satisfied') OR "
            "(decision = 'rejected' AND reason = 'policy_rejected'))",
            name="ck_w11_decision_reason",
        ),
        CheckConstraint("approval_role IN ('manager', 'security')", name="ck_w11_decision_role"),
        CheckConstraint("length(parameter_hash) = 64", name="ck_w11_decision_parameter_hash"),
        CheckConstraint("request_version >= 1", name="ck_w11_decision_request_version"),
        CheckConstraint("audit_sequence >= 1", name="ck_w11_decision_audit_sequence"),
        Index(
            "ix_w11_decisions_org_request_role",
            "organization_id",
            "request_id",
            "approval_role",
        ),
    )

    decision_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    request_id: Mapped[str] = mapped_column(String(68), nullable=False)
    decision: Mapped[str] = mapped_column(String(16))
    approver_user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    authority_id: Mapped[str] = mapped_column(String(68), nullable=False)
    approval_role: Mapped[str] = mapped_column(String(16))
    request_version: Mapped[int] = mapped_column(Integer)
    action_type: Mapped[str] = mapped_column(String(64))
    parameter_hash: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(String(32))
    audit_sequence: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApprovalGrant(Base):
    __tablename__ = "w11_approval_grants"
    __table_args__ = (
        ForeignKeyConstraint(
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
            ondelete="RESTRICT",
            name="fk_w11_grant_org_request_binding",
        ),
        ForeignKeyConstraint(
            ["organization_id", "executor_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w11_grant_org_executor",
        ),
        UniqueConstraint("organization_id", "grant_id", name="uq_w11_grant_owner"),
        UniqueConstraint("organization_id", "request_id", name="uq_w11_grant_request"),
        UniqueConstraint("organization_id", "execution_id", name="uq_w11_grant_execution"),
        CheckConstraint("risk_level IN ('L2', 'L3')", name="ck_w11_grant_risk"),
        CheckConstraint(
            "((risk_level = 'L2' AND action_type IN ('create_ticket', 'create_account', "
            "'assign_asset', 'create_mailbox', 'transfer_employee', 'close_ticket', "
            "'release_asset')) OR (risk_level = 'L3' AND action_type IN "
            "('create_account', 'grant_admin_privilege', 'revoke_account', "
            "'disable_employee', 'disable_mailbox', 'transfer_file_ownership')))",
            name="ck_w11_grant_risk_action",
        ),
        CheckConstraint(
            "status IN ('issued', 'claimed', 'consumed', 'revoked', 'expired', 'failed')",
            name="ck_w11_grant_status",
        ),
        CheckConstraint("length(parameter_hash) = 64", name="ck_w11_grant_parameter_hash"),
        CheckConstraint("length(approval_set_hash) = 64", name="ck_w11_grant_set_hash"),
        CheckConstraint("length(token_hash) = 64", name="ck_w11_grant_token_hash"),
        CheckConstraint("length(nonce_hash) = 64", name="ck_w11_grant_nonce_hash"),
        CheckConstraint(
            "authorization_hash IS NULL OR length(authorization_hash) = 64",
            name="ck_w11_grant_authorization_hash",
        ),
        CheckConstraint("version >= 1", name="ck_w11_grant_version"),
        Index(
            "ix_w11_grants_org_status_expiry_id",
            "organization_id",
            "status",
            "expires_at",
            "grant_id",
        ),
    )

    grant_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    request_id: Mapped[str] = mapped_column(String(68), nullable=False)
    task_id: Mapped[str] = mapped_column(String(80))
    step_id: Mapped[str] = mapped_column(String(40))
    action_type: Mapped[str] = mapped_column(String(64))
    parameter_hash: Mapped[str] = mapped_column(String(64))
    risk_level: Mapped[str] = mapped_column(String(2))
    approval_set_hash: Mapped[str] = mapped_column(String(64))
    executor_user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64))
    nonce_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="issued")
    version: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    execution_id: Mapped[str | None] = mapped_column(String(68))
    authorization_hash: Mapped[str | None] = mapped_column(String(64))
    receipt_reference: Mapped[str | None] = mapped_column(String(80))
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditChainHead(Base):
    __tablename__ = "w11_audit_chain_heads"
    __table_args__ = (
        CheckConstraint("head_sequence >= 0", name="ck_w11_audit_head_sequence"),
        CheckConstraint("length(head_hash) = 64", name="ck_w11_audit_head_hash"),
        CheckConstraint("version >= 1", name="ck_w11_audit_head_version"),
    )

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("w10_organizations.organization_id", ondelete="RESTRICT"), primary_key=True
    )
    head_sequence: Mapped[int] = mapped_column(Integer, default=0)
    head_hash: Mapped[str] = mapped_column(String(64), default="0" * 64)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditEvent(Base):
    __tablename__ = "w11_audit_events"
    __table_args__ = (
        UniqueConstraint("organization_id", "event_id", name="uq_w11_audit_event_owner"),
        CheckConstraint(
            "event_type IN ('risk_classified', 'l4_denied', 'approval_requested', "
            "'approval_approved', 'approval_rejected', 'request_cancelled', "
            "'request_expired', 'request_invalidated', 'grant_issued', 'grant_claimed', "
            "'grant_consumed', 'grant_rejected', 'execution_started', "
            "'execution_succeeded', 'execution_failed', 'recovery_resumed', "
            "'authority_disabled', 'audit_verified', 'run_waiting_approval', "
            "'run_queued', 'run_leased', 'run_started', 'run_recovered', "
            "'run_verifying', 'run_finished_ungraded', 'run_failed', "
            "'run_cancelled', 'run_expired', 'admission_rejected', "
            "'backpressure_rejected', 'rate_limited', 'lease_heartbeat', "
            "'lease_released', 'stale_fence_rejected', 'workflow_deduplicated')",
            name="ck_w11_audit_event_type",
        ),
        CheckConstraint("sequence >= 1", name="ck_w11_audit_sequence"),
        CheckConstraint("length(previous_hash) = 64", name="ck_w11_audit_previous_hash"),
        CheckConstraint("length(actor_reference) = 64", name="ck_w11_audit_actor_reference"),
        CheckConstraint(
            "length(subject_reference) BETWEEN 1 AND 68",
            name="ck_w11_audit_subject_reference",
        ),
        CheckConstraint("length(payload_json) <= 2048", name="ck_w11_audit_payload_size"),
        CheckConstraint("length(payload_hash) = 64", name="ck_w11_audit_payload_hash"),
        CheckConstraint("length(event_hash) = 64", name="ck_w11_audit_event_hash"),
        Index(
            "ix_w11_audit_org_type_sequence",
            "organization_id",
            "event_type",
            "sequence",
        ),
    )

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("w10_organizations.organization_id", ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(68), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40))
    actor_reference: Mapped[str] = mapped_column(String(64))
    subject_reference: Mapped[str] = mapped_column(String(68))
    payload_json: Mapped[str] = mapped_column(Text)
    payload_hash: Mapped[str] = mapped_column(String(64))
    previous_hash: Mapped[str] = mapped_column(String(64))
    event_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProductionRun(Base):
    __tablename__ = "w12_production_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "requester_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w12_run_org_requester",
        ),
        ForeignKeyConstraint(
            ["organization_id", "executor_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w12_run_org_executor",
        ),
        ForeignKeyConstraint(
            ["organization_id", "approval_request_id"],
            ["w11_approval_requests.organization_id", "w11_approval_requests.request_id"],
            ondelete="RESTRICT",
            name="fk_w12_run_org_approval_request",
        ),
        ForeignKeyConstraint(
            ["organization_id", "grant_id"],
            ["w11_approval_grants.organization_id", "w11_approval_grants.grant_id"],
            ondelete="RESTRICT",
            name="fk_w12_run_org_grant",
        ),
        ForeignKeyConstraint(
            ["organization_id", "execution_id"],
            ["w11_approval_grants.organization_id", "w11_approval_grants.execution_id"],
            ondelete="RESTRICT",
            name="fk_w12_run_org_execution",
        ),
        UniqueConstraint("organization_id", "run_id", name="uq_w12_run_owner"),
        UniqueConstraint(
            "organization_id", "approval_request_id", name="uq_w12_run_approval_request"
        ),
        UniqueConstraint("organization_id", "execution_id", name="uq_w12_run_execution"),
        CheckConstraint(
            "task_id IN ('w7-jml-joiner-001-v1', 'w7-jml-joiner-001-v2', "
            "'w7-jml-joiner-002-v1', 'w7-jml-joiner-002-v2', "
            "'w7-jml-mover-001-v1', 'w7-jml-mover-001-v2', "
            "'w7-jml-leaver-001-v1', 'w7-jml-leaver-001-v2')",
            name="ck_w12_run_task",
        ),
        CheckConstraint("process IN ('joiner', 'mover', 'leaver')", name="ck_w12_run_process"),
        CheckConstraint(
            "category IN ('standard_joiner', 'standard_mover', 'standard_leaver')",
            name="ck_w12_run_category",
        ),
        CheckConstraint(
            "((process = 'joiner' AND category = 'standard_joiner' AND task_id IN "
            "('w7-jml-joiner-001-v1', 'w7-jml-joiner-001-v2', "
            "'w7-jml-joiner-002-v1', 'w7-jml-joiner-002-v2')) OR "
            "(process = 'mover' AND category = 'standard_mover' AND "
            "task_id IN ('w7-jml-mover-001-v1', 'w7-jml-mover-001-v2')) OR "
            "(process = 'leaver' AND category = 'standard_leaver' AND "
            "task_id IN ('w7-jml-leaver-001-v1', 'w7-jml-leaver-001-v2')))",
            name="ck_w12_run_task_binding",
        ),
        CheckConstraint(
            "status IN ('waiting_approval', 'queued', 'leased', 'running', 'recovering', "
            "'verifying', 'finished_ungraded', 'failed', 'cancelled', 'expired')",
            name="ck_w12_run_status",
        ),
        CheckConstraint("version >= 1", name="ck_w12_run_version"),
        CheckConstraint("fencing_token >= 0", name="ck_w12_run_fence"),
        CheckConstraint("audit_sequence >= 1", name="ck_w12_run_audit_sequence"),
        CheckConstraint("length(parameter_hash) = 64", name="ck_w12_run_parameter_hash"),
        CheckConstraint("length(authorization_hash) = 64", name="ck_w12_run_auth_hash"),
        CheckConstraint(
            "approval_set_hash IS NULL OR length(approval_set_hash) = 64",
            name="ck_w12_run_approval_set_hash",
        ),
        CheckConstraint("length(payload_hash) = 64", name="ck_w12_run_payload_hash"),
        CheckConstraint("length(idempotency_hash) = 64", name="ck_w12_run_idem_hash"),
        CheckConstraint("length(body_hash) = 64", name="ck_w12_run_body_hash"),
        CheckConstraint("length(workflow_hash) = 64", name="ck_w12_run_workflow_hash"),
        CheckConstraint(
            "lease_owner_hash IS NULL OR length(lease_owner_hash) = 64",
            name="ck_w12_run_lease_owner_hash",
        ),
        CheckConstraint(
            "terminal_reason IS NULL OR terminal_reason IN ('agent_finished', "
            "'agent_failed', 'authorization_invalid', 'queue_expired', "
            "'lease_exhausted', 'cancelled_by_actor', 'workflow_rejected', "
            "'receipt_invalid', 'worker_drained', 'dependency_unavailable')",
            name="ck_w12_run_terminal_reason",
        ),
        Index(
            "ix_w12_runs_org_status_accepted",
            "organization_id",
            "status",
            "accepted_at",
            "run_id",
        ),
        Index(
            "ix_w12_runs_org_executor_status",
            "organization_id",
            "executor_user_id",
            "status",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    requester_user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    executor_user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    task_id: Mapped[str] = mapped_column(String(40))
    process: Mapped[str] = mapped_column(String(16))
    category: Mapped[str] = mapped_column(String(24))
    approval_request_id: Mapped[str | None] = mapped_column(String(68))
    grant_id: Mapped[str | None] = mapped_column(String(68))
    execution_id: Mapped[str | None] = mapped_column(String(68))
    action_type: Mapped[str] = mapped_column(String(64))
    parameter_hash: Mapped[str] = mapped_column(String(64))
    authorization_hash: Mapped[str] = mapped_column(String(64))
    approval_set_hash: Mapped[str | None] = mapped_column(String(64))
    payload_reference: Mapped[str] = mapped_column(String(80))
    payload_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24))
    version: Mapped[int] = mapped_column(Integer, default=1)
    idempotency_hash: Mapped[str] = mapped_column(String(64))
    body_hash: Mapped[str] = mapped_column(String(64))
    workflow_id: Mapped[str] = mapped_column(String(64))
    workflow_hash: Mapped[str] = mapped_column(String(64))
    lease_owner_hash: Mapped[str | None] = mapped_column(String(64))
    fencing_token: Mapped[int] = mapped_column(Integer, default=0)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    terminal_reason: Mapped[str | None] = mapped_column(String(32))
    receipt_reference: Mapped[str | None] = mapped_column(String(80))
    audit_sequence: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DispatchOutbox(Base):
    __tablename__ = "w12_dispatch_outbox"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "run_id"],
            ["w12_production_runs.organization_id", "w12_production_runs.run_id"],
            ondelete="RESTRICT",
            name="fk_w12_outbox_org_run",
        ),
        UniqueConstraint("organization_id", "outbox_id", name="uq_w12_outbox_owner"),
        UniqueConstraint("organization_id", "run_id", name="uq_w12_outbox_run"),
        CheckConstraint(
            "status IN ('ready', 'leased', 'dispatched', 'closed', 'cancelled', "
            "'expired', 'failed')",
            name="ck_w12_outbox_status",
        ),
        CheckConstraint("attempt_count BETWEEN 0 AND 3", name="ck_w12_outbox_attempts"),
        CheckConstraint("fencing_token >= 0", name="ck_w12_outbox_fence"),
        CheckConstraint("lease_version >= 0", name="ck_w12_outbox_lease_version"),
        CheckConstraint(
            "lease_owner_hash IS NULL OR length(lease_owner_hash) = 64",
            name="ck_w12_outbox_lease_owner_hash",
        ),
        Index(
            "ix_w12_outbox_org_status_available",
            "organization_id",
            "status",
            "available_at",
            "outbox_id",
        ),
        Index("ix_w12_outbox_status_lease_expiry", "status", "lease_expires_at", "outbox_id"),
    )

    outbox_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    run_id: Mapped[str] = mapped_column(String(68), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ready")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    fencing_token: Mapped[int] = mapped_column(Integer, default=0)
    lease_owner_hash: Mapped[str | None] = mapped_column(String(64))
    lease_version: Mapped[int] = mapped_column(Integer, default=0)
    leased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WorkerLease(Base):
    __tablename__ = "w12_worker_leases"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "outbox_id"],
            ["w12_dispatch_outbox.organization_id", "w12_dispatch_outbox.outbox_id"],
            ondelete="RESTRICT",
            name="fk_w12_lease_org_outbox",
        ),
        ForeignKeyConstraint(
            ["organization_id", "run_id"],
            ["w12_production_runs.organization_id", "w12_production_runs.run_id"],
            ondelete="RESTRICT",
            name="fk_w12_lease_org_run",
        ),
        UniqueConstraint("organization_id", "lease_id", name="uq_w12_lease_owner"),
        UniqueConstraint(
            "organization_id", "outbox_id", "fencing_token", name="uq_w12_lease_fence"
        ),
        CheckConstraint("length(worker_owner_hash) = 64", name="ck_w12_lease_owner_hash"),
        CheckConstraint("lease_version >= 1", name="ck_w12_lease_version"),
        CheckConstraint("fencing_token >= 1", name="ck_w12_lease_fence"),
        CheckConstraint("attempt_count BETWEEN 1 AND 3", name="ck_w12_lease_attempts"),
        CheckConstraint(
            "status IN ('active', 'released', 'expired', 'completed', 'failed')",
            name="ck_w12_lease_status",
        ),
        Index(
            "ix_w12_leases_org_run_fence",
            "organization_id",
            "run_id",
            "fencing_token",
        ),
    )

    lease_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    outbox_id: Mapped[str] = mapped_column(String(68), nullable=False)
    run_id: Mapped[str] = mapped_column(String(68), nullable=False)
    worker_owner_hash: Mapped[str] = mapped_column(String(64))
    lease_version: Mapped[int] = mapped_column(Integer)
    fencing_token: Mapped[int] = mapped_column(Integer)
    leased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lease_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SchedulerPartition(Base):
    __tablename__ = "w12_scheduler_partitions"
    __table_args__ = (
        UniqueConstraint("partition_id", name="uq_w12_partition_id"),
        CheckConstraint("ready_count BETWEEN 0 AND 32", name="ck_w12_partition_ready"),
        CheckConstraint("status IN ('ready', 'empty', 'disabled')", name="ck_w12_partition_status"),
        CheckConstraint("cursor_version >= 1", name="ck_w12_partition_version"),
        Index("ix_w12_partitions_status_selected", "status", "last_selected_at", "partition_id"),
    )

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("w10_organizations.organization_id", ondelete="RESTRICT"), primary_key=True
    )
    partition_id: Mapped[str] = mapped_column(String(68), nullable=False)
    ready_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="empty")
    cursor_version: Mapped[int] = mapped_column(Integer, default=1)
    last_selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RateLimitBucket(Base):
    __tablename__ = "w12_rate_limit_buckets"
    __table_args__ = (
        CheckConstraint("length(bucket_key_hash) = 64", name="ck_w12_bucket_key_hash"),
        CheckConstraint("scope_kind IN ('actor', 'organization')", name="ck_w12_bucket_scope"),
        CheckConstraint(
            "route_class IN ('production_submit', 'production_read', 'production_mutate')",
            name="ck_w12_bucket_route",
        ),
        CheckConstraint("tokens_micro >= 0", name="ck_w12_bucket_tokens"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_w12_bucket_status"),
        CheckConstraint("version >= 1", name="ck_w12_bucket_version"),
        Index(
            "ix_w12_buckets_org_route_scope",
            "organization_id",
            "route_class",
            "scope_kind",
        ),
    )

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("w10_organizations.organization_id", ondelete="RESTRICT"), primary_key=True
    )
    bucket_key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    route_class: Mapped[str] = mapped_column(String(24), primary_key=True)
    scope_kind: Mapped[str] = mapped_column(String(16))
    tokens_micro: Mapped[int] = mapped_column(BigInteger)
    last_refill_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class IdempotencyRecord(Base):
    __tablename__ = "w12_idempotency_records"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "actor_user_id"],
            ["w10_users.organization_id", "w10_users.user_id"],
            ondelete="RESTRICT",
            name="fk_w12_idempotency_org_actor",
        ),
        ForeignKeyConstraint(
            ["organization_id", "run_id"],
            ["w12_production_runs.organization_id", "w12_production_runs.run_id"],
            ondelete="RESTRICT",
            name="fk_w12_idempotency_org_run",
        ),
        UniqueConstraint(
            "organization_id", "actor_user_id", "key_hash", name="uq_w12_idempotency_actor_key"
        ),
        UniqueConstraint("organization_id", "idempotency_id", name="uq_w12_idempotency_owner"),
        CheckConstraint("length(key_hash) = 64", name="ck_w12_idempotency_key_hash"),
        CheckConstraint("length(body_hash) = 64", name="ck_w12_idempotency_body_hash"),
        Index("ix_w12_idempotency_org_run", "organization_id", "run_id"),
    )

    idempotency_id: Mapped[str] = mapped_column(String(68), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(68), nullable=False)
    actor_user_id: Mapped[str] = mapped_column(String(68), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64))
    body_hash: Mapped[str] = mapped_column(String(64))
    run_id: Mapped[str] = mapped_column(String(68), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
