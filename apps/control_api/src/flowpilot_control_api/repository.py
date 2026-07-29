"""Organization-qualified W10 repositories and atomic mutations."""

import hashlib
import secrets
from datetime import datetime

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot_control_api.auth import VerifiedIdentity
from flowpilot_control_api.etag import PreconditionFailed
from flowpilot_control_api.models import (
    Membership,
    OidcIdentity,
    Organization,
    OrganizationMemory,
    User,
)
from flowpilot_control_api.rbac import AuthorizationDenied, permissions_for_role
from flowpilot_control_api.schemas import (
    ActorContext,
    MembershipCreate,
    MembershipUpdate,
    MemoryCreate,
    MemoryUpdate,
    Role,
    UserCreate,
    UserUpdate,
    canonical_json_bytes,
    stable_hash,
)


class ResourceNotFound(RuntimeError):
    pass


class ResourceConflict(RuntimeError):
    pass


def _opaque_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(16)}"


def _authorization_hash(
    *,
    identity: OidcIdentity,
    organization: Organization,
    user: User,
    membership: Membership,
) -> str:
    return hashlib.sha256(
        canonical_json_bytes(
            {
                "schema_version": "w10-authorization-fact/1.0",
                "identity_id": identity.identity_id,
                "identity_version": identity.version,
                "organization_id": organization.organization_id,
                "organization_version": organization.version,
                "user_id": user.user_id,
                "user_version": user.version,
                "membership_id": membership.membership_id,
                "membership_version": membership.version,
                "role": membership.role,
            }
        )
    ).hexdigest()


def resolve_actor(session: Session, verified: VerifiedIdentity) -> ActorContext:
    statement = (
        select(OidcIdentity, User, Membership, Organization)
        .join(
            User,
            and_(
                User.organization_id == OidcIdentity.organization_id,
                User.user_id == OidcIdentity.user_id,
            ),
        )
        .join(
            Membership,
            and_(
                Membership.organization_id == User.organization_id,
                Membership.user_id == User.user_id,
            ),
        )
        .join(Organization, Organization.organization_id == User.organization_id)
        .where(
            OidcIdentity.issuer_id == verified.issuer_id,
            OidcIdentity.issuer_hash == verified.issuer_hash,
            OidcIdentity.subject_hash == verified.subject_hash,
            OidcIdentity.status == "active",
            User.status == "active",
            Membership.status == "active",
            Organization.status == "active",
        )
    )
    row = session.execute(statement).one_or_none()
    if row is None:
        raise AuthorizationDenied("inactive_or_unknown_identity")
    identity, user, membership, organization = row._tuple()
    try:
        role = Role(membership.role)
    except ValueError as exc:
        raise AuthorizationDenied("unknown_role") from exc
    if verified.claimed_role != role:
        raise AuthorizationDenied("role_claim_mismatch")
    permissions = permissions_for_role(role)
    return ActorContext(
        identity_id=identity.identity_id,
        issuer_hash=identity.issuer_hash,
        subject_hash=identity.subject_hash,
        user_id=user.user_id,
        organization_id=organization.organization_id,
        membership_id=membership.membership_id,
        role=role,
        permissions=permissions,
        organization_version=organization.version,
        user_version=user.version,
        membership_version=membership.version,
        authorization_hash=_authorization_hash(
            identity=identity,
            organization=organization,
            user=user,
            membership=membership,
        ),
    )


def require_actor_organization(actor: ActorContext, organization_id: str) -> None:
    if actor.organization_id != organization_id:
        raise ResourceNotFound("resource_not_found")


def get_organization(session: Session, actor: ActorContext, organization_id: str) -> Organization:
    require_actor_organization(actor, organization_id)
    record = session.scalar(
        select(Organization).where(Organization.organization_id == actor.organization_id)
    )
    if record is None:
        raise ResourceNotFound("resource_not_found")
    return record


