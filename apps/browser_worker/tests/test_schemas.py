import json

import pytest
from pydantic import TypeAdapter, ValidationError

from flowpilot_browser_worker.schemas import (
    BrowserAction,
    HybridActionEnvelope,
    HybridObservationRequest,
    Observation,
)


def test_action_union_accepts_typed_navigation() -> None:
    action = TypeAdapter(BrowserAction).validate_python(
        {
            "schema_version": "w4-dom-action/1.0",
            "action_id": "act_nav_1",
            "type": "navigate",
            "url": "/hris",
        }
    )
    assert action.type == "navigate"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("selector", "#submit"),
        ("xpath", "//button"),
        ("javascript", "document.cookie"),
        ("playwright", "page.click('button')"),
        ("shell", "whoami"),
        ("sql", "select * from users"),
        ("file_path", "/etc/passwd"),
        ("eval", "1+1"),
    ],
)
def test_action_union_rejects_arbitrary_execution_fields(field: str, value: str) -> None:
    payload = {
        "schema_version": "w4-dom-action/1.0",
        "action_id": "act_nav_1",
        "type": "navigate",
        "url": "/hris",
        field: value,
    }
    with pytest.raises(ValidationError):
        TypeAdapter(BrowserAction).validate_python(payload)


def test_action_union_rejects_unknown_action_and_wrong_types() -> None:
    adapter = TypeAdapter(BrowserAction)
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "schema_version": "w4-dom-action/1.0",
                "action_id": "act_bad_1",
                "type": "upload",
                "path": "x",
            }
        )
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "schema_version": "w4-dom-action/1.0",
                "action_id": "act_wait_1",
                "type": "wait",
                "duration_ms": "100",
            }
        )


def test_observation_schema_contains_no_visual_or_execution_surface() -> None:
    schema = json.dumps(Observation.model_json_schema(), sort_keys=True).lower()
    for prohibited in (
        "screenshot",
        "image_path",
        "pixel",
        "ocr",
        "vlm",
        "selector",
        "javascript",
        "cookie",
        "local_storage",
    ):
        assert prohibited not in schema


def test_hybrid_envelope_requires_a_declared_current_modality_and_no_coordinates() -> None:
    adapter = TypeAdapter(HybridActionEnvelope)
    action = adapter.validate_python(
        {
            "schema_version": "w6-hybrid-action-envelope/1.0",
            "session_id": "bw_abcdefghijklmnop",
            "generation": 1,
            "modality": "dom",
            "action": {
                "action_id": "act_hybrid_read",
                "type": "read",
                "observation_id": "obs_abcdefgh",
                "element_ref": "ref_abcdefgh",
            },
        }
    )
    assert action.modality == "dom"
    for missing in ("session_id", "generation"):
        payload = {
            "schema_version": "w6-hybrid-action-envelope/1.0",
            "session_id": "bw_abcdefghijklmnop",
            "generation": 1,
            "modality": "dom",
            "action": {
                "action_id": "act_hybrid_read",
                "type": "read",
                "observation_id": "obs_abcdefgh",
                "element_ref": "ref_abcdefgh",
            },
        }
        payload.pop(missing)
        with pytest.raises(ValidationError):
            adapter.validate_python(payload)
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "schema_version": "w6-hybrid-action-envelope/1.0",
                "session_id": "bw_abcdefghijklmnop",
                "generation": 1,
                "modality": "vision",
                "action": {
                    "action_id": "act_hybrid_bad",
                    "type": "read",
                    "observation_id": "vobs_abcdefgh",
                    "screenshot_ref": "shot_abcdefgh",
                    "grounding_ref": "gref_abcdefgh",
                    "x": 4,
                },
            }
        )
    with pytest.raises(ValidationError):
        HybridObservationRequest.model_validate({"modality": "dom", "selector": "#unsafe"})
