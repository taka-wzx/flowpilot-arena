# W11 agent contract - HITL, risk policy, one-time approval, and audit chain

## Authority, baselines, and sole objective

This contract translates the W11 roadmap row and the user-authorized W11 brief
into the only implementation authority for `week/11-approval`.

The immutable product baseline is W10 merge
`9bbb0303c6bc795468b094df676a86dfcbc69dcb`; W10 feature commit
`df0e48a3b965959425c42e14a1280b39a7899cb4` and tag `w10-identity`
remain unchanged. The local starting point is quota-maintenance commit
`b90cd44ec440eef2d69f12d03890bae57c845e37`. Maintenance PR #33 is open and
blocked only because Actions run `30440647089`, attempt 1, contains fourteen
zero-step failures after the Actions spending limit was exhausted. This remote
state does not block local W11 development. The current Release remains
`v0.2.0 - Hybrid + Recovery` at `w08-recovery`.

The literal `%SystemDrive%/` path is outside every read, enumeration, scan,
diff, status, staging, and modification operation. No `code_review_agent`
repository may be accessed.

W11 has one outcome: preserve every W1-W10 API, deterministic fake result,
catalog/checksum/split, W8 receipt/recovery/idempotency contract, W9 context
contract, W10 OIDC/RBAC/tenant/locking contract, Reporting freeze, and
independent Grader while adding a closed server-side L0-L4 risk policy,
database-derived manager/security authority, mandatory L2/L3 human approval,
parameter-bound one-time grants, a durable execution claim, and a per-
organization append-only tamper-evident audit chain. Agent finish remains
`finished_ungraded`; only the independent Sandbox database-fact Grader decides
task success.

## Exact W11 scope

W11 may add only:

1. one closed action catalog and trusted server-side L0-L4 classification over
   strict validated parameters plus current organization-qualified database
   facts;
2. Control Plane approval-authority, request, immutable decision, one-time
   grant/execution-claim, audit-head, and append-only audit-event persistence;
3. database-derived `manager` and `security` approval authorities kept
   separate from the three W10 business roles;
4. separation of duties, self-approval denial, current-active-state rechecks,
   request lifecycle transitions, expiry, cancellation, and invalidation;
5. cryptographically random short-lived credentials whose raw value exists
   only in a bounded in-process trusted executor vault and whose hashes alone
   are stored;
6. atomic one-winner grant claim, durable recovery authorization references,
   and receipt-bound completion without changing any W8 cap;
7. organization-qualified canonical audit append and deterministic
   genesis-to-head verification;
8. strong W11 ETags and required If-Match for mutable W11 resources;
9. minimal authenticated Control Web approval and read-only audit views;
10. one deterministic W11 Compose acceptance profile appended to the existing
    consolidated W4-W10 regression; and
11. W11 architecture, threat, evaluation, data, ADR, plan, evidence, README,
    changelog, roadmap, and CI updates.

W4-W10 synthetic regression routes remain isolated compatibility paths. They
are not caller-selectable bypasses for the W11 authenticated execution gate.
Planning remains Browser-only and receives no OIDC token, Control database,
approval repository, audit repository, approver list, raw grant, nonce, or
general Control API capability. Browser and Recovery receive no Control
database credential. W11 adds no W12 API/Worker production split.

## Explicit non-goals

W11 adds no production worker pool, API/Worker split, rate limiting,
backpressure, load test, 50-user/four-browser acceptance, `w12-production`,
`v0.3.0`, W13 telemetry/dashboard/replay, W14 malicious-page suite, W15
external benchmark/Reporting execution, W16 deployment/publication/SBOM, or
W12+ placeholder.

It adds no real identity, account, organization, user, approver, personal data,
model, provider, OCR, VLM, embedding, key, or egress call; SAML, SCIM, LDAP,
MFA, passkey, global approver, super-tenant, impersonation, delegation,
break-glass, emergency bypass, administrator override, L4 approval, dynamic
policy, ABAC, DSL, script, eval, regex policy, rules engine, arbitrary approval
flow, batch approval, notification/webhook, electronic signature, HSM,
blockchain, physical business/approval/audit deletion, or arbitrary Shell,
SQL, JavaScript, code, URL, header, selector, XPath, coordinate, or API
capability.

