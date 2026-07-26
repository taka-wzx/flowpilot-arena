from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

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


class EmployeeRead(EmployeeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class TicketCreate(BaseModel):
    employee_id: int = Field(gt=0)
    title: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    status: Literal["open"] = "open"


class TicketRead(TicketCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class AccountCreate(BaseModel):
    employee_id: int = Field(gt=0)
    username: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9.]{2,79}$")]
    role: Literal["employee"] = "employee"
    status: Literal["active"] = "active"


class AccountRead(AccountCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class AssetCreate(BaseModel):
    employee_id: int = Field(gt=0)
    asset_tag: SyntheticAssetTag
    device_type: Literal["laptop"] = "laptop"
    model: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    status: Literal["assigned"] = "assigned"


class AssetRead(AssetCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
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


class MailboxRead(MailboxCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
