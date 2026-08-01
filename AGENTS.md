# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is a production-oriented computer-use Agent paired with a
separate resettable synthetic evaluation environment. The authoritative
roadmap is `docs/project-roadmap.md`; the exact and sole W12 implementation
authority is `docs/agent-contract.md`.

This branch is W12: Production Control Plane, API/Worker separation, durable
admission, bounded scheduling, backpressure, rate limiting, deterministic load,
and complete local Docker Compose deployment on `week/12-production`. The
immutable W11 product baseline is merge
`84336fdc1dd056110b2dfb32383ce938361bf316` / tag `w11-approval`; the W11
feature commit is `21ac2d54e3e9577ede8a5d91cd8257ef6daf3397`. The current
Release remains `v0.2.0 - Hybrid + Recovery` / `w08-recovery` until a separate
remote-delivery authorization. W12's later authorized tag and release are
`w12-production` and `v0.3.0 - Production Control Plane`.

## W12 scope boundary

W12 preserves every W1-W11 API, security boundary, deterministic fake
baseline, released Sandbox migrations, W3/W7 catalog/checksum/split, W8
recovery and receipt contract, W9 context and ablation contract, W10 identity,
tenant, RBAC, and locking contract, W11 risk, approval, grant, and audit
contract, the independent Grader, `finished_ungraded`, and the Reporting
freeze. It may add only:

- authenticated asynchronous production run admission with strict schemas,
  strong ETags, bounded idempotency keys, durable organization-qualified run
  and outbox state, and atomic W11 audit append;
- one trusted, non-public Workflow Worker that claims organization-fair work,
  uses short leases and monotonically increasing fencing tokens, revalidates
  durable authorization bindings, and starts/resumes the existing W8 Temporal
  workflow with deterministic identity;
- one persistent server-configured token-bucket limiter, one bounded queue,
  closed 429/503 responses, and no caller-supplied priority, worker, quota, or
  tenant key;
- one global four-slot production execution cap while retaining per-run
  Browser context/session/cookie/storage isolation;
- one frozen Locust 50-user deterministic synthetic profile and stable result
  schema/checksum; and
- one complete Compose topology and one consolidated W4-W12 regression job.

W12 adds no W13 observability pipeline, W14 malicious-page suite, W15 external
benchmark or Reporting execution, W16 Helm/cloud/publication work, real IdP,
account, personal data, approver, model/provider/OCR/VLM/embedding/key/egress,
Kafka/Redis/RabbitMQ/Celery/NATS, dynamic policy/ABAC/DSL, global administrator
or approver, impersonation, delegation, break-glass, L4 approval, physical
deletion, arbitrary Shell/SQL/JavaScript/code/URL/API capability, generic
future framework, or placeholder.

## File ownership and change control

Change only exact paths listed in `docs/agent-contract.md`. Add a path to that
contract before changing it. Directory wildcards are forbidden. Any
scope-expanding service, database, provider, real data, physical deletion,
W13+ feature, or generic abstraction requires user direction first.

The literal pre-existing `%SystemDrive%/` path is outside ownership. Do not
inspect, enumerate, copy, modify, stage, scan, ignore, or delete it. Do not
access any `code_review_agent` repository.

## Engineering and security conventions

- Python target is 3.13. Use uv; never hand-edit a lockfile. Frontends remain
  TypeScript/React/Vite and use `npm ci`.
- Control API authenticates and authorizes before every tenant or rate-bucket
  query. Bearer material is accepted only in the Authorization header and is
  never logged or persisted.
- `ActorContext` comes only from fixed-policy verified OIDC plus current active
  organization-qualified database rows. Caller, page, model, body, query, and
  forwarding headers never choose identity, organization, role, risk, rate,
  queue, worker, priority, budget, approval, or success.
- Every tenant-owned read, count, constraint, index, claim, lease, and mutation
  is organization-qualified in SQL. Never read globally and filter in Python.
  Cross-organization and nonexistent objects share the same stable response.
