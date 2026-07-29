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
