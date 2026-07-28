# W8 agent contract - Durable Recovery

## Authority, baseline, and sole objective

This contract translates the W8 row of `docs/project-roadmap.md` and the
user-authorized W8 brief into the only implementation authority for the local
stacked branch `week/08-recovery`.

W8 is restacked on released W7 main commit
`0aa1349ffee0bfabdb8c9f02787f37dfe7f7c029`, which contains unchanged W7
source commit `146ab46b5b1753e16c64cbc46198668dba08ce01`. PR #29
merged normally after pull-request run `30342549814`, attempt 2, passed all 15
jobs. Post-merge main run `30416799576` also passed all 15 jobs, and annotated
tag `w07-planning` resolves to the W7 merge commit. The W8 rebase changed only
commit ancestry; its tree remained unchanged.

The literal `%SystemDrive%/` path remains outside every read, enumeration,
scan, diff, status, staging, and modification operation. No
`code_review_agent` repository may be accessed.

W8 has one outcome: preserve W1-W7 while adding deterministic Temporal
orchestration, versioned durable Checkpoints, fresh-epoch browser recovery,
transactional idempotency, bounded retry, trusted deterministic faults, and
one bounded immutable DAG revision. Independent database-fact grading remains
the only success authority; Agent finish remains `finished_ungraded`.

## Exact scope

W8 may add only:

1. one independent Python 3.13 Recovery Workflow Worker using Temporal Python
   SDK `1.30.0`, connected only to fixed Temporal Server and Planning Agent;
2. one fixed `temporalio/server:1.31.2` local server, fixed
   `temporalio/admin-tools:1.31.2` one-shot schema/namespace bootstrap, and a
   separate fixed PostgreSQL persistence service, with no UI, cloud service,
   or host port;
3. a deterministic Workflow that stores only versioned safe state, schedules
   Activities, uses Temporal workflow time/IDs, and chooses from closed reason
   codes;
4. an AES-256-GCM opaque durable envelope encrypted outside Workflow code with
   a runtime-injected key, so Temporal history never receives plaintext brief,
   objective, supplied values, DOM, screenshot, form content, or endpoint;
5. strict frozen W8 schemas for start/result, workflow state, Checkpoint,
   Activity, session epoch, retry, receipt, recovery, fault, DAG revision,
   budget, cleanup, and terminal results;
6. explicit fresh Browser/Context/Page session epochs, at most two recoveries,
   with old session/generation/observation/element/screenshot/grounding refs
   invalidated before a new epoch;
7. a forward-only Sandbox migration adding only the task-owned
   `w8_operation_receipts` table and its constraints/indexes;
8. transactionally atomic receipt creation and fixed synthetic mutation,
   same-key/same-hash replay, and same-key/different-hash rejection;
9. closed `no_retry` and `transient_once` policies, at most two attempts per
   Activity, and the fixed recovery order in this contract;
10. one deterministic fake-only partial replan that preserves completed steps
    and replaces only a failed step plus not-started descendants;
11. trusted acceptance-only fault scenarios, replay/determinism tests, W4-W7
    regressions, W8 Compose acceptance, and safe numeric/hash evidence; and
12. a CI trigger optimization that retains full pull-request CI, runs push CI
    only on main, and does not remove or weaken any W1-W8 job.

## Explicit non-goals

W8 adds no W9 context, summary, memory, retrieval, cache, or cross-task
history; W10 OIDC, users, organizations, RBAC, tenancy, or optimistic locking;
W11 HITL, approval service/token, risk-policy execution, or audit chain; W12
production worker, backpressure, rate limiting, load test, or production
deployment; W13 OTel, tracing, dashboard, replay platform, or monitoring; W14
malicious-page suite; W15 external benchmark, Reporting execution, formal
ablation, or repeated runs; or W16 Helm, cloud deployment, repository
publication, tag, release, or release automation.

It adds no real model/provider/OCR/VLM/key/egress, real enterprise system,
account, or data; arbitrary URL/header/interception/API/selector/XPath/
coordinate/rectangle/path/Shell/SQL/JavaScript/code; dynamic plugin, MCP, tool
discovery, generic Agent/workflow framework; physical deletion, compensating
transaction, business rollback, approval bypass, or W9 placeholder.

Released W2/W3 migrations, W3 Task Specs/fixtures/predicates/checksums/split,
W7 catalog/instances/checksums/split/Reporting manifest, and manual-baseline
evidence are immutable.

## Exact W8 file allowlist

Only the following paths may be created or modified. Any new path must be
added here before it changes; scope-expanding additions require new user
direction.

~~~text
AGENTS.md
README.md
CHANGELOG.md

