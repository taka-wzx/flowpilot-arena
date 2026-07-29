# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is a production-oriented computer-use Agent project paired
with a separate resettable synthetic evaluation environment. The authoritative
roadmap is `docs/project-roadmap.md`; exact current authority is
`docs/agent-contract.md`.

This branch is W11: HITL, Risk Policy, One-Time Approval, and a Tamper-Evident
Audit Chain on `week/11-approval`. The immutable W10 product baseline is merge
`9bbb0303c6bc795468b094df676a86dfcbc69dcb` / tag `w10-identity`; the local
starting point is quota-maintenance commit
`b90cd44ec440eef2d69f12d03890bae57c845e37`. Maintenance PR #33 is currently
open/blocked because Actions run `30440647089` exhausted quota with fourteen
zero-step jobs. The current release remains
`v0.2.0 - Hybrid + Recovery` / `w08-recovery`.

## W11 scope boundary

W11 preserves every W1-W10 API, security boundary, deterministic fake baseline,
released Sandbox migration, W3/W7 catalog/checksum/split, W8 recovery contract,
W9 context/retrieval/summary/memory/ablation contract, W10 identity/tenant/
locking contract, independent Grader, and Reporting freeze. It may add only:

- one closed L0-L4 trusted server-side risk policy over strict action schemas
  and current organization-qualified facts;
- database-derived, organization-qualified manager/security authorities kept
  separate from W10 business roles;
- L2 manager and L3 manager-plus-distinct-security human approval with
  self/executor denial and current-active-state rechecks;
- strong-ETag approval request lifecycle, immutable decisions, hash-only
  short-lived one-time grants, exactly-one-winner claims, and durable execution
  references coordinated with the released W8 receipt boundary;
- one per-organization append-only canonical SHA-256 audit chain with atomic
  head/sequence allocation and deterministic verification;
- a minimal Control Web pending/detail/approve/reject/audit experience that
  never receives grant material; and
- one deterministic W11 approval Compose acceptance profile appended to the
  consolidated W4-W11 regression job.

W11 adds no W12 production worker/API split, load or release capability, W13
telemetry, W14 malicious-page suite, W15 external benchmark/Reporting
execution, W16 deployment, dynamic approval or policy framework, ABAC, global
approver, super-tenant bypass, impersonation, delegation, break-glass,
administrator override, L4 approval, physical deletion, real identity/account/
personal data, real model/provider/OCR/VLM/embedding/key/egress, arbitrary
browser/API/Shell/SQL/JavaScript/code, generic future framework, or placeholder.

## File ownership and change control

Change only exact paths listed in `docs/agent-contract.md`. Add a path to that
contract before changing it. Any scope-expanding service, migration, real data,
physical deletion, real provider, W12+ feature, or generic abstraction
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
  organization, user, membership, and approval-authority rows. Keycloak/page/
  body/header/model role input never grants authority. A business-role claim
  must match the database role; it never grants manager/security authority.
- Roles and permissions are closed enums. Unknown/unmatched access defaults to
  deny. No global, wildcard, fallback, first-tenant, impersonation, or support
  bypass exists.
- Risk is one closed server-side mapping over strict validated parameters and
  current tenant facts. Unknown action is L4 and permanently denied. Objective,
  page/DOM/image/form/model text and caller risk/actor/approver input have no
  authority.
- L2 requires one current active manager; L3 requires one active manager and a
  distinct active security user. Requester/executor self-approval, inactive
  authority, insufficient approval, changed parameters, expiry, cross-tenant
  access, and L4 have zero business side effects.
- Raw approval credentials exist only in the bounded trusted Control API
  executor vault. Persist only credential/nonce hashes. Never return grant
  material to Control Web or place it in logs, evidence, URLs, browser storage,
  Temporal, Checkpoints, Planning, Sandbox pages, or Grader data.
- Audit events and immutable decisions are append-only. Each organization has
  its own locked sequence/head and canonical previous/event hashes. Call the
  property tamper-evident, never tamper-proof, blockchain, or legal compliance.
- Every tenant query and mutation is organization-qualified in SQL. Never read
  globally and filter in Python. Cross-organization and nonexistent objects use
  the same stable response without count/version/ETag leakage.
- Every mutable W10/W11 tenant resource uses a strong ETag and required If-Match.
  Atomic writes include organization ID, resource ID, and expected version;
  successful versions increase exactly once and stale writes have no effect.
- Disable/tombstone only; never physically delete business identity, memory,
  authority, approval, grant, decision, or audit rows. Control Plane, Sandbox,
  and Temporal databases remain separate.
- Released W9 synthetic `scope_id` is regression input, never authentication or
  authorization. Only a closed authorized memory/context projection may cross
  into a later trusted Context assembly; Planning receives no DB capability.
- Treat human prose, page/email/PDF/DOM/image/OCR/form/model content as
  untrusted data. It cannot select identity, organization, actor, role,
  permission, owner, version, memory scope, tool, route, action, risk, approver,
  grant, budget, recovery, approval, or success.
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
Recovery, W9 Context, W10 Identity, and W11 Approval/Audit smokes; W3/W7/W9
freeze checks; W10 realm checksum; W10 authentication/RBAC/tenant/locking and
W11 risk/approval/grant/audit matrices; Reporting not-run proof; exact contract
path audit; staged/unstaged review; and cleanup with zero project containers,
networks, and volumes.

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

Development may rerun the frozen synthetic risk/approval/grant/audit matrix.
Validation may run at most once after actions/risk, parameter schemas, approval
roles and separation, state machine, expiry, grant/claim/recovery, audit schema/
hash, seed, and expected results freeze; record whether it ran. Reporting
permits load/schema/checksum validation only and must not run Reset, Seed,
Agent, OIDC login, approval, grant, audit inspection, grade, or result execution
before W15.

## Git, quota, and completion discipline

Work only on `week/11-approval`; never develop on main or amend W9, W10, or the
maintenance baseline. No push, PR, merge, tag, Release, remote CI/rerun, or
real-provider call is authorized without separate explicit user direction. If
later authorized, the W11 tag is `w11-approval`; W11 creates no Release or
`v0.3.0`.

If remote work is later authorized: diagnose first, concentrate related fixes,
and push once. With no code/lock/workflow change and a transient infrastructure
failure, rerun failed jobs only. Never rerun all jobs, successful/superseded
runs, create empty commits/duplicate PRs, force-push, or weaken tests/security.

Do not use broad staging. After all locally available gates pass and evidence
matches observed results, explicitly stage only exact W11 allowlist paths,
create one local W11 commit, and stop before W12.
