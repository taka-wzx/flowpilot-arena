import hashlib
import json
from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

OpaqueId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_-]{7,79}$")]
TaskId = Annotated[
    str,
    StringConstraints(
        pattern=r"^(?:w3-joiner-00[1-5]|w7-jml-(?:joiner|mover|leaver)-[0-9]{3}-v[123])$",
        max_length=40,
    ),
]
StepId = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,39}$")]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Base64Text = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z0-9_-]+={0,2}$", min_length=16, max_length=16_384)
]
FaultScenario = Literal[
    "none",
    "activity_pre_dispatch_once",
    "post_commit_pre_checkpoint_once",
    "browser_session_lost_once",
    "browser_worker_restart_once",
    "recovery_worker_restart_once",
    "transient_timeout_once",
    "permanent_failure",
    "checkpoint_version_mismatch",
    "checkpoint_hash_mismatch",
    "idempotency_mismatch",
    "replan_eligible_once",
    "replan_disallowed",
]
ActivityOutcome = Literal[
    "started",
    "verified",
    "session_lost",
    "replan_eligible",
    "permanent_failure",
    "idempotency_mismatch",
    "cleaned",
]
ReceiptState = Literal["none", "created", "replayed", "mismatch"]
TerminalReason = Literal[
    "completed",
    "permanent_failure",
    "budget_exhausted",
    "checkpoint_invalid",
    "idempotency_mismatch",
    "replan_disallowed",
    "recovery_exhausted",
    "cancelled",
]
WorkflowTerminalStatus = Literal["finished_ungraded", "escalated", "failed", "cancelled"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class OpaqueEnvelope(StrictModel):
    schema_version: Literal["w8-opaque-envelope/1.0"] = "w8-opaque-envelope/1.0"
    key_id: Literal["w8-local-runtime-key/1"] = "w8-local-runtime-key/1"
    nonce: Base64Text
    ciphertext: Base64Text
    associated_data_hash: Sha256


class WorkflowBudget(StrictModel):
    max_activity_attempts: int = Field(default=2, ge=1, le=2)
    max_session_recoveries: int = Field(default=2, ge=0, le=2)
    max_replans: int = Field(default=1, ge=0, le=1)
    max_revisions: int = Field(default=2, ge=1, le=2)
    max_checkpoints: int = Field(default=18, ge=1, le=18)
    max_receipts: int = Field(default=24, ge=1, le=24)
    max_faults: int = Field(default=2, ge=0, le=2)
    max_duration_seconds: int = Field(default=300, ge=1, le=300)


class WorkflowStart(StrictModel):
    schema_version: Literal["w8-workflow-start/1.0"] = "w8-workflow-start/1.0"
    workflow_id: OpaqueId
    run_id: OpaqueId
    task_id: TaskId
    envelope: OpaqueEnvelope
    fault_scenario: FaultScenario = "none"
    fault_seed: int = Field(default=8_008, ge=8_008, le=8_008)
    budget: WorkflowBudget = WorkflowBudget()


class PlainRunInput(StrictModel):
    schema_version: Literal["w8-plain-run-input/1.0"] = "w8-plain-run-input/1.0"
    workflow_id: OpaqueId
    run_id: OpaqueId
    task_id: TaskId
    process: Literal["joiner", "mover", "leaver"]
    category: Literal["standard_joiner", "standard_mover", "standard_leaver"]
    human_brief: Annotated[str, StringConstraints(min_length=1, max_length=4_000)]
    supplied_values: dict[str, object]

    @model_validator(mode="after")
    def validate_category(self) -> Self:
        if self.category != f"standard_{self.process}":
            raise ValueError("process and category must match")
        return self


class PlanningUsage(StrictModel):
    plan_generations: int = Field(default=0, ge=0)
    plan_nodes: int = Field(default=0, ge=0)
    plan_edges: int = Field(default=0, ge=0)
    plan_depth: int = Field(default=0, ge=0)
    plan_serialized_bytes: int = Field(default=0, ge=0)
    tool_matches: int = Field(default=0, ge=0)
    tool_rejections: int = Field(default=0, ge=0)
    verifier_calls: int = Field(default=0, ge=0)
    verifier_probes: int = Field(default=0, ge=0)
    executed_steps: int = Field(default=0, ge=0)
    blocked_steps: int = Field(default=0, ge=0)
    worker_actions: int = Field(default=0, ge=0)
    model_calls: int = Field(default=0, ge=0)
    switches: int = Field(default=0, ge=0)
    route_decisions: int = Field(default=0, ge=0)
    dom_observations: int = Field(default=0, ge=0)
    dom_observation_bytes: int = Field(default=0, ge=0)
    compressed_dom_bytes: int = Field(default=0, ge=0)
    images: int = Field(default=0, ge=0)
    image_bytes: int = Field(default=0, ge=0)
    image_pixels: int = Field(default=0, ge=0)
    capture_ms: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    planning_input_tokens: int = Field(default=0, ge=0)
    planning_output_tokens: int = Field(default=0, ge=0)
    verifier_input_tokens: int = Field(default=0, ge=0)
    verifier_output_tokens: int = Field(default=0, ge=0)
    cost_microusd: int = Field(default=0, ge=0)
    planning_cost_microusd: int = Field(default=0, ge=0)
    verifier_cost_microusd: int = Field(default=0, ge=0)
    elapsed_ms: int = Field(default=0, ge=0)


class DurableUsage(StrictModel):
    activity_attempts: int = Field(default=0, ge=0, le=64)
    retries: int = Field(default=0, ge=0, le=16)
    session_recoveries: int = Field(default=0, ge=0, le=2)
    receipt_creates: int = Field(default=0, ge=0, le=24)
    receipt_replays: int = Field(default=0, ge=0, le=24)
    receipt_mismatches: int = Field(default=0, ge=0, le=24)
    duplicate_side_effects: int = Field(default=0, ge=0, le=24)
    faults: int = Field(default=0, ge=0, le=2)
    replans: int = Field(default=0, ge=0, le=1)
    replaced_nodes: int = Field(default=0, ge=0, le=16)
    workflow_replays: int = Field(default=0, ge=0, le=16)
    planning_usage: PlanningUsage = PlanningUsage()


class ReceiptRecord(StrictModel):
    idempotency_key: Annotated[str, StringConstraints(pattern=r"^op_[0-9a-f]{64}$", max_length=67)]
    request_hash: Sha256
    result_hash: Sha256
    state: ReceiptState


class Checkpoint(StrictModel):
    schema_version: Literal["w8-checkpoint/1.0"] = "w8-checkpoint/1.0"
    workflow_id: OpaqueId
    run_id: OpaqueId
    task_id: TaskId
    plan_hash: Sha256
    revision: int = Field(ge=1, le=2)
    topology: tuple[StepId, ...] = Field(min_length=1, max_length=16)
    completed_step_ids: tuple[StepId, ...] = Field(max_length=16)
    remaining_step_ids: tuple[StepId, ...] = Field(max_length=16)
    session_epoch: int = Field(ge=1, le=3)
    absolute_deadline_ms: int = Field(gt=0)
    usage: DurableUsage
    receipt_hashes: tuple[Sha256, ...] = Field(max_length=24)
    closed_reason: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    parent_checkpoint_hash: Sha256
    checkpoint_hash: Sha256

    @field_validator(
        "topology",
        "completed_step_ids",
        "remaining_step_ids",
        "receipt_hashes",
        mode="before",
    )
    @classmethod
    def accept_json_arrays(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class ActivityRequest(StrictModel):
    schema_version: Literal["w8-activity-request/1.0"] = "w8-activity-request/1.0"
    start: WorkflowStart
    checkpoint: Checkpoint | None = None
    step_id: StepId | None = None
    session_epoch: int = Field(default=1, ge=1, le=3)
    revision: int = Field(default=1, ge=1, le=2)


class ActivityResult(StrictModel):
    schema_version: Literal["w8-activity-result/1.0"] = "w8-activity-result/1.0"
    outcome: ActivityOutcome
    safe_reason: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    plan_hash: Sha256 | None = None
    topology: tuple[StepId, ...] = Field(default=(), max_length=16)
    step_id: StepId | None = None
    session_epoch: int = Field(ge=1, le=3)
    revision: int = Field(ge=1, le=2)
    receipt: ReceiptRecord | None = None
    replaced_step_ids: tuple[StepId, ...] = Field(default=(), max_length=16)
    activity_attempt: int = Field(default=1, ge=1, le=2)
    planning_usage: PlanningUsage | None = None

    @field_validator("topology", "replaced_step_ids", mode="before")
    @classmethod
    def accept_json_arrays(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class WorkflowResult(StrictModel):
    schema_version: Literal["w8-workflow-result/1.0"] = "w8-workflow-result/1.0"
    workflow_id: OpaqueId
    run_id: OpaqueId
    task_id: TaskId
    status: WorkflowTerminalStatus
    terminal_reason: TerminalReason
    plan_hash: Sha256 | None
    revision: int = Field(ge=1, le=2)
    session_epoch: int = Field(ge=1, le=3)
    completed_step_ids: tuple[StepId, ...] = Field(max_length=16)
    checkpoint_count: int = Field(ge=0, le=18)
    latest_checkpoint_hash: Sha256 | None
    usage: DurableUsage

    @field_validator("completed_step_ids", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


def canonical_json_bytes(value: BaseModel | dict[str, object]) -> bytes:
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_checkpoint(
    *,
    start: WorkflowStart,
    plan_hash: str,
    revision: int,
    topology: tuple[str, ...],
    completed: tuple[str, ...],
    remaining: tuple[str, ...],
    session_epoch: int,
    deadline: datetime,
    usage: DurableUsage,
    receipt_hashes: tuple[str, ...],
    reason: str,
    parent_hash: str,
) -> Checkpoint:
    fields: dict[str, object] = {
        "schema_version": "w8-checkpoint/1.0",
        "workflow_id": start.workflow_id,
        "run_id": start.run_id,
        "task_id": start.task_id,
        "plan_hash": plan_hash,
        "revision": revision,
        "topology": topology,
        "completed_step_ids": completed,
        "remaining_step_ids": remaining,
        "session_epoch": session_epoch,
        "absolute_deadline_ms": int(deadline.timestamp() * 1_000),
        "usage": usage.model_dump(mode="json"),
        "receipt_hashes": receipt_hashes,
        "closed_reason": reason,
        "parent_checkpoint_hash": parent_hash,
    }
    checkpoint_hash = sha256_hex(canonical_json_bytes(fields))
    checkpoint = Checkpoint.model_validate({**fields, "checkpoint_hash": checkpoint_hash})
    if len(canonical_json_bytes(checkpoint)) > 65_536:
        raise ValueError("checkpoint exceeds canonical byte cap")
    return checkpoint


def validate_checkpoint(checkpoint: Checkpoint) -> None:
    fields = checkpoint.model_dump(mode="json", exclude={"checkpoint_hash"})
    if sha256_hex(canonical_json_bytes(fields)) != checkpoint.checkpoint_hash:
        raise ValueError("checkpoint hash mismatch")
    completed = set(checkpoint.completed_step_ids)
    remaining = set(checkpoint.remaining_step_ids)
    if completed & remaining:
        raise ValueError("checkpoint step sets overlap")
    if completed | remaining != set(checkpoint.topology):
        raise ValueError("checkpoint step sets do not cover topology")
    if (
        tuple(step for step in checkpoint.topology if step in completed)
        != checkpoint.completed_step_ids
    ):
        raise ValueError("completed steps must preserve topology")
    if (
        tuple(step for step in checkpoint.topology if step in remaining)
        != checkpoint.remaining_step_ids
    ):
        raise ValueError("remaining steps must preserve topology")
