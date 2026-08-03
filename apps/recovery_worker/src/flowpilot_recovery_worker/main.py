import asyncio
from os import environ

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from flowpilot_recovery_worker.activities import RecoveryActivities
from flowpilot_recovery_worker.client import PlanningRecoveryClient
from flowpilot_recovery_worker.crypto import decode_runtime_key
from flowpilot_recovery_worker.workflow import DurableRecoveryWorkflow

TASK_QUEUE = "flowpilot-w8-recovery"
NAMESPACE = "flowpilot-w8"
MAX_CONCURRENT_ACTIVITIES = 2
MAX_CONCURRENT_WORKFLOW_TASKS = 4


async def run_worker() -> None:
    temporal_address = environ.get("TEMPORAL_ADDRESS", "temporal:7233")
    if temporal_address != "temporal:7233":
        raise ValueError("TEMPORAL_ADDRESS must name the fixed local Temporal service")
    key_value = environ.get("RECOVERY_ENVELOPE_KEY")
    if key_value is None:
        raise ValueError("RECOVERY_ENVELOPE_KEY is required at runtime")
    planning = PlanningRecoveryClient(
        environ.get("PLANNING_AGENT_URL", "http://planning-agent:8006")
    )
    try:
        client = await Client.connect(
            temporal_address,
            namespace=NAMESPACE,
            data_converter=pydantic_data_converter,
        )
        activities = RecoveryActivities(planning, decode_runtime_key(key_value))
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[DurableRecoveryWorkflow],
            activities=[
                activities.start_run,
                activities.execute_step,
                activities.refresh,
                activities.recover,
                activities.replan,
                activities.cleanup,
            ],
            max_concurrent_activities=MAX_CONCURRENT_ACTIVITIES,
            max_concurrent_workflow_tasks=MAX_CONCURRENT_WORKFLOW_TASKS,
        )
        await worker.run()
    finally:
        await planning.close()


if __name__ == "__main__":
    asyncio.run(run_worker())
