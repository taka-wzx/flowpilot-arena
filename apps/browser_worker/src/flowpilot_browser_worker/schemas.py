from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

SESSION_SCHEMA_VERSION: Final[Literal["w4-browser-session/1.0"]] = "w4-browser-session/1.0"
OBSERVATION_SCHEMA_VERSION: Final[Literal["w4-dom-observation/1.0"]] = "w4-dom-observation/1.0"
ACTION_SCHEMA_VERSION: Final[Literal["w4-dom-action/1.0"]] = "w4-dom-action/1.0"
ACTION_RESULT_SCHEMA_VERSION: Final[Literal["w4-dom-action-result/1.0"]] = (
    "w4-dom-action-result/1.0"
)

SessionId = Annotated[str, StringConstraints(pattern=r"^bw_[A-Za-z0-9_-]{16,64}$")]
ObservationId = Annotated[str, StringConstraints(pattern=r"^obs_[A-Za-z0-9_-]{8,64}$")]
ElementRef = Annotated[str, StringConstraints(pattern=r"^ref_[A-Za-z0-9_-]{8,80}$")]
ActionId = Annotated[str, StringConstraints(pattern=r"^act_[A-Za-z0-9_-]{1,64}$")]
ShortText = Annotated[str, StringConstraints(min_length=1, max_length=300)]

AllowedElementAction = Literal["click", "fill", "select", "read", "scroll"]
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


class SessionCreate(StrictModel):
    schema_version: Literal["w4-browser-session/1.0"] = SESSION_SCHEMA_VERSION
    initial_path: Literal["/hris"] = "/hris"


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
    allowed_actions: tuple[AllowedElementAction, ...]
    options: tuple[Annotated[str, StringConstraints(min_length=1, max_length=120)], ...] = ()


class LastAction(StrictModel):
    action_id: ActionId
    action_type: ActionType
    success: bool
    error_category: ErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=300)]


class Observation(StrictModel):
    schema_version: Literal["w4-dom-observation/1.0"] = OBSERVATION_SCHEMA_VERSION
    session_id: SessionId
    observation_id: ObservationId
    current_url: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    page_title: Annotated[str, StringConstraints(max_length=200)]
    semantic_nodes: tuple[SemanticNode, ...]
    interactive_elements: tuple[InteractiveElement, ...]
    last_action: LastAction | None = None
    page_error: Annotated[str, StringConstraints(max_length=300)] | None = None
    truncated: bool


class SessionCreated(StrictModel):
    schema_version: Literal["w4-browser-session/1.0"] = SESSION_SCHEMA_VERSION
    session_id: SessionId
    observation: Observation


class NavigateAction(StrictModel):
    schema_version: Literal["w4-dom-action/1.0"] = ACTION_SCHEMA_VERSION
    action_id: ActionId
    type: Literal["navigate"]
    url: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class ElementAction(StrictModel):
    schema_version: Literal["w4-dom-action/1.0"] = ACTION_SCHEMA_VERSION
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
    schema_version: Literal["w4-dom-action/1.0"] = ACTION_SCHEMA_VERSION
    action_id: ActionId
    type: Literal["wait"]
    duration_ms: int = Field(ge=1, le=5_000)


class FinishAction(StrictModel):
    schema_version: Literal["w4-dom-action/1.0"] = ACTION_SCHEMA_VERSION
    action_id: ActionId
    type: Literal["finish"]
    summary: Annotated[str, StringConstraints(max_length=300)] = ""


class FailAction(StrictModel):
    schema_version: Literal["w4-dom-action/1.0"] = ACTION_SCHEMA_VERSION
    action_id: ActionId
    type: Literal["fail"]
    category: Literal["failed", "escalated"]
    reason: ShortText


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


class ActionResult(StrictModel):
    schema_version: Literal["w4-dom-action-result/1.0"] = ACTION_RESULT_SCHEMA_VERSION
    session_id: SessionId
    action_id: ActionId
    action_type: ActionType
    success: bool
    terminal: bool
    error_category: ErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=300)]
    observation: Observation | None = None


class SessionClosed(StrictModel):
    schema_version: Literal["w4-browser-session/1.0"] = SESSION_SCHEMA_VERSION
    session_id: SessionId
    closed: bool
