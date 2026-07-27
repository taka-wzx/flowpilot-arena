import json
from dataclasses import dataclass

from conftest import FakeBrowserClient, make_observation

from flowpilot_dom_agent.loop import AgentLoop
from flowpilot_dom_agent.model import (
    DeterministicFakeModel,
    ModelCallError,
    ModelContext,
    RawModelResponse,
)
from flowpilot_dom_agent.schemas import (
    ActionResult,
    AgentBudget,
    BrowserAction,
    InteractiveElement,
    ModelUsage,
    Observation,
    SessionCreated,
)


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


class SafeRaisingModel:
    async def complete(self, _: ModelContext) -> RawModelResponse:
        raise ModelCallError(
            "GLM response did not finish normally",
            usage=ModelUsage(input_tokens=10, output_tokens=2, cost_microusd=34),
        )


def make_fill_observation(counter: int) -> Observation:
    observation = make_observation(counter)
    element = InteractiveElement(
        element_ref=f"ref_fill{counter:04d}_1",
        role="textbox",
        name="Employee ID",
        state={
            "disabled": False,
            "checked": None,
            "selected": None,
            "expanded": None,
            "readonly": False,
            "required": True,
        },
        allowed_actions=("fill",),
    )
    return observation.model_copy(update={"interactive_elements": (element,)})


class FillOnlyBrowser:
    def __init__(self) -> None:
        self.counter = 1
        self.closed = False

    async def create_session(self) -> SessionCreated:
        observation = make_fill_observation(self.counter)
        return SessionCreated(
            schema_version="w4-browser-session/1.0",
            session_id=observation.session_id,
            observation=observation,
        )

    async def execute_action(self, session_id: str, action: BrowserAction) -> ActionResult:
        if action.type == "finish":
            self.closed = True
            return ActionResult(
                schema_version="w4-dom-action-result/1.0",
                session_id=session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=True,
                terminal=True,
                message="terminal",
            )
        self.counter += 1
        return ActionResult(
            schema_version="w4-dom-action-result/1.0",
            session_id=session_id,
            action_id=action.action_id,
            action_type=action.type,
            success=True,
            terminal=False,
            message="ok",
            observation=make_fill_observation(self.counter),
        )

    async def close_session(self, _: str) -> None:
        self.closed = True


class FillThenFinishModel:
    def __init__(self) -> None:
        self.contexts: list[ModelContext] = []

    async def complete(self, context: ModelContext) -> RawModelResponse:
        self.contexts.append(context)
        if len(self.contexts) <= 3:
            element = context.observation.interactive_elements[0]
            action = {
                "schema_version": "w4-dom-action/1.0",
                "action_id": f"act_fill_{len(self.contexts)}",
                "type": "fill",
                "observation_id": context.observation.observation_id,
                "element_ref": element.element_ref,
                "text": "31001",
            }
        else:
            action = {
                "schema_version": "w4-dom-action/1.0",
                "action_id": "act_finish_fills",
                "type": "finish",
                "summary": "Synthetic fills complete; grading remains external",
            }
        return RawModelResponse(
            content=(
                '{"schema_version":"w4-model-decision/1.0","action":'
                + json.dumps(action, separators=(",", ":"))
                + "}"
            ),
            usage=ModelUsage(input_tokens=1, output_tokens=1, cost_microusd=0),
        )


async def test_model_exception_closes_browser_safely(fake_browser: FakeBrowserClient) -> None:
    result = await AgentLoop(fake_browser, RaisingModel()).run(
        "w3-joiner-001", "Synthetic human instruction", AgentBudget()
    )
    assert result.status == "model_error"
    assert result.model_calls == 0
    assert result.action_count == 0
    assert fake_browser.closed is True

    safe_browser = FakeBrowserClient()
    safe_result = await AgentLoop(safe_browser, SafeRaisingModel()).run(
        "w3-joiner-001",
        "Synthetic human instruction",
        AgentBudget(max_cost_microusd=100),
    )
    assert safe_result.status == "model_error"
    assert safe_result.terminal_reason == "GLM response did not finish normally"
    assert safe_result.model_calls == 1
    assert safe_result.input_tokens == 10
    assert safe_result.output_tokens == 2
    assert safe_result.cost_microusd == 34
    assert safe_browser.closed is True


async def test_successful_fills_are_progress_and_history_names_field_without_value() -> None:
    browser = FillOnlyBrowser()
    model = FillThenFinishModel()
    result = await AgentLoop(browser, model).run(
        "w3-joiner-001",
        "Use supplied employee ID 31001",
        AgentBudget(
            max_steps=6,
            max_model_calls=6,
            max_repeated_actions=5,
            max_no_progress=1,
        ),
    )

    assert result.status == "finished_ungraded"
    assert result.action_count == 4
    assert browser.closed is True
    assert "Employee ID" in model.contexts[1].prior_actions[-1]
    assert "31001" not in model.contexts[1].prior_actions[-1]


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
