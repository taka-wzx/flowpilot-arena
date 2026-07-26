# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is being built as a production-grade enterprise computer-use
agent and a separate, resettable evaluation environment. The authoritative
roadmap is [docs/project-roadmap.md](docs/project-roadmap.md).

This repository is currently in **W2: Sandbox Foundation**. W1 is merged and
tagged as `w01-foundation`. W2 establishes only the synthetic enterprise
Sandbox needed for a human to complete one observable onboarding flow.

## W2 scope boundary

W2 may contain only:

- the existing W1 control API health endpoint and static control web page;
- one local Sandbox FastAPI backend backed by PostgreSQL;
- SQLAlchemy models and one Alembic foundation migration for HRIS, ITSM, IAM,
  Asset, and Mail records;
- one React/Vite Sandbox frontend with five explicit module routes;
- manual CRUD needed to complete and inspect one synthetic onboarding flow;
- local Compose wiring for the two W1 services, PostgreSQL, Sandbox API, and
  Sandbox web;
- deterministic unit tests, dependency locks, CI updates, documentation, ADR,
  weekly plan, and observed evidence.

Do **not** implement or scaffold behaviour for later milestones. W2 must not
add Arena task specifications, general Reset/Seed, deterministic graders,
human-baseline tooling, task splits, faults, Playwright, browser workers,
DOM/accessibility observations, typed browser actions, Agent loops, screenshots,
OCR, VLM, model calls, planners, verifiers, approvals, memory, recovery,
Temporal, OIDC, RBAC, tenancy, queues, object storage, monitoring, external
enterprise integrations, shell execution, or benchmark/evaluation execution.

A hard-coded example in documentation or a fixed synthetic development fixture
is not a W3 Arena dataset. W2 must not expose a generic fixture reset or task
seeding interface.

## File ownership and change control

The precise W2 allowlist is in
[docs/agent-contract.md](docs/agent-contract.md). Change only paths owned by
that contract. Update the contract before a newly necessary path is added; if
the new path broadens scope, obtain user direction first.

`%SystemDrive%/` is a pre-existing untracked directory outside W2 ownership.
Do not inspect, copy, modify, stage, ignore, or delete it. Do not access, copy,
or modify any `code_review_agent` repository.

## Engineering conventions

- Python target: 3.13. Use `uv`; keep both Python lock files synchronized.
- Frontend: TypeScript, React, and Vite. Use `npm ci`; commit both frontend
  lock files.
- Keep `control_api` stateless and `control_web` static exactly as in W1.
- Sandbox persistence uses SQLAlchemy 2 and Alembic with PostgreSQL in Compose.
  SQLite may be used only as an isolated unit-test database.
- Each Sandbox entity must contain obviously synthetic business data only.
- Use type hints, strict type checking, deterministic tests, small modules, and
  explicit API validation. Do not add placeholder abstractions for W3+.
- Docker images must be buildable from their owning app directory.
- Use relative repository paths in committed documentation. Never commit a
  real API key, token, private endpoint, personal data, `.env`, local machine
  path, or generated credential.

## Required local checks

Run these after a relevant change and before W2 handoff:

```powershell
# W1 regression
Push-Location apps/control_api
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
Pop-Location

Push-Location apps/control_web
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
Pop-Location

# W2 Sandbox backend
Push-Location apps/sandbox_api
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
Pop-Location

# W2 Sandbox frontend
Push-Location apps/sandbox_web
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
Pop-Location

docker compose -f deploy/compose/compose.yaml config
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
# Run and record the manual synthetic onboarding flow, then:
docker compose -f deploy/compose/compose.yaml down -v

gitleaks detect --source . --no-git --redact --exit-code 1
git diff --check
git diff -- . ':!%SystemDrive%'
git status --short
```

If Docker or Gitleaks is unavailable, record that fact rather than weakening a
gate. Do not claim remote GitHub Actions passed until an authorized pushed PR
proves it.

## Git, evidence, and release discipline

- Work only on `week/02-sandbox`; never develop directly on `main`.
- Never force-push, merge, push, create a PR, or tag without explicit user
  authorization.
- Do not use broad staging such as `git add .`; stage the W2 allowlist
  explicitly and review both staged and unstaged diffs.
- The W2 evidence report must contain the exact changed files, validation
  results, migration result, Compose runtime result, manual five-module flow,
  known limitations, W3 boundary, and paid-model use/cost (zero).
- A local W2 commit is allowed only after all locally available gates pass and
  the evidence matches observed results. Stop after W2; do not begin W3.

## Completion checklist

W2 handoff is complete only when both W1 paths still pass, both Sandbox locks
are current, the migration executes, all five routes are accessible, a human
can complete and verify the synthetic onboarding flow, Compose actually starts,
all available checks pass, the full diff and secret exposure are reviewed, and
no push, PR, merge, or tag has occurred without permission.
