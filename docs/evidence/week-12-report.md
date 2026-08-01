# Week 12 local evidence - Production Control Plane

## Status and authority

- W11 immutable baseline: `84336fdc1dd056110b2dfb32383ce938361bf316`, tag
  `w11-approval`.
- W12 branch: `week/12-production`.
- Control migration: `20260801_0003`; Sandbox remains at released head
  `20260728_0003`.
- Exact contract allowlist: 65 paths. The final pre-stage audit found 58 changed
  paths before this report was added and zero outside the allowlist; the final
  audit is recorded below.
- Reporting was not executed. Real IdP/account/data/model/provider/OCR/VLM/
  embedding/egress calls and cost remained zero.
- No push, PR, merge, tag, Release, workflow dispatch, CI rerun, or W13 work was
  performed.

The implementation is Development-green after the fixes below, but formal
Validation ordinals 1 and 2 are both preserved failures and are not reported as
W12 acceptance passes. The user has subsequently authorized exactly one
auditable replacement formal Validation ordinal 3. Its frozen boundary is
recorded below; its outcome is recorded only after the guarded sequence
completes. This authorization does not erase either earlier failure.

## Frozen implementation

The public Control API performs authenticated admission only. Durable W12 state
is stored in Control PostgreSQL and handed to one private `workflow-worker`,
which has no public port, Bearer token, raw approval material, or caller-selected
authority. The Worker uses deterministic Temporal workflow identity and the
released W8 Recovery/receipt boundary; Planning still reaches only Browser
Worker. Control, Sandbox, Temporal, and Keycloak databases remain separate.

Run status is the closed set `waiting_approval`, `queued`, `leased`, `running`,
`recovering`, `verifying`, `finished_ungraded`, `failed`, `cancelled`, and
`expired`. Durable delivery is at-least-once with exactly one active fenced lease
winner; it is not described as distributed exactly-once. `finished_ungraded`
means only that the Agent ended. The independent Sandbox-fact Grader remains the
sole success authority.

Frozen scheduler and limiter values are:

| Field | Value |
|---|---:|
| global active pending capacity | 64 |
| per-organization active pending capacity | 32 |
| queue TTL | 300 seconds |
| browser slots | 4 |
| lease TTL | 30 seconds |
| heartbeat | 10 seconds |
| drain deadline | 25 seconds |
| maximum lease attempts | 3 |
| Retry-After clamp | 1-30 seconds |
| submit actor/org rate and burst | 5/s, 10 / 50/s, 100 |
| read actor/org rate and burst | 10/s, 20 / 200/s, 400 |
| mutate actor/org rate and burst | 2/s, 4 / 25/s, 50 |

Buckets are persistent, organization-qualified, microtoken-precision rows. The
limiter key comes only from verified identity, current local organization/user/
membership, and the fixed route class. Caller IP/forwarding headers, body, page,
or model content have no rate, queue, priority, or authority effect.

## Frozen workload and tools

- Locust `2.46.1`, Python image `3.13.5`, random seed `20260801`.
- 50 users, 25/25 organizations, 10 users/second spawn, all-user barrier,
  30-second measured phase, and fixed 100 ms think time.
- Exactly 20 protected operations per user and 1,000 protected requests:
  600 identity/run reads, 100 submissions, 100 idempotent replays, 100 accepted
  run reads, 50 ETag mutations, and 50 closed 404 probes.
- Joiner/Mover/Leaver user distribution: 20/15/15.
- Formal setup: 8 approval-backed executable runs, 56 capacity runs, 50 expected
  503 probes, and 50 expected 429 probes outside protected p95.
- Profile SHA-256:
  `b0f964ac3500e7d65fc914ae9c78b9f529e7619d3cc2bd6673f4b18689b28c36`.
- Result-schema SHA-256:
  `45530b83251698f155d8a51fde7a32efec7574f8970a2455fd1b930730ef8888`.
- Non-sensitive Docker runtime summary: 32 logical CPUs and 15,616 MiB memory
  bucket.

## Formal Validation ordinal 1

An initial pre-start attempt could not create `/results/validation.guard`
because the new named volume was root-owned. Both the result volume and
`w12_production_runs` were verified empty, so ordinal remained 0 and no product
request had run. The integration and load images were then fixed to share GID
10020 with a setgid result directory; a temporary-volume write/delete preflight
passed for both non-root images.

