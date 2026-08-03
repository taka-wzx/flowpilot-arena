"""Deterministic Temporal workflow identity and result binding tests."""

from datetime import UTC, datetime, timedelta

import pytest
from temporalio.exceptions import WorkflowAlreadyStartedError

from flowpilot_workflow_worker.config import WorkerSettings
from flowpilot_workflow_worker.schemas import WorkItem, stable_hash
from flowpilot_workflow_worker.temporal_client import TemporalGateway


def _item() -> WorkItem:
    now = datetime(2026, 8, 1, tzinfo=UTC)
    return WorkItem(
        organization_id="org_temporal_0001",
        outbox_id="out_temporal_0001",
        run_id="run_temporal_0001",
        executor_user_id="usr_temporal_0001",
        task_id="w7-jml-joiner-001-v1",
        process="joiner",
        category="standard_joiner",
        action_type="create_ticket",
        parameter_hash=stable_hash(
            {
                "schema_version": "w11-action-binding/1.0",
                "action_type": "create_ticket",
                "parameters": {
                    "schema_version": "w11-create-ticket-parameters/1.0",
                    "employee_id": 41011,
                    "ticket_code": "w7.joiner001v1",
                },
            }
        ),
        authorization_hash="a" * 64,
        payload_reference="taskref_temporal_0001",
        payload_hash=stable_hash(
            {
                "schema_version": "w12-trusted-task-reference/1.0",
                "task_id": "w7-jml-joiner-001-v1",
                "process": "joiner",
                "category": "standard_joiner",
            }
        ),
        workflow_id="workflow_temporal_0001",
        workflow_hash="b" * 64,
        worker_owner_hash="c" * 64,
        fencing_token=1,
        lease_version=1,
        attempt_count=1,
        leased_at=now,
        lease_expires_at=now + timedelta(seconds=30),
    )


def _result(item: WorkItem, *, run_id: str | None = None) -> dict[str, object]:
    return {
        "schema_version": "w8-workflow-result/1.0",
        "workflow_id": item.workflow_id,
        "run_id": run_id or item.run_id,
        "task_id": item.task_id,
        "status": "finished_ungraded",
        "terminal_reason": "workflow_finished_ungraded",
        "plan_hash": None,
        "revision": 1,
        "session_epoch": 1,
        "completed_step_ids": [],
        "checkpoint_count": 0,
        "latest_checkpoint_hash": None,
        "usage": {},
    }


class FakeHandle:
    def __init__(self, result: dict[str, object]) -> None:
        self._result = result

    async def result(self) -> dict[str, object]:
        return self._result


class FakeClient:
    def __init__(self, result: dict[str, object], *, duplicate: bool) -> None:
        self.handle = FakeHandle(result)
        self.duplicate = duplicate
        self.started: list[tuple[str, str, str]] = []
        self.retrieved: list[str] = []

    async def start_workflow(
        self,
        workflow_type: str,
        payload: dict[str, object],
        *,
        id: str,
        task_queue: str,
        result_type: object,
    ) -> FakeHandle:
        del payload, result_type
        self.started.append((workflow_type, id, task_queue))
        if self.duplicate:
            raise WorkflowAlreadyStartedError(id, workflow_type, run_id="temporal-run-0001")
        return self.handle

    def get_workflow_handle(self, workflow_id: str, *, result_type: object) -> FakeHandle:
        del result_type
        self.retrieved.append(workflow_id)
        return self.handle


@pytest.mark.parametrize("duplicate", [False, True])
async def test_start_or_deduplicate_uses_one_workflow_identity(
    settings: WorkerSettings,
    duplicate: bool,
) -> None:
    item = _item()
    client = FakeClient(_result(item), duplicate=duplicate)
    gateway = TemporalGateway(client, settings)  # type: ignore[arg-type]
    outcome = await gateway.start_and_wait(item)
    assert client.started == [
        (
            "FlowPilotDurableRecoveryWorkflow",
            item.workflow_id,
            "flowpilot-w8-recovery",
        )
    ]
    assert client.retrieved == ([item.workflow_id] if duplicate else [])
    assert outcome.deduplicated_start is duplicate
    assert outcome.result.status == "finished_ungraded"


async def test_result_binding_mismatch_fails_closed(settings: WorkerSettings) -> None:
    item = _item()
    client = FakeClient(_result(item, run_id="run_other_0001"), duplicate=False)
    gateway = TemporalGateway(client, settings)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="binding changed"):
        await gateway.start_and_wait(item)
