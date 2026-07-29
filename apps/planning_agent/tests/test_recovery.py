from flowpilot_planning_agent.recovery_schemas import PlanningRecoveryActivity


def test_recovery_activity_requires_step_for_step_commands() -> None:
    base = {
        "command": "step",
        "workflow_id": "workflow_w8_schema",
        "run_id": "run_w8_schema",
        "task_id": "w7-jml-leaver-001-v1",
        "process": "leaver",
        "category": "standard_leaver",
        "human_brief": "Synthetic bounded brief",
        "supplied_values": {"process": "leaver", "employee_id": 101},
        "fault_scenario": "none",
        "checkpoint": None,
        "step_id": None,
        "session_epoch": 1,
        "revision": 1,
    }
    try:
        PlanningRecoveryActivity.model_validate(base)
    except ValueError:
        pass
    else:
        raise AssertionError("step command without step_id was accepted")
