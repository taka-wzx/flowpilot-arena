import base64

import pytest

from flowpilot_vision_agent.schemas import (
    VisionActionResult,
    VisionBrowserAction,
    VisionObservation,
    VisionSessionCreated,
    VisualBounds,
    VisualGrounding,
)


def make_observation(counter: int = 1, *, same_image: bool = False) -> VisionObservation:
    image_suffix = 1 if same_image else counter
    image = b"\xff\xd8synthetic-" + str(image_suffix).encode("ascii") + b"\xff\xd9"
    return VisionObservation(
        schema_version="w5-vision-observation/1.0",
        session_id="bw_abcdefghijklmnop",
        observation_id=f"vobs_visual{counter:04d}",
        screenshot_ref=f"shot_visual{counter:04d}",
        image_mime_type="image/jpeg",
        image_base64=base64.b64encode(image).decode("ascii"),
        image_width=960,
        image_height=540,
        image_bytes=len(image),
        capture_duration_ms=1,
        groundings=(
            VisualGrounding(
                grounding_ref=f"gref_visual{counter:04d}_1",
                bounds=VisualBounds(x=10, y=10, width=20, height=20),
                allowed_actions=("click", "fill", "select", "read", "scroll"),
            ),
        ),
        truncated=False,
    )


def make_joiner_observation(counter: int = 1) -> VisionObservation:
    observation = make_observation(counter)
    return observation.model_copy(
        update={
            "groundings": (
                VisualGrounding(
                    grounding_ref=f"gref_joiner{counter:04d}_read",
                    bounds=VisualBounds(x=10, y=10, width=70, height=24),
                    allowed_actions=("click", "read", "scroll"),
                ),
                VisualGrounding(
                    grounding_ref=f"gref_joiner{counter:04d}_fill1",
                    bounds=VisualBounds(x=10, y=250, width=180, height=36),
                    allowed_actions=("fill", "read", "scroll"),
                ),
                VisualGrounding(
                    grounding_ref=f"gref_joiner{counter:04d}_fill2",
                    bounds=VisualBounds(x=220, y=250, width=180, height=36),
                    allowed_actions=("fill", "read", "scroll"),
                ),
                VisualGrounding(
                    grounding_ref=f"gref_joiner{counter:04d}_fill3",
                    bounds=VisualBounds(x=430, y=250, width=180, height=36),
                    allowed_actions=("fill", "read", "scroll"),
                ),
                VisualGrounding(
                    grounding_ref=f"gref_joiner{counter:04d}_submit",
                    bounds=VisualBounds(x=10, y=320, width=160, height=43),
                    allowed_actions=("click", "read", "scroll"),
                ),
            )
        }
    )


class FakeBrowserClient:
    def __init__(self, *, same_image: bool = False, joiner_geometry: bool = False) -> None:
        self.counter = 1
        self.same_image = same_image
        self.joiner_geometry = joiner_geometry
        self.actions: list[VisionBrowserAction] = []
        self.closed = False

    def _observation(self) -> VisionObservation:
        if self.joiner_geometry:
            return make_joiner_observation(self.counter)
        return make_observation(self.counter, same_image=self.same_image)

    async def create_session(self) -> VisionSessionCreated:
        observation = self._observation()
        return VisionSessionCreated(
            schema_version="w5-vision-session/1.0",
            session_id=observation.session_id,
            observation=observation,
        )

    async def execute_action(
        self, session_id: str, action: VisionBrowserAction
    ) -> VisionActionResult:
        assert session_id == "bw_abcdefghijklmnop"
        self.actions.append(action)
        if action.type in {"finish", "fail"}:
            self.closed = True
            return VisionActionResult(
                schema_version="w5-vision-action-result/1.0",
                session_id=session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=action.type == "finish",
                terminal=True,
                message="terminal",
            )
        self.counter += 1
        return VisionActionResult(
            schema_version="w5-vision-action-result/1.0",
            session_id=session_id,
            action_id=action.action_id,
            action_type=action.type,
            success=True,
            terminal=False,
            message="grounded action completed",
            observation=self._observation(),
        )

    async def close_session(self, _: str) -> None:
        self.closed = True

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_browser() -> FakeBrowserClient:
    return FakeBrowserClient()