.github/workflows/ci.yml

docs/agent-contract.md
docs/architecture.md
docs/threat-model.md
docs/evaluation-protocol.md
docs/adr/0008-w8-durable-recovery.md
docs/plans/week-08-recovery.md
docs/evidence/week-08-report.md
docs/data/week-08-recovery-data.md

deploy/compose/compose.yaml
deploy/compose/temporal/Dockerfile
deploy/compose/temporal/create-namespace.sh
deploy/compose/temporal/dynamicconfig/development-sql.yaml
deploy/compose/temporal/server.Dockerfile
deploy/compose/temporal/setup-postgres.sh

apps/recovery_worker/.dockerignore
apps/recovery_worker/Dockerfile
apps/recovery_worker/pyproject.toml
apps/recovery_worker/uv.lock
apps/recovery_worker/src/flowpilot_recovery_worker/__init__.py
apps/recovery_worker/src/flowpilot_recovery_worker/activities.py
apps/recovery_worker/src/flowpilot_recovery_worker/client.py
apps/recovery_worker/src/flowpilot_recovery_worker/crypto.py
apps/recovery_worker/src/flowpilot_recovery_worker/main.py
apps/recovery_worker/src/flowpilot_recovery_worker/schemas.py
apps/recovery_worker/src/flowpilot_recovery_worker/workflow.py
apps/recovery_worker/tests/conftest.py
apps/recovery_worker/tests/test_activities.py
apps/recovery_worker/tests/test_client.py
apps/recovery_worker/tests/test_crypto.py
apps/recovery_worker/tests/test_replay.py
apps/recovery_worker/tests/test_schemas.py
apps/recovery_worker/tests/test_workflow.py

apps/planning_agent/src/flowpilot_planning_agent/client.py
apps/planning_agent/src/flowpilot_planning_agent/main.py
apps/planning_agent/src/flowpilot_planning_agent/worker_schemas.py
apps/planning_agent/src/flowpilot_planning_agent/receipts.py
apps/planning_agent/src/flowpilot_planning_agent/recovery.py
apps/planning_agent/src/flowpilot_planning_agent/recovery_schemas.py
apps/planning_agent/src/flowpilot_planning_agent/replan.py
apps/planning_agent/tests/test_client.py
apps/planning_agent/tests/test_receipts.py
apps/planning_agent/tests/test_recovery.py
apps/planning_agent/tests/test_recovery_api.py
apps/planning_agent/tests/test_replan.py

apps/browser_worker/src/flowpilot_browser_worker/main.py
apps/browser_worker/src/flowpilot_browser_worker/recovery.py
apps/browser_worker/src/flowpilot_browser_worker/runtime.py
apps/browser_worker/src/flowpilot_browser_worker/schemas.py
apps/browser_worker/tests/test_api.py
apps/browser_worker/tests/test_recovery.py

apps/sandbox_api/migrations/versions/20260728_0003_w8_operation_receipts.py
apps/sandbox_api/src/flowpilot_sandbox_api/idempotency.py
apps/sandbox_api/src/flowpilot_sandbox_api/main.py
apps/sandbox_api/src/flowpilot_sandbox_api/models.py
apps/sandbox_api/src/flowpilot_sandbox_api/schemas.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/service.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/jml/service.py
apps/sandbox_api/tests/test_idempotency.py
apps/sandbox_api/tests/test_models.py
apps/sandbox_api/tests/test_arena_service.py
apps/sandbox_api/tests/test_jml_service.py

tests/integration/Dockerfile
tests/integration/pyproject.toml
tests/integration/uv.lock
tests/integration/w8_recovery_compose_smoke.py
tests/integration/w8_restart_driver.py
~~~

## Temporal and opaque-input contract

The Workflow may hold only strict deterministic data: schema/status versions,
opaque run/task/workflow IDs, plan and revision hashes, deterministic topology,
step safe states, completed/verified/remaining IDs, session epoch, absolute
workflow deadline, total usage, retry/recovery/replan/fault counts,
idempotency/request/result hashes, Checkpoint lineage, and closed reason codes.

Workflow code may schedule Activities; use Temporal workflow time, IDs, and
timers; update counters; validate closed state transitions; and choose the next
closed recovery decision. It must not perform HTTP, database, filesystem,
environment, random, system-time, Planner/model, Browser/Playwright, Sandbox,
Arena, Grader, page-text, or dynamic-tool work. It must not use unordered
iteration to create commands. Continue-As-New is prohibited.

