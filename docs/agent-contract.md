# W13 agent contract - observability and replay

## Authority, baseline, and stop condition

This contract translates the W13 roadmap row and the user-authorized W13 brief
into the sole implementation authority for `week/13-observability`.

W12 is the immutable published baseline:

- PR: https://github.com/taka-wzx/flowpilot-arena/pull/35
- merge commit: `2c642a67341d0cd1c9c62b6bf883ad8df2853f40`
- feature/head commit: `b00dff77b1626a3f347abfba485ac5a197b627a7`
- tag: `w12-production`
- Release: `v0.3.0 - Production Control Plane`

W13 has one local outcome: preserve every W1-W12 frozen boundary while adding a
deterministic, closed, tenant-qualified observability and replay layer that lets
one production run be traced and reviewed from admission through terminal
`finished_ungraded` or failure. The later expected week tag is
`w13-observability`. This authorization stops after one local feature commit
`feat: add W13 observability and replay`. It does not authorize push, PR, merge,
tag, Release, workflow_dispatch, CI rerun, W12 formal Validation rerun, W12
ordinal 4, W15 Reporting, or real provider/IdP/model/OCR/VLM/embedding/billing/
egress calls.

The literal `%SystemDrive%/` path is outside every read, enumeration, scan,
diff, status, staging, and modification operation. No `code_review_agent`
repository may be accessed.

## Preserved W1-W12 boundary

All W1-W12 public APIs, route semantics, strict schemas, deterministic fake
results, released Sandbox migrations, W3 ten tasks/checksum/6-2-2 split, W7 30
templates/90 instances, W8 Temporal workflow, checkpoint, receipt,
idempotency, recovery, cap, and `finished_ungraded` contract, W9 context and
ablation contract, W10 fixed OIDC, tenant isolation, database-derived
ActorContext, closed RBAC, and strong ETags, W11 risk/approval/grant/audit
contract, W12 asynchronous admission, durable outbox, organization-fair
scheduling, bounded rate limiter, queue/backpressure, lease/fence, private
Workflow Worker, four-slot cap, isolated Browser sessions, load schema/profile,
and formal ordinal 3 evidence remain frozen.

Trace, dashboard, replay, and cost records are observation data only. They never
authorize a task, select a tenant, bypass approval, change rate/queue/lease
policy, mutate Sandbox business state, create a W8 receipt, decide success, or
replace the independent Grader. W13 may classify an observed failure, but the
existing W8/W11/W12 terminal state remains the business source of truth.

## W13 design choice

W13 implements a Control-database append-only observability model plus a
Control API single-run trace export. It does not add Prometheus, Tempo, Grafana,
OpenTelemetry Collector, a public ingestion endpoint, frontend dashboard code,
or a new service. Dashboard output is a deterministic local/CI JSON report and
the dashboard section embedded in the trace export.

The trace is OTel-shaped without adding a dependency: every event stores a
stable W3C-compatible 32-hex `trace_id`, a deterministic 16-hex `span_id`, and
an optional 16-hex parent span. IDs are derived only from canonical
organization-qualified run/event references and contain no caller-supplied or
secret material.

## Closed observability data model

Control migration `20260803_0004` adds only `w13_observability_events`.
Rows are append-only and organization/run qualified. No W13 observability row is
physically deleted. Each row stores:

- schema version `w13-observability-event/1.0`;
- opaque event/run/organization references;
- per-run `event_sequence`, OTel-shaped trace/span IDs, and optional parent
  span;
- closed phase, status, failure category, and reason enums;
- compact canonical `attributes_json`, `attributes_hash`, `event_hash`; and
- UTC `observed_at`.

Allowed phases are `admission`, `approval`, `outbox`, `lease`, `dispatch`,
`workflow`, `recovery`, `planning`, `browser`, `receipt`, `grader`, `audit`,
`cost`, `terminal`, `replay`, and `dashboard`.

Allowed failure categories are `none`, `authn`, `authz`, `approval`, `schema`,
`rate_limit`, `backpressure`, `queue_expiry`, `lease_fence`,
`workflow_rejected`, `dependency_unavailable`, `browser_timeout`,
`browser_error`, `planning_failure`, `recovery_failure`, `receipt_invalid`,
`grader_verification`, and `audit_verification`.

Trace attributes are strict and bounded. They may contain only schema version,
opaque IDs/hashes, closed statuses/reasons, versions/fences, sequence/count
integers, latency/duration integers, receipt/checkpoint/audit references,
completed safe step IDs, deterministic fake-provider token/model counters,
`fake_cost_microusd`, `real_cost_microusd=0`, and the boolean
`sensitive_fields_present=false`. They must not contain Bearer tokens, OIDC raw
claims, authorization codes, approval credentials/nonces, Cookies, passwords,
private keys, names, emails, usernames, raw task/parameter/page/DOM/image/OCR/
model content, DSNs, secrets, or machine paths.

