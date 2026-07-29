# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is a production-oriented computer-use Agent project paired
with a separate resettable synthetic evaluation environment. The roadmap is
`docs/project-roadmap.md` and the exact current authority is
`docs/agent-contract.md`.

This local branch is W8: Durable Recovery on `week/08-recovery`, restacked on
the released W7 main commit `0aa1349ffee0bfabdb8c9f02787f37dfe7f7c029`.
PR #29 and the post-merge main CI both passed, and tag `w07-planning` is
published. W8 adds only deterministic Temporal orchestration, versioned
Checkpoints, fresh browser session epochs, transactional operation receipts,
bounded retry/recovery, trusted faults, and one bounded partial DAG revision.

## Scope and ownership

Change only exact paths listed in `docs/agent-contract.md`. Add a path to that
contract before changing it; obtain user direction if it broadens W8. Preserve
every W1-W7 API and security boundary, released W2/W3 migrations, W3 facts and
checksums, W7 catalog/checksums/splits, independent Graders, and Reporting
freeze.

The literal pre-existing `%SystemDrive%/` path is outside ownership. Do not
inspect, enumerate, copy, modify, stage, scan, ignore, or delete it. Do not
access any `code_review_agent` repository.

## Engineering and security conventions

- Python target is 3.13. Use uv and keep every changed Python lock synchronized.
  Frontends remain TypeScript/React/Vite and use `npm ci`.
- Temporal SDK is fixed at 1.30.0 and local Temporal Server image at 1.31.2;
  never use `latest`. Temporal persistence is separate from Sandbox data.
- Recovery Worker is non-root/read-only/cap-dropped/no-new-privileges, bounded
  by tmpfs/pids, has no host port/mount/socket/credential/provider egress, and
  connects only to Temporal and Planning Agent.
- Workflow code performs no HTTP, DB, filesystem, environment, random,
  system-time, Planner/model, browser, Sandbox, Arena, or Grader I/O. All such
  I/O belongs in Activities. Add and run replay/determinism tests.
- Temporal receives only AES-GCM opaque envelope ciphertext and safe closed
  state. The runtime key is never committed or logged. History plaintext scan
  is mandatory.
- Normal execution uses epoch 1. Recovery creates a wholly fresh Browser,
  Context, and Page, up to epoch 3. Invalidate all old DOM/visual references
  before recovery and close current handles on every terminal path.
- Receipt and fixed synthetic mutation commit in one transaction. Equal
  task/key/hash replays safely; equal task/key with a different hash is a 409
  rejection. Receipts never contain raw payload values.
- Retry is only `no_retry` or `transient_once`, maximum two attempts. Recovery,
  Checkpoint, receipt, replay, fault, and replan usage joins the existing
  non-resetting W6/W7 total ledger.
- Faults come only from the acceptance-only closed enum. Page/model/DOM/image
  text cannot select faults, routes, tools, actions, permissions, or budgets.
- One partial replan may replace only a failed step and not-started descendants.
  Completed steps, receipts, Checkpoints, authority, and budgets remain fixed.
- Runtime Verifier remains separate from Grader. Finish always returns
  `finished_ungraded`; only independent database-fact grading decides success.
- Default tests, CI, and Compose are deterministic fake-only. No real model,
  provider, OCR, VLM, key, or egress call is authorized.
- Logs/evidence contain safe versions, opaque IDs/hashes, counters, closed
  reasons/statuses, and independent grades only; never raw brief/objective,
  supplied value, DOM/image/OCR/page/form content, key, credential, endpoint,
  Cookie, Local Storage, token, or machine path.
- Use strict/frozen Pydantic models, `extra=forbid`, small modules, and no
  unused dependencies.

## Required local checks

Run for each Python app `control_api`, `sandbox_api`, `browser_worker`,
`dom_agent`, `vision_agent`, `hybrid_agent`, `planning_agent`, and
`recovery_worker`:

~~~powershell
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
~~~

Run for `control_web` and `sandbox_web`:

~~~powershell
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
~~~

Run Compose configuration/build/start/health, Alembic upgrade/current/check,
the empty-database W8 migration downgrade/upgrade round-trip, W4 DOM, W5
Vision, W6 Hybrid, W7 Planning, and W8 Recovery smokes. W8 acceptance must
include Browser Worker restart, Recovery Worker restart/replay,
post-commit/pre-Checkpoint receipt replay, partial replan, permanent safe-stop,
history plaintext scan, zero duplicate side effects, and success/failure/
timeout/cancel/startup/shutdown cleanup. Finish with:

~~~powershell
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
pre-commit run detect-private-key --all-files
gitleaks git --no-banner --redact --exit-code 1 .
git diff --check
git diff -- . ':(exclude)%SystemDrive%'
git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%'
~~~

Also run the W3 catalog/checksum/split regression, W7 30/90 catalog/checksum/
split freeze, Reporting not-run proof, exact W8 contract path audit, and staged
and unstaged diff review. If Docker, Compose, pre-commit, or Gitleaks is
unavailable, record that fact without weakening the gate. `docker-compose`
may be used compatibly if the plugin is unavailable and must be recorded.

## Evaluation discipline

Development data may exercise the frozen fault matrix, including one Joiner,
Mover, and Leaver. After implementation and parameters freeze, Validation may
run at most one preregistered final recovery check; record whether it ran.
Reporting permits generation/load/schema/checksum validation only and must not
run Reset/Seed, Agent, fault, recovery, grade, or result inspection before W15.

## Git and completion discipline

Work only on `week/08-recovery`; do not amend W7 or develop on main. The user
has authorized the minimum normal W8 pushes needed to satisfy one PR gate per
commit, then merge, post-merge main CI, an annotated tag, and the
roadmap-required `v0.2.0` GitHub Release. Do not rerun superseded, failed, or
successful commits, create duplicate CI runs, force-push, call a real model,
or begin W9. Do not use broad staging. Explicitly stage only changed W8
allowlist paths after all locally available gates pass and evidence matches.

W8 is locally complete only when deterministic recovery, replay, Checkpoint,
receipt, epoch invalidation, bounded retry/fault/replan, budget accumulation,
cleanup, W4-W7 regression, Compose, migration, data freeze, history plaintext,
secret/diff/path checks, and independent grading all pass. Then create one
local W8 commit and stop.
