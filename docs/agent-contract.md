# W5 agent contract — Vision Agent Foundation

## Authority, baseline, and sole objective

This contract translates the W5 row of [project-roadmap.md](project-roadmap.md)
and the user-authorized W5 brief into a bounded implementation agreement for
the branch week/05-vision.

The verified source baseline is main commit
c7a3e5a26477c1a92aa401b4f60f3eea333e1a02. HEAD, origin/main, and the
dereferenced annotated tag w04-dom-agent all resolved to that commit before
the branch was created. The contract-eligible worktree was empty. The
pre-existing untracked %SystemDrive%/ directory remains outside every read,
scan, diff, staging, and modification.

W5 has one outcome: retain all released W1-W4 behavior while adding bounded
in-memory screenshots, strict visual observations, opaque visual grounding,
and a separate Vision-only ReAct baseline. The unchanged W3 Grader remains the
only task-success authority.

The W4 historical rules in the prior contract are superseded for this branch
only. W1-W4 behavior and evidence remain regression inputs. Future roadmap
architecture is non-authorizing: W6 and later features remain prohibited.

## W5 scope

W5 may add only:

1. a versioned Browser Worker visual-session API that captures the current
   synthetic Sandbox Web viewport in bounded JPEG form;
2. a strict visual observation with screenshot metadata, a transient encoded
   image, and Worker-generated visual grounding candidates;
3. strict typed visual actions that refer only to a current opaque grounding
   reference and never contain a selector or arbitrary coordinate;
4. a separate non-root Vision Agent service with a deterministic fake vision
   model, bounded ReAct loop, and no DOM/accessibility observation field;
5. a fake-only Compose smoke, CI coverage, documentation, and observed W5
   evidence.

W5 preserves the W4 DOM session/action API and DOM Agent unchanged. It adds no
browser route outside the five released Sandbox paths, no database migration,
and no Sandbox API, PostgreSQL, Reset/Seed, or Grader capability to Browser
Worker, Vision Agent, or model.

## Explicit W5 non-goals

W5 does not add a DOM/Vision Router, DOM-quality heuristics, automatic
fallback, hybrid observation, planner DAG, verifier, recovery, checkpoint,
Temporal, fault injection, memory, retrieval, identity, RBAC, approval, audit
chain, production worker, monitoring, tracing, load test, external benchmark,
malicious-page suite, real enterprise integration, upload, download, general
proxy, arbitrary execution, or future-stage placeholder abstraction.

W5 does not add a model provider adapter, a model key, provider egress, a real
OCR service, image storage, a screenshot fixture, a trace, a raw OCR-text API,
or an image artifact in the repository. VLM/OCR is restricted to the typed
image input described below. A future real VLM adapter requires separate user
direction, exact disclosure, offline implementation, and fake-model gates
before any network call.

## Exact W5 file allowlist

Only the following paths may be created or modified in W5:

~~~text
AGENTS.md
README.md
CHANGELOG.md

.github/workflows/ci.yml

docs/agent-contract.md
docs/architecture.md
docs/threat-model.md
docs/evaluation-protocol.md
docs/adr/0005-w5-bounded-vision-worker-and-agent.md
docs/plans/week-05-vision.md
docs/evidence/week-05-report.md

deploy/compose/compose.yaml

apps/browser_worker/src/flowpilot_browser_worker/config.py
apps/browser_worker/src/flowpilot_browser_worker/schemas.py
apps/browser_worker/src/flowpilot_browser_worker/observation.py
apps/browser_worker/src/flowpilot_browser_worker/vision.py
apps/browser_worker/src/flowpilot_browser_worker/runtime.py
apps/browser_worker/src/flowpilot_browser_worker/main.py
apps/browser_worker/tests/conftest.py
apps/browser_worker/tests/test_api.py
apps/browser_worker/tests/test_observation.py
apps/browser_worker/tests/test_runtime.py
apps/browser_worker/tests/test_schemas.py
apps/browser_worker/tests/test_vision.py

apps/vision_agent/.dockerignore
apps/vision_agent/Dockerfile
apps/vision_agent/pyproject.toml
apps/vision_agent/uv.lock
apps/vision_agent/src/flowpilot_vision_agent/__init__.py
apps/vision_agent/src/flowpilot_vision_agent/schemas.py
apps/vision_agent/src/flowpilot_vision_agent/client.py
apps/vision_agent/src/flowpilot_vision_agent/model.py
apps/vision_agent/src/flowpilot_vision_agent/loop.py
apps/vision_agent/src/flowpilot_vision_agent/main.py
apps/vision_agent/tests/conftest.py
apps/vision_agent/tests/test_api.py
apps/vision_agent/tests/test_client.py
apps/vision_agent/tests/test_loop.py
apps/vision_agent/tests/test_model.py
apps/vision_agent/tests/test_schemas.py

