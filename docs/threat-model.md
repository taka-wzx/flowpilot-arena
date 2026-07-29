# W8 threat model - Durable Recovery

## Scope and assets

W8 protects released W1-W7 contracts and data; opaque input confidentiality;
Temporal determinism/history integrity; Checkpoint lineage; non-resetting
budgets; browser epoch/reference isolation; operation receipt atomicity; fault
authority; immutable DAG revision authority; and independent grading.

## Trust boundaries

~~~mermaid
flowchart LR
    Caller["Trusted acceptance caller"] -->|"AES-GCM opaque envelope"| Temporal["Temporal"]
    Temporal --> Recovery["Workflow Worker"]
    Recovery --> Planning["Planning Activities"]
    Planning --> Browser["Browser Worker"]
    Page["Untrusted page/DOM/image/text"] --> Browser
    Browser --> Sandbox["Fixed Sandbox mutation"]
    Sandbox --> DB["Business fact + receipt transaction"]
    Caller --> Grader["Independent Grader"]
    Grader --> DB
~~~

## Threats and controls

| Threat | W8 control | Remaining limitation |
|---|---|---|
| Brief/value leaks into Temporal | AES-256-GCM opaque envelope; decrypt only in Activity; history plaintext gate | Local runtime key injection is not production secret management |
| Nondeterministic replay | Workflow-only closed state/time/Activities; no I/O/random/env/system time; SDK Replayer tests | Version upgrades still require replay gates |
| Forged/tampered Checkpoint | Strict version/transition/caps and canonical parent hash chain | Temporal administrator compromise is outside W8 |
| History/counter growth bypass | 18 Checkpoints, no Continue-As-New, one ledger and 300-second limit | Long-lived production histories deferred |
| Old browser refs survive recovery | Epoch-bound W8 envelope; close and clear before fresh session; Worker revalidates all W6 refs | Browser process compromise is not formally proven contained |
| Post-commit Activity loss duplicates effect | Same deterministic key; receipt and business state in one transaction; replay safe result | Only fixed synthetic mutations are covered |
| Same key reused for changed input | Sandbox recomputes request hash and returns 409 before mutation | No general enterprise API adapter |
| Receipt becomes hidden success signal | Safe outcome only; Verifier remains bounded; Grader ignores receipts | Receipt proves commit, not task success |
| Retry loop/reset after restart | Temporal maximum attempts 2; durable attempt/recovery counters; non-retryable closed failures | Temporal service outage recovery is local only |
| Page/model injects a fault/replan | Fault enum supplied only by trusted harness; Workflow branches on closed reasons; replan authority fixed | W14 malicious-page suite deferred |
| Replan expands tools/permissions | Preserve process/category/values/global catalog/budget; replace failed/not-started descendants only | One deterministic fake replan, not general planning quality |
| Recovery Worker reaches business systems | Separate networks; only Temporal and Planning Agent; no DB/Sandbox/Browser route | Container isolation is not formal verification |
| Temporal DB mixed with business DB | Separate service, credentials, network, volume, retention and cleanup | Local Compose shares the host Docker daemon |
| Cleanup misses crash path | terminal/failure/timeout/cancel/startup/shutdown/replay tests and idempotent close | Host power loss is outside local acceptance |
| Reporting contamination | load/schema/checksum only; no Reporting run/grade/result | Formal evaluation waits for W15 |

## Fail-closed rules

- Unknown schema, state, transition, reason, retry/fault/replan value, epoch,
  hash, key, receipt, or budget count terminates without another business action.
- Validation, permission, idempotency mismatch, permanent fault, and budget
  exhaustion are never transient.
- Negative/inconclusive verification never advances a Checkpoint.
- Page text, DOM, screenshot, OCR, model output, raw objective, and fault
  message cannot authorize a route, tool, operation, retry, replan, or budget.
- Recovery cannot reset W6/W7 limits or reuse any old observation/reference.
- `finished_ungraded` is never interpreted as task success.

## Deferred threats

W9 semantic context/memory; W10 identity/tenant isolation; W11 approvals/audit;
W12 production scheduling/load; W13 telemetry/operational replay; W14 malicious
page suite; W15 external/Reporting evaluation; and W16 deployment/release are
deferred.
