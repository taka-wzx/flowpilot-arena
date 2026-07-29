# Week 10 plan - OIDC, RBAC, Tenant Isolation, and Optimistic Locking

## Objective

Preserve W1-W9 and add the smallest deterministic local OIDC boundary,
independent Control identity persistence, database-derived closed RBAC,
authenticated two-organization isolation, atomic strong-ETag writes, durable
authorized organization memory, and minimal Control Web PKCE experience. Exact
authority is `docs/agent-contract.md`.

## Frozen outcomes

| Area | W10 outcome | Deliberate limit |
|---|---|---|
| OIDC | One pinned Keycloak issuer/JWKS/audience/client/RS256 policy | No real/dynamic/multi-provider identity |
| Identity | Separate organizations/users/identities/memberships database | No Control data in Sandbox/Temporal |
| RBAC | Database-derived three-role closed permission matrix | No global admin, ABAC, wildcard, impersonation |
| Tenancy | Organization-qualified schema/repository/error semantics | Two synthetic organizations only |
| Locking | Strong ETag + required If-Match + atomic conditional SQL | No last-write-wins or generic event store |
| Memory/context | Durable authorized memory and safe projection | Released W9 fake path unchanged |
| Web | Login/callback/logout/current identity/forbidden with PKCE | No W11 approval or W12 admin console |
| Evaluation | Unit/API/PostgreSQL/Compose synthetic matrices | No Validation by default or Reporting execution |

## Implementation phases

1. Verify official W9 main/PR/CI/tag/Release state; create
   `week/10-identity` from exact main; freeze W10 contract and exact allowlist
   before application, migration, Compose, workflow, or lock changes.
2. Add strict OIDC config, token/JWKS verifier, closed authentication errors,
   database models/Alembic, deterministic seed, and ActorContext resolution.
3. Add closed roles/permissions, route authorization, organization-qualified
   repositories and response schemas, non-enumeration, disable/tombstone, and
   durable organization-memory lifecycle.
4. Add strong ETag encoding/parsing, required preconditions, atomic conditional
   mutations, rollback, memory collection reset, and SQLite/PostgreSQL
   exactly-one-winner tests.
5. Add authorized safe context projection without changing W9 Planning/fake
   behavior or any W8 recovery/task-success boundary.
6. Add Control Web Authorization Code + S256 PKCE/state/nonce flow, exact
   URI/origin allowlists, module-memory tokens, and minimal identity states.
7. Add pinned Keycloak/Control PostgreSQL Compose services, frozen realm import,
   W10 identity acceptance, and exactly one CI job while preserving triggers.
8. Update architecture, threat, evaluation, data, README, changelog, roadmap,
   AGENTS, ADR, and evidence.
9. Run all Python/frontend/migration/freeze/Compose/security/diff/path/cleanup
   gates, freeze observed evidence, explicitly stage exact allowlist paths,
   create one local W10 commit, and stop before W11.

## Frozen identity and concurrency limits

- Issuer/audience/client/algorithm: one exact contract-defined tuple.
- JWKS: one initial fetch, at most one bounded refresh, fixed timeout, no
  redirect, unknown-key fallback, request-provided URL, or arbitrary host.
- Dataset: 2 organizations; 6 users; 6 identities; 6 memberships; one
  organization administrator, operator, and auditor per organization.
- Every request re-resolves active organization/user/identity/membership and
  exact role agreement; no authorization cache or fallback.
- Initial version 1; successful mutation exactly +1; one strong ETag; one
  required If-Match; no wildcard/weak/multiple precondition.
- Mutation key: organization ID + resource ID + expected version in one
  transaction. Same-version concurrent writes: exactly one winner.
- No W6-W9 action/model/token/image/context/recovery cap changes.

## Handoff boundary

W10 stops after deterministic local evidence and one local commit. Default
delivery does not push, create a PR, merge, tag, Release, trigger remote CI,
backfill a W9 tag, run Validation, execute Reporting, call a real identity or
model provider, or begin W11.
