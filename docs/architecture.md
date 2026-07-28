# Architecture

## W6 current-state architecture

W6 preserves released W1 stateless control paths, W2 five-module Sandbox, W3
deterministic Arena, W4 DOM Agent, and W5 Vision Agent. It adds a third,
separate Browser Worker API path and a third, separate Hybrid Agent service.
The W4 and W5 APIs remain available and are not router inputs.

~~~mermaid
flowchart LR
    Caller["Trusted acceptance caller<br/>Reset/Seed · brief · grade"] --> Arena["W3 Arena API"]
    Caller --> DomAgent["W4 DOM Agent"]
    Caller --> VisionAgent["W5 Vision Agent"]
    Caller --> HybridAgent["W6 Hybrid Agent<br/>deterministic Router"]
    DomAgent -->|"internal agent-worker"| Worker["Isolated Browser Worker"]
    VisionAgent -->|"internal agent-worker"| Worker
    HybridAgent -->|"dedicated internal hybrid-worker"| Worker
    Worker -->|"internal browser-sandbox"| Web["sandbox_web<br/>five business pages"]
    Web --> Business["W2 business APIs"]
    Arena --> Grader["W3 DB-fact Grader"]
    Business --> DB["Synthetic PostgreSQL"]
    Grader --> DB

~~~

The acceptance callers are trusted test orchestration only. They own immutable
task lookup, equal Reset/Seed comparison, human-brief rendering, and
independent grading. None is an Agent tool or a default Compose service.

| Boundary | Responsibility | Deliberately excluded |
|---|---|---|
| Browser Worker DOM sessions | Released W4 DOM observation/actions | Screenshot field, router, Hybrid state |
| Browser Worker visual sessions | Released W5 JPEG/grounding/actions | DOM fallback, router, image storage |
| Browser Worker Hybrid sessions | One Browser/Context/Page, one current selected modality, safe route signal, strict session/generation/mode/reference validation | Joined W4/W5 sessions, dual-modal response, selectors/coordinates, persistence |
| DOM Agent | Released DOM-only ReAct | Vision/Hybrid input or route policy |
| Vision Agent | Released visual-only fake ReAct | DOM/Hybrid input or route policy |
| Hybrid Agent | Per-task deterministic Router, DOM compressor, fake-only loop | Sandbox/Arena/DB/Grader/provider access, history, planner, verifier, recovery |
| W3 Arena/Grader | Reset/Seed and sole task-success decision | Browser/model control |

## Hybrid session lifecycle

A Hybrid session starts at /hris with a fresh Browser, Context, and Page at the
fixed W5 viewport. The initial response is DOM. The Router receives only safe
structural route signals from the Worker, selects DOM or Vision, and asks the
same session for a selected current observation when a switch is needed.

~~~mermaid
sequenceDiagram
    participant H as Hybrid Agent
    participant R as Router
    participant W as Browser Worker
    participant P as One Page

    H->>W: create Hybrid session
    W->>P: launch one Browser/Context/Page
    W-->>H: current DOM observation + safe route signal
    H->>R: bounded signal + budget + action outcome
    R-->>H: DOM or Vision decision/reason
    alt Switch to Vision
        H->>W: request current Vision observation
        W->>W: invalidate all old DOM/visual refs
        W-->>H: current Vision observation + safe route signal
    end
    H->>W: strict session + generation + current-mode action envelope
    W->>W: validate session/generation/mode/observation/ref/action
    W->>P: typed Playwright action
    W->>W: invalidate all old refs and build one current observation
    W-->>H: action result + one selected current observation
~~~

Every new observation, modality switch, action success or failure, timeout,
terminal action, explicit delete, startup failure, cancellation, and shutdown clears both
reference maps. This prevents a DOM reference surviving a visual turn or vice
versa. W5 visual count/bytes/pixels/capture-time limits stay session-global.

## Router and compression

The Router is deterministic and versioned. Its closed inputs are route category
(standard or visual_recovery), Worker-derived DOM structural state,
interactive-element count, DOM byte count, a sanitized action error category,
and remaining numeric budgets. It never accepts page text, form values, model
output, URLs, screenshots, or cross-task data as a route instruction.

It starts DOM-first. It can switch one way to Vision for a structural DOM
problem, a safe DOM execution failure, or one completed DOM read probe under the
trusted visual_recovery category. It has a hard switch cap and no W6
Vision-to-DOM recovery.

Before a DOM model call, Hybrid Agent deterministically truncates a current
W4-shaped observation in DOM order to the W6 compression caps. Before a visual
model call, it passes only the current W5-shaped visual observation. Generic,
bounded prior action summaries are shared context; full DOM and JPEG are never
present in the same model context.

## Isolation and grading

Browser Worker remains non-root, read-only, cap-dropped, no-new-privileges,
tmpfs/pids/shm-bounded, unmounted, credential-free, and limited to Sandbox Web.
Hybrid Agent uses equivalent non-root/read-only controls, has no host port, and
joins only the dedicated internal hybrid-worker network. That network contains
Browser Worker but no DOM Agent, Vision Agent, Sandbox, Arena, database, or
provider-egress service.

Hybrid Agent finish is finished_ungraded. It has no success, score, or grading
field. Only unchanged W3 Grader reads synthetic database facts after Browser
cleanup. The W6 fake smoke proves circuit and isolation behavior, not real
DOM, Vision, Hybrid, OCR, or VLM capability.

## Explicit W7 boundary

There is no planner DAG, tool matching, verifier, new task model, checkpoint,
recovery, memory, context engine, provider adapter, or production worker in
this architecture.
