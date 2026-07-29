# FlowPilot Arena

> A governed enterprise computer-use Agent project and a separate resettable
> synthetic evaluation environment.

**Current status: local W9 - Context, Retrieval, Summary, and Organization
Memory, based on released W8.** W9 adds five ordered context layers,
deterministic fixed-catalog retrieval, deterministic task-local summary,
scope-bound synthetic organization memory, a reproducible Context Assembler,
five Development-only ablations, and cumulative context accounting.
Independent database-fact grading remains the only success authority.

W8 PR #30 merged at `9ecc31f3e525ae57260bc47ddab5d1d8c1baba6f`.
Its 17-job PR CI and 17-job post-merge main CI passed on their first attempts;
annotated tag `w08-recovery` and release `v0.2.0 - Hybrid + Recovery` are
published. W9 does not modify or republish that baseline.

## Current architecture

| Component | W9 responsibility | Deliberately absent |
|---|---|---|
| W1-W3 | Control skeleton, synthetic Sandbox, immutable Arena/Graders | Real systems/data and Agent-derived success |
| W4-W6 | Isolated Browser Worker and DOM/Vision/Hybrid baselines | Arbitrary browser/API/code capability |
| W7 Planning | Immutable bounded DAG, matcher, Verifier, total ledger | Arena/DB/Grader/provider access |
| W8 Recovery | Deterministic Temporal replay, Checkpoints, epochs, receipts | Semantic memory in Workflow history |
| W9 Context | Five strict layers, fixed retrieval/summary/memory/assembler | Vector DB, embedding, provider, generic memory framework |

~~~mermaid
flowchart LR
    Trusted["Trusted synthetic caller<br/>DB safe fact projection"] --> Context["W9 Context Assembler"]
    Catalog["Fixed enterprise catalog"] --> Context
    Memory["Scoped fake organization memory"] --> Context
    Context --> Planning["W7 Planning Agent + one total ledger"]
    Recovery["W8 Recovery Activities"] --> Planning
    Planning --> Browser["Browser Worker"]
    Browser --> Sandbox["Five synthetic pages"]
    Sandbox --> DB["Sandbox PostgreSQL"]
    Grader["Independent Grader"] --> DB
~~~

W9 remains inside the existing Planning Agent and adds no service, network
route, migration, or dependency. Planning Agent still reaches only Browser
Worker. Recovery Worker still reaches only Temporal and Planning Agent.

## Context and safety boundary

The fixed layer order is:

1. authoritative `task_facts` from a trusted synthetic database projection;
2. current, expiring `browser_working` safe events;
3. deterministic task-local `short_term` summary;
4. versioned, expiring, tombstoned `org_memory`; and
5. versioned `enterprise_knowledge` from a fixed local catalog.

Every emitted item carries source, trust, version, validity/expiry, content
hash, bytes, and deterministic token estimate. Task facts always win duplicate
resolution. Memory, page content, summaries, model output, and knowledge cannot
override database facts or independent grading.

- Retrieval uses only closed query categories, fixed lexical terms, fixed
  top-3 output, deterministic version/trust/hash ordering, and no free query,
  vector database, embedding, network, or model.
- Short-term summary uses closed safe events and fixed priority/dedupe/truncate
  rules. It cannot mutate facts or create hidden cross-task conversation memory.
- Organization memory is process-local and fake-only. Exact synthetic scope is
  required for reads/writes/deletes/reset; this is not a W10 tenant/RBAC claim.
- Whole context is capped at 32 items, 16,384 canonical bytes, and 4,096
  estimated tokens. Each layer has a smaller independent cap.
- Context/retrieval/summary/memory counters join the existing non-resetting
  ledger and W8 safe durable high-water projection. No W6-W8 cap is raised.
- Page, email, PDF, DOM, screenshot, OCR, form, and model text is untrusted and
  cannot choose context authority, query, tool, route, action, permission,
  budget, scope, write/delete, or success.
- Agent finish remains `finished_ungraded`; only the database-fact Grader
  decides success.

## Local start and deterministic acceptance

Python targets 3.13 and uses uv. Temporal Python SDK remains 1.30.0 and local
Temporal Server remains 1.31.2. Inject a temporary local W8 test key only for
Compose; never commit or log it.

~~~powershell
$env:RECOVERY_ENVELOPE_KEY = '<runtime-only base64 key>'
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
docker compose -f deploy/compose/compose.yaml --profile acceptance run --build --rm acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile vision-acceptance run --build --rm vision-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile hybrid-acceptance run --build --rm hybrid-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile planning-acceptance run --build --rm planning-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile recovery-acceptance run --build --rm recovery-acceptance-smoke
docker compose -f deploy/compose/compose.yaml --profile context-acceptance run --build --rm context-acceptance-smoke
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
Remove-Item Env:RECOVERY_ENVELOPE_KEY
~~~

The W9 smoke runs the frozen five-profile ablation matrix, rejects cross-scope,
untrusted-field, and over-budget requests, runs one Development Joiner/Mover/
Leaver through context-backed Planning, and independently grades each at 100.
It executes no Reporting and makes zero real model/provider/OCR/VLM/embedding
calls at zero actual cost.

Exact local gates are in [AGENTS.md](AGENTS.md), scope is in
[the W9 contract](docs/agent-contract.md), design is in
[ADR 0009](docs/adr/0009-w9-context.md), and implementation stages are in
[the W9 plan](docs/plans/week-09-context.md).

## Evaluation and release discipline

W3 and W7 catalogs/checksums/splits remain immutable. W9 ablations run only on
deterministic synthetic Development data. Validation may run once only after
the matrix and all parameters freeze. Reporting is load/schema/checksum
validated only and is not executed before W15.

W9 remote delivery is not authorized by default: no push, PR, merge, tag,
Release, or remote CI. If later authorized, the tag is `w09-context`; W9 does
not create `v0.3.0` because that release belongs to W12.

Licensed under Apache-2.0.
