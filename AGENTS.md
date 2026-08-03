# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is a production-oriented computer-use Agent paired with a
separate resettable synthetic evaluation environment. The authoritative
roadmap is `docs/project-roadmap.md`; the exact and sole W13 implementation
authority is `docs/agent-contract.md`.

This branch is W13: Observability and replay on `week/13-observability`. W12 is
the published baseline and must not be modified, rewritten, rolled back, retagged,
or rereleased:

- W12 PR: https://github.com/taka-wzx/flowpilot-arena/pull/35
- W12 merge commit: `2c642a67341d0cd1c9c62b6bf883ad8df2853f40`
- W12 feature/head commit: `b00dff77b1626a3f347abfba485ac5a197b627a7`
- W12 tag: `w12-production`
- W12 Release: `v0.3.0 - Production Control Plane`

The later W13 tag is expected to be `w13-observability`, but this local
authorization does not permit pushing, opening a PR, merging, tagging, creating
a Release, dispatching CI, or rerunning remote workflows.

## W13 scope boundary

W13 preserves every W1-W12 API, security boundary, deterministic fake baseline,
released Sandbox migrations, W3/W7 catalog/checksum/split, W8 recovery and
receipt contract, W9 context and ablation contract, W10 identity, tenant, RBAC,
and locking contract, W11 risk, approval, grant, and audit contract, W12
API/Worker separation, durable admission/outbox, limiter, backpressure,
lease/fence, four-slot cap, synthetic load contract, `finished_ungraded`, the
independent Grader, formal W12 ordinal 3 evidence, and the Reporting freeze.

W13 may add only deterministic local/CI observability and replay:

- OTel-shaped trace identifiers and closed/opaque trace events for one
  organization-qualified production run;
- deterministic fake cost counters with real cost fixed at zero;
- a safe single-run trace/replay export and local JSON dashboard artifact;
- a closed failure taxonomy for observability classification; and
- tests and evidence proving ordering, redaction, tenant isolation, replay, and
  W13 smoke coverage.

W13 does not change W8/W12 success semantics, approval/authorization, tenant
isolation, rate limiting, queue/backpressure, lease/fence, receipt/idempotency,
audit authority, or grader behavior. Trace, dashboard, and replay data are never
a business-success source.

W13 adds no W14 malicious-page suite, W15 Reporting or external benchmark,
W16 Helm/cloud/publication work, real IdP/account/personal data/approver,
provider/model/OCR/VLM/embedding/billing/egress, Kafka/Redis/RabbitMQ/Celery/
NATS, dynamic policy/ABAC/DSL, global administrator or approver, impersonation,
delegation, break-glass, L4 approval, physical deletion, arbitrary Shell/SQL/
JavaScript/code/URL/API capability, generic future framework, or placeholder.

## File ownership and change control

Change only exact paths listed in `docs/agent-contract.md`. Add a path to that
contract before changing it. Directory wildcards are forbidden. Any
scope-expanding service, database, provider, real data, physical deletion,
W14+ feature, or generic abstraction requires user direction first.

The literal pre-existing `%SystemDrive%/` path is outside ownership. Do not
inspect, enumerate, copy, modify, stage, scan, ignore, or delete it. Do not
access any `code_review_agent` repository.

## Engineering and security conventions

- Python target is 3.13. Use uv; never hand-edit a lockfile. Frontends remain
  TypeScript/React/Vite and use `npm ci` if touched.
- Control API authenticates and authorizes before every tenant, rate-bucket, run,
  trace, or replay query. Bearer material is accepted only in the Authorization
  header and is never logged, persisted, traced, exported, or replayed.
- `ActorContext` comes only from fixed-policy verified OIDC plus current active
  organization-qualified database rows. Caller, page, model, body, query, and
  forwarding headers never choose identity, organization, role, risk, rate,
  queue, worker, priority, budget, approval, success, trace, replay, or cost.