- Mutable external run resources use strong ETags and required If-Match.
  Successful conditional writes increase version exactly once; failed or stale
  writes have zero side effect and no version leak.
- W11 raw approval material remains only in the bounded Control API vault.
  Workflow Worker, Temporal, Recovery, Planning, Browser, Web, Sandbox, Grader,
  logs, evidence, and URLs receive no raw credential or nonce.
- Workflow Worker has no public port, Bearer-token path, browser/user endpoint,
  caller priority, global tenant query, or arbitrary execution capability. It
  receives only closed durable references and a trusted synthetic payload
  reference.
- Only the eight contract-frozen task/action/parameter hashes may start a W8
  production effect. Any other admitted binding fails before Temporal/Browser;
  L0/L1 read or plan authority never authorizes the full JML mutation.
- Delivery is durable at-least-once, with exactly one active lease winner,
  deterministic Temporal workflow identity, fencing of stale writes, and W8
  receipt/idempotency enforcing at-most-one business side effect. Never call
  this distributed exactly-once.
- Run, outbox, lease history, rate state, identity, memory, authority,
  approval, grant, decision, and audit rows are never physically deleted.
- Audit remains one append-only canonical SHA-256 chain per organization. Call
  it tamper-evident, never tamper-proof, blockchain, or legal compliance.
- Agent completion remains `finished_ungraded`; only the independent Sandbox
  database-fact Grader decides success.
- Default tests, Compose, and load use deterministic synthetic data only.
  Logs/evidence contain only versions, opaque IDs/hashes, counts, closed codes,
  HTTP states, latencies, receipt/grade references, and non-sensitive hardware
  summaries. Never include personal data, raw task/parameter/page/model data,
  secrets, DSNs, or machine paths.
- Use strict/frozen Pydantic, `extra=forbid`, closed enums, canonical sorted-key
  compact UTF-8 JSON, stable SHA-256, small modules, and no unused dependency.

## Required local checks

For `control_api`, `sandbox_api`, `browser_worker`, `dom_agent`,
`vision_agent`, `hybrid_agent`, `planning_agent`, `recovery_worker`, and
`workflow_worker`, run:

~~~powershell
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
~~~

For `control_web` and `sandbox_web`, run `npm ci`, lint, typecheck, test, and
build. For `tests/load`, run locked sync, Ruff, format, Mypy, pytest, schema and
checksum validation, the bounded Development profile, then the one frozen
Validation profile.

Run YAML/workflow policy validation; Compose config/build/up/health; Sandbox
Alembic current/check plus released-byte freeze; Control empty upgrade/current/
check/downgrade/upgrade; W4-W12 smokes; W3/W7/W9/W10/W11 freezes; W10 authn,
RBAC, tenant, and locking; W11 risk, approval, grant, and audit; W12 admission,
rate, backpressure, lease, fence, crash, restart, drain, four-slot, isolation,
and load matrices; Reporting-not-run and real-call-zero proof; sensitive-field
scan; exact allowlist; staged/unstaged review; and cleanup 0/0/0.

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

Development tests and bounded W12 smokes may repeat. Formal ordinals 1 and 2
remain preserved failures. The user explicitly authorized exactly one
replacement 50-user/four-browser W12 Validation ordinal 3, only after the
complete run, work-item, outbox, lease/fence, W11 handoff, idempotency,
limiter/queue values, load version/workload/counts, result schema/hash, Compose
topology, and fault matrix are frozen. After ordinal 3, do not tune or rerun
it; ordinal 4 is not authorized. Reporting remains unexecuted before W15.

Work only on `week/12-production`; never develop on main or amend W11. This
authorization permits one local W12 feature commit only. No push, PR, merge,
tag, Release, workflow dispatch, CI rerun, or real-provider call is authorized.
Never broad-stage. After every locally available gate and evidence
reconciliation, explicitly stage only exact W12 allowlist paths, create one
local commit `feat: add W12 production control plane`, and stop before W13.
