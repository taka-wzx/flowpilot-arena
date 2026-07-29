# ADR 0010: Fixed local OIDC and organization-qualified Control Plane identity

- Status: Accepted for local W10 implementation
- Date: 2026-07-29

## Context

W9 proves deterministic context mechanics with a synthetic scope but explicitly
does not authenticate users, authorize organizations, persist multi-user memory,
or prevent concurrent lost updates. W10 must add those boundaries without
giving Planning Agent a database route, mixing identity into Sandbox/Temporal,
trusting page/JWT role data as business authority, adding global administration,
or starting W11 approvals and W12 production work.

## Decision

### One frozen local issuer

Use Keycloak 26.3.2 only for deterministic local and CI Development. Freeze the
external issuer at `http://127.0.0.1:8080/realms/flowpilot`, internal JWKS URL at
the same realm on `keycloak:8080`, audience `flowpilot-control-api`, browser
client `flowpilot-control-web`, algorithm RS256, JWT header type, and Bearer
access-token type.

Control API verifies signature, key metadata, `kid`, issuer, audience,
authorized party, subject, expiry, optional `nbf`, `iat`, and token types before
any tenant query. JWKS uses a fixed host/path/timeout, no redirects, and at most
one bounded refresh. No request may select an issuer, discovery endpoint, JWKS,
client, or algorithm.

Control Web uses Authorization Code + S256 PKCE, cryptographic state and nonce,
and exact origin/redirect/post-logout allowlists. Access/ID tokens are kept only
in module memory; transient verifier/state/nonce transaction data is removed
from sessionStorage after callback validation.

### Independent Control identity persistence

Add a separate Control PostgreSQL database and Alembic history for
organizations, users, OIDC identities, memberships, and organization memories.
All tenant rows have non-null organization ownership and organization-aware
keys, foreign keys, uniqueness, indexes, and queries. External identity maps a
verified issuer and subject hash to a local user. Lifecycle is disable or
tombstone only; all business foreign keys restrict physical deletion.

This data never enters Sandbox Reset/Seed/Grader or Temporal. Planning Agent,
Browser Worker, Sandbox, and Grader receive no Control database route.

### Database-derived authorization

After strict token validation, resolve active OIDC identity, user,
organization, and membership in one organization-qualified join. Construct a
strict immutable ActorContext with opaque IDs, hashes, closed role/permissions,
authorization versions, and a stable authorization hash. It is not a request
model and contains no token, raw claim/subject, name, email, or username.

Freeze three roles. Organization administrator has all organization-local
permissions; operator can read organization/user/memory, write/reset memory,
and project context but cannot manage users/memberships; auditor is read-only
and can project context. Unknown roles/permissions default deny. A Keycloak role
must match the database membership but never grants permission alone. There is
no global admin, wildcard organization, impersonation, or fallback scope.

### Tenant-safe repositories and optimistic locking

Expose only organization-qualified repository operations. A path organization
ID selects a resource but cannot authorize it. Cross-organization and
nonexistent objects use the same 404 without count/version/ETag lookup or
leakage.

Every mutable W10 resource starts at version 1 and emits a strong ETag bound to
closed kind, organization, resource, and version. Mutation requires one exact
If-Match. Missing precondition is 428; malformed, weak, wildcard, cross-
resource, cross-organization, or stale is the same 412 without current version.
One SQL transaction and conditional organization/resource/expected-version
mutation increments exactly once. Two same-version concurrent writes have
exactly one winner. Memory reset uses an organization collection version and
atomically tombstones only that organization's active rows.

### W9 integration

Keep released W9 endpoints, fake organization-memory store, synthetic scope,
layer order, retrieval, summary, budgets, hashes, ablations, and results
unchanged. Add only a protected Control API safe projection derived from
ActorContext and organization-qualified durable memory. The projection contains
closed safe records and opaque hashes, never tokens, claims, personal data, or
database capability. It may feed a later trusted W9 assembly but does not create
a Planning-to-Control route.

## Consequences

- Local Development can reproduce strict authentication, closed RBAC, two-
  organization isolation, durable memory, ETag failure, and exactly-one-winner.
- Identity state and migrations are independent of Sandbox/Temporal.
- Authorization revocation is immediate because every request re-resolves
  current active database state and role agreement.
- Keycloak must join a host-reachable Control network for the loopback browser
  redirect and the internal identity network for JWKS.
- Results prove only the frozen synthetic environment, not production IdP,
  enterprise tenancy, scale, availability, or prompt-injection resistance.

## Rejected alternatives

- Trust Keycloak roles directly: violates database-authoritative membership.
- Put identity in Sandbox PostgreSQL: mixes Control and evaluation ownership.
- Give Planning Agent Control DB access: violates released Agent isolation.
- Dynamic multi-provider discovery: expands W10 trust roots and SSRF surface.
- Global administrator/support bypass: violates tenant isolation.
- Unconditional/last-write-wins updates: loses concurrent changes.
- Physical deletes: destroys durable identity/memory history.
- Store tokens/ActorContext in Temporal: leaks credentials and stale authority.
- Generic identity/policy/repository framework: premature future abstraction.
