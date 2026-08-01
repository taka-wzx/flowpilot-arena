# ADR 0012: durable production admission with a fenced Workflow Worker

- Status: accepted for W12
- Date: 2026-08-01
- Branch: `week/12-production`
- Baseline: W11 `84336fdc1dd056110b2dfb32383ce938361bf316`

## Context

W11 keeps its trusted execution gate in Control API and proves approval,
one-time claim, recovery binding, and tamper-evident audit locally. It does not
provide production-shaped asynchronous admission, a durable API-to-Worker
handoff, queue bounds, rate limits, organization fairness, browser concurrency
control, or load evidence. W12 must add those capabilities without moving raw
grant material out of Control API, giving Planning/Browser/Recovery a Control
database route, weakening W8 receipt semantics, or introducing a second broker.

## Decision

1. Keep Control PostgreSQL as the durable admission/outbox/limiter store. Add
   organization-qualified run, outbox, immutable lease history, scheduler
   partition, token bucket, and idempotency tables in revision
   `20260801_0003`.
2. Return 202 after one Control transaction. L0/L1 create queued work; L2/L3
   create a waiting run and no executable outbox until the existing W11 grant
   is atomically claimed with the run/outbox/audit transition.
3. Add one private `workflow-worker` with four asynchronous slots. It claims
   one item per organization round, owns a 30-second lease, heartbeats every
   10 seconds, and fences every later write with a monotonically increasing
   token. It has Control database and Temporal routes only.
4. Use deterministic Temporal workflow identity and the released W8 opaque
   encrypted start envelope. Redelivery converges on the same workflow; W8
   receipts retain at-most-one business effect. Do not claim distributed
   exactly-once.
5. Persist an atomic server-configured token bucket keyed only by verified
   ActorContext plus fixed route class. Freeze the 64/32 queue, 300-second TTL,
   all rates/bursts, 429/503 bodies, and Retry-After calculation in the W12
   contract.
6. Select Locust 2.46.1 as the only load tool and freeze one 50-user,
   two-organization, 30-second, 1,000-protected-request profile plus 50 rate
   and 50 backpressure probes. Results use one checksum-frozen JSON Schema.
7. Keep formal observation DB-less. The acceptance client pre-stages through
   public Control/approval routes and grades through Sandbox; the load client
   performs the guarded rate/protected phases; the collector reconciles opaque
   run fields and both public audit verifiers. Neither receives a Control DSN,
   Worker endpoint, Docker socket, or raw grant.
8. Acquire the formal ordinal guard before pre-staging, persist measurements
   and observations separately, shut down Compose, observe cleanup counts, and
   only then seal the strict result and canonical SHA-256. Finalization cannot
   issue HTTP load or create a second guard.

## Consequences

API threads no longer hold a browser session or synchronously declare task
success. Accepted work survives process restart and can be reclaimed, while
stale owners cannot heartbeat or commit results. Queue and rate state are
durable and tenant-qualified. Four production workflows bound browser
concurrency without changing Browser Worker APIs or W8 caps.

The result's single `audit.head_hash` is an aggregate digest over the two
organization-qualified verified head records, while event/head sequence counts
are summed. Each underlying chain is still independently verified; no global
chain or cross-tenant audit head is created in the product database.

The topology remains a deterministic local Compose production shape, not a
multi-region availability claim or real production SLO. A database
administrator or total storage loss remains outside the tamper-evident chain's
guarantee. One Worker service is not autoscaling. W13 telemetry, W14 malicious
pages, W15 Reporting, and W16 deployment stay deferred.

## Rejected alternatives

- Kafka, Redis, RabbitMQ, Celery, or NATS: unnecessary broker and trust surface.
- Control API directly starting Browser/Planning work: preserves the request-
  thread coupling and creates a production bypass.
- Raw approval credential in outbox/Temporal: violates the W11 vault boundary.
- Caller priority or dynamic policy: creates authority and fairness injection.
- Unfenced timeout/retry: permits stale Worker result corruption.
- A second load framework or custom stdlib load generator: violates the single
  frozen-tool requirement and weakens reproducibility.
