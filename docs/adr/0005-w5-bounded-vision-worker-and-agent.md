# ADR 0005: Bounded visual sessions and separate Vision-only Agent

- Status: Accepted for W5
- Date: 2026-07-27

## Context

Released W4 provides an isolated Browser Worker, strict DOM observations, and a
separate DOM Agent. W5 must add screenshot, OCR/VLM input, visual grounding,
and a Vision-only baseline without weakening those released paths or adding W6
hybrid routing.

Raw screenshots create new privacy, origin, resource, injection, and
coordinate-action risks. A model must see a current synthetic page image
without receiving arbitrary image URLs, browser control, DOM text, a direct
pixel-click primitive, database facts, Reset/Seed, or the Grader.

## Decision

Keep the released W4 DOM session API unchanged. Add a separate versioned visual
session API in the same isolated Browser Worker. A visual session creates the
same fresh Browser, Context, and Page as W4 but returns no DOM or accessibility
tree.

The Worker captures only the validated Sandbox page viewport after its existing
origin/request/redirect controls. Capture is fixed to one JPEG image at
960 × 540 CSS pixels, quality 60, no more than 184,320 bytes, 24 capture
attempts, and 3,000 ms per attempt. Images and visual references exist only in
the active request/session memory. They are never written to a file, log,
database, specification, trace, or repository.

A visual observation contains one opaque screenshot reference plus bounded
opaque grounding candidates. Each candidate has a Worker-generated reference,
an output-only clipped integer rectangle, and permitted action types. It does
not disclose DOM name, role, selector, locator recipe, input value, Cookie, or
storage. A model sends the current screenshot and grounding reference back;
the Worker verifies both and invokes its own internal locator. It never accepts
x/y, a bounding box, selector, XPath, CSS, JavaScript, or Playwright code.

Every new visual observation replaces the current screenshot and grounding
table. Prior visual references are invalid after successful and failed actions,
timeouts, terminal paths, session deletion, startup failure, and shutdown.

Create apps/vision_agent as an independent non-root/read-only FastAPI service
with only the Browser Worker network. Its model context contains the human
brief, one visual observation, generic bounded action summaries, and budgets.
It deliberately has no DOM observation, Sandbox/Arena/Grader client, provider
egress, credential, or real-model adapter. The default deterministic fake
vision model exercises one grounded action then finishes ungraded. A second,
test-only `complete_joiner` scenario accepts only a fixed supplied-values
suffix in the trusted human brief, chooses only current Groundings by
output-only geometry/allowed action kind, and follows the five fixed Sandbox
routes. It has no fixture-value map, Task Spec/expected-state/Grader input,
DOM/AX observation, OCR/VLM claim, router, or planner.

The trusted outer acceptance caller remains the sole owner of W3 Reset/Seed
and grading. It first runs two equivalent resets, invokes the one-read fake,
closes resources, and independently verifies the untouched 30/100 failure.
It then performs a new equal Reset/Seed pair, invokes `complete_joiner`, closes
resources, and independently requires W3 to return exactly 100/100 with
`passed=true`. Finish cannot become a success signal in either subrun.

## Consequences

- W4 DOM Agent behavior remains a separately testable regression path.
- A Vision-only model has no textual DOM/accessibility fallback, though it can
  use the supplied task brief and the image it sees.
- The model cannot manufacture a coordinate action. Grounding is limited to
  Worker-visible current interactive elements and current in-viewport boxes.
- Single-viewport JPEG and fixed caps make image volume, resolution, encoding,
  timing, and memory use bounded; a cap failure terminates safely.
- OCR is an untrusted visual-model inference within the one JPEG input, not a
  separate trusted tool or raw-text API.
- Default Compose and CI exercise fake-only code with zero provider traffic.
  A real VLM requires a later specific user authorization and disclosure.
- Existing five W3 Development pages can run the baseline without changing
  released task facts. The deterministic completion subrun proves typed visual
  plumbing and independent grading, not visual competence or VLM/OCR success.

## Rejected alternatives

- **Add a screenshot field to the W4 DOM observation:** mixes DOM and visual
  modalities and makes the Vision-only baseline ambiguous.
- **Expose a generic image download endpoint:** allows stale image retrieval,
  path/URL expansion, and longer-lived image handling.
- **Return DOM names or selectors next to visual boxes:** creates a hidden DOM
  fallback and an arbitrary browser-control surface.
- **Accept pixel coordinates from a model:** bypasses Worker-generated
  grounding and cannot be safely tied to a current element.
- **Embed Vision Agent in Browser Worker or DOM Agent:** weakens the process/API
  boundary and makes W4 regression behavior less isolated.
- **Use the W4 Zhipu key or real provider by default:** violates the separate
  W5 authorization gate and makes CI/Compose externally dependent.
- **Add routing, planner, verifier, recovery, or storage now:** belongs to W6+
  and is not needed for a bounded visual foundation.
