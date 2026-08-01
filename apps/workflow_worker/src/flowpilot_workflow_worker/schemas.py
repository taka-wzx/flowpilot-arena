"""Strict closed schemas shared by W12 dispatch and Temporal client."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
OpaqueId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_-]{7,79}$")]
TaskId = Literal[
    "w7-jml-joiner-001-v1",
    "w7-jml-joiner-001-v2",
    "w7-jml-joiner-002-v1",
    "w7-jml-joiner-002-v2",
    "w7-jml-mover-001-v1",
    "w7-jml-mover-001-v2",
    "w7-jml-leaver-001-v1",
    "w7-jml-leaver-001-v2",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class WorkItem(StrictModel):
    schema_version: Literal["w12-work-item/1.0"] = "w12-work-item/1.0"
    organization_id: OpaqueId
    outbox_id: OpaqueId
    run_id: OpaqueId
    executor_user_id: OpaqueId
    task_id: TaskId
    process: Literal["joiner", "mover", "leaver"]
    category: Literal["standard_joiner", "standard_mover", "standard_leaver"]
    action_type: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,63}$")]
    parameter_hash: Sha256
    authorization_hash: Sha256
    approval_request_id: OpaqueId | None = None
    grant_id: OpaqueId | None = None
    execution_id: OpaqueId | None = None
    approval_set_hash: Sha256 | None = None
    payload_reference: OpaqueId
    payload_hash: Sha256
    workflow_id: OpaqueId
    workflow_hash: Sha256
    worker_owner_hash: Sha256
    fencing_token: int = Field(ge=1)
    lease_version: int = Field(ge=1)
    attempt_count: int = Field(ge=1, le=3)
    leased_at: datetime
    lease_expires_at: datetime

    @field_validator("leased_at", "lease_expires_at", mode="before")
    @classmethod
    def timestamp_is_utc(cls, value: object) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime):
            raise ValueError("timestamp must be UTC")
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class OpaqueEnvelope(StrictModel):
    schema_version: Literal["w8-opaque-envelope/1.0"] = "w8-opaque-envelope/1.0"
    key_id: Literal["w8-local-runtime-key/1"] = "w8-local-runtime-key/1"
    nonce: Annotated[
        str, StringConstraints(pattern=r"^[A-Za-z0-9+/]+={0,2}$", min_length=16, max_length=64)
    ]
    ciphertext: Annotated[
        str,
        StringConstraints(pattern=r"^[A-Za-z0-9+/]+={0,2}$", min_length=16, max_length=16_384),
    ]
    associated_data_hash: Sha256


class WorkflowStart(StrictModel):
    schema_version: Literal["w8-workflow-start/1.0"] = "w8-workflow-start/1.0"
    workflow_id: OpaqueId
    run_id: OpaqueId
    task_id: TaskId
    envelope: OpaqueEnvelope
    fault_scenario: Literal["none"] = "none"
    fault_seed: Literal[8008] = 8008
    budget: dict[str, int] = Field(
        default_factory=lambda: {
            "max_activity_attempts": 2,
            "max_session_recoveries": 2,
            "max_replans": 1,
            "max_revisions": 2,
            "max_checkpoints": 18,
            "max_receipts": 24,
            "max_faults": 2,
            "max_duration_seconds": 300,
        }
    )


class WorkflowResult(StrictModel):
    schema_version: Literal["w8-workflow-result/1.0"] = "w8-workflow-result/1.0"
    workflow_id: OpaqueId
    run_id: OpaqueId
    task_id: TaskId
    status: Literal["finished_ungraded", "escalated", "failed", "cancelled"]
    terminal_reason: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    plan_hash: Sha256 | None
    revision: int = Field(ge=1, le=2)
    session_epoch: int = Field(ge=1, le=3)
    completed_step_ids: tuple[Annotated[str, StringConstraints(max_length=40)], ...] = Field(
        max_length=16
    )
    checkpoint_count: int = Field(ge=0, le=18)
    latest_checkpoint_hash: Sha256 | None
    usage: dict[str, object]

    @field_validator("completed_step_ids", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class TemporalOutcome(StrictModel):
    result: WorkflowResult
    deduplicated_start: bool


def _jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def canonical_json_bytes(value: BaseModel | dict[str, object]) -> bytes:
    return json.dumps(
        _jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def stable_hash(value: BaseModel | dict[str, object] | str) -> str:
    encoded = value.encode() if isinstance(value, str) else canonical_json_bytes(value)
    return hashlib.sha256(encoded).hexdigest()
