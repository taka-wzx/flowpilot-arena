import base64
import json
import re
from dataclasses import dataclass
from typing import Literal, Protocol

from flowpilot_vision_agent.schemas import ModelUsage, VisionObservation, VisualGrounding


@dataclass(frozen=True, slots=True)
class VisionModelContext:
    task_id: str
    instruction: str
    observation: VisionObservation
    prior_actions: tuple[str, ...]
    remaining_steps: int
    remaining_model_calls: int
    remaining_images: int
    remaining_image_bytes: int
    remaining_image_pixels: int
    remaining_capture_ms: int
    remaining_input_tokens: int
    remaining_output_tokens: int
    remaining_cost_microusd: int


@dataclass(frozen=True, slots=True)
class RawModelResponse:
    content: str
    usage: ModelUsage


@dataclass(frozen=True, slots=True)
class _JoinerValues:
    employee_id: str
    ticket_title: str
    username: str
    asset_tag: str
    laptop_model: str
    mailbox: str


@dataclass(frozen=True, slots=True)
class _JoinerPlanStep:
    type: Literal["read", "navigate", "fill", "click", "finish"]
    value: str | None = None
    fill_index: int | None = None


_JOINER_VALUES = re.compile(
    r"(?:^|\s)Supplied synthetic values: employee ID "
    r"(?P<employee_id>[1-9][0-9]{0,8}); ticket title "
    r"(?P<ticket_title>[^;\r\n]{1,200}); username "
    r"(?P<username>[a-z][a-z0-9.]{2,79}); asset tag "
    r"(?P<asset_tag>SYN-[A-Z0-9-]{1,80}); laptop model "
    r"(?P<laptop_model>[^;\r\n]{1,120}); mailbox "
    r"(?P<mailbox>[a-z0-9][a-z0-9._+-]{0,79}@flowpilot\.invalid)\.\Z"
)


class VisionModelClient(Protocol):
    async def complete(self, context: VisionModelContext) -> RawModelResponse: ...


class ModelCallError(RuntimeError):
    def __init__(self, safe_reason: str, *, usage: ModelUsage | None = None) -> None:
        super().__init__(safe_reason)
        self.safe_reason = safe_reason
        self.usage = usage


