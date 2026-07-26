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

TaskId = Annotated[str, StringConstraints(pattern=r"^w3-joiner-0(?:0[1-9]|10)$")]
Checksum = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
SyntheticEmail = Annotated[str, StringConstraints(min_length=6, max_length=255)]
NonEmpty80 = Annotated[str, StringConstraints(min_length=1, max_length=80)]
NonEmpty120 = Annotated[str, StringConstraints(min_length=1, max_length=120)]
NonEmpty200 = Annotated[str, StringConstraints(min_length=1, max_length=200)]
Username = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9.]{2,79}$")]
AssetTag = Annotated[str, StringConstraints(pattern=r"^SYN-W3-[0-9]{3}-[A-Z0-9-]+$", max_length=80)]

TaskSplit = Literal["development", "validation", "reporting"]
PredicateKind = Literal[
    "employee_matches",
    "ticket_exactly_one_linked",
    "iam_exactly_one_linked",
    "iam_no_elevated_role",
    "asset_exactly_one_linked",
    "mailbox_exactly_one_linked",
    "no_wrong_associations",
    "no_duplicate_business_records",
]

REQUIRED_PREDICATE_KINDS: tuple[PredicateKind, ...] = (
    "employee_matches",
    "ticket_exactly_one_linked",
    "iam_exactly_one_linked",
    "iam_no_elevated_role",
    "asset_exactly_one_linked",
    "mailbox_exactly_one_linked",
    "no_wrong_associations",
    "no_duplicate_business_records",
)


def _synthetic_email(value: str) -> str:
    normalized = value.lower()
    if "@" not in normalized or not normalized.endswith(".invalid"):
        raise ValueError("Arena task emails must use the non-deliverable .invalid domain")
    return normalized


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class SyntheticActor(StrictModel):
    alias: Annotated[str, StringConstraints(pattern=r"^synthetic-operator-[0-9]{3}$")]
    role: NonEmpty120


class FixtureReference(StrictModel):
    fixture_id: Annotated[str, StringConstraints(pattern=r"^w3-joiner-0(?:0[1-9]|10)-fixture$")]
    fixture_version: Literal["w3-fixture-v1"]
    source: Literal["FlowPilot W3 original synthetic fixture"]
    license: Literal["Apache-2.0"]


class EmployeeSeed(StrictModel):
    kind: Literal["target", "decoy"]
    id: int = Field(ge=31001, le=31910)
    first_name: NonEmpty80
    last_name: NonEmpty80
    work_email: SyntheticEmail
    department: NonEmpty120
    job_title: NonEmpty120
    location: NonEmpty120
    start_date: date
    status: Literal["confirmed"]
    created_at: datetime

    _validate_email = field_validator("work_email")(_synthetic_email)

    @field_validator("created_at")
    @classmethod
    def require_fixed_utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Seed timestamps must include a UTC offset")
        if value.microsecond != 0:
            raise ValueError("Seed timestamps must use whole seconds")
        return value


class InitialState(StrictModel):
    employees: tuple[EmployeeSeed, EmployeeSeed]


class ExpectedEmployee(StrictModel):
    id: int = Field(ge=31001, le=31010)
    first_name: NonEmpty80
    last_name: NonEmpty80
    work_email: SyntheticEmail
    department: NonEmpty120
    job_title: NonEmpty120
    location: NonEmpty120
    start_date: date
    status: Literal["confirmed"]

    _validate_email = field_validator("work_email")(_synthetic_email)


class ExpectedTicket(StrictModel):
    title: NonEmpty200
    status: Literal["open"]


class ExpectedAccount(StrictModel):
    username: Username
    role: Literal["employee"]
    status: Literal["active"]


class ExpectedAsset(StrictModel):
    asset_tag: AssetTag
    device_type: Literal["laptop"]
    model: NonEmpty120
    status: Literal["assigned"]


class ExpectedMailbox(StrictModel):
    address: SyntheticEmail
    status: Literal["active"]

    _validate_email = field_validator("address")(_synthetic_email)


class ExpectedFinalState(StrictModel):
    employee: ExpectedEmployee
    ticket: ExpectedTicket
    iam_account: ExpectedAccount
    asset: ExpectedAsset
    mailbox: ExpectedMailbox


class GraderPredicate(StrictModel):
    predicate_id: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{2,79}$")]
    kind: PredicateKind
    weight: int = Field(gt=0, le=100)


