from flowpilot_planning_agent.dag import validate_dag
from flowpilot_planning_agent.planner import DeterministicPlanner
from flowpilot_planning_agent.schemas import (
    LeaverSuppliedValues,
    MoverSuppliedValues,
    PlanRequest,
)


def test_planner_generates_valid_process_specific_dags(joiner_plan_request) -> None:
    requests = (
        joiner_plan_request,
        PlanRequest(
            process="mover",
            category="standard_mover",
            human_brief="Synthetic mover brief",
            supplied_values=MoverSuppliedValues(
                employee_id=42001,
                new_department="Synthetic Operations",
                new_job_title="Synthetic Lead",
                new_location="Synthetic East",
            ),
        ),
        PlanRequest(
            process="leaver",
            category="standard_leaver",
            human_brief="Synthetic leaver brief",
            supplied_values=LeaverSuppliedValues(employee_id=43001),
        ),
    )
    planner = DeterministicPlanner()
    results = tuple(planner.generate(request) for request in requests)
    assert all(validate_dag(result.dag).valid for result in results)
    assert tuple(len(result.dag.steps) for result in results) == (6, 3, 6)
    assert len({result.plan_id for result in results}) == 3