Released Sandbox migrations and W3/W7 catalogs, fixtures, predicates,
checksums, splits, Graders, Reporting manifests, W8 receipt/Checkpoint/recovery/
replan limits, W9 layer/retrieval/summary/budget/ablation/hash behavior, W10
issuer/JWKS/audience/client/RS256 policy, and `finished_ungraded` semantics are
immutable.

## Exact W11 file allowlist

Only the following paths may be created or modified. Every path is explicit;
directory wildcards are forbidden. A new path must be added here before it is
changed, and scope expansion requires new user direction.

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
docs/adr/0011-w11-approval.md
docs/plans/week-11-approval.md
docs/evidence/week-11-report.md
docs/data/week-11-approval-data.md

apps/control_api/migrations/versions/20260729_0002_w11_approval.py
apps/control_api/src/flowpilot_control_api/approval.py
apps/control_api/src/flowpilot_control_api/audit.py
apps/control_api/src/flowpilot_control_api/main.py
apps/control_api/src/flowpilot_control_api/models.py
apps/control_api/src/flowpilot_control_api/rbac.py
apps/control_api/src/flowpilot_control_api/repository.py
apps/control_api/src/flowpilot_control_api/risk.py
apps/control_api/src/flowpilot_control_api/schemas.py
apps/control_api/src/flowpilot_control_api/seed.py
apps/control_api/src/flowpilot_control_api/w11_etag.py
apps/control_api/tests/conftest.py
apps/control_api/tests/test_api.py
apps/control_api/tests/test_approval.py
apps/control_api/tests/test_audit.py
apps/control_api/tests/test_migrations.py
apps/control_api/tests/test_rbac.py
apps/control_api/tests/test_repository.py
apps/control_api/tests/test_risk.py

apps/control_web/src/App.css
apps/control_web/src/App.test.tsx
apps/control_web/src/App.tsx
apps/control_web/src/approval.test.ts
apps/control_web/src/approval.ts
apps/control_web/src/auth.test.ts
apps/control_web/src/auth.ts

deploy/compose/compose.yaml
deploy/compose/keycloak/flowpilot-realm.json
tests/integration/Dockerfile
tests/integration/w11_approval_compose_smoke.py
~~~

No dependency is added. Existing Python and frontend manifests and lockfiles
remain byte-identical. The integration image uses its existing locked
dependencies.

## Frozen risk policy

Risk levels are the closed enum `L0`, `L1`, `L2`, `L3`, and `L4`.

| Level | Closed actions | Behavior |
|---|---|---|
| L0 | `inspect_employee`, `inspect_task` | automatic trusted read |
| L1 | `create_draft`, `generate_plan` | automatic and audited |
| L2 | `create_ticket`, `create_account`, `assign_asset`, `create_mailbox`, `transfer_employee`, `close_ticket`, `release_asset` | one active manager |
| L3 | `grant_admin_privilege`, `revoke_account`, `disable_employee`, `disable_mailbox`, `transfer_file_ownership` | one active manager and one different active security user |
| L4 | `physical_delete`, `bypass_approval`, `modify_audit`, `cross_tenant_operation`, `arbitrary_code_execution` | permanently denied |

`create_account` is promoted from L2 to L3 when its organization-qualified
target user is currently an organization administrator. No action can be
downgraded below its frozen level. Unknown action, unknown parameter schema,
unknown risk level, or unclassifiable state fails closed: unknown action is an
L4 denial and a known action with invalid parameters is schema rejection.

Each known action has one strict/frozen/extra-forbid parameter model. Canonical
parameter bytes are sorted-key compact UTF-8 JSON over schema version, closed
action, and validated parameters. The binding is stable SHA-256. Key order
cannot change the hash; any validated value change does.

