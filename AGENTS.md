# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is a production-oriented computer-use Agent paired with a
separate resettable synthetic evaluation environment. The authoritative
roadmap is `docs/project-roadmap.md`; the exact and sole W14 implementation
authority is `docs/agent-contract.md`.

This branch is W14: Security on `week/14-security`. W12 and W13 are immutable
published baselines and must not be modified, rewritten, rolled back, retagged,
or rereleased:

- W12 PR: https://github.com/taka-wzx/flowpilot-arena/pull/35
- W12 merge commit: `2c642a67341d0cd1c9c62b6bf883ad8df2853f40`
- W12 feature/head commit: `b00dff77b1626a3f347abfba485ac5a197b627a7`
- W12 tag: `w12-production`
- W12 Release: `v0.3.0 - Production Control Plane`
- W13 PR: https://github.com/taka-wzx/flowpilot-arena/pull/36
- W13 merge commit: `cedc5f26d41262c955b60854cc69ed4f28baded6`
- W13 feature/head commit: `902e4078e1ece0f401f1c5c3010e56a7ae62acf5`
- W13 tag: `w13-observability`
- W13 Release: `v0.4.0 - Observability and Replay`

The later W14 tag is expected to be `w14-security`, but this local
authorization does not permit pushing, opening a PR, merging, tagging, creating
a Release, dispatching CI, or rerunning remote workflows.

## W14 scope boundary

W14 preserves every W1-W13 API and security boundary, deterministic fake
baseline, released migrations, frozen catalogs/checksums/splits, recovery and
receipt contract, context and ablation contract, identity/tenant/RBAC/locking,
risk/approval/grant/audit, durable admission/outbox/limiter/backpressure/
lease/fence/four-slot cap, `finished_ungraded`, the independent Grader, formal
W12 ordinal 3 evidence, and W13 trace/replay/dashboard authority boundary.

W14 may add only deterministic local/CI security protection and verification:

- fixed, harmless local malicious-page and prompt-injection fixtures;
- closed server-trusted security taxonomy and decisions;
- bounded secret redaction for observations, errors, logs, traces, replay,
  dashboard checks, URLs, and evidence;
- stricter fixed-origin browser isolation, navigation, redirect, download, and
  new-window checks; and
- tests and evidence for prompt injection, hostile tool/model output, tenant
  isolation, RBAC, approval, redaction, sandboxing, zero business side effects,
  and W13 compatibility.

W14 does not change W8/W12/W13 success semantics, approval/authorization,
tenant isolation, rate limiting, queue/backpressure, lease/fence,
receipt/idempotency, audit authority, trace/replay authority, or Grader
behavior. Security records and test results are observation data only and never
authorize work, select an organization, or decide success.

W14 adds no W15 Reporting or external benchmark, W16 Helm/cloud/publication,
real IdP/account/personal data/approver, provider/model/OCR/VLM/embedding/
billing/egress, new queue or service, dynamic policy/ABAC/DSL, global
administrator or approver, impersonation, delegation, break-glass, L4
approval, physical deletion, arbitrary Shell/SQL/JavaScript/code/URL/API
capability, generic security framework, production certification, penetration
test, legal compliance claim, vulnerability-bounty conclusion, or placeholder.

## File ownership and change control

Change only exact paths listed in `docs/agent-contract.md`. Add a path to that
contract before changing it. Directory wildcards are forbidden. Any new
service, database expansion, dependency, real data/network/provider, physical
deletion, W15+ feature, or generic abstraction requires user direction first.

The literal pre-existing `%SystemDrive%/` path is outside ownership. Do not
inspect, enumerate, copy, modify, stage, scan, ignore, or delete it. Do not
access any `code_review_agent` repository.

## Engineering and security conventions

- Python target is 3.13. Use uv; never hand-edit a lockfile. Frontends remain
  TypeScript/React/Vite and use `npm ci` if touched.
