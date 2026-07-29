# Week 09 evidence report - Context, Retrieval, Summary, and Organization Memory

- Status: local implementation and all required local gates complete
- Branch: `week/09-context`
- Baseline: released W8 merge `9ecc31f3e525ae57260bc47ddab5d1d8c1baba6f`
- Local W9 commit: amended after this evidence freeze; final SHA is recorded in
  the final handoff
- Remote W9 push/PR/CI/merge/tag/release: not run
- Real model/provider/OCR/VLM/embedding: not run; 0 calls; 0 billed tokens;
  0 cost
- Validation: not run
- Reporting execution: false

## Baseline and remote read-only verification

Local `origin/main` and annotated `w08-recovery` dereference to the official W8
merge. GitHub read-only verification found PR #30 merged normally at that SHA;
PR run `30419997200` passed 17/17 jobs on attempt 1; post-merge main run
`30420371034` passed 17/17 jobs on attempt 1; and published release
`v0.2.0 - Hybrid + Recovery` uses tag `w08-recovery`. Twenty unrelated open
Dependabot PRs existed and were not touched. W9 created zero remote PRs, zero
Actions runs/jobs, zero reruns, and zero extra runs.

The initial local `main` was the released W7 commit. A clean
`week/09-context` branch was created directly from official W8 `origin/main`.
W8 was not amended, retagged, or republished.

## Implementation and isolation

W9 is implemented inside Planning Agent with no new service, migration,
dependency, lock change, database connection, or network route. Planning Agent
continues to reach only Browser Worker; Recovery Worker continues to reach only
Temporal and Planning Agent.

The implementation adds strict/frozen/extra-forbid schemas; five ordered
layers; canonical JSON/SHA-256; source/trust/version/validity provenance; a
nine-record fixed catalog; closed deterministic lexical/hash retrieval;
deterministic short-term summary; process-local exact-scope synthetic
organization memory; layer/total budgets; five frozen ablations; and additive
context/context-backed Planning endpoints.

The existing W7 `TotalBudgetLedger` now includes cumulative W9 counters. The
context-backed endpoint passes that same object into released Planning
execution. W8 durable Planning usage mirrors only the new numeric counters and
uses its existing high-water comparison. No semantic context, catalog record,
summary, memory value, browser content, or task fact is stored in Temporal or a
Checkpoint.

## Deterministic unit context and ablation evidence

Planning Agent tests passed 47/47. They cover all five layers, authoritative
fact precedence, browser expiry, summary preservation/dedupe/hash, retrieval
version/source/trust/expiry/dedupe/order, memory scope/version/expiry/tombstone/
reset, untrusted field rejection, canonical JSON round-trip, context budget
failure, shared-ledger execution, and all five ablations.

The fixed enterprise catalog has 9 records, 6 categories, and checksum
`4d63a24a57a54f9f7d94abe6b98d34453525dde13a6b100e336c8442c68bfb15`.

Observed deterministic unit matrix:

| Profile | Layer counts TF/BW/ST/OM/EK | Items | Bytes | Tokens | Retrieval q/c/s | Summary i/o/d | Memory r/w/d | Context hash |
|---|---|---:|---:|---:|---|---|---|---|
| full_five_layer | 2/1/2/1/1 | 7 | 2507 | 628 | 1/2/1 | 2/2/0 | 1/1/0 | `288d8aa43996d41f299144144e1e418dd42928f8d15ccf1be4f35500322d6cad` |
| task_facts_only | 2/0/0/0/0 | 2 | 668 | 167 | 0/0/0 | 0/0/0 | 0/0/0 | `8c187fb16e68a90ee9795ab67788853ff406b6fb1313224686276f224fe785cd` |
| no_short_term | 2/1/0/1/1 | 5 | 1805 | 452 | 1/2/1 | 0/0/0 | 1/1/0 | `e455e8b98918c5a46dc496afce4ba204f255c58d432032feaf52430791c194ae` |
| no_enterprise_retrieval | 2/1/2/1/0 | 6 | 2107 | 528 | 0/0/0 | 2/2/0 | 1/1/0 | `66465e3b5dc7464fc71549ba567db98dee6e5361a4915853d9c121aa739c16b9` |
| no_organization_memory | 2/1/2/0/1 | 6 | 2134 | 534 | 1/2/1 | 2/2/0 | 0/0/0 | `c29e3cd674a499b0128988c5211438cca4de119f4a2cfba63f84ddbfa464f57e` |