Risk is computed only from the closed action, validated parameters, current
organization-qualified database facts, and this mapping. Objective, brief,
page, email, PDF, DOM, image, screenshot, OCR, form, model/Planning output,
body/query/header role or risk, JWT role, and caller-supplied actor,
organization, approver, authority, or risk cannot select or lower it.

## Identity, business RBAC, and approval authority

W10 business roles remain exactly `organization_admin`, `operator`, and
read-only `auditor`. Approval roles are exactly `manager` and `security`.
They are independent database facts. A business role never creates approval
authority; approval authority never creates a business permission.

An active authority row binds opaque authority ID, organization ID, user ID,
one approval role, `active|disabled|tombstone`, version, and UTC timestamps.
Only an organization administrator may read/manage authorities in their own
organization. Operators cannot manage them. An auditor cannot decide even if a
malformed seed attempted to grant authority. An organization administrator
without an active authority cannot approve. There is no global or fallback
approver.

`ActorContext` remains internal and is created only from verified fixed OIDC
identity plus current active organization, user, membership, database business
role, and organization-qualified active authority rows. Each protected request
re-resolves these facts. Keycloak role claims only have the existing exact
business-role agreement and never grant manager/security authority.

Authority create starts at version 1. Disable/tombstone requires a strong W11
ETag and exact If-Match, increments exactly once, is organization-qualified,
has no physical delete, and immediately blocks new decisions and unclaimed
grants. Cross-organization and nonexistent authorities have one uniform 404.

## Approval request and decision state machine

Request status is the closed enum `pending`, `approved`, `rejected`,
`cancelled`, `expired`, `invalidated`, `claimed`, `consumed`, and `failed`.
Each request binds schema version, opaque request ID, organization, task, step,
action, canonical parameter hash, frozen risk, requester user, executor user,
ordered required roles, status, version, validity/expiry, UTC timestamps,
closed reason, and audit sequence reference. Requester and executor are derived
from `ActorContext`, never request fields.

The authenticated execution gate behaves as follows:

- L0 is automatically authorized with no approval request;
- L1 is automatically authorized and audited with no approval request;
- L2 creates one pending manager request;
- L3 creates one pending manager-plus-security request;
- L4 and unknown action are permanently denied and audited.

Creation starts at version 1. Approve, reject, cancel, and invalidate require
one exact strong request ETag. Success increments exactly once. Missing
If-Match is 428. Weak, wildcard, multiple, malformed, cross-resource, or stale
input is the same 412 with no current version. Illegal transitions are 409.

Decision rows are immutable and append-only. A row binds opaque decision ID,
organization, request, approved/rejected, approver user and authority,
database-derived approval role, request version, action, parameter hash,
closed reason, UTC timestamp, and audit sequence. No decision update/delete/
replace/reorder route exists, and database triggers reject update/delete.

At decision time the organization, user, membership, authority, request,
action, parameter hash, expiry, and current request version are rechecked in
one transaction. Requester/executor cannot decide their own request. The same
user cannot decide twice or satisfy both L3 roles. A reject is terminal. Final
approval depends on current facts, not cached creation-time authority. Terminal
requests cannot be reactivated. Changed organization, task, step, action, or
parameters requires a new request; old decisions, grant, nonce, and ETag never
migrate.

## One-time grant and durable execution claim

After the exact approval set is complete, Control API creates one grant bound
to organization, request, task, step, action, parameter hash, risk, required-
approval-set hash, executor user, expiry, version, and closed status
`issued|claimed|consumed|revoked|expired|failed`.

The credential uses cryptographically secure randomness. The database stores
only SHA-256 credential and nonce hashes. The raw credential is placed once in
a bounded in-process trusted executor vault keyed by opaque grant ID. It is
never returned by an approval/Web response and never enters URL, query,
Cookie, Local Storage, log, evidence, database plaintext, Temporal history,
Checkpoint, Planning, DOM/Vision/Hybrid Agent, Sandbox page, or Grader.
Process loss discards it and fails closed; it is never reconstructed from a
hash.

