# Week 02 evidence report — Sandbox Foundation

- Status: local W2 quality, runtime, staged diff, and private-key acceptance complete
- Branch: `week/02-sandbox`
- Baseline commit: `1c23f79` (`w01-foundation`)
- Runtime baseline: Python 3.13
- Paid model calls and cost: 0 / 0
- Real enterprise-system or external API calls: 0

## Scope confirmation

W2 contains one local Sandbox FastAPI backend, PostgreSQL persistence,
SQLAlchemy models, one Alembic foundation migration, and one React/Vite web app
with HRIS, ITSM, IAM, Asset, and Mail routes. It preserves both W1 services.

The fixed Avery Example development recipe is conspicuously synthetic and is
not a W3 resettable Arena dataset, task seed, task specification, grader, split,
fault, or human-baseline tool. No Playwright, browser worker, Agent loop, model,
OCR/VLM, Temporal, planner, verifier, approval, identity, RBAC, tenant, queue,
object storage, monitoring, real enterprise integration, shell-execution
feature, external API, or paid model was added.

## Changed-file record

The W2 contract owns exactly these 53 changed or created files:

```text
AGENTS.md
README.md
CHANGELOG.md
.github/dependabot.yml
.github/workflows/ci.yml
docs/agent-contract.md
docs/architecture.md
docs/threat-model.md
docs/adr/0002-w2-single-sandbox-postgres.md
docs/plans/week-02-sandbox.md
docs/evidence/week-02-report.md

apps/sandbox_api/.dockerignore
apps/sandbox_api/Dockerfile
apps/sandbox_api/alembic.ini
apps/sandbox_api/pyproject.toml
apps/sandbox_api/uv.lock
apps/sandbox_api/migrations/env.py
apps/sandbox_api/migrations/script.py.mako
apps/sandbox_api/migrations/versions/20260726_0001_sandbox_foundation.py
apps/sandbox_api/src/flowpilot_sandbox_api/__init__.py
apps/sandbox_api/src/flowpilot_sandbox_api/database.py
apps/sandbox_api/src/flowpilot_sandbox_api/main.py
apps/sandbox_api/src/flowpilot_sandbox_api/models.py
apps/sandbox_api/src/flowpilot_sandbox_api/schemas.py
apps/sandbox_api/tests/conftest.py
apps/sandbox_api/tests/test_api.py
apps/sandbox_api/tests/test_models.py

apps/sandbox_web/.dockerignore
apps/sandbox_web/Dockerfile
apps/sandbox_web/nginx.conf
apps/sandbox_web/eslint.config.js
apps/sandbox_web/index.html
apps/sandbox_web/package.json
apps/sandbox_web/package-lock.json
apps/sandbox_web/tsconfig.json
apps/sandbox_web/tsconfig.app.json
apps/sandbox_web/tsconfig.node.json
apps/sandbox_web/vite.config.ts
apps/sandbox_web/src/App.tsx
apps/sandbox_web/src/App.css
apps/sandbox_web/src/App.test.tsx
apps/sandbox_web/src/api.ts
apps/sandbox_web/src/index.css
apps/sandbox_web/src/main.tsx
apps/sandbox_web/src/setupTests.ts
apps/sandbox_web/src/types.ts
apps/sandbox_web/src/vite-env.d.ts
apps/sandbox_web/src/pages/HrisPage.tsx
apps/sandbox_web/src/pages/ItsmPage.tsx
apps/sandbox_web/src/pages/IamPage.tsx
apps/sandbox_web/src/pages/AssetPage.tsx
apps/sandbox_web/src/pages/MailPage.tsx

deploy/compose/compose.yaml
```

`%SystemDrive%/` remained pre-existing, untracked, and outside the contract. It
was not read, copied, modified, staged, ignored, deleted, or scanned. No
`code_review_agent` repository was accessed.

## Validation results

| Area | Command | Observed result |
|---|---|---|
| W1 backend lock | `uv sync --locked --all-groups` | Passed; 43 locked packages resolved |
| W1 backend lint/format/type | Ruff check, Ruff format check, mypy `src` | Passed; 3 files formatted, no type issues in 2 source files |
| W1 backend unit test | `uv run pytest` | Passed; 1 test |
| W1 frontend lock | `npm.cmd ci` | Passed; 250 packages audited, 0 vulnerabilities |
| W1 frontend quality | lint, typecheck, test, build | Passed; 1 test and production build |
| Sandbox backend lock | `uv sync --locked --all-groups` | Passed; 42 locked packages resolved / 41 installed |
| Sandbox backend lint/format/type | Ruff check, Ruff format check, mypy `src` | Passed; 10 files formatted, no type issues in 5 source files |
| Sandbox backend unit test | `uv run pytest` | Passed; 6 tests; one upstream FastAPI/Starlette TestClient deprecation warning |
| Sandbox frontend lock | `npm.cmd ci` | Passed; 254 packages installed from the lock |
| Sandbox frontend quality | lint, typecheck, test, build | Passed; 6 tests and production build (48 modules) |
| Compose configuration | `docker-compose -f deploy/compose/compose.yaml config` | Passed; local CLI lacks the `docker compose` plugin |
| Compose build/runtime | `docker-compose ... up --build -d`, then `ps` | Passed after starting Docker Desktop; all five containers healthy |
| Migration startup | Sandbox API logs from a newly created empty volume | Passed; ran upgrade to `20260726_0001` with PostgreSQL transactional DDL |
| Migration revision | `docker-compose ... exec -T sandbox-api alembic current` | Passed; `20260726_0001 (head)` |
| Migration/model drift | `docker-compose ... exec -T sandbox-api alembic check` | Passed; no new upgrade operations detected |
| W1/W2 health smoke | `GET :8000/healthz` and `GET :8001/healthz` | Passed; both returned `status=ok` |
| Five web routes | HTTP requests to `/hris`, `/itsm`, `/iam`, `/assets`, `/mail` on port 5174 | Passed; every route returned 200 |
| Persistence | Rebuilt Sandbox API while retaining the DB volume, then listed all modules | Passed; all five linked records remained |
| Router version | `npm.cmd ls react-router-dom react-router --depth=1` | Passed; both resolved to pinned `7.11.0` |
| Diff integrity | `git diff --cached --check` and staged full review | Passed; exactly 53 contract files, no unstaged diff |
| Private-key check | pre-commit `detect-private-key --all-files` on the staged index | Passed |

