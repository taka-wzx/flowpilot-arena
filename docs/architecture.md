# Architecture

## W12 current-state architecture

W12 keeps identity, approval, admission, dispatch, limiting, and audit in the
Control Plane. A pinned local Keycloak is the synthetic OIDC issuer, and Control
PostgreSQL owns organization, user, external identity, membership, durable
organization memory, approval, grant/execution claim, audit chain, production
run, outbox, lease history, scheduler partition, token bucket, and idempotency
state.
Sandbox/Arena, Temporal, and Control persistence remain separate. Planning
Agent still reaches only Browser Worker and receives neither tokens nor any
database capability.

~~~mermaid
flowchart LR
    Human["Local browser"] -->|"Authorization Code + S256 PKCE"| KC["Keycloak 26.3.2\nflowpilot realm"]
    Human --> CW["Control Web"]
    CW -->|"Authorization: Bearer"| CA["Control API"]
    KC -->|"fixed JWKS\ninternal identity network"| CA
    CA --> Risk["Closed risk policy\nstrict parameters + DB facts"]
    Risk --> Approval["L2/L3 approval gate"]
    Approval --> CA
    CA --> CPDB["Control PostgreSQL\nidentity/approval/audit/run/outbox"]
    CPDB --> WW["Private Workflow Worker\nfour slots + fenced lease"]
    WW --> Temporal["Temporal + separate PostgreSQL"]
    CA -->|"closed authorized projection"| Context["W9 Context boundary"]
    Recovery["W8 Recovery Worker"] --> Planning["W9 Planning Agent"]
    Planning --> Browser["Browser Worker"]
    Browser --> Web["Synthetic Sandbox pages"]
    Web --> SDB["Sandbox PostgreSQL"]
    Grader["Independent Grader"] --> SDB
    Recovery --> Temporal
~~~

Keycloak is published only on host loopback `127.0.0.1:8080` for browser
redirects and is also connected to internal `identity` for Control API JWKS.
Control Web/API use `control-backend`; only Control API and the private Workflow
Worker join `control-database`. Workflow Worker also joins `temporal-control`
and exposes no port. Keycloak, Control Web, Planning, Browser, Sandbox,
Recovery, and Temporal have no Control database route. Workflow Worker has no
identity or browser-facing network, Bearer token, raw grant, Docker socket, or
public endpoint. Planning/Browser/Sandbox have no Keycloak administration
capability or credential.

## Authentication and ActorContext

The deployment freezes one issuer, internal JWKS URL, audience, browser client,
RS256 algorithm, JWT header type, and Bearer token type. The verifier accepts
Bearer material only in the Authorization header, never follows JWKS redirects,
uses one bounded refresh, and validates key metadata plus signature, `kid`,
issuer, audience, authorized party, subject, expiry, `nbf`, and `iat` before any
tenant query.

Successful verification produces only closed issuer/subject hashes and a
claimed closed role. One organization-qualified database join then resolves
active external identity, user, organization, and membership. The resulting
strict immutable `ActorContext` contains opaque IDs, the database role and
permission set, active organization-qualified approval authorities,
authorization versions, and one stable authorization hash. It
contains no token, raw claim/subject, name, email, username, password, code,
cookie, private key, or request-derived actor/organization.

~~~mermaid
flowchart TD
    Header["One Bearer header"] --> Verify["Fixed-policy JWT + JWKS verify"]
    Verify -->|"closed 401"| RejectAuth["Stop before tenant query"]
    Verify --> Lookup["Joined active identity/user/org/membership lookup"]
    Lookup -->|"inactive/missing/role mismatch"| RejectRole["Closed authorization rejection"]
    Lookup --> Actor["Immutable ActorContext"]
    Actor --> Permission["Closed route permission"]
    Permission --> Scoped["Organization-qualified repository"]
~~~

Keycloak realm roles do not grant application permissions. The token role must
exactly match the active local membership. Permissions are a fixed mapping for
`organization_admin`, `operator`, and read-only `auditor`. There is no global
role, cross-organization role, wildcard, fallback, impersonation, or policy
expression.

## Tenant-safe persistence

Control Plane tables are organizations, users, OIDC identities, memberships,
organization memories, approval authorities, requests, decisions, grants,
audit heads, and audit events. Tenant-owned rows carry non-null
`organization_id`; composite keys/foreign keys/uniqueness/indexes preserve that
ownership. External identity uniqueness is the verified issuer plus subject
hash. Membership uniqueness is organization plus user. All business foreign
keys use `RESTRICT`, and lifecycle transitions are active/disabled or active/
tombstone; no physical-delete route exists.

Repositories expose organization-qualified get/list/count/create/update/
disable/tombstone/reset only. Actor organization is database-derived. A path ID
can select an object but cannot authorize it. Cross-organization and nonexistent
objects have the same stable 404 response, and no list/count/page/error/version/
ETag reveals another tenant. There is no unscoped convenience lookup followed
by Python filtering and no global/default/first/synthetic fallback.

## Optimistic locking

Mutable W10/W11 resources start at version 1. A strong ETag includes a closed
resource kind, a 24-hex SHA-256 owner/resource fingerprint, and the version.
Mutations require one exact If-Match. Missing input returns 428. Malformed,
weak, wildcard, cross-resource, cross-organization, and stale input returns one
412 body without the current version.

