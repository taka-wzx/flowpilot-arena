from flowpilot_planning_agent.dag import validate_dag
from flowpilot_planning_agent.schemas import (
    AllowedAction,
    Fallback,
    Operation,
    Page,
    PlanningDag,
    PlanRequest,
    PlanResult,
    PlanStep,
    RiskLevel,
)


def _step(
    step_id: str,
    objective: str,
    dependencies: tuple[str, ...],
    operation: Operation,
    page: Page,
    actions: tuple[AllowedAction, ...],
    risk: RiskLevel = "low",
    fallback: Fallback = "stop",
) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        objective=objective,
        dependencies=dependencies,
        operation=operation,
        expected_page=page,
        required_context=("human_brief", "supplied_values", "current_observation"),
        allowed_actions=actions,
        preconditions=("dependencies_verified", "budget_available", "current_session"),
        postconditions=("action_succeeded", "expected_page_observed"),
        risk_level=risk,
        retry_policy="no_retry",
        fallback=fallback,
    )


class DeterministicPlanner:
    """One-shot fake planner using only finite process/category and strict values."""

    def generate(self, request: PlanRequest) -> PlanResult:
        if request.process == "joiner":
            steps = self._joiner_steps()
        elif request.process == "mover":
            steps = self._mover_steps()
        else:
            steps = self._leaver_steps()
        dag = PlanningDag(process=request.process, category=request.category, steps=steps)
        validation = validate_dag(dag)
        if not validation.valid or validation.plan_id is None:
            raise ValueError("deterministic planner generated an invalid DAG")
        return PlanResult(plan_id=validation.plan_id, dag=dag)

    @staticmethod
    def _joiner_steps() -> tuple[PlanStep, ...]:
        return (
            _step(
                "s00_inspect",
                "Inspect the current synthetic employee page.",
                (),
                "inspect_employee",
                "hris",
                ("navigate", "read"),
            ),
            _step(
                "s10_ticket",
                "Create the bounded onboarding ticket.",
                ("s00_inspect",),
                "create_ticket",
                "itsm",
                ("navigate", "fill", "click"),
            ),
            _step(
                "s20_account",
                "Create the ordinary synthetic IAM account.",
                ("s00_inspect",),
                "create_account",
                "iam",
                ("navigate", "fill", "click"),
            ),
            _step(
                "s30_asset",
                "Assign the synthetic laptop.",
                ("s00_inspect",),
                "assign_asset",
                "assets",
                ("navigate", "fill", "click"),
            ),
            _step(
                "s40_mail",
                "Create the non-deliverable synthetic mailbox.",
                ("s00_inspect",),
                "create_mailbox",
                "mail",
                ("navigate", "fill", "click"),
            ),
            _step(
                "s90_finalize",
                "Return to HRIS and end ungraded.",
                ("s10_ticket", "s20_account", "s30_asset", "s40_mail"),
                "finalize",
                "hris",
                ("navigate", "read", "finish"),
            ),
        )

    @staticmethod
    def _mover_steps() -> tuple[PlanStep, ...]:
        return (
            _step(
                "s10_transfer",
                "Apply the bounded synthetic employee transfer.",
                (),
                "transfer_employee",
                "hris",
                ("navigate", "fill", "click"),
                "medium",
            ),
            _step(
                "s20_close",
                "Close the employee-owned transition ticket.",
                ("s10_transfer",),
                "close_ticket",
                "itsm",
                ("navigate", "fill", "click"),
                "medium",
            ),
            _step(
                "s90_finalize",
                "Return to HRIS and end ungraded.",
                ("s10_transfer", "s20_close"),
                "finalize",
                "hris",
                ("navigate", "read", "finish"),
            ),
        )

    @staticmethod
    def _leaver_steps() -> tuple[PlanStep, ...]:
        return (
            _step(
                "s10_disable_employee",
                "Disable the synthetic employee profile.",
                (),
                "disable_employee",
                "hris",
                ("navigate", "fill", "click"),
                "high",
                "escalate",
            ),
            _step(
                "s20_close_ticket",
                "Close the employee-owned ticket.",
                ("s10_disable_employee",),
                "close_ticket",
                "itsm",
                ("navigate", "fill", "click"),
                "high",
                "escalate",
            ),
            _step(
                "s30_revoke_account",
                "Revoke the ordinary synthetic account.",
                ("s10_disable_employee",),
                "revoke_account",
                "iam",
                ("navigate", "fill", "click"),
                "high",
                "escalate",
            ),
            _step(
                "s40_release_asset",
                "Release the synthetic asset assignment.",
                ("s10_disable_employee",),
                "release_asset",
                "assets",
                ("navigate", "fill", "click"),
                "high",
                "escalate",
            ),
            _step(
                "s50_disable_mail",
                "Disable the synthetic mailbox.",
                ("s40_release_asset",),
                "disable_mailbox",
                "mail",
                ("navigate", "fill", "click"),
                "high",
                "escalate",
            ),
            _step(
                "s90_finalize",
                "Return to HRIS and end ungraded.",
                ("s20_close_ticket", "s30_revoke_account", "s40_release_asset", "s50_disable_mail"),
                "finalize",
                "hris",
                ("navigate", "read", "finish"),
            ),
        )
