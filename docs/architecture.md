# Architecture

## W7 current-state architecture

W7 preserves released W1 control paths, W2 five-module synthetic Sandbox, W3
Arena/Grader, W4 DOM Agent, W5 Vision Agent, and W6 Hybrid Agent. It adds a
fourth independent Agent service for one-shot bounded planning and an
independent W7 JML catalog inside the synthetic Arena management boundary.

~~~mermaid
flowchart LR
    Caller["Trusted acceptance caller<br/>Reset/Seed · brief · independent grade"] --> Arena["W3 Arena + W7 JML management"]
    Caller --> Dom["W4 DOM Agent"]
    Caller --> Vision["W5 Vision Agent"]
    Caller --> Hybrid["W6 Hybrid Agent"]
    Caller --> Planning["W7 Planning Agent<br/>Planner · Matcher · Verifier"]
    Dom --> Worker["Isolated Browser Worker"]
    Vision --> Worker
    Hybrid --> Worker
    Planning -->|"dedicated internal planning-worker"| Worker
    Worker --> Web["Five Sandbox pages"]
    Web --> API["Synthetic business APIs"]
    API --> DB["Synthetic PostgreSQL"]
    Arena --> DB
~~~

Acceptance orchestration alone may read immutable task metadata, compare
Reset/Seed results, render a human brief/supplied values, and call an
independent Grader. It is profile-only and is not an Agent tool.

| Boundary | Responsibility | Deliberately excluded |
|---|---|---|
| Browser Worker | Released W4-W6 one-session observations/actions and reference lifecycle | Plans, task facts, Grader, arbitrary browser control |
| Planning Agent | Frozen DAG, topology, matching, one ledger, runtime Verifier, deterministic fake execution | Sandbox/Arena/DB/Grader/provider/persistence/recovery |
| W7 JML Arena package | Versioned catalog/generator, task-owned Reset/Seed, DB-fact Grader | Browser/model control and Agent access |
| Sandbox API/UI | Five exact typed state transitions | Delete, generic patch, arbitrary data mutation, approval |
| W3/W7 Graders | Sole task-success decisions from owned DB facts | Page, observation, plan, model, or finish trust |

## Planning lifecycle

~~~mermaid
sequenceDiagram
    participant C as Trusted caller
    participant P as Planning Agent
    participant W as Browser Worker
    participant V as Runtime Verifier
    participant G as Independent Grader

    C->>P: finite process/category + bounded brief + supplied values
    P->>P: generate once, validate/freeze DAG, charge one ledger
    P->>W: create one W6 Hybrid session
    loop deterministic topological steps
        P->>P: require dependencies verified
        P->>P: match global ∩ step ∩ page/mode ∩ budget
        P->>W: current typed action envelope
        W-->>P: current action result + current observation
        P->>W: verification observation probe
        W-->>V: current observation (old refs invalidated)
        V-->>P: verified / not_verified / inconclusive
    end
    P->>W: finish then unconditional delete
    P-->>C: finished_ungraded + safe counters/hashes
    C->>G: independent database-fact grade
~~~

The validated Pydantic DAG is immutable and task-local. A lexical topological
order is calculated once. A step can execute only after every dependency is
verified. Verification failure stops or escalates; there is no retry or
runtime replanning.

## Authority and data flow

Planner consumes only a trusted finite process/category, bounded caller-
rendered brief, and strict supplied values. It does not receive a Task Spec,
expected state, fixture map, Grader predicate/checksum, database fact, DOM,
image, or Reporting result during plan generation.

The closed operation field, never objective prose, maps to exact step actions.
Matcher computes a four-way intersection before a current opaque Worker
reference can be selected. Browser Worker revalidates current session,
generation, modality, observation, reference, and action.

Runtime Verifier sees current observation, current action-result summary,
trusted step conditions, and current ledger only. It cannot declare task
success. Planning Agent finish remains `finished_ungraded`.

## JML data and Sandbox state

The W7 catalog is separate from immutable W3 resources. Thirty templates
generate three deterministic variants each. Task-level ownership confines
Reset/Seed and grading. Reporting artifacts are generated/checksummed/frozen
only and cannot influence W7 planning.

Existing database columns represent exact transitions: HRIS transfer/disable,
ITSM close, IAM revoke, Asset release, and Mail disable. No schema migration or
physical deletion is added. Planning Agent reaches these only through fixed UI
controls and Browser Worker.

## Isolation and W8 boundary

Planning Agent is non-root, read-only, cap-dropped, no-new-privileges,
tmpfs/pids-bounded, has no host port/mount/socket/credential, and joins only
`planning-worker` with Browser Worker. W7 has no retry, checkpoint, recovery,
Temporal, idempotency, fault injection, or partial replanning.
