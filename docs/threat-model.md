# W9 threat model - Context, Retrieval, Summary, and Organization Memory

## Scope and assets

W9 protects released W1-W8 contracts; database task-fact authority; context
layer precedence and provenance; synthetic scope/task ownership; fixed catalog
integrity; deterministic summary/retrieval/order/hash; organization-memory
version/delete/expiry semantics; non-resetting budgets; raw-content exclusion;
and independent grading.

## Trust boundaries

~~~mermaid
flowchart LR
    Caller["Trusted synthetic harness"] -->|"scope + DB safe projection"| Context["Context Assembler"]
    Untrusted["Page/email/PDF/DOM/image/OCR/model text"] -->|"data only"| Browser["Browser Worker"]
    Browser -->|"closed safe events"| Context
    Catalog["Reviewed fixed catalog"] --> Context
    Memory["Exact-scope fake memory"] --> Context
    Context --> Planning["Planning + one ledger"]
    Planning --> Browser
    Grader["Independent Grader"] --> DB["Sandbox database"]
~~~

## Threats and controls

| Threat | W9 control | Remaining limitation |
|---|---|---|
| Page/model invents a task fact | Task facts require closed schema, exact task/scope, `sandbox_database`, authoritative trust, version, snapshot hash | Trusted harness attestation is synthetic, not W10 identity |
| Summary/memory overrides database state | Fixed earlier-layer precedence and content-hash dedupe; task facts cannot be mutated by assembler | Semantic contradiction detection beyond closed values is deferred |
| Free query exfiltrates/injects content | Process/phase selects a closed category and frozen terms; no free query/network/embedding | Fixed lexical catalog does not prove real search quality |
| Catalog version/source spoofing | Packaged tuple, strict records, source/trust/validity filter, stable checksum | Repository compromise is outside W9 |
| Nondeterministic retrieval | Dedupe before explicit score/version/hash/ID sort; fixed top-3 | Future catalog changes require a new version/checksum |
| Summary silently drops critical state | Required-kind first selection, explicit counts/source hashes/drop count, fixed caps | Closed safe events do not preserve raw prose |
| Cross-scope memory read/write/delete | Exact actor/record scope equality, owner-task mutation binding, no wildcard/bypass/fallback | Real authentication/tenant authorization waits for W10 |
| Delete physically destroys business data | Organization memory uses a versioned tombstone; no business table is touched | Process-local fake store is not durable production retention |
| Expired browser/memory/knowledge used | Explicit UTC `as_of`, validity and exclusive expiry filtering | Caller clock trust is synthetic |
| Duplicate content changes ordering | Earlier layer wins; within-layer stable key; no unordered iteration | Hash collision resistance relies on SHA-256 |
| Context expands execution budget | Independent layer/total caps and cumulative existing ledger; no W6-W8 cap increases | Context quality under very small budgets is not evaluated |
| Raw content leaks into history/logs | Schemas accept closed safe values; W8 persists W9 counts only; evidence prints hashes/counts/codes | In-process runtime request contains synthetic brief/values as before |
| Context claims task success | No success/passed/score field in context; finish remains ungraded; independent Grader only | Grader correctness remains the released synthetic boundary |
| Ablation contaminates Reporting | Frozen profiles run Development only; Reporting is not executed | Formal causal claims wait for W15 |

## Fail-closed rules

- Unknown schema/version/field/layer/category/source/trust/status/ablation/scope,
  non-UTC time, invalid hash, owner mismatch, or cross-scope access is rejected.
- A context request without at least one authoritative task fact is rejected.
- Expired browser, organization, and enterprise records are omitted; a lower
  layer never fills in a missing authoritative fact.
- An oversized single item is rejected. Task-ledger item/byte/token/retrieval/
  summary/memory exhaustion stops the W9 run before another Planning action.
- Page/email/PDF/DOM/image/OCR/model text cannot select query, layer, source,
  trust, phase, scope, memory mutation, tool, route, action, permission, budget,
  retry, recovery, replan, or success.
- W8 only persists numeric W9 high-water usage. Semantic context never enters a
  Checkpoint or Temporal history.
- `finished_ungraded` is never interpreted as success.

## Deferred threats

W10 authentication, real tenant isolation, RBAC, optimistic locking, durable
multi-user memory, and identity-bound scope; W11 approval/audit; W12 production
scheduling/load/storage; W13 telemetry; W14 malicious-page suite; W15 external
benchmark/formal Reporting; and W16 deployment/release remain deferred.
