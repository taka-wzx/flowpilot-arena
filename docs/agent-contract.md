# W12 agent contract - production control plane and bounded execution

## Authority, baseline, and stop condition

This contract translates the W12 roadmap row and the user-authorized W12 brief
into the sole implementation authority for `week/12-production`.

The immutable W11 product baseline is merge
`84336fdc1dd056110b2dfb32383ce938361bf316`, feature commit
`21ac2d54e3e9577ede8a5d91cd8257ef6daf3397`, and annotated tag
`w11-approval`. W11 PR #34, PR run `30684262735` attempt 1, and main run
`30684566589` attempt 1 succeeded. Maintenance PR #33 was merged as
`61afa05fb9ba723db0dff8276a9da5023c26cf8b`; its development baseline was
`b90cd44ec440eef2d69f12d03890bae57c845e37`. The current Release remains
`v0.2.0 - Hybrid + Recovery` at `w08-recovery`; W11 created no Release.

W12 has one local outcome: preserve every W1-W11 frozen boundary while adding
an authenticated asynchronous production admission path, durable
organization-fair dispatch, one trusted Workflow Worker, rate limiting,
backpressure, a global four-browser execution cap, a frozen 50-user synthetic
load profile, and a complete local Compose deployment. The later authorized
week tag is `w12-production`; the later authorized Release is
`v0.3.0 - Production Control Plane`. This authorization stops after one local
feature commit. It does not authorize push, PR, merge, tag, Release,
workflow_dispatch, CI rerun, real provider/IdP/model/egress, or W13 work.

The literal `%SystemDrive%/` path is outside every read, enumeration, scan,
diff, status, staging, and modification operation. No `code_review_agent`
repository may be accessed.

## Preserved W1-W11 boundary

The following remain byte-, API-, behavior-, or authority-frozen as
applicable: all W1-W11 public routes and deterministic fake results; W3 ten
tasks/checksum/6-2-2 split; W7 30 templates/90 instances, 12/8/10 processes,
18/6/6 split and Reporting manifests/checksums; W4 DOM, W5 Vision, W6 Hybrid,
W7 typed Planning DAG/tool/budget/verifier; W8 Temporal Workflow,
Checkpoints, receipts, retries, recovery, epochs, replan/action/ledger caps;
W9 five-layer context, retrieval, summary, organization memory, hashes, and
five ablations; W10 fixed OIDC/JWKS/audience/client/RS256 policy,
database-derived ActorContext, closed business RBAC, tenant isolation, and
strong ETags; W11 closed strict L0-L4 policy, manager/security authorities,
L2/L3 separation, immutable decisions, hash-only one-time grant, and per-
organization audit chain; released Sandbox migration bytes; W10 realm policy;
the one non-resetting ledger; `finished_ungraded`; and independent Sandbox
database-fact grading.

Planning still reaches only Browser Worker and obtains no Control database,
OIDC token, approval repository, raw grant, queue, or scheduler capability.
Recovery still reaches only Temporal and Planning. Browser, Planning,
Recovery, Sandbox, and Grader receive no Control database credential. W9
`scope_id` remains synthetic regression input, never identity or authority.
W12 narrows the released Planning recovery coordinator's process-wide activity
lock to one lock per durable run. Commands for the same run remain strictly
serialized with unchanged W8 caps, checkpoint, receipt, and cleanup semantics;
different organization-qualified W12 runs may progress concurrently without
sharing recovery state, Browser sessions, or task references.
For the terminal W8 Recovery `finalize` node only, the coordinator reuses the
current DOM observation returned by its successful final navigation rather than
issuing the redundant non-mutating `read`. The frozen DAG, verifier
postconditions, Browser limits, effect sequence, receipts, and non-resetting
total ledger remain unchanged; this keeps the bounded terminal path within the
existing DOM observation and byte limits when the consolidated regression has
already seeded its synthetic baseline.
Likewise, when a fixed Recovery session's initial current observation is already
on the first node's expected page, its identical `navigate` is a no-op; later
or cross-page navigation remains mandatory. This reuses existing safe evidence
without changing the DAG, effect, page allowlist, or any limit.
The released Recovery Worker keeps its 30-second Temporal activity deadline
and every W8 retry/replan/action cap. Its fixed internal Planning HTTP timeout
is 28 seconds so a four-browser synthetic step may finish within that unchanged
deadline. Planning uses a fixed 25-second timeout only for its closed Recovery-to-
Browser calls; all released non-Recovery Planning-to-Browser calls retain their
10-second timeout. In the W12 Compose topology, the Browser Worker's fixed
server-side action deadline is 20 seconds, below the closed 25-second Recovery
client timeout and unchanged 30-second W8 activity deadline. Recovery retains four
concurrent workflow tasks but accepts at
most two concurrent Planning activities, so excess activity work remains queued in
Temporal before its unchanged 30-second start-to-close window begins. Callers cannot
select or extend any of these values.
A nonterminal W8 Recovery Browser result classified only as `browser_timeout` or
`browser_error` enters the existing closed `session_lost` refresh/recover path
with the same idempotency binding and caps. Other Browser failure categories
remain fail-closed and do not gain a retry, effect, or budget.

