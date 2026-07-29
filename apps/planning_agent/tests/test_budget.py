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
    assert usage.elapsed_ms == 1_250


def test_ledger_fails_closed_without_reset() -> None:
    ledger = TotalBudgetLedger(TotalBudget(max_steps=1))
    ledger.charge_action()
    with pytest.raises(BudgetExceeded, match="action_budget_exhausted"):
        ledger.charge_action()
    assert ledger.snapshot().worker_actions == 2
