# Week 11 implementation plan - HITL, risk, approval, and audit

## Authority and stop condition

Work only on `week/11-approval` from maintenance baseline
`b90cd44ec440eef2d69f12d03890bae57c845e37`, preserving W10 merge/tag
`9bbb0303c6bc795468b094df676a86dfcbc69dcb` / `w10-identity`. Exact path
authority is `docs/agent-contract.md`. Complete one local W11 commit and stop
before W12; no push, PR, merge, tag, Release, CI dispatch/rerun, or real
provider call is authorized.

## Frozen outcomes

| Area | W11 outcome | Deliberate limit |
|---|---|---|
| Risk | Closed strict 2/2/7/5/5 L0-L4 catalog plus one DB-fact promotion | No DSL, ABAC, caller/model override |
| Authority | Organization-local manager/security rows independent from business RBAC | No global/fallback approver |
| HITL | L2 manager; L3 distinct manager + security; self denial | No quorum/workflow framework or L4 approval |
| Lifecycle | Versioned request, immutable decision, strong ETag transitions | No physical delete or approval migration |
| Grant | Hash-only, short-lived, one-time, parameter/executor bound | Raw value only in bounded Control API memory |
| Recovery | Durable execution reference plus released W8 receipt | No W12 worker/API production split |
| Audit | Per-org append-only canonical SHA-256 chain and verification | Tamper-evident, not tamper-proof/compliance |
| Web | Minimal role/request/detail/decision/audit views | No grant/nonce/raw parameter display |
| Evaluation | Unit/API/PostgreSQL/Web/Compose synthetic matrix | One final Validation; Reporting not executed |

## Implementation phases

1. Verify W10/maintenance/PR/run/Release facts, create the exact local branch,
   and replace the contract/allowlist before any other edit.
2. Freeze the action catalog, strict parameter schemas, canonical hash,
   database-fact promotion, approval roles, state machine, expiry, grant,
   recovery, audit schema, seed, and expected acceptance counts.
3. Add Control revision `20260729_0002`, organization-qualified models,
   constraints/indexes/triggers, seed rows, and repository/ActorContext support.
4. Implement L0/L1 automatic audit, L4 denial, L2/L3 request/decision rules,
   strong ETags, immutable decisions, one-time vault/grants, one-winner claim,
   durable resume/completion, revocation, and audit append/verify.
5. Add authenticated APIs and minimal Control Web views while preserving raw
   credential, token, claim, and raw parameter exclusion.
6. Expand only the local synthetic realm, add one W11 acceptance service, and
   extend the existing consolidated W4-W10 CI job to W4-W11 with W11 last.
7. Update architecture, threat, evaluation, data, ADR, README, changelog,
   roadmap, AGENTS, and evidence.
8. Run all app/frontend/migration/freeze/Compose/security/path/cleanup gates;
   after the design and expectations are frozen, run Validation exactly once.
9. Reconcile evidence, audit staged/unstaged exact paths, explicitly stage only
   the allowlist, create one local W11 commit, and stop.

## Frozen limits

- Request TTL: 10 minutes; issued grant TTL: at most 2 minutes and never beyond
  the request expiry; process vault capacity is bounded.
- Request/authority create version: 1; every successful mutation exactly +1.
- Claim key: organization + request/grant + token/nonce hashes + expected
  status/version + task + step + action + parameter hash + executor + expiry.
- Audit chain: one head per organization, contiguous sequence from 1, canonical
  SHA-256, immutable decisions/events, no update/delete.
- Synthetic data: 2 organizations; 16 users/identities/memberships; 8
  authorities; no real identity/account/personal data.
- No W6-W10 budget, retry, recovery, action, grading, catalog, split, context,
  ablation, OIDC, tenant, ETag, or task-success rule changes.

## Validation and handoff

Development matrices may rerun. Validation runs once only after the final code,
realm checksum, migration, seed, Compose script, expected counts, and docs are
frozen. Reporting remains unexecuted. The final handoff reports every local
gate, unavailable tool, cleanup count, exact path count, local commit, remote
non-actions, tag/Release state, and the W12 stop boundary.
