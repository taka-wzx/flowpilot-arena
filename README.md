# FlowPilot Arena

> A governed enterprise computer-use Agent project and a separate resettable
> synthetic evaluation environment.

**Current status: local W10 - OIDC, Organization/User, RBAC, Tenant Isolation,
and Optimistic Locking, based on released W9.** W10 adds one fixed local OIDC
boundary, an independent Control Plane identity database, database-derived
authorization, organization-qualified access, atomic strong-ETag writes,
durable authorized organization memory, and a minimal PKCE login experience.
Independent Sandbox database-fact grading remains the only task-success
authority.

W9 PR #31 merged at `5e1868d30da70c2d8cd9db1705db0cb8f7dabfac`.
Its 18-job PR CI and 18-job post-merge main CI both passed on their first
attempts. No W9 tag exists. The current published release remains
`v0.2.0 - Hybrid + Recovery` using `w08-recovery`; W10 does not modify or
republish that baseline.

## Current architecture

| Component | Current responsibility | Deliberately absent |
|---|---|---|
| W1-W3 | Control skeleton, synthetic Sandbox, immutable Arena/Graders | Real systems/data and Agent-derived success |
| W4-W7 | Isolated Browser/DOM/Vision/Hybrid/Planning path | Arbitrary browser/API/code capability |
| W8 | Deterministic Temporal replay, Checkpoints, epochs, receipts | Identity/token/semantic data in history |
| W9 | Five strict context layers, fixed retrieval/summary/fake memory | Vector DB, embedding, real provider |
| W10 | Local OIDC, identity DB, closed RBAC, tenant-safe repositories, ETags | Global admin, approvals, production identity platform |

~~~mermaid
flowchart LR
    BrowserUser["Local browser user"] -->|"Code + S256 PKCE"| Keycloak["Keycloak 26.3.2\nfixed local realm"]
    BrowserUser --> Web["Control Web"]
    Web -->|"Bearer access token"| API["Control API"]
    Keycloak -->|"JWKS on internal identity network"| API
    API --> IdentityDB["Control PostgreSQL\nidentity + org memory"]
    API -->|"authorized safe projection only"| Context["W9 Context boundary"]
    Planning["Planning Agent"] --> Browser["Browser Worker"]
    Browser --> Sandbox["Synthetic Sandbox"]
    Grader["Independent Grader"] --> SandboxDB["Sandbox PostgreSQL"]
~~~

Control PostgreSQL, Sandbox PostgreSQL, and Temporal PostgreSQL are separate.
Planning Agent gains no Keycloak, Control API, Control DB, Sandbox DB, Arena, or
Grader route. Keycloak is reachable from the host only at
`127.0.0.1:8080` and from Control API through the dedicated identity network.

## Identity, authorization, and tenant boundary

The OIDC trust roots are frozen deployment policy: issuer
`http://127.0.0.1:8080/realms/flowpilot`, internal JWKS at the corresponding
`keycloak:8080` realm path, audience `flowpilot-control-api`, browser client
`flowpilot-control-web`, and algorithm `RS256`. Request-selected issuer, JWKS,
discovery, client, or algorithm is never accepted. Signature, `kid`, issuer,
audience, authorized party, subject, expiry, `nbf`, `iat`, JWT header type, and
Bearer token type fail closed before any tenant query.

The deterministic realm and Control Plane seed contain two synthetic
organizations and six users/identities/memberships: one
`organization_admin`, one `operator`, and one `auditor` in each organization.
Keycloak role claims do not grant business authority; they must exactly match
an active database membership. There is no global administrator, wildcard
tenant, fallback organization, impersonation, or break-glass path.

- `organization_admin` manages its own organization, users, memberships, and
  memory.
- `operator` reads organization/user/memory, writes or resets memory, and
  projects authorized context; it cannot manage membership or roles.
- `auditor` is read-only and may project authorized context.

Every tenant-owned key, foreign key, unique constraint, index, query, count,
write, disable, tombstone, and memory reset is organization-qualified. A cross-
organization object and a nonexistent object share the same stable 404
semantics. There is no physical delete.

Every mutable tenant resource starts at version 1. Strong ETags bind resource
kind, organization, resource ID, and version. Mutations require `If-Match`:
missing preconditions return 428; malformed, weak, cross-resource, cross-org,
or stale preconditions return the same 412 without disclosing a current
version. A successful atomic mutation increments exactly once; two concurrent
writes from one old version have exactly one winner.

W9's released synthetic `scope_id` remains only a fake regression input. New
W10 context projection derives actor and organization from verified identity
and returns only closed safe memory fields, versions, hashes, and opaque actor/
organization authorization hashes. It never forwards tokens, raw claims,
subjects, names, email, endpoints, or database capabilities to Planning,
Browser, Temporal, Sandbox, or Grader.

## Local start and deterministic acceptance

Python targets 3.13 and uses uv. Inject a temporary local W8 test envelope key
for Compose; never commit or log it.

~~~powershell
$env:RECOVERY_ENVELOPE_KEY = '<runtime-only base64 key>'
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
docker compose -f deploy/compose/compose.yaml --profile acceptance run --build --rm acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile vision-acceptance run --build --rm vision-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile hybrid-acceptance run --build --rm hybrid-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile planning-acceptance run --build --rm planning-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile recovery-acceptance run --build --rm recovery-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile context-acceptance run --build --rm context-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile identity-acceptance run --build --rm identity-acceptance-smoke
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
Remove-Item Env:RECOVERY_ENVELOPE_KEY
~~~

The W10 smoke uses only the pinned local issuer. It exercises token allow/deny,
closed RBAC rejection, two-organization isolation, strong ETag stale-write
rejection, concurrent exactly-one-winner, and authorized context projection.
It executes no Reporting, calls no real identity provider or model service, and
incurs zero actual cost.

Exact local gates are in [AGENTS.md](AGENTS.md), scope is in
[the W10 contract](docs/agent-contract.md), design is in
[ADR 0010](docs/adr/0010-w10-identity.md), and implementation stages are in
[the W10 plan](docs/plans/week-10-identity.md).

## Evaluation and release discipline

W3/W7 catalogs and W9 context hashes/ablations remain immutable. W10's identity,
role, tenant, ETag, and concurrency matrices run only on deterministic
synthetic Development data. Validation may run once only after all parameters
freeze. Reporting is load/schema/checksum validated only and is not executed
before W15.

W10 remote delivery is not authorized by default: no push, PR, merge, tag,
Release, or remote CI. If later authorized, the tag is `w10-identity`; W10 does
not create `v0.3.0`, which belongs to W12, and does not backfill a W9 tag.

Licensed under Apache-2.0.
