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
VisionObservationId = Annotated[str, StringConstraints(pattern=r"^vobs_[A-Za-z0-9_-]{8,64}$")]
ScreenshotRef = Annotated[str, StringConstraints(pattern=r"^shot_[A-Za-z0-9_-]{8,80}$")]
GroundingRef = Annotated[str, StringConstraints(pattern=r"^gref_[A-Za-z0-9_-]{8,80}$")]
ActionId = Annotated[str, StringConstraints(pattern=r"^act_[A-Za-z0-9_-]{1,64}$")]
EncodedJpeg = Annotated[
    str,
    StringConstraints(min_length=4, max_length=245_760, pattern=r"^[A-Za-z0-9+/]*={0,2}$"),
]
TaskId = Literal[
    "w3-joiner-001",
    "w3-joiner-002",
    "w3-joiner-003",
    "w3-joiner-004",
    "w3-joiner-005",
]
VisionActionType = Literal[
    "navigate", "click", "fill", "select", "read", "scroll", "wait", "finish", "fail"
]
GroundedActionType = Literal["click", "fill", "select", "read", "scroll"]
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
    allowed_actions: tuple[GroundedActionType, ...] = Field(min_length=1, max_length=5)


class VisionLastAction(StrictModel):
    action_id: ActionId
    action_type: VisionActionType
    success: bool
    error_category: VisionErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=300)]


class VisionObservation(StrictModel):
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
    schema_version: Literal["w5-vision-session/1.0"]
    session_id: SessionId
    observation: VisionObservation


class VisionNavigateAction(StrictModel):
    schema_version: Literal["w5-vision-action/1.0"] = "w5-vision-action/1.0"
    action_id: ActionId
    type: Literal["navigate"]
    url: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class VisionGroundingAction(StrictModel):
    schema_version: Literal["w5-vision-action/1.0"] = "w5-vision-action/1.0"
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
    schema_version: Literal["w5-vision-action/1.0"] = "w5-vision-action/1.0"
    action_id: ActionId
    type: Literal["wait"]
    duration_ms: int = Field(ge=1, le=5_000)


class VisionFinishAction(StrictModel):
    schema_version: Literal["w5-vision-action/1.0"] = "w5-vision-action/1.0"
    action_id: ActionId
    type: Literal["finish"]
    summary: Annotated[str, StringConstraints(max_length=300)] = ""


class VisionFailAction(StrictModel):
    schema_version: Literal["w5-vision-action/1.0"] = "w5-vision-action/1.0"
    action_id: ActionId
    type: Literal["fail"]
    category: Literal["failed", "escalated"]
    reason: Annotated[str, StringConstraints(min_length=1, max_length=300)]


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
    schema_version: Literal["w5-vision-action-result/1.0"]
    session_id: SessionId
    action_id: ActionId
    action_type: VisionActionType
    success: bool
    terminal: bool
    error_category: VisionErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=300)]
    observation: VisionObservation | None = None


class VisionModelDecision(StrictModel):
    schema_version: Literal["w5-vision-model-decision/1.0"] = "w5-vision-model-decision/1.0"
    action: VisionBrowserAction


class ModelUsage(StrictModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_microusd: int = Field(ge=0)


class VisionAgentBudget(StrictModel):
    max_steps: int = Field(default=24, ge=1, le=24)
    max_model_calls: int = Field(default=24, ge=1, le=24)
    max_repeated_actions: int = Field(default=2, ge=1, le=5)
    max_no_progress: int = Field(default=3, ge=1, le=8)
    max_duration_seconds: int = Field(default=300, ge=1, le=300)
    max_images: int = Field(default=24, ge=1, le=24)
    max_image_bytes: int = Field(default=4_423_680, ge=1, le=4_423_680)
    max_image_pixels: int = Field(default=12_441_600, ge=1, le=12_441_600)
    max_capture_ms: int = Field(default=72_000, ge=1, le=72_000)
    max_input_tokens: int = Field(default=100_000, ge=1, le=100_000)
    max_output_tokens: int = Field(default=20_000, ge=1, le=20_000)
    max_cost_microusd: int = Field(default=0, ge=0, le=1_000_000)


class VisionAgentRunRequest(StrictModel):
    schema_version: Literal["w5-vision-agent-run/1.0"] = "w5-vision-agent-run/1.0"
    task_id: TaskId
    instruction: Annotated[str, StringConstraints(min_length=1, max_length=4_000)]
    model: Literal["deterministic-fake-vision"] = "deterministic-fake-vision"
    fake_scenario: Literal[
        "grounded_read_then_finish",
        "complete_joiner",
        "finish_immediately",
        "invalid_json",
        "repeat_wait",
        "fail",
    ] = "grounded_read_then_finish"
    budget: VisionAgentBudget = VisionAgentBudget()


class ActionSummary(StrictModel):
    action_id: ActionId
    action_type: VisionActionType
    success: bool
    error_category: VisionErrorCategory | None = None
    message: Annotated[str, StringConstraints(max_length=160)]


VisionRunStatus = Literal[
    "finished_ungraded",
    "failed",
    "escalated",
    "invalid_model_output",
    "model_error",
    "repeated_action_limit",
    "no_progress_limit",
    "step_budget_exhausted",
    "model_call_budget_exhausted",
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


class VisionAgentRunResult(StrictModel):
    schema_version: Literal["w5-vision-agent-result/1.0"] = "w5-vision-agent-result/1.0"
    task_id: TaskId
    status: VisionRunStatus
    terminal_reason: Annotated[str, StringConstraints(min_length=1, max_length=300)]
    steps: int = Field(ge=0)
    action_count: int = Field(ge=0)
    model_calls: int = Field(ge=0)
    image_count: int = Field(ge=0)
    image_bytes: int = Field(ge=0)
    image_pixels: int = Field(ge=0)
    capture_duration_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_microusd: int = Field(ge=0)
    actions: tuple[ActionSummary, ...]
