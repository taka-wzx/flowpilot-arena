# Architecture

## W10 current-state architecture

W10 adds identity only to the Control Plane. A pinned local Keycloak is the
synthetic OIDC issuer, and a new Control PostgreSQL database owns organization,
user, external identity, membership, and durable organization-memory state.
Sandbox/Arena, Temporal, and Control persistence remain separate. Planning
Agent still reaches only Browser Worker and receives neither tokens nor any
database capability.

~~~mermaid
flowchart LR
    Human["Local browser"] -->|"Authorization Code + S256 PKCE"| KC["Keycloak 26.3.2\nflowpilot realm"]
    Human --> CW["Control Web"]
    CW -->|"Authorization: Bearer"| CA["Control API"]
    KC -->|"fixed JWKS\ninternal identity network"| CA
    CA --> CPDB["Control PostgreSQL\norganizations/users/identities/\nmemberships/org memory"]
    CA -->|"closed authorized projection"| Context["W9 Context boundary"]
    Recovery["W8 Recovery Worker"] --> Planning["W9 Planning Agent"]
    Planning --> Browser["Browser Worker"]
    Browser --> Web["Synthetic Sandbox pages"]
    Web --> SDB["Sandbox PostgreSQL"]
    Grader["Independent Grader"] --> SDB
    Recovery --> Temporal["Temporal + separate PostgreSQL"]
~~~

Keycloak is published only on host loopback `127.0.0.1:8080` for browser
redirects and is also connected to internal `identity` for Control API JWKS.
Control Web/API use `control-backend`; only Control API joins
`control-database`. Keycloak, Control Web, Planning, Browser, Sandbox, Recovery,
and Temporal have no Control database route. Planning/Browser/Sandbox have no
Keycloak administration capability or credential.

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
permission set, authorization versions, and one stable authorization hash. It
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
and organization memories. Tenant-owned rows carry non-null
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

Mutable W10 resources start at version 1. A strong ETag includes a closed
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
They receive no bearer token, claims, complete ActorContext, or semantic W10
memory. Recovery caps, current-reference validation, total-ledger accounting,
cleanup, `finished_ungraded`, and independent grading remain unchanged.
