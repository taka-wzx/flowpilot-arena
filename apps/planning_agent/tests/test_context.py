from datetime import UTC, datetime, timedelta

import pytest

from flowpilot_planning_agent.budget import BudgetExceeded, TotalBudgetLedger
from flowpilot_planning_agent.context import ContextAssembler
from flowpilot_planning_agent.context_schemas import (
    AblationProfile,
    BrowserWorkingInput,
    ContextAssembleRequest,
    MemoryMutation,
    ShortTermEvent,
    TaskFactInput,
    validate_context_hash,
)
from flowpilot_planning_agent.memory import OrganizationMemoryStore
from flowpilot_planning_agent.schemas import TotalBudget

AS_OF = datetime(2026, 7, 29, tzinfo=UTC)


def request(
    *,
    ablation: AblationProfile = "full_five_layer",
    budget: TotalBudget | None = None,
) -> ContextAssembleRequest:
    task_id = "w7-jml-joiner-001-v1"
    scope_id = "syn_scope_alpha"
    return ContextAssembleRequest(
        run_id="run_context01",
        task_id=task_id,
        scope_id=scope_id,
        actor_scope_id=scope_id,
        process="joiner",
        phase="planning",
        as_of=AS_OF,
        database_snapshot_hash="a" * 64,
        task_facts=(
            TaskFactInput(
                item_id="fact.process",
                task_id=task_id,
                scope_id=scope_id,
                category="task_process",
                safe_value="joiner",
                snapshot_version=7,
            ),
            TaskFactInput(
                item_id="fact.employee",
                task_id=task_id,
                scope_id=scope_id,
                category="employee_state",
                safe_value="pending",
                snapshot_version=7,
            ),
        ),
        browser_working=(
            BrowserWorkingInput(
                item_id="browser.current",
                task_id=task_id,
                scope_id=scope_id,
                category="current_page",
                safe_value="hris",
                observation_hash="b" * 64,
                ordinal=2,
                observed_at=AS_OF - timedelta(seconds=1),
                expires_at=AS_OF + timedelta(minutes=1),
            ),
            BrowserWorkingInput(
                item_id="browser.expired",
                task_id=task_id,
                scope_id=scope_id,
                category="local_failure",
                safe_value="failure.expired",
                observation_hash="c" * 64,
                ordinal=1,
                observed_at=AS_OF - timedelta(minutes=2),
                expires_at=AS_OF - timedelta(minutes=1),
            ),
        ),
        short_term_events=(
            ShortTermEvent(
                event_id="event.issue",
                task_id=task_id,
                scope_id=scope_id,
                kind="unresolved_issue",
                safe_value="issue.missing",
                source_hash="d" * 64,
                ordinal=2,
            ),
            ShortTermEvent(
                event_id="event.step",
                task_id=task_id,
                scope_id=scope_id,
                kind="pending_step",
                safe_value="step.ticket",
                source_hash="e" * 64,
                ordinal=1,
            ),
        ),
        memory_mutations=(
            MemoryMutation(
                action="upsert",
                memory_id="memory.department",
                field="department",
                safe_value="engineering",
                valid_from=datetime(2026, 1, 1, tzinfo=UTC),
                expires_at=datetime(2027, 1, 1, tzinfo=UTC),
            ),
        ),
        ablation=ablation,
        budget=budget or TotalBudget(),
    )


def assemble(payload: ContextAssembleRequest):
    ledger = TotalBudgetLedger(payload.budget, clock=lambda: 100.0)
    return ContextAssembler(OrganizationMemoryStore()).assemble(payload, ledger)


def test_full_context_has_five_layers_provenance_expiry_and_replay() -> None:
    payload = request()
    first = assemble(payload)
    second = assemble(payload)
    validate_context_hash(first.context)
    assert type(first.context).model_validate_json(first.context.model_dump_json()) == first.context
    assert first.context == second.context
    assert first.context.layer_counts.task_facts == 2
    assert first.context.layer_counts.browser_working == 1
    assert first.context.layer_counts.short_term == 2
    assert first.context.layer_counts.org_memory == 1
    assert first.context.layer_counts.enterprise_knowledge == 1
    assert "failure.expired" not in {item.safe_value for item in first.context.items}
    assert first.context.items[0].layer == "task_facts"
    assert all(item.content_hash and item.source and item.trust for item in first.context.items)
    assert first.usage.context_assemblies == 1
    assert first.usage.context_items == len(first.context.items)
    assert first.usage.retrieval_queries == 1
    assert first.usage.summary_inputs == 2
    assert first.usage.memory_writes == 1
    assert first.usage.memory_reads == 1


@pytest.mark.parametrize(
    ("profile", "expected"),
    (
        ("full_five_layer", (2, 1, 2, 1, 1)),
        ("task_facts_only", (2, 0, 0, 0, 0)),
        ("no_short_term", (2, 1, 0, 1, 1)),
        ("no_enterprise_retrieval", (2, 1, 2, 1, 0)),
        ("no_organization_memory", (2, 1, 2, 0, 1)),
    ),
)
def test_frozen_ablation_matrix(profile: AblationProfile, expected: tuple[int, ...]) -> None:
    counts = assemble(request(ablation=profile)).context.layer_counts
    assert (
        counts.task_facts,
        counts.browser_working,
        counts.short_term,
        counts.org_memory,
        counts.enterprise_knowledge,
    ) == expected


def test_task_fact_precedence_deduplicates_lower_layer_value() -> None:
    payload = request().model_copy(
        update={
            "browser_working": (
                request().browser_working[0].model_copy(update={"safe_value": "pending"}),
            )
        }
    )
    result = assemble(payload)
    pending = [item for item in result.context.items if item.safe_value == "pending"]
    assert len(pending) == 1
    assert pending[0].layer == "task_facts"
    assert pending[0].trust == "authoritative"


def test_context_budget_exhaustion_fails_closed_without_counter_reset() -> None:
    payload = request(budget=TotalBudget(max_context_items=1))
    ledger = TotalBudgetLedger(payload.budget, clock=lambda: 100.0)
    memory = OrganizationMemoryStore()
    with pytest.raises(BudgetExceeded, match="context_item_budget_exhausted"):
        ContextAssembler(memory).assemble(payload, ledger)
    usage = ledger.snapshot()
    assert usage.context_assemblies == 1
    assert usage.context_items == 2
    assert usage.memory_writes == 0
    assert (
        memory.read(
            actor_scope_id=payload.scope_id,
            scope_id=payload.scope_id,
            as_of=payload.as_of,
        )
        == ()
    )
