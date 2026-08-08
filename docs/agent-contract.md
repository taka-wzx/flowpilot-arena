# W15 agent contract - deterministic evaluation and reporting

## Authority, baselines, and stop condition

This contract is the sole implementation authority for W15 on
`week/15-evaluation`. It translates the roadmap and the user-authorized W15
brief while preserving every W1-W14 boundary.

W12, W13, and W14 are immutable published baselines:

- W12: PR 35; merge `2c642a67341d0cd1c9c62b6bf883ad8df2853f40`;
  feature/head `b00dff77b1626a3f347abfba485ac5a197b627a7`; tag
  `w12-production`; Release `v0.3.0 - Production Control Plane`.
- W13: PR 36; merge `cedc5f26d41262c955b60854cc69ed4f28baded6`;
  feature/head `902e4078e1ece0f401f1c5c3010e56a7ae62acf5`; tag
  `w13-observability`; Release `v0.4.0 - Observability and Replay`.
- W14: PR 41; merge `6bd960a031069f262fe60fbbb8bf2c65a09e409b`;
  feature/head `2874cfb6c02d8dfcf18baac069157e0a073ddd02`; tag
  `w14-security`; Release `v0.5.0 - Security Suite and Threat Model`.

Authorization ends after one local commit
`feat: add W15 evaluation and reporting`. No push, PR, merge, tag, Release,
workflow dispatch/rerun, W12 Validation, W16 work, Benchmark download, or real
provider/IdP/model/OCR/VLM/embedding/billing/account/data/egress call is
authorized.

The literal `%SystemDrive%/` path is outside every read, enumeration, scan,
diff, status, staging, and modification operation. No `code_review_agent`
repository may be accessed. Existing unrelated `.tmp/` content is preserved.

## Preserved W1-W14 authority

W3/W7 Task Specs, templates, instances, split/checksum discipline and database-
fact Graders; W4-W9 Agent/action/budget/recovery/context semantics; W10 identity,
tenant, RBAC, and locking; W11 approval/grant/audit; W12 admission/outbox/rate/
queue/lease/fence/four-slot/receipt/idempotency and formal ordinal-3 evidence;
W13 append-only trace/replay/dashboard; and W14 security decisions, redaction,
and browser isolation are frozen.

Agent terminal state remains `finished_ungraded`. Only the independent Sandbox
database-fact Grader decides task success. Reporting consumes safe observations
only. It cannot authorize a task, select identity or organization, change risk
or approval, start Temporal/Browser work, create a receipt, mutate product
state, write run/approval/audit/trace/security/Grader rows, or become a success
source.

## Design choice

Add a dependency-free W15 module to the existing Python 3.13
`tests/integration` project, which already locks Pydantic. It is an offline,
closed, deterministic evaluation/report generator and a Compose profile-only
smoke. There is no new service, persistent database, migration, dependency,
lockfile, public endpoint, product import, provider route, external egress, or
generic adapter framework.

The runner first validates the packaged W15 protocol and exact W3/W7 freeze
values. It then emits attempts in pre-registered configuration/task/seed order.
The shipped executor is `w15-deterministic-synthetic-runner/1.0`: a transparent
fake used to validate evaluation wiring and report determinism without a real
model or provider. Its observations are not evidence of real model quality,
external generalization, production SLOs, ROI, or statistical significance.

## Reporting split freeze

The primary Reporting set is the already frozen W7 JML set:

- catalog schema/version: `w7-jml-catalog/1.0`;
- catalog checksum:
  `62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f`;
- split manifest checksum:
  `1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee`;
- Reporting manifest checksum:
  `c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6`;
- six Reporting templates: two Joiner, two Mover, two Leaver;
- three fixed variants per template: 18 exact instances; and
- exact lexicographic template/variant order recorded in
  `tests/integration/w15-reporting-protocol.json`.

The released W3 ten-task catalog remains frozen at checksum
`e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9`
and is a compatibility gate, not the W15 Reporting result set.

