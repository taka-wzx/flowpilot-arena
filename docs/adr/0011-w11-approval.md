# ADR 0011: closed risk, one-time approval, and tamper-evident audit

- Status: accepted for W11
- Date: 2026-07-29
- Branch: `week/11-approval`
- Baseline: W10 `9bbb0303c6bc795468b094df676a86dfcbc69dcb`

## Context

W10 established a fixed local OIDC resource server, database-derived business
RBAC, tenant-qualified repositories, and strong optimistic locking. W11 must
gate higher-risk synthetic actions with human approval while preserving every
released Browser/Planning/Recovery/Sandbox/Grader boundary. It must not add the
W12 production API/Worker split, dynamic policy language, global approver,
break-glass path, physical deletion, real account/data/provider, or Reporting
execution.

The main risks are authority injection from JWT/page/model input, approving a
different parameter set than the one executed, requester self-approval,
insufficient or stale authority, grant replay/concurrent consumption, recovery
duplicating an effect, cross-tenant enumeration, raw credential leakage, and
silent modification of approval/execution history.

## Decision

1. Use one code-defined closed 21-action catalog and strict action-specific
   Pydantic schemas. Trusted server code maps 2/2/7/5/5 actions to L0-L4 and may
   only promote `create_account` from L2 to L3 using an organization-qualified
   current database fact. Unknown action is L4; invalid known parameters are a
   schema rejection.
2. Keep `manager` and `security` as closed approval authorities in Control
   PostgreSQL, separate from W10 business roles and all JWT claims. L2 requires
   one active manager. L3 requires an active manager and a different active
   security user. Requester/executor cannot decide their own request.
3. Persist organization-qualified versioned requests and immutable decisions.
   Strong ETags bind mutable request/authority identity and version. Every
   decision re-resolves organization, user, membership, business permission,
   authority, expiry, prior decisions, and request state.
4. On the final required approval, generate a cryptographically random token
   plus nonce. Persist only their SHA-256 hashes and keep the raw combined value
   in a bounded process-memory `TrustedGrantVault`. Never return raw material
   through the public API or place it in Web, URL, storage, log, evidence,
   Temporal, Checkpoint, Planning, Sandbox, or Grader data.
5. Claim in one transaction using organization, request/grant, hashes, status,
   version, task, step, action, parameter hash, executor, active approval set,
   authorization hash, and expiry. A durable execution ID authorizes recovery;
   released W8 receipt/idempotency completes the effect. Concurrent claim has
   exactly one winner.
6. Store a separate per-organization audit head and immutable append-only
   events in Control PostgreSQL. Allocate sequence/head under transaction,
   hash canonical sorted-key UTF-8 JSON with the previous hash, and verify from
   genesis to head. Database triggers reject update/delete.
7. Keep the trusted W11 execution gate inside Control API for this week.
   Planning, Browser Worker, and Recovery Worker source and network/database
   capabilities remain unchanged. This is the minimum closed boundary and does
   not pre-implement W12's production worker split.

## Alternatives rejected

- JWT/Keycloak manager roles: token claims are not current organization-local
  business facts and would couple identity provisioning to approval authority.
- Caller/model-selected risk or a rules engine: this creates downgrade and
  injection paths and exceeds the frozen action catalog.
- Persisting encrypted/raw approval credentials: W11 requires hash-only durable
  state and no replayable credential in history or storage.
- Letting Browser/Recovery query Control PostgreSQL: this violates service and
  credential isolation; durable opaque references are sufficient.
- Reusing Sandbox/Temporal for approval/audit: these stores have separate
  ownership, reset, grading, and recovery purposes.
- A global append-only log or blockchain: tenant head/count leakage, needless
  scope, and misleading tamper-proof/compliance claims.

## Consequences

The design is deliberately finite and testable. Authorization revocation and
parameter changes fail closed, approvals cannot migrate to a new request, raw
grant material is not recoverable after process loss, and the database retains
all business identity/approval/audit rows without physical deletion. The audit
chain can detect tampering but cannot prevent a privileged database operator
from destroying storage. Production worker availability, distributed grant
handoff, load, telemetry, malicious-page evaluation, and external Reporting
remain future-week work.
