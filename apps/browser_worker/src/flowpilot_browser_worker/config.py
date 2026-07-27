from dataclasses import dataclass
from os import environ

MAX_VISION_VIEWPORT_WIDTH = 960
MAX_VISION_VIEWPORT_HEIGHT = 540
MAX_VISION_PIXELS = MAX_VISION_VIEWPORT_WIDTH * MAX_VISION_VIEWPORT_HEIGHT
MAX_VISION_SCREENSHOT_BYTES = 184_320
MAX_VISION_SCREENSHOTS = 24
MAX_VISION_CAPTURE_MS = 3_000


def _positive_int(name: str, default: int) -> int:
    raw = environ.get(name)
    if raw is None:
        return default
    value = int(raw)
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _bounded_positive_int(name: str, default: int, maximum: int) -> int:
    value = _positive_int(name, default)
    if value > maximum:
        raise ValueError(f"{name} must not exceed {maximum}")
    return value


@dataclass(frozen=True, slots=True)
class WorkerLimits:
    max_actions: int = 50
    max_navigations: int = 10
    max_wait_ms: int = 5_000
    max_fill_chars: int = 300
    max_session_seconds: int = 300
    max_semantic_nodes: int = 120
    max_interactive_elements: int = 80
    max_node_text_chars: int = 240
    max_page_title_chars: int = 200
    max_observation_bytes: int = 32_768
    browser_action_timeout_ms: int = 5_000
    vision_viewport_width: int = MAX_VISION_VIEWPORT_WIDTH
    vision_viewport_height: int = MAX_VISION_VIEWPORT_HEIGHT
    max_vision_screenshot_bytes: int = MAX_VISION_SCREENSHOT_BYTES
    max_vision_screenshots: int = MAX_VISION_SCREENSHOTS
    max_vision_capture_ms: int = MAX_VISION_CAPTURE_MS

    def __post_init__(self) -> None:
        if (
            self.vision_viewport_width <= 0
            or self.vision_viewport_width > MAX_VISION_VIEWPORT_WIDTH
        ):
            raise ValueError("vision_viewport_width is outside the W5 capture envelope")
        if (
            self.vision_viewport_height <= 0
            or self.vision_viewport_height > MAX_VISION_VIEWPORT_HEIGHT
        ):
            raise ValueError("vision_viewport_height is outside the W5 capture envelope")
        if self.vision_viewport_width * self.vision_viewport_height > MAX_VISION_PIXELS:
            raise ValueError("vision viewport pixels exceed the W5 capture envelope")
        if (
            self.max_vision_screenshot_bytes <= 0
            or self.max_vision_screenshot_bytes > MAX_VISION_SCREENSHOT_BYTES
        ):
            raise ValueError("max_vision_screenshot_bytes is outside the W5 capture envelope")
        if self.max_vision_screenshots <= 0 or self.max_vision_screenshots > MAX_VISION_SCREENSHOTS:
            raise ValueError("max_vision_screenshots is outside the W5 capture envelope")
        if self.max_vision_capture_ms <= 0 or self.max_vision_capture_ms > MAX_VISION_CAPTURE_MS:
            raise ValueError("max_vision_capture_ms is outside the W5 capture envelope")


@dataclass(frozen=True, slots=True)
class WorkerConfig:
    sandbox_origin: str
    limits: WorkerLimits

    @classmethod
    def from_env(cls) -> "WorkerConfig":
        return cls(
            sandbox_origin=environ.get("SANDBOX_ORIGIN", "http://127.0.0.1:5174"),
            limits=WorkerLimits(
                max_actions=_positive_int("MAX_ACTIONS", 50),
                max_navigations=_positive_int("MAX_NAVIGATIONS", 10),
                max_wait_ms=_positive_int("MAX_WAIT_MS", 5_000),
                max_fill_chars=_positive_int("MAX_FILL_CHARS", 300),
                max_session_seconds=_positive_int("MAX_SESSION_SECONDS", 300),
                max_semantic_nodes=_positive_int("MAX_SEMANTIC_NODES", 120),
                max_interactive_elements=_positive_int("MAX_INTERACTIVE_ELEMENTS", 80),
                max_node_text_chars=_positive_int("MAX_NODE_TEXT_CHARS", 240),
                max_page_title_chars=_positive_int("MAX_PAGE_TITLE_CHARS", 200),
                max_observation_bytes=_positive_int("MAX_OBSERVATION_BYTES", 32_768),
                browser_action_timeout_ms=_positive_int("BROWSER_ACTION_TIMEOUT_MS", 5_000),
                vision_viewport_width=_bounded_positive_int(
                    "VISION_VIEWPORT_WIDTH", MAX_VISION_VIEWPORT_WIDTH, MAX_VISION_VIEWPORT_WIDTH
                ),
                vision_viewport_height=_bounded_positive_int(
                    "VISION_VIEWPORT_HEIGHT",
                    MAX_VISION_VIEWPORT_HEIGHT,
                    MAX_VISION_VIEWPORT_HEIGHT,
                ),
                max_vision_screenshot_bytes=_bounded_positive_int(
                    "MAX_VISION_SCREENSHOT_BYTES",
                    MAX_VISION_SCREENSHOT_BYTES,
                    MAX_VISION_SCREENSHOT_BYTES,
                ),
                max_vision_screenshots=_bounded_positive_int(
                    "MAX_VISION_SCREENSHOTS", MAX_VISION_SCREENSHOTS, MAX_VISION_SCREENSHOTS
                ),
                max_vision_capture_ms=_bounded_positive_int(
                    "MAX_VISION_CAPTURE_MS", MAX_VISION_CAPTURE_MS, MAX_VISION_CAPTURE_MS
                ),
            ),
        )
