from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

TaskId = Annotated[
    str,
    StringConstraints(
        pattern=r"^(?:w3-joiner-00[1-5]|w7-jml-(?:joiner|mover|leaver)-[0-9]{3}-v[123])$",
        max_length=40,
    ),
]
RunId = Annotated[str, StringConstraints(pattern=r"^run_[A-Za-z0-9_-]{8,64}$")]
StepId = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,39}$")]
Checksum = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
BusinessProcess = Literal["joiner", "mover", "leaver"]
ProcessCategory = Literal["standard_joiner", "standard_mover", "standard_leaver"]
Page = Literal["hris", "itsm", "iam", "assets", "mail"]
Modality = Literal["dom", "vision"]
Operation = Literal[
    "inspect_employee",
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
    "finalize",
]
RequiredContext = Literal[
    "human_brief", "supplied_values", "current_observation", "current_action_result"
]
AllowedAction = Literal[
    "navigate", "click", "fill", "select", "read", "scroll", "wait", "finish", "fail"
]
Condition = Literal[
    "dependencies_verified",
    "budget_available",
    "current_session",
    "action_succeeded",
    "expected_page_observed",
]
RiskLevel = Literal["low", "medium", "high"]
RetryPolicy = Literal["no_retry"]
Fallback = Literal["stop", "escalate"]
StepState = Literal["pending", "ready", "executing", "verified", "blocked", "failed", "escalated"]
VerifierStatus = Literal["verified", "not_verified", "inconclusive"]
VerifierReason = Literal[
    "conditions_satisfied",
    "action_failed",
    "page_mismatch",
    "observation_missing",
    "forced_inconclusive",
    "budget_exhausted",
]
ToolRejectionReason = Literal[
    "unknown_tool", "step_disallowed", "page_disallowed", "modality_disallowed", "budget_exhausted"
]
PlanValidationReason = Literal[
    "duplicate_step_id",
    "self_dependency",
    "unknown_dependency",
    "multiple_roots",
    "cycle",
    "unreachable_node",
    "node_limit",
    "edge_limit",
    "depth_limit",
    "width_limit",
    "dependency_limit",
    "byte_limit",
    "operation_page_mismatch",
    "operation_action_mismatch",
]
BudgetReason = Literal[
    "time_budget_exhausted",
    "plan_generation_budget_exhausted",
    "tool_match_budget_exhausted",
    "tool_rejection_budget_exhausted",
    "verifier_budget_exhausted",
    "verifier_probe_budget_exhausted",
    "executed_step_budget_exhausted",
    "blocked_step_budget_exhausted",
    "action_budget_exhausted",
    "model_call_budget_exhausted",
    "dom_observation_budget_exhausted",
    "dom_byte_budget_exhausted",
    "compressed_dom_budget_exhausted",
    "input_token_budget_exhausted",
    "output_token_budget_exhausted",
    "cost_budget_exhausted",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class JoinerSuppliedValues(StrictModel):
    process: Literal["joiner"] = "joiner"
    employee_id: int = Field(gt=0, le=999_999_999)
    ticket_title: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    username: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9.]{2,79}$")]
    asset_tag: Annotated[str, StringConstraints(pattern=r"^SYN-[A-Z0-9-]+$", max_length=80)]
    laptop_model: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    mailbox: Annotated[
        str, StringConstraints(pattern=r"^[a-z0-9._+-]+@[a-z0-9.-]+\.invalid$", max_length=255)
    ]


class MoverSuppliedValues(StrictModel):
    process: Literal["mover"] = "mover"
    employee_id: int = Field(gt=0, le=999_999_999)
    new_department: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    new_job_title: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    new_location: Annotated[str, StringConstraints(min_length=1, max_length=120)]


class LeaverSuppliedValues(StrictModel):
    process: Literal["leaver"] = "leaver"
    employee_id: int = Field(gt=0, le=999_999_999)


SuppliedValues = Annotated[
    JoinerSuppliedValues | MoverSuppliedValues | LeaverSuppliedValues,
    Field(discriminator="process"),
]