## Frozen topology and trust boundaries

The minimum W12 topology is:

~~~text
Control Web
  -> Control API
  -> Control PostgreSQL (identity, approval, audit, run, outbox, limiter)
  -> Workflow Worker (private, trusted, four concurrent dispatch slots)
  -> Temporal
  -> released W8 Recovery Worker
  -> Planning Agent
  -> Browser Worker
  -> Synthetic Sandbox
  -> independent Grader
~~~

Control API never calls Planning Agent or Browser Worker for a production run.
Workflow Worker has no public port and accepts no HTTP/browser/user request,
Bearer token, JWT claim, Cookie, Authorization Code, raw approval credential,
caller organization/actor/role/risk/approval/priority/queue/worker/budget, or
caller-declared success. It joins only `control-database` and
`temporal-control`. It receives the Control DSN, Temporal address, runtime W8
envelope key, and its opaque instance seed. It does not join identity,
control-backend, planning-worker, browser-sandbox, sandbox-backend, or any
model-egress network.

Control, Sandbox, Temporal, and Keycloak databases remain separate. No
cross-database foreign key exists. Workflow Worker may execute only the closed
W12 SQL statements and Temporal start/result calls implemented in its reviewed
repository/client modules. It cannot perform a global business-row read and
then filter in Python, administer identity/approval/audit state, or execute an
arbitrary URL, SQL string, Shell, JavaScript, selector, coordinate, or code.

## Closed production schemas and state machines

All W12 request, work-item, lease, result, and error models are strict, frozen,
extra-forbid, schema-versioned, bounded, and deterministic. IDs are opaque;
times are UTC. Canonical bytes are sorted-key compact UTF-8 JSON and hashes are
lowercase SHA-256.

The production create body is `w12-production-run-create/1.0` and contains
only one closed `task_id`, matching `process`, matching `category`, one closed
W11 `action_type`, and that action's strict W11 `parameters`. The effect catalog
is exactly eight released Development references:
`w7-jml-joiner-001-v1`, `w7-jml-joiner-001-v2`,
`w7-jml-joiner-002-v1`, `w7-jml-joiner-002-v2`,
`w7-jml-mover-001-v1`, `w7-jml-mover-001-v2`,
`w7-jml-leaver-001-v1`, and `w7-jml-leaver-001-v2`. Process is
`joiner|mover|leaver`; category is the
matching `standard_joiner|standard_mover|standard_leaver`. Caller fields for
organization, actor, executor, role, risk, approver, authority, priority,
queue, worker, workflow, grant, budget, fault, receipt, success, or expected
grade are forbidden.

Admission and effect authority are deliberately separate. L0/L1 and other
known W11 actions may exercise the frozen asynchronous admission path, but an
admitted action never grants the larger JML task effect merely because it names
the same task. Workflow Worker may start the released W8 effect only for these
eight exact server-known action bindings:

| Task | Required action | Frozen parameter hash |
|---|---|---|
| `w7-jml-joiner-001-v1` | `create_ticket` | `9f9a16bad25c578969e92f60e982510c9be6a4fe74d9236d06e8f9d96f9ea43b` |
| `w7-jml-joiner-001-v2` | `create_ticket` | `8f7967a3f5fa16a535c758ef421a6bed1b24e3f5d307cd80d28c2d7133b1f64c` |
| `w7-jml-joiner-002-v1` | `create_ticket` | `24a48d8f36f74aecec1dfc18a709e8682a1bc5b4985206ea419c27bd0fb1bd32` |
| `w7-jml-joiner-002-v2` | `create_ticket` | `5445094ff191a1beb668e68fb5501c91287e32bc447128cbbc3ae844d9849282` |
| `w7-jml-mover-001-v1` | `transfer_employee` | `417392e96f16078f9d9ac6bbb00cf0169945a149f322c787b99aa90e5377712f` |
| `w7-jml-mover-001-v2` | `transfer_employee` | `330c7a46e46648958a40f6e379acf266959eb93ec70b33a44d912145e9103d02` |
| `w7-jml-leaver-001-v1` | `disable_employee` | `ec514adaaaf6c5d9e3b9ac1143fa3526b93dfca511ff571dd947bdfa605fa756` |
| `w7-jml-leaver-001-v2` | `disable_employee` | `bb444aecec640db18cd003b4ff585b5d14a76c0f84470842f7799011a46eb5fc` |

