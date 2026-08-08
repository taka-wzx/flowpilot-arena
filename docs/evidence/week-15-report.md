# W15 evidence report - evaluation and reporting

## Scope and immutable baseline

- Branch: `week/15-evaluation`.
- Base: W14 merge `6bd960a031069f262fe60fbbb8bf2c65a09e409b`.
- W12/W13/W14 published baselines: immutable and unchanged.
- W12 formal Validation rerun / ordinal 4: no / not created.
- External Benchmark: unavailable; no asset downloaded or executed.
- Real provider/model/OCR/VLM/embedding/billing/egress calls and cost: 0.
- Remote push/PR/merge/tag/Release/workflow action: not authorized.

This evidence shell was created before implementation and Reporting unblinding,
then reconciled only with observed local facts. An unavailable entry is not a
pass. The authoritative machine result is
`docs/evidence/week-15-report.json` from the single final run.

## Pre-registration

The immutable protocol is `tests/integration/w15-reporting-protocol.json`.
It freezes W3/W7 hashes, all 18 ordered W7 Reporting instances, the 11-config
matrix, three seeds, 594 primary attempts, failure/retry rules, denominators,
aggregation, comparison direction, targets, Benchmark availability, and report
schema. Exact configuration/protocol/schema/report hashes are recorded here
before/after their respective gates and never changed in response to results.

- Configuration hash:
  `c9ea8d997e470a7b7584e40001e8dbff349bd9a73aa80cdbf1a32b84d81d7ec5`.
- Protocol hash:
  `b5aa0ddd4d0d07dd3d4a26faac11c947c223b85d14ac5dbc316681edc6de1379`.
- Report schema hash:
  `9a869a014f5ea34530230027dfbc780627ce0eed99ce753ff34ec897a8167962`.
- Protocol planned primary attempts: 594.

## Preserved pre-final protocol-test incident

Before the formal Reporting run, seven local pytest invocations each executed
five in-memory `build_reporting_report` unit-test constructions, for 35 total.
They used the frozen Reporting manifest and are therefore preserved as 35
non-formal failed `protocol_test_construction` events rather than silently
discarded or presented as the final experiment. No JSON report was written;
no Reset/Seed, Agent, product API, independent Grader, external Benchmark,
provider, model, OCR, VLM, embedding, billing, account-data, or egress call was
made; no product state changed; and no protocol/configuration/metric/threshold
was changed after observing them.

The user explicitly authorized remediation on 2026-08-08: retain this fact,
move all unit report/aggregation/stability tests to the three frozen Development
fixtures, keep the protocol/configuration freeze unchanged, rerun the gates,
then execute exactly one formal Reporting final. The final report's 594 planned
primary attempts remain a separate closed experiment and do not overwrite or
erase these 35 failed test constructions.

## Formal Reporting result

After the authorized test-isolation repair and all prerequisite protocol,
implementation, regression, security, migration, load, and Development gates,
the final Reporting command was executed once. The output path did not exist
before execution and the writer refuses overwrite.

- Report schema/version: `w15-evaluation-report/1.0`.
- Canonical report hash:
  `ef2f1690a662eb5119214fb1e4fef80c22b1879ad0a88603b1e3e520c5cd9d3e`.
- Raw report-byte SHA-256:
  `42058cc83d310b51011e4774909b32dab6f3e0370d546c3c7928a5518f86cc00`.
- Raw byte count: 802,492; canonical compact UTF-8; no trailing newline.
- Planned / primary records / executed: 594 / 594 / 594.
- Completed / Agent failed / timed out / controlled stop / infrastructure
  failed / missing: 594 / 0 / 0 / 0 / 0 / 0.
- Infrastructure retry records: 0; no primary record was replaced.
- Repeat summaries: 33 exact configuration/seed rows; configuration summaries:
  11; paired Full-system comparisons: 10.
- Real calls and real cost: 0 / 0.
- External Benchmark: `workarena`, `unavailable/local_assets_absent`, planned /
  executed 0 / 0, `passed=false`.

### Agent metrics by configuration

All values are integer basis points except step/plan means, which are
thousandths. Seed ranges are minimum/median/maximum over the three frozen
repetitions.

