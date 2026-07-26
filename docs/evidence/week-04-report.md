# Week 04 evidence report — DOM Agent Foundation

- Status: local W4 code, fake-model, Compose, regression, and secret acceptance complete; real-model acceptance not authorized
- Branch: `week/04-dom-agent`
- Baseline commit: `11c4494` (`w03-arena`)
- Runtime baseline: Python 3.13
- Paid model calls and actual cost: 0 / 0
- Real enterprise-system or external business API calls: 0
- Real-model five-task runs: not authorized; not run
- Screenshot, OCR, VLM, or visual data captured: 0
- Push, PR, merge, or W4 tag: 0

## Startup gate evidence

- W3 PR #20 was observed merged at `11c4494` on 2026-07-26.
- The final W3 push and pull-request workflows both reported success for W1
  backend/frontend, Sandbox/Arena backend, Sandbox frontend, Compose config,
  and `Secret scan`.
- Remote annotated tag object `1d4cc6f` dereferenced to `11c4494`.
- `git pull --ff-only` reported `Already up to date.`
- `week/04-dom-agent` was created from synchronized `main` with no
  contract-eligible working-tree changes.
- `%SystemDrive%/` and all `code_review_agent` repositories remained excluded
  from inspection, scanning, diff, staging, and modification.

## Scope and exact changed files

The final pre-staging W4 worktree contains exactly these 51 contract-owned
changed or new paths:

```text
.github/dependabot.yml
.github/workflows/ci.yml
AGENTS.md
CHANGELOG.md
README.md
deploy/compose/compose.yaml
docs/agent-contract.md
docs/architecture.md
docs/evaluation-protocol.md
docs/threat-model.md

apps/browser_worker/.dockerignore
apps/browser_worker/Dockerfile
apps/browser_worker/pyproject.toml
apps/browser_worker/uv.lock
apps/browser_worker/src/flowpilot_browser_worker/__init__.py
apps/browser_worker/src/flowpilot_browser_worker/config.py
apps/browser_worker/src/flowpilot_browser_worker/main.py
apps/browser_worker/src/flowpilot_browser_worker/observation.py
apps/browser_worker/src/flowpilot_browser_worker/policy.py
apps/browser_worker/src/flowpilot_browser_worker/runtime.py
apps/browser_worker/src/flowpilot_browser_worker/schemas.py
apps/browser_worker/tests/conftest.py
apps/browser_worker/tests/test_api.py
apps/browser_worker/tests/test_observation.py
apps/browser_worker/tests/test_policy.py
apps/browser_worker/tests/test_runtime.py
apps/browser_worker/tests/test_schemas.py

apps/sandbox_web/package.json
apps/sandbox_web/package-lock.json
apps/sandbox_web/src/App.tsx
apps/sandbox_web/src/App.test.tsx

apps/dom_agent/.dockerignore
apps/dom_agent/Dockerfile
apps/dom_agent/pyproject.toml
apps/dom_agent/uv.lock
apps/dom_agent/src/flowpilot_dom_agent/__init__.py
apps/dom_agent/src/flowpilot_dom_agent/client.py
apps/dom_agent/src/flowpilot_dom_agent/loop.py
apps/dom_agent/src/flowpilot_dom_agent/main.py
apps/dom_agent/src/flowpilot_dom_agent/model.py
apps/dom_agent/src/flowpilot_dom_agent/schemas.py
apps/dom_agent/tests/conftest.py
apps/dom_agent/tests/test_api.py
apps/dom_agent/tests/test_client.py
apps/dom_agent/tests/test_loop.py
apps/dom_agent/tests/test_schemas.py

docs/adr/0004-w4-isolated-dom-worker-and-agent.md
docs/evidence/week-04-report.md
docs/plans/week-04-dom-agent.md

tests/integration/Dockerfile
tests/integration/w4_compose_smoke.py
```

No W2/W3 migration, Sandbox business source, W3 Task Spec/checksum, W3 test, or
manual-baseline evidence file changed.

## ADR and final service boundary

Decision source:
[../adr/0004-w4-isolated-dom-worker-and-agent.md](../adr/0004-w4-isolated-dom-worker-and-agent.md).

Browser Worker routes are `GET /healthz`, `POST /api/browser/sessions`,
`POST /api/browser/sessions/{session_id}/actions`, and idempotent
`DELETE /api/browser/sessions/{session_id}`. DOM Agent routes are
`GET /healthz` and `POST /api/agent/runs`. The latter accepts only the
`deterministic-fake` model in W4 and returns no pass/score field.

The one-off `acceptance-smoke` profile is the outer trusted caller. It connects
to control, Sandbox management, and Agent networks solely to perform the
deterministic Reset/Seed → fake Agent → Grader proof. It is not started by the
normal Compose profile and contains no model or database driver.

