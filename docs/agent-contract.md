# W4 agent contract — DOM Agent Foundation

## Authority and objective

This contract translates the W4 row of
[project-roadmap.md](project-roadmap.md) and the user-authorized W4 brief into a
bounded implementation agreement for `week/04-dom-agent`.

The sole outcome is a minimal DOM-only Agent foundation: an isolated
Playwright Browser Worker exposes strict observations and typed actions to a
separate bounded ReAct loop. The acceptance caller resets fixed W3 Development
tasks before a run and grades database facts afterward. Only the unchanged W3
Grader may declare success.

The roadmap's final “start W1” paragraph is historical bootstrap guidance. The
specific W4 schedule row, completed W1-W3 releases, and this explicit W4
authorization govern the current branch. Future roadmap architecture remains
non-authorizing; W5+ is still prohibited.

## Baseline observed before W4 edits

- W3 PR #20 is merged into `main` at `11c4494`.
- Both final W3 push and pull-request CI runs completed successfully, including
  both `Secret scan` jobs.
- Remote annotated tag object `1d4cc6f` exists as `w03-arena` and dereferences
  to `11c4494`.
- `git pull --ff-only` reported `main` already up to date with `origin/main`.
- `week/04-dom-agent` was created from synchronized `main`.
- No tracked or contract-eligible untracked changes existed at the boundary.
- `%SystemDrive%/` and every `code_review_agent` repository remained outside
  all reads, scans, diffs, staging, and modifications.

## Conservative W4 architecture decisions

1. `apps/browser_worker` is an independent FastAPI process/container. It owns
   Playwright, Browser/Page/Context resources, observation construction,
   action validation, URL policy, session budgets, and cleanup. It has no
   database credential, repository mount, Docker socket, arbitrary execution
   endpoint, or network route to `sandbox-api`.
2. `apps/dom_agent` is a second independent FastAPI process/container. It owns
   the minimal ReAct loop and deterministic fake model. It communicates only
   with the Browser Worker and has no network route, library dependency, or
   credential for Sandbox APIs, PostgreSQL, Reset/Seed, or Grader.
3. An outer acceptance caller owns the W3 management sequence: fetch immutable
   task metadata, Reset/Seed twice, build the human-facing instruction brief,
   invoke the Agent, close resources, then call the W3 Grader. Those management
   calls are never model tools and never enter Browser Worker actions.
4. The W3 prose says to use “supplied synthetic identifiers” but does not spell
   all identifiers out in its `instructions` array. The acceptance caller may
   deterministically render a human-facing brief from the immutable Task Spec's
   title, `instructions`, and expected synthetic business values. The loop
   receives only that text, current observation, bounded action summaries, and
   remaining budgets—not grader predicates, database facts, or management API
   access. Specs/checksums remain unchanged.
5. Browser Worker and Agent use versioned JSON over narrow local HTTP APIs.
   There is no shared runtime package, dynamic code loading, selector input,
   or generic proxy. Both sides validate unknown fields strictly.
6. Compose uses three explicit internal networks. Browser Worker shares one
   network only with `sandbox-web` and one only with DOM Agent. `sandbox-web`
   alone bridges browser traffic to the existing Sandbox backend network.
7. No W4 database state is required. No W2/W3 migration or schema changes.
8. Playwright is pinned to `1.60.0`, whose bundled Chromium is
   `148.0.7778.96`. Python is pinned to the 3.13 line, uv to `0.11.14`, and
   container bases/tags and resolved digests are recorded in evidence.

These decisions are detailed in
[adr/0004-w4-isolated-dom-worker-and-agent.md](adr/0004-w4-isolated-dom-worker-and-agent.md).

## Exact W4 file allowlist

Only the following paths may be created or modified in W4:

```text
AGENTS.md
README.md
CHANGELOG.md

.github/dependabot.yml
.github/workflows/ci.yml

docs/agent-contract.md
docs/architecture.md
docs/threat-model.md
docs/evaluation-protocol.md
docs/adr/0004-w4-isolated-dom-worker-and-agent.md
docs/plans/week-04-dom-agent.md
docs/evidence/week-04-report.md

deploy/compose/compose.yaml

apps/sandbox_web/package.json
apps/sandbox_web/package-lock.json
apps/sandbox_web/src/App.tsx
apps/sandbox_web/src/App.test.tsx

apps/browser_worker/.dockerignore
apps/browser_worker/Dockerfile
apps/browser_worker/pyproject.toml
apps/browser_worker/uv.lock
apps/browser_worker/src/flowpilot_browser_worker/__init__.py
apps/browser_worker/src/flowpilot_browser_worker/config.py
apps/browser_worker/src/flowpilot_browser_worker/schemas.py
apps/browser_worker/src/flowpilot_browser_worker/policy.py
apps/browser_worker/src/flowpilot_browser_worker/observation.py
apps/browser_worker/src/flowpilot_browser_worker/runtime.py
apps/browser_worker/src/flowpilot_browser_worker/main.py
apps/browser_worker/tests/conftest.py
apps/browser_worker/tests/test_schemas.py
apps/browser_worker/tests/test_policy.py
apps/browser_worker/tests/test_observation.py
apps/browser_worker/tests/test_runtime.py
apps/browser_worker/tests/test_api.py

apps/dom_agent/.dockerignore
apps/dom_agent/Dockerfile
apps/dom_agent/pyproject.toml
apps/dom_agent/uv.lock
apps/dom_agent/src/flowpilot_dom_agent/__init__.py
apps/dom_agent/src/flowpilot_dom_agent/schemas.py
apps/dom_agent/src/flowpilot_dom_agent/model.py
apps/dom_agent/src/flowpilot_dom_agent/openai_model.py
apps/dom_agent/src/flowpilot_dom_agent/client.py
apps/dom_agent/src/flowpilot_dom_agent/loop.py
apps/dom_agent/src/flowpilot_dom_agent/main.py
apps/dom_agent/tests/conftest.py
apps/dom_agent/tests/test_schemas.py
apps/dom_agent/tests/test_client.py
apps/dom_agent/tests/test_loop.py
apps/dom_agent/tests/test_api.py
apps/dom_agent/tests/test_model.py

tests/integration/w4_compose_smoke.py
tests/integration/w4_real_model_acceptance.py
tests/integration/Dockerfile
```

The W1-W3 source, W2/W3 migrations, ten Task Specs, their checksums, and W3
manual-baseline evidence are regression inputs only and are not on this change
allowlist. Any newly necessary path must be added before it changes. A path
that broadens W4 scope requires user direction rather than an implicit edit.

## Browser Worker contract

- `POST /api/browser/sessions` accepts only schema version and a configured
  initial local Sandbox path. The worker generates the session ID.
- `POST /api/browser/sessions/{session_id}/actions` accepts one discriminated,
  strict typed action. The path session and body session, observation, and
  short-lived element references must agree where applicable.
- `DELETE /api/browser/sessions/{session_id}` idempotently closes Page,
  Context, and Browser. Finish, fail/escalate, timeout, and budget exhaustion
  also close them.
- No endpoint accepts JavaScript, Playwright source, CSS/XPath selector, shell,
  SQL, file path, command, eval, upload, download, Cookie, storage, arbitrary
  header, proxy target, or raw browser option.
- Navigation accepts only configured relative Sandbox routes or an exact URL
  on the configured origin. It rejects credentials, non-HTTP schemes, unknown
  hosts/ports, query-based proxying, and external redirect requests.
- Each task launches a fresh Browser, Context, and Page. Hard limits cover
  navigations, actions, waits, fill length, observation size, and wall time.

## Observation and element reference contract

Observation schema `w4-dom-observation/1.0` contains only:

- worker-generated `session_id` and `observation_id`;
- current URL and page title;
- bounded, normalized semantic DOM text nodes;
- bounded interactive elements with worker-generated `element_ref`, role,
  accessible name, safe state, and allowed actions;
- the last structured action result, sanitized page/action error, and a
  truncation flag.

The worker uses fixed internal extraction code only. Page text is untrusted
data. Script/style/noscript/template, hidden nodes, irrelevant attributes,
input values, password controls, credentials, Cookie/Local Storage, and long
text are excluded. Node count, per-text length, element count, and serialized
byte limits apply with stable DOM-order traversal and normalization.

Every new observation invalidates the previous reference table. References
contain an observation-scoped nonce and index generated inside the worker.
Unknown, forged, missing, and cross-observation references fail without
executing a browser action. No selector or locator recipe is returned.

Observation models deliberately have no screenshot, image, pixel, OCR, VLM,
visual feature, image path, selector, browser code, network log, trace, form
value dump, Cookie, or storage field.

## Typed action contract

