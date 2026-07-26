from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.router import router as arena_router
from flowpilot_sandbox_api.database import get_session
from flowpilot_sandbox_api.models import (
    AssetAssignment,
    Employee,
    IamAccount,
    Mailbox,
    OnboardingTicket,
)
from flowpilot_sandbox_api.schemas import (
    AccountCreate,
    AccountRead,
    AssetCreate,
    AssetRead,
    EmployeeCreate,
    EmployeeRead,
    MailboxCreate,
    MailboxRead,
    TicketCreate,
    TicketRead,
)

SessionDependency = Annotated[Session, Depends(get_session)]


def run_migrations() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    run_migrations()
    yield


app = FastAPI(
    title="FlowPilot Synthetic Sandbox API",
    version="0.1.0",
    lifespan=lifespan,
)


def persist[ModelT](session: Session, record: ModelT, duplicate_message: str) -> ModelT:
    session.add(record)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=duplicate_message) from exc
    session.refresh(record)
    return record


def require_employee(session: Session, employee_id: int) -> Employee:
    employee = session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "sandbox-api", "version": "0.1.0"}


@app.get("/api/hris/employees", response_model=list[EmployeeRead])
def list_employees(session: SessionDependency) -> list[Employee]:
    return list(session.scalars(select(Employee).order_by(Employee.id)))


@app.post(
    "/api/hris/employees",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(payload: EmployeeCreate, session: SessionDependency) -> Employee:
    return persist(session, Employee(**payload.model_dump()), "Synthetic work email already exists")


@app.get("/api/itsm/tickets", response_model=list[TicketRead])
def list_tickets(session: SessionDependency) -> list[OnboardingTicket]:
    return list(session.scalars(select(OnboardingTicket).order_by(OnboardingTicket.id)))


@app.post(
    "/api/itsm/tickets",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(payload: TicketCreate, session: SessionDependency) -> OnboardingTicket:
    employee = require_employee(session, payload.employee_id)
    return persist(
        session,
        OnboardingTicket(**payload.model_dump(), arena_task_id=employee.arena_task_id),
        "Ticket already exists",
    )


@app.get("/api/iam/accounts", response_model=list[AccountRead])
def list_accounts(session: SessionDependency) -> list[IamAccount]:
    return list(session.scalars(select(IamAccount).order_by(IamAccount.id)))


@app.post(
    "/api/iam/accounts",
    response_model=AccountRead,
    status_code=status.HTTP_201_CREATED,
)
def create_account(payload: AccountCreate, session: SessionDependency) -> IamAccount:
    employee = require_employee(session, payload.employee_id)
    return persist(
        session,
        IamAccount(**payload.model_dump(), arena_task_id=employee.arena_task_id),
        "Employee or username already has an account",
    )


@app.get("/api/assets/devices", response_model=list[AssetRead])
def list_assets(session: SessionDependency) -> list[AssetAssignment]:
    return list(session.scalars(select(AssetAssignment).order_by(AssetAssignment.id)))


@app.post(
    "/api/assets/devices",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
)
def create_asset(payload: AssetCreate, session: SessionDependency) -> AssetAssignment:
    employee = require_employee(session, payload.employee_id)
    return persist(
        session,
        AssetAssignment(**payload.model_dump(), arena_task_id=employee.arena_task_id),
        "Synthetic asset tag already exists",
    )


@app.get("/api/mail/mailboxes", response_model=list[MailboxRead])
def list_mailboxes(session: SessionDependency) -> list[Mailbox]:
    return list(session.scalars(select(Mailbox).order_by(Mailbox.id)))


@app.post(
    "/api/mail/mailboxes",
    response_model=MailboxRead,
    status_code=status.HTTP_201_CREATED,
)
def create_mailbox(payload: MailboxCreate, session: SessionDependency) -> Mailbox:
    employee = require_employee(session, payload.employee_id)
    return persist(
        session,
        Mailbox(**payload.model_dump(), arena_task_id=employee.arena_task_id),
        "Employee or address already has a mailbox",
    )


app.include_router(arena_router)