The executor claim revalidates active organization, executor user/membership,
all decision authorities/users/memberships, request/grant status and expiry,
task, step, action, canonical parameter hash, approval-set hash, and current
authorization hash. Claim is one conditional organization/request/grant/token-
hash/status/version/not-expired update. Exactly one concurrent claimant wins;
success changes `issued` to `claimed`, sets an opaque durable execution ID and
authorization hash, and increments version exactly once. Failure changes no
version, request, receipt, or business fact and uses one stable non-enumerating
rejection.

Raw credential replay after claim is rejected. Recovery may retain only opaque
request/grant/execution references, authorization hash, parameter hash, closed
status, receipt reference, organization/user opaque IDs, and versions. A
claimed execution resumes only through the identical durable execution claim
and W8 receipt. Completion is trusted receipt-derived, never caller-declared,
and atomically changes grant/request to consumed with audit. Authority disable,
request invalidation, parameter change, or authorization-hash mismatch fails
closed before an effect. W8 retry/recovery/replan/action caps do not increase.

## Tamper-evident audit chain

Audit state exists only in the Control Plane database. Each organization has
one head row and an independent sequence beginning at 1. Each event is
append-only and contains frozen schema version, organization ID, sequence,
opaque event ID, closed event type, UTC timestamp, previous hash, canonical
payload JSON, and event hash. Payload permits only opaque IDs/hashes, closed
actor/authority/role/risk/action/status/reason values, HTTP status, counts,
receipt/grade references, and versions.

Canonical event bytes are sorted-key compact UTF-8 JSON over every event field
except `event_hash`. The genesis previous hash is 64 zeros. Event hash is
SHA-256 of those bytes. Append locks the organization head, allocates exactly
one next sequence, inserts the event, and atomically updates the head. Database
constraints plus update/delete triggers protect event and decision rows.

Verification is organization-qualified and deterministically checks contiguous
sequence, previous hash, recomputed event hash, event count, and exact head.
It detects mutation, deletion, insertion, reorder, broken previous hash,
truncation, duplicate sequence, and forked head. Cross-organization list,
count, head, and verification have uniform non-enumeration. Auditor may read
and verify but never mutate.

Closed events cover `risk_classified`, `l4_denied`, `approval_requested`,
`approval_approved`, `approval_rejected`, `request_cancelled`,
`request_expired`, `request_invalidated`, `grant_issued`, `grant_claimed`,
`grant_consumed`, `grant_rejected`, `execution_started`,
`execution_succeeded`, `execution_failed`, `recovery_resumed`,
`authority_disabled`, and `audit_verified`.

No audit payload contains raw credential/nonce, bearer/ID/refresh token, raw
claim, authorization code, Cookie, password, private key, name, email,
username, page/DOM/image/form/model content, raw action parameter, real
organization data, or machine path. The property is called tamper-evident,
never tamper-proof, blockchain, external timestamping, or legal compliance.

## Transaction order

Within Control Plane, request mutation, immutable decision, grant issue/claim,
and audit append share the same database transaction. A commit cannot contain
a successful decision without its audit event, a grant claim without its
durable execution ID, or an approval mutation whose audit rolled back.

Synthetic business effects and W8 receipts retain the released idempotent
boundary; W11 does not claim a distributed transaction. A trusted completion
uses an existing durable W8 receipt fact and appends execution/audit state. No
caller supplies execution success.

## Minimal Control Web

Control Web retains W10 Authorization Code + S256 PKCE and module-memory token
storage. It adds pending request list/detail, approve/reject using the server
ETag, terminal status display, current actor approval roles, forbidden state,
read-only audit list, and verification result. It never generates, receives,
stores, or displays raw grant/nonce, raw parameters, or OIDC claims. Browser-
visible actor/role/risk/organization data is informational; the server rechecks
all facts.

## Deterministic synthetic matrix

Development contains exactly two synthetic organizations. Each has eight
users/identities/memberships: organization administrator, operator requester/
executor, auditor, active manager, active security, disabled manager user,
active user with disabled security authority, and active user without approval
authority. Each organization has four authority rows: active manager, active
security, manager bound to the disabled user, and disabled security. All IDs
and profiles are opaque synthetic values; no real identity or personal data is
used.

