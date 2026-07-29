"""Deterministic W7 Planning Compose smoke with independent grading."""

import json
from os import environ
from typing import Any
from urllib.request import Request, urlopen

CONTROL_API = environ.get("CONTROL_API_URL", "http://127.0.0.1:8000")
SANDBOX_API = environ.get("SANDBOX_API_URL", "http://127.0.0.1:8001")
BROWSER_WORKER = environ.get("BROWSER_WORKER_URL", "http://127.0.0.1:8002")
HYBRID_AGENT = environ.get("HYBRID_AGENT_URL", "http://127.0.0.1:8005")
PLANNING_AGENT = environ.get("PLANNING_AGENT_URL", "http://127.0.0.1:8006")
SANDBOX_WEB = environ.get("SANDBOX_WEB_URL", "http://127.0.0.1:5174")
W3_TASK_ID = "w3-joiner-001"


def request_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="POST" if data is not None else "GET",
    )
    with urlopen(request, timeout=90) as response:
        assert response.status in {200, 201}, (url, response.status)
        return json.loads(response.read().decode())


def require_page(path: str) -> None:
    with urlopen(f"{SANDBOX_WEB}{path}", timeout=20) as response:
        assert response.status == 200


def w3_brief_and_values(task: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    expected = task["expected_final_state"]
    supplied = {
        "process": "joiner",
        "employee_id": expected["employee"]["id"],
        "ticket_title": expected["ticket"]["title"],
        "username": expected["iam_account"]["username"],
        "asset_tag": expected["asset"]["asset_tag"],
        "laptop_model": expected["asset"]["model"],
        "mailbox": expected["mailbox"]["address"],
    }
    legacy_suffix = (
        f"Supplied synthetic values: employee ID {supplied['employee_id']}; "
        f"ticket title {supplied['ticket_title']}; username {supplied['username']}; "
        f"asset tag {supplied['asset_tag']}; laptop model {supplied['laptop_model']}; "
        f"mailbox {supplied['mailbox']}."
    )
    return " ".join((task["title"], *task["instructions"], legacy_suffix)), supplied


def reset_w3_twice() -> dict[str, Any]:
    first = request_json(f"{SANDBOX_API}/api/arena/tasks/{W3_TASK_ID}/reset-seed", {})
    second = request_json(f"{SANDBOX_API}/api/arena/tasks/{W3_TASK_ID}/reset-seed", {})
    assert first == second
    return first


def run_planning(
    *,
    run_id: str,
    task_id: str,
    process: str,
    category: str,
    brief: str,
    values: dict[str, Any],
    scenario: str,
) -> dict[str, Any]:
    return request_json(
        f"{PLANNING_AGENT}/api/planning/runs",
        {
            "schema_version": "w7-planning-run/1.0",
            "run_id": run_id,
            "task_id": task_id,
            "process": process,
            "category": category,
            "human_brief": brief,
            "supplied_values": values,
            "fake_scenario": scenario,
        },
    )


def plan_step(step_id: str, dependencies: list[str]) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "objective": "Bounded synthetic inspection.",
        "dependencies": dependencies,
        "operation": "inspect_employee",
        "expected_page": "hris",
        "required_context": ["human_brief", "supplied_values", "current_observation"],
        "allowed_actions": ["navigate", "read"],
        "preconditions": ["dependencies_verified", "budget_available", "current_session"],
        "postconditions": ["action_succeeded", "expected_page_observed"],
        "risk_level": "low",
        "retry_policy": "no_retry",
        "fallback": "stop",
    }


def verify_invalid_plans() -> None:
    cycle = {
        "schema_version": "w7-planning-dag/1.0",
        "process": "joiner",
        "category": "standard_joiner",
        "steps": [plan_step("s00", ["s01"]), plan_step("s01", ["s00"])],
    }
    missing = {
        **cycle,
        "steps": [plan_step("s00", []), plan_step("s01", ["missing_step"])],
    }
    over_limit = {
        **cycle,
        "steps": [
            plan_step(f"s{index:02d}", [] if index == 0 else [f"s{index - 1:02d}"])
            for index in range(17)
        ],
    }
    cycle_result = request_json(f"{PLANNING_AGENT}/api/planning/plans/validate", cycle)
    missing_result = request_json(f"{PLANNING_AGENT}/api/planning/plans/validate", missing)
    over_result = request_json(
        f"{PLANNING_AGENT}/api/planning/plans/validate", over_limit
    )
    assert not cycle_result["valid"] and "cycle" in cycle_result["reason_codes"]
    assert not missing_result["valid"] and "unknown_dependency" in missing_result["reason_codes"]
    assert not over_result["valid"] and "node_limit" in over_result["reason_codes"]


def assert_completed_run(result: dict[str, Any], expected_steps: int) -> None:
    assert result["status"] == "finished_ungraded"
    assert len(result["topology"]) == expected_steps
    assert [item["step_id"] for item in result["step_results"]] == result["topology"]
    assert all(item["state"] == "verified" for item in result["step_results"])
    assert "unknown_tool" in result["tool_rejection_reasons"]
    usage = result["usage"]
    assert usage["plan_generations"] == 1
    assert usage["executed_steps"] == expected_steps
    assert usage["verifier_calls"] == expected_steps
    assert usage["verifier_probes"] == 1
    assert usage["model_calls"] == 1 + expected_steps
    assert usage["tool_rejections"] >= 1
    assert usage["worker_actions"] <= 24
    assert usage["switches"] == 0
    assert usage["cost_microusd"] == 0
    assert not ({"success", "passed", "score"} & set(result))


