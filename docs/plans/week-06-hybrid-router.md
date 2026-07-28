# Week 06 plan - Hybrid Router

## Objective

Add the smallest safe Hybrid baseline over released W1-W5: one Worker-owned
Hybrid session, deterministic DOM-to-Vision routing, deterministic DOM
compression, strict current-mode action envelopes, and a separate fake-only
Hybrid Agent. W3 Grader remains the only success authority. The complete
boundary is docs/agent-contract.md.

## Planned outcomes

| Area | W6 outcome | Deliberate limit |
|---|---|---|
| Browser Worker | One Hybrid Browser/Context/Page with selected current DOM or Vision observation | No joined W4/W5 sessions, selectors, coordinates, storage, or external origin |
| Route signals | Bounded structural counts, truncation, bytes, and safe error category | No page text, form values, URL, model output, or history |
| Router | Versioned deterministic DOM-first policy with closed reason codes | No learning, retry/recovery, cache, or Vision-to-DOM fallback |
| Compression | Stable local DOM serialization with fixed node/element/history/byte caps | No LLM summary or persistence |
| Hybrid Agent | Separate fake-only bounded loop | No Sandbox/Arena/DB/Grader/provider access |
| Evaluation | W4/W5 regression and W6 fake DOM-to-Vision smoke | Fake circuit evidence is not a capability claim |

## Implementation sequence

1. Verify released W5 baseline and create week/06-hybrid-router.
2. Freeze W6 contract, exact allowlist, ADR, plan, threat/evaluation deltas,
   evidence skeleton, README, changelog, and branch instructions.
3. Define strict Worker Hybrid schemas and implement session/generation-bound
   one-session observation/action lifecycle with cross-mode invalidation.
4. Add deterministic Router, compressor, fake model, bounded loop, API, tests,
   and locked Hybrid Agent image.
5. Add dedicated Hybrid-to-Worker Compose/CI network isolation and a
   profile-only W6 fake acceptance caller while retaining W4/W5 profiles.
6. Cover schema rejection, quality signal bounds, route reasons/switch caps,
   compression caps, mode/reference validation, W5 image limits, action/error
   cleanup, all total budgets, and no simultaneous modality model input.
7. Run W1-W6 quality, Compose, migration, W4/W5/W6 smoke, secret, exact
   allowlist, diff, staged/unstaged, and cleanup gates. Record unavailable
   tooling without weakening the gate.
8. Do not call a real model. Record real DOM/Vision/Hybrid model rows as not
   run with zero W6 calls/cost unless separately authorized.

## Fixed acceptance inputs

- Development candidates remain w3-joiner-001 through w3-joiner-005.
- W3 facts, checksums, Reset/Seed, Grader, and human-brief rules remain
  unchanged.
- W6 smoke uses w3-joiner-001, equal Reset/Seed pairs, and a fresh Hybrid
  Browser/Context/Page per subrun.
- The immediate-finish subrun must independently grade 30/100 and false.
- The fresh completion subrun uses trusted visual_recovery only as a finite
  Router category; it must execute a real Worker DOM-to-Vision switch, end
  finished_ungraded, and independently grade 100/100 and true.
- All fakes have zero external calls and actual cost.

## Handoff boundary

W6 stops after bounded Hybrid routing, compression, and strict current-mode
actions. W7 planning, tool matching, verifier, and new task modeling are not
started.
