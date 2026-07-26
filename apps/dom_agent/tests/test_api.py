from conftest import FakeBrowserClient
from fastapi.testclient import TestClient

from flowpilot_dom_agent.main import app


def test_api_runs_only_deterministic_fake_and_returns_ungraded_result() -> None:
    with TestClient(app) as client:
        browser = FakeBrowserClient()
        app.state.browser_client = browser
        response = client.post(
            "/api/agent/runs",
            json={
                "schema_version": "w4-dom-agent-run/1.0",
                "task_id": "w3-joiner-001",
                "instruction": "Synthetic human instruction",
                "model": "deterministic-fake",
                "fake_scenario": "finish_immediately",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "finished_ungraded"
        assert "passed" not in body and "success" not in body and "score" not in body

        rejected = client.post(
            "/api/agent/runs",
            json={
                "schema_version": "w4-dom-agent-run/1.0",
                "task_id": "w3-joiner-001",
                "instruction": "Synthetic human instruction",
                "model": "external-provider",
            },
        )
        assert rejected.status_code == 422


def test_authorized_model_requires_environment_credential(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.post(
            "/api/agent/runs",
            json={
                "schema_version": "w4-dom-agent-run/1.0",
                "task_id": "w3-joiner-001",
                "instruction": "Synthetic human instruction",
                "model": "openai-gpt-5.6-terra",
            },
        )
        assert response.status_code == 503
        assert response.json() == {"detail": "Authorized model credential is unavailable"}
