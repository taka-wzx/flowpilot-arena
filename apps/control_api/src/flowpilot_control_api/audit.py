"""Organization-qualified append-only W11 tamper-evident audit chain."""

import json
import re
import secrets
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from flowpilot_control_api.models import AuditChainHead, AuditEvent
from flowpilot_control_api.schemas import (
    AuditEventRead,
    AuditEventType,
    AuditVerificationResult,
    canonical_json_bytes,
    stable_hash,
)

GENESIS_HASH = "0" * 64
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_PROHIBITED_KEYS = frozenset(
    {
        "token",
        "credential",
        "nonce",
        "claims",
        "authorization_code",
        "cookie",
        "password",
        "private_key",
        "name",
        "email",
        "username",
        "page",
        "dom",
        "image",
        "form",
        "parameters",
        "machine_path",
    }
)
_ALLOWED_KEYS = frozenset(
    {
        "schema_version",
        "action_type",
        "risk_level",
        "parameter_hash",
        "request_id",
        "decision_id",
        "authority_id",
        "approval_role",
        "request_status",
        "grant_id",
        "grant_status",
        "execution_id",
        "reason",
        "http_status",
        "count",
        "version",
        "receipt_reference",
        "authorization_hash",
        "valid",
    }
)


class AuditPayloadRejected(RuntimeError):
    pass


class AuditChainMissing(RuntimeError):
    pass


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _closed_payload(payload: dict[str, object]) -> dict[str, object]:
    if not set(payload) <= _ALLOWED_KEYS or set(payload) & _PROHIBITED_KEYS:
        raise AuditPayloadRejected("audit payload keys are outside the frozen schema")
    normalized: dict[str, object] = {}
    for key, value in payload.items():
        if (
            value is None
            or isinstance(value, (bool, int))
            or (isinstance(value, str) and len(value) <= 120)
        ):
            normalized[key] = value
        else:
            raise AuditPayloadRejected("audit payload value is outside the frozen schema")
    if len(canonical_json_bytes(normalized)) > 2_048:
        raise AuditPayloadRejected("audit payload exceeds the frozen byte bound")
    return normalized


def _event_fields(
    *,
    event_id: str,
    organization_id: str,
    sequence: int,
    event_type: str,
    actor_reference: str,
    subject_reference: str,
    payload: dict[str, object],
    previous_hash: str,
    created_at: datetime,
) -> dict[str, object]:
    return {
        "schema_version": "w11-audit-event/1.0",
        "event_id": event_id,
        "organization_id": organization_id,
        "sequence": sequence,
        "event_type": event_type,
        "actor_reference": actor_reference,
        "subject_reference": subject_reference,
        "payload": payload,
        "previous_hash": previous_hash,
        "created_at": _utc(created_at),
    }


def append_audit_event(
    session: Session,
    *,
    organization_id: str,
    event_type: AuditEventType,
    actor_reference: str,
    subject_reference: str,
    payload: dict[str, object],
    now: datetime,
) -> AuditEvent:
    if not _HEX64.fullmatch(actor_reference):
        raise AuditPayloadRejected("actor reference must be a stable hash")
    if not 1 <= len(subject_reference) <= 68:
        raise AuditPayloadRejected("audit subject reference is outside the bound")
    closed_payload = _closed_payload(payload)
    head = session.scalar(
        select(AuditChainHead)
        .where(AuditChainHead.organization_id == organization_id)
        .with_for_update()
    )
    if head is None:
        raise AuditChainMissing("organization audit head is unavailable")
    sequence = head.head_sequence + 1
    event_id = f"aud_{secrets.token_hex(16)}"
    created_at = _utc(now)
    fields = _event_fields(
        event_id=event_id,
        organization_id=organization_id,
        sequence=sequence,
        event_type=event_type.value,
        actor_reference=actor_reference,
        subject_reference=subject_reference,
        payload=closed_payload,
        previous_hash=head.head_hash,
        created_at=created_at,
    )
    payload_json = canonical_json_bytes(closed_payload).decode("utf-8")
    event_hash = stable_hash(fields)
    event = AuditEvent(
        organization_id=organization_id,
        sequence=sequence,
        event_id=event_id,
        event_type=event_type.value,
        actor_reference=actor_reference,
        subject_reference=subject_reference,
        payload_json=payload_json,
        payload_hash=stable_hash(closed_payload),
        previous_hash=head.head_hash,
        event_hash=event_hash,
        created_at=created_at,
    )
    session.add(event)
    head.head_sequence = sequence
    head.head_hash = event_hash
    head.version += 1
    head.updated_at = created_at
    session.flush()
    return event


