import asyncio

import pytest
from conftest import (
    hybrid_dom_observation,
    hybrid_vision_observation,
    supplied_values_brief,
)

from flowpilot_hybrid_agent.loop import HybridAgentLoop
from flowpilot_hybrid_agent.model import (
    DeterministicFakeHybridModel,
    HybridModelContext,
    ModelCallError,
    RawModelResponse,
)
from flowpilot_hybrid_agent.schemas import (
    HybridActionEnvelope,
    HybridActionResult,
    HybridAgentBudget,
    HybridSessionCreated,
    ModelUsage,
)


class FakeHybridBrowser:
    def __init__(self, *, image_bytes: int = 20, capture_duration_ms: int = 1) -> None:
        self.current = hybrid_dom_observation(generation=1)
        self.closed = False
        self._generation = 1
        self._image_bytes = image_bytes
        self._capture_duration_ms = capture_duration_ms

    async def create_session(self) -> HybridSessionCreated:
        return HybridSessionCreated(
            session_id="bw_abcdefghijklmnop",
            observation=self.current,
        )

    async def request_observation(self, session_id: str, modality: str):
        assert session_id == "bw_abcdefghijklmnop"
        assert modality == "vision"
        self._generation += 1
        self.current = hybrid_vision_observation(
            generation=self._generation,
            image_bytes=self._image_bytes,
            capture_duration_ms=self._capture_duration_ms,
        )
        return self.current

    async def execute_action(
        self,
        session_id: str,
        action: HybridActionEnvelope,
    ) -> HybridActionResult:
        assert session_id == "bw_abcdefghijklmnop"
        assert action.session_id == session_id
        assert action.generation == self.current.generation
        assert action.modality == self.current.modality
        if action.action.type == "finish":
            return HybridActionResult(
                session_id=session_id,
                action_id=action.action.action_id,
                modality=action.modality,
                action_type="finish",
                success=True,
                terminal=True,
                message="Synthetic finish",
            )
        self._generation += 1
        if action.modality == "dom":
            self.current = hybrid_dom_observation(generation=self._generation)
        else:
            self.current = hybrid_vision_observation(
                generation=self._generation,
                image_bytes=self._image_bytes,
                capture_duration_ms=self._capture_duration_ms,
            )
        return HybridActionResult(
            session_id=session_id,
            action_id=action.action.action_id,
            modality=action.modality,
            action_type=action.action.type,
            success=True,
            terminal=False,
            message="Synthetic action",
            observation=self.current,
        )

    async def close_session(self, _: str) -> None:
        self.closed = True


async def test_loop_completes_fake_workflow_through_a_real_router_switch() -> None:
    browser = FakeHybridBrowser()
    loop = HybridAgentLoop(
        browser,  # type: ignore[arg-type]
        DeterministicFakeHybridModel("complete_joiner_dom_to_vision"),
    )
    result = await loop.run(
        "w3-joiner-001",
        supplied_values_brief(),
        "visual_recovery",
        budget=result_budget(),
    )

    assert result.status == "finished_ungraded"
    assert result.steps == 20
    assert result.action_count == 20
    assert result.model_calls == 20
    assert result.switches == 1
    assert result.dom_observation_count == 2
    assert result.compressed_dom_bytes > 0
    assert result.image_count == 19
    assert result.cost_microusd == 0
    assert any(route.reason_code == "trusted_visual_recovery" for route in result.routes)
    assert result.actions[0].modality == "dom"
    assert all(action.modality == "vision" for action in result.actions[1:])


async def test_loop_enforces_repeated_action_limit_without_leaking_browser_state() -> None:
    browser = FakeHybridBrowser()
    loop = HybridAgentLoop(browser, DeterministicFakeHybridModel("repeat_wait"))  # type: ignore[arg-type]
    result = await loop.run(
        "w3-joiner-001",
        supplied_values_brief(),
        "standard",
        result_budget(),
    )

    assert result.status == "repeated_action_limit"
    assert result.steps == 2
    assert browser.closed is True


class UsageLessModelError:
    async def complete(self, _: object) -> object:
        raise ModelCallError("Synthetic model failure without usage")


async def test_loop_counts_a_model_call_when_it_fails_without_usage() -> None:
    browser = FakeHybridBrowser()
    loop = HybridAgentLoop(browser, UsageLessModelError())  # type: ignore[arg-type]
    result = await loop.run(
        "w3-joiner-001",
        supplied_values_brief(),
        "standard",
        result_budget(),
    )

    assert result.status == "model_error"
    assert result.model_calls == 1
    assert browser.closed is True


