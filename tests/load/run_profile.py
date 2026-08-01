"""Run static, bounded Development, or single guarded W12 Validation load modes."""

import argparse
import concurrent.futures
import json
import os
import time
from pathlib import Path
from profile import (
    FORMAL_SEQUENCE,
    FORMAL_VALIDATION_ORDINAL,
    PROFILE_SHA256,
    RESULT_SCHEMA_SHA256,
    acceptance_failures,
    finalize_result,
    load_frozen_profile,
    load_json,
    percentiles,
    validate_result,
)
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

import gevent  # type: ignore[import-untyped]
from locust.env import Environment

import locustfile

ALPHA = "org_syn_alpha_0001"
BETA = "org_syn_beta_0001"
CONTROL_API_PORT = 8000
IDENTITIES = {
    ALPHA: (
        "syn-alpha-admin",
        "syn-alpha-operator",
        "syn-alpha-auditor",
        "syn-alpha-manager",
        "syn-alpha-security",
        "syn-alpha-noauthority",
    ),
    BETA: (
        "syn-beta-admin",
        "syn-beta-operator",
        "syn-beta-auditor",
        "syn-beta-manager",
        "syn-beta-security",
        "syn-beta-noauthority",
    ),
}
WRITER_INDEXES = (0, 1, 3, 4, 5)
FORMAL_OBSERVATION_KEYS = frozenset(
    {
        "setup_accepted",
        "backpressure_probe_requests",
        "backpressured",
        "queue_wait_us",
        "max_browser_concurrency",
        "run_terminals",
        "worker",
        "workflow",
        "receipts",
        "security",
        "audit",
        "real_calls",
        "cost_microusd",
        "host",
    }
)
FORMAL_METRIC_KEYS = frozenset(
    {
        "users",
        "protected_requests",
        "api_latency_us",
        "expected_http",
        "unexpected_http",
        "unexpected_5xx",
        "accepted",
        "accepted_runs",
        "rate_probe_requests",
        "rate_limited",
    }
)
FORMAL_VALIDATION_GUARD = f"w12-validation-ordinal-{FORMAL_VALIDATION_ORDINAL}\n"


