import hashlib
import json
from collections.abc import Callable

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.models import W8OperationReceipt
from flowpilot_sandbox_api.schemas import W8IdempotencyMetadata, W8ReceiptResult

MAX_RECEIPTS_PER_TASK = 24


class IdempotencyMismatch(RuntimeError):
    pass


class ReceiptLimitExceeded(RuntimeError):
    pass


def _canonical_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def canonical_request_hash(
    metadata: W8IdempotencyMetadata,
    payload: dict[str, object],
) -> str:
    projection = metadata.model_dump(mode="json", exclude={"request_hash"})
    projection["schema_version"] = "w8-idempotent-mutation/1.0"
    projection["payload"] = payload
    return hashlib.sha256(_canonical_bytes(projection)).hexdigest()


def safe_result_hash(metadata: W8IdempotencyMetadata) -> str:
    return hashlib.sha256(
        _canonical_bytes(
            {
                "schema_version": "w8-safe-operation-result/1.0",
                "task_id": metadata.task_id,
                "plan_revision": metadata.plan_revision,
                "step_id": metadata.step_id,
                "operation": metadata.operation,
                "outcome_code": "committed",
            }
        )
    ).hexdigest()


def _existing(session: Session, metadata: W8IdempotencyMetadata) -> W8OperationReceipt | None:
    return session.get(W8OperationReceipt, (metadata.task_id, metadata.idempotency_key))


def execute_idempotent[RecordT](
    session: Session,
    metadata: W8IdempotencyMetadata,
    payload: dict[str, object],
    perform: Callable[[], RecordT],
    replay: Callable[[], RecordT],
) -> tuple[RecordT, W8ReceiptResult]:
    expected_hash = canonical_request_hash(metadata, payload)
    if expected_hash != metadata.request_hash:
        raise IdempotencyMismatch("request hash does not match validated mutation")
    existing = _existing(session, metadata)
    if existing is not None:
        if existing.request_hash != metadata.request_hash:
            raise IdempotencyMismatch("idempotency key was already bound to another request")
        return replay(), W8ReceiptResult(state="replayed", result_hash=existing.result_hash)

    count = session.scalar(
        select(func.count())
        .select_from(W8OperationReceipt)
        .where(W8OperationReceipt.task_id == metadata.task_id)
    )
    if count is None or count >= MAX_RECEIPTS_PER_TASK:
        raise ReceiptLimitExceeded("task receipt limit exhausted")

    result_hash = safe_result_hash(metadata)
    record = perform()
    session.add(
        W8OperationReceipt(
            task_id=metadata.task_id,
            idempotency_key=metadata.idempotency_key,
            request_hash=metadata.request_hash,
            plan_revision=metadata.plan_revision,
            step_id=metadata.step_id,
            operation=metadata.operation,
            outcome_code="committed",
            result_hash=result_hash,
        )
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raced = _existing(session, metadata)
        if raced is None or raced.request_hash != metadata.request_hash:
            raise
        return replay(), W8ReceiptResult(state="replayed", result_hash=raced.result_hash)
    session.refresh(record)
    return record, W8ReceiptResult(state="created", result_hash=result_hash)