- Authenticate and authorize before every tenant, rate-bucket, run, approval,
  trace, or replay query. Bearer material is accepted only in the Authorization
  header and is never logged, persisted, traced, exported, replayed, or placed
  in URLs.
- `ActorContext` comes only from fixed-policy verified OIDC plus current active
  organization-qualified database rows. Caller, page, DOM, screenshot, model,
  body, query, URL parameter, tool output, and forwarding headers never choose
  identity, organization, role, risk, approval, action allowlist, budget,
  priority, queue, worker, success, trace, replay, or cost.
- Every tenant-owned read, count, constraint, index, claim, lease, trace,
  replay, dashboard, and mutation is organization-qualified in SQL. Never read
  globally and filter in Python. Cross-organization and nonexistent objects
  share the same stable response.
- W11 raw approval material remains only in the bounded Control API vault.
  Workflow Worker, Temporal, Recovery, Planning, Browser, Web, Sandbox, Grader,
  logs, evidence, security records, trace, dashboard, replay, and URLs receive
  no raw credential or nonce.
- Prompt-injection policy is a fixed, closed, server-trusted decision. Page,
  DOM, screenshot, tool, and model text are always untrusted and cannot modify
  the policy or turn a rejection into an authorization.
- Each Browser run owns an isolated context and may reach only the configured
  local synthetic Sandbox origin. Reject boundary-crossing hosts, redirects,
  schemes, downloads, extra windows, and requests; never create real egress.
- Only the eight contract-frozen W12 task/action/parameter hashes may start a W8
  production effect. Any other admitted binding fails before Temporal/Browser.
- Delivery remains durable at-least-once with one active lease winner,
  deterministic workflow identity, stale-write fencing, and W8 receipt/
  idempotency enforcing at-most-one business side effect. Never call it
  distributed exactly-once.
- Agent completion remains `finished_ungraded`; only the independent Sandbox
  database-fact Grader decides success.
- Run, approval, audit, observability, trace, replay, dashboard, and security
  rows are never physically deleted. Audit remains one append-only canonical
  SHA-256 chain per organization and is tamper-evident, never tamper-proof.
- Default tests, Compose, security, trace, dashboard, and replay use only
  deterministic synthetic data. Evidence contains only versions, opaque IDs
  and hashes, counts, closed codes, HTTP states, latencies, security references,
  and real-call-zero counters. Never include raw task/page/DOM/model content,
  secrets, DSNs, personal data, or machine paths.
- Use strict/frozen Pydantic, `extra=forbid`, closed enums, canonical sorted-key
  compact UTF-8 JSON, stable SHA-256, small modules, and no unused dependency.

## Required local checks

For each changed Python project, run the locally available subset of:

~~~powershell
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
~~~

Because W14 adds one static Sandbox fixture, run `npm ci`, lint, typecheck, test,
and build for `apps/sandbox_web`. Run available YAML/workflow validation;
Compose config/build/up/health; relevant migration empty upgrade/current/check/
downgrade/upgrade; W4-W13 regression; W13 observability smoke; W14 deterministic
security smoke; frozen catalog/context/identity/approval/production checks;
real-call-zero proof; sensitive-field scan; exact allowlist review; staged and
unstaged review; and cleanup.

Do not rerun W12 formal Validation ordinal 3, create ordinal 4, execute W15
Reporting, or run an external benchmark.

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

Work only on `week/14-security`; never develop on main, W13, or amend a
published baseline. Development tests and bounded W14 smokes may repeat. This
authorization permits one local W14 feature commit only:

~~~text
feat: add W14 security suite and threat model
~~~

No push, PR, merge, tag, Release, workflow dispatch/rerun, formal W12
Validation, W15 Reporting, external benchmark, or real-provider call is
authorized. Never broad-stage. After every locally available gate and evidence
reconciliation, explicitly stage only exact W14 allowlist paths, create the one
local commit, and stop.
