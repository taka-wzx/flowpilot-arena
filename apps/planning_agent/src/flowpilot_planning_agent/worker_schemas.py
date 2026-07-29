from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

SessionId = Annotated[str, StringConstraints(pattern=r"^bw_[A-Za-z0-9_-]{16,64}$")]
ObservationId = Annotated[str, StringConstraints(pattern=r"^obs_[A-Za-z0-9_-]{8,64}$")]
ElementRef = Annotated[str, StringConstraints(pattern=r"^ref_[A-Za-z0-9_-]{8,80}$")]
ActionId = Annotated[str, StringConstraints(pattern=r"^act_[A-Za-z0-9_-]{1,64}$")]
AllowedElementAction = Literal["click", "fill", "select", "read", "scroll"]
SandboxPath = Literal["/hris", "/itsm", "/iam", "/assets", "/mail"]
ActionType = Literal[
    "navigate", "click", "fill", "select", "read", "scroll", "wait", "finish", "fail"
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
    allowed_actions: tuple[AllowedElementAction, ...]
    options: tuple[Annotated[str, StringConstraints(min_length=1, max_length=120)], ...] = ()


class DomLastAction(StrictModel):
    action_id: ActionId
    action_type: ActionType
    success: bool
    error_category: Annotated[str, StringConstraints(max_length=80)] | None = None
    message: Annotated[str, StringConstraints(max_length=300)]


class DomObservation(StrictModel):
    schema_version: Literal["w4-dom-observation/1.0"]
    session_id: SessionId
    observation_id: ObservationId
    current_url: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    page_title: Annotated[str, StringConstraints(max_length=200)]
    semantic_nodes: tuple[SemanticNode, ...] = Field(max_length=120)
    interactive_elements: tuple[InteractiveElement, ...] = Field(max_length=80)
    last_action: DomLastAction | None = None
    page_error: Annotated[str, StringConstraints(max_length=300)] | None = None
    truncated: bool


class HybridRouteSignals(StrictModel):
    dom_structure: Literal["usable", "empty", "truncated"]
    dom_interactive_count: int = Field(ge=0, le=80)
    dom_observation_bytes: int = Field(ge=0, le=32_768)
    last_action_error_category: Annotated[str, StringConstraints(max_length=80)] | None = None


class HybridDomObservation(StrictModel):
    schema_version: Literal["w6-hybrid-observation/1.0"]
    session_id: SessionId
    generation: int = Field(ge=1, le=24)
    modality: Literal["dom"]
    observation: DomObservation
    route_signals: HybridRouteSignals

    @model_validator(mode="after")
    def validate_identity(self) -> "HybridDomObservation":
        if self.observation.session_id != self.session_id:
            raise ValueError("nested observation must belong to the Hybrid session")
        return self


class HybridSessionCreated(StrictModel):
    schema_version: Literal["w6-hybrid-session/1.0"]
    session_id: SessionId
    observation: HybridDomObservation

    @model_validator(mode="after")
    def validate_identity(self) -> "HybridSessionCreated":
        if self.observation.session_id != self.session_id:
            raise ValueError("initial observation must belong to the session")
        return self


class DomNavigateAction(StrictModel):
    action_id: ActionId
    type: Literal["navigate"] = "navigate"
    url: SandboxPath


class DomElementAction(StrictModel):
    action_id: ActionId
    observation_id: ObservationId
    element_ref: ElementRef


class DomClickAction(DomElementAction):
    type: Literal["click"] = "click"


class DomFillAction(DomElementAction):
    type: Literal["fill"] = "fill"
    text: Annotated[str, StringConstraints(max_length=300)]


class DomSelectAction(DomElementAction):
    type: Literal["select"] = "select"
    option: Annotated[str, StringConstraints(min_length=1, max_length=120)]


class DomReadAction(DomElementAction):
    type: Literal["read"] = "read"


class DomScrollAction(DomElementAction):
    type: Literal["scroll"] = "scroll"
    direction: Literal["up", "down"]
    amount: Literal["small", "page"] = "small"


class DomWaitAction(StrictModel):
    action_id: ActionId
    type: Literal["wait"] = "wait"
    duration_ms: int = Field(ge=1, le=5_000)


class DomFinishAction(StrictModel):
    action_id: ActionId
    type: Literal["finish"] = "finish"
    summary: Annotated[str, StringConstraints(max_length=300)] = ""


class DomFailAction(StrictModel):
    action_id: ActionId
    type: Literal["fail"] = "fail"
    category: Literal["failed", "escalated"]
    reason: Annotated[str, StringConstraints(min_length=1, max_length=300)]


DomAction = Annotated[
    DomNavigateAction
    | DomClickAction
    | DomFillAction
    | DomSelectAction
    | DomReadAction
    | DomScrollAction
    | DomWaitAction
    | DomFinishAction
    | DomFailAction,
    Field(discriminator="type"),
]


class HybridDomActionEnvelope(StrictModel):
    schema_version: Literal["w6-hybrid-action-envelope/1.0"] = "w6-hybrid-action-envelope/1.0"
    session_id: SessionId
    generation: int = Field(ge=1, le=24)
    modality: Literal["dom"] = "dom"
    action: DomAction


class HybridActionResult(StrictModel):
    schema_version: Literal["w6-hybrid-action-result/1.0"]
    session_id: SessionId
    action_id: ActionId
    modality: Literal["dom"]
    action_type: ActionType
    success: bool
    terminal: bool
    error_category: Annotated[str, StringConstraints(max_length=80)] | None = None
    message: Annotated[str, StringConstraints(max_length=300)]
    observation: HybridDomObservation | None = None

    @model_validator(mode="after")
    def validate_result(self) -> "HybridActionResult":
        if self.terminal == (self.observation is not None):
            raise ValueError("terminal and observation fields are inconsistent")
        if self.observation is not None and self.observation.session_id != self.session_id:
            raise ValueError("result observation must belong to the session")
        return self
