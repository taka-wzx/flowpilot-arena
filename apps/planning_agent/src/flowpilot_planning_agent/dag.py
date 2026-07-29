import hashlib
import json
from collections import Counter, deque

from flowpilot_planning_agent.schemas import (
    AllowedAction,
    Operation,
    Page,
    PlanningDag,
    PlanStep,
    PlanValidationReason,
    PlanValidationResult,
    StepState,
)

MAX_NODES = 16
MAX_EDGES = 24
MAX_DEPTH = 8
MAX_WIDTH = 8
MAX_DEPENDENCIES = 4
MAX_SERIALIZED_BYTES = 32_768

OPERATION_CONTRACT: dict[Operation, tuple[Page, frozenset[AllowedAction]]] = {
    "inspect_employee": ("hris", frozenset({"navigate", "read"})),
    "create_ticket": ("itsm", frozenset({"navigate", "fill", "click"})),
    "create_account": ("iam", frozenset({"navigate", "fill", "click"})),
    "assign_asset": ("assets", frozenset({"navigate", "fill", "click"})),
    "create_mailbox": ("mail", frozenset({"navigate", "fill", "click"})),
    "transfer_employee": ("hris", frozenset({"navigate", "fill", "click"})),
    "disable_employee": ("hris", frozenset({"navigate", "fill", "click"})),
    "close_ticket": ("itsm", frozenset({"navigate", "fill", "click"})),
    "revoke_account": ("iam", frozenset({"navigate", "fill", "click"})),
    "release_asset": ("assets", frozenset({"navigate", "fill", "click"})),
    "disable_mailbox": ("mail", frozenset({"navigate", "fill", "click"})),
    "finalize": ("hris", frozenset({"navigate", "read", "finish"})),
}


def canonical_dag_bytes(dag: PlanningDag) -> bytes:
    return json.dumps(
        dag.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def validate_dag(dag: PlanningDag) -> PlanValidationResult:
    serialized = canonical_dag_bytes(dag)
    node_count = len(dag.steps)
    edge_count = sum(len(step.dependencies) for step in dag.steps)
    reasons: list[PlanValidationReason] = []
    ids = [step.step_id for step in dag.steps]
    if len(ids) != len(set(ids)):
        reasons.append("duplicate_step_id")
    by_id = {step.step_id: step for step in dag.steps}

    if node_count > MAX_NODES:
        reasons.append("node_limit")
    if edge_count > MAX_EDGES:
        reasons.append("edge_limit")
    if len(serialized) > MAX_SERIALIZED_BYTES:
        reasons.append("byte_limit")

    for step in dag.steps:
        if len(step.dependencies) > MAX_DEPENDENCIES:
            reasons.append("dependency_limit")
        if step.step_id in step.dependencies:
            reasons.append("self_dependency")
        if any(dependency not in by_id for dependency in step.dependencies):
            reasons.append("unknown_dependency")
        expected_page, expected_actions = OPERATION_CONTRACT[step.operation]
        if step.expected_page != expected_page:
            reasons.append("operation_page_mismatch")
        if frozenset(step.allowed_actions) != expected_actions:
            reasons.append("operation_action_mismatch")

    roots = [step.step_id for step in dag.steps if not step.dependencies]
    if len(roots) != 1:
        reasons.append("multiple_roots")

    topology: list[str] = []
    depth = 0
    width = 0
    if "duplicate_step_id" not in reasons and "unknown_dependency" not in reasons:
        dependents: dict[str, list[str]] = {step_id: [] for step_id in by_id}
        indegree = {step_id: 0 for step_id in by_id}
        for step in dag.steps:
            indegree[step.step_id] = len(step.dependencies)
            for dependency in step.dependencies:
                dependents[dependency].append(step.step_id)
        ready = sorted(step_id for step_id, count in indegree.items() if count == 0)
        while ready:
            current = ready.pop(0)
            topology.append(current)
            for dependent in sorted(dependents[current]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)
                    ready.sort()
        if len(topology) != node_count:
            reasons.append("cycle")
        else:
            depths: dict[str, int] = {}
            for step_id in topology:
                dependencies = by_id[step_id].dependencies
                depths[step_id] = (
                    1
                    if not dependencies
                    else 1 + max(depths[dependency] for dependency in dependencies)
                )
            depth = max(depths.values(), default=0)
            width = max(Counter(depths.values()).values(), default=0)
            if depth > MAX_DEPTH:
                reasons.append("depth_limit")
            if width > MAX_WIDTH:
                reasons.append("width_limit")

    if len(roots) == 1 and "unknown_dependency" not in reasons:
        adjacency: dict[str, list[str]] = {step_id: [] for step_id in by_id}
        for step in dag.steps:
            for dependency in step.dependencies:
                adjacency[dependency].append(step.step_id)
        seen: set[str] = set()
        queue: deque[str] = deque(roots)
        while queue:
            current = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            queue.extend(adjacency[current])
        if len(seen) != node_count:
            reasons.append("unreachable_node")

    reason_codes = tuple(dict.fromkeys(reasons))
    valid = not reason_codes
    plan_id = hashlib.sha256(serialized).hexdigest() if valid else None
    return PlanValidationResult(
        valid=valid,
        reason_codes=reason_codes,
        plan_id=plan_id,
        node_count=node_count,
        edge_count=edge_count,
        depth=depth,
        width=width,
        serialized_bytes=len(serialized),
        topology=tuple(topology) if valid else (),
    )


class DependencyBlocked(RuntimeError):
    pass


class StepStateMachine:
    def __init__(self, dag: PlanningDag) -> None:
        self._steps = {step.step_id: step for step in dag.steps}
        self._states: dict[str, StepState] = {step.step_id: "pending" for step in dag.steps}

    def start(self, step_id: str) -> None:
        step = self._steps.get(step_id)
        if step is None:
            raise DependencyBlocked("unknown step")
        if self._states[step_id] != "pending":
            raise DependencyBlocked("step is not pending")
        if any(self._states[dependency] != "verified" for dependency in step.dependencies):
            raise DependencyBlocked("dependencies are not verified")
        self._states[step_id] = "ready"
        self._states[step_id] = "executing"

    def verify(self, step_id: str) -> None:
        if self._states.get(step_id) != "executing":
            raise DependencyBlocked("only executing steps can be verified")
        self._states[step_id] = "verified"

    def terminate(self, step_id: str, state: StepState) -> None:
        if state not in {"blocked", "failed", "escalated"}:
            raise ValueError("invalid terminal step state")
        if self._states.get(step_id) not in {"pending", "ready", "executing"}:
            raise DependencyBlocked("step cannot enter the requested terminal state")
        self._states[step_id] = state

    def state(self, step_id: str) -> StepState:
        try:
            return self._states[step_id]
        except KeyError as exc:
            raise DependencyBlocked("unknown step") from exc

    @property
    def states(self) -> dict[str, StepState]:
        return dict(self._states)


def step_by_id(dag: PlanningDag, step_id: str) -> PlanStep:
    for step in dag.steps:
        if step.step_id == step_id:
            return step
    raise KeyError(step_id)
