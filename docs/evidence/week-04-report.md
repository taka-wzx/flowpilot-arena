# Week 04 evidence report — DOM Agent Foundation

- Status: W4 local foundation, fake-model acceptance, and authorized GLM 1.4 five-task Development acceptance complete at 5/5
- Branch: `week/04-dom-agent`
- Baseline commit: `11c4494` (`w03-arena`)
- Runtime baseline: Python 3.13
- Paid model calls and actual cost: OpenAI made 5 failed POST attempts with no reported usage; GLM made 302 POST attempts across 1.0-1.4, 300 usage-bearing completions reported 948,349 input and 68,110 output tokens, while 2 historical 1.0 abnormal completions omitted usage from the run record
- Real enterprise-system or external business API calls: 0
- Real-model five-task runs: OpenAI 0/5; GLM 1.0 0/5; GLM 1.1 0/5; GLM 1.2 3/5; GLM 1.3 4/5; GLM 1.4 grades 100, 100, 100, 100, and 100 (5/5)
- Current successful provider configuration: `w4-dom-react-glm/1.4`; one-off authorization consumed, no further paid run authorized
- Screenshot, OCR, VLM, or visual data captured: 0
- Remote delivery at this evidence freeze: branch pushed; PR #21 open with initial push/PR CI passed; merge and W4 tag pending

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

The final pre-staging W4 worktree contains exactly these 54 contract-owned
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
apps/dom_agent/src/flowpilot_dom_agent/glm_model.py
apps/dom_agent/src/flowpilot_dom_agent/schemas.py
apps/dom_agent/tests/conftest.py
apps/dom_agent/tests/test_api.py
apps/dom_agent/tests/test_client.py
apps/dom_agent/tests/test_loop.py
apps/dom_agent/tests/test_model.py
apps/dom_agent/tests/test_schemas.py

docs/adr/0004-w4-isolated-dom-worker-and-agent.md
docs/evidence/week-04-report.md
docs/plans/week-04-dom-agent.md

