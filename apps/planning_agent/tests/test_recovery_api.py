from fastapi.testclient import TestClient

from flowpilot_planning_agent.main import app
from flowpilot_planning_agent.recovery_schemas import PlanningActivityResult


class StubCoordinator:
    async def invoke(self, payload) -> PlanningActivityResult:
        return PlanningActivityResult(
            outcome="cleaned",
            safe_reason="stub cleanup",
            session_epoch=payload.session_epoch,
            revision=payload.revision,
        )

    async def close_all(self) -> None:
        pass


def test_recovery_api_is_strict_and_versioned() -> None:
    with TestClient(app) as client:
        app.state.recovery_coordinator = StubCoordinator()
        payload = {
            "schema_version": "w8-planning-activity/1.0",
            "command": "cleanup",
            "workflow_id": "workflow_w8_api",
            "run_id": "run_w8_api",
            "task_id": "w7-jml-leaver-001-v1",
            "process": "leaver",
            "category": "standard_leaver",
            "human_brief": "Synthetic bounded brief",
            "supplied_values": {"process": "leaver", "employee_id": 101},
            "fault_scenario": "none",
            "checkpoint": None,
            "step_id": None,
            "session_epoch": 1,
            "revision": 1,
        }
        response = client.post("/api/planning/recovery/activities", json=payload)
        assert response.status_code == 200
        assert response.json()["schema_version"] == "w8-activity-result/1.0"
        payload["selector"] = "#unsafe"
        assert client.post("/api/planning/recovery/activities", json=payload).status_code == 422
