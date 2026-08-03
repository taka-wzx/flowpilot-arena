"""Frozen W12 workload, result hashing, schema validation, and acceptance checks."""

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "frozen-profile.json"
RESULT_SCHEMA_PATH = ROOT / "result.schema.json"
PROFILE_SHA256 = "b0f964ac3500e7d65fc914ae9c78b9f529e7619d3cc2bd6673f4b18689b28c36"
RESULT_SCHEMA_SHA256 = "45530b83251698f155d8a51fde7a32efec7574f8970a2455fd1b930730ef8888"
FORMAL_VALIDATION_ORDINAL = 3
FORMAL_SEQUENCE = (
    "identity_read",
    "identity_read",
    "identity_read",
    "identity_read",
    "identity_read",
    "identity_read",
    "submit_first",
    "replay_first",
    "read_first",
    "mutate_first",
    "identity_read",
    "identity_read",
    "identity_read",
    "identity_read",
    "identity_read",
    "identity_read",
    "submit_second",
    "replay_second",
    "read_second",
    "closed_probe",
)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("W12 artifact must be a JSON object")
    return value


def load_frozen_profile() -> dict[str, Any]:
    if sha256_file(PROFILE_PATH) != PROFILE_SHA256:
        raise ValueError("frozen W12 profile checksum changed")
    profile = load_json(PROFILE_PATH)
    if (
        profile.get("profile_version") != "w12-validation-50x4/1.0"
        or profile.get("tool") != "locust"
        or profile.get("tool_version") != "2.46.1"
        or profile.get("protected_requests") != 1_000
        or profile.get("operations_per_user") != len(FORMAL_SEQUENCE)
    ):
        raise ValueError("frozen W12 profile values changed")
    return profile


def load_result_schema() -> dict[str, Any]:
    if sha256_file(RESULT_SCHEMA_PATH) != RESULT_SCHEMA_SHA256:
        raise ValueError("frozen W12 result schema checksum changed")
    schema = load_json(RESULT_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return schema


def nearest_rank(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    if not 0 < percentile <= 1:
        raise ValueError("percentile must be in (0, 1]")
    ordered = sorted(values)
    return ordered[math.ceil(percentile * len(ordered)) - 1]


def percentiles(values: list[int]) -> dict[str, int]:
    return {
        "p50": nearest_rank(values, 0.50),
        "p95": nearest_rank(values, 0.95),
        "p99": nearest_rank(values, 0.99),
    }


def result_hash(result: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in result.items() if key != "result_hash"}
    return hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


def finalize_result(result: dict[str, Any]) -> dict[str, Any]:
    finalized = dict(result)
    finalized["schema_sha256"] = RESULT_SCHEMA_SHA256
    finalized["result_hash"] = result_hash(finalized)
    return finalized


def validate_result(result: dict[str, Any]) -> None:
    Draft202012Validator(load_result_schema()).validate(result)
    if result["schema_sha256"] != RESULT_SCHEMA_SHA256:
        raise ValueError("result names a different schema checksum")
    if result["result_hash"] != result_hash(result):
        raise ValueError("result hash mismatch")
    if bool(result["validation_run"]) != (
        int(result["validation_ordinal"]) == FORMAL_VALIDATION_ORDINAL
    ):
        raise ValueError("Validation flag and ordinal disagree")


def acceptance_failures(result: dict[str, Any]) -> tuple[str, ...]:
    failures: list[str] = []
    checks = {
        "api_p95": int(result["api_latency_us"]["p95"]) < 500_000,
        "browser_concurrency": int(result["max_browser_concurrency"]) == 4,
        "unexpected_5xx": int(result["unexpected_5xx"]) == 0,
        "accepted_run_loss": int(result["security"]["accepted_run_loss"]) == 0,
        "duplicate_business_effects": int(result["security"]["duplicate_business_effects"]) == 0,
        "approval_bypass": int(result["security"]["approval_bypass"]) == 0,
        "cross_tenant_leak": int(result["security"]["cross_tenant_leak"]) == 0,
        "browser_context_crossflow": int(result["security"]["browser_context_crossflow"]) == 0,
        "stale_fence": int(result["worker"]["stale_fence_write_successes"]) == 0,
        "audit": int(result["audit"]["verification_failures"]) == 0,
        "real_calls": all(int(value) == 0 for value in result["real_calls"].values()),
        "cost": int(result["cost_microusd"]) == 0,
        "cleanup": all(int(value) == 0 for value in result["cleanup"].values()),
    }
    for name, passed in checks.items():
        if not passed:
            failures.append(name)
    return tuple(failures)


def logical_cpu_count() -> int:
    return max(1, os.cpu_count() or 1)


def memory_bucket_mib(total_mib: int) -> int:
    if total_mib < 256:
        return 256
    return max(256, (total_mib // 256) * 256)