tests/integration/Dockerfile
tests/integration/w4_compose_smoke.py
tests/integration/w4_real_model_acceptance.py
```

No W2/W3 migration, Sandbox business source, W3 Task Spec/checksum, W3 test, or
manual-baseline evidence file changed.

## ADR and final service boundary

Decision source:
[../adr/0004-w4-isolated-dom-worker-and-agent.md](../adr/0004-w4-isolated-dom-worker-and-agent.md).

Browser Worker routes are `GET /healthz`, `POST /api/browser/sessions`,
`POST /api/browser/sessions/{session_id}/actions`, and idempotent
`DELETE /api/browser/sessions/{session_id}`. DOM Agent routes are
`GET /healthz` and `POST /api/agent/runs`. The latter accepts the default
`deterministic-fake` model and the authorization-gated fixed
`zhipu-glm-5.2` adapter, and returns no pass/score field.

The one-off `acceptance-smoke` profile is the outer trusted caller. It connects
to control, Sandbox management, and Agent networks solely to perform the
deterministic Reset/Seed → fake Agent → Grader proof. It is not started by the
normal Compose profile and contains no model or database driver.

The profile-only `real-agent` uses the same non-root/read-only image, strict
loop, and Browser Worker boundary. It alone joins `model-egress`; it has a fixed
Zhipu Chat Completions URL/model, no provider tools or configurable endpoint, and no
Sandbox/control network or client. The `real-acceptance` caller has management
networks but no key. Both profile images built successfully without a call.

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
| DOM Agent / real Agent image | W4 Dockerfile | GLM 1.4 build `sha256:b0f0710b826e608f20c5d86156e23b6b8dff2c9cbccb73a8bf2e5cb88e8592c4` |
| Fake / real acceptance image | W4 smoke Dockerfile | GLM 1.4 caller build `sha256:c0d25d1ce6a9c6f9643cec00efc1380562529bf1253824bc49b55f7f19cbaf26` |
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

The initial OpenAI adapter previously passed its offline gates, then produced
the observed 0/5 record below. It was superseded by GLM scheme B. The current
GLM adapter passed offline tests for its fixed Chat Completions URL and exact
`glm-5.2`, JSON-object mode plus strict local schema validation, prompt config
version, enabled thinking, high reasoning effort, deterministic sampling,
response/usage validation, sanitized HTTP status/code errors, conservative
provider pricing, and pre-network cost rejection. The API rejects the GLM model
with HTTP 503 when `ZHIPU_API_KEY` is absent. No offline test sends network
traffic.

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

The complete locally available handoff suite was rerun on 2026-07-27 after
the final GLM 1.4 evidence update and before staging.

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
| DOM Agent quality | Ruff check/format, mypy `src`, pytest | Passed; 7 typed source files; 27 tests |
| GLM profile parse/build | Compose config; build `real-agent` and `real-acceptance` | Current 1.4 images passed; no container, credential injection, or provider call started |
| Compose parse | `docker-compose -f deploy/compose/compose.yaml config` | Passed |
| Compose build/start | W4 build, then complete `up -d` | Passed; seven normal-profile containers healthy |
| Migration | running-container `alembic current`, `alembic check` | `20260726_0002 (head)`; no drift |
| Host W1/W2 routes | health and five-page probes | Eight URLs returned HTTP 200 |
| Ten W3 task runtime regression | task detail; two Reset/Seeds; two initial grades each | All checksums matched W3; every grade repeated identically at 30/fail |
| W3 correct/negative/baseline regression | Sandbox/Arena pytest suite | Passed within 23 tests, including all-ten correct state, partial/wrong/elevated/duplicate/untouched, read-only grade, and manual baseline |
| W4 fake Compose smoke | `--profile acceptance run --build --rm acceptance-smoke` | Passed; real Chromium, 2 actions, finish ungraded, independent 30/fail grade |

All four Python FastAPI test suites reported the same upstream
`StarletteDeprecationWarning` for the current TestClient/httpx path. It did not
affect the 1, 23, 23, or 27 passing tests.

## Five Development task record

Real-model execution was authorized for `gpt-5.6-terra` and the revised
aggregate caps. On 2026-07-27 the Windows User environment exposed the key to
the elevated Compose launcher without printing or writing it. Each fixed task
was Reset/Seed twice, invoked exactly once, and independently graded. All five
first provider requests failed before returning usage or an action. The Agent
closed each fresh browser session and returned `model_error`; no retry was
made. A subsequent non-generating model metadata GET from the same container
returned HTTP 200 for `gpt-5.6-terra`, confirming key/model visibility but not
identifying the rejected Responses POST detail. The aggregate caller reported
12.536 seconds, 0 completed model calls, 0 input/output tokens, USD 0.00 cost,
and 0/5 passing grades. There is no fake-model substitution in this table.

| Task ID | Spec checksum | Seed checksum | Model/prompt config | Steps/actions/calls/tokens/cost | Grader | Failure/retry/timeout/human intervention |
|---|---|---|---|---|---|---|
| `w3-joiner-001` | `614b3b0b1d907bf98dd9990b723eb7107e8ff81c9ed0dd5c464383f70b4f33f2` | `c4f4cd863b43b93e6e131e9938e18f640c3036d188554d28f2058aaaa9445f07` | `gpt-5.6-terra` / `w4-dom-react-openai/1.0` | 0 / 0 / 0 completed / 0 in + 0 out / USD 0.00 | 30/100, fail | `model_error` on first provider request; 0 retries/timeouts/interventions |
| `w3-joiner-002` | `4bd620f0bf346240378e3a46a3ba6c9b31ec2b4bde08463c4a2f9f95a6d7f34b` | `a1994592eadf26dc99603e6274d9f6b9307895eb4c4c28d61da3807827e8242d` | `gpt-5.6-terra` / `w4-dom-react-openai/1.0` | 0 / 0 / 0 completed / 0 in + 0 out / USD 0.00 | 30/100, fail | `model_error` on first provider request; 0 retries/timeouts/interventions |
| `w3-joiner-003` | `2f8c2ccea4a5506ae66b55fe6e9b2fc4ec326164de3e449e6516991bdc5ceae3` | `d821dcf959d905fa60c05a55a1c4c105683929ac12d297752946e1678996e476` | `gpt-5.6-terra` / `w4-dom-react-openai/1.0` | 0 / 0 / 0 completed / 0 in + 0 out / USD 0.00 | 30/100, fail | `model_error` on first provider request; 0 retries/timeouts/interventions |
| `w3-joiner-004` | `6223046d9abd748c658cebe70cebbecac85027b33128ea9930abe26f203b182b` | `cdab69be05d7fb3c544c90c4cf361c01302636340d9d37b103bed17343c701fc` | `gpt-5.6-terra` / `w4-dom-react-openai/1.0` | 0 / 0 / 0 completed / 0 in + 0 out / USD 0.00 | 30/100, fail | `model_error` on first provider request; 0 retries/timeouts/interventions |
| `w3-joiner-005` | `f356405dfa41cdfe93b0d30ae98284aff91f3277d2eb0d832abaf23116c80662` | `69f472c3e1386059c31f40327e32e4fec762f7ce2feafa22d4d7fa2958a3d9a5` | `gpt-5.6-terra` / `w4-dom-react-openai/1.0` | 0 / 0 / 0 completed / 0 in + 0 out / USD 0.00 | 30/100, fail | `model_error` on first provider request; 0 retries/timeouts/interventions |

No model output, action trace, DOM, or run result was written into a Task Spec.
Five provider-request failures occurred. There were no actions, timeouts,
retries, or human interventions.

## GLM scheme B acceptance

On 2026-07-27 the user directed replacement of the active real-model path with
Zhipu `glm-5.2`. The fixed provider endpoint is
`https://open.bigmodel.cn/api/paas/v4/chat/completions`; prompt/config is
`w4-dom-react-glm/1.0`. The request uses JSON-object mode, enabled thinking,
high reasoning effort, deterministic sampling, at most 1,024 output tokens per
call, no tools, no configurable endpoint, and zero retries. Per-task caps are
25 calls, 100,000 input tokens, 20,000 output tokens, 180 seconds, and a USD
0.35 conservative cost envelope. Strict Pydantic action validation remains
local and unchanged.

