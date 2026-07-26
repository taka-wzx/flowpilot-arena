# Week 03 evidence report — Arena Foundation

- Status: local W3 implementation and acceptance complete; no push/PR/tag performed
- Branch: `week/03-arena`
- Baseline commit: `5d4647b` (`w02-sandbox`)
- Runtime baseline: Python 3.13
- Paid model calls and cost: 0 / 0
- Real enterprise-system or external API calls: 0
- W3 browser automation, Agent, or benchmark runs: 0

## Startup gate evidence

- GitHub PR #13 was observed merged to `main` at `5d4647b`.
- Both final W2 CI runs reported every job successful, including both `Secret
  scan` jobs.
- The local and remote annotated `w02-sandbox` tag object was
  `9a6772d6e498ee61edc09fa2f113dfbfc4112843`; it dereferenced locally to
  `5d4647b`.
- `main` and `origin/main` had divergence `0 0`; `git pull --ff-only` reported
  already up to date; `week/03-arena` was recreated from that commit.
- No tracked or contract-eligible untracked changes existed before W3 edits.

`%SystemDrive%/` remained excluded from every status, diff, allowlist, and
content/secret review command. It was not inspected, copied, modified, staged,
scanned, ignored, or deleted. No `code_review_agent` repository was accessed.

## Scope confirmation

W3 adds ten strict Task Specs, catalog and canonical checksums, task-owned
transactional Reset/Seed, database-fact-only deterministic grading, a narrow
Arena management API, and anonymous baseline recording with a grader-derived
score. It reuses W2's single Sandbox backend, PostgreSQL, and five business
pages and preserves both W1 services.

No Playwright/Selenium, browser worker, DOM/accessibility observation, typed
browser action, Agent loop, screenshot/OCR/VLM, router, planner, verifier,
fault, Temporal/recovery, context/memory, approval, OIDC/RBAC/tenancy,
production worker, monitoring, load test, external integration, real data,
arbitrary SQL/Shell/file interface, benchmark run, or paid model was added.

## Exact changed files

The final W3 worktree contains exactly these 41 contract-owned changed or new
paths:

```text
.github/workflows/ci.yml
AGENTS.md
CHANGELOG.md
README.md

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
apps/sandbox_api/tests/test_models.py
apps/sandbox_api/tests/test_arena_catalog.py
apps/sandbox_api/tests/test_arena_service.py
apps/sandbox_api/tests/test_arena_grader.py
apps/sandbox_api/tests/test_arena_baselines.py
apps/sandbox_api/tests/test_arena_api.py

docs/agent-contract.md
docs/architecture.md
docs/threat-model.md
docs/evaluation-protocol.md
docs/adr/0003-w3-embedded-task-owned-arena.md
docs/plans/week-03-arena.md
docs/evidence/week-03-report.md
```

The contract also allowed `apps/sandbox_api/tests/test_api.py`, but no W3
change to it was necessary. Frontend manifests/locks and Compose remained
unchanged; their existing locks and runtime configuration passed acceptance.

## Task catalog and canonical checksums

All ten specs validated with strict unknown-field rejection, fixed internal
references, `.invalid` email rules, `SYN-W3-...` assets, the frozen ordered
predicate set, weights totaling 100, and matching SHA-256 checksums.

| Task ID | Split | Canonical checksum |
|---|---|---|
| `w3-joiner-001` | Development | `614b3b0b1d907bf98dd9990b723eb7107e8ff81c9ed0dd5c464383f70b4f33f2` |
| `w3-joiner-002` | Development | `4bd620f0bf346240378e3a46a3ba6c9b31ec2b4bde08463c4a2f9f95a6d7f34b` |
| `w3-joiner-003` | Development | `2f8c2ccea4a5506ae66b55fe6e9b2fc4ec326164de3e449e6516991bdc5ceae3` |
| `w3-joiner-004` | Development | `6223046d9abd748c658cebe70cebbecac85027b33128ea9930abe26f203b182b` |
| `w3-joiner-005` | Development | `f356405dfa41cdfe93b0d30ae98284aff91f3277d2eb0d832abaf23116c80662` |
| `w3-joiner-006` | Development | `a268d9e4142cb489cfb826bdb2ce6bd6c70a3fcb185a5bbed426a04bf4ef5e91` |
| `w3-joiner-007` | Validation | `252e90ad3e7e68145c677a4df7add998c2bbc2cc24af9c752926e4c68cea3f3a` |
| `w3-joiner-008` | Validation | `42b9b598e2926a53d32499f43353f2b45a3e880b6ed1697db2bf7dd10f4be54c` |
| `w3-joiner-009` | Reporting | `732c0a22b4f1cd5a442bcfca8a7de3b2477240ed11db3fe26221eb0ef4172dd3` |
| `w3-joiner-010` | Reporting | `2af3858ac155bba1aed41b256b51d325d9e4b7613dc3fad2dbf6cef4a6f4d79f` |