The frozen matrix includes one representative action at each L0-L4 level,
unknown action, parameter change, cross-organization, concurrent claim, and
crash/recovery cases. Development may rerun. Validation may run exactly once
only after this contract, action schemas/mapping, roles, state machine,
parameter hash, expiry, credential/claim transaction, recovery rules, audit
schema/hash, seed, and expected acceptance results are frozen. Evidence records
whether it ran. Reporting remains unexecuted before W15.

## HTTP, tenancy, and migration

Authentication remains 401. A valid actor without business/approval authority
receives 403. Cross-organization and nonexistent tenant resources use the same
404 without count, version, ETag, audit head, or extra lookup disclosure.
Illegal state is 409, bad/stale/mismatched ETag is 412, missing If-Match is
428, and invalid strict schema is 422; all use a stable closed error schema.

Every W11 tenant-owned key, foreign key, unique constraint, index, read, count,
and mutation is organization-qualified. No global read followed by Python
filtering exists. No physical delete route exists. W11 tables are added only
to Control Plane. Sandbox and Temporal schemas receive no approval or audit
table, column, or foreign key.

Control revision `20260729_0002` is forward and reversible and must pass empty
upgrade, current, check, downgrade to W10, second upgrade, constraint/index/
trigger inspection, and transaction rollback. Released Sandbox migration bytes
remain identical and Sandbox head remains `20260728_0003`.

## Acceptance and evidence

Tests cover every risk action and fail-closed input; parameter canonicalization;
database-fact promotion; full authority allow/deny/revocation/tenant matrix;
self/executor approval; separation of duties; request ETags/transitions/
concurrency/expiry/invalidation; grant hash-only persistence, wrong bindings,
expiry/revocation/replay, one-winner claim, no failed side effect; durable
claim/recovery checks; L0-L4 execution behavior; audit genesis/sequence/hash/
concurrency/tamper matrix; migration round-trip; sensitive-field scan; and all
W1-W10 regression gates.

Compose retains fixed local Keycloak, separate Control/Sandbox/Temporal
databases, and Planning isolation. It adds one `approval-acceptance-smoke`
profile/service and runs W11 last in the consolidated W4-W11 job. It always
cleans project containers, networks, and volumes. W11 adds no separate CI
runner job or action dependency.

Evidence contains only versions, hashes, opaque synthetic IDs, closed codes,
HTTP statuses, counts, independent grades, call/cost zeros, run IDs, and tool
availability. It records the single Validation decision and Reporting false.
It never claims production enterprise approval, security compliance, legal
audit, load, availability, SLO, or ROI.

## CI quota, Git, and W12 boundary

The maintenance concurrency, main-push minimal jobs, ten PR quality jobs,
Dependabot heavy-Compose skip, one consolidated regression, secret scan, and
stable Required CI gate remain unchanged except W4-W10 becomes W4-W11. No
remote run is triggered during local work. If future delivery is authorized,
diagnose first, group fixes, push once, and rerun failed jobs only when code,
locks, migrations, Compose, and workflow are unchanged. Never rerun all,
successful, or superseded jobs; never force-push, create empty commits or
duplicate PRs, weaken tests, or bypass approval enforcement.

Local completion requires every application locked sync/quality/test gate,
both frontend gates, Control migration round-trip, Sandbox migration freeze,
W3/W7/W9/W10 freezes, W4-W11 Compose smokes, risk/approval/grant/audit matrix,
independent Joiner/Mover/Leaver grade 100, `finished_ungraded`, Reporting-not-
run proof, exact allowlist, secret, diff, status, staged/unstaged, and cleanup
audits. Unavailable tooling is recorded, never treated as passed.

After all locally available gates pass and evidence matches observations,
explicitly stage only exact W11 allowlist paths, create one local W11 feature
commit, and stop. Do not push, create a W11 PR, merge, tag, create a Release,
rerun CI, dispatch a workflow, call a real provider, or begin W12 without
separate user authorization. A later authorized W11 tag is `w11-approval`;
W11 creates no Release.