Joiner and Mover bindings are L2 and require the current manager path; Leaver
bindings are L3 and require current manager plus distinct security. Any other queued binding is
closed as `failed/workflow_rejected` before Temporal or Browser dispatch, with
no receipt or business effect. This fail-closed rule prevents a read or plan
authorization from becoming authority for a multi-step JML mutation.

The eight formal pre-staged effects use disjoint fixtures across organizations:
Alpha uses Joiner 001 v1/v2, Mover 001 v1, and Leaver 001 v1; Beta uses
Joiner 002 v1/v2, Mover 001 v2, and Leaver 001 v2. No executable task ID is
shared across organizations during the four-browser observation.

Run status is the closed enum:

~~~text
waiting_approval -> queued -> leased -> running -> recovering -> verifying
                                                          -> finished_ungraded
waiting_approval|queued|leased -> cancelled
waiting_approval|queued -> expired
leased|running|recovering|verifying -> failed
~~~

`failed`, `cancelled`, `expired`, and `finished_ungraded` are terminal and
never reactivate. The name `completed` is forbidden as a run status or success
claim. A successful Agent workflow first records `verifying`, then
`finished_ungraded`; only the independent Grader can report task success.

A run binds schema version, run ID, organization, requester and executor,
closed task/process/category, W11 request/grant/execution references when
applicable, action, parameter hash, authorization hash, approval-set hash,
trusted synthetic payload reference and its hash, status, version,
idempotency/body hashes, deterministic workflow ID/hash, current lease owner
hash/fence/expiry, accepted/queued/started/finished UTC timestamps, closed
terminal reason, receipt/checkpoint reference, and latest audit sequence.
Creation version is 1. Externally mutable run operations require a strong W12
ETag and exact If-Match; success increments once. Missing is 428. Weak,
wildcard, multiple, malformed, cross-resource, cross-organization, and stale
input share one 412 with no current version.

Outbox status is `ready|leased|dispatched|closed|cancelled|expired|failed`.
Lease status is `active|released|expired|completed|failed`. Scheduler partition
status is `ready|empty|disabled`. Rate route class is
`production_submit|production_read|production_mutate`. Closed terminal reasons
are `agent_finished|agent_failed|authorization_invalid|queue_expired|
lease_exhausted|cancelled_by_actor|workflow_rejected|receipt_invalid|
worker_drained|dependency_unavailable`.

## Admission, idempotency, approval handoff, and transaction order

`POST /api/v1/organizations/{organization_id}/production-runs` requires one
Authorization Bearer header and one `Idempotency-Key`. The key is ASCII
`[A-Za-z0-9._:-]`, 16-80 bytes. Only its SHA-256 is stored. Processing order is:

1. fixed-policy OIDC verification before any tenant or limiter query;
2. current active organization/user/identity/membership resolution and closed
   production-submit permission;
3. strict body/key parsing and canonical body hash;
4. organization+actor+key idempotency lookup;
5. W11 action-schema validation and current organization-qualified L0-L4 risk;
6. W11 automatic path or request/approval/grant state;
7. atomic actor and organization token buckets;
8. global and per-organization active pending-capacity checks;
9. one Control transaction for run, idempotency row, scheduler partition,
   executable outbox when authorized, and W11-compatible audit append; and
10. 202 with opaque run read model and strong ETag.

Same organization, actor, key, and canonical body returns the same run without
a second approval, grant, workflow, audit lifecycle, rate charge, or side
effect. Same tuple with a different body returns stable 409 and zero mutation.
The key grants no authority and is never shared across actor or organization.

L0/L1 create a `queued` run plus executable outbox; API never declares effect
success. L2/L3 create `waiting_approval` with no executable outbox. The released
W11 manager/security and self/executor rules remain exact. After the final
approval, the trusted executor claims the server-vault credential through the
production run claim route. Credential-hash verification, one-winner grant
claim, durable execution reference, run transition to `queued`, outbox insert,
partition update, and audit append share one Control transaction. Raw material
is removed from the bounded vault only after commit; a committed database claim
blocks replay even if process memory removal is delayed. Two claimants create
one execution, one run transition, and one outbox.

Before starting a Temporal effect, Workflow Worker rechecks, with organization
in every SQL predicate: active organization, executor user and membership,
exact run/request/grant/execution/action/parameter/approval-set/authorization
bindings, request/grant current status, all approving users/memberships/
authorities, expiry, cancellation, and fence. L0/L1 recheck active executor and
authorization hash. Disable, cancel, reject, expire, invalidate, parameter or
authorization-hash change fails closed before an effect.

Unknown action is W11 L4 and permanently denied. Known invalid parameters are
422. L4, unknown, unauthorized, cross-tenant, incomplete approval, or invalid
grant creates no executable outbox, consumes no browser slot, and has zero
business effect. Stable denial audit remains organization-local.

## Durable outbox, fairness, lease, fencing, and recovery