Official list pricing observed during implementation was CNY 8 per million
input tokens and CNY 28 per million output tokens. W4 cost-cap accounting uses
a deliberately conservative 4 CNY per USD envelope, so reported micro-USD cost
is `ceil((8 * input_tokens + 28 * output_tokens) / 4)` in micro-USD. This is a
budget upper-bound conversion, not an exchange-rate or provider-invoice claim.
The five-task aggregate caps are 125 calls, 500,000 input tokens, 100,000
output tokens, 900 seconds, zero retries, and a USD 1.75 conservative cost
envelope. At the token caps, official list price is at most CNY 6.8; the extra
USD 0.05 covers per-call integer rounding.
After exact disclosure, the user separately authorized the GLM run. A newly
rotated credential was read only from the Windows User environment and injected
only into `real-agent`. Five tasks ran once each with zero retries:

| Task ID | Steps/actions/completed calls | Input/output tokens | Accounted USD envelope | Grader | Terminal state | Missing required records |
|---|---|---|---|---|---|---|
| `w3-joiner-001` | 8 / 8 / 9 | 28,738 / 2,505 | 0.075011 | 60/100, fail | `invalid_model_output` | asset, mailbox |
| `w3-joiner-002` | 9 / 9 / 9 | 29,844 / 2,925 | 0.080163 | 45/100, fail | `no_progress_limit` | IAM, asset, mailbox |
| `w3-joiner-003` | 9 / 9 / 9 | 30,855 / 3,138 | 0.083676 | 45/100, fail | `no_progress_limit` | IAM, asset, mailbox |
| `w3-joiner-004` | 13 / 13 / 13 | 45,757 / 4,859 | 0.125527 | 60/100, fail | `model_error`: abnormal finish | asset, mailbox |
| `w3-joiner-005` | 14 / 14 / 14 | 49,642 / 4,113 | 0.128075 | 75/100, fail | `model_error`: abnormal finish | mailbox |

The aggregate caller reported 54 completed model calls, 184,836 input tokens,
17,540 output tokens, USD 0.492452 conservative envelope cost, 435.229 seconds,
0 retries, and 0/5 passes. At full uncached list prices, the usage-bearing
responses calculate to CNY 1.969808. Two additional responses ended abnormally
before `_response_usage` ran, so their provider usage and billing were omitted.
Consequently USD 0.492452 and CNY 1.969808 describe only the recorded subset,
not a complete invoice; the run cannot prove complete cost accounting even
though every reported aggregate remained below its cap.

