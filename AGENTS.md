# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is being built as a production-grade enterprise computer-use
agent and a separate, resettable evaluation environment. The authoritative
roadmap is [docs/project-roadmap.md](docs/project-roadmap.md).

This repository is currently in **W1: Foundation**. Before starting a task,
read the roadmap and the current week's plan. Treat W1 as a governance and
bootstrap milestone, not an early implementation of the target system.

## W1 scope boundary

W1 may contain only:

- project governance, contribution, security, licence, and delivery rules;
- product, architecture, threat-model, and evaluation-protocol documents;
- a minimal FastAPI control-plane health endpoint;
- a minimal React/Vite control-plane landing page;
- a two-service local Docker Compose skeleton;
- reproducible Python and frontend dependency locks;
- local quality tooling, CI, Dependabot configuration, and secret scanning;
- a weekly plan, ADR, and evidence report.

Do **not** implement or scaffold behaviour for future milestones. In
particular, W1 must not add a Sandbox or enterprise application pages/data,
Arena tasks/graders/faults/splits, Agent loop/planner, Playwright/browser
worker, VLM/OCR, Temporal/workflows, OIDC/RBAC, persistence, external
enterprise integrations, model providers, paid-model calls, telemetry, or
benchmark/evaluation execution.

Creating empty future subsystem directories merely to mirror the long-term
roadmap is also out of scope. Document deferred topology instead.

## File ownership and change control

The precise W1 allowlist is in
[docs/agent-contract.md](docs/agent-contract.md). Change only paths owned by
that contract. Update the contract before a newly necessary path is added; if
the new path broadens scope, obtain user direction first.

`%SystemDrive%/` is a pre-existing untracked directory outside W1 ownership.
Do not inspect, copy, modify, stage, ignore, or delete it. Do not access,
copy, or modify any `code_review_agent` repository.

## Engineering conventions

- Python target: 3.13. Use `uv` and keep `apps/control_api/uv.lock` in sync
  with `apps/control_api/pyproject.toml`.
- Frontend: TypeScript, React, and Vite. Use `npm ci` from
  `apps/control_web`; commit its `package-lock.json`.
- Keep the API intentionally stateless. `/healthz` may report only static
  service metadata; it must not call a database, model, network, or external
  system.
- Keep the web page static and explicit about W1 status. It must not make API,
  model, analytics, or external-service calls.
- Use type hints, strict type checking, deterministic unit tests, and small
  modules. Avoid hidden side effects and placeholder abstractions for W2+.
- Docker images must be buildable from their owning app directory. Compose may
  run only the W1 API and web services.
- Use relative repository paths in committed documentation. Never commit a
  real API key, token, private endpoint, personal data, `.env`, local machine
  path, or generated credential.

## Required local checks

Run these after a relevant change and before a W1 handoff:

```powershell
uv sync --locked --all-groups                 # from apps/control_api
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest

npm ci                                        # from apps/control_web
npm run lint
npm run typecheck
npm run test
npm run build

docker compose -f deploy/compose/compose.yaml config
# If the Docker CLI has no Compose plugin, use:
docker-compose -f deploy/compose/compose.yaml config
gitleaks detect --source . --no-git --redact --exit-code 1
git diff --check
git diff -- . ':!%SystemDrive%'
git status --short
```

If `gitleaks` is unavailable locally, record that fact and rely on the CI
secret-scan job rather than disabling the check. Do not claim remote GitHub
Actions passed until a pushed pull request proves it.

## Git, PR, evidence, and release discipline

- Work only on a weekly branch named `week/NN-topic`; W1 uses
  `week/01-foundation`.
- Never develop directly on `main`, force-push, merge to `main`, push, or tag
  without explicit user authorization.
- Do not use broad staging such as `git add .`; stage the contract allowlist
  explicitly and review both staged and unstaged diffs.
- Every weekly PR must include its plan/contract, changed-file list, design or
  ADR rationale, exact validation commands/results, evidence, known limits,
  deferred next-week items, and paid-model use/cost (W1 must be zero).
- After an authorized, green PR merge to `main`, create the annotated weekly
  tag specified by the roadmap (W1: `w01-foundation`) and push it only with
  authorization.
- Update `docs/evidence/week-01-report.md` only with observed results. State
  failures or unavailable tools plainly; never fabricate evidence.

## Completion checklist

A W1 handoff is complete only when the contract remains satisfied, both lock
files are current, all locally available checks pass, `git diff --check` and a
full diff review are clean, no secret/private data is present, the evidence
report matches reality, and the branch has not been pushed or merged without
permission.
