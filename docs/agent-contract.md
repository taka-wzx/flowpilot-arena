# W7 agent contract - Bounded Planning DAG

## Authority, baseline, and sole objective

This contract translates the W7 row of `docs/project-roadmap.md` and the
user-authorized W7 brief into a bounded implementation agreement for
`week/07-planning`.

The verified release baseline is main commit
`1b239fc52173bc550f5601d34b8e87efc5dbf45f`. Before this branch was created,
HEAD and `origin/main` resolved to that commit, the local `w06-hybrid` object
was an annotated tag, and its dereferenced commit was the same baseline. A
read-only GitHub API check proved that remote `refs/tags/w06-hybrid` points to
annotated tag object `19e74859cb6066837d6708d3ffc618be3b3e00ea`, which in
turn points to the baseline commit. The eligible worktree was clean.

The pre-existing untracked literal `%SystemDrive%/` path remains outside every
read, enumeration, scan, diff, status, staging, and modification operation. No
`code_review_agent` repository may be accessed.

W7 has one outcome: preserve every released W1-W6 API, security boundary, and
fake baseline while adding a strict immutable task-local Planning DAG,
deterministic closed-set tool matching, one monotonic total budget ledger,
step-level runtime verification, and a separately versioned 30-template / 90-
instance synthetic JML catalog. The independent Arena Grader remains the only
task-success authority.

The W6 branch rules are superseded only on `week/07-planning`. W8 and later
roadmap architecture is non-authorizing and prohibited.

## W7 scope

W7 may add only:

1. a separate Python 3.13, non-root, deterministic-fake-only Planning Agent
   that connects only to Browser Worker over a dedicated internal network;
2. strict, versioned, `extra=forbid` schemas for plan request/result, immutable
   DAGs, steps, dependencies, conditions, tool catalog/matches/rejections, plan
   validation, step execution, verifier request/result, one total budget/usage
   ledger, and run/result;
3. deterministic plan generation from a trusted finite process/category,
   bounded human brief, and strict supplied values, without task-spec, fixture,
   expected-state, Grader, database, or page-text input;
4. deterministic topological execution through exactly one W6 Hybrid session,
   preserving one fresh Browser, Context, and Page for the complete run;
5. deterministic closed-set tool matching and step-level verification that
   cannot expand Worker, route, action, or budget authority;
6. an independent versioned W7 JML catalog with 12 Joiner, 8 Mover, and 10
   Leaver templates, three deterministic synthetic variants per template,
   template-level 18/6/6 split, stable IDs/checksums, and an independent W7
   database-fact Grader;
7. the smallest typed, non-deleting state-transition API/UI additions required
   by Mover and Leaver templates within the existing HRIS, ITSM, IAM, Asset,
   and Mail synthetic applications; and
8. deterministic unit/Compose acceptance, CI, documentation, locks, and safe
   numeric evidence.

W4 DOM, W5 Vision, and W6 Hybrid APIs keep their released semantics. Planning
Agent does not import or mutate those services. It consumes the W6 Hybrid HTTP
contract and uses one W6 session; it never joins W4 and W5 sessions.

## Explicit non-goals

W7 does not add real or paid models, OCR, VLM, provider adapters, model keys,
provider egress, real systems/accounts/data, external benchmarks, arbitrary
URLs, selectors, XPath, coordinates, rectangles, upload/download, Cookie or
Local Storage access, browser options, Shell, SQL, JavaScript, code execution,
dynamic APIs, MCP, plugins, arbitrary tool discovery, or a generic Agent/model/
tool framework.

W7 does not add W8 Temporal, checkpoints, recovery, idempotency, retries, fault
injection, or runtime partial replanning; W9 context, summary, memory,
retrieval, cache, or cross-task history; W10 identity, OIDC, RBAC, tenancy, or
optimistic locking; W11 HITL, policy execution, approval token/service, or
audit chain; W12 production workers, backpressure, rate limiting, load tests,
or production deployment; W13 OTel, tracing, dashboards, formal replay, or
monitoring; W14 malicious-page evaluation; W15 external/Reporting evaluation,
formal ablation, or repeated benchmark runs; or W16 Helm/cloud/release work.

W7 does not edit the released W2/W3 migrations, W3 Task Specs, fixture,
expected state, grader predicates, canonical checksums, catalog checksum,
6/2/2 split, or manual-baseline evidence. It does not persist raw human briefs,
plans, DOM, screenshots, OCR, page text, form values, model output, Cookies,
Local Storage, credentials, endpoints, tokens, or machine paths.

## Exact W7 file allowlist

Only these paths may be created or modified in W7:

~~~text
AGENTS.md
README.md
CHANGELOG.md

