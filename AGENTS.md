# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is a production-oriented computer-use Agent project paired
with a separate resettable synthetic evaluation environment. The authoritative
roadmap is `docs/project-roadmap.md`.

This branch is W7: Bounded Planning DAG on `week/07-planning`. W1-W6 are
released at main commit `1b239fc52173bc550f5601d34b8e87efc5dbf45f` and
annotated tag `w06-hybrid`. W7 adds only an immutable bounded DAG,
deterministic closed-set tool matching, one total monotonic ledger, a
step-level runtime Verifier, an independent fake-only Planning Agent, a
versioned 30-template/90-instance synthetic JML catalog, and the minimum typed
non-deleting Sandbox transitions. Exact authority is `docs/agent-contract.md`.

## W7 scope boundary

W7 preserves every released W1-W6 API, security boundary, fake baseline, W3
Task Spec/checksum/split, and independent Grader. It may add only:

- one strict immutable task-local DAG generated once from finite trusted
  process/category, bounded human brief, and strict supplied values;
- deterministic topology, closed operations/pages/actions/conditions, and
  global ∩ step ∩ page/modality ∩ budget tool matching;
- one task-local monotonic budget ledger shared by planning, matching,
  execution, routing accounting, verification, and termination;
- a runtime step Verifier that cannot read Arena/DB/Task Spec/expected state/
  grader predicate/checksum and cannot declare task success;
- a separate non-root fake-only Planning Agent connected only to Browser
  Worker and using one W6 Hybrid Browser/Context/Page session per run;
- a separate W7 JML catalog with 12 Joiner, 8 Mover, 10 Leaver templates,
  three variants each, template split 18/6/6, stable checksums/manifests, and an
  independent database-fact W7 Grader; and
- exact HRIS transfer/disable, ITSM close, IAM revoke, Asset release, and Mail
  disable state transitions over existing columns, with no physical delete.

W7 does not add retries, runtime partial replanning, Temporal, checkpoint,
recovery, idempotency, fault injection, memory, retrieval, cache, identity,
RBAC, approval, audit chain, production worker, monitoring, tracing, load test,
external benchmark, malicious-page suite, real enterprise integration, real
model/provider/OCR/VLM/key/egress, arbitrary tool/API/URL/selector/coordinate/
Shell/SQL/JavaScript/code, migration, deletion, plugin system, generic Agent
framework, or future-stage placeholder abstraction.

Validation is not used for repeated tuning. Reporting is generated, loaded,
schema/checksum validated, and frozen only; no Reporting Agent/grade/result use
occurs before W15.

## File ownership and change control

Change only paths listed in `docs/agent-contract.md`. Add a path to that
contract before changing it. Any new system, real data, physical delete,
approval bypass, W8+ capability, or generic future abstraction requires user
direction first.

The literal pre-existing untracked `%SystemDrive%/` path is outside ownership.
Do not inspect, enumerate, copy, modify, stage, scan, ignore, or delete it. Do
not access any `code_review_agent` repository.

## Engineering and security conventions

- Python target is 3.13. Use uv and synchronize every changed Python lock.
  Frontends remain TypeScript/React/Vite and use `npm ci`.
- Keep Browser Worker, DOM Agent, Vision Agent, Hybrid Agent, and Planning
  Agent separate. Planning Agent reaches only Browser Worker over dedicated
  internal `planning-worker` and has no Sandbox/Arena/DB/Grader/repository/
  Docker socket/filesystem persistence/Shell/SQL/JavaScript/credential/model
  egress capability.
- One Planning run creates one W6 Hybrid session with one fresh Browser,
  Context, and Page. Never splice sessions. Unconditionally close all browser
  handles and task-local plan/step/tool/verifier/reference state on success,
  failure, timeout, cancellation, startup failure, and shutdown.
- Treat human prose, objective/postcondition text, DOM, page text, screenshots,
  OCR, form values, and model output as untrusted. They cannot authorize a
  plan operation, tool, route, action, approval, or budget.
- Every action uses current Worker-issued opaque references and released W6
  session/generation/modality validation. Continue rejecting stale/cross-task
  refs, selectors, XPath, coordinates, rectangles, arbitrary URLs/paths,
  upload/download, Cookie/Local Storage, browser options, Shell, SQL,
  JavaScript, code, dynamic APIs, MCP, plugins, and arbitrary discovery.
