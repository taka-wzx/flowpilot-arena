import pytest
from pydantic import ValidationError

from flowpilot_planning_agent.main import healthz, validate_plan
from flowpilot_planning_agent.planner import DeterministicPlanner
from flowpilot_planning_agent.schemas import PlanningDag


def test_health_and_plan_validation(joiner_plan_request) -> None:
    dag = DeterministicPlanner().generate(joiner_plan_request).dag
    health = healthz()
    validation = validate_plan(dag)
    assert health["service"] == "planning-agent"
    assert validation.valid is True
    assert PlanningDag.model_validate(dag.model_dump(mode="json")) == dag


def test_validation_contract_rejects_unknown_fields(joiner_plan_request) -> None:
    dag = DeterministicPlanner().generate(joiner_plan_request).dag.model_dump(mode="json")
    dag["selector"] = "#unsafe"
    with pytest.raises(ValidationError):
        PlanningDag.model_validate(dag)
