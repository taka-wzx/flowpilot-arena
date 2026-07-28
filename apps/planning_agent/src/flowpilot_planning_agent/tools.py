from flowpilot_planning_agent.budget import BudgetExceeded, TotalBudgetLedger
from flowpilot_planning_agent.schemas import (
    AllowedAction,
    Modality,
    Page,
    PlanStep,
    ToolMatchResult,
)

GLOBAL_TOOLS: frozenset[AllowedAction] = frozenset(
    {"navigate", "click", "fill", "select", "read", "scroll", "wait", "finish", "fail"}
)
PAGES: tuple[Page, ...] = ("hris", "itsm", "iam", "assets", "mail")
PAGE_TOOLS: dict[Page, frozenset[AllowedAction]] = {page: GLOBAL_TOOLS for page in PAGES}
MODALITY_TOOLS: dict[Modality, frozenset[AllowedAction]] = {
    "dom": GLOBAL_TOOLS,
    "vision": GLOBAL_TOOLS,
}


class DeterministicToolMatcher:
    def match(
        self,
        step: PlanStep,
        candidate: str,
        *,
        page: Page,
        modality: Modality,
        worker_allowed: frozenset[AllowedAction],
        ledger: TotalBudgetLedger,
    ) -> ToolMatchResult:
        if candidate not in GLOBAL_TOOLS:
            return self._reject(ledger, "unknown_tool")
        action: AllowedAction = candidate
        if action not in step.allowed_actions:
            return self._reject(ledger, "step_disallowed")
        if action != "navigate" and page != step.expected_page:
            return self._reject(ledger, "page_disallowed")
        if action not in PAGE_TOOLS[page]:
            return self._reject(ledger, "page_disallowed")
        if action not in MODALITY_TOOLS[modality] or action not in worker_allowed:
            return self._reject(ledger, "modality_disallowed")
        if not ledger.can_execute_action():
            return self._reject(ledger, "budget_exhausted")
        ledger.charge_tool_match(rejected=False)
        return ToolMatchResult(matched=True, action=action)

    @staticmethod
    def _reject(ledger: TotalBudgetLedger, reason: str) -> ToolMatchResult:
        try:
            ledger.charge_tool_match(rejected=True)
        except BudgetExceeded:
            return ToolMatchResult(matched=False, rejection_reason="budget_exhausted")
        return ToolMatchResult(matched=False, rejection_reason=reason)  # type: ignore[arg-type]