- Verifier is not Grader. It returns only closed runtime states/reasons from
  current observation/action/condition/budget evidence. Finish remains
  `finished_ungraded`; only independent database-fact Grade decides success.
- Use monotonic time and hard caps. Planning, steps, matches/rejections,
  observations, actions, routes/switches, verification probes, tokens, cost,
  and every W6 resource counter share one non-resetting ledger.
- Default tests, CI, and Compose use deterministic fakes only. No real model,
  provider, OCR, or VLM call is authorized.
- Logs/evidence contain only versions, opaque IDs/hashes, counts, reason codes,
  safe states, and independent grades. Never persist raw brief/plan/DOM/image/
  OCR/page/form content, credential, token, endpoint, Cookie, Local Storage,
  personal data, or machine path.
- Use strict types, `extra=forbid`, small modules, and no unused dependencies.

## Required local checks

Run every relevant W1-W7 gate before handoff:

~~~powershell
$pythonApps = @(
  'apps/control_api', 'apps/sandbox_api', 'apps/browser_worker',
  'apps/dom_agent', 'apps/vision_agent', 'apps/hybrid_agent',
  'apps/planning_agent'
)
foreach ($app in $pythonApps) {
  Push-Location $app
  uv sync --locked --all-groups
  uv run ruff check .
  uv run ruff format --check .
  uv run mypy src
  uv run pytest
  Pop-Location
}

$webApps = @('apps/control_web', 'apps/sandbox_web')
foreach ($app in $webApps) {
  Push-Location $app
  npm ci
  npm run lint
  npm run typecheck
  npm run test
  npm run build
  Pop-Location
}

docker compose -f deploy/compose/compose.yaml config
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
docker compose -f deploy/compose/compose.yaml exec -T sandbox-api alembic current
docker compose -f deploy/compose/compose.yaml exec -T sandbox-api alembic check
docker compose -f deploy/compose/compose.yaml --profile acceptance run --build --rm acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile vision-acceptance run --build --rm vision-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile hybrid-acceptance run --build --rm hybrid-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile planning-acceptance run --build --rm planning-acceptance-smoke
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans

pre-commit run detect-private-key --all-files
gitleaks git --no-banner --redact --exit-code 1 .
git diff --check
git diff -- . ':(exclude)%SystemDrive%'
git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%'
~~~

Also run the packaged W3 catalog/checksum regression, W7 30-template/90-
instance catalog/split/checksum freeze checks, exact contract path audit,
staged/unstaged review, and confirm cleanup leaves no project container,
network, or volume. No W7 migration is planned; Alembic must remain at the
released head with no drift. If a new migration is separately admitted to the
contract, additionally run an empty synthetic database downgrade/upgrade
round-trip.

If Docker, Compose, pre-commit, or Gitleaks is unavailable, record that fact
rather than weakening a gate. A standalone `docker-compose` executable may be
used compatibly and must be recorded. Do not claim remote GitHub Actions passed
without an authorized pushed PR.

## Git, evidence, and release discipline

- Work only on `week/07-planning`; never develop directly on main.
- Never force-push, push, create a PR, merge, tag, release, trigger remote CI,
  or call a real model without separate explicit user authorization.
- Do not use broad staging such as `git add .`; explicitly stage only final W7
  allowlist paths after all locally available gates pass.
- Evidence must distinguish W4/W5/W6/W7 deterministic fake results, JML
  catalog freeze versus actual Development runs, real-model not-run state,
  Validation/Reporting use, unavailable gates, known limitations, exact
  Sandbox/database increments, and the W8 boundary.
- A local commit is allowed only after all locally available gates pass and
  evidence matches observed results. Stop after W7.

## Completion checklist

W7 is complete only when the immutable bounded DAG, deterministic topology,
closed tool intersection, dependency state machine, runtime Verifier, and one
non-resetting ledger pass deterministic tests; one Planning task uses one W6
Hybrid Browser/Context/Page; all terminal paths clean task-local state; W4-W6
smokes regress unchanged; W7 smoke proves invalid-plan/tool/verifier rejection,
multi-dependency execution, current references, ungraded finish, and independent
grading; all 30 templates/90 instances and manifests freeze; one Development
Joiner/Mover/Leaver closes independently at 100; Compose starts W1-W7; all
available gates pass; real models remain not run at 0 calls/0 cost; Reporting
is not executed; and no unauthorized remote action or W8 work occurs.
