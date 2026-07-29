# Week 07 plan - Bounded Planning DAG

## Objective

Preserve W1-W6 and add the smallest strict Planning layer: one immutable
task-local DAG, closed deterministic tool matching, one total monotonic ledger,
step-level runtime verification, and a frozen 30-template/90-instance synthetic
JML catalog. The complete boundary is `docs/agent-contract.md`.

## Planned outcomes

| Area | W7 outcome | Deliberate limit |
|---|---|---|
| Plan | Strict bounded immutable DAG and deterministic topology | No retry, partial replanning, checkpoint, or recovery |
| Tools | Versioned closed catalog and four-way intersection | No dynamic discovery, arbitrary API, selector, coordinate, or code |
| Verifier | Step-level current-observation/action validation | Not Grader; no expected state or database |
| Budget | One monotonic W6+W7 ledger | No reset on steps, switches, probes, failure, or finish |
| Agent | Separate fake-only Planning service over one W6 session | No Sandbox/Arena/DB/Grader/provider route |
| JML | 30 templates, three variants each, stable manifests | Reporting generated/frozen only; no W15 result use |
| Sandbox | Five minimal employee-owned typed transitions | No migration, delete, generic patch, or approval |
| Evaluation | W4-W6 regressions plus W7 fake smoke | Circuit/isolation evidence, not real planning capability |

## Implementation sequence

1. Verify W6 release/tag/worktree and create `week/07-planning`.
2. Freeze W7 contract, exact allowlist, ADR, threat/evaluation deltas, JML
   checksum/licence rules, evidence skeleton, README/changelog, and branch guide.
3. Implement and test strict Planning schemas, DAG validation/topology,
   deterministic fake planner, tool matcher, Verifier, and monotonic ledger.
4. Implement Planning Agent execution through one W6 Hybrid session with
   dependency enforcement, current references, verification probes, terminal
   cleanup, and ungraded finish.
5. Implement the independent JML catalog/generator/reset/grader plus the five
   typed non-deleting Sandbox transitions and UI controls.
6. Add Planning-only network isolation, CI quality job, profile-only W7 smoke,
   and preserve W4/W5/W6 smokes unchanged.
7. Run all W1-W7 locks, quality gates, catalog/checksum checks, Compose,
   migrations, smokes, secret scans, exact-path audit, diff/staged review, and
   cleanup. Record only observed facts.
8. Do not call a real model, use Validation for repeated tuning, run Reporting,
   push, open a PR, merge, tag, release, or begin W8.

## Fixed data and acceptance

- Catalog: 12 Joiner, 8 Mover, 10 Leaver; variants v1-v3; 90 instances.
- Development/Validation/Reporting templates: 18/6/6, with per-process split
  8/2/2 Joiner, 4/2/2 Mover, and 6/2/2 Leaver.
- Pair W6 and W7 on `w3-joiner-001` with the unchanged seed checksum.
- W7 immediate finish independently grades 30/100 false.
- Fresh W7 Joiner completion ends `finished_ungraded` then independently grades
  exactly 100/100 true.
- One W7 Development Joiner, Mover, and Leaver each proves equal Reset/Seed,
  untouched failure, bounded completion, exact independent 100/100 grade.
- Reporting is loaded and checksum-frozen only. Validation and Reporting never
  tune the Planner.

## Handoff boundary

W7 ends with one-shot immutable planning and no retry. Temporal, checkpoints,
idempotency, recovery, fault injection, retries, and runtime local replanning
belong to W8.
