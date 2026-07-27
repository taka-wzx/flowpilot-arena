import base64

from fastapi.testclient import TestClient

from flowpilot_browser_worker.main import app
from flowpilot_browser_worker.schemas import (
    Observation,
    SessionClosed,
    SessionCreated,
    VisionActionResult,
    VisionBrowserAction,
    VisionSessionClosed,
    VisionSessionCreated,
)


class StubRuntime:
    async def create_session(self, _: str) -> SessionCreated:
        observation = Observation(
            session_id="bw_abcdefghijklmnop",
            observation_id="obs_abcdefgh",
            current_url="http://sandbox-web/hris",
            page_title="HRIS",
            semantic_nodes=(),
            interactive_elements=(),
            truncated=False,
        )
        return SessionCreated(session_id=observation.session_id, observation=observation)

    async def close_session(self, session_id: str) -> SessionClosed:
        return SessionClosed(session_id=session_id, closed=True)

    async def create_vision_session(self, _: str) -> VisionSessionCreated:
        return VisionSessionCreated(
            session_id="bw_abcdefghijklmnop",
            observation={
                "session_id": "bw_abcdefghijklmnop",
                "observation_id": "vobs_visual0001",
                "screenshot_ref": "shot_visual0001",
                "image_mime_type": "image/jpeg",
                "image_base64": base64.b64encode(b"\xff\xd8fake\xff\xd9").decode("ascii"),
                "image_width": 960,
                "image_height": 540,
                "image_bytes": 8,
                "capture_duration_ms": 1,
                "groundings": (),
                "truncated": False,
            },
        )

    async def execute_vision_action(
        self, session_id: str, action: VisionBrowserAction
    ) -> VisionActionResult:
        return VisionActionResult(
            session_id=session_id,
            action_id=action.action_id,
            action_type=action.type,
            success=action.type == "finish",
            terminal=True,
            message="Visual Agent loop ended",
        )

    async def close_vision_session(self, session_id: str) -> VisionSessionClosed:
        return VisionSessionClosed(session_id=session_id, closed=True)

    async def close_all(self) -> None:
        pass


def test_api_health_strict_session_and_unknown_action_rejection() -> None:
    with TestClient(app) as client:
        app.state.runtime = StubRuntime()
        assert client.get("/healthz").json()["status"] == "ok"
        created = client.post(
            "/api/browser/sessions",
            json={"schema_version": "w4-browser-session/1.0", "initial_path": "/hris"},
        )
        assert created.status_code == 201
        unknown_field = client.post(
            "/api/browser/sessions",
            json={
                "schema_version": "w4-browser-session/1.0",
                "initial_path": "/hris",
                "selector": "#unsafe",
            },
        )
        assert unknown_field.status_code == 422
        unknown_action = client.post(
            "/api/browser/sessions/bw_abcdefghijklmnop/actions",
            json={
                "schema_version": "w4-dom-action/1.0",
                "action_id": "act_bad",
                "type": "javascript",
                "code": "document.cookie",
            },
        )
        assert unknown_action.status_code == 422
        closed = client.delete("/api/browser/sessions/bw_abcdefghijklmnop")
        assert closed.status_code == 200 and closed.json()["closed"] is True
        vision_created = client.post(
            "/api/browser/vision-sessions",
            json={"schema_version": "w5-vision-session/1.0", "initial_path": "/hris"},
        )
        assert vision_created.status_code == 201
        assert "semantic_nodes" not in vision_created.json()["observation"]
        rejected_coordinate = client.post(
            "/api/browser/vision-sessions/bw_abcdefghijklmnop/actions",
            json={
                "schema_version": "w5-vision-action/1.0",
                "action_id": "act_vision_bad",
                "type": "read",
                "observation_id": "vobs_visual0001",
                "screenshot_ref": "shot_visual0001",
                "grounding_ref": "gref_visual0001_1",
                "x": 4,
            },
        )
        assert rejected_coordinate.status_code == 422
        vision_closed = client.delete("/api/browser/vision-sessions/bw_abcdefghijklmnop")
        assert vision_closed.status_code == 200 and vision_closed.json()["closed"] is True
