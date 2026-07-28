import base64
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

SessionId = Annotated[str, StringConstraints(pattern=r"^bw_[A-Za-z0-9_-]{16,64}$")]
ObservationId = Annotated[str, StringConstraints(pattern=r"^obs_[A-Za-z0-9_-]{8,64}$")]
VisionObservationId = Annotated[str, StringConstraints(pattern=r"^vobs_[A-Za-z0-9_-]{8,64}$")]
ElementRef = Annotated[str, StringConstraints(pattern=r"^ref_[A-Za-z0-9_-]{8,80}$")]
ScreenshotRef = Annotated[str, StringConstraints(pattern=r"^shot_[A-Za-z0-9_-]{8,80}$")]
GroundingRef = Annotated[str, StringConstraints(pattern=r"^gref_[A-Za-z0-9_-]{8,80}$")]
ActionId = Annotated[str, StringConstraints(pattern=r"^act_[A-Za-z0-9_-]{1,64}$")]
EncodedJpeg = Annotated[
    str,
    StringConstraints(min_length=4, max_length=245_760, pattern=r"^[A-Za-z0-9+/]*={0,2}$"),
]
ShortText = Annotated[str, StringConstraints(min_length=1, max_length=300)]
TaskId = Literal[
    "w3-joiner-001",
    "w3-joiner-002",
    "w3-joiner-003",
    "w3-joiner-004",
    "w3-joiner-005",
]
HybridModality = Literal["dom", "vision"]
ActionType = Literal[
    "navigate",
    "click",
    "fill",
    "select",
    "read",
    "scroll",
    "wait",
    "finish",
    "fail",
]
AllowedElementAction = Literal["click", "fill", "select", "read", "scroll"]
RouteCategory = Literal["standard", "visual_recovery"]
RouteReasonCode = Literal[
    "dom_default",
    "dom_usable",
    "dom_structure_weak",
    "dom_action_failure",
    "trusted_visual_recovery",
    "vision_retained",
    "switch_refused_budget",
    "switch_limit_reached",
]
SafeRouteErrorCategory = Literal[
    "invalid_url",
    "stale_reference",
    "unknown_reference",
    "action_not_allowed",
    "input_rejected",
    "browser_timeout",
    "browser_error",
    "budget_exhausted",
]
HybridErrorCategory = Literal[
    "invalid_url",
    "invalid_modality",
    "stale_hybrid_ref",
    "unknown_hybrid_ref",
    "action_not_allowed",
    "action_budget_exhausted",
    "navigation_budget_exhausted",
    "session_timeout",
    "wait_limit_exceeded",
    "input_rejected",
    "browser_timeout",
    "browser_error",
    "screenshot_budget_exhausted",
    "screenshot_byte_limit_exceeded",
    "screenshot_capture_timeout",
    "hybrid_observation_budget_exhausted",
    "hybrid_dom_observation_budget_exhausted",
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


class VisualBounds(StrictModel):
    x: int = Field(ge=0, le=959)
    y: int = Field(ge=0, le=539)
    width: int = Field(ge=1, le=960)
    height: int = Field(ge=1, le=540)

    @model_validator(mode="after")
    def _inside_fixed_viewport(self) -> "VisualBounds":
        if self.x + self.width > 960 or self.y + self.height > 540:
            raise ValueError("grounding bounds must remain inside the fixed visual viewport")
        return self


class VisualGrounding(StrictModel):
    grounding_ref: GroundingRef
    bounds: VisualBounds
    allowed_actions: tuple[AllowedElementAction, ...] = Field(min_length=1, max_length=5)


class VisionLastAction(StrictModel):
    action_id: ActionId
    action_type: ActionType
    success: bool
    error_category: Annotated[str, StringConstraints(max_length=80)] | None = None
    message: Annotated[str, StringConstraints(max_length=300)]


class VisualObservation(StrictModel):
    schema_version: Literal["w5-vision-observation/1.0"]
    session_id: SessionId
    observation_id: VisionObservationId
    screenshot_ref: ScreenshotRef
    image_mime_type: Literal["image/jpeg"]
    image_base64: EncodedJpeg
    image_width: int = Field(ge=1, le=960)
    image_height: int = Field(ge=1, le=540)
    image_bytes: int = Field(ge=1, le=184_320)
    capture_duration_ms: int = Field(ge=0, le=3_000)
    groundings: tuple[VisualGrounding, ...] = Field(max_length=80)
    last_action: VisionLastAction | None = None
    page_error: Annotated[str, StringConstraints(max_length=300)] | None = None
    truncated: bool

    @field_validator("image_base64")
    @classmethod
    def _validate_jpeg_payload(cls, value: str) -> str:
        try:
            image = base64.b64decode(value, validate=True)
        except ValueError as exc:
            raise ValueError("image_base64 must be canonical base64") from exc
        if not image.startswith(b"\xff\xd8") or not image.endswith(b"\xff\xd9"):
            raise ValueError("image_base64 must contain a JPEG")
        return value

    @model_validator(mode="after")
    def _validate_image_metadata(self) -> "VisualObservation":
        if len(base64.b64decode(self.image_base64, validate=True)) != self.image_bytes:
            raise ValueError("image_bytes must match the encoded JPEG")
        if self.image_width * self.image_height > 518_400:
            raise ValueError("image pixels exceed the W5 capture envelope")
        return self


class HybridRouteSignals(StrictModel):
    dom_structure: Literal["usable", "empty", "truncated"]
    dom_interactive_count: int = Field(ge=0, le=80)
    dom_observation_bytes: int = Field(ge=0, le=32_768)
    last_action_error_category: SafeRouteErrorCategory | None = None


class HybridDomObservation(StrictModel):
    schema_version: Literal["w6-hybrid-observation/1.0"]
    session_id: SessionId
    generation: int = Field(ge=1, le=24)
    modality: Literal["dom"]
    observation: DomObservation
    route_signals: HybridRouteSignals

    @model_validator(mode="after")
    def _validate_current_dom_metadata(self) -> "HybridDomObservation":
        if self.observation.session_id != self.session_id:
            raise ValueError("nested DOM observation must belong to the Hybrid session")
        effective_count = sum(
            1
            for element in self.observation.interactive_elements
            if not element.state.disabled and bool(element.allowed_actions)
        )
        if self.route_signals.dom_interactive_count != effective_count:
            raise ValueError("DOM route count must match effective interactive elements")
        serialized_bytes = len(self.observation.model_dump_json().encode("utf-8"))
        if self.route_signals.dom_observation_bytes != serialized_bytes:
            raise ValueError("DOM route bytes must match the current observation")
        expected_structure: Literal["usable", "empty", "truncated"]
        if self.observation.truncated:
            expected_structure = "truncated"
        elif effective_count == 0:
            expected_structure = "empty"
        else:
            expected_structure = "usable"
        if self.route_signals.dom_structure != expected_structure:
            raise ValueError("DOM route structure must match the current observation")
        return self


class HybridVisionObservation(StrictModel):
    schema_version: Literal["w6-hybrid-observation/1.0"]
    session_id: SessionId
    generation: int = Field(ge=1, le=24)
    modality: Literal["vision"]
    observation: VisualObservation
    route_signals: HybridRouteSignals

    @model_validator(mode="after")
    def _validate_current_visual_metadata(self) -> "HybridVisionObservation":
        if self.observation.session_id != self.session_id:
            raise ValueError("nested visual observation must belong to the Hybrid session")
        return self


type HybridObservation = Annotated[
    HybridDomObservation | HybridVisionObservation,
    Field(discriminator="modality"),
]


class HybridSessionCreated(StrictModel):
    schema_version: Literal["w6-hybrid-session/1.0"] = "w6-hybrid-session/1.0"
    session_id: SessionId
    observation: HybridObservation

    @model_validator(mode="after")
    def _validate_initial_observation(self) -> "HybridSessionCreated":
        if self.observation.session_id != self.session_id:
            raise ValueError("initial observation must belong to the created Hybrid session")
        return self


class HybridObservationRequest(StrictModel):
    schema_version: Literal["w6-hybrid-observation-request/1.0"] = (
        "w6-hybrid-observation-request/1.0"
    )
    modality: HybridModality


class DomNavigateAction(StrictModel):
    action_id: ActionId
    type: Literal["navigate"]
    url: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class DomElementAction(StrictModel):
    action_id: ActionId
    observation_id: ObservationId
    element_ref: ElementRef


class DomClickAction(DomElementAction):
    type: Literal["click"]


class DomFillAction(DomElementAction):
    type: Literal["fill"]
    text: Annotated[str, StringConstraints(max_length=300)]


class DomSelectAction(DomElementAction):
    type: Literal["select"]
    option: Annotated[str, StringConstraints(min_length=1, max_length=120)]


class DomReadAction(DomElementAction):
    type: Literal["read"]


class DomScrollAction(DomElementAction):
    type: Literal["scroll"]
    direction: Literal["up", "down"]
    amount: Literal["small", "page"] = "small"


class DomWaitAction(StrictModel):
    action_id: ActionId
    type: Literal["wait"]
    duration_ms: int = Field(ge=1, le=5_000)


class DomFinishAction(StrictModel):
    action_id: ActionId
    type: Literal["finish"]
    summary: Annotated[str, StringConstraints(max_length=300)] = ""


class DomFailAction(StrictModel):
    action_id: ActionId
    type: Literal["fail"]
    category: Literal["failed", "escalated"]
    reason: ShortText


type DomAction = Annotated[
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


class VisionNavigateAction(StrictModel):
    action_id: ActionId
    type: Literal["navigate"]
    url: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class VisionGroundingAction(StrictModel):
    action_id: ActionId
    observation_id: VisionObservationId
    screenshot_ref: ScreenshotRef
    grounding_ref: GroundingRef


class VisionClickAction(VisionGroundingAction):
    type: Literal["click"]


class VisionFillAction(VisionGroundingAction):
    type: Literal["fill"]
    text: Annotated[str, StringConstraints(max_length=300)]


class VisionSelectAction(VisionGroundingAction):
    type: Literal["select"]
    option: Annotated[str, StringConstraints(min_length=1, max_length=120)]


class VisionReadAction(VisionGroundingAction):
    type: Literal["read"]


class VisionScrollAction(VisionGroundingAction):
    type: Literal["scroll"]
    direction: Literal["up", "down"]
    amount: Literal["small", "page"] = "small"


class VisionWaitAction(StrictModel):
    action_id: ActionId
    type: Literal["wait"]
    duration_ms: int = Field(ge=1, le=5_000)


class VisionFinishAction(StrictModel):
    action_id: ActionId
    type: Literal["finish"]
    summary: Annotated[str, StringConstraints(max_length=300)] = ""


class VisionFailAction(StrictModel):
    action_id: ActionId
    type: Literal["fail"]
    category: Literal["failed", "escalated"]
    reason: ShortText


type VisionAction = Annotated[
    VisionNavigateAction
    | VisionClickAction
    | VisionFillAction
    | VisionSelectAction
    | VisionReadAction
    | VisionScrollAction
    | VisionWaitAction
    | VisionFinishAction
    | VisionFailAction,
    Field(discriminator="type"),
]


class HybridDomActionEnvelope(StrictModel):
    schema_version: Literal["w6-hybrid-action-envelope/1.0"] = "w6-hybrid-action-envelope/1.0"
    session_id: SessionId
    generation: int = Field(ge=1, le=24)
    modality: Literal["dom"]
    action: DomAction


class HybridVisionActionEnvelope(StrictModel):
    schema_version: Literal["w6-hybrid-action-envelope/1.0"] = "w6-hybrid-action-envelope/1.0"
    session_id: SessionId
    generation: int = Field(ge=1, le=24)
    modality: Literal["vision"]
    action: VisionAction


type HybridActionEnvelope = Annotated[
    HybridDomActionEnvelope | HybridVisionActionEnvelope,
    Field(discriminator="modality"),
]


class HybridActionResult(StrictModel):
    schema_version: Literal["w6-hybrid-action-result/1.0"] = "w6-hybrid-action-result/1.0"
    session_id: SessionId
    action_id: ActionId
    modality: HybridModality
    action_type: ActionType
    success: bool
    terminal: bool
    error_category: HybridErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=300)]
    observation: HybridObservation | None = None

    @model_validator(mode="after")
    def _validate_result_observation(self) -> "HybridActionResult":
        if self.terminal and self.observation is not None:
            raise ValueError("terminal Hybrid results cannot retain an observation")
        if not self.terminal and self.observation is None:
            raise ValueError("non-terminal Hybrid results require a current observation")
        if self.observation is not None and self.observation.session_id != self.session_id:
            raise ValueError("result observation must belong to the Hybrid session")
        return self


