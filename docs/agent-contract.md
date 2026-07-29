# W10 agent contract - OIDC, tenant RBAC, and optimistic locking

## Authority, baseline, and sole objective

This contract translates the W10 row of `docs/project-roadmap.md` and the
user-authorized W10 brief into the only implementation authority for
`week/10-identity`.

W10 starts from the official W9 merge commit
`5e1868d30da70c2d8cd9db1705db0cb8f7dabfac`. W9 feature commit
`08275b7aac239c0495a5dae629692533ee0d484b`, pull request #31, its 18-job
pull-request run `30425071418`, and the 18-job post-merge main run
`30425554286` are immutable and passed on their first attempts. W9 has no tag.
The current published release remains `v0.2.0 - Hybrid + Recovery` at
`w08-recovery`; W10 neither creates the missing W9 tag nor a Release.

The literal `%SystemDrive%/` path remains outside every read, enumeration,
scan, diff, status, staging, and modification operation. No
`code_review_agent` repository may be accessed.

W10 has one outcome: preserve every W1-W9 API, deterministic fake result,
catalog/checksum/split, W8 recovery/idempotency contract, W9 context behavior,
Reporting freeze, and independent Grader while adding one fixed local OIDC
boundary, a separate Control Plane identity database, closed tenant RBAC,
authenticated tenant isolation, strong-ETag optimistic locking, durable safe
organization memory, and the minimum browser login experience. Data and
identities remain synthetic. Agent finish remains `finished_ungraded`; only
the independent Sandbox database-fact Grader decides task success.

## Exact W10 scope

W10 may add only:

1. strict verification of bearer access tokens issued by the one configured
   local Keycloak realm, with a fixed issuer, resource audience, public browser
   client, `RS256`, exact local JWKS endpoint, bounded refresh, and no
   request-selected identity configuration;
2. a separate Control Plane PostgreSQL database and reversible Alembic
   migration for organizations, users, OIDC identities, memberships, and
   durable organization memory;
3. database-derived `ActorContext`, active-state enforcement, a closed
   three-role permission matrix, and default-deny authorization;
4. organization-qualified keys, foreign keys, uniqueness, indexes, reads,
   counts, writes, disables, tombstones, and memory reset operations;
5. explicit monotonically increasing versions and strong ETag/If-Match
   preconditions for every mutable W10 tenant-owned resource;
6. protected organization, user, membership, memory, current-identity, and
   authorized context-projection routes in Control API;
7. a minimal Control Web Authorization Code + PKCE login, callback, logout,
   current-identity, and forbidden experience with token material held only in
   process memory;
8. a pinned local-only Keycloak realm/client/users configuration, an isolated
   Control Plane database, one W10 Compose acceptance service, and one CI job;
9. deterministic negative authentication, RBAC, cross-organization,
   optimistic-lock, migration, frontend callback, and regression tests; and
10. W10 architecture, threat, evaluation, synthetic-data, plan, ADR, changelog,
    README, and evidence updates.

No W10 authenticated request enters Temporal or W8 Recovery. Consequently no
token, claim, or W10 actor state is added to a Checkpoint. If a future
authenticated recovery path is authorized, it must re-resolve active database
authorization and may persist only opaque actor/organization IDs and an
authorization hash; that future integration is outside W10.

## Explicit non-goals

W10 adds no W11 approval, HITL, risk policy, approval token/nonce, or audit
chain; W12 production Worker/API split, rate limiting, backpressure, load test,
deployment, or `v0.3.0`; W13 telemetry/dashboard/replay; W14 malicious-page
suite; W15 external benchmark/formal Reporting/repeated evaluation; or W16
Helm/cloud/publication/SBOM/release.

It adds no SAML, SCIM, LDAP, social login, MFA, passkey, account recovery,
password management, dynamic identity provider, arbitrary issuer/JWKS/
discovery URL, global administrator, super-tenant bypass, impersonation,
break-glass access, wildcard organization/permission, ABAC/policy language,
generic identity/repository/gateway/plugin framework, physical business-data
deletion, real enterprise account/data, real model/provider/OCR/VLM/embedding/
vector store/key/egress, or arbitrary browser/API/Shell/SQL/JavaScript/code
capability.

Released Sandbox migrations and W3/W7 catalogs, fixtures, predicates,
checksums, splits, Graders, Reporting manifests, W8 receipts/Checkpoints/
recovery/replan limits, W9 layer order/retrieval/summary/budgets/ablations/
hashes/fake-memory behavior, and `finished_ungraded` semantics are immutable.

## Exact W10 file allowlist

