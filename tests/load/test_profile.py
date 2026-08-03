"""Static tests for the immutable W12 profile and deterministic result contract."""

import copy
import hashlib
import threading
from profile import (
    FORMAL_SEQUENCE,
    PROFILE_PATH,
    PROFILE_SHA256,
    RESULT_SCHEMA_PATH,
    RESULT_SCHEMA_SHA256,
    acceptance_failures,
    canonical_json_bytes,
    finalize_result,
    load_frozen_profile,
    load_result_schema,
    memory_bucket_mib,
    nearest_rank,
    percentiles,
    sha256_file,
    validate_result,
)

import pytest
from jsonschema import ValidationError


def _result() -> dict[str, object]:
    zeros = {code: 0 for code in ("200", "202", "404", "409", "412", "429", "503")}
    result: dict[str, object] = {
        "schema_version": "w12-load-result/1.0",
        "profile_version": "w12-validation-50x4/1.0",
        "seed": 20260801,
        "validation_ordinal": 3,
        "validation_run": True,
        "reporting_executed": False,
        "tool": "locust",
        "tool_version": "2.46.1",
        "users": 50,
        "organizations": 2,
        "protected_requests": 1000,
        "rate_probe_requests": 50,
        "backpressure_probe_requests": 50,
        "api_latency_us": {"p50": 10_000, "p95": 20_000, "p99": 30_000},
        "queue_wait_us": {"p50": 1, "p95": 2, "p99": 3},
        "max_browser_concurrency": 4,
        "accepted": 164,
        "rate_limited": 50,
        "backpressured": 50,
        "expected_http": {**zeros, "200": 750, "202": 200, "404": 50},
        "unexpected_http": zeros,
        "unexpected_5xx": 0,
        "run_terminals": {
            "waiting_approval": 50,
            "queued": 0,
            "leased": 0,
            "running": 0,
            "recovering": 0,
            "verifying": 0,
            "finished_ungraded": 8,
            "failed": 56,
            "cancelled": 50,
            "expired": 0,
        },
        "worker": {
            "claims": 64,
            "reclaims": 0,
            "stale_fence_rejections": 0,
            "stale_fence_write_successes": 0,
            "database_lock_conflicts": 0,
        },
        "workflow": {
            "duplicate_dispatches": 0,
            "duplicate_starts": 0,
            "deduplicated_starts": 0,
        },
        "receipts": {"created": 8, "replayed": 0, "mismatched": 0},
        "security": {
            "accepted_run_loss": 0,
            "duplicate_business_effects": 0,
            "approval_bypass": 0,
            "cross_tenant_leak": 0,
            "browser_context_crossflow": 0,
        },
        "audit": {
            "event_count": 1,
            "head_sequence": 1,
            "head_hash": "a" * 64,
            "verification_failures": 0,
            "duplicate_sequences": 0,
            "forks": 0,
            "broken_heads": 0,
        },
        "real_calls": {
            "idp": 0,
            "account_data": 0,
            "model": 0,
            "provider": 0,
            "ocr": 0,
            "vlm": 0,
            "embedding": 0,
            "egress": 0,
        },
        "cost_microusd": 0,
        "host": {"logical_cpu_count": 8, "memory_bucket_mib": 8192},
        "cleanup": {"containers": 0, "networks": 0, "volumes": 0},
    }
    return finalize_result(result)


def test_frozen_artifact_hashes_and_operation_counts() -> None:
    profile = load_frozen_profile()
    load_result_schema()
    assert sha256_file(PROFILE_PATH) == PROFILE_SHA256
    assert sha256_file(RESULT_SCHEMA_PATH) == RESULT_SCHEMA_SHA256
    assert len(FORMAL_SEQUENCE) == 20
    assert FORMAL_SEQUENCE.count("identity_read") == 12
    assert profile["users"] * len(FORMAL_SEQUENCE) == profile["protected_requests"]


def test_protected_task_effect_hashes_match_the_worker_contract() -> None:
    from locustfile import TASKS

    expected = {
        "w7-jml-joiner-001-v1": "9f9a16bad25c578969e92f60e982510c9be6a4fe74d9236d06e8f9d96f9ea43b",
        "w7-jml-mover-001-v1": "417392e96f16078f9d9ac6bbb00cf0169945a149f322c787b99aa90e5377712f",
        "w7-jml-leaver-001-v1": "ec514adaaaf6c5d9e3b9ac1143fa3526b93dfca511ff571dd947bdfa605fa756",
    }
    observed: dict[str, str] = {}
    for task_id, _, _, binding in TASKS:
        observed[task_id] = hashlib.sha256(
            canonical_json_bytes(
                {
                    "schema_version": "w11-action-binding/1.0",
                    "action_type": binding["action_type"],
                    "parameters": binding["parameters"],
                }
            )
        ).hexdigest()
    assert observed == expected


def test_nearest_rank_and_memory_bucketing() -> None:
    assert nearest_rank([4, 1, 3, 2], 0.50) == 2
    assert percentiles(list(range(1, 101))) == {"p50": 50, "p95": 95, "p99": 99}
    assert memory_bucket_mib(255) == 256
    assert memory_bucket_mib(8319) == 8192
    with pytest.raises(ValueError):
        nearest_rank([1], 0)


def test_rate_probe_uses_a_concurrent_burst_for_every_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import locustfile
    import run_profile

    tokens = locustfile.TokenPool(
        readers={
            run_profile.ALPHA: tuple(f"alpha-{index}" for index in range(6)),
            run_profile.BETA: tuple(f"beta-{index}" for index in range(6)),
        },
        writers={run_profile.ALPHA: (), run_profile.BETA: ()},
    )
    counts: dict[str, int] = {}
    lock = threading.Lock()

    def fake_read(reference: tuple[str, str]) -> tuple[int, int | None]:
        _, token = reference
        with lock:
            count = counts.get(token, 0) + 1
            counts[token] = count
        return (429, 1) if count > 20 else (404, None)

    monkeypatch.setattr(run_profile, "_read_probe", fake_read)
    monkeypatch.setattr(run_profile.time, "sleep", lambda _: None)

    result = run_profile.run_rate_probe(tokens)

    assert result == {"rate_probe_requests": 50, "rate_limited": 50}
    assert len(counts) == 12
    assert min(counts.values()) >= 30


def test_result_schema_hash_and_acceptance_are_fail_closed() -> None:
    result = _result()
    validate_result(result)
    assert acceptance_failures(result) == ()
    assert sum(result["run_terminals"].values()) == result["accepted"]  # type: ignore[union-attr]

    tampered = copy.deepcopy(result)
    tampered["unexpected_5xx"] = 1
    tampered = finalize_result(tampered)
    validate_result(tampered)
    assert acceptance_failures(tampered) == ("unexpected_5xx",)

    invalid = copy.deepcopy(result)
    invalid["users"] = 49
    invalid = finalize_result(invalid)
    with pytest.raises(ValidationError):
        validate_result(invalid)
