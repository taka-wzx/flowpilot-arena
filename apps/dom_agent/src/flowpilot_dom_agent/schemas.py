from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ObservationId = Annotated[str, StringConstraints(pattern=r"^obs_[A-Za-z0-9_-]{8,64}$")]
ElementRef = Annotated[str, StringConstraints(pattern=r"^ref_[A-Za-z0-9_-]{8,80}$")]
ActionId = Annotated[str, StringConstraints(pattern=r"^act_[A-Za-z0-9_-]{1,64}$")]
SessionId = Annotated[str, StringConstraints(pattern=r"^bw_[A-Za-z0-9_-]{16,64}$")]
TaskId = Literal[
    "w3-joiner-001",
    "w3-joiner-002",
    "w3-joiner-003",
    "w3-joiner-004",
    "w3-joiner-005",
]
ActionType = Literal[
    "navigate", "click", "fill", "select", "read", "scroll", "wait", "finish", "fail"
]
ErrorCategory = Literal[
    "invalid_url",
    "stale_element_ref",
    "unknown_element_ref",
    "action_not_allowed",
    "action_budget_exhausted",
    "navigation_budget_exhausted",
    "session_timeout",
    "wait_limit_exceeded",
    "input_rejected",
    "browser_timeout",
    "browser_error",
    "session_closed",
    "internal_error",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ElementState(StrictModel):
    disabled: bool = False
    checked: bool | None = None
    selected: bool | None = None
    expanded: bool | None = None
    readonly: bool = False
    required: bool = False


class SemanticNode(StrictModel):
    role: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    name: Annotated[str, StringConstraints(max_length=240)]
    text: Annotated[str, StringConstraints(max_length=240)]


class InteractiveElement(StrictModel):
    element_ref: ElementRef
    role: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    name: Annotated[str, StringConstraints(max_length=240)]
    state: ElementState
    allowed_actions: tuple[Literal["click", "fill", "select", "read", "scroll"], ...]
    options: tuple[Annotated[str, StringConstraints(min_length=1, max_length=120)], ...] = ()


class LastAction(StrictModel):
    action_id: ActionId
    action_type: ActionType
    success: bool
    error_category: ErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=300)]


class Observation(StrictModel):
    schema_version: Literal["w4-dom-observation/1.0"]
    session_id: SessionId
    observation_id: ObservationId
    current_url: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    page_title: Annotated[str, StringConstraints(max_length=200)]
    semantic_nodes: tuple[SemanticNode, ...]
    interactive_elements: tuple[InteractiveElement, ...]
    last_action: LastAction | None = None
    page_error: Annotated[str, StringConstraints(max_length=300)] | None = None
    truncated: bool


class NavigateAction(StrictModel):
    schema_version: Literal["w4-dom-action/1.0"] = "w4-dom-action/1.0"
    action_id: ActionId
    type: Literal["navigate"]
    url: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class ElementAction(StrictModel):
    schema_version: Literal["w4-dom-action/1.0"] = "w4-dom-action/1.0"
    action_id: ActionId
    observation_id: ObservationId
    element_ref: ElementRef


class ClickAction(ElementAction):
    type: Literal["click"]


class FillAction(ElementAction):
    type: Literal["fill"]
    text: Annotated[str, StringConstraints(max_length=300)]


class SelectAction(ElementAction):
    type: Literal["select"]
    option: Annotated[str, StringConstraints(min_length=1, max_length=120)]


class ReadAction(ElementAction):
    type: Literal["read"]


class ScrollAction(ElementAction):
    type: Literal["scroll"]
    direction: Literal["up", "down"]
    amount: Literal["small", "page"] = "small"


class WaitAction(StrictModel):
    schema_version: Literal["w4-dom-action/1.0"] = "w4-dom-action/1.0"
    action_id: ActionId
    type: Literal["wait"]
    duration_ms: int = Field(ge=1, le=5_000)


class FinishAction(StrictModel):
    schema_version: Literal["w4-dom-action/1.0"] = "w4-dom-action/1.0"
    action_id: ActionId
    type: Literal["finish"]
    summary: Annotated[str, StringConstraints(max_length=300)] = ""


class FailAction(StrictModel):
    schema_version: Literal["w4-dom-action/1.0"] = "w4-dom-action/1.0"
    action_id: ActionId
    type: Literal["fail"]
    category: Literal["failed", "escalated"]
    reason: Annotated[str, StringConstraints(min_length=1, max_length=300)]


type BrowserAction = Annotated[
    NavigateAction
    | ClickAction
    | FillAction
    | SelectAction
    | ReadAction
    | ScrollAction
    | WaitAction
    | FinishAction
    | FailAction,
    Field(discriminator="type"),
]


class SessionCreated(StrictModel):
    schema_version: Literal["w4-browser-session/1.0"]
    session_id: SessionId
    observation: Observation


class ActionResult(StrictModel):
    schema_version: Literal["w4-dom-action-result/1.0"]
    session_id: SessionId
    action_id: ActionId
    action_type: ActionType
    success: bool
    terminal: bool
    error_category: ErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=300)]
    observation: Observation | None = None


class ModelDecision(StrictModel):
    schema_version: Literal["w4-model-decision/1.0"] = "w4-model-decision/1.0"
    action: BrowserAction


class ModelUsage(StrictModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_microusd: int = Field(ge=0)


class AgentBudget(StrictModel):
    max_steps: int = Field(default=12, ge=1, le=50)
    max_model_calls: int = Field(default=12, ge=1, le=50)
    max_repeated_actions: int = Field(default=2, ge=1, le=5)
    max_no_progress: int = Field(default=3, ge=1, le=8)
    max_duration_seconds: int = Field(default=120, ge=1, le=300)
    max_input_tokens: int = Field(default=20_000, ge=1, le=100_000)
    max_output_tokens: int = Field(default=5_000, ge=1, le=20_000)
    max_cost_microusd: int = Field(default=0, ge=0, le=1_000_000)


class AgentRunRequest(StrictModel):
    schema_version: Literal["w4-dom-agent-run/1.0"] = "w4-dom-agent-run/1.0"
    task_id: TaskId
    instruction: Annotated[str, StringConstraints(min_length=1, max_length=4_000)]
    model: Literal["deterministic-fake", "zhipu-glm-5.2"] = "deterministic-fake"
    fake_scenario: Literal[
        "inspect_then_finish", "finish_immediately", "invalid_json", "repeat_wait", "fail"
    ] = "inspect_then_finish"
    budget: AgentBudget = AgentBudget()


class ActionSummary(StrictModel):
    action_id: ActionId
    action_type: ActionType
    success: bool
    error_category: ErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=160)]


RunStatus = Literal[
    "finished_ungraded",
    "failed",
    "escalated",
    "invalid_model_output",
    "model_error",
    "repeated_action_limit",
    "no_progress_limit",
    "step_budget_exhausted",
    "model_call_budget_exhausted",
    "input_token_budget_exhausted",
    "output_token_budget_exhausted",
    "cost_budget_exhausted",
    "time_budget_exhausted",
    "browser_error",
]


class AgentRunResult(StrictModel):
    schema_version: Literal["w4-dom-agent-result/1.0"] = "w4-dom-agent-result/1.0"
    task_id: TaskId
    status: RunStatus
    terminal_reason: Annotated[str, StringConstraints(min_length=1, max_length=300)]
    steps: int = Field(ge=0)
    action_count: int = Field(ge=0)
    model_calls: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_microusd: int = Field(ge=0)
    actions: tuple[ActionSummary, ...]