`q/c/s` means queries/candidates/selected, `i/o/d` means input/output/dropped,
and `r/w/d` means reads/writes/deletes. Every row has one context assembly.
Memory deletion is zero in this matrix but a separate unit test exercised an
exact-owner delete at version 3 and verified a tombstone plus empty active
read. A deliberately one-item total budget stopped on the second monotonic
context-item charge without counter reset.

The first local development test run exposed a canonical UTC representation
mismatch between direct datetime values and JSON `Z` output. Hashing was moved
to the validated JSON-mode projection and explicit strict UTC parsing was added.
Ruff/Mypy and the complete 47-test suite then passed. This caused no commit,
push, PR, Actions run, or rerun.

## W1-W8 local regression gates

All eight Python applications passed `uv sync --locked --all-groups`, Ruff
check, Ruff format check, strict Mypy, and pytest:

| Application | Tests |
|---|---:|
| Control API | 1 |
| Sandbox API | 35 |
| Browser Worker | 41 |
| DOM Agent | 27 |
| Vision Agent | 20 |
| Hybrid Agent | 31 |
| Planning Agent | 47 |
| Recovery Worker | 12 |

Recovery Worker tests include the numeric W9 durable usage projection; W8
recovery logic and limits were unchanged. The frontend locked installs also
passed lint, typecheck, tests, and production builds: Control Web 1 test and
Sandbox Web 9 tests. No manifest or lockfile changed.

The packaged W3 catalog loaded 10 tasks and retained checksum
`e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9`.
The W7 catalog loaded 30 templates/90 instances, 12/8/10 process counts and
18/6/6 split, with catalog checksum
`62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f`,
split checksum
`1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee`,
and Reporting checksum
`c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6`.
Released migration and W3/W7 Arena source diffs against `origin/main` were
empty. Offline Alembic heads reported `20260728_0003 (head)`.

## Compose, Alembic, JML, and cleanup

The Docker Compose plugin was unavailable; compatible standalone
`docker-compose 5.3.1` was used. `config --quiet` passed. The frozen
`context-acceptance` profile and `context-acceptance-smoke` service were present
when the profile was enabled. CI YAML retained main-only push plus full PR
trigger and parsed structurally as 18 jobs including the W9 Context job. The
standalone client warned that the optional buildx plugin was absent and used its
classic builder successfully; this did not weaken or skip a build.

Docker Desktop Server `29.6.2` was started locally. Compose built the W1-W9
images, created the two isolated database volumes and internal networks, and
observed all 13 long-running services healthy. Online Alembic reported
`20260728_0003 (head)` and `alembic check` reported no new upgrade operations.
W9 adds no migration, so no new-migration downgrade/upgrade round-trip was
required; all released migration files remained byte-unchanged.

All deterministic Compose smokes passed in release order:

| Smoke | Required observation |
|---|---|
| W4 DOM | `finished_ungraded`, 2 actions, independent grade 30 expected baseline, 0 cost |
| W5 Vision | `finished_ungraded`, 20 actions/images, independent grade 100, 0 cost |
| W6 Hybrid | `finished_ungraded`, 20 actions, 1 switch, 19 images, independent grade 100, 0 cost |
| W7 Planning | W3 grade 100; Development Joiner/Mover/Leaver each grade 100; catalog 30/90 |
| W8 Recovery | fault/retry/receipt/recovery/replan matrix passed; zero duplicate effects; history plaintext matches 0 |
| W9 Context | five ablations, rejection gates, replay, J/M/L context-backed Planning and independent grades passed |

W8 retained `finished_ungraded` on successful scenarios, safe failure on
permanent/Checkpoint/idempotency/replan-disallowed scenarios, zero external
model calls, zero actual model cost, `validation_run=false`, and
`reporting_executed=false`.

