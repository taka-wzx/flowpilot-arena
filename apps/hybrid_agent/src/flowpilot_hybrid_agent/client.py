from urllib.parse import urlsplit

import httpx
from pydantic import TypeAdapter

from flowpilot_hybrid_agent.schemas import (
    HybridActionEnvelope,
    HybridActionResult,
    HybridModality,
    HybridObservation,
    HybridObservationRequest,
    HybridSessionCreated,
)

_HYBRID_OBSERVATION_ADAPTER: TypeAdapter[HybridObservation] = TypeAdapter(HybridObservation)


class BrowserWorkerClient:
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        parsed = urlsplit(base_url)
        if parsed.scheme != "http" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("BROWSER_WORKER_URL must be a credential-free HTTP origin")
        if parsed.hostname.lower() not in {"browser-worker", "localhost", "127.0.0.1", "::1"}:
            raise ValueError("BROWSER_WORKER_URL must name the local Browser Worker service")
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("BROWSER_WORKER_URL must not contain a path, query, or fragment")
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(10.0))
        self._owns_client = client is None

    async def create_session(self) -> HybridSessionCreated:
        response = await self._client.post(
            f"{self._base_url}/api/browser/hybrid-sessions",
            json={"schema_version": "w6-hybrid-session/1.0", "initial_path": "/hris"},
        )
        response.raise_for_status()
        return HybridSessionCreated.model_validate_json(response.text)

    async def request_observation(
        self,
        session_id: str,
        modality: HybridModality,
    ) -> HybridObservation:
        payload = HybridObservationRequest(modality=modality)
        response = await self._client.post(
            f"{self._base_url}/api/browser/hybrid-sessions/{session_id}/observations",
            json=payload.model_dump(mode="json"),
        )
        response.raise_for_status()
        return _HYBRID_OBSERVATION_ADAPTER.validate_json(response.text)

    async def execute_action(
        self,
        session_id: str,
        action: HybridActionEnvelope,
    ) -> HybridActionResult:
        response = await self._client.post(
            f"{self._base_url}/api/browser/hybrid-sessions/{session_id}/actions",
            json=action.model_dump(mode="json"),
        )
        response.raise_for_status()
        return HybridActionResult.model_validate_json(response.text)

    async def close_session(self, session_id: str) -> None:
        response = await self._client.delete(
            f"{self._base_url}/api/browser/hybrid-sessions/{session_id}"
        )
        response.raise_for_status()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
