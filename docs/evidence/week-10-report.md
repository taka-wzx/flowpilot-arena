# Week 10 evidence report - OIDC, RBAC, Tenant Isolation, and Optimistic Locking

- Status: local implementation and all required local gates complete
- Branch: `week/10-identity`
- Baseline: released W9 merge `5e1868d30da70c2d8cd9db1705db0cb8f7dabfac`
- Local W10 commit: created after this evidence freeze; final SHA is recorded in
  the handoff
- W10 remote push/PR/CI/merge/tag/Release: not run
- Real identity provider/account/data: not run; 0 calls
- Real model/provider/OCR/VLM/embedding: not run; 0 calls; 0 billed tokens;
  0 cost
- Validation: not run
- Reporting execution: false

## Baseline and remote read-only verification

Official W9 PR #31 merged normally at the baseline SHA. PR run `30425071418`
and post-merge main run `30425554286` each passed 18/18 jobs on attempt 1 with
no failed job, rerun, or follow-up repair. No W9 tag exists. The current
published Release remains `v0.2.0 - Hybrid + Recovery` using `w08-recovery`.

W10 was created directly from the exact official W9 main SHA. It did not amend,
retag, republish, or change W9 history. W10 used zero remote feature pushes,
PRs, merges, Actions runs/jobs, reruns, workflow dispatches, tags, Releases, or
extra runs.

## Implementation and isolation

W10 adds a pinned Keycloak 26.3.2 local synthetic issuer; strict Control API
Bearer/JWT/JWKS verification; a separate Control PostgreSQL/Alembic identity
schema; database-derived ActorContext; three closed roles and ten closed
permissions; organization-qualified repositories; uniform non-enumeration;
strong ETag/If-Match writes; durable organization memory; a closed authorized
context projection; and a minimal Control Web Code + S256 PKCE flow.

Control, Sandbox, and Temporal databases remain independent. Planning Agent
still reaches only Browser Worker and receives no Keycloak, Control API,
Control database, Sandbox database, Arena, Grader, credential, token, or raw
claim capability. W9's synthetic scope and fake memory path remain unchanged
and are not authorization input. W8 Recovery and `finished_ungraded` semantics
are unchanged; independent Sandbox database-fact grading remains authoritative.

All tenant-owned reads, lists, counts, writes, disable/tombstone operations,
memory reset, constraints, and indexes include organization ownership. There is
no global administrator, wildcard organization/permission, impersonation,
fallback tenant, ABAC/policy language, or physical-delete route.

## Frozen identity data and OIDC configuration

- Keycloak: `26.3.2`
- Realm import SHA-256:
  `38fb45f4c28ea3c5e2814cf6d413cdc036246ef81bed42cbd6b1bd529c77a5d8`
- Realm clients / closed roles / synthetic users: 1 / 3 / 6
- Control organizations / users / OIDC identities / memberships: 2 / 6 / 6 / 6
- Issuer/audience/client/algorithm policy: one exact contract-frozen tuple
- Browser discovery from the host: HTTP 200 with the exact frozen issuer
- Keycloak published host binding: loopback only
- Bootstrap-admin environment variables after recreation: 0

The first clean realm import exposed a Keycloak 26 user-profile requirement for
the six synthetic users. Fixed `.invalid` synthetic profiles were added, failed
realm data was removed, and a clean import succeeded. A later network check
found that a container attached only to the internal identity bridge retained a
declared PortBinding but created no host listener. Attaching Keycloak to the
existing Control frontend network for loopback browser ingress, while retaining
the internal identity network for JWKS, restored the expected binding. A clean
recreation proved the final configuration. Neither diagnosis made a real IdP
call or persisted token/claim data.

## Closed RBAC evidence

| Permission | organization_admin | operator | auditor |
|---|---:|---:|---:|
| organization read/update | yes/yes | yes/no | yes/no |
| user read/manage | yes/yes | yes/no | yes/no |
| membership read/manage | yes/yes | no/no | yes/no |
| memory read/write/reset | yes/yes/yes | yes/yes/yes | yes/no/no |
| context project | yes | yes | yes |

