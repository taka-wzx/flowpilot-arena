# W12 threat model - production admission, fenced Worker, and bounded load

## Scope and assets

W12 preserves the fixed local OIDC trust roots, bearer/JWKS verification,
tenant isolation, optimistic locking, closed W11 risk/approval/grant policy,
raw one-time credential boundary, W8 receipt/recovery semantics, and
organization-local audit chains. It additionally protects production run and
idempotency bindings; bounded outbox capacity; persistent rate buckets;
organization-fair scheduler metadata; lease owner/version/fence state;
deterministic workflow identity; the private Workflow Worker boundary; four
browser slots; and load/result artifacts. It continues to protect
organization/user/identity/membership state; database-derived ActorContext;
closed roles and permissions; tenant-owned records, counts, versions, and
ETags; durable organization memory; atomic conditional writes; W9 safe context
projection; raw token/claim/personal-data exclusion; and all released W1-W10
security, recovery, context, and independent-grading boundaries.

## Trust boundaries

~~~mermaid
flowchart LR
    Browser["Local browser"] -->|"Code + PKCE"| KC["Fixed local Keycloak"]
    Browser -->|"Bearer token"| API["Control API"]
    KC -->|"Pinned internal JWKS"| API
    API --> DB["Control database\nidentity + approval + run/outbox"]
    API --> Policy["Closed L0-L4 risk policy"]
    Policy --> Approval["Approval state machine"]
    Approval --> DB
    API --> Audit["Per-organization audit chain"]
    Audit --> DB
    DB --> W["Private Workflow Worker\nfour slots + fence"]
    W --> Temporal["Temporal / W8 recovery"]
    Untrusted["Body/query/page/DOM/image/OCR/model text"] -->|"data only"| API
    API -->|"closed safe projection"| Context["W9 context boundary"]
    Planning["Planning Agent"] --> Worker["Browser Worker"]
    Grader["Independent Grader"] --> Sandbox["Sandbox database"]
~~~

## Threats and controls

