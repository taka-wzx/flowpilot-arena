# ADR 0007: Bounded immutable Planning DAG and isolated runtime Verifier

- Status: Accepted for W7
- Date: 2026-07-28

## Context

Released W6 provides one Hybrid Browser session with one Browser, Context, and
Page, selected current modality, strict typed actions, deterministic routing,
and total Hybrid budgets. W7 must add dynamic task-specific planning, tool
matching, step verification, and the full synthetic JML catalog without
changing W4-W6 APIs, exposing Arena facts to the Agent, or starting W8
replanning/recovery.

The principal risks are a plan objective authorizing tools, malformed or
unbounded DAGs, out-of-order execution, page/model data expanding authority,
Verifier becoming a hidden Grader, a new budget resetting W6 counters, and
Mover/Leaver support introducing deletion or generic patch APIs.

## Decision

Create `apps/planning_agent` as a separate Python 3.13 FastAPI service. It
connects only to Browser Worker over internal `planning-worker`. It has no
Sandbox, Arena, database, Grader, repository, Docker socket, credential,
provider-egress, persistence, Shell, SQL, or JavaScript capability.

Planning Agent creates one released W6 Hybrid session and retains it for the
whole run. The shipped fake executor uses current DOM observations and
Worker-issued references; Browser Worker remains the owner of Playwright,
generation/modality validation, reference invalidation, and one
Browser/Context/Page cleanup.

Plans are frozen Pydantic models with closed operation/page/context/action/
condition/risk/retry/fallback enums. Objective text is bounded untrusted
display data. Authority comes from the finite process/category, closed
operation, supplied-values schema, fixed tool catalog, current Worker
allowlist, and remaining budget.

Freeze plan limits at 16 nodes, 24 edges, depth 8, width 8, four dependencies
per node, 40-character step IDs, 240-character objectives, eight
preconditions/postconditions each, and 32,768 canonical UTF-8 bytes. Require a
single root and deterministic lexical topological tie-breaking. Reject cycles,
self/unknown/duplicate dependencies, duplicate/unknown IDs, unreachable
nodes, cap breaches, and execution before all dependencies are verified.

Use a versioned deterministic tool catalog mapped only to released W6
observation and typed-action capabilities on `/hris`, `/itsm`, `/iam`,
`/assets`, and `/mail`. A match is the intersection of global, step,
page/modality, and budget allowlists. Unknown candidates return a safe
rejection and cannot reach Worker.

The runtime Verifier consumes only current observation, current action-result
summary, trusted step conditions, step identity, and remaining budget. It
returns `verified`, `not_verified`, or `inconclusive`. It never reads a Task
Spec, expected state, grader predicate/checksum, database, Arena, or page
success prose. Negative/inconclusive results stop or escalate under the fixed
fallback and never become success.

Use one task-local monotonic ledger for planning, matching, execution, routing,
verification, W6 observation/image/action/model/token/cost limits, and W7
counters. No code path can replace or reset it. `finish` remains
`finished_ungraded`.

Add an independent W7 JML package beside the immutable W3 Arena package. One
strict JSON catalog freezes 12 Joiner, 8 Mover, and 10 Leaver templates.
Generator `w7-jml-variant-generator/1.0` creates three stable variants per
template and freezes catalog, instance, split, and Reporting checksums.

Use existing database columns. Add only employee-owned typed transitions:
HRIS transfer/disable, ITSM close, IAM revoke, Asset release, and Mail disable.
No table, column, migration, physical delete, arbitrary field patch, approval
artifact, or generic transition API is introduced. Planning Agent can reach
these controls only through fixed Sandbox UI and Browser Worker.

## Consequences

- Plan structure and order are reproducible and bounded, but W7 has no retry,
  partial replanning, checkpoint, recovery, or learned policy.
- The Agent cannot grade itself; runtime verification proves only current
  step evidence, while independent database-fact grading remains authoritative.
- Current DOM names may select an opaque reference only after the operation
  and action are already authorized; page text cannot add a tool.
- The 30-template catalog is stable and independent of W3, while 90 instances
  avoid duplicated hand-written fixtures.
- Existing status columns avoid migration risk. The tradeoff is that W7 state
  integrity is enforced by strict APIs and grader checks rather than new DB
  enum constraints.

## Rejected alternatives

- Mutate W3 Task Specs/catalog: breaks released checksums and split discipline.
- Put Planner/Verifier in Browser Worker or Sandbox: collapses trust
  boundaries and grants Playwright/database capability.
- Give Planning Agent Arena or Grader access: leaks expected state and permits
  self-grading.
- Let objective/page/model output name tools: turns untrusted text into
  authority.
- Build a generic plugin/tool/model framework: unnecessary W8+ abstraction.
- Add retries, local replanning, Temporal, or checkpoints: W8 scope.
- Add delete or arbitrary PATCH endpoints: exceeds the synthetic JML minimum.
