import base64
from dataclasses import replace
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from flowpilot_browser_worker.config import WorkerConfig, WorkerLimits
from flowpilot_browser_worker.observation import INTERACTIVE_SELECTOR, ElementTarget
from flowpilot_browser_worker.runtime import BrowserRuntime
from flowpilot_browser_worker.schemas import (
    VisionBrowserAction,
    VisionFinishAction,
    VisionObservation,
    VisionWaitAction,
    VisualBounds,
    VisualGrounding,
)
from flowpilot_browser_worker.vision import (
    VisionCaptureError,
    VisionObservationBuild,
    VisionObservationBuilder,
)


def jpeg_bytes() -> bytes:
    return b"\xff\xd8synthetic-jpeg\xff\xd9"


def encoded_jpeg() -> str:
    return base64.b64encode(jpeg_bytes()).decode("ascii")


def visual_observation(
    *,
    observation_id: str = "vobs_visual0001",
    screenshot_ref: str = "shot_visual0001",
    grounding_ref: str = "gref_visual0001_1",
) -> VisionObservation:
    return VisionObservation(
        session_id="bw_abcdefghijklmnop",
        observation_id=observation_id,
        screenshot_ref=screenshot_ref,
        image_mime_type="image/jpeg",
        image_base64=encoded_jpeg(),
        image_width=960,
        image_height=540,
        image_bytes=len(jpeg_bytes()),
        capture_duration_ms=1,
        groundings=(
            VisualGrounding(
                grounding_ref=grounding_ref,
                bounds=VisualBounds(x=1, y=2, width=20, height=10),
                allowed_actions=("click", "fill", "select", "read", "scroll"),
            ),
        ),
        truncated=False,
    )


def test_visual_schemas_reject_coordinates_and_do_not_expose_dom() -> None:
    adapter = TypeAdapter(VisionBrowserAction)
    action = adapter.validate_python(
        {
            "schema_version": "w5-vision-action/1.0",
            "action_id": "act_visual_read",
            "type": "read",
            "observation_id": "vobs_visual0001",
            "screenshot_ref": "shot_visual0001",
            "grounding_ref": "gref_visual0001_1",
        }
    )
    assert action.type == "read"
    for field, value in (
        ("x", 12),
        ("y", 9),
        ("selector", "#unsafe"),
        ("xpath", "//button"),
        ("javascript", "document.cookie"),
        ("file_path", "/tmp/image.jpg"),
        ("image_url", "https://example.invalid/image.jpg"),
    ):
        with pytest.raises(ValidationError):
            adapter.validate_python(
                {
                    "schema_version": "w5-vision-action/1.0",
                    "action_id": "act_visual_read",
                    "type": "read",
                    "observation_id": "vobs_visual0001",
                    "screenshot_ref": "shot_visual0001",
                    "grounding_ref": "gref_visual0001_1",
                    field: value,
                }
            )

    schema = VisionObservation.model_json_schema()
    serialized = str(schema).lower()
    for prohibited in (
        "semantic_nodes",
        "interactive_elements",
        "element_ref",
        "current_url",
        "page_title",
        "selector",
        "cookie",
        "local_storage",
        "ocr_text",
        "image_path",
        "image_url",
    ):
        assert prohibited not in serialized


def test_visual_observation_validates_jpeg_bytes_and_bounds() -> None:
    invalid_jpeg = visual_observation().model_dump()
    invalid_jpeg["image_base64"] = base64.b64encode(b"not-a-jpeg").decode("ascii")
    with pytest.raises(ValidationError):
        VisionObservation.model_validate(invalid_jpeg)
    mismatched_bytes = visual_observation().model_dump()
    mismatched_bytes["image_bytes"] = len(jpeg_bytes()) + 1
    with pytest.raises(ValidationError):
        VisionObservation.model_validate(mismatched_bytes)
    with pytest.raises(ValidationError):
        VisualBounds(x=950, y=0, width=20, height=10)
    with pytest.raises(ValueError):
        WorkerLimits(vision_viewport_width=961)
    with pytest.raises(ValueError):
        WorkerLimits(max_vision_screenshots=25)
    with pytest.raises(ValueError):
        WorkerLimits(max_vision_capture_ms=3_001)


class CaptureItem:
    def __init__(self, metadata: dict[str, Any], box: dict[str, float] | None) -> None:
        self.metadata = metadata
        self.box = box

    async def is_visible(self) -> bool:
        return True

    async def evaluate(self, _: str) -> dict[str, Any]:
        return self.metadata

    async def bounding_box(self) -> dict[str, float] | None:
        return self.box


