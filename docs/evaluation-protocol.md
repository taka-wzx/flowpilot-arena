# Evaluation protocol

## Purpose and preserved boundary

W10 evaluates strict authentication, database-derived authorization, synthetic
tenant isolation, and optimistic concurrency under a pinned local identity
provider. It does not evaluate a real enterprise IdP, production tenancy,
prompt-injection resistance, identity UX, or load. W3/W7 database-fact Graders
remain the only task-success authority.

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
| users / identities / memberships | 6 / 6 / 6 |
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

## Database and migration protocol

The independent Control Plane migration runs on an empty PostgreSQL database:
upgrade, `current`, `check`, downgrade to base, second upgrade, `current`, and
`check`. Schema inspection verifies organization-aware foreign keys, unique
constraints, and indexes. Released Sandbox migration bytes remain identical to
W9; online Sandbox Alembic remains at `20260728_0003 (head)` with no drift.
Control data is never included in Sandbox Reset/Seed/Grader or Temporal state.

## Compose Development protocol

After a clean-volume start, W10 identity acceptance uses the pinned local issuer
and verifies authentication allow/reject, authorization rejection, two-
organization rejection, optimistic success/stale, concurrent exactly-one-
winner, and safe context projection. It reports counts and closed booleans only,
with real identity-provider calls 0, real model/provider calls 0, cost 0,
Validation false, and Reporting false.

W4-W9 smokes run in release order. W9 must retain all five frozen ablation
hashes, enterprise catalog checksum, context-backed Development Joiner/Mover/
Leaver grade 100, and `finished_ungraded`. W8 retains zero duplicate effects
and all fault/recovery/replay caps. W3/W7 freeze checks and independent grading
remain authoritative.

## Data, Validation, and Reporting discipline

The realm checksum, deterministic identity counts, closed role/permission
matrix, ETag encoding, and Control migration revision are frozen in
`docs/data/week-10-identity-data.md`. Development may rerun while implementing.
After all parameters freeze, Validation may run at most one preregistered final
identity check; evidence states whether it ran.

Reporting is limited to generation/load/schema/checksum validation. Before W15
it receives no Reset, Seed, Agent, OIDC login, identity, organization, user,
membership, RBAC, tenant, memory, context, grade, or result execution or result
inspection.

## Interpretation and real-call boundary

Passing results establish deterministic local authentication, authorization,
two-organization isolation, non-enumeration, optimistic concurrency, migration,
regression, and cleanup behavior. They do not prove production identity
security, real enterprise isolation, external generalization, malicious-page
resistance, production availability, load capacity, SLOs, or ROI.

Calls to a real identity provider/account/data source and real model/provider/
OCR/VLM/embedding services remain not run at 0 calls and 0 cost. W11 approvals
and audit are outside W10.
