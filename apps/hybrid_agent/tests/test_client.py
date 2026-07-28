import httpx
import pytest
from conftest import hybrid_dom_observation
from pydantic import TypeAdapter

from flowpilot_hybrid_agent.client import BrowserWorkerClient
from flowpilot_hybrid_agent.schemas import (
    HybridActionEnvelope,
    HybridActionResult,
    HybridSessionCreated,
)


async def test_client_uses_only_fixed_hybrid_worker_routes() -> None:
    calls: list[str] = []
    created = HybridSessionCreated(
        session_id="bw_abcdefghijklmnop",
        observation=hybrid_dom_observation(),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.method == "POST" and request.url.path.endswith("/hybrid-sessions"):
            return httpx.Response(201, json=created.model_dump(mode="json"))
        if request.url.path.endswith("/observations"):
            return httpx.Response(200, json=created.observation.model_dump(mode="json"))
        if request.url.path.endswith("/actions"):
            return httpx.Response(
                200,
                json=HybridActionResult(
                    session_id="bw_abcdefghijklmnop",
                    action_id="act_finish",
                    modality="dom",
                    action_type="finish",
                    success=True,
                    terminal=True,
                    message="Synthetic",
                ).model_dump(mode="json"),
            )
        return httpx.Response(200, json={"closed": True})

    client = BrowserWorkerClient(
        "http://browser-worker:8002",
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    session = await client.create_session()
    observation = await client.request_observation(session.session_id, "dom")
    action = TypeAdapter(HybridActionEnvelope).validate_python(
        {
            "schema_version": "w6-hybrid-action-envelope/1.0",
            "session_id": session.session_id,
            "generation": observation.generation,
            "modality": "dom",
            "action": {
                "action_id": "act_finish",
                "type": "finish",
                "summary": "Synthetic",
            },
        }
    )
    result = await client.execute_action(
        session.session_id,
        action,
    )
    await client.close_session(session.session_id)

    assert observation.modality == "dom"
    assert result.terminal is True
    assert calls == [
        "/api/browser/hybrid-sessions",
        "/api/browser/hybrid-sessions/bw_abcdefghijklmnop/observations",
        "/api/browser/hybrid-sessions/bw_abcdefghijklmnop/actions",
        "/api/browser/hybrid-sessions/bw_abcdefghijklmnop",
    ]


def test_client_rejects_non_worker_or_credentialed_urls() -> None:
    with pytest.raises(ValueError):
        BrowserWorkerClient("https://browser-worker")
    with pytest.raises(ValueError):
        BrowserWorkerClient("http://user:pass@browser-worker")
    with pytest.raises(ValueError):
        BrowserWorkerClient("http://sandbox-web")