def _fixed_url(value: str, *, hostname: str, path: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != hostname
        or parsed.path != path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("load endpoint differs from the frozen Compose topology")
    return value.rstrip("/")


def _token(token_url: str, username: str, password: str) -> str:
    request = Request(
        token_url,
        data=urlencode(
            {
                "grant_type": "password",
                "client_id": "flowpilot-control-web",
                "username": username,
                "password": password,
                "scope": "openid",
            }
        ).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("local synthetic identity endpoint was unavailable") from exc
    access_token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(access_token, str) or payload.get("token_type") != "Bearer":
        raise RuntimeError("local synthetic identity response was invalid")
    return access_token


def acquire_tokens() -> locustfile.TokenPool:
    token_url = _fixed_url(
        os.environ.get(
            "KEYCLOAK_TOKEN_URL",
            "http://keycloak:8080/realms/flowpilot/protocol/openid-connect/token",
        ),
        hostname="keycloak",
        path="/realms/flowpilot/protocol/openid-connect/token",
    )
    password = os.environ.get("W12_SYNTHETIC_PASSWORD", "")
    if not password:
        raise ValueError("W12 synthetic password is required at runtime")
    readers: dict[str, tuple[str, ...]] = {}
    writers: dict[str, tuple[str, ...]] = {}
    for organization_id, usernames in IDENTITIES.items():
        values = tuple(_token(token_url, username, password) for username in usernames)
        readers[organization_id] = values
        writers[organization_id] = tuple(values[index] for index in WRITER_INDEXES)
    return locustfile.TokenPool(readers=readers, writers=writers)


def run_locust(
    *,
    users: int,
    spawn_rate: int,
    steady_seconds: int,
    tokens: locustfile.TokenPool | None = None,
    include_run_references: bool = False,
) -> dict[str, Any]:
    if tokens is None:
        tokens = acquire_tokens()
    locustfile.configure_load(users=users, steady_seconds=steady_seconds, tokens=tokens)
    environment = Environment(user_classes=[locustfile.FlowPilotLoadUser])
    runner = environment.create_local_runner()
    runner.start(user_count=users, spawn_rate=spawn_rate)
    timeout = steady_seconds + max(1, users // max(1, spawn_rate)) + 30
    if not locustfile.COORDINATOR.completed.wait(timeout=timeout):
        runner.quit()
        coordinator = locustfile.COORDINATOR
        runner_error_count = sum(
            int(details.get("count", 0))
            for details in runner.exceptions.values()
            if isinstance(details, dict)
        )
        raise RuntimeError(
            "bounded load users did not finish "
            f"(arrived={coordinator.arrived}, released={coordinator.released}, "
            f"task_started={coordinator.task_started}, finished={coordinator.finished}, "
            f"protected={len(coordinator.latencies_us)}, "
            f"accepted={len(coordinator.accepted_runs)}, "
            f"runner_users={runner.user_count}, barrier={int(coordinator.barrier.is_set())}, "
            f"runner_errors={runner_error_count})"
        )
    deadline = locustfile.COORDINATOR.started_at + steady_seconds
    gevent.sleep(max(0.0, deadline - time.perf_counter()))
    runner.quit()
    coordinator = locustfile.COORDINATOR
    protected = len(coordinator.latencies_us)
    if protected != users * len(FORMAL_SEQUENCE):
        raise RuntimeError("protected request budget changed")
    metrics = {
        "users": users,
        "protected_requests": protected,
        "api_latency_us": percentiles(coordinator.latencies_us),
        "expected_http": dict(coordinator.expected_http),
        "unexpected_http": dict(coordinator.unexpected_http),
        "unexpected_5xx": coordinator.unexpected_5xx,
        "accepted": len(coordinator.accepted_runs),
    }
    if include_run_references:
        metrics["accepted_runs"] = [
            {"organization_id": organization_id, "run_id": run_id}
            for run_id, organization_id in sorted(coordinator.accepted_runs.items())
        ]
    return metrics


def _read_probe(reference: tuple[str, str]) -> tuple[int, int | None]:
    organization_id, token = reference
    request = Request(
        (
            f"http://control-api:{CONTROL_API_PORT}/api/v1/organizations/"
            f"{organization_id}/production-runs/run_missing_0001"
        ),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=10) as response:
            response.read()
            return response.status, None
    except HTTPError as exc:
        exc.read()
        retry_after = exc.headers.get("Retry-After")
        return exc.code, int(retry_after) if retry_after is not None else None
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("local W12 rate-probe endpoint was unavailable") from exc


def run_rate_probe(tokens: locustfile.TokenPool) -> dict[str, int]:
    readers = (tokens.readers[ALPHA], tokens.readers[BETA])
    if len(readers[0]) != 6 or len(readers[1]) != 6:
        raise RuntimeError("frozen rate-probe identity distribution changed")

    def exhaust_and_probe(item: tuple[tuple[str, str], int]) -> int:
        reference, probe_count = item
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            warmup = tuple(executor.map(_read_probe, (reference,) * 30))
            if any(status not in {404, 429} for status, _ in warmup):
                raise RuntimeError("rate-probe setup returned an unexpected status")
            for _ in range(80):
                status, retry_after = _read_probe(reference)
                if status not in {404, 429}:
                    raise RuntimeError("rate-probe setup returned an unexpected status")
                if status != 429:
                    continue
                if retry_after is None or not 1 <= retry_after <= 30:
                    raise RuntimeError("rate probe returned an invalid Retry-After")
                probes = tuple(executor.map(_read_probe, (reference,) * probe_count))
                if not all(probe_status == 429 for probe_status, _ in probes):
                    continue
                if any(
                    probe_retry is None or not 1 <= probe_retry <= 30 for _, probe_retry in probes
                ):
                    raise RuntimeError("formal rate probes returned an invalid Retry-After")
                return len(probes)
        raise RuntimeError("rate-probe actor bucket did not become exhausted")

    rate_limited = 0
    for reader_index in range(6):
        probe_count = 5 if reader_index == 0 else 4
        pair = (
            ((ALPHA, readers[0][reader_index]), probe_count),
            ((BETA, readers[1][reader_index]), probe_count),
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            rate_limited += sum(executor.map(exhaust_and_probe, pair))
    if rate_limited != 50:
        raise RuntimeError("formal rate-probe request count changed")
    time.sleep(2.1)
    return {"rate_probe_requests": rate_limited, "rate_limited": rate_limited}


def _formal_result(
    metrics: dict[str, Any],
    observations: dict[str, Any],
    cleanup: dict[str, int],
) -> dict[str, Any]:
    if set(metrics) != FORMAL_METRIC_KEYS:
        raise ValueError("formal measurements differ from the frozen closed schema")
    if set(observations) != FORMAL_OBSERVATION_KEYS:
        raise ValueError("formal observations differ from the frozen closed schema")
    result: dict[str, Any] = {
        "schema_version": "w12-load-result/1.0",
        "profile_version": "w12-validation-50x4/1.0",
        "seed": 20260801,
        "validation_ordinal": FORMAL_VALIDATION_ORDINAL,
        "validation_run": True,
        "reporting_executed": False,
        "tool": "locust",
        "tool_version": "2.46.1",
        "users": metrics["users"],
        "organizations": 2,
        "protected_requests": metrics["protected_requests"],
        "rate_probe_requests": metrics["rate_probe_requests"],
        "backpressure_probe_requests": observations["backpressure_probe_requests"],
        "api_latency_us": metrics["api_latency_us"],
        "queue_wait_us": observations["queue_wait_us"],
        "max_browser_concurrency": observations["max_browser_concurrency"],
        "accepted": metrics["accepted"] + observations["setup_accepted"],
        "rate_limited": metrics["rate_limited"],
        "backpressured": observations["backpressured"],
        "expected_http": metrics["expected_http"],
        "unexpected_http": metrics["unexpected_http"],
        "unexpected_5xx": metrics["unexpected_5xx"],
        "run_terminals": observations["run_terminals"],
        "worker": observations["worker"],
        "workflow": observations["workflow"],
        "receipts": observations["receipts"],
        "security": observations["security"],
        "audit": observations["audit"],
        "real_calls": observations["real_calls"],
        "cost_microusd": observations["cost_microusd"],
        "host": observations["host"],
        "cleanup": cleanup,
    }
    return finalize_result(result)


def run_development() -> int:
    metrics = run_locust(users=5, spawn_rate=5, steady_seconds=5)
    summary = {
        "schema_version": "w12-development-load/1.0",
        "validation_run": False,
        "reporting_executed": False,
        **metrics,
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0 if metrics["protected_requests"] == 100 and metrics["unexpected_5xx"] == 0 else 1


def run_ci_acceptance() -> int:
    metrics = run_locust(users=50, spawn_rate=10, steady_seconds=30)
    expected = {"200": 750, "202": 200, "404": 50, "409": 0, "412": 0, "429": 0, "503": 0}
    passed = (
        metrics["protected_requests"] == 1_000
        and metrics["expected_http"] == expected
        and not any(metrics["unexpected_http"].values())
        and metrics["unexpected_5xx"] == 0
    )
    summary = {
        "schema_version": "w12-ci-load/1.0",
        "validation_run": False,
        "reporting_executed": False,
        **metrics,
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0 if passed else 1


def run_validation_measurement(metrics_path: Path, guard_path: Path) -> int:
    if guard_path.read_text(encoding="utf-8") != FORMAL_VALIDATION_GUARD:
        raise ValueError("formal Validation pre-stage guard is missing or invalid")
    tokens = acquire_tokens()
    probe = run_rate_probe(tokens)
    metrics = {
        **run_locust(
            users=50,
            spawn_rate=10,
            steady_seconds=30,
            tokens=tokens,
            include_run_references=True,
        ),
        **probe,
    }
    if set(metrics) != FORMAL_METRIC_KEYS:
        raise ValueError("formal measurements differ from the frozen closed schema")
    with metrics_path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(metrics, sort_keys=True, separators=(",", ":")) + "\n")
    print(
        json.dumps(
            {
                "schema_version": "w12-validation-measurement/1.0",
                "protected_requests": metrics["protected_requests"],
                "rate_probe_requests": metrics["rate_probe_requests"],
                "validation_ordinal": FORMAL_VALIDATION_ORDINAL,
                "validation_run": True,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


def finalize_validation(
    metrics_path: Path,
    observation_path: Path,
    output_path: Path,
    guard_path: Path,
    cleanup: dict[str, int],
) -> int:
    if guard_path.read_text(encoding="utf-8") != FORMAL_VALIDATION_GUARD:
        raise ValueError("formal Validation guard is missing or invalid")
    metrics = load_json(metrics_path)
    observations = load_json(observation_path)
    result = _formal_result(metrics, observations, cleanup)
    validate_result(result)
    failures = acceptance_failures(result)
    with output_path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(
        json.dumps(
            {
                "schema_version": result["schema_version"],
                "result_hash": result["result_hash"],
                "acceptance_failures": list(failures),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--static", action="store_true")
    mode.add_argument("--development", action="store_true")
    mode.add_argument("--ci", action="store_true")
    mode.add_argument("--validation", action="store_true")
    mode.add_argument("--finalize-validation", action="store_true")
    parser.add_argument("--observations", type=Path, default=Path("/results/observations.json"))
    parser.add_argument("--metrics", type=Path, default=Path("/results/metrics.json"))
    parser.add_argument("--output", type=Path, default=Path("/results/result.json"))
    parser.add_argument("--guard", type=Path, default=Path("/results/validation.guard"))
    parser.add_argument("--cleanup-containers", type=int)
    parser.add_argument("--cleanup-networks", type=int)
    parser.add_argument("--cleanup-volumes", type=int)
    args = parser.parse_args()
    _fixed_url(
        os.environ.get("CONTROL_API_URL", f"http://control-api:{CONTROL_API_PORT}"),
        hostname="control-api",
        path="",
    )
    profile = load_frozen_profile()
    if args.static:
        print(
            json.dumps(
                {
                    "profile_version": profile["profile_version"],
                    "profile_sha256": PROFILE_SHA256,
                    "schema_sha256": RESULT_SCHEMA_SHA256,
                    "validation_run": False,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    if args.development:
        return run_development()
    if args.ci:
        return run_ci_acceptance()
    if args.validation:
        return run_validation_measurement(args.metrics, args.guard)
    cleanup_values = (args.cleanup_containers, args.cleanup_networks, args.cleanup_volumes)
    if any(value is None or value < 0 for value in cleanup_values):
        raise ValueError("cleanup finalization requires three non-negative observed counts")
    cleanup = {
        "containers": args.cleanup_containers,
        "networks": args.cleanup_networks,
        "volumes": args.cleanup_volumes,
    }
    return finalize_validation(
        args.metrics,
        args.observations,
        args.output,
        args.guard,
        cleanup,
    )


if __name__ == "__main__":
    raise SystemExit(main())
