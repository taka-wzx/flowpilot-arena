# W6 threat model - Hybrid Router

## Scope and assets

W6 protects released W1-W5 source and locks; immutable W3 Task Specs/checksums;
synthetic task state and deterministic grades; Browser Worker integrity; current
DOM and visual observations; opaque DOM/visual references; deterministic route
decisions; compressed DOM output; and Hybrid Agent budget/termination
integrity.

W6 adds no persistent asset. A current DOM observation, current JPEG, route
signal, compression result, and action summary are task-local transient memory
only. Page content, screenshots, OCR, DOM text, and image instructions remain
untrusted data. Default Compose/CI has no model/OCR/VLM network call.

## Trust boundaries

~~~mermaid
flowchart LR
    Page["Untrusted Sandbox page, DOM, image, and text"] --> Worker["Strict Browser Worker"]
    Worker --> Router["Hybrid Router<br/>safe bounded inputs only"]
    Router --> Model["Untrusted fake model output"]
    Model --> Agent["Strict Hybrid Agent loop"]
    Agent --> Worker
    Caller["Trusted acceptance caller"] --> Arena["W3 Reset/Seed + Grader"]
    Caller --> Agent
    Arena --> DB["Synthetic PostgreSQL"]
~~~

The Router does not consume page text or model output. The model gets exactly
one selected modality. Worker validates references again before Playwright.
Acceptance orchestration is trusted only for Reset/Seed, brief rendering, and
independent grade, never as an Agent tool.

## Threats and W6 controls

| Threat | W6 control | Remaining limitation |
|---|---|---|
| Two-session state splice | One Hybrid session owns one Browser/Context/Page across both modalities | No recovery after browser failure in W6 |
| Stale cross-mode action | Every envelope binds session and generation; clear both DOM/visual maps before every observation and action result; validate mode/observation/current refs | A page race can still fail safely |
| Dual-modal model context | Selected DOM compression or selected visual observation only | Human brief remains an allowed immutable task input |
| Page/model-directed routing | Router input schema has only closed category, counts, flags, safe error, budgets | W14 measures malicious prompt resistance |
| DOM quality leaks page data | Worker emits counts, byte size, truncation, and safe category only | DOM model turn legitimately receives bounded DOM content |
| Compression bypass/resource exhaustion | Fixed deterministic node/element/history/byte limits, monotonic totals, strict schema | W12 covers load/concurrency behavior |
| Visual budget reset by switch | W5 count/bytes/pixels/capture timers stay on one session | No real VLM evaluation is included |
| Arbitrary browser control | Strict typed current-mode actions; selectors, coordinates, code, paths, URLs, and stale refs rejected | Synthetic pages only |
| Router learning/history | Router state is per-run memory and discarded; no DB/cache/statistics | No measured success-rate optimization |
| Hybrid Agent privilege expansion | Dedicated internal hybrid-worker only; no peer Agent/Sandbox/Arena/DB/Grader/filesystem/shell/provider network | Container sandbox is development hardening, not formal proof |
| Model self-declared pass | Result lacks pass/score/success; W3 Grade remains independent | Fixed Development tasks do not establish reliability |
| Raw data persistence | No schemas/logs/fixtures/store for JPEG/DOM/OCR/page content; numeric safe evidence only | Process memory is not forensic zeroization |

## Deterministic control rules

- Session, generation, observation, screenshot, grounding, and element IDs are runtime
  isolation tokens only. They are discarded on every invalidation event.
- Router category is a strict caller input that never reaches the model as a
  route instruction and is not looked up from a task or fixture map.
- Router reason codes, action summaries, budgets, compression counters, and
  timestamps are bounded safe metadata. Time uses monotonic clocks.
- The fake completion parses only supplied synthetic values in the human brief.
  It has no Task Spec/expected state/Grader/database input and does not treat
  page text/image instruction as policy.
- Worker navigation stays on fixed Sandbox Web paths. Browser writes occur only
  through Worker-validated typed UI actions.
- Reset/Seed and grading stay outside Worker and every Agent service.

## Deferred threats

W7 planner/verifier risks; W8 checkpoint/recovery/fault-injection risks; W9
memory/retrieval risks; W10 identity/RBAC; W11 approval/audit; W12 production
worker/monitoring/load; W14 malicious-page evaluation; and W15 external
Reporting evaluation remain deferred.
