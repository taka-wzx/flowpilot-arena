import pytest
from pydantic import ValidationError

from flowpilot_planning_agent.schemas import (
    JoinerSuppliedValues,
    PlanningRunResult,
    PlanRequest,
)


def test_strict_plan_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        PlanRequest.model_validate(
            {
                "process": "joiner",
                "category": "standard_joiner",
                "human_brief": "Synthetic brief",
                "supplied_values": {
                    "process": "joiner",
                    "employee_id": 41001,
                    "ticket_title": "Ticket",
                    "username": "synthetic.user",
                    "asset_tag": "SYN-W7-ONE",
                    "laptop_model": "Laptop",
                    "mailbox": "synthetic.user@flowpilot.invalid",
                },
                "selector": "#unsafe",
            }
        )


def test_process_and_category_must_match() -> None:
    with pytest.raises(ValidationError):
        PlanRequest(
            process="mover",
            category="standard_mover",
            human_brief="Synthetic brief",
            supplied_values=JoinerSuppliedValues(
                employee_id=41001,
                ticket_title="Ticket",
                username="synthetic.user",
                asset_tag="SYN-W7-ONE",
                laptop_model="Laptop",
                mailbox="synthetic.user@flowpilot.invalid",
            ),
        )


def test_run_result_has_no_success_grade_or_score_fields() -> None:
    fields = PlanningRunResult.model_fields
    assert "success" not in fields
    assert "passed" not in fields
    assert "score" not in fields
