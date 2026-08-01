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
AuthorityId = Annotated[str, StringConstraints(pattern=r"^aut_[A-Za-z0-9_-]{8,64}$", max_length=68)]
ApprovalRequestId = Annotated[
    str, StringConstraints(pattern=r"^apr_[A-Za-z0-9_-]{8,64}$", max_length=68)
]
DecisionId = Annotated[str, StringConstraints(pattern=r"^dec_[A-Za-z0-9_-]{8,64}$", max_length=68)]
GrantId = Annotated[str, StringConstraints(pattern=r"^grt_[A-Za-z0-9_-]{8,64}$", max_length=68)]
ExecutionId = Annotated[str, StringConstraints(pattern=r"^exe_[A-Za-z0-9_-]{8,64}$", max_length=68)]
AuditEventId = Annotated[
    str, StringConstraints(pattern=r"^aud_[A-Za-z0-9_-]{8,64}$", max_length=68)
]
ProductionRunId = Annotated[
    str, StringConstraints(pattern=r"^run_[A-Za-z0-9_-]{8,64}$", max_length=68)
]
OutboxId = Annotated[str, StringConstraints(pattern=r"^out_[A-Za-z0-9_-]{8,64}$", max_length=68)]
IdempotencyKey = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9._:-]{16,80}$", min_length=16, max_length=80),
]
TaskReference = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_-]{7,79}$", max_length=80)
]
StepReference = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,39}$", max_length=40)]
ActionCandidate = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,63}$", max_length=64)
]
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
    APPROVAL_AUTHORITY_READ = "approval.authority.read"
    APPROVAL_AUTHORITY_MANAGE = "approval.authority.manage"
    APPROVAL_REQUEST_READ = "approval.request.read"
    APPROVAL_REQUEST_CREATE = "approval.request.create"
    APPROVAL_REQUEST_DECIDE = "approval.request.decide"
    APPROVAL_REQUEST_CANCEL = "approval.request.cancel"
    APPROVAL_GRANT_CLAIM = "approval.grant.claim"
    AUDIT_READ = "audit.read"
    AUDIT_VERIFY = "audit.verify"
    PRODUCTION_RUN_READ = "production.run.read"
    PRODUCTION_RUN_SUBMIT = "production.run.submit"
    PRODUCTION_RUN_MUTATE = "production.run.mutate"


class ApprovalRole(StrEnum):
    MANAGER = "manager"
    SECURITY = "security"


class ApprovalAuthorityStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    TOMBSTONE = "tombstone"


class RiskLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class ApprovalRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    CLAIMED = "claimed"
    CONSUMED = "consumed"
    FAILED = "failed"


