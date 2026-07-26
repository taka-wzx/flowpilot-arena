"""Tests for the W1 health endpoint."""

import httpx
import pytest

from flowpilot_control_api.main import app


@pytest.fixture
def anyio_backend() -> str:
    """Run the ASGI smoke test on the installed asyncio backend only."""

    return "asyncio"


@pytest.mark.anyio
async def test_healthz_returns_static_service_metadata() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "control-api",
        "version": "0.1.0",
    }
