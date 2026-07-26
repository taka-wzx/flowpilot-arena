# Week 01 plan — Foundation

## Objective

Create the governed, reproducible foundation for FlowPilot Arena without
implementing an agent, sandbox, workflow, model integration, or evaluation
system. The authoritative scope contract is
[../agent-contract.md](../agent-contract.md).

## Planned outcomes

| Area | W1 outcome | Deliberate limit |
|---|---|---|
| Governance | Repository rules, contribution/security policy, licensing, change log, PR template, branch/tag discipline | No remote configuration changes or push |
| Documentation | Product brief, current-state architecture, threat model, evaluation protocol, ADR, evidence format | No benchmark, task, or threat-suite implementation |
| API | FastAPI application with static `GET /healthz` | No database, auth, task, agent, or external API |
| Web | React/Vite landing page showing W1 status | No data fetching, routing, login, or enterprise UI |
| Deployment | API + web Dockerfiles and parseable Compose file | No database, queue, identity, storage, monitoring, or worker |
| Quality | Python 3.13 and locked dependencies, lint, type checking, unit tests, build, CI, Dependabot, secret scan | No paid model, service integration, or remote CI claim |

## Implementation sequence

1. Freeze the W1 contract, allowlist, non-goals, assumptions, and weekly Git
   delivery rules.
2. Add project governance and foundational documentation, including a small ADR
   that explains why the monorepo begins with only runnable application roots.
3. Add the stateless FastAPI health-check application and its isolated unit
   test; lock Python dependencies with `uv`.
4. Add the static React/Vite landing page and its unit test; lock frontend
   dependencies with npm.
5. Add app-local Dockerfiles and a two-service Compose file. Validate its
   rendered configuration without starting future infrastructure.
6. Add local quality configuration and GitHub Actions jobs for backend checks,
   frontend checks/build, Compose parsing, and secret scanning.
7. Run the acceptance suite, inspect all diffs, record observed evidence and
   known limits, then create a local W1 commit if every applicable check passes.

## Validation commands

Run from the repository root unless a directory is noted.

```powershell
# Backend
Push-Location apps/control_api
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run uvicorn flowpilot_control_api.main:app --host 127.0.0.1 --port 8000
Pop-Location

# Frontend
Push-Location apps/control_web
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
Pop-Location

# Deployment, secret defense, and review
docker compose -f deploy/compose/compose.yaml config
# Or, where the Compose plugin is unavailable:
docker-compose -f deploy/compose/compose.yaml config
gitleaks detect --source . --no-git --redact --exit-code 1
git diff --check
git diff -- . ':!%SystemDrive%'
git status --short
```

For the API smoke test, start the server in one terminal and request
`http://127.0.0.1:8000/healthz` from another. Stop it immediately after the
check. If Docker or Gitleaks is absent, record the unavailable executable in
the evidence report; do not substitute an unreviewed scan or claim success.

## Acceptance criteria

- The API health endpoint returns a deterministic successful response.
- The web application has a passing unit test and production build.
- The Compose file parses successfully.
- Backend and frontend lint, type checks, and unit tests pass.
- Both lock files are present and match their manifests.
- CI contains visible jobs for lint, type-check, unit test, build, Compose
  validation, and secret scanning.
- No paid models, external enterprise systems, API keys, private absolute
  paths, or personal data are introduced.
- The evidence report lists exact modified files, command outcomes, limitations,
  W2 boundary, and a full Git diff review.

## Handoff boundary

W2 may start only after this branch is independently reviewed and merged under
the project's Git policy. W2 owns the enterprise Sandbox data model and basic
HRIS/ITSM/IAM/Asset/Mail pages. This week does not create them.
