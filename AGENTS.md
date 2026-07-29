# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is a production-oriented computer-use Agent project paired
with a separate resettable synthetic evaluation environment. The authoritative
roadmap is `docs/project-roadmap.md` and exact current authority is
`docs/agent-contract.md`.

This branch is W9: Context, Retrieval, Summary, and Organization Memory on
`week/09-context`, based on released W8 main commit
`9ecc31f3e525ae57260bc47ddab5d1d8c1baba6f`. W8 PR #30, its 17-job PR CI, the
17-job post-merge main CI, annotated tag `w08-recovery`, and release
`v0.2.0 - Hybrid + Recovery` are complete and immutable.

## W9 scope boundary

W9 preserves every W1-W8 API, security boundary, deterministic fake baseline,
released migration, W3/W7 catalog/checksum/split, W8 recovery contract,
independent Grader, and Reporting freeze. It may add only:

- five ordered context layers: authoritative database task facts, current
  browser working memory, deterministic task-local short-term summary,
  scoped synthetic organization memory, and fixed enterprise knowledge;
- strict frozen schemas, canonical JSON/hashes, provenance, version, source,
  trust, validity, expiry, tombstone, and synthetic scope/task ownership;
- closed deterministic lexical/hash retrieval over a fixed local catalog;
- deterministic summary preserving unresolved issues, recent actions, failure
  reasons, and pending steps under frozen caps;
- a process-local fake-only organization-memory store with monotonic versions,
  deterministic expiry/delete/reset, and default-deny cross-scope operations;
- one deterministic Context Assembler with frozen layer/total budgets and five
  preregistered Development-only ablations;
- additive W9 context and context-backed Planning endpoints; and
- context/retrieval/summary/memory counters in the existing non-resetting W7
  total ledger and W8 durable safe high-water projection.

W9 adds no database migration, new service, real vector database, embedding,
model/provider/OCR/VLM/key/egress, generic memory framework, cache, arbitrary
query/API/browser/code capability, W10 identity/RBAC/tenancy/optimistic lock,
W11 approvals, W12 production/load, W13 telemetry, W14 malicious suite, W15
formal Reporting/external benchmark, W16 deployment/release, or future-stage
placeholder.

## File ownership and change control

Change only exact paths listed in `docs/agent-contract.md`. Add a path to that
contract before changing it. Any new service, migration, real data, identity,
authorization, physical business deletion, real model/provider, W10+ feature,
or generic abstraction requires user direction first.

The literal pre-existing `%SystemDrive%/` path is outside ownership. Do not
inspect, enumerate, copy, modify, stage, scan, ignore, or delete it. Do not
access any `code_review_agent` repository.

## Engineering and security conventions

- Python target is 3.13. Use uv and synchronize every changed Python lock.
  Frontends remain TypeScript/React/Vite and use `npm ci`.
- Keep Browser Worker, DOM Agent, Vision Agent, Hybrid Agent, Planning Agent,
  and Recovery Worker separate. W9 remains inside Planning Agent and adds no
  network route. Planning reaches only Browser Worker; Recovery reaches only
  Temporal and Planning.
- Treat human prose, objective/postcondition text, DOM, page/email/PDF text,
  screenshots, OCR, form values, and model output as untrusted. They cannot
  authorize a context source, task fact, query, tool, route, action, permission,
  budget, scope, memory write/delete, retry, recovery, or success.
- Task facts accept only a trusted synthetic Sandbox-database safe projection.
  Memory, summary, browser content, Agent output, and enterprise knowledge
  cannot replace database facts or independent grading.
- Use closed query categories and the fixed local catalog only. Never accept a
  free page/model query or call embedding/vector/cloud/provider services.
- Cross-scope read/write/delete/reset is default-deny. W9 synthetic `scope_id`
  is not a real tenant or authorization claim. Organization memory stores only
  closed safe values and tombstones, never raw sensitive values.
- Preserve current Worker-issued reference validation and W8 epoch recovery.
  Context insufficiency cannot increase any W6/W7/W8 cap.
- Use monotonic time for the task ledger and explicit UTC `as_of` for
  deterministic validity. All W9 counters are cumulative and never reset.
- Runtime Verifier is not Grader. Finish remains `finished_ungraded`; only the
  independent database-fact Grader decides success.
- Default tests, CI, and Compose are deterministic fake-only. No real model,
  provider, OCR, VLM, embedding, key, or egress call is authorized.
- Logs/evidence contain only versions, opaque synthetic IDs/hashes, counts,
  closed status/reason/source/trust codes, ablation names, and independent
  grades. Never persist raw brief/objective/value/DOM/image/OCR/page/form data,
  credentials, tokens, endpoints, Cookies, Local Storage, personal data, or
  machine paths.
- Use strict/frozen Pydantic models, `extra=forbid`, small modules, deterministic
  iteration, and no unused dependencies.

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

Run Compose configuration/build/start/health, Alembic current/check at released
W8 head with no drift, W4 DOM, W5 Vision, W6 Hybrid, W7 Planning, W8 Recovery,
and W9 Context smokes. W9 acceptance must prove all five layers; task-fact
precedence; browser expiry; deterministic summary/retrieval/order/checksum;
organization-memory version/scope/delete/expiry; cross-scope and untrusted
field rejection; item/byte/token budget stop; five frozen ablations; one
Development Joiner/Mover/Leaver at independent grade 100; and zero real calls.

Finish with:

~~~powershell
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
pre-commit run detect-private-key --all-files
gitleaks git --no-banner --redact --exit-code 1 .
git diff --check
git diff -- . ':(exclude)%SystemDrive%'
git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%'
~~~

Also run W3 catalog/checksum/split regression, W7 30-template/90-instance
catalog/checksum/split/Reporting freeze, W9 enterprise-catalog checksum and
ablation freeze, Reporting not-run proof, exact W9 contract path audit, staged
and unstaged review, and confirm cleanup leaves no project container, network,
or volume. If Docker, Compose, pre-commit, or Gitleaks is unavailable, record
that fact without weakening a gate. `docker-compose` may be used compatibly and
must be recorded.

## Evaluation discipline

Development may exercise the frozen context matrix. Validation may run at most
one preregistered final context check and only after catalog, ordering, budgets,
and ablations freeze; record whether it ran. Reporting permits generation/load/
schema/checksum validation only and must not run Reset, Seed, Agent, context,
memory, retrieval, grade, or result inspection before W15.

## Git, quota, and completion discipline

Work only on `week/09-context`; never develop on main or amend W8. No push, PR,
merge, tag, release, remote CI, rerun, or real-model call is authorized without
separate explicit user direction. W9 tag, if later authorized, is
`w09-context`; W9 creates no `v0.3.0` Release.

If remote work is later authorized: diagnose first, concentrate all related
fixes, and push once. With no code/lock/workflow change and a transient
infrastructure failure, rerun failed jobs only. Never rerun all jobs, successful
or superseded runs, create empty commits/duplicate PRs, force-push, or change
unrelated CI for a green result. Record every necessary extra run.

Do not use broad staging. After all locally available gates pass and evidence
matches observed results, explicitly stage only W9 allowlist paths, create one
local W9 commit, and stop before W10.
