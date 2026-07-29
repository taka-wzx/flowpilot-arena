# W10 threat model - OIDC, RBAC, Tenant Isolation, and Optimistic Locking

## Scope and assets

W10 protects the fixed local OIDC trust roots; bearer and JWKS verification;
organization/user/identity/membership state; database-derived ActorContext;
closed roles and permissions; tenant-owned records, counts, versions, and
ETags; durable organization memory; atomic conditional writes; W9 safe context
projection; raw token/claim/personal-data exclusion; and all released W1-W9
security, recovery, context, and independent-grading boundaries.

## Trust boundaries

~~~mermaid
flowchart LR
    Browser["Local browser"] -->|"Code + PKCE"| KC["Fixed local Keycloak"]
    Browser -->|"Bearer token"| API["Control API"]
    KC -->|"Pinned internal JWKS"| API
    API --> DB["Control identity database"]
    Untrusted["Body/query/page/DOM/image/OCR/model text"] -->|"data only"| API
    API -->|"closed safe projection"| Context["W9 context boundary"]
    Planning["Planning Agent"] --> Worker["Browser Worker"]
    Grader["Independent Grader"] --> Sandbox["Sandbox database"]
~~~

## Threats and controls

| Threat | W10 control | Remaining limitation |
|---|---|---|
| Request selects issuer/JWKS/algorithm | Values are frozen deployment policy; strict URL/host/path/algorithm validation; no per-request field | Only one local deterministic issuer is evaluated |
| `alg=none`, confusion, bad key/signature, unknown `kid` | RS256-only header/key agreement, RSA signing-use checks, exact `kid`, bounded fail-closed JWKS refresh | Key rotation is tested locally, not against a production IdP |
| Replayed/invalid token enters tenant lookup | Exact issuer/audience/client/subject/exp/nbf/iat/type validation before repository access | W11 session/approval replay controls remain deferred |
| Bearer or claim leakage | Header-only token input; no access logs; strict safe schemas/evidence; no token/claim/code/cookie persistence | Browser token exists in module memory during its session |
| JWT role grants authority | Database active membership is authoritative and must exactly match the closed claim | Realm provisioning is deterministic synthetic data |
| Disabled identity keeps access | Active organization/user/identity/membership re-resolved on every request | Production cache invalidation is not exercised because no auth cache exists |
| Body/page/model injects actor/org/role | ActorContext cannot be request-deserialized; extras are forbidden; organization and permissions are database-derived | Safe synthetic values remain data, never authorization |
| Global or fallback tenant bypass | No global admin/wildcard/impersonation; no default/first/caller-scope fallback | Cross-tenant support workflows are deliberately absent |
| Cross-organization get/list/count | SQL is organization-qualified before object/count/version lookup; uniform 404 | Database administrator compromise is outside W10 |
| Cross-organization create/update/disable/reset | Owner/target derived from ActorContext; atomic predicates include organization | Only fixed synthetic tenants are evaluated |
| Object existence leaks through error/ETag/version | Cross-org and nonexistent share response; mismatch stops before lookup; no current version in 412 | Network timing side-channel analysis is deferred |
| Last-write-wins loses an update | Required strong If-Match and atomic organization/resource/expected-version SQL | Multi-region conflict resolution is outside W10 |
| Stale write causes partial effects | Single transaction, zero-row failure, rollback, no version/side-effect increase | Production failover behavior is not evaluated |
| Concurrent same-version writes both win | Conditional mutation; PostgreSQL test requires exactly one winner | Load-scale contention testing is W12 |
| Delete destroys identity/history | Active/disabled and active/tombstone states; `RESTRICT` FKs; no physical-delete route | Long-term retention policy is not defined in W10 |
| W9 synthetic scope becomes auth | W10 dependencies never accept W9 scope; new projection uses verified ActorContext only | W9 fake store remains for frozen regression |
| Token/identity enters Planning/Temporal/Sandbox | Closed projection excludes token/claims/personal fields; no network/DB route; W8 persists no semantic W10 data | Production distributed identity propagation is deferred |
| Auth failure expands Agent budget | Authorization stops before W9/W6-W8 execution and cannot raise any cap | End-user retry UX is intentionally minimal |

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
  memory scope, tool, action, budget, approval, recovery, or success.
- `finished_ungraded` is never interpreted as success; only the independent
  Sandbox database-fact Grader decides task outcome.

## Deferred threats

W11 approvals/HITL/risk/audit; W12 production scheduling, rate limiting,
backpressure, load and `v0.3.0`; W13 telemetry; W14 malicious-page and full
prompt-injection suite; W15 external benchmark/Reporting; W16 deployment; real
enterprise identity providers/accounts/data; SAML/SCIM/LDAP/MFA/passkeys;
multi-provider discovery; global support roles; and production incident/break-
glass operation remain outside W10.
