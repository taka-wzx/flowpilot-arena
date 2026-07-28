import asyncio
import base64
import hashlib
import json
import os
import secrets
from datetime import timedelta
from typing import Any
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

SANDBOX_API = os.environ.get("SANDBOX_API_URL", "http://sandbox-api:8001").rstrip("/")
TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "temporal:7233")
TASK_QUEUE = "flowpilot-w8-recovery"
NAMESPACE = "flowpilot-w8"


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


def canonical(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def runtime_key() -> bytes:
    value = os.environ["RECOVERY_ENVELOPE_KEY"]
    key = base64.b64decode(value.encode(), altchars=b"-_", validate=True)
    assert len(key) == 32
    return key


def encrypted_start(
    *,
    task: dict[str, Any],
    scenario: str,
    ordinal: int,
) -> tuple[dict[str, object], tuple[str, ...]]:
    workflow_id = f"workflow_w8_{ordinal:03d}"
    run_id = f"run_w8_{ordinal:03d}"
    task_id = task["task_id"]
    plain: dict[str, object] = {
        "schema_version": "w8-plain-run-input/1.0",
        "workflow_id": workflow_id,
        "run_id": run_id,
        "task_id": task_id,
        "process": task["process"],
        "category": task["category"],
        "human_brief": task["human_brief"],
        "supplied_values": task["supplied_values"],
    }
    aad = canonical(
        {
            "schema_version": "w8-opaque-envelope/1.0",
            "key_id": "w8-local-runtime-key/1",
            "workflow_id": workflow_id,
            "run_id": run_id,
            "task_id": task_id,
        }
    )
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(runtime_key()).encrypt(nonce, canonical(plain), aad)
    start: dict[str, object] = {
        "schema_version": "w8-workflow-start/1.0",
        "workflow_id": workflow_id,
        "run_id": run_id,
        "task_id": task_id,
        "envelope": {
            "schema_version": "w8-opaque-envelope/1.0",
            "key_id": "w8-local-runtime-key/1",
            "nonce": base64.urlsafe_b64encode(nonce).decode(),
            "ciphertext": base64.urlsafe_b64encode(ciphertext).decode(),
            "associated_data_hash": hashlib.sha256(aad).hexdigest(),
        },
        "fault_scenario": scenario,
        "fault_seed": 8008,
    }
    values = task["supplied_values"]
    sentinels = (
        task["human_brief"],
        *(str(value) for key, value in values.items() if key != "process"),
        ".invalid",
        "SYN-",
        os.environ["RECOVERY_ENVELOPE_KEY"],
        os.environ["PLANNING_AGENT_URL"],
    )
    return start, sentinels


async def run_case(
    client: Client,
    *,
    task_id: str,
    scenario: str,
    ordinal: int,
    should_complete: bool,
) -> dict[str, object]:
    task = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}")
    first = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/reset-seed", {})
    second = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/reset-seed", {})
    assert first == second
    start, sentinels = encrypted_start(task=task, scenario=scenario, ordinal=ordinal)
    handle = await client.start_workflow(
        "FlowPilotDurableRecoveryWorkflow",
        start,
        id=start["workflow_id"],
        task_queue=TASK_QUEUE,
        execution_timeout=timedelta(seconds=300),
    )
    result = await handle.result()
    assert not ({"success", "passed", "score"} & set(result))
    grade = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/grade", {})
    if should_complete:
        assert result["status"] == "finished_ungraded", (scenario, result)
        assert grade["total_score"] == 100 and grade["passed"] is True
        assert result["usage"]["duplicate_side_effects"] == 0
    else:
        assert result["status"] in {"failed", "escalated"}
        assert grade["passed"] is False
    history = await handle.fetch_history()
    serialized = json.dumps(history.to_json_dict(), sort_keys=True)
    for sentinel in sentinels:
        assert sentinel not in serialized, (scenario, "plaintext_history_match")
    return {
        "scenario": scenario,
        "task_id": task_id,
        "status": result["status"],
        "terminal_reason": result["terminal_reason"],
        "grade": grade["total_score"],
        "checkpoints": result["checkpoint_count"],
        "epoch": result["session_epoch"],
        "attempts": result["usage"]["activity_attempts"],
        "retries": result["usage"]["retries"],
        "recoveries": result["usage"]["session_recoveries"],
        "receipt_creates": result["usage"]["receipt_creates"],
        "receipt_replays": result["usage"]["receipt_replays"],
        "receipt_mismatches": result["usage"]["receipt_mismatches"],
        "duplicate_side_effects": result["usage"]["duplicate_side_effects"],
        "replans": result["usage"]["replans"],
        "replaced_nodes": result["usage"]["replaced_nodes"],
        "planning_usage": result["usage"]["planning_usage"],
    }


async def main() -> None:
    client = await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=NAMESPACE,
        data_converter=pydantic_data_converter,
    )
    cases = (
        ("w7-jml-joiner-001-v1", "none", True),
        ("w7-jml-mover-001-v1", "none", True),
        ("w7-jml-leaver-001-v1", "none", True),
        ("w7-jml-mover-001-v1", "activity_pre_dispatch_once", True),
        ("w7-jml-mover-001-v1", "post_commit_pre_checkpoint_once", True),
        ("w7-jml-mover-001-v1", "browser_session_lost_once", True),
        ("w7-jml-mover-001-v1", "transient_timeout_once", True),
        ("w7-jml-mover-001-v1", "replan_eligible_once", True),
        ("w7-jml-joiner-001-v1", "permanent_failure", False),
        ("w7-jml-joiner-001-v1", "checkpoint_hash_mismatch", False),
        ("w7-jml-joiner-001-v1", "checkpoint_version_mismatch", False),
        ("w7-jml-joiner-001-v1", "idempotency_mismatch", False),
        ("w7-jml-mover-001-v1", "replan_disallowed", False),
    )
    results = []
    for ordinal, (task_id, scenario, should_complete) in enumerate(cases, start=1):
        results.append(
            await run_case(
                client,
                task_id=task_id,
                scenario=scenario,
                ordinal=ordinal,
                should_complete=should_complete,
            )
        )
    catalog = request_json(f"{SANDBOX_API}/api/arena/w7/catalog")
    print(
        json.dumps(
            {
                "schema_version": "w8-recovery-smoke/1.0",
                "catalog_checksum": catalog["catalog_checksum"],
                "split_manifest_checksum": catalog["split_manifest_checksum"],
                "reporting_manifest_checksum": catalog["reporting_manifest_checksum"],
                "development_results": results,
                "history_plaintext_matches": 0,
                "external_model_calls": 0,
                "actual_model_cost": 0,
                "validation_run": False,
                "reporting_executed": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
