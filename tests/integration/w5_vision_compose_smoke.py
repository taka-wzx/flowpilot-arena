"""Deterministic W5 Vision-only Compose smoke with independent W3 grading."""

import json
from os import environ
from typing import Any
from urllib.request import Request, urlopen

CONTROL_API = environ.get("CONTROL_API_URL", "http://127.0.0.1:8000")
SANDBOX_API = environ.get("SANDBOX_API_URL", "http://127.0.0.1:8001")
BROWSER_WORKER = environ.get("BROWSER_WORKER_URL", "http://127.0.0.1:8002")
VISION_AGENT = environ.get("VISION_AGENT_URL", "http://127.0.0.1:8004")
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


def require_page(path: str) -> None:
    with urlopen(f"{SANDBOX_WEB}{path}", timeout=20) as response:
        assert response.status == 200, (path, response.status)


def render_human_brief(task: dict[str, Any]) -> str:
    expected = task["expected_final_state"]
    supplied = (
        f"Supplied synthetic values: employee ID {expected['employee']['id']}; "
        f"ticket title {expected['ticket']['title']}; "
        f"username {expected['iam_account']['username']}; asset tag "
        f"{expected['asset']['asset_tag']}; laptop model {expected['asset']['model']}; "
        f"mailbox {expected['mailbox']['address']}."
    )
    return " ".join((task["title"], *task["instructions"], supplied))


def reset_seed_twice() -> dict[str, Any]:
    first_seed = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/reset-seed", {})
    second_seed = request_json(
        f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/reset-seed", {}
    )
    assert first_seed == second_seed
    return first_seed


def run_fake_agent(instruction: str, scenario: str) -> dict[str, Any]:
    return request_json(
        f"{VISION_AGENT}/api/vision-agent/runs",
        {
            "schema_version": "w5-vision-agent-run/1.0",
            "task_id": TASK_ID,
            "instruction": instruction,
            "model": "deterministic-fake-vision",
            "fake_scenario": scenario,
        },
    )


def main() -> None:
    assert request_json(f"{CONTROL_API}/healthz")["status"] == "ok"
    assert request_json(f"{SANDBOX_API}/healthz")["status"] == "ok"
    assert request_json(f"{BROWSER_WORKER}/healthz")["status"] == "ok"
    assert request_json(f"{VISION_AGENT}/healthz")["status"] == "ok"
    for path in ("/hris", "/itsm", "/iam", "/assets", "/mail"):
        require_page(path)

    task = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}")
    brief = render_human_brief(task)
    untouched_seed = reset_seed_twice()

    untouched_run = run_fake_agent(brief, "grounded_read_then_finish")
    assert untouched_run["status"] == "finished_ungraded"
    assert untouched_run["cost_microusd"] == 0
    assert untouched_run["image_count"] == 2
    assert untouched_run["image_bytes"] > 0
    assert untouched_run["image_pixels"] == 2 * 960 * 540
    assert untouched_run["capture_duration_ms"] >= 0
    assert not ({"success", "passed", "score", "image_base64"} & set(untouched_run))

    untouched_grade = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/grade", {})
    assert untouched_grade["total_score"] == 30
    assert untouched_grade["passed"] is False

    completion_seed = reset_seed_twice()
    completion_run = run_fake_agent(brief, "complete_joiner")
    assert completion_run["status"] == "finished_ungraded"
    assert completion_run["cost_microusd"] == 0
    assert completion_run["steps"] == 20
    assert completion_run["action_count"] == 20
    assert completion_run["model_calls"] == 20
    assert completion_run["image_count"] == 20
    assert completion_run["image_bytes"] > 0
    assert completion_run["image_pixels"] == 20 * 960 * 540
    assert completion_run["capture_duration_ms"] >= 0
    assert not ({"success", "passed", "score", "image_base64"} & set(completion_run))

    completion_grade = request_json(
        f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/grade", {}
    )
    assert completion_grade["total_score"] == 100
    assert completion_grade["passed"] is True

    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "spec_checksum": task["canonical_checksum"],
                "untouched_seed_checksum": untouched_seed["seed_summary"][
                    "fact_checksum"
                ],
                "untouched_grade": untouched_grade["total_score"],
                "untouched_passed": untouched_grade["passed"],
                "completion_seed_checksum": completion_seed["seed_summary"][
                    "fact_checksum"
                ],
                "agent_status": completion_run["status"],
                "agent_steps": completion_run["steps"],
                "agent_actions": completion_run["action_count"],
                "model_calls": completion_run["model_calls"],
                "image_count": completion_run["image_count"],
                "image_bytes": completion_run["image_bytes"],
                "image_pixels": completion_run["image_pixels"],
                "capture_duration_ms": completion_run["capture_duration_ms"],
                "tokens": completion_run["input_tokens"]
                + completion_run["output_tokens"],
                "cost_microusd": completion_run["cost_microusd"],
                "grade": completion_grade["total_score"],
                "passed": completion_grade["passed"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
