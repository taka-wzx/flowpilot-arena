# Week 08 evidence report - Durable Recovery

- Status: local implementation, all locally available gates, cleanup, one
  local commit, and restack complete
- Branch: `week/08-recovery`, based on released W7 main commit
  `0aa1349ffee0bfabdb8c9f02787f37dfe7f7c029`
- W7 release: PR #29 merged normally; PR run `30342549814`, attempt 2, passed
  15/15 jobs; post-merge main run `30416799576` passed 15/15 jobs; annotated
  tag `w07-planning` resolves to the W7 merge commit. The earlier push run
  `30342499055` remains superseded and was not rerun.
- Real model/provider/OCR/VLM: not run; 0 calls; 0 cost
- Remote W8 push/PR/CI/merge/tag/release: not run as of this local evidence
  freeze; the user subsequently authorized the quota-conscious release path

## Frozen scope, versions, and isolation

The exact path audit found 67 changed/created paths and zero paths outside the
W8 allowlist. Recovery Worker is Python 3.13 with Temporal SDK `1.30.0` and
`cryptography 49.0.0`, both locked. Local Temporal uses fixed supported
`temporalio/server:1.31.2` and `temporalio/admin-tools:1.31.2` images plus
`postgres:17.6-alpine`; no `latest` image is used.

Temporal schema and namespace creation run as bounded one-shot admin-tools
containers. Temporal has its own PostgreSQL database and volume. Recovery
Worker is non-root, read-only, `cap_drop: ALL`, no-new-privileges, PID/tmpfs
bounded, has no host port, repository mount, Docker socket, Browser, Sandbox,
Arena, Grader, business database, credential, or provider route, and joins
only `temporal-control` and `recovery-planning`. All long-running W1-W8
services were observed healthy. Schema/namespace bootstrap containers exited
0. Standalone `docker-compose 5.3.1` was used because the Docker Compose plugin
was unavailable; config parsing passed.

## W4-W7 regression

- W4 DOM retained its released fake baseline: `finished_ungraded`, 2 actions,
  grade 30, `passed=false`. This is the expected untouched baseline, not a W8
  test failure.
- W5 Vision: `finished_ungraded`, grade 100, 20 actions/model calls, 20 images.
- W6 Hybrid: `finished_ungraded`, grade 100, 20 actions/model calls, one
  trusted modality switch, 19 images, two DOM observations.
- W7 Planning: paired W3 grade 100; Development Joiner/Mover/Leaver each grade
  100; W7 catalog 30 templates/90 instances; external calls 0 and cost 0.

## Deterministic Workflow, Checkpoint, and replay

Recovery Worker quality passed Ruff, format, Mypy, and 11 tests. The official
Temporal `Replayer` replayed captured history without nondeterminism. Strict
Checkpoint construction validates the canonical SHA-256, parent lineage,
topology partition, 65,536-byte cap, 18-count cap, schema version, epoch,
revision, absolute deadline, receipts, recovery counters, and the W7 total
ledger high-water snapshot. A unit test rejects any decreasing Planning
counter.

The final 13-case smoke scanned every exported history for the human brief,
supplied values, `.invalid`, `SYN-`, runtime key, and Planning endpoint:
`history_plaintext_matches=0`. No DOM, screenshot, form value, raw Planner
output, or grader fact is persisted. Continue-As-New is not used.

## Idempotency and duplicate side effects

`post_commit_pre_checkpoint_once` completed at grade 100 with six Activity
attempts, one retry, one receipt create, one receipt replay, and zero duplicate
side effects. `idempotency_mismatch` produced one closed mismatch, zero receipt
creates, grade 20, terminal `idempotency_mismatch`, and no duplicate side
effect. Sandbox unit tests separately proved same task/key/hash replay,
different-hash 409, one business mutation, one receipt, and task-owned
Reset/Seed retention. The receipt and fixed synthetic mutation use one
SQLAlchemy transaction; the Grader reads business facts only.

## Browser and Worker recovery

The deterministic session-loss case completed grade 100 at epoch 2 with eight
Activity attempts, five Checkpoints, one recovery, and zero duplicates. The
host restart harness then restarted the actual Browser Worker during a live
Workflow: it completed `finished_ungraded`, grade 100, epoch 2, five
Checkpoints, one recovery, and rejected the pre-restart
session/observation/element envelope.

The harness separately restarted the actual Recovery Worker during the first
attempt of a live Activity. Temporal resumed at attempt 2; the result retained
six Activity attempts, one retry, four Checkpoints, epoch 1, grade 100, and zero
duplicates. Durable Planning high-water values remained nonzero and intact:
one plan generation, three nodes/steps, 13 worker actions, three Verifier
calls, 14 DOM observations, 56 input/28 output fake tokens, and zero cost.
Both restart histories had zero plaintext matches.

## Fault and partial-replan matrix

Final Development results:

| Scenario | Terminal | Grade | Attempts | Retry/recovery/replan | Checkpoints | Receipts create/replay/mismatch | Duplicates |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: |
| Joiner/Mover/Leaver no fault | finished_ungraded | 100 each | 8/5/8 | 0/0/0 | 7/4/7 | 4/0/0, 2/0/0, 5/0/0 | 0 |
| activity_pre_dispatch_once | finished_ungraded | 100 | 6 | 1/0/0 | 4 | 2/0/0 | 0 |
| post_commit_pre_checkpoint_once | finished_ungraded | 100 | 6 | 1/0/0 | 4 | 1/1/0 | 0 |
| browser_session_lost_once | finished_ungraded | 100 | 8 | 0/1/0 | 5 | 2/0/0 | 0 |
| transient_timeout_once | finished_ungraded | 100 | 6 | 1/0/0 | 4 | 2/0/0 | 0 |
| replan_eligible_once | finished_ungraded | 100 | 7 | 0/0/1; 2 nodes | 5 | 2/0/0 | 0 |
| permanent_failure | failed | 20 | 3 | 0/0/0 | 1 | 0/0/0 | 0 |
| checkpoint hash/version mismatch | failed | 20 each | 3 | 0/0/0 | 1 | 0/0/0 | 0 |
| idempotency_mismatch | failed | 20 | 4 | 0/0/0 | 2 | 0/0/1 | 0 |
| replan_disallowed | failed | 80 | 4 | 0/0/0 | 2 | 1/0/0 | 0 |

All retry, replay, recovery, fault, receipt, replan, DAG/step/action,
Verifier, route, DOM-byte, token, cost, and elapsed counters remained in one
monotonic durable usage value. Model/image/switch counters remained zero for
the DOM-only W8 fake path. Budget/schema/permission/permanent/mismatch paths
are non-retryable and terminate safely.

## Data use

Only W7 Development instances `w7-jml-joiner-001-v1`,
`w7-jml-mover-001-v1`, and `w7-jml-leaver-001-v1` were executed for W8.
Validation recovery was not run (`validation_run=false`). Reporting was only
loaded/schema/checksum validated; no Reporting Agent, recovery, fault, grade,
or result inspection ran (`reporting_executed=false`).

W3 remains 10 tasks with 6/2/2 split and checksum
`e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9`.
W7 remains 30 templates/90 instances, 12/8/10 process counts, 18/6/6 split,
catalog checksum `62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f`,
split checksum `1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee`,
and Reporting checksum
`c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6`.

## Database and migration

Forward revision `20260728_0003` adds only task-owned table
`w8_operation_receipts`; file SHA-256 is
`01c36fab26b5be01b3c2d74cf46b6b1ae5197cace092712bf35e9b42dadf649f`.
Released revisions `20260726_0001` and `20260726_0002` have zero diff from the
W7 baseline. Default PostgreSQL reported `20260728_0003 (head)` and `alembic
check` found no new operations. A one-time empty synthetic database passed
upgrade from base to head, downgrade to `20260726_0002`, upgrade back to head,
and was deleted afterward.

## Local gates and cleanup

Python test counts: control API 1, Sandbox API 35, Browser Worker 41, DOM Agent
27, Vision Agent 20, Hybrid Agent 31, Planning Agent 30, Recovery Worker 11;
all passed locked sync, Ruff check, Ruff format, Mypy, and pytest. Control Web
passed lint/typecheck/build and 1 test; Sandbox Web passed the same gates and
9 tests. Compose config/build/up/health, W4-W8 smokes, both real restart
drivers, Alembic, path/data/YAML checks, and migration round-trip passed.

`pre-commit detect-private-key --all-files` passed. Gitleaks scanned 41 commits
and about 2.21 MB with no leaks. CI YAML parsed with 17 jobs and feature push
is limited to `main` while full PR CI remains. Final `git diff --check`, staged
and unstaged review and explicit staging are recorded immediately before the
local commit. Final Compose cleanup observed zero project containers, zero
project networks, and zero project volumes.

As of this local evidence freeze, no GitHub Actions run was triggered for W8
and no remote W8 CI result is claimed. GitHub PR, Actions, tag, and Release
objects are the authoritative evidence for the later remote delivery sequence.

## Known limitations and W9 boundary

W8 makes Temporal orchestration durable, not Planning Agent live memory;
Planning Agent process crash recovery is deliberately not implemented. The
local runtime key is ephemeral test injection, not production secret
management. Temporal is unauthenticated only on isolated internal local
networks with no host port; this is not a production deployment. There is no
Temporal UI, general replay platform, monitoring, approval, compensation,
production backpressure, or real provider.

This branch was restacked on the official W7 main baseline after W7 PR and
post-merge CI passed and tag `w07-planning` was published. The restack changed
ancestry only and preserved the W8 tree. Remote W8 delivery is now authorized
through one PR/main CI sequence; no duplicate or superseded workflow should be
rerun. W8 stops here: no W9 context, summary, memory, retrieval, cache, or
cross-task history was added.
