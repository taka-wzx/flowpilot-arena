import pytest

from flowpilot_recovery_worker.crypto import encrypt_plain_input
from flowpilot_recovery_worker.schemas import PlainRunInput, WorkflowStart


@pytest.fixture
def envelope_key() -> bytes:
    return b"k" * 32


@pytest.fixture
def plain_input() -> PlainRunInput:
    return PlainRunInput(
        workflow_id="workflow_w8_tests",
        run_id="run_w8_tests",
        task_id="w7-jml-joiner-001-v1",
        process="joiner",
        category="standard_joiner",
        human_brief="Synthetic secret recovery brief",
        supplied_values={
            "process": "joiner",
            "employee_id": 101,
            "ticket_title": "Synthetic secret ticket",
            "username": "secret.user",
            "asset_tag": "SYN-W8-SECRET",
            "laptop_model": "Synthetic laptop",
            "mailbox": "secret.user@example.invalid",
        },
    )


@pytest.fixture
def workflow_start(plain_input: PlainRunInput, envelope_key: bytes) -> WorkflowStart:
    return WorkflowStart(
        workflow_id=plain_input.workflow_id,
        run_id=plain_input.run_id,
        task_id=plain_input.task_id,
        envelope=encrypt_plain_input(plain_input, envelope_key, nonce=b"n" * 12),
    )
