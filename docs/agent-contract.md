# W6 agent contract - Hybrid Router

## Authority, baseline, and sole objective

This contract translates the W6 row of project-roadmap.md and the
user-authorized W6 brief into a bounded implementation agreement for
week/06-hybrid-router.

The verified source baseline is main commit
5981bf9f2d419854f51e0ced826efb3ac3864953. HEAD, origin/main, and the
dereferenced annotated tag w05-vision all resolved to that commit before this
branch was created. The contract-eligible worktree was clean. The pre-existing
untracked %SystemDrive%/ directory remains outside every read, scan, diff,
staging, and modification.

W6 has one outcome: retain all released W1-W5 behavior while adding a bounded,
deterministic DOM/Vision Router, deterministic local observation compression,
strict cross-modality action validation, and an independent fake-only Hybrid
Agent baseline. The unchanged W3 Grader remains the only task-success
authority.

The W5 branch rules are superseded only on this W6 branch. W1-W5 APIs,
behavior, security controls, and evidence remain regression inputs. W7 and
later roadmap architecture is non-authorizing and prohibited.

## W6 scope

W6 may add only:

1. a Browser Worker Hybrid session API that creates exactly one fresh
   Playwright Browser, Context, and Page for a task and exposes one selected
   current modality at a time;
2. strict versioned hybrid session, observation request/response, route
   decision, action envelope, action result, and run/result schemas;
3. Worker-derived bounded DOM structural quality signals without page text,
   form values, arbitrary URLs, or model output;
4. deterministic, pure-local DOM observation compression with fixed caps;
5. a separate non-root Hybrid Agent service containing a small deterministic
   per-task router and deterministic fake model; and
6. fake-only Compose/CI acceptance, documentation, locks, tests, and observed
   W6 evidence.

W4 DOM sessions/actions and the DOM Agent remain unchanged. W5 visual
sessions/actions and the Vision Agent remain unchanged. A Hybrid task never
joins a W4 session to a W5 session and never exposes both full DOM and image
data to one model call.

## Explicit W6 non-goals

W6 does not add a planner DAG, tool matching, verifier, new task template,
checkpoint, recovery, Temporal, fault injection, partial replanning, memory,
retrieval, cache, short- or long-term context, cross-task history, learned
routing, online tuning, database statistics, identity, RBAC, approval, audit
chain, production worker, monitoring, tracing, load test, external benchmark,
malicious-page suite, real enterprise integration, real model, provider
adapter, model credential, provider egress, database migration, Sandbox
business change, upload, download, generic proxy, arbitrary execution, or
future-stage placeholder abstraction.

W6 does not modify W2/W3 migrations, W3 Task Specs, expected state, grader
predicates, canonical checksums, manual-baseline evidence, or Sandbox pages.
It does not write raw DOM, screenshots, OCR, page text, form values, Cookies,
Local Storage, model output, endpoints, credentials, tokens, or machine paths
to a repository, database, log, fixture, trace, or long-term store.

## Exact W6 file allowlist

Only these paths may be created or modified in W6:

~~~text
AGENTS.md
README.md
CHANGELOG.md

.github/workflows/ci.yml

docs/agent-contract.md
docs/architecture.md
docs/threat-model.md
docs/evaluation-protocol.md
docs/adr/0006-w6-bounded-hybrid-router.md
docs/plans/week-06-hybrid-router.md
docs/evidence/week-06-report.md

deploy/compose/compose.yaml

apps/browser_worker/src/flowpilot_browser_worker/config.py
apps/browser_worker/src/flowpilot_browser_worker/hybrid.py
apps/browser_worker/src/flowpilot_browser_worker/main.py
apps/browser_worker/src/flowpilot_browser_worker/runtime.py
apps/browser_worker/src/flowpilot_browser_worker/schemas.py
apps/browser_worker/tests/test_api.py
apps/browser_worker/tests/test_hybrid.py
apps/browser_worker/tests/test_schemas.py

apps/hybrid_agent/.dockerignore
apps/hybrid_agent/Dockerfile
apps/hybrid_agent/pyproject.toml
apps/hybrid_agent/uv.lock
apps/hybrid_agent/src/flowpilot_hybrid_agent/__init__.py
apps/hybrid_agent/src/flowpilot_hybrid_agent/client.py
apps/hybrid_agent/src/flowpilot_hybrid_agent/compressor.py
apps/hybrid_agent/src/flowpilot_hybrid_agent/loop.py
apps/hybrid_agent/src/flowpilot_hybrid_agent/main.py
apps/hybrid_agent/src/flowpilot_hybrid_agent/model.py
apps/hybrid_agent/src/flowpilot_hybrid_agent/router.py
apps/hybrid_agent/src/flowpilot_hybrid_agent/schemas.py
apps/hybrid_agent/tests/conftest.py
apps/hybrid_agent/tests/test_api.py
apps/hybrid_agent/tests/test_client.py
apps/hybrid_agent/tests/test_compressor.py
apps/hybrid_agent/tests/test_loop.py
apps/hybrid_agent/tests/test_model.py
apps/hybrid_agent/tests/test_router.py
apps/hybrid_agent/tests/test_schemas.py