Action schema `w4-dom-action/1.0` is a strict discriminated union containing
`navigate`, `click`, `fill`, `select`, `read`, `scroll`, `wait`, `finish`, and
`fail`. Every action has a constrained `action_id`; element actions also carry
the current `observation_id` and `element_ref`.

- `navigate` accepts one allowed URL/path and is navigation-budgeted.
- `click`, `fill`, `select`, `read`, and element `scroll` resolve only the
  current reference table. `fill` rejects password controls, non-synthetic
  email/account patterns, control characters, and overlong text.
- `wait` is millisecond-bounded. It cannot wait indefinitely.
- `finish` ends the loop and closes the session. It has no `passed` or
  `success` field and cannot invoke or substitute for grading.
- `fail` records a constrained category/reason, closes resources, and does not
  claim a grade.
- Results contain structured success/failure, an enumerated error category,
  a sanitized message, and a new observation only while the session remains
  active.

## DOM Agent loop contract

- Model context contains only the human-facing task brief, current strict DOM
  observation, a bounded summary of prior actions, and remaining step/call/
  token/cost/time budgets.
- Model output is JSON validated as a strict typed action envelope. Invalid
  JSON, unknown fields/actions, invalid types, stale references, and invalid
  budget usage fail safely.
- The model interface has no Browser, HTTP, database, Reset/Seed, Grader,
  filesystem, shell, SQL, or JavaScript method. The loop can call only the
  Browser Worker client after local validation.
- Hard caps cover steps, model calls, repeated identical actions, no-progress
  observations, duration, input/output tokens, and actual provider-reported
  cost. Cap exhaustion closes the browser session and returns a non-success
  terminal reason.
- W4 implements no planner, verifier, checkpoint, replay, recovery, memory,
  dynamic router, approval, or visual fallback.
- CI and default Compose use deterministic fake models. The user authorized a
  one-off OpenAI `gpt-5.6-terra` five-task run on 2026-07-26 after disclosure
  of prompt/config `w4-dom-react-openai/1.0`. After a documented minimum-action
  audit, the user separately authorized revised 125-call, 500,000-input,
  100,000-output, 900-second, zero-retry, USD 3.25 aggregate caps.
- The authorized provider adapter uses only the fixed OpenAI Responses URL,
  exact model, strict JSON Schema output, `store=false`, no provider tools,
  and medium reasoning. The API key is environment-only and never logged,
  returned, mounted from a file, or committed.
- A profile-only real Agent may additionally use one outbound bridge solely
  so its fixed adapter can reach the authorized provider. It remains absent
  from default Compose and has no Sandbox API/PostgreSQL network or client.

## Five-task and evidence rules

- Only `w3-joiner-001` through `w3-joiner-005` are W4 acceptance candidates.
- Before each authorized real-model run, the caller compares two Reset/Seed
  results, starts at HRIS in a fresh browser session, and records task/spec/seed
  checksum and prompt/config version.
- The Agent acts only through the five W2 pages. It cannot call business APIs
  directly or read database facts to choose actions.
- After termination, the caller invokes the W3 Grader independently. Only
  100/100 is a completion. Record steps, actions, calls, tokens, actual cost,
  score, failures, retries, timeouts, and human intervention.
- Without separate real-model authorization, record all five real runs as not
  run. Fake-model unit/smoke results are not presented as five-task success.
- Do not tune against Validation or Reporting tasks and do not modify any W3
  Task Spec/checksum based on W4 outcomes.

## Explicit prohibitions

W4 must not contain W5 screenshots/OCR/VLM/pixel actions; W6 routers/hybrid
observations; W7 planning/verifier/JML expansion; W8 Temporal/checkpoints/
recovery/faults; W9 context engines/retrieval/memory; W10 identity/RBAC/
tenancy; W11+ approvals/audit/production workers/monitoring/load; W14 malicious
page evaluation; W15 external benchmarks/reporting evaluation; real systems,
real accounts, personal data, real mail, arbitrary execution interfaces, or
unauthorized external APIs/models.

## Handoff and Git rules

- Preserve all W1-W3 paths and behaviours as regression contracts.
- Do not access `code_review_agent` or `%SystemDrive%/`.
- Do not push, create a PR, merge, tag, force-push, or call a real model without
  explicit authorization.
- Explicitly stage only contract paths after all locally available W4 gates
  pass and evidence matches observed facts.
- Stop at W4 completion.
