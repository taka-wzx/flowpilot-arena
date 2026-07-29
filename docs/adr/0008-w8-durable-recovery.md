# ADR 0008: Deterministic Temporal recovery with opaque durable input

- Status: Accepted for local W8 implementation
- Date: 2026-07-28

## Context

W7 executes one immutable DAG through one W6 Hybrid Browser session and keeps
its total ledger in Planning Agent memory. A Browser Worker or Recovery Worker
crash currently loses orchestration state. Retrying an Activity after a
business mutation also creates an ambiguity window: the database commit may
have succeeded although the Activity result and next Checkpoint were not
recorded.

W8 must make that path durable without storing human brief, supplied values,
plan objectives, DOM, screenshots, form values, or grader facts in Temporal;
without giving a Workflow nondeterministic I/O; and without giving Recovery
Worker Browser, Sandbox, Arena, Grader, database, or provider access.

Official Temporal Python material was checked before implementation. The
Python SDK documents `DataConverter`/`PayloadCodec` as the bytes-to-bytes
boundary before payload storage, provides a `Replayer`, and requires external
I/O to be Activities. The official 2026-07 releases support Python SDK 1.30.0
and Temporal Server 1.31.2. W8 fixes those versions and uses no `latest` tag.

## Decision

Create `apps/recovery_worker` as a standalone Temporal Worker. Its Workflow
contains only closed deterministic state and schedules fixed Activities. The
Activities call Planning Agent over `recovery-planning`; Planning Agent remains
the only Agent service that calls Browser Worker over `planning-worker`.
Recovery Worker has no route to Browser Worker, Sandbox, Arena, Grader, or any
database.

Use the supported fixed `temporalio/server:1.31.2` image with a separate
PostgreSQL volume. Fixed `temporalio/admin-tools:1.31.2` one-shot containers
perform only schema setup and namespace creation using baked-in, reviewed
scripts; the deprecated `auto-setup` image is not used. Split networks so the
Server and schema bootstrap alone join the database network, while Recovery
Worker joins `temporal-control` and `recovery-planning`. Do not add Temporal
UI, cloud, host ports, repository mounts, or Docker sockets.

### Safe input persistence

Use an equivalent opaque durable envelope rather than allow Pydantic plaintext
to reach the default Temporal converter. A trusted caller canonicalizes the
strict start payload and encrypts it with AES-256-GCM before starting the
Workflow. Associated data binds schema version, opaque run/task/workflow IDs,
and key ID. The Workflow receives only base64 nonce/ciphertext and a hash.

Only Activity code reads the runtime-injected `RECOVERY_ENVELOPE_KEY`, verifies
the envelope, and decrypts immediately before calling Planning Agent. Activity
inputs and Workflow history still contain the opaque envelope, not plaintext.
Activity outputs are safe closed schemas and hashes only. The key is never in
source, logs, results, or Temporal. Tests export history and search both JSON
and decoded payload bytes for all preregistered synthetic plaintext sentinels.
Any match fails the gate.

This design is deliberately narrower than a general codec server: there is no
UI decoder, arbitrary payload codec endpoint, key registry, rotation service,
or production secret management. W10+ may later replace local injection under
a new contract.

### Deterministic recovery state

The Workflow maintains one `w8-workflow-state/1.0` value and creates canonical
`w8-checkpoint/1.0` values after verified progress. Checkpoints form a parent-
hash chain and contain only safe topology, step IDs/states, epoch, absolute
deadline, ledger usage, counters, receipt hashes, and closed reasons. They are
limited to 65,536 bytes and 18 entries. Continue-As-New is forbidden.

Activity retry is `maximum_attempts=2` only for `transient_once`, with bounded
intervals. Workflow decisions follow the fixed refresh, retry, new epoch,
Checkpoint resume, one partial replan, safe-stop order. Temporal workflow time
supplies the absolute deadline. No system clock, randomness, environment,
HTTP, database, filesystem, Planner, Browser, or page data is used by Workflow
code.

### Browser epoch and transactional receipt

Planning Agent adds separate W8 recovery endpoints and task-local session
state while preserving W7 endpoints. Normal runs open epoch 1. Recovery closes
and clears the current session, opens a fresh Browser/Context/Page with the
next epoch, requests a new observation, and resumes only remaining steps from
the latest verified Checkpoint. W8 Browser envelopes bind epoch in addition to
the released W6 session/generation/modality/reference fields.

Add one forward-only migration for `w8_operation_receipts`. For each fixed
synthetic mutation, Sandbox computes the canonical request hash from its
validated body. New receipt and business mutation commit in the same database
transaction. Same task/key/hash returns a stored safe result; a different hash
returns 409 without mutation. Browser Worker may attach only fixed W8 headers
from a strict W8 action envelope to the exact mutation request and clears them
immediately afterward.

### Partial replan

Revision 1 remains immutable. One deterministic fake replan may produce
revision 2, preserving completed nodes and replacing only the failed node plus
not-started descendants. Parent plan hash, boundary, replaced IDs, and new
canonical hash are durable. Authority and the original total ledger cannot
expand; no rollback or compensating transaction is implemented.

## Consequences

- Recovery Worker replay can reconstruct orchestration state while Browser
  handles and observations remain ephemeral.
- Post-commit Activity loss becomes safe because the retried UI mutation uses
  the same deterministic key and receives a receipt replay.
- Temporal history remains operationally inspectable only through safe
  hashes/counters; human-readable payload debugging is intentionally absent.
- Planning Agent retains task-local live session state and is not itself made
  durable in W8. Planning crash recovery remains a known limitation.
- The fixed Server/admin-tools/PostgreSQL Compose stack is only a local
  synthetic acceptance deployment and is not a production Temporal claim.

## Rejected alternatives

- Plain Pydantic Workflow input: leaks brief and supplied values into history.
- Store Browser handles/DOM/screenshots in Checkpoints: violates privacy,
  determinism, and reference lifecycle.
- Let Workflow call HTTP/Planner/Browser/DB: makes replay nondeterministic.
- Give Recovery Worker Browser Worker or Sandbox access: collapses the intended
  trust boundary.
- Retry the UI mutation without a database receipt: cannot close the
  post-commit/pre-Checkpoint ambiguity window.
- A generic request interceptor/header API: creates arbitrary network
  authority; W8 supports only fixed synthetic mutations.
- Continue-As-New: could hide history growth or reset counters.
- Rollback/compensation: outside W8 and unsafe for already committed effects.
