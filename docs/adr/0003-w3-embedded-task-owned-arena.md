# ADR 0003: Embedded task-owned Arena foundation

- Status: Accepted for W3
- Date: 2026-07-26

## Context

W3 needs versioned Task Specs, task-level deterministic Reset/Seed, database
fact grading, ten fixed synthetic joiner tasks, and manual-baseline recording.
The W2 Sandbox already has the five required business entities, pages, one
FastAPI backend, and one PostgreSQL database. The roadmap leaves open whether
Arena management is a separate service and how task ownership is represented.

The conservative choice must preserve W1/W2, prevent a reset from touching
manual development data, keep the grader independent of browser state, and
avoid scaffolding W4 or later infrastructure.

## Decision

Implement Arena as a visibly separate Python package and `/api/arena` router
inside `apps/sandbox_api`. Reuse its SQLAlchemy transaction boundary and
PostgreSQL database; do not create another deployable service or add Arena
behaviour to `control_api`.

Store the ten Task Specs as strict source-controlled JSON resources. Validate
unknown fields, IDs, references, synthetic values, predicate weights, split
allocation, and a SHA-256 checksum of canonical JSON. Calculate a catalog hash
from sorted task/checksum pairs. Runtime and test results remain separate from
these immutable specifications.

Add nullable `arena_task_id` ownership columns to the five W2 fact tables via a
new migration. Existing W2/manual rows remain null. Seeded target and decoy
employees carry the selected task ID; records created through the five business
APIs inherit it from their employee. Reset/Seed deletes only matching owned rows
in dependency order and recreates fixed initial rows inside one transaction.
Fixed initial primary keys and values make repeated fact summaries identical.

Evaluate an ordered, enumerated predicate list solely through read queries over
the five fact tables. A grade call never writes or infers success conditions
from task prose. It returns a 0–100 score, a pass flag that is true only at 100,
and stable per-predicate facts.

Store manual-baseline records in one new table behind the Arena router. The
caller supplies a catalog task ID, constrained anonymous alias, start/end
timestamps, manual action count, and optional synthetic notes. Duration is
derived and validated; the final score is obtained from the read-only Grader
against the current database state, so the caller cannot self-report success.
No browser automation or telemetry is introduced.

Use a conservative fixed split of six Development, two Validation, and two
Reporting specs. This is not the final roadmap dataset. Reporting spec content
and checksums freeze on the first W3 commit and must not be tuned before W15.

## Consequences

- Reset scope is enforced by database facts rather than identifier guesses or
  arbitrary caller queries, and W2 manual rows are preserved.
- A decoy employee per task makes incorrect associations representable and
  safely cleanable without introducing faults or random data.
- Existing pages remain usable for both ordinary W2 data and W3 human task
  completion; no frontend automation or new service is required.
- Arena management shares the Sandbox process and database failure domain. This
  is acceptable for the local synthetic W3 environment and is not a production
  authorization design.
- The new migration is required for ownership and baseline persistence; the
  released W2 migration remains unchanged.

## Rejected alternatives

- **A new Arena microservice/database:** adds deployment and distributed
  transaction complexity without improving the W3 acceptance proof.
- **Reset by guessed names or prefixes:** cannot safely distinguish task-owned
  mistakes from unrelated manual records.
- **Global truncate/reset:** violates task isolation and can destroy W2 data.
- **Mutable database Task Specs:** weakens versioning and risks writing run
  results into the specification source.
- **Browser-based grading or baseline capture:** violates the database-fact and
  no-automation W3 boundary.
- **Random fixture generation:** makes replay and checksums unstable and starts
  later dataset-generation work prematurely.
