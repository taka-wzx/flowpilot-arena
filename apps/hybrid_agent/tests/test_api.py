from conftest import hybrid_dom_observation, supplied_values_brief
from fastapi.testclient import TestClient

from flowpilot_hybrid_agent.main import app
from flowpilot_hybrid_agent.schemas import HybridActionResult, HybridSessionCreated


class StubBrowser:
    async def create_session(self) -> HybridSessionCreated:
        return HybridSessionCreated(
            session_id="bw_abcdefghijklmnop",
            observation=hybrid_dom_observation(),
        )

    async def execute_action(self, session_id: str, action: object) -> HybridActionResult:
        action_id = action.action.action_id  # type: ignore[attr-defined]
        return HybridActionResult(
            session_id=session_id,
            action_id=action_id,
            modality="dom",
            action_type="finish",
            success=True,
            terminal=True,
            message="Synthetic",
        )

    async def close_session(self, _: str) -> None:
        pass

    async def close(self) -> None:
        pass


def test_api_runs_only_the_strict_fake_model_and_returns_no_grade_fields() -> None:
    with TestClient(app) as client:
        app.state.browser_client = StubBrowser()
        assert client.get("/healthz").json()["service"] == "hybrid-agent"
        response = client.post(
            "/api/hybrid-agent/runs",
            json={
                "schema_version": "w6-hybrid-agent-run/1.0",
                "task_id": "w3-joiner-001",
                "instruction": supplied_values_brief(),
                "route_category": "standard",
                "model": "deterministic-fake-hybrid",
                "fake_scenario": "finish_immediately",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "finished_ungraded"
        assert not ({"success", "passed", "score", "image_base64"} & set(payload))

        unknown = client.post(
            "/api/hybrid-agent/runs",
            json={
                "schema_version": "w6-hybrid-agent-run/1.0",
                "task_id": "w3-joiner-001",
                "instruction": supplied_values_brief(),
                "model": "deterministic-fake-hybrid",
                "fake_scenario": "finish_immediately",
                "provider_url": "https://example.invalid",
            },
        )
        assert unknown.status_code == 422