After the run, the adapter was corrected offline so `ModelCallError` carries
optional provider usage, GLM usage is parsed before finish-state validation,
and the Agent loop accounts that usage and reapplies post-call budgets before
terminating safely. The deterministic regression for an abnormal completion
now verifies one call, 10 input tokens, 2 output tokens, and 34 micro-USD while
still returning `model_error` and closing the browser. The paid run was not
repeated, so its two historical abnormal responses remain unaccounted in the
observed provider totals above.

Detailed re-grading confirmed that every created record used the correct target
and no elevated IAM role or wrong association was introduced. Failure came from
incomplete required record creation, plus the invalid/no-progress/abnormal-
finish terminal conditions above. No fake result was substituted and no GLM
retry occurred.

Offline root-cause review found two deterministic orchestration weaknesses
consistent with the incomplete run. First, observations intentionally exclude
input values, but the loop treated an unchanged observation fingerprint after
a successful fill as no progress. Four such fills could therefore trigger the
configured limit despite real hidden form-state progress. Second, each
stateless model call received only six generic action summaries such as
`fill:true:none`, so it could not reliably distinguish fields already filled
or modules already submitted. These defects can explain premature/incomplete
form workflows without changing any W3 fact or grader predicate.

Prompt/config `w4-dom-react-glm/1.1` fixes those offline: successful fill/select
actions reset no-progress; up to 24 summaries retain safe accessible field or
button names and success/error state while omitting filled values and stale
references; the system prompt gives explicit JSON-only and one-action workflow
rules; and the per-call output ceiling is raised from 1,024 to 2,048 within the
unchanged task token/cost caps. A new deterministic test proves three
same-fingerprint successful fills do not terminate and that history contains
`Employee ID` but not its filled value. Ruff, format, mypy, and all 20 DOM
Agent tests pass.

The historical 1.0 invalid action body was not persisted, so its exact schema
mistake cannot be reconstructed. Likewise, the sanitized abnormal-finish
record did not preserve the provider finish reason; output truncation is only
a plausible cause, not an observed fact.

## GLM scheme B 1.1 acceptance

After exact disclosure, the user separately authorized prompt/config
`w4-dom-react-glm/1.1` for the same five tasks and aggregate hard caps. On
2026-07-27 each task was Reset/Seed twice, run exactly once, and independently
graded. No retry or human intervention occurred:

| Task ID | Steps/actions/completed calls | Input/output tokens | Accounted USD envelope | Grader | Terminal state |
|---|---|---|---|---|---|
| `w3-joiner-001` | 0 / 0 / 1 | 4,023 / 215 | 0.009551 | 30/100, fail | `invalid_model_output` |
| `w3-joiner-002` | 1 / 1 / 2 | 8,187 / 654 | 0.020952 | 30/100, fail | `invalid_model_output` |
| `w3-joiner-003` | 1 / 1 / 2 | 8,624 / 1,146 | 0.025270 | 30/100, fail | `invalid_model_output` |
| `w3-joiner-004` | 0 / 0 / 1 | 5,372 / 217 | 0.012263 | 30/100, fail | `invalid_model_output` |
| `w3-joiner-005` | 8 / 8 / 9 | 32,801 / 1,677 | 0.077341 | 60/100, fail | `invalid_model_output` |

The aggregate caller reported 15 completed/provider calls, 59,007 input
tokens, 3,909 output tokens, USD 0.145377 conservative envelope cost, 73.389
seconds, 0 retries, and 0/5 passes. Full uncached list pricing for recorded
usage calculates to CNY 0.581508. All 15 responses reported usage and finished
at the provider layer; every terminal failure was the repository's strict
`ModelDecision` validation, not API authorization, HTTP, time, or cost failure.
The exact invalid bodies were intentionally not persisted, and no second 1.1
attempt is claimed. Cleanup removed every container, network, and volume;
subsequent `ps -a` returned no services.

Provider `json_object` mode guarantees valid JSON but does not enforce this
repository's complete Pydantic action schema. Version 1.1 still asked GLM to
generate transport-only `schema_version`, `action_id`, and `observation_id`
fields as part of that full schema. Offline prompt/config
`w4-dom-react-glm/1.2` instead accepts only a compact strict typed action choice
with unknown fields forbidden. The trusted adapter generates those three
transport fields, binds element actions to the current observation, and then
validates the complete `ModelDecision`. A mock-provider regression verifies
metadata binding and another proves an unknown `selector` is rejected while
usage remains accounted. Ruff, format, mypy, and all 21 DOM Agent tests pass.
The offline 1.2 implementation was subsequently authorized once under the
same aggregate caps; its observed result follows.