tests/integration/Dockerfile
tests/integration/w5_vision_compose_smoke.py
~~~

Released W1-W4 source, Dockerfiles, locks, migrations, task facts, predicates,
checksums, manual baseline, W4 ADR, and W4 evidence are not W5 change targets.
The existing W4 files are regression inputs. Any additional path must be added
to this contract before it changes. Any requested path that broadens W5 beyond
this contract requires user direction before it is added.

## Visual Browser Worker contract

The existing W4 DOM API stays versioned and unchanged. W5 adds separate narrow
visual-session routes:

- POST /api/browser/vision-sessions accepts only w5-vision-session/1.0 and the
  fixed initial path /hris;
- POST /api/browser/vision-sessions/{session_id}/actions accepts only one
  discriminated w5-vision-action/1.0 action;
- DELETE /api/browser/vision-sessions/{session_id} idempotently closes the
  current Browser, Context, and Page.

The Worker still creates a fresh Playwright process, Browser Context, and Page
per task. It uses the released exact local Sandbox origin policy, request
interception, final-navigation validation, service-worker blocking,
download rejection, resource limits, and unconditional terminal/startup/
shutdown cleanup. The visual routes have no browser-option, JavaScript,
selector, XPath, CSS, shell, SQL, file, URL, Cookie, Local Storage, upload,
download, proxy, credential, or raw binary endpoint.

Screenshot capture is permitted only after the Worker verifies that the current
top-level URL is the configured Sandbox origin and one of the five business
paths. Request interception blocks external subresources and redirect escape.
The Worker captures the page viewport only, never host desktop or browser UI.
No full-page, browser-chrome, cross-origin, other-session, or host image can
be requested.

The immutable W5 capture envelope is:

| Limit | Value |
|---|---:|
| Image MIME and encoding | image/jpeg only |
| Viewport | 960 × 540 CSS pixels |
| Maximum pixels per image | 518,400 |
| JPEG quality | fixed Worker value 60 |
| Maximum image bytes | 184,320 |
| Maximum capture attempts per session | 24 |
| Maximum capture duration per attempt | 3,000 ms |
| Maximum total image bytes per session | 4,423,680 |
| Maximum total capture duration per session | 72,000 ms |

Capture count includes a failed or oversized capture attempt, so an error path
cannot bypass the cap. The Worker rejects an oversized image or exhausted
visual budget, closes the session where it cannot make another compliant
observation, and returns only a bounded error category/message. Environment
settings may reduce these limits but cannot increase them.

## Visual observation, OCR/VLM input, and lifecycle

Visual observation schema w5-vision-observation/1.0 contains only:

- Worker-generated session_id, observation_id, and screenshot_ref;
- JPEG MIME type, encoded current image, pixel width/height, byte count, and
  capture duration;
- bounded Worker-generated visual grounding candidates, each containing only
  grounding_ref, an in-viewport integer rectangle, and allowed action kinds;
- sanitized last-action outcome, a truncation flag, and no DOM semantic field.

The encoded image is the single transient VLM/OCR input. It is passed directly
from the current observation to the Vision Agent's model interface; it is not
written to a file, log, Task Spec, test fixture, database, cache, long-term
store, or action history. There is no image URL, file path, arbitrary MIME
type, raw OCR text endpoint, or model-provided image input.

OCR is not a trusted tool or Worker API. Any text a vision model infers from
the JPEG is untrusted page data, cannot change system instructions, and is
discarded with the model call. The fake model makes no OCR-capability claim.
The Vision Agent model context contains the human task brief, one current
bounded visual observation, generic bounded prior action summaries, and
remaining budgets. It receives no DOM, accessibility tree, page title, current
URL, selector, input value, Cookie, Local Storage, Reset/Seed, Grader, database
fact, filesystem, shell, SQL, JavaScript, or browser object.

Every visual observation creates a fresh screenshot_ref and grounding table.
The Worker keeps only current grounding handles in memory. A success, failed
action, new observation, timeout, terminal action, explicit deletion, startup
failure, or service shutdown invalidates references and clears temporary
visual data. Unknown, forged, cross-session, stale-observation, and
stale-screenshot references fail before Playwright execution.

## Grounding and typed visual action contract

A visual grounding rectangle is Worker-generated metadata that identifies a
visible, nonzero, in-viewport interactive element in the current viewport.
Coordinates are output-only, integer CSS-pixel rectangles clipped to the
960 × 540 image. They help the model associate screenshot content with an
opaque grounding_ref; they are not accepted back as coordinates and do not
reveal a selector, locator, element name, role, DOM text, or input value.

For click, fill, select, read, and scroll, model output must carry the current
observation_id, screenshot_ref, and grounding_ref. The Worker resolves that
current opaque reference to its internal locator, verifies that the chosen
action is allowed, and then uses the existing typed browser operation. A
visual action can never contain x/y, bounding box, selector, locator recipe,
JavaScript, Playwright source, or arbitrary URL. Navigate remains constrained
to the five fixed local paths; wait remains bounded; fill uses the released
synthetic-data and credential-rejection policy; select is checked against the
Worker's current internal option list; finish and fail close the session.

