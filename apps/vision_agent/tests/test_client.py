import json

import httpx
import pytest
from conftest import make_observation

from flowpilot_vision_agent.client import BrowserWorkerClient
from flowpilot_vision_agent.schemas import VisionFinishAction


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


async def test_client_uses_only_fixed_visual_worker_routes_and_strict_responses() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(f"{request.method} {request.url.path}")
        observation = make_observation()
        if request.method == "POST" and request.url.path.endswith("vision-sessions"):
            return httpx.Response(
                201,
                json={
                    "schema_version": "w5-vision-session/1.0",
                    "session_id": observation.session_id,
                    "observation": json.loads(observation.model_dump_json()),
                },
            )
        if request.method == "POST":
            payload = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "schema_version": "w5-vision-action-result/1.0",
                    "session_id": observation.session_id,
                    "action_id": payload["action_id"],
                    "action_type": payload["type"],
                    "success": True,
                    "terminal": True,
                    "message": "terminal",
                },
            )
        return httpx.Response(
            200,
            json={
                "schema_version": "w5-vision-session/1.0",
                "session_id": observation.session_id,
                "closed": True,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = BrowserWorkerClient("http://browser-worker:8002", http_client)
        created = await client.create_session()
        await client.execute_action(
            created.session_id,
            VisionFinishAction(action_id="act_finish", type="finish"),
        )
        await client.close_session(created.session_id)

    assert seen == [
        "POST /api/browser/vision-sessions",
        "POST /api/browser/vision-sessions/bw_abcdefghijklmnop/actions",
        "DELETE /api/browser/vision-sessions/bw_abcdefghijklmnop",
    ]
