from dataclasses import dataclass

from conftest import FakeBrowserClient

from flowpilot_dom_agent.loop import AgentLoop
from flowpilot_dom_agent.model import DeterministicFakeModel, ModelContext, RawModelResponse
from flowpilot_dom_agent.schemas import AgentBudget, ModelUsage


async def test_finish_is_explicitly_ungraded(fake_browser: FakeBrowserClient) -> None:
    result = await AgentLoop(fake_browser, DeterministicFakeModel("inspect_then_finish")).run(
        "w3-joiner-001", "Synthetic human instruction", AgentBudget()
    )
    assert result.status == "finished_ungraded"
    assert result.steps == 2
    assert result.action_count == 2
    assert result.cost_microusd == 0
    assert fake_browser.closed is True
    assert "grade" in result.terminal_reason.lower()


async def test_invalid_json_stops_without_browser_action(fake_browser: FakeBrowserClient) -> None:
    result = await AgentLoop(fake_browser, DeterministicFakeModel("invalid_json")).run(
        "w3-joiner-001", "Synthetic human instruction", AgentBudget()
    )
    assert result.status == "invalid_model_output"
    assert result.action_count == 0
    assert result.model_calls == 1
    assert fake_browser.closed is True


async def test_repeated_action_and_no_progress_limits(fake_browser: FakeBrowserClient) -> None:
    repeated = await AgentLoop(fake_browser, DeterministicFakeModel("repeat_wait")).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        AgentBudget(max_repeated_actions=2, max_no_progress=8),
    )
    assert repeated.status == "repeated_action_limit"
    assert repeated.action_count == 2

    second_browser = FakeBrowserClient()
    no_progress = await AgentLoop(second_browser, DeterministicFakeModel("repeat_wait")).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        AgentBudget(max_repeated_actions=5, max_no_progress=1),
    )
    assert no_progress.status == "no_progress_limit"


@dataclass
class UsageModel:
    usage: ModelUsage

    async def complete(self, _: ModelContext) -> RawModelResponse:
        return RawModelResponse(
            content=(
                '{"schema_version":"w4-model-decision/1.0","action":'
                '{"schema_version":"w4-dom-action/1.0","action_id":"act_finish",'
                '"type":"finish","summary":"done"}}'
            ),
            usage=self.usage,
        )


class RaisingModel:
    async def complete(self, _: ModelContext) -> RawModelResponse:
        raise RuntimeError("synthetic model failure")


async def test_model_exception_closes_browser_safely(fake_browser: FakeBrowserClient) -> None:
    result = await AgentLoop(fake_browser, RaisingModel()).run(
        "w3-joiner-001", "Synthetic human instruction", AgentBudget()
    )
    assert result.status == "model_error"
    assert result.model_calls == 0
    assert result.action_count == 0
    assert fake_browser.closed is True


async def test_token_cost_step_call_and_time_budgets() -> None:
    cases = [
        (
            UsageModel(ModelUsage(input_tokens=2, output_tokens=0, cost_microusd=0)),
            AgentBudget(max_input_tokens=1),
            "input_token_budget_exhausted",
        ),
        (
            UsageModel(ModelUsage(input_tokens=0, output_tokens=2, cost_microusd=0)),
            AgentBudget(max_output_tokens=1),
            "output_token_budget_exhausted",
        ),
        (
            UsageModel(ModelUsage(input_tokens=0, output_tokens=0, cost_microusd=1)),
            AgentBudget(max_cost_microusd=0),
            "cost_budget_exhausted",
        ),
    ]
    for model, budget, expected in cases:
        browser = FakeBrowserClient()
        result = await AgentLoop(browser, model).run(
            "w3-joiner-001", "Synthetic human instruction", budget
        )
        assert result.status == expected
        assert browser.closed is True

    step_browser = FakeBrowserClient()
    step = await AgentLoop(step_browser, DeterministicFakeModel("repeat_wait")).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        AgentBudget(max_steps=1, max_repeated_actions=5, max_no_progress=8),
    )
    assert step.status == "step_budget_exhausted"

    call_browser = FakeBrowserClient()
    call = await AgentLoop(call_browser, DeterministicFakeModel("repeat_wait")).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        AgentBudget(max_model_calls=1, max_repeated_actions=5, max_no_progress=8),
    )
    assert call.status == "model_call_budget_exhausted"

    ticks = iter((0.0, 2.0))
    time_browser = FakeBrowserClient()
    timed = await AgentLoop(
        time_browser,
        DeterministicFakeModel("finish_immediately"),
        clock=lambda: next(ticks),
    ).run("w3-joiner-001", "Synthetic human instruction", AgentBudget(max_duration_seconds=1))
    assert timed.status == "time_budget_exhausted"
    assert time_browser.closed is True
