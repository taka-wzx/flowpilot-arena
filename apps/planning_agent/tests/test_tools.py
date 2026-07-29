from flowpilot_planning_agent.budget import TotalBudgetLedger
from flowpilot_planning_agent.planner import DeterministicPlanner
from flowpilot_planning_agent.schemas import TotalBudget
from flowpilot_planning_agent.tools import GLOBAL_TOOLS, DeterministicToolMatcher


def test_matcher_uses_closed_intersection_and_rejects_unknown(joiner_plan_request) -> None:
    step = DeterministicPlanner().generate(joiner_plan_request).dag.steps[0]
    ledger = TotalBudgetLedger(TotalBudget())
    matcher = DeterministicToolMatcher()
    matched = matcher.match(
        step,
        "read",
        page="hris",
        modality="dom",
        worker_allowed=GLOBAL_TOOLS,
        ledger=ledger,
    )
    unknown = matcher.match(
        step,
        "shell",
        page="hris",
        modality="dom",
        worker_allowed=GLOBAL_TOOLS,
        ledger=ledger,
    )
    disallowed = matcher.match(
        step,
        "fill",
        page="hris",
        modality="dom",
        worker_allowed=GLOBAL_TOOLS,
        ledger=ledger,
    )
    navigation = matcher.match(
        step,
        "navigate",
        page="itsm",
        modality="dom",
        worker_allowed=GLOBAL_TOOLS,
        ledger=ledger,
    )
    wrong_page = matcher.match(
        step,
        "read",
        page="itsm",
        modality="dom",
        worker_allowed=GLOBAL_TOOLS,
        ledger=ledger,
    )
    assert matched.matched and matched.action == "read"
    assert unknown.rejection_reason == "unknown_tool"
    assert disallowed.rejection_reason == "step_disallowed"
    assert navigation.matched and navigation.action == "navigate"
    assert wrong_page.rejection_reason == "page_disallowed"
    assert ledger.snapshot().tool_rejections == 3
