# Week 06 evidence report - Hybrid Router

- Status: W6 local implementation, deterministic tests, W4/W5 regressions,
  fake Hybrid Compose acceptance, isolation inspection, cleanup, and all
  available secret/diff checks complete
- Branch: week/06-hybrid-router
- Baseline commit: 5981bf9f2d419854f51e0ced826efb3ac3864953 (w05-vision)
- Runtime baseline: Python 3.13; Playwright 1.60.0; Chromium revision 1223
- Real DOM/Vision/Hybrid model, VLM, or OCR calls and actual cost: not run;
  0 calls; 0 cost
- Screenshot, OCR, DOM, page-text, form-content, or credential artifacts
  committed or persisted: 0
- Remote delivery, remote CI, push, PR, merge, and tag: not run or authorized

## Startup gate evidence

- Read AGENTS.md, roadmap, W5 contract, architecture, threat model,
  evaluation protocol, W4/W5 evidence, W4/W5 ADRs, and W5 plan before W6
  edits.
- On 2026-07-27, main, origin/main, and dereferenced w05-vision resolved to
  5981bf9f2d419854f51e0ced826efb3ac3864953.
- Created week/06-hybrid-router from the synchronized main baseline.
- The eligible worktree had no change before branch work. Git emitted a
  permission warning for the host global ignore file, but returned no eligible
  change entries.
- The pre-existing %SystemDrive%/ directory and every code_review_agent
  repository remained excluded from inspection, scan, diff, staging, and
  change.
- On the 2026-07-28 continuation, the environment was already on
  week/06-hybrid-router with 42 allowlisted unstaged W6 paths. HEAD, main,
  origin/main, and dereferenced w05-vision still resolved to the baseline;
  the index was empty. The continuation preserved and re-audited that work
  instead of resetting it.

## Scope and exact changed files

The final W6 worktree contains exactly these 42 allowlisted paths:

~~~text
.github/workflows/ci.yml
AGENTS.md
CHANGELOG.md
README.md

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

deploy/compose/compose.yaml

docs/agent-contract.md
docs/architecture.md
docs/evaluation-protocol.md
docs/threat-model.md
docs/adr/0006-w6-bounded-hybrid-router.md
docs/evidence/week-06-report.md
docs/plans/week-06-hybrid-router.md

tests/integration/Dockerfile
tests/integration/w6_hybrid_compose_smoke.py
~~~

No W2/W3 migration, Sandbox business source, W3 Task Spec/checksum, Grader
predicate, manual baseline, DOM Agent, Vision Agent, or real-model path changed.

## Architecture, isolation, and lifecycle

W6 adds one Browser Worker Hybrid session and a separate Hybrid Agent service.
One Hybrid task creates exactly one Browser, Context, and Page at the fixed
960 x 540 visual viewport; it never joins a W4 session to a W5 session.

The Worker begins with a DOM observation and returns exactly one selected
current modality on every Hybrid response. It exposes only bounded route
signals to the Router: DOM structural state, effective interactive count,
serialized observation byte count, and sanitized action error category. The
Router receives no page text, form values, URL, model output, or cross-task
history.

Every new observation, modality switch, success/failure result, timeout,
terminal action, deletion, startup failure, cancellation, and shutdown clears
both DOM element references and visual screenshot/grounding references. Strict
W6 action envelopes bind session_id, generation, and modality; Worker rechecks
those fields plus observation/reference lifecycle and allowed action before
Playwright execution.

Observed local container inspection:

| Setting | Browser Worker | Hybrid Agent |
|---|---|---|
| User | flowpilot-browser | flowpilot-hybrid |
| Read-only root | true | true |
| Dropped capabilities | ALL | ALL |
| Security option | no-new-privileges:true | no-new-privileges:true |
| Host port binding | none | none |
| Networks | internal browser-sandbox, released agent-worker, and dedicated hybrid-worker | dedicated internal hybrid-worker only |
| DB/model credential or provider egress | none | none |

The Compose configuration also set only Browser Worker URL for Hybrid Agent.
The dedicated hybrid-worker network contains Browser Worker and Hybrid Agent,
but no DOM Agent, Vision Agent, Sandbox, Arena, database, or provider-egress
service. It attached no repository/host mount or Docker socket and applied
init, tmpfs, and 64-pid limits. Browser Worker retained its W5 image/JPEG
limits and 256-pid limit.