Only the following paths may be created or modified. Every path is explicit;
directory wildcards are forbidden. A new path must be added here before it is
changed, and a scope-expanding path requires new user direction.

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
docs/adr/0010-w10-identity.md
docs/plans/week-10-identity.md
docs/evidence/week-10-report.md
docs/data/week-10-identity-data.md

apps/control_api/Dockerfile
apps/control_api/alembic.ini
apps/control_api/pyproject.toml
apps/control_api/uv.lock
apps/control_api/migrations/env.py
apps/control_api/migrations/script.py.mako
apps/control_api/migrations/versions/20260729_0001_w10_identity.py
apps/control_api/src/flowpilot_control_api/auth.py
apps/control_api/src/flowpilot_control_api/config.py
apps/control_api/src/flowpilot_control_api/context_projection.py
apps/control_api/src/flowpilot_control_api/database.py
apps/control_api/src/flowpilot_control_api/etag.py
apps/control_api/src/flowpilot_control_api/main.py
apps/control_api/src/flowpilot_control_api/models.py
apps/control_api/src/flowpilot_control_api/rbac.py
apps/control_api/src/flowpilot_control_api/repository.py
apps/control_api/src/flowpilot_control_api/schemas.py
apps/control_api/src/flowpilot_control_api/seed.py
apps/control_api/tests/conftest.py
apps/control_api/tests/test_api.py
apps/control_api/tests/test_auth.py
apps/control_api/tests/test_context_projection.py
apps/control_api/tests/test_etag.py
apps/control_api/tests/test_health.py
apps/control_api/tests/test_migrations.py
apps/control_api/tests/test_rbac.py
apps/control_api/tests/test_repository.py

apps/control_web/src/App.css
apps/control_web/src/App.test.tsx
apps/control_web/src/App.tsx
apps/control_web/src/auth.test.ts
apps/control_web/src/auth.ts
apps/control_web/src/vite-env.d.ts
apps/control_web/vite.config.ts

deploy/compose/compose.yaml
deploy/compose/keycloak/flowpilot-realm.json
tests/integration/Dockerfile
tests/integration/w10_identity_compose_smoke.py
~~~

Control Web needs no new dependency. Control API manifest and lock are both
allowlisted because W10 requires SQLAlchemy, Alembic, PostgreSQL, HTTP/JWKS,
JWT, and cryptographic verification. Locks are generated only by `uv`, never
edited by hand. The integration smoke uses its existing locked dependencies.

## Frozen OIDC trust boundary

The only policy is:

| Field | Frozen value |
|---|---|
| issuer | `http://127.0.0.1:8080/realms/flowpilot` |
| internal JWKS URL | `http://keycloak:8080/realms/flowpilot/protocol/openid-connect/certs` |
| resource audience | `flowpilot-control-api` |
| browser client | `flowpilot-control-web` |
| signing algorithm | `RS256` |
| access-token type | `Bearer` |
| header type | `JWT` |

These values are deployment trust roots, not request fields. HTTP redirects,
credentials in the JWKS URL, an unexpected scheme/host/path, duplicate or
unknown `kid`, non-RSA key, wrong key use/algorithm, or malformed JWKS fail
closed. The JWKS cache permits one initial fetch and at most one bounded
refresh, never follows redirects, uses a fixed timeout, and never falls back to
an arbitrary key.

Bearer material is accepted only as one exact `Authorization: Bearer ...`
header. Query/body/cookie token aliases are rejected. Verification requires
signature, exact algorithm, issuer, audience, authorized party/client,
subject, expiry, issued-at, valid not-before when present, header type, claim
token type, `kid`, and one closed synthetic role claim. `alg=none`, algorithm
confusion, bad signature, unknown `kid`, wrong issuer/audience/client/type,
missing subject, expired token, future `nbf`, or invalid/future `iat` returns
the same closed 401 response before any tenant query.

The verifier emits only a closed issuer ID, issuer hash, subject hash, identity
lookup hash, and claimed closed role. It never emits or persists the bearer
token, raw subject, original claims, name, email, username, authorization code,
refresh token, session secret, or private key.

## Identity persistence and ActorContext

All identifiers use closed prefixes plus opaque random or fixed synthetic
suffixes: `org_`, `usr_`, `idn_`, `mbr_`, and `mem_`. Fixed Development IDs
and Keycloak subjects contain no real personal or enterprise data.

The Control Plane schema is:

- `organizations`: opaque ID, `active|disabled`, resource version, memory
  collection version, UTC timestamps;
