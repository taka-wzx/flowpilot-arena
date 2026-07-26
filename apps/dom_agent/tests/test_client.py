import json

import httpx
import pytest
from conftest import make_observation

from flowpilot_dom_agent.client import BrowserWorkerClient


@pytest.mark.parametrize(
    "url",
    (
        "https://browser-worker:8002",
        "http://example.com:8002",
        "http://user:pass@browser-worker:8002",
        "http://browser-worker:8002/api",
    ),
)
def test_client_rejects_nonlocal_or_credentialed_worker_urls(url: str) -> None:
    with pytest.raises(ValueError):
        BrowserWorkerClient(url)


async def test_client_uses_only_fixed_worker_routes_and_strict_responses() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(f"{request.method} {request.url.path}")
        if request.method == "POST":
            observation = make_observation()
            return httpx.Response(
                201,
                json={
                    "schema_version": "w4-browser-session/1.0",
                    "session_id": observation.session_id,
                    "observation": json.loads(observation.model_dump_json()),
                },
            )
        return httpx.Response(
            200,
            json={
                "schema_version": "w4-browser-session/1.0",
                "session_id": "bw_abcdefghijklmnop",
                "closed": True,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = BrowserWorkerClient("http://browser-worker:8002", http_client)
        created = await client.create_session()
        await client.close_session(created.session_id)
    assert seen == [
        "POST /api/browser/sessions",
        "DELETE /api/browser/sessions/bw_abcdefghijklmnop",
    ]
