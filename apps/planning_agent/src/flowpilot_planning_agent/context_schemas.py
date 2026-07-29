import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from flowpilot_planning_agent.schemas import (
    BusinessProcess,
    Checksum,
    PlanningRunRequest,
    PlanningRunResult,
    RunId,
    StrictModel,
    TaskId,
    TotalBudget,
    TotalUsage,
)

ScopeId = Annotated[
    str,
    StringConstraints(pattern=r"^syn_scope_[a-z0-9_]{3,48}$", max_length=58),
]
SafeId = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9_.:-]{1,79}$", max_length=80),
]
SafeValue = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9][a-z0-9_.:-]{0,119}$", max_length=120),
]

ContextLayer = Literal[
    "task_facts",
    "browser_working",
    "short_term",
    "org_memory",
    "enterprise_knowledge",
]
TaskPhase = Literal["planning", "executing", "recovering", "verifying"]
TrustLevel = Literal[
    "authoritative",
    "runtime_observed",
    "task_supplied",
    "organization_curated",
    "enterprise_curated",
]
SourceKind = Literal[
    "sandbox_database",
    "browser_worker",
    "task_session",
    "organization_memory",
    "enterprise_catalog",
]
FactCategory = Literal[
    "task_process",
    "employee_state",
    "ticket_state",
    "account_state",
    "asset_state",
    "mailbox_state",
]
BrowserCategory = Literal[
    "current_page",
    "recent_action",
    "local_failure",
    "pending_step",
]
SummaryEventKind = Literal[
    "unresolved_issue",
    "recent_action",
    "failure_reason",
    "pending_step",
    "user_supplement",
]
MemoryField = Literal[
    "department",
    "role",
    "location",
    "device_preference",
    "approval_chain",
]
KnowledgeCategory = Literal[
    "joiner_policy",
    "mover_policy",
    "leaver_policy",
    "permission_matrix",
    "device_standard",
    "operating_manual",
]
ContextCategory = (
    FactCategory | BrowserCategory | SummaryEventKind | MemoryField | KnowledgeCategory
)
AblationProfile = Literal[
    "full_five_layer",
    "task_facts_only",
    "no_short_term",
    "no_enterprise_retrieval",
    "no_organization_memory",
]
MemoryAction = Literal["upsert", "delete"]
MemoryStatus = Literal["active", "tombstone"]

TRUST_RANK: dict[TrustLevel, int] = {
    "authoritative": 5,
    "runtime_observed": 4,
    "task_supplied": 3,
    "organization_curated": 2,
    "enterprise_curated": 1,
}


def _jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def canonical_json_bytes(value: BaseModel | dict[str, object]) -> bytes:
    data = _jsonable(value)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def content_hash(value: str) -> str:
    return sha256_hex(value.encode())


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("timestamp must be UTC")
    return value


def parse_utc(value: object) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be ISO-8601 UTC") from exc
    if not isinstance(value, datetime):
        raise ValueError("timestamp must be datetime")
    return require_utc(value)


def parse_optional_utc(value: object) -> datetime | None:
    return None if value is None else parse_utc(value)


class TaskFactInput(StrictModel):
    item_id: SafeId
    task_id: TaskId
    scope_id: ScopeId
    category: FactCategory
    safe_value: SafeValue
    source: Literal["sandbox_database"] = "sandbox_database"
    trust: Literal["authoritative"] = "authoritative"
    snapshot_version: int = Field(ge=1, le=1_000_000)