- Catalog checksum:
  `e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9`.
- Fixture version for every task: `w3-fixture-v1`.
- Reporting specs 009 and 010 freeze at the first W3 commit. No result-driven
  tuning was performed.
- This is a fixed ten-task joiner foundation, not the final 30-template or
  roughly 90-instance roadmap dataset.

## Migration and Compose results

The host lacks the `docker compose` plugin (`docker: unknown command`) but has
Docker Compose v5.3.0 as `docker-compose`. The compatible executable was used
without changing the repository configuration.

| Check | Exact command | Observed result |
|---|---|---|
| Compose parse | `docker-compose -f deploy/compose/compose.yaml config` | Passed; all five services and named volume resolved |
| Clean database | `docker-compose ... down -v --remove-orphans`, then `up -d postgres` | Passed; new volume and healthy PostgreSQL 17 container |
| Build | `docker-compose ... build sandbox-api`, then `up --build -d` | Passed; all W1/W2/W3 images built; all five containers healthy |
| W2 migration boundary | `docker-compose ... run --rm sandbox-api alembic upgrade 20260726_0001` | Passed from empty PostgreSQL; `alembic current` printed `20260726_0001` |
| W3 migration | `docker-compose ... run --rm sandbox-api alembic upgrade head` | Passed; observed `20260726_0001 -> 20260726_0002` |
| Current head | one-off and running-container `alembic current` | Passed; `20260726_0002 (head)` |
| Model drift | one-off and running-container `alembic check` | Passed; `No new upgrade operations detected.` |
| Health | `GET :8000/healthz`, `GET :8001/healthz` | Passed; both returned `status=ok` |
| Five routes | `GET /hris`, `/itsm`, `/iam`, `/assets`, `/mail` on port 5174 | Passed; each returned HTTP 200 |
| Cleanup | `docker-compose -f deploy/compose/compose.yaml down -v` | Passed; five containers, network, and synthetic DB volume removed |

Docker warned that the optional Buildx plugin is unavailable and used the
classic builder successfully.

## Reset/Seed and grader runtime acceptance

Each task was loaded through `/api/arena/tasks/{task_id}`, Reset/Seed twice,
graded in its untouched initial state, completed with the exact five-module
facts through the local business APIs, and graded twice again. Both seed JSON
responses and both final grade JSON responses were byte-equivalent after stable
PowerShell serialization. Initial state scored 30/100 and did not pass; correct
state scored 100/100 and passed for every task.

| Task ID | Stable seed fact checksum (both runs) | Initial | Correct | Repeat grade |
|---|---|---|---|---|
| `w3-joiner-001` | `c4f4cd863b43b93e6e131e9938e18f640c3036d188554d28f2058aaaa9445f07` | 30, fail | 100, pass | Identical |
| `w3-joiner-002` | `a1994592eadf26dc99603e6274d9f6b9307895eb4c4c28d61da3807827e8242d` | 30, fail | 100, pass | Identical |
| `w3-joiner-003` | `d821dcf959d905fa60c05a55a1c4c105683929ac12d297752946e1678996e476` | 30, fail | 100, pass | Identical |
| `w3-joiner-004` | `cdab69be05d7fb3c544c90c4cf361c01302636340d9d37b103bed17343c701fc` | 30, fail | 100, pass | Identical |
| `w3-joiner-005` | `69f472c3e1386059c31f40327e32e4fec762f7ce2feafa22d4d7fa2958a3d9a5` | 30, fail | 100, pass | Identical |
| `w3-joiner-006` | `cd748ae56d3332216e241a964064bffcfaa081ea17b1ebac1ab3df774aec9463` | 30, fail | 100, pass | Identical |
| `w3-joiner-007` | `fe2b5d00c90c4242a3814312299933238286916b880a3a25859332e8355c4a51` | 30, fail | 100, pass | Identical |
| `w3-joiner-008` | `6afbdce79bd8601e5bdc8520c99247f59ab4bd144f9646f8b510aad5c8f4e507` | 30, fail | 100, pass | Identical |
| `w3-joiner-009` | `8664451d3e409f4c084e3294f29b8140422992c8c1210499dd228b7178ff7ebb` | 30, fail | 100, pass | Identical |
| `w3-joiner-010` | `03c6dcd10391620c993bd20ee46ed4caa38e33b9827e36c7e66099fc747e64ce` | 30, fail | 100, pass | Identical |

The unit/integration suite separately exercised correct, partial, wrong target
association, extra administrator role, duplicate ticket/asset, and completely
untouched states. Every negative state remained below 100 and failed. The
ten-task correct-state test snapshots facts before and after repeated grading;
state remained equal and both `GradeResult` values were identical.

Reset/Seed tests also inserted task-owned residue before the second run,
verified exact stable snapshots/checksums, verified a null-owned W2 employee
survived, and verified an ownership conflict rolled back without deleting the
unowned record.

