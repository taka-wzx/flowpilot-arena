# W12 production data and workload freeze

## Baseline and schema versions

- W11 merge: `84336fdc1dd056110b2dfb32383ce938361bf316`
- W11 tag: `w11-approval`
- W12 branch: `week/12-production`
- Control migration: `20260801_0003`
- production create: `w12-production-run-create/1.0`
- production run: `w12-production-run/1.0`
- work item: `w12-work-item/1.0`
- lease: `w12-worker-lease/1.0`
- load profile: `w12-load-profile/1.0`
- Validation profile: `w12-validation-50x4/1.0`
- load result: `w12-load-result/1.0`

## Immutable queue, limiter, and Worker values

- queue active total/per organization: 64 / 32
- queue TTL: 300 seconds
- Workflow Worker services/slots: 1 / 4
- claim batch: one item per free slot
- lease TTL / heartbeat / drain: 30 / 10 / 25 seconds
- maximum lease attempts: 3
- fence: per-outbox monotonic integer beginning at 1
- organization fairness: locked deterministic round robin, one item per
  partition per round, no caller priority
- `production_submit`: actor 5/s burst 10; organization 50/s burst 100
- `production_read`: actor 10/s burst 20; organization 200/s burst 400
- `production_mutate`: actor 2/s burst 4; organization 25/s burst 50
- token unit: 1,000,000 microtokens; elapsed/refill precision: integer UTC
  microseconds with floor; clock rollback refill zero
- Retry-After: ceiling of the larger actor/organization deficit time, clamped
  to 1-30 seconds

## Frozen effect-authority bindings

- Joiner / `create_ticket`:
  `9f9a16bad25c578969e92f60e982510c9be6a4fe74d9236d06e8f9d96f9ea43b`
- Joiner 001 v2 / `create_ticket`:
  `8f7967a3f5fa16a535c758ef421a6bed1b24e3f5d307cd80d28c2d7133b1f64c`
- Joiner 002 v1 / `create_ticket`:
  `24a48d8f36f74aecec1dfc18a709e8682a1bc5b4985206ea419c27bd0fb1bd32`
- Joiner 002 v2 / `create_ticket`:
  `5445094ff191a1beb668e68fb5501c91287e32bc447128cbbc3ae844d9849282`
- Mover / `transfer_employee`:
  `417392e96f16078f9d9ac6bbb00cf0169945a149f322c787b99aa90e5377712f`
- Mover v2 / `transfer_employee`:
  `330c7a46e46648958a40f6e379acf266959eb93ec70b33a44d912145e9103d02`
- Leaver / `disable_employee`:
  `ec514adaaaf6c5d9e3b9ac1143fa3526b93dfca511ff571dd947bdfa605fa756`
- Leaver v2 / `disable_employee`:
  `bb444aecec640db18cd003b4ff585b5d14a76c0f84470842f7799011a46eb5fc`

No other admitted action binding can start Temporal or Browser execution.

## Load artifact freeze

- tool/version: Locust `2.46.1`
- profile raw-byte SHA-256:
  `b0f964ac3500e7d65fc914ae9c78b9f529e7619d3cc2bd6673f4b18689b28c36`
- result JSON Schema raw-byte SHA-256:
  `45530b83251698f155d8a51fde7a32efec7574f8970a2455fd1b930730ef8888`
- seed: 20260801
- users and organizations: 50 and 2, split 25/25
- spawn rate / steady / think: 10 users/s, 30 seconds, fixed 100 ms
- protected requests: 1,000, exactly 20 per user
- protected mix: 600 identity/run reads, 100 submissions, 100 same-body
  idempotent replays, 100 accepted-run reads, 50 ETag mutations, and 50
  cross-tenant/not-found checks
- setup probes: 50 rate-limit requests expecting 429 and 50 capacity requests
  expecting 503; excluded from protected p95
- setup order: stop Workflow Worker; acquire the explicitly authorized
  ordinal-3 replacement guard; approve/claim 8
  executable runs; add 56 L1 fail-closed runs to reach 64 active outboxes;
  require 50 capacity 503s; restart Worker; exhaust production-read actor
  buckets; require 50 per-user 429s; wait 2.1 seconds before protected timing
- pre-staged executable runs: 8, four per organization; at least five ready
  together; maximum active production Browser tasks exactly four
- task/user counts: Joiner 20, Mover 15, Leaver 15
- ordinals 1 and 2: preserved failed formal attempts
- replacement Validation allowed: exactly one ordinal 3; Reporting executed:
  false

## Percentiles and result hash

API and queue p50/p95/p99 use nearest rank over integer microseconds after
deterministic sort: rank is `ceil(percentile * count)` with one-based indexing.
Protected API latency excludes only token acquisition, approval preparation,
intentional Retry-After waiting, probe setup, and Browser/LLM execution. The
result hash is SHA-256 over sorted-key compact UTF-8 JSON after excluding only
the `result_hash` member. Raw artifacts use LF line endings and their raw-byte
hashes above.

Formal measurement, public-API observations, and cleanup sealing are separate.
The exclusive guard is created before pre-staging. Measurement writes opaque
accepted run/organization references for exact reconciliation. The collector
uses only Control API and Sandbox Grader, never a database credential. After
Compose shutdown, finalization accepts the observed project container/network/
volume counts and computes the result hash without issuing another HTTP request.

The result's `audit.event_count` and `audit.head_sequence` sum the two verified
organization chains. `audit.head_hash` is SHA-256 over canonical sorted-key
compact JSON containing the two ordered
`{organization_id,event_count,head_sequence,head_hash}` records. This is a
result-artifact aggregate only; the product retains two separate tenant chains.

## Frozen success checks

Protected API p95 is below 500,000 microseconds; all 50 clients are present;
max production Browser concurrency is exactly four and never higher;
unexpected 5xx, accepted-run loss, duplicate business effect, approval bypass,
cross-tenant leak, browser-context crossflow, stale-fence write success, audit
verification failure, duplicate audit sequence/fork/broken head, real calls,
and cost are all zero. Cleanup is containers/networks/volumes 0/0/0. These are
deterministic local/CI synthetic criteria, not real production SLO, security or
compliance certification, legal audit, or ROI evidence.
