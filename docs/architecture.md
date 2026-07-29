# Architecture

## W9 current-state architecture

W9 preserves the W1-W8 service and network topology. Context lives inside the
existing Planning Agent because it is task-local execution input; there is no
new service, database, migration, dependency, or network route. Planning Agent
still reaches only Browser Worker. Recovery Worker still reaches only Temporal
and Planning Agent. Arena and independent Graders remain outside every Agent.

~~~mermaid
flowchart LR
    Caller["Trusted synthetic caller<br/>scope + DB safe fact projection"] --> Context["W9 Context Assembler"]
    BrowserMemory["Current safe browser events"] --> Context
    Session["Closed task-local events"] --> Summary["Deterministic summary"]
    Summary --> Context
    Org["Process-local scoped org memory"] --> Context
    Catalog["Fixed enterprise catalog"] --> Retrieval["Closed lexical/hash retrieval"]
    Retrieval --> Context
    Context --> Ledger["One W7-W9 total ledger"]
    Ledger --> Planning["W7 bounded Planning Agent"]
    Recovery["W8 Recovery Activities"] --> Planning
    Planning --> Browser["Browser Worker"]
    Browser --> Web["Five synthetic Sandbox pages"]
    Web --> DB["Sandbox database"]
    Grader["Independent Grader"] --> DB
~~~

## Five-layer assembly

~~~mermaid
flowchart TD
    A["Validate task/scope/process/phase/as_of"] --> B["Apply exact-scope org-memory mutations"]
    B --> C["1. authoritative task_facts"]
    C --> D["2. current browser_working"]
    D --> E["3. deterministic short_term"]
    E --> F["4. active exact-scope org_memory"]
    F --> G["5. closed enterprise_knowledge retrieval"]
    G --> H["Expiry/trust/source filters"]
    H --> I["Earlier-layer content-hash dedupe"]
    I --> J["Per-layer then total budget"]
    J --> K["Canonical provenance + context hash"]
~~~

Task facts are accepted only with `sandbox_database` source,
`authoritative` trust, exact task/scope owner, snapshot version, and database
snapshot hash. The assembler does not read Arena, Task Spec, expected state,
Grader predicate/checksum, or Reporting result. Lower layers cannot replace a
task fact or declare success.

The context-backed Planning endpoint creates one `TotalBudgetLedger`, assembles
context, then passes that same ledger to the unchanged W7 executor. Planning,
tool matching, browser actions, observations, Verifier calls, context items,
retrieval, summary, and memory usage therefore share one non-resetting task
counter set. The released W8 Planning usage projection copies all W9 counters
into Checkpoints and rejects a decrease; it persists counts only, never semantic
context.

## Retrieval and summary

Enterprise knowledge is a fixed tuple packaged with Planning Agent. A trusted
process/phase maps to one closed category. Each category maps to frozen lexical
terms. Retrieval filters scope, source, trust, version, and explicit UTC
validity; deduplicates content hashes by highest active version; ranks by
lexical score, version, hash, and ID; and emits at most three records. It has no
free string query, embedding, vector store, network, provider, or model.

Short-term summary accepts at most 12 closed safe events. It sorts by fixed
event priority and descending ordinal, deduplicates kind/value pairs, preserves
one present unresolved issue/recent action/failure reason/pending step before
supplements, and emits at most 8 entries/4,096 bytes/1,024 estimated tokens.
Summary hashes cover the complete safe result excluding only the hash field.

## Organization memory

The W9 store is process-local and fake-only. A key is exact synthetic scope plus
memory ID. Records contain closed field/value, source/trust, owner task, version,
status, validity, expiry, and content hash. Upsert increments version by one;
delete creates a tombstone; read omits tombstones/expired records; reset
tombstones only exact task/scope-owned active records. Cross-scope or owner-
changing mutation fails before lookup/write. Process restart reconstructs an
empty fixed fake store, so this is not production durability or W10 identity,
tenant, RBAC, or optimistic locking.

## Preserved W8 boundary

Temporal Workflow history still stores only opaque input, closed operational
state, hashes, topology, and counters. It never receives raw W9 context,
summary, memory values, catalog records, browser content, or task facts. W8
epochs, receipt transactions, retry/recovery/replan caps, cleanup, and
`finished_ungraded` semantics remain unchanged.
