# Week 02 plan — Sandbox Foundation

## Objective

Build a small local enterprise Sandbox with one persistent backend and five
explicit web modules so a human can complete one synthetic onboarding flow.
The authoritative boundary is [../agent-contract.md](../agent-contract.md).

## Planned outcomes

| Area | W2 outcome | Deliberate limit |
|---|---|---|
| Data | Five linked SQLAlchemy entities and one Alembic migration | No Arena task, reset, seed, grader, split, or fault model |
| API | FastAPI create/list endpoints for the onboarding closure | No auth, tenancy, workflow, update/delete, or external calls |
| Web | React routes for HRIS, ITSM, IAM, Asset, and Mail | No Playwright, browser worker, agent, or visual automation |
| Runtime | PostgreSQL plus Sandbox API/web added to Compose | No queue, object storage, Keycloak, Temporal, or monitoring |
| Quality | Backend/frontend locks, lint, type checks, unit tests, build, CI | No benchmark or paid model execution |
| Evidence | Migration, runtime, manual-flow, diff, and secret-review facts | No claim about remote CI before an authorized PR |

## Implementation sequence

1. Freeze W2 rules, exact paths, assumptions, manual closure, plan, evidence
   template, and the single-backend/PostgreSQL ADR.
2. Implement the Sandbox ORM schema, migration, FastAPI endpoints, validation,
   and isolated unit tests; generate the Python lock under 3.13.
3. Implement the five explicit React routes and create/list forms, with mocked
   frontend unit tests and a locked npm dependency graph.
4. Add image-local Docker builds and Compose wiring for PostgreSQL, Sandbox API,
   and Sandbox web while preserving both W1 services.
5. Update CI, Dependabot, README, architecture, threat model, and changelog.
6. Run all W1 regression and W2 quality gates, execute the migration, start the
   complete Compose runtime, perform the frozen synthetic onboarding flow, and
   inspect all five final states.
7. Review the full contract-owned diff and secret exposure, record only
   observed evidence, explicitly stage the allowlist, create one local commit,
   and stop before W3.

## Frozen synthetic manual flow

Use these conspicuously fictional values when recording runtime evidence:

| Module | Values |
|---|---|
| HRIS | Avery Example; `avery.example@flowpilot.invalid`; Platform Engineering; Sandbox Engineer; Shanghai Lab; start `2026-08-03` |
| ITSM | `Synthetic onboarding for Avery Example`; status `open` |
| IAM | username `avery.example`; role `employee`; status `active` |
| Asset | tag `SYN-LAPTOP-0001`; laptop model `ExampleBook 14`; status `assigned` |
| Mail | `avery.example@flowpilot.invalid`; status `active` |

The `.invalid` top-level domain and names above are test-only. This table is a
human development recipe, not a resettable Arena dataset.

## Validation commands

Run the W1 and W2 app-local commands listed in [../../AGENTS.md](../../AGENTS.md),
then:

```powershell
docker compose -f deploy/compose/compose.yaml config
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps

# Confirm both W1 and W2 health paths.
Invoke-RestMethod http://127.0.0.1:8000/healthz
Invoke-RestMethod http://127.0.0.1:8001/healthz

# Complete the frozen flow at http://127.0.0.1:5174 and revisit all modules.

docker compose -f deploy/compose/compose.yaml down -v
gitleaks detect --source . --no-git --redact --exit-code 1
git diff --check
git diff -- . ':!%SystemDrive%'
git status --short
```

The Sandbox API container runs `alembic upgrade head` before Uvicorn. Its log
and successful health response are migration/runtime evidence. Missing Docker
or Gitleaks must be reported as unavailable, not silently substituted.

## Acceptance criteria

- PostgreSQL becomes healthy and the Alembic upgrade reaches head.
- Both W1 services remain runnable and their original quality checks pass.
- All five Sandbox routes render and their create/list API paths are tested.
- A human completes the fixed synthetic onboarding sequence and sees the final
  linked state across all modules.
- All four dependency locks match their manifests.
- Backend/frontend lint, type checks, tests, builds, Compose parsing, runtime,
  diff checks, and available secret scans pass.
- No prohibited W3+ behaviour, paid model, real external system, real identity,
  credential, personal data, or private absolute path is present.

## Handoff boundary

W3 may later define resettable Arena data, tasks, seed/reset semantics, graders,
and human-baseline tooling. W2's schema and manual synthetic recipe provide no
such behaviour and must not be described as evaluation infrastructure.
