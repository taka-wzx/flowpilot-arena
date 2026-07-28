"""Deterministic W6 Hybrid Compose smoke with independent W3 grading."""

import json
from os import environ
from typing import Any
from urllib.request import Request, urlopen

CONTROL_API = environ.get("CONTROL_API_URL", "http://127.0.0.1:8000")
SANDBOX_API = environ.get("SANDBOX_API_URL", "http://127.0.0.1:8001")
BROWSER_WORKER = environ.get("BROWSER_WORKER_URL", "http://127.0.0.1:8002")
HYBRID_AGENT = environ.get("HYBRID_AGENT_URL", "http://127.0.0.1:8005")
SANDBOX_WEB = environ.get("SANDBOX_WEB_URL", "http://127.0.0.1:5174")
TASK_ID = "w3-joiner-001"


def request_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="POST" if data is not None else "GET",
    )
    with urlopen(request, timeout=30) as response:
        assert response.status in {200, 201}, (url, response.status)
        return json.loads(response.read().decode("utf-8"))


def delete_json(url: str) -> dict[str, Any]:
    request = Request(url, method="DELETE")
    with urlopen(request, timeout=30) as response:
        assert response.status == 200, (url, response.status)
        return json.loads(response.read().decode("utf-8"))


def require_page(path: str) -> None:
    with urlopen(f"{SANDBOX_WEB}{path}", timeout=20) as response:
        assert response.status == 200, (path, response.status)


def render_human_brief(task: dict[str, Any]) -> str:
    expected = task["expected_final_state"]
    supplied = (
        f"Supplied synthetic values: employee ID {expected['employee']['id']}; "
        f"ticket title {expected['ticket']['title']}; "
        f"username {expected['iam_account']['username']}; "
        f"asset tag {expected['asset']['asset_tag']}; laptop model {expected['asset']['model']}; "
        f"mailbox {expected['mailbox']['address']}."
    )
    return " ".join((task["title"], *task["instructions"], supplied))


def reset_seed_twice() -> dict[str, Any]:
    first_seed = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/reset-seed", {})
    second_seed = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/reset-seed", {})
    assert first_seed == second_seed
    return first_seed


def run_fake_agent(
    instruction: str,
    route_category: str,
    scenario: str,
) -> dict[str, Any]:
    return request_json(
        f"{HYBRID_AGENT}/api/hybrid-agent/runs",
        {
            "schema_version": "w6-hybrid-agent-run/1.0",
            "task_id": TASK_ID,
            "instruction": instruction,
            "route_category": route_category,
            "model": "deterministic-fake-hybrid",
            "fake_scenario": scenario,
        },
    )


def verify_worker_reference_lifecycle() -> None:
    created = request_json(
        f"{BROWSER_WORKER}/api/browser/hybrid-sessions",
        {"schema_version": "w6-hybrid-session/1.0", "initial_path": "/hris"},
    )
    session_id = created["session_id"]
    dom = created["observation"]
    assert dom["modality"] == "dom"
    assert dom["observation"]["interactive_elements"]
    element = dom["observation"]["interactive_elements"][0]

    visual = request_json(
        f"{BROWSER_WORKER}/api/browser/hybrid-sessions/{session_id}/observations",
        {"schema_version": "w6-hybrid-observation-request/1.0", "modality": "vision"},
    )
    assert visual["modality"] == "vision"
    assert visual["observation"]["groundings"]

    wrong_mode = request_json(
        f"{BROWSER_WORKER}/api/browser/hybrid-sessions/{session_id}/actions",
        {
            "schema_version": "w6-hybrid-action-envelope/1.0",
            "session_id": session_id,
            "generation": visual["generation"],
            "modality": "dom",
            "action": {
                "action_id": "act_smoke_wrong_mode",
                "type": "read",
                "observation_id": dom["observation"]["observation_id"],
                "element_ref": element["element_ref"],
            },
        },
    )
    assert wrong_mode["error_category"] == "invalid_modality"
    assert wrong_mode["observation"]["modality"] == "vision"

    grounding = visual["observation"]["groundings"][0]
    stale_visual = request_json(
        f"{BROWSER_WORKER}/api/browser/hybrid-sessions/{session_id}/actions",
        {
            "schema_version": "w6-hybrid-action-envelope/1.0",
            "session_id": session_id,
            "generation": wrong_mode["observation"]["generation"],
            "modality": "vision",
            "action": {
                "action_id": "act_smoke_stale_visual",
                "type": "read",
                "observation_id": visual["observation"]["observation_id"],
                "screenshot_ref": visual["observation"]["screenshot_ref"],
                "grounding_ref": grounding["grounding_ref"],
            },
        },
    )
    assert stale_visual["error_category"] == "stale_hybrid_ref"
    assert stale_visual["observation"]["generation"] > wrong_mode["observation"]["generation"]
    assert delete_json(f"{BROWSER_WORKER}/api/browser/hybrid-sessions/{session_id}")["closed"]
    assert delete_json(f"{BROWSER_WORKER}/api/browser/hybrid-sessions/{session_id}")["closed"]


