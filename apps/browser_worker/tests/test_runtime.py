import asyncio
from dataclasses import replace
from typing import Any

import pytest

from flowpilot_browser_worker.config import WorkerConfig
from flowpilot_browser_worker.observation import ElementTarget, ObservationBuild
from flowpilot_browser_worker.policy import PolicyViolation
from flowpilot_browser_worker.runtime import BrowserRuntime
from flowpilot_browser_worker.schemas import (
    ClickAction,
    FailAction,
    FillAction,
    FinishAction,
    InteractiveElement,
    NavigateAction,
    Observation,
    ReadAction,
    ScrollAction,
    SelectAction,
    WaitAction,
)


class FakeMouse:
    def __init__(self) -> None:
        self.wheels: list[tuple[int, int]] = []

    async def wheel(self, x: int, y: int) -> None:
        self.wheels.append((x, y))


class FakeLocator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    async def click(self) -> None:
        self.calls.append(("click", None))

    async def fill(self, text: str) -> None:
        self.calls.append(("fill", text))

    async def select_option(self, *, value: str) -> None:
        self.calls.append(("select", value))

    async def scroll_into_view_if_needed(self) -> None:
        self.calls.append(("scroll", None))


class FakePage:
    def __init__(self, redirect: bool = False) -> None:
        self.url = "about:blank"
        self.redirect = redirect
        self.closed = False
        self.mouse = FakeMouse()
        self.routes: list[Any] = []

    def set_default_timeout(self, _: int) -> None:
        pass

    def set_default_navigation_timeout(self, _: int) -> None:
        pass

    async def route(self, _: str, handler: Any) -> None:
        self.routes.append(handler)

    async def goto(self, url: str, *, wait_until: str) -> None:
        assert wait_until == "domcontentloaded"
        self.url = "https://example.invalid/escape" if self.redirect else url

    async def wait_for_timeout(self, _: int) -> None:
        pass

    async def close(self) -> None:
        self.closed = True


class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self.page = page
        self.closed = False

    async def new_page(self) -> FakePage:
        return self.page

    async def close(self) -> None:
        self.closed = True


class FakeBrowser:
    def __init__(self, page: FakePage) -> None:
        self.context = FakeContext(page)
        self.closed = False

    async def new_context(self, **_: Any) -> FakeContext:
        return self.context

    async def close(self) -> None:
        self.closed = True


class FakeChromium:
    def __init__(self, browser: FakeBrowser) -> None:
        self.browser = browser

    async def launch(self, *, headless: bool) -> FakeBrowser:
        assert headless is True
        return self.browser


class FakePlaywright:
    def __init__(self, browser: FakeBrowser) -> None:
        self.chromium = FakeChromium(browser)
        self.stopped = False

    async def stop(self) -> None:
        self.stopped = True


class FakeStarter:
    def __init__(self, playwright: FakePlaywright) -> None:
        self.playwright = playwright

    async def start(self) -> FakePlaywright:
        return self.playwright


class StubObservationBuilder:
    def __init__(self, locator: FakeLocator) -> None:
        self.locator = locator
        self.counter = 0

    async def build(
        self, page: FakePage, session_id: str, *args: Any, **kwargs: Any
    ) -> ObservationBuild:
        self.counter += 1
        observation_id = f"obs_nonce{self.counter:04d}"
        element_ref = f"ref_nonce{self.counter:04d}_1"
        element = InteractiveElement(
            element_ref=element_ref,
            role="textbox",
            name="Synthetic field",
            state={
                "disabled": False,
                "checked": None,
                "selected": None,
                "expanded": None,
                "readonly": False,
                "required": False,
            },
            allowed_actions=("click", "fill", "select", "read", "scroll"),
            options=("Choice",),
        )
        observation = Observation(
            session_id=session_id,
            observation_id=observation_id,
            current_url=page.url,
            page_title="Synthetic",
            semantic_nodes=(),
            interactive_elements=(element,),
            last_action=kwargs.get("last_action") or (args[0] if args else None),
            page_error=kwargs.get("page_error"),
            truncated=False,
        )
        target = ElementTarget(
            locator=self.locator,
            allowed_actions=element.allowed_actions,
            input_type="text",
            safe_name="Synthetic field",
            option_values={"Choice": "choice"},
        )
        return ObservationBuild(observation=observation, references={element_ref: target})


