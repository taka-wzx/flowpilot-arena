# W9 agent contract - Context, Retrieval, Summary, and Organization Memory

## Authority, baseline, and sole objective

This contract translates the W9 row and section 7 of
`docs/project-roadmap.md` plus the user-authorized W9 brief into the only
implementation authority for `week/09-context`.

W9 starts from the released W8 merge commit
`9ecc31f3e525ae57260bc47ddab5d1d8c1baba6f`. Pull request #30 merged normally;
pull-request run `30419997200` and post-merge main run `30420371034` each passed
17/17 jobs on their first attempt. Annotated tag `w08-recovery` dereferences to
that merge commit and the published release is `v0.2.0 - Hybrid + Recovery`.
W8 is immutable and is neither amended nor republished by W9.

The literal `%SystemDrive%/` path remains outside every read, enumeration,
scan, diff, status, staging, and modification operation. No
`code_review_agent` repository may be accessed.

W9 has one outcome: preserve every W1-W8 API, database fact, Grader,
Reporting freeze, security boundary, budget, and deterministic fake baseline
while adding a strict five-layer task-local context result, deterministic
fixed-catalog retrieval, deterministic short-term summary, scoped synthetic
organization memory, context ablations, and cumulative context accounting.
Database facts remain the only task-fact authority; Agent finish remains
`finished_ungraded`; only the independent database-fact Grader decides
success.

## Exact W9 scope

W9 may add only:

1. five ordered layers named `task_facts`, `browser_working`, `short_term`,
   `org_memory`, and `enterprise_knowledge` inside the existing Planning Agent;
2. strict frozen W9 schemas with closed enums, explicit schema versions,
   canonical sorted-key UTF-8 JSON, and reproducible SHA-256 hashes;
3. task facts supplied only as a trusted synthetic Sandbox-database safe
   projection; no page, model, summary, or memory value may create or override
   a task fact;
4. browser working memory made only from current closed browser event codes,
   current opaque references/hashes, expiry, and pending step IDs; it stores no
   DOM, screenshot, OCR, page, form, URL, selector, or arbitrary text;
5. one deterministic task-local short-term summarizer over closed safe events,
   preserving unresolved issues, recent actions, failure reasons, and pending
   steps under frozen item/byte/token limits;
6. one process-local fake-only organization-memory store for closed synthetic
   department, role, location, device preference, and approval-chain
   projections, with trusted scope/task ownership, monotonic versions,
   deterministic expiry and tombstones, and default-deny cross-scope access;
7. one fixed local synthetic enterprise-knowledge catalog with version,
   source, trust, validity, scope, closed category, keywords, content hash, and
   deterministic lexical/hash retrieval;
8. one deterministic Context Assembler that filters identity/scope, routes by
   closed task phase, retrieves, filters expiry/trust, deduplicates, sorts,
   budgets each layer and the whole result, and emits complete provenance;
9. frozen Development-only ablations `full_five_layer`, `task_facts_only`,
   `no_short_term`, `no_enterprise_retrieval`, and
   `no_organization_memory`; no browser-working-memory ablation is admitted;
10. additive W9 endpoints for context assembly and context-backed Planning
    runs without modifying or replacing any released W7/W8 endpoint;
11. additive context/retrieval/summary/memory counters in the same task-local
    W7 total ledger and its W8 durable safe projection, with every released
    W6-W8 cap unchanged; and
12. deterministic unit, API, replay/round-trip, Compose, ablation, JML
    Development, independent-grade, regression, cleanup, and safe evidence
    checks.

The organization-memory store is deliberately process-local and synthetic.
It proves strict schemas, version/delete/expiry behavior, and scope rejection;
it is not a claim of production durability, authentication, tenancy, or
authorization. Fixed seed records can be reconstructed after process restart.
No hidden cross-task conversation history exists.

## Explicit non-goals

W9 adds no W10 OIDC, login, user/organization directory, RBAC, authenticated
tenant isolation, real tenant, optimistic locking, or identity provider; W11
HITL, approval service/token, risk execution, or audit chain; W12 production
worker, backpressure, rate limiting, concurrency/load test, or deployment; W13
OTel, tracing, dashboard, replay platform, or monitoring; W14 malicious-page
suite; W15 external benchmark, formal Reporting, repeated evaluation, or
result inspection; or W16 Helm, cloud, publication, tag, or release.