The complete matrix contains 21 allowed and 9 denied role/permission cells.
API tests cover route allows/denies, unknown roles/permissions, claim/database
role mismatch, auditor write rejection, operator membership rejection, actor/
organization/role injection rejection, and immediate identity/user/
organization/membership revocation. Every permission is database-derived and
organization-local.

## Authentication, tenant, and optimistic-lock evidence

Control API tests passed 36/36 and cover missing/malformed Bearer input,
`alg=none`, algorithm confusion, wrong signature, unknown key, wrong issuer/
audience/client/type, missing subject, expiry, future not-before, invalid/future
issued-at, key/JWKS validation, bounded refresh, active-state enforcement,
authorization, tenant isolation, non-enumeration, ETags, rollback, concurrency,
migration, and safe projection.

The final clean-seed Compose W10 summary was:

| Measure | Observation |
|---|---:|
| local OIDC calls | 4 |
| authentication allow / reject | 4 / 1 |
| authorization allow / reject | 5 / 3 |
| cross-organization rejects | 7 |
| optimistic success / stale-conflict | 1 / 1 |
| concurrent exactly-one-winner | true |
| authorized context projection items | 1 |
| real identity-provider calls | 0 |
| real model/provider calls | 0 |
| cost | 0 |
| Validation / Reporting | false / false |

The smoke rejected cross-organization organization read, user list/count/
update, membership update, memory reset, and context projection. The allowed
path created version 1 memory, ran two simultaneous writes with one 200 and one
412, returned one closed safe projection item, disabled one membership with a
strong precondition, and rejected its next request immediately. Failed cross-
organization and stale operations produced no opposing-tenant state change,
partial update, duplicate effect, or extra version increase.

A deliberate second smoke on the already-mutated persistent Development volume
failed because the first smoke had correctly disabled its synthetic auditor.
The required clean-volume procedure was then applied, the full stack was
rebuilt, and the final smoke above passed. This was a local initial-state reset,
not a remote CI rerun or security relaxation.

## Migration and database evidence

Control Plane revision is `20260729_0001`. Online Control PostgreSQL reported
that revision at head and `alembic check` found no new operations. A separate
empty synthetic PostgreSQL database passed upgrade, current, check, downgrade
to base, second upgrade, current, and check; the temporary database was removed
in all cases.

Online Sandbox PostgreSQL remained at released `20260728_0003 (head)` and
`alembic check` found no new operations. A baseline diff proved every released
Sandbox migration byte unchanged. Schema/API tests cover organization-aware
foreign keys, uniqueness, indexes, and Control/Sandbox separation. No W10
Control row enters Sandbox Reset/Seed/Grader or Temporal persistence.

## Application and frontend gates

All eight Python applications passed `uv sync --locked --all-groups`, Ruff
check, Ruff format check, strict Mypy, and pytest:

| Application | Tests |
|---|---:|
| Control API | 36 |
| Sandbox API | 35 |
| Browser Worker | 41 |
| DOM Agent | 27 |
| Vision Agent | 20 |
| Hybrid Agent | 31 |
| Planning Agent | 47 |
| Recovery Worker | 12 |

The initial Control pytest invocation was blocked only by an inaccessible stale
system pytest temp root after 21 tests had passed. The complete 36-test suite
then passed unchanged using a dedicated temporary pytest root; that verified
temporary directory was removed afterward.

Both frontend locked installs passed lint, typecheck, tests, and production
builds: Control Web 5/5 and Sandbox Web 9/9. PowerShell policy blocked the
`npm.ps1` shim, so the same installed `npm.cmd` executable was used. No manifest
or lock changed as a result.

The W10 integration script passed Ruff lint and format. Its first format check
reported mechanical layout differences; Ruff formatted the allowlisted file,
and the final rebuilt smoke passed with unchanged logic.

## W3/W7/W9 freeze and W4-W9 Compose regression

W3 retained 10 tasks, 6/2/2 split, and checksum
`e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9`.
W7 retained 30 templates/90 instances, 12/8/10 processes, 18/6/6 split,
catalog checksum
`62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f`,
split checksum
`1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee`,
and Reporting checksum
`c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6`.
W9 retained nine enterprise records, five exact ablation names, and checksum
`4d63a24a57a54f9f7d94abe6b98d34453525dde13a6b100e336c8442c68bfb15`.