def update_organization(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    expected_version: int,
    profile_code: str,
) -> Organization:
    require_actor_organization(actor, organization_id)
    statement = (
        update(Organization)
        .where(
            Organization.organization_id == actor.organization_id,
            Organization.version == expected_version,
        )
        .values(profile_code=profile_code, version=Organization.version + 1, updated_at=func.now())
        .returning(Organization)
        .execution_options(synchronize_session=False)
    )
    record = session.scalars(statement).one_or_none()
    if record is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    session.commit()
    return record


def disable_organization(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    expected_version: int,
) -> Organization:
    require_actor_organization(actor, organization_id)
    statement = (
        update(Organization)
        .where(
            Organization.organization_id == actor.organization_id,
            Organization.version == expected_version,
            Organization.status == "active",
        )
        .values(status="disabled", version=Organization.version + 1, updated_at=func.now())
        .returning(Organization)
        .execution_options(synchronize_session=False)
    )
    record = session.scalars(statement).one_or_none()
    if record is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    session.commit()
    return record


def list_users(session: Session, actor: ActorContext, organization_id: str) -> list[User]:
    require_actor_organization(actor, organization_id)
    return list(
        session.scalars(
            select(User)
            .where(User.organization_id == actor.organization_id)
            .order_by(User.user_id)
            .limit(100)
        )
    )


def count_users(session: Session, actor: ActorContext, organization_id: str) -> int:
    require_actor_organization(actor, organization_id)
    return int(
        session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.organization_id == actor.organization_id)
        )
        or 0
    )


def get_user(session: Session, actor: ActorContext, organization_id: str, user_id: str) -> User:
    require_actor_organization(actor, organization_id)
    record = session.scalar(
        select(User).where(
            User.organization_id == actor.organization_id,
            User.user_id == user_id,
        )
    )
    if record is None:
        raise ResourceNotFound("resource_not_found")
    return record


def create_user(
    session: Session, actor: ActorContext, organization_id: str, payload: UserCreate
) -> User:
    require_actor_organization(actor, organization_id)
    record = User(
        user_id=_opaque_id("usr"),
        organization_id=actor.organization_id,
        profile_code=payload.profile_code,
        status="active",
        version=1,
    )
    session.add(record)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ResourceConflict("conflict") from exc
    session.refresh(record)
    return record


def update_user(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    user_id: str,
    expected_version: int,
    payload: UserUpdate,
) -> User:
    require_actor_organization(actor, organization_id)
    statement = (
        update(User)
        .where(
            User.organization_id == actor.organization_id,
            User.user_id == user_id,
            User.version == expected_version,
        )
        .values(
            profile_code=payload.profile_code,
            version=User.version + 1,
            updated_at=func.now(),
        )
        .returning(User)
        .execution_options(synchronize_session=False)
    )
    record = session.scalars(statement).one_or_none()
    if record is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    session.commit()
    return record


def disable_user(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    user_id: str,
    expected_version: int,
) -> User:
    require_actor_organization(actor, organization_id)
    statement = (
        update(User)
        .where(
            User.organization_id == actor.organization_id,
            User.user_id == user_id,
            User.version == expected_version,
            User.status == "active",
        )
        .values(status="disabled", version=User.version + 1, updated_at=func.now())
        .returning(User)
        .execution_options(synchronize_session=False)
    )
    record = session.scalars(statement).one_or_none()
    if record is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    session.commit()
    return record


def list_memberships(
    session: Session, actor: ActorContext, organization_id: str
) -> list[Membership]:
    require_actor_organization(actor, organization_id)
    return list(
        session.scalars(
            select(Membership)
            .where(Membership.organization_id == actor.organization_id)
            .order_by(Membership.membership_id)
            .limit(100)
        )
    )


def count_memberships(session: Session, actor: ActorContext, organization_id: str) -> int:
    require_actor_organization(actor, organization_id)
    return int(
        session.scalar(
            select(func.count())
            .select_from(Membership)
            .where(Membership.organization_id == actor.organization_id)
        )
        or 0
    )