It adds no real vector database, embedding, model, provider, OCR, VLM, key,
credential, or egress; arbitrary query, URL, header, interception, API,
selector, XPath, coordinate, rectangle, path, Shell, SQL, JavaScript, or code;
real enterprise system/account/data; generic Agent/memory/retrieval framework;
dynamic plugin/MCP/tool discovery; cache; physical business-data deletion;
cross-scope fallback; or W10+ placeholder abstraction.

Released W2/W3 migrations, W3 Task Specs/fixtures/predicates/checksums/splits,
W7 catalog/instances/checksums/splits, W8 migration/receipt/Checkpoint/recovery
contracts, independent Graders, and Reporting manifests are immutable. W9
introduces no database migration and Alembic must remain at released W8 head
`20260728_0003` with no drift.

## Exact W9 file allowlist

Only the following paths may be created or modified. A new path must be added
here before it changes; any scope-expanding path requires new user direction.

~~~text
AGENTS.md
README.md
CHANGELOG.md

.github/workflows/ci.yml

docs/agent-contract.md
docs/project-roadmap.md
docs/architecture.md
docs/threat-model.md
docs/evaluation-protocol.md
docs/adr/0009-w9-context.md
docs/plans/week-09-context.md
docs/evidence/week-09-report.md
docs/data/week-09-context-data.md

apps/planning_agent/src/flowpilot_planning_agent/budget.py
apps/planning_agent/src/flowpilot_planning_agent/context.py
apps/planning_agent/src/flowpilot_planning_agent/context_catalog.py
apps/planning_agent/src/flowpilot_planning_agent/context_schemas.py
apps/planning_agent/src/flowpilot_planning_agent/executor.py
apps/planning_agent/src/flowpilot_planning_agent/main.py
apps/planning_agent/src/flowpilot_planning_agent/memory.py
apps/planning_agent/src/flowpilot_planning_agent/retrieval.py
apps/planning_agent/src/flowpilot_planning_agent/schemas.py
apps/planning_agent/src/flowpilot_planning_agent/summary.py
apps/planning_agent/tests/test_api.py
apps/planning_agent/tests/test_budget.py
apps/planning_agent/tests/test_context.py
apps/planning_agent/tests/test_context_schemas.py
apps/planning_agent/tests/test_executor.py
apps/planning_agent/tests/test_memory.py
apps/planning_agent/tests/test_retrieval.py
apps/planning_agent/tests/test_summary.py

apps/recovery_worker/src/flowpilot_recovery_worker/schemas.py
apps/recovery_worker/tests/test_schemas.py

deploy/compose/compose.yaml
tests/integration/Dockerfile
tests/integration/w9_context_compose_smoke.py
~~~

No dependency or lockfile change is planned. If implementation discovers that
one is necessary, both manifest and lockfile must first be added to this
allowlist and the addition must remain inside the user-authorized W9 scope.

## Strict schemas, canonicalization, and provenance

All W9 Pydantic models inherit the existing strict/frozen/`extra=forbid`
configuration. Collections are immutable tuples after JSON-array validation.
Closed enums define layer, process, phase, category, source, trust, status,
event, memory field, mutation, ablation, and rejection values. Unknown fields,
versions, values, scope, task owner, expiry, trust, source, or hash fail closed.

Canonical JSON is UTF-8 with sorted keys, no insignificant whitespace, and
unescaped Unicode. SHA-256 is lowercase hexadecimal. A context-result hash
excludes only `context_hash`; a summary hash excludes only `summary_hash`; a
catalog checksum covers the ordered canonical catalog; memory content hashes
cover only the safe closed projection. Ordering never depends on set/dict
iteration.

Every emitted context item includes its layer, closed category, safe value,
source ID, source version, trust level, validity/expiry, content hash, byte
count, and deterministic token estimate. Runtime values are safe synthetic
projections, not raw brief/objective/form/page/DOM/image/OCR/model content.

## Five-layer authority and trust boundary

Layer order and precedence are fixed:

1. `task_facts`: `sandbox_database` source and `authoritative` trust only;
2. `browser_working`: current Worker-issued safe observation/action projection
   with `runtime_observed` trust;
3. `short_term`: deterministic current-task summary with `task_supplied` trust;
4. `org_memory`: exact trusted synthetic scope, active record, and
   `organization_curated` trust; and
5. `enterprise_knowledge`: fixed catalog with `enterprise_curated` trust.

