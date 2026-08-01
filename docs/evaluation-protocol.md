# Evaluation protocol

## Purpose and preserved boundary

W12 evaluates authenticated asynchronous admission, actor-scoped idempotency,
persistent actor/organization rate buckets, bounded queue/backpressure,
organization-fair durable dispatch, a private four-slot fenced Workflow Worker,
deterministic Temporal identity, W8 receipt convergence, and one checksum-
frozen 50-user synthetic load profile. It preserves W10 authentication/tenant/
locking and W11 risk/approval/grant/audit policy. It does not evaluate a real
enterprise IdP/approver/data source, a production SLO, legal compliance,
malicious-page resistance, multi-region failover, autoscaling, or cloud
deployment. W3/W7 database-fact Graders remain the only task-success authority.

W3 ten-task catalog/checksum/6-2-2 split; W7 30-template/90-instance catalog,
12/8/10 process counts, 18/6/6 split, manifests/checksums and Reporting freeze;
W4 DOM; W5 Vision; W6 Hybrid; W7 Planning; W8 recovery/receipts/Checkpoints/
replay; and W9 five-layer context/retrieval/summary/memory/ablations remain
unchanged.

## Frozen Development configuration

| Field | Value |
|---|---|
| IdP | local Keycloak `26.3.2` |
| issuer | `http://127.0.0.1:8080/realms/flowpilot` |
| audience | `flowpilot-control-api` |
| browser client | `flowpilot-control-web` |
| algorithm | `RS256` |
| organizations | 2 synthetic |
| users / identities / memberships | 16 / 16 / 16 |
| approval authorities | 8: 4 per organization |
| approval roles | `manager`, `security` |
| action counts L0/L1/L2/L3/L4 | 2 / 2 / 7 / 5 / 5 |
| request/grant TTL | 10 minutes / 2 minutes |
| audit | one canonical SHA-256 chain per organization |
| run/outbox capacity | 64 global / 32 per organization; 300-second TTL |
| Workflow Worker | one private service / four slots |
| lease / heartbeat / drain | 30 / 10 / 25 seconds; maximum 3 attempts |
| submit rate | actor 5/s burst 10; organization 50/s burst 100 |
| read rate | actor 10/s burst 20; organization 200/s burst 400 |
| mutate rate | actor 2/s burst 4; organization 25/s burst 50 |
| load | Locust 2.46.1; 50 users; 25/25 organizations; 1,000 protected requests |
| roles per organization | organization_admin / operator / auditor |
| initial mutable version | 1 |
| HTTP concurrency | strong ETag + required If-Match |

Realm/client/redirect/role/users are loaded from one checksum-frozen import.
Control Plane seed IDs and subjects are fixed opaque synthetic values. Unit
tests create ephemeral signing keys at runtime; no private key or real token is
committed.

## Authentication protocol

Unit/API tests cover missing and malformed Bearer input; `alg=none`; algorithm
confusion; wrong signature; unknown `kid`; malformed/duplicate/non-RSA/wrong-
use JWKS; wrong issuer/audience/client/header type/token type; missing subject;
expired token; future `nbf`; invalid/future `iat`; bounded refresh; redirect
rejection; and valid local tokens. Invalid authentication returns one closed
401 before a tenant lookup.

Control Web tests cover cryptographic state/nonce/verifier generation,
S256 PKCE, exact redirect/origin/post-logout allowlists, callback missing/
mismatched state/nonce/issuer/audience/expiry/code/transaction rejection,
transaction removal, module-memory token storage, current identity, forbidden,
and logout. Tests assert no token in URL, Local Storage, rendered output, log,
database, Temporal, or evidence.

## Authorization and tenant protocol

The complete frozen role/permission allow/deny matrix is exercised. Unknown
roles/permissions, no/inactive membership, inactive identity/user/organization,
role claim mismatch, auditor writes, operator membership administration, and
request/page/model role or organization injection are rejected.

With two synthetic organizations, tests cover same-organization read/list/
count/create/update/disable, membership and memory operations, then reject
cross-organization get/list/count/create owner injection/update/disable,
membership mutation, memory read/write/tombstone/reset, and context projection.
Before and after each rejection, both organizations' state is unchanged. Cross-
organization and nonexistent resources have identical closed response bodies
and do not disclose IDs, counts, versions, or ETags. No global/default/fallback
organization path is admitted.

## Optimistic-lock protocol