class DeterministicFakeVisionModel:
    """No-network W5 fake that proves only the typed visual circuit."""

    def __init__(
        self,
        scenario: Literal[
            "grounded_read_then_finish",
            "complete_joiner",
            "finish_immediately",
            "invalid_json",
            "repeat_wait",
            "fail",
        ],
    ) -> None:
        self._scenario = scenario
        self._calls = 0
        self._joiner_values: _JoinerValues | None = None

    async def complete(self, context: VisionModelContext) -> RawModelResponse:
        self._calls += 1
        self._validate_restricted_image(context.observation)
        usage = ModelUsage(input_tokens=32, output_tokens=16, cost_microusd=0)
        if self._scenario == "invalid_json":
            return RawModelResponse(content="{not-json", usage=usage)
        if self._scenario == "repeat_wait":
            action: dict[str, object] = {
                "schema_version": "w5-vision-action/1.0",
                "action_id": f"act_fake_{self._calls}",
                "type": "wait",
                "duration_ms": 1,
            }
        elif self._scenario == "fail":
            action = {
                "schema_version": "w5-vision-action/1.0",
                "action_id": f"act_fake_{self._calls}",
                "type": "fail",
                "category": "failed",
                "reason": "Deterministic fake requested safe termination",
            }
        elif self._scenario == "complete_joiner":
            action = self._complete_joiner_action(context)
        elif self._scenario == "finish_immediately" or self._calls > 1:
            action = {
                "schema_version": "w5-vision-action/1.0",
                "action_id": f"act_fake_{self._calls}",
                "type": "finish",
                "summary": "Fake vision model ended the loop; grading remains external",
            }
        else:
            readable = next(
                (
                    grounding
                    for grounding in context.observation.groundings
                    if "read" in grounding.allowed_actions
                ),
                None,
            )
            if readable is None:
                action = {
                    "schema_version": "w5-vision-action/1.0",
                    "action_id": f"act_fake_{self._calls}",
                    "type": "wait",
                    "duration_ms": 1,
                }
            else:
                action = {
                    "schema_version": "w5-vision-action/1.0",
                    "action_id": f"act_fake_{self._calls}",
                    "type": "read",
                    "observation_id": context.observation.observation_id,
                    "screenshot_ref": context.observation.screenshot_ref,
                    "grounding_ref": readable.grounding_ref,
                }
        envelope = {"schema_version": "w5-vision-model-decision/1.0", "action": action}
        return RawModelResponse(
            content=json.dumps(envelope, sort_keys=True, separators=(",", ":")),
            usage=usage,
        )

    def _complete_joiner_action(self, context: VisionModelContext) -> dict[str, object]:
        values = self._joiner_values_from(context.instruction)
        plan = (
            _JoinerPlanStep("read"),
            _JoinerPlanStep("navigate", "/itsm"),
            _JoinerPlanStep("fill", values.employee_id, 0),
            _JoinerPlanStep("fill", values.ticket_title, 1),
            _JoinerPlanStep("click"),
            _JoinerPlanStep("navigate", "/iam"),
            _JoinerPlanStep("fill", values.employee_id, 0),
            _JoinerPlanStep("fill", values.username, 1),
            _JoinerPlanStep("click"),
            _JoinerPlanStep("navigate", "/assets"),
            _JoinerPlanStep("fill", values.employee_id, 0),
            _JoinerPlanStep("fill", values.asset_tag, 1),
            _JoinerPlanStep("fill", values.laptop_model, 2),
            _JoinerPlanStep("click"),
            _JoinerPlanStep("navigate", "/mail"),
            _JoinerPlanStep("fill", values.employee_id, 0),
            _JoinerPlanStep("fill", values.mailbox, 1),
            _JoinerPlanStep("click"),
            _JoinerPlanStep("navigate", "/hris"),
            _JoinerPlanStep("finish"),
        )
        step = plan[self._calls - 1]
        action_id = f"act_fake_{self._calls}"
        if step.type == "navigate":
            return {
                "schema_version": "w5-vision-action/1.0",
                "action_id": action_id,
                "type": "navigate",
                "url": step.value,
            }
        if step.type == "finish":
            return {
                "schema_version": "w5-vision-action/1.0",
                "action_id": action_id,
                "type": "finish",
                "summary": "Deterministic fake workflow ended; grading remains external",
            }
        if step.type == "read":
            grounding = self._grounding_for(context.observation, "read", 0)
            return self._grounded_action(context.observation, action_id, "read", grounding)
        if step.type == "fill":
            if step.fill_index is None or step.value is None:
                raise ModelCallError("Deterministic fake workflow was internally incomplete")
            grounding = self._grounding_for(context.observation, "fill", step.fill_index)
            return self._grounded_action(
                context.observation,
                action_id,
                "fill",
                grounding,
                text=step.value,
            )
        grounding = self._submit_grounding(context.observation)
        return self._grounded_action(context.observation, action_id, "click", grounding)

    def _joiner_values_from(self, instruction: str) -> _JoinerValues:
        if self._joiner_values is not None:
            return self._joiner_values
        match = _JOINER_VALUES.search(instruction.strip())
        if match is None:
            raise ModelCallError("Deterministic fake requires a valid supplied-values brief")
        self._joiner_values = _JoinerValues(**match.groupdict())
        return self._joiner_values

    @staticmethod
    def _grounded_action(
        observation: VisionObservation,
        action_id: str,
        action_type: Literal["click", "fill", "read"],
        grounding: VisualGrounding,
        *,
        text: str | None = None,
    ) -> dict[str, object]:
        action: dict[str, object] = {
            "schema_version": "w5-vision-action/1.0",
            "action_id": action_id,
            "type": action_type,
            "observation_id": observation.observation_id,
            "screenshot_ref": observation.screenshot_ref,
            "grounding_ref": grounding.grounding_ref,
        }
        if text is not None:
            action["text"] = text
        return action

    @staticmethod
    def _grounding_for(
        observation: VisionObservation,
        action_type: Literal["fill", "read"],
        index: int,
    ) -> VisualGrounding:
        candidates = sorted(
            (
                grounding
                for grounding in observation.groundings
                if action_type in grounding.allowed_actions
            ),
            key=DeterministicFakeVisionModel._geometry_key,
        )
        if index >= len(candidates):
            raise ModelCallError("Current visual Grounding set cannot satisfy the fake workflow")
        return candidates[index]

    @staticmethod
    def _submit_grounding(observation: VisionObservation) -> VisualGrounding:
        candidates = [
            grounding
            for grounding in observation.groundings
            if "click" in grounding.allowed_actions
        ]
        if not candidates:
            raise ModelCallError("Current visual Grounding set cannot satisfy the fake workflow")
        return max(
            candidates,
            key=lambda grounding: (
                grounding.bounds.y + grounding.bounds.height,
                grounding.bounds.x + grounding.bounds.width,
                grounding.bounds.height,
                grounding.bounds.width,
                grounding.grounding_ref,
            ),
        )

    @staticmethod
    def _geometry_key(grounding: VisualGrounding) -> tuple[int, int, int, int, str]:
        return (
            grounding.bounds.y,
            grounding.bounds.x,
            grounding.bounds.height,
            grounding.bounds.width,
            grounding.grounding_ref,
        )

    @staticmethod
    def _validate_restricted_image(observation: VisionObservation) -> None:
        try:
            image = base64.b64decode(observation.image_base64, validate=True)
        except ValueError as exc:
            raise ModelCallError("Visual input was not a valid bounded JPEG") from exc
        if (
            observation.image_mime_type != "image/jpeg"
            or len(image) != observation.image_bytes
            or not image.startswith(b"\xff\xd8")
            or not image.endswith(b"\xff\xd9")
        ):
            raise ModelCallError("Visual input was not a valid bounded JPEG")
