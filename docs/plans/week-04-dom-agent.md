# Week 04 plan — DOM Agent Foundation

## Objective

Build the smallest isolated DOM-only browser and Agent foundation that can act
through the five existing Sandbox pages while preserving the W3 database-fact
Grader as the sole success authority. The authoritative boundary is
[../agent-contract.md](../agent-contract.md).

## Planned outcomes

| Area | W4 outcome | Deliberate limit |
|---|---|---|
| Browser runtime | Non-root Playwright Worker in a separate container and network boundary | No generic browsing, host mounts, Docker socket, DB/API credential, upload/download, or browser code input |
| Observation | Strict bounded DOM/accessibility summary with ephemeral element references | No screenshot, pixels, OCR, VLM, selectors, trace, credentials, or full form values |
| Actions | Strict navigate/click/fill/select/read/scroll/wait/finish/fail union | No JavaScript, Playwright, CSS/XPath, shell, SQL, file path, or unbounded wait |
| Agent | Separate minimal ReAct loop with strict fake-model output and hard budgets | No planner, verifier, recovery, memory, routing, approval, or real model by default |
| Evaluation | W3 Reset/Seed outside the loop and W3 Grader after it | `finish` is never success; no Validation/Reporting tuning |
| Runtime | Compose isolation plus one deterministic fake-model smoke | No production deployment or external network use |
| Evidence | Exact versions, isolation, schemas, tests, regressions, costs, failures, and unrun real tasks | No success-rate, recovery, reliability, or ROI claim |

## Implementation sequence

1. Verify merged/tagged/green W3, synchronize `main`, branch, read governance,
   and freeze W4 instructions, exact paths, ADR, plan, and evidence template.
2. Define strict observation/action/session/result models and URL/data policy
   before Playwright execution code.
3. Implement per-session Browser/Page/Context ownership, origin interception,
   bounded DOM extraction, ephemeral references, typed action dispatch, and
   unconditional cleanup.
4. Implement the separate Browser Worker API without arbitrary browser options
   or debugging/execution surfaces.
5. Implement the strict model decision schema, deterministic fake model,
   Browser Worker client, and bounded no-planner ReAct loop.
6. Add deterministic tests for schema rejection, dangerous URLs, redirects,
   observation filtering/bounds, reference freshness, every action path,
   cleanup, invalid model output, repeated/no-progress actions, and all budgets.
7. Add isolated Compose networks, non-root/read-only service settings, pinned
   runtimes, a fake-model smoke test, CI jobs, and dependency update rules.
8. Update architecture, threats, evaluation protocol, README, and changelog to
   match only observed W4 implementation.
9. Run every W1-W4 lock, lint, format, type, test, build, Compose, migration,
   smoke, secret, and diff gate available on the host; fill evidence from
   observed outputs and clean Compose volumes.
10. Real-model acceptance was separately authorized for fixed OpenAI
    `gpt-5.6-terra`, prompt/config `w4-dom-react-openai/1.0`, tasks 001-005,
    zero retries, and revised aggregate caps of 125 calls, 500,000 input,
    100,000 output, 900 seconds, and USD 3.25. Run only through the profile-only
    Agent after offline/provider-readiness gates pass; otherwise record the
    credential or execution blocker without fabricating results.
11. Review the exact contract-owned diff, explicitly stage allowlisted files,
    create a local commit only if every available gate passes, and stop before
    W5.

## Fixed acceptance inputs

- W4 task IDs: `w3-joiner-001` through `w3-joiner-005`.
- W3 specs, facts, predicates, checksums, fixture version, reset semantics, and
  grader semantics remain unchanged.
- Each run begins after two byte-equivalent Reset/Seed results and at the HRIS
  route in a fresh Browser/Context/Page.
- An outer caller renders the task's existing human instructions and supplied
  immutable synthetic values into text; the loop receives no grader predicate
  or database/tool capability.
- Default tests and Compose use fake models with actual external cost zero.

## Acceptance commands

Run every app-local and Compose command in [../../AGENTS.md](../../AGENTS.md).
The evidence report records exact commands and observed results. An unavailable
executable or separately unauthorized real-model run is a limitation, not a
silently weakened or fabricated gate.

## Handoff boundary

W5 may later add screenshots, OCR/VLM, visual grounding, pixel actions, and a
Vision-only baseline after separate authorization and a new contract. W4 ends
without image capture/storage, visual fields, router scaffolding, or W5 code.