The first request to `/assets` exposed a production-server route collision with
Vite's static `assets` directory. Nginx originally redirected the business path
and lost the published port. Exact `/assets` and `/assets/` SPA locations were
added, the image was rebuilt, and all five routes then returned 200.

## Manual onboarding evidence

The final run started from a newly created empty PostgreSQL volume and used the
same-origin Sandbox web proxy (`http://127.0.0.1:5174/api/...`) that the UI uses.
Frontend tests exercised the five routes and an HRIS form submission; no
Playwright or other browser automation was used.

| Step | Observable record | Result |
|---|---|---|
| HRIS | Avery Example; `.invalid` work email; employee `#1` | Passed; `confirmed` |
| ITSM | Synthetic onboarding ticket linked to employee `#1` | Passed; `open` |
| IAM | `avery.example`, ordinary `employee` role, linked to `#1` | Passed; `active` |
| Asset | `SYN-LAPTOP-0001`, ExampleBook 14, linked to `#1` | Passed; `assigned` |
| Mail | `.invalid` mailbox linked to employee `#1` | Passed; `active` |
| Final review | Listed all five modules and requested all five web routes | Passed; one linked record per module and every page returned 200 |

This establishes the manual UI/API closure capability without claiming an
automated end-to-end browser test. The synthetic database volume is removed at
handoff with the operator-only Compose `down -v` command; the final removal
completed successfully.

## Security and dependency review

- API validation rejects deliverable email domains and non-`SYN-` asset tags.
- IAM role and status, device type/status, ticket status, and employee/mailbox
  statuses are closed W2 literals; no administrator role is accepted.
- All downstream rows use foreign keys; business identifiers that must be
  singular are protected by unique constraints and API conflict handling.
- The W2 API exposes create/list only. There is no update, delete, reset, seed,
  grader, outbound integration, analytics, model, or shell-execution endpoint.
- The latest unconstrained React Router resolution initially produced two
  high-severity audit entries from one advisory affecting versions beginning at
  7.12. The manifest and lock were pinned to `7.11.0`, outside the audit's
  reported affected range, and the installed tree confirms that version.
- The local `gitleaks` executable is unavailable. The CI Gitleaks job remains
  enabled and unchanged in strength; no remote pass is claimed.

## Known limitations

1. This host has `docker-compose` but no `docker compose` plugin. Configuration,
   build, startup, migration, health, and runtime acceptance all passed with the
   compatible executable. Docker also warned that the optional Buildx plugin is
   absent and used the classic builder successfully.
2. Docker Desktop was initially stopped. A restricted launch omitted the
   standard `ProgramData` environment and its backend exited; restarting it
   with the normal user environment plus `ProgramData` restored the engine.
   This was a host startup issue, not a repository change.
3. Sandbox API tests pass with one upstream FastAPI/Starlette warning that the
   current `httpx` TestClient path is deprecated in favor of a future client.
4. After the initial useful vulnerability response, two final Sandbox npm audit
   retries failed because the npm advisory endpoint returned a gzip body as
   malformed JSON. The fixed installed Router versions were verified locally;
   a final zero-vulnerability audit result is therefore not claimed.
5. The local Gitleaks binary is unavailable. The repository retains its CI
   history scan, and the explicit staged private-key check is recorded
   separately.
6. W2 is unauthenticated, local-only, create/list-only, and not production-ready.
   It has no cross-step transaction, update/reconciliation UI, or mover/leaver
   flow. OIDC, RBAC, and tenancy remain W10.
7. The same-origin HTTP closure and frontend unit tests were observed, but no
   automated browser/e2e claim is made because Playwright is explicitly out of
   W2 scope.

## W3 boundary

W3 owns Arena Task Spec, generic Reset/Seed, deterministic Grader, task splits,
faults, and human-baseline tooling. None was backfilled into W2. Work stops
after this W2 handoff; no W3 implementation has begun.