Lower layers can add context but can never replace, contradict, close, or mark
success for a task fact. Duplicate content hashes keep the earliest layer;
within a layer, the deterministic ranking rules apply. Browser/page/email/PDF
text is untrusted data and has no schema path for selecting a query, tool,
route, phase, action, permission, budget, memory scope, write, delete, or
success state.

`task_facts` accepts only closed safe facts whose request declares the exact
task ID, trusted synthetic scope ID, `sandbox_database` source, snapshot
version, and database snapshot hash. The Context Assembler does not read the
Arena, Task Spec, expected state, Grader predicate/checksum, or Reporting
result. A caller that cannot provide the trusted snapshot fails closed instead
of substituting memory or browser content.

## Deterministic retrieval contract

Enterprise queries are selected only from the closed categories
`joiner_policy`, `mover_policy`, `leaver_policy`, `permission_matrix`,
`device_standard`, and `operating_manual`. The assembler derives the category
from trusted process and task phase. It accepts no free query string or page/
model-proposed term.

Each closed query maps to frozen lexical terms. Retrieval filters exact/global
synthetic scope, allowed source, minimum trust, active version, and validity at
the request's explicit UTC `as_of`. It groups by content hash, keeps the
highest-version trusted active item, then sorts by descending lexical score,
descending trust rank, descending version, content hash, and item ID. The
content hash is also the deterministic final tie breaker. `top_k` is fixed at
3. Zero-score items are rejected. No embedding, vector index, network, model,
or provider is called.

## Deterministic summary contract

Short-term input is limited to closed safe event kinds
`unresolved_issue`, `recent_action`, `failure_reason`, `pending_step`, and
`user_supplement`, each with a safe code/value, source hash, ordinal, and task
owner. The summarizer validates task/scope ownership, sorts by fixed kind
priority then descending ordinal then source hash, deduplicates equal
kind/value pairs, and applies the frozen item/byte/token caps. It preserves at
least one entry of every present required kind before lower-priority duplicate
or supplemental entries.

Summary output records ordered entries, ordered source hashes, input count,
deduplicated count, emitted count, dropped count, canonical byte/token counts,
and summary hash. It never modifies task facts, calls a model, creates an
implicit memory write, or carries data to another task.

## Organization-memory contract

Synthetic scope IDs and task IDs are supplied only by the trusted Development
harness. Read/upsert/delete requires the same actor scope, record scope, and
task owner; mismatch is rejected before lookup or mutation. There is no
wildcard, administrator bypass, fallback scope, or tenant claim.

Records contain only closed memory field and safe synthetic value, source,
trust, version, active/tombstone status, validity interval, and content hash.
The store increments version exactly by one per `(scope_id, memory_id)` write.
Delete creates a deterministic tombstone and does not physically erase prior
business data. Reads omit tombstones and expired records. Reset is limited to
the exact task/scope owner. Optimistic locking is deliberately absent because
it belongs to W10; W9 serializes process-local mutations.

## Context budgets and one monotonic ledger

Layer caps are frozen:

| Layer | Items | Canonical bytes | Estimated tokens |
|---|---:|---:|---:|
| task facts | 8 | 4,096 | 1,024 |
| browser working | 6 | 3,072 | 768 |
| short term | 8 | 4,096 | 1,024 |
| organization memory | 6 | 3,072 | 768 |
| enterprise knowledge | 6 | 4,096 | 1,024 |

The whole result is capped at 32 items, 16,384 canonical bytes, and 4,096
estimated tokens. Tokens are deterministically estimated as
`ceil(UTF-8 bytes / 4)`. Earlier-layer precedence is preserved when the total
cap truncates later layers. Oversized single items are rejected, never partly
cut. Frozen short-term caps are 12 inputs, 8 outputs, 4,096 bytes, and 1,024
tokens. Retrieval is at most 6 candidates and fixed top-3 output. Organization
memory is at most 6 reads, 6 writes, and 6 deletes per task context run.

New cumulative counters are `context_assemblies`, `context_items`,
`context_bytes`, `context_tokens`, `retrieval_queries`,
`retrieval_candidates`, `retrieval_selected`, `summary_inputs`,
`summary_outputs`, `summary_dropped`, `memory_reads`, `memory_writes`,
`memory_deletes`, and `memory_rejections`. They live in the existing sole
Planning `TotalBudgetLedger`; W8 copies them into its existing durable safe
usage high-water projection and rejects decreases. They never reset during a
task or recovery and contain no raw content.

