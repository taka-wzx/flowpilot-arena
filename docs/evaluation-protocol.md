# Evaluation protocol

## Purpose and current boundary

This document freezes W5 Vision-only evaluation discipline without turning a
deterministic fake into a visual-capability claim. W3 database-fact grading
remains the sole task-success authority. W5 adds bounded screenshot/grounding
plumbing but no real VLM/OCR result unless separately authorized.

## Preserved W3 task protocol

The ten W3 specs, canonical checksums, catalog checksum, fixture version,
6/2/2 Development/Validation/Reporting allocation, Reset/Seed semantics,
grader predicates, and manual baseline remain unchanged. W5 Development
candidates are only w3-joiner-001 through w3-joiner-005. Task 006 stays
outside this W5 acceptance set. Validation and Reporting must not influence W5
implementation, prompt/config, or visual tuning.

Existing W2 pages are the synthetic screenshot surface. If those fixed tasks
later prove insufficient for a valid visual evaluation, do not alter them:
submit a minimum W5 visual-task proposal and obtain user direction first.

## Deterministic fake-vision protocol

Unit tests and CI use deterministic fake vision output with declared zero
external cost. They must cover:

1. strict visual session, observation, grounding, action, result, model
   decision, budget, and run schemas, including unknown fields/types/actions;
2. current local-origin path policy, dangerous schemes, direct API paths,
   redirects, and no external/cross-origin capture;
3. fixed JPEG encoding, viewport/pixel size, image byte/count/time limits,
   failed-attempt accounting, no screenshot file/URL path, and capture cleanup;
4. no DOM/AX/title/URL/name/role/text/selector/element_ref/form/Cookie/storage
   field in a Vision Agent observation or model context;
5. current, forged, mismatched, and stale screenshot/grounding behavior;
6. success and failure for navigate, grounded click/fill/select/read/scroll,
   bounded wait, finish, fail, and unconditional cleanup;
7. strict rejection of arbitrary x/y/rectangle, selector, code, path, URL,
   unknown field, unsupported target, and stale reference;
8. fake valid grounded action, invalid JSON/action, repetition, no progress,
   image/count/bytes/pixels/capture-time/step/call/time/token/cost exhaustion,
   and safe termination;
9. a W4 DOM fake Compose smoke regression and a W5 Compose smoke that
   Reset/Seeds twice, invokes fake Vision Agent through actual isolated
   Chromium, and grades independently;
10. proof that fake finish leaves untouched initial state at its non-passing
    database-derived grade rather than producing Agent-declared success;
11. after a second equal Reset/Seed pair, the bounded `complete_joiner` fake
    scenario must use current visual Grounding references and a fixed
    supplied-values brief, finish ungraded, and receive an unchanged W3
    100/100, `passed=true` grade.

The fake W5 smoke is infrastructure/contract evidence only. Its 100/100
completion subrun proves that Agent finish cannot substitute for the external
Grader even when the deterministic test policy creates the required synthetic
records. It is not a real VLM/OCR call, a five-task Vision-only success rate,
or proof of visual understanding.

## Real VLM/OCR authorization gate

Before any real or paid visual/OCR model call, stop and obtain separate explicit
user authorization after disclosing:

- provider, exact model, and fixed endpoint;
- prompt/config version and human-brief construction;
- image MIME, maximum resolution/pixels, maximum image count, and in-memory
  data handling;
- exact planned task IDs;
- maximum model calls, input/output tokens, images/bytes/capture time, wall
  time, retries, and cost.

The W4 ZHIPU key, endpoint, prompts, and DOM results do not authorize a W5
visual call. Without W5 authorization, record all real VLM/OCR runs as not run
with zero observed W5 calls/tokens/cost. Do not estimate unobserved use or
represent a DOM-only result as Vision-only.

## Five-task protocol after authorization

For each authorized task among w3-joiner-001 through w3-joiner-005:

1. record task ID, spec checksum, fixture version, model identity, prompt/config,
   image envelope, and hard caps;
2. execute Reset/Seed twice and require identical full result/seed checksum;
3. render only title, human instructions, and immutable supplied synthetic
   values into the human-facing brief; never pass grader predicates;
4. create a fresh Browser/Context/Page at HRIS and confirm only the bounded
   visual observation reaches Vision Agent;
5. record every screenshot count/bytes/pixels/capture duration, model call,
   input/output token, provider-reported cost, invalid output, failure, retry,
   timeout, and human intervention;
6. close all browser/temporary visual resources, then invoke W3 Grader
   independently;
7. count completion only when unchanged Grader returns exactly 100/100 and
   passed=true.

Do not filter failures, modify W3 facts/predicates/checksums, tune against
Validation/Reporting, retain raw images/OCR text, or treat model finish/natural
language as evidence.

## Result interpretation

Only an observed, separately authorized, independently graded visual run may
report a fixed Development Vision-only result. Five observations do not prove
general visual capability, OCR robustness, safety against malicious imagery,
recovery, production reliability, or enterprise ROI. Fake results prove only
the bounded circuit and Grader isolation.

## Weekly evidence format

Every W5 report records exact scope/changed artifacts, dependencies/image
versions, isolation settings, visual schemas/limits, lifecycle/cleanup,
commands and exits, W1-W4 regressions, fake results, all real task rows or
not-run rows, actual image/token/cost/latency metrics, secret/diff review,
limitations, and the W6 boundary. The current skeleton is
[evidence/week-05-report.md](evidence/week-05-report.md).