- `users`: opaque ID, non-null organization ID, `active|disabled`, version,
  UTC timestamps, and unique `(organization_id, id)` owner key;
- `oidc_identities`: opaque ID, non-null organization/user IDs, closed issuer
  ID/hash, subject hash, `active|disabled`, version, unique verified
  `(issuer_id, subject_hash)`, and organization-aware foreign key;
- `memberships`: opaque ID, non-null organization/user IDs, closed role,
  `active|disabled`, version, unique `(organization_id, user_id)`, and
  organization-aware foreign key; and
- `organization_memories`: opaque ID, non-null organization/owner user IDs,
  closed field/safe value, `active|tombstone`, version, validity/expiry,
  content hash, UTC timestamps, and organization-aware owner foreign key.

All foreign keys use `RESTRICT`; there is no physical-delete route. Every
tenant-owned unique constraint and index begins with `organization_id` where
applicable. Control Plane identity data is never stored in, reset by, seeded
into, or graded from the Sandbox/Arena or Temporal databases.

`ActorContext` is constructed only after token verification and one joined,
organization-qualified database resolution of active identity, user,
organization, and membership. It contains opaque IDs, closed issuer/subject
hashes, closed role and permissions, the three database authorization
versions, and a stable authorization hash. It contains no token, raw claim, or
personal field and is not an API request model. A disabled identity, user,
organization, or membership is immediately rejected. If a token carries a
role that differs from the current database membership, authorization fails.

## Closed RBAC matrix

Permissions are a closed enum. Unknown roles/permissions and unmatched access
default deny. Every protected route declares one permission.

| Permission | organization_admin | operator | auditor |
|---|---:|---:|---:|
| `organization.read` | yes | yes | yes |
| `organization.update` | yes | no | no |
| `user.read` | yes | yes | yes |
| `user.manage` | yes | no | no |
| `membership.read` | yes | no | yes |
| `membership.manage` | yes | no | no |
| `memory.read` | yes | yes | yes |
| `memory.write` | yes | yes | no |
| `memory.reset` | yes | yes | no |
| `context.project` | yes | yes | yes |

Keycloak role claims never grant business authority by themselves; they must
exactly match the active local membership. No role has global or cross-
organization authority. Organization creation and first-admin bootstrap are
limited to the deterministic Development seed because a tenant-global
administrator is explicitly forbidden.

## Authenticated tenant isolation

The organization in `ActorContext` is always database-derived. A path
organization ID selects a resource only. A mismatch is rejected before object,
count, version, or ETag lookup. Request bodies have no actor, owner,
organization, role, permission, issuer, JWKS, or algorithm fields; such extras
fail strict validation.

Repositories expose only organization-qualified get/list/count/create/update/
disable/tombstone/reset operations. They do not provide global convenience
lookups followed by Python filtering. Atomic mutations always include
`organization_id`, resource ID, and expected version. Cross-organization and
nonexistent objects share the same stable 404 body. Lists, counts, paging,
errors, hashes, versions, and ETags contain only the actor organization. There
is no global/default/first/synthetic/caller-provided fallback.

## Optimistic-lock HTTP and database contract

Every mutable W10 tenant resource starts at version 1. Successful mutation
increments exactly once. Responses for a single resource carry a strong ETag:

~~~text
"w10-<closed-kind>-<24 lowercase hex owner/resource fingerprint>-v<version>"
~~~

The fingerprint is the first 24 hexadecimal characters of SHA-256 over the
closed resource kind, organization ID, and resource ID. It contains no raw
identity or memory value. Weak ETags are forbidden.

`PATCH`, disable/tombstone `DELETE`, and memory reset require one `If-Match`.
Missing input returns 428 `precondition_required`. Malformed, weak,
cross-resource, cross-organization, or stale input returns the same 412
`precondition_failed` body without a current version. The server never accepts
`*` or last-write-wins.

Update/disable/tombstone executes one transaction and one conditional SQL
mutation keyed by `(organization_id, resource_id, expected_version)`. Zero
affected rows returns 412 with no follow-up unscoped lookup. A stale write
creates no partial state, side effect, tombstone, or version increase. Two
concurrent writes using one version have exactly one winner. Memory collection
reset uses the organization's explicit memory-collection version as its
precondition, atomically tombstones only that organization, increments each
changed memory version once, and increments the collection version once.

## W9 memory/context identity binding

Released W9 endpoints, synthetic `scope_id`, five-layer order, schemas,
retrieval, summary, hashes, budgets, ablations, fake store, and results remain
unchanged for regression. A W9 synthetic scope is never accepted by a W10
authentication or authorization dependency.

