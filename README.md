# FlowPilot Arena

> A governed enterprise computer-use Agent project and a separate resettable
> synthetic evaluation environment.

**Current status: local W11 - HITL, closed risk policy, one-time approval, and
a tamper-evident audit chain.** W11 builds on the immutable W10 identity tag
`w10-identity` at `9bbb0303c6bc795468b094df676a86dfcbc69dcb`. It adds
database-derived manager/security authority, mandatory L2/L3 approval,
parameter-bound one-time grant claims, recovery-safe execution references, and
per-organization canonical audit chains. Independent Sandbox database-fact
grading remains the only task-success authority.

The local W11 branch starts from quota-maintenance commit
`b90cd44ec440eef2d69f12d03890bae57c845e37`. Maintenance PR #33 remains
open/blocked because its first run exhausted Actions quota before fourteen jobs
started; that remote state does not weaken local gates. The current published
release remains `v0.2.0 - Hybrid + Recovery` using `w08-recovery`.

## Current architecture

| Component | Current responsibility | Deliberately absent |
|---|---|---|
| W1-W3 | Control skeleton, synthetic Sandbox, immutable Arena/Graders | Real systems/data and Agent-derived success |
| W4-W7 | Isolated Browser/DOM/Vision/Hybrid/Planning path | Arbitrary browser/API/code capability |
| W8 | Deterministic Temporal replay, Checkpoints, epochs, receipts | Identity/token/semantic data in history |
| W9 | Five strict context layers, fixed retrieval/summary/fake memory | Vector DB, embedding, real provider |
| W10 | Local OIDC, identity DB, closed RBAC, tenant-safe repositories, ETags | Global admin, approvals, production identity platform |
| W11 | Closed L0-L4 risk, L2/L3 HITL, one-time grants, audit chain | Dynamic policy, L4 override, production worker split |

~~~mermaid
flowchart LR
    BrowserUser["Local browser user"] -->|"Code + S256 PKCE"| Keycloak["Keycloak 26.3.2\nfixed local realm"]
    BrowserUser --> Web["Control Web"]
    Web -->|"Bearer access token"| API["Control API"]
    Keycloak -->|"JWKS on internal identity network"| API
    API --> IdentityDB["Control PostgreSQL\nidentity + org memory"]
    API --> Risk["Closed L0-L4 policy"]
    Risk --> Approval["L2/L3 approval state machine"]
    Approval --> IdentityDB
    API --> Audit["Per-organization audit chain"]
    Audit --> IdentityDB
    API -->|"authorized safe projection only"| Context["W9 Context boundary"]
    Planning["Planning Agent"] --> Browser["Browser Worker"]
    Browser --> Sandbox["Synthetic Sandbox"]
    Grader["Independent Grader"] --> SandboxDB["Sandbox PostgreSQL"]
~~~

Control PostgreSQL, Sandbox PostgreSQL, and Temporal PostgreSQL are separate.
Planning Agent gains no Keycloak, Control API, Control DB, Sandbox DB, Arena, or
Grader route. Keycloak is reachable from the host only at
`127.0.0.1:8080` and from Control API through the dedicated identity network.

## Identity, approval, and tenant boundary

The OIDC trust roots are frozen deployment policy: issuer
`http://127.0.0.1:8080/realms/flowpilot`, internal JWKS at the corresponding
`keycloak:8080` realm path, audience `flowpilot-control-api`, browser client
`flowpilot-control-web`, and algorithm `RS256`. Request-selected issuer, JWKS,
discovery, client, or algorithm is never accepted. Signature, `kid`, issuer,
audience, authorized party, subject, expiry, `nbf`, `iat`, JWT header type, and
Bearer token type fail closed before any tenant query.

The deterministic realm and Control Plane seed contain two synthetic
organizations and sixteen users/identities/memberships: each organization has
an administrator, requester/executor, auditor, active manager, active security,
disabled manager user, disabled security authority, and no-authority user.
Each organization has four authority rows. Keycloak role claims do not grant
business or approval authority; they must match the active database membership,
while manager/security authority is resolved independently from database rows.
There is no global approver, wildcard tenant, fallback organization,
impersonation, administrator override, break-glass path, or L4 approval.

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

The risk catalog is frozen at 2/2/7/5/5 actions for L0/L1/L2/L3/L4. L0 and L1
execute automatically and are audited. L2 requires one active manager. L3
requires an active manager and a different active security user. L4 and unknown
actions are permanently denied. Strict action parameters are canonicalized and
SHA-256 bound; caller, page, DOM, model, header, and role input cannot lower
risk or select an approver.

Completed approvals issue one short-lived grant whose raw credential exists
only in the bounded Control API executor vault; PostgreSQL stores token and
nonce hashes only. Claim predicates bind organization, request, task, step,
action, parameter hash, executor, expiry, state, and version, so concurrent
claim has exactly one winner and replay cannot create a second effect. Audit
events are append-only canonical JSON with a per-organization sequence,
previous hash, and event hash. Verification is deterministic and the property
is tamper-evident, not tamper-proof or a legal-compliance claim.

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
docker compose -f deploy/compose/compose.yaml --profile approval-acceptance run --build --rm approval-acceptance-smoke
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
Remove-Item Env:RECOVERY_ENVELOPE_KEY
~~~

The W10 smoke retains the pinned local issuer/RBAC/tenant/locking regression.
The W11 smoke then exercises L0-L4 policy, L2/L3 separation of duties,
self/inactive/cross-organization rejection, parameter invalidation, one-winner
claim/replay, and audit verification. It executes no Reporting, calls no real
identity provider or model service, and incurs zero actual cost.

Exact local gates are in [AGENTS.md](AGENTS.md), scope is in
[the W11 contract](docs/agent-contract.md), design is in
[ADR 0011](docs/adr/0011-w11-approval.md), and implementation stages are in
[the W11 plan](docs/plans/week-11-approval.md).

## Evaluation and release discipline

W3/W7 catalogs, W9 context hashes/ablations, and W10 identity/tenant behavior
remain immutable. W11 matrices use deterministic synthetic Development data.
Validation may run exactly once only after every risk, approval, grant,
recovery, audit, seed, and expected result freezes. Reporting is load/schema/
checksum validated only and is not executed before W15.

W11 remote delivery is not authorized by default: no push, PR, merge, tag,
Release, or remote CI. If later authorized, the tag is `w11-approval`; W11
creates no Release or `v0.3.0`, which belongs to W12.

Licensed under Apache-2.0.