No released W6/W7/W8 action, step, observation, image, model, token, cost,
time, retry, recovery, receipt, Checkpoint, fault, or replan limit is raised.
Context exhaustion safely stops the W9 context-backed run before Planning
execution; it does not borrow from or enlarge an existing cap.

## Context assembly and ablations

Assembly order is fixed: validate trusted identity/scope/task/process/phase;
charge the ledger; apply exact-scope memory mutations; validate authoritative
task facts; filter current browser working entries; summarize short-term
events; retrieve the closed enterprise category; read active organization
memory; normalize provenance; deduplicate by content hash; enforce each layer
budget; enforce total budget; canonicalize and hash.

The frozen Development matrix is:

| Profile | task facts | browser | short term | org memory | enterprise |
|---|---:|---:|---:|---:|---:|
| full_five_layer | on | on | on | on | on |
| task_facts_only | on | off | off | off | off |
| no_short_term | on | on | off | on | on |
| no_enterprise_retrieval | on | on | on | on | off |
| no_organization_memory | on | on | on | off | on |

Every profile retains authoritative task facts. The matrix is immutable before
any Validation run. Ablations run only on deterministic synthetic Development
instances; Reporting is not executed and W15 formal evaluation is not claimed.

## Evaluation, evidence, and data discipline

Unit and API tests cover strict/frozen schemas; canonical replay and checksum;
all five layers; task-fact precedence; browser expiry; summary preservation,
dedupe, truncation, and no fact mutation; retrieval scope/version/source/trust/
expiry/dedupe/order; organization-memory version/scope/delete/expiry/reset;
cross-scope rejection; untrusted instruction rejection; item/byte/token and
ledger budgets; deterministic ordering; all frozen ablations; and W8 durable
counter monotonicity.

Compose Development runs one Joiner, one Mover, and one Leaver through the W9
context-backed Planning path after equal Reset/Seed, expects
`finished_ungraded`, and independently grades database facts. W4-W8 smokes run
unchanged. Immediate finish still fails independent grading. W3 and W7 catalog,
split, checksum, and Reporting-manifest freeze checks remain required.

Validation may run at most one preregistered final context check and only after
catalog, budgets, ordering, and ablation matrix freeze. Evidence must state
whether it ran. Reporting is limited to generation/load/schema/checksum
validation and receives no Reset, Seed, Agent, context, memory, retrieval,
grade, result execution, or result inspection before W15.

Logs, evidence, durable usage, and CI output may contain only schema/catalog
versions, opaque synthetic IDs/hashes, counts, closed status/reason/source/
trust codes, ablation names, and independent numeric grades. They must not
contain raw brief, objective, supplied/form value, DOM, screenshot, OCR,
page/email/PDF content, model output, credential, token, key, endpoint, Cookie,
Local Storage, personal data, or machine path. Real model/provider/OCR/VLM/
embedding calls remain not run at 0 calls and 0 cost.

## GitHub Actions quota and Git completion rules

W9 remote delivery is not authorized. Do not push, create a PR, merge, tag,
release, trigger/rerun remote CI, or call a real model without separate explicit
user authorization in the current conversation. W9 creates no `v0.3.0`
Release; that version belongs to W12.

If remote delivery is later authorized, diagnose all failures first, make one
concentrated fix and one necessary feature push. With no code/lock/workflow
change and a transient infrastructure failure, rerun failed jobs only. Never
rerun all jobs, a successful run, a superseded run, or create an empty commit,
duplicate PR, quota-only workflow dispatch, force-push, or unrelated CI change.
Record every necessary extra run ID, commit SHA, trigger, code-change state,
and why failed-job-only rerun was insufficient.

Local completion requires all app locks/quality/tests; W3/W7 data freeze;
W4-W9 Compose smokes; released Alembic head/current/check with no migration;
one frozen Development Joiner/Mover/Leaver at independent grade 100; all five
ablations; exact allowlist audit; secret/diff/path checks; staged and unstaged
review; and zero remaining project container, network, or volume. Unavailable
Docker, Compose, pre-commit, Gitleaks, or network tooling is recorded, never
treated as a pass or repeatedly retried.

After every locally available gate passes and evidence matches observed
results, explicitly stage only exact allowlist paths, create one local W9
commit, and stop. Do not begin W10.
