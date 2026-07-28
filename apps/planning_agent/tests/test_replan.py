from flowpilot_planning_agent.dag import validate_dag
from flowpilot_planning_agent.planner import DeterministicPlanner
from flowpilot_planning_agent.replan import partial_replan
from flowpilot_planning_agent.schemas import JoinerSuppliedValues, PlanRequest


def _joiner_plan():
    return (
        DeterministicPlanner()
        .generate(
            PlanRequest(
                process="joiner",
                category="standard_joiner",
                human_brief="Synthetic bounded brief",
                supplied_values=JoinerSuppliedValues(
                    employee_id=101,
                    ticket_title="Synthetic ticket",
                    username="synthetic.user",
                    asset_tag="SYN-W8-ASSET",
                    laptop_model="Synthetic laptop",
                    mailbox="synthetic.user@example.invalid",
                ),
            )
        )
        .dag
    )


def test_partial_replan_preserves_completed_and_replaces_only_descendants() -> None:
    original = _joiner_plan()
    revised, replaced = partial_replan(original, "s10_ticket", frozenset({"s00_inspect"}))
    assert replaced == ("s10_ticket", "s90_finalize")
    assert revised.steps[0] == original.steps[0]
    assert "s00_inspect" in validate_dag(revised).topology
    assert "r2_s10_ticket" in validate_dag(revised).topology
    assert validate_dag(revised).valid is True


def test_completed_or_unknown_step_cannot_be_replanned() -> None:
    original = _joiner_plan()
    for step_id in ("s00_inspect", "unknown"):
        try:
            partial_replan(original, step_id, frozenset({"s00_inspect"}))
        except ValueError:
            pass
        else:
            raise AssertionError("ineligible replan was accepted")