class PlanStep(StrictModel):
    step_id: StepId
    objective: Annotated[str, StringConstraints(min_length=1, max_length=240)]
    dependencies: tuple[StepId, ...] = Field(max_length=8)
    operation: Operation
    expected_page: Page
    required_context: tuple[RequiredContext, ...] = Field(min_length=1, max_length=8)
    allowed_actions: tuple[AllowedAction, ...] = Field(min_length=1, max_length=9)
    preconditions: tuple[Condition, ...] = Field(min_length=1, max_length=8)
    postconditions: tuple[Condition, ...] = Field(min_length=1, max_length=8)
    risk_level: RiskLevel
    retry_policy: RetryPolicy = "no_retry"
    fallback: Fallback

    @field_validator(
        "dependencies",
        "required_context",
        "allowed_actions",
        "preconditions",
        "postconditions",
        mode="before",
    )
    @classmethod
    def accept_json_arrays(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class PlanningDag(StrictModel):
    schema_version: Literal["w7-planning-dag/1.0"] = "w7-planning-dag/1.0"
    process: BusinessProcess
    category: ProcessCategory
    steps: tuple[PlanStep, ...] = Field(min_length=1, max_length=32)

    @field_validator("steps", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class PlanRequest(StrictModel):
    schema_version: Literal["w7-plan-request/1.0"] = "w7-plan-request/1.0"
    process: BusinessProcess
    category: ProcessCategory
    human_brief: Annotated[str, StringConstraints(min_length=1, max_length=4_000)]
    supplied_values: SuppliedValues

    @model_validator(mode="after")
    def validate_process(self) -> Self:
        if (
            self.supplied_values.process != self.process
            or self.category != f"standard_{self.process}"
        ):
            raise ValueError("process, category, and supplied values must match")
        return self


class PlanResult(StrictModel):
    schema_version: Literal["w7-plan-result/1.0"] = "w7-plan-result/1.0"
    plan_id: Checksum
    dag: PlanningDag


class PlanValidationResult(StrictModel):
    schema_version: Literal["w7-plan-validation-result/1.0"] = "w7-plan-validation-result/1.0"
    valid: bool
    reason_codes: tuple[PlanValidationReason, ...]
    plan_id: Checksum | None = None
    node_count: int = Field(ge=0, le=32)
    edge_count: int = Field(ge=0)
    depth: int = Field(ge=0)
    width: int = Field(ge=0)
    serialized_bytes: int = Field(ge=0)
    topology: tuple[StepId, ...]


class ToolMatchRequest(StrictModel):
    schema_version: Literal["w7-tool-match-request/1.0"] = "w7-tool-match-request/1.0"
    step_id: StepId
    candidate: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    page: Page
    modality: Modality


class ToolMatchResult(StrictModel):
    schema_version: Literal["w7-tool-match-result/1.0"] = "w7-tool-match-result/1.0"
    matched: bool
    action: AllowedAction | None = None
    rejection_reason: ToolRejectionReason | None = None

    @model_validator(mode="after")
    def validate_outcome(self) -> Self:
        if self.matched != (self.action is not None and self.rejection_reason is None):
            raise ValueError("tool match result fields are inconsistent")
        return self


class VerifierRequest(StrictModel):
    schema_version: Literal["w7-verifier-request/1.0"] = "w7-verifier-request/1.0"
    step_id: StepId
    expected_page: Page
    current_page: Page | None
    observation_generation: int | None = Field(default=None, ge=1, le=24)
    action_success: bool
    postconditions: tuple[Condition, ...] = Field(min_length=1, max_length=8)
    force_inconclusive: bool = False


class VerifierResult(StrictModel):
    schema_version: Literal["w7-verifier-result/1.0"] = "w7-verifier-result/1.0"
    step_id: StepId
    status: VerifierStatus
    reason_code: VerifierReason


class StepExecutionResult(StrictModel):
    schema_version: Literal["w7-step-execution-result/1.0"] = "w7-step-execution-result/1.0"
    step_id: StepId
    state: StepState
    action_count: int = Field(ge=0, le=24)
    verifier: VerifierResult | None = None


class TotalBudget(StrictModel):
    max_plan_generations: int = Field(default=1, ge=1, le=1)
    max_tool_matches: int = Field(default=64, ge=1, le=64)
    max_tool_rejections: int = Field(default=16, ge=0, le=16)
    max_verifier_calls: int = Field(default=16, ge=1, le=16)
    max_verifier_probes: int = Field(default=16, ge=1, le=16)
    max_executed_steps: int = Field(default=16, ge=1, le=16)
    max_blocked_steps: int = Field(default=16, ge=1, le=16)
    max_steps: int = Field(default=24, ge=1, le=24)
    max_model_calls: int = Field(default=24, ge=1, le=24)
    max_switches: int = Field(default=2, ge=0, le=2)
    max_dom_observations: int = Field(default=24, ge=1, le=24)
    max_dom_observation_bytes: int = Field(default=262_144, ge=1, le=262_144)
    max_compressed_dom_bytes: int = Field(default=147_456, ge=1, le=147_456)
    max_images: int = Field(default=24, ge=1, le=24)
    max_image_bytes: int = Field(default=4_423_680, ge=1, le=4_423_680)
    max_image_pixels: int = Field(default=12_441_600, ge=1, le=12_441_600)
    max_capture_ms: int = Field(default=72_000, ge=1, le=72_000)
    max_input_tokens: int = Field(default=100_000, ge=1, le=100_000)
    max_output_tokens: int = Field(default=20_000, ge=1, le=20_000)
    max_planning_input_tokens: int = Field(default=100_000, ge=1, le=100_000)
    max_planning_output_tokens: int = Field(default=20_000, ge=1, le=20_000)
    max_verifier_input_tokens: int = Field(default=100_000, ge=1, le=100_000)
    max_verifier_output_tokens: int = Field(default=20_000, ge=1, le=20_000)
    max_cost_microusd: int = Field(default=0, ge=0, le=1_000_000)
    max_planning_cost_microusd: int = Field(default=0, ge=0, le=1_000_000)
    max_verifier_cost_microusd: int = Field(default=0, ge=0, le=1_000_000)
    max_duration_seconds: int = Field(default=300, ge=1, le=300)


class TotalUsage(StrictModel):
    plan_generations: int = Field(ge=0)
    plan_nodes: int = Field(ge=0)
    plan_edges: int = Field(ge=0)
    plan_depth: int = Field(ge=0)
    plan_serialized_bytes: int = Field(ge=0)
    tool_matches: int = Field(ge=0)
    tool_rejections: int = Field(ge=0)
    verifier_calls: int = Field(ge=0)
    verifier_probes: int = Field(ge=0)
    executed_steps: int = Field(ge=0)
    blocked_steps: int = Field(ge=0)
    worker_actions: int = Field(ge=0)
    model_calls: int = Field(ge=0)
    switches: int = Field(ge=0)
    route_decisions: int = Field(ge=0)
    dom_observations: int = Field(ge=0)
    dom_observation_bytes: int = Field(ge=0)
    compressed_dom_bytes: int = Field(ge=0)
    images: int = Field(ge=0)
    image_bytes: int = Field(ge=0)
    image_pixels: int = Field(ge=0)
    capture_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    planning_input_tokens: int = Field(ge=0)
    planning_output_tokens: int = Field(ge=0)
    verifier_input_tokens: int = Field(ge=0)
    verifier_output_tokens: int = Field(ge=0)
    cost_microusd: int = Field(ge=0)
    planning_cost_microusd: int = Field(ge=0)
    verifier_cost_microusd: int = Field(ge=0)
    elapsed_ms: int = Field(ge=0)


PlanningRunStatus = Literal[
    "finished_ungraded",
    "failed",
    "escalated",
    "invalid_plan",
    "dependency_blocked",
    "tool_rejected",
    "verification_not_verified",
    "verification_inconclusive",
    "budget_exhausted",
    "browser_error",
]


class PlanningRunRequest(StrictModel):
    schema_version: Literal["w7-planning-run/1.0"] = "w7-planning-run/1.0"
    run_id: RunId
    task_id: TaskId
    process: BusinessProcess
    category: ProcessCategory
    human_brief: Annotated[str, StringConstraints(min_length=1, max_length=4_000)]
    supplied_values: SuppliedValues
    fake_scenario: Literal[
        "complete_with_rejection_probe",
        "finish_immediately",
        "verifier_inconclusive",
        "out_of_order_probe",
    ] = "complete_with_rejection_probe"
    budget: TotalBudget = TotalBudget()

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        PlanRequest(
            process=self.process,
            category=self.category,
            human_brief=self.human_brief,
            supplied_values=self.supplied_values,
        )
        return self


class PlanningRunResult(StrictModel):
    schema_version: Literal["w7-planning-result/1.0"] = "w7-planning-result/1.0"
    run_id: RunId
    task_id: TaskId
    status: PlanningRunStatus
    terminal_reason: Annotated[str, StringConstraints(min_length=1, max_length=300)]
    plan_id: Checksum | None
    topology: tuple[StepId, ...] = Field(max_length=16)
    step_results: tuple[StepExecutionResult, ...] = Field(max_length=16)
    tool_rejection_reasons: tuple[ToolRejectionReason, ...] = Field(max_length=16)
    usage: TotalUsage
