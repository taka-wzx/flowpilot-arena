# Week 05 evidence report — Vision Agent Foundation

- Status: W5 local implementation, deterministic tests, W4 regression, and
  fake Vision-only Compose acceptance observed after deterministic completion
  amendment
- Branch: week/05-vision
- Baseline commit: c7a3e5a26477c1a92aa401b4f60f3eea333e1a02
  (w04-dom-agent)
- Real W5 VLM/OCR calls and actual cost: 0
- W5 fake Vision-only acceptance: untouched-state isolation retained 30/100,
  `passed=false`; bounded `complete_joiner` returned an independent 100/100,
  `passed=true` after a fresh Reset/Seed pair
- W5 real VLM/OCR results: not run and not authorized
- Screenshot/OCR artifacts committed or persistently stored: 0
- Remote CI, push, PR, merge, tag, and local commit: not performed

## Deterministic-completion amendment evidence

The current source adds a bounded `complete_joiner` deterministic fake scenario
and changes the Vision Compose smoke to retain the existing untouched 30/100,
`passed=false` subrun, then Reset/Seed again and require an independent
100/100, `passed=true` grade. It parses only the trusted caller's fixed
supplied-values brief and uses current opaque visual Grounding geometry; it has
no Task Spec/expected-state/Grader input, DOM fallback, provider call, or OCR/
VLM claim.

The current Vision Agent format, Ruff, Mypy, and 20 unit tests passed. The
standalone `docker-compose` 5.3.0 configuration parsed, the eight default
services became healthy, Alembic reported `20260726_0002 (head)` with no
upgrade drift, and cleanup removed all services, internal networks, and the
synthetic PostgreSQL volume.

The current Vision acceptance command completed through actual isolated
Chromium. Its first Reset/Seed pair produced the untouched 30/100,
`passed=false` proof. A fresh equal pair then produced this separate completion
result; Agent status remains ungraded and the score comes only from the
unchanged external W3 Grader:

~~~json
{"agent_actions":20,"agent_status":"finished_ungraded","agent_steps":20,"capture_duration_ms":483,"completion_seed_checksum":"c4f4cd863b43b93e6e131e9938e18f640c3036d188554d28f2058aaaa9445f07","cost_microusd":0,"grade":100,"image_bytes":575211,"image_count":20,"image_pixels":10368000,"model_calls":20,"passed":true,"spec_checksum":"614b3b0b1d907bf98dd9990b723eb7107e8ff81c9ed0dd5c464383f70b4f33f2","task_id":"w3-joiner-001","tokens":960,"untouched_grade":30,"untouched_passed":false,"untouched_seed_checksum":"c4f4cd863b43b93e6e131e9938e18f640c3036d188554d28f2058aaaa9445f07"}
~~~

## Startup gate evidence

- Read AGENTS.md, roadmap, contract, architecture, threat model, evaluation
  protocol, W4 evidence, and W4 ADR before W5 edits.
- Refreshed origin main/tags. HEAD, origin/main, and the dereferenced annotated
  tag w04-dom-agent all resolved to
  c7a3e5a26477c1a92aa401b4f60f3eea333e1a02.
- Created week/05-vision from synchronized main.
- The contract-eligible worktree before edits was clean.
- The pre-existing %SystemDrive%/ directory and every code_review_agent
  repository remained excluded from inspection, scan, diff, staging, and
  modification.

## Scope and exact changed files

The final pre-staging W5 worktree contains these 38 contract-owned changed or
new paths. The final path audit found 42 allowed, 38 changed, and 0 outside the
allowlist.

~~~text
.github/workflows/ci.yml
AGENTS.md
CHANGELOG.md
README.md

apps/browser_worker/src/flowpilot_browser_worker/config.py
apps/browser_worker/src/flowpilot_browser_worker/main.py
apps/browser_worker/src/flowpilot_browser_worker/observation.py
apps/browser_worker/src/flowpilot_browser_worker/runtime.py
apps/browser_worker/src/flowpilot_browser_worker/schemas.py
apps/browser_worker/src/flowpilot_browser_worker/vision.py
apps/browser_worker/tests/test_api.py
apps/browser_worker/tests/test_vision.py

