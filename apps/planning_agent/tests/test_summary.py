from flowpilot_planning_agent.context_schemas import (
    ShortTermEvent,
    validate_summary_hash,
)
from flowpilot_planning_agent.summary import DeterministicShortTermSummarizer


def event(kind: str, value: str, ordinal: int) -> ShortTermEvent:
    return ShortTermEvent.model_validate(
        {
            "event_id": f"event.{ordinal}",
            "task_id": "w7-jml-joiner-001-v1",
            "scope_id": "syn_scope_alpha",
            "kind": kind,
            "safe_value": value,
            "source_hash": f"{ordinal:064x}",
            "ordinal": ordinal,
        }
    )


def test_summary_preserves_required_kinds_deduplicates_and_hashes() -> None:
    events = (
        event("recent_action", "action.inspect", 9),
        event("unresolved_issue", "issue.missing", 8),
        event("failure_reason", "failure.page", 7),
        event("pending_step", "step.ticket", 6),
        event("recent_action", "action.inspect", 5),
        event("user_supplement", "supplement.synthetic", 4),
    )
    summarizer = DeterministicShortTermSummarizer()
    summary = summarizer.summarize(
        task_id="w7-jml-joiner-001-v1",
        scope_id="syn_scope_alpha",
        events=events,
    )
    validate_summary_hash(summary)
    assert {entry.kind for entry in summary.entries}.issuperset(
        {"unresolved_issue", "recent_action", "failure_reason", "pending_step"}
    )
    assert summary.input_count == 6
    assert summary.deduplicated_count == 5
    assert summary.emitted_count == 5
    assert summary.dropped_count == 1
    assert summary == summarizer.summarize(
        task_id="w7-jml-joiner-001-v1",
        scope_id="syn_scope_alpha",
        events=events,
    )


def test_summary_rejects_cross_task_event() -> None:
    foreign = event("pending_step", "step.ticket", 1).model_copy(
        update={"task_id": "w7-jml-mover-001-v1"}
    )
    try:
        DeterministicShortTermSummarizer().summarize(
            task_id="w7-jml-joiner-001-v1",
            scope_id="syn_scope_alpha",
            events=(foreign,),
        )
    except ValueError as exc:
        assert "owner mismatch" in str(exc)
    else:
        raise AssertionError("cross-task summary event was accepted")
