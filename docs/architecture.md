# Architecture

## W8 current-state architecture

W8 preserves W1-W7 and adds one isolated durable orchestration boundary.
Recovery Workflow Worker does not execute browser or business operations. It
replays deterministic safe state and calls Planning Agent Activities; Planning
Agent alone reaches Browser Worker; Browser Worker alone drives the fixed
synthetic pages. Arena/Grader remain outside every Agent service.

~~~mermaid
flowchart LR
    Caller["Trusted W8 acceptance caller<br/>encrypt · start · independent grade"]
    Caller -->|"opaque ciphertext + closed fault"| Temporal["Temporal Server 1.31.2"]
    Temporal -->|"temporal-control"| Recovery["Recovery Workflow Worker<br/>Workflow + Activities"]
    Recovery -->|"recovery-planning"| Planning["W7 Planning Agent<br/>W8 recovery/step API"]
    Planning -->|"planning-worker"| Browser["Browser Worker<br/>epoch + current refs"]
    Browser -->|"browser-sandbox"| Web["Five synthetic Sandbox pages"]
    Web --> API["Typed Sandbox API<br/>business fact + receipt transaction"]
    API --> SandboxDB["Synthetic PostgreSQL"]
    Temporal --> TemporalDB["Independent Temporal PostgreSQL"]
    Caller --> Arena["W3/W7 Reset/Seed + Grader"]
    Arena --> SandboxDB
~~~

Temporal Server joins two networks: `temporal-db` with only its persistence
database, and `temporal-control` with Recovery Worker and profile-only trusted
acceptance. Recovery Worker additionally joins `recovery-planning` with
Planning Agent. It cannot resolve Browser Worker, Sandbox Web/API, Arena,
Grader, or either database. Planning Agent retains only `planning-worker` for
Browser Worker. No Temporal UI or host port exists.

## Durable lifecycle

~~~mermaid
sequenceDiagram
    participant C as Trusted caller
    participant T as Temporal
    participant R as Recovery Worker
    participant P as Planning Agent
    participant B as Browser Worker
    participant S as Sandbox transaction
    participant G as Independent Grader

    C->>C: validate and AES-GCM encrypt strict input
    C->>T: start workflow with opaque envelope
    T->>R: replay deterministic workflow state
    R->>P: Activity decrypts and starts epoch 1
    P->>B: fresh Browser/Context/Page + observation
    loop lexical remaining steps
        T->>R: schedule bounded step Activity
        R->>P: strict step request + latest Checkpoint
        P->>B: current epoch/generation/ref action
        B->>S: fixed mutation + key/hash headers
        S-->>B: committed or receipt replay safe code
        B-->>P: current observation + safe receipt result
        P-->>R: closed verified step result
        R->>R: update ledger and hash Checkpoint
    end
    Note over R,P: closed fault may force retry, fresh epoch, or one replan
    R-->>C: finished_ungraded + safe hashes/counters
    C->>G: independent database-fact grade
~~~

The Workflow never sees decrypted business input. Only Activity code decrypts
immediately before its Planning call and returns safe hashes/counters. Planner,
Browser, persistence, fault injection I/O, and cleanup are Activities.

## Checkpoint and browser epochs

A Checkpoint is a canonical safe-state projection, not a browser snapshot. It
contains immutable plan/revision hashes, topology and safe step states,
verified/completed/remaining IDs, session epoch, deadline and total usage,
retry/recovery/replan/fault counters, receipt hashes, and parent/current hash.
It contains no handle, observation/reference, page/model content, task spec, or
grader data.

Epoch 1 is the no-fault path. Each recovery first closes/invalidates current
state, then opens one wholly fresh Browser, Context, and Page. Epochs 2 and 3
are the only recovery epochs. Planning resumes from the latest verified
Checkpoint and re-observes current Sandbox facts; it never combines epochs.

## Idempotency transaction

For a fixed W8 mutation click, Browser Worker temporarily attaches only the
validated W8 task/key/hash/revision/step/operation headers to the exact
same-origin request. Sandbox validates the typed body, recomputes the canonical
hash, and in one database transaction either applies the business change plus
receipt or returns the existing receipt. Hash mismatch returns 409 before the
business change. Grader reads business facts only and ignores receipts.

## Failure and replan policy

Recovery order is fresh observation, one transient retry, new epoch, verified
Checkpoint resume, one local replan, then escalation/safe failure. All attempts,
faults, receipts, replays, Checkpoints, epochs, and revisions accumulate in the
same total ledger. Revision 2 may replace only the failed and not-started
descendant subgraph; completed nodes and side effects remain immutable.

## W9 boundary

W8 adds no context builder, memory, summary, retrieval, cache, or cross-task
history. Temporal durable state is strictly operational safe state and cannot
be used as semantic memory.