def make_runtime(monkeypatch: pytest.MonkeyPatch, config: WorkerConfig, redirect: bool = False):
    page = FakePage(redirect=redirect)
    browser = FakeBrowser(page)
    playwright = FakePlaywright(browser)
    monkeypatch.setattr(
        "flowpilot_browser_worker.runtime.async_playwright", lambda: FakeStarter(playwright)
    )
    locator = FakeLocator()
    runtime = BrowserRuntime(
        config,
        session_id_factory=lambda: "bw_abcdefghijklmnop",
        observation_builder=StubObservationBuilder(locator),  # type: ignore[arg-type]
    )
    return runtime, page, browser, playwright, locator


async def test_all_typed_action_success_paths_and_stale_reference_cleanup(
    monkeypatch: pytest.MonkeyPatch, worker_config: WorkerConfig
) -> None:
    runtime, page, browser, playwright, locator = make_runtime(monkeypatch, worker_config)
    created = await runtime.create_session()
    observation = created.observation

    actions = [
        ClickAction(
            action_id="act_click",
            type="click",
            observation_id=observation.observation_id,
            element_ref=observation.interactive_elements[0].element_ref,
        ),
    ]
    result = await runtime.execute_action(created.session_id, actions[0])
    assert result.success is True and result.observation is not None

    stale = FillAction(
        action_id="act_stale",
        type="fill",
        observation_id=observation.observation_id,
        element_ref=observation.interactive_elements[0].element_ref,
        text="synthetic",
    )
    stale_result = await runtime.execute_action(created.session_id, stale)
    assert stale_result.error_category == "stale_element_ref"
    assert stale_result.observation is not None

    current = stale_result.observation
    ref = current.interactive_elements[0].element_ref
    for action in (
        FillAction(
            action_id="act_fill",
            type="fill",
            observation_id=current.observation_id,
            element_ref=ref,
            text="synthetic",
        ),
    ):
        result = await runtime.execute_action(created.session_id, action)
    assert result.observation is not None
    current = result.observation
    ref = current.interactive_elements[0].element_ref
    result = await runtime.execute_action(
        created.session_id,
        SelectAction(
            action_id="act_select",
            type="select",
            observation_id=current.observation_id,
            element_ref=ref,
            option="Choice",
        ),
    )
    current = result.observation
    assert current is not None
    ref = current.interactive_elements[0].element_ref
    result = await runtime.execute_action(
        created.session_id,
        ReadAction(
            action_id="act_read",
            type="read",
            observation_id=current.observation_id,
            element_ref=ref,
        ),
    )
    current = result.observation
    assert current is not None
    ref = current.interactive_elements[0].element_ref
    result = await runtime.execute_action(
        created.session_id,
        ScrollAction(
            action_id="act_scroll",
            type="scroll",
            observation_id=current.observation_id,
            element_ref=ref,
            direction="down",
        ),
    )
    assert result.observation is not None
    result = await runtime.execute_action(
        created.session_id, WaitAction(action_id="act_wait", type="wait", duration_ms=1)
    )
    assert result.observation is not None
    result = await runtime.execute_action(
        created.session_id, NavigateAction(action_id="act_nav", type="navigate", url="/mail")
    )
    assert result.success is True
    terminal = await runtime.execute_action(
        created.session_id, FinishAction(action_id="act_finish", type="finish")
    )
    assert terminal.terminal is True and terminal.success is True
    assert browser.context.closed and browser.closed and page.closed and playwright.stopped
    assert {call[0] for call in locator.calls} >= {"click", "fill", "select", "scroll"}


async def test_forged_reference_and_action_budget_fail_safely(
    monkeypatch: pytest.MonkeyPatch, worker_config: WorkerConfig
) -> None:
    limited = replace(worker_config, limits=replace(worker_config.limits, max_actions=1))
    runtime, _, browser, _, _ = make_runtime(monkeypatch, limited)
    created = await runtime.create_session()
    observation = created.observation
    forged = ReadAction(
        action_id="act_forged",
        type="read",
        observation_id=observation.observation_id,
        element_ref="ref_forged99",
    )
    first = await runtime.execute_action(created.session_id, forged)
    assert first.error_category == "unknown_element_ref"
    exhausted = await runtime.execute_action(
        created.session_id, WaitAction(action_id="act_over", type="wait", duration_ms=1)
    )
    assert exhausted.terminal is True
    assert exhausted.error_category == "action_budget_exhausted"
    assert browser.closed is True