Observed current image IDs were Browser Worker
sha256:23ff8fb5fecf43a02d886e298dd7fb602c63d6fc3bdb0a93518dc5e2db81cb41,
Hybrid Agent
sha256:cb321fe81ee10e9074d3c685f69e91f6557dd531c383f224a7b016013a857982,
and Hybrid acceptance
sha256:905f03723d435f2511e285c4040ddec14b85a4d5537f813d6fa85bc23225dd57.

## Routing, compression, and action evidence

| Item | W6 contract | Observed local evidence |
|---|---:|---|
| Initial modality | DOM | Hybrid smoke began DOM-first |
| Route categories | standard, visual_recovery | Strict run schema and Router tests passed |
| Actual switch | DOM to Vision only | Completion smoke recorded one trusted_visual_recovery switch |
| Hard switch cap | 2 | Router/loop tests passed; shipped policy made one switch |
| DOM compression | 32 nodes, 40 elements, 12 action summaries, 12,288 bytes/observation, 2,048 summary bytes | Compressor tests passed; smoke completion used 5,138 total compressed bytes |
| Current-mode validation | Every envelope binds session/generation/mode; element actions add DOM obs/ref or visual obs/screenshot/grounding | Wrong-session, wrong-mode, forged, stale-generation, stale-observation, and unknown references passed unit tests before Playwright |
| W5 image envelope | 24 images, 4,423,680 bytes, 12,441,600 pixels, 72,000 capture ms maximum | Hybrid completion used 19 images, 545,563 bytes, 9,849,600 pixels, 423 ms |
| Hybrid total budget | steps/calls/switches/repetition/progress/DOM/image/token/cost/time hard caps | Router, loop, Worker, and Agent unit tests passed |

No model call receives full DOM and a JPEG together. DOM model input is a
current deterministic compressed DOM observation; visual model input is the
current W5 JPEG/grounding observation only. Compression and action summaries
remain task-local in memory.

## Fake baseline results

All runs used task w3-joiner-001, spec checksum
614b3b0b1d907bf98dd9990b723eb7107e8ff81c9ed0dd5c464383f70b4f33f2, and
seed checksum c4f4cd863b43b93e6e131e9938e18f640c3036d188554d28f2058aaaa9445f07
after each equal Reset/Seed pair.

| Baseline | Subrun | Safe metrics | Independent W3 grade |
|---|---|---|---|
| W4 DOM fake | grounded read then finish | 2 steps/actions/calls, 72 tokens, 0 cost | 30/100, passed=false |
| W5 Vision fake | untouched read then finish | 2 steps/actions/calls/images, 0 cost | 30/100, passed=false |
| W5 Vision fake | fresh complete_joiner | 20 steps/actions/calls/images, 575,211 image bytes, 10,368,000 pixels, 494 ms, 960 tokens, 0 cost | 100/100, passed=true |
| W6 Hybrid fake | immediate finish | 1 step/action/call, 0 switches, 1 DOM observation, 6,378 raw DOM bytes, 6,467 compressed bytes, 0 images, 48 tokens, 0 cost | 30/100, passed=false |
| W6 Hybrid fake | fresh DOM-to-Vision complete_joiner | 20 steps/actions/calls, 1 switch, 2 DOM observations, 11,644 raw DOM bytes, 5,138 compressed bytes, 19 images, 545,563 image bytes, 9,849,600 pixels, 423 ms, 960 tokens, 0 cost | 100/100, passed=true |

Every Agent result was finished_ungraded. None returned success, passed, score,
or raw page/image data. The W6 completion route reasons were DOM default,
trusted_visual_recovery, then retained Vision. The deterministic fake parses
only the trusted caller-rendered supplied-values brief and current opaque
references. These results are circuit/isolation and Grader-boundary evidence
only, not real DOM, Vision, Hybrid, OCR, or VLM capability claims.

## Real model evaluation

No W6 real model, provider, endpoint, credential, egress, VLM, OCR, image
call, retry, token use, or cost was authorized or run. Historical W4 DOM
authorization and W5 fake result were not reused.

| Category | Status | Calls | Cost |
|---|---|---:|---:|
| Real DOM-only | not run | 0 | 0 |
| Real Vision-only/VLM/OCR | not run | 0 | 0 |
| Real Hybrid | not run | 0 | 0 |

## Local gate results on the current source

