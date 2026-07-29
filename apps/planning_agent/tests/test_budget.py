import pytest

from flowpilot_planning_agent.budget import BudgetExceeded, TotalBudgetLedger
from flowpilot_planning_agent.schemas import TotalBudget


def test_one_ledger_accumulates_planning_execution_and_verification() -> None:
    now = [100.0]
    ledger = TotalBudgetLedger(TotalBudget(), clock=lambda: now[0])
    ledger.charge_plan(nodes=6, edges=8, depth=3, serialized_bytes=2_000)
    ledger.charge_tool_match(rejected=True)
    ledger.charge_step()
    ledger.charge_action()
    ledger.charge_dom_observation(1_000)
    ledger.charge_verifier(probe=True)
    ledger.charge_context_assembly()
    ledger.charge_context_item(canonical_bytes=100, estimated_tokens=25)
    ledger.charge_retrieval(candidates=2, selected=1)
    ledger.charge_summary(inputs=3, outputs=2, dropped=1)
    ledger.charge_memory(reads=1, writes=1)
    now[0] += 1.25
    usage = ledger.snapshot()
    assert usage.plan_generations == 1
    assert usage.tool_matches == 1
    assert usage.tool_rejections == 1
    assert usage.executed_steps == 1
    assert usage.worker_actions == 1
    assert usage.verifier_calls == 1
    assert usage.verifier_probes == 1
    assert usage.model_calls == 2
    assert usage.context_assemblies == 1
    assert usage.context_items == 1
    assert usage.context_bytes == 100
    assert usage.retrieval_candidates == 2
    assert usage.summary_dropped == 1
    assert usage.memory_reads == 1
    assert usage.memory_writes == 1
    assert usage.elapsed_ms == 1_250


def test_ledger_fails_closed_without_reset() -> None:
    ledger = TotalBudgetLedger(TotalBudget(max_steps=1))
    ledger.charge_action()
    with pytest.raises(BudgetExceeded, match="action_budget_exhausted"):
        ledger.charge_action()
    assert ledger.snapshot().worker_actions == 2
