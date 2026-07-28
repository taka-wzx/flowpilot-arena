# FlowPilot Arena

> A governed enterprise computer-use agent project and a separate, synthetic
> evaluation environment.
> 面向企业级 Computer-Use Agent 与独立合成评测环境的受治理项目。

**Current status: W6 - Hybrid Router.** Released W4 DOM-only and W5
Vision-only paths remain intact. W6 adds one bounded Hybrid Browser session,
safe DOM-quality routing signals, deterministic DOM compression, strict
current-mode action envelopes, and a separate fake-only Hybrid Agent. W3's
database-fact Grader remains the only success authority.

## What works in W6

| Component | Current capability | Deliberately absent |
|---|---|---|
| W1 control paths | Static control web and health endpoint | Tasks, DB, Agent behavior |
| W2 Sandbox | Five manual HRIS/ITSM/IAM/Asset/Mail pages and APIs | Real systems/data, auth, production workflow |
| W3 Arena | Fixed specs, task-only Reset/Seed, DB-only grade | Browser/model-derived success |
| W4 DOM path | Bounded DOM observation, opaque refs, typed actions | Screenshot field or router in W4 APIs |
| W5 visual path | Bounded JPEG, opaque Grounding, typed visual actions | Image storage/path/URL, arbitrary pixels/selectors/code |
| W6 Hybrid Worker | One Browser/Context/Page and one selected current modality | Joined W4/W5 sessions, dual-modal model input |
| W6 Hybrid Agent | Deterministic DOM-first Router, local compression, fake-only total budgets | Learning, cache/history, planner, verifier, recovery, provider egress |
| Acceptance smokes | Independent Reset/Seed and W3 Grade for DOM, Vision, and Hybrid fakes | Fake finish as a success claim |

~~~mermaid
flowchart LR
    Caller["Trusted acceptance caller"] --> Arena["W3 Reset/Seed + Grader"]
    Caller --> DomAgent["W4 DOM Agent"]
    Caller --> VisionAgent["W5 Vision Agent"]
    Caller --> HybridAgent["W6 Hybrid Agent"]
    DomAgent --> Worker["Typed Browser Worker"]
    VisionAgent --> Worker
    HybridAgent --> Worker
    Worker --> Web["Five Sandbox pages"]
    Web --> API["W2 business APIs"]
    API --> DB["Synthetic PostgreSQL"]
    Arena --> DB
~~~

## Quick start

Prerequisite: Docker Compose. Published ports bind to loopback. Browser Worker,
DOM Agent, Vision Agent, and Hybrid Agent have no host port and use internal
Docker networks.

~~~powershell
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
~~~

On a host with the standalone compatible executable:

~~~powershell
docker-compose -f deploy/compose/compose.yaml up --build -d
docker-compose -f deploy/compose/compose.yaml ps
~~~

Open:

- Sandbox web: http://127.0.0.1:5174/hris
- Sandbox API docs: http://127.0.0.1:8001/docs
- W1 control web: http://127.0.0.1:5173
- W1 control API health: http://127.0.0.1:8000/healthz

Run all trusted fake-only acceptance profiles:

~~~powershell
docker compose -f deploy/compose/compose.yaml --profile acceptance run --build --rm acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile vision-acceptance run --build --rm vision-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile hybrid-acceptance run --build --rm hybrid-acceptance-smoke
~~~

The W4 DOM smoke and W5 Vision untouched subrun independently grade untouched
state at 30/100, passed=false. W5's fresh deterministic completion independently
grades 100/100, passed=true. W6 Hybrid similarly proves immediate finish remains
30/100, then uses a fresh Reset/Seed pair for a deterministic DOM-to-Vision
completion that ends finished_ungraded and independently grades 100/100. These
are zero-cost fake circuit/Grade-boundary checks, not DOM, Vision, Hybrid, OCR,
or VLM capability claims.

Stop and remove disposable synthetic state after acceptance:

~~~powershell
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
~~~

## Browser and Agent safety boundary

- Browser Worker runs non-root with a read-only root filesystem, no bind mount
  or Docker socket, all capabilities dropped, no-new-privileges, bounded
  tmpfs/shm/pids, and no database environment.
- A Hybrid task owns one fresh Browser, Context, and Page. It starts DOM-first
  at the fixed visual viewport and never splices independent W4/W5 sessions.
- Every Hybrid response exposes one selected current modality. The Router sees
  only bounded structural counts, truncation, byte size, safe error category,
  trusted route category, and remaining numeric budgets.
- DOM turns use deterministic local compression. Visual turns retain W5's
  current JPEG/grounding envelope. A model never receives full DOM and image
  in the same call.
- Every Hybrid action envelope binds the current session and observation
  generation. Every observation, switch, action success/failure, timeout,
  terminal path, deletion, startup failure, cancellation, and shutdown
  invalidates all DOM and visual references. The Worker rejects wrong-mode,
  stale, forged, selector,
  coordinate, rectangle, code, path, URL, JavaScript, shell, and SQL input.
- Screenshots, DOM/OCR/page/form data, cookies, storage, credentials, tokens,
  and endpoints remain transient and are never written to repository, logs,
  Task Specs, database, or long-term storage.
- Hybrid Agent reaches only Browser Worker on a dedicated internal network. It
  has no Sandbox/Arena/DB/Grader route, credential, model egress, filesystem
  persistence, Docker socket,
  shell, SQL, or JavaScript capability.
- Router/model/page output cannot declare a pass. Agent finish is
  finished_ungraded; only W3 Grade 100/100 is success.

## Local development and quality

Python targets 3.13 and uses uv; frontends use committed npm locks. Playwright
remains pinned to 1.60.0 with Chromium 148.0.7778.96.

~~~powershell
Push-Location apps/browser_worker
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
Pop-Location

Push-Location apps/hybrid_agent
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
Pop-Location
~~~

The complete W1-W6 gate sequence is frozen in
docs/plans/week-06-hybrid-router.md.

## Model authorization and milestone boundary

No real DOM/Vision/Hybrid model, VLM, OCR provider, key, endpoint, or egress is
configured or called by default. Before a real model call, disclose the
provider, exact model, endpoint, prompt/config, selected-modality input
handling, task IDs, retries, and hard call/token/image/DOM/time/cost limits;
then obtain separate explicit user approval.

W6 has no W7 planner DAG, tool matching, verifier, new task template,
checkpoint, recovery, memory, identity, approval, production worker,
monitoring, tracing, or other W7+ behavior. See docs/agent-contract.md and
docs/threat-model.md.

Development occurs only on week/06-hybrid-router. No push, PR, merge, or tag is
authorized. Licensed under the Apache License 2.0.
