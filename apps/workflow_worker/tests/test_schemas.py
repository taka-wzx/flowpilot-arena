"""Strict work-item, trusted payload, and envelope tests."""

import base64
import json
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import ValidationError

from flowpilot_workflow_worker.crypto import build_workflow_start
from flowpilot_workflow_worker.schemas import WorkItem, canonical_json_bytes, stable_hash

EFFECT_BINDINGS = (
    (
        "w7-jml-joiner-001-v1",
        "joiner",
        "standard_joiner",
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41011,
            "ticket_code": "w7.joiner001v1",
        },
        "9f9a16bad25c578969e92f60e982510c9be6a4fe74d9236d06e8f9d96f9ea43b",
    ),
    (
        "w7-jml-joiner-001-v2",
        "joiner",
        "standard_joiner",
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41012,
            "ticket_code": "w7.joiner001v2",
        },
        "8f7967a3f5fa16a535c758ef421a6bed1b24e3f5d307cd80d28c2d7133b1f64c",
    ),
    (
        "w7-jml-joiner-002-v1",
        "joiner",
        "standard_joiner",
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41021,
            "ticket_code": "w7.joiner002v1",
        },
        "24a48d8f36f74aecec1dfc18a709e8682a1bc5b4985206ea419c27bd0fb1bd32",
    ),
    (
        "w7-jml-joiner-002-v2",
        "joiner",
        "standard_joiner",
        "create_ticket",
        {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41022,
            "ticket_code": "w7.joiner002v2",
        },
        "5445094ff191a1beb668e68fb5501c91287e32bc447128cbbc3ae844d9849282",
    ),
    (
        "w7-jml-mover-001-v1",
        "mover",
        "standard_mover",
        "transfer_employee",
        {
            "schema_version": "w11-transfer-employee-parameters/1.0",
            "employee_id": 41131,
            "destination_code": "w7.mover001v1",
        },
        "417392e96f16078f9d9ac6bbb00cf0169945a149f322c787b99aa90e5377712f",
    ),
    (
        "w7-jml-mover-001-v2",
        "mover",
        "standard_mover",
        "transfer_employee",
        {
            "schema_version": "w11-transfer-employee-parameters/1.0",
            "employee_id": 41132,
            "destination_code": "w7.mover001v2",
        },
        "330c7a46e46648958a40f6e379acf266959eb93ec70b33a44d912145e9103d02",
    ),
    (
        "w7-jml-leaver-001-v1",
        "leaver",
        "standard_leaver",
        "disable_employee",
        {
            "schema_version": "w11-employee-mutation-parameters/1.0",
            "employee_id": 41211,
        },
        "ec514adaaaf6c5d9e3b9ac1143fa3526b93dfca511ff571dd947bdfa605fa756",
    ),
    (
        "w7-jml-leaver-001-v2",
        "leaver",
        "standard_leaver",
        "disable_employee",
        {
            "schema_version": "w11-employee-mutation-parameters/1.0",
            "employee_id": 41212,
        },
        "bb444aecec640db18cd003b4ff585b5d14a76c0f84470842f7799011a46eb5fc",
    ),
)


def _item() -> WorkItem:
    payload = {
        "schema_version": "w12-trusted-task-reference/1.0",
        "task_id": "w7-jml-joiner-001-v1",
        "process": "joiner",
        "category": "standard_joiner",
    }
    action = {
        "schema_version": "w11-action-binding/1.0",
        "action_type": "create_ticket",
        "parameters": {
            "schema_version": "w11-create-ticket-parameters/1.0",
            "employee_id": 41011,
            "ticket_code": "w7.joiner001v1",
        },
    }
    now = datetime(2026, 8, 1, tzinfo=UTC)
    return WorkItem(
        organization_id="org_schema_0001",
        outbox_id="out_schema_0001",
        run_id="run_schema_0001",
        executor_user_id="usr_schema_0001",
        task_id="w7-jml-joiner-001-v1",
        process="joiner",
        category="standard_joiner",
        action_type="create_ticket",
        parameter_hash=stable_hash(action),
        authorization_hash="a" * 64,
        payload_reference="taskref_schema_0001",
        payload_hash=stable_hash(payload),
        workflow_id="workflow_schema_0001",
        workflow_hash="b" * 64,
        worker_owner_hash="c" * 64,
        fencing_token=1,
        lease_version=1,
        attempt_count=1,
        leased_at=now,
        lease_expires_at=now + timedelta(seconds=30),
    )


def test_work_item_is_strict_bounded_and_extra_forbid() -> None:
    item = _item()
    assert item.schema_version == "w12-work-item/1.0"
    with pytest.raises(ValidationError):
        WorkItem.model_validate({**item.model_dump(), "token": "forbidden"})
    with pytest.raises(ValidationError):
        WorkItem.model_validate({**item.model_dump(), "fencing_token": 0})


def test_envelope_uses_released_first_w7_joiner_values() -> None:
    item = _item()
    key = b"e" * 32
    start = build_workflow_start(item, key)
    aad = canonical_json_bytes(
        {
            "schema_version": "w8-opaque-envelope/1.0",
            "key_id": "w8-local-runtime-key/1",
            "workflow_id": item.workflow_id,
            "run_id": item.run_id,
            "task_id": item.task_id,
        }
    )
    plaintext = AESGCM(key).decrypt(
        base64.b64decode(start.envelope.nonce),
        base64.b64decode(start.envelope.ciphertext),
        aad,
    )
    decoded = json.loads(plaintext)
    assert decoded["supplied_values"] == {
        "asset_tag": "SYN-W7-JOINER-001-V1",
        "employee_id": 41011,
        "laptop_model": "Synthetic Laptop 3",
        "mailbox": "w7.joiner001v1@flowpilot.invalid",
        "process": "joiner",
        "ticket_title": "W7 Joiner 001 Variant 1",
        "username": "w7.joiner001v1",
    }
    assert start.envelope.associated_data_hash == stable_hash(aad.decode("utf-8"))


@pytest.mark.parametrize(
    ("task_id", "process", "category", "action_type", "parameters", "expected_hash"),
    EFFECT_BINDINGS,
)
def test_all_frozen_effect_bindings_match_the_contract(
    task_id: str,
    process: str,
    category: str,
    action_type: str,
    parameters: dict[str, object],
    expected_hash: str,
) -> None:
    action_binding: dict[str, object] = {
        "schema_version": "w11-action-binding/1.0",
        "action_type": action_type,
        "parameters": parameters,
    }
    payload = {
        "schema_version": "w12-trusted-task-reference/1.0",
        "task_id": task_id,
        "process": process,
        "category": category,
    }
    item = _item().model_copy(
        update={
            "task_id": task_id,
            "process": process,
            "category": category,
            "action_type": action_type,
            "parameter_hash": stable_hash(action_binding),
            "payload_hash": stable_hash(payload),
        }
    )

    assert item.parameter_hash == expected_hash
    assert build_workflow_start(item, b"e" * 32).task_id == task_id


def test_unapproved_action_cannot_authorize_task_effect() -> None:
    item = _item().model_copy(
        update={
            "action_type": "generate_plan",
            "parameter_hash": stable_hash(
                {
                    "schema_version": "w11-action-binding/1.0",
                    "action_type": "generate_plan",
                    "parameters": {
                        "schema_version": "w11-task-parameters/1.0",
                        "task_reference": "w7-jml-joiner-001-v1",
                    },
                }
            ),
        }
    )
    with pytest.raises(ValueError, match="does not authorize"):
        build_workflow_start(item, b"e" * 32)
