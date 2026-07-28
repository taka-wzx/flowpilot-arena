# ADR 0006: Bounded Hybrid session and deterministic DOM-to-Vision Router

- Status: Accepted for W6
- Date: 2026-07-27

## Context

Released W4 supplies a DOM-only Browser Worker and Agent. Released W5 supplies
a separate visual-session Worker API and Vision-only Agent. W6 needs a Hybrid
baseline without joining their sessions, leaking both modalities to a model,
or adding W7 planning, recovery, memory, or provider access.

The risks are ambiguous modality ownership, a stale reference surviving a
switch, router decisions influenced by untrusted page text, visual limits reset
by a mode change, and a Hybrid service that gains Sandbox or grading access.

## Decision

Add one new Worker Hybrid session. It owns exactly one Browser, Context, and
Page at the W5 fixed visual viewport. The session starts with a DOM observation
and supports strict requests for one current DOM or Vision observation. It
returns a selected observation plus bounded Worker-derived DOM quality signals;
the signals contain counts, byte size, truncation state, and sanitized action
category only.

Every new observation, explicit switch, action result, timeout, terminal path,
delete, startup failure, cancellation, and shutdown clears both DOM and visual
reference maps. Every W6 action envelope carries its current session ID,
generation, and DOM or Vision mode. Element actions additionally carry only
that mode's current opaque references. The Worker checks session, generation,
mode, observation, and references before Playwright execution, so stale
navigate, wait, finish, and fail actions are rejected as well as stale element
actions.

Create a third Agent service, Hybrid Agent, separate from DOM Agent, Vision
Agent, and Browser Worker. Its deterministic Router has closed categories
standard and visual_recovery, starts in DOM, has at most two switches, and
ships with at most one DOM-to-Vision transition. It uses only Worker quality
signals, generic action outcome, numeric budgets, and category. It may switch
for structural DOM weakness, a safe DOM execution error, or one successful DOM
read probe under visual_recovery. It refuses a switch when any shared cap cannot
support it.

The Agent compresses DOM locally and deterministically before a DOM model call.
It retains at most 32 semantic nodes, 40 interactive elements, 12 action
summaries, 12,288 observation bytes, and 2,048 action-summary bytes. Visual
turns receive only the W5 bounded JPEG/grounding observation. No model call
receives both modalities. No observation, image, or compression result is
persisted.

The only runtime model is deterministic-fake-hybrid. A profile-only trusted
acceptance caller owns Reset/Seed and W3 grading. It proves a W6 fake
DOM-to-Vision completion and grade boundary without a real-model claim.

## Consequences

- Hybrid modality state remains in one Worker-owned browser lifecycle, so
  switching cannot splice two task states.
- Router choices are reproducible and inspectable through small reason codes,
  but W6 makes no learning or success-rate claim.
- Old references fail safely at the cost of a fresh observation after every
  switch and action outcome.
- The Hybrid Agent receives no task database or grading capability and cannot
  declare success. Its dedicated internal network contains only Hybrid Agent
  and Browser Worker; the trusted profile-only caller joins only for acceptance.
- W5 image caps remain global within a Hybrid session. W6 DOM/compression caps
  add a comparable bound for DOM mode.

## Rejected alternatives

- Reuse a W4 session and a W5 session for one task: page state, cookies, and
  reference lifetimes would be ambiguous.
- Add screenshots to W4 DOM observations or DOM to W5 visual observations:
  this would give a model both modalities by default.
- Let the model choose arbitrary modality or coordinates: routing and browser
  control would become unbounded/untrusted.
- Use page text, form values, URL, model output, or cross-task success history
  as router policy: these violate the W6 trust boundary or create W9 memory.
- Introduce an Agent superclass, provider gateway, planner, verifier, cache,
  or recovery hook: each is outside the narrowly bounded W6 outcome.