The new protected Control API context-projection route derives organization
and actor solely from verified `ActorContext`, reads durable active memory with
organization-qualified queries, and returns only a closed safe projection:
opaque memory ID, closed field, safe synthetic value, version, validity,
expiry, content hash, opaque organization/actor hashes, and authorization hash.
It returns no token, raw claim, subject, email, name, username, endpoint, or
database capability. This projection is the only W10 input admitted for later
trusted W9 Context assembly; W10 does not add a Planning-to-database route or
change any W9 fake result.

## Control Web contract

Control Web exposes only login, callback, logout, current identity, forbidden,
and failure states. Login uses Authorization Code + S256 PKCE, cryptographic
state and nonce, one exact redirect URI, one exact post-logout URI, and one
exact origin. The transient verifier/state/nonce transaction may use
`sessionStorage` only until callback validation, then is removed. Access and ID
tokens live only in module memory; no token enters a URL, Local Storage,
persistent browser storage, application log, or rendered text.

Callback rejects missing/mismatched state, nonce, issuer, audience, expiry,
code, or PKCE transaction before identity display. Browser-visible role and
organization are informational only; every API operation is independently
authorized by Control API.

## Deterministic Development identity matrix

The fixed local realm and Control Plane seed contain two synthetic
organizations and, in each, one `organization_admin`, one `operator`, and one
`auditor`, for totals of 2 organizations, 6 users, 6 OIDC identities, and 6
memberships. Subjects and IDs are fixed opaque synthetic values. Passwords are
local disposable test credentials, never real credentials. Tests generate
ephemeral RSA private keys at runtime only; no private key or real token is
committed.

Development may repeatedly execute the frozen authentication, role allow/deny,
two-organization isolation, memory lifecycle, ETag, stale/concurrent-write,
and migration matrices. Validation may run at most once after all of the
issuer/audience/client/algorithm, RBAC, dataset, ETag, and locking rules above
freeze. Reporting is limited to load/schema/checksum validation and is not
executed before W15.

## Acceptance and evidence

Unit/API tests must cover all negative OIDC cases in the user brief; active and
disabled identity states; the complete role allow/deny matrix; role injection
and role mismatch; same-organization operations; every requested cross-
organization get/list/count/create/update/disable/membership/memory/context
case; uniform non-enumeration; missing/malformed/weak/cross-resource/stale
ETags; successful +1; stale rollback/replay; and concurrent exactly-one-winner.

Control Plane Alembic must pass empty upgrade, current, check, downgrade, and
second upgrade. Released Sandbox migration bytes must match W9 exactly and its
head remains `20260728_0003`. Compose must start W1-W10, exercise the pinned
local issuer, verify the realm configuration checksum, run W4-W10 smokes, and
clean all project containers/networks/volumes.

Evidence records only versions, stable config/catalog hashes, opaque synthetic
IDs/hashes, closed role/permission/status/reason codes, HTTP statuses, counts,
resource versions, grades, and call/cost zeros. It never records raw token,
claim, subject, authorization code, cookie, private key, password, endpoint,
personal data, or machine path. Local Keycloak is a frozen synthetic test
issuer; calls to real identity providers remain 0. Real model/provider/OCR/
VLM/embedding calls remain 0 and cost remains 0.

## GitHub Actions quota, Git, and W11 boundary

CI retains main-only push and full pull-request triggers and adds exactly one
necessary W10 job, for 19 total jobs. Remote delivery is not authorized. Do not
push, create a PR, merge, tag, release, trigger/rerun Actions, or call a real
identity/model/provider service without separate explicit user authorization.

If remote delivery is later authorized, diagnose all failures first, make one
concentrated fix and one necessary feature push. With no code/lock/migration/
Compose/workflow change and a transient infrastructure failure, rerun failed
jobs only. Never rerun all jobs, a successful/superseded run, create an empty
commit or duplicate PR, force-push, or change unrelated CI. Record every
necessary extra run ID, SHA, trigger, code-change state, and why a failed-job-
only rerun was insufficient.

Local completion requires every application lock/quality/test gate; Control
Plane migration round-trip; Sandbox migration freeze; W3/W7/W9 freezes; W4-W10
Compose smokes; deterministic Joiner/Mover/Leaver grade 100; exact allowlist,
secret, diff, status, staged/unstaged, and cleanup audits. Unavailable tooling
is recorded, never treated as a pass.

After all locally available gates pass and evidence matches observations,
explicitly stage only exact allowlist paths, create one local W10 commit, and
stop. Do not begin W11, create `w09-context`, create `w10-identity`, or create a
Release.