def paired_w3_baselines(task: dict[str, Any]) -> dict[str, Any]:
    brief, values = w3_brief_and_values(task)
    w6_seed = reset_w3_twice()
    w6 = request_json(
        f"{HYBRID_AGENT}/api/hybrid-agent/runs",
        {
            "schema_version": "w6-hybrid-agent-run/1.0",
            "task_id": W3_TASK_ID,
            "instruction": brief,
            "route_category": "visual_recovery",
            "model": "deterministic-fake-hybrid",
            "fake_scenario": "complete_joiner_dom_to_vision",
        },
    )
    assert w6["status"] == "finished_ungraded" and w6["switches"] == 1
    w6_grade = request_json(f"{SANDBOX_API}/api/arena/tasks/{W3_TASK_ID}/grade", {})
    assert w6_grade["total_score"] == 100 and w6_grade["passed"] is True

    immediate_seed = reset_w3_twice()
    assert immediate_seed["seed_summary"]["fact_checksum"] == w6_seed["seed_summary"]["fact_checksum"]
    immediate = run_planning(
        run_id="run_w3immediate",
        task_id=W3_TASK_ID,
        process="joiner",
        category="standard_joiner",
        brief=brief,
        values=values,
        scenario="finish_immediately",
    )
    immediate_grade = request_json(f"{SANDBOX_API}/api/arena/tasks/{W3_TASK_ID}/grade", {})
    assert immediate["status"] == "finished_ungraded"
    assert immediate_grade["total_score"] == 30 and immediate_grade["passed"] is False

    reset_w3_twice()
    order_probe = run_planning(
        run_id="run_w3orderprobe",
        task_id=W3_TASK_ID,
        process="joiner",
        category="standard_joiner",
        brief=brief,
        values=values,
        scenario="out_of_order_probe",
    )
    assert order_probe["status"] == "dependency_blocked"
    assert order_probe["step_results"][0]["state"] == "blocked"

    reset_w3_twice()
    inconclusive = run_planning(
        run_id="run_w3inconclusive",
        task_id=W3_TASK_ID,
        process="joiner",
        category="standard_joiner",
        brief=brief,
        values=values,
        scenario="verifier_inconclusive",
    )
    assert inconclusive["status"] == "verification_inconclusive"
    assert inconclusive["step_results"][0]["verifier"]["status"] == "inconclusive"

    completion_seed = reset_w3_twice()
    completion = run_planning(
        run_id="run_w3completion",
        task_id=W3_TASK_ID,
        process="joiner",
        category="standard_joiner",
        brief=brief,
        values=values,
        scenario="complete_with_rejection_probe",
    )
    assert_completed_run(completion, 6)
    grade = request_json(f"{SANDBOX_API}/api/arena/tasks/{W3_TASK_ID}/grade", {})
    assert grade["total_score"] == 100 and grade["passed"] is True
    return {
        "w6_switches": w6["switches"],
        "w6_grade": w6_grade["total_score"],
        "w7_immediate_grade": immediate_grade["total_score"],
        "w7_grade": grade["total_score"],
        "seed_checksum": completion_seed["seed_summary"]["fact_checksum"],
        "w7_actions": completion["usage"]["worker_actions"],
        "w7_verifier_calls": completion["usage"]["verifier_calls"],
    }


def run_jml_task(task_id: str, run_id: str) -> dict[str, Any]:
    task = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}")
    assert task["split"] == "development"
    first = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/reset-seed", {})
    second = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/reset-seed", {})
    assert first == second
    untouched = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/grade", {})
    assert untouched["passed"] is False
    result = run_planning(
        run_id=run_id,
        task_id=task_id,
        process=task["process"],
        category=task["category"],
        brief=task["human_brief"],
        values=task["supplied_values"],
        scenario="complete_with_rejection_probe",
    )
    assert_completed_run(result, 3 if task["process"] == "mover" else 6)
    grade = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/grade", {})
    assert grade["total_score"] == 100 and grade["passed"] is True
    return {
        "task_id": task_id,
        "instance_checksum": task["canonical_checksum"],
        "seed_checksum": first["fact_checksum"],
        "untouched_grade": untouched["total_score"],
        "grade": grade["total_score"],
        "actions": result["usage"]["worker_actions"],
        "verifier_calls": result["usage"]["verifier_calls"],
    }


def main() -> None:
    for url in (CONTROL_API, SANDBOX_API, BROWSER_WORKER, HYBRID_AGENT, PLANNING_AGENT):
        assert request_json(f"{url}/healthz")["status"] == "ok"
    for path in ("/hris", "/itsm", "/iam", "/assets", "/mail"):
        require_page(path)

    catalog = request_json(f"{SANDBOX_API}/api/arena/w7/catalog")
    tasks = request_json(f"{SANDBOX_API}/api/arena/w7/tasks")
    assert catalog["template_count"] == 30 and catalog["instance_count"] == 90
    assert len(tasks) == 90
    verify_invalid_plans()

    w3_task = request_json(f"{SANDBOX_API}/api/arena/tasks/{W3_TASK_ID}")
    paired = paired_w3_baselines(w3_task)
    jml = [
        run_jml_task("w7-jml-joiner-001-v1", "run_jmljoiner01"),
        run_jml_task("w7-jml-mover-001-v1", "run_jmlmover001"),
        run_jml_task("w7-jml-leaver-001-v1", "run_jmlleaver01"),
    ]
    print(
        json.dumps(
            {
                "schema_version": "w7-planning-smoke/1.0",
                "catalog_checksum": catalog["catalog_checksum"],
                "split_manifest_checksum": catalog["split_manifest_checksum"],
                "reporting_manifest_checksum": catalog["reporting_manifest_checksum"],
                "template_count": catalog["template_count"],
                "instance_count": catalog["instance_count"],
                "paired_w3": paired,
                "jml_development": jml,
                "external_calls": 0,
                "actual_cost": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
