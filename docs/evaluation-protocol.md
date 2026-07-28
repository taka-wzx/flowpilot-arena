# Evaluation protocol

## Purpose and current boundary

This document freezes W6 Hybrid evaluation discipline without turning a
deterministic fake route into a Hybrid capability claim. W3 database-fact
grading remains the sole task-success authority. W6 adds route, compression,
and cross-modality validation only; no real model is authorized.

## Preserved task protocol

The ten W3 specs, canonical checksums, catalog checksum, fixture version,
6/2/2 allocation, Reset/Seed semantics, grader predicates, and manual
baseline remain unchanged. W6 Development candidates are only
w3-joiner-001 through w3-joiner-005. Validation and Reporting do not influence
W6 implementation, policy, fake behavior, or compression limits.

The same fixed synthetic pages support paired DOM-only, Vision-only, and
Hybrid fake circuit runs. If they cannot establish a required routing,
compression, or action-validation property, propose the smallest separate W6
evaluation design and obtain user direction; do not alter a task or grader.

## Deterministic fake protocol

Unit tests and CI use deterministic fakes with zero external cost. They cover:

1. strict Hybrid session, observation request/response, route decision,
   compression, action envelope/result, model decision, budget, and run/result
   schemas including unknown fields/types/actions;
2. one Browser/Context/Page per Hybrid task, current modality only, and no W4
   or W5 API regression;
3. fixed DOM structural signal bounds without page content and deterministic
   compression byte/node/element/history truncation;
4. DOM-first route default, closed reason codes, refusal rules, switch hard
   cap, and no cross-task/learned route state;
5. one-model-modality isolation: DOM model context contains no JPEG/grounding;
   visual context contains no DOM/AX/title/URL/element ref/page text;
6. current, forged, wrong-mode, cross-session, stale-generation, stale-observation,
   stale-screenshot, and stale-grounding rejection before Playwright;
7. success/failure for current DOM and visual typed actions, observation
   switching, action failure refresh, and unconditional cleanup;
8. total step/call/switch/repetition/progress/DOM/image/token/cost/time limits
   that cannot reset after a switch;
9. W4 fake DOM Compose regression, W5 fake Vision Compose regression, and W6
   Hybrid Compose smoke through actual isolated Chromium; and
10. proof that finish remains ungraded and independent W3 grading sees actual
    task facts only.

## W6 fake Hybrid smoke

The trusted outer caller uses the same task ID, human brief construction, and
equal Reset/Seed protocol as W4/W5. It runs two fresh subruns:

1. immediate finish must return finished_ungraded at zero external cost and
   independently grade untouched state at exactly 30/100, passed=false;
2. after a fresh equal Reset/Seed pair, deterministic completion under the
   closed visual_recovery route category must make a real Worker DOM-to-Vision
   switch, deliberately reject wrong-mode and stale visual references, use
   current references for completion, respect compression and total budgets,
   clean up, return finished_ungraded, and independently grade exactly
   100/100, passed=true.

The smoke records only task/spec/seed checksums, safe route reasons/count,
numeric DOM/compression/image/action/call/token/cost/latency metrics, terminal
state, and independent grade. It records no raw DOM, screenshot, OCR, page
text, or form value. These fake results prove a bounded circuit and Grade
isolation, not real DOM, Vision, Hybrid, OCR, or VLM performance.

## Real-model authorization gate

No W6 real DOM/Vision/Hybrid, VLM, or OCR call is authorized. Before any
provider call, stop and obtain separate explicit user approval after
disclosing provider, exact model, endpoint, prompt/config, selected-modality
input handling, image MIME/resolution/count, task IDs, retries, call/token/
image/DOM/time/cost caps, and the planned independent grade sequence.

Without authorization, final evidence records all real model rows as not run
with zero observed calls/tokens/cost. W4 historical DOM authorization and W5
fake result do not carry forward.

## Result interpretation and W7 boundary

Only observed, separately authorized, independently graded runs may make a
fixed Development result claim. W6 fake outcomes cannot establish visual
reasoning, route quality, recovery, generalization, safety against malicious
pages, production reliability, or enterprise ROI. W7 planning, verifier, task
DAG, and tool matching remain out of scope.
