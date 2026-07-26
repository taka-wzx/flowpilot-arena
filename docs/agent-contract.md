# W3 agent contract — Arena Foundation

## Authority and objective

This contract translates the W3 row of
[project-roadmap.md](project-roadmap.md) and the user-authorized W3 brief into a
bounded implementation agreement for `week/03-arena`.

The sole outcome is a versioned and deterministic local Arena foundation for
ten fixed synthetic joiner tasks. A human can select a task, Reset/Seed its
owned Sandbox facts, perform work through the existing five business pages,
request a database-fact grade, and store an anonymous manual-baseline record.
W3 does not execute an Agent or automate a browser.

## Baseline observed before W3 edits

- W2 PR #13 is merged into `main` at merge commit `5d4647b`.
- The final W2 pull-request checks passed, including both `Secret scan` jobs.
- The annotated `w02-sandbox` tag object is present locally and on `origin`; it
  dereferences locally to the W2 merge commit.
- `main` and `origin/main` were synchronized with `git pull --ff-only`.
- `week/03-arena` was recreated from synchronized `main`.
- No tracked or contract-eligible untracked changes existed at the boundary.
- The excluded `%SystemDrive%/` entry was not inspected, copied, modified,
  staged, scanned, ignored, or deleted. No `code_review_agent` repository was
  accessed.

## Conservative W3 architecture decisions

1. Arena remains an explicit package and `/api/arena` router inside the single
   W2 `sandbox_api` deployment. It does not enter `control_api`, create a new
   service, or mix management endpoints into the five business routers.
2. Task Specs are ten repository-versioned JSON resources validated into
   strict Pydantic models. Their canonical SHA-256 checksum covers the
   normalized spec excluding only the checksum field itself.
3. Each Sandbox business row gains a nullable `arena_task_id`. Null continues
   to mean W2 manual/development data. W3 Reset deletes, in dependency order,
   only rows whose marker exactly equals the requested task ID and then inserts
   the task's fixed initial facts in one transaction.
4. Downstream records created through existing business APIs inherit the
   selected employee's `arena_task_id`; the caller cannot supply ownership.
   Every task seeds a target and a clearly labelled decoy employee so wrong
   associations remain observable, task-owned, and safely resettable.
5. Specs are source-controlled resources, not mutable database rows. Test or
   runtime results are never written into the specs.
6. The grader uses only SQLAlchemy reads over Sandbox fact tables. It evaluates
   enumerated predicate kinds and structured expected state; it never infers
   conditions from titles, actor instructions, notes, logs, pages, or models.
7. Human baseline entries use caller-supplied anonymous aliases and timestamps.
   They store task ID, start/end, derived duration, action count, a final score
   derived from the read-only Grader at record time, and optional synthetic
   notes only. The caller cannot declare the score. Entries collect no keyboard,
   screenshot, page, selector, browser, or personal telemetry.
8. No frontend change is needed for Arena management. Reset/Seed, grade, task
   catalog, and baseline recording use narrow local management APIs; the five
   W2 pages remain the only manual business-action surfaces.

These decisions are detailed in
[adr/0003-w3-embedded-task-owned-arena.md](adr/0003-w3-embedded-task-owned-arena.md).

## Fixed task allocation and freeze rule

The ten specs are distinct fixed joiner tasks, not claims about the final
30-template dataset:

| Split | Task IDs | W3 rule |
|---|---|---|
| Development | `w3-joiner-001` through `w3-joiner-006` | May change only while completing W3, with checksum updates and evidence |
| Validation | `w3-joiner-007`, `w3-joiner-008` | Used only for W3 validation; later changes require a new fixture/spec version |
| Reporting | `w3-joiner-009`, `w3-joiner-010` | Content and canonical checksums freeze when first committed; do not tune against results before W15 |

All ten use `schema_version = "1.0"` and `fixture_version = "w3-fixture-v1"`.
The catalog additionally has a deterministic checksum derived from the sorted
`task_id`/canonical-checksum pairs. Splits are by these fixed specifications;
no randomized instance split exists.

## Exact W3 file allowlist

Only the following paths may be created or modified in W3:

```text
AGENTS.md
README.md
CHANGELOG.md

.github/workflows/ci.yml

docs/agent-contract.md
docs/architecture.md
docs/threat-model.md
docs/evaluation-protocol.md
docs/adr/0003-w3-embedded-task-owned-arena.md
docs/plans/week-03-arena.md
docs/evidence/week-03-report.md

apps/sandbox_api/pyproject.toml
apps/sandbox_api/uv.lock
apps/sandbox_api/migrations/versions/20260726_0002_arena_foundation.py
apps/sandbox_api/src/flowpilot_sandbox_api/main.py
apps/sandbox_api/src/flowpilot_sandbox_api/models.py
apps/sandbox_api/src/flowpilot_sandbox_api/schemas.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/__init__.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/schemas.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/catalog.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/service.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/grader.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/baselines.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/router.py
apps/sandbox_api/src/flowpilot_sandbox_api/arena/tasks/w3-joiner-001.json
apps/sandbox_api/src/flowpilot_sandbox_api/arena/tasks/w3-joiner-002.json
apps/sandbox_api/src/flowpilot_sandbox_api/arena/tasks/w3-joiner-003.json
apps/sandbox_api/src/flowpilot_sandbox_api/arena/tasks/w3-joiner-004.json
apps/sandbox_api/src/flowpilot_sandbox_api/arena/tasks/w3-joiner-005.json
apps/sandbox_api/src/flowpilot_sandbox_api/arena/tasks/w3-joiner-006.json
apps/sandbox_api/src/flowpilot_sandbox_api/arena/tasks/w3-joiner-007.json
apps/sandbox_api/src/flowpilot_sandbox_api/arena/tasks/w3-joiner-008.json
apps/sandbox_api/src/flowpilot_sandbox_api/arena/tasks/w3-joiner-009.json
apps/sandbox_api/src/flowpilot_sandbox_api/arena/tasks/w3-joiner-010.json
apps/sandbox_api/tests/conftest.py
apps/sandbox_api/tests/test_api.py
apps/sandbox_api/tests/test_models.py
apps/sandbox_api/tests/test_arena_catalog.py
apps/sandbox_api/tests/test_arena_service.py
apps/sandbox_api/tests/test_arena_grader.py
apps/sandbox_api/tests/test_arena_baselines.py
apps/sandbox_api/tests/test_arena_api.py
```

Frontend manifests and locks remain in the acceptance gates but are not on the
change allowlist because W3 adds no browser dependency or frontend behaviour.
Compose already starts the only services W3 needs, so it is validated but not
modified unless a concrete runtime defect is first added here. Any newly
necessary path must be added before it changes. A path that broadens W3 scope
requires user direction rather than an implicit contract edit.

## Task Spec contract

Each JSON document must contain exactly:

- `task_id`, `schema_version`, `title`, and `business_process`;
- structured `synthetic_actor` and human `instructions`;
- `split` and a `fixture` ID/version reference;
- structured `initial_state` with fixed target and decoy employees;
- structured `expected_final_state` separate from prose;
- an ordered list of recognized `grader_predicates` with integer weights that
  total 100;
- its lower-case hexadecimal `canonical_checksum`.

Validation rejects unknown fields, duplicate task or predicate IDs, unsupported
schema/fixture versions, invalid references, unrecognized predicate kinds,
weight totals other than 100, inconsistent task/split allocation, any email
outside `.invalid`, and any asset identifier outside the fixed `SYN-W3-...`
namespace. Selectors, DOM, screenshots, browser actions, prompts, model
parameters, planner structures, run results, and mutable execution state are
not schema fields and are therefore rejected.

## Reset/Seed and grading rules

- Reset/Seed accepts only a catalog `task_id`, never SQL, table names, paths,
  commands, arbitrary fixtures, or caller-supplied records.
- One transaction deletes only the exact task marker from Mail, Asset, IAM,
  ITSM, and HRIS rows, then inserts the frozen initial state.
- Fixed primary keys and values make the observable initial fact summary
  identical across repeated runs. The response contains task ID, fixture
  version, spec checksum, and a stable fact summary/checksum.
- Rollback leaves the prior state intact on failure.
- Grading performs no flush, commit, mutation, network, browser, log, file,
  model, or external call. Its result contains total score, pass/fail, ordered
  per-predicate results, and short structured-fact explanations.
- The same database facts and spec produce byte-equivalent serialized results.
- Correct, partial, wrong-association, elevated-role, duplicate-record, and
  untouched states are tested. Only 100/100 passes.

## Explicit prohibitions

W3 must not contain W4 browser automation, observations, typed actions, or
Agent loop; W5 screenshots/OCR/VLM; W6 routing; W7 planner/verifier/budgets;
W8 Temporal/recovery/faults; W9 context/knowledge/memory; W10 identity/RBAC/
tenancy; W11+ approvals/audit chain/production workers/monitoring/load tests;
real systems, real accounts, personal data, external APIs, paid models,
arbitrary shell/SQL/file interfaces, benchmark execution, UI randomization,
login faults, prompt injection, or malicious page content.

## Handoff and Git rules

- Preserve the W1 control paths and W2 five-module manual flow.
- Do not edit the released W2 migration.
- Do not access `code_review_agent` or `%SystemDrive%/`.
- Do not push, create a PR, merge, tag, or force-push without authorization.
- Explicitly stage only contract paths after all locally available W3 gates
  pass and the evidence report matches observed facts.
- Stop at W3 completion.
