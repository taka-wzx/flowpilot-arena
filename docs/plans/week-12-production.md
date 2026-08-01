# Week 12 implementation plan - Production Control Plane

## Authority and stop condition

Work only on `week/12-production` from W11 merge
`84336fdc1dd056110b2dfb32383ce938361bf316`. Exact scope, values, workload,
paths, and stop conditions are in `docs/agent-contract.md`. Complete one local
W12 commit and stop. No remote delivery or W13 work is authorized.

## Frozen outcomes

| Area | W12 outcome | Deliberate limit |
|---|---|---|
| API | authenticated 202 admission, strict idempotency and run ETags | no synchronous Browser/Planning execution |
| Approval | W11 claim and run/outbox in one transaction | raw material remains Control API memory only |
| Dispatch | persistent 64/32 outbox and organization round robin | no caller priority or broker |
| Worker | one private service, four slots, 30/10-second lease/heartbeat | no public endpoint or autoscaling |
| Recovery | deterministic W8 Temporal identity and receipt replay | no W8 cap increase or distributed exactly-once claim |
| Limiter | persistent atomic actor+organization token buckets | no IP/forwarding-header authority |
| Load | Locust 2.46.1, 50 users, 1,000 protected requests | synthetic local/CI evidence only |
| Deployment | one complete isolated Compose stack and W4-W12 regression | no Helm/cloud/W13 telemetry |

## Implementation phases

1. Verify the clean W11 baseline, fetch refs, create the exact W12 branch, read
   W8-W11 authority, then replace AGENTS/contract before any implementation.
2. Freeze queue/rate/lease/workload/result schema and hashes; create W12 data,
   ADR, and plan documents.
3. Add the reversible Control migration and strict production models/schemas,
   organization-qualified repository, admission, idempotency, limiter,
   backpressure, run ETag, cancel, and audit paths.
4. Integrate L2/L3 grant claim with post-commit vault removal and atomic
   run/outbox handoff while retaining every W11 behavior and test.
5. Add the private Workflow Worker, closed task-reference projection, W8 opaque
   envelope, deterministic Temporal start, four slots, round-robin claim,
   heartbeat, fencing, recovery, terminal mapping, and graceful drain.
6. Add Compose, W12 smoke/fault matrices, Locust project/profile/result
   verification, and CI quality plus the single consolidated W4-W12 job.
7. Update architecture, threat, evaluation, roadmap, README, changelog, and
   evidence; run app/frontend/migration/freeze/security/Compose Development
   gates and fix observed defects.
8. Ordinals 1 and 2 failed and remain recorded. After the user explicitly
authorized the replacement and every value and expectation is frozen, run
formal W12 Validation ordinal 3 once only: stop Worker and acquire the
ordinal-3 guard before 8-run/64-capacity pre-stage, collect 50 bounded 503
probes, restart Worker, collect 50 bounded 429 probes and the 1,000 protected
requests, reconcile through public APIs/Grader, then seal cleanup counts after
stack shutdown. Record it without tuning/rerunning; no fourth formal run is
authorized.
9. Reconcile evidence, clean Compose to 0/0/0, audit exact paths and staged/
   unstaged diff, explicitly stage only changed paths among the 65 exact
   allowlist entries, create
   one local `feat: add W12 production control plane` commit, and stop.

## Validation discipline

Development may repeat bounded unit, rate, backpressure, lease/fence, four-slot,
and deterministic W12 smoke checks. Ordinals 1 and 2 remain failed formal
attempts. The formal profile may run exactly once more as explicitly authorized
ordinal 3 after code, schemas, migration, profile, checksums, Compose topology,
expected counts, and fault matrix freeze. A further failure is final unless
separately authorized by the user. Reporting remains unexecuted.
