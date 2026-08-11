# W17 agent contract — Portfolio Demo Console

## Authority and frozen history

W17 runs only on `codex/w17-portfolio-demo-console`, created from the exact PR
55 squash merge on `origin/main`:
`1d54afc738cf34a6cec1ebb144368b47a7a4b2dd`. PR 55 CI run `31467351190` and
post-merge main CI run `31468247367` passed before W17 began.

W12-W16 and the public v1.0 release remain immutable. In particular:

- W12 `2c642a67341d0cd1c9c62b6bf883ad8df2853f40` / `w12-production`.
- W13 `cedc5f26d41262c955b60854cc69ed4f28baded6` / `w13-observability`.
- W14 `6bd960a031069f262fe60fbbb8bf2c65a09e409b` / `w14-security`.
- W15 `94e5a8d74b970c93c9610725dad7cb352545f654` / `w15-evaluation`.
- W16 PR 45 through PR 55 merge objects listed in `AGENTS.md`.
- Annotated `v1.0.0` and its published GitHub Release remain at
  `4795aefe15be66f2405a2b899db7e5764810b8ea`.

No history rewrite, rollback, force push to main, tag move, retag, rerelease,
Release edit, workflow dispatch, or cloud mutation is authorized.

W15 frozen evidence remains byte-identified:

- `docs/evidence/week-15-report.json` SHA-256:
  `42058cc83d310b51011e4774909b32dab6f3e0370d546c3c7928a5518f86cc00`.
- W15 self-excluding `report_hash`:
  `ef2f1690a662eb5119214fb1e4fef80c22b1879ad0a88603b1e3e520c5cd9d3e`.
- `tests/integration/w15-reporting-protocol.json` byte SHA-256:
  `42d5439629be60727b7d69324fd5f1c76ba879d2e10fa6bb2d5ad2496901ae41`.
- Protocol hash:
  `b5aa0ddd4d0d07dd3d4a26faac11c947c223b85d14ac5dbc316681edc6de1379`.
- Configuration hash:
  `c9ea8d997e470a7b7584e40001e8dbff349bd9a73aa80cdbf1a32b84d81d7ec5`.
- Schema hash:
  `9a869a014f5ea34530230027dfbc780627ce0eed99ce753ff34ec897a8167962`.
- WorkArena: `unavailable/local_assets_absent`.

## Product authority boundary

W17 refines only the existing Control Web presentation. It does not change any
backend API, database, migration, identity, tenant, RBAC, approval, audit,
queue/rate/lease/fence, receipt/idempotency, recovery, Grader, security, Arena,
or W1-W16 semantics.

`finished_ungraded` is an Agent terminal state, not business success. Only the
independent Sandbox database-fact Grader can determine business success. The
Control API used by W17 does not return that verdict; the UI must state
`Grader result unavailable from this surface` and must not infer a result from
run status, trace status, receipt, audit, or Dashboard metadata.

The console is synthetic, local, and deterministic. `production-runs` is a
historical API name, not a production claim. There is no real provider, IdP,
model, OCR, VLM, embedding, billing account, personal data, production
identity, public deployment, SLO, ROI, or security certification. The completed
Aliyun cloud check was temporary ECS single-node K3s validation, not ACK,
managed-cluster deployment, high availability, public ingress, or production
certification. No further cloud action is permitted.

## UI contract

Control Web at `http://127.0.0.1:5173` must provide:

1. A visible `SYNTHETIC LOCAL DEMO` environment marker.
2. Overview of current opaque identity, organization, business/approval role,
   active and terminal run counts, pending approvals, and audit-chain status.
3. Fixed Joiner/Mover/Leaver submission using the existing task IDs, closed
   schema, current organization, `generate_plan`, and task-reference parameter.
4. A run list with process, task reference, status, updated timestamp, and a
   client-side all/active/terminal filter.
5. Strict loading, empty, forbidden, failure, stale, and polling-timeout states.
6. Run detail with observe → plan → execute → recover → verify timing derived
   only from fields returned by run and trace APIs.
7. Constrained trace/replay showing only ordinal/sequence, phase, status,
   reason, failure category, and observed time.
8. Existing approval decisions through the current strong ETag read-before-
   decide flow and stale-decision protection.
9. Separate Agent and independent-Grader result presentation.
10. A normal external link to `http://127.0.0.1:5174`; no iframe or browser-
    isolation bypass.
11. Responsive desktop/tablet layout, semantic controls, keyboard operation,
    visible focus, meaningful labels, live status, and alert semantics.

The UI must not accept arbitrary JSON, URL, provider, Shell, SQL, JavaScript,
secret, token, DSN, browser payload, or personal-data input. It must not render
access/ID tokens, nonce, grant material, internal worker/lease/claim endpoints,
trace/span IDs, worker references, authorization hashes, raw attributes,
receipt payloads, or sensitive fields.

## API and browser-security contract

W17 may call only:

- `GET/POST /api/v1/organizations/{organization_id}/production-runs`
- `GET /api/v1/organizations/{organization_id}/production-runs/{run_id}`
- `GET /api/v1/organizations/{organization_id}/production-runs/{run_id}/trace`
- Existing identity, approval, and audit endpoints already used by Control Web.

The `auth.ts` allowlist binds each exact path to GET or POST, limits organization
IDs to `org_[A-Za-z0-9_-]{8,64}` and run IDs to
`run_[A-Za-z0-9_-]{8,64}`, and rejects queries, fragments, cross-origin URLs,
unknown paths, caller-provided Authorization, claim/lease/worker surfaces, and
unsupported methods.

Access tokens remain module-memory-only. Existing pre-login OIDC PKCE/state/
nonce transaction material remains a bounded, one-use `sessionStorage` record;
tokens are never written to `localStorage` or `sessionStorage`. Polling uses a
five-second fixed interval and a two-minute maximum duration, exposes manual
refresh, and stops on terminal state, visibility loss, unmount, error, or
timeout.

Run and trace parsers require exact schema versions, exact key sets, closed
statuses/taxonomies, bounded arrays/integers, UTC timestamps, valid IDs, matching
organization/run identity, ordered trace/replay, and
`sensitive_fields_present = false`. Unknown and extra fields fail closed.

## Exact file allowlist

Only these exact paths may be created or modified:

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

No package manifest, lockfile, backend, Compose, Helm, workflow, database,
migration, service, dependency, or other path may change. `%SystemDrive%/`,
`.tmp/`, and every `code_review_agent` repository are outside scope and must not
be inspected, enumerated, modified, deleted, or staged.

## Verification and closure

Run in `apps/control_web`:

~~~powershell
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
~~~

Also parse Compose YAML without starting services; compare bilingual README
commands and relative links; verify W12-W16 objects and W15 hashes; run
detect-private-key, gitleaks, `git diff --check`, exact allowlist review, and
staged diff review. Unavailable tooling is evidence, not a pass.

Do not run W15 Reporting final, W12 formal Validation, an external Benchmark,
either W16 release workflow, ECS deployment, ACK creation, or any cloud action.

The single W17 commit subject is:

    feat(web): add W17 portfolio demo console

After local closure, push the W17 branch, open one non-Draft PR, wait for normal
PR CI, and squash merge only when CI is green and GitHub reports CLEAN/
MERGEABLE. Verify one post-merge main CI run, then delete the remote W17 branch.
The annotated `v1.0.0` tag and published Release remain unchanged.
