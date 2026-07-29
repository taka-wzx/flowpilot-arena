# Week 08 plan - Durable Recovery

## Objective

Preserve W1-W7 and add the smallest deterministic durable recovery layer:
Temporal Workflow/Activities, opaque encrypted input, verified Checkpoints,
fresh browser epochs, transactional operation receipts, bounded retry, trusted
faults, and one bounded partial DAG revision. The complete authority is
`docs/agent-contract.md`.

## Frozen outcomes

| Area | W8 outcome | Deliberate limit |
|---|---|---|
| Temporal | Deterministic Workflow and replayable safe state | No UI/cloud/production cluster/general orchestration |
| Input | Runtime-key AES-GCM opaque durable envelope | No plaintext brief/value/objective in history |
| Checkpoint | Verified safe-state hash lineage, 18/65,536-byte caps | No browser/page/model/grader content |
| Recovery | Epoch 1-3 with wholly fresh Browser/Context/Page | No cross-epoch observation/reference reuse |
| Idempotency | Transactional `w8_operation_receipts`, safe replay/mismatch | No raw payload receipt or compensating transaction |
| Retry/fault | Closed reasons, transient-once, trusted acceptance faults | No unbounded retry or page/model-directed fault |
| Replan | One immutable revision replacing failed/not-started subgraph | No authority/budget expansion or rollback |
| Evaluation | W4-W7 regression plus W8 fault/replay matrix | Fake circuit evidence, not production reliability |

## Implementation phases

1. Verify W7 commit/PR/CI state, create the local stacked W8 branch, read all
   required authority, and freeze W8 contract/allowlist/ADR/threat/evaluation/
   data/evidence documents before application edits.
2. Implement strict W8 schemas, canonical hashing, opaque AES-GCM envelope,
   deterministic Workflow, fixed Activities, replay tests, and Recovery Worker
   container/locks.
3. Add Planning Agent W8 recovery/step/replan APIs and one non-resetting durable
   usage projection while preserving every W7 endpoint and fake baseline.
4. Add Browser Worker W8 epoch/action schemas, old-epoch rejection, fixed
   idempotency header binding, response receipt extraction, and unconditional
   cleanup without changing W4-W7 schemas.
5. Add the forward-only receipt migration, transactional idempotency helper,
   fixed business-route integration, task-owned Reset/Seed cleanup, and
   duplicate/mismatch tests. Verify released migration hashes remain unchanged.
6. Add fixed Temporal/Recovery services, separated internal networks,
   acceptance runner, W8 CI jobs, and push-trigger deduplication without
   weakening W1-W8 jobs.
7. Run app locks/quality/tests, frontend regressions, catalog freezes, Compose,
   Alembic round-trip, W4-W8 smokes, real Browser and Recovery Worker restart
   tests, history plaintext scan, receipt zero-duplicate assertions, isolation,
   secrets, diff, exact-path, and cleanup gates.
8. Freeze observed evidence, explicitly stage only the W8 allowlist, create one
   local W8 commit if every locally available gate passes, and stop before W9.

## Frozen hard limits

- Temporal SDK 1.30.0; Temporal Server and admin-tools 1.31.2.
- One-day local Temporal namespace retention; no Continue-As-New.
- Checkpoint: 65,536 canonical bytes and 18 entries.
- Session recovery: 2; epochs: 1 through 3.
- Activity attempts: 2; retry policy: no-retry or transient-once.
- Partial replan: 1; total immutable revisions: 2.
- Operation receipts: 24; injected faults: 2.
- Total duration: existing 300 seconds; every W6/W7 cap remains unchanged.

## Acceptance sequence

Development runs preregistered no-fault, Activity pre-dispatch,
post-commit/pre-Checkpoint, session loss, actual Browser Worker restart,
actual Recovery Worker restart/replay, transient timeout, permanent failure,
Checkpoint version/hash mismatch, idempotency mismatch, eligible/disallowed
replan, budget exhaustion, and cleanup paths. At least one Development Joiner,
Mover, and Leaver is independently graded. Validation may run once only after
parameters freeze. Reporting is never executed.

## Handoff boundary

W8 stops after local durable recovery evidence. W9 context, memory, retrieval,
summary, cache, and cross-task history are not started. No remote W8 action is
authorized while W7 remains unreleased.
