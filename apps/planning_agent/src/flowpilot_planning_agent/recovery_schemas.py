import hashlib
import json
from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints, field_validator, model_validator

from flowpilot_planning_agent.schemas import (
    BusinessProcess,
    Checksum,
    ProcessCategory,
    StepId,
    StrictModel,
    SuppliedValues,
    TaskId,
    TotalUsage,
)

OpaqueId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_-]{7,79}$")]
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
    planning_usage: TotalUsage


class Checkpoint(StrictModel):
    schema_version: Literal["w8-checkpoint/1.0"] = "w8-checkpoint/1.0"
    workflow_id: OpaqueId
    run_id: OpaqueId
    task_id: TaskId
    plan_hash: Checksum
    revision: int = Field(ge=1, le=2)
    topology: tuple[StepId, ...] = Field(min_length=1, max_length=16)
    completed_step_ids: tuple[StepId, ...] = Field(max_length=16)
    remaining_step_ids: tuple[StepId, ...] = Field(max_length=16)
    session_epoch: int = Field(ge=1, le=3)
    absolute_deadline_ms: int = Field(gt=0)
    usage: DurableUsage
    receipt_hashes: tuple[Checksum, ...] = Field(max_length=24)
    closed_reason: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    parent_checkpoint_hash: Checksum
    checkpoint_hash: Checksum

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


class PlanningRecoveryActivity(StrictModel):
    schema_version: Literal["w8-planning-activity/1.0"] = "w8-planning-activity/1.0"
    command: Literal["start", "step", "refresh", "recover", "replan", "cleanup"]
    workflow_id: OpaqueId
    run_id: OpaqueId
    task_id: TaskId
    process: BusinessProcess
    category: ProcessCategory
    human_brief: Annotated[str, StringConstraints(min_length=1, max_length=4_000)]
    supplied_values: SuppliedValues
    fault_scenario: FaultScenario
    checkpoint: Checkpoint | None = None
    step_id: StepId | None = None
    session_epoch: int = Field(ge=1, le=3)
    revision: int = Field(ge=1, le=2)

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        if (
            self.category != f"standard_{self.process}"
            or self.supplied_values.process != self.process
        ):
            raise ValueError("process, category, and supplied values must match")
        if self.command in {"step", "refresh", "replan"} and self.step_id is None:
            raise ValueError("command requires step_id")
        return self


class ReceiptRecord(StrictModel):
    idempotency_key: Annotated[str, StringConstraints(pattern=r"^op_[0-9a-f]{64}$")]
    request_hash: Checksum
    result_hash: Checksum
    state: Literal["none", "created", "replayed", "mismatch"]


class PlanningActivityResult(StrictModel):
    schema_version: Literal["w8-activity-result/1.0"] = "w8-activity-result/1.0"
    outcome: ActivityOutcome
    safe_reason: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    plan_hash: Checksum | None = None
    topology: tuple[StepId, ...] = Field(default=(), max_length=16)
    step_id: StepId | None = None
    session_epoch: int = Field(ge=1, le=3)
    revision: int = Field(ge=1, le=2)
    receipt: ReceiptRecord | None = None
    replaced_step_ids: tuple[StepId, ...] = Field(default=(), max_length=16)
    activity_attempt: int = Field(default=1, ge=1, le=2)
    planning_usage: TotalUsage | None = None


def validate_checkpoint(checkpoint: Checkpoint) -> None:
    canonical = json.dumps(
        checkpoint.model_dump(mode="json", exclude={"checkpoint_hash"}),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    if hashlib.sha256(canonical).hexdigest() != checkpoint.checkpoint_hash:
        raise ValueError("checkpoint hash mismatch")