- Every tenant-owned read, count, constraint, index, claim, lease, trace, replay,
  dashboard, and mutation is organization-qualified in SQL. Never read globally
  and filter in Python. Cross-organization and nonexistent objects share the
  same stable response.
- Mutable external run resources use strong ETags and required If-Match.
  Successful conditional writes increase version exactly once; failed or stale
  writes have zero business side effect and no version leak.
- W11 raw approval material remains only in the bounded Control API vault.
  Workflow Worker, Temporal, Recovery, Planning, Browser, Web, Sandbox, Grader,
  logs, evidence, trace, dashboard, replay, and URLs receive no raw credential
  or nonce.
- Workflow Worker has no public port, Bearer-token path, browser/user endpoint,
  caller priority, global tenant query, arbitrary execution capability, or trace
  ingestion endpoint. It writes only closed durable trace events tied to already
  fenced run state.
- Only the eight contract-frozen W12 task/action/parameter hashes may start a W8
  production effect. Any other admitted binding fails before Temporal/Browser.
- Delivery remains durable at-least-once, with exactly one active lease winner,
  deterministic Temporal workflow identity, stale-write fencing, and W8
  receipt/idempotency enforcing at-most-one business side effect. Never call
  this distributed exactly-once.
- Run, outbox, lease history, rate state, identity, memory, authority, approval,
  grant, decision, audit, observability, trace, replay, and dashboard rows are
  never physically deleted.
- Audit remains one append-only canonical SHA-256 chain per organization. Call
  it tamper-evident, never tamper-proof, blockchain, or legal compliance.
- Agent completion remains `finished_ungraded`; only the independent Sandbox
  database-fact Grader decides success.
- Default tests, Compose, load, trace, dashboard, and replay use deterministic
  synthetic data only. Logs/evidence contain only versions, opaque IDs/hashes,
  counts, closed codes, HTTP states, latencies, receipt/grade/audit references,
  synthetic fake cost counters, and non-sensitive hardware summaries. Never
  include personal data, raw task/parameter/page/model data, secrets, DSNs, or
  machine paths.
- Use strict/frozen Pydantic, `extra=forbid`, closed enums, canonical sorted-key
  compact UTF-8 JSON, stable SHA-256, small modules, and no unused dependency.

## Required local checks

For changed Python projects, run the locally available subset of:

~~~powershell
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
~~~

For `control_web` and `sandbox_web`, run `npm ci`, lint, typecheck, test, and
build only if W13 touches frontend paths. For `tests/load`, do not rerun W12
formal Validation ordinal 3 and do not create ordinal 4; bounded development
checks may run if needed. Reporting remains unexecuted before W15.

Run available YAML/workflow policy validation; Compose config/build/up/health;
Control empty upgrade/current/check/downgrade/upgrade; W4-W12 smokes; W13
deterministic observability smoke; W3/W7/W9/W10/W11/W12 freezes where locally
available; real-call-zero proof; sensitive-field scan; exact allowlist; staged/
unstaged review; and cleanup.

Finish with:

~~~powershell
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
pre-commit run detect-private-key --all-files
gitleaks git --no-banner --redact --exit-code 1 .
git diff --check
git diff -- . ':(exclude)%SystemDrive%'
git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%'
~~~

Record unavailable tooling without weakening or claiming the gate passed.

## Evaluation, Git, and completion discipline

Development tests and bounded W13 smokes may repeat. Formal W12 ordinals 1 and
2 remain preserved failures, ordinal 3 remains the sole accepted W12 Validation,
and ordinal 4 is not authorized. Do not rerun W12 formal Validation ordinal 3.
Do not execute W15 Reporting.

Work only on `week/13-observability`; never develop on main or amend W12. This
authorization permits one local W13 feature commit only:

~~~text
feat: add W13 observability and replay
~~~

No push, PR, merge, tag, Release, workflow dispatch, CI rerun, or real-provider
call is authorized. Never broad-stage. After every locally available gate and
evidence reconciliation, explicitly stage only exact W13 allowlist paths, create
the one local commit, and stop.