@pytest.mark.parametrize(
    ("scenario", "overrides", "expected_status"),
    [
        (
            "repeat_wait",
            {"max_model_calls": 1, "max_repeated_actions": 5},
            "model_call_budget_exhausted",
        ),
        ("repeat_wait", {"max_steps": 1, "max_repeated_actions": 5}, "step_budget_exhausted"),
        (
            "repeat_wait",
            {"max_no_progress": 1, "max_repeated_actions": 5},
            "no_progress_limit",
        ),
        (
            "repeat_wait",
            {"max_dom_observations": 1, "max_repeated_actions": 5},
            "dom_observation_budget_exhausted",
        ),
        (
            "finish_immediately",
            {"max_dom_observation_bytes": 1},
            "dom_observation_byte_budget_exhausted",
        ),
        ("finish_immediately", {"max_compressed_dom_bytes": 1}, "compressed_dom_budget_exhausted"),
        ("finish_immediately", {"max_input_tokens": 1}, "input_token_budget_exhausted"),
        ("finish_immediately", {"max_output_tokens": 1}, "output_token_budget_exhausted"),
        (
            "complete_joiner_dom_to_vision",
            {"max_switches": 0},
            "switch_budget_exhausted",
        ),
    ],
)
async def test_loop_enforces_total_hard_budgets(
    scenario: str,
    overrides: dict[str, int],
    expected_status: str,
) -> None:
    browser = FakeHybridBrowser()
    loop = HybridAgentLoop(browser, DeterministicFakeHybridModel(scenario))  # type: ignore[arg-type]
    result = await loop.run(
        "w3-joiner-001",
        supplied_values_brief(),
        "visual_recovery" if scenario == "complete_joiner_dom_to_vision" else "standard",
        result_budget(**overrides),
    )

    assert result.status == expected_status
    assert browser.closed is True


@pytest.mark.parametrize(
    ("browser_kwargs", "budget_overrides", "expected_status"),
    [
        ({}, {"max_images": 1}, "image_budget_exhausted"),
        ({"image_bytes": 100_000}, {"max_image_bytes": 184_320}, "image_byte_budget_exhausted"),
        ({}, {"max_image_pixels": 518_400}, "image_pixel_budget_exhausted"),
        (
            {"capture_duration_ms": 2_000},
            {"max_capture_ms": 3_000},
            "capture_time_budget_exhausted",
        ),
    ],
)
async def test_loop_enforces_visual_totals_across_the_switch(
    browser_kwargs: dict[str, int],
    budget_overrides: dict[str, int],
    expected_status: str,
) -> None:
    browser = FakeHybridBrowser(**browser_kwargs)
    loop = HybridAgentLoop(
        browser,  # type: ignore[arg-type]
        DeterministicFakeHybridModel("complete_joiner_dom_to_vision"),
    )
    result = await loop.run(
        "w3-joiner-001",
        supplied_values_brief(),
        "visual_recovery",
        result_budget(**budget_overrides),
    )

    assert result.status == expected_status
    assert result.switches == 1
    assert browser.closed is True


class UsageOverrideModel:
    def __init__(self, usage: ModelUsage) -> None:
        self._base = DeterministicFakeHybridModel("finish_immediately")
        self._usage = usage

    async def complete(self, context: HybridModelContext) -> RawModelResponse:
        response = await self._base.complete(context)
        return RawModelResponse(content=response.content, usage=self._usage)


async def test_loop_enforces_cost_and_monotonic_time_and_cleans_up() -> None:
    cost_browser = FakeHybridBrowser()
    cost_loop = HybridAgentLoop(
        cost_browser,  # type: ignore[arg-type]
        UsageOverrideModel(ModelUsage(input_tokens=0, output_tokens=0, cost_microusd=1)),
    )
    cost_result = await cost_loop.run(
        "w3-joiner-001",
        supplied_values_brief(),
        "standard",
        result_budget(max_cost_microusd=0),
    )
    assert cost_result.status == "cost_budget_exhausted"
    assert cost_browser.closed is True

    ticks = iter((0.0, 301.0, 301.0))
    time_browser = FakeHybridBrowser()
    time_loop = HybridAgentLoop(
        time_browser,  # type: ignore[arg-type]
        DeterministicFakeHybridModel("finish_immediately"),
        clock=lambda: next(ticks),
    )
    time_result = await time_loop.run(
        "w3-joiner-001",
        supplied_values_brief(),
        "standard",
        result_budget(),
    )
    assert time_result.status == "time_budget_exhausted"
    assert time_browser.closed is True


class CancelledModel:
    async def complete(self, _: HybridModelContext) -> RawModelResponse:
        raise asyncio.CancelledError


async def test_loop_closes_the_hybrid_session_when_cancelled() -> None:
    browser = FakeHybridBrowser()
    loop = HybridAgentLoop(browser, CancelledModel())  # type: ignore[arg-type]
    with pytest.raises(asyncio.CancelledError):
        await loop.run(
            "w3-joiner-001",
            supplied_values_brief(),
            "standard",
            result_budget(),
        )
    assert browser.closed is True


def result_budget(**overrides: int) -> HybridAgentBudget:
    values = HybridAgentBudget().model_dump()
    values.update(overrides)
    return HybridAgentBudget.model_validate(values)