Any template, instance, order, checksum, catalog, split, protocol,
configuration, schema, or report mismatch fails before attempt generation.
Development may use only the protocol's Development smoke references.
Validation is not run. Reporting is executed once after freeze.

## Frozen matrix, seeds, pairing, and attempts

The exact matrix contains five baselines and six ablations, in this order:

1. `dom_react`;
2. `vision_only_react`;
3. `hybrid_no_recovery`;
4. `hybrid_planner`;
5. `full_system`;
6. `no_vision_router`;
7. `no_verifier`;
8. `no_checkpoint`;
9. `no_short_term_memory`;
10. `no_enterprise_knowledge_retrieval`; and
11. `no_local_replanning`.

All configurations retain frozen W10-W14 security/identity/tenant/RBAC/
approval/browser isolation and the independent Grader. Only the six named
Agent capabilities are disabled by an ablation. Security comparisons run only
in the local synthetic Arena and never disable security.

Seeds are exactly `2026081501`, `2026081502`, and `2026081503`, in order.
Pairing key is `(task_id, seed)` and attempt order is configuration, exact
Reporting instance order, then seed. This produces 11 x 18 x 3 = 594 planned
primary attempts. Opaque attempt IDs are deterministic SHA-256 references over
the protocol version, configuration ID, task checksum, seed, and retry ordinal.

The configuration hash is SHA-256 over the canonical sorted-key compact UTF-8
configuration array. The protocol hash is computed similarly while excluding
only its declared `protocol_hash`. The frozen configuration hash is
`c9ea8d997e470a7b7584e40001e8dbff349bd9a73aa80cdbf1a32b84d81d7ec5` and
the frozen protocol hash is
`b5aa0ddd4d0d07dd3d4a26faac11c947c223b85d14ac5dbc316681edc6de1379`.
Both values are sealed before implementation and before the Reporting run.

## Closed status, failure, and retry rules

Primary attempt statuses are `completed`, `agent_failed`, `timed_out`,
`controlled_stop`, `infrastructure_failed`, and `missing`. Grader outcomes are
`passed`, `failed`, and `not_graded`. Agent failure reasons are `none`,
`action_error`, `budget_exhausted`, `verification_failed`, `timeout`, and
`controlled_stop`. Infrastructure reasons are `none`, `fixture_unavailable`,
`service_unavailable`, `infrastructure_timeout`, and `protocol_mismatch`.

Every planned primary attempt is present in the authoritative report. Agent
failure, timeout, and controlled stop are never retried. One infrastructure
retry is permitted only when the closed reason is retryable; it is appended
with a distinct attempt reference and the original record remains. A retry
cannot replace a worse result. Missing attempts remain visible. The shipped
frozen synthetic run expects no retry, but tests exercise failure, missing, and
append-only retry handling.

If a protocol or implementation defect is found after unblinding, stop and
request user authorization. Do not tune a threshold, prompt, task, Grader,
metric, seed, order, denominator, or configuration and do not silently rerun.

## Metrics, denominators, and aggregation

Primary denominators include all 594 planned cells. Completed `passed` is
success; failed/not-graded, timeout, controlled stop, infrastructure failure,
and missing are not success. Subgoal and action ratios use summed closed
counts. Mean steps, plan modifications, model calls, tokens, and synthetic cost
use all planned cells with absent execution contributing zero and separately
reported availability counts. Recovery rate is recovered/recoverable; an empty
denominator is unavailable, never 100%.

System API and queue p50/p95/p99 use nearest rank over available integer
microsecond samples. Browser concurrency is the maximum observed. Worker
recoveries, lock conflicts, duplicate effects, cross-tenant reads, approval
bypasses, prompt-injection successes, unauthorized operations, sensitive leaks,
and duplicate external operations are summed counts.

Each seed reports its raw closed summary. Across three seeds report median and
range. Baseline/ablation comparisons are paired on task and seed, expressed as
percentage-point differences in success and integer/ratio differences for
other metrics. No p-value, confidence claim, or significance language is
permitted for three repetitions. Pareto points use higher success and lower
synthetic cost; real cost is always zero.

