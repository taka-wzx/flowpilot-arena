"""Deterministic, redacted W16 synthetic demo trace.

This module never calls a provider, network, browser, database, or cloud API.
It emits only closed event codes and opaque synthetic references.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any

SCHEMA_VERSION = "w16-reproducible-demo/1.0"
SCENARIO = "synthetic-jml-recovery"
EVENT_CODES = (
    "observe",
    "plan",
    "execute",
    "contradiction_follow_up",
    "dom_to_vision_fallback",
    "high_risk_approval",
    "worker_restart",
    "recovered",
    "verify",
    "independent_grader",
    "trace_replay",
)
OPAQUE_ACCOUNT = "acct_synthetic_demo"
OPAQUE_TASK = "task_w16_jml_synthetic_01"


def canonical_bytes(value: Any) -> bytes:
    """Serialize JSON deterministically as compact UTF-8 bytes."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def build_demo() -> dict[str, Any]:
    """Build the fixed redacted event sequence."""

    events = [
        {"sequence": index, "code": code, "status": "observed"}
        for index, code in enumerate(EVENT_CODES, start=1)
    ]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "scenario": SCENARIO,
        "source": "local-deterministic-runner",
        "synthetic": True,
        "account_ref": OPAQUE_ACCOUNT,
        "task_ref": OPAQUE_TASK,
        "events": events,
        "agent_terminal_state": "finished_ungraded",
        "grader": {
            "authority": "independent-sandbox-database-fact",
            "outcome": "passed",
        },
        "trace_replay": {"status": "available", "content": "opaque-only"},
        "media": {
            "status": "unavailable",
            "reason": "recording-tool-not-installed",
            "static_fallback": "docs/demo.md",
        },
        "real_calls": 0,
        "real_cost_microusd": 0,
    }
    payload["trace_hash"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true", help="indent output for a human reader")
    args = parser.parse_args()
    separators = None if args.pretty else (",", ":")
    print(
        json.dumps(
            build_demo(),
            ensure_ascii=False,
            sort_keys=True,
            indent=2 if args.pretty else None,
            separators=separators,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