Observed W9 Development context-backed results:

| Task | Grade | Context items | Retrieval queries | Summary inputs | Memory reads/writes | Context hash |
|---|---:|---:|---:|---:|---|---|
| Joiner `w7-jml-joiner-001-v1` | 100 | 9 | 1 | 4 | 1/1 | `720070e0d3f1604412f58c04e6ad73c044770138efb45ae7aacdb4f85b5a0771` |
| Mover `w7-jml-mover-001-v1` | 100 | 9 | 1 | 4 | 2/1 | `9357c53d631179a6839671f29fdf3e1dfc35f42bc925abe34c9ef770302b5f3a` |
| Leaver `w7-jml-leaver-001-v1` | 100 | 9 | 1 | 4 | 3/1 | `c50cece25a957fb8e03324d3772d81f086601713e4c2d89007cc0d0533a77611` |

The increasing same-scope memory read counts prove deterministic synthetic
organization-memory reuse across the three tasks; writes remain exact-owner and
cross-scope access remains rejected. Observed Compose ablation hashes were:

- `full_five_layer`:
  `e52bffb00f08cddb9bc0c47dadb252bb2a94b1d2fb0957e6b5a61ef5acfd2bb9`;
- `task_facts_only`:
  `1020f9ec450675c10c154d24dfee4e5fdb63373be074d478700ab6f92694cd9f`;
- `no_short_term`:
  `7306bfc481773c9bc8c97134be4e0723d9978c20d863bfb0cad51cb5f4ec1192`;
- `no_enterprise_retrieval`:
  `9b2a8f108d78d434e79903eb577e2f47d2815279971641e7d297d36c24eb3d69`;
- `no_organization_memory`:
  `5a245b5df22014f3447d1a59e058532c6b99aefbad1f50ca0d895f6f3fe7bd74`.

The W9 smoke additionally rejected the cross-scope actor, untrusted page field,
and deliberately insufficient item budget; replayed an identical
task-facts-only context; retained enterprise catalog checksum
`4d63a24a57a54f9f7d94abe6b98d34453525dde13a6b100e336c8442c68bfb15`;
and reported zero real model/provider/OCR/VLM/embedding calls and zero cost.

Final `down -v --remove-orphans` removed the stack and both synthetic volumes.
Project-label enumeration observed exactly 0 containers, 0 networks, and 0
volumes afterward.

## Security, contract, and diff gates

- Exact contract audit: 36 allowlist paths, 36 changed/created paths, 0 outside.
- Gitleaks historical and staged scans passed with no leaks; the final
  post-amend scan is recorded immediately before handoff.
- `pre-commit` was absent globally, so the exact
  `detect-private-key --all-files` hook was run through a temporary `uvx`
  environment and passed. No repository dependency or lockfile changed.
- `git diff --check` passed.
- Compose config and W9 integration-script Ruff/format checks passed.
- No literal `%SystemDrive%/` path or `code_review_agent` repository was
  accessed, scanned, staged, or modified.
- Staged and unstaged exact-path review is performed immediately before the one
  local commit.

## Evaluation, tokens, calls, and cost

Deterministic unit and Compose Development context were executed. The unit
table's token values are the frozen `ceil(canonical bytes / 4)` context
estimates; they are not billed model tokens and incur no cost. Real model calls,
provider calls, OCR calls, VLM calls, embedding calls, and billed tokens/cost
are all 0.

Validation was not run. Reporting was not executed. W3/W7/W9 packaged
catalog/schema/checksum values were validated, but no Reporting Reset, Seed,
Agent, context, memory, retrieval, grade, result execution, or result inspection
occurred.

## GitHub quota and W10 boundary

W9 used no remote commit, feature push, PR, merge, tag, Release, workflow run,
job, rerun, or extra run. W8 baseline run IDs were read only. No failed remote
job existed and no Actions quota was consumed.

The process-local synthetic organization-memory store is not production
durability, authentication, user/organization identity, real tenant isolation,
RBAC, or optimistic locking. Those remain W10. W9 does not start W10, create
`w09-context` remotely, or create `v0.3.0`.