Pre-registered roadmap targets are comparisons only: Full versus DOM ReAct
success +15 percentage points; single-application >=85%; multi-application
>=65%; recovery >=90%; approval bypass, cross-tenant leak, duplicate business
effect, prompt-injection success, unauthorized operation, sensitive leak, and
duplicate external operation all zero; API p95 below 500,000 microseconds; and
maximum browser concurrency at least four. A target with no eligible sample is
`unavailable`, not passed. Results are never preclaimed.

## External Benchmark decision

Preferred Benchmark: WorkArena. Repository audit found no versioned WorkArena
data/image/dependency, task subset, licence artifact, or content checksum. Its
closed status is `unavailable/local_assets_absent`; version, subset, licence,
and content checksum are absent because no external content was downloaded or
consumed. It has zero planned/executed attempts and cannot be presented as a
pass.

No fallback Benchmark is silently selected. Downloading WorkArena or switching
to WebArena-Verified, MiniWoB, or VisualWebArena requires new user direction
covering the exact source, immutable version, subset, licence, content checksum,
and download/install action. JML Arena remains the only executed primary set.

## Report contract and redaction

The machine authority is `docs/evidence/week-15-report.json` with schema
`w15-evaluation-report/1.0`. It uses strict/frozen Pydantic, `extra=forbid`,
closed enums, canonical sorted-key compact UTF-8 JSON, stable SHA-256, and a
checked static JSON Schema frozen at
`9a869a014f5ea34530230027dfbc780627ce0eed99ce753ff34ec897a8167962`.
`report_hash` excludes only itself. Identical
frozen inputs must produce byte-identical output and hash.

The report contains only schema/protocol/config/catalog/split/report hashes,
opaque attempt/task/config references, closed states/reasons, counts, aggregate
metrics, versions, bounded latency, zero real-call/cost counters, and opaque
security references. It contains no raw task/page/DOM/screenshot/model/tool
content, Bearer/approval credential/nonce, Cookie, password, private key, DSN,
personal data, real secret, URL query/fragment, or machine path.

## Exact W15 file allowlist

Only these exact paths may be created or modified. There are no directory
wildcards. A new path must first be added here; any non-goal expansion requires
new user direction.

~~~text
.github/workflows/ci.yml
AGENTS.md

docs/agent-contract.md
docs/evaluation-protocol.md
docs/benchmark-card.md
docs/adr/0015-w15-evaluation.md
docs/plans/week-15-evaluation.md
docs/evidence/week-15-report.md
docs/evidence/week-15-report.json

tests/integration/Dockerfile
tests/integration/w15-reporting-protocol.json
tests/integration/w15-report.schema.json
tests/integration/w15_evaluation.py
tests/integration/test_w15_evaluation.py
tests/integration/w15_evaluation_smoke.py

deploy/compose/compose.yaml
~~~

The allowlist contains 16 exact paths. Existing application code, migrations,
Task Specs/catalogs, Graders, product state, frontends, dependencies, lockfiles,
load artifacts, trace/replay/security schemas, and W1-W14 evidence remain
unchanged.

## Required completion

Run every locally available gate in `AGENTS.md`, including W3/W7 freeze checks,
W15 unit/schema/hash/determinism/redaction tests, Development smoke, W4-W14
regression, W13/W14 smokes, Compose/migration/real-call-zero/sensitive scans,
and cleanup. Only after prerequisite gates pass, seal the protocol and execute
the W15 Reporting final once. Record planned/executed/missing/retry counts and
all unavailable tools honestly.

Explicitly stage only changed paths from the 16-path allowlist, create one local
commit `feat: add W15 evaluation and reporting`, and stop. Do not push, open a
PR, merge, tag, create a Release, dispatch/rerun CI, run W12 Validation, execute
an external Benchmark, or begin W16.