def event_read(event: AuditEvent) -> AuditEventRead:
    return AuditEventRead(
        event_id=event.event_id,
        organization_id=event.organization_id,
        sequence=event.sequence,
        event_type=AuditEventType(event.event_type),
        previous_hash=event.previous_hash,
        event_hash=event.event_hash,
        payload_hash=event.payload_hash,
        created_at=event.created_at,
    )


def list_audit_events(
    session: Session, organization_id: str, *, limit: int = 200
) -> tuple[list[AuditEvent], AuditChainHead]:
    head = session.scalar(
        select(AuditChainHead).where(AuditChainHead.organization_id == organization_id)
    )
    if head is None:
        raise AuditChainMissing("organization audit head is unavailable")
    events = list(
        session.scalars(
            select(AuditEvent)
            .where(AuditEvent.organization_id == organization_id)
            .order_by(AuditEvent.sequence)
            .limit(limit)
        )
    )
    return events, head


def verify_audit_chain(session: Session, organization_id: str) -> AuditVerificationResult:
    head = session.scalar(
        select(AuditChainHead).where(AuditChainHead.organization_id == organization_id)
    )
    if head is None:
        raise AuditChainMissing("organization audit head is unavailable")
    events = list(
        session.scalars(
            select(AuditEvent)
            .where(AuditEvent.organization_id == organization_id)
            .order_by(AuditEvent.sequence)
        )
    )
    previous_hash = GENESIS_HASH
    for expected_sequence, event in enumerate(events, start=1):
        if event.sequence != expected_sequence:
            return _verification(False, events, head, "sequence_mismatch")
        if event.previous_hash != previous_hash:
            return _verification(False, events, head, "previous_hash_mismatch")
        try:
            payload: Any = json.loads(event.payload_json)
            if not isinstance(payload, dict):
                raise ValueError
            closed_payload = _closed_payload(payload)
        except (json.JSONDecodeError, ValueError, AuditPayloadRejected):
            return _verification(False, events, head, "event_hash_mismatch")
        if canonical_json_bytes(closed_payload).decode("utf-8") != event.payload_json:
            return _verification(False, events, head, "event_hash_mismatch")
        if stable_hash(closed_payload) != event.payload_hash:
            return _verification(False, events, head, "event_hash_mismatch")
        fields = _event_fields(
            event_id=event.event_id,
            organization_id=event.organization_id,
            sequence=event.sequence,
            event_type=event.event_type,
            actor_reference=event.actor_reference,
            subject_reference=event.subject_reference,
            payload=closed_payload,
            previous_hash=event.previous_hash,
            created_at=event.created_at,
        )
        if stable_hash(fields) != event.event_hash:
            return _verification(False, events, head, "event_hash_mismatch")
        previous_hash = event.event_hash
    if head.head_sequence != len(events) or head.head_hash != previous_hash:
        return _verification(False, events, head, "head_mismatch")
    return _verification(True, events, head, "valid")


def _verification(
    valid: bool,
    events: list[AuditEvent],
    head: AuditChainHead,
    reason: str,
) -> AuditVerificationResult:
    return AuditVerificationResult(
        valid=valid,
        event_count=len(events),
        head_sequence=head.head_sequence,
        head_hash=head.head_hash,
        reason=reason,  # type: ignore[arg-type]
    )
