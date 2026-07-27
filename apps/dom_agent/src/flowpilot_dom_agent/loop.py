import json
from collections.abc import Callable
from contextlib import suppress
from time import monotonic

from pydantic import ValidationError

from flowpilot_dom_agent.client import BrowserWorkerClient
from flowpilot_dom_agent.model import ModelCallError, ModelClient, ModelContext
from flowpilot_dom_agent.schemas import (
    ActionResult,
    ActionSummary,
    AgentBudget,
    AgentRunResult,
    BrowserAction,
    ClickAction,
    FailAction,
    FillAction,
    FinishAction,
    ModelDecision,
    NavigateAction,
    Observation,
    ReadAction,
    RunStatus,
    ScrollAction,
    SelectAction,
    TaskId,
    WaitAction,
)

MAX_PRIOR_ACTION_SUMMARIES = 24


class AgentLoop:
    def __init__(
        self,
        browser: BrowserWorkerClient,
        model: ModelClient,
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
        budget: AgentBudget,
    ) -> AgentRunResult:
        started = self._clock()
        actions: list[ActionSummary] = []
        context_history: list[str] = []
        model_calls = 0
        input_tokens = 0
        output_tokens = 0
        cost_microusd = 0
        steps = 0
        session_id: str | None = None
        try:
            created = await self._browser.create_session()
            session_id = created.session_id
            observation = created.observation
        except Exception:
            return self._result(
                task_id,
                "browser_error",
                "Unable to create an isolated Browser Worker session",
                steps,
                model_calls,
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
                started, model_calls, input_tokens, output_tokens, cost_microusd, budget
            )
            if terminal is not None:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    terminal[0],
                    terminal[1],
                    steps,
                    model_calls,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

            context = ModelContext(
                task_id=task_id,
                instruction=instruction,
                observation=observation,
                prior_actions=tuple(context_history[-MAX_PRIOR_ACTION_SUMMARIES:]),
                remaining_steps=budget.max_steps - steps,
                remaining_model_calls=budget.max_model_calls - model_calls,
                remaining_input_tokens=budget.max_input_tokens - input_tokens,
                remaining_output_tokens=budget.max_output_tokens - output_tokens,
                remaining_cost_microusd=budget.max_cost_microusd - cost_microusd,
            )
            try:
                response = await self._model.complete(context)
            except ModelCallError as exc:
                if exc.usage is not None:
                    model_calls += 1
                    input_tokens += exc.usage.input_tokens
                    output_tokens += exc.usage.output_tokens
                    cost_microusd += exc.usage.cost_microusd
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
                    "Model call failed and the browser session was closed",
                    steps,
                    model_calls,
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
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

            try:
                decision = ModelDecision.model_validate_json(response.content)
            except ValidationError:
                await self._safe_close(session_id)
                return self._result(
                    task_id,
                    "invalid_model_output",
                    "Model output was not valid strict action JSON",
                    steps,
                    model_calls,
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
                    "Browser Worker rejected or failed the typed action",
                    steps,
                    model_calls,
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
            context_history.append(
                self._context_action_summary(decision.action, observation, result)
            )
            if result.terminal:
                status, reason = self._terminal_action_status(decision.action, result.message)
                return self._result(
                    task_id,
                    status,
                    reason,
                    steps,
                    model_calls,
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
                    "Non-terminal Browser Worker result omitted its observation",
                    steps,
                    model_calls,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

            observation = result.observation
            fingerprint = self._observation_fingerprint(observation)
            hidden_form_progress = result.success and isinstance(
                decision.action, (FillAction, SelectAction)
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
                    "Observation state made no progress for too many actions",
                    steps,
                    model_calls,
                    input_tokens,
                    output_tokens,
                    cost_microusd,
                    actions,
                )

        await self._safe_close(session_id)
        return self._result(
            task_id,
            "step_budget_exhausted",
            "Agent exhausted its step budget",
            steps,
            model_calls,
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
        budget: AgentBudget,
    ) -> tuple[RunStatus, str] | None:
        if self._clock() - started > budget.max_duration_seconds:
            return "time_budget_exhausted", "Agent exceeded its wall-time budget"
        if model_calls >= budget.max_model_calls:
            return "model_call_budget_exhausted", "Agent exhausted its model-call budget"
        if input_tokens >= budget.max_input_tokens:
            return "input_token_budget_exhausted", "Agent exhausted its input-token budget"
        if output_tokens >= budget.max_output_tokens:
            return "output_token_budget_exhausted", "Agent exhausted its output-token budget"
        if cost_microusd > budget.max_cost_microusd:
            return "cost_budget_exhausted", "Agent exceeded its cost budget"
        return None

    def _post_call_budget_status(
        self,
        started: float,
        input_tokens: int,
        output_tokens: int,
        cost_microusd: int,
        budget: AgentBudget,
    ) -> tuple[RunStatus, str] | None:
        if self._clock() - started > budget.max_duration_seconds:
            return "time_budget_exhausted", "Agent exceeded its wall-time budget"
        if input_tokens > budget.max_input_tokens:
            return "input_token_budget_exhausted", "Model response exceeded input-token budget"
        if output_tokens > budget.max_output_tokens:
            return "output_token_budget_exhausted", "Model response exceeded output-token budget"
        if cost_microusd > budget.max_cost_microusd:
            return "cost_budget_exhausted", "Model response exceeded cost budget"
        return None

    async def _safe_close(self, session_id: str) -> None:
        with suppress(Exception):
            await self._browser.close_session(session_id)

    @staticmethod
    def _terminal_action_status(action: BrowserAction, message: str) -> tuple[RunStatus, str]:
        if isinstance(action, FinishAction):
            return "finished_ungraded", "Agent finished; an independent W3 grade is still required"
        if isinstance(action, FailAction) and action.category == "escalated":
            return "escalated", message or "Agent escalated"
        return "failed", message or "Agent failed"

    @staticmethod
    def _action_signature(action: BrowserAction) -> str:
        payload = action.model_dump(mode="json", exclude={"action_id"})
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _context_action_summary(
        action: BrowserAction,
        observation: Observation,
        result: ActionResult,
    ) -> str:
        target = ""
        if isinstance(action, (ClickAction, FillAction, SelectAction, ReadAction, ScrollAction)):
            target = next(
                (
                    element.name
                    for element in observation.interactive_elements
                    if element.element_ref == action.element_ref
                ),
                "unknown element",
            )
        elif isinstance(action, NavigateAction):
            target = action.url
        elif isinstance(action, WaitAction):
            target = f"{action.duration_ms}ms"
        elif isinstance(action, FinishAction):
            target = "finish"
        elif isinstance(action, FailAction):
            target = action.category
        payload = {
            "action": action.type,
            "target": target[:120],
            "success": result.success,
            "error_category": result.error_category,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _observation_fingerprint(observation: Observation) -> str:
        payload = {
            "url": observation.current_url,
            "title": observation.page_title,
            "semantic": [item.model_dump() for item in observation.semantic_nodes],
            "interactive": [
                {
                    "role": item.role,
                    "name": item.name,
                    "state": item.state.model_dump(),
                    "actions": item.allowed_actions,
                    "options": item.options,
                }
                for item in observation.interactive_elements
            ],
            "error": observation.page_error,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _result(
        task_id: TaskId,
        status: RunStatus,
        reason: str,
        steps: int,
        model_calls: int,
        input_tokens: int,
        output_tokens: int,
        cost_microusd: int,
        actions: list[ActionSummary],
    ) -> AgentRunResult:
        return AgentRunResult(
            task_id=task_id,
            status=status,
            terminal_reason=reason[:300],
            steps=steps,
            action_count=len(actions),
            model_calls=model_calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_microusd=cost_microusd,
            actions=tuple(actions),
        )
