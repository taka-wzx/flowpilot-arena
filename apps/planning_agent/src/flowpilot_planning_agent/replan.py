from collections import deque

from flowpilot_planning_agent.dag import validate_dag
from flowpilot_planning_agent.schemas import PlanningDag


def partial_replan(
    dag: PlanningDag,
    failed_step_id: str,
    completed_step_ids: frozenset[str],
) -> tuple[PlanningDag, tuple[str, ...]]:
    by_id = {step.step_id: step for step in dag.steps}
    if failed_step_id not in by_id or failed_step_id in completed_step_ids:
        raise ValueError("failed step is not eligible for partial replan")
    children: dict[str, list[str]] = {step_id: [] for step_id in by_id}
    for step in dag.steps:
        for dependency in step.dependencies:
            children[dependency].append(step.step_id)
    replaced: set[str] = set()
    queue = deque([failed_step_id])
    while queue:
        current = queue.popleft()
        if current in completed_step_ids or current in replaced:
            continue
        replaced.add(current)
        queue.extend(sorted(children[current]))
    mapping = {step_id: f"r2_{step_id}" for step_id in sorted(replaced)}
    if any(len(value) > 40 for value in mapping.values()):
        raise ValueError("replacement step identifier exceeds W7 cap")
    steps = []
    for step in dag.steps:
        if step.step_id in replaced:
            steps.append(
                step.model_copy(
                    update={
                        "step_id": mapping[step.step_id],
                        "dependencies": tuple(
                            mapping.get(dependency, dependency) for dependency in step.dependencies
                        ),
                    }
                )
            )
        else:
            steps.append(step)
    revised = PlanningDag(process=dag.process, category=dag.category, steps=tuple(steps))
    validation = validate_dag(revised)
    if not validation.valid:
        raise ValueError("partial replan violated the frozen W7 DAG contract")
    return revised, tuple(sorted(replaced))
