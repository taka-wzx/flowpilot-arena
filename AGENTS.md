# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is a production-oriented computer-use Agent project paired
with a separate resettable synthetic evaluation environment. The authoritative
roadmap is `docs/project-roadmap.md`; exact current authority is
`docs/agent-contract.md`.

This branch is W10: OIDC, Organization/User, RBAC, Tenant Isolation, and
Optimistic Locking on `week/10-identity`, based on released W9 main commit
`5e1868d30da70c2d8cd9db1705db0cb8f7dabfac`. W9 PR #31 and both 18-job PR and
post-merge main CI runs passed on their first attempts. No W9 tag exists; the
current release remains `v0.2.0 - Hybrid + Recovery` / `w08-recovery`.

## W10 scope boundary

W10 preserves every W1-W9 API, security boundary, deterministic fake baseline,
released Sandbox migration, W3/W7 catalog/checksum/split, W8 recovery contract,
W9 context/retrieval/summary/memory/ablation contract, independent Grader, and
Reporting freeze. It may add only:

- one fixed local Keycloak OIDC issuer and strict Control API bearer resource
  server with frozen issuer, JWKS, audience, client, and RS256 policy;
- an independent Control Plane PostgreSQL/Alembic schema for organizations,
  users, OIDC identities, memberships, and durable organization memory;
- database-derived `ActorContext`, three closed roles, closed permissions, and
  default-deny route authorization;
- organization-qualified repositories, constraints, indexes, queries, counts,
  writes, disable/tombstone/reset operations, and uniform non-enumeration;
- strong ETag/If-Match preconditions and atomic organization/resource/version
  mutations with exactly-one-winner concurrency;
- an identity-bound closed safe context projection while the released W9 fake
  path and Planning isolation remain unchanged;
- a minimal Control Web Authorization Code + S256 PKCE login/callback/logout/
  current-identity/forbidden experience with token material held in memory;
  and
- one deterministic W10 identity Compose acceptance profile and one CI job.

W10 adds no W11 approval/HITL/risk/audit capability, W12 production worker/
load/release capability, W13 telemetry, W14 malicious-page suite, W15 external
benchmark/Reporting execution, W16 deployment, SAML/SCIM/LDAP/MFA/passkeys,
dynamic or multi-provider identity framework, global administrator,
super-tenant bypass, impersonation, ABAC/policy language, physical deletion,
real identity/account/personal data, real model/provider/OCR/VLM/embedding/key/
egress, arbitrary browser/API/Shell/SQL/JavaScript/code, generic future
framework, or placeholder.

## File ownership and change control

Change only exact paths listed in `docs/agent-contract.md`. Add a path to that
contract before changing it. Any scope-expanding service, migration, real data,
approval, physical deletion, real provider, W11+ feature, or generic abstraction
requires user direction first.

The literal pre-existing `%SystemDrive%/` path is outside ownership. Do not
inspect, enumerate, copy, modify, stage, scan, ignore, or delete it. Do not
access any `code_review_agent` repository.

## Engineering and security conventions

- Python target is 3.13. Use uv and synchronize every changed Python lock.
  Frontends remain TypeScript/React/Vite and use `npm ci`.
- Keep Browser Worker, DOM Agent, Vision Agent, Hybrid Agent, Planning Agent,
  and Recovery Worker separate. Planning still reaches only Browser Worker;
  it gains no Control Plane/Sandbox/Arena/DB/Grader/Keycloak route.
- The only OIDC policy is the contract-frozen local issuer, internal JWKS URL,
  resource audience, browser client, RS256, JWT header type, and Bearer token
  type. Never accept a request-selected issuer/JWKS/discovery/algorithm.
- Bearer tokens are accepted only in the Authorization header. Reject bad
  signature/algorithm/kid/issuer/audience/client/subject/time/type before any
  tenant query; never log or persist tokens, claims, codes, cookies, secrets,
  passwords, or private keys.
- Construct `ActorContext` only from verified OIDC identity plus active local
  organization, user, and membership rows. Keycloak/page/body/header/model role
  input never grants authority. A role claim must match the database role.
