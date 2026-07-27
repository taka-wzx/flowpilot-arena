from conftest import FakeBrowserClient
from fastapi.testclient import TestClient

from flowpilot_vision_agent.main import app


def test_api_runs_only_fake_vision_and_returns_ungraded_result() -> None:
    with TestClient(app) as client:
        browser = FakeBrowserClient()
        app.state.browser_client = browser
        response = client.post(
            "/api/vision-agent/runs",
            json={
                "schema_version": "w5-vision-agent-run/1.0",
                "task_id": "w3-joiner-001",
                "instruction": "Synthetic human instruction",
                "model": "deterministic-fake-vision",
                "fake_scenario": "finish_immediately",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "finished_ungraded"
        assert "passed" not in body and "success" not in body and "score" not in body

        rejected = client.post(
            "/api/vision-agent/runs",
            json={
                "schema_version": "w5-vision-agent-run/1.0",
                "task_id": "w3-joiner-001",
                "instruction": "Synthetic human instruction",
                "model": "external-provider",
            },
        )
        assert rejected.status_code == 422