Control PostgreSQL owns `production_runs`, `dispatch_outbox`,
`worker_leases`, `scheduler_partitions`, `rate_limit_buckets`, and
`idempotency_records`. Separate tables are retained because immutable lease
history and idempotency uniqueness cannot be represented safely by a mutable
run row. No row is physically deleted.

Queue limits are frozen before implementation:

| Limit | Frozen value |
|---|---:|
| global active pending capacity | 64 |
| per-organization active pending capacity | 32 |
| queue TTL from acceptance | 300 seconds |
| active browser/Temporal dispatch slots | 4 globally |
| Workflow Worker Compose instances | 1 |
| claim batch per free slot | 1 |
| maximum lease attempts | 3 |

`active pending` means ready/leased/dispatched outbox not terminal; it excludes
waiting approval because no executable outbox exists. Capacity checks and
insert occur under locked scheduler rows in the admission transaction. Queue
or limiter database failure fails closed with 503 and no approval/grant/claim/
receipt/business effect.

Organization fairness is deterministic round robin over non-empty opaque
partition IDs ordered after a locked cursor. One item is claimed per selected
organization before another round. Callers cannot set priority. Global
scheduler metadata contains only opaque organization partition ID, ready count,
cursor, status, and version; it is never returned by an API.

Lease values are frozen:

| Field | Frozen value/meaning |
|---|---|
| lease TTL | 30 seconds |
| heartbeat interval | 10 seconds |
| graceful drain deadline | 25 seconds |
| worker owner | SHA-256 of runtime opaque instance ID |
| fence | monotonically increasing per outbox item, begins at 1 |
| claim | one PostgreSQL locked/conditional organization+outbox+status update |

Claim creates an append-only lease-history row and atomically changes outbox
and run to leased with the same fence and audit event. Heartbeat, start,
receipt, result, release, and terminal writes include organization, run,
outbox, active lease, owner hash, lease version, and fence. Stale or expired
fences change zero rows and append no success event. After expiry, exactly one
new claimant increments the fence and reuses the same run and workflow ID.

Temporal workflow ID is `w12-` plus the first 48 hex characters of SHA-256 over
canonical organization ID and run ID. Duplicate start is treated only as the
same deterministic workflow; it never creates a second workflow identity.
Workflow Worker derives the exact released W8 encrypted start envelope from a
closed trusted local task-reference projection. Temporal history receives the
opaque W8 envelope, IDs, hashes, closed faults (`none` only in production), and
released caps, never token, ActorContext, raw approval, raw task brief from an
external caller, page/model data, or Control DSN.

Delivery is described only as durable at-least-once, exactly-one active lease
winner, deterministic workflow identity, stale-write fencing, and W8 receipt/
idempotency at-most-one business side effect. Distributed exactly-once is not
claimed.

Workflow result is trusted only after Temporal returns the released strict W8
result and the active fence remains current. `finished_ungraded` transitions
through verifying and stores only receipt/checkpoint hashes and closed counts.
Other W8 terminal results map to failed/cancelled. Receipt replay uses the same
run/workflow/reference and does not duplicate a business mutation. A Worker
crash at any pre/post-start/pre/post-receipt/pre-terminal window is resolved by
lease expiry, deterministic Temporal identity, W8 replay, and the active fence.

Graceful drain stops new claims. Existing four or fewer claims may finish for
25 seconds; otherwise their leases are safely released or allowed to expire.
Browser/Recovery restart does not increase any W8 cap. Every production run
uses the released Browser Runtime's fresh context/session/page and cleanup;
no page, Cookie, storage, session, task ID, receipt, observation, or Checkpoint
is reused across another actor, organization, or run.

## Frozen token-bucket limiter and HTTP backpressure

The limiter is one persistent atomic token bucket per verified organization,
actor, and fixed route class plus one persistent organization bucket per route
class. A token equals 1,000,000 microtokens. Elapsed time is integer UTC
microseconds; refill is `floor(elapsed_us * rate_microtokens / 1_000_000)` and
is capped at burst. The transaction locks both rows, refills, requires one
whole token from each, and decrements both or neither. Clock rollback contributes
zero elapsed time. Rows are disabled/tombstoned, never deleted.

Frozen values:

| Route class | Per actor rate / burst | Per organization rate / burst |
|---|---|---|
| production_submit | 5 tokens/s / 10 | 50 tokens/s / 100 |
| production_read | 10 tokens/s / 20 | 200 tokens/s / 400 |
| production_mutate | 2 tokens/s / 4 | 25 tokens/s / 50 |

`Retry-After` is `ceil(max(actor_deficit/actor_rate,
organization_deficit/organization_rate))`, clamped to integer 1-30 seconds.
Rate excess is 429 `rate_limited`; global/per-organization queue capacity or
required scheduler/limiter unavailability is 503 `backpressure`. Both have the
bounded header and stable closed body only. They never return token count,
queue depth, another tenant capacity/wait, worker identity, version, or ETag,
and failed mutation never increments a resource version.

