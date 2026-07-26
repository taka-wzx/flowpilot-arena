# Week 01 evidence report — Foundation

- Status: local W1 acceptance complete; remote CI remediation in progress
- Branch: `week/01-foundation`
- Runtime baseline: Python 3.13 (explicitly authorized for W1)
- Paid model calls and cost: 0 / 0
- Real enterprise-system calls: 0

## Scope confirmation

This delivery contains only W1 governance, documentation, a stateless FastAPI
health endpoint, a static React/Vite page, a two-service Compose skeleton,
locks, and quality/security automation. It contains no Sandbox, Arena,
Agent loop, Playwright, VLM/OCR, Temporal workflow, model provider, external
enterprise integration, persistence, or evaluation implementation.

## Changed-file record

The following paths are owned by the W1 contract. `docs/project-roadmap.md`
was preserved as the supplied roadmap and staged unchanged.

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

docs/project-roadmap.md
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

`%SystemDrive%/` was pre-existing, untracked, and outside the W1 contract. It
was not read, changed, staged, ignored, or deleted.

## Validation results

| Area | Command | Observed result |
|---|---|---|
| Python lock | `uv lock` | Passed; resolved 43 packages using CPython 3.13.0 |
| Python lock freshness | `uv lock --check` | Passed; lock remained current |
| Python install | `uv sync --locked --all-groups` | Passed; locked API and development environment installed |
| Backend lint | `uv run --locked ruff check .` | Passed |
| Backend format | `uv run --locked ruff format --check .` | Passed; 3 files already formatted |
| Backend type check | `uv run --locked mypy src` | Passed; no issues in 2 source files |
| Backend unit test | `uv run --locked pytest` | Passed; 1 test passed without warnings |
| API smoke | temporary local Uvicorn process + `GET /healthz` | Passed; returned `status=ok`, `service=control-api`, `version=0.1.0` |
| Frontend lock | `npm install --package-lock-only --ignore-scripts` | Passed; committed lock generated |
| Frontend install | `npm ci` | Passed; 0 audit vulnerabilities reported |
| Frontend lint | `npm run lint` | Passed |
| Frontend type check | `npm run typecheck` | Passed |
| Frontend unit test | `npm run test` | Passed; 1 test passed |
| Frontend build | `npm run build` | Passed; production bundle emitted |
| Dependency audit | `npm audit --json` | Passed; 0 vulnerabilities (the initial ESLint 9 transitive alert was remediated by the compatible ESLint 10 upgrade before final locking) |
| Compose | `docker-compose -f deploy/compose/compose.yaml config` | Passed; two-service configuration rendered |
| YAML syntax | PyYAML parse of CI, Dependabot, pre-commit, and Compose files | Passed; 4 files parsed |
| Local private-key check | `pre-commit run detect-private-key --files <W1 allowlist>` | Passed |

## Secret-defense evidence

- `.gitignore` excludes local environment and common credential containers;
  `.env.example` contains no secret value.
- Pre-commit's `detect-private-key` hook passed across the W1 allowlist.
- `.github/workflows/ci.yml` contains a repository-history Gitleaks job.
- The local `gitleaks` executable is not installed, so an equivalent local
  Gitleaks run could not be performed. This CI gate was not removed or
  weakened; remote execution remains pending an authorized push.

## CI and Git review evidence

- The CI workflow has separate backend-quality, frontend-quality,
  compose-config, and secret-scan jobs.
- Dependabot covers Python, npm, and GitHub Actions.
- `git diff --cached --check` passed after one README whitespace correction.
- The staged full diff review covered all 48 contract-owned paths: governance,
  documentation, API/web source and configuration, Compose, and both generated
  locks. Lock integrity was independently checked with `uv lock --check`,
  `npm ci`, npm audit, and structured lock parsing.
- A staged-file private absolute-path pattern check passed.
- Final status retains only the pre-existing excluded `%SystemDrive%/`
  directory as untracked; no non-contract file is staged.
- The first remote PR CI run confirmed backend, frontend, and Compose jobs.
  Its Gitleaks job failed because the workflow token lacked pull-request
  access (`Resource not accessible by integration`). The W1-only remediation
  grants `pull-requests: write`; the follow-up CI result must be recorded
  before merge.

## Known limitations

1. This environment provides `docker-compose` rather than the `docker compose`
   plugin. The configuration was validated with the compatible executable; CI
   uses the standard plugin available on GitHub-hosted runners.
2. The sandbox blocked Vite from writing its temporary config file under
   `node_modules` in an unprivileged process. The unchanged `npm run test` and
   `npm run build` commands both passed with normal local file permissions;
   this is an execution-sandbox limitation, not a code or dependency failure.
3. The local Gitleaks binary is absent. Pre-commit private-key detection and
   npm audit ran locally; the full Gitleaks history scan is enforced by CI once
   an authorized push occurs.
4. Branch protection, GitHub native secret scanning/push protection, required
   checks, Project board, and Milestone configuration are hosted settings that
   must be enabled by repository maintainers after a remote repository is
   available.
5. `main` remains untouched by design and therefore cannot expose the W1
   runtime until this branch passes an authorized PR merge. The W1 branch itself
   passed the recorded local runtime checks; no claim is made that unmodified
   `main` already contains them.

## W2 boundary

W2 may introduce only the enterprise Sandbox data model and basic
HRIS/ITSM/IAM/Asset/Mail pages under its own weekly contract. It must not be
backfilled into W1, and it does not authorize Agent loops, Playwright, VLM,
Temporal, workflow recovery, or evaluation work.
