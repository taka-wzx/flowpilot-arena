from flowpilot_planning_agent.budget import BudgetExceeded, TotalBudgetLedger
from flowpilot_planning_agent.schemas import VerifierRequest, VerifierResult


class DeterministicStepVerifier:
    """Runtime evidence check; deliberately not an Arena Grader."""

    def verify(
        self,
        request: VerifierRequest,
        ledger: TotalBudgetLedger,
        *,
        probe: bool,
    ) -> VerifierResult:
        try:
            ledger.charge_verifier(probe=probe)
        except BudgetExceeded:
            return VerifierResult(
                step_id=request.step_id,
                status="inconclusive",
                reason_code="budget_exhausted",
            )
        if request.force_inconclusive:
            return VerifierResult(
                step_id=request.step_id,
                status="inconclusive",
                reason_code="forced_inconclusive",
            )
        if request.current_page is None or request.observation_generation is None:
            return VerifierResult(
                step_id=request.step_id,
                status="inconclusive",
                reason_code="observation_missing",
            )
        if not request.action_success:
            return VerifierResult(
                step_id=request.step_id,
                status="not_verified",
                reason_code="action_failed",
            )
        if request.current_page != request.expected_page:
            return VerifierResult(
                step_id=request.step_id,
                status="not_verified",
                reason_code="page_mismatch",
            )
        return VerifierResult(
            step_id=request.step_id,
            status="verified",
            reason_code="conditions_satisfied",
        )
