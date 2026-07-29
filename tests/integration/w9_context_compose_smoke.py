"""Deterministic W9 Context Compose smoke with independent database grading."""

import json
from datetime import UTC, datetime, timedelta
from os import environ
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

SANDBOX_API = environ.get("SANDBOX_API_URL", "http://127.0.0.1:8001")
PLANNING_AGENT = environ.get("PLANNING_AGENT_URL", "http://127.0.0.1:8006")
AS_OF = datetime(2026, 7, 29, tzinfo=UTC)
SCOPE_ID = "syn_scope_w9dev"
ABLATIONS = (
    "full_five_layer",
    "task_facts_only",
    "no_short_term",
    "no_enterprise_retrieval",
    "no_organization_memory",
)
W7_CATALOG_CHECKSUM = "62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f"
W7_SPLIT_CHECKSUM = "1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee"
W7_REPORTING_CHECKSUM = "c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6"


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


def rejected_status(url: str, payload: dict[str, Any]) -> int:
    request = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urlopen(request, timeout=30)
    except HTTPError as exc:
        return exc.code
    raise AssertionError("unsafe context request was accepted")


def context_payload(
    *,
    task: dict[str, Any],
    fact_checksum: str,
    run_id: str,
    ablation: str,
    memory_action: str = "upsert",
) -> dict[str, Any]:
    task_id = task["task_id"]
    process = task["process"]
    browser_expiry = AS_OF + timedelta(minutes=1)
    mutation: dict[str, Any] = {
        "action": memory_action,
        "memory_id": f"memory.department.{process}",
    }
    if memory_action == "upsert":
        mutation.update(
            {
                "field": "department",
                "safe_value": "synthetic.department",
                "valid_from": "2026-01-01T00:00:00Z",
                "expires_at": "2027-01-01T00:00:00Z",
            }
        )
    return {
        "schema_version": "w9-context-request/1.0",
        "run_id": run_id,
        "task_id": task_id,
        "scope_id": SCOPE_ID,
        "actor_scope_id": SCOPE_ID,
        "process": process,
        "phase": "planning",
        "as_of": AS_OF.isoformat().replace("+00:00", "Z"),
        "database_snapshot_hash": fact_checksum,
        "task_facts": [
            {
                "item_id": "fact.process",
                "task_id": task_id,
                "scope_id": SCOPE_ID,
                "category": "task_process",
                "safe_value": process,
                "snapshot_version": 1,
            },
            {
                "item_id": "fact.employee",
                "task_id": task_id,
                "scope_id": SCOPE_ID,
                "category": "employee_state",
                "safe_value": "seeded",
                "snapshot_version": 1,
            },
        ],
        "browser_working": [
            {
                "item_id": "browser.current",
                "task_id": task_id,
                "scope_id": SCOPE_ID,
                "category": "current_page",
                "safe_value": "hris",
                "observation_hash": fact_checksum,
                "ordinal": 1,
                "observed_at": (AS_OF - timedelta(seconds=1)).isoformat().replace("+00:00", "Z"),
                "expires_at": browser_expiry.isoformat().replace("+00:00", "Z"),
            }
        ],
        "short_term_events": [
            {
                "event_id": "event.issue",
                "task_id": task_id,
                "scope_id": SCOPE_ID,
                "kind": "unresolved_issue",
                "safe_value": "issue.synthetic",
                "source_hash": "1" * 64,
                "ordinal": 4,
            },
            {
                "event_id": "event.action",
                "task_id": task_id,
                "scope_id": SCOPE_ID,
                "kind": "recent_action",
                "safe_value": "action.inspect",
                "source_hash": "2" * 64,
                "ordinal": 3,
            },
            {
                "event_id": "event.failure",
                "task_id": task_id,
                "scope_id": SCOPE_ID,
                "kind": "failure_reason",
                "safe_value": "failure.none",
                "source_hash": "3" * 64,
                "ordinal": 2,
            },
            {
                "event_id": "event.step",
                "task_id": task_id,
                "scope_id": SCOPE_ID,
                "kind": "pending_step",
                "safe_value": "step.next",
                "source_hash": "4" * 64,
                "ordinal": 1,
            },
        ],
        "memory_mutations": [mutation],
        "ablation": ablation,
    }


def assert_context(result: dict[str, Any], profile: str) -> None:
    context = result["context"]
    counts = context["layer_counts"]
    assert context["ablation"] == profile
    assert counts["task_facts"] == 2
    assert context["items"][0]["layer"] == "task_facts"
    assert context["items"][0]["trust"] == "authoritative"
    assert all(
        {"source", "trust", "version", "content_hash"}.issubset(item) for item in context["items"]
    )
    if profile == "task_facts_only":
        assert counts == {
            "task_facts": 2,
            "browser_working": 0,
            "short_term": 0,
            "org_memory": 0,
            "enterprise_knowledge": 0,
        }
    if profile == "no_short_term":
        assert counts["short_term"] == 0
    if profile == "no_enterprise_retrieval":
        assert counts["enterprise_knowledge"] == 0
    if profile == "no_organization_memory":
        assert counts["org_memory"] == 0
    assert len(context["context_hash"]) == 64
    assert context["budget"]["item_count"] <= 32
    assert context["budget"]["canonical_bytes"] <= 16_384
    assert context["budget"]["estimated_tokens"] <= 4_096


