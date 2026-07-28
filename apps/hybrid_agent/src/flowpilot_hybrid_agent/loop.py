import asyncio
import hashlib
import json
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from time import monotonic

from pydantic import ValidationError

from flowpilot_hybrid_agent.client import BrowserWorkerClient
from flowpilot_hybrid_agent.compressor import CompressionError, DeterministicDomCompressor
from flowpilot_hybrid_agent.model import (
    HybridModelClient,
    HybridModelContext,
    ModelCallError,
)
from flowpilot_hybrid_agent.router import DeterministicRouter, RouterBudget, RouterState
from flowpilot_hybrid_agent.schemas import (
    ActionSummary,
    CompressedObservation,
    CompressedVisualObservation,
    DomFailAction,
    DomFinishAction,
    HybridActionEnvelope,
    HybridAgentBudget,
    HybridAgentRunResult,
    HybridDomObservation,
    HybridModelDecision,
    HybridObservation,
    HybridRunStatus,
    ModelUsage,
    RouteCategory,
    RouteDecision,
    TaskId,
    VisionFailAction,
    VisionFinishAction,
)


@dataclass(slots=True)
class _RunState:
    actions: list[ActionSummary] = field(default_factory=list)
    routes: list[RouteDecision] = field(default_factory=list)
    model_calls: int = 0
    steps: int = 0
    dom_observation_count: int = 0
    dom_observation_bytes: int = 0
    compressed_dom_bytes: int = 0
    image_count: int = 0
    image_bytes: int = 0
    image_pixels: int = 0
    capture_duration_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_microusd: int = 0
    last_action: ActionSummary | None = None


