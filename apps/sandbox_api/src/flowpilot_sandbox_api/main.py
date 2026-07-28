from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.jml.router import router as jml_router
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
    AccountRevoke,
    AssetCreate,
    AssetRead,
    AssetRelease,
    EmployeeCreate,
    EmployeeDisable,
    EmployeeRead,
    EmployeeTransfer,
    MailboxCreate,
    MailboxDisable,
    MailboxRead,
    TicketClose,
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


def require_single[ModelT](records: list[ModelT], missing_message: str) -> ModelT:
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=missing_message)
    if len(records) != 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Synthetic transition requires exactly one employee-owned record",
        )
    return records[0]


def commit_transition[ModelT](session: Session, record: ModelT) -> ModelT:
    session.commit()
    session.refresh(record)
    return record


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


@app.patch("/api/hris/employees/{employee_id}/transfer", response_model=EmployeeRead)
def transfer_employee(
    employee_id: int,
    payload: EmployeeTransfer,
    session: SessionDependency,
) -> Employee:
    employee = require_employee(session, employee_id)
    if employee.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee transfer requires confirmed state",
        )
    employee.department = payload.department
    employee.job_title = payload.job_title
    employee.location = payload.location
    employee.status = "transferred"
    return commit_transition(session, employee)


@app.patch("/api/hris/employees/{employee_id}/disable", response_model=EmployeeRead)
def disable_employee(
    employee_id: int,
    _payload: EmployeeDisable,
    session: SessionDependency,
) -> Employee:
    employee = require_employee(session, employee_id)
    if employee.status not in {"confirmed", "transferred"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee disable requires confirmed or transferred state",
        )
    employee.status = "disabled"
    return commit_transition(session, employee)


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


@app.patch("/api/itsm/employees/{employee_id}/close", response_model=TicketRead)
def close_ticket(
    employee_id: int,
    _payload: TicketClose,
    session: SessionDependency,
) -> OnboardingTicket:
    record = require_single(
        list(
            session.scalars(
                select(OnboardingTicket).where(OnboardingTicket.employee_id == employee_id)
            )
        ),
        "Employee-owned ticket not found",
    )
    if record.status != "open":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket is not open")
    record.status = "closed"
    return commit_transition(session, record)


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


@app.patch("/api/iam/employees/{employee_id}/revoke", response_model=AccountRead)
def revoke_account(
    employee_id: int,
    _payload: AccountRevoke,
    session: SessionDependency,
) -> IamAccount:
    record = require_single(
        list(session.scalars(select(IamAccount).where(IamAccount.employee_id == employee_id))),
        "Employee-owned account not found",
    )
    if record.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account is not active")
    record.status = "revoked"
    return commit_transition(session, record)


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


@app.patch("/api/assets/employees/{employee_id}/release", response_model=AssetRead)
def release_asset(
    employee_id: int,
    _payload: AssetRelease,
    session: SessionDependency,
) -> AssetAssignment:
    record = require_single(
        list(
            session.scalars(
                select(AssetAssignment).where(AssetAssignment.employee_id == employee_id)
            )
        ),
        "Employee-owned asset not found",
    )
    if record.status != "assigned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset is not assigned")
    record.status = "released"
    return commit_transition(session, record)


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


@app.patch("/api/mail/employees/{employee_id}/disable", response_model=MailboxRead)
def disable_mailbox(
    employee_id: int,
    _payload: MailboxDisable,
    session: SessionDependency,
) -> Mailbox:
    record = require_single(
        list(session.scalars(select(Mailbox).where(Mailbox.employee_id == employee_id))),
        "Employee-owned mailbox not found",
    )
    if record.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mailbox is not active")
    record.status = "disabled"
    return commit_transition(session, record)


app.include_router(arena_router)
app.include_router(jml_router)
