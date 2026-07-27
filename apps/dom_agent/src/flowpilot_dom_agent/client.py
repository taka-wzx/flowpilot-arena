from urllib.parse import urlsplit

import httpx

from flowpilot_dom_agent.schemas import ActionResult, BrowserAction, SessionCreated


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

    async def create_session(self) -> SessionCreated:
        response = await self._client.post(
            f"{self._base_url}/api/browser/sessions",
            json={"schema_version": "w4-browser-session/1.0", "initial_path": "/hris"},
        )
        response.raise_for_status()
        return SessionCreated.model_validate_json(response.text)

    async def execute_action(self, session_id: str, action: BrowserAction) -> ActionResult:
        response = await self._client.post(
            f"{self._base_url}/api/browser/sessions/{session_id}/actions",
            json=action.model_dump(mode="json"),
        )
        response.raise_for_status()
        return ActionResult.model_validate_json(response.text)

    async def close_session(self, session_id: str) -> None:
        response = await self._client.delete(f"{self._base_url}/api/browser/sessions/{session_id}")
        response.raise_for_status()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