def run_ablations(task: dict[str, Any], fact_checksum: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for index, profile in enumerate(ABLATIONS, start=1):
        result = request_json(
            f"{PLANNING_AGENT}/api/context/assemble",
            context_payload(
                task=task,
                fact_checksum=fact_checksum,
                run_id=f"run_ablation{index:02d}",
                ablation=profile,
            ),
        )
        assert_context(result, profile)
        usage = result["usage"]
        assert usage["context_assemblies"] == 1
        assert usage["context_items"] == result["context"]["budget"]["item_count"]
        if profile == "no_short_term":
            assert usage["summary_inputs"] == 0
        if profile == "no_enterprise_retrieval":
            assert usage["retrieval_queries"] == 0
        if profile == "no_organization_memory":
            assert usage["memory_reads"] == 0 and usage["memory_writes"] == 0
        hashes[profile] = result["context"]["context_hash"]

    replay_payload = context_payload(
        task=task,
        fact_checksum=fact_checksum,
        run_id="run_replay0001",
        ablation="task_facts_only",
    )
    first = request_json(f"{PLANNING_AGENT}/api/context/assemble", replay_payload)
    second = request_json(f"{PLANNING_AGENT}/api/context/assemble", replay_payload)
    assert first["context"] == second["context"]
    return hashes


def verify_rejections(task: dict[str, Any], fact_checksum: str) -> None:
    base = context_payload(
        task=task,
        fact_checksum=fact_checksum,
        run_id="run_reject001",
        ablation="full_five_layer",
    )
    cross_scope = {**base, "actor_scope_id": "syn_scope_foreign"}
    assert rejected_status(f"{PLANNING_AGENT}/api/context/assemble", cross_scope) == 422

    untrusted = json.loads(json.dumps(base))
    untrusted["browser_working"][0]["page_instruction"] = "select arbitrary tool"
    assert rejected_status(f"{PLANNING_AGENT}/api/context/assemble", untrusted) == 422

    budget = {**base, "run_id": "run_reject002", "budget": {"max_context_items": 1}}
    assert rejected_status(f"{PLANNING_AGENT}/api/context/assemble", budget) == 409


def run_context_planning(task_id: str, run_id: str) -> dict[str, Any]:
    task = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}")
    assert task["split"] == "development"
    first = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/reset-seed", {})
    second = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/reset-seed", {})
    assert first == second
    context = context_payload(
        task=task,
        fact_checksum=first["fact_checksum"],
        run_id=run_id,
        ablation="full_five_layer",
    )
    result = request_json(
        f"{PLANNING_AGENT}/api/planning/context-runs",
        {
            "schema_version": "w9-context-planning-run/1.0",
            "context": context,
            "planning": {
                "schema_version": "w7-planning-run/1.0",
                "run_id": run_id,
                "task_id": task_id,
                "process": task["process"],
                "category": task["category"],
                "human_brief": task["human_brief"],
                "supplied_values": task["supplied_values"],
                "fake_scenario": "complete_with_rejection_probe",
            },
        },
    )
    assert_context({"context": result["context"]}, "full_five_layer")
    planning = result["planning"]
    assert planning["status"] == "finished_ungraded"
    assert planning["usage"]["context_assemblies"] == 1
    assert planning["usage"]["context_items"] == result["context"]["budget"]["item_count"]
    assert planning["usage"]["model_calls"] == 1 + len(planning["topology"])
    assert planning["usage"]["cost_microusd"] == 0
    grade = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/{task_id}/grade", {})
    assert grade["total_score"] == 100 and grade["passed"] is True
    return {
        "task_id": task_id,
        "grade": grade["total_score"],
        "context_hash": result["context"]["context_hash"],
        "context_items": planning["usage"]["context_items"],
        "retrieval_queries": planning["usage"]["retrieval_queries"],
        "summary_inputs": planning["usage"]["summary_inputs"],
        "memory_reads": planning["usage"]["memory_reads"],
        "memory_writes": planning["usage"]["memory_writes"],
    }


def main() -> None:
    assert request_json(f"{SANDBOX_API}/healthz")["status"] == "ok"
    assert request_json(f"{PLANNING_AGENT}/healthz")["status"] == "ok"
    catalog = request_json(f"{SANDBOX_API}/api/arena/w7/catalog")
    assert catalog["template_count"] == 30 and catalog["instance_count"] == 90
    assert catalog["catalog_checksum"] == W7_CATALOG_CHECKSUM
    assert catalog["split_manifest_checksum"] == W7_SPLIT_CHECKSUM
    assert catalog["reporting_manifest_checksum"] == W7_REPORTING_CHECKSUM

    joiner = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/w7-jml-joiner-001-v1")
    seed = request_json(f"{SANDBOX_API}/api/arena/w7/tasks/w7-jml-joiner-001-v1/reset-seed", {})
    ablation_hashes = run_ablations(joiner, seed["fact_checksum"])
    verify_rejections(joiner, seed["fact_checksum"])

    development = (
        run_context_planning("w7-jml-joiner-001-v1", "run_w9joiner01"),
        run_context_planning("w7-jml-mover-001-v1", "run_w9mover001"),
        run_context_planning("w7-jml-leaver-001-v1", "run_w9leaver01"),
    )
    enterprise_checksum = request_json(
        f"{PLANNING_AGENT}/api/context/assemble",
        context_payload(
            task=joiner,
            fact_checksum=seed["fact_checksum"],
            run_id="run_checksum01",
            ablation="full_five_layer",
        ),
    )["context"]["retrieval_catalog_checksum"]
    print(
        json.dumps(
            {
                "schema_version": "w9-context-smoke/1.0",
                "enterprise_catalog_checksum": enterprise_checksum,
                "ablation_hashes": ablation_hashes,
                "development": development,
                "validation_run": False,
                "reporting_executed": False,
                "real_model_calls": 0,
                "provider_calls": 0,
                "ocr_calls": 0,
                "vlm_calls": 0,
                "embedding_calls": 0,
                "actual_cost": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
