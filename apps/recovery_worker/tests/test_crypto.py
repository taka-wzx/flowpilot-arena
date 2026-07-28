import pytest
from cryptography.exceptions import InvalidTag

from flowpilot_recovery_worker.crypto import decrypt_plain_input


def test_opaque_envelope_round_trip_contains_no_plaintext(
    workflow_start, plain_input, envelope_key: bytes
) -> None:
    serialized = workflow_start.model_dump_json()
    assert plain_input.human_brief not in serialized
    assert ".invalid" not in serialized
    assert "SYN-W8-SECRET" not in serialized
    assert decrypt_plain_input(workflow_start, envelope_key) == plain_input


def test_tampered_ciphertext_and_identity_fail_closed(workflow_start, envelope_key: bytes) -> None:
    tampered = workflow_start.model_copy(
        update={
            "envelope": workflow_start.envelope.model_copy(
                update={"ciphertext": "A" + workflow_start.envelope.ciphertext[1:]}
            )
        }
    )
    with pytest.raises((InvalidTag, ValueError)):
        decrypt_plain_input(tampered, envelope_key)
    wrong_identity = workflow_start.model_copy(update={"run_id": "run_w8_changed"})
    with pytest.raises(ValueError):
        decrypt_plain_input(wrong_identity, envelope_key)