The actual guarded ordinal-1 sequence then started once. Its pre-stage passed:

| Observation | Result |
|---|---:|
| guard | `w12-validation-ordinal-1` |
| setup accepted | 64 |
| approval-backed executable runs | 8 |
| capacity runs | 56 |
| expected 503 probes | 50/50 |
| protected metrics artifact | not created |
| observations artifact | not created |
| final result/hash | not created |

The formal run failed while exhausting the twelve actor read buckets, before
the 1,000 protected requests. The same-organization missing-run path rolled back
the token-bucket update with the 404 transaction, so the formal client raised
`rate-probe actor bucket did not become exhausted`. The guard and pre-stage
artifact existed; metrics, observations, and result artifacts did not. This is
the one consumed formal Validation. A second formal run required explicit user
direction, which was later granted and is recorded below.

Consequently, formal API p50/p95/p99, queue-wait percentiles, run terminal
counts, Worker claim/reclaim/fence counts, workflow duplicate counts, receipt
counts, accepted-run reconciliation, aggregate audit count/head/hash, and final
acceptance result are unavailable. Development observations below are not
substituted for them.

## Historical replacement Validation ordinal 2 freeze

After reviewing the preserved ordinal-1 failure, the user expressly authorized
one replacement formal Validation. At that time, the authorization was limited
to ordinal 2; it neither erased ordinal 1 nor authorized an ordinal 3 or later
run.

Before the ordinal-2 guard was created, the following replacement boundary was
frozen:

| Field | Frozen replacement value |
|---|---|
| guard | `w12-validation-ordinal-2` |
| result `validation_ordinal` | JSON Schema constant `2` |
| result-schema SHA-256 | `0e6f6be248b119d246cc1d2a95880f9b534b4b243c2e6ca80c4e2954825f70e0` |
| profile SHA-256 | unchanged `b0f964ac3500e7d65fc914ae9c78b9f529e7619d3cc2bd6673f4b18689b28c36` |
| product queue/rate/lease/workload values | unchanged |
| Reporting | not executed |

The replacement schema change makes the ordinal-2 artifact non-interchangeable
with the failed ordinal-1 attempt; it is not a product-policy or load-tuning
change. The resulting ordinal-2 run was the then-single authorized formal
sequence.

## Post-failure Development fixes and verification

Between ordinal 1 and ordinal 2, the following defects were fixed without
changing the frozen product rates, queue capacities, measured sequence, or
profile hash:

1. OIDC database actor resolution was moved off the async event loop, and W12
   synchronous database routes run in the bounded thread pool. This removed a
   50-request connection-pool starvation condition that produced zero completed
   Locust requests.
2. Same-organization missing-run reads now commit the authenticated read-rate
   charge before returning the stable 404. Cross-organization rejection still
   occurs before rate lookup.
3. Rate warmup now uses bounded concurrent per-actor bursts and counts only an
   immediate complete 429 probe group, yielding exactly 50 counted probes while
   retaining the 2.1-second frozen refill wait.
4. Capacity admission ensures a partition without pre-locking it, then locks all
   scheduler partitions in one deterministic order. This removed the observed
   alpha/beta partition deadlock.
5. Integration and load images use the same fixed result-volume GID and remain
   non-root and read-only.

After the ordinal-2 collector failure, one bounded correctness repair was made
before the separately authorized ordinal-3 freeze: `waiting_approval` runs no
longer consume executable queue capacity, and successful admission takes the
rate charge, executable-only capacity lock, then audit lock in that order. This
matches the frozen definition that only executable pending work occupies queue
capacity and removes the observed lock-order risk. The focused Control API
test suite passed with 65 tests.

The latest clean non-formal 50-user Development run observed:

| Metric | Result |
|---|---:|
| users | 50 |
| protected requests | 1,000 |
| counted rate probes / 429 | 50 / 50 |
| accepted protected runs | 100 |
| API p50 | 45.604 ms |
| API p95 | 182.075 ms |
| API p99 | 316.067 ms |
| expected HTTP | 750x200, 200x202, 50x404 |
| unexpected HTTP | 0 |
| unexpected 5xx | 0 |
| PostgreSQL deadlocks after lock fix | 0 |
| Validation flag | false |
| Reporting flag | false |

