import json
from dataclasses import dataclass
from typing import Literal, Protocol

from flowpilot_dom_agent.schemas import ModelUsage, Observation


@dataclass(frozen=True, slots=True)
class ModelContext:
    task_id: str
    instruction: str
    observation: Observation
    prior_actions: tuple[str, ...]
    remaining_steps: int
    remaining_model_calls: int
    remaining_input_tokens: int
    remaining_output_tokens: int
    remaining_cost_microusd: int


@dataclass(frozen=True, slots=True)
class RawModelResponse:
    content: str
    usage: ModelUsage


class ModelClient(Protocol):
    async def complete(self, context: ModelContext) -> RawModelResponse: ...


class DeterministicFakeModel:
    """A no-network fake used by tests and the default Compose smoke path."""

    def __init__(
        self,
        scenario: Literal[
            "inspect_then_finish", "finish_immediately", "invalid_json", "repeat_wait", "fail"
        ],
    ) -> None:
        self._scenario = scenario
        self._calls = 0

    async def complete(self, context: ModelContext) -> RawModelResponse:
        self._calls += 1
        usage = ModelUsage(input_tokens=24, output_tokens=12, cost_microusd=0)
        if self._scenario == "invalid_json":
            return RawModelResponse(content="{not-json", usage=usage)
        if self._scenario == "repeat_wait":
            action: dict[str, object] = {
                "schema_version": "w4-dom-action/1.0",
                "action_id": f"act_fake_{self._calls}",
                "type": "wait",
                "duration_ms": 1,
            }
        elif self._scenario == "fail":
            action = {
                "schema_version": "w4-dom-action/1.0",
                "action_id": f"act_fake_{self._calls}",
                "type": "fail",
                "category": "failed",
                "reason": "Deterministic fake requested safe termination",
            }
        elif self._scenario == "finish_immediately" or self._calls > 1:
            action = {
                "schema_version": "w4-dom-action/1.0",
                "action_id": f"act_fake_{self._calls}",
                "type": "finish",
                "summary": "Fake model ended the loop; grading remains external",
            }
        else:
            readable = next(
                (
                    element
                    for element in context.observation.interactive_elements
                    if "read" in element.allowed_actions
                ),
                None,
            )
            if readable is None:
                action = {
                    "schema_version": "w4-dom-action/1.0",
                    "action_id": f"act_fake_{self._calls}",
                    "type": "wait",
                    "duration_ms": 1,
                }
            else:
                action = {
                    "schema_version": "w4-dom-action/1.0",
                    "action_id": f"act_fake_{self._calls}",
                    "type": "read",
                    "observation_id": context.observation.observation_id,
                    "element_ref": readable.element_ref,
                }
        envelope = {"schema_version": "w4-model-decision/1.0", "action": action}
        return RawModelResponse(
            content=json.dumps(envelope, sort_keys=True, separators=(",", ":")),
            usage=usage,
        )
