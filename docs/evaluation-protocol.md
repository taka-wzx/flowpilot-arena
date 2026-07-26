# Evaluation protocol

## Purpose

This document freezes the evidence rules that later evaluation work must
follow. It does not create an Arena, task specification, grader, baseline,
benchmark adapter, dataset, metric collection, or evaluation result in W1.

## W1 evidence protocol

W1 may report only foundation evidence:

- exact dependency-lock, lint, format, type-check, unit-test, build, Compose,
  and secret-scan commands;
- observed exit status and concise result for each command;
- a health-endpoint smoke response;
- the changed-file list and Git diff review result;
- zero paid-model calls, zero model cost, and zero real enterprise-system
  calls;
- unavailable local prerequisites and their effect on validation.

W1 must not report an agent success rate, benchmark score, recovery rate,
security metric, latency target, cost metric, or production ROI. There is no
valid system under test for those measures yet.

## Future evaluation invariants

When later milestones add evaluation capabilities, they must preserve these
rules from the roadmap:

1. Use resettable, deterministic evaluation state rather than self-reported
   agent completion.
2. Split by task template rather than randomly splitting task instances.
3. Freeze the Reporting configuration/hash in W3 and do not tune against it
   before W15.
4. Record task provenance, licence, seed/reset configuration, model identity,
   prompt/configuration version, and actual cost.
5. Keep security ablations isolated from real write operations.
6. Run declared baselines and ablations under comparable conditions.
7. Report failures, retries, exclusions, and uncertainty instead of filtering
   them away.

## Weekly evidence format

Every weekly report should contain:

| Field | Required record |
|---|---|
| Scope | Contract reference and explicit non-goals |
| Inputs | Code/data/model provenance relevant to that week |
| Commands | Exact validation commands and exit outcomes |
| Artifacts | Commit/PR context, screenshots/traces only if created |
| Results | Measured values only; no unsupported claims |
| Limits | Missing tools, infrastructure, or intentionally deferred tests |
| Cost | Paid-model use and actual spend; W1 is zero |
| Next boundary | What the next week may do and what remains prohibited |

The W1 report at [evidence/week-01-report.md](evidence/week-01-report.md)
will be completed only after its checks run.
