from fastapi.testclient import TestClient

from flowpilot_browser_worker.main import app
from flowpilot_browser_worker.schemas import Observation, SessionClosed, SessionCreated


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
