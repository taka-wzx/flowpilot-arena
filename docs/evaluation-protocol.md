# Evaluation protocol

## Purpose and preserved boundary

W9 evaluates deterministic fake-only context construction, not real retrieval,
memory quality, production tenancy, or model reasoning. W3/W7 database-fact
Graders remain the only success authority. No real model, provider, OCR, VLM,
embedding, vector database, or cloud call is authorized.

W3 ten-task catalog/checksum/6-2-2 split, W7 30-template/90-instance catalog,
12/8/10 processes, 18/6/6 split, stable manifests/checksums, W4 DOM, W5 Vision,
W6 Hybrid, W7 Planning, W8 Recovery, Reset/Seed, receipts, and Graders remain
unchanged.

## Unit and schema protocol

Tests cover:

1. strict/frozen/extra-forbid W9 request/result, five-layer item, fact, browser,
   event, summary, memory, knowledge, retrieval, budget, and ablation schemas;
2. canonical JSON/hash replay, JSON round-trip, stable catalog checksum, closed
   enums, exact UTC validity, and rejection of unknown/raw fields;
3. task-fact source/trust/owner validation and earlier-layer precedence;
4. browser expiry and exclusion of stale working memory;
5. summary priority, required-kind preservation, dedupe, truncation, source/
   compression counts, deterministic hash, and no task-fact mutation;
6. retrieval category routing, lexical score, exact/global scope, version,
   source, trust, expiry, dedupe-before-sort, fixed top-3, and stable ordering;
7. organization-memory monotonic version, field identity, expiry, tombstone,
   exact-owner reset, cross-task mutation rejection, and cross-scope rejection;
8. per-layer and total item/byte/token limits, cumulative retrieval/summary/
   memory counters, fail-closed exhaustion, and no W6-W8 cap increase;
9. all five frozen ablations and deterministic replay; and
10. W8 durable Planning high-water projection containing W9 counts only and
    rejecting any counter decrease.

## Frozen Development matrix

| Profile | task facts | browser | short term | org memory | enterprise |
|---|---:|---:|---:|---:|---:|
| full_five_layer | on | on | on | on | on |
| task_facts_only | on | off | off | off | off |
| no_short_term | on | on | off | on | on |
| no_enterprise_retrieval | on | on | on | on | off |
| no_organization_memory | on | on | on | off | on |

No browser-working ablation is admitted. Every profile retains authoritative
task facts. This matrix, catalog, ranking, top-k, validity window, and all
budgets freeze before any Validation run.

## Compose Development protocol

After equal Reset/Seed, W9 Context acceptance:

- verifies W7 catalog/split/Reporting checksums without running Reporting;
- runs all five ablations and checks expected layer/counter absence;
- replays a task-facts-only request and requires byte-equivalent context;
- rejects cross-scope actor, untrusted extra page instruction, and a deliberately
  insufficient context-item budget;
- runs one W7 Development Joiner, Mover, and Leaver through the additive
  context-backed Planning endpoint;
- requires `finished_ungraded`, cumulative W9 plus W7 counters, zero cost, and
  no success claim in the Agent/context result; and
- invokes the independent database-fact Grader after execution and requires
  100 for each task.

W4-W8 Compose smokes run separately and unchanged. Immediate finish continues
to fail independent grading in released regression. Alembic remains at W8 head
`20260728_0003`; W9 adds no migration.

## Data and checksum freeze

The W9 enterprise catalog is code-local, synthetic, Apache-2.0 repository data.
Its schema version, nine records, six closed categories, intentional
version-dedup pairs, UTC validity, query terms, and checksum are frozen in
`docs/data/week-09-context-data.md`. Evidence records only checksums, hashes,
counts, closed codes, ablation names, and grades.

## Validation and Reporting discipline

Development may rerun while implementing. After parameters freeze, Validation
may run at most one preregistered final context check; evidence states whether
it ran. Reporting is limited to generation/load/schema/checksum validation. It
receives no Reset, Seed, Agent, context, memory, retrieval, grade, or result
execution/inspection before W15.

## Interpretation

Passing results establish strict deterministic schemas, provenance, ordering,
hashing, scope rejection, fake memory lifecycle, budget accumulation,
context-backed fake Planning, cleanup, and independent grading on fixed pages.
They do not prove real enterprise retrieval, semantic memory quality, prompt-
injection resistance, authenticated tenancy, durable production storage,
external generalization, causal ablation benefit, production SLOs, or ROI.

## Real-call and W10 boundary

Real model/provider/OCR/VLM/embedding calls remain not run at 0 calls and 0
cost. W10 identity, users, organizations, RBAC, real tenant isolation, durable
authorized memory, and optimistic locking are outside W9.
