from typing import Literal

from flowpilot_browser_worker.schemas import (
    HybridDomObservation,
    HybridRouteSignals,
    HybridVisionObservation,
    Observation,
    SafeRouteErrorCategory,
    VisionObservation,
)


def safe_route_error(category: str | None) -> SafeRouteErrorCategory | None:
    if category is None:
        return None
    if category in {"stale_element_ref", "stale_visual_ref"}:
        return "stale_reference"
    if category in {"unknown_element_ref", "unknown_visual_ref"}:
        return "unknown_reference"
    if category == "action_not_allowed":
        return "action_not_allowed"
    if category == "invalid_url":
        return "invalid_url"
    if category == "input_rejected":
        return "input_rejected"
    if category == "browser_timeout":
        return "browser_timeout"
    if category in {"browser_error", "internal_error", "session_closed"}:
        return "browser_error"
    return "budget_exhausted"


def dom_route_signals(observation: Observation) -> HybridRouteSignals:
    serialized_bytes = len(observation.model_dump_json().encode("utf-8"))
    interactive_count = sum(
        1
        for element in observation.interactive_elements
        if not element.state.disabled and bool(element.allowed_actions)
    )
    structure: Literal["usable", "empty", "truncated"]
    if observation.truncated:
        structure = "truncated"
    elif interactive_count == 0:
        structure = "empty"
    else:
        structure = "usable"
    return HybridRouteSignals(
        dom_structure=structure,
        dom_interactive_count=interactive_count,
        dom_observation_bytes=serialized_bytes,
        last_action_error_category=safe_route_error(
            observation.last_action.error_category if observation.last_action else None
        ),
    )


def hybrid_dom_observation(
    observation: Observation,
    generation: int,
) -> HybridDomObservation:
    return HybridDomObservation(
        session_id=observation.session_id,
        generation=generation,
        observation=observation,
        route_signals=dom_route_signals(observation),
    )


def hybrid_vision_observation(
    observation: VisionObservation,
    generation: int,
    previous_route_signals: HybridRouteSignals,
) -> HybridVisionObservation:
    route_signals = previous_route_signals.model_copy(
        update={
            "last_action_error_category": safe_route_error(
                observation.last_action.error_category if observation.last_action else None
            )
        }
    )
    return HybridVisionObservation(
        session_id=observation.session_id,
        generation=generation,
        observation=observation,
        route_signals=route_signals,
    )
