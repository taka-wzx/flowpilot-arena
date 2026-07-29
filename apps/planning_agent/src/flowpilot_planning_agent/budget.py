from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic

from flowpilot_planning_agent.schemas import BudgetReason, TotalBudget, TotalUsage


class BudgetExceeded(RuntimeError):
    def __init__(self, reason: BudgetReason) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(slots=True)
class _Counters:
    plan_generations: int = 0
    plan_nodes: int = 0
    plan_edges: int = 0
    plan_depth: int = 0
    plan_serialized_bytes: int = 0
    tool_matches: int = 0
    tool_rejections: int = 0
    verifier_calls: int = 0
    verifier_probes: int = 0
    executed_steps: int = 0
    blocked_steps: int = 0
    worker_actions: int = 0
    model_calls: int = 0
    switches: int = 0
    route_decisions: int = 0
    dom_observations: int = 0
    dom_observation_bytes: int = 0
    compressed_dom_bytes: int = 0
    images: int = 0
    image_bytes: int = 0
    image_pixels: int = 0
    capture_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    planning_input_tokens: int = 0
    planning_output_tokens: int = 0
    verifier_input_tokens: int = 0
    verifier_output_tokens: int = 0
    cost_microusd: int = 0
    planning_cost_microusd: int = 0
    verifier_cost_microusd: int = 0
    context_assemblies: int = 0
    context_items: int = 0
    context_bytes: int = 0
    context_tokens: int = 0
    retrieval_queries: int = 0
    retrieval_candidates: int = 0
    retrieval_selected: int = 0
    summary_inputs: int = 0
    summary_outputs: int = 0
    summary_dropped: int = 0
    memory_reads: int = 0
    memory_writes: int = 0
    memory_deletes: int = 0
    memory_rejections: int = 0


