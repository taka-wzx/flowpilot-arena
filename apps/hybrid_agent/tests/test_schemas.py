import json

import pytest
from conftest import hybrid_dom_observation
from pydantic import TypeAdapter, ValidationError

from flowpilot_hybrid_agent.schemas import (
    CompressedVisualObservation,
    HybridActionEnvelope,
    HybridActionResult,
    HybridDomObservation,
    RouteDecision,
)


def test_hybrid_schema_rejects_unknown_execution_fields_and_wrong_mode_references() -> None:
    adapter = TypeAdapter(HybridActionEnvelope)
    valid = adapter.validate_python(
        {
            "schema_version": "w6-hybrid-action-envelope/1.0",
            "session_id": "bw_abcdefghijklmnop",
            "generation": 1,
            "modality": "dom",
            "action": {
                "action_id": "act_valid",
                "type": "read",
                "observation_id": "obs_abcdefgh",
                "element_ref": "ref_abcdefgh",
            },
        }
    )
    assert valid.modality == "dom"
    for missing in ("session_id", "generation"):
        payload = valid.model_dump(mode="json")
        payload.pop(missing)
        with pytest.raises(ValidationError):
            adapter.validate_python(payload)
    for field, value in (
        ("selector", "#unsafe"),
        ("x", 12),
        ("bounding_box", [1, 2, 3, 4]),
        ("javascript", "document.cookie"),
        ("path", "/tmp/unsafe"),
    ):
        with pytest.raises(ValidationError):
            adapter.validate_python(
                {
                    "schema_version": "w6-hybrid-action-envelope/1.0",
                    "session_id": "bw_abcdefghijklmnop",
                    "generation": 1,
                    "modality": "vision",
                    "action": {
                        "action_id": "act_bad",
                        "type": "read",
                        "observation_id": "vobs_abcdefgh",
                        "screenshot_ref": "shot_abcdefgh",
                        "grounding_ref": "gref_abcdefgh",
                        field: value,
                    },
                }
            )


def test_route_decision_and_selected_visual_schema_are_strictly_bounded() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(
            from_modality="dom",
            to_modality="vision",
            reason_code="dom_structure_weak",
            switched=False,
            switch_count=0,
        )
    schema = json.dumps(CompressedVisualObservation.model_json_schema(), sort_keys=True).lower()
    for prohibited in ("semantic_nodes", "interactive_elements", "element_ref", "current_url"):
        assert prohibited not in schema


def test_hybrid_observation_and_result_identity_invariants_are_strict() -> None:
    current = hybrid_dom_observation()
    payload = current.model_dump(mode="json")
    payload["route_signals"]["dom_interactive_count"] = 0
    with pytest.raises(ValidationError):
        HybridDomObservation.model_validate(payload)

    with pytest.raises(ValidationError):
        HybridActionResult(
            session_id=current.session_id,
            action_id="act_missing_observation",
            modality="dom",
            action_type="wait",
            success=True,
            terminal=False,
            message="Non-terminal result must carry a refreshed observation",
        )
    with pytest.raises(ValidationError):
        HybridActionResult(
            session_id=current.session_id,
            action_id="act_terminal_observation",
            modality="dom",
            action_type="finish",
            success=True,
            terminal=True,
            message="Terminal result must release its observation",
            observation=current,
        )
