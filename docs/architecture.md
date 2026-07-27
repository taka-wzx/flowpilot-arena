# Architecture

## W5 current-state architecture

W5 preserves the released W1 stateless control paths, W2 five-module Sandbox,
W3 deterministic Arena, and W4 DOM Worker/Agent behavior. It adds two distinct
browser observation paths in the same isolated Browser Worker:

- the unchanged W4 DOM-session API for the DOM Agent;
- a new W5 visual-session API for the Vision-only Agent.

The paths are deliberately not routed, merged, or automatically selected in
W5. Neither Agent nor the Worker has a database credential or may declare task
success.

~~~mermaid
flowchart LR
    Caller["Trusted acceptance caller<br/>Reset/Seed · brief · grade"] --> Arena["W3 Arena API"]
    Caller --> DomAgent["W4 DOM Agent<br/>strict bounded ReAct"]
    Caller --> VisionAgent["W5 Vision Agent<br/>strict bounded fake ReAct"]
    DomAgent --> Worker["Isolated Browser Worker<br/>DOM sessions + visual sessions"]
    VisionAgent --> Worker
    Worker --> Web["sandbox_web<br/>five business pages"]
    Web --> Business["W2 business APIs"]
    Arena --> Specs["10 immutable W3 specs"]
    Arena --> Grader["W3 DB-fact Grader"]
    Business --> DB["PostgreSQL"]
    Grader --> DB

    subgraph AgentNetwork["internal agent-worker network"]
        DomAgent
        VisionAgent
        Worker
    end
    subgraph BrowserNetwork["internal browser-sandbox network"]
        Worker
        Web
    end
    subgraph SandboxNetwork["sandbox-backend network"]
        Web
        Business
        Arena
        Grader
        DB
    end
~~~

The one-off W4 acceptance-smoke profile remains the trusted caller for the
released DOM regression. W5 adds a separate fake-only Vision acceptance caller.
Both may reach management APIs and their respective Agent service but contain
no Browser driver, database driver, model key, or general execution API.
Normal Compose starts neither profile.

| Boundary | Responsibility | Deliberately excluded |
|---|---|---|
| Control API/web | Preserve W1 health/static behavior | Agent, browser, database change |
| Sandbox API/web/PostgreSQL | Preserve W2 pages and W3 facts | Worker/Agent embedding |
| Browser Worker DOM sessions | Released W4 DOM extraction and typed actions | Screenshot field or visual fallback in W4 schema |
| Browser Worker visual sessions | Fixed synthetic viewport JPEG, visual observation, grounding validation, cleanup | Image storage/path/URL, arbitrary pixels/selectors/code, provider access |
| DOM Agent | Released strict DOM ReAct loop | Vision input, router, planner, verifier |
| Vision Agent | Visual-only strict fake ReAct loop and numeric budgets | DOM/AX input, Sandbox/Arena/Grader client, real provider by default |
| Acceptance caller | Reset/Seed twice, brief, Agent invocation, independent grade | Model tool or success override |

## Browser Worker process and network boundary

The Browser Worker remains a non-root FastAPI container with read-only root
filesystem, dropped capabilities, no-new-privileges, bounded pids/shared
memory/tmpfs, no bind mount, no Docker socket, no database credential, and no
route to Sandbox API/PostgreSQL. It connects only to:

- browser-sandbox with sandbox-web;
- agent-worker with DOM Agent and Vision Agent.

Those Worker networks are Docker-internal. The configured Sandbox origin is
exactly local Sandbox Web and navigation permits only /hris, /itsm, /iam,
/assets, and /mail. Request interception permits same-origin page resources and
blocks external requests/redirect escape. URL credentials, non-HTTP schemes,
query/fragment proxying, unknown hosts/ports, and direct API paths are
rejected.

Every DOM or visual session launches a separate Playwright process, Browser
Context, and Page. Finish, fail/escalate, timeout, cap exhaustion, explicit
delete, startup error, cancellation, and service shutdown close Page, Context,
Browser, and Playwright handles.

## Released DOM observation path

The W4 DOM contract stays unchanged:

- schema w4-dom-observation/1.0;
- semantic DOM/accessibility nodes and opaque element_ref values;
- schema w4-dom-action/1.0 and strict typed action result;
- no screenshot, OCR, image, visual feature, coordinate, or image storage
  field.

The DOM Agent remains a separate service and its W4 fake smoke stays a required
regression. W5 does not expose its DOM observations to Vision Agent.

## W5 visual observation path

Visual sessions use separate routes and w5-vision-observation/1.0. A visual
observation holds one current in-memory image only:

| Field class | W5 contents | Exclusions |
|---|---|---|
| Identity | Worker session, observation, screenshot references | Task fact, URL, page title |
| Image metadata | image/jpeg, 960 × 540, byte count, capture duration | File path, URL, other MIME, full page/browser UI |
| Image data | One bounded encoded current JPEG | Persistent store, fixture, trace, log |
| Grounding | Opaque ref, output-only clipped rectangle, allowed action kinds | DOM name/role/text, selector, locator recipe, element_ref |
| Result state | Sanitized generic last-action/error state, truncation | OCR text, input values, Cookie, Local Storage |

The fixed capture envelope is one 960 × 540 JPEG at quality 60, no more than
184,320 bytes and 3,000 ms per attempt. Each session permits at most 24
attempts, 4,423,680 image bytes, and 72,000 capture milliseconds. A cap failure
cannot fall back to DOM or another image source; it fails safely and cleanup
runs.

The Worker takes a viewport screenshot only after validating the current
top-level Sandbox route and retaining request interception. Playwright viewport
screenshots exclude browser chrome and host desktop by construction. No visual
route offers a raw-image fetch, arbitrary image target, file path, or screenshot
option.

## Grounding and visual actions

The Worker internally finds visible interactive elements and emits only
current-screen visual grounding candidates. A rectangle is an output-only,
integer CSS-pixel, nonzero, in-viewport area clipped to the fixed image. It
helps a model associate what it sees with an opaque grounding_ref.

The visual model must return current observation_id, screenshot_ref, and
grounding_ref for click, fill, select, read, and scroll. The Worker verifies
all three, checks action permission, and then resolves its internal locator.
The model can never return an x/y coordinate, a rectangle, selector, locator,
browser source, JavaScript, or arbitrary URL. New observations replace the
entire screenshot/grounding table; unknown and stale values fail before
Playwright execution.

Schema w5-vision-action/1.0 is a strict discriminated union for navigate,
grounding-bound click/fill/select/read/scroll, bounded wait, finish, and fail.
Schema w5-vision-action-result/1.0 returns a new visual observation only for a
non-terminal result. Result text is generic so it cannot leak DOM names or OCR
content.

## Vision Agent and restricted VLM/OCR input

apps/vision_agent is a separate non-root/read-only Python 3.13 FastAPI
container. It joins agent-worker only, can resolve Browser Worker only, and has
no Sandbox Web/API/PostgreSQL/Arena/Grader route, credential, Docker socket,
repository mount, or provider egress.

The model context has a human-facing task brief, the one current visual
observation, generic bounded prior action summaries, and remaining budgets. It
does not have a DOM/accessibility tree, URL/title, selector, page text, input
value, Cookie, Local Storage, or service/tool object. The encoded JPEG is the
only OCR/VLM input. Any visual text or instruction inference is untrusted data
and cannot create tools or override the strict action schema.

The only W5 runtime model is deterministic-fake-vision. It has no network and
zero external cost. Its default scenario demonstrates one typed
image/grounding action before finishing. Its test-only `complete_joiner`
scenario parses only the fixed supplied-values grammar in the trusted human
brief and selects current opaque Groundings by geometry/allowed action kind;
it has no task-fact lookup, DOM/AX input, OCR, VLM inference, router, or
planner. No real VLM provider, adapter, key, endpoint, or egress exists in
default Compose or CI.

W5 budgets cap 24 steps/calls/images, total image bytes/pixels/capture time,
input/output tokens, cost, duration, repetition, and no progress. Model result
records only numeric image/call/token/cost/latency totals plus bounded action
metadata; it never persists pixels or text.

## Task input and grading boundary

The outer caller may render immutable W3 title/instructions and supplied
synthetic values into a human-readable brief. It must not modify a task,
checksum, predicate, or manual baseline, and must not send grader predicates to
the model. For W5 Development candidates it runs two equal Reset/Seed calls,
starts a fresh session at HRIS, invokes the Vision Agent, ensures cleanup, and
then calls the W3 Grader independently.

Agent finish produces finished_ungraded. Only an unchanged W3 100/100 grade is
a pass. The W5 fake acceptance first proves that the untouched read/finish
subrun remains 30/100 and non-passing, then Reset/Seeds again and requires the
bounded `complete_joiner` subrun to receive an independent 100/100,
`passed=true` grade. That latter fact proves the outer grading boundary still
decides the outcome for the deterministic test policy; it is not a real
Vision-only VLM/OCR result, a success-rate sample, or proof of visual
understanding.

## Explicit W6 boundary

There is no DOM/Vision Router, DOM-quality signal, hybrid context, modality
switch, planner, verifier, checkpoint, recovery, memory, or routing policy in
this architecture. Those choices remain future work.