def get_membership(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    membership_id: str,
) -> Membership:
    require_actor_organization(actor, organization_id)
    record = session.scalar(
        select(Membership).where(
            Membership.organization_id == actor.organization_id,
            Membership.membership_id == membership_id,
        )
    )
    if record is None:
        raise ResourceNotFound("resource_not_found")
    return record


def create_membership(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    payload: MembershipCreate,
) -> Membership:
    require_actor_organization(actor, organization_id)
    user_exists = session.scalar(
        select(User.user_id).where(
            User.organization_id == actor.organization_id,
            User.user_id == payload.user_id,
        )
    )
    if user_exists is None:
        raise ResourceNotFound("resource_not_found")
    record = Membership(
        membership_id=_opaque_id("mbr"),
        organization_id=actor.organization_id,
        user_id=payload.user_id,
        role=payload.role.value,
        status="active",
        version=1,
    )
    session.add(record)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ResourceConflict("conflict") from exc
    session.refresh(record)
    return record


def update_membership(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    membership_id: str,
    expected_version: int,
    payload: MembershipUpdate,
) -> Membership:
    require_actor_organization(actor, organization_id)
    statement = (
        update(Membership)
        .where(
            Membership.organization_id == actor.organization_id,
            Membership.membership_id == membership_id,
            Membership.version == expected_version,
        )
        .values(role=payload.role.value, version=Membership.version + 1, updated_at=func.now())
        .returning(Membership)
        .execution_options(synchronize_session=False)
    )
    record = session.scalars(statement).one_or_none()
    if record is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    session.commit()
    return record


def disable_membership(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    membership_id: str,
    expected_version: int,
) -> Membership:
    require_actor_organization(actor, organization_id)
    statement = (
        update(Membership)
        .where(
            Membership.organization_id == actor.organization_id,
            Membership.membership_id == membership_id,
            Membership.version == expected_version,
            Membership.status == "active",
        )
        .values(status="disabled", version=Membership.version + 1, updated_at=func.now())
        .returning(Membership)
        .execution_options(synchronize_session=False)
    )
    record = session.scalars(statement).one_or_none()
    if record is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    session.commit()
    return record


