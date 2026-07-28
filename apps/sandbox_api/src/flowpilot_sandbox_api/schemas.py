from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

SyntheticEmail = Annotated[str, StringConstraints(min_length=6, max_length=255)]
SyntheticAssetTag = Annotated[str, StringConstraints(pattern=r"^SYN-[A-Z0-9-]+$", max_length=80)]


class EmployeeCreate(BaseModel):
    first_name: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    last_name: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    work_email: SyntheticEmail
    department: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    job_title: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    location: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    start_date: date
    status: Literal["confirmed"] = "confirmed"

    @field_validator("work_email")
    @classmethod
    def require_synthetic_email(cls, value: str) -> str:
        if not value.lower().endswith(".invalid") or "@" not in value:
            raise ValueError("W2 accepts only synthetic .invalid email addresses")
        return value.lower()


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    work_email: str
    department: str
    job_title: str
    location: str
    start_date: date
    status: Literal["confirmed", "transferred", "disabled"]
    arena_task_id: str | None
    created_at: datetime


class TicketCreate(BaseModel):
    employee_id: int = Field(gt=0)
    title: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    status: Literal["open"] = "open"


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    title: str
    status: Literal["open", "closed"]
    arena_task_id: str | None
    created_at: datetime


class AccountCreate(BaseModel):
    employee_id: int = Field(gt=0)
    username: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9.]{2,79}$")]
    role: Literal["employee"] = "employee"
    status: Literal["active"] = "active"


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    username: str
    role: Literal["employee"]
    status: Literal["active", "revoked"]
    arena_task_id: str | None
    created_at: datetime


class AssetCreate(BaseModel):
    employee_id: int = Field(gt=0)
    asset_tag: SyntheticAssetTag
    device_type: Literal["laptop"] = "laptop"
    model: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    status: Literal["assigned"] = "assigned"


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    asset_tag: str
    device_type: Literal["laptop"]
    model: str
    status: Literal["assigned", "released"]
    arena_task_id: str | None
    created_at: datetime


class MailboxCreate(BaseModel):
    employee_id: int = Field(gt=0)
    address: SyntheticEmail
    status: Literal["active"] = "active"

    @field_validator("address")
    @classmethod
    def require_synthetic_email(cls, value: str) -> str:
        if not value.lower().endswith(".invalid") or "@" not in value:
            raise ValueError("W2 accepts only synthetic .invalid email addresses")
        return value.lower()


class MailboxRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    address: str
    status: Literal["active", "disabled"]
    arena_task_id: str | None
    created_at: datetime


class W7StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EmployeeTransfer(W7StrictModel):
    department: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    job_title: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    location: Annotated[str, StringConstraints(min_length=1, max_length=120)]


class EmployeeDisable(W7StrictModel):
    pass


class TicketClose(W7StrictModel):
    pass


class AccountRevoke(W7StrictModel):
    pass


class AssetRelease(W7StrictModel):
    pass


class MailboxDisable(W7StrictModel):
    pass


W8Operation = Literal[
    "create_ticket",
    "create_account",
    "assign_asset",
    "create_mailbox",
    "transfer_employee",
    "disable_employee",
    "close_ticket",
    "revoke_account",
    "release_asset",
    "disable_mailbox",
]


class W8IdempotencyMetadata(W7StrictModel):
    task_id: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    idempotency_key: Annotated[str, StringConstraints(pattern=r"^op_[0-9a-f]{64}$")]
    request_hash: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    plan_revision: int = Field(ge=1, le=2)
    step_id: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,39}$")]
    operation: W8Operation


class W8ReceiptResult(W7StrictModel):
    schema_version: Literal["w8-receipt-result/1.0"] = "w8-receipt-result/1.0"
    state: Literal["created", "replayed", "mismatch"]
    result_hash: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")] | None = None

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if (self.state == "mismatch") == (self.result_hash is not None):
            raise ValueError("receipt result fields are inconsistent")
        return self
