"""Public W10 health endpoint regression."""

from fastapi.testclient import TestClient


def test_healthz_remains_public_and_static(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "control-api",
        "version": "0.10.0",
    }
