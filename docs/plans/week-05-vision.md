# Week 05 plan — Vision Agent Foundation

## Objective

Add the smallest safe Vision-only foundation over the released W1-W4 stack:
bounded synthetic viewport screenshots, strict visual observation and grounding,
and a separate deterministic-fake Vision Agent. The unchanged W3 Grader remains
the sole authority for task success. The complete boundary is
[../agent-contract.md](../agent-contract.md).

## Planned outcomes

| Area | W5 outcome | Deliberate limit |
|---|---|---|
| Browser Worker | Separate visual sessions with bounded JPEG capture and cleanup | No browser UI/desktop/cross-origin capture, image storage, path, URL, download, or provider access |
| Visual observation | One current image plus opaque screenshot-scoped grounding references | No DOM/AX text, selectors, OCR text API, form values, Cookies, or Local Storage |
| Grounding/actions | Output-only boxes and strict grounding-bound action union | No arbitrary coordinate, selector, code, JavaScript, or unsupported URL |
| Vision Agent | Separate fake-only bounded ReAct service | No DOM fallback, router, provider adapter, planner, verifier, recovery, or memory |
| Evaluation | Existing five Development tasks, external Reset/Seed and Grader | Fake 100/100 is deterministic circuit evidence, not a real VLM result or visual-capability claim |
| Runtime/evidence | Fake-only Compose/CI, image/call/token/cost/latency accounting | No model key, egress, stored screenshot, or Reporting/Validation tuning |

## Implementation sequence

1. Verify released W4 baseline and synchronized main; create week/05-vision;
   freeze this plan, W5 contract/allowlist, ADR, threat/evaluation deltas, and
   evidence skeleton before code.
2. Define strict visual session, observation, grounding, visual action, and
   result schemas before Playwright changes.
3. Implement fixed viewport JPEG capture, byte/count/time limits, screenshot
   and grounding invalidation, and unconditional cleanup in Browser Worker.
4. Implement visual-session API endpoints while retaining all W4 DOM endpoints
   and tests unchanged.
5. Implement the independent fake-only Vision Agent with a visual-only model
   context, strict decisions, bounded generic history, numeric image metrics,
   monotonic budgets, and safe termination.
6. Add deterministic tests for schema rejection, image limits, origin/viewport
   restriction, no DOM leakage, current/forged/stale grounding, every typed
   action, cleanup, fake-model invalid output, repetition/progress, and every
   image/call/token/cost/time cap.
7. Add Compose isolation, CI quality gates, a W4 DOM smoke regression, and a
   W5 fake vision smoke that first preserves untouched 30/100 grading, then
   Reset/Seeds again and requires an independent 100/100 `complete_joiner`
   result through real Chromium.
8. Update current architecture, threats, evaluation protocol, README, changelog,
   and evidence from observed facts only.
9. Run all available W1-W5 quality, build, Compose, migration, smoke, secret,
   exact-allowlist, diff, and cleanup gates. Record unavailable tooling rather
   than weakening it.
10. Do not call a real VLM. Record it as not run unless the user later receives
    a complete disclosure and gives separate explicit authorization.
11. Review exact staged/unstaged diffs, explicitly stage only allowlisted
    files, create a local commit only after observed gates pass, and stop before
    W6.

## Fixed acceptance inputs

- Development task candidates: w3-joiner-001 through w3-joiner-005.
- W3 specs, facts, checksums, fixture version, Reset/Seed, and grader semantics
  remain unchanged.
- Each run begins with two equivalent Reset/Seed responses and a fresh
  Browser/Context/Page at HRIS.
- The outer caller derives a human-facing brief only from immutable synthetic
  task content; it does not give grader predicates or management capabilities
  to the model.
- Default fake result has zero external calls and zero actual cost.

## Acceptance commands

Run the exact W1-W5 commands in [../../AGENTS.md](../../AGENTS.md). The
evidence report must contain observed exit outcomes, image metrics, fake result,
real-VLM not-run status, cleanup, limitations, and the W6 boundary.

## Handoff boundary

W5 ends at bounded Vision-only capture, grounding, and fake-model wiring. W6
may later decide whether and how DOM/Vision observations are routed; W5 creates
no router or hybrid fallback.
