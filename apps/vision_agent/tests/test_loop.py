import json
from dataclasses import dataclass

from conftest import FakeBrowserClient

from flowpilot_vision_agent.loop import VisionAgentLoop
from flowpilot_vision_agent.model import (
    DeterministicFakeVisionModel,
    ModelCallError,
    RawModelResponse,
    VisionModelContext,
)
from flowpilot_vision_agent.schemas import (
    ModelUsage,
    VisionAgentBudget,
)

JOINER_BRIEF = (
    "Complete the synthetic onboarding. Supplied synthetic values: employee ID 31001; "
    "ticket title Synthetic onboarding: Nova Quill [W3-001]; username nova.quill.w3001; "
    "asset tag SYN-W3-001-LAPTOP; laptop model ExampleBook Air 13; "
    "mailbox nova.quill.w3001@flowpilot.invalid."
)


async def test_finish_is_explicitly_ungraded_and_records_image_metrics(
    fake_browser: FakeBrowserClient,
) -> None:
    result = await VisionAgentLoop(
        fake_browser, DeterministicFakeVisionModel("grounded_read_then_finish")
    ).run("w3-joiner-001", "Synthetic human instruction", VisionAgentBudget())
    assert result.status == "finished_ungraded"
    assert result.steps == 2
    assert result.action_count == 2
    assert result.image_count == 2
    assert result.image_pixels == 2 * 960 * 540
    assert result.cost_microusd == 0
    assert fake_browser.closed is True
    assert "grade" in result.terminal_reason.lower()


async def test_invalid_json_and_image_budget_close_safely(
    fake_browser: FakeBrowserClient,
) -> None:
    invalid = await VisionAgentLoop(fake_browser, DeterministicFakeVisionModel("invalid_json")).run(
        "w3-joiner-001", "Synthetic human instruction", VisionAgentBudget()
    )
    assert invalid.status == "invalid_model_output"
    assert invalid.action_count == 0
    assert invalid.image_count == 1
    assert fake_browser.closed is True

    limited_browser = FakeBrowserClient()
    limited = await VisionAgentLoop(
        limited_browser, DeterministicFakeVisionModel("grounded_read_then_finish")
    ).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        VisionAgentBudget(max_images=1),
    )
    assert limited.status == "image_budget_exhausted"
    assert limited.image_count == 2
    assert limited_browser.closed is True


async def test_complete_joiner_finishes_ungraded_within_all_fake_budgets() -> None:
    browser = FakeBrowserClient(joiner_geometry=True)
    result = await VisionAgentLoop(browser, DeterministicFakeVisionModel("complete_joiner")).run(
        "w3-joiner-001", JOINER_BRIEF, VisionAgentBudget()
    )

    assert result.status == "finished_ungraded"
    assert result.steps == 20
    assert result.action_count == 20
    assert result.model_calls == 20
    assert result.image_count == 20
    assert result.image_pixels == 20 * 960 * 540
    assert result.input_tokens == 20 * 32
    assert result.output_tokens == 20 * 16
    assert result.cost_microusd == 0
    assert [action.action_type for action in result.actions] == [
        "read",
        "navigate",
        "fill",
        "fill",
        "click",
        "navigate",
        "fill",
        "fill",
        "click",
        "navigate",
        "fill",
        "fill",
        "fill",
        "click",
        "navigate",
        "fill",
        "fill",
        "click",
        "navigate",
        "finish",
    ]
    assert browser.closed is True


async def test_repetition_and_no_progress_limits_close_safely() -> None:
    repeated_browser = FakeBrowserClient(same_image=True)
    repeated = await VisionAgentLoop(
        repeated_browser, DeterministicFakeVisionModel("repeat_wait")
    ).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        VisionAgentBudget(max_repeated_actions=2, max_no_progress=8),
    )
    assert repeated.status == "repeated_action_limit"
    assert repeated.action_count == 2

    no_progress_browser = FakeBrowserClient(same_image=True)
    no_progress = await VisionAgentLoop(
        no_progress_browser, DeterministicFakeVisionModel("repeat_wait")
    ).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        VisionAgentBudget(max_repeated_actions=5, max_no_progress=1),
    )
    assert no_progress.status == "no_progress_limit"
    assert no_progress_browser.closed is True


