# Evaluation protocol

## Purpose and preserved boundary

W11 evaluates a closed server-side risk policy, database-derived approval
authority, L2/L3 HITL, parameter-bound one-time grants, durable claim/recovery,
and a per-organization tamper-evident audit chain. It preserves W10 strict
authentication, tenant isolation, and optimistic locking. It does not evaluate
a real enterprise IdP/approver, production tenancy, legal compliance,
prompt-injection resistance, production worker split, or load. W3/W7 database-
fact Graders remain the only task-success authority.

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

## Database and migration protocol

The independent Control Plane migration runs on an empty PostgreSQL database:
upgrade through `20260729_0002`, `current`, `check`, downgrade to W10, second
upgrade, `current`, and `check`. Schema inspection verifies organization-aware
foreign keys, unique constraints, indexes, append-only triggers, and rollback.
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

The acceptance-only split is closed to `development|validation`. It changes
only the final observation flag; it cannot select a product policy, actor,
organization, risk, approval, grant, audit event, side effect, or expected
count.

W4-W10 smokes run in release order before W11. W9 must retain all five frozen ablation
hashes, enterprise catalog checksum, context-backed Development Joiner/Mover/
Leaver grade 100, and `finished_ungraded`. W8 retains zero duplicate effects
and all fault/recovery/replay caps. W3/W7 freeze checks and independent grading
remain authoritative.

## Data, Validation, and Reporting discipline

The realm checksum, deterministic identity/authority counts, action/risk
mapping, approval roles/state/expiry, grant/claim/recovery bindings, audit
schema, ETag encoding, and Control migration revision are frozen in
`docs/data/week-11-approval-data.md`. Development may rerun while implementing.
After all parameters and expected results freeze, Validation may run exactly
once; evidence records its ordinal and observed counts/hashes.

Reporting is limited to generation/load/schema/checksum validation. Before W15
it receives no Reset, Seed, Agent, OIDC login, identity, approval, grant,
audit-result inspection, organization, user, membership, RBAC, tenant, memory,
context, grade, or result execution or inspection.

## Interpretation and real-call boundary

Passing results establish deterministic local authentication, authorization,
two-organization isolation, closed risk/approval behavior, one-time claim,
tamper detection, optimistic concurrency, migration, regression, and cleanup.
They do not prove production identity/approval security, real enterprise
isolation, external generalization, malicious-page resistance, legal
compliance, production availability, load capacity, SLOs, or ROI.

Calls to a real identity provider/account/data source and real model/provider/
OCR/VLM/embedding services remain not run at 0 calls and 0 cost. W12 production
worker/load/release behavior is outside W11.
