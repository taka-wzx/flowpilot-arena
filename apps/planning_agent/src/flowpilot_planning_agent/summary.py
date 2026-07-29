from flowpilot_planning_agent.context_schemas import (
    ScopeId,
    ShortTermEvent,
    ShortTermSummary,
    SummaryEntry,
    SummaryEventKind,
    canonical_json_bytes,
    sha256_hex,
)
from flowpilot_planning_agent.schemas import TaskId

KIND_PRIORITY: dict[SummaryEventKind, int] = {
    "unresolved_issue": 0,
    "recent_action": 1,
    "failure_reason": 2,
    "pending_step": 3,
    "user_supplement": 4,
}
REQUIRED_KINDS: tuple[SummaryEventKind, ...] = (
    "unresolved_issue",
    "recent_action",
    "failure_reason",
    "pending_step",
)


class DeterministicShortTermSummarizer:
    def summarize(
        self,
        *,
        task_id: TaskId,
        scope_id: ScopeId,
        events: tuple[ShortTermEvent, ...],
    ) -> ShortTermSummary:
        if len(events) > 12:
            raise ValueError("short-term input count exceeds frozen cap")
        if any(event.task_id != task_id or event.scope_id != scope_id for event in events):
            raise ValueError("short-term event owner mismatch")

        ordered = sorted(
            events,
            key=lambda event: (
                KIND_PRIORITY[event.kind],
                -event.ordinal,
                event.source_hash,
                event.event_id,
            ),
        )
        unique: list[ShortTermEvent] = []
        seen_pairs: set[tuple[str, str]] = set()
        for event in ordered:
            key = (event.kind, event.safe_value)
            if key not in seen_pairs:
                seen_pairs.add(key)
                unique.append(event)

        required: list[ShortTermEvent] = []
        for kind in REQUIRED_KINDS:
            match = next((event for event in unique if event.kind == kind), None)
            if match is not None:
                required.append(match)
        selected_ids = {event.event_id for event in required}
        candidates = required + [event for event in unique if event.event_id not in selected_ids]

        entries: list[SummaryEntry] = []
        for event in candidates:
            if len(entries) >= 8:
                break
            candidate = SummaryEntry(
                kind=event.kind,
                safe_value=event.safe_value,
                source_hash=event.source_hash,
                ordinal=event.ordinal,
            )
            projected = tuple((*entries, candidate))
            byte_count = len(canonical_json_bytes({"entries": projected}))
            token_count = (byte_count + 3) // 4
            if byte_count <= 4_096 and token_count <= 1_024:
                entries.append(candidate)

        entry_payload = canonical_json_bytes({"entries": tuple(entries)})
        source_hashes = tuple(dict.fromkeys(event.source_hash for event in ordered))
        fields: dict[str, object] = {
            "schema_version": "w9-short-term-summary/1.0",
            "task_id": task_id,
            "scope_id": scope_id,
            "entries": tuple(entries),
            "source_hashes": source_hashes,
            "input_count": len(events),
            "deduplicated_count": len(unique),
            "emitted_count": len(entries),
            "dropped_count": len(events) - len(entries),
            "canonical_bytes": len(entry_payload),
            "estimated_tokens": (len(entry_payload) + 3) // 4,
        }
        return ShortTermSummary.model_validate(
            {**fields, "summary_hash": sha256_hex(canonical_json_bytes(fields))}
        )
