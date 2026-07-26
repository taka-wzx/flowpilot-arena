"""Deterministic W4 Compose smoke using no external model or browser telemetry."""

import json
from os import environ
from typing import Any
from urllib.request import Request, urlopen

CONTROL_API = environ.get("CONTROL_API_URL", "http://127.0.0.1:8000")
SANDBOX_API = environ.get("SANDBOX_API_URL", "http://127.0.0.1:8001")
BROWSER_WORKER = environ.get("BROWSER_WORKER_URL", "http://127.0.0.1:8002")
DOM_AGENT = environ.get("DOM_AGENT_URL", "http://127.0.0.1:8003")
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
    with urlopen(request, timeout=20) as response:
        assert response.status in {200, 201}, (url, response.status)
        return json.loads(response.read().decode("utf-8"))


def require_page(path: str) -> None:
    with urlopen(f"{SANDBOX_WEB}{path}", timeout=20) as response:
        assert response.status == 200, (path, response.status)


def render_human_brief(task: dict[str, Any]) -> str:
    expected = task["expected_final_state"]
    supplied = (
        f"Supplied synthetic values: ticket title {expected['ticket']['title']}; "
        f"username {expected['iam_account']['username']}; asset tag "
        f"{expected['asset']['asset_tag']}; laptop model {expected['asset']['model']}; "
        f"mailbox {expected['mailbox']['address']}."
    )
    return " ".join((task["title"], *task["instructions"], supplied))


def main() -> None:
    assert request_json(f"{CONTROL_API}/healthz")["status"] == "ok"
    assert request_json(f"{SANDBOX_API}/healthz")["status"] == "ok"
    assert request_json(f"{BROWSER_WORKER}/healthz")["status"] == "ok"
    assert request_json(f"{DOM_AGENT}/healthz")["status"] == "ok"
    for path in ("/hris", "/itsm", "/iam", "/assets", "/mail"):
        require_page(path)

    task = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}")
    first_seed = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/reset-seed", {})
    second_seed = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/reset-seed", {})
    assert first_seed == second_seed

    run = request_json(
        f"{DOM_AGENT}/api/agent/runs",
        {
            "schema_version": "w4-dom-agent-run/1.0",
            "task_id": TASK_ID,
            "instruction": render_human_brief(task),
            "model": "deterministic-fake",
            "fake_scenario": "inspect_then_finish",
        },
    )
    assert run["status"] == "finished_ungraded"
    assert run["cost_microusd"] == 0
    assert not ({"success", "passed", "score"} & set(run))

    grade = request_json(f"{SANDBOX_API}/api/arena/tasks/{TASK_ID}/grade", {})
    assert grade["total_score"] == 30
    assert grade["passed"] is False

    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "spec_checksum": task["canonical_checksum"],
                "seed_checksum": first_seed["seed_summary"]["fact_checksum"],
                "agent_status": run["status"],
                "agent_steps": run["steps"],
                "agent_actions": run["action_count"],
                "model_calls": run["model_calls"],
                "tokens": run["input_tokens"] + run["output_tokens"],
                "cost_microusd": run["cost_microusd"],
                "grade": grade["total_score"],
                "passed": grade["passed"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
