# Evaluation protocol

## Purpose and current boundary

This document freezes W7 Planning and JML evaluation discipline without
turning deterministic fake execution into a real planning, reasoning, or
Verifier capability claim. Independent database-fact grading remains the only
task-success authority. No real model, VLM, or OCR call is authorized.

## Preserved W3-W6 protocol

The ten W3 specs, canonical/catalog checksums, fixture version, 6/2/2 split,
Reset/Seed, grader predicates, and manual evidence remain unchanged. W4 DOM,
W5 Vision, and W6 Hybrid APIs and fake smokes run without semantic change.

On `w3-joiner-001`, the trusted caller uses identical Reset/Seed and human
brief inputs for the released W6 Hybrid baseline and W7 Hybrid+Planner
baseline. Immediate finish must remain 30/100 false. Fresh bounded completion
must return `finished_ungraded` and only afterward independently grade exactly
100/100 true.

## W7 JML freeze protocol

The separate W7 catalog must strictly load exactly 30 templates and generate
90 instances with stable IDs/checksums:

- 12 Joiner, 8 Mover, 10 Leaver;
- three variants per template;
- Development 8/4/6, Validation 2/2/2, Reporting 2/2/2;
- catalog, generator, fixture, split-manifest, and Reporting-manifest versions
  and checksums fixed in source/evidence.

All data is original synthetic Apache-2.0 content using `.invalid` email and
`SYN-W7-` assets. Tests verify two Reset/Seeds produce the same facts/checksum
for all 90 instances and that grader schemas are deterministic. Validation is
not used for repeated tuning. Reporting is generated, loaded, schema/checksum
validated, and frozen only; no Reporting Agent run, grade inspection, or
result-driven change occurs before W15.

## Deterministic schema and unit protocol

Unit tests cover:

1. strict versioned plan, DAG, step, dependency, condition, tool, validation,
   execution, Verifier, ledger, and run/result schemas, including unknown fields;
2. node/edge/depth/width/dependency/field/serialized-byte caps;
3. duplicate/unknown IDs, self-dependency, cycle, missing dependency, multiple
   roots, unreachable nodes, and deterministic lexical topology;
4. immutable one-plan identity and refusal of execution before dependencies
   are verified;
5. the global ∩ step ∩ page/modality ∩ budget tool intersection, plus unknown,
   disallowed, wrong-page, wrong-modality, and exhausted-budget rejection;
6. objective/brief/page/model/risk data cannot expand operations or tools;
7. Verifier closed statuses/reasons, current evidence only, and negative/
   inconclusive results never treated as success;
8. one monotonic ledger across planning, matching, action, routing,
   observation, verification, token/cost, failure, and finish paths;
9. one W6 Hybrid session per Planning run, current references, verification-
   probe invalidation, cancellation/startup/terminal cleanup, and no second
   session or direct Sandbox/Arena/Grader access;
10. strict synthetic transition prior states, no physical delete, JML
    Reset/Seed ownership, database-fact grading, and W3 regression.

## W7 fake Planning Compose smoke

The trusted profile-only caller proves:

1. invalid cycle, missing-dependency, over-limit plans and out-of-order step
   execution are rejected;
2. an unknown/unauthorized tool probe is rejected without Worker execution;
3. a forced inconclusive Verifier subrun stops/escalates, cleans up, and is not
   called success;
4. immediate finish on the fixed W3 task remains `finished_ungraded` and
   independently grades 30/100 false;
5. a fresh W3 completion executes a multi-node, multi-dependency immutable DAG
   in deterministic order through one W6 session, performs successful matches
   and step verification, preserves total counters, cleans up, returns
   `finished_ungraded`, and independently grades 100/100 true; and
6. one Development Joiner, Mover, and Leaver instance each has equal Reset/
   Seed results, untouched failing grade, bounded deterministic completion,
   `finished_ungraded`, and exact independent 100/100 passing grade.

Smoke output is restricted to schema versions, IDs/checksums, DAG counts/depth/
order, step-state counts, tool/reason counts, route/DOM/compression/image/action/
call/token/cost/latency metrics, terminal status, and independent grades. It
contains no raw brief, plan prose, DOM, screenshot, OCR, page/form content,
credential, endpoint, or machine path.

## Real-model authorization gate

No W7 real Planner, Verifier, DOM/Vision/Hybrid model, VLM, or OCR call is
authorized. Before any provider call, stop and obtain separate explicit user
approval after disclosing provider, exact model, endpoint, prompt/config,
selected input envelope, task IDs/splits, retries, and every call/token/image/
DOM/time/cost cap. Without authorization, final evidence records not run,
0 calls, and 0 cost.

## Interpretation and W8 boundary

Fake results prove strict schemas, deterministic wiring, dependency/tool/
Verifier/ledger isolation, current Worker action paths, synthetic state
closure, and independent grading only. They do not establish real planning,
reasoning, verification quality, generalization, malicious-page resistance,
production reliability, or enterprise ROI. Retry, checkpoint, recovery,
idempotency, Temporal, fault injection, and partial replanning begin in W8.
