# Evaluation protocol

## Purpose and current boundary

This document freezes W4 DOM-only evidence without converting deterministic
fake tests into Agent success claims. W3 database-fact grading remains the sole
task-success authority. W4 has no screenshot, vision path, Reporting run,
external benchmark, success-rate result, recovery result, or ROI claim.

## Preserved W3 task protocol

The ten W3 specs, canonical checksums, catalog checksum, fixture version,
6/2/2 Development/Validation/Reporting allocation, Reset/Seed semantics,
grader predicates, and manual baseline remain unchanged. Reporting tasks 009
and 010 remain frozen and unused for W4 tuning.

W4 acceptance candidates are only `w3-joiner-001` through
`w3-joiner-005`. Task 006 remains Development in the W3 catalog but is outside
the user-authorized five-task W4 acceptance set. Validation/Reporting results
must not influence W4 implementation or prompts.

## Deterministic fake-model protocol

Unit tests and CI use fake model output with declared zero external cost. They
must cover:

1. strict session, observation, action, result, model-decision, budget, and run
   schemas, including unknown fields/types/actions;
2. origin allowlist, dangerous schemes, direct API paths, external redirects,
   and local network isolation;
3. stable DOM-order observation, hidden/value filtering, text/node/element/
   serialized limits, and absence of visual/selector/credential fields;
4. current, forged, and stale `element_ref` behaviour;
5. success and failure for navigate, click, fill, select, read, scroll, wait,
   finish, and fail/escalate, plus unconditional cleanup;
6. valid fake action, invalid JSON, invalid action, repetition, no progress,
   step/call/time/token/cost exhaustion, and safe termination;
7. a Compose smoke that Reset/Seeds twice, invokes the fake Agent through an
   actual isolated Chromium session, then grades independently;
8. proof that fake `finish` leaves untouched initial state at its database-
   derived non-passing score rather than producing Agent-declared success.

The fake Compose smoke is infrastructure/contract evidence only. It is not one
of the five real-model task runs and is not an Agent success-rate sample.

## Real-model authorization gate

Before any real or paid model call, stop and obtain separate explicit user
authorization after disclosing:

- provider and exact model;
- prompt/config version and human-brief construction;
- planned tasks 001-005;
- maximum model calls, input/output tokens, wall time, retries, and cost.

Without authorization, record all five runs as not run. Do not estimate tokens
or cost as observed use and do not claim the Agent completed the tasks.

Authorization was received on 2026-07-26 for OpenAI `gpt-5.6-terra`, prompt
config `w4-dom-react-openai/1.0`, tasks 001-005, no retries, and revised hard
aggregate caps of 125 calls, 500,000 input tokens, 100,000 output tokens,
900 seconds, and USD 3.25. The 2026-07-27 run was observed at 0/5 and is kept
as historical evidence. The user then directed implementation of GLM scheme B.
That direction authorizes offline implementation, not a paid GLM call; the
fixed GLM model/prompt/cost-accounting details and hard caps must be disclosed
and explicitly authorized before GLM acceptance runs.

The separately authorized GLM `w4-dom-react-glm/1.0` and `1.1` runs were each
observed at 0/5; the separately authorized `1.2` and `1.3` runs were observed
at 3/5 and 4/5; the separately authorized 1.4 run was observed at 5/5. All
remain historical evidence and all authorizations have been consumed. The
successful 1.4 configuration is Zhipu `glm-5.2` Chat Completions, JSON-object
output parsed as a compact strict action choice before
trusted transport metadata is added and the full action is locally validated.
It additionally normalizes only an explicitly typed direct action or exact
legacy transport metadata, discards only a validated bounded non-finish
summary, bounds finish summary to 300 characters, and emits sanitized
validation type/path on failure.
Enabled thinking, high reasoning effort, deterministic sampling, no tools,
zero retries, and at most 2,048 output tokens per call remain fixed. No further
paid run is active without a new exact disclosure and explicit authorization.

## Five-task run protocol after authorization

For each task 001-005:

1. load and record task ID, spec checksum, fixture version, prompt/config, and
   model identity;
2. execute Reset/Seed twice and require identical full results/seed checksum;
3. render only the title, human instructions, and immutable supplied synthetic
   values into the human-facing brief; do not pass grader predicates;
4. create a fresh Browser/Context/Page at HRIS;
5. allow the Agent to act only through typed actions on the five W2 pages;
6. record every step/action/model call, actual input/output tokens, actual
   provider-reported cost, invalid output, failure, retry, timeout, repetition,
   and human intervention;
7. close browser resources, then invoke W3 Grader independently;
8. count completion only when Grader returns exactly 100/100 and `passed=true`.

Do not filter failed runs, alter W3 facts/predicates/checksums, tune against
Validation/Reporting, or treat model `finish`/natural language as evidence.

## Result interpretation

W4 may show that five fixed simple Development tasks are runnable only after
their actual authorized results exist. Five observations do not establish a
general success rate. W4 never claims planner quality, failure recovery,
production reliability, security against malicious pages, or enterprise ROI.

## Weekly evidence format

Every weekly report records exact scope, changed artifacts, dependency/browser
versions and image IDs, isolation settings, schema versions and limits, exact
commands/exit outcomes, W1-W3 regressions, fake-model results, all five
task/spec/seed rows, real-model authorization/run status, failures/retries,
secret/diff review, actual paid cost, limitations, and the next prohibited
boundary.

The W4 report is [evidence/week-04-report.md](evidence/week-04-report.md).