No W4 database migration was added. Running-container `alembic current`
reported `20260726_0002 (head)` and `alembic check` reported
`No new upgrade operations detected.`

## Pinned runtime and image versions

| Component | Declared pin/tag | Observed version or local content ID |
|---|---|---|
| Browser/Agent Python | `python:3.13.5-slim-bookworm` | 3.13.5; `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419` |
| uv | 0.11.14 | `uv 0.11.14 (x86_64-unknown-linux-gnu)` |
| Playwright Python | 1.60.0 | 1.60.0 |
| Chromium | Playwright revision 1223 | Chrome for Testing and headless shell 148.0.7778.96 |
| Browser Worker image | W4 Dockerfile | `sha256:5b87e1bccc1cd31ab24d4164afbc25e790ed6bb595825d535ce9ec21d3102778` |
| DOM Agent image | W4 Dockerfile | `sha256:7899a69c5ff736109c298f2085b28d8c579f80858e51299dafae8f3ad106bdf5` |
| Acceptance image | W4 smoke Dockerfile | `sha256:63eb619581bd2153a5c67de91237df62dab9a801bc4772e8d0d542631caabf53` |
| Host Node/npm | synchronized frontend locks | Node 24.15.0; npm 11.12.1 |
| Frontend build image | `node:24-alpine` | `sha256:a0b9bf06e4e6193cf7a0f58816cc935ff8c2a908f81e6f1a95432d679c54fbfd` |
| Frontend runtime image | `nginx:1.27-alpine` | `sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10` |
| PostgreSQL | `postgres:17-alpine` | `sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193` |

The Browser Worker build installed only the Chromium family required by
Playwright plus its FFmpeg runtime. No Firefox or WebKit was installed. A
repeat W4 image build completed from cached layers, and direct image checks
confirmed that Ruff, mypy, and pytest are absent from both runtime images.

## Worker isolation, network, and filesystem evidence

Container inspection observed:

| Setting | Browser Worker | DOM Agent |
|---|---|---|
| User | `flowpilot-browser` | `flowpilot-agent` |
| Read-only root | true | true |
| Host bind mounts | none (`null`) | none (`null`) |
| Dropped capabilities | `ALL` | `ALL` |
| Security option | `no-new-privileges:true` | `no-new-privileges:true` |
| Networks | internal `browser-sandbox`, internal `agent-worker` | internal `agent-worker` only |
| Published host port | none | none |
| DB/model credential environment | none | none |

Browser Worker resolved `sandbox-web` and did not resolve `sandbox-api`,
`postgres`, or `pypi.org`. DOM Agent resolved `browser-worker` and did not
resolve `sandbox-web`, `sandbox-api`, `postgres`, or `pypi.org`. Both internal
networks had an empty gateway in Docker inspection. Browser Worker had bounded
1 GiB shared memory, 256 pids, and tmpfs only at `/tmp` and its synthetic home;
DOM Agent had 64 pids and smaller tmpfs equivalents. Neither had a Docker
socket or repository mount.

W1/W2 host ports remained loopback-only. Host probes returned HTTP 200 for
control API/web, Sandbox API, and all five pages.

## Observation and action contracts

- Observation schema: `w4-dom-observation/1.0`.
- Action schema: `w4-dom-action/1.0`.
- Action result schema: `w4-dom-action-result/1.0`.
- Session schema: `w4-browser-session/1.0`.
- Model decision schema: `w4-model-decision/1.0`.
- Agent run/result schemas: `w4-dom-agent-run/1.0` and
  `w4-dom-agent-result/1.0`.

Default observation limits are 120 semantic nodes, 80 interactive elements,
240 characters per node/name, 200 title characters, and 32,768 serialized
bytes. Stable DOM-order traversal, whitespace normalization, hidden-node
filtering, input-value exclusion, select-label-only exposure, and truncation
were tested. Schema inspection confirmed no screenshot, image path, pixel,
OCR, VLM, selector, JavaScript, Cookie, or Local Storage fields.

Every observation uses a new internal nonce. Its reference map replaces the
prior map after successes and failures. Current references succeeded; forged
references returned `unknown_element_ref`; prior-observation references
returned `stale_element_ref`; neither executed the target action.

Typed navigate, click, fill, select, read, scroll, wait, finish, and
fail/escalate paths passed. Tests also covered dangerous URL schemes/origins,
direct API paths, redirect escape, real-email/password/credential/card-like/
multiline/overlong fills, unknown select labels, overlong waits, action budget,
distinct per-session Browser Contexts, and terminal/startup/shutdown cleanup.

## DOM Agent and fake-model results