Tests require version 1 on create, success increment exactly once, missing
If-Match 428, malformed/weak/wildcard/cross-resource/stale precondition 412,
stale update/disable/memory mutation with no effect, repeat of one old version
with no duplicate side effect, transaction rollback, and tenant mismatch with
no true version disclosure. SQLite repository tests and PostgreSQL integration
both require exactly one winner from two concurrent writes using one ETag.

W11 extends the same requirement to approval-authority disable/tombstone and
approval request decision/cancel/invalidate. Decisions and audit events are
immutable append-only rows. Concurrent decisions from one request version and
concurrent claims from one grant each require exactly one winner.

## Risk and approval protocol

Tests cover every frozen action, database-fact promotion of `create_account`,
unknown action to L4, invalid/extra parameters, caller/page/model risk or
approver injection, canonical key-order stability, value-change hashes, and
deterministic replay. L0/L1 execute only through the automatic audited path;
L4 and unknown actions are permanently denied.

The approval matrix covers active manager L2; L3 manager plus distinct active
security; self/executor denial; admin without authority; inactive user,
organization, membership, and authority; wrong organization; duplicate and
stale decisions; reject/cancel/expire/invalidate terminal behavior; required
If-Match; and no physical deletion. Failed cases have no grant, receipt, or
business effect.

## Grant, recovery, and audit protocol

The grant matrix checks no issuance before the required set, hash-only
persistence, absence of raw material in public/browser/durable surfaces,
wrong/malformed/expired/revoked/cross-org/wrong-executor/binding rejection,
parameter invalidation, exactly-one concurrent claim, and replay rejection.
Recovery tests cover crashes while waiting, before/after claim, before effect,
after receipt, authority/request/parameter changes, active authorization hash,
same receipt, W8 caps, `finished_ungraded`, and independent grading.

Audit tests cover genesis, sequence, previous/event hashes, concurrent append,
no duplicate/fork, organization-local list/count/head/verify, read-only auditor,
append-only triggers, lifecycle coverage, sensitive-field scans, and detection
of mutation, deletion, insertion, reorder, broken previous hash, and head
mismatch. Verification is deterministic but is not a tamper-proof or legal-
compliance claim.

## Production admission, handoff, and HTTP protocol

API tests cover strict create/claim models; L0/L1 queued admission; L2 manager
and L3 manager-plus-distinct-security waiting admission; L4/unknown denial;
old W11-claim blocking for W12-owned requests; same-key/same-body replay; same-
key/different-body 409; run read/list tenant isolation; strong ETag cancel;
429/503 bounded Retry-After; capacity rollback; and rate rejection audit
persistence. Invalid authentication is rejected before tenant or bucket access.

The production claim matrix proves credential-hash verification, exactly one
grant winner, execution/run/outbox/audit in one Control transaction, post-
commit raw-vault removal, replay prevention, and zero dispatch on incomplete,
expired, revoked, changed-parameter, changed-authorization, cross-tenant, or L4
paths. API code has no Planning/Browser client and never declares task success.

HTTP meanings remain closed: 202 is accepted/waiting/queued only; 401 invalid
authentication; 403 permission; uniform 404 cross-tenant/missing; 409 illegal
transition/idempotency mismatch; 412 invalid/stale ETag; 422 strict schema; 428
missing If-Match; 429 actor/organization rate; and 503 queue/scheduler
unavailable. Failed mutation does not increment a resource version.

## Worker, lease, fencing, and failure protocol

Repository tests cover deterministic organization round robin; exactly one
claim winner; 30-second lease and 10-second heartbeat; lease expiry/reclaim;
monotonic fence; stale heartbeat/start/result/release rejection; queue expiry;
effect-bound current authorization invalidation; deterministic workflow ID;
duplicate Temporal start convergence; `finished_ungraded`; cancellation/drain
release; and four active slots with a queued fifth. Conditional claim and
terminal updates include organization, IDs, status/version, owner, lease
version, and fence so cancel/claim and stale-terminal races cannot resurrect a
run.

Eight task/action/parameter hashes are independently checked against the
contract. The four-per-organization formal allocation uses disjoint Sandbox
fixtures. A known admitted action with the wrong effect binding becomes
`failed/workflow_rejected` before Temporal or Browser and has no receipt.

## Database and migration protocol

