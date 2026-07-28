from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    work_email: Mapped[str] = mapped_column(String(255), unique=True)
    department: Mapped[str] = mapped_column(String(120))
    job_title: Mapped[str] = mapped_column(String(120))
    location: Mapped[str] = mapped_column(String(120))
    start_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="confirmed")
    arena_task_id: Mapped[str | None] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tickets: Mapped[list["OnboardingTicket"]] = relationship(back_populates="employee")
    account: Mapped["IamAccount | None"] = relationship(back_populates="employee")
    assets: Mapped[list["AssetAssignment"]] = relationship(back_populates="employee")
    mailbox: Mapped["Mailbox | None"] = relationship(back_populates="employee")


class OnboardingTicket(Base):
    __tablename__ = "onboarding_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), default="open")
    arena_task_id: Mapped[str | None] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped[Employee] = relationship(back_populates="tickets")


class IamAccount(Base):
    __tablename__ = "iam_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), unique=True
    )
    username: Mapped[str] = mapped_column(String(80), unique=True)
    role: Mapped[str] = mapped_column(String(32), default="employee")
    status: Mapped[str] = mapped_column(String(32), default="active")
    arena_task_id: Mapped[str | None] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped[Employee] = relationship(back_populates="account")


class AssetAssignment(Base):
    __tablename__ = "asset_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))
    asset_tag: Mapped[str] = mapped_column(String(80), unique=True)
    device_type: Mapped[str] = mapped_column(String(40), default="laptop")
    model: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default="assigned")
    arena_task_id: Mapped[str | None] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped[Employee] = relationship(back_populates="assets")


class Mailbox(Base):
    __tablename__ = "mailboxes"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), unique=True
    )
    address: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    arena_task_id: Mapped[str | None] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped[Employee] = relationship(back_populates="mailbox")


class HumanBaselineRecord(Base):
    __tablename__ = "human_baseline_records"
    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="ck_baseline_duration_nonnegative"),
        CheckConstraint("action_count >= 0", name="ck_baseline_actions_nonnegative"),
        CheckConstraint("final_score >= 0 AND final_score <= 100", name="ck_baseline_score_range"),
    )

    record_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(32), index=True)
    operator_alias: Mapped[str] = mapped_column(String(80))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    action_count: Mapped[int] = mapped_column(Integer)
    final_score: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class W8OperationReceipt(Base):
    __tablename__ = "w8_operation_receipts"
    __table_args__ = (
        CheckConstraint("length(idempotency_key) = 67", name="ck_w8_receipt_key_length"),
        CheckConstraint("length(request_hash) = 64", name="ck_w8_receipt_request_hash_length"),
        CheckConstraint("length(result_hash) = 64", name="ck_w8_receipt_result_hash_length"),
        CheckConstraint("plan_revision >= 1 AND plan_revision <= 2", name="ck_w8_revision"),
        CheckConstraint("outcome_code = 'committed'", name="ck_w8_outcome"),
    )

    task_id: Mapped[str] = mapped_column(String(40), primary_key=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(67), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    plan_revision: Mapped[int] = mapped_column(SmallInteger)
    step_id: Mapped[str] = mapped_column(String(40))
    operation: Mapped[str] = mapped_column(String(40))
    outcome_code: Mapped[str] = mapped_column(String(32), default="committed")
    result_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
