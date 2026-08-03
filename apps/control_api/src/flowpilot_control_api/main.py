"""W10 OIDC-authenticated, tenant-isolated Control Plane API."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, Header, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from flowpilot_control_api.approval import (
    ApprovalStateConflict,
    GrantRejected,
    RiskDenied,
    TrustedGrantVault,
    authority_read,
    claim_grant,
    close_request,
    create_authority,
    create_execution_gate,
    decide_request,
    disable_authority,
    get_authority,
    get_request,
    list_authorities,
    list_requests,
    request_read,
)
from flowpilot_control_api.audit import (
    AuditChainMissing,
    append_audit_event,
    event_read,
    list_audit_events,
    verify_audit_chain,
)
from flowpilot_control_api.auth import (
    AuthenticationError,
    HttpJwksSource,
    OidcVerifier,
    extract_bearer,
)
from flowpilot_control_api.config import Settings, load_settings
from flowpilot_control_api.context_projection import build_context_projection
from flowpilot_control_api.database import engine, get_session
from flowpilot_control_api.etag import (
    PreconditionFailed,
    PreconditionRequired,
    expected_version,
    strong_etag,
)
from flowpilot_control_api.models import Membership, Organization, OrganizationMemory, User
from flowpilot_control_api.observability import (
    ObservabilityPayloadRejected,
    build_run_trace_export,
)
from flowpilot_control_api.production import (
    BackpressureExceeded,
    IdempotencyConflict,
    ProductionStateConflict,
    RateLimitExceeded,
    admit_production_run,
    cancel_production_run,
    claim_production_run,
    ensure_scheduler_partitions,
    get_production_run,
    list_production_runs,
    run_read,
)
from flowpilot_control_api.rbac import AuthorizationDenied, require_permission
from flowpilot_control_api.repository import (
    ResourceConflict,
    ResourceNotFound,
    count_memberships,
    count_memories,
    count_users,
    create_membership,
    create_memory,
    create_user,
    disable_membership,
    disable_organization,
    disable_user,
    get_membership,
    get_memory,
    get_organization,
    get_user,
    list_memberships,
    list_memories,
    list_users,
    reset_memories,
    resolve_actor,
    tombstone_memory,
    update_membership,
    update_memory,
    update_organization,
    update_user,
)
from flowpilot_control_api.risk import RiskSchemaRejected
from flowpilot_control_api.schemas import (
    ActiveStatus,
    ActorContext,
    ApprovalAuthorityCreate,
    ApprovalAuthorityList,
    ApprovalAuthorityRead,
    ApprovalDecisionCreate,
    ApprovalDecisionResult,
    ApprovalRequestId,
    ApprovalRequestList,
    ApprovalRequestRead,
    AuditEventList,
    AuditEventType,
    AuditVerificationResult,
    AuthorityId,
    AuthorizedContextProjection,
    CountResponse,
    CurrentApprovalAuthorities,
    CurrentIdentityResponse,
    ErrorCode,
    ErrorResponse,
    ExecutionClaimRead,
    ExecutionGateRequest,
    ExecutionGateResponse,
    GrantClaimRequest,
    HealthResponse,
    IdempotencyKey,
    MembershipCreate,
    MembershipId,
    MembershipList,
    MembershipRead,
    MembershipUpdate,
    MemoryCreate,
    MemoryField,
    MemoryId,
    MemoryList,
    MemoryRead,
    MemoryResetResult,
    MemoryStatus,
    MemoryUpdate,
    OrganizationId,
    OrganizationRead,
    OrganizationUpdate,
    Permission,
    ProductionRunClaim,
    ProductionRunCreate,
    ProductionRunId,
    ProductionRunList,
    ProductionRunRead,
    RequestClose,
    ResourceKind,
    Role,
    RunTraceExport,
    UserCreate,
    UserId,
    UserList,
    UserRead,
    UserUpdate,
)
from flowpilot_control_api.seed import seed_synthetic_identities
from flowpilot_control_api.w11_etag import (
    W11ResourceKind,
    expected_w11_version,
    strong_w11_etag,
)

SessionDependency = Annotated[Session, Depends(get_session)]
IfMatch = Annotated[str | None, Header(alias="If-Match")]


def _error(code: ErrorCode, http_status: int, *, authenticate: bool = False) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if authenticate else None
    return JSONResponse(
        status_code=http_status,
        content=ErrorResponse(code=code).model_dump(mode="json"),
        headers=headers,
    )


def _organization_read(record: Organization) -> OrganizationRead:
    return OrganizationRead(
        organization_id=record.organization_id,
        profile_code=record.profile_code,
        status=ActiveStatus(record.status),
        version=record.version,
        memory_version=record.memory_version,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _user_read(record: User) -> UserRead:
    return UserRead(
        user_id=record.user_id,
        organization_id=record.organization_id,
        profile_code=record.profile_code,
        status=ActiveStatus(record.status),
        version=record.version,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _membership_read(record: Membership) -> MembershipRead:
    return MembershipRead(
        membership_id=record.membership_id,
        organization_id=record.organization_id,
        user_id=record.user_id,
        role=Role(record.role),
        status=ActiveStatus(record.status),
        version=record.version,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _memory_read(record: OrganizationMemory) -> MemoryRead:
    return MemoryRead(
        memory_id=record.memory_id,
        organization_id=record.organization_id,
        owner_user_id=record.owner_user_id,
        field=MemoryField(record.field),
        safe_value=record.safe_value,
        status=MemoryStatus(record.status),
        version=record.version,
        valid_from=record.valid_from,
        expires_at=record.expires_at,
        content_hash=record.content_hash,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _set_resource_etag(
    response: Response,
    kind: ResourceKind,
    organization_id: str,
    resource_id: str,
    version: int,
) -> None:
    response.headers["ETag"] = strong_etag(kind, organization_id, resource_id, version)


def _set_w11_etag(
    response: Response,
    kind: W11ResourceKind,
    organization_id: str,
    resource_id: str,
    version: int,
) -> None:
    response.headers["ETag"] = strong_w11_etag(kind, organization_id, resource_id, version)


def create_app(
    *,
    settings: Settings | None = None,
    verifier: OidcVerifier | None = None,
    run_startup: bool = True,
) -> FastAPI:
    current_settings = settings or load_settings()
    current_settings.validate()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if run_startup:
            root = Path(__file__).resolve().parents[2]
            alembic = Config(str(root / "alembic.ini"))
            command.upgrade(alembic, "head")
            if current_settings.seed_synthetic_identities:
                with Session(engine) as session:
                    seed_synthetic_identities(session, current_settings.oidc)
            with Session(engine) as session:
                ensure_scheduler_partitions(session, now=datetime.now(UTC))
        active_verifier = verifier or OidcVerifier(
            current_settings.oidc,
            HttpJwksSource(current_settings.oidc),
        )
        app.state.oidc_verifier = active_verifier
        app.state.grant_vault = TrustedGrantVault()
        yield
        await active_verifier.close()

    application = FastAPI(
        title="FlowPilot W12 Control API",
        version="0.12.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[current_settings.allowed_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "If-Match", "Idempotency-Key"],
        expose_headers=["ETag", "Retry-After"],
        max_age=600,
    )

    @application.exception_handler(AuthenticationError)
    async def authentication_error(_: Request, exc: AuthenticationError) -> JSONResponse:
        code = (
            ErrorCode.AUTHENTICATION_REQUIRED
            if exc.reason == "authentication_required"
            else ErrorCode.INVALID_AUTHENTICATION
        )
        return _error(code, status.HTTP_401_UNAUTHORIZED, authenticate=True)

    @application.exception_handler(AuthorizationDenied)
    async def authorization_error(_: Request, __: AuthorizationDenied) -> JSONResponse:
        return _error(ErrorCode.FORBIDDEN, status.HTTP_403_FORBIDDEN)

    @application.exception_handler(ResourceNotFound)
    async def resource_error(_: Request, __: ResourceNotFound) -> JSONResponse:
        return _error(ErrorCode.RESOURCE_NOT_FOUND, status.HTTP_404_NOT_FOUND)

    @application.exception_handler(PreconditionRequired)
    async def precondition_required(_: Request, __: PreconditionRequired) -> JSONResponse:
        return _error(ErrorCode.PRECONDITION_REQUIRED, status.HTTP_428_PRECONDITION_REQUIRED)

    @application.exception_handler(PreconditionFailed)
    async def precondition_failed(_: Request, __: PreconditionFailed) -> JSONResponse:
        return _error(ErrorCode.PRECONDITION_FAILED, status.HTTP_412_PRECONDITION_FAILED)

    @application.exception_handler(ResourceConflict)
    async def resource_conflict(_: Request, __: ResourceConflict) -> JSONResponse:
        return _error(ErrorCode.CONFLICT, status.HTTP_409_CONFLICT)

    @application.exception_handler(RequestValidationError)
    async def schema_rejected(_: Request, __: RequestValidationError) -> JSONResponse:
        return _error(ErrorCode.SCHEMA_REJECTED, status.HTTP_422_UNPROCESSABLE_CONTENT)

    @application.exception_handler(RiskSchemaRejected)
    async def risk_schema_rejected(_: Request, __: RiskSchemaRejected) -> JSONResponse:
        return _error(ErrorCode.SCHEMA_REJECTED, status.HTTP_422_UNPROCESSABLE_CONTENT)

    @application.exception_handler(RiskDenied)
    async def risk_denied(_: Request, __: RiskDenied) -> JSONResponse:
        return _error(ErrorCode.RISK_DENIED, status.HTTP_403_FORBIDDEN)

    @application.exception_handler(ApprovalStateConflict)
    async def approval_conflict(_: Request, __: ApprovalStateConflict) -> JSONResponse:
        return _error(ErrorCode.CONFLICT, status.HTTP_409_CONFLICT)

    @application.exception_handler(GrantRejected)
    async def grant_rejected(_: Request, __: GrantRejected) -> JSONResponse:
        return _error(ErrorCode.GRANT_REJECTED, status.HTTP_409_CONFLICT)

    @application.exception_handler(IdempotencyConflict)
    async def idempotency_conflict(_: Request, __: IdempotencyConflict) -> JSONResponse:
        return _error(ErrorCode.CONFLICT, status.HTTP_409_CONFLICT)

    @application.exception_handler(ProductionStateConflict)
    async def production_conflict(_: Request, __: ProductionStateConflict) -> JSONResponse:
        return _error(ErrorCode.CONFLICT, status.HTTP_409_CONFLICT)

    @application.exception_handler(RateLimitExceeded)
    async def rate_limited(_: Request, exc: RateLimitExceeded) -> JSONResponse:
        response = _error(ErrorCode.RATE_LIMITED, status.HTTP_429_TOO_MANY_REQUESTS)
        response.headers["Retry-After"] = str(exc.retry_after)
        return response

    @application.exception_handler(BackpressureExceeded)
    async def backpressure(_: Request, exc: BackpressureExceeded) -> JSONResponse:
        response = _error(ErrorCode.BACKPRESSURE, status.HTTP_503_SERVICE_UNAVAILABLE)
        response.headers["Retry-After"] = str(exc.retry_after)
        return response

    @application.exception_handler(AuditChainMissing)
    async def audit_missing(_: Request, __: AuditChainMissing) -> JSONResponse:
        return _error(ErrorCode.RESOURCE_NOT_FOUND, status.HTTP_404_NOT_FOUND)

    @application.exception_handler(ObservabilityPayloadRejected)
    async def observability_rejected(_: Request, __: ObservabilityPayloadRejected) -> JSONResponse:
        return _error(ErrorCode.SCHEMA_REJECTED, status.HTTP_422_UNPROCESSABLE_CONTENT)

    @application.get("/healthz", response_model=HealthResponse, tags=["health"])
    def healthz() -> HealthResponse:
        return HealthResponse()

    async def current_actor(
        request: Request,
        session: SessionDependency,
        authorization: Annotated[str | None, Header()] = None,
    ) -> ActorContext:
        token = extract_bearer(
            authorization,
            query_names=set(request.query_params.keys()),
            cookie_names=set(request.cookies.keys()),
        )
        oidc = request.app.state.oidc_verifier
        verified = await oidc.verify(token)
        return await run_in_threadpool(resolve_actor, session, verified)

    ActorDependency = Annotated[ActorContext, Depends(current_actor)]

    def authorize(actor: ActorContext, permission: Permission) -> None:
        require_permission(actor.role, permission)

    @application.get("/api/v1/identity/me", response_model=CurrentIdentityResponse)
    async def current_identity(actor: ActorDependency) -> CurrentIdentityResponse:
        return CurrentIdentityResponse(
            user_id=actor.user_id,
            organization_id=actor.organization_id,
            membership_id=actor.membership_id,
            role=actor.role,
            permissions=actor.permissions,
            authorization_hash=actor.authorization_hash,
        )

    @application.get("/api/v1/organizations/{organization_id}", response_model=OrganizationRead)
    async def read_organization(
        organization_id: OrganizationId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> OrganizationRead:
        authorize(actor, Permission.ORGANIZATION_READ)
        record = get_organization(session, actor, organization_id)
        _set_resource_etag(
            response,
            ResourceKind.ORGANIZATION,
            organization_id,
            organization_id,
            record.version,
        )
        return _organization_read(record)

    @application.patch("/api/v1/organizations/{organization_id}", response_model=OrganizationRead)
    async def patch_organization(
        organization_id: OrganizationId,
        payload: OrganizationUpdate,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> OrganizationRead:
        authorize(actor, Permission.ORGANIZATION_UPDATE)
        version = expected_version(
            if_match,
            kind=ResourceKind.ORGANIZATION,
            organization_id=organization_id,
            resource_id=organization_id,
        )
        record = update_organization(session, actor, organization_id, version, payload.profile_code)
        _set_resource_etag(
            response,
            ResourceKind.ORGANIZATION,
            organization_id,
            organization_id,
            record.version,
        )
        return _organization_read(record)

    @application.delete("/api/v1/organizations/{organization_id}", response_model=OrganizationRead)
    async def delete_organization(
        organization_id: OrganizationId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> OrganizationRead:
        authorize(actor, Permission.ORGANIZATION_UPDATE)
        version = expected_version(
            if_match,
            kind=ResourceKind.ORGANIZATION,
            organization_id=organization_id,
            resource_id=organization_id,
        )
        record = disable_organization(session, actor, organization_id, version)
        _set_resource_etag(
            response,
            ResourceKind.ORGANIZATION,
            organization_id,
            organization_id,
            record.version,
        )
        return _organization_read(record)

    @application.get("/api/v1/organizations/{organization_id}/users", response_model=UserList)
    async def read_users(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> UserList:
        authorize(actor, Permission.USER_READ)
        items = tuple(_user_read(item) for item in list_users(session, actor, organization_id))
        return UserList(items=items, count=len(items))

    @application.get(
        "/api/v1/organizations/{organization_id}/users/count", response_model=CountResponse
    )
    async def read_user_count(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> CountResponse:
        authorize(actor, Permission.USER_READ)
        return CountResponse(resource="users", count=count_users(session, actor, organization_id))

    @application.post(
        "/api/v1/organizations/{organization_id}/users",
        response_model=UserRead,
        status_code=status.HTTP_201_CREATED,
    )
    async def post_user(
        organization_id: OrganizationId,
        payload: UserCreate,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> UserRead:
        authorize(actor, Permission.USER_MANAGE)
        record = create_user(session, actor, organization_id, payload)
        _set_resource_etag(
            response, ResourceKind.USER, organization_id, record.user_id, record.version
        )
        return _user_read(record)

    @application.get(
        "/api/v1/organizations/{organization_id}/users/{user_id}", response_model=UserRead
    )
    async def read_user(
        organization_id: OrganizationId,
        user_id: UserId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> UserRead:
        authorize(actor, Permission.USER_READ)
        record = get_user(session, actor, organization_id, user_id)
        _set_resource_etag(response, ResourceKind.USER, organization_id, user_id, record.version)
        return _user_read(record)

    @application.patch(
        "/api/v1/organizations/{organization_id}/users/{user_id}", response_model=UserRead
    )
    async def patch_user(
        organization_id: OrganizationId,
        user_id: UserId,
        payload: UserUpdate,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> UserRead:
        authorize(actor, Permission.USER_MANAGE)
        version = expected_version(
            if_match,
            kind=ResourceKind.USER,
            organization_id=organization_id,
            resource_id=user_id,
        )
        record = update_user(session, actor, organization_id, user_id, version, payload)
        _set_resource_etag(response, ResourceKind.USER, organization_id, user_id, record.version)
        return _user_read(record)

    @application.delete(
        "/api/v1/organizations/{organization_id}/users/{user_id}", response_model=UserRead
    )
    async def delete_user(
        organization_id: OrganizationId,
        user_id: UserId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> UserRead:
        authorize(actor, Permission.USER_MANAGE)
        version = expected_version(
            if_match,
            kind=ResourceKind.USER,
            organization_id=organization_id,
            resource_id=user_id,
        )
        record = disable_user(session, actor, organization_id, user_id, version)
        _set_resource_etag(response, ResourceKind.USER, organization_id, user_id, record.version)
        return _user_read(record)

    @application.get(
        "/api/v1/organizations/{organization_id}/memberships",
        response_model=MembershipList,
    )
    async def read_memberships(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> MembershipList:
        authorize(actor, Permission.MEMBERSHIP_READ)
        items = tuple(
            _membership_read(item) for item in list_memberships(session, actor, organization_id)
        )
        return MembershipList(items=items, count=len(items))

    @application.get(
        "/api/v1/organizations/{organization_id}/memberships/count",
        response_model=CountResponse,
    )
    async def read_membership_count(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> CountResponse:
        authorize(actor, Permission.MEMBERSHIP_READ)
        return CountResponse(
            resource="memberships",
            count=count_memberships(session, actor, organization_id),
        )

    @application.post(
        "/api/v1/organizations/{organization_id}/memberships",
        response_model=MembershipRead,
        status_code=status.HTTP_201_CREATED,
    )
    async def post_membership(
        organization_id: OrganizationId,
        payload: MembershipCreate,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> MembershipRead:
        authorize(actor, Permission.MEMBERSHIP_MANAGE)
        record = create_membership(session, actor, organization_id, payload)
        _set_resource_etag(
            response,
            ResourceKind.MEMBERSHIP,
            organization_id,
            record.membership_id,
            record.version,
        )
        return _membership_read(record)

    @application.get(
        "/api/v1/organizations/{organization_id}/memberships/{membership_id}",
        response_model=MembershipRead,
    )
    async def read_membership(
        organization_id: OrganizationId,
        membership_id: MembershipId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> MembershipRead:
        authorize(actor, Permission.MEMBERSHIP_READ)
        record = get_membership(session, actor, organization_id, membership_id)
        _set_resource_etag(
            response,
            ResourceKind.MEMBERSHIP,
            organization_id,
            membership_id,
            record.version,
        )
        return _membership_read(record)

    @application.patch(
        "/api/v1/organizations/{organization_id}/memberships/{membership_id}",
        response_model=MembershipRead,
    )
    async def patch_membership(
        organization_id: OrganizationId,
        membership_id: MembershipId,
        payload: MembershipUpdate,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> MembershipRead:
        authorize(actor, Permission.MEMBERSHIP_MANAGE)
        version = expected_version(
            if_match,
            kind=ResourceKind.MEMBERSHIP,
            organization_id=organization_id,
            resource_id=membership_id,
        )
        record = update_membership(session, actor, organization_id, membership_id, version, payload)
        _set_resource_etag(
            response,
            ResourceKind.MEMBERSHIP,
            organization_id,
            membership_id,
            record.version,
        )
        return _membership_read(record)

    @application.delete(
        "/api/v1/organizations/{organization_id}/memberships/{membership_id}",
        response_model=MembershipRead,
    )
    async def delete_membership(
        organization_id: OrganizationId,
        membership_id: MembershipId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> MembershipRead:
        authorize(actor, Permission.MEMBERSHIP_MANAGE)
        version = expected_version(
            if_match,
            kind=ResourceKind.MEMBERSHIP,
            organization_id=organization_id,
            resource_id=membership_id,
        )
        record = disable_membership(session, actor, organization_id, membership_id, version)
        _set_resource_etag(
            response,
            ResourceKind.MEMBERSHIP,
            organization_id,
            membership_id,
            record.version,
        )
        return _membership_read(record)

    @application.get("/api/v1/organizations/{organization_id}/memories", response_model=MemoryList)
    async def read_memories(
        organization_id: OrganizationId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> MemoryList:
        authorize(actor, Permission.MEMORY_READ)
        records, collection_version = list_memories(session, actor, organization_id)
        _set_resource_etag(
            response,
            ResourceKind.MEMORY_COLLECTION,
            organization_id,
            organization_id,
            collection_version,
        )
        return MemoryList(
            items=tuple(_memory_read(item) for item in records),
            count=len(records),
            collection_version=collection_version,
        )

    @application.get(
        "/api/v1/organizations/{organization_id}/memories/count",
        response_model=CountResponse,
    )
    async def read_memory_count(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> CountResponse:
        authorize(actor, Permission.MEMORY_READ)
        return CountResponse(
            resource="memories", count=count_memories(session, actor, organization_id)
        )

    @application.post(
        "/api/v1/organizations/{organization_id}/memories/reset",
        response_model=MemoryResetResult,
    )
    async def post_memory_reset(
        organization_id: OrganizationId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> MemoryResetResult:
        authorize(actor, Permission.MEMORY_RESET)
        version = expected_version(
            if_match,
            kind=ResourceKind.MEMORY_COLLECTION,
            organization_id=organization_id,
            resource_id=organization_id,
        )
        changed, memory_version = reset_memories(session, actor, organization_id, version)
        _set_resource_etag(
            response,
            ResourceKind.MEMORY_COLLECTION,
            organization_id,
            organization_id,
            memory_version,
        )
        return MemoryResetResult(
            organization_id=organization_id,
            changed_count=changed,
            memory_version=memory_version,
        )

    @application.post(
        "/api/v1/organizations/{organization_id}/memories",
        response_model=MemoryRead,
        status_code=status.HTTP_201_CREATED,
    )
    async def post_memory(
        organization_id: OrganizationId,
        payload: MemoryCreate,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> MemoryRead:
        authorize(actor, Permission.MEMORY_WRITE)
        record = create_memory(session, actor, organization_id, payload)
        _set_resource_etag(
            response, ResourceKind.MEMORY, organization_id, record.memory_id, record.version
        )
        return _memory_read(record)

    @application.get(
        "/api/v1/organizations/{organization_id}/memories/{memory_id}",
        response_model=MemoryRead,
    )
    async def read_memory(
        organization_id: OrganizationId,
        memory_id: MemoryId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> MemoryRead:
        authorize(actor, Permission.MEMORY_READ)
        record = get_memory(session, actor, organization_id, memory_id)
        _set_resource_etag(
            response, ResourceKind.MEMORY, organization_id, memory_id, record.version
        )
        return _memory_read(record)

    @application.patch(
        "/api/v1/organizations/{organization_id}/memories/{memory_id}",
        response_model=MemoryRead,
    )
    async def patch_memory(
        organization_id: OrganizationId,
        memory_id: MemoryId,
        payload: MemoryUpdate,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> MemoryRead:
        authorize(actor, Permission.MEMORY_WRITE)
        version = expected_version(
            if_match,
            kind=ResourceKind.MEMORY,
            organization_id=organization_id,
            resource_id=memory_id,
        )
        record = update_memory(session, actor, organization_id, memory_id, version, payload)
        _set_resource_etag(
            response, ResourceKind.MEMORY, organization_id, memory_id, record.version
        )
        return _memory_read(record)

    @application.delete(
        "/api/v1/organizations/{organization_id}/memories/{memory_id}",
        response_model=MemoryRead,
    )
    async def delete_memory(
        organization_id: OrganizationId,
        memory_id: MemoryId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> MemoryRead:
        authorize(actor, Permission.MEMORY_WRITE)
        version = expected_version(
            if_match,
            kind=ResourceKind.MEMORY,
            organization_id=organization_id,
            resource_id=memory_id,
        )
        record = tombstone_memory(session, actor, organization_id, memory_id, version)
        _set_resource_etag(
            response, ResourceKind.MEMORY, organization_id, memory_id, record.version
        )
        return _memory_read(record)

    @application.get(
        "/api/v1/organizations/{organization_id}/context-projection",
        response_model=AuthorizedContextProjection,
    )
    async def context_projection(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> AuthorizedContextProjection:
        authorize(actor, Permission.CONTEXT_PROJECT)
        return build_context_projection(
            session,
            actor,
            organization_id,
            datetime.now(UTC),
        )

    @application.get(
        "/api/v1/approval-authorities/me",
        response_model=CurrentApprovalAuthorities,
    )
    async def current_approval_authorities(
        actor: ActorDependency,
    ) -> CurrentApprovalAuthorities:
        return CurrentApprovalAuthorities(
            roles=tuple(item.role for item in actor.approval_authorities),
            authority_ids=tuple(item.authority_id for item in actor.approval_authorities),
            authorization_hash=actor.authorization_hash,
        )

    @application.get(
        "/api/v1/organizations/{organization_id}/approval-authorities",
        response_model=ApprovalAuthorityList,
    )
    async def read_approval_authorities(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> ApprovalAuthorityList:
        authorize(actor, Permission.APPROVAL_AUTHORITY_READ)
        items = tuple(
            authority_read(item) for item in list_authorities(session, actor, organization_id)
        )
        return ApprovalAuthorityList(items=items, count=len(items))

    @application.post(
        "/api/v1/organizations/{organization_id}/approval-authorities",
        response_model=ApprovalAuthorityRead,
        status_code=status.HTTP_201_CREATED,
    )
    async def post_approval_authority(
        organization_id: OrganizationId,
        payload: ApprovalAuthorityCreate,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> ApprovalAuthorityRead:
        authorize(actor, Permission.APPROVAL_AUTHORITY_MANAGE)
        record = create_authority(session, actor, organization_id, payload)
        _set_w11_etag(
            response,
            W11ResourceKind.AUTHORITY,
            organization_id,
            record.authority_id,
            record.version,
        )
        return authority_read(record)

    @application.get(
        "/api/v1/organizations/{organization_id}/approval-authorities/{authority_id}",
        response_model=ApprovalAuthorityRead,
    )
    async def read_approval_authority(
        organization_id: OrganizationId,
        authority_id: AuthorityId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> ApprovalAuthorityRead:
        authorize(actor, Permission.APPROVAL_AUTHORITY_READ)
        record = get_authority(session, actor, organization_id, authority_id)
        _set_w11_etag(
            response,
            W11ResourceKind.AUTHORITY,
            organization_id,
            authority_id,
            record.version,
        )
        return authority_read(record)

    @application.delete(
        "/api/v1/organizations/{organization_id}/approval-authorities/{authority_id}",
        response_model=ApprovalAuthorityRead,
    )
    async def delete_approval_authority(
        organization_id: OrganizationId,
        authority_id: AuthorityId,
        response: Response,
        request: Request,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> ApprovalAuthorityRead:
        authorize(actor, Permission.APPROVAL_AUTHORITY_MANAGE)
        version = expected_w11_version(
            if_match,
            kind=W11ResourceKind.AUTHORITY,
            organization_id=organization_id,
            resource_id=authority_id,
        )
        record = disable_authority(
            session,
            actor,
            organization_id,
            authority_id,
            version,
            now=datetime.now(UTC),
            vault=request.app.state.grant_vault,
        )
        _set_w11_etag(
            response,
            W11ResourceKind.AUTHORITY,
            organization_id,
            authority_id,
            record.version,
        )
        return authority_read(record)

    @application.post(
        "/api/v1/organizations/{organization_id}/execution-gates",
        response_model=ExecutionGateResponse,
    )
    async def post_execution_gate(
        organization_id: OrganizationId,
        payload: ExecutionGateRequest,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> ExecutionGateResponse:
        authorize(actor, Permission.APPROVAL_REQUEST_CREATE)
        result = create_execution_gate(
            session,
            actor,
            organization_id,
            payload,
            now=datetime.now(UTC),
        )
        if result.request is not None:
            _set_w11_etag(
                response,
                W11ResourceKind.APPROVAL_REQUEST,
                organization_id,
                result.request.request_id,
                result.request.version,
            )
        return result

    @application.get(
        "/api/v1/organizations/{organization_id}/approval-requests",
        response_model=ApprovalRequestList,
    )
    async def read_approval_requests(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> ApprovalRequestList:
        authorize(actor, Permission.APPROVAL_REQUEST_READ)
        items = tuple(request_read(item) for item in list_requests(session, actor, organization_id))
        return ApprovalRequestList(items=items, count=len(items))

    @application.get(
        "/api/v1/organizations/{organization_id}/approval-requests/{request_id}",
        response_model=ApprovalRequestRead,
    )
    async def read_approval_request(
        organization_id: OrganizationId,
        request_id: ApprovalRequestId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> ApprovalRequestRead:
        authorize(actor, Permission.APPROVAL_REQUEST_READ)
        record = get_request(session, actor, organization_id, request_id)
        _set_w11_etag(
            response,
            W11ResourceKind.APPROVAL_REQUEST,
            organization_id,
            request_id,
            record.version,
        )
        return request_read(record)

    @application.post(
        "/api/v1/organizations/{organization_id}/approval-requests/{request_id}/decisions",
        response_model=ApprovalDecisionResult,
    )
    async def post_approval_decision(
        organization_id: OrganizationId,
        request_id: ApprovalRequestId,
        payload: ApprovalDecisionCreate,
        response: Response,
        request: Request,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> ApprovalDecisionResult:
        authorize(actor, Permission.APPROVAL_REQUEST_DECIDE)
        version = expected_w11_version(
            if_match,
            kind=W11ResourceKind.APPROVAL_REQUEST,
            organization_id=organization_id,
            resource_id=request_id,
        )
        result = decide_request(
            session,
            actor,
            organization_id,
            request_id,
            version,
            payload,
            now=datetime.now(UTC),
            vault=request.app.state.grant_vault,
        )
        _set_w11_etag(
            response,
            W11ResourceKind.APPROVAL_REQUEST,
            organization_id,
            request_id,
            result.request.version,
        )
        return result

    @application.post(
        "/api/v1/organizations/{organization_id}/approval-requests/{request_id}/cancel",
        response_model=ApprovalRequestRead,
    )
    async def cancel_approval_request(
        organization_id: OrganizationId,
        request_id: ApprovalRequestId,
        payload: RequestClose,
        response: Response,
        request: Request,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> ApprovalRequestRead:
        authorize(actor, Permission.APPROVAL_REQUEST_CANCEL)
        version = expected_w11_version(
            if_match,
            kind=W11ResourceKind.APPROVAL_REQUEST,
            organization_id=organization_id,
            resource_id=request_id,
        )
        record = close_request(
            session,
            actor,
            organization_id,
            request_id,
            version,
            reason=payload.reason,
            invalidate=False,
            now=datetime.now(UTC),
            vault=request.app.state.grant_vault,
        )
        _set_w11_etag(
            response,
            W11ResourceKind.APPROVAL_REQUEST,
            organization_id,
            request_id,
            record.version,
        )
        return request_read(record)

    @application.post(
        "/api/v1/organizations/{organization_id}/approval-requests/{request_id}/invalidate",
        response_model=ApprovalRequestRead,
    )
    async def invalidate_approval_request(
        organization_id: OrganizationId,
        request_id: ApprovalRequestId,
        payload: RequestClose,
        response: Response,
        request: Request,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> ApprovalRequestRead:
        authorize(actor, Permission.APPROVAL_AUTHORITY_MANAGE)
        version = expected_w11_version(
            if_match,
            kind=W11ResourceKind.APPROVAL_REQUEST,
            organization_id=organization_id,
            resource_id=request_id,
        )
        record = close_request(
            session,
            actor,
            organization_id,
            request_id,
            version,
            reason=payload.reason,
            invalidate=True,
            now=datetime.now(UTC),
            vault=request.app.state.grant_vault,
        )
        _set_w11_etag(
            response,
            W11ResourceKind.APPROVAL_REQUEST,
            organization_id,
            request_id,
            record.version,
        )
        return request_read(record)

    @application.post(
        "/api/v1/organizations/{organization_id}/approval-requests/{request_id}/claim",
        response_model=ExecutionClaimRead,
    )
    async def claim_approval_grant(
        organization_id: OrganizationId,
        request_id: ApprovalRequestId,
        payload: GrantClaimRequest,
        request: Request,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> ExecutionClaimRead:
        authorize(actor, Permission.APPROVAL_GRANT_CLAIM)
        return claim_grant(
            session,
            actor,
            organization_id,
            request_id,
            payload,
            now=datetime.now(UTC),
            vault=request.app.state.grant_vault,
        )

    @application.get(
        "/api/v1/organizations/{organization_id}/audit-events",
        response_model=AuditEventList,
    )
    async def read_audit_events(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> AuditEventList:
        authorize(actor, Permission.AUDIT_READ)
        if actor.organization_id != organization_id:
            raise ResourceNotFound("resource_not_found")
        events, head = list_audit_events(session, organization_id)
        return AuditEventList(
            items=tuple(event_read(item) for item in events),
            count=len(events),
            head_sequence=head.head_sequence,
            head_hash=head.head_hash,
        )

    @application.post(
        "/api/v1/organizations/{organization_id}/audit-events/verify",
        response_model=AuditVerificationResult,
    )
    async def verify_audit_events(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> AuditVerificationResult:
        authorize(actor, Permission.AUDIT_VERIFY)
        if actor.organization_id != organization_id:
            raise ResourceNotFound("resource_not_found")
        result = verify_audit_chain(session, organization_id)
        if not result.valid:
            return result
        append_audit_event(
            session,
            organization_id=organization_id,
            event_type=AuditEventType.AUDIT_VERIFIED,
            actor_reference=actor.authorization_hash,
            subject_reference=organization_id,
            payload={
                "schema_version": "w11-audit-payload/1.0",
                "valid": True,
                "count": result.event_count,
            },
            now=datetime.now(UTC),
        )
        session.commit()
        return verify_audit_chain(session, organization_id)

    @application.post(
        "/api/v1/organizations/{organization_id}/production-runs",
        response_model=ProductionRunRead,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def post_production_run(
        organization_id: OrganizationId,
        payload: ProductionRunCreate,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
        idempotency_key: Annotated[IdempotencyKey, Header(alias="Idempotency-Key")],
    ) -> ProductionRunRead:
        authorize(actor, Permission.PRODUCTION_RUN_SUBMIT)
        record = admit_production_run(
            session,
            actor,
            organization_id,
            idempotency_key,
            payload,
            current_settings.production,
            now=datetime.now(UTC),
        )
        _set_resource_etag(
            response,
            ResourceKind.PRODUCTION_RUN,
            organization_id,
            record.run_id,
            record.version,
        )
        return run_read(record)

    @application.get(
        "/api/v1/organizations/{organization_id}/production-runs",
        response_model=ProductionRunList,
    )
    def read_production_runs(
        organization_id: OrganizationId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> ProductionRunList:
        authorize(actor, Permission.PRODUCTION_RUN_READ)
        items = tuple(
            run_read(record)
            for record in list_production_runs(
                session,
                actor,
                organization_id,
                current_settings.production,
                now=datetime.now(UTC),
            )
        )
        return ProductionRunList(items=items, count=len(items))

    @application.get(
        "/api/v1/organizations/{organization_id}/production-runs/{run_id}",
        response_model=ProductionRunRead,
    )
    def read_production_run(
        organization_id: OrganizationId,
        run_id: ProductionRunId,
        response: Response,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> ProductionRunRead:
        authorize(actor, Permission.PRODUCTION_RUN_READ)
        record = get_production_run(
            session,
            actor,
            organization_id,
            run_id,
            current_settings.production,
            now=datetime.now(UTC),
        )
        _set_resource_etag(
            response,
            ResourceKind.PRODUCTION_RUN,
            organization_id,
            run_id,
            record.version,
        )
        return run_read(record)

    @application.get(
        "/api/v1/organizations/{organization_id}/production-runs/{run_id}/trace",
        response_model=RunTraceExport,
    )
    def read_production_run_trace(
        organization_id: OrganizationId,
        run_id: ProductionRunId,
        session: SessionDependency,
        actor: ActorDependency,
    ) -> RunTraceExport:
        authorize(actor, Permission.OBSERVABILITY_TRACE_READ)
        record = get_production_run(
            session,
            actor,
            organization_id,
            run_id,
            current_settings.production,
            now=datetime.now(UTC),
        )
        return build_run_trace_export(session, run=run_read(record))

    @application.post(
        "/api/v1/organizations/{organization_id}/production-runs/{run_id}/claim",
        response_model=ProductionRunRead,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def claim_waiting_production_run(
        organization_id: OrganizationId,
        run_id: ProductionRunId,
        payload: ProductionRunClaim,
        response: Response,
        request: Request,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> ProductionRunRead:
        authorize(actor, Permission.PRODUCTION_RUN_MUTATE)
        version = expected_version(
            if_match,
            kind=ResourceKind.PRODUCTION_RUN,
            organization_id=organization_id,
            resource_id=run_id,
        )
        record = claim_production_run(
            session,
            actor,
            organization_id,
            run_id,
            version,
            payload,
            current_settings.production,
            now=datetime.now(UTC),
            vault=request.app.state.grant_vault,
        )
        _set_resource_etag(
            response,
            ResourceKind.PRODUCTION_RUN,
            organization_id,
            run_id,
            record.version,
        )
        return run_read(record)

    @application.post(
        "/api/v1/organizations/{organization_id}/production-runs/{run_id}/cancel",
        response_model=ProductionRunRead,
    )
    def cancel_waiting_production_run(
        organization_id: OrganizationId,
        run_id: ProductionRunId,
        response: Response,
        request: Request,
        session: SessionDependency,
        actor: ActorDependency,
        if_match: IfMatch = None,
    ) -> ProductionRunRead:
        authorize(actor, Permission.PRODUCTION_RUN_MUTATE)
        version = expected_version(
            if_match,
            kind=ResourceKind.PRODUCTION_RUN,
            organization_id=organization_id,
            resource_id=run_id,
        )
        record = cancel_production_run(
            session,
            actor,
            organization_id,
            run_id,
            version,
            current_settings.production,
            now=datetime.now(UTC),
            vault=request.app.state.grant_vault,
        )
        _set_resource_etag(
            response,
            ResourceKind.PRODUCTION_RUN,
            organization_id,
            run_id,
            record.version,
        )
        return run_read(record)

    return application


app = create_app()