- Roles and permissions are closed enums. Unknown/unmatched access defaults to
  deny. No global, wildcard, fallback, first-tenant, impersonation, or support
  bypass exists.
- Every tenant query and mutation is organization-qualified in SQL. Never read
  globally and filter in Python. Cross-organization and nonexistent objects use
  the same stable response without count/version/ETag leakage.
- Every mutable W10 tenant resource uses a strong ETag and required If-Match.
  Atomic writes include organization ID, resource ID, and expected version;
  successful versions increase exactly once and stale writes have no effect.
- Disable/tombstone only; never physically delete business identity or memory
  rows. Control Plane, Sandbox, and Temporal databases remain separate.
- Released W9 synthetic `scope_id` is regression input, never authentication or
  authorization. Only a closed authorized memory/context projection may cross
  into a later trusted Context assembly; Planning receives no DB capability.
- Treat human prose, page/email/PDF/DOM/image/OCR/form/model content as
  untrusted data. It cannot select identity, organization, actor, role,
  permission, owner, version, memory scope, tool, route, action, budget,
  recovery, approval, or success.
- Preserve current Worker reference validation, W8 recovery caps, the one
  non-resetting ledger, `finished_ungraded`, and independent database-fact
  grading.
- Default tests, CI, and Compose use deterministic synthetic data only. No real
  identity provider/account/data or real model/provider/OCR/VLM/embedding/key/
  egress call is authorized.
- Logs/evidence contain only versions, opaque IDs/hashes, counts, closed codes,
  HTTP states, and independent grades. Never persist personal data or machine
  paths.
- Use strict/frozen Pydantic models, `extra=forbid`, closed enums, deterministic
  canonical JSON/hashes, small modules, and no unused dependencies.

## Required local checks

Run for each Python app `control_api`, `sandbox_api`, `browser_worker`,
`dom_agent`, `vision_agent`, `hybrid_agent`, `planning_agent`, and
`recovery_worker`:

~~~powershell
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
~~~

Run for `control_web` and `sandbox_web`:

~~~powershell
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
~~~

Run Compose config/build/start/health; Sandbox Alembic current/check at released
W8 head with byte-identical migrations; Control Plane empty-database upgrade/
current/check/downgrade/upgrade; W4 DOM, W5 Vision, W6 Hybrid, W7 Planning, W8
Recovery, W9 Context, and W10 Identity smokes; W3/W7/W9 freeze checks; realm
checksum; Reporting not-run proof; exact contract path audit; staged/unstaged
review; and cleanup with zero project containers, networks, and volumes.

Finish with:

~~~powershell
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
pre-commit run detect-private-key --all-files
gitleaks git --no-banner --redact --exit-code 1 .
git diff --check
git diff -- . ':(exclude)%SystemDrive%'
git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%'
~~~

If the Docker Compose plugin is unavailable, compatible `docker-compose` may be
used and its version must be recorded. Any unavailable tool is recorded without
weakening the gate.

## Evaluation discipline

Development may rerun the frozen synthetic identity/RBAC/tenant/concurrency
matrix. Validation may run at most once after issuer/audience/client/algorithm,
roles/permissions, tenant data, ETags, and locking rules freeze; record whether
it ran. Reporting permits load/schema/checksum validation only and must not run
Reset, Seed, Agent, OIDC login, identity, tenant, memory, context, grade, or
result execution/inspection before W15.

## Git, quota, and completion discipline

Work only on `week/10-identity`; never develop on main or amend W9. No push, PR,
merge, tag, Release, remote CI/rerun, or real-provider call is authorized
without separate explicit user direction. Do not backfill a W9 tag. If later
authorized, the W10 tag is `w10-identity`; W10 creates no `v0.3.0` Release.

If remote work is later authorized: diagnose first, concentrate related fixes,
and push once. With no code/lock/workflow change and a transient infrastructure
failure, rerun failed jobs only. Never rerun all jobs, successful/superseded
runs, create empty commits/duplicate PRs, force-push, or weaken tests/security.

Do not use broad staging. After all locally available gates pass and evidence
matches observed results, explicitly stage only exact W10 allowlist paths,
create one local W10 commit, and stop before W11.
