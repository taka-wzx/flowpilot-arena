from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.idempotency import canonical_request_hash
from flowpilot_sandbox_api.models import OnboardingTicket, W8OperationReceipt
from flowpilot_sandbox_api.schemas import W8IdempotencyMetadata


def _metadata(task_id: str, payload: dict[str, object]) -> W8IdempotencyMetadata:
    pending = W8IdempotencyMetadata(
        task_id=task_id,
        idempotency_key="op_" + "1" * 64,
        request_hash="0" * 64,
        plan_revision=1,
        step_id="s10_ticket",
        operation="create_ticket",
    )
    return pending.model_copy(update={"request_hash": canonical_request_hash(pending, payload)})


def _headers(metadata: W8IdempotencyMetadata) -> dict[str, str]:
    return {
        "X-FlowPilot-W8-Task-Id": metadata.task_id,
        "X-FlowPilot-W8-Idempotency-Key": metadata.idempotency_key,
        "X-FlowPilot-W8-Request-Hash": metadata.request_hash,
        "X-FlowPilot-W8-Plan-Revision": str(metadata.plan_revision),
        "X-FlowPilot-W8-Step-Id": metadata.step_id,
        "X-FlowPilot-W8-Operation": metadata.operation,
    }


def test_same_key_and_hash_replays_without_duplicate_side_effect(
    client, db_session: Session
) -> None:
    task_id = "w7-jml-joiner-001-v1"
    detail = client.get(f"/api/arena/w7/tasks/{task_id}").json()
    client.post(f"/api/arena/w7/tasks/{task_id}/reset-seed", json={})
    payload = {
        "employee_id": detail["supplied_values"]["employee_id"],
        "title": detail["supplied_values"]["ticket_title"],
        "status": "open",
    }
    metadata = _metadata(task_id, payload)

    created = client.post("/api/itsm/tickets", json=payload, headers=_headers(metadata))
    replayed = client.post("/api/itsm/tickets", json=payload, headers=_headers(metadata))

    assert created.status_code == 201
    assert created.headers["X-FlowPilot-W8-Receipt-State"] == "created"
    assert replayed.status_code == 201
    assert replayed.headers["X-FlowPilot-W8-Receipt-State"] == "replayed"
    assert (
        created.headers["X-FlowPilot-W8-Result-Hash"]
        == replayed.headers["X-FlowPilot-W8-Result-Hash"]
    )
    assert db_session.scalar(select(func.count()).select_from(OnboardingTicket)) == 1
    assert db_session.scalar(select(func.count()).select_from(W8OperationReceipt)) == 1


def test_changed_hash_is_rejected_and_reset_removes_only_owned_receipt(
    client, db_session: Session
) -> None:
    task_id = "w7-jml-joiner-001-v1"
    other_task_id = "w7-jml-joiner-002-v1"
    detail = client.get(f"/api/arena/w7/tasks/{task_id}").json()
    client.post(f"/api/arena/w7/tasks/{task_id}/reset-seed", json={})
    payload = {
        "employee_id": detail["supplied_values"]["employee_id"],
        "title": detail["supplied_values"]["ticket_title"],
        "status": "open",
    }
    metadata = _metadata(task_id, payload)
    created = client.post("/api/itsm/tickets", json=payload, headers=_headers(metadata))
    assert created.status_code == 201

    changed = metadata.model_copy(update={"request_hash": "f" * 64})
    mismatch = client.post("/api/itsm/tickets", json=payload, headers=_headers(changed))
    assert mismatch.status_code == 409
    assert mismatch.json()["detail"] == "idempotency_mismatch"
    assert db_session.scalar(select(func.count()).select_from(OnboardingTicket)) == 1

    db_session.add(
        W8OperationReceipt(
            task_id=other_task_id,
            idempotency_key="op_" + "2" * 64,
            request_hash="2" * 64,
            plan_revision=1,
            step_id="s10_ticket",
            operation="create_ticket",
            outcome_code="committed",
            result_hash="3" * 64,
        )
    )
    db_session.commit()
    client.post(f"/api/arena/w7/tasks/{task_id}/reset-seed", json={})
    assert db_session.get(W8OperationReceipt, (task_id, metadata.idempotency_key)) is None
    assert db_session.get(W8OperationReceipt, (other_task_id, "op_" + "2" * 64)) is not None