`X-Forwarded-For`, `Forwarded`, caller IP headers, body, query, page, model,
JWT business/approval input, and idempotency key cannot select or bypass a
bucket. This Compose topology has no trusted reverse proxy, so all forwarding
headers are ignored for authority and quota.

HTTP semantics are: 401 invalid/missing authentication before tenant/limiter;
403 valid actor without permission or W11 risk denial; uniform 404 for missing
and cross-organization; 409 illegal transition/idempotency mismatch/grant
conflict; 412 invalid/stale/cross-resource ETag; 422 strict schema rejection;
428 missing If-Match; 429 rate limit; 503 queue/dependency backpressure. 202
means only waiting approval or queued, never success.

## Audit events and atomicity

W11 canonical event bytes and all old events remain compatible. The W12 closed
event additions are:

~~~text
run_waiting_approval
run_queued
run_leased
run_started
run_recovered
run_verifying
run_finished_ungraded
run_failed
run_cancelled
run_expired
admission_rejected
backpressure_rejected
rate_limited
lease_heartbeat
lease_released
stale_fence_rejected
workflow_deduplicated
~~~

Successful admission, approval claim handoff, outbox dispatch, lease, start,
recovery, verifying, and terminal transition append the matching event in the
same Control transaction as their mutation. Rejections that have a verified
organization append only the frozen safe denial event and no business state.
Temporal acknowledgement, Worker DB response, or caller body is never success.

Audit payload permits only schema version, opaque IDs/hashes, closed actor,
role, risk, action, run/outbox/lease/status/reason, HTTP status, counts,
versions/fences, receipt/grade references, and bounded latency/duration bucket.
It contains no Bearer token/claim/code/cookie, credential/nonce, password/
private key, name/email/username, raw task brief/parameter, page/DOM/image/OCR/
model content, machine path, or DSN. Each organization retains one append-only
tamper-evident chain with atomic sequence/head and deterministic verification;
duplicate sequence, fork, broken previous hash, and head mismatch are failures.

## Frozen fault and race outcomes

Unless stated otherwise, the loser returns the stable 409/412/429/503 for its
class, changes no version, appends no success event, creates no second receipt
or workflow, and has zero business effect.

| Race/fault | Sole legal outcome |
|---|---|
| same key + same body, sequential/concurrent | one run/version 1 and one lifecycle; every replay returns it |
| same key + different body | first may win; mismatch is 409 and zero mutation |
| rate accept vs refill | one locked atomic bucket result; no negative tokens |
| backpressure vs retry | capacity winner creates one run/outbox; rejection is 503 |
| crash before admission commit | no run, outbox, idempotency, or audit |
| crash after admission commit | durable queued run/outbox remains claimable |
| two workers claim one item | one active lease at fence N; one run version increment |
| lease claim vs cancel | either cancel wins with no effect or fenced lease wins; never both success |
| heartbeat vs expiry | active timely heartbeat extends once; expired heartbeat is fenced |
| stale result vs new fence | stale result writes zero; new owner alone may terminate |
| duplicate Temporal start | same workflow ID and one workflow/result lineage |
| crash after claim before Temporal start | lease expiry/reclaim starts same workflow ID |
| crash after effect before W8 receipt response | W8 receipt replay, one business effect |
| crash after receipt before run terminal | reclaim reads same workflow/result and commits one terminal path |
| worker restart/drain | no new claim while draining; active claims finish/release/expire |
| Browser restart | fresh W8 epoch/context; old references rejected; caps unchanged |
| approve vs reject/cancel/expire/invalidate | exactly one W11 legal transition; no outbox unless final valid approval is claimed |
| authority disable vs final approval/claim/effect | disable winner makes later path fail closed; effect cannot start on stale authority |
| two grant claimants | one grant/execution/run/outbox winner |
| same ETag writes | one mutation/version +1; loser 412 |
| concurrent audit append | contiguous unique organization sequence and one head |
| simultaneous cross-organization load | independent data/buckets/queue caps/audit heads; no leakage |

The consolidated W4-W12 regression uses the dedicated local-only
`syn-alpha-revocation-auditor` identity only for the W10 membership-revocation
check. W10 permanently disables that probe membership without restoring or
deleting it. The frozen W12 load continues to use `syn-alpha-auditor`, never the
revocation probe, so the durable W10 mutation cannot revoke a later load reader.
The probe has no production data and no W11 approval authority.

## Frozen 50-user/four-browser workload

Locust `2.46.1` is the only load tool. It is selected because it supports
Python 3.13, uses the repository's uv/Python toolchain, runs headlessly in
Compose, and needs no second runtime or image. Its exact dependency graph is
locked in `tests/load/uv.lock`; no k6 or second load framework remains.