@dataclass
class UsageModel:
    usage: ModelUsage

    async def complete(self, _: VisionModelContext) -> RawModelResponse:
        return RawModelResponse(
            content=(
                '{"schema_version":"w5-vision-model-decision/1.0","action":'
                '{"schema_version":"w5-vision-action/1.0","action_id":"act_finish",'
                '"type":"finish","summary":"done"}}'
            ),
            usage=self.usage,
        )


class CapturingModel:
    def __init__(self) -> None:
        self.contexts: list[VisionModelContext] = []

    async def complete(self, context: VisionModelContext) -> RawModelResponse:
        self.contexts.append(context)
        if len(self.contexts) == 1:
            grounding = context.observation.groundings[0]
            action: dict[str, object] = {
                "schema_version": "w5-vision-action/1.0",
                "action_id": "act_read",
                "type": "read",
                "observation_id": context.observation.observation_id,
                "screenshot_ref": context.observation.screenshot_ref,
                "grounding_ref": grounding.grounding_ref,
            }
        else:
            action = {
                "schema_version": "w5-vision-action/1.0",
                "action_id": "act_finish",
                "type": "finish",
                "summary": "done",
            }
        return RawModelResponse(
            content=json.dumps(
                {"schema_version": "w5-vision-model-decision/1.0", "action": action},
                separators=(",", ":"),
            ),
            usage=ModelUsage(input_tokens=1, output_tokens=1, cost_microusd=0),
        )


class RaisingModel:
    async def complete(self, _: VisionModelContext) -> RawModelResponse:
        raise ModelCallError(
            "Synthetic visual model failure",
            usage=ModelUsage(input_tokens=10, output_tokens=2, cost_microusd=0),
        )


async def test_context_history_excludes_image_and_grounding_data() -> None:
    browser = FakeBrowserClient()
    model = CapturingModel()
    result = await VisionAgentLoop(browser, model).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        VisionAgentBudget(),
    )
    assert result.status == "finished_ungraded"
    history = model.contexts[1].prior_actions[-1]
    assert "grounded element" in history
    assert "gref_" not in history
    assert "shot_" not in history
    assert "base64" not in history


async def test_token_cost_call_step_and_time_budgets() -> None:
    cases = [
        (
            UsageModel(ModelUsage(input_tokens=2, output_tokens=0, cost_microusd=0)),
            VisionAgentBudget(max_input_tokens=1),
            "input_token_budget_exhausted",
        ),
        (
            UsageModel(ModelUsage(input_tokens=0, output_tokens=2, cost_microusd=0)),
            VisionAgentBudget(max_output_tokens=1),
            "output_token_budget_exhausted",
        ),
        (
            UsageModel(ModelUsage(input_tokens=0, output_tokens=0, cost_microusd=1)),
            VisionAgentBudget(max_cost_microusd=0),
            "cost_budget_exhausted",
        ),
    ]
    for model, budget, expected in cases:
        browser = FakeBrowserClient()
        result = await VisionAgentLoop(browser, model).run(
            "w3-joiner-001", "Synthetic human instruction", budget
        )
        assert result.status == expected
        assert browser.closed is True

    step_browser = FakeBrowserClient()
    step = await VisionAgentLoop(step_browser, DeterministicFakeVisionModel("repeat_wait")).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        VisionAgentBudget(max_steps=1, max_repeated_actions=5, max_no_progress=8),
    )
    assert step.status == "step_budget_exhausted"

    call_browser = FakeBrowserClient()
    call = await VisionAgentLoop(call_browser, DeterministicFakeVisionModel("repeat_wait")).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        VisionAgentBudget(max_model_calls=1, max_repeated_actions=5, max_no_progress=8),
    )
    assert call.status == "model_call_budget_exhausted"

    ticks = iter((0.0, 2.0))
    timed = await VisionAgentLoop(
        FakeBrowserClient(),
        DeterministicFakeVisionModel("finish_immediately"),
        clock=lambda: next(ticks),
    ).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        VisionAgentBudget(max_duration_seconds=1),
    )
    assert timed.status == "time_budget_exhausted"