Update/disable/tombstone is one transaction with one conditional SQL mutation
over organization ID, resource ID, and expected version. Success increments
exactly once. A zero-row result has no fallback lookup or side effect. Memory
reset uses the organization's memory-collection version and atomically
tombstones only its active memories. PostgreSQL concurrent writes from the same
old version have exactly one winner; SQLite unit tests exercise the same
repository contract.

## Risk, approval, and execution gate

The trusted policy validates one closed action-specific parameter model, reads
only required organization-qualified facts, and maps to frozen L0-L4. L0/L1
automatically append execution audit events. L2 creates a request requiring one
manager. L3 requires manager plus a different security user. L4 and unknown
actions stop permanently. Objective/page/model/body role, risk, actor, or
approver data cannot select or reduce authority.

Requests bind opaque task/step/action references, canonical parameter hash,
risk, requester/executor, required roles, expiry, status, and version.
Decisions are immutable. The final required decision creates a hash-only
short-lived grant and temporarily places its cryptographically random raw form
in a bounded Control API process vault. Claim revalidates identity, authority,
request, decisions, task/step/action/parameters, expiry, authorization hash,
grant hash, and version in one atomic transition. Exactly one concurrent claim
wins; replay has no second receipt or effect.

Recovery persists only the opaque request/grant/execution reference and closed
hashes/status/version. A claimed execution resumes through the durable claim
and released W8 receipt contract, never by replaying raw credential material.
Planning, Browser Worker, Recovery Worker, Temporal, Sandbox, and Grader receive
no Control database credential or raw approval material.

## Production admission and atomic handoff

`POST /api/v1/organizations/{organization_id}/production-runs` authenticates
first, reconstructs current ActorContext, validates one strict closed task and
W11 action schema, applies risk, consumes persistent actor and organization
route buckets, checks the locked 64/32 active queue capacity, and commits the
run, idempotency row, scheduler state, executable outbox when authorized, and
audit event together. It returns 202 and a strong run ETag; it never waits for
Planning, Browser, Temporal, or grading.

L2/L3 admission creates `waiting_approval` without outbox work. The final W11
approval still issues a hash-only one-time grant. The trusted production claim
route verifies the raw credential inside the Control API vault, atomically
claims the grant, creates the durable execution reference, changes the existing
run to `queued`, inserts outbox work, and appends audit. Vault removal occurs
only after commit; a committed claim blocks replay even if removal is delayed.

Run status is closed to `waiting_approval`, `queued`, `leased`, `running`,
`recovering`, `verifying`, `finished_ungraded`, `failed`, `cancelled`, and
`expired`. Terminal states never reactivate. L0/L1 may exercise asynchronous
admission, but only eight exact task/action/parameter hashes authorize a JML
effect. Any other admitted binding becomes `failed/workflow_rejected` before
Temporal or Browser work.

## Durable scheduling, limiter, and Worker

The bounded outbox is partitioned by opaque organization ID. A locked cursor
selects one non-empty organization, claims one item, and advances round robin;
callers provide no priority. Global active pending capacity is 64, per-
organization capacity is 32, and queue TTL is 300 seconds. A queue or limiter
dependency failure is closed 503 with bounded Retry-After and zero partial
admission.

Persistent integer-microtoken buckets use only verified actor, current
organization, and fixed route class. Submit/read/mutate actor rates are
5/10/2 per second with bursts 10/20/4; organization rates are 50/200/25 with
bursts 100/400/50. Refill uses integer UTC microseconds and floor; Retry-After
is the ceiling of the larger deficit, clamped to 1-30 seconds. Forwarded/IP,
body, query, page, and model fields never select a bucket.

One Workflow Worker owns four asynchronous slots. Each claim creates immutable
lease history, increments a per-item fence, and leases for 30 seconds with a
10-second heartbeat. Every heartbeat, start, receipt, release, and terminal
write includes organization, run, outbox, owner hash, lease version, and fence.
Expired owners write zero; one later claimant reuses the same run and
deterministic Temporal workflow identity. Delivery is durable at-least-once
with exactly one active lease winner, not distributed exactly-once. The 25-
second drain stops new claims and finishes or safely releases current work.

## Tamper-evident audit chain

Each organization owns one locked head and a contiguous sequence of append-only
events. Canonical sorted-key UTF-8 JSON binds schema version, sequence,
previous hash, closed event type, opaque actor/subject references, payload hash,
and UTC time into SHA-256. Verification recomputes genesis-to-head order and
detects mutation, deletion, insertion, reorder, broken previous hash, or head
mismatch. Database constraints/triggers reject update/delete. This is
tamper-evident application evidence, not tamper-proof storage, a blockchain,
or legal-compliance proof.

## W9 context and W8 recovery preservation

Released W9 endpoints, synthetic scope, five-layer order, hashes, budgets,
ablations, fake memory store, and results are unchanged. The W10 protected
projection reads only actor-organization durable active memory and returns a
closed safe record containing opaque memory ID, field, safe value, version,
validity/expiry, content hash, and opaque actor/organization authorization
hashes. It is data for a trusted later Context input, not a Planning database
route or authorization declaration.

Temporal history and Checkpoints continue to store only opaque W8 input,
closed operational state, hashes, topology, and numeric high-water counters.
They receive no bearer token, claims, complete ActorContext, semantic W10
memory, raw grant, nonce, or approver data. Recovery caps, current-reference validation, total-ledger accounting,
cleanup, `finished_ungraded`, and independent grading remain unchanged.
