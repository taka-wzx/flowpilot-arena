import hashlib
import json
from typing import cast

from flowpilot_planning_agent.recovery_schemas import PlanningRecoveryActivity
from flowpilot_planning_agent.schemas import (
    JoinerSuppliedValues,
    LeaverSuppliedValues,
    MoverSuppliedValues,
    Operation,
    SuppliedValues,
)
from flowpilot_planning_agent.worker_schemas import (
    RecoveryIdempotencyBinding,
    RecoveryOperation,
)


def _canonical(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def mutation_payload(operation: Operation, values: SuppliedValues) -> dict[str, object]:
    employee_id = values.employee_id
    if operation == "create_ticket" and isinstance(values, JoinerSuppliedValues):
        return {"employee_id": employee_id, "title": values.ticket_title, "status": "open"}
    if operation == "create_account" and isinstance(values, JoinerSuppliedValues):
        return {
            "employee_id": employee_id,
            "username": values.username,
            "role": "employee",
            "status": "active",
        }
    if operation == "assign_asset" and isinstance(values, JoinerSuppliedValues):
        return {
            "employee_id": employee_id,
            "asset_tag": values.asset_tag,
            "device_type": "laptop",
            "model": values.laptop_model,
            "status": "assigned",
        }
    if operation == "create_mailbox" and isinstance(values, JoinerSuppliedValues):
        return {"employee_id": employee_id, "address": values.mailbox, "status": "active"}
    if operation == "transfer_employee" and isinstance(values, MoverSuppliedValues):
        return {
            "employee_id": employee_id,
            "department": values.new_department,
            "job_title": values.new_job_title,
            "location": values.new_location,
        }
    if operation in {
        "disable_employee",
        "close_ticket",
        "revoke_account",
        "release_asset",
        "disable_mailbox",
    } and isinstance(values, (MoverSuppliedValues, LeaverSuppliedValues)):
        return {"employee_id": employee_id}
    raise ValueError("operation has no W8 idempotent mutation payload")


def build_binding(
    request: PlanningRecoveryActivity, operation: Operation
) -> RecoveryIdempotencyBinding:
    if request.step_id is None:
        raise ValueError("idempotency binding requires a step")
    key_material = _canonical(
        {
            "schema_version": "w8-idempotency-key/1.0",
            "run_id": request.run_id,
            "plan_revision": request.revision,
            "step_id": request.step_id,
            "operation_index": 0,
        }
    )
    idempotency_key = f"op_{hashlib.sha256(key_material).hexdigest()}"
    metadata: dict[str, object] = {
        "task_id": request.task_id,
        "idempotency_key": idempotency_key,
        "plan_revision": request.revision,
        "step_id": request.step_id,
        "operation": operation,
        "schema_version": "w8-idempotent-mutation/1.0",
        "payload": mutation_payload(operation, request.supplied_values),
    }
    request_hash = hashlib.sha256(_canonical(metadata)).hexdigest()
    return RecoveryIdempotencyBinding(
        task_id=request.task_id,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        plan_revision=request.revision,
        step_id=request.step_id,
        operation=cast(RecoveryOperation, operation),
    )
