import pytest

from flowpilot_planning_agent.client import BrowserWorkerClient


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