class TaskSpec(StrictModel):
    task_id: TaskId
    schema_version: Literal["1.0"]
    title: NonEmpty200
    business_process: Literal["joiner"]
    synthetic_actor: SyntheticActor
    instructions: tuple[Annotated[str, StringConstraints(min_length=1, max_length=300)], ...] = (
        Field(min_length=1, max_length=6)
    )
    split: TaskSplit
    fixture: FixtureReference
    initial_state: InitialState
    expected_final_state: ExpectedFinalState
    grader_predicates: tuple[GraderPredicate, ...] = Field(min_length=1)
    canonical_checksum: Checksum

    @model_validator(mode="after")
    def validate_internal_references(self) -> Self:
        number = int(self.task_id.rsplit("-", maxsplit=1)[1])
        expected_split: TaskSplit
        if number <= 6:
            expected_split = "development"
        elif number <= 8:
            expected_split = "validation"
        else:
            expected_split = "reporting"
        if self.split != expected_split:
            raise ValueError(f"{self.task_id} must use split {expected_split}")
        if self.fixture.fixture_id != f"{self.task_id}-fixture":
            raise ValueError("fixture_id must be derived from task_id")

        employees_by_kind = {employee.kind: employee for employee in self.initial_state.employees}
        if set(employees_by_kind) != {"target", "decoy"}:
            raise ValueError("initial_state must contain exactly one target and one decoy employee")
        if len({employee.id for employee in self.initial_state.employees}) != 2:
            raise ValueError("initial employee IDs must be unique")
        if len({employee.work_email for employee in self.initial_state.employees}) != 2:
            raise ValueError("initial employee emails must be unique")

        target = employees_by_kind["target"]
        target_facts = target.model_dump(exclude={"kind", "created_at"})
        if self.expected_final_state.employee.model_dump() != target_facts:
            raise ValueError("expected employee must exactly reference the target seed employee")
        if self.expected_final_state.mailbox.address != target.work_email:
            raise ValueError("expected mailbox address must equal the target synthetic email")
        expected_asset_prefix = f"SYN-W3-{number:03d}-"
        if not self.expected_final_state.asset.asset_tag.startswith(expected_asset_prefix):
            raise ValueError("asset tag must use the task-specific synthetic namespace")

        predicate_ids = [item.predicate_id for item in self.grader_predicates]
        if len(predicate_ids) != len(set(predicate_ids)):
            raise ValueError("predicate IDs must be unique within a task")
        predicate_kinds = tuple(item.kind for item in self.grader_predicates)
        if predicate_kinds != REQUIRED_PREDICATE_KINDS:
            raise ValueError("grader predicates must use the frozen ordered W3 predicate set")
        if sum(item.weight for item in self.grader_predicates) != 100:
            raise ValueError("grader predicate weights must total 100")

        prohibited = ("playwright", "selector", "screenshot", "dom tree", "model parameter")
        prose = " ".join((self.title, *self.instructions)).lower()
        if any(token in prose for token in prohibited):
            raise ValueError("Task prose must not embed browser, visual, or model instructions")
        return self


class TaskCatalogEntry(StrictModel):
    task_id: TaskId
    schema_version: Literal["1.0"]
    title: str
    business_process: Literal["joiner"]
    split: TaskSplit
    fixture_version: Literal["w3-fixture-v1"]
    canonical_checksum: Checksum


class FactCounts(StrictModel):
    employees: int = Field(ge=0)
    tickets: int = Field(ge=0)
    iam_accounts: int = Field(ge=0)
    assets: int = Field(ge=0)
    mailboxes: int = Field(ge=0)


class SeedSummary(StrictModel):
    employee_ids: tuple[int, ...]
    employee_emails: tuple[str, ...]
    counts: FactCounts
    fact_checksum: Checksum


class ResetSeedResult(StrictModel):
    task_id: TaskId
    fixture_version: Literal["w3-fixture-v1"]
    spec_checksum: Checksum
    seed_summary: SeedSummary


class EmptyArenaRequest(StrictModel):
    pass


class PredicateResult(StrictModel):
    predicate_id: str
    kind: PredicateKind
    weight: int
    passed: bool
    awarded_points: int
    fact: str


class GradeResult(StrictModel):
    task_id: TaskId
    spec_checksum: Checksum
    total_score: int = Field(ge=0, le=100)
    passed: bool
    predicates: tuple[PredicateResult, ...]


class ManualBaselineCreate(StrictModel):
    record_id: Annotated[str, StringConstraints(pattern=r"^baseline-w3-[a-z0-9-]{3,60}$")]
    task_id: TaskId
    operator_alias: Annotated[str, StringConstraints(pattern=r"^anon-[a-z0-9-]{2,60}$")]
    started_at: datetime
    ended_at: datetime
    action_count: int = Field(ge=0, le=10000)
    notes: Annotated[str, StringConstraints(max_length=500)] | None = None

    @field_validator("started_at", "ended_at", mode="before")
    @classmethod
    def parse_json_timestamp(cls, value: object) -> object:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("Baseline timestamps must use ISO 8601") from exc
        return value

    @model_validator(mode="after")
    def validate_times(self) -> Self:
        for timestamp in (self.started_at, self.ended_at):
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("Baseline timestamps must include an offset")
            if timestamp.microsecond != 0:
                raise ValueError("Baseline timestamps must use whole seconds")
        if self.ended_at < self.started_at:
            raise ValueError("Baseline end must not precede start")
        return self


class ManualBaselineRead(ManualBaselineCreate):
    model_config = ConfigDict(extra="forbid", from_attributes=True, frozen=True, strict=True)

    duration_seconds: int = Field(ge=0)
    final_score: int = Field(ge=0, le=100)
    created_at: datetime