.github/workflows/ci.yml

docs/agent-contract.md
docs/architecture.md
docs/threat-model.md
docs/evaluation-protocol.md
docs/adr/0007-w7-bounded-planning-dag.md
docs/plans/week-07-planning.md
docs/evidence/week-07-report.md
docs/data/week-07-jml-catalog.md

deploy/compose/compose.yaml

apps/planning_agent/.dockerignore
apps/planning_agent/Dockerfile
apps/planning_agent/pyproject.toml
apps/planning_agent/uv.lock
apps/planning_agent/src/flowpilot_planning_agent/__init__.py
apps/planning_agent/src/flowpilot_planning_agent/budget.py
apps/planning_agent/src/flowpilot_planning_agent/client.py
apps/planning_agent/src/flowpilot_planning_agent/dag.py
apps/planning_agent/src/flowpilot_planning_agent/executor.py
apps/planning_agent/src/flowpilot_planning_agent/main.py
apps/planning_agent/src/flowpilot_planning_agent/planner.py
apps/planning_agent/src/flowpilot_planning_agent/schemas.py
apps/planning_agent/src/flowpilot_planning_agent/tools.py
apps/planning_agent/src/flowpilot_planning_agent/verifier.py
apps/planning_agent/src/flowpilot_planning_agent/worker_schemas.py
apps/planning_agent/tests/conftest.py
apps/planning_agent/tests/test_api.py
apps/planning_agent/tests/test_budget.py
apps/planning_agent/tests/test_client.py
apps/planning_agent/tests/test_dag.py
apps/planning_agent/tests/test_executor.py
apps/planning_agent/tests/test_planner.py
apps/planning_agent/tests/test_schemas.py
apps/planning_agent/tests/test_tools.py
apps/planning_agent/tests/test_verifier.py

apps/sandbox_api/src/flowpilot_sandbox_api/main.py
apps/sandbox_api/src/flowpilot_sandbox_api/schemas.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/jml/__init__.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/jml/catalog.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/jml/grader.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/jml/router.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/jml/schemas.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/jml/service.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/jml/data/catalog-v1.json
apps/sandbox_api/tests/test_business_transitions.py
apps/sandbox_api/tests/test_jml_api.py
apps/sandbox_api/tests/test_jml_catalog.py
apps/sandbox_api/tests/test_jml_grader.py
apps/sandbox_api/tests/test_jml_service.py

apps/sandbox_web/src/api.ts
apps/sandbox_web/src/types.ts
apps/sandbox_web/src/pages/HrisPage.tsx
apps/sandbox_web/src/pages/ItsmPage.tsx
apps/sandbox_web/src/pages/IamPage.tsx
apps/sandbox_web/src/pages/AssetPage.tsx
apps/sandbox_web/src/pages/MailPage.tsx
apps/sandbox_web/src/App.test.tsx

tests/integration/Dockerfile
tests/integration/w7_planning_compose_smoke.py
~~~

Released source outside this list is a regression input, not a W7 target. No
database migration is required or allowed by this contract: existing bounded
string state fields and HRIS transfer fields represent every authorized W7
transition. If implementation evidence proves a schema change necessary, its
exact forward-only migration and related paths must be added here before any
such file is created; released migrations remain immutable.

Any other path must be added to this contract before it changes. A path that
introduces another system, real data, physical deletion, approval bypass, W8+
capability, or generic future abstraction requires new user direction first.

## Planning DAG contract

All W7 Planning models are frozen strict Pydantic models with unknown fields
forbidden and immutable validated instances. Schema versions are under the
`w7-* /1.0` namespace. Every run accepts one bounded human brief, one finite
process/category, one discriminated strict supplied-values object, one fake
scenario, and one total budget. The planner may not inspect `task_id` to choose
facts or behavior.

Each step includes `step_id`, untrusted bounded `objective`, `dependencies`,
closed `operation`, `expected_page`, `required_context`, `allowed_actions`,
`preconditions`, `postconditions`, `risk_level`, `retry_policy`, and
`fallback`. `objective` never authorizes an operation, route, tool, action, or
value. Authority comes only from the validated finite process/category,
closed operation, strict supplied values, global catalog, Worker state, and
remaining ledger.

Frozen DAG caps are:

| Limit | Maximum |
|---|---:|
| nodes | 16 |
| edges | 24 |
| depth | 8 |
| width at one topological level | 8 |
| dependencies per node | 4 |
| step ID length | 40 characters |
| objective length | 240 characters |
| conditions per pre/post list | 8 |
| serialized canonical plan | 32,768 UTF-8 bytes |