The deterministic W12 Development smoke also passed with one automatic
`workflow_rejected`, L2 and L3 `finished_ungraded`, eight additional
`finished_ungraded` effect runs, exactly four simultaneous browser tasks,
cross-tenant rejection, a valid tamper-evident audit chain, zero real calls,
and zero cost. Observed queue-wait bounds were 85,686-24,355,459 microseconds.
These are synthetic Development observations, not a formal Validation,
production SLO, certification, legal compliance, or ROI result.

## Formal Validation ordinal 2

The user-authorized replacement began from a clean 0/0/0 Compose state. Its
guarded pre-stage completed successfully before the Worker was restarted:

| Observation | Result |
|---|---:|
| guard | `w12-validation-ordinal-2` |
| setup accepted | 64 |
| approval-backed executable runs | 8 |
| expected 503 probes | 50/50 |
| rate probes / 429 | 50/50 |
| protected requests | 1,000 |
| intended protected accepted runs | 100 |
| observed protected accepted runs | 98 |

The guarded measurement artifact was written with `validation_ordinal: 2`, but
the collector then failed before observations because its required 100 protected
run references were not present. The measurement records two unexpected 409
responses and two `unexpected_5xx` counter increments; its expected HTTP
counts were 750x200, 194x202, and 54x404. The API latency values were p50
49,661 microseconds, p95 474,910 microseconds, and p99 1,495,849 microseconds.
The collector raised `formal protected run references changed` before any
`observations.json`, result, result hash, terminal reconciliation, or formal
acceptance decision could be created.

| Artifact | SHA-256 / state |
|---|---|
| `validation.guard` | `64739fec74b57f1f171e266108f8b1ed7e94c1e819d361ea9e8443c0aea45132` |
| `prestage.json` | `c8a50bf3074431f4aa1bbd2d8a9ec8a3c4c41811d95f3074f64685ab5aa57b19` |
| `metrics.json` | `7ddaa6eee64981507fede6dfe1b82f7cda21d1a07b1a5e2b94004a4d93fcd787` |
| `observations.json` | not created |
| final result / hash | not created |

Ordinal 2 is therefore a preserved formal failure, not a W12 acceptance pass.
No source or frozen-workload tuning, result reconstruction, or collection retry
was performed. The volume was removed only after the artifact facts above were
recorded. At the end of ordinal 2, ordinal 3 had not been authorized.

## Authorized replacement Validation ordinal 3 freeze

After reviewing the two preserved failures, the user expressly authorized one
replacement formal Validation ordinal 3. Before its guard can be created, the
following boundary is frozen:

| Field | Frozen replacement value |
|---|---|
| guard | `w12-validation-ordinal-3` |
| result `validation_ordinal` | JSON Schema constant `3` |
| result-schema SHA-256 | `45530b83251698f155d8a51fde7a32efec7574f8970a2455fd1b930730ef8888` |
| profile SHA-256 | unchanged `b0f964ac3500e7d65fc914ae9c78b9f529e7619d3cc2bd6673f4b18689b28c36` |
| product queue/rate/lease/workload values | unchanged |
| Reporting | not executed |
| further formal Validation | ordinal 4 is not authorized |

The ordinal-3 result schema re-freeze makes all three formal ordinals
non-interchangeable without changing product policy, queue/rate values,
workload, counts, seed, or frozen profile. Load static/schema verification
passed before this boundary; formal results below must come from the one guarded
ordinal-3 run and may not be tuned or rerun.

## Formal Validation ordinal 3

The one authorized guarded sequence completed from a clean 0/0/0 Compose
state. The Worker was stopped for pre-stage, then restarted and healthy before
the single measurement. Its independent collector completed before Compose was
removed:

| Observation | Result |
|---|---:|
| guard | `w12-validation-ordinal-3` |
| setup accepted | 64 |
| approval-backed executable runs | 8 |
| expected 503 probes | 50 / 50 |
| rate probes / 429 | 50 / 50 |
| protected requests | 1,000 |
| protected accepted runs | 100 |
| total accepted runs reconciled | 164 |
| API p50 / p95 / p99 | 52.762 / 353.186 / 503.074 ms |
| unexpected HTTP / 5xx | 0 / 0 |
| queue wait p50 / p95 / p99 | 21,566,080 / 46,310,370 / 46,310,370 microseconds |
| maximum browser concurrency | 4 |

