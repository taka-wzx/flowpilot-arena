import json

import pytest
from pydantic import ValidationError

from flowpilot_vision_agent.schemas import (
    VisionAgentRunRequest,
    VisionAgentRunResult,
    VisionModelDecision,
)


def test_run_request_rejects_unknown_fields_and_non_w5_tasks() -> None:
    with pytest.raises(ValidationError):
        VisionAgentRunRequest.model_validate(
            {
                "schema_version": "w5-vision-agent-run/1.0",
                "task_id": "w3-joiner-006",
                "instruction": "Synthetic task",
            }
        )
    with pytest.raises(ValidationError):
        VisionAgentRunRequest.model_validate(
            {
                "schema_version": "w5-vision-agent-run/1.0",
                "task_id": "w3-joiner-001",
                "instruction": "Synthetic task",
                "provider_url": "https://example.invalid",
            }
        )


def test_model_decision_rejects_coordinates_selectors_and_unknown_fields() -> None:
    for field, value in (
        ("x", 10),
        ("y", 20),
        ("selector", "#submit"),
        ("javascript", "document.cookie"),
        ("image_url", "https://example.invalid/image.jpg"),
    ):
        with pytest.raises(ValidationError):
            VisionModelDecision.model_validate(
                {
                    "schema_version": "w5-vision-model-decision/1.0",
                    "action": {
                        "schema_version": "w5-vision-action/1.0",
                        "action_id": "act_unsafe",
                        "type": "click",
                        "observation_id": "vobs_visual0001",
                        "screenshot_ref": "shot_visual0001",
                        "grounding_ref": "gref_visual0001_1",
                        field: value,
                    },
                }
            )


def test_agent_result_has_no_success_score_or_visual_payload() -> None:
    schema = json.dumps(VisionAgentRunResult.model_json_schema(), sort_keys=True).lower()
    properties = VisionAgentRunResult.model_json_schema()["properties"]
    for prohibited in ("success", "passed", "score", "grader"):
        assert prohibited not in properties
    for prohibited in (
        "image_base64",
        "ocr",
        "screenshot_ref",
        "grounding_ref",
        "semantic_nodes",
        "interactive_elements",
    ):
        assert prohibited not in properties
        assert prohibited not in schema