class TotalBudgetLedger:
    """The sole mutable accounting object for one Planning run."""

    def __init__(
        self,
        budget: TotalBudget,
        *,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.budget = budget
        self._clock = clock
        self._started = clock()
        self._counters = _Counters()

    def check_time(self) -> None:
        if self._clock() - self._started > self.budget.max_duration_seconds:
            raise BudgetExceeded("time_budget_exhausted")

    def charge_plan(self, *, nodes: int, edges: int, depth: int, serialized_bytes: int) -> None:
        self.check_time()
        counters = self._counters
        counters.plan_generations += 1
        counters.model_calls += 1
        counters.plan_nodes = nodes
        counters.plan_edges = edges
        counters.plan_depth = depth
        counters.plan_serialized_bytes = serialized_bytes
        counters.planning_input_tokens += 32
        counters.planning_output_tokens += 16
        counters.input_tokens += 32
        counters.output_tokens += 16
        if counters.plan_generations > self.budget.max_plan_generations:
            raise BudgetExceeded("plan_generation_budget_exhausted")
        self._check_model_and_tokens()

    def charge_tool_match(self, *, rejected: bool) -> None:
        self.check_time()
        counters = self._counters
        counters.tool_matches += 1
        if counters.tool_matches > self.budget.max_tool_matches:
            raise BudgetExceeded("tool_match_budget_exhausted")
        if rejected:
            counters.tool_rejections += 1
            if counters.tool_rejections > self.budget.max_tool_rejections:
                raise BudgetExceeded("tool_rejection_budget_exhausted")

    def charge_verifier(self, *, probe: bool) -> None:
        self.check_time()
        counters = self._counters
        counters.verifier_calls += 1
        counters.model_calls += 1
        counters.verifier_input_tokens += 8
        counters.verifier_output_tokens += 4
        counters.input_tokens += 8
        counters.output_tokens += 4
        if probe:
            counters.verifier_probes += 1
        if counters.verifier_calls > self.budget.max_verifier_calls:
            raise BudgetExceeded("verifier_budget_exhausted")
        if counters.verifier_probes > self.budget.max_verifier_probes:
            raise BudgetExceeded("verifier_probe_budget_exhausted")
        self._check_model_and_tokens()

    def charge_step(self, *, blocked: bool = False) -> None:
        self.check_time()
        if blocked:
            self._counters.blocked_steps += 1
            if self._counters.blocked_steps > self.budget.max_blocked_steps:
                raise BudgetExceeded("blocked_step_budget_exhausted")
        else:
            self._counters.executed_steps += 1
            if self._counters.executed_steps > self.budget.max_executed_steps:
                raise BudgetExceeded("executed_step_budget_exhausted")

    def charge_action(self) -> None:
        self.check_time()
        self._counters.worker_actions += 1
        if self._counters.worker_actions > self.budget.max_steps:
            raise BudgetExceeded("action_budget_exhausted")

    def charge_dom_observation(self, raw_bytes: int) -> None:
        self.check_time()
        counters = self._counters
        counters.dom_observations += 1
        counters.dom_observation_bytes += raw_bytes
        counters.compressed_dom_bytes += min(raw_bytes, 6_144)
        counters.route_decisions += 1
        if counters.dom_observations > self.budget.max_dom_observations:
            raise BudgetExceeded("dom_observation_budget_exhausted")
        if counters.dom_observation_bytes > self.budget.max_dom_observation_bytes:
            raise BudgetExceeded("dom_byte_budget_exhausted")
        if counters.compressed_dom_bytes > self.budget.max_compressed_dom_bytes:
            raise BudgetExceeded("compressed_dom_budget_exhausted")

    def charge_context_assembly(self) -> None:
        self.check_time()
        self._counters.context_assemblies += 1
        if self._counters.context_assemblies > self.budget.max_context_assemblies:
            raise BudgetExceeded("context_assembly_budget_exhausted")

    def charge_context_item(self, *, canonical_bytes: int, estimated_tokens: int) -> None:
        self.check_time()
        counters = self._counters
        counters.context_items += 1
        counters.context_bytes += canonical_bytes
        counters.context_tokens += estimated_tokens
        if counters.context_items > self.budget.max_context_items:
            raise BudgetExceeded("context_item_budget_exhausted")
        if counters.context_bytes > self.budget.max_context_bytes:
            raise BudgetExceeded("context_byte_budget_exhausted")
        if counters.context_tokens > self.budget.max_context_tokens:
            raise BudgetExceeded("context_token_budget_exhausted")

    def charge_retrieval(self, *, candidates: int, selected: int) -> None:
        self.check_time()
        counters = self._counters
        counters.retrieval_queries += 1
        counters.retrieval_candidates += candidates
        counters.retrieval_selected += selected
        if (
            counters.retrieval_queries > self.budget.max_retrieval_queries
            or counters.retrieval_candidates > self.budget.max_retrieval_candidates
            or counters.retrieval_selected > self.budget.max_retrieval_selected
        ):
            raise BudgetExceeded("retrieval_budget_exhausted")

    def charge_summary(self, *, inputs: int, outputs: int, dropped: int) -> None:
        self.check_time()
        counters = self._counters
        counters.summary_inputs += inputs
        counters.summary_outputs += outputs
        counters.summary_dropped += dropped
        if (
            counters.summary_inputs > self.budget.max_summary_inputs
            or counters.summary_outputs > self.budget.max_summary_outputs
            or counters.summary_dropped > self.budget.max_summary_dropped
        ):
            raise BudgetExceeded("summary_budget_exhausted")

    def charge_memory(
        self,
        *,
        reads: int = 0,
        writes: int = 0,
        deletes: int = 0,
        rejections: int = 0,
    ) -> None:
        self.check_time()
        counters = self._counters
        counters.memory_reads += reads
        counters.memory_writes += writes
        counters.memory_deletes += deletes
        counters.memory_rejections += rejections
        if (
            counters.memory_reads > self.budget.max_memory_reads
            or counters.memory_writes > self.budget.max_memory_writes
            or counters.memory_deletes > self.budget.max_memory_deletes
            or counters.memory_rejections > self.budget.max_memory_rejections
        ):
            raise BudgetExceeded("memory_budget_exhausted")

    def can_execute_action(self) -> bool:
        try:
            self.check_time()
        except BudgetExceeded:
            return False
        return self._counters.worker_actions < self.budget.max_steps

    def _check_model_and_tokens(self) -> None:
        counters = self._counters
        if counters.model_calls > self.budget.max_model_calls:
            raise BudgetExceeded("model_call_budget_exhausted")
        if (
            counters.input_tokens > self.budget.max_input_tokens
            or counters.planning_input_tokens > self.budget.max_planning_input_tokens
            or counters.verifier_input_tokens > self.budget.max_verifier_input_tokens
        ):
            raise BudgetExceeded("input_token_budget_exhausted")
        if (
            counters.output_tokens > self.budget.max_output_tokens
            or counters.planning_output_tokens > self.budget.max_planning_output_tokens
            or counters.verifier_output_tokens > self.budget.max_verifier_output_tokens
        ):
            raise BudgetExceeded("output_token_budget_exhausted")
        if (
            counters.cost_microusd > self.budget.max_cost_microusd
            or counters.planning_cost_microusd > self.budget.max_planning_cost_microusd
            or counters.verifier_cost_microusd > self.budget.max_verifier_cost_microusd
        ):
            raise BudgetExceeded("cost_budget_exhausted")

    def snapshot(self) -> TotalUsage:
        counters = self._counters
        return TotalUsage(
            **{field: getattr(counters, field) for field in counters.__dataclass_fields__},
            elapsed_ms=max(0, int((self._clock() - self._started) * 1_000)),
        )
