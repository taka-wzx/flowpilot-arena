import hashlib
import json
from collections.abc import Callable
from contextlib import suppress
from time import monotonic

from pydantic import ValidationError

from flowpilot_vision_agent.client import BrowserWorkerClient
from flowpilot_vision_agent.model import (
    ModelCallError,
    VisionModelClient,
    VisionModelContext,
)
from flowpilot_vision_agent.schemas import (
    ActionSummary,
    ModelUsage,
    TaskId,
    VisionActionResult,
    VisionAgentBudget,
    VisionAgentRunResult,
    VisionBrowserAction,
    VisionFailAction,
    VisionFillAction,
    VisionFinishAction,
    VisionModelDecision,
    VisionNavigateAction,
    VisionObservation,
    VisionRunStatus,
    VisionSelectAction,
    VisionWaitAction,
)

MAX_PRIOR_ACTION_SUMMARIES = 24


class VisionAgentLoop:
    def __init__(
        self,
        browser: BrowserWorkerClient,
        model: VisionModelClient,
        *,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._browser = browser
        self._model = model
        self._clock = clock

    async def run(
        self,
        task_id: TaskId,
        instruction: str,
        budget: VisionAgentBudget,
    ) -> VisionAgentRunResult:
        started = self._clock()
        actions: list[ActionSummary] = []
        context_history: list[str] = []
        model_calls = 0
        input_tokens = 0
        output_tokens = 0
        cost_microusd = 0
        steps = 0
        image_count = 0
        image_bytes = 0
        image_pixels = 0
        capture_duration_ms = 0
        session_id: str | None = None
        try:
            created = await self._browser.create_session()
            session_id = created.session_id
            observation = created.observation
        except Exception:
            return self._result(
                task_id,
                "browser_error",
                "Unable to create an isolated visual Browser Worker session",
                steps,
                model_calls,
                image_count,
                image_bytes,
                image_pixels,
                capture_duration_ms,
                input_tokens,
                output_tokens,
                cost_microusd,
                actions,
            )

        image_count, image_bytes, image_pixels, capture_duration_ms = self._add_image(
            observation,
            image_count,
            image_bytes,
            image_pixels,
            capture_duration_ms,
        )
        initial_budget = self._image_budget_status(
            image_count,
            image_bytes,
            image_pixels,
            capture_duration_ms,
            budget,
        )
        if initial_budget is not None:
            await self._safe_close(session_id)
            return self._result(
                task_id,
                initial_budget[0],
                initial_budget[1],
                steps,
                model_calls,
                image_count,
                image_bytes,
                image_pixels,
                capture_duration_ms,
                input_tokens,
                output_tokens,
                cost_microusd,
                actions,
            )

        previous_signature: str | None = None
        repeated = 0
        no_progress = 0
        prior_fingerprint = self._observation_fingerprint(observation)

        while steps < budget.max_steps:
            terminal = self._pre_call_budget_status(
                started,
                model_calls,
                input_tokens,
                output_tokens,
                cost_microusd,
                budget,
            )
            if terminal is not None:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    terminal[0],
                    terminal[1],
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

            context = VisionModelContext(
                task_id=task_id,
                instruction=instruction,
                observation=observation,
                prior_actions=tuple(context_history[-MAX_PRIOR_ACTION_SUMMARIES:]),
                remaining_steps=budget.max_steps - steps,
                remaining_model_calls=budget.max_model_calls - model_calls,
                remaining_images=budget.max_images - image_count,
                remaining_image_bytes=budget.max_image_bytes - image_bytes,
                remaining_image_pixels=budget.max_image_pixels - image_pixels,
                remaining_capture_ms=budget.max_capture_ms - capture_duration_ms,
                remaining_input_tokens=budget.max_input_tokens - input_tokens,
                remaining_output_tokens=budget.max_output_tokens - output_tokens,
                remaining_cost_microusd=budget.max_cost_microusd - cost_microusd,
            )
            try:
                response = await self._model.complete(context)
            except ModelCallError as exc:
                model_calls, input_tokens, output_tokens, cost_microusd = self._apply_error_usage(
                    exc.usage,
                    model_calls,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                )
                await self._safe_close(session_id)
                post_call = self._post_call_budget_status(
                    started, input_tokens, output_tokens, cost_microusd, budget
                )
                if post_call is not None:
                    return self._result(
                        task_id,
                        post_call[0],
                        post_call[1],
                        steps,
                        model_calls,
                        image_count,
                        image_bytes,
                        image_pixels,
                        capture_duration_ms,
                        input_tokens,
                        output_tokens,
                        cost_microusd,
                        actions,
                    )
                return self._result(
                    task_id,
                    "model_error",
                    exc.safe_reason,
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )
            except Exception:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "model_error",
                    "Vision model call failed and the browser session was closed",
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

            model_calls += 1
            input_tokens += response.usage.input_tokens
            output_tokens += response.usage.output_tokens
            cost_microusd += response.usage.cost_microusd
            post_call = self._post_call_budget_status(
                started, input_tokens, output_tokens, cost_microusd, budget
            )
            if post_call is not None:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    post_call[0],
                    post_call[1],
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

            try:
                decision = VisionModelDecision.model_validate_json(response.content)
            except ValidationError:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "invalid_model_output",
                    "Vision model output was not valid strict action JSON",
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
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
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

            try:
                result = await self._browser.execute_action(session_id, decision.action)
            except Exception:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "browser_error",
                    "Browser Worker rejected or failed the typed visual action",
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

            steps += 1
            actions.append(
                ActionSummary(
                    action_id=result.action_id,
                    action_type=result.action_type,
                    success=result.success,
                    error_category=result.error_category,
                    message=result.message[:160],
                )
            )
            context_history.append(self._context_action_summary(decision.action, result))
            if result.terminal:
                status, reason = self._terminal_action_status(decision.action, result.message)
                return self._result(
                    task_id,
                    status,
                    reason,
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )
            if result.observation is None:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "browser_error",
                    "Non-terminal Browser Worker result omitted its visual observation",
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

            observation = result.observation
            image_count, image_bytes, image_pixels, capture_duration_ms = self._add_image(
                observation,
                image_count,
                image_bytes,
                image_pixels,
                capture_duration_ms,
            )
            image_budget = self._image_budget_status(
                image_count,
                image_bytes,
                image_pixels,
                capture_duration_ms,
                budget,
            )
            if image_budget is not None:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    image_budget[0],
                    image_budget[1],
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

            fingerprint = self._observation_fingerprint(observation)
            hidden_form_progress = result.success and isinstance(
                decision.action, (VisionFillAction, VisionSelectAction)
            )
            no_progress = (
                0 if hidden_form_progress or fingerprint != prior_fingerprint else no_progress + 1
            )
            prior_fingerprint = fingerprint
            if no_progress > budget.max_no_progress:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "no_progress_limit",
                    "Visual observation made no progress for too many actions",
                    steps,
                    model_calls,
                    image_count,
                    image_bytes,
                    image_pixels,
                    capture_duration_ms,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

        await self._safe_close(session_id)
        return self._result(
            task_id,
            "step_budget_exhausted",
            "Vision Agent exhausted its step budget",
            steps,
            model_calls,
            image_count,
            image_bytes,
            image_pixels,
            capture_duration_ms,
            input_tokens,
            output_tokens,
            cost_microusd,
            actions,
        )

    def _pre_call_budget_status(
        self,
        started: float,
        model_calls: int,
        input_tokens: int,
        output_tokens: int,
        cost_microusd: int,
        budget: VisionAgentBudget,
    ) -> tuple[VisionRunStatus, str] | None:
        if self._clock() - started > budget.max_duration_seconds:
            return "time_budget_exhausted", "Vision Agent exceeded its wall-time budget"
        if model_calls >= budget.max_model_calls:
            return "model_call_budget_exhausted", "Vision Agent exhausted its model-call budget"
        if input_tokens >= budget.max_input_tokens:
            return "input_token_budget_exhausted", "Vision Agent exhausted its input-token budget"
        if output_tokens >= budget.max_output_tokens:
            return "output_token_budget_exhausted", "Vision Agent exhausted its output-token budget"
        if cost_microusd > budget.max_cost_microusd:
            return "cost_budget_exhausted", "Vision Agent exceeded its cost budget"
        return None

    def _post_call_budget_status(
        self,
        started: float,
        input_tokens: int,
        output_tokens: int,
        cost_microusd: int,
        budget: VisionAgentBudget,
    ) -> tuple[VisionRunStatus, str] | None:
        if self._clock() - started > budget.max_duration_seconds:
            return "time_budget_exhausted", "Vision Agent exceeded its wall-time budget"
        if input_tokens > budget.max_input_tokens:
            return (
                "input_token_budget_exhausted",
                "Vision model response exceeded input-token budget",
            )
        if output_tokens > budget.max_output_tokens:
            return (
                "output_token_budget_exhausted",
                "Vision model response exceeded output-token budget",
            )
        if cost_microusd > budget.max_cost_microusd:
            return "cost_budget_exhausted", "Vision model response exceeded cost budget"
        return None

    @staticmethod
    def _image_budget_status(
        image_count: int,
        image_bytes: int,
        image_pixels: int,
        capture_duration_ms: int,
        budget: VisionAgentBudget,
    ) -> tuple[VisionRunStatus, str] | None:
        if image_count > budget.max_images:
            return "image_budget_exhausted", "Vision Agent exhausted its image budget"
        if image_bytes > budget.max_image_bytes:
            return "image_byte_budget_exhausted", "Vision Agent exceeded its image-byte budget"
        if image_pixels > budget.max_image_pixels:
            return "image_pixel_budget_exhausted", "Vision Agent exceeded its image-pixel budget"
        if capture_duration_ms > budget.max_capture_ms:
            return "capture_time_budget_exhausted", "Vision Agent exceeded capture-time budget"
        return None

    @staticmethod
    def _add_image(
        observation: VisionObservation,
        image_count: int,
        image_bytes: int,
        image_pixels: int,
        capture_duration_ms: int,
    ) -> tuple[int, int, int, int]:
        return (
            image_count + 1,
            image_bytes + observation.image_bytes,
            image_pixels + observation.image_width * observation.image_height,
            capture_duration_ms + observation.capture_duration_ms,
        )

    @staticmethod
    def _apply_error_usage(
        usage: ModelUsage | None,
        model_calls: int,
        input_tokens: int,
        output_tokens: int,
        cost_microusd: int,
    ) -> tuple[int, int, int, int]:
        if usage is None:
            return model_calls, input_tokens, output_tokens, cost_microusd
        return (
            model_calls + 1,
            input_tokens + usage.input_tokens,
            output_tokens + usage.output_tokens,
            cost_microusd + usage.cost_microusd,
        )

    async def _safe_close(self, session_id: str) -> None:
        with suppress(Exception):
            await self._browser.close_session(session_id)

    @staticmethod
    def _terminal_action_status(
        action: VisionBrowserAction, message: str
    ) -> tuple[VisionRunStatus, str]:
        if isinstance(action, VisionFinishAction):
            return (
                "finished_ungraded",
                "Vision Agent finished; an independent W3 grade is still required",
            )
        if isinstance(action, VisionFailAction) and action.category == "escalated":
            return "escalated", message or "Vision Agent escalated"
        return "failed", message or "Vision Agent failed"

    @staticmethod
    def _action_signature(action: VisionBrowserAction) -> str:
        payload = action.model_dump(
            mode="json",
            exclude={"action_id", "observation_id", "screenshot_ref", "grounding_ref"},
        )
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _context_action_summary(action: VisionBrowserAction, result: VisionActionResult) -> str:
        if isinstance(action, VisionNavigateAction):
            target = action.url
        elif isinstance(action, VisionWaitAction):
            target = f"{action.duration_ms}ms"
        elif isinstance(action, VisionFinishAction):
            target = "finish"
        elif isinstance(action, VisionFailAction):
            target = action.category
        else:
            target = "grounded element"
        payload = {
            "action": action.type,
            "target": target,
            "success": result.success,
            "error_category": result.error_category,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _observation_fingerprint(observation: VisionObservation) -> str:
        image_digest = hashlib.sha256(observation.image_base64.encode("ascii")).hexdigest()
        payload = {
            "image_digest": image_digest,
            "width": observation.image_width,
            "height": observation.image_height,
            "groundings": [
                {
                    "bounds": grounding.bounds.model_dump(),
                    "actions": grounding.allowed_actions,
                }
                for grounding in observation.groundings
            ],
            "error": observation.page_error,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _result(
        task_id: TaskId,
        status: VisionRunStatus,
        reason: str,
        steps: int,
        model_calls: int,
        image_count: int,
        image_bytes: int,
        image_pixels: int,
        capture_duration_ms: int,
        input_tokens: int,
        output_tokens: int,
        cost_microusd: int,
        actions: list[ActionSummary],
    ) -> VisionAgentRunResult:
        return VisionAgentRunResult(
            task_id=task_id,
            status=status,
            terminal_reason=reason[:300],
            steps=steps,
            action_count=len(actions),
            model_calls=model_calls,
            image_count=image_count,
            image_bytes=image_bytes,
            image_pixels=image_pixels,
            capture_duration_ms=capture_duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_microusd=cost_microusd,
            actions=tuple(actions),
        )