| Area | Observed result |
|---|---|
| Control API | locked sync, Ruff, format, Mypy, pytest passed; 1 test |
| Control Web | npm.cmd ci, lint, typecheck, test, build passed; 1 test, 0 vulnerabilities |
| Sandbox/Arena API | locked sync, Ruff, format, Mypy, pytest passed; 23 tests |
| Sandbox Web | npm.cmd ci, lint, typecheck, test, build passed; 8 tests, 0 vulnerabilities |
| Browser Worker | locked sync, Ruff, format, Mypy, pytest passed; 39 tests |
| DOM Agent | locked sync, Ruff, format, Mypy, pytest passed; 27 tests |
| Vision Agent | locked sync, Ruff, format, Mypy, pytest passed; 20 tests |
| Hybrid Agent | locked sync, Ruff, format, Mypy, pytest passed; 31 tests |
| Compose configuration | standalone docker-compose 5.3.1 passed for default and all fake acceptance profiles; docker compose plugin unavailable |
| Compose build/start/ps | Passed; all nine normal W1-W6 services built and became healthy |
| Alembic | current reported 20260726_0002 (head); check reported no new upgrade operations |
| W4 smoke regression | Passed; finished_ungraded and independent 30/100 false |
| W5 smoke regression | Passed; untouched 30/100 false, fresh completion 100/100 true |
| W6 Hybrid smoke | Passed; explicit wrong-mode/stale-reference rejection and idempotent cleanup, immediate 30/100 false, fresh DOM-to-Vision completion 100/100 true |
| Container isolation | Passed; Hybrid Agent non-root/read-only/cap-drop/no-new-privileges/no mounts/no host port, resolves only Browser Worker on dedicated internal network |
| Container cleanup | Passed; down -v --remove-orphans left no project containers, networks, or volumes |
| Private-key detector | Passed; explicitly authorized temporary uvx runner initialized the configured pre-commit-hooks v5.0.0 environment and detect-private-key passed all files |
| Gitleaks | Passed: 37 commits/about 1.60 MB history and all 42 exact changed paths; no leaks |
| Diff format | git diff --check passed |
| Exact allowlist audit | 42 changed, 42 allowed, 0 outside, 0 allowlisted-but-unchanged |
| Staged/unstaged review | Passed before local commit; 42 allowlisted paths staged, 0 outside, 0 missing, and 0 unstaged |

Host PowerShell uses npm.cmd because the npm.ps1 policy is blocked. Frontend
Vite temporary-directory operations required the same elevated local rerun as
W5 and then passed. Python API test suites emitted the existing Starlette/httpx
deprecation warning; it did not affect outcomes. Mypy and Ruff caches were
redirected to a temporary directory because existing repository cache
directories were not writable; checked source and configuration were unchanged.
This Git build rejected the requested `':!%SystemDrive%'` shorthand with
`Unimplemented pathspec magic '%'`; the compatible
`':(exclude)%SystemDrive%'` form was used for diff, status, allowlist, and
changed-path secret checks without reading the protected directory.

## Known limitations

1. W6 fake results prove bounded wiring, deterministic route policy, reference
   lifecycle, compression, and independent grade isolation only. They do not
   prove visual reasoning, OCR, VLM quality, Hybrid generalization, or success
   rate.
2. The shipped Router is deliberately DOM-first and one-way DOM-to-Vision. It
   has no learned policy, historical success rate, Vision-to-DOM recovery,
   retry, planner, verifier, or checkpoint.
3. No real model/provider route exists in W6 default runtime. A real evaluation
   needs separate disclosure and explicit authorization.
4. This is development hardening, not a formal proof against browser
   compromise or malicious-page prompt injection.
5. The host provides standalone docker-compose 5.3.1 rather than docker compose
   and lacks the docker compose plugin and Buildx. Compatible classic builds,
   migrations, all three fake smoke profiles, isolation inspection, and cleanup
   passed without weakening their acceptance semantics.
6. The global pre-commit entry point is unavailable. After explicit user
   authorization, a temporary uvx runner downloaded pre-commit and the exact
   configured pre-commit-hooks v5.0.0 environment; detect-private-key passed all
   files. No runner, hook environment, ignore, or baseline was added to the
   repository. Gitleaks history and exact changed-path scans also passed.

## W7 boundary

W6 stops after bounded Hybrid routing, deterministic compression, strict
current-mode actions, and fake-only paired baseline evidence. W7 planner DAG,
tool matching, verifier, new task modeling, and every W8+ capability remain
out of scope.
