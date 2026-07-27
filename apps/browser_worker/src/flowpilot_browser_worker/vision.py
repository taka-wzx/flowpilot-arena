import base64
import math
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Final, Literal

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import FloatRect, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from flowpilot_browser_worker.config import WorkerLimits
from flowpilot_browser_worker.observation import (
    ElementTarget,
    extract_interactive_elements,
    normalize_text,
)
from flowpilot_browser_worker.schemas import (
    VisionLastAction,
    VisionObservation,
    VisualBounds,
    VisualGrounding,
)

JPEG_QUALITY: Final = 60
JPEG_MIME_TYPE: Final[Literal["image/jpeg"]] = "image/jpeg"


class VisionCaptureError(RuntimeError):
    def __init__(
        self,
        category: Literal[
            "screenshot_budget_exhausted",
            "screenshot_byte_limit_exceeded",
            "screenshot_capture_timeout",
        ],
        message: str,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.message = message


@dataclass(frozen=True, slots=True)
class VisionObservationBuild:
    observation: VisionObservation
    references: dict[str, ElementTarget]


class VisionObservationBuilder:
    def __init__(
        self,
        limits: WorkerLimits,
        nonce_factory: Callable[[], str] | None = None,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._limits = limits
        self._nonce_factory = nonce_factory or (lambda: secrets.token_urlsafe(9))
        self._clock = clock

    async def build(
        self,
        page: Page,
        session_id: str,
        last_action: VisionLastAction | None = None,
        page_error: str | None = None,
    ) -> VisionObservationBuild:
        nonce = self._nonce_factory()
        started = self._clock()
        try:
            image = await page.screenshot(
                type="jpeg",
                quality=JPEG_QUALITY,
                full_page=False,
                animations="disabled",
                caret="hide",
                scale="css",
                timeout=self._limits.max_vision_capture_ms,
            )
        except PlaywrightTimeoutError as exc:
            raise VisionCaptureError(
                "screenshot_capture_timeout",
                "Screenshot capture exceeded its configured limit",
            ) from exc
        capture_duration_ms = max(0, math.ceil((self._clock() - started) * 1_000))
        if capture_duration_ms > self._limits.max_vision_capture_ms:
            raise VisionCaptureError(
                "screenshot_capture_timeout",
                "Screenshot capture exceeded its configured limit",
            )
        if len(image) > self._limits.max_vision_screenshot_bytes:
            raise VisionCaptureError(
                "screenshot_byte_limit_exceeded",
                "Screenshot exceeded its configured byte limit",
            )

        _, dom_references, interactive_truncated = await extract_interactive_elements(
            page, nonce, self._limits
        )
        groundings, references, bounds_truncated = await self._groundings(dom_references, nonce)
        error = normalize_text(page_error, 300) if page_error else None
        observation = VisionObservation(
            session_id=session_id,
            observation_id=f"vobs_{nonce}",
            screenshot_ref=f"shot_{nonce}",
            image_mime_type=JPEG_MIME_TYPE,
            image_base64=base64.b64encode(image).decode("ascii"),
            image_width=self._limits.vision_viewport_width,
            image_height=self._limits.vision_viewport_height,
            image_bytes=len(image),
            capture_duration_ms=capture_duration_ms,
            groundings=tuple(groundings),
            last_action=last_action,
            page_error=error,
            truncated=interactive_truncated or bounds_truncated,
        )
        return VisionObservationBuild(observation=observation, references=references)

    async def _groundings(
        self,
        dom_references: dict[str, ElementTarget],
        nonce: str,
    ) -> tuple[list[VisualGrounding], dict[str, ElementTarget], bool]:
        groundings: list[VisualGrounding] = []
        references: dict[str, ElementTarget] = {}
        truncated = False
        for index, target in enumerate(dom_references.values(), start=1):
            try:
                box = await target.locator.bounding_box()
            except PlaywrightError:
                truncated = True
                continue
            bounds = self._clip_bounds(box)
            if bounds is None:
                truncated = True
                continue
            grounding_ref = f"gref_{nonce}_{index}"
            groundings.append(
                VisualGrounding(
                    grounding_ref=grounding_ref,
                    bounds=bounds,
                    allowed_actions=target.allowed_actions,
                )
            )
            references[grounding_ref] = target
        return groundings, references, truncated

    def _clip_bounds(self, box: FloatRect | None) -> VisualBounds | None:
        if box is None:
            return None
        left = max(0, math.floor(box["x"]))
        top = max(0, math.floor(box["y"]))
        right = min(
            self._limits.vision_viewport_width,
            math.ceil(box["x"] + box["width"]),
        )
        bottom = min(
            self._limits.vision_viewport_height,
            math.ceil(box["y"] + box["height"]),
        )
        if right <= left or bottom <= top:
            return None
        return VisualBounds(x=left, y=top, width=right - left, height=bottom - top)
