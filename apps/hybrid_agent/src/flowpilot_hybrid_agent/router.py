from dataclasses import dataclass

from flowpilot_hybrid_agent.schemas import (
    ActionSummary,
    HybridModality,
    HybridRouteSignals,
    RouteCategory,
    RouteDecision,
    RouteReasonCode,
)

_SAFE_DOM_SWITCH_ERRORS = {
    "invalid_url",
    "stale_reference",
    "unknown_reference",
    "action_not_allowed",
    "input_rejected",
    "browser_timeout",
    "browser_error",
}
_MAX_IMAGE_BYTES = 184_320
_MAX_IMAGE_PIXELS = 960 * 540
_MAX_CAPTURE_MS = 3_000
_FAKE_INPUT_TOKENS = 32
_FAKE_OUTPUT_TOKENS = 16


@dataclass(slots=True)
class RouterState:
    switch_count: int = 0
    successful_dom_probes: int = 0

    def note_action(self, action: ActionSummary) -> None:
        if action.modality == "dom" and action.action_type == "read" and action.success:
            self.successful_dom_probes += 1


@dataclass(frozen=True, slots=True)
class RouterBudget:
    remaining_steps: int
    remaining_model_calls: int
    remaining_dom_observations: int
    remaining_dom_observation_bytes: int
    remaining_compressed_dom_bytes: int
    remaining_images: int
    remaining_image_bytes: int
    remaining_image_pixels: int
    remaining_capture_ms: int
    remaining_input_tokens: int
    remaining_output_tokens: int
    remaining_cost_microusd: int
    remaining_duration_seconds: int
    max_switches: int

    def can_request_vision(self) -> bool:
        return (
            self.remaining_steps > 0
            and self.remaining_model_calls > 0
            and self.remaining_dom_observations >= 0
            and self.remaining_dom_observation_bytes >= 0
            and self.remaining_compressed_dom_bytes >= 0
            and self.remaining_images > 0
            and self.remaining_image_bytes >= _MAX_IMAGE_BYTES
            and self.remaining_image_pixels >= _MAX_IMAGE_PIXELS
            and self.remaining_capture_ms >= _MAX_CAPTURE_MS
            and self.remaining_input_tokens >= _FAKE_INPUT_TOKENS
            and self.remaining_output_tokens >= _FAKE_OUTPUT_TOKENS
            and self.remaining_cost_microusd >= 0
            and self.remaining_duration_seconds > _MAX_CAPTURE_MS // 1_000
        )


class DeterministicRouter:
    """Closed W6 DOM-first policy with no cross-task state."""

    def decide(
        self,
        current_modality: HybridModality,
        route_signals: HybridRouteSignals,
        route_category: RouteCategory,
        last_action: ActionSummary | None,
        state: RouterState,
        budget: RouterBudget,
    ) -> RouteDecision:
        if current_modality == "vision":
            return self._decision("vision", "vision", "vision_retained", state.switch_count)

        should_switch, reason = self._should_switch(
            route_signals,
            route_category,
            last_action,
            state,
        )
        if not should_switch:
            return self._decision("dom", "dom", reason, state.switch_count)
        if state.switch_count >= min(1, budget.max_switches):
            return self._decision("dom", "dom", "switch_limit_reached", state.switch_count)
        if not budget.can_request_vision():
            return self._decision("dom", "dom", "switch_refused_budget", state.switch_count)
        state.switch_count += 1
        return self._decision("dom", "vision", reason, state.switch_count)

    @staticmethod
    def _should_switch(
        route_signals: HybridRouteSignals,
        route_category: RouteCategory,
        last_action: ActionSummary | None,
        state: RouterState,
    ) -> tuple[bool, RouteReasonCode]:
        if route_signals.dom_structure in {"empty", "truncated"}:
            return True, "dom_structure_weak"
        if route_signals.last_action_error_category in _SAFE_DOM_SWITCH_ERRORS:
            return True, "dom_action_failure"
        if route_category == "visual_recovery" and state.successful_dom_probes >= 1:
            return True, "trusted_visual_recovery"
        if last_action is None:
            return False, "dom_default"
        return False, "dom_usable"

    @staticmethod
    def _decision(
        from_modality: HybridModality,
        to_modality: HybridModality,
        reason_code: RouteReasonCode,
        switch_count: int,
    ) -> RouteDecision:
        return RouteDecision(
            from_modality=from_modality,
            to_modality=to_modality,
            reason_code=reason_code,
            switched=from_modality != to_modality,
            switch_count=switch_count,
        )
