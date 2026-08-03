"""W13 deterministic, closed observability and replay helpers."""

import json
import secrets
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flowpilot_control_api.models import ObservabilityEvent, ProductionRun
from flowpilot_control_api.schemas import (
    CostSummary,
    FailureCategory,
    ObservabilityEventRead,
    ObservabilityPhase,
    ObservabilityStatus,
    ProductionRunRead,
    ProductionRunStatus,
    ProductionTerminalReason,
    ReplayStep,
    RunTraceExport,
    TraceAttributes,
    TraceDashboard,
    TraceReason,
    canonical_json_bytes,
    stable_hash,
)

_FORBIDDEN_ATTRIBUTE_KEYS = frozenset(
    {
        "token",
        "access_token",
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
        "parameters",
        "task",
        "page",
        "dom",
        "image",
        "ocr",
        "model_content",
        "dsn",
        "secret",
        "machine_path",
    }
)
_FORBIDDEN_TEXT = (
    "bearer ",
    "access_token",
    "authorization_code",
    "credential",
    "nonce",
    "cookie",
    "password",
    "private_key",
    "@",
    "postgresql://",
    "sqlite+pysqlite://",
    "%systemdrive%",
    ":\\",
)


class ObservabilityPayloadRejected(RuntimeError):
    pass


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def trace_id_for_run(organization_id: str, run_id: str) -> str:
    return stable_hash(
        {
            "schema_version": "w13-trace-id/1.0",
            "organization_id": organization_id,
            "run_id": run_id,
        }
    )[:32]


def _span_id(
    *,
    organization_id: str,
    run_id: str,
    event_sequence: int,
    phase: ObservabilityPhase,
    reason: TraceReason,
) -> str:
    return stable_hash(
        {
            "schema_version": "w13-span-id/1.0",
            "organization_id": organization_id,
            "run_id": run_id,
            "event_sequence": event_sequence,
            "phase": phase.value,
            "reason": reason.value,
        }
    )[:16]


def _safe_attributes(value: TraceAttributes | dict[str, object] | None) -> TraceAttributes:
    try:
        attributes = TraceAttributes() if value is None else TraceAttributes.model_validate(value)
    except ValidationError as exc:
        raise ObservabilityPayloadRejected("trace attributes are outside the W13 schema") from exc
    fields = attributes.model_dump(mode="json", exclude_none=True)
    if set(fields) & _FORBIDDEN_ATTRIBUTE_KEYS:
        raise ObservabilityPayloadRejected("trace attributes contain a forbidden key")
    encoded = json.dumps(fields, sort_keys=True, separators=(",", ":")).lower()
    if any(marker in encoded for marker in _FORBIDDEN_TEXT):
        raise ObservabilityPayloadRejected("trace attributes contain forbidden material")
    if len(canonical_json_bytes(fields)) > 2_048:
        raise ObservabilityPayloadRejected("trace attributes exceed the W13 byte bound")
    return attributes


def _event_fields(
    *,
    event_id: str,
    organization_id: str,
    run_id: str,
    event_sequence: int,
    trace_id: str,
    span_id: str,
    parent_span_id: str | None,
    phase: ObservabilityPhase,
    status: ObservabilityStatus,
    failure_category: FailureCategory,
    reason: TraceReason,
    attributes: TraceAttributes,
    attributes_hash: str,
    observed_at: datetime,
) -> dict[str, object]:
    return {
        "schema_version": "w13-observability-event/1.0",
        "event_id": event_id,
        "organization_id": organization_id,
        "run_id": run_id,
        "event_sequence": event_sequence,
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "phase": phase.value,
        "status": status.value,
        "failure_category": failure_category.value,
        "reason": reason.value,
        "attributes": attributes.model_dump(mode="json", exclude_none=True),
        "attributes_hash": attributes_hash,
        "observed_at": _utc(observed_at),
    }


