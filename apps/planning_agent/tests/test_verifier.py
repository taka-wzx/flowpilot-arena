from flowpilot_planning_agent.budget import TotalBudgetLedger
from flowpilot_planning_agent.schemas import TotalBudget, VerifierRequest
from flowpilot_planning_agent.verifier import DeterministicStepVerifier


def _request(**updates: object) -> VerifierRequest:
    values: dict[str, object] = {
        "step_id": "s00_inspect",
        "expected_page": "hris",
        "current_page": "hris",
        "observation_generation": 2,
        "action_success": True,
        "postconditions": ("action_succeeded", "expected_page_observed"),
    }
    values.update(updates)
    return VerifierRequest.model_validate(values)


def test_verifier_closed_outcomes_never_promote_negative() -> None:
    verifier = DeterministicStepVerifier()
    verified = verifier.verify(_request(), TotalBudgetLedger(TotalBudget()), probe=True)
    negative = verifier.verify(
        _request(action_success=False), TotalBudgetLedger(TotalBudget()), probe=False
    )
    inconclusive = verifier.verify(
        _request(force_inconclusive=True), TotalBudgetLedger(TotalBudget()), probe=False
    )
    assert verified.status == "verified"
    assert negative.status == "not_verified"
    assert inconclusive.status == "inconclusive"
