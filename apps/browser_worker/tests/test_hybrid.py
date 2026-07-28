import asyncio
import base64
from dataclasses import replace
from typing import Any

import pytest
from pydantic import TypeAdapter

from flowpilot_browser_worker.config import WorkerConfig, WorkerLimits
from flowpilot_browser_worker.hybrid import dom_route_signals, safe_route_error
from flowpilot_browser_worker.observation import ElementTarget, ObservationBuild
from flowpilot_browser_worker.runtime import BrowserRuntime, HybridObservationError
from flowpilot_browser_worker.schemas import (
    HybridActionEnvelope,
    HybridObservationRequest,
    InteractiveElement,
    Observation,
    VisionObservation,
    VisualBounds,
    VisualGrounding,
)
from flowpilot_browser_worker.vision import VisionObservationBuild


class FakeMouse:
    async def wheel(self, _: int, __: int) -> None:
        pass


class FakeLocator:
    async def click(self) -> None:
        pass

    async def fill(self, _: str) -> None:
        pass

    async def select_option(self, *, value: str) -> None:
        assert value == "choice"

    async def scroll_into_view_if_needed(self) -> None:
        pass


class FakePage:
    def __init__(self) -> None:
        self.url = "about:blank"
        self.closed = False
        self.mouse = FakeMouse()

    def set_default_timeout(self, _: int) -> None:
        pass

    def set_default_navigation_timeout(self, _: int) -> None:
        pass

    async def route(self, _: str, __: object) -> None:
        pass

    async def goto(self, url: str, *, wait_until: str) -> None:
        assert wait_until == "domcontentloaded"
        self.url = url

    async def wait_for_timeout(self, _: int) -> None:
        pass

    async def close(self) -> None:
        self.closed = True


class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self._page = page
        self.closed = False

    async def new_page(self) -> FakePage:
        return self._page

    async def close(self) -> None:
        self.closed = True


class FakeBrowser:
    def __init__(self, page: FakePage) -> None:
        self._context = FakeContext(page)
        self.closed = False

    async def new_context(self, **_: object) -> FakeContext:
        return self._context

    async def close(self) -> None:
        self.closed = True


class FakeChromium:
    def __init__(self, browser: FakeBrowser) -> None:
        self._browser = browser

    async def launch(self, *, headless: bool) -> FakeBrowser:
        assert headless is True
        return self._browser


class FakePlaywright:
    def __init__(self, browser: FakeBrowser) -> None:
        self.chromium = FakeChromium(browser)
        self.stopped = False

    async def stop(self) -> None:
        self.stopped = True


class FakeStarter:
    def __init__(self, playwright: FakePlaywright) -> None:
        self._playwright = playwright

    async def start(self) -> FakePlaywright:
        return self._playwright