apps/vision_agent/.dockerignore
apps/vision_agent/Dockerfile
apps/vision_agent/pyproject.toml
apps/vision_agent/uv.lock
apps/vision_agent/src/flowpilot_vision_agent/__init__.py
apps/vision_agent/src/flowpilot_vision_agent/client.py
apps/vision_agent/src/flowpilot_vision_agent/loop.py
apps/vision_agent/src/flowpilot_vision_agent/main.py
apps/vision_agent/src/flowpilot_vision_agent/model.py
apps/vision_agent/src/flowpilot_vision_agent/schemas.py
apps/vision_agent/tests/conftest.py
apps/vision_agent/tests/test_api.py
apps/vision_agent/tests/test_client.py
apps/vision_agent/tests/test_loop.py
apps/vision_agent/tests/test_model.py
apps/vision_agent/tests/test_schemas.py

deploy/compose/compose.yaml

docs/agent-contract.md
docs/architecture.md
docs/evaluation-protocol.md
docs/threat-model.md
docs/adr/0005-w5-bounded-vision-worker-and-agent.md
docs/evidence/week-05-report.md
docs/plans/week-05-vision.md

tests/integration/Dockerfile
tests/integration/w5_vision_compose_smoke.py
~~~

No W2/W3 migration, Sandbox business source, W3 Task Spec/checksum, Grader
predicate, or manual-baseline evidence changed.

## Architecture, isolation, and cleanup

W4 DOM sessions and DOM Agent remain distinct regression paths. W5 adds
separate visual-session Browser Worker routes and a separate Vision Agent
service. Default Compose has no model key, provider endpoint, or model-egress
attachment for Vision Agent.

Observed container inspection:

| Setting | Browser Worker | Vision Agent |
|---|---|---|
| User | flowpilot-browser | flowpilot-vision |
| Read-only root | true | true |
| Host bind mounts | none | none |
| Dropped capabilities | ALL | ALL |
| Security option | no-new-privileges:true | no-new-privileges:true |
| Networks | internal browser-sandbox and internal agent-worker | internal agent-worker only |
| Published host port | none | none |
| W5 model credential/egress | none | none |

Observed DNS probes confirmed Browser Worker resolved sandbox-web but not
sandbox-api or postgres. Vision Agent resolved browser-worker but not
sandbox-web, sandbox-api, or postgres. Container network inspection showed no
gateway on either internal Worker/Agent network.

Every visual task creates a fresh Browser, Context, and Page. The Worker clears
current visual references on a new observation and terminal cleanup; the
Vision Agent returns only numeric image aggregates. The post-acceptance
docker-compose down -v --remove-orphans removed all W5 containers, networks,
and the synthetic PostgreSQL volume; subsequent Compose ps returned no
services.

## Pinned runtime and image facts

| Component | Declared pin/tag | Observed W5 fact |
|---|---|---|
| Browser/Vision Python base | python:3.13.5-slim-bookworm | W5 images built successfully |
| uv | 0.11.14 | W5 image build and locked local sync passed |
| Playwright Python | 1.60.0 | Runtime reported 1.60.0 |
| Chromium | Playwright revision 1223 / 148.0.7778.96 | Existing W4 pin retained; W5 smoke used actual isolated Chromium |
| Browser Worker image | W5 Dockerfile | sha256:59b361e0c62ff149a52907036a1c328b431ae8bec898a6486ddf4bb8b83c9e30 |
| Vision Agent image | W5 Dockerfile | sha256:daab1ae82d343f7c2744dfedabee9d9d0b95d8dfa973d98c0f8d201782a3f5b7 |
| Fake acceptance image | Integration Dockerfile | sha256:f5f0f757709270b364fe2d1d3d860f3b292fb555f1bf9d7f214828acac7ea76e |
| Compose executable | standalone docker-compose | 5.3.0; docker compose plugin unavailable |

