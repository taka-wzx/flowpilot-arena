import asyncio
import secrets
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass, field
from time import monotonic
from typing import Literal

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Route,
    async_playwright,
)
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from flowpilot_browser_worker.config import WorkerConfig
from flowpilot_browser_worker.observation import ElementTarget, ObservationBuilder
from flowpilot_browser_worker.policy import PolicyViolation, URLPolicy, validate_fill_text
from flowpilot_browser_worker.schemas import (
    ActionResult,
    BrowserAction,
    ClickAction,
    ErrorCategory,
    FailAction,
    FillAction,
    FinishAction,
    LastAction,
    NavigateAction,
    ReadAction,
    ScrollAction,
    SelectAction,
    SessionClosed,
    SessionCreated,
    VisionActionResult,
    VisionBrowserAction,
    VisionClickAction,
    VisionErrorCategory,
    VisionFailAction,
    VisionFillAction,
    VisionFinishAction,
    VisionLastAction,
    VisionNavigateAction,
    VisionReadAction,
    VisionScrollAction,
    VisionSelectAction,
    VisionSessionClosed,
    VisionSessionCreated,
    VisionWaitAction,
    WaitAction,
)
from flowpilot_browser_worker.vision import (
    VisionCaptureError,
    VisionObservationBuild,
    VisionObservationBuilder,
)


class UnknownSessionError(KeyError):
    """Raised when a session identifier is unknown, closed, or has the wrong mode."""


@dataclass(slots=True)
class BrowserSession:
    session_id: str
    mode: Literal["dom", "vision"]
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page
    started_at: float
    observation_id: str
    references: dict[str, ElementTarget]
    vision_screenshot_ref: str | None = None
    vision_references: dict[str, ElementTarget] = field(default_factory=dict)
    vision_screenshot_count: int = 0
    vision_image_bytes: int = 0
    vision_capture_ms: int = 0
    action_count: int = 0
    navigation_count: int = 1
    closed: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    expiry_task: asyncio.Task[None] | None = None