class BrowserWorkingInput(StrictModel):
    item_id: SafeId
    task_id: TaskId
    scope_id: ScopeId
    category: BrowserCategory
    safe_value: SafeValue
    source: Literal["browser_worker"] = "browser_worker"
    trust: Literal["runtime_observed"] = "runtime_observed"
    observation_hash: Checksum
    ordinal: int = Field(ge=1, le=1_000_000)
    observed_at: datetime
    expires_at: datetime

    @field_validator("observed_at", "expires_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime:
        return parse_utc(value)

    @model_validator(mode="after")
    def expiry_follows_observation(self) -> Self:
        if self.expires_at <= self.observed_at:
            raise ValueError("browser working memory expiry must follow observation")
        return self


class ShortTermEvent(StrictModel):
    event_id: SafeId
    task_id: TaskId
    scope_id: ScopeId
    kind: SummaryEventKind
    safe_value: SafeValue
    source: Literal["task_session"] = "task_session"
    trust: Literal["task_supplied"] = "task_supplied"
    source_hash: Checksum
    ordinal: int = Field(ge=1, le=1_000_000)


class SummaryEntry(StrictModel):
    kind: SummaryEventKind
    safe_value: SafeValue
    source_hash: Checksum
    ordinal: int = Field(ge=1, le=1_000_000)


class ShortTermSummary(StrictModel):
    schema_version: Literal["w9-short-term-summary/1.0"] = "w9-short-term-summary/1.0"
    task_id: TaskId
    scope_id: ScopeId
    entries: tuple[SummaryEntry, ...] = Field(max_length=8)
    source_hashes: tuple[Checksum, ...] = Field(max_length=12)
    input_count: int = Field(ge=0, le=12)
    deduplicated_count: int = Field(ge=0, le=12)
    emitted_count: int = Field(ge=0, le=8)
    dropped_count: int = Field(ge=0, le=12)
    canonical_bytes: int = Field(ge=0, le=4_096)
    estimated_tokens: int = Field(ge=0, le=1_024)
    summary_hash: Checksum

    @field_validator("entries", "source_hashes", mode="before")
    @classmethod
    def accept_json_arrays(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_hash(self) -> Self:
        fields = self.model_dump(mode="json", exclude={"summary_hash"})
        if sha256_hex(canonical_json_bytes(fields)) != self.summary_hash:
            raise ValueError("summary hash mismatch")
        return self


class MemoryMutation(StrictModel):
    action: MemoryAction
    memory_id: SafeId
    field: MemoryField | None = None
    safe_value: SafeValue | None = None
    source: Literal["organization_memory"] = "organization_memory"
    trust: Literal["organization_curated"] = "organization_curated"
    valid_from: datetime | None = None
    expires_at: datetime | None = None

    @field_validator("valid_from", "expires_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime | None:
        return parse_optional_utc(value)

    @model_validator(mode="after")
    def validate_action_fields(self) -> Self:
        if self.action == "upsert":
            if self.field is None or self.safe_value is None or self.valid_from is None:
                raise ValueError("memory upsert requires field, value, and validity")
            if self.expires_at is not None and self.expires_at <= self.valid_from:
                raise ValueError("memory expiry must follow validity start")
        elif any(
            value is not None
            for value in (self.field, self.safe_value, self.valid_from, self.expires_at)
        ):
            raise ValueError("memory delete accepts only memory_id")
        return self


class OrganizationMemoryRecord(StrictModel):
    schema_version: Literal["w9-organization-memory/1.0"] = "w9-organization-memory/1.0"
    memory_id: SafeId
    scope_id: ScopeId
    owner_task_id: TaskId
    field: MemoryField
    safe_value: SafeValue
    source: Literal["organization_memory"] = "organization_memory"
    trust: Literal["organization_curated"] = "organization_curated"
    version: int = Field(ge=1, le=1_000_000)
    status: MemoryStatus
    valid_from: datetime
    expires_at: datetime | None = None
    content_hash: Checksum

    @field_validator("valid_from", "expires_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime | None:
        return parse_optional_utc(value)

    @model_validator(mode="after")
    def validate_hash(self) -> Self:
        hash_value = (
            self.safe_value
            if self.status == "active"
            else f"tombstone.{self.memory_id}.{self.version}"
        )
        if content_hash(hash_value) != self.content_hash:
            raise ValueError("organization memory content hash mismatch")
        return self


class EnterpriseKnowledgeRecord(StrictModel):
    schema_version: Literal["w9-enterprise-knowledge/1.0"] = "w9-enterprise-knowledge/1.0"
    knowledge_id: SafeId
    scope_id: ScopeId
    category: KnowledgeCategory
    safe_value: SafeValue
    keywords: tuple[SafeValue, ...] = Field(min_length=1, max_length=8)
    source_id: SafeId
    source: Literal["enterprise_catalog"] = "enterprise_catalog"
    trust: Literal["enterprise_curated"] = "enterprise_curated"
    version: int = Field(ge=1, le=1_000_000)
    valid_from: datetime
    expires_at: datetime | None = None
    content_hash: Checksum

    @field_validator("keywords", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("valid_from", "expires_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime | None:
        return parse_optional_utc(value)

    @model_validator(mode="after")
    def validate_hash(self) -> Self:
        if content_hash(self.safe_value) != self.content_hash:
            raise ValueError("enterprise knowledge content hash mismatch")
        return self


class RetrievalMatch(StrictModel):
    record: EnterpriseKnowledgeRecord
    lexical_score: int = Field(ge=1, le=8)


class RetrievalResult(StrictModel):
    schema_version: Literal["w9-retrieval-result/1.0"] = "w9-retrieval-result/1.0"
    category: KnowledgeCategory
    catalog_checksum: Checksum
    candidate_count: int = Field(ge=0, le=6)
    selected: tuple[RetrievalMatch, ...] = Field(max_length=3)

    @field_validator("selected", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class ContextItem(StrictModel):
    layer: ContextLayer
    item_id: SafeId
    category: ContextCategory
    safe_value: SafeValue
    source_id: SafeId
    source: SourceKind
    trust: TrustLevel
    version: int = Field(ge=1, le=1_000_000)
    valid_from: datetime
    expires_at: datetime | None = None
    content_hash: Checksum
    canonical_bytes: int = Field(ge=1, le=4_096)
    estimated_tokens: int = Field(ge=1, le=1_024)

    @field_validator("valid_from", "expires_at", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime | None:
        return parse_optional_utc(value)

    @model_validator(mode="after")
    def validate_provenance_and_hash(self) -> Self:
        expected: dict[ContextLayer, tuple[SourceKind, TrustLevel]] = {
            "task_facts": ("sandbox_database", "authoritative"),
            "browser_working": ("browser_worker", "runtime_observed"),
            "short_term": ("task_session", "task_supplied"),
            "org_memory": ("organization_memory", "organization_curated"),
            "enterprise_knowledge": ("enterprise_catalog", "enterprise_curated"),
        }
        if (self.source, self.trust) != expected[self.layer]:
            raise ValueError("context layer provenance mismatch")
        if content_hash(self.safe_value) != self.content_hash:
            raise ValueError("context item content hash mismatch")
        return self


class LayerCounts(StrictModel):
    task_facts: int = Field(ge=0, le=8)
    browser_working: int = Field(ge=0, le=6)
    short_term: int = Field(ge=0, le=8)
    org_memory: int = Field(ge=0, le=6)
    enterprise_knowledge: int = Field(ge=0, le=6)


class ContextBudgetSnapshot(StrictModel):
    item_count: int = Field(ge=1, le=32)
    canonical_bytes: int = Field(ge=1, le=16_384)
    estimated_tokens: int = Field(ge=1, le=4_096)


class AssembledContext(StrictModel):
    schema_version: Literal["w9-assembled-context/1.0"] = "w9-assembled-context/1.0"
    run_id: RunId
    task_id: TaskId
    scope_id: ScopeId
    process: BusinessProcess
    phase: TaskPhase
    ablation: AblationProfile
    as_of: datetime
    database_snapshot_hash: Checksum
    layer_counts: LayerCounts
    budget: ContextBudgetSnapshot
    summary_hash: Checksum | None = None
    retrieval_catalog_checksum: Checksum | None = None
    items: tuple[ContextItem, ...] = Field(min_length=1, max_length=32)
    context_hash: Checksum

    @field_validator("as_of", mode="before")
    @classmethod
    def timestamp_is_utc(cls, value: object) -> datetime:
        return parse_utc(value)

    @field_validator("items", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_counts_order_and_hash(self) -> Self:
        layer_index = {
            "task_facts": 0,
            "browser_working": 1,
            "short_term": 2,
            "org_memory": 3,
            "enterprise_knowledge": 4,
        }
        indexes = tuple(layer_index[item.layer] for item in self.items)
        if indexes != tuple(sorted(indexes)):
            raise ValueError("context layers are out of order")
        expected_counts = {
            layer: sum(item.layer == layer for item in self.items) for layer in layer_index
        }
        if self.layer_counts.model_dump() != expected_counts:
            raise ValueError("context layer counts mismatch")
        if (
            self.budget.item_count != len(self.items)
            or self.budget.canonical_bytes != sum(item.canonical_bytes for item in self.items)
            or self.budget.estimated_tokens != sum(item.estimated_tokens for item in self.items)
        ):
            raise ValueError("context budget projection mismatch")
        if self.context_hash != "0" * 64:
            fields = self.model_dump(mode="json", exclude={"context_hash"})
            if sha256_hex(canonical_json_bytes(fields)) != self.context_hash:
                raise ValueError("context hash mismatch")
        return self


class ContextAssembleRequest(StrictModel):
    schema_version: Literal["w9-context-request/1.0"] = "w9-context-request/1.0"
    run_id: RunId
    task_id: TaskId
    scope_id: ScopeId
    actor_scope_id: ScopeId
    process: BusinessProcess
    phase: TaskPhase
    as_of: datetime
    database_snapshot_hash: Checksum
    task_facts: tuple[TaskFactInput, ...] = Field(min_length=1, max_length=8)
    browser_working: tuple[BrowserWorkingInput, ...] = Field(max_length=12)
    short_term_events: tuple[ShortTermEvent, ...] = Field(max_length=12)
    memory_mutations: tuple[MemoryMutation, ...] = Field(max_length=12)
    ablation: AblationProfile = "full_five_layer"
    budget: TotalBudget = TotalBudget()

    @field_validator(
        "task_facts",
        "browser_working",
        "short_term_events",
        "memory_mutations",
        mode="before",
    )
    @classmethod
    def accept_json_arrays(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("as_of", mode="before")
    @classmethod
    def timestamp_is_utc(cls, value: object) -> datetime:
        return parse_utc(value)

    @model_validator(mode="after")
    def validate_ownership(self) -> Self:
        if self.actor_scope_id != self.scope_id:
            raise ValueError("cross-scope context request rejected")
        fact_mismatch = any(
            item.task_id != self.task_id or item.scope_id != self.scope_id
            for item in self.task_facts
        )
        browser_mismatch = any(
            item.task_id != self.task_id or item.scope_id != self.scope_id
            for item in self.browser_working
        )
        event_mismatch = any(
            item.task_id != self.task_id or item.scope_id != self.scope_id
            for item in self.short_term_events
        )
        if fact_mismatch or browser_mismatch or event_mismatch:
            raise ValueError("context item owner mismatch")
        if self.task_id.startswith("w3-"):
            expected_process = "joiner"
        else:
            expected_process = self.task_id.split("-")[2]
        if self.process != expected_process:
            raise ValueError("task ID and process mismatch")
        return self


class ContextAssembleResult(StrictModel):
    schema_version: Literal["w9-context-result/1.0"] = "w9-context-result/1.0"
    context: AssembledContext
    usage: TotalUsage


class ContextPlanningRunRequest(StrictModel):
    schema_version: Literal["w9-context-planning-run/1.0"] = "w9-context-planning-run/1.0"
    context: ContextAssembleRequest
    planning: PlanningRunRequest

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if (
            self.context.run_id != self.planning.run_id
            or self.context.task_id != self.planning.task_id
            or self.context.process != self.planning.process
            or self.context.budget != self.planning.budget
        ):
            raise ValueError("context and Planning identities or budgets differ")
        return self


class ContextPlanningRunResult(StrictModel):
    schema_version: Literal["w9-context-planning-result/1.0"] = "w9-context-planning-result/1.0"
    context: AssembledContext
    planning: PlanningRunResult


def validate_context_hash(context: AssembledContext) -> None:
    fields = context.model_dump(mode="json", exclude={"context_hash"})
    if sha256_hex(canonical_json_bytes(fields)) != context.context_hash:
        raise ValueError("context hash mismatch")


def validate_summary_hash(summary: ShortTermSummary) -> None:
    fields = summary.model_dump(mode="json", exclude={"summary_hash"})
    if sha256_hex(canonical_json_bytes(fields)) != summary.summary_hash:
        raise ValueError("summary hash mismatch")
