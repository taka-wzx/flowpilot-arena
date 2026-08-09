"""Unit tests for the W16 deterministic demo contract."""

from __future__ import annotations

import json

from w16_demo import EVENT_CODES, build_demo, canonical_bytes


def test_demo_is_byte_deterministic() -> None:
    first = canonical_bytes(build_demo())
    second = canonical_bytes(build_demo())
    assert first == second
    assert len(build_demo()["trace_hash"]) == 64


def test_demo_is_redacted_and_closed() -> None:
    demo = build_demo()
    assert tuple(event["code"] for event in demo["events"]) == EVENT_CODES
    assert demo["synthetic"] is True
    assert demo["account_ref"] == "acct_synthetic_demo"
    assert demo["agent_terminal_state"] == "finished_ungraded"
    assert demo["grader"] == {
        "authority": "independent-sandbox-database-fact",
        "outcome": "passed",
    }
    encoded = json.dumps(demo, sort_keys=True)
    for forbidden in ("Bearer ", "Cookie", "password", "private_key", "DSN", "nonce="):
        assert forbidden not in encoded
    assert demo["real_calls"] == 0
    assert demo["real_cost_microusd"] == 0