class CaptureCollection:
    def __init__(self, item: CaptureItem) -> None:
        self.item = item

    async def count(self) -> int:
        return 1

    def nth(self, _: int) -> CaptureItem:
        return self.item


class CapturePage:
    url = "http://sandbox-web/hris"

    def __init__(self, image: bytes, box: dict[str, float] | None) -> None:
        self.image = image
        self.box = box
        self.screenshot_kwargs: dict[str, object] | None = None

    def locator(self, selector: str) -> CaptureCollection:
        assert selector == INTERACTIVE_SELECTOR
        return CaptureCollection(
            CaptureItem(
                {
                    "tag": "button",
                    "role": "button",
                    "name": "Synthetic submit",
                    "text": "Synthetic submit",
                    "inputType": "",
                    "disabled": False,
                    "checked": None,
                    "selected": None,
                    "expanded": None,
                    "readonly": False,
                    "required": False,
                    "options": [],
                },
                self.box,
            )
        )

    async def screenshot(self, **kwargs: object) -> bytes:
        self.screenshot_kwargs = kwargs
        return self.image


async def test_vision_observation_builder_binds_jpeg_to_clipped_grounding() -> None:
    page = CapturePage(jpeg_bytes(), {"x": -2.5, "y": 530.2, "width": 30.0, "height": 20.0})
    built = await VisionObservationBuilder(
        WorkerLimits(), nonce_factory=lambda: "visual0001"
    ).build(page, "bw_abcdefghijklmnop")  # type: ignore[arg-type]

    assert built.observation.image_base64 == encoded_jpeg()
    assert built.observation.image_width == 960
    assert built.observation.image_height == 540
    assert built.observation.groundings[0].bounds == VisualBounds(x=0, y=530, width=28, height=10)
    assert set(built.references) == {"gref_visual0001_1"}
    assert page.screenshot_kwargs == {
        "type": "jpeg",
        "quality": 60,
        "full_page": False,
        "animations": "disabled",
        "caret": "hide",
        "scale": "css",
        "timeout": 3_000,
    }


async def test_vision_observation_builder_rejects_oversized_image() -> None:
    page = CapturePage(
        b"\xff\xd8" + b"x" * 100 + b"\xff\xd9", {"x": 1, "y": 1, "width": 2, "height": 2}
    )
    limits = WorkerLimits(max_vision_screenshot_bytes=16)
    with pytest.raises(VisionCaptureError, match="byte limit"):
        await VisionObservationBuilder(limits, nonce_factory=lambda: "visual0001").build(
            page, "bw_abcdefghijklmnop"
        )  # type: ignore[arg-type]


async def test_vision_observation_builder_rejects_slow_capture() -> None:
    page = CapturePage(jpeg_bytes(), {"x": 1, "y": 1, "width": 2, "height": 2})
    ticks = iter((0.0, 3.001))
    with pytest.raises(VisionCaptureError, match="capture exceeded"):
        await VisionObservationBuilder(
            WorkerLimits(),
            nonce_factory=lambda: "visual0001",
            clock=lambda: next(ticks),
        ).build(page, "bw_abcdefghijklmnop")  # type: ignore[arg-type]


class FakeMouse:
    async def wheel(self, _: int, __: int) -> None:
        pass


class FakeLocator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    async def click(self) -> None:
        self.calls.append(("click", None))

    async def fill(self, text: str) -> None:
        self.calls.append(("fill", text))

    async def select_option(self, *, value: str) -> None:
        self.calls.append(("select", value))

    async def scroll_into_view_if_needed(self) -> None:
        self.calls.append(("scroll", None))


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

    async def new_context(self, **_: object) -> FakeContext:
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


class StubVisionObservationBuilder:
    def __init__(self, locator: FakeLocator) -> None:
        self.locator = locator
        self.counter = 0

    async def build(
        self, _: FakePage, session_id: str, *args: object, **kwargs: object
    ) -> VisionObservationBuild:
        self.counter += 1
        nonce = f"visual{self.counter:04d}"
        observation = visual_observation(
            observation_id=f"vobs_{nonce}",
            screenshot_ref=f"shot_{nonce}",
            grounding_ref=f"gref_{nonce}_1",
        ).model_copy(update={"session_id": session_id})
        target = ElementTarget(
            locator=self.locator,  # type: ignore[arg-type]
            allowed_actions=("click", "fill", "select", "read", "scroll"),
            input_type="text",
            safe_name="Synthetic field",
            option_values={"Choice": "choice"},
        )
        return VisionObservationBuild(
            observation=observation,
            references={observation.groundings[0].grounding_ref: target},
        )


