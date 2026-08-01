"""Build the released W8 opaque Temporal start envelope from a closed task reference."""

import base64
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from flowpilot_workflow_worker.schemas import (
    OpaqueEnvelope,
    WorkflowStart,
    WorkItem,
    canonical_json_bytes,
    stable_hash,
)

_TASKS: dict[str, tuple[str, str, dict[str, object]]] = {
    "w7-jml-joiner-001-v1": (
        "joiner",
        "standard_joiner",
        {
            "process": "joiner",
            "employee_id": 41011,
            "ticket_title": "W7 Joiner 001 Variant 1",
            "username": "w7.joiner001v1",
            "asset_tag": "SYN-W7-JOINER-001-V1",
            "laptop_model": "Synthetic Laptop 3",
            "mailbox": "w7.joiner001v1@flowpilot.invalid",
        },
    ),
    "w7-jml-joiner-001-v2": (
        "joiner",
        "standard_joiner",
        {
            "process": "joiner",
            "employee_id": 41012,
            "ticket_title": "W7 Joiner 001 Variant 2",
            "username": "w7.joiner001v2",
            "asset_tag": "SYN-W7-JOINER-001-V2",
            "laptop_model": "Synthetic Laptop 4",
            "mailbox": "w7.joiner001v2@flowpilot.invalid",
        },
    ),
    "w7-jml-joiner-002-v1": (
        "joiner",
        "standard_joiner",
        {
            "process": "joiner",
            "employee_id": 41021,
            "ticket_title": "W7 Joiner 002 Variant 1",
            "username": "w7.joiner002v1",
            "asset_tag": "SYN-W7-JOINER-002-V1",
            "laptop_model": "Synthetic Laptop 4",
            "mailbox": "w7.joiner002v1@flowpilot.invalid",
        },
    ),
    "w7-jml-joiner-002-v2": (
        "joiner",
        "standard_joiner",
        {
            "process": "joiner",
            "employee_id": 41022,
            "ticket_title": "W7 Joiner 002 Variant 2",
            "username": "w7.joiner002v2",
            "asset_tag": "SYN-W7-JOINER-002-V2",
            "laptop_model": "Synthetic Laptop 1",
            "mailbox": "w7.joiner002v2@flowpilot.invalid",
        },
    ),
    "w7-jml-mover-001-v1": (
        "mover",
        "standard_mover",
        {
            "process": "mover",
            "employee_id": 41131,
            "new_department": "Synthetic Transfer Department 2",
            "new_job_title": "Synthetic Transfer Lead 2",
            "new_location": "Synthetic Transfer Location 1",
        },
    ),
    "w7-jml-mover-001-v2": (
        "mover",
        "standard_mover",
        {
            "process": "mover",
            "employee_id": 41132,
            "new_department": "Synthetic Transfer Department 2",
            "new_job_title": "Synthetic Transfer Lead 2",
            "new_location": "Synthetic Transfer Location 2",
        },
    ),
    "w7-jml-leaver-001-v1": (
        "leaver",
        "standard_leaver",
        {"process": "leaver", "employee_id": 41211},
    ),
    "w7-jml-leaver-001-v2": (
        "leaver",
        "standard_leaver",
        {"process": "leaver", "employee_id": 41212},
    ),
}

_EFFECT_BINDINGS: dict[str, tuple[str, dict[str, object]]] = {
    "w7-jml-joiner-001-v1": (
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41011,
            "ticket_code": "w7.joiner001v1",
        },
    ),
    "w7-jml-joiner-001-v2": (
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41012,
            "ticket_code": "w7.joiner001v2",
        },
    ),
    "w7-jml-joiner-002-v1": (
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41021,
            "ticket_code": "w7.joiner002v1",
        },
    ),
    "w7-jml-joiner-002-v2": (
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41022,
            "ticket_code": "w7.joiner002v2",
        },
    ),
    "w7-jml-mover-001-v1": (
        "transfer_employee",
        {
            "schema_version": "w11-transfer-employee-parameters/1.0",
            "employee_id": 41131,
            "destination_code": "w7.mover001v1",
        },
    ),
    "w7-jml-mover-001-v2": (
        "transfer_employee",
        {
            "schema_version": "w11-transfer-employee-parameters/1.0",
            "employee_id": 41132,
            "destination_code": "w7.mover001v2",
        },
    ),
    "w7-jml-leaver-001-v1": (
        "disable_employee",
        {
            "schema_version": "w11-employee-mutation-parameters/1.0",
            "employee_id": 41211,
        },
    ),
    "w7-jml-leaver-001-v2": (
        "disable_employee",
        {
            "schema_version": "w11-employee-mutation-parameters/1.0",
            "employee_id": 41212,
        },
    ),
}


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def build_workflow_start(item: WorkItem, key: bytes) -> WorkflowStart:
    if len(key) != 32:
        raise ValueError("W8 envelope key must be 32 bytes")
    process, category, supplied_values = _TASKS[item.task_id]
    if process != item.process or category != item.category:
        raise ValueError("trusted task reference binding changed")
    action_type, parameters = _EFFECT_BINDINGS[item.task_id]
    action_binding: dict[str, object] = {
        "schema_version": "w11-action-binding/1.0",
        "action_type": action_type,
        "parameters": parameters,
    }
    if item.action_type != action_type or item.parameter_hash != stable_hash(action_binding):
        raise ValueError("production action does not authorize trusted task effect")
    trusted_projection: dict[str, object] = {
        "schema_version": "w12-trusted-task-reference/1.0",
        "task_id": item.task_id,
        "process": process,
        "category": category,
    }
    if stable_hash(trusted_projection) != item.payload_hash:
        raise ValueError("trusted task reference hash changed")
    plain: dict[str, object] = {
        "schema_version": "w8-plain-run-input/1.0",
        "workflow_id": item.workflow_id,
        "run_id": item.run_id,
        "task_id": item.task_id,
        "process": process,
        "category": category,
        "human_brief": "Synthetic bounded production task",
        "supplied_values": supplied_values,
    }
    aad = canonical_json_bytes(
        {
            "schema_version": "w8-opaque-envelope/1.0",
            "key_id": "w8-local-runtime-key/1",
            "workflow_id": item.workflow_id,
            "run_id": item.run_id,
            "task_id": item.task_id,
        }
    )
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, canonical_json_bytes(plain), aad)
    return WorkflowStart(
        workflow_id=item.workflow_id,
        run_id=item.run_id,
        task_id=item.task_id,
        envelope=OpaqueEnvelope(
            nonce=_b64(nonce),
            ciphertext=_b64(ciphertext),
            associated_data_hash=stable_hash(aad.decode("utf-8")),
        ),
    )
