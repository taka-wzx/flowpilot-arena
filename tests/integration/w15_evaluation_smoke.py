"""Development-only deterministic W15 evaluation smoke."""

from w15_evaluation import canonical_bytes, development_smoke_summary, load_protocol


def main() -> int:
    protocol = load_protocol()
    summary = development_smoke_summary(protocol)
    assert summary["attempts"] == 33
    assert summary["reporting_executed"] is False
    assert summary["validation_executed"] is False
    assert summary["external_benchmark_executed"] is False
    assert summary["finished_ungraded"] == 33
    assert summary["independent_grade_observations"] == 33
    assert summary["security_failures"] == 0
    assert summary["duplicate_business_effects"] == 0
    assert summary["real_calls"] == 0
    assert summary["real_cost_microusd"] == 0
    print(canonical_bytes(summary).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