The first W5 image build found an escaped PATH literal in the new Vision Agent
Dockerfile, so pip was unavailable during the container build. The Dockerfile
was corrected before any service or smoke ran; the subsequent build/start and
both smokes passed. Classic Docker build emitted a Buildx-availability warning
but completed successfully.

## Visual schema, limits, and lifecycle evidence

| Item | Contract value | Observed evidence |
|---|---:|---|
| Visual session schema | w5-vision-session/1.0 | Worker/API tests passed |
| Visual observation schema | w5-vision-observation/1.0 | Worker/Vision tests passed |
| Visual action/result schemas | w5-vision-action/1.0 / w5-vision-action-result/1.0 | Strict API/schema tests passed |
| Vision model/run/result schemas | w5-vision-model-decision/1.0 and w5 Vision Agent versions | Vision Agent tests passed |
| Encoding | image/jpeg only | Fake smoke received real Worker JPEG observations |
| Viewport | 960 × 540 CSS pixels | Completion smoke reported 10,368,000 pixels across 20 images |
| Per-image pixels | 518,400 maximum | Schema/config tests passed |
| JPEG quality | Worker-fixed 60 | Builder test inspected capture arguments |
| Per-image bytes | 184,320 maximum | Oversize rejection test passed |
| Capture attempts/session | 24 maximum | Exhaustion test passed |
| Capture duration/image | 3,000 ms maximum | Slow-capture rejection test passed |
| Total image limits/run | 24 images, 4,423,680 bytes, 12,441,600 pixels, 72,000 ms | Vision loop budget tests passed |
| Grounding | current opaque ref plus output-only clipped rectangle | Current/forged/stale/cross-observation behavior tested |
| DOM/AX leakage into Vision path | prohibited | Schema/context tests found no DOM/AX/title/URL/name/role/text/selector/element_ref fields |
| Persistence | prohibited | No image path/URL/storage/fixture/trace endpoint exists; smoke output retained numeric metrics only |

The visual route accepts no raw image target, image path, file, OCR text,
selector, XPath, JavaScript, arbitrary coordinate, or unrestricted URL.
Grounding-bound actions require matching current observation_id, screenshot_ref,
and grounding_ref. Result messages are generic and do not return DOM labels or
OCR text.

## Fake-model results

### W4 DOM regression

The released fake DOM Compose smoke passed through actual isolated Chromium:

~~~json
{"agent_actions":2,"agent_status":"finished_ungraded","agent_steps":2,"cost_microusd":0,"grade":30,"model_calls":2,"passed":false,"seed_checksum":"c4f4cd863b43b93e6e131e9938e18f640c3036d188554d28f2058aaaa9445f07","spec_checksum":"614b3b0b1d907bf98dd9990b723eb7107e8ff81c9ed0dd5c464383f70b4f33f2","task_id":"w3-joiner-001","tokens":72}
~~~

### W5 Vision-only fake smoke

The first deterministic fake subrun received the current Worker JPEG, selected
one current Grounding read action, then finished without mutating state. Two
equal Reset/Seed responses preceded it, and the unchanged W3 Grader returned
30/100 with `passed=false` for that untouched state.

The smoke then Reset/Seeded twice again. `complete_joiner` consumed only the
current bounded JPEG/opaque Groundings and the caller-rendered supplied-values
brief; it completed 20 typed actions in a fresh Browser/Context/Page and
finished ungraded. The independent Grader result is the 100/100,
`passed=true` row recorded above. The run used 20 images, 575,211 image bytes,
10,368,000 image pixels, 483 ms capture time, 20 fake calls, 960 fake tokens,
and zero external calls/cost.

This is deterministic fake circuit evidence, not a real VLM/OCR call, OCR
accuracy result, Vision-only success-rate sample, or proof of visual
understanding.

## Real VLM/OCR evaluation

No W5 real VLM/OCR provider, model, endpoint, prompt/config, image call, retry,
token use, or cost was authorized. The W4 DOM-model authorization was not
reused.

