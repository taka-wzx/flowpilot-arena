# W17 plan — Portfolio Demo Console

## Objective

Present the existing local synthetic Control Plane capabilities through one
resume-ready Control Web console without changing any backend or W1-W16
authority boundary.

## Baseline

- Branch: `codex/w17-portfolio-demo-console`.
- Exact start: PR 55 squash merge
  `1d54afc738cf34a6cec1ebb144368b47a7a4b2dd`.
- PR 55 CI: run `31467351190`, passed before W17.
- Post-merge main CI: run `31468247367`, passed before W17.
- Existing annotated `v1.0.0` and GitHub Release remain unchanged.
- No cloud execution, release-workflow dispatch, W15 Reporting final, W12
  formal Validation, or external Benchmark is authorized.

## Work packages

### 1. Contract and architecture

- Replace the W16 working guide with W17 branch, scope, allowlist, and closure.
- Record the decision to compose existing frontend clients and public APIs only.
- Preserve W12-W16 objects, W15 hashes, and all Agent/Grader semantics.

### 2. Strict run client

- Extend `auth.ts` with exact GET/POST run routes.
- Reject bad IDs, query, fragment, cross-origin, unknown method/path, and
  internal mutation/worker routes.
- Add exact run list/detail and trace/replay parsers.
- Project trace data onto a presentation-safe subset.
- Add fixed JML submission and in-memory idempotency retry behavior.
- Add five-second/two-minute bounded polling with all stop conditions.

### 3. Console UX

- Add the environment marker and overview metrics.
- Add fixed task creation and client-side status filtering.
- Add loading, empty, forbidden, failure, stale, and timeout states.
- Add run detail, lifecycle timeline, bounded trace/replay, and manual refresh.
- Link approval detail to the existing strong-ETag decision flow.
- Separate Agent terminal status from independent grading.
- Add a normal Sandbox Web link without iframe.
- Support desktop/tablet/mobile layout, semantic controls, keyboard focus, and
  ARIA status/alert behavior.

### 4. Tests

- Strict run/trace parse acceptance and rejection.
- Bad/unknown fields, statuses, IDs, tenant identity, and route origins.
- Fixed submit, idempotency replay, retry retention, and failure.
- Poll start, terminal stop, timeout, page-hide stop, and cleanup.
- Approval linkage, ETag stale notice, and audit verification.
- Loading, empty, forbidden, failure, stale, and trace-unavailable UI.
- `finished_ungraded` and Grader separation.
- Keyboard-focusable native controls and no sensitive DOM/storage material.

### 5. Documentation and evidence

- Update bilingual README and demo guide with exact local endpoints and limits.
- Update the project roadmap and authoritative contract.
- Record commands, outcomes, unavailable tools, exact changed paths, and frozen
  object checks in W17 evidence.

## Acceptance gates

Run in `apps/control_web`:

~~~powershell
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
~~~

Run repository closure gates without starting services:

~~~powershell
docker compose -f deploy/compose/compose.yaml config --quiet
pre-commit run detect-private-key --all-files
gitleaks git --no-banner --redact --exit-code 1 .
git diff --check
~~~

Also compare bilingual commands and relative links, verify frozen objects and
W15 hashes, review the exact allowlist, and review the staged diff. Any
unavailable command is reported as unavailable, never passed.

## Git closure

Create one commit:

    feat(web): add W17 portfolio demo console

Push one branch, open one non-Draft PR, wait for normal CI, and squash merge
only when CI is green and the PR is CLEAN/MERGEABLE. Verify the resulting main
CI, delete the remote W17 branch, and confirm `v1.0.0` did not move.
