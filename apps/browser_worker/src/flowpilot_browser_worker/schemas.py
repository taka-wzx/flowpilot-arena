import base64
from typing import Annotated, Final, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

SESSION_SCHEMA_VERSION: Final[Literal["w4-browser-session/1.0"]] = "w4-browser-session/1.0"
OBSERVATION_SCHEMA_VERSION: Final[Literal["w4-dom-observation/1.0"]] = "w4-dom-observation/1.0"
ACTION_SCHEMA_VERSION: Final[Literal["w4-dom-action/1.0"]] = "w4-dom-action/1.0"
ACTION_RESULT_SCHEMA_VERSION: Final[Literal["w4-dom-action-result/1.0"]] = (
    "w4-dom-action-result/1.0"
)
VISION_SESSION_SCHEMA_VERSION: Final[Literal["w5-vision-session/1.0"]] = "w5-vision-session/1.0"
VISION_OBSERVATION_SCHEMA_VERSION: Final[Literal["w5-vision-observation/1.0"]] = (
    "w5-vision-observation/1.0"
)
VISION_ACTION_SCHEMA_VERSION: Final[Literal["w5-vision-action/1.0"]] = "w5-vision-action/1.0"
VISION_ACTION_RESULT_SCHEMA_VERSION: Final[Literal["w5-vision-action-result/1.0"]] = (
    "w5-vision-action-result/1.0"
)

SESSION_ID_PATTERN = r"^bw_[A-Za-z0-9_-]{16,64}$"
OBSERVATION_ID_PATTERN = r"^obs_[A-Za-z0-9_-]{8,64}$"
VISION_OBSERVATION_ID_PATTERN = r"^vobs_[A-Za-z0-9_-]{8,64}$"
ELEMENT_REF_PATTERN = r"^ref_[A-Za-z0-9_-]{8,80}$"
SCREENSHOT_REF_PATTERN = r"^shot_[A-Za-z0-9_-]{8,80}$"
GROUNDING_REF_PATTERN = r"^gref_[A-Za-z0-9_-]{8,80}$"
ACTION_ID_PATTERN = r"^act_[A-Za-z0-9_-]{1,64}$"

SessionId = Annotated[str, StringConstraints(pattern=SESSION_ID_PATTERN)]
ObservationId = Annotated[str, StringConstraints(pattern=OBSERVATION_ID_PATTERN)]
VisionObservationId = Annotated[str, StringConstraints(pattern=VISION_OBSERVATION_ID_PATTERN)]
ElementRef = Annotated[str, StringConstraints(pattern=ELEMENT_REF_PATTERN)]
ScreenshotRef = Annotated[str, StringConstraints(pattern=SCREENSHOT_REF_PATTERN)]
GroundingRef = Annotated[str, StringConstraints(pattern=GROUNDING_REF_PATTERN)]
ActionId = Annotated[str, StringConstraints(pattern=ACTION_ID_PATTERN)]
ShortText = Annotated[str, StringConstraints(min_length=1, max_length=300)]
EncodedJpeg = Annotated[
    str,
    StringConstraints(min_length=4, max_length=245_760, pattern=r"^[A-Za-z0-9+/]*={0,2}$"),
]

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
VisionErrorCategory = Literal[
    "invalid_url",
    "stale_visual_ref",
    "unknown_visual_ref",
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


class VisionSessionCreate(StrictModel):
    schema_version: Literal["w5-vision-session/1.0"] = VISION_SESSION_SCHEMA_VERSION
    initial_path: Literal["/hris"] = "/hris"


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
    error_category: VisionErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=300)]


class VisionObservation(StrictModel):
    schema_version: Literal["w5-vision-observation/1.0"] = VISION_OBSERVATION_SCHEMA_VERSION
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
            decoded = base64.b64decode(value, validate=True)
        except ValueError as exc:
            raise ValueError("image_base64 must be canonical base64") from exc
        if not decoded.startswith(b"\xff\xd8") or not decoded.endswith(b"\xff\xd9"):
            raise ValueError("image_base64 must contain a JPEG")
        return value

    @model_validator(mode="after")
    def _validate_image_metadata(self) -> "VisionObservation":
        decoded_length = len(base64.b64decode(self.image_base64, validate=True))
        if decoded_length != self.image_bytes:
            raise ValueError("image_bytes must match the encoded JPEG")
        if self.image_width * self.image_height > 518_400:
            raise ValueError("image pixels exceed the W5 capture envelope")
        return self


class VisionSessionCreated(StrictModel):
    schema_version: Literal["w5-vision-session/1.0"] = VISION_SESSION_SCHEMA_VERSION
    session_id: SessionId
    observation: VisionObservation


class VisionNavigateAction(StrictModel):
    schema_version: Literal["w5-vision-action/1.0"] = VISION_ACTION_SCHEMA_VERSION
    action_id: ActionId
    type: Literal["navigate"]
    url: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class VisionGroundingAction(StrictModel):
    schema_version: Literal["w5-vision-action/1.0"] = VISION_ACTION_SCHEMA_VERSION
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
    schema_version: Literal["w5-vision-action/1.0"] = VISION_ACTION_SCHEMA_VERSION
    action_id: ActionId
    type: Literal["wait"]
    duration_ms: int = Field(ge=1, le=5_000)


class VisionFinishAction(StrictModel):
    schema_version: Literal["w5-vision-action/1.0"] = VISION_ACTION_SCHEMA_VERSION
    action_id: ActionId
    type: Literal["finish"]
    summary: Annotated[str, StringConstraints(max_length=300)] = ""


class VisionFailAction(StrictModel):
    schema_version: Literal["w5-vision-action/1.0"] = VISION_ACTION_SCHEMA_VERSION
    action_id: ActionId
    type: Literal["fail"]
    category: Literal["failed", "escalated"]
    reason: ShortText


type VisionBrowserAction = Annotated[
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


class VisionActionResult(StrictModel):
    schema_version: Literal["w5-vision-action-result/1.0"] = VISION_ACTION_RESULT_SCHEMA_VERSION
    session_id: SessionId
    action_id: ActionId
    action_type: ActionType
    success: bool
    terminal: bool
    error_category: VisionErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=300)]
    observation: VisionObservation | None = None


class VisionSessionClosed(StrictModel):
    schema_version: Literal["w5-vision-session/1.0"] = VISION_SESSION_SCHEMA_VERSION
    session_id: SessionId
    closed: bool