class StubDomBuilder:
    def __init__(self, locator: FakeLocator) -> None:
        self._locator = locator
        self._counter = 0

    async def build(
        self,
        page: FakePage,
        session_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> ObservationBuild:
        self._counter += 1
        nonce = f"hybrid{self._counter:04d}"
        element_ref = f"ref_{nonce}_1"
        element = InteractiveElement(
            element_ref=element_ref,
            role="textbox",
            name="Synthetic field",
            state={},
            allowed_actions=("click", "fill", "select", "read", "scroll"),
            options=("Choice",),
        )
        observation = Observation(
            session_id=session_id,
            observation_id=f"obs_{nonce}",
            current_url=page.url,
            page_title="Synthetic",
            semantic_nodes=(),
            interactive_elements=(element,),
            last_action=kwargs.get("last_action") or (args[0] if args else None),
            page_error=kwargs.get("page_error"),
            truncated=False,
        )
        target = ElementTarget(
            locator=self._locator,  # type: ignore[arg-type]
            allowed_actions=element.allowed_actions,
            input_type="text",
            safe_name="Synthetic field",
            option_values={"Choice": "choice"},
        )
        return ObservationBuild(observation=observation, references={element_ref: target})


class StubVisionBuilder:
    def __init__(self, locator: FakeLocator) -> None:
        self._locator = locator
        self._counter = 0

    async def build(
        self,
        _: FakePage,
        session_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> VisionObservationBuild:
        self._counter += 1
        nonce = f"hybridvisual{self._counter:04d}"
        grounding_ref = f"gref_{nonce}_1"
        image = b"\xff\xd8synthetic\xff\xd9"
        observation = VisionObservation(
            session_id=session_id,
            observation_id=f"vobs_{nonce}",
            screenshot_ref=f"shot_{nonce}",
            image_mime_type="image/jpeg",
            image_base64=base64.b64encode(image).decode("ascii"),
            image_width=960,
            image_height=540,
            image_bytes=len(image),
            capture_duration_ms=1,
            groundings=(
                VisualGrounding(
                    grounding_ref=grounding_ref,
                    bounds=VisualBounds(x=1, y=1, width=10, height=10),
                    allowed_actions=("click", "fill", "select", "read", "scroll"),
                ),
            ),
            last_action=kwargs.get("last_action") or (args[0] if args else None),
            page_error=kwargs.get("page_error"),
            truncated=False,
        )
        target = ElementTarget(
            locator=self._locator,  # type: ignore[arg-type]
            allowed_actions=("click", "fill", "select", "read", "scroll"),
            input_type="text",
            safe_name="Synthetic field",
            option_values={"Choice": "choice"},
        )
        return VisionObservationBuild(observation=observation, references={grounding_ref: target})


def make_runtime(
    monkeypatch: pytest.MonkeyPatch,
    limits: WorkerLimits | None = None,
) -> tuple[BrowserRuntime, FakePage, FakeBrowser, FakePlaywright]:
    page = FakePage()
    browser = FakeBrowser(page)
    playwright = FakePlaywright(browser)
    monkeypatch.setattr(
        "flowpilot_browser_worker.runtime.async_playwright",
        lambda: FakeStarter(playwright),
    )
    locator = FakeLocator()
    runtime = BrowserRuntime(
        WorkerConfig(
            sandbox_origin="http://sandbox-web",
            limits=limits or WorkerLimits(),
        ),
        session_id_factory=lambda: "bw_abcdefghijklmnop",
        observation_builder=StubDomBuilder(locator),  # type: ignore[arg-type]
        vision_observation_builder=StubVisionBuilder(locator),  # type: ignore[arg-type]
    )
    return runtime, page, browser, playwright


def envelope(payload: dict[str, object]) -> HybridActionEnvelope:
    return TypeAdapter(HybridActionEnvelope).validate_python(payload)


async def test_hybrid_uses_one_session_and_invalidates_all_cross_mode_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime, page, browser, playwright = make_runtime(monkeypatch)
    created = await runtime.create_hybrid_session()
    assert created.observation.modality == "dom"
    first_dom = created.observation
    assert first_dom.generation == 1

    dom_read = envelope(
        {
            "schema_version": "w6-hybrid-action-envelope/1.0",
            "session_id": created.session_id,
            "generation": first_dom.generation,
            "modality": "dom",
            "action": {
                "action_id": "act_dom_read",
                "type": "read",
                "observation_id": first_dom.observation.observation_id,
                "element_ref": first_dom.observation.interactive_elements[0].element_ref,
            },
        }
    )
    read_result = await runtime.execute_hybrid_action(created.session_id, dom_read)
    assert read_result.success is True
    assert read_result.observation is not None and read_result.observation.modality == "dom"

    visual = await runtime.request_hybrid_observation(
        created.session_id,
        HybridObservationRequest(modality="vision"),
    )
    assert visual.modality == "vision"
    assert visual.generation == 3

    wrong_mode = await runtime.execute_hybrid_action(
        created.session_id,
        envelope(
            {
                "schema_version": "w6-hybrid-action-envelope/1.0",
                "session_id": created.session_id,
                "generation": visual.generation,
                "modality": "dom",
                "action": {
                    "action_id": "act_wrong_mode",
                    "type": "read",
                    "observation_id": first_dom.observation.observation_id,
                    "element_ref": first_dom.observation.interactive_elements[0].element_ref,
                },
            }
        ),
    )
    assert wrong_mode.success is False
    assert wrong_mode.error_category == "invalid_modality"
    assert wrong_mode.observation is not None and wrong_mode.observation.modality == "vision"

    stale_visual = envelope(
        {
            "schema_version": "w6-hybrid-action-envelope/1.0",
            "session_id": created.session_id,
            "generation": visual.generation,
            "modality": "vision",
            "action": {
                "action_id": "act_stale_visual",
                "type": "read",
                "observation_id": visual.observation.observation_id,
                "screenshot_ref": visual.observation.screenshot_ref,
                "grounding_ref": visual.observation.groundings[0].grounding_ref,
            },
        }
    )
    stale_result = await runtime.execute_hybrid_action(created.session_id, stale_visual)
    assert stale_result.success is False
    assert stale_result.error_category == "stale_hybrid_ref"
    assert stale_result.observation is not None and stale_result.observation.modality == "vision"
    current_visual = stale_result.observation

    wrong_mode_finish = await runtime.execute_hybrid_action(
        created.session_id,
        envelope(
            {
                "schema_version": "w6-hybrid-action-envelope/1.0",
                "session_id": created.session_id,
                "generation": current_visual.generation,
                "modality": "dom",
                "action": {
                    "action_id": "act_wrong_mode_finish",
                    "type": "finish",
                    "summary": "Must not close a Vision observation",
                },
            }
        ),
    )
    assert wrong_mode_finish.success is False
    assert wrong_mode_finish.terminal is False
    assert wrong_mode_finish.error_category == "invalid_modality"
    assert wrong_mode_finish.observation is not None
    assert wrong_mode_finish.observation.modality == "vision"
    assert page.closed is False
    current_visual = wrong_mode_finish.observation

    terminal = await runtime.execute_hybrid_action(
        created.session_id,
        envelope(
            {
                "schema_version": "w6-hybrid-action-envelope/1.0",
                "session_id": created.session_id,
                "generation": current_visual.generation,
                "modality": "vision",
                "action": {
                    "action_id": "act_finish",
                    "type": "finish",
                    "summary": "Synthetic completion",
                },
            }
        ),
    )
    assert terminal.terminal is True and terminal.success is True
    assert page.closed and browser.closed and playwright.stopped


async def test_hybrid_observation_limit_closes_the_one_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limits = replace(WorkerLimits(), max_hybrid_observations=1)
    runtime, page, browser, playwright = make_runtime(monkeypatch, limits)
    created = await runtime.create_hybrid_session()
    assert created.observation.modality == "dom"

    with pytest.raises(HybridObservationError, match="observation budget"):
        await runtime.request_hybrid_observation(
            created.session_id,
            HybridObservationRequest(modality="vision"),
        )
    assert page.closed and browser.closed and playwright.stopped


async def test_hybrid_non_element_actions_require_current_session_and_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime, page, browser, playwright = make_runtime(monkeypatch)
    created = await runtime.create_hybrid_session()
    refreshed = await runtime.request_hybrid_observation(
        created.session_id,
        HybridObservationRequest(modality="dom"),
    )
    assert refreshed.generation == 2

    stale_finish = await runtime.execute_hybrid_action(
        created.session_id,
        envelope(
            {
                "schema_version": "w6-hybrid-action-envelope/1.0",
                "session_id": created.session_id,
                "generation": 1,
                "modality": "dom",
                "action": {
                    "action_id": "act_stale_finish",
                    "type": "finish",
                    "summary": "This stale finish must not terminate the task",
                },
            }
        ),
    )
    assert stale_finish.terminal is False
    assert stale_finish.error_category == "stale_hybrid_ref"
    assert stale_finish.observation is not None
    assert page.closed is False

    wrong_session_wait = await runtime.execute_hybrid_action(
        created.session_id,
        envelope(
            {
                "schema_version": "w6-hybrid-action-envelope/1.0",
                "session_id": "bw_qrstuvwxyzABCDEF",
                "generation": stale_finish.observation.generation,
                "modality": "dom",
                "action": {
                    "action_id": "act_wrong_session_wait",
                    "type": "wait",
                    "duration_ms": 1,
                },
            }
        ),
    )
    assert wrong_session_wait.terminal is False
    assert wrong_session_wait.error_category == "unknown_hybrid_ref"
    assert wrong_session_wait.observation is not None
    assert page.closed is False

    terminal = await runtime.execute_hybrid_action(
        created.session_id,
        envelope(
            {
                "schema_version": "w6-hybrid-action-envelope/1.0",
                "session_id": created.session_id,
                "generation": wrong_session_wait.observation.generation,
                "modality": "dom",
                "action": {
                    "action_id": "act_current_finish",
                    "type": "finish",
                    "summary": "Current generation may terminate ungraded",
                },
            }
        ),
    )
    assert terminal.terminal is True and terminal.success is True
    assert page.closed and browser.closed and playwright.stopped


async def test_hybrid_visual_actions_reject_forged_and_stale_current_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime, _, _, _ = make_runtime(monkeypatch)
    created = await runtime.create_hybrid_session()
    visual = await runtime.request_hybrid_observation(
        created.session_id,
        HybridObservationRequest(modality="vision"),
    )
    grounding = visual.observation.groundings[0]
    current_read = envelope(
        {
            "schema_version": "w6-hybrid-action-envelope/1.0",
            "session_id": created.session_id,
            "generation": visual.generation,
            "modality": "vision",
            "action": {
                "action_id": "act_visual_current",
                "type": "read",
                "observation_id": visual.observation.observation_id,
                "screenshot_ref": visual.observation.screenshot_ref,
                "grounding_ref": grounding.grounding_ref,
            },
        }
    )
    current_result = await runtime.execute_hybrid_action(created.session_id, current_read)
    assert current_result.success is True
    assert current_result.observation is not None
    current_visual = current_result.observation

    stale_result = await runtime.execute_hybrid_action(
        created.session_id,
        envelope(
            {
                "schema_version": "w6-hybrid-action-envelope/1.0",
                "session_id": created.session_id,
                "generation": current_visual.generation,
                "modality": "vision",
                "action": {
                    "action_id": "act_visual_stale_refs",
                    "type": "read",
                    "observation_id": visual.observation.observation_id,
                    "screenshot_ref": visual.observation.screenshot_ref,
                    "grounding_ref": grounding.grounding_ref,
                },
            }
        ),
    )
    assert stale_result.error_category == "stale_hybrid_ref"
    assert stale_result.observation is not None
    current_visual = stale_result.observation

    forged_result = await runtime.execute_hybrid_action(
        created.session_id,
        envelope(
            {
                "schema_version": "w6-hybrid-action-envelope/1.0",
                "session_id": created.session_id,
                "generation": current_visual.generation,
                "modality": "vision",
                "action": {
                    "action_id": "act_visual_forged_ref",
                    "type": "read",
                    "observation_id": current_visual.observation.observation_id,
                    "screenshot_ref": current_visual.observation.screenshot_ref,
                    "grounding_ref": "gref_forged0001",
                },
            }
        ),
    )
    assert forged_result.error_category == "unknown_hybrid_ref"
    await runtime.close_hybrid_session(created.session_id)


async def test_hybrid_dom_byte_limit_closes_startup_handles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limits = replace(WorkerLimits(), max_hybrid_dom_observation_bytes=1)
    runtime, page, browser, playwright = make_runtime(monkeypatch, limits)
    with pytest.raises(HybridObservationError, match="DOM observation budget"):
        await runtime.create_hybrid_session()
    assert page.closed and browser.closed and playwright.stopped


def test_route_signals_are_bounded_structural_metadata_only() -> None:
    disabled = InteractiveElement(
        element_ref="ref_disabled0001",
        role="textbox",
        name="Untrusted page label",
        state={"disabled": True},
        allowed_actions=("read",),
    )
    observation = Observation(
        session_id="bw_abcdefghijklmnop",
        observation_id="obs_routes001",
        current_url="http://sandbox-web/hris",
        page_title="Untrusted title",
        semantic_nodes=(),
        interactive_elements=(disabled,),
        truncated=False,
    )
    signals = dom_route_signals(observation)
    assert signals.dom_structure == "empty"
    assert signals.dom_interactive_count == 0
    assert signals.dom_observation_bytes == len(observation.model_dump_json().encode("utf-8"))
    assert set(signals.model_dump()) == {
        "dom_structure",
        "dom_interactive_count",
        "dom_observation_bytes",
        "last_action_error_category",
    }
    assert safe_route_error("stale_visual_ref") == "stale_reference"
    assert safe_route_error("unknown_element_ref") == "unknown_reference"
    assert safe_route_error("navigation_budget_exhausted") == "budget_exhausted"


class CancelledDomBuilder:
    async def build(self, *_: object, **__: object) -> ObservationBuild:
        raise asyncio.CancelledError


async def test_hybrid_startup_cancellation_closes_every_browser_handle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime, page, browser, playwright = make_runtime(monkeypatch)
    runtime._builder = CancelledDomBuilder()  # type: ignore[assignment]
    with pytest.raises(asyncio.CancelledError):
        await runtime.create_hybrid_session()
    assert page.closed and browser.closed and playwright.stopped
