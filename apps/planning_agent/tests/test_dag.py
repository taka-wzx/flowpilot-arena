import pytest

from flowpilot_planning_agent.dag import DependencyBlocked, StepStateMachine, validate_dag
from flowpilot_planning_agent.planner import DeterministicPlanner
from flowpilot_planning_agent.schemas import PlanningDag


def test_joiner_topology_is_deterministic_and_multi_dependency(joiner_plan_request) -> None:
    dag = DeterministicPlanner().generate(joiner_plan_request).dag
    result = validate_dag(dag)
    assert result.valid
    assert result.node_count == 6
    assert result.edge_count == 8
    assert result.depth == 3
    assert result.width == 4
    assert result.topology == (
        "s00_inspect",
        "s10_ticket",
        "s20_account",
        "s30_asset",
        "s40_mail",
        "s90_finalize",
    )


def test_cycle_and_missing_dependency_are_rejected(joiner_plan_request) -> None:
    dag = DeterministicPlanner().generate(joiner_plan_request).dag
    steps = list(dag.steps)
    steps[0] = steps[0].model_copy(update={"dependencies": ("s90_finalize",)})
    cycle = validate_dag(dag.model_copy(update={"steps": tuple(steps)}))
    assert not cycle.valid
    assert "cycle" in cycle.reason_codes

    steps = list(dag.steps)
    steps[1] = steps[1].model_copy(update={"dependencies": ("missing_step",)})
    missing = validate_dag(dag.model_copy(update={"steps": tuple(steps)}))
    assert not missing.valid
    assert "unknown_dependency" in missing.reason_codes


def test_node_limit_is_rejected(joiner_plan_request) -> None:
    original = DeterministicPlanner().generate(joiner_plan_request).dag.steps[0]
    steps = tuple(
        original.model_copy(
            update={
                "step_id": f"s{number:02d}_node",
                "dependencies": () if number == 0 else (f"s{number - 1:02d}_node",),
            }
        )
        for number in range(17)
    )
    result = validate_dag(PlanningDag(process="joiner", category="standard_joiner", steps=steps))
    assert not result.valid
    assert "node_limit" in result.reason_codes


def test_state_machine_rejects_out_of_order_execution(joiner_plan_request) -> None:
    dag = DeterministicPlanner().generate(joiner_plan_request).dag
    machine = StepStateMachine(dag)
    with pytest.raises(DependencyBlocked):
        machine.start("s10_ticket")
    machine.start("s00_inspect")
    machine.verify("s00_inspect")
    machine.start("s10_ticket")
    assert machine.state("s10_ticket") == "executing"
