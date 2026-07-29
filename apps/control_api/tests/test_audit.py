"""W11 audit-chain determinism, isolation, and tamper detection."""

import hashlib
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from flowpilot_control_api.audit import (
    AuditPayloadRejected,
    append_audit_event,
    list_audit_events,
    verify_audit_chain,
)
from flowpilot_control_api.models import AuditChainHead, AuditEvent
from flowpilot_control_api.schemas import AuditEventType

ALPHA = "org_syn_alpha_0001"
BETA = "org_syn_beta_0001"
ACTOR_HASH = hashlib.sha256(b"synthetic-actor").hexdigest()
NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)


def _append(session: Session, organization_id: str, index: int) -> AuditEvent:
    return append_audit_event(
        session,
        organization_id=organization_id,
        event_type=AuditEventType.RISK_CLASSIFIED,
        actor_reference=ACTOR_HASH,
        subject_reference=f"action_{index}",
        payload={
            "schema_version": "w11-audit-payload/1.0",
            "action_type": "inspect_task",
            "risk_level": "L0",
            "parameter_hash": hashlib.sha256(f"parameters-{index}".encode()).hexdigest(),
            "count": index,
        },
        now=NOW,
    )


def test_genesis_sequence_previous_hash_and_deterministic_verification(
    database_engine: Engine,
) -> None:
    with Session(database_engine) as session:
        events = [_append(session, ALPHA, index) for index in range(1, 4)]
        session.commit()
        result = verify_audit_chain(session, ALPHA)
        listed, head = list_audit_events(session, ALPHA)

    assert result.valid and result.reason == "valid"
    assert result.event_count == 3 and head.head_sequence == 3
    assert events[0].previous_hash == "0" * 64
    assert events[1].previous_hash == events[0].event_hash
    assert events[2].previous_hash == events[1].event_hash
    assert [item.sequence for item in listed] == [1, 2, 3]
    assert head.head_hash == events[-1].event_hash


@pytest.mark.parametrize(
    ("tamper", "reason"),
    [
        ("mutation", "event_hash_mismatch"),
        ("deletion", "sequence_mismatch"),
        ("insertion", "previous_hash_mismatch"),
        ("reorder", "previous_hash_mismatch"),
        ("previous", "previous_hash_mismatch"),
        ("truncate", "head_mismatch"),
    ],
)
def test_tamper_matrix_is_detected(database_engine: Engine, tamper: str, reason: str) -> None:
    with Session(database_engine) as session:
        _append(session, ALPHA, 1)
        _append(session, ALPHA, 2)
        _append(session, ALPHA, 3)
        session.commit()
        if tamper == "mutation":
            session.execute(
                update(AuditEvent)
                .where(AuditEvent.organization_id == ALPHA, AuditEvent.sequence == 2)
                .values(payload_json='{"schema_version":"w11-audit-payload/1.0"}')
            )
        elif tamper == "deletion":
            session.execute(
                delete(AuditEvent).where(
                    AuditEvent.organization_id == ALPHA, AuditEvent.sequence == 2
                )
            )
        elif tamper == "insertion":
            third = session.scalar(
                select(AuditEvent).where(
                    AuditEvent.organization_id == ALPHA, AuditEvent.sequence == 3
                )
            )
            assert third is not None
            third.sequence = 4
            session.flush()
            session.add(
                AuditEvent(
                    organization_id=ALPHA,
                    sequence=3,
                    event_id="aud_tampered_insert_0001",
                    event_type="risk_classified",
                    actor_reference=ACTOR_HASH,
                    subject_reference="inserted",
                    payload_json='{"schema_version":"w11-audit-payload/1.0"}',
                    payload_hash="f" * 64,
                    previous_hash="f" * 64,
                    event_hash="f" * 64,
                    created_at=NOW,
                )
            )
        elif tamper == "reorder":
            first = session.scalar(
                select(AuditEvent).where(
                    AuditEvent.organization_id == ALPHA, AuditEvent.sequence == 1
                )
            )
            second = session.scalar(
                select(AuditEvent).where(
                    AuditEvent.organization_id == ALPHA, AuditEvent.sequence == 2
                )
            )
            assert first is not None and second is not None
            first.sequence = 99
            session.flush()
            second.sequence = 1
            session.flush()
            first.sequence = 2
        elif tamper == "previous":
            session.execute(
                update(AuditEvent)
                .where(AuditEvent.organization_id == ALPHA, AuditEvent.sequence == 2)
                .values(previous_hash="f" * 64)
            )
        elif tamper == "truncate":
            head = session.get(AuditChainHead, ALPHA)
            assert head is not None
            head.head_sequence = 2
        session.commit()
        result = verify_audit_chain(session, ALPHA)
    assert not result.valid and result.reason == reason


def test_organization_chains_are_independent_and_sensitive_payload_is_rejected(
    database_engine: Engine,
) -> None:
    with Session(database_engine) as session:
        alpha = _append(session, ALPHA, 1)
        beta = _append(session, BETA, 1)
        session.commit()
        assert alpha.sequence == beta.sequence == 1
        assert alpha.previous_hash == beta.previous_hash == "0" * 64
        assert verify_audit_chain(session, ALPHA).valid
        assert verify_audit_chain(session, BETA).valid
        with pytest.raises(AuditPayloadRejected):
            append_audit_event(
                session,
                organization_id=ALPHA,
                event_type=AuditEventType.GRANT_ISSUED,
                actor_reference=ACTOR_HASH,
                subject_reference="grt_synthetic_0001",
                payload={"token": "must-not-persist"},
                now=NOW,
            )
        with pytest.raises(AuditPayloadRejected):
            append_audit_event(
                session,
                organization_id=ALPHA,
                event_type=AuditEventType.GRANT_ISSUED,
                actor_reference=ACTOR_HASH,
                subject_reference="grt_synthetic_0001",
                payload={"parameters": {"raw": "must-not-persist"}},
                now=NOW,
            )
