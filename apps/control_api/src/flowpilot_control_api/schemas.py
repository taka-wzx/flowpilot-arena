"""Strict W10 identity, tenant, and concurrency schemas."""

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
OrganizationId = Annotated[
    str, StringConstraints(pattern=r"^org_[A-Za-z0-9_-]{8,64}$", max_length=68)
]
UserId = Annotated[str, StringConstraints(pattern=r"^usr_[A-Za-z0-9_-]{8,64}$", max_length=68)]
IdentityId = Annotated[str, StringConstraints(pattern=r"^idn_[A-Za-z0-9_-]{8,64}$", max_length=68)]
MembershipId = Annotated[
    str, StringConstraints(pattern=r"^mbr_[A-Za-z0-9_-]{8,64}$", max_length=68)
]
MemoryId = Annotated[str, StringConstraints(pattern=r"^mem_[A-Za-z0-9_-]{8,64}$", max_length=68)]
SafeCode = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9][a-z0-9_.:-]{0,119}$", max_length=120),
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Role(StrEnum):
    ORGANIZATION_ADMIN = "organization_admin"
    OPERATOR = "operator"
    AUDITOR = "auditor"


class Permission(StrEnum):
    ORGANIZATION_READ = "organization.read"
    ORGANIZATION_UPDATE = "organization.update"
    USER_READ = "user.read"
    USER_MANAGE = "user.manage"
    MEMBERSHIP_READ = "membership.read"
    MEMBERSHIP_MANAGE = "membership.manage"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    MEMORY_RESET = "memory.reset"
    CONTEXT_PROJECT = "context.project"


class ActiveStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class MemoryStatus(StrEnum):
    ACTIVE = "active"
    TOMBSTONE = "tombstone"


class MemoryField(StrEnum):
    DEPARTMENT = "department"
    ROLE = "role"
    LOCATION = "location"
    DEVICE_PREFERENCE = "device_preference"
    APPROVAL_CHAIN = "approval_chain"


class ResourceKind(StrEnum):
    ORGANIZATION = "organization"
    USER = "user"
    MEMBERSHIP = "membership"
    MEMORY = "memory"
    MEMORY_COLLECTION = "memory-collection"


class ErrorCode(StrEnum):
    AUTHENTICATION_REQUIRED = "authentication_required"
    INVALID_AUTHENTICATION = "invalid_authentication"
    FORBIDDEN = "forbidden"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PRECONDITION_REQUIRED = "precondition_required"
    PRECONDITION_FAILED = "precondition_failed"
    CONFLICT = "conflict"
    SCHEMA_REJECTED = "schema_rejected"


def require_utc(value: object) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be ISO-8601 UTC") from exc
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("timestamp must be UTC")
    normalized = value.astimezone(UTC)
    if value.utcoffset() != UTC.utcoffset(normalized):
        raise ValueError("timestamp must be UTC")
    return normalized


