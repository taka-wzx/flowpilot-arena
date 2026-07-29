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
from flowpilot_control_api.schemas import (
    ActiveStatus,
    ActorContext,
    AuthorizedContextProjection,
    CountResponse,
    CurrentIdentityResponse,
    ErrorCode,
    ErrorResponse,
    HealthResponse,
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
    ResourceKind,
    Role,
    UserCreate,
    UserId,
    UserList,
    UserRead,
    UserUpdate,
)
from flowpilot_control_api.seed import seed_synthetic_identities

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
        active_verifier = verifier or OidcVerifier(
            current_settings.oidc,
            HttpJwksSource(current_settings.oidc),
        )
        app.state.oidc_verifier = active_verifier
        yield
        await active_verifier.close()

    application = FastAPI(
        title="FlowPilot W10 Control API",
        version="0.10.0",
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
        allow_headers=["Authorization", "Content-Type", "If-Match"],
        expose_headers=["ETag"],
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
        return resolve_actor(session, verified)

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

    return application


app = create_app()
