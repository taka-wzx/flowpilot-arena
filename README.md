# FlowPilot Arena

> A governed enterprise computer-use Agent project and a separate synthetic
> evaluation environment.
> 面向企业级 Computer-Use Agent 与独立合成评测环境的受治理项目。

**Current status: W7 - Bounded Planning DAG.** Released W4 DOM-only, W5
Vision-only, and W6 Hybrid paths remain intact. W7 adds one immutable bounded
task DAG, deterministic closed-set tool matching, a single monotonic W6+W7
budget ledger, step-level runtime verification, a separate fake-only Planning
Agent, and a frozen 30-template/90-instance synthetic JML catalog. Independent
database-fact grading remains the only success authority.

## What W7 contains

| Component | Current capability | Deliberately absent |
|---|---|---|
| W1-W3 | Control skeleton, five-app Sandbox, immutable W3 Arena/Grader | Real systems/data and browser/model-derived success |
| W4 DOM | Bounded DOM observation, opaque refs, typed actions | Vision/router/planner in W4 API |
| W5 Vision | Bounded JPEG, opaque Grounding, typed actions | Storage/path/URL, arbitrary pixels/selectors/code |
| W6 Hybrid | One Browser/Context/Page, selected modality, deterministic Router/compression | Joined sessions, dual-modal call, planner/recovery |
| W7 Planning Agent | Frozen bounded DAG, deterministic topology/matcher/Verifier/ledger | Arena/DB/Grader/provider access, retry/replanning/checkpoint |
| W7 JML | 12 Joiner, 8 Mover, 10 Leaver templates; three stable variants each | Real people/data, Reporting execution, external benchmark |
| Sandbox increment | Exact transfer/disable/close/revoke/release transitions | Migration, physical delete, arbitrary patch, approval bypass |

~~~mermaid
flowchart LR
    Caller["Trusted acceptance caller"] --> Arena["W3 + W7 Reset/Seed and independent Graders"]
    Caller --> Planning["W7 Planning Agent"]
    Caller --> Hybrid["W6 Hybrid Agent regression"]
    Planning -->|"internal planning-worker"| Worker["Typed Browser Worker"]
    Hybrid --> Worker
    Worker --> Web["Five synthetic Sandbox pages"]
    Web --> API["Strict business APIs"]
    API --> DB["Synthetic PostgreSQL"]
    Arena --> DB
~~~

Planning Agent receives only a finite process/category, bounded caller-rendered
brief, and strict supplied values. Objective/page/model text cannot authorize
an operation or tool. Effective tools are the intersection of the global
catalog, current step, current page/modality Worker allowlist, and remaining
budget. Runtime Verifier cannot read task specs, expected state, database, or
grader facts. Agent finish is always `finished_ungraded`.

## Quick start

Prerequisite: Docker Compose. Published W1/Sandbox ports bind to loopback.
Browser and Agent services have no host port and use internal networks.

~~~powershell
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
~~~

Open the synthetic Sandbox at <http://127.0.0.1:5174/hris> and its local API
documentation at <http://127.0.0.1:8001/docs>.

Run deterministic fake-only acceptance:

~~~powershell
docker compose -f deploy/compose/compose.yaml --profile acceptance run --build --rm acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile vision-acceptance run --build --rm vision-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile hybrid-acceptance run --build --rm hybrid-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile planning-acceptance run --build --rm planning-acceptance-smoke
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
~~~

The W7 smoke must prove invalid DAG/tool/Verifier rejection, actual
multi-dependency execution through one W6 Hybrid session, non-resetting budget
accounting, cleanup, ungraded finish, and independent grades. Fake runs prove
wiring and isolation only; they are not real planning, Verifier, DOM, Vision,
Hybrid, OCR, or VLM capability claims.

## Safety boundary

- Planning Agent runs non-root, read-only, cap-dropped, no-new-privileges,
  tmpfs/pids-bounded, without host port/mount/socket/key/provider egress, and
  connects only to Browser Worker.
- One Planning run uses one fresh W6 Hybrid Browser, Context, and Page. Every
  observation/action/probe/switch/terminal path invalidates old references;
  Browser Worker revalidates current session/generation/modality/reference.
- Plans are strict and immutable: 16 nodes, 24 edges, depth 8, width 8, four
  dependencies per node, and 32,768 canonical UTF-8 bytes maximum.
- Unknown fields, pages, operations, actions, tools, dependencies, illegal
  transitions, selectors, XPath, coordinates, arbitrary URLs, upload/download,
  Cookie/Local Storage, Shell, SQL, JavaScript, code, MCP, and plugins fail closed.
- Runtime Verifier is not Grader. `finish` cannot return success, pass, or score.
- Raw brief/plan/DOM/image/OCR/page/form data, credentials, tokens, endpoints,
  and machine paths are not persisted. Evidence uses safe hashes/counts/reasons.
- Default tests/CI/Compose make zero external model/OCR/VLM calls and incur zero
  actual model cost.

## Local development

Python targets 3.13 and uses uv; frontends use committed npm locks. Run Ruff,
format check, Mypy, and pytest for control API, Sandbox API, Browser Worker,
DOM/Vision/Hybrid/Planning Agents; run npm ci, lint, typecheck, tests, and build
for both frontends; then run Compose/Alembic/catalog/smoke/secret/diff gates.
The exact sequence is frozen in [AGENTS.md](AGENTS.md) and
[the W7 plan](docs/plans/week-07-planning.md).

## Model and milestone boundary

No real W7 Planner/Verifier/model, OCR, or VLM provider/key/endpoint/egress is
authorized. Any real call requires a new exact disclosure and separate user
approval. Validation is not used for repeated tuning; Reporting is generated
and checksum-frozen only.

Development occurs only on `week/07-planning`. No push, PR, merge, tag,
release, remote CI trigger, or W8 work is authorized. W8 alone may add retry,
Temporal, checkpoints, idempotency, recovery, fault injection, and runtime
partial replanning. Licensed under Apache-2.0.