W5 action and result schemas are w5-vision-action/1.0 and
w5-vision-action-result/1.0. Unknown fields, action kinds, output types,
coordinates, code, stale references, unsupported paths, and oversized strings
are rejected strictly. Result messages are generic and do not return a DOM
label or OCR text.

## Vision Agent, fake model, and budgets

apps/vision_agent is a separate Python 3.13 FastAPI service. It has only a
credential-free local Browser Worker URL and only joins the internal
agent-worker network. It has no Sandbox/API/DB/Arena/Grader client, credential,
provider egress, repository mount, Docker socket, host mount, or production
control responsibility.

Its run/result schemas are w5-vision-agent-run/1.0 and
w5-vision-agent-result/1.0. Its strict model decision schema is
w5-vision-model-decision/1.0. Default and only W5 runtime model is
deterministic-fake-vision. It receives the current JPEG data in memory and can
return only the typed visual action envelope. It has no tool calls. The fake
has zero external calls and zero actual cost.

The deterministic fake also has one test-only `complete_joiner` scenario for
the fixed Development surface. It accepts no task database fact, Task Spec,
expected-state object, or Grader predicate: the trusted caller must place the
required synthetic identifiers in the human-facing brief. The scenario parses
only that fixed supplied-values grammar, validates the current JPEG envelope,
and chooses only current Worker-generated Groundings by their output-only
geometry and allowed action kinds. Its route and form sequence is deliberately
deterministic test policy, not OCR, VLM inference, a DOM fallback, or a
general-purpose planner. It never treats page image/text instructions as
policy and it does not use the task ID as a fixture-value lookup key.

The default per-run hard limits are 24 steps, 24 model calls, 24 images,
4,423,680 total image bytes, 12,441,600 total image pixels, 72,000 ms total
capture duration, 100,000 input tokens, 20,000 output tokens, 300 seconds,
and zero micro-USD cost. Repetition and no-progress limits are also bounded.
Model-reported input/output token and cost values are accumulated and compared
before/after every call using monotonic time. Cap exhaustion fails safely and
closes the Browser session. Action summaries and results contain only bounded
metadata plus numeric image/token/cost/latency aggregates, never pixels, OCR,
or form/page content.

No provider or paid model is authorized by this contract. Before a real VLM or
OCR-capable model is even called, stop and obtain separate explicit user
authorization after disclosing the provider, exact model, endpoint,
prompt/config version, image MIME/max resolution/max image count, exact task
IDs, call/input/output/image/time/cost caps, and retry count. The W4 ZHIPU key
and W4 authorization do not authorize W5 VLM use.

## Evaluation and evidence rules

W5 Development candidates are only w3-joiner-001 through w3-joiner-005.
Existing W2 pages provide the synthetic screenshot surface; W5 does not alter
them or their W3 facts. Development may inform implementation. Validation may
not be repeatedly tuned against and Reporting remains frozen for final
reporting only. If a later W5 evaluation cannot establish visual capability on
this fixed set, propose a minimal new visual task separately rather than
changing a released task.

The outer trusted caller alone loads immutable task metadata, executes two
equal Reset/Seed calls, renders the human-facing brief, invokes Vision Agent,
and independently invokes the unchanged W3 Grader after cleanup. The model and
Worker cannot call, receive, or substitute for Reset/Seed or Grader. Finish is
finished_ungraded, never success.

W5 fake acceptance has two separately Reset/Seed-controlled subruns through a
real isolated Chromium visual session. The first performs a grounded read then
finishes, and must independently retain the untouched 30/100, `passed=false`
grade. The second uses the bounded `complete_joiner` test scenario and must
finish ungraded before the unchanged W3 Grader independently returns exactly
100/100 and `passed=true`. Both record zero external calls/cost. The second is
deterministic fake behavioral evidence for the typed visual circuit only; it
is not a real VLM/OCR call, a Vision-only success-rate observation, or proof
of visual understanding. The evidence report must separately record fake
results, real VLM results, unrun real VLM items, image/call/token/cost/latency
metrics, failures, cleanup, all available gates, limitations, and the W6
boundary.

## Git and handoff rules

Work only on week/05-vision. Do not push, create a PR, merge, tag, force-push,
or call a real model without separate explicit user authorization. Do not
stage broadly; stage only the final exact W5 allowlist after every locally
available gate passes and evidence matches observed facts. Never inspect,
copy, modify, stage, scan, ignore, or delete %SystemDrive%/, and never access
any code_review_agent repository.

W5 stops after the Vision-only foundation. W6 routing or hybrid behavior is
explicitly out of scope.
