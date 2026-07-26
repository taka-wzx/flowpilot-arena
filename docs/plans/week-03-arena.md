# Week 03 plan — Arena Foundation

## Objective

Build the smallest deterministic Arena foundation that lets a human repeatably
Reset/Seed, perform, grade, and anonymously record baseline work for ten fixed
synthetic onboarding tasks. The authoritative boundary is
[../agent-contract.md](../agent-contract.md).

## Planned outcomes

| Area | W3 outcome | Deliberate limit |
|---|---|---|
| Task data | Ten strict, versioned, canonical-checksummed JSON specs | Not the final 30-template/90-instance dataset |
| State | Task-owned transactional Reset/Seed in the W2 database | No generic reset, random fixtures, faults, or production data |
| Grading | Pure database-fact predicates with deterministic detail | No page, log, browser, screenshot, model, or prose inference |
| Human baseline | Anonymous timing/action/score record API | No browser control, keyboard capture, telemetry, or ROI claim |
| Runtime | Reuse W2 API/web/PostgreSQL and W1 services | No new microservice or infrastructure component |
| Evidence | Ten-task acceptance, migration, runtime, regression, diff and secret facts | No Agent/benchmark result or paid model call |

## Implementation sequence

1. Freeze W3 instructions, exact paths, assumptions, split rules, ADR, plan,
   and evidence template before application changes.
2. Add the forward-only W3 migration and task-ownership/baseline ORM fields
   without modifying the W2 foundation migration.
3. Define strict Task Spec models, canonical JSON/checksum rules, catalog-wide
   reference validation, and ten fixed joiner documents.
4. Implement one-transaction Reset/Seed with task-only deletes, fixed initial
   facts, stable summaries, and downstream ownership inheritance.
5. Implement the read-only predicate grader and narrow `/api/arena` task,
   Reset/Seed, grade, and manual-baseline endpoints.
6. Add deterministic tests for schema rejection, catalog/checksum stability,
   two-pass Reset/Seed identity, rollback, correct/partial/wrong/elevated/
   duplicate/untouched grading, grader non-mutation, baseline validation, and
   management API boundaries.
7. Update architecture, threats, evaluation protocol, README, changelog, and CI
   only where observed implementation requires it.
8. Run W1/W2/W3 locks and quality gates; migrate PostgreSQL from the W2 head;
   check Alembic drift; start Compose; exercise all ten tasks twice; manually
   complete one task through the five pages; grade it; and record one anonymous
   baseline sample.
9. Review the full contract-owned diff and secret exposure, finish the evidence
   report, explicitly stage only allowlisted paths, create a local commit if all
   available gates pass, and stop before W4.

## Frozen data rules

- Task IDs are `w3-joiner-001` through `w3-joiner-010`.
- Each task has one target employee and one clearly named decoy employee.
- Numeric IDs, start dates, names, departments, roles, locations, usernames,
  tickets, mailboxes, and assets are fixed in source.
- Emails end in `.invalid`; assets use the `SYN-W3-...` namespace.
- Tasks cover varied fictional employees, departments, job titles, locations,
  devices, and dates while remaining completable through the W2 pages.
- Development receives tasks 001–006, Validation 007–008, Reporting 009–010.
  Reporting content/checksums freeze on first W3 commit and are not tuned
  against results before W15.

## Acceptance commands

Run every app-local command in [../../AGENTS.md](../../AGENTS.md), then the
Compose migration/runtime checks and the ten-task acceptance sequence described
there. The evidence report records exact commands and observed results; an
unavailable executable is a limitation, not a silently weakened gate.

## Handoff boundary

W4 may later add an isolated Playwright worker, DOM/accessibility observation,
typed browser actions, and a DOM ReAct baseline. W3 creates no browser runtime,
automation, observation, action schema, Agent loop, model call, or benchmark.
