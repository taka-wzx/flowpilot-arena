import httpx
import pytest

from flowpilot_planning_agent.client import BrowserWorkerClient
from flowpilot_planning_agent.worker_schemas import RecoveryDomActionEnvelope


@pytest.mark.parametrize(
    "url",
    (
        "https://browser-worker:8002",
        "http://sandbox-web",
        "http://user:secret@browser-worker:8002",
        "http://browser-worker:8002/api",
        "http://example.invalid",
    ),
)
def test_client_rejects_non_worker_origins(url: str) -> None:
    with pytest.raises(ValueError):
        BrowserWorkerClient(url)


async def test_client_accepts_fixed_worker_origin() -> None:
    client = BrowserWorkerClient("http://browser-worker:8002")
    assert client is not None
    await client.close()


async def test_recovery_calls_use_fixed_25_second_timeout() -> None:
    observed: list[dict[str, float]] = []

    def capture(request: httpx.Request) -> httpx.Response:
        observed.append(request.extensions["timeout"])
        raise RuntimeError("timeout captured")

    async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as http_client:
        client = BrowserWorkerClient(
            "http://browser-worker:8002",
            http_client,
        )
        envelope = RecoveryDomActionEnvelope.model_validate(
            {
                "session_id": "bw_abcdefghijklmnop",
                "session_epoch": 1,
                "generation": 1,
                "action": {
                    "action_id": "act_w8_finish",
                    "type": "finish",
                    "summary": "finished",
                },
            }
        )
        calls = (
            client.create_recovery_session(1),
            client.request_recovery_observation("bw_abcdefghijklmnop", 1),
            client.execute_recovery_action("bw_abcdefghijklmnop", envelope),
            client.close_recovery_session("bw_abcdefghijklmnop"),
        )
        for call in calls:
            with pytest.raises(RuntimeError, match="timeout captured"):
                await call

    assert len(observed) == 4
    assert all(
        timeout == {"connect": 25.0, "read": 25.0, "write": 25.0, "pool": 25.0}
        for timeout in observed
    )