## Trace coverage

W13 must record closed events for:

- Control API admission to `waiting_approval` or `queued`;
- W11 approval handoff into W12 production claim/outbox;
- outbox readiness, lease, recovery reclaim, heartbeat/release, and fence
  rejection references;
- Workflow Worker dispatch and deterministic Temporal workflow reference;
- W8 Recovery/Planning/Browser summaries derived from the strict W8 result;
- receipt/checkpoint reference;
- `finished_ungraded`, failed, cancelled, or expired terminal transition;
- audit sequence/head reference; and
- deterministic fake cost accounting with real cost fixed to zero.

If a run is terminal before a downstream phase exists, replay exports the
observed prefix and the closed terminal category. Missing future events do not
invent success.

## API and replay contract

W13 adds one authenticated read-only route:

~~~text
GET /api/v1/organizations/{organization_id}/production-runs/{run_id}/trace
~~~

The route requires the new closed permission `observability.trace.read`, charges
the existing W12 `production_read` rate bucket, and returns schema
`w13-run-trace-export/1.0`. It uses the same organization-qualified lookup and
stable 404 behavior as production-run reads.

The export contains the run read model, ordered trace events, ordered replay
steps, fake/real cost summary, deterministic JSON dashboard summary, and a
stable SHA-256 export hash over canonical sorted-key compact JSON excluding the
hash field. The replay is a reconstruction of observed closed events; it is not
an executable workflow, a success source, or a source of raw business data.

## Tests and evidence

W13 must add locally runnable tests for:

- trace schema strictness, hash stability, and closed failure taxonomy;
- redaction rejection and absence of forbidden fields in exports;
- event ordering and single-run replay reconstruction;
- tenant isolation and uniform cross-organization/missing responses;
- Workflow Worker trace writes for lease/dispatch/workflow/recovery/planning/
  browser/receipt/cost/terminal events;
- Control migration upgrade/current/check/downgrade/upgrade with the W13 table;
  and
- a deterministic Compose W13 observability smoke proving one production run can
  be traced and replayed.

Evidence must state that W13 trace/dashboard data is deterministic local/CI
synthetic observability only. It is not a production SLO, certification, legal
compliance statement, security attestation, or ROI claim. Formal W12 ordinal 3
must not be rerun and ordinal 4 must not be created.

## Explicit non-goals

W13 adds no public telemetry ingestion service; no Prometheus, Tempo, Grafana,
OpenTelemetry Collector, SaaS telemetry, billing/provider integration, real
cost import, egress, external benchmark, Reporting execution, malicious-page
suite, Helm/cloud deployment, UI redesign, dynamic policy, arbitrary execution,
physical deletion, global tracing across tenants, trace-derived success, or
generic future framework.

## Exact W13 file allowlist

Only the following exact paths may be created or modified. There are no
directory wildcards. A new path must first be added here; any scope expansion
listed in the non-goals requires new user direction.

~~~text
AGENTS.md
CHANGELOG.md
.github/workflows/ci.yml

docs/agent-contract.md
docs/adr/0013-w13-observability.md
docs/plans/week-13-observability.md
docs/evidence/week-13-report.md

apps/control_api/migrations/versions/20260803_0004_w13_observability.py
apps/control_api/src/flowpilot_control_api/main.py
apps/control_api/src/flowpilot_control_api/models.py
apps/control_api/src/flowpilot_control_api/observability.py
apps/control_api/src/flowpilot_control_api/production.py
apps/control_api/src/flowpilot_control_api/rbac.py
apps/control_api/src/flowpilot_control_api/schemas.py
apps/control_api/tests/test_migrations.py
apps/control_api/tests/test_observability.py
apps/control_api/tests/test_rbac.py

apps/workflow_worker/src/flowpilot_workflow_worker/repository.py
apps/workflow_worker/tests/conftest.py
apps/workflow_worker/tests/test_repository.py

deploy/compose/compose.yaml
tests/integration/Dockerfile
tests/integration/w13_observability_compose_smoke.py
~~~

The allowlist contains 23 exact paths. Existing Control, Browser, Planning,
Recovery, Sandbox, frontend, load, realm, and released migration files not
listed above remain unchanged.

## Required local completion

After all locally available gates pass and evidence matches observations,
explicitly stage only paths above; never use broad staging. Create one local
commit `feat: add W13 observability and replay` and stop. Do not push, create a
PR, merge, tag, create a Release, rerun/dispatch CI, call a real provider, rerun
W12 formal Validation ordinal 3, create ordinal 4, execute W15 Reporting, or
begin W14.