The strict Agent loop passed valid fake action, invalid JSON, unknown fields,
external-model rejection, repeated action, no progress, step budget, model-call
exception, input/output token budget, cost budget, wall-time budget, finish,
failure, escalation, Worker error, and close paths. The Browser client exposes
only fixed create/action/delete routes and rejects external/credentialed/path-
bearing base URLs.

`AgentRunResult` has no `success`, `passed`, `score`, or Grader field. Finish
returns `finished_ungraded`.

The actual Compose smoke observed:

```json
{"agent_actions":2,"agent_status":"finished_ungraded","agent_steps":2,"cost_microusd":0,"grade":30,"model_calls":2,"passed":false,"seed_checksum":"c4f4cd863b43b93e6e131e9938e18f640c3036d188554d28f2058aaaa9445f07","spec_checksum":"614b3b0b1d907bf98dd9990b723eb7107e8ff81c9ed0dd5c464383f70b4f33f2","task_id":"w3-joiner-001","tokens":72}
```

The fake performed one DOM read and then finish in real isolated Chromium.
Two complete Reset/Seed responses were equal. The unchanged Grader then read
the untouched initial database facts as 30/100 and failed. This proves runtime
wiring and that finish does not bypass grading; it is not task completion.

## W1/W2/W3/W4 validation results

| Area | Exact commands | Observed result |
|---|---|---|
| W1 backend lock | `uv sync --locked --all-groups` | Passed; 43 packages resolved / 42 checked |
| W1 backend quality | Ruff check/format, mypy `src`, pytest | Passed; 3 files formatted; 2 typed files; 1 test |
| W1 frontend lock | `npm.cmd ci` | Passed; 249 packages added; audit reported 0 vulnerabilities |
| W1 frontend quality | lint, typecheck, test, build | Passed; 1 test; 30-module Vite build |
| Sandbox/Arena backend lock | `uv sync --locked --all-groups` | Passed; 42 packages resolved |
| Sandbox/Arena backend quality | Ruff check/format, mypy `src`, pytest | Passed; 23 files formatted; 12 typed files; 23 tests |
| Sandbox frontend lock | `npm.cmd ci` | Passed; 250 packages added; audit reported 0 vulnerabilities |
| Sandbox frontend quality | lint, typecheck, test, build | Passed; 8 tests; 36-module Vite build |
| Browser Worker lock | `uv sync --locked --all-groups` | Passed; 38 packages resolved/installed |
| Browser Worker quality | Ruff check/format, mypy `src`, pytest | Passed; 7 typed source files; 23 tests |
| DOM Agent lock | `uv sync --locked --all-groups` | Passed; 35 packages resolved/installed |
| DOM Agent quality | Ruff check/format, mypy `src`, pytest | Passed; 6 typed source files; 14 tests |
| Compose parse | `docker-compose -f deploy/compose/compose.yaml config` | Passed |
| Compose build/start | W4 build, then complete `up -d` | Passed; seven normal-profile containers healthy |
| Migration | running-container `alembic current`, `alembic check` | `20260726_0002 (head)`; no drift |
| Host W1/W2 routes | health and five-page probes | Eight URLs returned HTTP 200 |
| Ten W3 task runtime regression | task detail; two Reset/Seeds; two initial grades each | All checksums matched W3; every grade repeated identically at 30/fail |
| W3 correct/negative/baseline regression | Sandbox/Arena pytest suite | Passed within 23 tests, including all-ten correct state, partial/wrong/elevated/duplicate/untouched, read-only grade, and manual baseline |
| W4 fake Compose smoke | `--profile acceptance run --build --rm acceptance-smoke` | Passed; real Chromium, 2 actions, finish ungraded, independent 30/fail grade |

All three Python FastAPI test suites reported the same upstream
`StarletteDeprecationWarning` for the current TestClient/httpx path. It did not
affect the 23, 23, or 14 passing tests.

## Five Development task record

Real-model execution requires separate user authorization. Every row is
explicitly not run; fake-model tests are not substituted.

