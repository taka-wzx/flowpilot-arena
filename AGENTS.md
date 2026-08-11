# FlowPilot Arena agent guide

## Current phase and immutable baselines

This branch is the authorized W17 Portfolio Demo Console on
`codex/w17-portfolio-demo-console`. It was created from the verified PR 55
squash merge on `origin/main`:

- W17 start / PR 55 merge: `1d54afc738cf34a6cec1ebb144368b47a7a4b2dd`.
- PR 55 CI run `31467351190` passed.
- Post-merge main CI run `31468247367` passed.

The authoritative W17 contract is `docs/agent-contract.md`; the roadmap is
`docs/project-roadmap.md`. W12-W16, the two security-maintenance merges, and
their tags/releases are immutable:

- W12 merge `2c642a67341d0cd1c9c62b6bf883ad8df2853f40`, tag `w12-production`.
- W13 merge `cedc5f26d41262c955b60854cc69ed4f28baded6`, tag `w13-observability`.
- W14 merge `6bd960a031069f262fe60fbbb8bf2c65a09e409b`, tag `w14-security`.
- W15 merge `94e5a8d74b970c93c9610725dad7cb352545f654`, tag `w15-evaluation`.
- PR 43 merge `697c8b8b9a6b4c25b571e7b0dbf6c01bcb82bbf3`.
- PR 44 merge `078eb22deb137191660a5511c496fd1dff2b74f3`.
- W16 PR 45 merge `d1b03993fc912179d3cdbef00b9f26f524ca9c52`.
- W16 closure PR 46 merge `aab7efed479ad208ced4786ff43f8e72e4f1c458`.
- W16 Private-workflow compatibility PR 47 merge
  `7661db412fde625ec0a6ff81261d26343cf53052`.
- W16 Private-image remediation PR 48 merge
  `f334441612f0c3508f197cecf8d0456296a771cf`.
- W16 rollback namespace PR 49 merge
  `b62333492aea62a0d4b12147ce863ab76bda0133`.
- W16 scoped DNS egress PR 50 merge
  `5f37b49a3eb30b63c7aed7fe91676708a28721ac`.
- W16 public-release evidence PR 51 merge
  `bc5da48060b999e85553d9d2db6d03b16303d5c9`.
- W16 public README PR 52 merge, annotated `v1.0.0` tag, and published GitHub
  Release `4795aefe15be66f2405a2b899db7e5764810b8ea`.
- W16 post-release compliance PR 53 merge
  `14ad304ef64df638c9a61a898db5c3329021fd33`.
- W16 post-release evidence PR 54 merge
  `66c71a5a5b47f1cae814092b6832006ac43fddca`.

Do not rewrite, roll back, retag, rerelease, or otherwise modify those objects.
W15's report, protocol, configuration, schema, and hashes remain frozen. Never
move or replace the existing `v1.0.0` tag or edit/rerelease its GitHub Release.

## W17 authority boundary

W17 may refine only the existing Control Web into a unified, resume-ready,
synthetic Portfolio Demo Console. It must not change backend API, database,
migration, identity, tenant, RBAC, approval, audit, queue/rate/lease/fence,
receipt/idempotency, recovery, Grader, security, Arena, or W1-W16 semantics.
`finished_ungraded` remains the Agent terminal state; it is not business
success. Only the independent Sandbox database-fact Grader determines business
success. If its result is absent from the Control API, the UI must say so.

The console is local, deterministic, and synthetic. It may offer only fixed
Joiner, Mover, and Leaver submissions using existing schemas and the current
fixed organization. It must not accept arbitrary JSON, URL, Shell, SQL,
JavaScript, provider, secret, account, billing, model, OCR/VLM/embedding, or
personal-data inputs. Do not expose internal claim, lease, worker-only, nonce,
token, DSN, raw browser payload, or sensitive trace fields.

Use only these existing Control API surfaces:

- `GET/POST /api/v1/organizations/{organization_id}/production-runs`
- `GET /api/v1/organizations/{organization_id}/production-runs/{run_id}`
- `GET /api/v1/organizations/{organization_id}/production-runs/{run_id}/trace`
- Existing identity, approval, and audit endpoints.