| Threat | W12 control | Remaining limitation |
|---|---|---|
| Request selects issuer/JWKS/algorithm | Values are frozen deployment policy; strict URL/host/path/algorithm validation; no per-request field | Only one local deterministic issuer is evaluated |
| `alg=none`, confusion, bad key/signature, unknown `kid` | RS256-only header/key agreement, RSA signing-use checks, exact `kid`, bounded fail-closed JWKS refresh | Key rotation is tested locally, not against a production IdP |
| Replayed/invalid token enters tenant lookup | Exact issuer/audience/client/subject/exp/nbf/iat/type validation before repository access | Production session revocation remains outside the local issuer |
| Bearer or claim leakage | Header-only token input; no access logs; strict safe schemas/evidence; no token/claim/code/cookie persistence | Browser token exists in module memory during its session |
| JWT role grants authority | Database active membership is authoritative and must exactly match the closed claim | Realm provisioning is deterministic synthetic data |
| Disabled identity keeps access | Active organization/user/identity/membership re-resolved on every request | Production cache invalidation is not exercised because no auth cache exists |
| Body/page/model injects actor/org/role | ActorContext cannot be request-deserialized; extras are forbidden; organization and permissions are database-derived | Safe synthetic values remain data, never authorization |
| Global or fallback tenant bypass | No global admin/wildcard/impersonation; no default/first/caller-scope fallback | Cross-tenant support workflows are deliberately absent |
| Cross-organization get/list/count | SQL is organization-qualified before object/count/version lookup; uniform 404 | Database administrator compromise is outside W12 |
| Cross-organization create/update/disable/reset | Owner/target derived from ActorContext; atomic predicates include organization | Only fixed synthetic tenants are evaluated |
| Object existence leaks through error/ETag/version | Cross-org and nonexistent share response; mismatch stops before lookup; no current version in 412 | Network timing side-channel analysis is deferred |
| Last-write-wins loses an update | Required strong If-Match and atomic organization/resource/expected-version SQL | Multi-region conflict resolution is outside W12 |
| Stale write causes partial effects | Single transaction, zero-row failure, rollback, no version/side-effect increase | Production failover behavior is not evaluated |
| Concurrent same-version writes both win | Conditional mutation; PostgreSQL test requires exactly one winner | Load-scale contention testing is W12 |
| Delete destroys identity/history | Active/disabled and active/tombstone states; `RESTRICT` FKs; no physical-delete route | Long-term retention policy is not defined in W11 |
| W9 synthetic scope becomes auth | W10 dependencies never accept W9 scope; new projection uses verified ActorContext only | W9 fake store remains for frozen regression |
| Token/identity enters Planning/Temporal/Sandbox | Closed projection excludes token/claims/personal fields; no network/DB route; W8 persists no semantic W10 data | Production distributed identity propagation is deferred |
| Auth failure expands Agent budget | Authorization stops before W9/W6-W8 execution and cannot raise any cap | End-user retry UX is intentionally minimal |
| Page/model/caller lowers risk | Closed action-specific schemas plus server mapping and current tenant facts; unknown/unclassifiable is L4 | Only the frozen synthetic action catalog is evaluated |
| JWT/business role grants approval | Active organization-qualified authority row is independent of business role and re-resolved at decision/claim/resume | Enterprise approver provisioning is not evaluated |
| Requester or executor approves self | Actor IDs are database-derived and both identities are rejected before decision append | Delegation and substitute approvers are absent |
| One user satisfies both L3 roles | L3 approved decision set requires distinct manager/security users | Larger quorum workflows are deliberately absent |
| Inactive authority remains effective | User, membership, organization, authority and authorization hash are rechecked; disable revokes unclaimed grants | No distributed cache exists in W11 |
| Parameter/task/action substitution | Request, decision, grant, claim, recovery, and receipt references bind canonical hashes and closed identifiers | No arbitrary browser/API action is authorized |
| Grant plaintext leaks or replays | Raw credential is bounded to process memory; DB stores hashes; Web/log/evidence/Temporal/Checkpoint exclusion; atomic claim | Process-memory compromise is outside this synthetic evaluation |
| Concurrent consumers both win | One conditional organization/request/grant/status/version/expiry transaction plus locked vault take | Load-scale contention belongs to W12 |
| Recovery replays credential/effect | Durable execution claim plus W8 receipt/idempotency; active-state and authorization-hash recheck | Production worker handoff is deferred to W12 |
| Audit event is edited/deleted/inserted/reordered | Append-only DB triggers, per-org locked head/sequence, canonical previous/event hashes, genesis-to-head verification | A database administrator can still destroy storage; chain is tamper-evident, not tamper-proof |
| Cross-organization audit head leaks | Audit list/head/verify SQL and responses are organization-qualified with uniform 404 | Network timing analysis remains deferred |
| API request directly starts Browser/Planning | Public API commits run/outbox and returns 202; only private Worker reaches Temporal; no production compatibility bypass | Local Compose has one Worker service |
| Raw approval material crosses handoff | Grant hash verification and claim stay in Control API vault transaction; Worker receives opaque execution/request/grant references and hashes only | Control API process-memory compromise is not evaluated |
| Crash leaves claimed grant without dispatch | Grant claim, execution reference, run transition, outbox insert, partition update, and audit append share one transaction; vault removal is post-commit | Full database disaster recovery is outside W12 |
| Idempotency key replays or crosses tenant | Database stores key hash under organization+actor; same body returns one run, mismatch is 409, and no key grants authority | Client-side retry policy is minimal |
| Caller selects queue/priority/Worker | Strict create schema forbids those fields; scheduler is locked deterministic organization round robin | No weighted fairness or autoscaling |
| Queue exhaustion causes partial admission | Locked 64 global/32 organization capacity and insert are atomic; 503 has bounded Retry-After and no run/outbox/claim effect | Fixed local capacity is not a production sizing claim |
| Forwarded/IP headers bypass limits | Buckets derive only from verified ActorContext, organization, and fixed route class; forwarded headers are ignored | Multi-instance limiter throughput is not evaluated |
| Limiter race overspends tokens | Persistent locked integer-microtoken actor and organization buckets commit atomically; unavailable limiter fails closed | One Control PostgreSQL is evaluated |
| Two Workers claim one item | Conditional locked claim creates one active lease winner and increments the fence | Delivery remains at-least-once |
| Expired Worker commits heartbeat/result | All later writes bind organization/run/outbox/owner/version/fence; stale writes affect zero rows and may be safely audited | Host clock discipline is local synthetic only |
| Redelivery duplicates workflow/effect | Same run derives one deterministic Temporal workflow ID; W8 receipt/idempotency converges business effect to at most one | Distributed exactly-once is not claimed |
| Worker bypasses current approval | Effect boundary locks and rechecks organization, executor, membership, request/grant/decision/authority, expiry, hashes, cancellation, and fence | Real enterprise authority provisioning is absent |
| Fifth Browser task exceeds isolation | One Worker service owns a four-slot semaphore; extra work remains queued/backpressured; every W8 run creates fresh context/session/page | Recommended-hardware result is local synthetic evidence |
| Load container gains database/Worker power | Smoke/load join public Control/identity/synthetic networks only, use no DB DSN, Docker socket, raw grant, or Worker endpoint | Test clients still hold local synthetic bearer tokens in memory |
| Result is tuned or rerun after failure | Profile/schema hashes and values freeze first; guard is exclusive before setup; ordinals 1 and 2 are preserved and the explicitly authorized ordinal-3 replacement is the final formal run; cleanup is observed before result sealing | No ordinal 4 run is authorized |

