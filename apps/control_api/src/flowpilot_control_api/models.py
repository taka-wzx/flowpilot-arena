"""Control Plane-owned W10 identity and durable memory tables."""

from datetime import datetime

from sqlalchemy import (
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
            "'authority_disabled', 'audit_verified')",
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
