"""Development-only W16 deterministic demo smoke."""

from __future__ import annotations

from w16_demo import EVENT_CODES, build_demo, canonical_bytes


def main() -> int:
    demo = build_demo()
    assert tuple(event["code"] for event in demo["events"]) == EVENT_CODES
    assert demo["agent_terminal_state"] == "finished_ungraded"
    assert demo["grader"]["authority"] == "independent-sandbox-database-fact"
    assert demo["real_calls"] == 0
    assert demo["real_cost_microusd"] == 0
    print(canonical_bytes(demo).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