def _charge_memory_collection(session: Session, organization_id: str) -> None:
    result = session.execute(
        update(Organization)
        .where(Organization.organization_id == organization_id)
        .values(memory_version=Organization.memory_version + 1, updated_at=func.now())
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        raise ResourceNotFound("resource_not_found")


def list_memories(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    *,
    as_of: datetime | None = None,
) -> tuple[list[OrganizationMemory], int]:
    require_actor_organization(actor, organization_id)
    conditions = [
        OrganizationMemory.organization_id == actor.organization_id,
        OrganizationMemory.status == "active",
    ]
    if as_of is not None:
        conditions.extend(
            [
                OrganizationMemory.valid_from <= as_of,
                or_(
                    OrganizationMemory.expires_at.is_(None),
                    OrganizationMemory.expires_at > as_of,
                ),
            ]
        )
    records = list(
        session.scalars(
            select(OrganizationMemory)
            .where(*conditions)
            .order_by(OrganizationMemory.field, OrganizationMemory.memory_id)
            .limit(100)
        )
    )
    memory_version = session.scalar(
        select(Organization.memory_version).where(
            Organization.organization_id == actor.organization_id
        )
    )
    if memory_version is None:
        raise ResourceNotFound("resource_not_found")
    return records, memory_version


def count_memories(session: Session, actor: ActorContext, organization_id: str) -> int:
    require_actor_organization(actor, organization_id)
    return int(
        session.scalar(
            select(func.count())
            .select_from(OrganizationMemory)
            .where(
                OrganizationMemory.organization_id == actor.organization_id,
                OrganizationMemory.status == "active",
            )
        )
        or 0
    )


def get_memory(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    memory_id: str,
) -> OrganizationMemory:
    require_actor_organization(actor, organization_id)
    record = session.scalar(
        select(OrganizationMemory).where(
            OrganizationMemory.organization_id == actor.organization_id,
            OrganizationMemory.memory_id == memory_id,
        )
    )
    if record is None:
        raise ResourceNotFound("resource_not_found")
    return record


def create_memory(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    payload: MemoryCreate,
) -> OrganizationMemory:
    require_actor_organization(actor, organization_id)
    memory_id = _opaque_id("mem")
    record = OrganizationMemory(
        memory_id=memory_id,
        organization_id=actor.organization_id,
        owner_user_id=actor.user_id,
        field=payload.field.value,
        safe_value=payload.safe_value,
        status="active",
        version=1,
        valid_from=payload.valid_from,
        expires_at=payload.expires_at,
        content_hash=stable_hash(payload.safe_value),
    )
    try:
        _charge_memory_collection(session, actor.organization_id)
        session.add(record)
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ResourceConflict("conflict") from exc
    session.refresh(record)
    return record


def update_memory(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    memory_id: str,
    expected_version: int,
    payload: MemoryUpdate,
) -> OrganizationMemory:
    require_actor_organization(actor, organization_id)
    _charge_memory_collection(session, actor.organization_id)
    statement = (
        update(OrganizationMemory)
        .where(
            OrganizationMemory.organization_id == actor.organization_id,
            OrganizationMemory.memory_id == memory_id,
            OrganizationMemory.version == expected_version,
            OrganizationMemory.status == "active",
        )
        .values(
            safe_value=payload.safe_value,
            valid_from=payload.valid_from,
            expires_at=payload.expires_at,
            content_hash=stable_hash(payload.safe_value),
            version=OrganizationMemory.version + 1,
            updated_at=func.now(),
        )
        .returning(OrganizationMemory)
        .execution_options(synchronize_session=False)
    )
    record = session.scalars(statement).one_or_none()
    if record is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    session.commit()
    return record


def tombstone_memory(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    memory_id: str,
    expected_version: int,
) -> OrganizationMemory:
    require_actor_organization(actor, organization_id)
    _charge_memory_collection(session, actor.organization_id)
    tombstone_hash = stable_hash(
        f"tombstone.{actor.organization_id}.{memory_id}.{expected_version + 1}"
    )
    statement = (
        update(OrganizationMemory)
        .where(
            OrganizationMemory.organization_id == actor.organization_id,
            OrganizationMemory.memory_id == memory_id,
            OrganizationMemory.version == expected_version,
            OrganizationMemory.status == "active",
        )
        .values(
            status="tombstone",
            content_hash=tombstone_hash,
            version=OrganizationMemory.version + 1,
            updated_at=func.now(),
        )
        .returning(OrganizationMemory)
        .execution_options(synchronize_session=False)
    )
    record = session.scalars(statement).one_or_none()
    if record is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    session.commit()
    return record


def reset_memories(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    expected_collection_version: int,
) -> tuple[int, int]:
    require_actor_organization(actor, organization_id)
    organization = session.scalars(
        update(Organization)
        .where(
            Organization.organization_id == actor.organization_id,
            Organization.memory_version == expected_collection_version,
        )
        .values(memory_version=Organization.memory_version + 1, updated_at=func.now())
        .returning(Organization)
        .execution_options(synchronize_session=False)
    ).one_or_none()
    if organization is None:
        session.rollback()
        raise PreconditionFailed("precondition_failed")
    records = list(
        session.scalars(
            select(OrganizationMemory)
            .where(
                OrganizationMemory.organization_id == actor.organization_id,
                OrganizationMemory.status == "active",
            )
            .order_by(OrganizationMemory.memory_id)
        )
    )
    for record in records:
        next_version = record.version + 1
        record.status = "tombstone"
        record.version = next_version
        record.content_hash = stable_hash(
            f"tombstone.{actor.organization_id}.{record.memory_id}.{next_version}"
        )
    session.commit()
    return len(records), organization.memory_version
