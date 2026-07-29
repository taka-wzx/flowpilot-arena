from flowpilot_planning_agent.receipts import build_binding, mutation_payload
from flowpilot_planning_agent.recovery_schemas import PlanningRecoveryActivity
from flowpilot_planning_agent.schemas import JoinerSuppliedValues


def _request() -> PlanningRecoveryActivity:
    return PlanningRecoveryActivity(
        command="step",
        workflow_id="workflow_w8_receipt",
        run_id="run_w8_receipt",
        task_id="w7-jml-joiner-001-v1",
        process="joiner",
        category="standard_joiner",
        human_brief="Synthetic bounded brief",
        supplied_values=JoinerSuppliedValues(
            employee_id=101,
            ticket_title="Synthetic ticket",
            username="synthetic.user",
            asset_tag="SYN-W8-ASSET",
            laptop_model="Synthetic laptop",
            mailbox="synthetic.user@example.invalid",
        ),
        fault_scenario="none",
        step_id="s10_ticket",
        session_epoch=1,
        revision=1,
    )


def test_idempotency_key_and_request_hash_are_deterministic() -> None:
    request = _request()
    first = build_binding(request, "create_ticket")
    second = build_binding(request, "create_ticket")
    assert first == second
    assert first.idempotency_key.startswith("op_")
    assert len(first.idempotency_key) == 67
    assert mutation_payload("create_ticket", request.supplied_values) == {
        "employee_id": 101,
        "title": "Synthetic ticket",
        "status": "open",
    }


def test_revision_changes_idempotency_key() -> None:
    first = build_binding(_request(), "create_ticket")
    revised = build_binding(_request().model_copy(update={"revision": 2}), "create_ticket")
    assert first.idempotency_key != revised.idempotency_key
