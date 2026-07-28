from urllib.parse import urlsplit

import httpx

from flowpilot_recovery_worker.schemas import ActivityRequest, ActivityResult, PlainRunInput


class PlanningRecoveryClient:
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"planning-agent", "localhost", "127.0.0.1", "::1"}
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("PLANNING_AGENT_URL must be a credential-free local HTTP origin")
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(20.0))
        self._owns_client = client is None

    async def invoke(
        self,
        command: str,
        request: ActivityRequest,
        plain: PlainRunInput,
    ) -> ActivityResult:
        if command not in {"start", "step", "refresh", "recover", "replan", "cleanup"}:
            raise ValueError("unknown Planning recovery command")
        payload = {
            "schema_version": "w8-planning-activity/1.0",
            "command": command,
            "workflow_id": plain.workflow_id,
            "run_id": plain.run_id,
            "task_id": plain.task_id,
            "process": plain.process,
            "category": plain.category,
            "human_brief": plain.human_brief,
            "supplied_values": plain.supplied_values,
            "fault_scenario": request.start.fault_scenario,
            "checkpoint": (
                request.checkpoint.model_dump(mode="json")
                if request.checkpoint is not None
                else None
            ),
            "step_id": request.step_id,
            "session_epoch": request.session_epoch,
            "revision": request.revision,
        }
        response = await self._client.post(
            f"{self._base_url}/api/planning/recovery/activities", json=payload
        )
        response.raise_for_status()
        return ActivityResult.model_validate_json(response.text)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