All deterministic Compose smokes passed in release order:

| Smoke | Required observation |
|---|---|
| W4 DOM | `finished_ungraded`, independent grade 30 baseline, 0 cost |
| W5 Vision | `finished_ungraded`, independent grade 100, 0 cost |
| W6 Hybrid | `finished_ungraded`, independent grade 100, 0 cost |
| W7 Planning | 30/90 freeze and Development Joiner/Mover/Leaver grade 100 |
| W8 Recovery | complete fault/retry/receipt/Checkpoint/replay matrix; duplicate effects 0 |
| W9 Context | five ablations, frozen hashes/checksum, J/M/L grade 100 |
| W10 Identity | pinned local issuer, RBAC/tenant/ETag/concurrency/projection matrix |

Observed W9 Development context-backed results remained:

| Task | Grade | Context items | Retrieval | Summary inputs | Memory read/write | Context hash |
|---|---:|---:|---:|---:|---|---|
| Joiner | 100 | 9 | 1 | 4 | 1/1 | `720070e0d3f1604412f58c04e6ad73c044770138efb45ae7aacdb4f85b5a0771` |
| Mover | 100 | 9 | 1 | 4 | 2/1 | `9357c53d631179a6839671f29fdf3e1dfc35f42bc925abe34c9ef770302b5f3a` |
| Leaver | 100 | 9 | 1 | 4 | 3/1 | `c50cece25a957fb8e03324d3772d81f086601713e4c2d89007cc0d0533a77611` |

W9 Compose ablation hashes remained full five-layer
`e52bffb00f08cddb9bc0c47dadb252bb2a94b1d2fb0957e6b5a61ef5acfd2bb9`,
task-facts-only
`1020f9ec450675c10c154d24dfee4e5fdb63373be074d478700ab6f92694cd9f`,
no-short-term
`7306bfc481773c9bc8c97134be4e0723d9978c20d863bfb0cad51cb5f4ec1192`,
no-enterprise-retrieval
`9b2a8f108d78d434e79903eb577e2f47d2815279971641e7d297d36c24eb3d69`,
and no-organization-memory
`5a245b5df22014f3447d1a59e058532c6b99aefbad1f50ca0d895f6f3fe7bd74`.

## Compose, cleanup, security, and contract gates

The Docker Compose plugin was unavailable. Compatible standalone
`docker-compose 5.3.1` was used and `config --quiet` passed. Docker Engine
29.6.2 built all images and all 15 long-running W1-W10 services were healthy.
The optional buildx plugin was absent; the classic builder completed every
required build without weakening a gate.

Final `down -v --remove-orphans` removed all synthetic services and persistence.
Project-label enumeration observed exactly 0 containers, 0 networks, and 0
volumes.

Gitleaks historical scan passed 46 commits with no leaks; the exact staged scan
also found no leak. The globally installed `pre-commit` command was unavailable,
so the exact `detect-private-key --all-files` hook ran through an isolated `uvx`
environment and passed. This final evidence-only edit is restaged and both
secret gates rerun before commit; cached/unstaged diff and path results are
recorded in the handoff.

The contract contains 51 exact allowlist paths. Before evidence creation the
audit found 49 changed/created paths and 0 outside; this evidence file brings
the final changed/created count to 50, with the allowlisted unchanged Control
Web environment declaration accounting for the remaining path. No literal
`%SystemDrive%/` path or `code_review_agent` repository was accessed, scanned,
staged, or modified.

## Evaluation and W11 boundary

Development unit and Compose identity matrices were executed. Validation was
not run. Reporting was not executed. Packaged catalog/schema/checksum values
were validated only; no Reporting Reset, Seed, Agent, OIDC login, identity,
organization, user, membership, RBAC, tenant, memory, context, grade, or result
execution/inspection occurred.

W10 proves only the frozen deterministic synthetic environment. It does not
claim production OIDC security, real enterprise tenant isolation, real account
protection, malicious-page resistance, external benchmark performance, load,
availability, SLO, or ROI. W11 approvals/HITL/risk/audit were not started.