The collector reconciled 8 `finished_ungraded` effect runs, 56 failed capacity
runs, 50 cancelled runs, and 50 `waiting_approval` runs. It recorded 64 Worker
claims, zero database lock conflicts, reclaims, duplicate dispatches/starts,
stale-fence write successes, receipt mismatches/replays, accepted-run loss,
approval bypasses, cross-tenant leaks, browser-context crossflow, duplicate
business effects, audit verification failures, real calls, and cost.

The aggregate tamper-evident audit verification recorded 1,103 events and head
sequence 1,103 with head digest
`a47732cd4762ba73ae052663409d7a123ac8a4199d7edfea021198edadb25115`;
duplicate sequences, forks, and broken heads were all zero. The non-sensitive
host summary was 32 logical CPUs and a 15,616 MiB memory bucket. Reporting
remained false.

| Artifact | SHA-256 / state |
|---|---|
| `validation.guard` | `9927e079ccf2105c09e78c40f169634ab6ee367c49c3f58524bea252b7da2079` |
| `prestage.json` | `b715940a7abc92df5703576f162f08889a417d3b19c6eae6efb938646a498317` |
| `metrics.json` | `6724ea7a69894fac1496094dff74a3ab4cb19c6d82bdad076539b2d791f7786e` |
| `observations.json` | `2fb046f85bcfe0e2e843cab8454ea60a9c42d2135ef1587237b6e1d3ac7d2e88` |
| `result.json` raw bytes | `74eb44e0273ecccd9fcc2d68bc70775569a884bcac771e89a0c402b4da51150c` |
| canonical result `result_hash` | `0870e71e8bd395cad94d180567dafcd38d916eba0205b8fd6103402d8144e24d` |
| schema validation / acceptance failures | valid / `[]` |

Ordinal 3 is the formal W12 local Validation acceptance pass. It does not erase
ordinals 1 or 2, does not authorize a rerun, and does not authorize ordinal 4.

## Local gates

- Control API: Ruff, format, mypy, and 65 tests passed after the final fixes.
- Workflow Worker: Ruff, format, mypy, and 22 tests passed.
- Planning Agent: Ruff, format, mypy, and 48 tests passed.
- Recovery Worker: Ruff, format, mypy, and 12 tests passed.
- Load project: Ruff, format, mypy, 5 tests, profile checksum, and schema
  checksum passed before the ordinal-3 guard; final result schema validation
  and an empty acceptance-failure list passed after cleanup.
- All other Python application, frontend, W4-W11 Compose regression, migration
  round-trip/freeze, realm/catalog/context freeze, and W10/W11 security matrix
  gates passed earlier in the same local W12 work and were not affected by the
  final scoped changes.
- Control live migration current/check passed at `20260801_0003`; Sandbox live
  migration current/check passed at `20260728_0003`.
- The final W12 smoke and clean 50-user Development run passed as recorded
  above.
- Classic `docker-compose` `v5.3.1` was used; Docker server was `29.6.2`.
  Docker buildx was unavailable. `uv` was `0.11.14`, pre-commit `4.3.0`, and
  gitleaks `8.30.1`.
- The classic builder cannot stat the ignored `tests/load/.pytest_cache` because
  of a host Windows ACL. The exact ten authorized load-context files were copied
  to an authorized temporary directory for image builds and the directory was
  removed after each build. No repository file or frozen profile was replaced.

## Final cleanup and Git boundary

- Final project resources: 0 containers / 0 networks / 0 volumes. Classic
  Compose did not remove the profile-only `w12-results` volume with `down -v`,
  so its exact project label was verified and the synthetic volume was removed
  explicitly.
- `pre-commit run detect-private-key --all-files`: passed. The user-level cache
  had an invalid manifest, so the hook was initialized in an authorized isolated
  temporary cache; the cache was removed afterward.
- `gitleaks git --no-banner --redact --exit-code 1 .`: passed; 50 commits and
  approximately 3.90 MB scanned, no leaks found.
- `git diff --check`: passed.
- Final exact-path audit: 59 changed paths, 65 allowlisted paths, 0 outside.
- The 14 paths changed during ordinal-3 repair/freeze/evidence reconciliation
  were explicitly staged and folded into the existing one authorized local W12
  feature commit with subject `feat: add W12 production control plane`; no
  second W12 commit was created. Ordinal 3 was executed once and accepted;
  ordinal 4 is not authorized.
- Remote PR/run/job activity: none. W12 tag and Release: not created. W13 was
  not started.
