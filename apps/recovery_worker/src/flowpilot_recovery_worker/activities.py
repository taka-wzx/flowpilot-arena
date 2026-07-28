import asyncio

from temporalio import activity
from temporalio.exceptions import ApplicationError

from flowpilot_recovery_worker.client import PlanningRecoveryClient
from flowpilot_recovery_worker.crypto import decrypt_plain_input
from flowpilot_recovery_worker.schemas import ActivityRequest


class RecoveryActivities:
    def __init__(self, client: PlanningRecoveryClient, envelope_key: bytes) -> None:
        self._client = client
        self._key = envelope_key
        self._injected_faults: set[tuple[str, str]] = set()

    async def _invoke(self, command: str, payload: dict[str, object]) -> dict[str, object]:
        request = ActivityRequest.model_validate(payload)
        attempt = activity.info().attempt
        plain = decrypt_plain_input(request.start, self._key)
        scenario = request.start.fault_scenario
        fault_key = (request.start.run_id, scenario)
        if (
            command == "step"
            and attempt == 1
            and fault_key not in self._injected_faults
            and scenario
            in {
                "activity_pre_dispatch_once",
                "transient_timeout_once",
            }
        ):
            self._injected_faults.add(fault_key)
            fault_type = (
                "activity_pre_dispatch"
                if scenario == "activity_pre_dispatch_once"
                else "transient_timeout"
            )
            raise ApplicationError(
                "trusted transient fault",
                type=fault_type,
                non_retryable=False,
            )
        if (
            command == "step"
            and attempt == 1
            and fault_key not in self._injected_faults
            and scenario in {"browser_worker_restart_once", "recovery_worker_restart_once"}
        ):
            self._injected_faults.add(fault_key)
            await asyncio.sleep(5)
        result = await self._client.invoke(command, request, plain)
        if (
            command == "step"
            and attempt == 1
            and fault_key not in self._injected_faults
            and scenario == "post_commit_pre_checkpoint_once"
            and result.outcome == "verified"
            and result.receipt is not None
        ):
            self._injected_faults.add(fault_key)
            raise ApplicationError(
                "trusted post-commit pre-checkpoint fault",
                type="post_commit_pre_checkpoint",
                non_retryable=False,
            )
        return result.model_copy(update={"activity_attempt": attempt}).model_dump(mode="json")

    @activity.defn(name="w8_start_run")
    async def start_run(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._invoke("start", payload)

    @activity.defn(name="w8_execute_step")
    async def execute_step(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._invoke("step", payload)

    @activity.defn(name="w8_refresh")
    async def refresh(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._invoke("refresh", payload)

    @activity.defn(name="w8_recover")
    async def recover(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._invoke("recover", payload)

    @activity.defn(name="w8_replan")
    async def replan(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._invoke("replan", payload)

    @activity.defn(name="w8_cleanup")
    async def cleanup(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._invoke("cleanup", payload)