class ApprovalDecisionValue(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalReason(StrEnum):
    POLICY_SATISFIED = "policy_satisfied"
    POLICY_REJECTED = "policy_rejected"
    REQUESTER_CANCELLED = "requester_cancelled"
    PARAMETERS_CHANGED = "parameters_changed"
    AUTHORITY_INACTIVE = "authority_inactive"
    REQUEST_EXPIRED = "request_expired"


class GrantStatus(StrEnum):
    ISSUED = "issued"
    CLAIMED = "claimed"
    CONSUMED = "consumed"
    REVOKED = "revoked"
    EXPIRED = "expired"
    FAILED = "failed"


class ExecutionGateStatus(StrEnum):
    AUTOMATIC = "automatic"
    WAITING_APPROVAL = "waiting_approval"


class AuditEventType(StrEnum):
    RISK_CLASSIFIED = "risk_classified"
    L4_DENIED = "l4_denied"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    REQUEST_CANCELLED = "request_cancelled"
    REQUEST_EXPIRED = "request_expired"
    REQUEST_INVALIDATED = "request_invalidated"
    GRANT_ISSUED = "grant_issued"
    GRANT_CLAIMED = "grant_claimed"
    GRANT_CONSUMED = "grant_consumed"
    GRANT_REJECTED = "grant_rejected"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_SUCCEEDED = "execution_succeeded"
    EXECUTION_FAILED = "execution_failed"
    RECOVERY_RESUMED = "recovery_resumed"
    AUTHORITY_DISABLED = "authority_disabled"
    AUDIT_VERIFIED = "audit_verified"
    RUN_WAITING_APPROVAL = "run_waiting_approval"
    RUN_QUEUED = "run_queued"
    RUN_LEASED = "run_leased"
    RUN_STARTED = "run_started"
    RUN_RECOVERED = "run_recovered"
    RUN_VERIFYING = "run_verifying"
    RUN_FINISHED_UNGRADED = "run_finished_ungraded"
    RUN_FAILED = "run_failed"
    RUN_CANCELLED = "run_cancelled"
    RUN_EXPIRED = "run_expired"
    ADMISSION_REJECTED = "admission_rejected"
    BACKPRESSURE_REJECTED = "backpressure_rejected"
    RATE_LIMITED = "rate_limited"
    LEASE_HEARTBEAT = "lease_heartbeat"
    LEASE_RELEASED = "lease_released"
    STALE_FENCE_REJECTED = "stale_fence_rejected"
    WORKFLOW_DEDUPLICATED = "workflow_deduplicated"


class ProductionRunStatus(StrEnum):
    WAITING_APPROVAL = "waiting_approval"
    QUEUED = "queued"
    LEASED = "leased"
    RUNNING = "running"
    RECOVERING = "recovering"
    VERIFYING = "verifying"
    FINISHED_UNGRADED = "finished_ungraded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ProductionTerminalReason(StrEnum):
    AGENT_FINISHED = "agent_finished"
    AGENT_FAILED = "agent_failed"
    AUTHORIZATION_INVALID = "authorization_invalid"
    QUEUE_EXPIRED = "queue_expired"
    LEASE_EXHAUSTED = "lease_exhausted"
    CANCELLED_BY_ACTOR = "cancelled_by_actor"
    WORKFLOW_REJECTED = "workflow_rejected"
    RECEIPT_INVALID = "receipt_invalid"
    WORKER_DRAINED = "worker_drained"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"


class ProductionProcess(StrEnum):
    JOINER = "joiner"
    MOVER = "mover"
    LEAVER = "leaver"


class ProductionCategory(StrEnum):
    JOINER = "standard_joiner"
    MOVER = "standard_mover"
    LEAVER = "standard_leaver"


class ProductionRouteClass(StrEnum):
    SUBMIT = "production_submit"
    READ = "production_read"
    MUTATE = "production_mutate"


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
    PRODUCTION_RUN = "production-run"


class ErrorCode(StrEnum):
    AUTHENTICATION_REQUIRED = "authentication_required"
    INVALID_AUTHENTICATION = "invalid_authentication"
    FORBIDDEN = "forbidden"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PRECONDITION_REQUIRED = "precondition_required"
    PRECONDITION_FAILED = "precondition_failed"
    CONFLICT = "conflict"
    SCHEMA_REJECTED = "schema_rejected"
    RISK_DENIED = "risk_denied"
    APPROVAL_REJECTED = "approval_rejected"
    GRANT_REJECTED = "grant_rejected"
    RATE_LIMITED = "rate_limited"
    BACKPRESSURE = "backpressure"


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


class ApprovalAuthorityContext(StrictModel):
    authority_id: AuthorityId
    role: ApprovalRole
    version: int = Field(ge=1)


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
    approval_authorities: tuple[ApprovalAuthorityContext, ...] = ()
    authorization_hash: Sha256

    @field_validator("permissions", "approval_authorities", mode="before")
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


class ApprovalAuthorityCreate(StrictModel):
    schema_version: Literal["w11-approval-authority-create/1.0"] = (
        "w11-approval-authority-create/1.0"
    )
    user_id: UserId
    role: ApprovalRole

    @field_validator("role", mode="before")
    @classmethod
    def parse_closed_role(cls, value: object) -> ApprovalRole:
        if isinstance(value, ApprovalRole):
            return value
        if not isinstance(value, str):
            raise ValueError("approval role must be a closed string")
        return ApprovalRole(value)


class ApprovalAuthorityRead(StrictModel):
    schema_version: Literal["w11-approval-authority/1.0"] = "w11-approval-authority/1.0"
    authority_id: AuthorityId
    organization_id: OrganizationId
    user_id: UserId
    role: ApprovalRole
    status: ApprovalAuthorityStatus
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime:
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return require_utc(value)


class ApprovalAuthorityList(StrictModel):
    schema_version: Literal["w11-approval-authority-list/1.0"] = "w11-approval-authority-list/1.0"
    items: tuple[ApprovalAuthorityRead, ...] = Field(max_length=100)
    count: int = Field(ge=0, le=100)

    @field_validator("items", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class CurrentApprovalAuthorities(StrictModel):
    schema_version: Literal["w11-current-approval-authorities/1.0"] = (
        "w11-current-approval-authorities/1.0"
    )
    roles: tuple[ApprovalRole, ...] = Field(max_length=2)
    authority_ids: tuple[AuthorityId, ...] = Field(max_length=2)
    authorization_hash: Sha256

    @field_validator("roles", "authority_ids", mode="before")
    @classmethod
    def accept_json_arrays(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class ExecutionGateRequest(StrictModel):
    schema_version: Literal["w11-execution-gate-request/1.0"] = "w11-execution-gate-request/1.0"
    task_id: TaskReference
    step_id: StepReference
    action_type: ActionCandidate
    parameters: dict[str, object]

    @field_validator("parameters")
    @classmethod
    def bound_parameters(cls, value: dict[str, object]) -> dict[str, object]:
        if len(value) > 12 or len(canonical_json_bytes(value)) > 4_096:
            raise ValueError("action parameters exceed the W11 bound")
        return value


class ApprovalRequestRead(StrictModel):
    schema_version: Literal["w11-approval-request/1.0"] = "w11-approval-request/1.0"
    request_id: ApprovalRequestId
    organization_id: OrganizationId
    task_id: TaskReference
    step_id: StepReference
    action_type: ActionCandidate
    parameter_hash: Sha256
    risk_level: RiskLevel
    requester_user_id: UserId
    executor_user_id: UserId
    required_roles: tuple[ApprovalRole, ...] = Field(min_length=1, max_length=2)
    status: ApprovalRequestStatus
    version: int = Field(ge=1)
    expires_at: datetime
    closed_reason: ApprovalReason | None = None
    audit_sequence: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime

    @field_validator("required_roles", mode="before")
    @classmethod
    def accept_roles_array(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(ApprovalRole(item) for item in value.split(",") if item)
        return tuple(value) if isinstance(value, list) else value

    @field_validator("expires_at", "created_at", "updated_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime:
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return require_utc(value)


class ApprovalRequestList(StrictModel):
    schema_version: Literal["w11-approval-request-list/1.0"] = "w11-approval-request-list/1.0"
    items: tuple[ApprovalRequestRead, ...] = Field(max_length=100)
    count: int = Field(ge=0, le=100)

    @field_validator("items", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class ExecutionGateResponse(StrictModel):
    schema_version: Literal["w11-execution-gate-result/1.0"] = "w11-execution-gate-result/1.0"
    status: ExecutionGateStatus
    risk_level: RiskLevel
    action_type: ActionCandidate
    parameter_hash: Sha256
    request: ApprovalRequestRead | None = None
    audit_sequence: int = Field(ge=1)

    @model_validator(mode="after")
    def request_matches_status(self) -> Self:
        if (self.status == ExecutionGateStatus.WAITING_APPROVAL) != (self.request is not None):
            raise ValueError("execution gate request/status mismatch")
        return self


class ApprovalDecisionCreate(StrictModel):
    schema_version: Literal["w11-approval-decision-create/1.0"] = "w11-approval-decision-create/1.0"
    decision: ApprovalDecisionValue
    reason: ApprovalReason

    @field_validator("decision", mode="before")
    @classmethod
    def parse_closed_decision(cls, value: object) -> ApprovalDecisionValue:
        if isinstance(value, ApprovalDecisionValue):
            return value
        if not isinstance(value, str):
            raise ValueError("approval decision must be a closed string")
        return ApprovalDecisionValue(value)

    @field_validator("reason", mode="before")
    @classmethod
    def parse_closed_reason(cls, value: object) -> ApprovalReason:
        if isinstance(value, ApprovalReason):
            return value
        if not isinstance(value, str):
            raise ValueError("approval reason must be a closed string")
        return ApprovalReason(value)

    @model_validator(mode="after")
    def reason_matches_decision(self) -> Self:
        expected = (
            ApprovalReason.POLICY_SATISFIED
            if self.decision == ApprovalDecisionValue.APPROVED
            else ApprovalReason.POLICY_REJECTED
        )
        if self.reason != expected:
            raise ValueError("approval decision reason does not match the closed decision")
        return self


class ApprovalDecisionRead(StrictModel):
    schema_version: Literal["w11-approval-decision/1.0"] = "w11-approval-decision/1.0"
    decision_id: DecisionId
    organization_id: OrganizationId
    request_id: ApprovalRequestId
    decision: ApprovalDecisionValue
    approver_user_id: UserId
    authority_id: AuthorityId
    approval_role: ApprovalRole
    request_version: int = Field(ge=1)
    action_type: ActionCandidate
    parameter_hash: Sha256
    reason: ApprovalReason
    audit_sequence: int = Field(ge=1)
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def timestamp_is_utc(cls, value: object) -> datetime:
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return require_utc(value)


class ApprovalDecisionResult(StrictModel):
    schema_version: Literal["w11-approval-decision-result/1.0"] = "w11-approval-decision-result/1.0"
    decision: ApprovalDecisionRead
    request: ApprovalRequestRead
    grant_issued: bool


class RequestClose(StrictModel):
    schema_version: Literal["w11-approval-request-close/1.0"] = "w11-approval-request-close/1.0"
    reason: ApprovalReason

    @field_validator("reason", mode="before")
    @classmethod
    def parse_closed_reason(cls, value: object) -> ApprovalReason:
        if isinstance(value, ApprovalReason):
            return value
        if not isinstance(value, str):
            raise ValueError("approval reason must be a closed string")
        return ApprovalReason(value)


class GrantClaimRequest(StrictModel):
    schema_version: Literal["w11-grant-claim-request/1.0"] = "w11-grant-claim-request/1.0"
    task_id: TaskReference
    step_id: StepReference
    action_type: ActionCandidate
    parameters: dict[str, object]

    @field_validator("parameters")
    @classmethod
    def bound_parameters(cls, value: dict[str, object]) -> dict[str, object]:
        if len(value) > 12 or len(canonical_json_bytes(value)) > 4_096:
            raise ValueError("action parameters exceed the W11 bound")
        return value


class ExecutionClaimRead(StrictModel):
    schema_version: Literal["w11-execution-claim/1.0"] = "w11-execution-claim/1.0"
    execution_id: ExecutionId
    grant_id: GrantId
    request_id: ApprovalRequestId
    organization_id: OrganizationId
    task_id: TaskReference
    step_id: StepReference
    action_type: ActionCandidate
    parameter_hash: Sha256
    authorization_hash: Sha256
    grant_status: GrantStatus
    grant_version: int = Field(ge=1)
    claimed_at: datetime

    @field_validator("claimed_at", mode="before")
    @classmethod
    def timestamp_is_utc(cls, value: object) -> datetime:
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return require_utc(value)


class AuditEventRead(StrictModel):
    schema_version: Literal["w11-audit-event/1.0"] = "w11-audit-event/1.0"
    event_id: AuditEventId
    organization_id: OrganizationId
    sequence: int = Field(ge=1)
    event_type: AuditEventType
    previous_hash: Sha256
    event_hash: Sha256
    payload_hash: Sha256
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def timestamp_is_utc(cls, value: object) -> datetime:
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return require_utc(value)


class AuditEventList(StrictModel):
    schema_version: Literal["w11-audit-event-list/1.0"] = "w11-audit-event-list/1.0"
    items: tuple[AuditEventRead, ...] = Field(max_length=200)
    count: int = Field(ge=0, le=200)
    head_sequence: int = Field(ge=0)
    head_hash: Sha256

    @field_validator("items", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class AuditVerificationResult(StrictModel):
    schema_version: Literal["w11-audit-verification/1.0"] = "w11-audit-verification/1.0"
    valid: bool
    event_count: int = Field(ge=0)
    head_sequence: int = Field(ge=0)
    head_hash: Sha256
    reason: Literal[
        "valid",
        "sequence_mismatch",
        "previous_hash_mismatch",
        "event_hash_mismatch",
        "head_mismatch",
    ]


class ProductionRunCreate(StrictModel):
    schema_version: Literal["w12-production-run-create/1.0"] = "w12-production-run-create/1.0"
    task_id: Literal[
        "w7-jml-joiner-001-v1",
        "w7-jml-joiner-001-v2",
        "w7-jml-joiner-002-v1",
        "w7-jml-joiner-002-v2",
        "w7-jml-mover-001-v1",
        "w7-jml-mover-001-v2",
        "w7-jml-leaver-001-v1",
        "w7-jml-leaver-001-v2",
    ]
    process: ProductionProcess
    category: ProductionCategory
    action_type: ActionCandidate
    parameters: dict[str, object]

    @field_validator("process", mode="before")
    @classmethod
    def parse_process(cls, value: object) -> ProductionProcess:
        if isinstance(value, ProductionProcess):
            return value
        if not isinstance(value, str):
            raise ValueError("process must be a closed string")
        return ProductionProcess(value)

    @field_validator("category", mode="before")
    @classmethod
    def parse_category(cls, value: object) -> ProductionCategory:
        if isinstance(value, ProductionCategory):
            return value
        if not isinstance(value, str):
            raise ValueError("category must be a closed string")
        return ProductionCategory(value)

    @field_validator("parameters")
    @classmethod
    def bound_parameters(cls, value: dict[str, object]) -> dict[str, object]:
        if len(value) > 12 or len(canonical_json_bytes(value)) > 4_096:
            raise ValueError("production parameters exceed the W12 bound")
        return value

    @model_validator(mode="after")
    def task_process_category_match(self) -> Self:
        expected = {
            "w7-jml-joiner-001-v1": (
                ProductionProcess.JOINER,
                ProductionCategory.JOINER,
            ),
            "w7-jml-joiner-001-v2": (
                ProductionProcess.JOINER,
                ProductionCategory.JOINER,
            ),
            "w7-jml-joiner-002-v1": (
                ProductionProcess.JOINER,
                ProductionCategory.JOINER,
            ),
            "w7-jml-joiner-002-v2": (
                ProductionProcess.JOINER,
                ProductionCategory.JOINER,
            ),
            "w7-jml-mover-001-v1": (
                ProductionProcess.MOVER,
                ProductionCategory.MOVER,
            ),
            "w7-jml-mover-001-v2": (
                ProductionProcess.MOVER,
                ProductionCategory.MOVER,
            ),
            "w7-jml-leaver-001-v1": (
                ProductionProcess.LEAVER,
                ProductionCategory.LEAVER,
            ),
            "w7-jml-leaver-001-v2": (
                ProductionProcess.LEAVER,
                ProductionCategory.LEAVER,
            ),
        }[self.task_id]
        if (self.process, self.category) != expected:
            raise ValueError("task, process, and category must match")
        return self


class ProductionRunClaim(StrictModel):
    schema_version: Literal["w12-production-run-claim/1.0"] = "w12-production-run-claim/1.0"
    action_type: ActionCandidate
    parameters: dict[str, object]

    @field_validator("parameters")
    @classmethod
    def bound_parameters(cls, value: dict[str, object]) -> dict[str, object]:
        if len(value) > 12 or len(canonical_json_bytes(value)) > 4_096:
            raise ValueError("production parameters exceed the W12 bound")
        return value


class ProductionRunRead(StrictModel):
    schema_version: Literal["w12-production-run/1.0"] = "w12-production-run/1.0"
    run_id: ProductionRunId
    organization_id: OrganizationId
    requester_user_id: UserId
    executor_user_id: UserId
    task_id: Literal[
        "w7-jml-joiner-001-v1",
        "w7-jml-joiner-001-v2",
        "w7-jml-joiner-002-v1",
        "w7-jml-joiner-002-v2",
        "w7-jml-mover-001-v1",
        "w7-jml-mover-001-v2",
        "w7-jml-leaver-001-v1",
        "w7-jml-leaver-001-v2",
    ]
    process: ProductionProcess
    category: ProductionCategory
    approval_request_id: ApprovalRequestId | None = None
    grant_id: GrantId | None = None
    execution_id: ExecutionId | None = None
    action_type: ActionCandidate
    parameter_hash: Sha256
    authorization_hash: Sha256
    approval_set_hash: Sha256 | None = None
    payload_hash: Sha256
    status: ProductionRunStatus
    version: int = Field(ge=1)
    workflow_hash: Sha256
    fencing_token: int = Field(ge=0)
    accepted_at: datetime
    queued_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    terminal_reason: ProductionTerminalReason | None = None
    receipt_reference: (
        Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{8,80}$", max_length=80)] | None
    ) = None
    audit_sequence: int = Field(ge=1)

    @field_validator("accepted_at", "queued_at", "started_at", "finished_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return require_utc(value)


class ProductionRunList(StrictModel):
    schema_version: Literal["w12-production-run-list/1.0"] = "w12-production-run-list/1.0"
    items: tuple[ProductionRunRead, ...] = Field(max_length=100)
    count: int = Field(ge=0, le=100)

    @field_validator("items", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value
