"""Trusted host/container pair for real W8 Compose restart acceptance."""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import time
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from w8_recovery_compose_smoke import (
    NAMESPACE,
    SANDBOX_API,
    TASK_QUEUE,
    encrypted_start,
    request_json,
)

BROWSER_WORKER = os.environ.get("BROWSER_WORKER_URL", "http://browser-worker:8002").rstrip("/")
READY_PREFIX = "W8_RESTART_READY "
RESULT_PREFIX = "W8_RESTART_RESULT "


def post_json(url: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    request = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode())
    except HTTPError as exc:
        body = json.loads(exc.read().decode())
        return exc.code, body


def create_stale_probe() -> tuple[str, dict[str, object]]:
    status, created = post_json(
        f"{BROWSER_WORKER}/api/browser/recovery-sessions",
        {
            "schema_version": "w8-recovery-session/1.0",
            "initial_path": "/hris",
            "session_epoch": 1,
        },
    )
    assert status == 201
    observation = created["observation"]
    nested = observation["observation"]
    element = nested["interactive_elements"][0]
    envelope: dict[str, object] = {
        "schema_version": "w8-recovery-action-envelope/1.0",
        "session_id": created["session_id"],
        "session_epoch": 1,
        "generation": observation["generation"],
        "modality": "dom",
        "action": {
            "action_id": "act_w8_stale_probe",
            "type": "read",
            "observation_id": nested["observation_id"],
            "element_ref": element["element_ref"],
        },
        "idempotency": None,
    }
    return str(created["session_id"]), envelope


async def run_container_case(scenario: str) -> None:
    if scenario not in {"browser_worker_restart_once", "recovery_worker_restart_once"}:
        raise ValueError("unsupported restart scenario")
    ordinal = 81 if scenario == "browser_worker_restart_once" else 82
    task_id = "w7-jml-mover-001-v1"
    task = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}")
    first = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/reset-seed", {})
    second = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/reset-seed", {})
    assert first == second
    stale_probe = create_stale_probe() if scenario == "browser_worker_restart_once" else None
    start, sentinels = encrypted_start(task=task, scenario=scenario, ordinal=ordinal)
    client = await Client.connect(
        os.environ.get("TEMPORAL_ADDRESS", "temporal:7233"),
        namespace=NAMESPACE,
        data_converter=pydantic_data_converter,
    )
    handle = await client.start_workflow(
        "FlowPilotDurableRecoveryWorkflow",
        start,
        id=start["workflow_id"],
        task_queue=TASK_QUEUE,
        execution_timeout=timedelta(seconds=300),
    )
    print(f"{READY_PREFIX}{scenario}", flush=True)
    result = await handle.result()
    grade = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/grade", {})
    assert result["status"] == "finished_ungraded", result
    assert grade["passed"] is True and grade["total_score"] == 100
    assert result["usage"]["duplicate_side_effects"] == 0
    if scenario == "browser_worker_restart_once":
        assert result["session_epoch"] == 2
        assert result["usage"]["session_recoveries"] == 1
        assert stale_probe is not None
        session_id, envelope = stale_probe
        status, _ = post_json(
            f"{BROWSER_WORKER}/api/browser/recovery-sessions/{session_id}/actions",
            envelope,
        )
        assert status in {404, 409}, status
    else:
        assert result["session_epoch"] == 1
        assert result["usage"]["retries"] == 1
        assert result["usage"]["activity_attempts"] >= 6
    planning_usage = result["usage"]["planning_usage"]
    assert planning_usage["plan_generations"] >= 1
    assert planning_usage["executed_steps"] >= 3
    assert planning_usage["worker_actions"] >= 1
    assert planning_usage["verifier_calls"] >= 3
    history = await handle.fetch_history()
    serialized = json.dumps(history.to_json_dict(), sort_keys=True)
    assert all(sentinel not in serialized for sentinel in sentinels)
    print(
        RESULT_PREFIX
        + json.dumps(
            {
                "scenario": scenario,
                "status": result["status"],
                "grade": grade["total_score"],
                "session_epoch": result["session_epoch"],
                "checkpoints": result["checkpoint_count"],
                "activity_attempts": result["usage"]["activity_attempts"],
                "retries": result["usage"]["retries"],
                "session_recoveries": result["usage"]["session_recoveries"],
                "duplicate_side_effects": result["usage"]["duplicate_side_effects"],
                "history_plaintext_matches": 0,
                "old_reference_rejected": scenario == "browser_worker_restart_once",
                "planning_usage": planning_usage,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def compose_command(compose_file: Path) -> list[str]:
    standalone = shutil.which("docker-compose")
    if standalone is not None:
        return [standalone, "-f", str(compose_file)]
    docker = shutil.which("docker")
    if docker is None:
        raise RuntimeError("Docker Compose is unavailable")
    return [docker, "compose", "-f", str(compose_file)]


def wait_healthy(service: str, timeout_seconds: int = 90) -> None:
    container = f"flowpilot-arena-w8-{service}-1"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip() == "healthy":
            return
        time.sleep(1)
    raise RuntimeError(f"{service} did not become healthy")


def host_case(compose: list[str], scenario: str) -> dict[str, object]:
    service = "browser-worker" if scenario == "browser_worker_restart_once" else "recovery-worker"
    command = [
        *compose,
        "--profile",
        "recovery-acceptance",
        "run",
        "--rm",
        "recovery-acceptance-smoke",
        "python",
        "w8_restart_driver.py",
        "--container-case",
        scenario,
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
    )
    assert process.stdout is not None
    result: dict[str, object] | None = None
    restarted = False
    for line in process.stdout:
        print(line, end="")
        stripped = line.strip()
        if stripped == f"{READY_PREFIX}{scenario}" and not restarted:
            time.sleep(2)
            subprocess.run([*compose, "restart", service], check=True, env=os.environ.copy())
            wait_healthy(service)
            restarted = True
        if stripped.startswith(RESULT_PREFIX):
            result = json.loads(stripped.removeprefix(RESULT_PREFIX))
    return_code = process.wait()
    if return_code != 0 or not restarted or result is None:
        raise RuntimeError(f"restart case failed: {scenario} (exit {return_code})")
    return result


def run_host(compose_file: Path, cases: tuple[str, ...]) -> None:
    if "RECOVERY_ENVELOPE_KEY" not in os.environ:
        raise RuntimeError("RECOVERY_ENVELOPE_KEY must be runtime-injected")
    compose = compose_command(compose_file)
    results = [host_case(compose, scenario) for scenario in cases]
    print(
        json.dumps(
            {
                "schema_version": "w8-restart-smoke/1.0",
                "results": results,
                "external_model_calls": 0,
                "actual_model_cost": 0,
                "reporting_executed": False,
            },
            sort_keys=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host-orchestrated", action="store_true")
    parser.add_argument(
        "--container-case",
        choices=("browser_worker_restart_once", "recovery_worker_restart_once"),
    )
    parser.add_argument(
        "--case",
        choices=("all", "browser", "recovery"),
        default="all",
    )
    parser.add_argument(
        "--compose-file",
        type=Path,
        default=Path("deploy/compose/compose.yaml"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.container_case is not None:
        asyncio.run(run_container_case(args.container_case))
        return
    if not args.host_orchestrated:
        raise SystemExit("This trusted driver requires --host-orchestrated")
    cases = {
        "all": ("browser_worker_restart_once", "recovery_worker_restart_once"),
        "browser": ("browser_worker_restart_once",),
        "recovery": ("recovery_worker_restart_once",),
    }[args.case]
    run_host(args.compose_file.resolve(), cases)


if __name__ == "__main__":
    main()
