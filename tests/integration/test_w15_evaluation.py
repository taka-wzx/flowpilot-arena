"""W15 protocol, attempt retention, aggregation, schema, and report tests."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from w15_evaluation import (
    EXPECTED_CONFIGURATION_HASH,
    EXPECTED_CONFIGURATION_IDS,
    EXPECTED_PROTOCOL_HASH,
    EXPECTED_REPORTING_IDS,
    EXPECTED_SEEDS,
    PROTOCOL_PATH,
    REPORT_SCHEMA_PATH,
    AgentFailureReason,
    AttemptMetrics,
    AttemptRecord,
    AttemptStatus,
    BenchmarkAvailability,
    ConfigurationId,
    EvaluationConfiguration,
    EvaluationProtocol,
    GradeOutcome,
    InfrastructureReason,
    RealCallCounters,
    SecurityCounters,
    _configuration_summary,
    _pareto,
    _repeat_summary,
    canonical_bytes,
    canonical_hash,
    development_smoke_summary,
    generate_attempts,
    infrastructure_retry,
    load_protocol,
    report_schema_document,
    report_schema_hash,
    validate_attempt_set,
    write_once,
)

from flowpilot_sandbox_api.arena.catalog import get_catalog as get_w3_catalog
from flowpilot_sandbox_api.arena.jml.catalog import get_catalog as get_w7_catalog


def _zero_metrics() -> AttemptMetrics:
    return AttemptMetrics(
        subgoals_total=0,
        subgoals_completed=0,
        actions_total=0,
        error_actions=0,
        steps=0,
        plan_modifications=0,
        human_takeover=False,
        recoverable_failures=0,
        recovered_failures=0,
        api_latency_microseconds=None,
        queue_wait_microseconds=None,
        browser_concurrency=0,
        worker_recoveries=0,
        database_lock_conflicts=0,
        duplicate_business_effects=0,
        model_calls=0,
        input_tokens=0,
        output_tokens=0,
        vlm_calls=0,
        cache_hits=0,
        cache_lookups=0,
        synthetic_cost_microusd=0,
    )


def _validated_update(attempt: AttemptRecord, **changes: object) -> AttemptRecord:
    payload = attempt.model_dump(mode="python")
    payload.update(changes)
    return AttemptRecord.model_validate(payload)


def test_protocol_freezes_split_matrix_seeds_order_and_hashes() -> None:
    protocol = load_protocol()
    assert protocol.configuration_hash == EXPECTED_CONFIGURATION_HASH
    assert protocol.protocol_hash == EXPECTED_PROTOCOL_HASH
    assert tuple(item.config_id.value for item in protocol.configurations) == (
        EXPECTED_CONFIGURATION_IDS
    )
    assert tuple(item.task_id for item in protocol.reporting_instances) == (EXPECTED_REPORTING_IDS)
    assert protocol.seeds == EXPECTED_SEEDS
    assert protocol.planned_primary_attempts == 594
    assert len({item.template_id for item in protocol.reporting_instances}) == 6
    assert len({item.canonical_checksum for item in protocol.reporting_instances}) == 18
    assert protocol.external_benchmark.availability is BenchmarkAvailability.UNAVAILABLE
    assert protocol.external_benchmark.planned_attempts == 0


def test_packaged_w3_w7_catalogs_match_the_frozen_protocol() -> None:
    protocol = load_protocol()
    w3 = get_w3_catalog()
    w7 = get_w7_catalog()
    summary = w7.summary()
    reporting_entries = tuple(item for item in w7.entries() if item.split == "reporting")
    assert w3.canonical_checksum == protocol.w3_catalog_checksum
    assert summary.catalog_checksum == protocol.w7_catalog_checksum
    assert summary.split_manifest_checksum == protocol.w7_split_manifest_checksum
    assert summary.reporting_manifest_checksum == protocol.w7_reporting_manifest_checksum
    assert tuple(item.task_id for item in reporting_entries) == tuple(
        item.task_id for item in protocol.reporting_instances
    )
    assert tuple(item.canonical_checksum for item in reporting_entries) == tuple(
        item.canonical_checksum for item in protocol.reporting_instances
    )


def test_protocol_hash_mismatch_and_unknown_fields_fail_closed() -> None:
    payload = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    payload["seeds"][0] += 1
    with pytest.raises(ValidationError, match="seed order changed"):
        EvaluationProtocol.model_validate_json(json.dumps(payload))

    payload = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    payload["protocol_hash"] = "0" * 64
    with pytest.raises(ValidationError, match="protocol hash mismatch"):
        EvaluationProtocol.model_validate_json(json.dumps(payload))

    payload = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    payload["security_ablation"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        EvaluationProtocol.model_validate_json(json.dumps(payload))


def test_security_identity_approval_and_grader_are_not_configuration_fields() -> None:
    prohibited = {
        "security",
        "identity",
        "tenant_isolation",
        "rbac",
        "approval",
        "browser_isolation",
        "grader",
    }
    assert prohibited.isdisjoint(EvaluationConfiguration.model_fields)
    payload = load_protocol().configurations[0].model_dump(mode="python")
    payload["grader"] = False
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        EvaluationConfiguration.model_validate(payload)


def test_attempt_generation_is_complete_ordered_paired_and_deterministic() -> None:
    protocol = load_protocol()
    first = generate_attempts(
        protocol,
        instances=protocol.development_smoke_instances,
        seeds=protocol.seeds,
    )
    second = generate_attempts(
        protocol,
        instances=protocol.development_smoke_instances,
        seeds=protocol.seeds,
    )
    assert first == second
    assert len(first) == 99
    assert len({item.attempt_reference for item in first}) == 99
    assert first[0].configuration_id is ConfigurationId.DOM_REACT
    assert first[0].seed == EXPECTED_SEEDS[0]
    assert first[1].seed == EXPECTED_SEEDS[1]
    assert first[2].seed == EXPECTED_SEEDS[2]
    assert first[9].configuration_id is ConfigurationId.VISION_ONLY_REACT
    assert all(item.retry_ordinal == 0 for item in first)
    assert all(item.status is AttemptStatus.COMPLETED for item in first)
    assert all(item.terminal_status == "finished_ungraded" for item in first)
    assert all(item.grade_outcome is not GradeOutcome.NOT_GRADED for item in first)
    assert all(item.metrics.security.total == 0 for item in first)
    assert all(item.metrics.real_calls.total == 0 for item in first)
    validate_attempt_set(
        protocol,
        first,
        instances=protocol.development_smoke_instances,
        seeds=protocol.seeds,
    )


def test_attempt_closed_statuses_and_unknown_fields_are_strict() -> None:
    protocol = load_protocol()
    attempt = generate_attempts(
        protocol,
        instances=protocol.development_smoke_instances,
        seeds=(protocol.seeds[0],),
    )[0]
    payload = attempt.model_dump(mode="python")
    payload["raw_task"] = "forbidden"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AttemptRecord.model_validate(payload)

    with pytest.raises(ValidationError, match="timeout status/reason disagree"):
        _validated_update(
            attempt,
            status=AttemptStatus.TIMED_OUT,
            terminal_status=None,
            grade_outcome=GradeOutcome.NOT_GRADED,
            agent_failure_reason=AgentFailureReason.ACTION_ERROR,
        )

    with pytest.raises(ValidationError, match="non-completed attempt"):
        _validated_update(attempt, status=AttemptStatus.MISSING)


def test_missing_failure_and_infrastructure_retry_are_retained_append_only() -> None:
    protocol = load_protocol()
    attempts = list(
        generate_attempts(
            protocol,
            instances=protocol.development_smoke_instances,
            seeds=protocol.seeds,
        )
    )
    missing = _validated_update(
        attempts[0],
        status=AttemptStatus.MISSING,
        terminal_status=None,
        grade_outcome=GradeOutcome.NOT_GRADED,
        metrics=_zero_metrics(),
    )
    infrastructure = _validated_update(
        attempts[1],
        status=AttemptStatus.INFRASTRUCTURE_FAILED,
        terminal_status=None,
        grade_outcome=GradeOutcome.NOT_GRADED,
        infrastructure_reason=InfrastructureReason.SERVICE_UNAVAILABLE,
        metrics=_zero_metrics(),
    )
    attempts[0] = missing
    attempts[1] = infrastructure
    retry = infrastructure_retry(
        protocol,
        infrastructure,
        protocol.development_smoke_instances[0],
        protocol.configurations[0],
        passed=True,
    )
    records = tuple(attempts + [retry])
    validate_attempt_set(
        protocol,
        records,
        instances=protocol.development_smoke_instances,
        seeds=protocol.seeds,
    )
    assert len(records) == 100
    assert sum(item.retry_ordinal == 0 for item in records) == 99
    assert sum(item.retry_ordinal == 1 for item in records) == 1
    assert sum(item.status is AttemptStatus.MISSING for item in records) == 1
    assert sum(item.status is AttemptStatus.INFRASTRUCTURE_FAILED for item in records) == 1
    assert records[0].attempt_reference == missing.attempt_reference
    assert records[-1].primary_attempt_reference == infrastructure.attempt_reference

    duplicate_retry = retry.model_copy(update={"attempt_reference": "att_" + "f" * 24})
    with pytest.raises(ValueError, match="retry cap exceeded"):
        validate_attempt_set(
            protocol,
            records + (duplicate_retry,),
            instances=protocol.development_smoke_instances,
            seeds=protocol.seeds,
        )


def test_agent_failure_timeout_and_controlled_stop_are_not_retryable() -> None:
    protocol = load_protocol()
    attempt = generate_attempts(
        protocol,
        instances=protocol.development_smoke_instances,
        seeds=(protocol.seeds[0],),
    )[0]
    agent_failed = _validated_update(
        attempt,
        status=AttemptStatus.AGENT_FAILED,
        terminal_status=None,
        grade_outcome=GradeOutcome.NOT_GRADED,
        agent_failure_reason=AgentFailureReason.ACTION_ERROR,
    )
    with pytest.raises(ValueError, match="only a primary infrastructure failure"):
        infrastructure_retry(
            protocol,
            agent_failed,
            protocol.development_smoke_instances[0],
            protocol.configurations[0],
            passed=False,
        )


def test_report_schema_is_static_strict_and_closed() -> None:
    schema = json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema == report_schema_document()
    assert schema["additionalProperties"] is False
    assert report_schema_hash() == canonical_hash(schema)
    assert "ConfigurationId" in schema["$defs"]
    assert schema["$defs"]["ConfigurationId"]["enum"] == list(EXPECTED_CONFIGURATION_IDS)


def test_development_artifact_is_byte_stable_hashed_and_write_once(tmp_path: Path) -> None:
    protocol = load_protocol()
    first = development_smoke_summary(protocol)
    second = development_smoke_summary(protocol)
    assert first == second
    first_bytes = canonical_bytes(first)
    second_bytes = canonical_bytes(second)
    assert first_bytes == second_bytes
    assert canonical_hash(first) == canonical_hash(second)
    first_path = tmp_path / "development.json"
    write_once(first_path, first_bytes)
    assert first_path.read_bytes() == second_bytes
    assert not first_path.read_bytes().endswith(b"\n")
    with pytest.raises(FileExistsError, match="overwrite is forbidden"):
        write_once(first_path, second_bytes)


def test_aggregation_and_pareto_use_development_fixtures_only() -> None:
    protocol = load_protocol()
    attempts = generate_attempts(
        protocol,
        instances=protocol.development_smoke_instances,
        seeds=protocol.seeds,
    )
    selected = [item for item in attempts if item.configuration_id is ConfigurationId.DOM_REACT]
    repeats = []
    aggregated_attempts = []
    for seed in protocol.seeds:
        seed_attempts = [item for item in selected if item.seed == seed] * 6
        repeats.append(_repeat_summary(ConfigurationId.DOM_REACT, seed, seed_attempts))
        aggregated_attempts.extend(seed_attempts)
    summary = _configuration_summary(
        ConfigurationId.DOM_REACT,
        aggregated_attempts,
        repeats,
    )
    assert summary.planned_attempts == 54
    assert summary.status_counts.completed == 54
    assert summary.success_repeat_range.minimum <= summary.success_repeat_range.median
    assert summary.success_repeat_range.median <= summary.success_repeat_range.maximum
    assert summary.system.api_latency_microseconds.sample_count == 54
    assert summary.security.total == 0
    assert summary.cost.real_cost_microusd == 0
    higher_cost = summary.model_copy(
        update={
            "configuration_id": ConfigurationId.VISION_ONLY_REACT,
            "cost": summary.cost.model_copy(
                update={
                    "average_synthetic_cost_microusd": (
                        summary.cost.average_synthetic_cost_microusd + 1
                    )
                }
            ),
        }
    )
    pareto = _pareto((summary, higher_cost))
    assert pareto[0].dominated is False
    assert pareto[1].dominated is True


def test_report_contains_only_opaque_task_references_and_safe_fields() -> None:
    protocol = load_protocol()
    attempts = generate_attempts(
        protocol,
        instances=protocol.development_smoke_instances,
        seeds=(protocol.seeds[0],),
    )
    payload = canonical_bytes(
        {
            "attempts": [item.model_dump(mode="json") for item in attempts],
            "summary": development_smoke_summary(protocol),
        }
    ).decode()
    lowered = payload.lower()
    assert "w7-jml-" not in payload
    assert "task_id" not in payload
    for forbidden in (
        "authorization",
        "cookie",
        "password",
        "private_key",
        "approval_credential",
        "approval_nonce",
        "raw_content",
        "machine_path",
        "dsn",
        "bearer ",
    ):
        assert forbidden not in lowered
    assert all(item.task_reference.startswith("tsk_") for item in attempts)
    assert all(item.sensitive_fields_present is False for item in attempts)


def test_unit_suite_has_no_reporting_execution_call() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden_call = "build_" + "reporting_report("
    assert forbidden_call not in source


def test_development_smoke_is_separate_from_reporting() -> None:
    summary = development_smoke_summary(load_protocol())
    assert summary["attempts"] == 33
    assert summary["reporting_executed"] is False
    assert summary["validation_executed"] is False
    assert summary["external_benchmark_executed"] is False
    assert summary["finished_ungraded"] == 33
    assert summary["independent_grade_observations"] == 33
    assert summary["security_failures"] == 0
    assert summary["real_calls"] == 0


def test_defaults_are_zero_and_frozen() -> None:
    assert SecurityCounters().total == 0
    assert RealCallCounters().total == 0
