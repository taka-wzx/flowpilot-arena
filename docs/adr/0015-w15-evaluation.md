# ADR 0015: frozen offline W15 evaluation and deterministic JSON reporting

- Status: Accepted for W15 local implementation
- Date: 2026-08-08
- Branch: `week/15-evaluation`
- Baseline: W14 merge `6bd960a031069f262fe60fbbb8bf2c65a09e409b`

## Context

W15 must unblind the W7 Reporting split exactly once, run five roadmap baselines
and six ablations with three pre-registered repetitions, retain failures, and
produce a frozen report. It must not change independent grading, product
success, identity, approval, tenant, scheduler, trace/replay, security, or any
released W1-W14 data. Real providers are prohibited, and no external Benchmark
asset or licence bundle is present locally.

The risks are Reporting contamination; result-driven protocol changes;
selective reruns; an evaluator deciding success; hidden missing attempts;
security becoming an ablation; report data flowing back into product state;
non-deterministic serialization; sensitive-content leakage; and an unavailable
external Benchmark being fabricated as a pass.

## Decision

Use the existing `tests/integration` Python 3.13 project and its locked Pydantic
dependency. Add no service, database, migration, dependency, lockfile, network,
or product implementation change.

Freeze one protocol JSON before Reporting. It names the exact W3/W7 hashes,
the 18 ordered Reporting instance IDs/checksums, 11 ordered configurations,
three fixed seeds, pairing and attempt-ID rules, closed failures/retries,
metric denominators, aggregation, targets, external-Benchmark availability,
and report schema. Canonical sorted-key compact UTF-8 JSON and SHA-256 protect
the configuration and protocol. Any mismatch hard-fails before generation.
The sealed configuration hash is
`c9ea8d997e470a7b7584e40001e8dbff349bd9a73aa80cdbf1a32b84d81d7ec5`;
the sealed protocol hash (excluding only its own field) is
`b5aa0ddd4d0d07dd3d4a26faac11c947c223b85d14ac5dbc316681edc6de1379`.

Use `w15-deterministic-synthetic-runner/1.0` for local/CI pipeline evidence.
It emits an Agent terminal observation (`finished_ungraded`) separately from a
closed synthetic Sandbox-grade observation. Reporting only aggregates the
grade field; it never promotes the Agent terminal to success and has no product
database or API route. Because the runner is a transparent fake, the report and
evidence must not claim real Agent capability or external generalization.

Generate all 594 primary attempts in exact configuration/task/seed order.
Retain every planned cell. Agent failures/timeouts/stops are not retried. A
single retry is allowed only for a closed infrastructure failure and is
append-only. Three seed summaries use median/range and paired percentage-point
differences; no significance test is reported.

The JSON report is the only machine authority. Strict/frozen Pydantic models,
`extra=forbid`, closed enums, a checked static schema, canonical serialization,
and a hash excluding only `report_hash` make repeated generation byte-identical.
The static report-schema hash is frozen before Reporting at
`9a869a014f5ea34530230027dfbc780627ce0eed99ce753ff34ec897a8167962`.
Safe output fields are limited to hashes, opaque references, closed codes,
counts, versions, latencies, aggregate metrics, and zero real-call/cost values.

WorkArena remains the preferred external Benchmark but is recorded
`unavailable/local_assets_absent`. Version, subset, licence, and content hash
cannot be frozen because no content was authorized or consumed. It has zero
attempts. No fallback or download occurs without new user authorization.

## Consequences

- W15 can prove protocol closure, attempt accounting, deterministic reporting,
  and unchanged authority boundaries without external or paid calls.
- The 594 synthetic observations are reproducible pipeline evidence, not a
  model-quality or real-browser Benchmark.
- Reporting can show a target as met, missed, or unavailable within the fake
  dataset, but this cannot authorize work or claim production readiness.
- External-generalization evidence remains unavailable until exact assets and
  download terms are separately authorized.

## Rejected alternatives

- Download WorkArena or a fallback: no exact user authorization, version,
  licence bundle, or content checksum.
- Reuse Validation ordinal 3 or create ordinal 4: violates the W12 freeze.
- Add reporting tables or product endpoints: permits observation to flow into
  product authority and expands the database.
- Put evaluation logic in Sandbox Grader: collapses aggregation and success
  authority.
- Disable security/identity/approval/Grader for an ablation: violates W10-W14.
- Add a generic benchmark/plugin framework: unnecessary W16+ abstraction.
- Report only best seed or replace failures: selective and non-reproducible.
- Claim p-values from three repetitions: overstates the sample.
