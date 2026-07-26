# Evaluation protocol

## Purpose and current boundary

This document freezes evidence and future evaluation invariants. W3 now has a
deterministic Arena foundation, but it still has no Agent, browser automation,
benchmark run, experimental comparison, success-rate claim, or ROI result.

## W3 task foundation protocol

The W3 dataset contains exactly ten original synthetic joiner Task Specs. Each
has provenance, schema/fixture version, human instructions, fixed initial facts,
structured expected final facts, ordered grader predicates, split, and a
canonical SHA-256 checksum. Run results are never written into a spec.

The conservative fixed split is:

- Development: `w3-joiner-001` through `w3-joiner-006`;
- Validation: `w3-joiner-007` and `w3-joiner-008`;
- Reporting: `w3-joiner-009` and `w3-joiner-010`.

This is a small foundation set, not the roadmap's final 30 templates. The two
Reporting specs and their checksums freeze on the first W3 commit. They must not
be changed or used for tuning before W15; an essential correction requires a
new spec/fixture version and explicit evidence rather than silent replacement.

## Deterministic acceptance protocol

For each of the ten tasks:

1. Validate the strict schema, references, predicate weights, split, fixture,
   per-spec checksum, and catalog checksum.
2. Execute Reset/Seed twice and compare the complete stable fact summary and
   checksum. No task-owned residue may remain; unrelated W2/manual rows must
   remain unchanged.
3. Grade the untouched initial state and confirm it does not pass.
4. Create the exact expected facts through supported business operations and
   confirm a 100/100 passing grade.
5. Grade again and compare serialized results and before/after facts.

The deterministic test suite must also prove that partial completion, a wrong
employee link, duplicate task-owned business records, an elevated IAM role,
and complete non-completion cannot score 100. A human or future Agent cannot
declare completion; only the database-fact grader result is authoritative.

Grading excludes browser/page/DOM/screenshot/log/model output, baseline notes,
and task prose. No external API or model may contribute to task facts or scores.

## Human baseline protocol

W3 proves only that a manual record can be stored. It does not establish an
efficiency gain or enterprise ROI. A record contains:

- catalog `task_id` and synthetic record ID;
- an anonymous `anon-...` operator alias;
- offset-aware start/end time and derived duration;
- manually counted actions;
- final score derived from the deterministic grader at record time;
- optional synthetic notes.

The tool captures no personal identity, key content, screenshot, page state,
selector, extension data, or browser telemetry, and performs no browser action.

## Future evaluation invariants

Later milestones must preserve these roadmap rules:

1. Use resettable deterministic facts rather than self-reported completion.
2. Split by task template/specification, never random task instances.
3. Keep Reporting configuration/spec hashes frozen and do not tune against them
   before W15.
4. Record task provenance/licence, fixture/reset version, model identity,
   prompt/configuration version, exclusions, retries, and actual cost.
5. Keep security ablations isolated from real write operations.
6. Run declared baselines/ablations under comparable conditions and report
   uncertainty and failures rather than filtering them away.

## Weekly evidence format

Every weekly report records:

| Field | Required record |
|---|---|
| Scope | Contract reference and explicit non-goals |
| Inputs | Code/data/model provenance relevant to that week |
| Commands | Exact validation commands and exit outcomes |
| Artifacts | Commit/PR context; screenshots/traces only if authorized and created |
| Results | Measured values only; no unsupported claims |
| Limits | Missing tools, infrastructure, or intentionally deferred tests |
| Cost | Paid-model use and actual spend; W1–W3 are zero |
| Next boundary | What the next week may do and what remains prohibited |

The W3 evidence report is [evidence/week-03-report.md](evidence/week-03-report.md).