class BrowserRuntime:
    def __init__(
        self,
        config: WorkerConfig,
        *,
        clock: Callable[[], float] = monotonic,
        session_id_factory: Callable[[], str] | None = None,
        observation_builder: ObservationBuilder | None = None,
        vision_observation_builder: VisionObservationBuilder | None = None,
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.config = config
        self.policy = URLPolicy(config.sandbox_origin)
        self._clock = clock
        self._session_id_factory = session_id_factory or (lambda: f"bw_{secrets.token_urlsafe(18)}")
        self._builder = observation_builder or ObservationBuilder(config.limits)
        self._vision_builder = vision_observation_builder or VisionObservationBuilder(
            config.limits, clock=clock
        )
        self._sleeper = sleeper
        self._sessions: dict[str, BrowserSession] = {}
        self._sessions_lock = asyncio.Lock()

    async def create_session(self, initial_path: str = "/hris") -> SessionCreated:
        session = await self._open_session(initial_path, "dom")
        try:
            built = await self._builder.build(session.page, session.session_id)
            session.observation_id = built.observation.observation_id
            session.references = built.references
            await self._register_session(session)
            return SessionCreated(session_id=session.session_id, observation=built.observation)
        except Exception:
            await self._close_session(session)
            raise

    async def create_vision_session(self, initial_path: str = "/hris") -> VisionSessionCreated:
        session = await self._open_session(initial_path, "vision")
        try:
            built = await self._refresh_vision_observation(session)
            await self._register_session(session)
            return VisionSessionCreated(
                session_id=session.session_id, observation=built.observation
            )
        except Exception:
            await self._close_session(session)
            raise

    async def execute_action(self, session_id: str, action: BrowserAction) -> ActionResult:
        session = await self._require_session(session_id, "dom")
        async with session.lock:
            terminal_error = self._terminal_budget_error(session, action)
            if terminal_error is not None:
                await self._close_session(session)
                return terminal_error

            session.action_count += 1
            if isinstance(action, (FinishAction, FailAction)):
                message = action.summary if isinstance(action, FinishAction) else action.reason
                await self._close_session(session)
                return ActionResult(
                    session_id=session_id,
                    action_id=action.action_id,
                    action_type=action.type,
                    success=isinstance(action, FinishAction),
                    terminal=True,
                    message=self._sanitize(message or "Agent loop ended"),
                )

            target: ElementTarget | None = None
            if isinstance(
                action, (ClickAction, FillAction, SelectAction, ReadAction, ScrollAction)
            ):
                reference_error, target = self._resolve_target(session, action)
                if reference_error is not None:
                    return await self._failure_observation(session, action, *reference_error)

            try:
                message = await self._dispatch(session, action, target)
                self.policy.assert_final_navigation(session.page.url)
                return await self._success_observation(session, action, message)
            except PolicyViolation as exc:
                category: ErrorCategory = (
                    "invalid_url" if isinstance(action, NavigateAction) else "input_rejected"
                )
                return await self._failure_observation(
                    session, action, category, self._sanitize(str(exc))
                )
            except PlaywrightTimeoutError:
                return await self._failure_observation(
                    session, action, "browser_timeout", "Browser action exceeded its timeout"
                )
            except PlaywrightError as exc:
                return await self._failure_observation(
                    session, action, "browser_error", self._sanitize(str(exc))
                )

    async def execute_vision_action(
        self, session_id: str, action: VisionBrowserAction
    ) -> VisionActionResult:
        session = await self._require_session(session_id, "vision")
        async with session.lock:
            terminal_error = self._vision_terminal_budget_error(session, action)
            if terminal_error is not None:
                await self._close_session(session)
                return terminal_error

            session.action_count += 1
            if isinstance(action, (VisionFinishAction, VisionFailAction)):
                message = (
                    action.summary if isinstance(action, VisionFinishAction) else action.reason
                )
                await self._close_session(session)
                return VisionActionResult(
                    session_id=session_id,
                    action_id=action.action_id,
                    action_type=action.type,
                    success=isinstance(action, VisionFinishAction),
                    terminal=True,
                    message=self._sanitize(message or "Vision Agent loop ended"),
                )

            target: ElementTarget | None = None
            if isinstance(
                action,
                (
                    VisionClickAction,
                    VisionFillAction,
                    VisionSelectAction,
                    VisionReadAction,
                    VisionScrollAction,
                ),
            ):
                reference_error, target = self._resolve_vision_target(session, action)
                if reference_error is not None:
                    return await self._vision_failure_observation(session, action, *reference_error)

            try:
                message = await self._dispatch_vision(session, action, target)
                self.policy.assert_final_navigation(session.page.url)
                return await self._vision_success_observation(session, action, message)
            except PolicyViolation as exc:
                category: VisionErrorCategory = (
                    "invalid_url" if isinstance(action, VisionNavigateAction) else "input_rejected"
                )
                return await self._vision_failure_observation(
                    session, action, category, self._sanitize(str(exc))
                )
            except PlaywrightTimeoutError:
                return await self._vision_failure_observation(
                    session,
                    action,
                    "browser_timeout",
                    "Browser action exceeded its timeout",
                )
            except PlaywrightError as exc:
                return await self._vision_failure_observation(
                    session, action, "browser_error", self._sanitize(str(exc))
                )

    async def close_session(self, session_id: str) -> SessionClosed:
        async with self._sessions_lock:
            session = self._sessions.get(session_id)
        if session is not None:
            async with session.lock:
                await self._close_session(session)
        return SessionClosed(session_id=session_id, closed=True)

    async def close_vision_session(self, session_id: str) -> VisionSessionClosed:
        async with self._sessions_lock:
            session = self._sessions.get(session_id)
        if session is not None:
            async with session.lock:
                if session.mode != "vision":
                    raise UnknownSessionError(session_id)
                await self._close_session(session)
        return VisionSessionClosed(session_id=session_id, closed=True)

    async def close_all(self) -> None:
        async with self._sessions_lock:
            sessions = list(self._sessions.values())
        for session in sessions:
            async with session.lock:
                await self._close_session(session)

    async def _open_session(
        self, initial_path: str, mode: Literal["dom", "vision"]
    ) -> BrowserSession:
        session_id = self._session_id_factory()
        initial_url = self.policy.resolve_navigation(initial_path)
        playwright = await async_playwright().start()
        browser: Browser | None = None
        context: BrowserContext | None = None
        page: Page | None = None
        try:
            browser = await playwright.chromium.launch(headless=True)
            if mode == "vision":
                context = await browser.new_context(
                    accept_downloads=False,
                    service_workers="block",
                    viewport={
                        "width": self.config.limits.vision_viewport_width,
                        "height": self.config.limits.vision_viewport_height,
                    },
                    device_scale_factor=1,
                )
            else:
                context = await browser.new_context(
                    accept_downloads=False,
                    service_workers="block",
                    viewport={"width": 1280, "height": 720},
                )
            page = await context.new_page()
            page.set_default_timeout(self.config.limits.browser_action_timeout_ms)
            page.set_default_navigation_timeout(self.config.limits.browser_action_timeout_ms)

            async def guard_request(route: Route) -> None:
                request = route.request
                if self.policy.allows_request(request.url):
                    await route.continue_()
                else:
                    await route.abort("blockedbyclient")

            await page.route("**/*", guard_request)
            await page.goto(initial_url, wait_until="domcontentloaded")
            self.policy.assert_final_navigation(page.url)
            return BrowserSession(
                session_id=session_id,
                mode=mode,
                playwright=playwright,
                browser=browser,
                context=context,
                page=page,
                started_at=self._clock(),
                observation_id="",
                references={},
            )
        except Exception:
            await self._close_handles(page, context, browser, playwright)
            raise

    async def _register_session(self, session: BrowserSession) -> None:
        async with self._sessions_lock:
            self._sessions[session.session_id] = session
        session.expiry_task = asyncio.create_task(self._expire_session(session.session_id))

    async def _expire_session(self, session_id: str) -> None:
        await self._sleeper(self.config.limits.max_session_seconds)
        try:
            session = await self._require_session(session_id)
        except UnknownSessionError:
            return
        async with session.lock:
            await self._close_session(session)

    async def _require_session(
        self, session_id: str, mode: Literal["dom", "vision"] | None = None
    ) -> BrowserSession:
        async with self._sessions_lock:
            session = self._sessions.get(session_id)
        if session is None or session.closed or (mode is not None and session.mode != mode):
            raise UnknownSessionError(session_id)
        return session

    def _terminal_budget_error(
        self, session: BrowserSession, action: BrowserAction
    ) -> ActionResult | None:
        if self._clock() - session.started_at > self.config.limits.max_session_seconds:
            return ActionResult(
                session_id=session.session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=False,
                terminal=True,
                error_category="session_timeout",
                message="Browser session exceeded its wall-time limit",
            )
        if session.action_count >= self.config.limits.max_actions:
            return ActionResult(
                session_id=session.session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=False,
                terminal=True,
                error_category="action_budget_exhausted",
                message="Browser session exhausted its action budget",
            )
        if (
            isinstance(action, NavigateAction)
            and session.navigation_count >= self.config.limits.max_navigations
        ):
            return ActionResult(
                session_id=session.session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=False,
                terminal=True,
                error_category="navigation_budget_exhausted",
                message="Browser session exhausted its navigation budget",
            )
        if isinstance(action, WaitAction) and action.duration_ms > self.config.limits.max_wait_ms:
            return ActionResult(
                session_id=session.session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=False,
                terminal=True,
                error_category="wait_limit_exceeded",
                message="Wait exceeds the configured limit",
            )
        return None

    def _vision_terminal_budget_error(
        self, session: BrowserSession, action: VisionBrowserAction
    ) -> VisionActionResult | None:
        if self._clock() - session.started_at > self.config.limits.max_session_seconds:
            return VisionActionResult(
                session_id=session.session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=False,
                terminal=True,
                error_category="session_timeout",
                message="Browser session exceeded its wall-time limit",
            )
        if session.action_count >= self.config.limits.max_actions:
            return VisionActionResult(
                session_id=session.session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=False,
                terminal=True,
                error_category="action_budget_exhausted",
                message="Browser session exhausted its action budget",
            )
        if (
            isinstance(action, VisionNavigateAction)
            and session.navigation_count >= self.config.limits.max_navigations
        ):
            return VisionActionResult(
                session_id=session.session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=False,
                terminal=True,
                error_category="navigation_budget_exhausted",
                message="Browser session exhausted its navigation budget",
            )
        if (
            isinstance(action, VisionWaitAction)
            and action.duration_ms > self.config.limits.max_wait_ms
        ):
            return VisionActionResult(
                session_id=session.session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=False,
                terminal=True,
                error_category="wait_limit_exceeded",
                message="Wait exceeds the configured limit",
            )
        return None

    @staticmethod
    def _resolve_target(
        session: BrowserSession,
        action: ClickAction | FillAction | SelectAction | ReadAction | ScrollAction,
    ) -> tuple[tuple[ErrorCategory, str] | None, ElementTarget | None]:
        if action.observation_id != session.observation_id:
            return (
                ("stale_element_ref", "Element reference belongs to an expired observation"),
                None,
            )
        target = session.references.get(action.element_ref)
        if target is None:
            return (("unknown_element_ref", "Element reference is unknown or forged"), None)
        if action.type not in target.allowed_actions:
            return (("action_not_allowed", "Action is not allowed for this element"), None)
        return None, target

    @staticmethod
    def _resolve_vision_target(
        session: BrowserSession,
        action: VisionClickAction
        | VisionFillAction
        | VisionSelectAction
        | VisionReadAction
        | VisionScrollAction,
    ) -> tuple[tuple[VisionErrorCategory, str] | None, ElementTarget | None]:
        if (
            action.observation_id != session.observation_id
            or action.screenshot_ref != session.vision_screenshot_ref
        ):
            return (
                ("stale_visual_ref", "Visual reference belongs to an expired observation"),
                None,
            )
        target = session.vision_references.get(action.grounding_ref)
        if target is None:
            return (("unknown_visual_ref", "Visual reference is unknown or forged"), None)
        if action.type not in target.allowed_actions:
            return (("action_not_allowed", "Action is not allowed for this grounding"), None)
        return None, target

    async def _dispatch(
        self,
        session: BrowserSession,
        action: BrowserAction,
        target: ElementTarget | None,
    ) -> str:
        if isinstance(action, NavigateAction):
            url = self.policy.resolve_navigation(action.url)
            session.navigation_count += 1
            await session.page.goto(url, wait_until="domcontentloaded")
            self.policy.assert_final_navigation(session.page.url)
            return "Navigation completed"
        if isinstance(action, ClickAction):
            await self._target(target).locator.click()
            await session.page.wait_for_timeout(100)
            return "Click completed"
        if isinstance(action, FillAction):
            safe_target = self._target(target)
            validate_fill_text(action.text, safe_target.input_type, self.config.limits)
            await safe_target.locator.fill(action.text)
            return "Fill completed"
        if isinstance(action, SelectAction):
            safe_target = self._target(target)
            value = safe_target.option_values.get(action.option)
            if value is None:
                raise PolicyViolation("Select option was not exposed by the current observation")
            await safe_target.locator.select_option(value=value)
            return "Select completed"
        if isinstance(action, ReadAction):
            return self._sanitize(self._target(target).safe_name or "Readable element has no name")
        if isinstance(action, ScrollAction):
            await self._target(target).locator.scroll_into_view_if_needed()
            amount = 240 if action.amount == "small" else 640
            await session.page.mouse.wheel(0, amount if action.direction == "down" else -amount)
            return "Scroll completed"
        if isinstance(action, WaitAction):
            await session.page.wait_for_timeout(action.duration_ms)
            return "Bounded wait completed"
        raise AssertionError("Terminal actions are handled before dispatch")

    async def _dispatch_vision(
        self,
        session: BrowserSession,
        action: VisionBrowserAction,
        target: ElementTarget | None,
    ) -> str:
        if isinstance(action, VisionNavigateAction):
            url = self.policy.resolve_navigation(action.url)
            session.navigation_count += 1
            await session.page.goto(url, wait_until="domcontentloaded")
            self.policy.assert_final_navigation(session.page.url)
            return "Navigation completed"
        if isinstance(action, VisionClickAction):
            await self._target(target).locator.click()
            await session.page.wait_for_timeout(100)
            return "Grounded click completed"
        if isinstance(action, VisionFillAction):
            safe_target = self._target(target)
            validate_fill_text(action.text, safe_target.input_type, self.config.limits)
            await safe_target.locator.fill(action.text)
            return "Grounded fill completed"
        if isinstance(action, VisionSelectAction):
            safe_target = self._target(target)
            value = safe_target.option_values.get(action.option)
            if value is None:
                raise PolicyViolation("Select option was not exposed by the current observation")
            await safe_target.locator.select_option(value=value)
            return "Grounded select completed"
        if isinstance(action, VisionReadAction):
            self._target(target)
            return "Grounded read completed"
        if isinstance(action, VisionScrollAction):
            await self._target(target).locator.scroll_into_view_if_needed()
            amount = 240 if action.amount == "small" else 640
            await session.page.mouse.wheel(0, amount if action.direction == "down" else -amount)
            return "Grounded scroll completed"
        if isinstance(action, VisionWaitAction):
            await session.page.wait_for_timeout(action.duration_ms)
            return "Bounded wait completed"
        raise AssertionError("Terminal actions are handled before dispatch")

    async def _success_observation(
        self, session: BrowserSession, action: BrowserAction, message: str
    ) -> ActionResult:
        last_action = LastAction(
            action_id=action.action_id,
            action_type=action.type,
            success=True,
            message=self._sanitize(message),
        )
        built = await self._builder.build(session.page, session.session_id, last_action)
        session.observation_id = built.observation.observation_id
        session.references = built.references
        return ActionResult(
            session_id=session.session_id,
            action_id=action.action_id,
            action_type=action.type,
            success=True,
            terminal=False,
            message=self._sanitize(message),
            observation=built.observation,
        )

    async def _failure_observation(
        self,
        session: BrowserSession,
        action: BrowserAction,
        category: ErrorCategory,
        message: str,
    ) -> ActionResult:
        last_action = LastAction(
            action_id=action.action_id,
            action_type=action.type,
            success=False,
            error_category=category,
            message=self._sanitize(message),
        )
        built = await self._builder.build(
            session.page, session.session_id, last_action, page_error=message
        )
        session.observation_id = built.observation.observation_id
        session.references = built.references
        return ActionResult(
            session_id=session.session_id,
            action_id=action.action_id,
            action_type=action.type,
            success=False,
            terminal=False,
            error_category=category,
            message=self._sanitize(message),
            observation=built.observation,
        )

    async def _vision_success_observation(
        self,
        session: BrowserSession,
        action: VisionBrowserAction,
        message: str,
    ) -> VisionActionResult:
        last_action = VisionLastAction(
            action_id=action.action_id,
            action_type=action.type,
            success=True,
            message=self._sanitize(message),
        )
        try:
            built = await self._refresh_vision_observation(session, last_action)
        except (PolicyViolation, VisionCaptureError) as exc:
            return await self._vision_observation_failure(session, action, exc)
        return VisionActionResult(
            session_id=session.session_id,
            action_id=action.action_id,
            action_type=action.type,
            success=True,
            terminal=False,
            message=self._sanitize(message),
            observation=built.observation,
        )

    async def _vision_failure_observation(
        self,
        session: BrowserSession,
        action: VisionBrowserAction,
        category: VisionErrorCategory,
        message: str,
    ) -> VisionActionResult:
        last_action = VisionLastAction(
            action_id=action.action_id,
            action_type=action.type,
            success=False,
            error_category=category,
            message=self._sanitize(message),
        )
        try:
            built = await self._refresh_vision_observation(session, last_action, page_error=message)
        except (PolicyViolation, VisionCaptureError) as exc:
            return await self._vision_observation_failure(session, action, exc)
        return VisionActionResult(
            session_id=session.session_id,
            action_id=action.action_id,
            action_type=action.type,
            success=False,
            terminal=False,
            error_category=category,
            message=self._sanitize(message),
            observation=built.observation,
        )

    async def _vision_observation_failure(
        self,
        session: BrowserSession,
        action: VisionBrowserAction,
        error: PolicyViolation | VisionCaptureError,
    ) -> VisionActionResult:
        if isinstance(error, VisionCaptureError):
            category: VisionErrorCategory = error.category
            message = error.message
        else:
            category = "invalid_url"
            message = "Current page is outside the permitted Sandbox origin"
        await self._close_session(session)
        return VisionActionResult(
            session_id=session.session_id,
            action_id=action.action_id,
            action_type=action.type,
            success=False,
            terminal=True,
            error_category=category,
            message=message,
        )

    async def _refresh_vision_observation(
        self,
        session: BrowserSession,
        last_action: VisionLastAction | None = None,
        page_error: str | None = None,
    ) -> VisionObservationBuild:
        self.policy.assert_final_navigation(session.page.url)
        session.vision_references.clear()
        session.vision_screenshot_ref = None
        if session.vision_screenshot_count >= self.config.limits.max_vision_screenshots:
            raise VisionCaptureError(
                "screenshot_budget_exhausted",
                "Browser session exhausted its screenshot budget",
            )
        session.vision_screenshot_count += 1
        built = await self._vision_builder.build(
            session.page,
            session.session_id,
            last_action,
            page_error=page_error,
        )
        session.vision_image_bytes += built.observation.image_bytes
        session.vision_capture_ms += built.observation.capture_duration_ms
        if (
            session.vision_image_bytes
            > self.config.limits.max_vision_screenshots
            * self.config.limits.max_vision_screenshot_bytes
            or session.vision_capture_ms
            > self.config.limits.max_vision_screenshots * self.config.limits.max_vision_capture_ms
        ):
            raise VisionCaptureError(
                "screenshot_budget_exhausted",
                "Browser session exhausted its visual capture budget",
            )
        session.observation_id = built.observation.observation_id
        session.vision_screenshot_ref = built.observation.screenshot_ref
        session.vision_references = built.references
        return built

    async def _close_session(self, session: BrowserSession) -> None:
        if session.closed:
            return
        session.closed = True
        current_task = asyncio.current_task()
        if session.expiry_task is not None and session.expiry_task is not current_task:
            session.expiry_task.cancel()
        session.expiry_task = None
        session.references.clear()
        session.vision_references.clear()
        session.vision_screenshot_ref = None
        await self._close_handles(
            session.page, session.context, session.browser, session.playwright
        )
        async with self._sessions_lock:
            self._sessions.pop(session.session_id, None)

    @staticmethod
    async def _close_handles(
        page: Page | None,
        context: BrowserContext | None,
        browser: Browser | None,
        playwright: Playwright,
    ) -> None:
        for close in (
            page.close if page is not None else None,
            context.close if context is not None else None,
            browser.close if browser is not None else None,
            playwright.stop,
        ):
            if close is None:
                continue
            with suppress(PlaywrightError):
                await close()

    @staticmethod
    def _target(target: ElementTarget | None) -> ElementTarget:
        if target is None:
            raise AssertionError("Element action target was not resolved")
        return target

    @staticmethod
    def _sanitize(value: str) -> str:
        return " ".join(value.split())[:300]
