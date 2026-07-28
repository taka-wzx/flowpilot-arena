# FlowPilot Arena

> A governed enterprise computer-use Agent project and a separate resettable
> synthetic evaluation environment.

**Current status: W8 - Durable Recovery, based on released W7.** W8 adds
deterministic Temporal orchestration, opaque encrypted durable input, verified
Checkpoints, fresh browser session epochs, transactional operation receipts,
bounded retry/fault recovery, and one bounded partial DAG revision. Independent
database-fact grading remains the only success authority.

W7 PR #29 merged at `0aa1349ffee0bfabdb8c9f02787f37dfe7f7c029` after its
15-job PR CI and 15-job post-merge main CI passed. Tag `w07-planning` is
published, and W8 was restacked on that exact baseline without a tree change.

## Current architecture

| Component | W8 responsibility | Deliberately absent |
|---|---|---|
| W1-W3 | Control skeleton, synthetic Sandbox, immutable Arena/Graders | Real systems/data and Agent-derived success |
| W4-W6 | Isolated Browser Worker and DOM/Vision/Hybrid baselines | Arbitrary browser/API/code capability |
| W7 Planning | Immutable bounded DAG, matcher, Verifier, total ledger | Arena/DB/Grader/provider access |
| Temporal | Durable deterministic safe orchestration state | UI/cloud/production cluster/plaintext business input |
| Recovery Worker | Workflow replay and fixed Planning Activities | Browser/Sandbox/Arena/Grader/DB/model route |
| Sandbox receipt | Atomic fixed mutation plus safe idempotency receipt | Raw payload, general API proxy, rollback/compensation |

~~~mermaid
flowchart LR
    Caller["Trusted acceptance caller"] -->|"opaque AES-GCM envelope"| Temporal["Temporal 1.31.2"]
    Temporal --> Recovery["Recovery Worker"]
    Recovery --> Planning["Planning Agent W8 API"]
    Planning --> Browser["Browser Worker epoch"]
    Browser --> Web["Five synthetic pages"]
    Web --> API["Typed business + receipt transaction"]
    API --> DB["Sandbox PostgreSQL"]
    Caller --> Grader["Independent Grader"]
    Grader --> DB
~~~

The Workflow sees ciphertext, closed states, opaque IDs/hashes, topology, and
counters only. It performs no HTTP, database, filesystem, environment, random,
system-time, Planner/model, Browser, Sandbox, Arena, or Grader I/O. Activities
decrypt the runtime envelope and call only Planning Agent.

## Safety boundary

- Normal execution uses epoch 1 with one fresh Browser/Context/Page. Recovery
  may create epochs 2 and 3 only, after invalidating every old session,
  generation, observation, element, screenshot, and grounding reference.
- Checkpoints are canonical safe-state hashes, limited to 18 and 65,536 bytes;
  they contain no browser handle/ref, page/model content, Task Spec, or grader
  data.
- The `w8_operation_receipts` row and fixed synthetic business mutation commit
  in one transaction. Same key/hash replays; changed hash is rejected before a
  side effect. Graders ignore receipts.
- Activity retry is at most once and only for a closed transient reason.
  Retry/replay/recovery/fault/receipt/replan usage joins the existing
  non-resetting W6/W7 total ledger.
- One immutable revision may replace only a failed step and not-started
  descendants. Completed steps/effects, authority, and budgets cannot expand.
- Runtime Verifier is not Grader. Agent finish remains `finished_ungraded`.
- Default tests, CI, and Compose are deterministic fake-only and make zero real
  model/OCR/VLM calls at zero actual model cost.

## Local start and acceptance

Python targets 3.13 and uses uv. Temporal Python SDK is fixed at 1.30.0;
Temporal Server is fixed at 1.31.2. Before starting W8 services, inject a
temporary local 32-byte base64 AES key in `RECOVERY_ENVELOPE_KEY`; do not store
it in the repository or shell history.

~~~powershell
$env:RECOVERY_ENVELOPE_KEY = '<runtime-only base64 key>'
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
docker compose -f deploy/compose/compose.yaml --profile acceptance run --build --rm acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile vision-acceptance run --build --rm vision-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile hybrid-acceptance run --build --rm hybrid-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile planning-acceptance run --build --rm planning-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile recovery-acceptance run --build --rm recovery-acceptance-smoke
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
Remove-Item Env:RECOVERY_ENVELOPE_KEY
~~~

Published Control/Sandbox ports bind to loopback. Browser, Agent, Recovery, and
Temporal services have no host port. The W8 smoke must scan complete raw
Temporal history for plaintext sentinels and assert zero duplicate side
effects before it can pass.

The exact local gates are in [AGENTS.md](AGENTS.md), the scope in
[the W8 contract](docs/agent-contract.md), and the staged plan in
[the W8 plan](docs/plans/week-08-recovery.md).

## Data and milestone discipline

W3 and W7 catalogs/checksums/splits remain immutable. Development may exercise
the fault matrix. Validation may run once only after freeze. Reporting is
loaded/schema/checksum-validated only and is not executed before W15.

W8 remote delivery follows one quota-conscious path: one feature push, one PR
CI, one post-merge main CI, tag `w08-recovery`, and roadmap release `v0.2.0`.
Superseded or successful workflows are not rerun. No real model call or W9 work
is authorized. Licensed under Apache-2.0.