## GLM scheme B 1.2 acceptance

After exact disclosure, the user separately authorized prompt/config
`w4-dom-react-glm/1.2`, compact strict action choices, trusted transport-field
binding, enabled thinking, high reasoning, no tools, zero retries, and the same
five-task aggregate caps. On 2026-07-27 each task was Reset/Seed twice, run
exactly once, and independently graded:

| Task ID | Steps/actions/completed calls | Input/output tokens | Accounted USD envelope | Grader | Terminal state |
|---|---|---|---|---|---|
| `w3-joiner-001` | 17 / 17 / 18 | 50,301 / 2,566 | 0.118564 | 100/100, pass | `model_error`: strict provider choice rejection after required facts were complete |
| `w3-joiner-002` | 4 / 4 / 5 | 14,595 / 1,305 | 0.038325 | 45/100, fail | `model_error`: strict provider choice rejection |
| `w3-joiner-003` | 4 / 4 / 5 | 15,543 / 1,021 | 0.038233 | 45/100, fail | `model_error`: strict provider choice rejection |
| `w3-joiner-004` | 19 / 19 / 19 | 57,938 / 5,092 | 0.151520 | 100/100, pass | `finished_ungraded`; external Grader passed |
| `w3-joiner-005` | 18 / 18 / 18 | 57,120 / 3,343 | 0.137641 | 100/100, pass | `finished_ungraded`; external Grader passed |

The aggregate caller reported 65 completed/provider calls, 195,497 input
tokens, 13,327 output tokens, USD 0.484283 conservative envelope cost, 330.974
seconds, 0 retries, 0 human interventions, and 3/5 passes. Full uncached list
pricing for recorded usage calculates to CNY 1.937132. All aggregate values
remained below the authorized 125-call, 500,000-input, 100,000-output,
900-second, and USD 1.75 limits.

Only the unchanged W3 Grader determined pass. Task 001 demonstrates that Agent
terminal status is not substituted for grading: its final provider choice was
rejected, but the independently observed database facts were already complete,
so it correctly graded 100/pass. Tasks 002 and 003 each executed four actions
before their fifth provider response failed the compact strict choice schema;
they graded 45/fail. The raw invalid choices were not persisted, so their exact
unknown/missing field cannot be reconstructed. No retry, second 1.2 attempt,
fake substitution, or human correction occurred. Cleanup removed all
containers, networks, and the PostgreSQL volume; subsequent `ps -a` returned
no services.

## GLM scheme B 1.3 offline remediation

Prompt/config `w4-dom-react-glm/1.3` keeps the single preferred compact
provider envelope and full strict local action validation. To address the
intermittent 1.2 shape drift without accepting arbitrary output, it adds two
explicit compatibility forms: a directly returned typed action, and legacy
transport metadata. Legacy schema versions must equal the W4 versions, a
legacy action ID must satisfy the existing `ActionId` type, and a supplied
element-action observation ID must exactly equal the current observation.
These fields are then discarded and trusted local metadata is generated.
Every other unknown field, including a selector, remains forbidden; stale
observation IDs remain rejected.

Validation failures now expose only a bounded Pydantic error type and schema
path, for example `extra_forbidden at action.click.selector`. They never expose
the raw provider body, page/form values, task facts, or credentials. Mock
provider tests cover compact, direct, exact legacy, stale-observation, unknown-
selector, usage-accounting, and full action binding paths. Ruff, format, mypy,
and all 24 DOM Agent tests passed before the separately authorized 1.3 run.

## GLM scheme B 1.3 acceptance

After exact disclosure, the user separately authorized prompt/config
`w4-dom-react-glm/1.3` under the same model, five tasks, and aggregate caps. On
2026-07-27 each task was Reset/Seed twice, run exactly once, and independently
graded:

| Task ID | Steps/actions/completed calls | Input/output tokens | Accounted USD envelope | Grader | Terminal state |
|---|---|---|---|---|---|
| `w3-joiner-001` | 18 / 18 / 18 | 50,302 / 2,767 | 0.119973 | 100/100, pass | `finished_ungraded`; external Grader passed |
| `w3-joiner-002` | 18 / 18 / 18 | 52,447 / 4,259 | 0.134707 | 100/100, pass | `finished_ungraded`; external Grader passed |
| `w3-joiner-003` | 1 / 1 / 2 | 7,230 / 1,240 | 0.023140 | 30/100, fail | `model_error`: `extra_forbidden at action.click.summary` |
| `w3-joiner-004` | 18 / 18 / 19 | 60,712 / 3,678 | 0.147170 | 100/100, pass | `model_error`: `string_too_long at action.finish.summary` after facts were complete |
| `w3-joiner-005` | 18 / 18 / 18 | 58,237 / 4,207 | 0.145923 | 100/100, pass | `finished_ungraded`; external Grader passed |

The aggregate caller reported 75 completed/provider calls, 228,928 input
tokens, 16,151 output tokens, USD 0.570913 conservative envelope cost, 379.844
seconds, 0 retries, 0 human interventions, and 4/5 passes. Full uncached list
pricing for recorded usage calculates to CNY 2.283652. All aggregate values
remained below the authorized caps. Only the W3 Grader determined pass: task
004 correctly passed because all required facts existed before its overlong
finish summary was rejected.

The sanitized diagnostic precisely identifies the remaining task-003 failure:
GLM attached a string `summary` to a `click` choice. The raw body and summary
value were not persisted. No retry, second 1.3 attempt, fake substitution, or
human correction occurred. Cleanup removed all containers, networks, and the
PostgreSQL volume; subsequent `ps -a` returned no services.

## GLM scheme B 1.4 offline remediation

Prompt/config `w4-dom-react-glm/1.4` treats `summary` only as non-executable
compatibility metadata. A summary attached to a non-finish action is discarded
only after strict string and 1,000-character validation; invalid types or
oversized values fail safely. A finish summary may validate up to 1,000
characters at the provider-choice boundary and is deterministically truncated
to the complete W4 action's 300-character limit before full validation. No
action type, URL, element reference, fill/select value, or executable field is
coerced or discarded. Tests cover the observed click-summary shape, invalid
summary metadata, and finish bounding; Ruff, format, mypy, and all 27 DOM Agent
tests passed before the separately authorized 1.4 run.

## GLM scheme B 1.4 acceptance

After exact disclosure, the user separately authorized prompt/config
`w4-dom-react-glm/1.4` under the same exact model, five Development tasks,
thinking/reasoning settings, zero-retry rule, and aggregate hard caps. On
2026-07-27 each task was Reset/Seed twice, run exactly once, and independently
graded:

| Task ID | Steps/actions/completed calls | Input/output tokens | Accounted USD envelope | Grader | Terminal state |
|---|---|---|---|---|---|
| `w3-joiner-001` | 18 / 18 / 18 | 49,881 / 2,829 | 0.119565 | 100/100, pass | `finished_ungraded`; external Grader passed |
| `w3-joiner-002` | 18 / 18 / 18 | 52,506 / 4,133 | 0.133943 | 100/100, pass | `finished_ungraded`; external Grader passed |
| `w3-joiner-003` | 19 / 19 / 19 | 59,703 / 3,527 | 0.144095 | 100/100, pass | `finished_ungraded`; external Grader passed |
| `w3-joiner-004` | 18 / 18 / 18 | 57,659 / 3,070 | 0.136808 | 100/100, pass | `finished_ungraded`; external Grader passed |
| `w3-joiner-005` | 18 / 18 / 18 | 60,332 / 3,624 | 0.146032 | 100/100, pass | `finished_ungraded`; external Grader passed |

The aggregate caller reported 91 completed/provider calls, 280,081 input
tokens, 17,183 output tokens, USD 0.680443 conservative envelope cost, 502.733
seconds, 0 retries, 0 human interventions, and 5/5 passes. Full uncached list
pricing for recorded usage calculates to CNY 2.721772. All aggregate values
remained below the authorized 125-call, 500,000-input, 100,000-output,
900-second, and USD 1.75 limits.

All five Agents returned `finished_ungraded`; none could declare success or
invoke grading. Only the unchanged outer W3 Grader observed the database facts
and returned 100/pass for every task. No retry, second 1.4 attempt, fake
substitution, human correction, Validation/Reporting tuning, or W3 fact/checksum
change occurred. Cleanup removed all containers, networks, and the PostgreSQL
volume; subsequent `ps -a` returned no services. The one-off 1.4 authorization
is consumed.