def main() -> None:
    assert request_json(f"{CONTROL_API}/healthz")["status"] == "ok"
    assert request_json(f"{SANDBOX_API}/healthz")["status"] == "ok"
    assert request_json(f"{BROWSER_WORKER}/healthz")["status"] == "ok"
    assert request_json(f"{HYBRID_AGENT}/healthz")["status"] == "ok"
    for path in ("/hris", "/itsm", "/iam", "/assets", "/mail"):
        require_page(path)
    verify_worker_reference_lifecycle()

    task = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}")
    brief = render_human_brief(task)
    untouched_seed = reset_seed_twice()

    untouched_run = run_fake_agent(brief, "standard", "finish_immediately")
    assert untouched_run["status"] == "finished_ungraded"
    assert untouched_run["steps"] == 1
    assert untouched_run["action_count"] == 1
    assert untouched_run["model_calls"] == 1
    assert untouched_run["switches"] == 0
    assert untouched_run["dom_observation_count"] == 1
    assert 0 < untouched_run["compressed_dom_bytes"] <= 12_288
    assert untouched_run["image_count"] == 0
    assert untouched_run["cost_microusd"] == 0
    assert not ({"success", "passed", "score", "image_base64"} & set(untouched_run))

    untouched_grade = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/grade", {})
    assert untouched_grade["total_score"] == 30
    assert untouched_grade["passed"] is False

    completion_seed = reset_seed_twice()
    assert (
        completion_seed["seed_summary"]["fact_checksum"]
        == untouched_seed["seed_summary"]["fact_checksum"]
    )
    completion_run = run_fake_agent(brief, "visual_recovery", "complete_joiner_dom_to_vision")
    assert completion_run["status"] == "finished_ungraded"
    assert completion_run["steps"] == 20
    assert completion_run["action_count"] == 20
    assert completion_run["model_calls"] == 20
    assert completion_run["switches"] == 1
    assert completion_run["dom_observation_count"] == 2
    assert completion_run["dom_observation_bytes"] > 0
    assert 0 < completion_run["compressed_dom_bytes"] <= 12_288
    assert completion_run["image_count"] == 19
    assert completion_run["image_bytes"] > 0
    assert completion_run["image_pixels"] == 19 * 960 * 540
    assert completion_run["capture_duration_ms"] >= 0
    assert completion_run["cost_microusd"] == 0
    assert any(
        route["reason_code"] == "trusted_visual_recovery" and route["switched"]
        for route in completion_run["routes"]
    )
    assert not ({"success", "passed", "score", "image_base64"} & set(completion_run))

    completion_grade = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/grade", {})
    assert completion_grade["total_score"] == 100
    assert completion_grade["passed"] is True

    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "spec_checksum": task["canonical_checksum"],
                "untouched_seed_checksum": untouched_seed["seed_summary"]["fact_checksum"],
                "untouched_grade": untouched_grade["total_score"],
                "untouched_passed": untouched_grade["passed"],
                "untouched_agent_steps": untouched_run["steps"],
                "untouched_agent_actions": untouched_run["action_count"],
                "untouched_model_calls": untouched_run["model_calls"],
                "untouched_switches": untouched_run["switches"],
                "untouched_dom_observation_count": untouched_run["dom_observation_count"],
                "untouched_dom_observation_bytes": untouched_run["dom_observation_bytes"],
                "untouched_compressed_dom_bytes": untouched_run["compressed_dom_bytes"],
                "untouched_image_count": untouched_run["image_count"],
                "untouched_image_bytes": untouched_run["image_bytes"],
                "untouched_image_pixels": untouched_run["image_pixels"],
                "untouched_capture_duration_ms": untouched_run["capture_duration_ms"],
                "untouched_tokens": untouched_run["input_tokens"] + untouched_run["output_tokens"],
                "untouched_cost_microusd": untouched_run["cost_microusd"],
                "completion_seed_checksum": completion_seed["seed_summary"]["fact_checksum"],
                "agent_status": completion_run["status"],
                "agent_steps": completion_run["steps"],
                "agent_actions": completion_run["action_count"],
                "model_calls": completion_run["model_calls"],
                "switches": completion_run["switches"],
                "route_reasons": [route["reason_code"] for route in completion_run["routes"]],
                "dom_observation_count": completion_run["dom_observation_count"],
                "dom_observation_bytes": completion_run["dom_observation_bytes"],
                "compressed_dom_bytes": completion_run["compressed_dom_bytes"],
                "image_count": completion_run["image_count"],
                "image_bytes": completion_run["image_bytes"],
                "image_pixels": completion_run["image_pixels"],
                "capture_duration_ms": completion_run["capture_duration_ms"],
                "tokens": completion_run["input_tokens"] + completion_run["output_tokens"],
                "cost_microusd": completion_run["cost_microusd"],
                "grade": completion_grade["total_score"],
                "passed": completion_grade["passed"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