| Configuration | Success bp | Seed success range | Subgoal bp | Error action bp | Steps milli | Plan changes milli | Human bp | Recovery bp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DOM ReAct | 5185 | 4444 / 5556 / 5556 | 6620 | 493 | 20667 | 0 | 370 | 0 |
| Vision-only ReAct | 5370 | 4444 / 5556 / 6111 | 6944 | 475 | 20667 | 0 | 370 | 0 |
| Hybrid, no recovery | 5926 | 4444 / 6111 / 7222 | 7731 | 430 | 20667 | 0 | 370 | 0 |
| Hybrid + Planner | 6852 | 6111 / 6111 / 8333 | 8495 | 341 | 21944 | 1278 | 370 | 0 |
| Full system | 8333 | 7778 / 8333 / 8889 | 9491 | 161 | 21796 | 1130 | 185 | 10000 |
| No Vision Router | 7222 | 6667 / 6667 / 8333 | 8819 | 296 | 21907 | 1241 | 185 | 10000 |
| No Verifier | 7037 | 6111 / 6667 / 8333 | 8727 | 323 | 21926 | 1259 | 185 | 10000 |
| No Checkpoint | 7222 | 6667 / 6667 / 8333 | 8819 | 296 | 21907 | 1241 | 185 | 10000 |
| No short-term memory | 7407 | 6667 / 7222 / 8333 | 8981 | 269 | 21889 | 1222 | 185 | 10000 |
| No enterprise knowledge retrieval | 7407 | 6667 / 7222 / 8333 | 8981 | 269 | 21889 | 1222 | 185 | 10000 |
| No local replanning | 7222 | 6667 / 6667 / 8333 | 8819 | 296 | 21907 | 1241 | 185 | 10000 |

The JSON authority additionally retains every per-attempt model-call, input/
output-token, VLM, cache, synthetic-cost, latency, queue, concurrency, Worker,
lock, duplicate-effect, security, and zero-real-call counter. Average synthetic
cost ranges from 4,172 to 11,576 microusd-equivalent units per task; it is a
fake comparison unit and not billed cost. Full-system API p95 is 133,988
microseconds and maximum browser concurrency is four.

### Paired success differences

Each comparison uses the same 54 `(task_reference, seed)` cells. Values are
Full system minus the named configuration in basis points; higher is better.

| Compared configuration | Difference bp |
|---|---:|
| DOM ReAct | 3148 |
| Vision-only ReAct | 2963 |
| Hybrid, no recovery | 2407 |
| Hybrid + Planner | 1481 |
| No Vision Router | 1111 |
| No Verifier | 1296 |
| No Checkpoint | 1111 |
| No short-term memory | 926 |
| No enterprise knowledge retrieval | 926 |
| No local replanning | 1111 |

No p-value, confidence interval, or significance claim is made from three
repetitions. The exact repeat rows, paired cells, and Pareto flags remain in the
machine report.

### Pre-registered target comparison

| Target | Observed | Threshold | Status |
|---|---:|---:|---|
| Full system minus DOM ReAct | 3148 bp | at least 1500 bp | met |
| Single-application success | unavailable | at least 8500 bp | unavailable |
| Multi-application success | 8333 bp | at least 6500 bp | met |
| Recovery rate | 10000 bp | at least 9000 bp | met |
| Security failures | 0 | at most 0 | met |
| Duplicate business effects | 0 | at most 0 | met |
| API p95 | 133,988 us | below 500,000 us | met |
| Browser concurrency | 4 | at least 4 | met |
| Real calls | 0 | at most 0 | met |
| Real cost | 0 | at most 0 | met |

These statuses apply only to the frozen deterministic synthetic runner. The
single-application target has no eligible Reporting sample and is not converted
to a pass.

## Local gate evidence

- W15 locked Sandbox/Arena toolchain sync passed without a lockfile change.
  Ruff, format, strict Mypy, 15 Development-only tests, actual W3/W7 catalog
  comparison, schema/hash checks, and Development CLI smoke passed after the
  authorized isolation repair.
- Development smoke: 33 attempts over three Development J/M/L instances and 11
  configurations; 33 `finished_ungraded`, 33 independent grade observations,
  zero security failures, duplicate effects, real calls, and real cost; summary
  hash `bf71626f01e99cad9668173ace136150a823678282cd3ae28066eab86e34bec0`.
- YAML/workflow and standalone Compose configuration parsed successfully.
  The repaired W15 profile ran with `network_mode:none`, read-only rootfs,
  dropped capabilities, no-new-privileges, bounded PIDs/tmpfs, and no product
  service dependency.
