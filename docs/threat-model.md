# W7 threat model - Bounded Planning DAG

## Scope and assets

W7 protects all released W1-W6 code/contracts; immutable W3 specs/checksums;
W7 catalog/manifests; synthetic task state and deterministic grades; one W6
Hybrid session and its current opaque references; immutable plan identity and
topology; tool authority; Verifier state; and total-ledger integrity.

Raw brief, objective text, DOM, screenshot, OCR, page/form content, and model
output are untrusted transient data. W7 adds no persistent Agent asset and no
external model call.

## Trust boundaries

~~~mermaid
flowchart LR
    Brief["Trusted finite wrapper<br/>bounded brief + supplied values"] --> Planner["Deterministic fake Planner"]
    Page["Untrusted page / DOM / image / text"] --> Worker["Strict Browser Worker"]
    Planner --> DAG["Frozen validated DAG"]
    DAG --> Matcher["Four-way tool intersection"]
    Worker --> Matcher
    Matcher --> Worker
    Worker --> Verifier["Runtime Verifier<br/>current evidence only"]
    Caller["Trusted acceptance caller"] --> Arena["Reset/Seed + independent Grader"]
    Caller --> Planner
    Arena --> DB["Synthetic PostgreSQL"]
~~~

## Threats and controls

| Threat | W7 control | Remaining limitation |
|---|---|---|
| Objective/page/model grants a tool | Closed operation and four-way intersection; candidate strings cannot create catalog entries | Fixed synthetic pages, W14 malicious suite deferred |
| Cyclic/oversized/malformed plan | Strict unknown-field rejection; single root; cycle/reachability and node/edge/depth/width/dependency/byte caps | No runtime replanning |
| Dependency bypass | Explicit step state machine; execute only after every dependency is verified | In-process logic, covered deterministically |
| Plan replacement during run | One frozen plan object and SHA-256 identity per run | No checkpoint persistence |
| Task ID leaks hidden fixture | Planner behavior ignores task ID and accepts only finite process/category plus supplied values | Trusted caller still knows catalog metadata |
| Dynamic/arbitrary tool discovery | Versioned fixed catalog only; unknown candidates safely rejected | Catalog changes require a new contract/version |
| Stale cross-step reference | Verification probes and every Worker observation/action invalidate old refs; Worker revalidates envelope | Page races fail safely |
| Verifier becomes Grader | No Arena/DB/expected/predicate/checksum input or network; closed statuses only | Runtime verification is intentionally weaker than final grading |
| Planner/finish self-declares success | Result has no success/pass/score; finish is finished_ungraded | Independent Grader required after cleanup |
| Budget reset by planning/probe/switch/failure | One monotonic ledger object, before/after charging, no replacement API | W12 concurrency/load behavior deferred |
| Mover/Leaver causes delete/arbitrary patch | Exact employee-owned transitions and prior-state checks only | API authorization remains local synthetic until W10/W11 |
| Planning Agent privilege expansion | Dedicated internal Worker-only network; no DB/Arena/Sandbox/provider/mount/socket/key | Container hardening is not formal proof |
| Reporting contamination | Reporting generation/load/checksum freeze only; no Agent/grade/result inspection | Formal evaluation waits for W15 |
| Raw sensitive persistence | No Agent persistence; safe counters/hashes/reasons only | Process memory is not forensic zeroization |

## Deterministic control rules

- Objective and postcondition display strings never authorize operations.
- Risk level is non-authorizing metadata and cannot manufacture approval.
- Retry is only `no_retry`; fallback is only `stop` or `escalate`.
- Router inputs remain the released W6 closed structural signals/categories,
  action outcomes, and budgets; plan/page/model text cannot direct routing.
- Worker navigation stays on the five fixed synthetic paths and actions retain
  released current-reference validation.
- Runtime Verifier negative/inconclusive results never become verified.
- Reset/Seed and grading remain outside every Agent service.

## Deferred threats

W8 recovery/checkpoint/idempotency/fault/retry risks; W9 context/memory;
W10 identity/tenancy; W11 approval/audit; W12 production/load; W13 telemetry;
W14 full malicious-page evaluation; W15 external/Reporting evaluation; and W16
release/deployment remain deferred.
