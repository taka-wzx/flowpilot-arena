import pytest
from pydantic import ValidationError

from flowpilot_browser_worker.recovery import fixed_headers, mutation_matches, parse_receipt
from flowpilot_browser_worker.schemas import (
    RecoveryDomActionEnvelope,
    RecoveryIdempotencyBinding,
)


def _binding() -> RecoveryIdempotencyBinding:
    return RecoveryIdempotencyBinding(
        task_id="w7-jml-joiner-001-v1",
        idempotency_key="op_" + "1" * 64,
        request_hash="2" * 64,
        plan_revision=1,
        step_id="s10_ticket",
        operation="create_ticket",
    )


def test_only_fixed_mutation_paths_receive_fixed_headers() -> None:
    binding = _binding()
    assert mutation_matches("create_ticket", "POST", "http://sandbox-web/api/itsm/tickets")
    assert not mutation_matches("create_ticket", "GET", "http://sandbox-web/api/itsm/tickets")
    assert not mutation_matches("create_ticket", "POST", "http://sandbox-web/api/iam/accounts")
    assert set(fixed_headers(binding)) == {
        "X-FlowPilot-W8-Task-Id",
        "X-FlowPilot-W8-Idempotency-Key",
        "X-FlowPilot-W8-Request-Hash",
        "X-FlowPilot-W8-Plan-Revision",
        "X-FlowPilot-W8-Step-Id",
        "X-FlowPilot-W8-Operation",
    }


def test_receipt_parser_and_envelope_fail_closed() -> None:
    created = parse_receipt(
        201,
        {
            "x-flowpilot-w8-receipt-state": "created",
            "x-flowpilot-w8-result-hash": "a" * 64,
        },
    )
    assert created.state == "created"
    assert parse_receipt(409, {}).state == "mismatch"
    with pytest.raises(ValueError):
        parse_receipt(200, {})
    with pytest.raises(ValidationError):
        RecoveryDomActionEnvelope.model_validate(
            {
                "session_id": "bw_abcdefghijklmnop",
                "session_epoch": 1,
                "generation": 1,
                "action": {"action_id": "act_w8_wait", "type": "wait", "duration_ms": 1},
                "idempotency": _binding().model_dump(mode="json"),
            }
        )