def append_observability_event(
    session: Session,
    *,
    organization_id: str,
    run_id: str,
    phase: ObservabilityPhase,
    status: ObservabilityStatus,
    reason: TraceReason,
    now: datetime,
    failure_category: FailureCategory = FailureCategory.NONE,
    attributes: TraceAttributes | dict[str, object] | None = None,
) -> ObservabilityEvent:
    observed_at = _utc(now)
    run_exists = session.scalar(
        select(ProductionRun.run_id)
        .where(
            ProductionRun.organization_id == organization_id,
            ProductionRun.run_id == run_id,
        )
        .with_for_update()
    )
    if run_exists is None:
        raise ObservabilityPayloadRejected("trace event must reference an existing run")
    event_sequence = (
        int(
            session.scalar(
                select(func.coalesce(func.max(ObservabilityEvent.event_sequence), 0)).where(
                    ObservabilityEvent.organization_id == organization_id,
                    ObservabilityEvent.run_id == run_id,
                )
            )
            or 0
        )
        + 1
    )
    if event_sequence > 256:
        raise ObservabilityPayloadRejected("trace event sequence exceeds the W13 bound")
    trace_id = trace_id_for_run(organization_id, run_id)
    span_id = _span_id(
        organization_id=organization_id,
        run_id=run_id,
        event_sequence=event_sequence,
        phase=phase,
        reason=reason,
    )
    parent_span_id = (
        session.scalar(
            select(ObservabilityEvent.span_id).where(
                ObservabilityEvent.organization_id == organization_id,
                ObservabilityEvent.run_id == run_id,
                ObservabilityEvent.event_sequence == 1,
            )
        )
        if event_sequence > 1
        else None
    )
    event_id = f"obs_{secrets.token_hex(16)}"
    safe_attributes = _safe_attributes(attributes)
    attributes_json = canonical_json_bytes(
        safe_attributes.model_dump(mode="json", exclude_none=True)
    ).decode("utf-8")
    attributes_hash = stable_hash(safe_attributes.model_dump(mode="json", exclude_none=True))
    event_hash = stable_hash(
        _event_fields(
            event_id=event_id,
            organization_id=organization_id,
            run_id=run_id,
            event_sequence=event_sequence,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            phase=phase,
            status=status,
            failure_category=failure_category,
            reason=reason,
            attributes=safe_attributes,
            attributes_hash=attributes_hash,
            observed_at=observed_at,
        )
    )
    event = ObservabilityEvent(
        event_id=event_id,
        organization_id=organization_id,
        run_id=run_id,
        event_sequence=event_sequence,
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        phase=phase.value,
        status=status.value,
        failure_category=failure_category.value,
        reason=reason.value,
        attributes_json=attributes_json,
        attributes_hash=attributes_hash,
        event_hash=event_hash,
        observed_at=observed_at,
    )
    session.add(event)
    session.flush()
    return event


def event_read(event: ObservabilityEvent) -> ObservabilityEventRead:
    attributes_value: Any = json.loads(event.attributes_json)
    attributes = TraceAttributes.model_validate(attributes_value)
    return ObservabilityEventRead(
        event_id=event.event_id,
        organization_id=event.organization_id,
        run_id=event.run_id,
        event_sequence=event.event_sequence,
        trace_id=event.trace_id,
        span_id=event.span_id,
        parent_span_id=event.parent_span_id,
        phase=ObservabilityPhase(event.phase),
        status=ObservabilityStatus(event.status),
        failure_category=FailureCategory(event.failure_category),
        reason=TraceReason(event.reason),
        attributes=attributes,
        attributes_hash=event.attributes_hash,
        event_hash=event.event_hash,
        observed_at=event.observed_at,
    )


def list_observability_events(
    session: Session,
    *,
    organization_id: str,
    run_id: str,
) -> tuple[ObservabilityEventRead, ...]:
    events = tuple(
        event_read(event)
        for event in session.scalars(
            select(ObservabilityEvent)
            .where(
                ObservabilityEvent.organization_id == organization_id,
                ObservabilityEvent.run_id == run_id,
            )
            .order_by(ObservabilityEvent.event_sequence)
            .limit(256)
        )
    )
    for ordinal, event in enumerate(events, start=1):
        if event.event_sequence != ordinal:
            raise ObservabilityPayloadRejected("trace event sequence is not contiguous")
    return events


def _event_failure(events: tuple[ObservabilityEventRead, ...]) -> FailureCategory:
    for event in events:
        if event.failure_category != FailureCategory.NONE:
            return event.failure_category
    return FailureCategory.NONE