The sole formal profile is `w12-validation-50x4/1.0`:

| Field | Frozen value |
|---|---|
| random seed | 20260801 |
| virtual users | 50 for the entire measured phase |
| organization split | 25 / 25 |
| spawn rate | 10 users/second |
| post-spawn barrier | all 50 present before measurement |
| steady measured duration | 30 seconds |
| think time | fixed 100 milliseconds |
| protected request budget | exactly 1,000 |
| operations per user | exactly 20 |
| per-user sequence | 12 reads, 2 submissions, 2 idempotent replays, 2 run reads, 1 ETag mutation, 1 closed probe |
| task distribution | Joiner/Mover/Leaver 20/15/15 users |
| identity distribution | fixed modulo over synthetic admin/operator/auditor readers; only admin/operator submit/mutate |
| pre-staged executable runs | 8 total, 4 per organization, approved/claimed before measured timing |
| intentional rate probes | 50 HTTP requests, exactly one per user, outside protected p95 |
| intentional backpressure probes | 50 HTTP requests after a fixed per-org capacity precondition, outside protected p95 |
| fake providers | deterministic released fake only |

The endpoint/request-class mix for the 1,000 protected requests is frozen to
600 identity/run reads, 100 production submissions, 100 same-key/same-body
replays, 100 accepted-run reads, 50 strong-ETag mutations, and 50 closed
cross-tenant/not-found checks. The two groups of 50 intentional 429/503 probes
are setup assertions and are not part of the 1,000 protected latency sample.
Token acquisition, approval preparation, intentional Retry-After waits,
browser/LLM execution, and probe setup are outside protected Control API
latency. Every protected HTTP request from first byte sent to full response is
inside it, including expected 202/200/404/409/412 responses.

Formal setup is one guarded clean-stack sequence. Recorded ordinals 1 and 2
failed before final acceptance. Under the user's explicit new direction,
exactly one replacement sequence is authorized as ordinal 3, with guard content
`w12-validation-ordinal-3`. No ordinal 4 or later formal run is authorized.
With Workflow Worker stopped, the acceptance client exclusively creates
`validation.guard`, approves/claims
the eight disjoint executable runs, and adds 56 L1 fail-closed runs so the
global outbox is exactly 64 and each organization is exactly 32. It then sends
25 capacity probes per organization and requires 50 bounded 503 responses.
Workflow Worker is restarted. The load client concurrently exhausts the twelve
production-read actor buckets using only same-organization missing-run reads,
sends one probe for each of the 50 virtual users, requires 50 bounded 429
responses, waits 2.1 seconds for full actor-burst refill, and only then starts
the protected barrier/timing. The 56 capacity runs fail `workflow_rejected`
before Temporal; the eight approved runs alone may create receipts/effects.

Expected fixed counts are: 50 users present; 1,000 protected requests; 50 rate
probe responses all 429; 50 capacity probe responses all 503; 8 pre-staged
accepted executable runs; at least 5 of those simultaneously ready so slot
queuing is observed; unexpected response codes 0; unexpected 5xx 0. The
result may report outcome-dependent accepted/terminal counts, but every
accepted run must be reconciled to waiting, queued, leased, running,
recovering, verifying, or one terminal state; lost accepted runs must be 0.

Acceptance is protected API p95 below 500 ms, max production browser
concurrency exactly 4 and never above 4, accepted-run loss 0, duplicate
workflow identity 0 (deduplicated starts may be nonzero), duplicate business
effects 0, cross-tenant leak 0, approval bypass 0, stale-fence write success 0,
browser-context cross-flow 0, audit verification failures 0, unexpected 5xx 0,
real IdP/account/data/model/provider/OCR/VLM/embedding/egress calls 0, cost 0,
and cleanup 0/0/0. These are deterministic local/CI synthetic observations,
not a production SLO, enterprise security certification, legal compliance, or
ROI claim.

Load results use strict schema `w12-load-result/1.0`, deterministic key order,
integer microseconds/counts, and p50/p95/p99 nearest-rank percentiles. The
result contains profile/schema versions, schema checksum, seed, validation
ordinal, user/org/request counts, expected/unexpected HTTP counts, API and
queue percentiles, run terminals, max browser concurrency, admission/rate/
backpressure, worker claim/reclaim/stale-fence, workflow duplicate, receipt
create/replay/mismatch, loss/duplicate/bypass/leak/context/audit checks,
non-sensitive CPU/logical-memory summary, real-call/cost zeros, Validation and
Reporting flags, and a SHA-256 over the canonical result excluding its own
`result_hash`. The raw-byte SHA-256 of `tests/load/result.schema.json` is
`45530b83251698f155d8a51fde7a32efec7574f8970a2455fd1b930730ef8888`;
the raw-byte SHA-256 of `tests/load/frozen-profile.json` is
`b0f964ac3500e7d65fc914ae9c78b9f529e7619d3cc2bd6673f4b18689b28c36`.
The profile value was frozen before application implementation. The result
schema checksum was re-frozen only for this explicitly authorized ordinal-3
replacement, to make the three formal ordinals non-interchangeable without
changing product policy, workload, counts, or the frozen profile. Any further
change invalidates the replacement Validation.