class HybridModelDecision(StrictModel):
    schema_version: Literal["w6-hybrid-model-decision/1.0"] = "w6-hybrid-model-decision/1.0"
    action: HybridActionEnvelope


class ModelUsage(StrictModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_microusd: int = Field(ge=0)


class RouteDecision(StrictModel):
    schema_version: Literal["w6-router-decision/1.0"] = "w6-router-decision/1.0"
    from_modality: HybridModality
    to_modality: HybridModality
    reason_code: RouteReasonCode
    switched: bool
    switch_count: int = Field(ge=0, le=2)

    @model_validator(mode="after")
    def _matches_modalities(self) -> "RouteDecision":
        if self.switched != (self.from_modality != self.to_modality):
            raise ValueError("switched must match the route modalities")
        return self


class CompressedSemanticNode(StrictModel):
    role: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    name: Annotated[str, StringConstraints(max_length=240)]
    text: Annotated[str, StringConstraints(max_length=240)]


class CompressedInteractiveElement(StrictModel):
    element_ref: ElementRef
    role: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    name: Annotated[str, StringConstraints(max_length=240)]
    state: ElementState
    allowed_actions: tuple[AllowedElementAction, ...]
    options: tuple[Annotated[str, StringConstraints(min_length=1, max_length=120)], ...] = ()


class CompressedDomObservation(StrictModel):
    schema_version: Literal["w6-compressed-observation/1.0"] = "w6-compressed-observation/1.0"
    modality: Literal["dom"]
    session_id: SessionId
    generation: int = Field(ge=1, le=24)
    observation_id: ObservationId
    semantic_nodes: tuple[CompressedSemanticNode, ...] = Field(max_length=32)
    interactive_elements: tuple[CompressedInteractiveElement, ...] = Field(max_length=40)
    truncated: bool
    serialized_bytes: int = Field(ge=1, le=12_288)


class CompressedVisualObservation(StrictModel):
    schema_version: Literal["w6-compressed-observation/1.0"] = "w6-compressed-observation/1.0"
    modality: Literal["vision"]
    session_id: SessionId
    generation: int = Field(ge=1, le=24)
    observation_id: VisionObservationId
    visual_observation: VisualObservation

    @model_validator(mode="after")
    def _validate_visual_identity(self) -> "CompressedVisualObservation":
        if self.visual_observation.session_id != self.session_id:
            raise ValueError("visual model input must belong to the Hybrid session")
        if self.visual_observation.observation_id != self.observation_id:
            raise ValueError("visual model input must carry its current observation")
        return self


type CompressedObservation = Annotated[
    CompressedDomObservation | CompressedVisualObservation,
    Field(discriminator="modality"),
]


class ActionSummary(StrictModel):
    modality: HybridModality
    action_type: ActionType
    success: bool
    error_category: HybridErrorCategory | None = None


class HybridAgentBudget(StrictModel):
    max_steps: int = Field(default=24, ge=1, le=24)
    max_model_calls: int = Field(default=24, ge=1, le=24)
    max_switches: int = Field(default=2, ge=0, le=2)
    max_repeated_actions: int = Field(default=2, ge=1, le=5)
    max_no_progress: int = Field(default=3, ge=1, le=8)
    max_duration_seconds: int = Field(default=300, ge=1, le=300)
    max_dom_observations: int = Field(default=24, ge=1, le=24)
    max_dom_observation_bytes: int = Field(default=262_144, ge=1, le=262_144)
    max_compressed_dom_bytes: int = Field(default=147_456, ge=1, le=147_456)
    max_images: int = Field(default=24, ge=1, le=24)
    max_image_bytes: int = Field(default=4_423_680, ge=1, le=4_423_680)
    max_image_pixels: int = Field(default=12_441_600, ge=1, le=12_441_600)
    max_capture_ms: int = Field(default=72_000, ge=1, le=72_000)
    max_input_tokens: int = Field(default=100_000, ge=1, le=100_000)
    max_output_tokens: int = Field(default=20_000, ge=1, le=20_000)
    max_cost_microusd: int = Field(default=0, ge=0, le=1_000_000)


class HybridAgentRunRequest(StrictModel):
    schema_version: Literal["w6-hybrid-agent-run/1.0"] = "w6-hybrid-agent-run/1.0"
    task_id: TaskId
    instruction: Annotated[str, StringConstraints(min_length=1, max_length=4_000)]
    route_category: RouteCategory = "standard"
    model: Literal["deterministic-fake-hybrid"] = "deterministic-fake-hybrid"
    fake_scenario: Literal[
        "finish_immediately",
        "complete_joiner_dom_to_vision",
        "invalid_json",
        "repeat_wait",
        "fail",
    ] = "finish_immediately"
    budget: HybridAgentBudget = HybridAgentBudget()


HybridRunStatus = Literal[
    "finished_ungraded",
    "failed",
    "escalated",
    "invalid_model_output",
    "model_error",
    "repeated_action_limit",
    "no_progress_limit",
    "step_budget_exhausted",
    "model_call_budget_exhausted",
    "switch_budget_exhausted",
    "dom_observation_budget_exhausted",
    "dom_observation_byte_budget_exhausted",
    "compressed_dom_budget_exhausted",
    "image_budget_exhausted",
    "image_byte_budget_exhausted",
    "image_pixel_budget_exhausted",
    "capture_time_budget_exhausted",
    "input_token_budget_exhausted",
    "output_token_budget_exhausted",
    "cost_budget_exhausted",
    "time_budget_exhausted",
    "browser_error",
]


class HybridAgentRunResult(StrictModel):
    schema_version: Literal["w6-hybrid-agent-result/1.0"] = "w6-hybrid-agent-result/1.0"
    task_id: TaskId
    status: HybridRunStatus
    terminal_reason: Annotated[str, StringConstraints(min_length=1, max_length=300)]
    steps: int = Field(ge=0)
    action_count: int = Field(ge=0)
    model_calls: int = Field(ge=0)
    switches: int = Field(ge=0, le=2)
    dom_observation_count: int = Field(ge=0)
    dom_observation_bytes: int = Field(ge=0)
    compressed_dom_bytes: int = Field(ge=0)
    image_count: int = Field(ge=0)
    image_bytes: int = Field(ge=0)
    image_pixels: int = Field(ge=0)
    capture_duration_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_microusd: int = Field(ge=0)
    routes: tuple[RouteDecision, ...] = Field(max_length=24)
    actions: tuple[ActionSummary, ...] = Field(max_length=24)