Validation rejects unknown or duplicate step IDs, self-dependency, unknown or
missing dependencies, cycles, more than one root, nodes unreachable from the
single root, and every cap breach. It calculates a deterministic topological
order using lexical `step_id` tie-breaking. A run owns exactly one validated
frozen DAG and its SHA-256 identifier. It cannot be replaced or partially
replanned while running.

Executor state transitions are `pending -> ready -> executing -> verified` or
`pending/ready/executing -> blocked/failed/escalated`. A step may enter
`executing` only when every dependency is `verified`. Unknown, duplicate,
terminal-to-running, or out-of-order transitions fail closed. `retry_policy`
is only `no_retry`; `fallback` is only `stop` or `escalate`.

## Deterministic tool matching and execution

The versioned tool catalog is a closed mapping to released W6 observation and
typed-action capabilities only. Pages are exactly HRIS `/hris`, ITSM `/itsm`,
IAM `/iam`, Asset `/assets`, and Mail `/mail`. No candidate string can create
a tool.

For every match, the effective tools are the intersection of:

1. the W7 global tool allowlist;
2. the current step's closed `allowed_actions`;
3. the current fixed page and selected Worker modality allowlist; and
4. the current remaining total budget.

Brief text, objective/postcondition text, page/DOM/JPEG/OCR content, model
output, and risk metadata cannot add authority. Unknown and disallowed
candidates return a closed safe rejection reason and never reach Browser
Worker. Element-name matching may select only a current Worker-issued opaque
reference after the operation/action has already been authorized by the four-
way intersection. The Worker revalidates the session, generation, modality,
observation, reference, and action before Playwright.

Planning Agent creates one W6 Hybrid session at `/hris`, retains that session
for the whole immutable DAG, and uses current DOM observations for the shipped
fake execution. It never creates another session to change modality. W6 Router
semantics and the independent W6 DOM-to-Vision smoke remain unchanged. Any new
observation, action success/failure, verification probe, modality switch,
timeout, terminal action, deletion, startup failure, cancellation, or shutdown
continues to invalidate old DOM and visual references in Browser Worker.

## Step Verifier contract

The runtime Verifier is not Arena Grader. It returns only `verified`,
`not_verified`, or `inconclusive` with closed safe reason codes. It may consume
only the current Worker observation, current typed action result summary,
trusted bounded step conditions, immutable step identity, and current total
budget. It cannot read Task Spec, fixture maps, expected state, grader
predicate, canonical checksum, database, Arena, Reset/Seed, Reporting results,
Planner/model self-report, page success prose, or `finish` as proof.

Verifier cannot expand tools, actions, routes, or budgets. A negative or
inconclusive result never marks a step verified. With `no_retry`, verification
failure follows the step's fixed `stop` or `escalate` fallback. Agent `finish`
returns only `finished_ungraded`; independent Grader alone may return score,
passed, or success.

## One monotonic total budget ledger

Planning, tool matching/rejection, browser execution, routing accounting,
verification, and termination share one task-local ledger using a monotonic
clock. No plan step, observation, mode switch, verifier probe, failure, or
terminal path may replace or reset it.

Default maxima freeze at: one plan generation; the DAG caps above; 64 tool
match attempts; 16 tool rejections; 16 verifier calls; 16 verifier probes; 16
executed steps; 16 blocked/failed steps; 24 Worker actions/steps; 24 model
calls; two switches; two repeated actions; three no-progress events; 24 DOM
observations; 262,144 raw DOM bytes; 147,456 compressed-DOM accounting bytes;
24 images; 4,423,680 image bytes; 12,441,600 image pixels; 72,000 capture ms;
100,000 total input tokens; 20,000 total output tokens; 100,000 planning input
tokens; 20,000 planning output tokens; 100,000 verifier input tokens; 20,000
verifier output tokens; zero micro-USD total/planning/verifier cost; and 300
monotonic seconds. Request values may only reduce these schema maxima.

Budget checks occur before and after every counted operation. Usage and result
schemas expose safe counters, closed reason codes, opaque hashes, and terminal
state only.

## W7 JML catalog and Sandbox increments

The W7 catalog is independent of the immutable W3 catalog. Its catalog schema,
variant generator, fixture, split manifest, and grader schemas are versioned.
It contains exactly 12 Joiner, 8 Mover, and 10 Leaver templates. Each template
generates variants `v1`, `v2`, and `v3`, producing exactly 90 stable instance
IDs and canonical checksums.

Template-level split is fixed as:

| Split | Joiner | Mover | Leaver | Total |
|---|---:|---:|---:|---:|
| Development | 8 | 4 | 6 | 18 |
| Validation | 2 | 2 | 2 | 6 |
| Reporting | 2 | 2 | 2 | 6 |