Measurement writes only protected metrics and opaque accepted run/organization
references. A separate DB-less collector uses Control API plus independent
Sandbox Grader to reconcile all 164 accepted setup/protected runs and both
organization audit verifiers. Result `audit.event_count` and
`audit.head_sequence` are sums; `audit.head_hash` is SHA-256 over canonical
sorted-key compact JSON of the two ordered
`{organization_id,event_count,head_sequence,head_hash}` records. This artifact
digest does not create a global product audit chain. After exporting guarded
metrics/observations, Compose is removed and finalization seals observed project
container/network/volume counts into the result without another load or guard.

Development may repeat a bounded 5-user, 5-second, 100-request profile using the
same product policy and result schema. It is never called Validation.

## Compose and CI freeze

Compose adds `workflow-worker` with no ports and `production-acceptance-smoke`
and `production-load` profile services. The complete W1-W12 stack retains
read-only filesystems, non-root images, `cap_drop: ALL`, no-new-privileges,
bounded PIDs/tmpfs, fixed health/readiness, runtime envelope key, no repository
mount or Docker socket, no checked-in secret, separate databases, and no real
provider egress. Workflow Worker joins only Control database and Temporal
control networks. Load/smoke join only the public Control/identity/synthetic
networks needed for their closed client behavior and receive no database,
Worker, raw grant, or Docker capability.

CI retains main-push Compose configuration, secret scan, and Required CI gate
only. Human PR/manual dispatch runs existing quality jobs, one new Workflow
Worker quality job, one load static/schema job, and the single consolidated
W4-W12 Compose regression. Dependabot runs quality/config/secret, skips heavy
Compose/load, and retains a stable Required gate. No second heavy Compose job
is added. W4-W11 order and expected results remain; W12 smoke then the W12
load profile run last in the same built stack. Cleanup always runs.

## Data, migration, validation, and evidence discipline

Control migration `20260801_0003` is forward and reversible to W11. It adds
only the six W12 Control tables, organization-qualified foreign keys,
uniqueness, checks, indexes, and immutable lease/idempotency history controls.
It must pass empty upgrade, current, check, downgrade to `20260729_0002`,
second upgrade/current/check, constraint/index inspection, rollback,
concurrent claim, stale fence, and tenant mismatch. Sandbox head stays
`20260728_0003` with every released migration byte identical. Temporal and
Sandbox receive no W12 table.

Development unit, admission/rate/backpressure, lease/fence/four-slot, and W12
smoke may repeat. Ordinals 1 and 2 are preserved formal failures. The user has
explicitly authorized exactly one replacement formal W12 Validation, ordinal
3, only after code, migration, run/work schemas, approval handoff, queue/rate
values, lease/fence, load dependency/profile/counts, result schema/checksum,
Compose topology, fault matrix, seed, and expectations are frozen. If it
fails, evidence records the failure and no further formal Validation is
authorized. No post-result tuning is allowed.

Reporting before W15 permits only packaged generation/load/schema/checksum
validation. It receives no Reset, Seed, Agent, OIDC login, approval/grant,
audit inspection, grade, result aggregation, external benchmark, or repeated
execution. Evidence contains only closed safe observations and records
Validation ordinal, Reporting false, real-call/cost zero, tool versions,
unavailable tools, cleanup, exact path counts, and remote non-actions.

## Explicit non-goals

W12 adds no OTel/Prometheus/Tempo/Grafana/dashboard/trace replay/cost panel or
full failure taxonomy; malicious-page/prompt-injection suite; external
benchmark, three repetitions, or Reporting execution; Helm/cloud/public demo,
SBOM/video/v1.0 publication; real enterprise identity/account/organization/
user/approver/personal data; SAML/SCIM/LDAP/MFA/passkey; global admin/approver,
super-tenant, impersonation, delegation, break-glass, administrator override,
or L4 approval; dynamic policy/ABAC/DSL/rules engine; Kafka, Redis, RabbitMQ,
Celery, NATS, autoscaling, multi-region, Kubernetes, or service mesh; physical
delete; arbitrary Shell/SQL/JavaScript/code/URL/header/selector/XPath/
coordinate/API; real model/provider/OCR/VLM/embedding/key/egress; generic
future framework; W13+ placeholder or empty directory.

## Exact W12 file allowlist

Only the following exact paths may be created or modified. There are no
directory wildcards. A new path must first be added here; any scope expansion
listed in the non-goals requires new user direction.

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
docs/adr/0012-w12-production.md
docs/plans/week-12-production.md
docs/evidence/week-12-report.md
docs/data/week-12-production-data.md