## Manual-baseline recorder sample

| Field | Recorded value |
|---|---|
| Record ID | `baseline-w3-runtime-sample-001` |
| Task ID | `w3-joiner-010` |
| Anonymous alias | `anon-runtime-acceptance` |
| Start/end | `2026-07-26T06:00:00Z` / `2026-07-26T06:11:30Z` |
| Derived duration | 690 seconds |
| Manual action count field | 20 |
| Grader-derived final score | 100 |
| Notes | Synthetic recorder acceptance; no browser telemetry collected |

This is a synthetic recorder acceptance sample, not a measured human-efficiency
claim. The correct business state used for the runtime matrix was created
through the supported local business APIs; no browser was controlled. Frontend
tests separately exercised all five routes and a form submission, and runtime
requests confirmed all five published routes. W3 does not claim observed human
timing, an efficiency improvement, a benchmark result, or enterprise ROI.

## Validation results

| Area | Commands | Observed result |
|---|---|---|
| W1 backend lock | `uv sync --locked --all-groups` | Passed; 43 packages resolved / 42 checked |
| W1 backend quality | `uv run ruff check .`, `ruff format --check .`, `mypy src`, `pytest` | Passed; 3 source files formatted, 2 typed source files, 1 test |
| W1 frontend lock | `npm.cmd ci` | Passed; 249 packages added, 250 audited, 0 vulnerabilities |
| W1 frontend quality | lint, typecheck, test, build | Passed; 1 test; Vite production build |
| Sandbox/Arena backend lock | `uv sync --locked --all-groups` | Passed; 42 packages resolved; local package updated to 0.2.0 |
| Sandbox/Arena backend quality | Ruff check/format, mypy `src`, pytest | Passed; 23 source/test files formatted, 12 typed source files, 23 tests |
| Sandbox frontend lock | `npm.cmd ci` | Passed; 254 packages installed from committed lock |
| Sandbox frontend quality | lint, typecheck, test, build | Passed; 6 tests; 48-module Vite production build |
| Catalog load | local catalog load and CI catalog command definition | Passed locally; 10 specs; catalog checksum matched |
| Diff whitespace | `git diff --check` | Passed |
| Contract path audit | actual tracked/untracked changes compared with exact contract block | Passed; all 41 paths are allowlisted |
| Explicit secret-pattern review | private-key, AWS, GitHub, OpenAI-style, and Bearer-token patterns over the 41 changed files | Passed; no matches |
| Pre-commit private-key scan | `pre-commit clean`, `pre-commit install-hooks`, then `pre-commit run detect-private-key --all-files` | Passed; damaged user cache was rebuilt successfully |
| Gitleaks history scan | `gitleaks git --no-banner --redact --exit-code 1 .` | Passed with Gitleaks 8.30.1; all 24 local commits scanned; no leaks found |

One upstream `StarletteDeprecationWarning` remains in pytest for FastAPI's
current `TestClient` import path. It does not affect the 23 passing tests.

## Secret and diff review

The initial local review found no Gitleaks executable and a damaged user-level
pre-commit hook cache. The cache was removed through `pre-commit clean`, the
locked hooks were reinstalled, and `detect-private-key --all-files` passed.
Gitleaks 8.30.1 was then installed through Winget in the current-user scope and
its package directory added to the user PATH. `gitleaks git` scanned all 24
local commits, including the evidence-only repair commit, without finding a
leak. Git mode was used deliberately so the pre-existing untracked
`%SystemDrive%/` directory was never traversed. No remote W3 CI claim is made
because the branch is unpushed.

The complete contract-owned implementation, migration, Task Specs, tests,
locks, CI, and documentation were reviewed together with the exact 41-path
status and `git diff --check`. No contract-external path is changed.

## Known limitations

1. This host has `docker-compose` v5.3.0 but no `docker compose` plugin and no
   Buildx plugin. Compatible Compose and the classic builder completed every
   required runtime check.
2. A remote W3 Gitleaks/CI result still requires an authorized push and PR;
   only the repaired local pre-commit and Gitleaks results are claimed here.
3. The baseline sample proves the narrow recorder and grader-derived score, not
   a measured human completion session, productivity change, or ROI.
4. W3 is unauthenticated and local-only. Any local caller can select one of the
   ten catalog tasks. OIDC, RBAC, and tenancy remain W10.
5. The ten tasks are fixed joiner tasks and intentionally do not cover mover,
   leaver, approvals, faults, UI variation, or the final 30-template dataset.
6. SQLite supports deterministic unit/integration tests, but PostgreSQL Compose
   remains the authoritative migration/runtime evidence recorded above.

## W4 boundary

W4 may add an isolated Playwright worker, DOM/accessibility observation, typed
browser actions, and a DOM ReAct baseline. W3 stops without implementing or
scaffolding those capabilities. No push, PR, merge, or `w03-arena` tag has been
performed.