class HybridAgentLoop:
    def __init__(
        self,
        browser: BrowserWorkerClient,
        model: HybridModelClient,
        *,
        router: DeterministicRouter | None = None,
        compressor: DeterministicDomCompressor | None = None,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._browser = browser
        self._model = model
        self._router = router or DeterministicRouter()
        self._compressor = compressor or DeterministicDomCompressor()
        self._clock = clock

    async def run(
        self,
        task_id: TaskId,
        instruction: str,
        route_category: RouteCategory,
        budget: HybridAgentBudget,
    ) -> HybridAgentRunResult:
        started = self._clock()
        state = _RunState()
        session_id: str | None = None
        try:
            created = await self._browser.create_session()
            session_id = created.session_id
            observation = created.observation
        except Exception:
            return self._result(
                task_id,
                "browser_error",
                "Unable to create an isolated Hybrid Browser Worker session",
                state,
                0,
            )

        observation_status = self._record_observation(observation, state, budget)
        if observation_status is not None:
            await self._safe_close(session_id)
            return self._result(task_id, *observation_status, state, 0)

        router_state = RouterState()
        previous_signature: str | None = None
        repeated = 0
        no_progress = 0
        prior_fingerprint = self._observation_fingerprint(observation)

        while state.steps < budget.max_steps:
            pre_call = self._pre_call_budget_status(started, state, budget)
            if pre_call is not None:
                await self._safe_close(session_id)
                return self._result(task_id, *pre_call, state, router_state.switch_count)

            route = self._router.decide(
                observation.modality,
                observation.route_signals,
                route_category,
                state.last_action,
                router_state,
                self._router_budget(started, state, budget),
            )
            state.routes.append(route)
            if route.reason_code in {"switch_limit_reached", "switch_refused_budget"}:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "switch_budget_exhausted",
                    "Hybrid Router refused a required modality switch within total budgets",
                    state,
                    router_state.switch_count,
                )
            if route.switched:
                try:
                    observation = await self._browser.request_observation(
                        session_id,
                        route.to_modality,
                    )
                except asyncio.CancelledError:
                    await self._safe_close(session_id)
                    raise
                except Exception:
                    await self._safe_close(session_id)
                    return self._result(
                        task_id,
                        "browser_error",
                        "Browser Worker could not switch the current Hybrid observation",
                        state,
                        router_state.switch_count,
                    )
                observation_status = self._record_observation(observation, state, budget)
                if observation_status is not None:
                    await self._safe_close(session_id)
                    return self._result(
                        task_id,
                        *observation_status,
                        state,
                        router_state.switch_count,
                    )

            try:
                model_observation = self._model_observation(observation, state, budget)
            except CompressionError as exc:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "compressed_dom_budget_exhausted",
                    str(exc),
                    state,
                    router_state.switch_count,
                )
            compressed_status = self._compressed_budget_status(state, budget)
            if compressed_status is not None:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    *compressed_status,
                    state,
                    router_state.switch_count,
                )

            context = HybridModelContext(
                task_id=task_id,
                instruction=instruction,
                observation=model_observation,
                prior_actions=self._compressor.compact_action_history(state.actions),
                remaining_steps=budget.max_steps - state.steps,
                remaining_model_calls=budget.max_model_calls - state.model_calls,
                remaining_switches=budget.max_switches - router_state.switch_count,
                remaining_dom_observations=budget.max_dom_observations
                - state.dom_observation_count,
                remaining_dom_observation_bytes=budget.max_dom_observation_bytes
                - state.dom_observation_bytes,
                remaining_compressed_dom_bytes=budget.max_compressed_dom_bytes
                - state.compressed_dom_bytes,
                remaining_images=budget.max_images - state.image_count,
                remaining_image_bytes=budget.max_image_bytes - state.image_bytes,
                remaining_image_pixels=budget.max_image_pixels - state.image_pixels,
                remaining_capture_ms=budget.max_capture_ms - state.capture_duration_ms,
                remaining_input_tokens=budget.max_input_tokens - state.input_tokens,
                remaining_output_tokens=budget.max_output_tokens - state.output_tokens,
                remaining_cost_microusd=budget.max_cost_microusd - state.cost_microusd,
            )
            try:
                state.model_calls += 1
                response = await self._model.complete(context)
            except asyncio.CancelledError:
                await self._safe_close(session_id)
                raise
            except ModelCallError as exc:
                self._apply_usage(exc.usage, state)
                await self._safe_close(session_id)
                post_call = self._post_call_budget_status(started, state, budget)
                if post_call is not None:
                    return self._result(task_id, *post_call, state, router_state.switch_count)
                return self._result(
                    task_id,
                    "model_error",
                    exc.safe_reason,
                    state,
                    router_state.switch_count,
                )
            except Exception:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "model_error",
                    "Hybrid model call failed and the browser session was closed",
                    state,
                    router_state.switch_count,
                )

            self._apply_usage(response.usage, state)
            post_call = self._post_call_budget_status(started, state, budget)
            if post_call is not None:
                await self._safe_close(session_id)
                return self._result(task_id, *post_call, state, router_state.switch_count)

            try:
                decision = HybridModelDecision.model_validate_json(response.content)
            except ValidationError:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "invalid_model_output",
                    "Hybrid model output was not valid strict action JSON",
                    state,
                    router_state.switch_count,
                )
            if decision.action.modality != observation.modality:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "invalid_model_output",
                    "Hybrid model action did not match the current selected modality",
                    state,
                    router_state.switch_count,
                )

            signature = self._action_signature(decision.action)
            if signature == previous_signature:
                repeated += 1
            else:
                repeated = 1
                previous_signature = signature
            if repeated > budget.max_repeated_actions:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "repeated_action_limit",
                    "Consecutive identical action limit reached",
                    state,
                    router_state.switch_count,
                )

            try:
                result = await self._browser.execute_action(session_id, decision.action)
            except asyncio.CancelledError:
                await self._safe_close(session_id)
                raise
            except Exception:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "browser_error",
                    "Browser Worker rejected or failed the typed Hybrid action",
                    state,
                    router_state.switch_count,
                )

            state.steps += 1
            summary = ActionSummary(
                modality=result.modality,
                action_type=result.action_type,
                success=result.success,
                error_category=result.error_category,
            )
            state.actions.append(summary)
            state.last_action = summary
            router_state.note_action(summary)

            if result.terminal:
                status, reason = self._terminal_action_status(decision.action, result.message)
                await self._safe_close(session_id)
                return self._result(task_id, status, reason, state, router_state.switch_count)
            if result.observation is None:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "browser_error",
                    "Non-terminal Browser Worker result omitted its current observation",
                    state,
                    router_state.switch_count,
                )

            observation = result.observation
            observation_status = self._record_observation(observation, state, budget)
            if observation_status is not None:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    *observation_status,
                    state,
                    router_state.switch_count,
                )

            fingerprint = self._observation_fingerprint(observation)
            hidden_form_progress = result.success and result.action_type in {"fill", "select"}
            no_progress = (
                0 if hidden_form_progress or fingerprint != prior_fingerprint else no_progress + 1
            )
            prior_fingerprint = fingerprint
            if no_progress > budget.max_no_progress:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "no_progress_limit",
                    "Current selected observation made no progress for too many actions",
                    state,
                    router_state.switch_count,
                )

        await self._safe_close(session_id)
        return self._result(
            task_id,
            "step_budget_exhausted",
            "Hybrid Agent exhausted its step budget",
            state,
            router_state.switch_count,
        )

    def _model_observation(
        self,
        observation: HybridObservation,
        state: _RunState,
        budget: HybridAgentBudget,
    ) -> CompressedObservation:
        if isinstance(observation, HybridDomObservation):
            compressed = self._compressor.compress(observation)
            state.compressed_dom_bytes += compressed.serialized_bytes
            if state.compressed_dom_bytes > budget.max_compressed_dom_bytes:
                raise CompressionError("Hybrid Agent exhausted its compressed DOM-byte budget")
            return compressed
        return CompressedVisualObservation(
            modality="vision",
            session_id=observation.session_id,
            generation=observation.generation,
            observation_id=observation.observation.observation_id,
            visual_observation=observation.observation,
        )

    @staticmethod
    def _record_observation(
        observation: HybridObservation,
        state: _RunState,
        budget: HybridAgentBudget,
    ) -> tuple[HybridRunStatus, str] | None:
        if isinstance(observation, HybridDomObservation):
            state.dom_observation_count += 1
            state.dom_observation_bytes += observation.route_signals.dom_observation_bytes
            if state.dom_observation_count > budget.max_dom_observations:
                return "dom_observation_budget_exhausted", "Hybrid Agent exhausted DOM observations"
            if state.dom_observation_bytes > budget.max_dom_observation_bytes:
                return (
                    "dom_observation_byte_budget_exhausted",
                    "Hybrid Agent exceeded DOM observation bytes",
                )
            return None
        image = observation.observation
        state.image_count += 1
        state.image_bytes += image.image_bytes
        state.image_pixels += image.image_width * image.image_height
        state.capture_duration_ms += image.capture_duration_ms
        if state.image_count > budget.max_images:
            return "image_budget_exhausted", "Hybrid Agent exhausted image observations"
        if state.image_bytes > budget.max_image_bytes:
            return "image_byte_budget_exhausted", "Hybrid Agent exceeded image bytes"
        if state.image_pixels > budget.max_image_pixels:
            return "image_pixel_budget_exhausted", "Hybrid Agent exceeded image pixels"
        if state.capture_duration_ms > budget.max_capture_ms:
            return "capture_time_budget_exhausted", "Hybrid Agent exceeded image capture time"
        return None

    @staticmethod
    def _compressed_budget_status(
        state: _RunState,
        budget: HybridAgentBudget,
    ) -> tuple[HybridRunStatus, str] | None:
        if state.compressed_dom_bytes > budget.max_compressed_dom_bytes:
            return "compressed_dom_budget_exhausted", "Hybrid Agent exceeded compressed DOM bytes"
        return None

    def _pre_call_budget_status(
        self,
        started: float,
        state: _RunState,
        budget: HybridAgentBudget,
    ) -> tuple[HybridRunStatus, str] | None:
        if self._clock() - started > budget.max_duration_seconds:
            return "time_budget_exhausted", "Hybrid Agent exceeded its wall-time budget"
        if state.model_calls >= budget.max_model_calls:
            return "model_call_budget_exhausted", "Hybrid Agent exhausted model calls"
        if state.input_tokens >= budget.max_input_tokens:
            return "input_token_budget_exhausted", "Hybrid Agent exhausted input tokens"
        if state.output_tokens >= budget.max_output_tokens:
            return "output_token_budget_exhausted", "Hybrid Agent exhausted output tokens"
        if state.cost_microusd > budget.max_cost_microusd:
            return "cost_budget_exhausted", "Hybrid Agent exceeded its cost budget"
        return None

    def _post_call_budget_status(
        self,
        started: float,
        state: _RunState,
        budget: HybridAgentBudget,
    ) -> tuple[HybridRunStatus, str] | None:
        if self._clock() - started > budget.max_duration_seconds:
            return "time_budget_exhausted", "Hybrid Agent exceeded its wall-time budget"
        if state.input_tokens > budget.max_input_tokens:
            return "input_token_budget_exhausted", "Hybrid model response exceeded input tokens"
        if state.output_tokens > budget.max_output_tokens:
            return "output_token_budget_exhausted", "Hybrid model response exceeded output tokens"
        if state.cost_microusd > budget.max_cost_microusd:
            return "cost_budget_exhausted", "Hybrid model response exceeded cost budget"
        return None

    def _router_budget(
        self,
        started: float,
        state: _RunState,
        budget: HybridAgentBudget,
    ) -> RouterBudget:
        elapsed = self._clock() - started
        return RouterBudget(
            remaining_steps=budget.max_steps - state.steps,
            remaining_model_calls=budget.max_model_calls - state.model_calls,
            remaining_dom_observations=budget.max_dom_observations - state.dom_observation_count,
            remaining_dom_observation_bytes=budget.max_dom_observation_bytes
            - state.dom_observation_bytes,
            remaining_compressed_dom_bytes=budget.max_compressed_dom_bytes
            - state.compressed_dom_bytes,
            remaining_images=budget.max_images - state.image_count,
            remaining_image_bytes=budget.max_image_bytes - state.image_bytes,
            remaining_image_pixels=budget.max_image_pixels - state.image_pixels,
            remaining_capture_ms=budget.max_capture_ms - state.capture_duration_ms,
            remaining_input_tokens=budget.max_input_tokens - state.input_tokens,
            remaining_output_tokens=budget.max_output_tokens - state.output_tokens,
            remaining_cost_microusd=budget.max_cost_microusd - state.cost_microusd,
            remaining_duration_seconds=max(0, int(budget.max_duration_seconds - elapsed)),
            max_switches=budget.max_switches,
        )

    @staticmethod
    def _apply_usage(usage: ModelUsage | None, state: _RunState) -> None:
        if usage is None:
            return
        state.input_tokens += usage.input_tokens
        state.output_tokens += usage.output_tokens
        state.cost_microusd += usage.cost_microusd

    async def _safe_close(self, session_id: str | None) -> None:
        if session_id is None:
            return
        with suppress(Exception):
            await self._browser.close_session(session_id)

    @staticmethod
    def _terminal_action_status(
        action: HybridActionEnvelope,
        message: str,
    ) -> tuple[HybridRunStatus, str]:
        if isinstance(action.action, (DomFinishAction, VisionFinishAction)):
            return "finished_ungraded", "Hybrid Agent finished; an independent W3 grade is required"
        if (
            isinstance(action.action, (DomFailAction, VisionFailAction))
            and action.action.category == "escalated"
        ):
            return "escalated", message or "Hybrid Agent escalated"
        return "failed", message or "Hybrid Agent failed"

    @staticmethod
    def _action_signature(action: HybridActionEnvelope) -> str:
        payload = action.action.model_dump(
            mode="json",
            exclude={
                "action_id",
                "observation_id",
                "element_ref",
                "screenshot_ref",
                "grounding_ref",
            },
        )
        return json.dumps(
            {"modality": action.modality, "action": payload},
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _observation_fingerprint(observation: HybridObservation) -> str:
        if isinstance(observation, HybridDomObservation):
            payload = {
                "modality": "dom",
                "structure": observation.route_signals.dom_structure,
                "interactive": [
                    {
                        "role": element.role,
                        "actions": element.allowed_actions,
                        "disabled": element.state.disabled,
                    }
                    for element in observation.observation.interactive_elements
                ],
                "truncated": observation.observation.truncated,
                "error": observation.route_signals.last_action_error_category,
            }
        else:
            visual = observation.observation
            payload = {
                "modality": "vision",
                "image_digest": hashlib.sha256(visual.image_base64.encode("ascii")).hexdigest(),
                "groundings": [
                    {
                        "bounds": grounding.bounds.model_dump(),
                        "actions": grounding.allowed_actions,
                    }
                    for grounding in visual.groundings
                ],
                "error": visual.page_error,
            }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _result(
        task_id: TaskId,
        status: HybridRunStatus,
        reason: str,
        state: _RunState,
        switches: int,
    ) -> HybridAgentRunResult:
        return HybridAgentRunResult(
            task_id=task_id,
            status=status,
            terminal_reason=reason[:300],
            steps=state.steps,
            action_count=len(state.actions),
            model_calls=state.model_calls,
            switches=switches,
            dom_observation_count=state.dom_observation_count,
            dom_observation_bytes=state.dom_observation_bytes,
            compressed_dom_bytes=state.compressed_dom_bytes,
            image_count=state.image_count,
            image_bytes=state.image_bytes,
            image_pixels=state.image_pixels,
            capture_duration_ms=state.capture_duration_ms,
            input_tokens=state.input_tokens,
            output_tokens=state.output_tokens,
            cost_microusd=state.cost_microusd,
            routes=tuple(state.routes),
            actions=tuple(state.actions),
        )