Human brief and strict supplied values are canonicalized, encrypted with
AES-256-GCM outside Workflow code, and passed as `w8-opaque-envelope/1.0`.
The envelope binds schema version, opaque run/task IDs, workflow ID, key ID,
nonce, ciphertext, and associated-data hash. Only Activity code reads the
runtime `RECOVERY_ENVELOPE_KEY` and decrypts. The key is never committed,
logged, returned, put in Temporal payloads, or treated as a production secret.
Authentication failure, unknown key/version, malformed base64, or identity
mismatch fails closed before Planning is called.

Tests and Compose acceptance export raw Workflow history and reject any
occurrence of the synthetic brief, objective, supplied values, `.invalid`,
`SYN-`, page/form data, key material, or configured endpoint. The history scan
is a completion gate, not a best-effort check.

## Workflow state, Checkpoint, and retention

Workflow states are exactly `received`, `planning`, `executing`,
`checkpointed`, `recovering`, `replanning`, `verifying`,
`finished_ungraded`, `escalated`, `failed`, and `cancelled`. Unknown state,
version, field, transition, hash, counter, or reason fails closed.

Checkpoint schema `w8-checkpoint/1.0` stores only the allowed Workflow fields
plus a SHA-256 hash over canonical sorted-key UTF-8 JSON excluding the hash
field. Maximum canonical serialized size is 65,536 bytes and maximum count is
18. Every new Checkpoint names its parent hash; the first uses an explicit
genesis hash. Only a step with a positive runtime Verifier result can enter the
verified/completed sets and advance the recoverable Checkpoint.

Checkpoint never stores Browser/Context/Page handles; DOM, screenshot, OCR,
page/form text; observation/element/screenshot/grounding refs; raw brief,
objective, postcondition, Planner/model output; Task Spec, expected state,
grader predicate/checksum; Cookie/Local Storage, credential, token, endpoint,
or machine path. Current Browser/session references remain process-local and
are erased on every terminal/recovery/shutdown path.

Temporal namespace retention is fixed to one day for local synthetic W8.
Sandbox Reset/Seed deletes only receipts owned by the selected synthetic task.
No long-term checkpoint export or application database copy exists. Compose
cleanup removes the independent Temporal database volume and Sandbox volume.

## Session epoch and reference lifecycle

Normal W8 execution creates epoch 1 with one fresh Browser, Context, and Page.
Recovery may create epoch 2 and then epoch 3; more than two recoveries fails
closed. Before opening a new epoch, Planning Agent closes the current session
best-effort and clears every task-local current reference. Browser Worker W8
session creation and action envelopes bind the exact epoch. W8 actions also
retain W6 session, generation, modality, observation, and opaque-reference
validation.

A recovered epoch never reuses or composes prior DOM/image data. It obtains a
fresh observation and continues only from the latest verified Checkpoint.
Actions carrying an old epoch, session, generation, observation, element,
screenshot, or grounding reference are rejected before execution. Success,
failure, timeout, cancellation, startup failure, Worker shutdown, and replay
failure unconditionally close the current epoch and clear task-local state.

## Transactional idempotency and receipt contract

The only new business-database object is `w8_operation_receipts`. Each row has:

- `task_id` (synthetic task owner, maximum 40 characters);
- `idempotency_key` (`op_` plus 64 lowercase hex characters);
- `request_hash` (64 lowercase hex);
- `plan_revision` (1 or 2);
- `step_id` (maximum 40 characters);
- `operation` (the existing closed W7 operation enum);
- `outcome_code` (`committed` only in stored rows);
- `result_hash` (hash of a safe canonical outcome projection); and
- database-created `created_at`.

Primary uniqueness is `(task_id, idempotency_key)`. Additional constraints
bind non-empty closed fields and revision range. No receipt stores raw payload,
form value, page/DOM text, credential, browser ref, or result body. A run may
create or replay at most 24 receipts.

The key is deterministically derived from opaque run ID, plan revision, step
ID, and operation index. The request hash covers schema version, task owner,
revision, step ID, closed operation, and canonical strict mutation payload.
For an existing task/key: equal hash returns the stored safe outcome and does
not execute; unequal hash returns HTTP 409 `idempotency_mismatch` and does not
execute. For a new key, receipt insert and the fixed business mutation commit
in the same SQLAlchemy transaction. Integrity races re-read and apply the same
rule. Grader ignores receipts and scores business facts only.

W8 Browser Worker accepts idempotency metadata only in the W8 typed action
envelope, only for a closed mutation click, and only through fixed
`X-FlowPilot-W8-*` headers attached temporarily to the exact synthetic UI
request. It rejects arbitrary header names/values, URLs, interception rules,
and non-mutation use. Sandbox recomputes the request hash from its validated
typed body before applying the transaction.