## Secret and diff review

| Gate | Observed result |
|---|---|
| `pre-commit detect-private-key --all-files` | Passed via temporary `uvx` runner after final handoff suite |
| Gitleaks complete Git history | Passed; 30 commits and approximately 1.26 MB scanned, no leaks found |
| Gitleaks final staged W4 state | Passed; 20-file current delta and approximately 67 KB scanned, no leaks found |
| `git diff --check` | Passed after final evidence update |
| Exact contract path audit | Passed in final state; changed 54, allowed 54, outside 0, allowed-but-unchanged 0 |
| Staged/unstaged review | Passed; 20-file current delta explicitly staged, including the contract-documented deletion of the superseded OpenAI adapter; no contract-owned unstaged delta |
| Real-acceptance cleanup | Passed; `docker-compose ... --profile real-acceptance down -v` removed all containers, networks, and the PostgreSQL volume; subsequent `ps -a` returned no services |

The first broad directory scan included local `.venv` dependencies and found
two known Playwright package strings plus two generic-key false positives in a
local URL/document sentence. The source wording was made unambiguous, and the
authoritative exact-file scan excluded local tool caches and passed. No ignore
or baseline suppression was added.

The global `pre-commit` entry point was not present on `PATH`; a temporary
`uvx` runner provided the same configured hook and passed. The final handoff
found the WinGet Gitleaks executable, reran complete-history scanning, and
found no leaks. No ignore or baseline suppression was added.

## Remote CI evidence

The validated branch was pushed and PR #21 was opened against `main`. Initial
GitHub Actions push run `30242879951` and pull-request run `30242906806` each
passed all nine jobs: backend, frontend, Sandbox/Arena backend, Sandbox
frontend, Browser Worker, DOM Agent, Compose configuration, Secret scan, and
W4 deterministic Compose smoke. The two smoke jobs completed in 2m50s and
2m47s. No paid-model credential or call is present in CI.

This evidence-only follow-up is itself subject to the same remote checks before
merge. Merge and `w04-dom-agent` tag creation are intentionally not claimed at
this evidence freeze; they are authorized subsequent release actions.

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
5. The OpenAI five-task acceptance ran once per task. All five first provider
   requests failed before usage or an action was returned; every independent
   grade was 30/fail. Its exact Responses POST rejection was unavailable from
   the run record. No OpenAI retry or second attempt is claimed.
6. The separately authorized GLM 1.0 five-task acceptance also passed 0/5, although
   it created progressively more correct records and reached grades up to 75.
   Two abnormal completions bypassed usage extraction, leaving total provider
   billing incomplete in the evidence. No 1.0 retry is claimed.
7. GLM 1.1 also passed 0/5: all five tasks terminated on strict local schema
   rejection, after 0, 1, 1, 0, and 8 actions respectively. Prompt/config 1.2
   minimizes the provider-owned schema.
8. The authorized GLM 1.2 run improved to 3/5. Tasks 001, 004, and 005 passed;
   002 and 003 stopped on compact choice rejection after four actions and
   graded 45. This is material progress but not five-task success.
9. The authorized GLM 1.3 run improved to 4/5. Task 003 stopped when a click
   carried non-executable summary metadata.
10. The authorized GLM 1.4 run passed 5/5 with every fixed Development task at
    100/100, zero retries, and all aggregate caps respected. This result does
    not authorize tuning or claims on Validation/Reporting tasks.
11. W4 proves bounded DOM-only foundations and this fixed Development result,
    not failure recovery, production reliability, malicious-page resistance,
    external generalization, or enterprise ROI.
12. Initial push and pull-request GitHub Actions passed all jobs. The final
    evidence-only follow-up must also pass before the authorized merge and tag.

Compose cleanup completed after final acceptance: all runtime containers,
five W4 networks, the one-off acceptance container, and the
synthetic PostgreSQL volume were removed. `ps -a` then returned no services.

## W5 boundary

W5 is not started. Screenshot capture/storage, OCR/VLM, visual grounding,
pixel-coordinate actions, image fields, and Vision-only evaluation require a
new branch, contract, ADR, and explicit authorization.