| Task ID | Spec checksum | Seed checksum | Model/prompt config | Steps/actions/calls/tokens/cost | Grader | Failure/retry/timeout/human intervention |
|---|---|---|---|---|---|---|
| `w3-joiner-001` | `614b3b0b1d907bf98dd9990b723eb7107e8ff81c9ed0dd5c464383f70b4f33f2` | `c4f4cd863b43b93e6e131e9938e18f640c3036d188554d28f2058aaaa9445f07` | Not authorized | Not run / 0 / 0 | Not run | None; no run |
| `w3-joiner-002` | `4bd620f0bf346240378e3a46a3ba6c9b31ec2b4bde08463c4a2f9f95a6d7f34b` | `a1994592eadf26dc99603e6274d9f6b9307895eb4c4c28d61da3807827e8242d` | Not authorized | Not run / 0 / 0 | Not run | None; no run |
| `w3-joiner-003` | `2f8c2ccea4a5506ae66b55fe6e9b2fc4ec326164de3e449e6516991bdc5ceae3` | `d821dcf959d905fa60c05a55a1c4c105683929ac12d297752946e1678996e476` | Not authorized | Not run / 0 / 0 | Not run | None; no run |
| `w3-joiner-004` | `6223046d9abd748c658cebe70cebbecac85027b33128ea9930abe26f203b182b` | `cdab69be05d7fb3c544c90c4cf361c01302636340d9d37b103bed17343c701fc` | Not authorized | Not run / 0 / 0 | Not run | None; no run |
| `w3-joiner-005` | `f356405dfa41cdfe93b0d30ae98284aff91f3277d2eb0d832abaf23116c80662` | `69f472c3e1386059c31f40327e32e4fec762f7ce2feafa22d4d7fa2958a3d9a5` | Not authorized | Not run / 0 / 0 | Not run | None; no run |

No model output, action trace, DOM, or run result was written into a Task Spec.
No failure, timeout, retry, or human intervention occurred because the real
runs did not occur.

## Secret and diff review

| Gate | Observed result |
|---|---|
| `pre-commit detect-private-key` over exact 51 files | Passed via temporary `uvx` runner |
| Gitleaks complete Git history | Passed before `d661c0a`; follow-up executable unavailable, so not rerun |
| Gitleaks exact W4 changed files | Original 47 files passed before `d661c0a`; six-file remediation delta not run because Gitleaks became unavailable |
| `git diff --check` | Passed after final evidence update |
| Exact contract path audit | Passed; changed 51, allowed 51, outside 0, allowed-but-unchanged 0 |
| Staged/unstaged review | Passed; the six-file remediation delta was staged explicitly, staged diff check passed, and no contract-owned unstaged path remained |

The first broad directory scan included local `.venv` dependencies and found
two known Playwright package strings plus two generic-key false positives in a
local URL/document sentence. The source wording was made unambiguous, and the
authoritative exact-file scan excluded local tool caches and passed. No ignore
or baseline suppression was added.

For the remediation follow-up, neither `gitleaks` nor the global `pre-commit`
entry point was present on `PATH`. `pre-commit` was recovered with a temporary
`uvx` runner and passed. Gitleaks could not be recovered from standard local
installation paths and is explicitly recorded as unavailable rather than
silently weakening or claiming its rerun.

## Observed implementation corrections and limitations

1. The host has standalone `docker-compose` 5.3.0 but no `docker compose`
   plugin. It also lacks Buildx; compatible Compose/classic build completed.
2. The first aggregate build client timed out at 124 seconds while Chromium
   dependencies were still installing. A scoped W4 build with a longer client
   timeout completed in about 130 seconds without code/security changes.
3. Making every Compose network `internal` prevented host W1/W2 port
   publication on this Docker implementation. W1/W2 networks were restored to
   loopback-published bridge networks; Browser/Agent networks remain internal
   and un-routed. The one-off acceptance profile now runs smoke inside Compose.
4. The original `sandbox_web` lock produced two high-severity package entries
   for direct `react-router-dom@7.11.0` and transitive `react-router@7.11.0`.
   The expanded advisory set included XSS, redirect, deserialization, DoS, and
   CSRF reports. npm first proposed `7.18.1`; after testing that version, the
   registry reported `GHSA-qwww-vcr4-c8h2` across `>=7.12.0 <8.3.0`, leaving no
   secure 7.x version. W4 therefore removed the unnecessary routing dependency
   and its `cookie`, `react-router`, and `set-cookie-parser` transitives. A
   bounded five-path in-app router preserves the existing pages, active link,
   history navigation, and unknown-path `/hris` fallback. Host and container
   `npm ci` now report zero vulnerabilities; all eight frontend tests pass.
5. Real-model five-task acceptance is not authorized and is not claimed.
6. W4 proves bounded DOM-only foundations and deterministic fake/runtime paths,
   not a task success rate, failure recovery, production reliability, malicious
   page resistance, or enterprise ROI.
7. Remote W4 GitHub Actions are not claimed because no push or PR is authorized
   or performed.

Compose cleanup completed after final smoke: all seven normal-profile
containers, four W4 networks, the one-off acceptance container, and the
synthetic PostgreSQL volume were removed. `ps -a` then returned no services.

## W5 boundary

W5 is not started. Screenshot capture/storage, OCR/VLM, visual grounding,
pixel-coordinate actions, image fields, and Vision-only evaluation require a
new branch, contract, ADR, and explicit authorization.