def make_vision_runtime(
    monkeypatch: pytest.MonkeyPatch, limits: WorkerLimits
) -> tuple[
    BrowserRuntime, FakePage, FakeBrowser, FakePlaywright, FakeLocator, StubVisionObservationBuilder
]:
    page = FakePage()
    browser = FakeBrowser(page)
    playwright = FakePlaywright(browser)
    monkeypatch.setattr(
        "flowpilot_browser_worker.runtime.async_playwright", lambda: FakeStarter(playwright)
    )
    locator = FakeLocator()
    builder = StubVisionObservationBuilder(locator)
    runtime = BrowserRuntime(
        WorkerConfig(sandbox_origin="http://sandbox-web", limits=limits),
        session_id_factory=lambda: "bw_abcdefghijklmnop",
        vision_observation_builder=builder,  # type: ignore[arg-type]
    )
    return runtime, page, browser, playwright, locator, builder


def grounded_action(
    action_type: str, observation: VisionObservation, action_id: str
) -> VisionBrowserAction:
    payload: dict[str, object] = {
        "schema_version": "w5-vision-action/1.0",
        "action_id": action_id,
        "type": action_type,
        "observation_id": observation.observation_id,
        "screenshot_ref": observation.screenshot_ref,
        "grounding_ref": observation.groundings[0].grounding_ref,
    }
    if action_type == "fill":
        payload["text"] = "synthetic"
    if action_type == "select":
        payload["option"] = "Choice"
    if action_type == "scroll":
        payload["direction"] = "down"
    return TypeAdapter(VisionBrowserAction).validate_python(payload)


async def test_visual_actions_are_grounded_stale_safe_and_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime, page, browser, playwright, locator, _ = make_vision_runtime(
        monkeypatch, WorkerLimits()
    )
    created = await runtime.create_vision_session()
    first = created.observation

    result = await runtime.execute_vision_action(
        created.session_id, grounded_action("read", first, "act_read")
    )
    assert result.success is True and result.observation is not None
    assert result.message == "Grounded read completed"
    assert "Synthetic" not in result.message

    stale = await runtime.execute_vision_action(
        created.session_id, grounded_action("fill", first, "act_stale")
    )
    assert stale.error_category == "stale_visual_ref"
    assert stale.observation is not None

    current = stale.observation
    for action_type, action_id in (
        ("click", "act_click"),
        ("fill", "act_fill"),
        ("select", "act_select"),
        ("scroll", "act_scroll"),
    ):
        next_result = await runtime.execute_vision_action(
            created.session_id, grounded_action(action_type, current, action_id)
        )
        assert next_result.success is True and next_result.observation is not None
        current = next_result.observation

    wait_result = await runtime.execute_vision_action(
        created.session_id,
        VisionWaitAction(action_id="act_wait", type="wait", duration_ms=1),
    )
    assert wait_result.observation is not None
    current = wait_result.observation
    navigate_result = await runtime.execute_vision_action(
        created.session_id,
        TypeAdapter(VisionBrowserAction).validate_python(
            {
                "schema_version": "w5-vision-action/1.0",
                "action_id": "act_nav",
                "type": "navigate",
                "url": "/mail",
            }
        ),
    )
    assert navigate_result.success is True and navigate_result.observation is not None
    terminal = await runtime.execute_vision_action(
        created.session_id,
        VisionFinishAction(action_id="act_finish", type="finish"),
    )
    assert terminal.terminal is True
    assert page.closed and browser.closed and playwright.stopped
    assert {name for name, _ in locator.calls} >= {"click", "fill", "select", "scroll"}


async def test_visual_screenshot_budget_exhaustion_closes_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limits = replace(WorkerLimits(), max_vision_screenshots=1)
    runtime, _, browser, _, _, builder = make_vision_runtime(monkeypatch, limits)
    created = await runtime.create_vision_session()

    result = await runtime.execute_vision_action(
        created.session_id,
        VisionWaitAction(action_id="act_wait", type="wait", duration_ms=1),
    )
    assert result.terminal is True
    assert result.error_category == "screenshot_budget_exhausted"
    assert browser.closed is True
    assert builder.counter == 1


async def test_visual_observation_never_captures_after_origin_escape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime, page, browser, _, _, builder = make_vision_runtime(monkeypatch, WorkerLimits())
    created = await runtime.create_vision_session()
    page.url = "https://example.invalid/"

    result = await runtime.execute_vision_action(
        created.session_id,
        VisionWaitAction(action_id="act_wait", type="wait", duration_ms=1),
    )
    assert result.terminal is True
    assert result.error_category == "invalid_url"
    assert browser.closed is True
    assert builder.counter == 1