def _jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return require_utc(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def canonical_json_bytes(value: BaseModel | dict[str, object]) -> bytes:
    data = _jsonable(value)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def stable_hash(value: BaseModel | dict[str, object] | str) -> str:
    payload = value.encode() if isinstance(value, str) else canonical_json_bytes(value)
    return hashlib.sha256(payload).hexdigest()


class HealthResponse(StrictModel):
    status: Literal["ok"] = "ok"
    service: Literal["control-api"] = "control-api"
    version: Literal["0.10.0"] = "0.10.0"


class ErrorResponse(StrictModel):
    schema_version: Literal["w10-error/1.0"] = "w10-error/1.0"
    code: ErrorCode


class ActorContext(StrictModel):
    """Internal-only authorization result; never accepted as a request body."""

    schema_version: Literal["w10-actor-context/1.0"] = "w10-actor-context/1.0"
    identity_id: IdentityId
    issuer_id: Literal["local_keycloak"] = "local_keycloak"
    issuer_hash: Sha256
    subject_hash: Sha256
    user_id: UserId
    organization_id: OrganizationId
    membership_id: MembershipId
    role: Role
    permissions: tuple[Permission, ...]
    organization_version: int = Field(ge=1)
    user_version: int = Field(ge=1)
    membership_version: int = Field(ge=1)
    authorization_hash: Sha256

    @field_validator("permissions", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class CurrentIdentityResponse(StrictModel):
    schema_version: Literal["w10-current-identity/1.0"] = "w10-current-identity/1.0"
    user_id: UserId
    organization_id: OrganizationId
    membership_id: MembershipId
    role: Role
    permissions: tuple[Permission, ...]
    authorization_hash: Sha256

    @field_validator("permissions", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class OrganizationUpdate(StrictModel):
    schema_version: Literal["w10-organization-update/1.0"] = "w10-organization-update/1.0"
    profile_code: SafeCode


class OrganizationRead(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, from_attributes=True)

    schema_version: Literal["w10-organization/1.0"] = "w10-organization/1.0"
    organization_id: OrganizationId
    profile_code: SafeCode
    status: ActiveStatus
    version: int = Field(ge=1)
    memory_version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime:
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return require_utc(value)


class UserCreate(StrictModel):
    schema_version: Literal["w10-user-create/1.0"] = "w10-user-create/1.0"
    profile_code: SafeCode


class UserUpdate(StrictModel):
    schema_version: Literal["w10-user-update/1.0"] = "w10-user-update/1.0"
    profile_code: SafeCode


class UserRead(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, from_attributes=True)

    schema_version: Literal["w10-user/1.0"] = "w10-user/1.0"
    user_id: UserId
    organization_id: OrganizationId
    profile_code: SafeCode
    status: ActiveStatus
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime:
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return require_utc(value)


class UserList(StrictModel):
    schema_version: Literal["w10-user-list/1.0"] = "w10-user-list/1.0"
    items: tuple[UserRead, ...]
    count: int = Field(ge=0, le=100)

    @field_validator("items", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class CountResponse(StrictModel):
    schema_version: Literal["w10-count/1.0"] = "w10-count/1.0"
    resource: Literal["users", "memberships", "memories"]
    count: int = Field(ge=0, le=1_000_000)


class MembershipCreate(StrictModel):
    schema_version: Literal["w10-membership-create/1.0"] = "w10-membership-create/1.0"
    user_id: UserId
    role: Role

    @field_validator("role", mode="before")
    @classmethod
    def parse_closed_role(cls, value: object) -> Role:
        if isinstance(value, Role):
            return value
        if not isinstance(value, str):
            raise ValueError("role must be a closed string")
        return Role(value)


class MembershipUpdate(StrictModel):
    schema_version: Literal["w10-membership-update/1.0"] = "w10-membership-update/1.0"
    role: Role

    @field_validator("role", mode="before")
    @classmethod
    def parse_closed_role(cls, value: object) -> Role:
        if isinstance(value, Role):
            return value
        if not isinstance(value, str):
            raise ValueError("role must be a closed string")
        return Role(value)


class MembershipRead(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, from_attributes=True)

    schema_version: Literal["w10-membership/1.0"] = "w10-membership/1.0"
    membership_id: MembershipId
    organization_id: OrganizationId
    user_id: UserId
    role: Role
    status: ActiveStatus
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime:
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return require_utc(value)


class MembershipList(StrictModel):
    schema_version: Literal["w10-membership-list/1.0"] = "w10-membership-list/1.0"
    items: tuple[MembershipRead, ...]
    count: int = Field(ge=0, le=100)

    @field_validator("items", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class MemoryCreate(StrictModel):
    schema_version: Literal["w10-memory-create/1.0"] = "w10-memory-create/1.0"
    field: MemoryField
    safe_value: SafeCode
    valid_from: datetime
    expires_at: datetime | None = None

    @field_validator("field", mode="before")
    @classmethod
    def parse_closed_field(cls, value: object) -> MemoryField:
        if isinstance(value, MemoryField):
            return value
        if not isinstance(value, str):
            raise ValueError("memory field must be a closed string")
        return MemoryField(value)

    @field_validator("valid_from", "expires_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime | None:
        return None if value is None else require_utc(value)

    @model_validator(mode="after")
    def expiry_follows_validity(self) -> Self:
        if self.expires_at is not None and self.expires_at <= self.valid_from:
            raise ValueError("memory expiry must follow validity")
        return self


class MemoryUpdate(StrictModel):
    schema_version: Literal["w10-memory-update/1.0"] = "w10-memory-update/1.0"
    safe_value: SafeCode
    valid_from: datetime
    expires_at: datetime | None = None

    @field_validator("valid_from", "expires_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime | None:
        return None if value is None else require_utc(value)

    @model_validator(mode="after")
    def expiry_follows_validity(self) -> Self:
        if self.expires_at is not None and self.expires_at <= self.valid_from:
            raise ValueError("memory expiry must follow validity")
        return self


class MemoryRead(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, from_attributes=True)

    schema_version: Literal["w10-organization-memory/1.0"] = "w10-organization-memory/1.0"
    memory_id: MemoryId
    organization_id: OrganizationId
    owner_user_id: UserId
    field: MemoryField
    safe_value: SafeCode
    status: MemoryStatus
    version: int = Field(ge=1)
    valid_from: datetime
    expires_at: datetime | None = None
    content_hash: Sha256
    created_at: datetime
    updated_at: datetime

    @field_validator("valid_from", "expires_at", "created_at", "updated_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return require_utc(value)


class MemoryList(StrictModel):
    schema_version: Literal["w10-memory-list/1.0"] = "w10-memory-list/1.0"
    items: tuple[MemoryRead, ...]
    count: int = Field(ge=0, le=100)
    collection_version: int = Field(ge=1)

    @field_validator("items", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class MemoryResetResult(StrictModel):
    schema_version: Literal["w10-memory-reset/1.0"] = "w10-memory-reset/1.0"
    organization_id: OrganizationId
    changed_count: int = Field(ge=0, le=100)
    memory_version: int = Field(ge=1)


class AuthorizedMemoryProjection(StrictModel):
    memory_id: MemoryId
    field: MemoryField
    safe_value: SafeCode
    version: int = Field(ge=1)
    valid_from: datetime
    expires_at: datetime | None = None
    content_hash: Sha256

    @field_validator("valid_from", "expires_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime | None:
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return None if value is None else require_utc(value)


class AuthorizedContextProjection(StrictModel):
    schema_version: Literal["w10-authorized-context-projection/1.0"] = (
        "w10-authorized-context-projection/1.0"
    )
    organization_hash: Sha256
    actor_hash: Sha256
    authorization_hash: Sha256
    as_of: datetime
    memory_items: tuple[AuthorizedMemoryProjection, ...] = Field(max_length=6)
    projection_hash: Sha256

    @field_validator("as_of", mode="before")
    @classmethod
    def timestamp_is_utc(cls, value: object) -> datetime:
        return require_utc(value)

    @field_validator("memory_items", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_projection_hash(self) -> Self:
        fields = self.model_dump(mode="json", exclude={"projection_hash"})
        if self.projection_hash != stable_hash(fields):
            raise ValueError("context projection hash mismatch")
        return self