async def test_invalid_url_fill_select_wait_and_fail_paths_are_structured(
    monkeypatch: pytest.MonkeyPatch, worker_config: WorkerConfig
) -> None:
    config = replace(worker_config, limits=replace(worker_config.limits, max_wait_ms=10))
    runtime, page, browser, _, _ = make_runtime(monkeypatch, config)
    created = await runtime.create_session()

    invalid_url = await runtime.execute_action(
        created.session_id,
        NavigateAction(action_id="act_external", type="navigate", url="https://example.invalid"),
    )
    assert invalid_url.error_category == "invalid_url"
    assert invalid_url.observation is not None

    current = invalid_url.observation
    ref = current.interactive_elements[0].element_ref
    invalid_fill = await runtime.execute_action(
        created.session_id,
        FillAction(
            action_id="act_real_email",
            type="fill",
            observation_id=current.observation_id,
            element_ref=ref,
            text="person@example.com",
        ),
    )
    assert invalid_fill.error_category == "input_rejected"
    assert invalid_fill.observation is not None

    current = invalid_fill.observation
    ref = current.interactive_elements[0].element_ref
    invalid_select = await runtime.execute_action(
        created.session_id,
        SelectAction(
            action_id="act_unknown_option",
            type="select",
            observation_id=current.observation_id,
            element_ref=ref,
            option="Not exposed",
        ),
    )
    assert invalid_select.error_category == "input_rejected"

    over_wait = await runtime.execute_action(
        created.session_id,
        WaitAction(action_id="act_long_wait", type="wait", duration_ms=11),
    )
    assert over_wait.terminal is True
    assert over_wait.error_category == "wait_limit_exceeded"
    assert page.closed and browser.closed

    second_runtime, second_page, second_browser, _, _ = make_runtime(monkeypatch, worker_config)
    second = await second_runtime.create_session()
    failed = await second_runtime.execute_action(
        second.session_id,
        FailAction(
            action_id="act_fail",
            type="fail",
            category="escalated",
            reason="Synthetic escalation",
        ),
    )
    assert failed.terminal is True and failed.success is False
    assert second_page.closed and second_browser.closed


async def test_redirect_escape_is_rejected_and_resources_close(
    monkeypatch: pytest.MonkeyPatch, worker_config: WorkerConfig
) -> None:
    runtime, page, browser, playwright, _ = make_runtime(monkeypatch, worker_config, redirect=True)
    with pytest.raises(PolicyViolation):
        await runtime.create_session()
    assert page.closed and browser.context.closed and browser.closed and playwright.stopped


async def test_each_session_owns_distinct_browser_context_and_close_all_cleans_them(
    monkeypatch: pytest.MonkeyPatch, worker_config: WorkerConfig
) -> None:
    browsers: list[FakeBrowser] = []
    playwrights: list[FakePlaywright] = []

    def starter_factory() -> FakeStarter:
        browser = FakeBrowser(FakePage())
        playwright = FakePlaywright(browser)
        browsers.append(browser)
        playwrights.append(playwright)
        return FakeStarter(playwright)

    monkeypatch.setattr("flowpilot_browser_worker.runtime.async_playwright", starter_factory)
    session_ids = iter(("bw_abcdefghijklmnop", "bw_qrstuvwxyzABCDEF"))
    runtime = BrowserRuntime(
        worker_config,
        session_id_factory=lambda: next(session_ids),
        observation_builder=StubObservationBuilder(FakeLocator()),  # type: ignore[arg-type]
    )
    first = await runtime.create_session()
    second = await runtime.create_session()
    assert first.session_id != second.session_id
    assert browsers[0].context is not browsers[1].context
    await runtime.close_all()
    assert all(browser.closed and browser.context.closed for browser in browsers)
    assert all(playwright.stopped for playwright in playwrights)


async def test_idle_session_expires_and_closes_without_another_action(
    monkeypatch: pytest.MonkeyPatch, worker_config: WorkerConfig
) -> None:
    expiry_released = False

    async def release_expiry(_: float) -> None:
        nonlocal expiry_released
        expiry_released = True

    runtime, page, browser, playwright, locator = make_runtime(monkeypatch, worker_config)
    expiring_runtime = BrowserRuntime(
        worker_config,
        session_id_factory=lambda: "bw_abcdefghijklmnop",
        observation_builder=StubObservationBuilder(locator),  # type: ignore[arg-type]
        sleeper=release_expiry,
    )
    await expiring_runtime.create_session()
    for _ in range(10):
        if page.closed:
            break
        await asyncio.sleep(0)
    assert expiry_released is True
    assert page.closed and browser.closed and playwright.stopped