tests/integration/Dockerfile
tests/integration/w6_hybrid_compose_smoke.py
~~~

Released W1-W5 source outside this list, all W2/W3 migrations/task/grader
inputs, all Sandbox business code, DOM Agent, Vision Agent, existing locks, and
all W4/W5 evidence/ADR/plan files are regression inputs and not W6 targets.
Any additional path must be added to this contract before it changes. Any path
that broadens W6 requires user direction before it is added.

## Hybrid Browser Worker contract

The Worker adds only these routes:

- POST /api/browser/hybrid-sessions accepts w6-hybrid-session/1.0 and fixed
  initial path /hris;
- POST /api/browser/hybrid-sessions/{session_id}/observations accepts one
  strict w6-hybrid-observation-request/1.0 modality request;
- POST /api/browser/hybrid-sessions/{session_id}/actions accepts one
  discriminated w6-hybrid-action-envelope/1.0 action;
- DELETE /api/browser/hybrid-sessions/{session_id} idempotently closes the
  one Browser, Context, Page, Playwright process, and all task-local maps.

The initial Hybrid observation is DOM at the fixed W5 viewport so later visual
capture remains bounded. A fresh observation request returns exactly one
selected modality: a W4-shaped DOM observation or a W5-shaped visual
observation, never both. Each response includes a bounded route signal only:
DOM structural state, effective interactive-element count, serialized DOM
observation byte count, and a sanitized safe last-action error category. It
contains no semantic node text, name, form value, page title, URL, selector,
image, model output, or arbitrary route instruction.

The Worker retains W4 local-origin policy, request interception, final URL
validation, blocked service workers/downloads, bounded waits/fills/actions,
and unconditional cleanup. It creates one Browser/Context/Page per Hybrid
task, with W5's fixed 960 x 540 CSS-pixel viewport, and never creates a second
session to change modality.

The Worker enforces a current observation generation and clears every DOM and
visual reference map before building any new observation. Every action
envelope carries the current session_id and generation; the Worker compares
both with the path-owned session before considering modality or action fields.
A new observation, explicit modality switch, successful action, failed action,
timeout, terminal action, deletion, startup failure, cancellation, or shutdown
invalidates all old DOM
element_ref, visual screenshot_ref, and grounding_ref values. A W6 action
envelope declares modality; element actions additionally carry the selected
modality's current opaque references. The Worker checks session, generation,
modality, allowed action, and current reference lifecycle before Playwright
execution. Cross-mode, forged, stale, unknown, coordinate,
rectangle, selector, XPath, code, path, URL, JavaScript, shell, SQL, Cookie,
Local Storage, upload, download, and browser-option input is rejected.

W5 visual JPEG limits remain unchanged: image/jpeg only, 960 x 540 maximum,
518,400 pixels, quality 60, 184,320 bytes/image, 24 capture attempts/session,
3,000 ms/capture, 4,423,680 total image bytes, and 72,000 total capture ms.
Hybrid switching never resets those counters. W6 additionally caps Hybrid
observations and total Worker-produced DOM observation bytes. A limit breach
returns a bounded category and closes the session where a compliant current
observation cannot be produced.

## Deterministic routing and compression contract

The only trusted route categories are standard and visual_recovery. They are
strict run-request values consumed by the Router, not page/model text and not a
task-spec or fixture lookup. The Router version is w6-router/1.0 and has no
cross-task state.

Default routing starts in DOM. The total schema cap is two switches, while the
shipped W6 one-way policy performs at most one DOM-to-Vision switch. It selects
Vision only when all remaining budgets allow a visual observation and one of
these fixed conditions holds:

1. the current DOM quality signal is structurally empty or truncated;
2. the current safe DOM action outcome is a stale/unknown reference,
   disallowed-action, browser, or policy category; or
3. the trusted visual_recovery category has completed one successful bounded
   DOM read probe action.