## Fail-closed rules

- Missing/malformed/multiple Authorization, unknown schema/field/role/
  permission/status, invalid JWKS/key/token, inactive identity state, or token-
  membership role mismatch is rejected before a protected operation.
- Unknown/mismatched organization IDs are not authority. Repository reads,
  counts, and mutations always include the ActorContext organization.
- Unknown permission or route mismatch defaults to deny. Auditor writes and
  operator membership management are rejected.
- Missing If-Match stops with 428. Weak, wildcard, malformed, cross-resource,
  cross-organization, and stale ETags stop with the same 412 and no side effect.
- Disable/tombstone/reset never becomes physical deletion and never crosses an
  organization boundary.
- Human prose, objective, page/email/PDF/DOM/image/OCR/form/model output cannot
  choose identity, actor, tenant, role, permission, owner, expected version,
  memory scope, tool, action, risk, approver, grant, budget, approval, recovery,
  audit hash, or success.
- Unknown action/risk/parameter state is never approvable. L4 has no override.
  L2/L3 cannot execute before the exact current approval set is satisfied.
- Request/decision/grant/audit rows are never physically deleted. Stale,
  expired, revoked, wrong-binding, wrong-executor, replayed, or cross-tenant
  grants have no business receipt or side effect.
- Rate rejection is 429 and capacity/dependency rejection is 503 with bounded
  Retry-After. Neither returns bucket tokens, queue depth, another tenant's
  wait, current version, ETag, or Worker identity.
- Terminal run states never reactivate. A stale fence, changed authorization,
  invalid effect binding, unknown action, L4, or incomplete approval has zero
  Browser budget and zero business side effect.
- `finished_ungraded` is never interpreted as success; only the independent
  Sandbox database-fact Grader decides task outcome.

## Deferred threats

W13 telemetry, production dashboards and trace replay; W14 malicious-page and
full prompt-injection suite; W15 external benchmark/Reporting; W16 Helm/cloud
deployment; real enterprise identity providers/accounts/data; SAML/SCIM/LDAP/
MFA/passkeys;
multi-provider discovery; global support roles; and production incident/break-
glass operation remain outside W12.