The independent Control Plane migration runs on an empty PostgreSQL database:
upgrade through W12 `20260801_0003`, `current`, `check`, downgrade to W11
`20260729_0002`, second upgrade, `current`, and `check`. Schema inspection
verifies the six W12 tables, all eight task/process/category constraints,
organization-aware foreign keys, unique constraints, indexes, immutable lease/
idempotency triggers, and rollback.
Released Sandbox migration bytes remain identical to W10; online Sandbox
Alembic remains at `20260728_0003 (head)` with no drift.
Control data is never included in Sandbox Reset/Seed/Grader or Temporal state.

## Compose Development protocol

After a clean-volume start, W10 identity acceptance uses the pinned local issuer
and verifies authentication allow/reject, authorization rejection, two-
organization rejection, optimistic success/stale, concurrent exactly-one-
winner, and safe context projection. It reports counts and closed booleans only,
with real identity-provider calls 0, real model/provider calls 0, cost 0,
Validation false, and Reporting false. W11 then runs last and verifies one
representative L0-L4 action, schema rejection, L2/L3 roles and decisions,
self/inactive/cross-tenant rejection, terminal rejection/invalidation,
one-winner claim/replay, audit lifecycle events, chain verification, and public
payload sensitive-data exclusion.

W12 acceptance then exercises an L1 admission that fails before effect, L2/L3
approval-to-outbox execution, eight disjoint task effects, maximum concurrency
four, queue wait, independent grade 100, cross-tenant/missing equality, and both
organization audit verification. Smoke/load containers receive no database,
Worker, raw grant, or Docker capability.

W4-W11 smokes run in release order before W12. W9 must retain all five frozen ablation
hashes, enterprise catalog checksum, context-backed Development Joiner/Mover/
Leaver grade 100, and `finished_ungraded`. W8 retains zero duplicate effects
and all fault/recovery/replay caps. W3/W7 freeze checks and independent grading
remain authoritative.

## Data, Validation, and Reporting discipline

The realm checksum, W11 action/approval/audit state, W12 effect hashes, queue/
rate/lease values, Locust dependency version, 50-user sequence, result schema,
and artifact hashes are frozen in `docs/data/week-12-production-data.md`.
Development may rerun while implementing.

Formal `w12-validation-50x4/1.0` ordinal 3 is the explicitly authorized
replacement clean-stack sequence; ordinals 1 and 2 remain preserved failures:

1. Stop Workflow Worker, acquire the exclusive ordinal-3 guard, approve/claim
   eight disjoint executable runs, fill the remaining 56 queue slots, and
   require 50 capacity probes to return 503.
2. Restart Worker, exhaust only production-read actor buckets, require one 429
   probe per virtual user with bounded Retry-After, allow refill, then run 50
   users (25/25 organizations), 10 users/s, 30 seconds, fixed 100 ms think, and
   exactly 20 operations/1,000 protected requests.
3. Through public Control API and Sandbox Grader only, reconcile all 164
   accepted setup/protected runs, eight receipts/grades, queue percentiles,
   maximum browser concurrency, fences, workflow hashes, tenant rejection, and
   both audit chains. The reported audit head hash is SHA-256 over canonical
   sorted `{organization_id,event_count,head_sequence,head_hash}` records.
4. Export guarded metrics/observations, run Compose down, observe project
   container/network/volume counts, then seal cleanup values into the strict
   result and compute its final hash. Result sealing cannot perform load again.

The guard is acquired before setup. Ordinals 1 and 2 are retained as failed
formal attempts; the user's authorization permits exactly this ordinal-3
replacement and no ordinal 4 run. The repeatable CI 50-user mode is explicitly
`validation_run: false` and omits formal probes/result sealing.

Reporting is limited to generation/load/schema/checksum validation. Before W15
it receives no Reset, Seed, Agent, OIDC login, identity, approval, grant,
audit-result inspection, organization, user, membership, RBAC, tenant, memory,
context, grade, or result execution or inspection.

## Interpretation and real-call boundary

Passing results establish deterministic local authentication, authorization,
two-organization isolation, closed risk/approval behavior, one-time claim,
bounded admission/rates, fenced scheduling, four-slot execution, tamper
detection, optimistic concurrency, migration, regression, and cleanup. They do
not prove production identity/approval security, real enterprise isolation,
external generalization, malicious-page resistance, legal compliance,
production availability, real load capacity, SLOs, or ROI.

Calls to a real identity provider/account/data source and real model/provider/
OCR/VLM/embedding services remain not run at 0 calls and 0 cost. W13 telemetry
and every later phase remain outside W12.
