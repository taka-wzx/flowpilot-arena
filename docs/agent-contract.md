# W1 agent contract — Foundation

## Authority and source

This contract translates the W1 row of
[project-roadmap.md](project-roadmap.md) into a bounded implementation
agreement. It governs the `week/01-foundation` branch only.

The intended W1 outcome is a documented, reproducible, empty-system starting
point: governance and quality gates plus a minimal API health check and web
landing page. It is not a partial enterprise automation product.

### User-authorized W1 toolchain adjustment

The roadmap names Python 3.12. The user has explicitly authorized Python 3.13
for W1, so all W1 Python manifests, CI, and container images must use 3.13.
This is a runtime-version adjustment only; it does not broaden W1 scope or
authorize any later-week component.

## Baseline observed before W1 edits

- Git branch: `week/01-foundation`.
- `main`, `origin/main`, and the current branch point at the initial repository
  commit.
- `docs/project-roadmap.md` exists as an untracked, read-only planning input.
- `%SystemDrive%/` is a separate pre-existing untracked directory. It is
  explicitly excluded from W1 ownership and must remain untouched.

## Allowed W1 paths

Only the following files may be created or modified for W1. Existing
`docs/project-roadmap.md` may be staged unchanged, but its content must not be
edited in this week.

```text
AGENTS.md
README.md
LICENSE
SECURITY.md
CONTRIBUTING.md
CHANGELOG.md
.gitignore
.gitattributes
.env.example
.pre-commit-config.yaml

.github/CODEOWNERS
.github/PULL_REQUEST_TEMPLATE.md
.github/dependabot.yml
.github/workflows/ci.yml

docs/project-roadmap.md                         # existing; stage unchanged only
docs/agent-contract.md
docs/product-brief.md
docs/architecture.md
docs/threat-model.md
docs/evaluation-protocol.md
docs/adr/0001-w1-minimal-monorepo.md
docs/plans/week-01-foundation.md
docs/evidence/week-01-report.md

apps/control_api/.dockerignore
apps/control_api/Dockerfile
apps/control_api/pyproject.toml
apps/control_api/uv.lock
apps/control_api/src/flowpilot_control_api/__init__.py
apps/control_api/src/flowpilot_control_api/main.py
apps/control_api/tests/test_health.py

apps/control_web/.dockerignore
apps/control_web/Dockerfile
apps/control_web/eslint.config.js
apps/control_web/index.html
apps/control_web/package.json
apps/control_web/package-lock.json
apps/control_web/tsconfig.json
apps/control_web/tsconfig.app.json
apps/control_web/tsconfig.node.json
apps/control_web/vite.config.ts
apps/control_web/src/App.tsx
apps/control_web/src/App.css
apps/control_web/src/App.test.tsx
apps/control_web/src/index.css
apps/control_web/src/main.tsx
apps/control_web/src/setupTests.ts
apps/control_web/src/vite-env.d.ts

deploy/compose/compose.yaml
```

Any newly needed file must first be added here with a W1-only rationale. A path
outside this list requires user direction instead of an implicit scope change.

## Required W1 deliverables

1. Governance: `AGENTS.md`, Apache-2.0-compatible `LICENSE`, contribution and
   security policies, changelog, ignore rules, env template, branch/PR/tag
   convention, and an explicit weekly contract.
2. Documentation: product brief, W1 current-state architecture, threat model,
   evaluation protocol (protocol only), ADR, week plan, and evidence report.
3. Minimal runnable path: one FastAPI process exposing only an unauthenticated
   static `/healthz` response, and one static React/Vite page describing the
   foundation status.
4. Local deployment skeleton: Dockerfiles for those two processes and Compose
   configuration that parses without external infrastructure.
5. Reproducibility and quality: Python 3.13 with committed `uv.lock`, frontend
   `package-lock.json`, lint/type/test/build scripts, CI, Dependabot, a
   pre-commit private-key check, and a CI secret scan.

## Explicit non-goals and prohibited early implementation

The following are prohibited in W1, including stubs that expose their runtime
behaviour:

- Sandbox, HRIS, ITSM, IAM, Asset, Mail, seed data, or enterprise-app pages;
- Arena task specifications, reset/seed, graders, faults, splits, baselines,
  benchmark adapters, metrics, or evaluation runs;
- Agent loop, planner/DAG, context/memory, typed browser actions, verifier,
  recovery, approvals, or audit chains;
- Playwright, browser workers, screenshots, OCR, VLM, model adapters, model
  calls, token/cost tracking, or any paid model use;
- Temporal, workflows, queues, workers, databases, ORM/migrations, object
  storage, OIDC, RBAC, tenant data, or observability stack;
- real external enterprise systems, real credentials, personal data, or
  production claims.

## Scope assumptions recorded from roadmap ambiguities

1. The roadmap's long-term directory map is a target topology, not a mandate to
   create all directories in W1. W1 will create only directories that contain
   a currently runnable artifact; future topology is documented rather than
   represented by empty placeholders.
2. “CI 全绿” can be established locally by exercising the same commands and by
   committing a GitHub Actions workflow. Remote GitHub status cannot be claimed
   until an authorized push and pull request occur.
3. The roadmap requires a PR merge and tag only after the weekly branch has
   passed review. The user currently authorizes a local commit only, so W1 must
   neither merge to `main`, create the release tag, nor push.
4. “Compose 可解析” is satisfied by `docker compose ... config` or the
   compatible `docker-compose ... config`; it does not authorize adding
   PostgreSQL, Keycloak, Temporal, MinIO, monitoring, or any other
   infrastructure service.
5. A health endpoint is a foundation smoke check, not a control-plane API
   contract. It must be deterministic and have no external side effects.

## Acceptance commands

The week plan defines the exact commands. At minimum, W1 must record results
for backend lint/format/type/test, frontend lint/type/test/build, Compose
parsing, secret scan, and Git diff review. Missing local prerequisites must be
recorded as limitations rather than worked around by weakening a gate.

## Handoff and Git rules

- Keep `main` untouched; make all W1 changes on `week/01-foundation`.
- Do not access `code_review_agent` or `%SystemDrive%/`.
- Do not push, merge, tag, or create a PR without explicit authorization.
- A local commit is permitted only after every locally runnable acceptance gate
  has passed and the evidence report contains observed results.
