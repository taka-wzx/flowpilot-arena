from flowpilot_hybrid_agent.router import DeterministicRouter, RouterBudget, RouterState
from flowpilot_hybrid_agent.schemas import ActionSummary, HybridRouteSignals


def router_budget(**overrides: int) -> RouterBudget:
    values = {
        "remaining_steps": 10,
        "remaining_model_calls": 10,
        "remaining_dom_observations": 10,
        "remaining_dom_observation_bytes": 100_000,
        "remaining_compressed_dom_bytes": 100_000,
        "remaining_images": 10,
        "remaining_image_bytes": 1_000_000,
        "remaining_image_pixels": 10 * 960 * 540,
        "remaining_capture_ms": 10_000,
        "remaining_input_tokens": 100,
        "remaining_output_tokens": 100,
        "remaining_cost_microusd": 0,
        "remaining_duration_seconds": 10,
        "max_switches": 2,
    }
    values.update(overrides)
    return RouterBudget(**values)


def usable_signals() -> HybridRouteSignals:
    return HybridRouteSignals(
        dom_structure="usable",
        dom_interactive_count=2,
        dom_observation_bytes=512,
    )


def test_router_starts_dom_first_and_switches_only_for_closed_conditions() -> None:
    router = DeterministicRouter()
    state = RouterState()
    initial = router.decide("dom", usable_signals(), "standard", None, state, router_budget())
    assert initial.to_modality == "dom"
    assert initial.reason_code == "dom_default"

    weak = router.decide(
        "dom",
        usable_signals().model_copy(update={"dom_structure": "truncated"}),
        "standard",
        None,
        state,
        router_budget(),
    )
    assert weak.switched is True
    assert weak.to_modality == "vision"
    assert weak.reason_code == "dom_structure_weak"
    assert weak.switch_count == 1

    vision = router.decide("vision", usable_signals(), "standard", None, state, router_budget())
    assert vision.to_modality == "vision"
    assert vision.reason_code == "vision_retained"


def test_router_uses_safe_action_outcome_or_trusted_category_and_refuses_budget_bypass() -> None:
    router = DeterministicRouter()
    state = RouterState()
    failure = ActionSummary(
        modality="dom",
        action_type="read",
        success=False,
        error_category="stale_hybrid_ref",
    )
    failure_signals = usable_signals().model_copy(
        update={"last_action_error_category": "stale_reference"}
    )
    routed = router.decide("dom", failure_signals, "standard", failure, state, router_budget())
    assert routed.switched is True
    assert routed.reason_code == "dom_action_failure"

    recovery_state = RouterState()
    recovery_state.note_action(ActionSummary(modality="dom", action_type="read", success=True))
    recovery = router.decide(
        "dom",
        usable_signals(),
        "visual_recovery",
        recovery_state_action := ActionSummary(modality="dom", action_type="read", success=True),
        recovery_state,
        router_budget(),
    )
    assert recovery_state_action.success is True
    assert recovery.switched is True
    assert recovery.reason_code == "trusted_visual_recovery"

    denied = router.decide(
        "dom",
        usable_signals().model_copy(update={"dom_structure": "empty"}),
        "standard",
        None,
        RouterState(),
        router_budget(remaining_images=0),
    )
    assert denied.switched is False
    assert denied.reason_code == "switch_refused_budget"


def test_router_requires_a_successful_read_probe_and_full_visual_envelope_budget() -> None:
    router = DeterministicRouter()
    state = RouterState()
    state.note_action(ActionSummary(modality="dom", action_type="fill", success=True))
    retained = router.decide(
        "dom",
        usable_signals(),
        "visual_recovery",
        ActionSummary(modality="dom", action_type="fill", success=True),
        state,
        router_budget(),
    )
    assert retained.switched is False
    assert retained.reason_code == "dom_usable"

    state.note_action(ActionSummary(modality="dom", action_type="read", success=True))
    for constrained in (
        {"remaining_image_bytes": 184_319},
        {"remaining_image_pixels": 518_399},
        {"remaining_capture_ms": 2_999},
        {"remaining_input_tokens": 31},
        {"remaining_output_tokens": 15},
        {"remaining_duration_seconds": 3},
    ):
        refused = router.decide(
            "dom",
            usable_signals(),
            "visual_recovery",
            ActionSummary(modality="dom", action_type="read", success=True),
            RouterState(successful_dom_probes=1),
            router_budget(**constrained),
        )
        assert refused.switched is False
        assert refused.reason_code == "switch_refused_budget"