- All 15 base services built and became healthy. Sandbox migration reached
  `20260728_0003 (head)` with no drift. Control reached
  `20260803_0004 (head)`, successfully round-tripped to W12
  `20260801_0003` and back, and reported no drift.
- W4-W14 deterministic Compose smokes all exited zero. W7 retained 30
  templates, 90 instances, the frozen split/Reporting hashes, and independent
  Development J/M/L grades of 100. W8 retained zero duplicate effects and
  Reporting false. W9 retained its five ablation hashes and real-call-zero.
  W10 identity isolation and exact-one concurrency passed; W11 approval/audit
  passed with zero pre-approval/duplicate side effects.
- W12 Production retained four-browser concurrency, audit validity,
  `finished_ungraded`, zero real calls, and Reporting false. Its non-formal
  50-user Development CI profile completed 1,000 protected requests, 100
  accepted runs, API p95 190,487 microseconds, zero unexpected HTTP/5xx,
  `validation_run=false`, and `reporting_executed=false`. Formal Validation
  ordinal 3 was not rerun and ordinal 4 was not created.
- W13 observability produced 21 ordered events/replay steps, terminal
  `finished_ungraded`, independent Grader pass, zero real calls/cost, and the
  unchanged `w13-run-trace-export/1.0` boundary. W14 rejected approval bypass
  and cross-tenant read, produced zero security-path business side effects,
  retained independent Grader pass and W13 compatibility, and reported zero
  real calls with sensitive fields absent.
- Published Python regression: Ruff, format, and Mypy passed for all nine
  projects. Unit tests passed: Control 68, Sandbox 35, Browser 56, DOM 27,
  Vision 20, Hybrid 31, Planning 53, bounded Recovery 12, and Workflow 24
  (326 total).
- Sensitive report scan passed: no raw W7 task ID, task-ID field, Authorization,
  Cookie, password, private-key, approval credential/nonce, raw-content,
  machine-path, DSN, or Bearer material. Report Pydantic validation, static
  schema equality, canonical bytes, schema hash, and report hash all passed.
- Final cleanup completed after the last W15 no-network smoke. The exact
  Compose project-label query returned zero containers, zero networks, and
  zero volumes. A final sensitive-value scan over all 16 allowlisted paths
  returned zero report-token and zero secret-pattern matches.
- Final YAML parsing covered the CI workflow and Compose file. The unstaged
  allowlist comparison found exactly 16 expected W15 paths with zero missing
  or extra paths, and the tracked diff whitespace check passed. Gitleaks
  8.30.1 scanned 56 Git commits (approximately 4.15 MB) and found no leaks.
- Explicit staging selected exactly the 16 contract paths, with zero missing,
  zero extra, and zero remaining unstaged changes in those paths. The staged
  whitespace check passed. The staged report remained 802,492 bytes with raw
  SHA-256 `42058cc83d310b51011e4774909b32dab6f3e0370d546c3c7928a5518f86cc00`.
  The final staged gitleaks scan covered all staged bytes and found no leaks.

## Tooling limitations and non-actions

- Docker CLI plugin `docker compose` was unavailable. Standalone Compose 5.3.1
  and Docker Engine 29.6.2 were used. The buildx plugin was unavailable;
  Compose warned and the classic builder completed all local synthetic builds.
- Two Recovery replay tests require an uncached external Temporal test-server
  binary. They were not downloaded; the remaining 12 Recovery tests passed.
- The `pre-commit run detect-private-key` wrapper was unavailable because its
  existing local hook cache has an invalid manifest; neither the standalone
  hook executable nor its Python module is installed. No cache repair or
  download was attempted. The exact 16-path PEM/private-key and sensitive-
  value scan passed, but this substitute is not recorded as a pre-commit pass.
- Frontend source was not in the W15 allowlist and was not modified. Locked
  frontend images were built by the Compose regression; no separate source
  npm gate was required for W15.
- No external Benchmark, real provider/model/OCR/VLM/embedding/billing/IdP/
  account-data/egress call, W12 formal Validation, W16 work, remote push, PR,
  merge, tag, Release, workflow dispatch, or rerun occurred.

## Interpretation limit

The shipped W15 runner is deterministic synthetic fake evidence for the
evaluation/reporting pipeline. It is not a real-model evaluation, external
Benchmark, production SLO, ROI result, security certification, or claim of
statistical significance. WorkArena is unavailable and no substitute result is
invented.
