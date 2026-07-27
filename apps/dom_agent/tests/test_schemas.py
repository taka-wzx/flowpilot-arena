import json

import pytest
from pydantic import ValidationError

from flowpilot_dom_agent.schemas import AgentRunRequest, AgentRunResult, ModelDecision


def test_run_request_rejects_unknown_fields_and_non_w4_tasks() -> None:
    with pytest.raises(ValidationError):
        AgentRunRequest.model_validate(
            {
                "schema_version": "w4-dom-agent-run/1.0",
                "task_id": "w3-joiner-006",
                "instruction": "Synthetic task",
            }
        )
    with pytest.raises(ValidationError):
        AgentRunRequest.model_validate(
            {
                "schema_version": "w4-dom-agent-run/1.0",
                "task_id": "w3-joiner-001",
                "instruction": "Synthetic task",
                "grader_url": "http://sandbox-api:8001/api/arena/grade",
            }
        )


def test_model_decision_rejects_unknown_action_fields() -> None:
    with pytest.raises(ValidationError):
        ModelDecision.model_validate(
            {
                "schema_version": "w4-model-decision/1.0",
                "action": {
                    "schema_version": "w4-dom-action/1.0",
                    "action_id": "act_unsafe",
                    "type": "click",
                    "observation_id": "obs_abcdefgh",
                    "element_ref": "ref_abcdefgh",
                    "selector": "#submit",
                },
            }
        )


def test_agent_result_has_no_success_passed_or_grade_field() -> None:
    schema = json.dumps(AgentRunResult.model_json_schema(), sort_keys=True).lower()
    properties = AgentRunResult.model_json_schema()["properties"]
    assert "success" not in properties
    assert "passed" not in properties
    assert "score" not in properties
    assert "grader" not in schema
