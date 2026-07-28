# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- W6 bounded Hybrid Browser Worker session with one fresh Browser/Context/Page,
  selected current DOM or visual observations, safe structural route signals,
  strict session/generation-bound current-mode action envelopes, and
  cross-modality reference invalidation.
- W6 separate fake-only Hybrid Agent with deterministic DOM-first routing,
  closed reason codes/categories, local versioned DOM compression, total
  switch/observation/image/token/cost/time budgets, and no Sandbox/Arena/DB/
  Grader/provider access.
- W6 Compose/CI Hybrid isolation on a dedicated Hybrid-to-Worker internal
  network and deterministic DOM-to-Vision fake smoke proving wrong-mode/stale
  reference rejection, immediate-finish grade isolation, and a fresh
  independently graded completion circuit without a real model claim.
- W1 Foundation governance, scope contract, architecture documents, minimal
  API/web startup path, reproducible locks, and CI/security gates.
- W2 synthetic Sandbox foundation with one FastAPI/PostgreSQL backend,
  SQLAlchemy/Alembic schema, and five manual HRIS/ITSM/IAM/Asset/Mail routes.
- W2 backend and frontend unit tests, dependency locks, CI jobs, Compose runtime
  wiring, weekly ADR/plan/evidence, and a frozen synthetic onboarding recipe.
- W3 strict and canonical-checksummed Task Spec schema with ten fixed synthetic
  joiner tasks and a frozen 6/2/2 Development/Validation/Reporting allocation.
- W3 task-owned transactional Reset/Seed, database-fact-only deterministic
  Grader, narrow Arena management API, and anonymous manual-baseline recording
  with grader-derived scores.
- W3 Alembic ownership/baseline migration and deterministic catalog, reset,
  grading, negative-state, baseline, and API tests.
- W4 isolated non-root Playwright Browser Worker with local-origin policy,
  bounded DOM/accessibility observations, opaque observation-scoped element
  references, typed browser actions, and unconditional resource cleanup.
- W4 separate DOM Agent service with strict model JSON, deterministic fake
  scenarios, fixed Browser Worker client, and step/call/repetition/progress/
  time/token/cost budgets.
- W4 isolated Compose networks, one-off fake-model acceptance caller, pinned
  Python/uv/Playwright/Chromium runtime, CI jobs, dependency locks, and
  deterministic Worker/Agent/security/smoke tests.
- W4 authorization-gated profile-only Zhipu `glm-5.2` adapter and five-task
  caller with JSON-object output, strict local action validation, fixed
  endpoint, no tools/retries, environment-only key, and hard aggregate
  call/token/time/cost caps.
- W5 separate fake-only Vision Agent, strict versioned visual-session,
  observation, grounding, action, result, model-decision, budget, and run
  schemas, plus numeric image/latency/token/cost result metrics.
- W5 Browser Worker visual-session API with current in-memory JPEG viewport
  capture, fixed size/encoding/byte/count/time caps, output-only grounding
  rectangles, screenshot-scoped opaque references, and strict rejection of
  arbitrary coordinates, selectors, and code.
- W5 deterministic Vision-only Compose smoke, CI quality/smoke jobs, and
  fake-model tests proving both untouched-state 30/100 isolation and a
  separately reset, independently graded 100/100 `complete_joiner` circuit
  path without a provider call or Vision capability claim.

### Changed

- Superseded the unsuccessful OpenAI W4 real-model path with user-directed GLM
  scheme B while preserving the observed OpenAI 0/5 evidence.
- Remediated the observed GLM 0/5 path offline as prompt/config 1.1: successful
  hidden form fills now count as progress, bounded action history retains safe
  field/button names without values, strict output instructions are explicit,
  and the per-call output ceiling is 2,048 tokens.
- After prompt/config 1.1 was again observed at 0/5 from strict-schema
  rejection, added offline prompt/config 1.2: GLM returns a compact strict
  action choice while the trusted adapter generates transport-only versions,
  action IDs, and current observation IDs before full action validation.
- Recorded the separately authorized prompt/config 1.2 five-task outcome at
  3/5: tasks 001, 004, and 005 graded 100 while 002 and 003 graded 45; all
  calls remained within caps with zero retries.
- Added offline prompt/config 1.3 strict compatibility normalization for a
  direct typed action and exact legacy transport metadata, plus sanitized
  Pydantic error type/path reporting; unknown fields and stale observation IDs
  remain rejected.
- Recorded the separately authorized prompt/config 1.3 outcome at 4/5 and used
  its sanitized diagnostics to add offline 1.4 handling for bounded,
  non-executable summary metadata and deterministic finish-summary truncation.
- Recorded the separately authorized prompt/config 1.4 Development acceptance
  at 5/5: all five tasks independently graded 100 with zero retries and all
  aggregate call/token/time/cost limits respected.

### Security

- Restricted W6 routing to bounded Worker-derived structural metadata, safe
  action outcomes, trusted finite categories, and numeric budgets; rejected
  page/model-directed routing, joined sessions, dual-modal model input,
  cross-mode/stale references, learning/history/cache, and switching that
  resets any hard limit.
- Added ignored secret-file patterns, pre-commit private-key detection, and a
  CI Gitleaks scan.
- Restricted W2 email fields to `.invalid`, asset tags to `SYN-`, IAM roles to
  ordinary `employee`, and the API surface to non-destructive create/list calls.
- Restricted W3 reset to exact catalog task IDs and ownership markers; rejected
  unknown spec/API fields and caller-supplied baseline scores; kept grading
  read-only and based only on structured database facts.
- Isolated W4 Browser Worker from Sandbox API/PostgreSQL and host resources;
  isolated DOM Agent from every Sandbox/Arena/Grader route; rejected dangerous
  origins, redirects, selectors/code/commands, stale references, password/real
  email/credential-like input, and unbounded actions or waits.
- Isolated W5 Vision Agent to the Browser Worker network with no provider
  credential or egress; restricted visual data to a current synthetic Sandbox
  JPEG in memory; invalidated screenshot/grounding references after every
  observation; and rejected persistent image paths/URLs, raw OCR text, DOM
  fallback fields, arbitrary pixel actions, and stale visual references.
