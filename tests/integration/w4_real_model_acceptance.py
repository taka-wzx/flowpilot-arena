"""Authorized one-off W4 OpenAI five-task acceptance caller."""

import json
from os import environ
from time import monotonic
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

CONTROL_API = environ.get("CONTROL_API_URL", "http://127.0.0.1:8000")
SANDBOX_API = environ.get("SANDBOX_API_URL", "http://127.0.0.1:8001")
REAL_AGENT = environ.get("REAL_AGENT_URL", "http://127.0.0.1:8004")
TASK_IDS = tuple(f"w3-joiner-{index:03d}" for index in range(1, 6))
PROMPT_CONFIG_VERSION = "w4-dom-react-openai/1.0"
MODEL = "openai-gpt-5.6-terra"

PER_TASK_BUDGET = {
    "max_steps": 25,
    "max_model_calls": 25,
    "max_repeated_actions": 2,
    "max_no_progress": 3,
    "max_duration_seconds": 180,
    "max_input_tokens": 100_000,
    "max_output_tokens": 20_000,
    "max_cost_microusd": 650_000,
}
MAX_TOTAL_CALLS = 125
MAX_TOTAL_INPUT_TOKENS = 500_000
MAX_TOTAL_OUTPUT_TOKENS = 100_000
MAX_TOTAL_SECONDS = 900
MAX_TOTAL_COST_MICROUSD = 3_250_000


def request_json(
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: int = 30,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="POST" if data is not None else "GET",
    )
    with urlopen(request, timeout=timeout) as response:
        if response.status not in {200, 201}:
            raise RuntimeError(f"Unexpected HTTP status {response.status} for {url}")
        body = json.loads(response.read().decode("utf-8"))
        if not isinstance(body, dict):
            raise RuntimeError(f"Expected JSON object from {url}")
        return body


def render_human_brief(task: dict[str, Any]) -> str:
    expected = task["expected_final_state"]
    supplied = (
        f"Supplied immutable synthetic values: target employee ID {expected['employee']['id']}; "
        f"ticket title {expected['ticket']['title']} with open status; username "
        f"{expected['iam_account']['username']} with ordinary employee role and active status; "
        f"asset tag {expected['asset']['asset_tag']}, laptop model "
        f"{expected['asset']['model']}, assigned status; mailbox "
        f"{expected['mailbox']['address']} with active status."
    )
    return " ".join((task["title"], *task["instructions"], supplied))


def run_task(task_id: str) -> dict[str, Any]:
    task = request_json(f"{SANDBOX_API}/api/arena/tasks/{task_id}")
    first_seed = request_json(f"{SANDBOX_API}/api/arena/tasks/{task_id}/reset-seed", {})
    second_seed = request_json(f"{SANDBOX_API}/api/arena/tasks/{task_id}/reset-seed", {})
    if first_seed != second_seed:
        raise RuntimeError(f"Reset/Seed mismatch for {task_id}")

    run: dict[str, Any]
    outer_error: str | None = None
    try:
        run = request_json(
            f"{REAL_AGENT}/api/agent/runs",
            {
                "schema_version": "w4-dom-agent-run/1.0",
                "task_id": task_id,
                "instruction": render_human_brief(task),
                "model": MODEL,
                "budget": PER_TASK_BUDGET,
            },
            timeout=220,
        )
    except (HTTPError, OSError, RuntimeError) as exc:
        outer_error = f"{type(exc).__name__}: agent invocation failed"
        run = {
            "status": "outer_error",
            "terminal_reason": outer_error,
            "steps": 0,
            "action_count": 0,
            "model_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_microusd": 0,
        }

    grade = request_json(f"{SANDBOX_API}/api/arena/tasks/{task_id}/grade", {})
    return {
        "task_id": task_id,
        "spec_checksum": task["canonical_checksum"],
        "seed_checksum": first_seed["seed_summary"]["fact_checksum"],
        "fixture_version": task["fixture"]["fixture_version"],
        "model": "gpt-5.6-terra",
        "prompt_config_version": PROMPT_CONFIG_VERSION,
        "agent_status": run["status"],
        "terminal_reason": run["terminal_reason"],
        "steps": run["steps"],
        "actions": run["action_count"],
        "model_calls": run["model_calls"],
        "input_tokens": run["input_tokens"],
        "output_tokens": run["output_tokens"],
        "cost_microusd": run["cost_microusd"],
        "grade": grade["total_score"],
        "passed": grade["passed"],
        "retries": 0,
        "human_intervention": False,
        "outer_error": outer_error,
    }


def main() -> None:
    started = monotonic()
    if request_json(f"{CONTROL_API}/healthz")["status"] != "ok":
        raise RuntimeError("Control API is unhealthy")
    if request_json(f"{SANDBOX_API}/healthz")["status"] != "ok":
        raise RuntimeError("Sandbox API is unhealthy")
    if request_json(f"{REAL_AGENT}/healthz")["status"] != "ok":
        raise RuntimeError("Real Agent is unhealthy")

    results: list[dict[str, Any]] = []
    for task_id in TASK_IDS:
        if monotonic() - started >= MAX_TOTAL_SECONDS:
            raise RuntimeError("Aggregate wall-time budget exhausted before next task")
        result = run_task(task_id)
        results.append(result)
        print(json.dumps(result, sort_keys=True), flush=True)

    elapsed = monotonic() - started
    totals = {
        "tasks": len(results),
        "passed": sum(1 for item in results if item["passed"] is True),
        "model_calls": sum(int(item["model_calls"]) for item in results),
        "input_tokens": sum(int(item["input_tokens"]) for item in results),
        "output_tokens": sum(int(item["output_tokens"]) for item in results),
        "cost_microusd": sum(int(item["cost_microusd"]) for item in results),
        "elapsed_seconds": round(elapsed, 3),
        "retries": 0,
    }
    if totals["model_calls"] > MAX_TOTAL_CALLS:
        raise RuntimeError("Aggregate model-call cap exceeded")
    if totals["input_tokens"] > MAX_TOTAL_INPUT_TOKENS:
        raise RuntimeError("Aggregate input-token cap exceeded")
    if totals["output_tokens"] > MAX_TOTAL_OUTPUT_TOKENS:
        raise RuntimeError("Aggregate output-token cap exceeded")
    if totals["cost_microusd"] > MAX_TOTAL_COST_MICROUSD:
        raise RuntimeError("Aggregate cost cap exceeded")
    if elapsed > MAX_TOTAL_SECONDS:
        raise RuntimeError("Aggregate wall-time cap exceeded")
    print(json.dumps({"aggregate": totals}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