The catalog checksum is SHA-256 over canonical sorted template JSON excluding
its checksum field. Instance checksums are SHA-256 over canonical generated
instance JSON. Split and Reporting manifest checksums are SHA-256 over sorted
template/instance/checksum rows. Source and license are fixed to original
FlowPilot synthetic W7 data under Apache-2.0. Names/identifiers are explicitly
fictional, emails use `.invalid`, and assets use `SYN-W7-...`.

Reporting is limited in W7 to deterministic generation, loading, strict schema
and checksum verification, and manifest freezing. No Reporting Agent run,
grade-result inspection, tuning, or policy change is permitted. Validation is
not used for repeated tuning.

The only Sandbox behavior additions are:

- HRIS: `confirmed -> transferred` with bounded new department/job/location,
  or `confirmed/transferred -> disabled`;
- ITSM: `open -> closed`;
- IAM: `active -> revoked`;
- Asset: `assigned -> released`; and
- Mail: `active -> disabled`.

They are employee-owned, strict typed transitions over existing rows. Unknown
employees/rows, wrong prior states, extra fields, unsupported values, and
repeated transitions fail closed. There is no physical deletion, arbitrary
field patch, generic transition endpoint, approval artifact, or new database
schema. Planning Agent cannot call these APIs directly; only Browser Worker
may operate their fixed Sandbox UI controls.

Reset/Seed deletes only rows owned by the selected W7 task ID in dependency
order and recreates fixed synthetic facts in one transaction. The independent
W7 Grader reads database facts only and does not expose predicates/expected
state to Planning Agent. W3 Reset/Seed and Grader remain byte-for-byte
regression targets.

## Evaluation, Compose, and evidence

Default tests, CI, Compose, Planner, execution model, and Verifier are local
deterministic fakes with zero external calls and zero actual cost. W4 DOM, W5
Vision, and W6 Hybrid fake smokes run unchanged.

W7 fake Planning acceptance must prove an actually executed multi-node,
multi-dependency DAG; deterministic topology; successful matching; explicit
unknown/unauthorized-tool rejection; step verification; negative/inconclusive
verification not counted as success; rejection of cycle, missing dependency,
out-of-order execution, and over-limit plans; one non-resetting ledger;
terminal cleanup; and `finished_ungraded` isolation.

On the same W3 Development task and equal Reset/Seed checksum, W6 Hybrid and
W7 Hybrid+Planner fake baselines are paired. W7 immediate finish must grade
30/100 false. Fresh W7 deterministic completion must return
`finished_ungraded` and independently grade exactly 100/100 true.

For W7 Development data, one Joiner, Mover, and Leaver instance each receives
two equal Reset/Seeds, an untouched failing grade, a bounded deterministic
completion returning `finished_ungraded`, and an independent exact 100/100
passing grade. All 30 templates / 90 instances are checked for count, process
distribution, split distribution, stable IDs/checksums, deterministic Reset/
Seed, and Grader schema without using Validation/Reporting for tuning.

Compose adds Planning Agent as non-root, read-only, cap-dropped,
no-new-privileges, tmpfs/pids-bounded, credential-free, without host port,
mount, Docker socket, or provider egress. It joins only dedicated internal
`planning-worker`, which contains Browser Worker and no Sandbox, Arena,
database, DOM/Vision/Hybrid Agent, or provider service. Profile-only acceptance
orchestration may join management networks for Reset/Seed and independent
grading; it is not an Agent tool or normal-profile service.

Evidence records only schema versions, opaque IDs/hashes, template/task/
variant IDs and checksums, DAG counts/depth/order, step state counts, tool
match/rejection counts and safe reasons, route/DOM/compression/image/action/
model/token/cost/latency counters, terminal status, and independent grade. It
records no raw brief, plan prose, DOM, screenshot, OCR, page/form content,
credential, token, endpoint, Cookie, Local Storage, personal data, or machine
path. Fake evidence proves wiring and isolation, not real planning, reasoning,
Verifier, DOM, Vision, Hybrid, OCR, or VLM capability.

## Git and handoff rules

Work only on `week/07-planning`. Do not push, create a PR, merge, tag, release,
trigger remote CI, force-push, or call a real model without separate explicit
user authorization. Do not stage broadly; stage only exact final allowlist
paths after all locally available gates pass and evidence matches observed
facts. Record unavailable Docker/Compose/pre-commit/Gitleaks tooling rather
than weakening a gate.

W7 stops after bounded Planning DAG, matching, ledger, runtime Verifier, full
synthetic JML catalog, minimum transitions, and fake-only evidence. W8 work is
not started.
