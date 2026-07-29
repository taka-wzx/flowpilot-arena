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

TemplateId = Annotated[str, StringConstraints(pattern=r"^w7-jml-(?:joiner|mover|leaver)-[0-9]{3}$")]
TaskId = Annotated[
    str, StringConstraints(pattern=r"^w7-jml-(?:joiner|mover|leaver)-[0-9]{3}-v[123]$")
]
Checksum = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Process = Literal["joiner", "mover", "leaver"]
Category = Literal["standard_joiner", "standard_mover", "standard_leaver"]
Split = Literal["development", "validation", "reporting"]
Variant = Literal["v1", "v2", "v3"]
EmployeeStatus = Literal["confirmed", "transferred", "disabled"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class JmlTemplate(StrictModel):
    schema_version: Literal["w7-jml-template/1.0"]
    template_id: TemplateId
    process: Process
    category: Category
    split: Split
    title: Annotated[str, StringConstraints(min_length=1, max_length=200)]


class CatalogDocument(StrictModel):
    schema_version: Literal["w7-jml-catalog/1.0"]
    fixture_version: Literal["w7-jml-fixture/1.0"]
    generator_version: Literal["w7-jml-variant-generator/1.0"]
    source: Literal["FlowPilot W7 original synthetic fixture"]
    license: Literal["Apache-2.0"]
    catalog_checksum: Checksum
    templates: tuple[JmlTemplate, ...] = Field(min_length=30, max_length=30)


class EmployeeFact(StrictModel):
    id: int = Field(ge=41_000, le=99_999)
    first_name: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    last_name: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    work_email: Annotated[str, StringConstraints(min_length=6, max_length=255)]
    department: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    job_title: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    location: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    start_date: date
    status: EmployeeStatus
    created_at: datetime

    @field_validator("work_email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or not value.endswith(".invalid"):
            raise ValueError("W7 JML emails must be non-deliverable .invalid values")
        return value.lower()


class TicketFact(StrictModel):
    id: int = Field(ge=700_000, le=999_999)
    employee_id: int = Field(ge=41_000, le=99_999)
    title: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    status: Literal["open", "closed"]


class AccountFact(StrictModel):
    id: int = Field(ge=700_000, le=999_999)
    employee_id: int = Field(ge=41_000, le=99_999)
    username: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9.]{2,79}$")]
    role: Literal["employee"]
    status: Literal["active", "revoked"]


class AssetFact(StrictModel):
    id: int = Field(ge=700_000, le=999_999)
    employee_id: int = Field(ge=41_000, le=99_999)
    asset_tag: Annotated[str, StringConstraints(pattern=r"^SYN-W7-[A-Z0-9-]+$", max_length=80)]
    device_type: Literal["laptop"]
    model: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    status: Literal["assigned", "released"]


class MailboxFact(StrictModel):
    id: int = Field(ge=700_000, le=999_999)
    employee_id: int = Field(ge=41_000, le=99_999)
    address: Annotated[str, StringConstraints(min_length=6, max_length=255)]
    status: Literal["active", "disabled"]

    @field_validator("address")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or not value.endswith(".invalid"):
            raise ValueError("W7 JML mailboxes must be non-deliverable .invalid values")
        return value.lower()


class FactBundle(StrictModel):
    target: EmployeeFact
    decoy: EmployeeFact
    ticket: TicketFact | None
    account: AccountFact | None
    asset: AssetFact | None
    mailbox: MailboxFact | None


class JoinerValues(StrictModel):
    process: Literal["joiner"] = "joiner"
    employee_id: int
    ticket_title: str
    username: str
    asset_tag: str
    laptop_model: str
    mailbox: str


class MoverValues(StrictModel):
    process: Literal["mover"] = "mover"
    employee_id: int
    new_department: str
    new_job_title: str
    new_location: str


class LeaverValues(StrictModel):
    process: Literal["leaver"] = "leaver"
    employee_id: int


SuppliedValues = Annotated[
    JoinerValues | MoverValues | LeaverValues, Field(discriminator="process")
]


class JmlInstance(StrictModel):
    schema_version: Literal["w7-jml-instance/1.0"]
    task_id: TaskId
    template_id: TemplateId
    variant: Variant
    process: Process
    category: Category
    split: Split
    fixture_version: Literal["w7-jml-fixture/1.0"]
    generator_version: Literal["w7-jml-variant-generator/1.0"]
    human_brief: Annotated[str, StringConstraints(min_length=1, max_length=1_000)]
    supplied_values: SuppliedValues
    initial_state: FactBundle
    expected_state: FactBundle
    canonical_checksum: Checksum

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        if self.task_id != f"{self.template_id}-{self.variant}":
            raise ValueError("task ID must derive from template and variant")
        if self.supplied_values.process != self.process:
            raise ValueError("supplied values must match process")
        if self.category != f"standard_{self.process}":
            raise ValueError("category must match process")
        if self.initial_state.target.id != self.expected_state.target.id:
            raise ValueError("target identity must remain stable")
        if self.initial_state.decoy != self.expected_state.decoy:
            raise ValueError("decoy state must remain unchanged")
        initial_downstream = (
            self.initial_state.ticket,
            self.initial_state.account,
            self.initial_state.asset,
            self.initial_state.mailbox,
        )
        expected_downstream = (
            self.expected_state.ticket,
            self.expected_state.account,
            self.expected_state.asset,
            self.expected_state.mailbox,
        )
        if self.process == "joiner" and (any(initial_downstream) or not all(expected_downstream)):
            raise ValueError("joiner state contract is invalid")
        if self.process != "joiner" and (
            not all(initial_downstream) or not all(expected_downstream)
        ):
            raise ValueError("mover/leaver state contract is invalid")
        return self


class CatalogEntry(StrictModel):
    task_id: TaskId
    template_id: TemplateId
    variant: Variant
    process: Process
    split: Split
    fixture_version: Literal["w7-jml-fixture/1.0"]
    canonical_checksum: Checksum


class CatalogSummary(StrictModel):
    schema_version: Literal["w7-jml-catalog-summary/1.0"] = "w7-jml-catalog-summary/1.0"
    template_count: Literal[30]
    instance_count: Literal[90]
    joiner_templates: Literal[12]
    mover_templates: Literal[8]
    leaver_templates: Literal[10]
    development_templates: Literal[18]
    validation_templates: Literal[6]
    reporting_templates: Literal[6]
    catalog_checksum: Checksum
    split_manifest_checksum: Checksum
    reporting_manifest_checksum: Checksum


class FactCounts(StrictModel):
    employees: int = Field(ge=0)
    tickets: int = Field(ge=0)
    iam_accounts: int = Field(ge=0)
    assets: int = Field(ge=0)
    mailboxes: int = Field(ge=0)


class ResetSeedResult(StrictModel):
    schema_version: Literal["w7-jml-reset-seed/1.0"] = "w7-jml-reset-seed/1.0"
    task_id: TaskId
    fixture_version: Literal["w7-jml-fixture/1.0"]
    instance_checksum: Checksum
    fact_checksum: Checksum
    counts: FactCounts


PredicateKind = Literal[
    "employee_matches", "ticket_matches", "account_matches", "asset_matches", "mailbox_matches"
]


class PredicateResult(StrictModel):
    kind: PredicateKind
    weight: Literal[20]
    passed: bool
    awarded_points: Literal[0, 20]
    fact: Annotated[str, StringConstraints(min_length=1, max_length=200)]


class GradeResult(StrictModel):
    schema_version: Literal["w7-jml-grade/1.0"] = "w7-jml-grade/1.0"
    task_id: TaskId
    instance_checksum: Checksum
    total_score: int = Field(ge=0, le=100)
    passed: bool
    predicates: tuple[
        PredicateResult, PredicateResult, PredicateResult, PredicateResult, PredicateResult
    ]


class EmptyRequest(StrictModel):
    pass
