# ADR 0009: Deterministic five-layer context inside Planning Agent

- Status: Accepted for local W9 implementation
- Date: 2026-07-29

## Context

W8 durably replays operational safe state but intentionally has no semantic
context. W9 must add database-authoritative task facts, current browser working
memory, task-local summary, organization memory, and enterprise knowledge
without changing W1-W8 APIs, giving Planning Agent database/Arena/Grader
access, storing raw content in Temporal, adding a real provider/vector service,
or prematurely implementing W10 tenancy.

## Decision

Place the smallest W9 context engine inside existing Planning Agent. Add no
service, database migration, dependency, or network. A trusted synthetic caller
supplies an exact task/scope-bound safe database snapshot projection. The
assembler validates that authority, combines only closed safe browser/session
events, reads a process-local exact-scope fake organization store, and queries a
fixed packaged enterprise catalog.

### Strict safe projection

All W9 models use existing strict/frozen/extra-forbid configuration and explicit
`w9-*/1.0` versions. Runtime values are restricted to safe identifiers/codes.
Every output item carries source, trust, version, validity/expiry, content hash,
canonical byte count, and deterministic token estimate. Canonical JSON is
sorted-key compact UTF-8; SHA-256 results are reproducible.

The trusted caller, not Planning Agent, obtains the database snapshot. This
preserves Planning Agent's Browser-only network boundary and keeps Task Spec,
expected state, Grader predicate/checksum, and Reporting result out of context.
W10 will supply real authenticated identity/scope; W9 synthetic scope is not
presented as tenant authorization.

### Retrieval

Use nine fixed synthetic records across six closed categories. Process/phase
selects one category; there is no query string field. Filter global/exact scope,
fixed source/trust, active validity, and version. Group content hashes and keep
the highest version, then sort score/version/hash/ID and emit top 3. No vector
database, embedding, provider, network, cache, or model exists.

### Summary

Accept at most 12 current-task events from five closed kinds. Fixed priority and
ordinal ordering, kind/value dedupe, required-kind first selection, and fixed
item/byte/token caps produce at most 8 entries. Output exposes source hashes and
input/dedupe/emitted/drop counts. It neither mutates facts nor writes memory.

### Organization memory

Use a locked process-local mapping keyed by exact synthetic scope plus memory
ID. It proves version, expiry, tombstone, reset, and scope/owner behavior without
new persistence or W10 optimistic locking. Upsert versions increase by one;
delete/reset creates tombstones. Process restart clears this fake store. No raw
brief/page/form/personal value is admitted.

### Assembly and ledger

Fixed layer order establishes precedence. Earlier content hashes win. Per-layer
caps apply before a whole-result 32-item/16,384-byte/4,096-token cap. Additive
context endpoints preserve released W7/W8 endpoints. A context-backed Planning
run creates one existing `TotalBudgetLedger`, assembles once, and passes the
same object into W7 execution. W8 durable usage schema adds numeric W9 fields;
its existing high-water comparison automatically rejects decreases. Semantic
context never enters Temporal or Checkpoints.

## Consequences

- W9 behavior is deterministic, replayable, fake-only, and locally testable.
- Planning's Browser-only boundary and W8 opaque operational history remain
  intact.
- Organization memory is intentionally not production durable or authenticated.
- Fixed safe codes demonstrate mechanics, not natural-language retrieval or
  memory quality.
- Formal ablation conclusions, malicious-page resistance, real tenancy, and
  production storage remain deferred.

## Rejected alternatives

- New Context service: unnecessary network/trust/deployment surface for W9.
- Planning Agent database connection: violates the released isolation boundary.
- Store semantic context in Temporal: leaks meaning into operational history.
- New organization-memory migration: premature W10/W12 persistence and locking.
- SQLite/file persistence: adds machine paths and an ungoverned durable store.
- Vector database/embedding/provider: violates deterministic fake-only scope.
- Page/model-generated retrieval query or memory write: transfers authority to
  untrusted content.
- Generic memory/RAG framework: unnecessary future abstraction.
