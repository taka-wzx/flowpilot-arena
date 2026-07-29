# Evaluation protocol

## Purpose and preserved boundary

W8 evaluates deterministic durable recovery wiring, not real planning,
reasoning, visual understanding, or production reliability. W3 and W7
database-fact Graders remain the only success authority. No real model,
provider, OCR, or VLM call is authorized.

W3 ten-task catalog/checksum/6-2-2 split, W7 30-template/90-instance catalog,
12/8/10 processes, 18/6/6 split, stable manifests/checksums, W4 DOM, W5 Vision,
W6 Hybrid, W7 Planning, Reset/Seed, and Graders remain unchanged.

## Unit, schema, and replay protocol

Tests cover:

1. strict/frozen/extra-forbid W8 start/result, Workflow state, Checkpoint,
   Activity, epoch, retry, receipt, recovery, fault, revision, ledger, cleanup,
   and terminal schemas;
2. closed legal state transitions, canonical hashes, parent lineage, 65,536
   bytes, 18 Checkpoints, 24 receipts, two attempts/recoveries/faults/revisions,
   and one replan;
3. deterministic Workflow replay from captured history and rejection of
   nondeterministic Workflow changes;
4. opaque-envelope authentication, identity binding, unknown key/version,
   malformed ciphertext, and no plaintext input in history;
5. epoch 1 normal path, fresh epoch recovery, old session/generation/
   observation/element/screenshot/grounding rejection, and all cleanup paths;
6. receipt create/replay/mismatch/race behavior, atomic mutation, Reset/Seed
   ownership, and zero duplicate business side effects;
7. transient-once versus non-retryable failures, durable attempts, fixed
   recovery order, and non-resetting W6/W7/W8 counters;
8. partial replan boundary/lineage, completed-node preservation, authority and
   budget non-expansion, W7 DAG caps, and disallowed replan safe-stop; and
9. Verifier/Grader separation and `finished_ungraded` terminal semantics.

## Development acceptance matrix

After equal Reset/Seed, the frozen W8 smoke must prove:

| Scenario | Required observation |
|---|---|
| no fault | epoch 1, finished_ungraded, independent 100 |
| activity pre-dispatch | at most one retry, no initial side effect, ledger cumulative, grade 100 |
| post-commit/pre-Checkpoint | same key, receipt replay, zero duplicate side effect, grade 100 |
| browser session lost | new epoch, old ref rejected, latest verified Checkpoint resume, grade 100 |
| Browser Worker restart | actual Compose restart, healthy service, fresh epoch, workflow continuation, grade 100 |
| Recovery Worker restart | actual Compose restart, Temporal replay, attempts/ledger/Checkpoint unchanged, grade 100 |
| transient timeout | exactly one retry maximum |
| permanent fault | safe failed/escalated status, no false success, cleanup |
| Checkpoint version/hash mismatch | fail closed before next action |
| idempotency mismatch | HTTP 409/closed rejection and no side effect |
| partial replan | only failed/not-started descendants replaced, revision <=2, grade 100 |
| budget | retry/recovery/replay/fault/replan cumulative; over-limit safe-stop |
| cleanup | success/failure/timeout/cancel/startup/shutdown/replay-failure state cleared |

At least one W7 Development Joiner, Mover, and Leaver receives a recovery run,
ends `finished_ungraded`, and is independently graded. W4-W7 Compose smokes run
as regression inputs. Immediate finish still fails independent grading.

## History plaintext gate

The acceptance caller preregisters the exact synthetic brief, objective,
supplied values, `.invalid` address, `SYN-` identifier, runtime key sentinel,
and configured Planning endpoint. It exports complete raw Workflow history and
searches serialized JSON, base64-decoded payload data, and metadata. Any match
fails acceptance. Only opaque IDs/hashes, ciphertext, safe topology, counters,
and closed reasons are permitted.

## Migration and data protocol

Released W2/W3 migration hashes are compared with the W7 baseline. A fresh
synthetic PostgreSQL database upgrades through W8, downgrades from W8 to the
released W3 head, and upgrades again. Alembic `current` and `check` must report
the new head and no drift. Receipt Reset/Seed tests prove selected-task cleanup
and cross-task preservation. Graders must ignore receipt rows.

## Validation and Reporting discipline

Development may run the fault matrix during implementation. Once behavior and
parameters freeze, Validation may run at most one preregistered final recovery
check; the evidence states whether it ran. Reporting is limited to deterministic
generation/load/schema/checksum verification. It receives no Reset/Seed,
Agent, fault, recovery, grade, or result run/inspection before W15.

## Interpretation

Passing fake results establish deterministic schemas, Temporal replay wiring,
bounded recovery decisions, transactional synthetic idempotency, epoch/ref
isolation, cleanup, and independent grading on fixed pages. They do not prove
real-model capability, recovery under arbitrary infrastructure failures,
malicious-page resistance, external generalization, production SLOs, or ROI.

## Real-model authorization and W9 boundary

Real Planner/Verifier/DOM/Vision/Hybrid/OCR/VLM calls remain not run at 0 calls
and 0 cost. Any call requires a new exact disclosure and separate user
authorization. W9 context, summary, memory, retrieval, cache, and cross-task
history are not part of W8 evaluation.
