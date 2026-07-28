import pytest

from flowpilot_planning_agent.schemas import JoinerSuppliedValues, PlanRequest


@pytest.fixture
def joiner_plan_request() -> PlanRequest:
    return PlanRequest(
        process="joiner",
        category="standard_joiner",
        human_brief="Complete the bounded synthetic joiner workflow.",
        supplied_values=JoinerSuppliedValues(
            employee_id=41001,
            ticket_title="Synthetic onboarding 001",
            username="synthetic.user001",
            asset_tag="SYN-W7-J001-V1",
            laptop_model="Synthetic Laptop 1",
            mailbox="synthetic.user001@flowpilot.invalid",
        ),
    )
