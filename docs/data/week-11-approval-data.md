# W11 risk, approval, grant, and audit freeze

## Baseline and realm

- W10 merge/tag: `9bbb0303c6bc795468b094df676a86dfcbc69dcb` / `w10-identity`
- Maintenance baseline: `b90cd44ec440eef2d69f12d03890bae57c845e37`
- Control migration head: `20260729_0002`
- Sandbox migration head: immutable `20260728_0003`
- Keycloak: `26.3.2`, realm/client/realm roles/users = 1 / 1 / 3 / 16
- Realm import SHA-256:
  `b0f11d87a0cce0c78eb324035870060cd675e5134364c85a421f03fd024f1e53`

The realm contains only fixed synthetic `.invalid` profiles and disposable
local credentials. All 10 added W11 identities retain business role `operator`;
manager/security authority is not a realm or JWT role.

## Synthetic Control Plane matrix

| Object | Total | Per organization |
|---|---:|---:|
| organizations | 2 | 1 |
| users / OIDC identities / memberships | 16 / 16 / 16 | 8 / 8 / 8 |
| approval authorities | 8 | 4 |
| active manager / active security | 2 / 2 | 1 / 1 |
| authority on disabled manager user | 2 | 1 |
| disabled security authority | 2 | 1 |
| active no-authority users | 2 | 1 |

Each organization has one administrator, requester/executor, auditor, active
manager, active security, disabled manager user, active user with disabled
security authority, and active no-authority user. IDs are opaque synthetic
values. No real identity, account, organization, email, approver, or personal
data is used.

## Closed action and parameter catalog

| Risk | Actions | Required approval |
|---|---|---|
| L0 | `inspect_employee`, `inspect_task` | automatic read |
| L1 | `create_draft`, `generate_plan` | automatic, audited |
| L2 | `create_ticket`, `create_account`, `assign_asset`, `create_mailbox`, `transfer_employee`, `close_ticket`, `release_asset` | one manager |
| L3 | `grant_admin_privilege`, `revoke_account`, `disable_employee`, `disable_mailbox`, `transfer_file_ownership` | manager + distinct security |
| L4 | `physical_delete`, `bypass_approval`, `modify_audit`, `cross_tenant_operation`, `arbitrary_code_execution` | permanently denied |

Counts are L0/L1/L2/L3/L4 = 2/2/7/5/5. `create_account` is promoted from L2
to L3 when the current organization-qualified target user is an organization
administrator. Unknown action is L4. Invalid/extra known parameters are schema
rejection. There is no downgrade or L4 override.

Each action validates one of these frozen parameter shapes: employee reference;
task reference; employee plus ticket/account/asset/mailbox/destination code;
target user plus account/permission code; employee mutation; source reference
plus target user; or empty forbidden parameters. Canonical binding bytes are
compact sorted-key UTF-8 JSON over binding schema, closed action, and validated
parameter object. SHA-256 is stable under input key reorder and changes with a
validated value.

## Approval and grant freeze

- Approval roles: `manager`, `security`.
- Request states: `pending`, `approved`, `rejected`, `cancelled`, `expired`,
  `invalidated`, `claimed`, `consumed`, `failed`.
- Decision values: `approved`, `rejected`; reason values:
  `policy_satisfied`, `policy_rejected`, `requester_cancelled`,
  `parameters_changed`, `authority_inactive`, `request_expired`.
- Request TTL: 10 minutes. Grant TTL: 2 minutes maximum and capped by request.
- Grant states: `issued`, `claimed`, `consumed`, `revoked`, `expired`, `failed`.
- Raw credential: secure random token plus nonce in bounded process memory.
  Durable values: SHA-256 token/nonce hashes only.
- Claim binding: organization, request/grant, token/nonce hashes, status,
  version, task, step, action, parameter hash, approval-set hash, executor,
  authorization hash, and not-expired condition.
- Strong ETag form:
  `"w11-<authority|approval-request>-<24 lowercase hex fingerprint>-v<version>"`.

## Audit freeze

One organization-qualified head stores `head_sequence` and `head_hash`.
Events are immutable and include schema, opaque ID, organization, contiguous
sequence, closed event type, previous hash, event hash, payload hash, and UTC
time. Event types are:

~~~text
risk_classified, l4_denied, approval_requested, approval_approved,
approval_rejected, request_cancelled, request_expired, request_invalidated,
grant_issued, grant_claimed, grant_consumed, grant_rejected,
execution_started, execution_succeeded, execution_failed, recovery_resumed,
authority_disabled, audit_verified
~~~

The event hash binds canonical schema version, organization, sequence, event
type, opaque actor/subject references, previous hash, payload hash, and time.
Genesis uses 64 zeroes. Verification checks every sequence/previous/event hash
and final head. Database triggers reject decision/event update and delete.

## Frozen Compose acceptance expectations

The clean W11 smoke runs after W4-W10 and expects: 4 representative risk allows
(L0-L3), 2 risk denials (L4 plus unknown), 1 schema rejection, 4 approval
requests, manager approve/reject 3/1, security approve 1, self rejection 1,
inactive/missing authority rejection 3, cross-organization rejection 1,
parameter invalidation 1, grants issued/claimed/rejected 3/2/5, concurrent
exactly-one-winner true, pre-approval/duplicate effects 0/0, exactly 37 new
audit events, a 64-lowercase-hex head, valid verification, sensitive scan pass,
real IdP/model calls 0, cost 0, and Reporting false.

`W11_EVALUATION_SPLIT` is a closed acceptance-only value: `development` by
default or `validation` for the single final run. It changes only the emitted
`validation_run` observation and cannot alter identity, risk, approval, grant,
audit, side effects, or expected counts.

Development may rerun. Validation runs exactly once after this freeze. Audit
IDs/timestamps and therefore the observed head hash are runtime opaque values;
the expected hash contract is the verified canonical 64-hex chain property,
not a preselected constant.

## Preserved freezes

W3 remains 10 tasks, 6/2/2 split, checksum
`e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9`.
W7 remains 30 templates/90 instances, 18/6/6 split, catalog
`62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f`, split
`1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee`, and
Reporting
`c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6`.
W9 remains 9 records with catalog
`4d63a24a57a54f9f7d94abe6b98d34453525dde13a6b100e336c8442c68bfb15`, five
frozen ablations, and unchanged J/M/L results. W10 issuer/RBAC/tenant/ETag/
locking behavior remains unchanged. Reporting is not executed before W15.