The browser route allowlist must enforce exact organization/run ID formats and
GET/POST methods and reject query strings, fragments, cross-origin URLs, and
unknown paths. Tokens remain in memory only. The pre-login OIDC transaction may
continue using its existing short-lived `sessionStorage` record; access and ID
tokens must never use `localStorage` or `sessionStorage`. Polling must use a
fixed interval and finite maximum duration, expose manual refresh, and stop on
terminal state, page hiding, unmount, or timeout.

No new npm dependency is authorized. Do not modify package manifests,
lockfiles, backend code, Compose, Helm, workflows, databases, or migrations.

No cloud mutation is authorized. Do not redeploy ECS, create ACK, open a public
port, create paid resources, or perform any other cloud change. The completed
Aliyun ECS validation was a single-node K3s validation, not ACK and not
production certification. Do not rerun W15 Reporting final, W12 formal
Validation, an external Benchmark, or either completed W16 release workflow.

The literal `%SystemDrive%/` path, `.tmp/`, and every `code_review_agent`
repository are outside scope. Do not inspect, enumerate, scan, modify, delete,
or stage them; preserve their contents.

## Exact W17 file allowlist

Only the following exact paths may be created or modified. Directory wildcards
are forbidden. Stop and explain before any additional path is considered.

~~~text
AGENTS.md
README.md
README.zh-CN.md
docs/agent-contract.md
docs/project-roadmap.md
docs/demo.md
docs/adr/0017-w17-portfolio-demo-console.md
docs/plans/week-17-portfolio-demo-console.md
docs/evidence/week-17-portfolio-demo-console.md
apps/control_web/src/App.tsx
apps/control_web/src/App.css
apps/control_web/src/App.test.tsx
apps/control_web/src/auth.ts
apps/control_web/src/auth.test.ts
apps/control_web/src/runs.ts
apps/control_web/src/runs.test.ts
apps/control_web/src/components/DemoConsole.tsx
apps/control_web/src/components/DemoConsole.test.tsx
apps/control_web/src/components/RunTimeline.tsx
apps/control_web/src/components/RunTimeline.test.tsx
~~~

## W17 implementation and verification

The UI must provide a visible `SYNTHETIC LOCAL DEMO` marker, identity/role,
active and terminal run counts, pending approvals, audit-chain state, fixed JML
submission, filterable run list, bounded run detail and trace/replay timeline,
approval linkage with existing ETag protection, strict Agent/Grader separation,
and a normal link to `http://127.0.0.1:5174` without iframe or isolation bypass.
It must render loading, empty, forbidden, stale, failure, and polling-timeout
states and remain keyboard-operable with semantic markup, visible focus, and
appropriate ARIA.

Before implementation, read the existing backend schemas, routes, and
integration tests. Frontend parsers must accept exactly the returned schema;
unknown fields, values, IDs, and statuses are rejected rather than guessed.

Run in `apps/control_web`:

~~~powershell
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
~~~

Also run Compose YAML config parsing without starting services, bilingual
README command/link consistency checks, W12-W16 frozen hash/object checks,
detect-private-key, gitleaks, `git diff --check`, exact allowlist review, and
staged diff review. Record unavailable tooling honestly; never turn an
unavailable check into a passing claim.

Finish with local forms of:

~~~powershell
docker compose -f deploy/compose/compose.yaml config --quiet
pre-commit run detect-private-key --all-files
gitleaks git --no-banner --redact --exit-code 1 .
git diff --check
git diff -- . ':(exclude)%SystemDrive%' ':(exclude).tmp'
git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%' ':(exclude).tmp'
~~~

## Git closure authorization

The only W17 commit subject is:

    feat(web): add W17 portfolio demo console

Push `codex/w17-portfolio-demo-console`, open a non-Draft PR, wait for normal PR
CI, and squash merge only when CI is green and GitHub reports the PR
CLEAN/MERGEABLE. Then wait for and verify post-merge main CI and delete the
remote W17 branch. Never force-push `main`, alter any tag or Release, dispatch a
release workflow, or perform cloud operations.
