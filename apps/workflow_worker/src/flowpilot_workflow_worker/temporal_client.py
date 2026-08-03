"""Fixed W8 Temporal client with deterministic workflow identity."""

from temporalio.client import Client, WorkflowHandle
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.exceptions import WorkflowAlreadyStartedError

from flowpilot_workflow_worker.config import WorkerSettings
from flowpilot_workflow_worker.crypto import build_workflow_start
from flowpilot_workflow_worker.schemas import TemporalOutcome, WorkflowResult, WorkItem


class TemporalGateway:
    def __init__(self, client: Client, settings: WorkerSettings) -> None:
        self._client = client
        self._settings = settings
        self._key = settings.decoded_key()

    @classmethod
    async def connect(cls, settings: WorkerSettings) -> "TemporalGateway":
        client = await Client.connect(
            settings.temporal_address,
            namespace=settings.temporal_namespace,
            data_converter=pydantic_data_converter,
        )
        return cls(client, settings)

    async def start_and_wait(self, item: WorkItem) -> TemporalOutcome:
        start = build_workflow_start(item, self._key)
        deduplicated = False
        handle: WorkflowHandle[dict[str, object], dict[str, object]]
        try:
            handle = await self._client.start_workflow(
                "FlowPilotDurableRecoveryWorkflow",
                start.model_dump(mode="json"),
                id=item.workflow_id,
                task_queue=self._settings.temporal_task_queue,
                result_type=dict[str, object],
            )
        except WorkflowAlreadyStartedError:
            deduplicated = True
            handle = self._client.get_workflow_handle(
                item.workflow_id,
                result_type=dict[str, object],
            )
        raw = await handle.result()
        result = WorkflowResult.model_validate(raw)
        if (
            result.workflow_id != item.workflow_id
            or result.run_id != item.run_id
            or result.task_id != item.task_id
        ):
            raise ValueError("Temporal result binding changed")
        return TemporalOutcome(result=result, deduplicated_start=deduplicated)
