import httpx
import pytest

from flowpilot_recovery_worker.client import PlanningRecoveryClient
from flowpilot_recovery_worker.schemas import ActivityRequest


def test_client_rejects_external_or_credentialed_origins() -> None:
    for value in (
        "https://planning-agent:8006",
        "http://user:pass@planning-agent:8006",
        "http://example.com",
        "http://planning-agent:8006/path",
    ):
        with pytest.raises(ValueError):
            PlanningRecoveryClient(value)


async def test_client_sends_only_fixed_planning_route(workflow_start, plain_input) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/planning/recovery/activities"
        return httpx.Response(
            200,
            json={
                "schema_version": "w8-activity-result/1.0",
                "outcome": "cleaned",
                "safe_reason": "cleaned",
                "plan_hash": None,
                "topology": [],
                "step_id": None,
                "session_epoch": 1,
                "revision": 1,
                "receipt": None,
                "replaced_step_ids": [],
                "activity_attempt": 1,
            },
        )

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = PlanningRecoveryClient("http://planning-agent:8006", http_client)
    result = await client.invoke("cleanup", ActivityRequest(start=workflow_start), plain_input)
    assert result.outcome == "cleaned"
    await http_client.aclose()