| Task ID | Provider/model/config | Images/calls/tokens/cost | Grader | Status |
|---|---|---|---|---|
| w3-joiner-001 | Not run | 0 observed | Not run | Not authorized |
| w3-joiner-002 | Not run | 0 observed | Not run | Not authorized |
| w3-joiner-003 | Not run | 0 observed | Not run | Not authorized |
| w3-joiner-004 | Not run | 0 observed | Not run | Not authorized |
| w3-joiner-005 | Not run | 0 observed | Not run | Not authorized |

## W1-W5 validation results

| Area | Exact gate | Observed result |
|---|---|---|
| W1 backend | uv sync, Ruff, format, Mypy, pytest | Passed; 1 test |
| W1 frontend | npm.cmd ci, lint, typecheck, test, build | Passed; 1 test and production build |
| Sandbox/Arena backend | uv sync, Ruff, format, Mypy, pytest | Passed; 23 tests |
| Sandbox frontend | npm.cmd ci, lint, typecheck, test, build | Passed; 8 tests and production build |
| Browser Worker | uv sync, Ruff, format, Mypy, pytest | Passed; 31 tests |
| W4 DOM Agent | uv sync, Ruff, format, Mypy, pytest | Passed; 27 tests |
| W5 Vision Agent | uv sync, Ruff, format, Mypy, pytest | Passed after amendment; task-local temporary uv cache enabled locked host sync, then 20 tests passed |
| Compose parse | docker-compose config | Passed |
| Compose runtime | up --build -d, ps | Passed after amendment; eight default services healthy |
| Migration | alembic current, alembic check | 20260726_0002 (head); no new upgrade operations |
| W4 fake smoke regression | acceptance profile | Passed; external grade 30/fail |
| W5 fake Vision smoke | vision-acceptance profile | Passed; untouched external grade 30/fail, then fresh-reset completion external grade 100/pass |
| Cleanup | docker-compose down -v --remove-orphans, ps | Passed; no services remained |
| Private-key hook | `pre-commit detect-private-key --all-files` | Passed after amendment using an isolated task-local pre-commit cache |
| Gitleaks Git history | gitleaks git with redact | Passed; 32 commits / about 1.33 MB / no leaks |
| Gitleaks W5 delta | gitleaks dir on each exact changed path | Passed after amendment; 38 paths / no leaks |
| Diff format | git diff --check | Passed after amendment |
| Exact contract path audit | changed paths versus W5 allowlist | Passed after amendment; 42 allowed, 38 changed, 0 outside |
| Staged/unstaged review | explicit review before handoff | No staged files; all 38 W5 paths remain unstaged for user review |

The host PowerShell policy blocks npm.ps1, so npm.cmd was used as the compatible
npm executable. The first non-escalated frontend attempt could not remove a
Vite temporary directory; the same locked commands reran with the required
write permission and passed. TestClient emitted the existing Starlette/httpx
deprecation warning in Python API suites; it did not affect test outcomes.
The requested Git exclusion shorthand ':!%SystemDrive%' is not implemented by
this Git build; its compatible ':(exclude)%SystemDrive%' form produced a
3,225-line tracked diff without touching the protected directory.

## Known limitations

1. W5 fake evidence proves bounded screenshot/grounding plumbing, typed
   deterministic completion, and independent grading only. It does not prove
   OCR, VLM visual reasoning, general Vision-only success, generalization, or
   provider cost.
2. No real visual provider adapter, endpoint, key, egress, or call is included
   in default runtime. A real VLM/OCR evaluation requires separate exact
   disclosure and user approval.
3. The synthetic fixed Development pages are used only as a runnable visual
   surface. Validation and Reporting were not used for tuning.
4. W5 is development hardening, not a formal proof against browser compromise
   or malicious-image prompt injection.
5. The host has standalone docker-compose 5.3.0 rather than the docker compose
   plugin; classic builds passed despite a Buildx-availability warning.

## W6 boundary

W5 ends with isolated visual capture, restricted VLM/OCR image input, opaque
Grounding, and a fake-only Vision Agent baseline. It contains no DOM/Vision
Router, DOM-quality route signal, hybrid automatic switch, planner, verifier,
checkpoint, recovery, Temporal, memory, identity, approval, production worker,
monitoring, tracing, or any other W6+ behavior.
