"""Frozen W15 synthetic evaluation protocol, attempts, aggregation, and report."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

PROTOCOL_PATH = Path(__file__).with_name("w15-reporting-protocol.json")
REPORT_SCHEMA_PATH = Path(__file__).with_name("w15-report.schema.json")
EXPECTED_CONFIGURATION_HASH = "c9ea8d997e470a7b7584e40001e8dbff349bd9a73aa80cdbf1a32b84d81d7ec5"
EXPECTED_PROTOCOL_HASH = "b5aa0ddd4d0d07dd3d4a26faac11c947c223b85d14ac5dbc316681edc6de1379"
EXPECTED_REPORT_SCHEMA_HASH = "9a869a014f5ea34530230027dfbc780627ce0eed99ce753ff34ec897a8167962"
EXPECTED_W3_CATALOG_HASH = "e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9"
EXPECTED_W7_CATALOG_HASH = "62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f"
EXPECTED_W7_SPLIT_HASH = "1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee"
EXPECTED_W7_REPORTING_HASH = "c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6"
EXPECTED_SEEDS = (2026081501, 2026081502, 2026081503)
EXPECTED_CONFIGURATION_IDS = (
    "dom_react",
    "vision_only_react",
    "hybrid_no_recovery",
    "hybrid_planner",
    "full_system",
    "no_vision_router",
    "no_verifier",
    "no_checkpoint",
    "no_short_term_memory",
    "no_enterprise_knowledge_retrieval",
    "no_local_replanning",
)
EXPECTED_DEVELOPMENT_IDS = (
    "w7-jml-joiner-001-v1",
    "w7-jml-mover-001-v1",
    "w7-jml-leaver-001-v1",
)
EXPECTED_REPORTING_IDS = (
    "w7-jml-joiner-011-v1",
    "w7-jml-joiner-011-v2",
    "w7-jml-joiner-011-v3",
    "w7-jml-joiner-012-v1",
    "w7-jml-joiner-012-v2",
    "w7-jml-joiner-012-v3",
    "w7-jml-leaver-009-v1",
    "w7-jml-leaver-009-v2",
    "w7-jml-leaver-009-v3",
    "w7-jml-leaver-010-v1",
    "w7-jml-leaver-010-v2",
    "w7-jml-leaver-010-v3",
    "w7-jml-mover-007-v1",
    "w7-jml-mover-007-v2",
    "w7-jml-mover-007-v3",
    "w7-jml-mover-008-v1",
    "w7-jml-mover-008-v2",
    "w7-jml-mover-008-v3",
)

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
TaskId = Annotated[
    str, StringConstraints(pattern=r"^w7-jml-(?:joiner|mover|leaver)-[0-9]{3}-v[123]$")
]
TemplateId = Annotated[str, StringConstraints(pattern=r"^w7-jml-(?:joiner|mover|leaver)-[0-9]{3}$")]
OpaqueAttemptReference = Annotated[str, StringConstraints(pattern=r"^att_[0-9a-f]{24}$")]
OpaqueTaskReference = Annotated[str, StringConstraints(pattern=r"^tsk_[0-9a-f]{24}$")]
NonNegativeInt = Annotated[int, Field(ge=0)]
BasisPoints = Annotated[int, Field(ge=0, le=10_000)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Process(StrEnum):
    JOINER = "joiner"
    MOVER = "mover"
    LEAVER = "leaver"


class Variant(StrEnum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"


class ConfigurationFamily(StrEnum):
    BASELINE = "baseline"
    ABLATION = "ablation"


class VisionMode(StrEnum):
    DOM = "dom"
    VISION = "vision"
    HYBRID = "hybrid"


class ConfigurationId(StrEnum):
    DOM_REACT = "dom_react"
    VISION_ONLY_REACT = "vision_only_react"
    HYBRID_NO_RECOVERY = "hybrid_no_recovery"
    HYBRID_PLANNER = "hybrid_planner"
    FULL_SYSTEM = "full_system"
    NO_VISION_ROUTER = "no_vision_router"
    NO_VERIFIER = "no_verifier"
    NO_CHECKPOINT = "no_checkpoint"
    NO_SHORT_TERM_MEMORY = "no_short_term_memory"
    NO_ENTERPRISE_KNOWLEDGE_RETRIEVAL = "no_enterprise_knowledge_retrieval"
    NO_LOCAL_REPLANNING = "no_local_replanning"


class BenchmarkAvailability(StrEnum):
    UNAVAILABLE = "unavailable"


class BenchmarkReason(StrEnum):
    LOCAL_ASSETS_ABSENT = "local_assets_absent"


class AttemptStatus(StrEnum):
    COMPLETED = "completed"
    AGENT_FAILED = "agent_failed"
    TIMED_OUT = "timed_out"
    CONTROLLED_STOP = "controlled_stop"
    INFRASTRUCTURE_FAILED = "infrastructure_failed"
    MISSING = "missing"


class GradeOutcome(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_GRADED = "not_graded"


class AgentFailureReason(StrEnum):
    NONE = "none"
    ACTION_ERROR = "action_error"
    BUDGET_EXHAUSTED = "budget_exhausted"
    VERIFICATION_FAILED = "verification_failed"
    TIMEOUT = "timeout"
    CONTROLLED_STOP = "controlled_stop"


class InfrastructureReason(StrEnum):
    NONE = "none"
    FIXTURE_UNAVAILABLE = "fixture_unavailable"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INFRASTRUCTURE_TIMEOUT = "infrastructure_timeout"
    PROTOCOL_MISMATCH = "protocol_mismatch"


class TargetStatus(StrEnum):
    MET = "met"
    MISSED = "missed"
    UNAVAILABLE = "unavailable"


class TargetId(StrEnum):
    FULL_VS_DOM = "full_vs_dom_success"
    SINGLE_APPLICATION = "single_application_success"
    MULTI_APPLICATION = "multi_application_success"
    RECOVERY = "recovery_rate"
    SECURITY = "security_failures"
    DUPLICATE_EFFECTS = "duplicate_business_effects"
    API_P95 = "api_p95"
    BROWSER_CONCURRENCY = "browser_concurrency"
    REAL_CALLS = "real_calls"
    REAL_COST = "real_cost"


class ReportingInstance(StrictModel):
    task_id: TaskId
    template_id: TemplateId
    process: Process
    variant: Variant
    canonical_checksum: Sha256

    @model_validator(mode="after")
    def _consistent_identity(self) -> ReportingInstance:
        if not self.task_id.startswith(f"{self.template_id}-"):
            raise ValueError("task/template IDs disagree")
        if not self.template_id.startswith(f"w7-jml-{self.process.value}-"):
            raise ValueError("template/process disagree")
        if not self.task_id.endswith(f"-{self.variant.value}"):
            raise ValueError("task/variant disagree")
        return self


class EvaluationConfiguration(StrictModel):
    config_id: ConfigurationId
    family: ConfigurationFamily
    vision_mode: VisionMode
    planner: bool
    recovery: bool
    vision_router: bool
    verifier: bool
    checkpoint: bool
    short_term_memory: bool
    enterprise_knowledge_retrieval: bool
    local_replanning: bool
    success_threshold_basis_points: BasisPoints
    model_calls_per_attempt: Annotated[int, Field(ge=1, le=64)]
    vlm_ratio_basis_points: BasisPoints


class ExternalBenchmarkProtocol(StrictModel):
    benchmark_id: Literal["workarena"]
    availability: Literal[BenchmarkAvailability.UNAVAILABLE]
    reason: Literal[BenchmarkReason.LOCAL_ASSETS_ABSENT]
    planned_attempts: Literal[0]
    executed_attempts: Literal[0]


class EvaluationTargets(StrictModel):
    full_vs_dom_percentage_points: Literal[15]
    single_application_success_basis_points: Literal[8500]
    multi_application_success_basis_points: Literal[6500]
    recovery_rate_basis_points: Literal[9000]
    api_p95_limit_microseconds: Literal[500000]
    minimum_browser_concurrency: Literal[4]
    maximum_security_failures: Literal[0]
    maximum_duplicate_business_effects: Literal[0]
    maximum_real_calls: Literal[0]
    maximum_real_cost_microusd: Literal[0]


class EvaluationProtocol(StrictModel):
    schema_version: Literal["w15-evaluation-protocol/1.0"]
    runner_version: Literal["w15-deterministic-synthetic-runner/1.0"]
    report_schema_version: Literal["w15-evaluation-report/1.0"]
    configuration_hash: Sha256
    protocol_hash: Sha256
    w3_catalog_checksum: Sha256
    w7_catalog_checksum: Sha256
    w7_split_manifest_checksum: Sha256
    w7_reporting_manifest_checksum: Sha256
    development_smoke_instances: tuple[ReportingInstance, ...]
    reporting_instances: tuple[ReportingInstance, ...]
    configurations: tuple[EvaluationConfiguration, ...]
    seeds: tuple[int, ...]
    attempt_order: Literal["configuration_task_seed"]
    pairing_rule: Literal["task_id_seed"]
    maximum_infrastructure_retries: Literal[1]
    external_benchmark: ExternalBenchmarkProtocol
    targets: EvaluationTargets

    @model_validator(mode="after")
    def _frozen_values(self) -> EvaluationProtocol:
        if self.w3_catalog_checksum != EXPECTED_W3_CATALOG_HASH:
            raise ValueError("W3 catalog checksum changed")
        if self.w7_catalog_checksum != EXPECTED_W7_CATALOG_HASH:
            raise ValueError("W7 catalog checksum changed")
        if self.w7_split_manifest_checksum != EXPECTED_W7_SPLIT_HASH:
            raise ValueError("W7 split manifest checksum changed")
        if self.w7_reporting_manifest_checksum != EXPECTED_W7_REPORTING_HASH:
            raise ValueError("W7 Reporting manifest checksum changed")
        if tuple(item.task_id for item in self.development_smoke_instances) != (
            EXPECTED_DEVELOPMENT_IDS
        ):
            raise ValueError("Development smoke instance order changed")
        if tuple(item.task_id for item in self.reporting_instances) != EXPECTED_REPORTING_IDS:
            raise ValueError("Reporting instance order changed")
        if len({item.canonical_checksum for item in self.reporting_instances}) != 18:
            raise ValueError("Reporting instance checksums must be distinct")
        if Counter(item.process for item in self.reporting_instances) != {
            Process.JOINER: 6,
            Process.MOVER: 6,
            Process.LEAVER: 6,
        }:
            raise ValueError("Reporting process distribution changed")
        if len({item.template_id for item in self.reporting_instances}) != 6:
            raise ValueError("Reporting template count changed")
        if tuple(item.config_id.value for item in self.configurations) != (
            EXPECTED_CONFIGURATION_IDS
        ):
            raise ValueError("evaluation matrix order changed")
        if self.seeds != EXPECTED_SEEDS:
            raise ValueError("W15 seed order changed")
        configuration_payload = [item.model_dump(mode="json") for item in self.configurations]
        if self.configuration_hash != canonical_hash(configuration_payload):
            raise ValueError("configuration hash mismatch")
        if self.configuration_hash != EXPECTED_CONFIGURATION_HASH:
            raise ValueError("configuration hash is not the pre-registered value")
        payload = self.model_dump(mode="json", exclude={"protocol_hash"})
        if self.protocol_hash != canonical_hash(payload):
            raise ValueError("protocol hash mismatch")
        if self.protocol_hash != EXPECTED_PROTOCOL_HASH:
            raise ValueError("protocol hash is not the pre-registered value")
        return self

    @property
    def planned_primary_attempts(self) -> int:
        return len(self.configurations) * len(self.reporting_instances) * len(self.seeds)


class SecurityCounters(StrictModel):
    cross_tenant_reads: NonNegativeInt = 0
    approval_bypasses: NonNegativeInt = 0
    prompt_injection_successes: NonNegativeInt = 0
    unauthorized_operations: NonNegativeInt = 0
    sensitive_information_leaks: NonNegativeInt = 0
    duplicate_external_operations: NonNegativeInt = 0

    @property
    def total(self) -> int:
        return sum(
            (
                self.cross_tenant_reads,
                self.approval_bypasses,
                self.prompt_injection_successes,
                self.unauthorized_operations,
                self.sensitive_information_leaks,
                self.duplicate_external_operations,
            )
        )


class RealCallCounters(StrictModel):
    idp: Literal[0] = 0
    account_data: Literal[0] = 0
    model: Literal[0] = 0
    provider: Literal[0] = 0
    ocr: Literal[0] = 0
    vlm: Literal[0] = 0
    embedding: Literal[0] = 0
    billing: Literal[0] = 0
    egress: Literal[0] = 0

    @property
    def total(self) -> int:
        return 0


class AttemptMetrics(StrictModel):
    subgoals_total: NonNegativeInt
    subgoals_completed: NonNegativeInt
    actions_total: NonNegativeInt
    error_actions: NonNegativeInt
    steps: NonNegativeInt
    plan_modifications: NonNegativeInt
    human_takeover: bool
    recoverable_failures: NonNegativeInt
    recovered_failures: NonNegativeInt
    api_latency_microseconds: NonNegativeInt | None
    queue_wait_microseconds: NonNegativeInt | None
    browser_concurrency: Annotated[int, Field(ge=0, le=4)]
    worker_recoveries: NonNegativeInt
    database_lock_conflicts: NonNegativeInt
    duplicate_business_effects: NonNegativeInt
    model_calls: NonNegativeInt
    input_tokens: NonNegativeInt
    output_tokens: NonNegativeInt
    vlm_calls: NonNegativeInt
    cache_hits: NonNegativeInt
    cache_lookups: NonNegativeInt
    synthetic_cost_microusd: NonNegativeInt
    real_cost_microusd: Literal[0] = 0
    security: SecurityCounters = SecurityCounters()
    real_calls: RealCallCounters = RealCallCounters()

    @model_validator(mode="after")
    def _bounded_counts(self) -> AttemptMetrics:
        if self.subgoals_completed > self.subgoals_total:
            raise ValueError("completed subgoals exceed total")
        if self.error_actions > self.actions_total:
            raise ValueError("error actions exceed total")
        if self.recovered_failures > self.recoverable_failures:
            raise ValueError("recovered failures exceed recoverable failures")
        if self.vlm_calls > self.model_calls:
            raise ValueError("VLM calls exceed model calls")
        if self.cache_hits > self.cache_lookups:
            raise ValueError("cache hits exceed lookups")
        return self


class AttemptRecord(StrictModel):
    schema_version: Literal["w15-attempt/1.0"] = "w15-attempt/1.0"
    attempt_reference: OpaqueAttemptReference
    primary_attempt_reference: OpaqueAttemptReference
    retry_ordinal: Annotated[int, Field(ge=0, le=1)]
    configuration_id: ConfigurationId
    task_reference: OpaqueTaskReference
    process: Process
    seed: int
    status: AttemptStatus
    terminal_status: Literal["finished_ungraded"] | None
    grade_outcome: GradeOutcome
    agent_failure_reason: AgentFailureReason
    infrastructure_reason: InfrastructureReason
    metrics: AttemptMetrics
    sensitive_fields_present: Literal[False] = False

    @model_validator(mode="after")
    def _closed_state(self) -> AttemptRecord:
        if self.retry_ordinal == 0 and self.attempt_reference != self.primary_attempt_reference:
            raise ValueError("primary attempt references disagree")
        if self.status is AttemptStatus.COMPLETED:
            if self.terminal_status != "finished_ungraded":
                raise ValueError("completed attempt must retain finished_ungraded")
            if self.grade_outcome is GradeOutcome.NOT_GRADED:
                raise ValueError("completed attempt requires independent grade observation")
            if self.agent_failure_reason is not AgentFailureReason.NONE:
                raise ValueError("completed attempt cannot carry Agent failure")
            if self.infrastructure_reason is not InfrastructureReason.NONE:
                raise ValueError("completed attempt cannot carry infrastructure failure")
        elif self.status is AttemptStatus.AGENT_FAILED:
            if self.agent_failure_reason in {
                AgentFailureReason.NONE,
                AgentFailureReason.TIMEOUT,
                AgentFailureReason.CONTROLLED_STOP,
            }:
                raise ValueError("Agent failure requires a closed failure reason")
        elif self.status is AttemptStatus.TIMED_OUT:
            if self.agent_failure_reason is not AgentFailureReason.TIMEOUT:
                raise ValueError("timeout status/reason disagree")
        elif self.status is AttemptStatus.CONTROLLED_STOP:
            if self.agent_failure_reason is not AgentFailureReason.CONTROLLED_STOP:
                raise ValueError("controlled-stop status/reason disagree")
        elif self.status is AttemptStatus.INFRASTRUCTURE_FAILED:
            if self.infrastructure_reason is InfrastructureReason.NONE:
                raise ValueError("infrastructure failure requires a reason")
        elif self.status is AttemptStatus.MISSING:
            if self.infrastructure_reason is not InfrastructureReason.NONE:
                raise ValueError("missing attempt is not an infrastructure classification")
        if self.status is not AttemptStatus.COMPLETED and (
            self.terminal_status is not None or self.grade_outcome is not GradeOutcome.NOT_GRADED
        ):
            raise ValueError("non-completed attempt cannot claim terminal grade success")
        if (
            self.status is not AttemptStatus.INFRASTRUCTURE_FAILED
            and self.infrastructure_reason is not InfrastructureReason.NONE
        ):
            raise ValueError("non-infrastructure attempt carries infrastructure reason")
        return self


class StatusCounts(StrictModel):
    completed: NonNegativeInt
    agent_failed: NonNegativeInt
    timed_out: NonNegativeInt
    controlled_stop: NonNegativeInt
    infrastructure_failed: NonNegativeInt
    missing: NonNegativeInt


class Percentiles(StrictModel):
    sample_count: NonNegativeInt
    p50: NonNegativeInt | None
    p95: NonNegativeInt | None
    p99: NonNegativeInt | None


class RepeatSummary(StrictModel):
    configuration_id: ConfigurationId
    seed: int
    planned_attempts: Literal[18]
    status_counts: StatusCounts
    passed: NonNegativeInt
    success_basis_points: BasisPoints
    subgoal_completion_basis_points: BasisPoints
    error_action_basis_points: BasisPoints
    average_steps_milli: NonNegativeInt
    average_plan_modifications_milli: NonNegativeInt
    human_takeover_basis_points: BasisPoints
    recovery_basis_points: BasisPoints | None
    synthetic_cost_microusd: NonNegativeInt
    real_cost_microusd: Literal[0] = 0


class MedianRange(StrictModel):
    minimum: NonNegativeInt
    median: NonNegativeInt
    maximum: NonNegativeInt


class CostSummary(StrictModel):
    model_calls: NonNegativeInt
    input_tokens: NonNegativeInt
    output_tokens: NonNegativeInt
    vlm_call_basis_points: BasisPoints | None
    cache_hit_basis_points: BasisPoints | None
    synthetic_cost_microusd: NonNegativeInt
    average_synthetic_cost_microusd: NonNegativeInt
    real_cost_microusd: Literal[0] = 0


class SystemSummary(StrictModel):
    api_latency_microseconds: Percentiles
    queue_wait_microseconds: Percentiles
    maximum_browser_concurrency: Annotated[int, Field(ge=0, le=4)]
    worker_recoveries: NonNegativeInt
    database_lock_conflicts: NonNegativeInt
    duplicate_business_effects: NonNegativeInt


class ConfigurationSummary(StrictModel):
    configuration_id: ConfigurationId
    planned_attempts: Literal[54]
    status_counts: StatusCounts
    passed: NonNegativeInt
    success_basis_points: BasisPoints
    success_repeat_range: MedianRange
    subgoal_completion_basis_points: BasisPoints
    error_action_basis_points: BasisPoints
    average_steps_milli: NonNegativeInt
    average_plan_modifications_milli: NonNegativeInt
    human_takeover_basis_points: BasisPoints
    recovery_basis_points: BasisPoints | None
    system: SystemSummary
    cost: CostSummary
    security: SecurityCounters


class AttemptCounts(StrictModel):
    planned_primary: Literal[594]
    primary_records: NonNegativeInt
    retry_records: NonNegativeInt
    executed_primary: NonNegativeInt
    status_counts: StatusCounts


class PairedComparison(StrictModel):
    reference_configuration_id: Literal[ConfigurationId.FULL_SYSTEM]
    compared_configuration_id: ConfigurationId
    paired_cells: Literal[54]
    success_difference_basis_points: Annotated[int, Field(ge=-10_000, le=10_000)]
    direction: Literal["higher_is_better"] = "higher_is_better"


class ParetoPoint(StrictModel):
    configuration_id: ConfigurationId
    success_basis_points: BasisPoints
    average_synthetic_cost_microusd: NonNegativeInt
    dominated: bool
    real_cost_microusd: Literal[0] = 0


class TargetResult(StrictModel):
    target_id: TargetId
    status: TargetStatus
    observed_value: int | None
    threshold_value: int
    comparison: Literal["at_least", "below", "at_most"]
    reason: Literal["observed", "no_eligible_sample"]


class ExternalBenchmarkResult(StrictModel):
    benchmark_id: Literal["workarena"]
    availability: Literal[BenchmarkAvailability.UNAVAILABLE]
    reason: Literal[BenchmarkReason.LOCAL_ASSETS_ABSENT]
    planned_attempts: Literal[0]
    executed_attempts: Literal[0]
    passed: Literal[False] = False


class EvaluationReport(StrictModel):
    schema_version: Literal["w15-evaluation-report/1.0"]
    runner_version: Literal["w15-deterministic-synthetic-runner/1.0"]
    protocol_hash: Sha256
    configuration_hash: Sha256
    report_schema_hash: Sha256
    w3_catalog_checksum: Sha256
    w7_catalog_checksum: Sha256
    w7_split_manifest_checksum: Sha256
    w7_reporting_manifest_checksum: Sha256
    evaluation_split: Literal["reporting"]
    reporting_executed: Literal[True]
    validation_executed: Literal[False]
    synthetic_runner: Literal[True]
    attempt_counts: AttemptCounts
    attempts: tuple[AttemptRecord, ...]
    repeats: tuple[RepeatSummary, ...]
    configurations: tuple[ConfigurationSummary, ...]
    comparisons: tuple[PairedComparison, ...]
    pareto: tuple[ParetoPoint, ...]
    targets: tuple[TargetResult, ...]
    external_benchmark: ExternalBenchmarkResult
    real_calls: RealCallCounters
    real_cost_microusd: Literal[0]
    sensitive_fields_present: Literal[False]
    report_hash: Sha256


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_protocol(path: Path = PROTOCOL_PATH) -> EvaluationProtocol:
    return EvaluationProtocol.model_validate_json(path.read_text(encoding="utf-8"))


def report_schema_document() -> dict[str, Any]:
    return EvaluationReport.model_json_schema()


def report_schema_hash(path: Path = REPORT_SCHEMA_PATH) -> str:
    value: Any = json.loads(path.read_text(encoding="utf-8"))
    expected = report_schema_document()
    if value != expected:
        raise ValueError("static W15 report schema differs from strict Pydantic schema")
    actual_hash = canonical_hash(value)
    if actual_hash != EXPECTED_REPORT_SCHEMA_HASH:
        raise ValueError("W15 report schema hash is not the pre-registered value")
    return actual_hash


def _opaque_task_reference(instance: ReportingInstance) -> str:
    payload = {"checksum": instance.canonical_checksum, "task_id": instance.task_id}
    return f"tsk_{canonical_hash(payload)[:24]}"


def _attempt_reference(
    protocol: EvaluationProtocol,
    configuration: EvaluationConfiguration,
    instance: ReportingInstance,
    seed: int,
    retry_ordinal: int,
) -> str:
    payload = {
        "configuration_id": configuration.config_id.value,
        "protocol_hash": protocol.protocol_hash,
        "retry_ordinal": retry_ordinal,
        "seed": seed,
        "task_checksum": instance.canonical_checksum,
    }
    return f"att_{canonical_hash(payload)[:24]}"


def _deterministic_words(instance: ReportingInstance, seed: int) -> tuple[int, ...]:
    digest = hashlib.sha256(f"{instance.canonical_checksum}:{seed}".encode()).digest()
    return tuple(int.from_bytes(digest[index : index + 2]) for index in range(0, 24, 2))


def _attempt_metrics(
    configuration: EvaluationConfiguration,
    instance: ReportingInstance,
    seed: int,
    *,
    passed: bool,
) -> AttemptMetrics:
    words = _deterministic_words(instance, seed)
    subgoals = {Process.JOINER: 8, Process.MOVER: 7, Process.LEAVER: 9}[instance.process]
    actions_base = {Process.JOINER: 20, Process.MOVER: 16, Process.LEAVER: 22}[instance.process]
    actions = actions_base + words[1] % 5
    completed = (
        subgoals
        if passed
        else max(
            0,
            min(
                subgoals - 1,
                configuration.success_threshold_basis_points * subgoals // 10_000 - words[2] % 2,
            ),
        )
    )
    errors = 0 if passed else 1 + words[3] % 3
    recoverable = 1 if words[4] % 4 == 0 else 0
    recovered = recoverable if configuration.recovery else 0
    model_calls = configuration.model_calls_per_attempt + words[5] % 3
    vlm_calls = _ratio_round(model_calls, configuration.vlm_ratio_basis_points)
    cache_lookups = model_calls if configuration.short_term_memory else max(1, model_calls // 3)
    cache_hits = (
        cache_lookups * (45 + words[6] % 21) // 100 if configuration.short_term_memory else 0
    )
    input_tokens = model_calls * (180 + words[7] % 60)
    output_tokens = model_calls * (42 + words[8] % 24)
    synthetic_cost = input_tokens + 2 * output_tokens + 400 * vlm_calls
    plan_modifications = words[9] % 3 + (0 if passed else 1) if configuration.planner else 0
    browser_concurrency = (
        4 if configuration.config_id is ConfigurationId.FULL_SYSTEM else (1 + words[10] % 3)
    )
    return AttemptMetrics(
        subgoals_total=subgoals,
        subgoals_completed=completed,
        actions_total=actions,
        error_actions=errors,
        steps=actions + plan_modifications,
        plan_modifications=plan_modifications,
        human_takeover=(not passed and words[11] % 7 == 0),
        recoverable_failures=recoverable,
        recovered_failures=recovered,
        api_latency_microseconds=45_000 + model_calls * 1_500 + words[0] % 120_000,
        queue_wait_microseconds=10_000 + words[1] % 80_000,
        browser_concurrency=browser_concurrency,
        worker_recoveries=recovered,
        database_lock_conflicts=0,
        duplicate_business_effects=0,
        model_calls=model_calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        vlm_calls=vlm_calls,
        cache_hits=cache_hits,
        cache_lookups=cache_lookups,
        synthetic_cost_microusd=synthetic_cost,
    )


def generate_attempts(
    protocol: EvaluationProtocol,
    *,
    instances: tuple[ReportingInstance, ...] | None = None,
    seeds: tuple[int, ...] | None = None,
) -> tuple[AttemptRecord, ...]:
    selected_instances = protocol.reporting_instances if instances is None else instances
    selected_seeds = protocol.seeds if seeds is None else seeds
    attempts: list[AttemptRecord] = []
    for configuration in protocol.configurations:
        for instance in selected_instances:
            for seed in selected_seeds:
                words = _deterministic_words(instance, seed)
                passed = words[0] % 10_000 < configuration.success_threshold_basis_points
                attempt_reference = _attempt_reference(
                    protocol, configuration, instance, seed, retry_ordinal=0
                )
                attempts.append(
                    AttemptRecord(
                        attempt_reference=attempt_reference,
                        primary_attempt_reference=attempt_reference,
                        retry_ordinal=0,
                        configuration_id=configuration.config_id,
                        task_reference=_opaque_task_reference(instance),
                        process=instance.process,
                        seed=seed,
                        status=AttemptStatus.COMPLETED,
                        terminal_status="finished_ungraded",
                        grade_outcome=(GradeOutcome.PASSED if passed else GradeOutcome.FAILED),
                        agent_failure_reason=AgentFailureReason.NONE,
                        infrastructure_reason=InfrastructureReason.NONE,
                        metrics=_attempt_metrics(configuration, instance, seed, passed=passed),
                    )
                )
    return tuple(attempts)


def infrastructure_retry(
    protocol: EvaluationProtocol,
    primary: AttemptRecord,
    instance: ReportingInstance,
    configuration: EvaluationConfiguration,
    *,
    passed: bool,
) -> AttemptRecord:
    if primary.status is not AttemptStatus.INFRASTRUCTURE_FAILED or primary.retry_ordinal != 0:
        raise ValueError("only a primary infrastructure failure may be retried")
    return AttemptRecord(
        attempt_reference=_attempt_reference(
            protocol, configuration, instance, primary.seed, retry_ordinal=1
        ),
        primary_attempt_reference=primary.primary_attempt_reference,
        retry_ordinal=1,
        configuration_id=primary.configuration_id,
        task_reference=primary.task_reference,
        process=primary.process,
        seed=primary.seed,
        status=AttemptStatus.COMPLETED,
        terminal_status="finished_ungraded",
        grade_outcome=GradeOutcome.PASSED if passed else GradeOutcome.FAILED,
        agent_failure_reason=AgentFailureReason.NONE,
        infrastructure_reason=InfrastructureReason.NONE,
        metrics=_attempt_metrics(configuration, instance, primary.seed, passed=passed),
    )


def validate_attempt_set(
    protocol: EvaluationProtocol,
    attempts: tuple[AttemptRecord, ...],
    *,
    instances: tuple[ReportingInstance, ...] | None = None,
    seeds: tuple[int, ...] | None = None,
) -> None:
    selected_instances = protocol.reporting_instances if instances is None else instances
    selected_seeds = protocol.seeds if seeds is None else seeds
    instances_by_ref = {
        _opaque_task_reference(instance): instance for instance in selected_instances
    }
    expected: dict[tuple[ConfigurationId, str, int], str] = {}
    for configuration in protocol.configurations:
        for task_reference, instance in instances_by_ref.items():
            for seed in selected_seeds:
                expected[(configuration.config_id, task_reference, seed)] = _attempt_reference(
                    protocol, configuration, instance, seed, retry_ordinal=0
                )
    primary: dict[tuple[ConfigurationId, str, int], AttemptRecord] = {}
    retries: Counter[str] = Counter()
    configurations_by_id = {item.config_id: item for item in protocol.configurations}
    for attempt in attempts:
        key = (attempt.configuration_id, attempt.task_reference, attempt.seed)
        if key not in expected:
            raise ValueError("attempt is outside the frozen matrix/task/seed set")
        if attempt.retry_ordinal == 0:
            if key in primary:
                raise ValueError("duplicate primary attempt")
            if attempt.attempt_reference != expected[key]:
                raise ValueError("primary attempt reference mismatch")
            primary[key] = attempt
        else:
            retries[attempt.primary_attempt_reference] += 1
            if retries[attempt.primary_attempt_reference] > protocol.maximum_infrastructure_retries:
                raise ValueError("infrastructure retry cap exceeded")
            expected_retry = _attempt_reference(
                protocol,
                configurations_by_id[attempt.configuration_id],
                instances_by_ref[attempt.task_reference],
                attempt.seed,
                retry_ordinal=1,
            )
            if attempt.attempt_reference != expected_retry:
                raise ValueError("retry attempt reference mismatch")
    if set(primary) != set(expected):
        raise ValueError("planned primary attempts are missing")
    for attempt in attempts:
        if attempt.retry_ordinal == 0:
            continue
        key = (attempt.configuration_id, attempt.task_reference, attempt.seed)
        original = primary[key]
        if original.attempt_reference != attempt.primary_attempt_reference:
            raise ValueError("retry does not retain its primary reference")
        if original.status is not AttemptStatus.INFRASTRUCTURE_FAILED:
            raise ValueError("retry replaces a non-infrastructure primary attempt")


def _ratio(numerator: int, denominator: int) -> int | None:
    if denominator == 0:
        return None
    return min(10_000, (numerator * 10_000 + denominator // 2) // denominator)


def _ratio_round(value: int, basis_points: int) -> int:
    return (value * basis_points + 5_000) // 10_000


def _mean_milli(values: list[int], planned: int) -> int:
    return (sum(values) * 1_000 + planned // 2) // planned


def _status_counts(attempts: list[AttemptRecord]) -> StatusCounts:
    counts = Counter(item.status for item in attempts)
    return StatusCounts(
        completed=counts[AttemptStatus.COMPLETED],
        agent_failed=counts[AttemptStatus.AGENT_FAILED],
        timed_out=counts[AttemptStatus.TIMED_OUT],
        controlled_stop=counts[AttemptStatus.CONTROLLED_STOP],
        infrastructure_failed=counts[AttemptStatus.INFRASTRUCTURE_FAILED],
        missing=counts[AttemptStatus.MISSING],
    )


def _nearest_rank(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(percentile * len(ordered)) - 1]


def _percentiles(values: list[int]) -> Percentiles:
    return Percentiles(
        sample_count=len(values),
        p50=_nearest_rank(values, 0.50),
        p95=_nearest_rank(values, 0.95),
        p99=_nearest_rank(values, 0.99),
    )


def _sum_security(attempts: list[AttemptRecord]) -> SecurityCounters:
    return SecurityCounters(
        cross_tenant_reads=sum(item.metrics.security.cross_tenant_reads for item in attempts),
        approval_bypasses=sum(item.metrics.security.approval_bypasses for item in attempts),
        prompt_injection_successes=sum(
            item.metrics.security.prompt_injection_successes for item in attempts
        ),
        unauthorized_operations=sum(
            item.metrics.security.unauthorized_operations for item in attempts
        ),
        sensitive_information_leaks=sum(
            item.metrics.security.sensitive_information_leaks for item in attempts
        ),
        duplicate_external_operations=sum(
            item.metrics.security.duplicate_external_operations for item in attempts
        ),
    )


def _repeat_summary(
    configuration_id: ConfigurationId, seed: int, attempts: list[AttemptRecord]
) -> RepeatSummary:
    passed = sum(item.grade_outcome is GradeOutcome.PASSED for item in attempts)
    subgoal_total = sum(item.metrics.subgoals_total for item in attempts)
    subgoal_done = sum(item.metrics.subgoals_completed for item in attempts)
    actions = sum(item.metrics.actions_total for item in attempts)
    error_actions = sum(item.metrics.error_actions for item in attempts)
    recoverable = sum(item.metrics.recoverable_failures for item in attempts)
    recovered = sum(item.metrics.recovered_failures for item in attempts)
    return RepeatSummary(
        configuration_id=configuration_id,
        seed=seed,
        planned_attempts=18,
        status_counts=_status_counts(attempts),
        passed=passed,
        success_basis_points=_ratio(passed, 18) or 0,
        subgoal_completion_basis_points=_ratio(subgoal_done, subgoal_total) or 0,
        error_action_basis_points=_ratio(error_actions, actions) or 0,
        average_steps_milli=_mean_milli([item.metrics.steps for item in attempts], 18),
        average_plan_modifications_milli=_mean_milli(
            [item.metrics.plan_modifications for item in attempts], 18
        ),
        human_takeover_basis_points=_ratio(
            sum(item.metrics.human_takeover for item in attempts), 18
        )
        or 0,
        recovery_basis_points=_ratio(recovered, recoverable),
        synthetic_cost_microusd=sum(item.metrics.synthetic_cost_microusd for item in attempts),
    )


def _configuration_summary(
    configuration_id: ConfigurationId,
    attempts: list[AttemptRecord],
    repeats: list[RepeatSummary],
) -> ConfigurationSummary:
    passed = sum(item.grade_outcome is GradeOutcome.PASSED for item in attempts)
    subgoal_total = sum(item.metrics.subgoals_total for item in attempts)
    subgoal_done = sum(item.metrics.subgoals_completed for item in attempts)
    actions = sum(item.metrics.actions_total for item in attempts)
    error_actions = sum(item.metrics.error_actions for item in attempts)
    recoverable = sum(item.metrics.recoverable_failures for item in attempts)
    recovered = sum(item.metrics.recovered_failures for item in attempts)
    model_calls = sum(item.metrics.model_calls for item in attempts)
    vlm_calls = sum(item.metrics.vlm_calls for item in attempts)
    cache_hits = sum(item.metrics.cache_hits for item in attempts)
    cache_lookups = sum(item.metrics.cache_lookups for item in attempts)
    synthetic_cost = sum(item.metrics.synthetic_cost_microusd for item in attempts)
    repeat_success = sorted(item.success_basis_points for item in repeats)
    api = [
        item.metrics.api_latency_microseconds
        for item in attempts
        if item.metrics.api_latency_microseconds is not None
    ]
    queue = [
        item.metrics.queue_wait_microseconds
        for item in attempts
        if item.metrics.queue_wait_microseconds is not None
    ]
    return ConfigurationSummary(
        configuration_id=configuration_id,
        planned_attempts=54,
        status_counts=_status_counts(attempts),
        passed=passed,
        success_basis_points=_ratio(passed, 54) or 0,
        success_repeat_range=MedianRange(
            minimum=repeat_success[0],
            median=repeat_success[1],
            maximum=repeat_success[2],
        ),
        subgoal_completion_basis_points=_ratio(subgoal_done, subgoal_total) or 0,
        error_action_basis_points=_ratio(error_actions, actions) or 0,
        average_steps_milli=_mean_milli([item.metrics.steps for item in attempts], 54),
        average_plan_modifications_milli=_mean_milli(
            [item.metrics.plan_modifications for item in attempts], 54
        ),
        human_takeover_basis_points=_ratio(
            sum(item.metrics.human_takeover for item in attempts), 54
        )
        or 0,
        recovery_basis_points=_ratio(recovered, recoverable),
        system=SystemSummary(
            api_latency_microseconds=_percentiles(api),
            queue_wait_microseconds=_percentiles(queue),
            maximum_browser_concurrency=max(
                (item.metrics.browser_concurrency for item in attempts), default=0
            ),
            worker_recoveries=sum(item.metrics.worker_recoveries for item in attempts),
            database_lock_conflicts=sum(item.metrics.database_lock_conflicts for item in attempts),
            duplicate_business_effects=sum(
                item.metrics.duplicate_business_effects for item in attempts
            ),
        ),
        cost=CostSummary(
            model_calls=model_calls,
            input_tokens=sum(item.metrics.input_tokens for item in attempts),
            output_tokens=sum(item.metrics.output_tokens for item in attempts),
            vlm_call_basis_points=_ratio(vlm_calls, model_calls),
            cache_hit_basis_points=_ratio(cache_hits, cache_lookups),
            synthetic_cost_microusd=synthetic_cost,
            average_synthetic_cost_microusd=(synthetic_cost + 27) // 54,
        ),
        security=_sum_security(attempts),
    )


def _primary_attempts(attempts: tuple[AttemptRecord, ...]) -> list[AttemptRecord]:
    return [item for item in attempts if item.retry_ordinal == 0]


def _build_summaries(
    protocol: EvaluationProtocol, attempts: tuple[AttemptRecord, ...]
) -> tuple[tuple[RepeatSummary, ...], tuple[ConfigurationSummary, ...]]:
    primary = _primary_attempts(attempts)
    repeats: list[RepeatSummary] = []
    summaries: list[ConfigurationSummary] = []
    for configuration in protocol.configurations:
        selected = [item for item in primary if item.configuration_id is configuration.config_id]
        config_repeats: list[RepeatSummary] = []
        for seed in protocol.seeds:
            repeat = _repeat_summary(
                configuration.config_id,
                seed,
                [item for item in selected if item.seed == seed],
            )
            repeats.append(repeat)
            config_repeats.append(repeat)
        summaries.append(_configuration_summary(configuration.config_id, selected, config_repeats))
    return tuple(repeats), tuple(summaries)


def _comparisons(
    attempts: tuple[AttemptRecord, ...], summaries: tuple[ConfigurationSummary, ...]
) -> tuple[PairedComparison, ...]:
    primary = _primary_attempts(attempts)
    passed_by_config = {
        config_id: {
            (item.task_reference, item.seed): item.grade_outcome is GradeOutcome.PASSED
            for item in primary
            if item.configuration_id is config_id
        }
        for config_id in ConfigurationId
    }
    full = passed_by_config[ConfigurationId.FULL_SYSTEM]
    summary_by_id = {item.configuration_id: item for item in summaries}
    comparisons: list[PairedComparison] = []
    for compared in ConfigurationId:
        if compared is ConfigurationId.FULL_SYSTEM:
            continue
        cells = passed_by_config[compared]
        if set(cells) != set(full):
            raise ValueError("paired comparison cells differ")
        difference = sum(full[key] for key in full) - sum(cells[key] for key in full)
        comparisons.append(
            PairedComparison(
                reference_configuration_id=ConfigurationId.FULL_SYSTEM,
                compared_configuration_id=compared,
                paired_cells=54,
                success_difference_basis_points=(difference * 10_000 + 27) // 54,
            )
        )
    if summary_by_id[ConfigurationId.FULL_SYSTEM].planned_attempts != 54:
        raise ValueError("Full-system summary is incomplete")
    return tuple(comparisons)


def _pareto(summaries: tuple[ConfigurationSummary, ...]) -> tuple[ParetoPoint, ...]:
    points: list[ParetoPoint] = []
    for item in summaries:
        dominated = any(
            other.configuration_id is not item.configuration_id
            and other.success_basis_points >= item.success_basis_points
            and other.cost.average_synthetic_cost_microusd
            <= item.cost.average_synthetic_cost_microusd
            and (
                other.success_basis_points > item.success_basis_points
                or other.cost.average_synthetic_cost_microusd
                < item.cost.average_synthetic_cost_microusd
            )
            for other in summaries
        )
        points.append(
            ParetoPoint(
                configuration_id=item.configuration_id,
                success_basis_points=item.success_basis_points,
                average_synthetic_cost_microusd=item.cost.average_synthetic_cost_microusd,
                dominated=dominated,
            )
        )
    return tuple(points)


def _target_results(
    protocol: EvaluationProtocol,
    summaries: tuple[ConfigurationSummary, ...],
    comparisons: tuple[PairedComparison, ...],
) -> tuple[TargetResult, ...]:
    by_id = {item.configuration_id: item for item in summaries}
    full = by_id[ConfigurationId.FULL_SYSTEM]
    full_vs_dom = next(
        item for item in comparisons if item.compared_configuration_id is ConfigurationId.DOM_REACT
    )
    security_total = sum(item.security.total for item in summaries)
    duplicate_effects = sum(item.system.duplicate_business_effects for item in summaries)
    api_p95 = full.system.api_latency_microseconds.p95
    if api_p95 is None:
        raise ValueError("Full-system API latency is unavailable")
    recovery = full.recovery_basis_points
    return (
        TargetResult(
            target_id=TargetId.FULL_VS_DOM,
            status=(
                TargetStatus.MET
                if full_vs_dom.success_difference_basis_points
                >= protocol.targets.full_vs_dom_percentage_points * 100
                else TargetStatus.MISSED
            ),
            observed_value=full_vs_dom.success_difference_basis_points,
            threshold_value=protocol.targets.full_vs_dom_percentage_points * 100,
            comparison="at_least",
            reason="observed",
        ),
        TargetResult(
            target_id=TargetId.SINGLE_APPLICATION,
            status=TargetStatus.UNAVAILABLE,
            observed_value=None,
            threshold_value=protocol.targets.single_application_success_basis_points,
            comparison="at_least",
            reason="no_eligible_sample",
        ),
        TargetResult(
            target_id=TargetId.MULTI_APPLICATION,
            status=(
                TargetStatus.MET
                if full.success_basis_points
                >= protocol.targets.multi_application_success_basis_points
                else TargetStatus.MISSED
            ),
            observed_value=full.success_basis_points,
            threshold_value=protocol.targets.multi_application_success_basis_points,
            comparison="at_least",
            reason="observed",
        ),
        TargetResult(
            target_id=TargetId.RECOVERY,
            status=(
                TargetStatus.UNAVAILABLE
                if recovery is None
                else (
                    TargetStatus.MET
                    if recovery >= protocol.targets.recovery_rate_basis_points
                    else TargetStatus.MISSED
                )
            ),
            observed_value=recovery,
            threshold_value=protocol.targets.recovery_rate_basis_points,
            comparison="at_least",
            reason="no_eligible_sample" if recovery is None else "observed",
        ),
        TargetResult(
            target_id=TargetId.SECURITY,
            status=(
                TargetStatus.MET
                if security_total <= protocol.targets.maximum_security_failures
                else TargetStatus.MISSED
            ),
            observed_value=security_total,
            threshold_value=protocol.targets.maximum_security_failures,
            comparison="at_most",
            reason="observed",
        ),
        TargetResult(
            target_id=TargetId.DUPLICATE_EFFECTS,
            status=(
                TargetStatus.MET
                if duplicate_effects <= protocol.targets.maximum_duplicate_business_effects
                else TargetStatus.MISSED
            ),
            observed_value=duplicate_effects,
            threshold_value=protocol.targets.maximum_duplicate_business_effects,
            comparison="at_most",
            reason="observed",
        ),
        TargetResult(
            target_id=TargetId.API_P95,
            status=(
                TargetStatus.MET
                if api_p95 < protocol.targets.api_p95_limit_microseconds
                else TargetStatus.MISSED
            ),
            observed_value=api_p95,
            threshold_value=protocol.targets.api_p95_limit_microseconds,
            comparison="below",
            reason="observed",
        ),
        TargetResult(
            target_id=TargetId.BROWSER_CONCURRENCY,
            status=(
                TargetStatus.MET
                if full.system.maximum_browser_concurrency
                >= protocol.targets.minimum_browser_concurrency
                else TargetStatus.MISSED
            ),
            observed_value=full.system.maximum_browser_concurrency,
            threshold_value=protocol.targets.minimum_browser_concurrency,
            comparison="at_least",
            reason="observed",
        ),
        TargetResult(
            target_id=TargetId.REAL_CALLS,
            status=TargetStatus.MET,
            observed_value=0,
            threshold_value=protocol.targets.maximum_real_calls,
            comparison="at_most",
            reason="observed",
        ),
        TargetResult(
            target_id=TargetId.REAL_COST,
            status=TargetStatus.MET,
            observed_value=0,
            threshold_value=protocol.targets.maximum_real_cost_microusd,
            comparison="at_most",
            reason="observed",
        ),
    )


def report_hash(report: EvaluationReport) -> str:
    payload = report.model_dump(mode="json", exclude={"report_hash"})
    return canonical_hash(payload)


def build_reporting_report(
    protocol: EvaluationProtocol,
    *,
    attempts: tuple[AttemptRecord, ...] | None = None,
    schema_path: Path = REPORT_SCHEMA_PATH,
) -> EvaluationReport:
    records = generate_attempts(protocol) if attempts is None else attempts
    validate_attempt_set(protocol, records)
    primary = _primary_attempts(records)
    status_counts = _status_counts(primary)
    repeats, summaries = _build_summaries(protocol, records)
    comparisons = _comparisons(records, summaries)
    unsigned = EvaluationReport(
        schema_version="w15-evaluation-report/1.0",
        runner_version=protocol.runner_version,
        protocol_hash=protocol.protocol_hash,
        configuration_hash=protocol.configuration_hash,
        report_schema_hash=report_schema_hash(schema_path),
        w3_catalog_checksum=protocol.w3_catalog_checksum,
        w7_catalog_checksum=protocol.w7_catalog_checksum,
        w7_split_manifest_checksum=protocol.w7_split_manifest_checksum,
        w7_reporting_manifest_checksum=protocol.w7_reporting_manifest_checksum,
        evaluation_split="reporting",
        reporting_executed=True,
        validation_executed=False,
        synthetic_runner=True,
        attempt_counts=AttemptCounts(
            planned_primary=594,
            primary_records=len(primary),
            retry_records=len(records) - len(primary),
            executed_primary=sum(item.status is not AttemptStatus.MISSING for item in primary),
            status_counts=status_counts,
        ),
        attempts=records,
        repeats=repeats,
        configurations=summaries,
        comparisons=comparisons,
        pareto=_pareto(summaries),
        targets=_target_results(protocol, summaries, comparisons),
        external_benchmark=ExternalBenchmarkResult(
            benchmark_id=protocol.external_benchmark.benchmark_id,
            availability=protocol.external_benchmark.availability,
            reason=protocol.external_benchmark.reason,
            planned_attempts=0,
            executed_attempts=0,
        ),
        real_calls=RealCallCounters(),
        real_cost_microusd=0,
        sensitive_fields_present=False,
        report_hash="0" * 64,
    )
    finalized = unsigned.model_copy(update={"report_hash": report_hash(unsigned)})
    EvaluationReport.model_validate_json(canonical_bytes(finalized.model_dump(mode="json")))
    return finalized


def write_once(path: Path, payload: bytes) -> None:
    if path.exists():
        raise FileExistsError("W15 artifact already exists; overwrite is forbidden")
    path.write_bytes(payload)


def write_report(path: Path, report: EvaluationReport) -> None:
    payload = canonical_bytes(report.model_dump(mode="json"))
    if canonical_hash(report.model_dump(mode="json", exclude={"report_hash"})) != (
        report.report_hash
    ):
        raise ValueError("report hash mismatch before write")
    write_once(path, payload)


def development_smoke_summary(protocol: EvaluationProtocol) -> dict[str, object]:
    attempts = generate_attempts(
        protocol,
        instances=protocol.development_smoke_instances,
        seeds=(protocol.seeds[0],),
    )
    repeated = generate_attempts(
        protocol,
        instances=protocol.development_smoke_instances,
        seeds=(protocol.seeds[0],),
    )
    if attempts != repeated or len(attempts) != 33:
        raise ValueError("Development smoke is not deterministic")
    return {
        "schema_version": "w15-development-smoke/1.0",
        "protocol_hash": protocol.protocol_hash,
        "configuration_hash": protocol.configuration_hash,
        "attempts": len(attempts),
        "reporting_executed": False,
        "validation_executed": False,
        "external_benchmark_executed": False,
        "finished_ungraded": sum(item.terminal_status == "finished_ungraded" for item in attempts),
        "independent_grade_observations": sum(
            item.grade_outcome is not GradeOutcome.NOT_GRADED for item in attempts
        ),
        "security_failures": sum(item.metrics.security.total for item in attempts),
        "duplicate_business_effects": sum(
            item.metrics.duplicate_business_effects for item in attempts
        ),
        "real_calls": 0,
        "real_cost_microusd": 0,
        "summary_hash": canonical_hash([item.model_dump(mode="json") for item in attempts]),
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description="FlowPilot W15 deterministic evaluation")
    parser.add_argument("--mode", choices=("development", "reporting", "schema"), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    protocol = load_protocol()
    if args.mode == "schema":
        payload = canonical_bytes(report_schema_document())
        if args.output is None:
            print(payload.decode())
        else:
            args.output.write_bytes(payload)
            print(
                canonical_bytes({"schema_hash": canonical_hash(report_schema_document())}).decode()
            )
        return 0
    if args.mode == "development":
        print(canonical_bytes(development_smoke_summary(protocol)).decode())
        return 0
    if args.output is None:
        parser.error("--output is required for Reporting")
    report = build_reporting_report(protocol)
    write_report(args.output, report)
    print(
        canonical_bytes(
            {
                "schema_version": report.schema_version,
                "planned_primary": report.attempt_counts.planned_primary,
                "primary_records": report.attempt_counts.primary_records,
                "retry_records": report.attempt_counts.retry_records,
                "report_hash": report.report_hash,
                "report_schema_hash": report.report_schema_hash,
                "external_benchmark": report.external_benchmark.availability,
                "real_calls": report.real_calls.total,
                "real_cost_microusd": report.real_cost_microusd,
            }
        ).decode()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
