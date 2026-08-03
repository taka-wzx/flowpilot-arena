# Week 13 evidence report - observability and replay

## Status

Implemented and locally validated on `week/13-observability`.

## Baseline

- W12 merge: `2c642a67341d0cd1c9c62b6bf883ad8df2853f40`
- W12 feature/head: `b00dff77b1626a3f347abfba485ac5a197b627a7`
- W12 tag: `w12-production`
- W12 Release: `v0.3.0 - Production Control Plane`

W12 formal Validation ordinal 3 was not rerun. Ordinal 4 was not created.
W15 Reporting was not executed.

## W13 design evidence

W13 trace/dashboard/replay is deterministic local/CI synthetic observability.
It is not a production SLO, enterprise certification, legal compliance claim,
security attestation, or ROI statement.

Dashboard choice: deterministic JSON export embedded in
`w13-run-trace-export/1.0` plus the Compose smoke artifact. No Prometheus,
Tempo, Grafana, OTel Collector, SaaS telemetry, provider billing, or egress is
added.

## Verification Log

Local tool note: this Windows host exposes standalone `docker-compose`
v5.3.1, while `docker compose` is not available. Local Compose validation used
the equivalent standalone command. Docker reported that the buildx plugin is
not installed, but classic builder completed the local synthetic builds.

Python gates:

- `apps/control_api`: `uv sync --locked --all-groups` passed.
- `apps/control_api`: `uv run ruff check .` passed.
- `apps/control_api`: `uv run ruff format --check .` passed.
- `apps/control_api`: `uv run mypy src` passed.
- `apps/control_api`: `uv run pytest --basetemp ..\..\.tmp\pytest-control-w13`
  passed: 67 passed, 1 pre-existing Starlette/httpx deprecation warning.
- `apps/workflow_worker`: `uv sync --locked --all-groups` passed.
- `apps/workflow_worker`: `uv run ruff check .` passed.
- `apps/workflow_worker`: `uv run ruff format --check .` passed.
- `apps/workflow_worker`: `uv run mypy src` passed.
- `apps/workflow_worker`: `uv run pytest --basetemp ..\..\.tmp\pytest-worker-w13`
  passed: 24 passed.

Compose and migration gates:

- Compose config passed with standalone `docker-compose`.
- Clean W1-W13 stack `up --build -d --wait` passed after using a valid local
  runtime-only recovery envelope key.
- Sandbox `alembic current`: `20260728_0003 (head)`.
- Sandbox `alembic check`: no new upgrade operations detected.
- Control `alembic current`: `20260803_0004 (head)`.
- Control `alembic check`: no new upgrade operations detected.

Deterministic local Compose smokes:

- W4 fake-model smoke passed as a command with the preserved fake baseline
  result: grade 30, `passed=false`, cost 0.
- W5 Vision smoke passed: grade 100, `passed=true`, cost 0.
- W6 Hybrid smoke passed: grade 100, `passed=true`, cost 0.
- W7 Planning smoke passed: 30 templates, 90 instances, development grades 100,
  actual cost 0, external calls 0.
- W8 Recovery smoke passed: duplicate side effects 0, actual model cost 0,
  `validation_run=false`, `reporting_executed=false`.
- W9 Context smoke passed: real model/provider/OCR/VLM/embedding calls 0,
  `validation_run=false`, `reporting_executed=false`.
- W10 Identity smoke passed: cross-organization rejects 7,
  concurrent exact-one-winner true, real identity/model provider calls 0,
  `validation_run=false`, `reporting_executed=false`.
- W11 Approval/Audit smoke passed: audit chain valid, duplicate side effects 0,
  sensitive information scan passed, real identity/model provider calls 0,
  `validation_run=false`, `reporting_executed=false`.
- W12 Production smoke passed: max browser concurrency 4, cross-tenant
  rejection 1, audit valid true, real calls 0, `reporting_executed=false`.
- W13 Observability smoke passed: terminal status `finished_ungraded`,
  independent grader passed true, event count 20, replay step count 20,
  phases covered admission, approval, outbox, lease, dispatch, workflow,
  recovery, planning, browser, receipt, cost, grader, audit, and terminal.
  Real calls for IdP, account data, model, provider, OCR, VLM, embedding, and
  egress were all 0; real cost was 0; Reporting was false.

The first Compose startup attempt failed closed because the local runtime
envelope key supplied to the command was not valid base64. This was an operator
setup error; Workflow Worker and Recovery Worker rejected it before running.
The clean retry used a valid local synthetic key and passed.

Final local checks:

- `docker-compose -f deploy/compose/compose.yaml down -v --remove-orphans`
  completed and removed the local synthetic project containers, networks, and
  volumes.
- `pre-commit run detect-private-key --all-files` passed after rerunning with
  access to the local pre-commit cache.
- `gitleaks git --no-banner --redact --exit-code 1 .` passed after rerunning
  with access to the local executable.
- `git diff --check -- . ':(exclude)%SystemDrive%' ':(exclude)code_review_agent'`
  passed.
- Exact allowlist check passed: all 22 changed code/doc paths are inside the
  23-path W13 allowlist. `apps/workflow_worker/tests/conftest.py` remains
  authorized but unchanged.
- `git diff -- . ':(exclude)%SystemDrive%' ':(exclude)code_review_agent'` was
  reviewed.
- `git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%'`
  showed only W13 allowlist changes plus pre-existing `.tmp` local artifacts.
  The two pytest basetemp directories created during this run were removed.

## Remote Non-Actions

- No push.
- No PR.
- No merge.
- No tag.
- No Release.
- No workflow dispatch or remote CI rerun.
- No real provider, model, OCR, VLM, embedding, IdP, billing, account-data, or
  egress call.