Otherwise it retains DOM. W6 does not implement Vision-to-DOM recovery,
learned policy, success-rate history, online tuning, cache, or retry policy.
It refuses a requested switch when the switch limit, remaining image, DOM,
step, call, token, cost, or monotonic-time budget cannot accommodate it. For
the fake-only W6 runtime, the conservative switch reservation is one complete
W5 image envelope (184,320 bytes, 518,400 pixels, and 3,000 capture ms), one
32-input/16-output-token fake call, and more than three seconds remaining.
Reason codes are a closed strict enum and are reported as safe metadata.

Before a DOM model call, Hybrid Agent compresses only the current DOM
observation using deterministic DOM order and fixed JSON serialization:
32 semantic nodes, 40 interactive elements, 12 prior action summaries,
12,288 bytes per compressed DOM observation, and 2,048 bytes of summaries.
It removes trailing semantic nodes before interactive elements, records
truncation and exact serialized bytes, and never uses an LLM or stores input.
The selected visual path preserves the W5 bounded JPEG and current grounding
envelope. The model receives exactly one compressed DOM observation or one
current visual observation per call, never both.

## Hybrid Agent, models, and budgets

apps/hybrid_agent is a separate Python 3.13 FastAPI service. It resolves only
the credential-free local Browser Worker URL and joins only the dedicated
internal hybrid-worker network shared with Browser Worker. DOM Agent and
Vision Agent remain on their released agent-worker network. Hybrid Agent has
no Sandbox/API/Arena/Grader/DB client or network, no credential, repository
mount, Docker socket, filesystem persistence, shell,
SQL, JavaScript, browser object, provider egress, model key, or production
control responsibility.

Its strict schemas are w6-hybrid-agent-run/1.0,
w6-hybrid-agent-result/1.0, w6-router-decision/1.0,
w6-compressed-observation/1.0, and w6-hybrid-model-decision/1.0. The default
and only W6 runtime model is deterministic-fake-hybrid with zero external
calls and zero actual cost. The test-only DOM-to-Vision completion scenario
parses only the caller-rendered supplied-values brief, chooses current DOM
element refs or current visual groundings by allowed action/geometry, and has
no Task Spec, expected-state, grader predicate, database, OCR/VLM, DOM
fallback during a visual turn, or fixture map.

Default total hard limits are 24 steps, 24 model calls, two switches, two
repeated actions, three no-progress events, 300 seconds, 24 DOM observations,
262,144 raw DOM bytes, 147,456 compressed DOM bytes, 24 images, 4,423,680
image bytes, 12,441,600 image pixels, 72,000 capture ms, 100,000 input tokens,
20,000 output tokens, and zero micro-USD cost. Counters are monotonic across
all modalities and no switch can reset, hide, or bypass them. Result/action
summaries expose only safe numeric metrics, action type/outcome, route reason,
and termination state. Finish is finished_ungraded and never includes pass,
score, success, raw screenshot, DOM, or page content.

## Evaluation, Compose, and evidence

W6 Development candidates are w3-joiner-001 through w3-joiner-005. The outer
trusted caller alone reads immutable task metadata, Reset/Seeds twice, renders
the human-facing supplied-values brief, calls Hybrid Agent, and independently
calls the unchanged W3 Grader after cleanup. It must not give grader predicates
to the model. A fake completion is only fake circuit and isolation evidence.

W4 fake DOM smoke must continue to grade untouched state at 30/100,
passed=false. W5 fake Vision smoke must continue to show untouched 30/100,
passed=false and fresh deterministic completion 100/100, passed=true. W6 adds
a fake Hybrid smoke on the same Development task and equal Reset/Seed
conditions. Its first immediate-finish run must independently grade 30/100,
passed=false. Its fresh deterministic completion must perform an actual
DOM-to-Vision Worker modality switch, exercise current-reference validation,
compression cap accounting, and cleanup, return finished_ungraded, then be
independently graded exactly 100/100, passed=true. All fake results have zero
external calls and cost and make no real hybrid, DOM, Vision, OCR, or VLM
capability claim.

Default Compose and CI add a non-root, read-only, cap-dropped,
no-new-privileges Hybrid Agent with tmpfs, pids limit, no host port, no
credential, no provider egress, and only dedicated hybrid-worker attachment. The
profile-only hybrid acceptance caller has management networks solely for
Reset/Seed and independent grading; it is not an Agent tool and is not in the
normal profile.

## Git and handoff rules

Work only on week/06-hybrid-router. Do not push, create a PR, merge, tag,
force-push, or call a real model without separate explicit user authorization.
Do not stage broadly; stage only the final exact W6 allowlist after every
locally available gate passes and evidence matches observed facts. Never
inspect, copy, modify, stage, scan, ignore, or delete %SystemDrive%/, and
never access any code_review_agent repository.

W6 stops after bounded routing, compression, and action validation. W7
planning, verifier, and task-DAG work remain explicitly out of scope.