apps/control_api/migrations/versions/20260801_0003_w12_production.py
apps/control_api/src/flowpilot_control_api/approval.py
apps/control_api/src/flowpilot_control_api/audit.py
apps/control_api/src/flowpilot_control_api/config.py
apps/control_api/src/flowpilot_control_api/etag.py
apps/control_api/src/flowpilot_control_api/main.py
apps/control_api/src/flowpilot_control_api/models.py
apps/control_api/src/flowpilot_control_api/production.py
apps/control_api/src/flowpilot_control_api/rbac.py
apps/control_api/src/flowpilot_control_api/repository.py
apps/control_api/src/flowpilot_control_api/schemas.py
apps/control_api/src/flowpilot_control_api/seed.py
apps/control_api/tests/conftest.py
apps/control_api/tests/test_api.py
apps/control_api/tests/test_approval.py
apps/control_api/tests/test_audit.py
apps/control_api/tests/test_migrations.py
apps/control_api/tests/test_production.py
apps/control_api/tests/test_rbac.py
apps/control_api/tests/test_repository.py

apps/workflow_worker/.dockerignore
apps/workflow_worker/Dockerfile
apps/workflow_worker/pyproject.toml
apps/workflow_worker/uv.lock
apps/workflow_worker/src/flowpilot_workflow_worker/__init__.py
apps/workflow_worker/src/flowpilot_workflow_worker/config.py
apps/workflow_worker/src/flowpilot_workflow_worker/crypto.py
apps/workflow_worker/src/flowpilot_workflow_worker/main.py
apps/workflow_worker/src/flowpilot_workflow_worker/repository.py
apps/workflow_worker/src/flowpilot_workflow_worker/schemas.py
apps/workflow_worker/src/flowpilot_workflow_worker/temporal_client.py
apps/workflow_worker/tests/conftest.py
apps/workflow_worker/tests/test_config.py
apps/workflow_worker/tests/test_repository.py
apps/workflow_worker/tests/test_schemas.py
apps/workflow_worker/tests/test_temporal_client.py

apps/planning_agent/src/flowpilot_planning_agent/recovery.py
apps/planning_agent/src/flowpilot_planning_agent/client.py
apps/planning_agent/tests/test_recovery.py
apps/planning_agent/tests/test_client.py

apps/recovery_worker/src/flowpilot_recovery_worker/client.py
apps/recovery_worker/src/flowpilot_recovery_worker/main.py
apps/recovery_worker/src/flowpilot_recovery_worker/workflow.py
apps/recovery_worker/tests/test_main.py
apps/recovery_worker/tests/test_replay.py

deploy/compose/compose.yaml
deploy/compose/keycloak/Dockerfile
deploy/compose/keycloak/flowpilot-realm.json

tests/integration/Dockerfile
tests/integration/w10_identity_compose_smoke.py
tests/integration/w12_production_compose_smoke.py

tests/load/Dockerfile
tests/load/.dockerignore
tests/load/pyproject.toml
tests/load/uv.lock
tests/load/frozen-profile.json
tests/load/locustfile.py
tests/load/profile.py
tests/load/result.schema.json
tests/load/run_profile.py
tests/load/test_profile.py
~~~

The allowlist contains 74 exact paths. Existing Control, Browser, Planning,
Recovery, Sandbox, frontend, realm, integration lockfile/base image, and released
migration files not listed above remain unchanged.

## Required acceptance and local completion

The implementation must cover API/Worker separation; no public Worker route;
strict work item; token/claim/grant/nonce exclusion; L0/L1 enqueue; L2 manager
and L3 distinct manager/security enqueue after claim; self/executor denial;
L4/unknown no outbox; parameter/authority invalidation; run ETag/cancel;
idempotency; token refill/burst and actor/org isolation; 429/503 and bounded
Retry-After; queue capacity/fairness; one lease winner; heartbeat/expiry/fence;
deterministic Temporal identity/duplicate dispatch; Worker crash windows;
Browser restart/drain/four-slot/context isolation; cross-tenant load;
same-ETag and grant-claim concurrency; audit concurrency; no duplicate receipt/
effect; `finished_ungraded`; independent Grader; Control migration round trip;
Sandbox byte freeze; W3/W7/W9/W10/W11 freezes; W4-W12 Compose; 50-user/four-
browser Validation once; sensitive scan; Reporting-not-run; real-call/cost
zero; cleanup 0/0/0; and exact allowlist.

After all locally available gates pass and evidence matches observations,
explicitly stage only paths above; never use broad staging. Create one local
commit `feat: add W12 production control plane` and stop. Do not push, create a
PR, merge, tag, create a Release, rerun/dispatch CI, call a real provider, or
begin W13.
