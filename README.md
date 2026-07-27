# FlowPilot Arena

> A governed enterprise computer-use agent project and a separate, synthetic
> evaluation environment.
> 面向企业级 Computer-Use Agent 与独立合成评测环境的受治理项目。

**Current status: W5 — Vision Agent Foundation.** The released W4 DOM path is
preserved. W5 adds bounded in-memory synthetic viewport screenshots, strict
visual observations, opaque screenshot-scoped Grounding, and a separate
Vision-only fake-model ReAct baseline. W3's database-fact Grader remains the
only success authority.

## What works in W5

| Component | Current capability | Deliberately absent |
|---|---|---|
| W1 control paths | Static control web and health endpoint | Tasks, DB, Agent behavior |
| W2 Sandbox | Five manual HRIS/ITSM/IAM/Asset/Mail pages and APIs | Real systems/data, auth, production workflow |
| W3 Arena | Ten strict specs, task-only Reset/Seed, DB-only grade, baseline records | Browser/model-derived success |
| Browser Worker DOM path | Released bounded DOM observation, opaque refs, typed actions | Visual fields or fallback in the W4 schema |
| Browser Worker visual path | One current JPEG viewport, fixed image limits, opaque Grounding, strict visual actions | Image storage/path/URL, arbitrary pixels/selectors/code, external web |
| DOM Agent | Released strict DOM-only bounded ReAct loop | Vision input, routing, planner, verifier |
| Vision Agent | Separate fake-only visual ReAct loop with image/call/token/cost/time budgets | DOM/AX fallback, provider egress/key, real VLM by default |
| Acceptance smokes | Reset/Seed → fake Agent → independent grade, with a fresh reset before deterministic completion | Fake output or finish as a task-success claim |

~~~mermaid
flowchart LR
    Caller["Trusted acceptance caller"] --> Arena["W3 Reset/Seed + Grader"]
    Caller --> DomAgent["W4 DOM Agent"]
    Caller --> VisionAgent["W5 Vision Agent"]
    DomAgent --> Worker["Typed Browser Worker"]
    VisionAgent --> Worker
    Worker --> Web["Five Sandbox pages"]
    Web --> API["W2 business APIs"]
    API --> DB["Synthetic PostgreSQL"]
    Arena --> DB
~~~

## Quick start

Prerequisite: Docker Compose. Published ports bind to loopback. Browser Worker,
DOM Agent, and Vision Agent have no host port and use internal Docker networks.

~~~powershell
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
~~~

On a host with the standalone compatible executable instead:

~~~powershell
docker-compose -f deploy/compose/compose.yaml up --build -d
docker-compose -f deploy/compose/compose.yaml ps
~~~

Open:

- Sandbox web: http://127.0.0.1:5174/hris
- Sandbox API docs: http://127.0.0.1:8001/docs
- W1 control web: http://127.0.0.1:5173
- W1 control API health: http://127.0.0.1:8000/healthz

Run both trusted fake-only acceptance profiles:

~~~powershell
docker compose -f deploy/compose/compose.yaml --profile acceptance run --build --rm acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile vision-acceptance run --build --rm vision-acceptance-smoke
~~~

The DOM smoke and the Vision smoke's untouched-read subrun must both end as
finished_ungraded with zero external cost, then independently grade the
untouched initial task at 30/100 with passed=false. After a fresh equal
Reset/Seed pair, the Vision smoke's fixed `complete_joiner` scenario also ends
finished_ungraded and must receive an independent 100/100 with passed=true.
It uses only the caller-rendered synthetic brief and current opaque visual
Groundings; this deterministic fake result is a circuit/Grader-boundary check,
not a Vision-only VLM/OCR task-success or capability claim. The Vision smoke
records only numeric JPEG count/bytes/pixels/capture duration.

Stop and remove the disposable synthetic volume after acceptance:

~~~powershell
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
~~~

## Browser and Agent safety boundary

- Browser Worker runs non-root with a read-only root filesystem, no bind mount
  or Docker socket, all capabilities dropped, no-new-privileges, bounded
  tmpfs/shm/pids, and no database environment.
- It resolves only Sandbox Web plus the internal Agent network; it cannot
  resolve Sandbox API or PostgreSQL. Navigation is limited to five local pages
  and redirects are rechecked.
- The W5 visual route captures only the validated headless page viewport:
  fixed JPEG at 960 × 540 CSS pixels, quality 60, at most 184,320 bytes and
  3,000 ms per capture, with at most 24 attempts per session.
- Screenshots exist only in the current in-memory Worker response/model call.
  They are not written to files, database, logs, Task Specs, traces, or the
  repository. Browser chrome, host desktop, arbitrary URL/path, other origin,
  and other task capture are not inputs.
- A visual Grounding rectangle is output-only metadata. The model returns only
  the current opaque screenshot and Grounding references; it cannot send x/y,
  a rectangle, selector, XPath, JavaScript, Playwright, shell, SQL, file, or
  raw browser option.
- Every visual observation replaces the prior screenshot/Grounding map. Forged
  or stale references fail before Playwright execution.
- Vision Agent sees a human brief, one current JPEG observation, generic
  bounded action history, and remaining budgets. It has no DOM/AX/title/URL,
  page text, selector, input value, Cookie, Local Storage, Arena, business API,
  database, Reset/Seed, or Grader client.
- OCR or page instructions inferred from an image are untrusted data. Agent
  finish is finished_ungraded; only W3 Grader 100/100 is success.

## Local development and quality

Python targets 3.13 and uses uv; both frontends use committed npm locks.
Playwright remains pinned to 1.60.0 with Chromium 148.0.7778.96.

~~~powershell
Push-Location apps/browser_worker
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
Pop-Location

Push-Location apps/dom_agent
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
Pop-Location

Push-Location apps/vision_agent
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
Pop-Location
~~~

The complete W1-W5 regression, migration, Compose, secret-scan, and diff
sequence is frozen in [docs/plans/week-05-vision.md](docs/plans/week-05-vision.md).

## Model authorization and milestone boundary

No W5 real VLM/OCR provider, key, endpoint, or egress is configured or called
by default. The W4 DOM model authorization and historical DOM result do not
authorize a visual call. Before any real or paid visual call, disclose the
provider, exact model, endpoint, prompt/config, JPEG MIME/resolution/count,
task IDs, call/input/output/image/time/cost caps, and retries; then obtain
separate explicit user approval.

W5 has no DOM/Vision Router, DOM-quality heuristic, hybrid automatic switch,
planner, verifier, recovery, checkpoint, memory, identity, production worker,
monitoring, tracing, or other W6+ behavior. See
[docs/agent-contract.md](docs/agent-contract.md) and
[docs/threat-model.md](docs/threat-model.md).

Development occurs only on week/05-vision. No push, PR, merge, or tag is
authorized. Licensed under the [Apache License 2.0](LICENSE).