## Retry, recovery, fault, and replan rules

The recovery order is fixed:

1. request a fresh current observation;
2. retry one explicitly transient, not-safely-completed Activity once;
3. create a fresh Browser session epoch;
4. resume from the latest verified Checkpoint;
5. perform one eligible local replan of the failed/not-started subgraph; then
6. escalate or terminate safely.

Retry policies are exactly `no_retry` and `transient_once`. Temporal Activity
retry is fixed to maximum attempts 2, bounded initial/maximum interval, and no
unbounded exponential schedule. Validation, permission, schema, Checkpoint
version/hash, idempotency mismatch, unknown operation, budget exhaustion, and
permanent faults are non-retryable. Attempt numbers survive Worker restart.

Run maxima are: 2 Activity attempts; 2 session recoveries; 1 replan; 2 DAG
revisions; 18 Checkpoints; 24 receipts; 2 injected faults; and the existing
300-second duration. Retry, replay, recovery, fault, receipt, Checkpoint, and
replan counters join the same non-resetting W6/W7 ledger; no existing action,
model, token, cost, step, switch, repetition, no-progress, DOM, or image cap is
increased.

Fault scenarios are a trusted acceptance-only closed enum:
`none`, `activity_pre_dispatch_once`, `post_commit_pre_checkpoint_once`,
`browser_session_lost_once`, `browser_worker_restart_once`,
`recovery_worker_restart_once`, `transient_timeout_once`,
`permanent_failure`, `checkpoint_version_mismatch`,
`checkpoint_hash_mismatch`, `idempotency_mismatch`,
`replan_eligible_once`, and `replan_disallowed`. Each has a fixed injection
point, maximum count, retry/recovery classification, and expected terminal
status. No normal API exposes a generic fault endpoint; page/model data cannot
select a fault.

Revision 1 remains immutable. One revision 2 may replace only the failed step
and its not-started descendants, preserving all verified/completed nodes,
receipts, Checkpoints, authority, supplied values, process/category, and total
budget. It records parent plan hash, replacement boundary, replaced IDs, and a
canonical revision hash. The union of old/new nodes remains charged and must
fit W7 node/edge/depth/width/dependency/byte limits. No completed side effect is
rolled back or compensated.

## Verifier, Grader, data, and evidence

Runtime Verifier remains strictly weaker than Grader. It may read only current
observation/action result, safe receipt replay state, closed step conditions,
and ledger. It receives no Task Spec, expected state, predicate/checksum,
Arena/DB/Reporting result, page-success prose, or Planner self-report.
Negative/inconclusive results cannot advance a Checkpoint.

W3 catalog/checksum/6-2-2 split and W7 30-template/90-instance catalog,
12/8/10 distribution, 18/6/6 split, checksums, IDs, Grader, and Reporting
freeze remain unchanged. Development may run the fault matrix. Validation may
run at most one preregistered final recovery check after parameters freeze.
Reporting is limited to load/schema/checksum validation and receives no
Reset/Seed, Agent, fault, recovery, grade, or result inspection.

Evidence records only versions, opaque IDs/hashes, safe statuses/reasons,
Checkpoint/revision topology and counts, Activity attempts, retry/recovery/
epoch counts, receipt create/replay/mismatch counts, duplicate-side-effect
count, fault/replan counters, inherited W6/W7 counters, terminal state, and
independent grade. It records no raw brief, objective, supplied value, DOM,
image, OCR, page/form content, credential, key, endpoint, token, Cookie, Local
Storage, or machine path.

## Git and completion rules

Work only on `week/08-recovery`. The user has authorized the quota-conscious
W8 remote sequence: one normal feature push, one pull-request CI, normal merge,
one post-merge main CI, annotated tag `w08-recovery`, and roadmap-required
GitHub Release `v0.2.0`. Do not rerun the superseded W7 push run, rerun a
successful workflow, create duplicate CI, force-push, call a real model, or
begin W9. Stage only exact allowlist paths after all locally available gates
pass and evidence matches.

W8 local completion requires deterministic/replay tests; W4-W7 regression;
the W8 no-fault, pre-dispatch, post-commit, epoch-loss, Browser Worker restart,
Recovery Worker restart, transient/permanent, Checkpoint mismatch,
idempotency mismatch, partial-replan, budget, and cleanup proofs; migration
round-trip; history plaintext scan; zero duplicate side effects; Development
Joiner/Mover/Leaver recovery; independent grades; secret/diff/path checks; and
complete Compose cleanup. Unavailable tooling is recorded, never treated as a
pass. A local commit is allowed only after all locally available gates pass.