def _terminal_failure(run: ProductionRunRead) -> FailureCategory:
    if run.status == ProductionRunStatus.FINISHED_UNGRADED:
        return FailureCategory.NONE
    if run.terminal_reason is None:
        return FailureCategory.NONE
    return {
        ProductionTerminalReason.AUTHORIZATION_INVALID: FailureCategory.AUTHZ,
        ProductionTerminalReason.QUEUE_EXPIRED: FailureCategory.QUEUE_EXPIRY,
        ProductionTerminalReason.LEASE_EXHAUSTED: FailureCategory.LEASE_FENCE,
        ProductionTerminalReason.WORKFLOW_REJECTED: FailureCategory.WORKFLOW_REJECTED,
        ProductionTerminalReason.RECEIPT_INVALID: FailureCategory.RECEIPT_INVALID,
        ProductionTerminalReason.WORKER_DRAINED: FailureCategory.LEASE_FENCE,
        ProductionTerminalReason.DEPENDENCY_UNAVAILABLE: FailureCategory.DEPENDENCY_UNAVAILABLE,
        ProductionTerminalReason.AGENT_FAILED: FailureCategory.RECOVERY_FAILURE,
        ProductionTerminalReason.CANCELLED_BY_ACTOR: FailureCategory.NONE,
    }[run.terminal_reason]


def build_run_trace_export(
    session: Session,
    *,
    run: ProductionRunRead,
) -> RunTraceExport:
    events = list_observability_events(
        session,
        organization_id=run.organization_id,
        run_id=run.run_id,
    )
    replay_steps = tuple(
        ReplayStep(
            ordinal=index,
            phase=event.phase,
            status=event.status,
            failure_category=event.failure_category,
            reason=event.reason,
            reference_hash=event.event_hash,
            observed_at=event.observed_at,
        )
        for index, event in enumerate(events, start=1)
    )
    model_calls = sum(event.attributes.model_calls or 0 for event in events)
    input_tokens = sum(event.attributes.input_tokens or 0 for event in events)
    output_tokens = sum(event.attributes.output_tokens or 0 for event in events)
    fake_cost = sum(event.attributes.fake_cost_microusd or 0 for event in events)
    real_cost = sum(event.attributes.real_cost_microusd or 0 for event in events)
    if real_cost != 0 or any(event.attributes.sensitive_fields_present for event in events):
        raise ObservabilityPayloadRejected("trace export safety invariant failed")
    cost = CostSummary(
        model_calls=model_calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        fake_cost_microusd=fake_cost,
        real_cost_microusd=0,
    )
    failure_category = _event_failure(events)
    if failure_category == FailureCategory.NONE:
        failure_category = _terminal_failure(run)
    dashboard_fields: dict[str, object] = {
        "schema_version": "w13-trace-dashboard/1.0",
        "event_count": len(events),
        "replay_step_count": len(replay_steps),
        "terminal_status": run.status.value,
        "failure_category": failure_category.value,
        "model_calls": model_calls,
        "fake_cost_microusd": fake_cost,
        "real_cost_microusd": 0,
        "sensitive_fields_present": False,
    }
    dashboard = TraceDashboard(
        event_count=len(events),
        replay_step_count=len(replay_steps),
        terminal_status=run.status,
        failure_category=failure_category,
        model_calls=model_calls,
        fake_cost_microusd=fake_cost,
        real_cost_microusd=0,
        sensitive_fields_present=False,
        dashboard_hash=stable_hash(dashboard_fields),
    )
    trace_id = events[0].trace_id if events else trace_id_for_run(run.organization_id, run.run_id)
    export_fields: dict[str, object] = {
        "schema_version": "w13-run-trace-export/1.0",
        "run": run.model_dump(mode="json"),
        "trace_id": trace_id,
        "events": [event.model_dump(mode="json") for event in events],
        "replay_steps": [step.model_dump(mode="json") for step in replay_steps],
        "cost": cost.model_dump(mode="json"),
        "dashboard": dashboard.model_dump(mode="json"),
    }
    return RunTraceExport(
        run=run,
        trace_id=trace_id,
        events=events,
        replay_steps=replay_steps,
        cost=cost,
        dashboard=dashboard,
        export_hash=stable_hash(export_fields),
    )
