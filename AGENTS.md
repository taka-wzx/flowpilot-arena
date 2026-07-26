# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is a production-oriented computer-use agent project paired
with a separate, resettable synthetic evaluation environment. The authoritative
roadmap is [docs/project-roadmap.md](docs/project-roadmap.md).

This repository is currently in **W3: Arena Foundation**. W1 and W2 are merged
and tagged as `w01-foundation` and `w02-sandbox`. W3 adds only versioned task
specifications, task-scoped deterministic Reset/Seed, database-state grading,
and manual-baseline recording for ten fixed synthetic onboarding tasks.

## W3 scope boundary

W3 may contain only:

- the unchanged W1 control API health endpoint and static control web page;
- the W2 Sandbox API, PostgreSQL schema, and five manual business pages;
- a strictly validated and checksummed Arena Task Spec format;
- ten fixed, conspicuously synthetic onboarding Task Specs;
- task-owned, transactional, idempotent Reset/Seed within the local Sandbox;
- a read-only deterministic grader based solely on database facts;
- a manual-baseline record tool that stores no browser or keyboard telemetry;
- one forward-only W3 Alembic migration, tests, locks, CI, documentation, ADR,
  weekly plan, and observed evidence.

Do **not** implement or scaffold W4+ behaviour. W3 must not add Playwright,
Selenium, browser workers, DOM/accessibility observations, typed browser
actions, Agent loops, screenshots, OCR, VLM, model calls, routers, planners,
verifiers, approvals, memory, recovery, Temporal, faults, UI randomization,
OIDC, RBAC, tenancy, queues, object storage, monitoring, external enterprise
integrations, shell/SQL/file execution interfaces, benchmarks, or Agent runs.

The ten W3 tasks are a small fixed foundation dataset, not the roadmap's final
30-template or roughly 90-instance dataset. They cover joiner flows only. Their
conservative 6/2/2 Development/Validation/Reporting allocation is frozen in
the W3 contract; Reporting specs and checksums must not be tuned before W15.

## File ownership and change control

The exact W3 allowlist is in
[docs/agent-contract.md](docs/agent-contract.md). Change only paths listed in
that contract. Add a newly necessary path to the contract before changing it;
obtain user direction first if it would broaden the W3 objective.

`%SystemDrive%/` is a pre-existing untracked directory outside W3 ownership.
Do not inspect, copy, modify, stage, scan, ignore, or delete it. Do not access,
copy, or modify any `code_review_agent` repository.

## Engineering conventions

- Python target: 3.13. Use `uv`; keep Python locks synchronized with manifests.
- Frontend: TypeScript, React, and Vite. Use `npm ci`; keep both frontend locks
  current even when W3 requires no frontend dependency change.
- Keep `control_api` stateless and `control_web` static exactly as in W1.
- Reuse the single W2 Sandbox backend and PostgreSQL deployment. Arena code and
  APIs must remain visibly separate from the five business-module APIs.
- Do not edit the released W2 migration. Add W3 schema through a new Alembic
  revision whose `down_revision` is the W2 head.
- Runtime persistence uses PostgreSQL. SQLite is permitted only for isolated,
  deterministic unit and integration tests.
- Task facts use fixed identifiers, fixed dates, `.invalid` email addresses,
  synthetic asset tags, and no random, current-time, network, model, or
  external-service inputs.
- Reset/Seed is task-scoped, transactional, deterministic, and idempotent. It
  may delete only rows carrying the selected task's ownership marker.
- The grader is side-effect free and must derive every result from structured
  predicates and database facts, never task prose or self-reported completion.
- Use strict types, reject unknown fields, and keep modules small. Do not add
  placeholder abstractions for later milestones.
- Use relative paths in committed documents. Never commit a real key, token,
  private endpoint, personal data, `.env`, machine path, or credential.

## Required local checks

Run these after relevant changes and before W3 handoff:

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

# W2/W3 Sandbox and Arena backend
Push-Location apps/sandbox_api
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
Pop-Location

# W2 Sandbox frontend regression
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
docker compose -f deploy/compose/compose.yaml exec -T sandbox-api alembic current
docker compose -f deploy/compose/compose.yaml exec -T sandbox-api alembic check
# Exercise all ten Reset/Seed and Grader paths and record observed output.
# Complete one task manually through all five W2 pages and store one anonymous
# baseline record without browser automation.
docker compose -f deploy/compose/compose.yaml down -v

gitleaks detect --source . --no-git --redact --exit-code 1
git diff --check
git diff -- . ':!%SystemDrive%'
git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%'
```

If Docker, the Compose plugin, or Gitleaks is unavailable, record that fact
rather than weakening a gate. Do not claim remote GitHub Actions passed until
an authorized pushed PR proves it.

## Git, evidence, and release discipline

- Work only on `week/03-arena`; never develop directly on `main`.
- Never force-push, merge, push, create a PR, or tag without explicit user
  authorization.
- Do not use broad staging such as `git add .`; stage the W3 allowlist
  explicitly and review staged and unstaged diffs.
- The W3 evidence report must record exact changed files; migration, Compose,
  ten-task checksum/reset/seed/grader results; the manual baseline sample;
  every local gate; limitations; W4 boundary; and paid-model cost of zero.
- A local W3 commit is allowed only after all locally available gates pass and
  evidence matches observed results. Stop after W3; do not begin W4.

## Completion checklist

W3 handoff is complete only when the new migration reaches head without model
drift; all ten strict specs and stable checksums validate; repeated Reset/Seed
is identical for every task; correct states score fully while partial, wrong,
duplicated, and over-privileged states do not; repeated grading is identical
and side-effect free; one anonymous manual baseline is recorded without
browser automation; W1/W2 regressions and all available gates pass; and no
push, PR, merge, or W3 tag occurs without permission.
