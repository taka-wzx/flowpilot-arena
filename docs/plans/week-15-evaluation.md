# Week 15 plan - deterministic evaluation and reporting

## Outcome

Create a frozen, deterministic W15 evaluation/reporting pipeline over the
released W7 JML Reporting manifest, with five baselines, six closed ablations,
three pre-registered seeds, complete attempt retention, conservative paired
aggregation, strict JSON authority, and an explicit unavailable WorkArena
record. Preserve every W1-W14 product and security boundary.

## Frozen inputs

- Branch/base: `week/15-evaluation` from W14 merge
  `6bd960a031069f262fe60fbbb8bf2c65a09e409b`.
- Reporting set: six W7 templates, 18 fixed variants, exact order and checksums
  in `tests/integration/w15-reporting-protocol.json`.
- W7 catalog/split/Reporting checksums: `62737e...f8f8f`,
  `1d4b09...164ee`, and `c05bdf...4f2b6` respectively.
- Seeds: `2026081501`, `2026081502`, `2026081503`.
- Matrix order: DOM ReAct; Vision-only ReAct; Hybrid without recovery; Hybrid
  + Planner; Full system; then no Vision Router, Verifier, Checkpoint,
  short-term memory, enterprise knowledge retrieval, or local replanning.
- Safety/identity/tenant/RBAC/approval/browser isolation/Grader: always frozen
  on, never an ablation.
- WorkArena: unavailable because no authorized local version/subset/licence/
  checksum exists; zero external attempts.

## Implementation sequence

1. Verify origin/main contains the immutable W14 merge; create the exact W15
   branch and inspect W3/W7/W9/W12-W14 authority.
2. Replace AGENTS/contract and create this plan, ADR, evidence shell, Benchmark
   card, and exact protocol before implementation.
3. Implement strict protocol/report models, hash gates, deterministic opaque
   IDs, closed synthetic attempt runner, retry retention, aggregation,
   comparisons, target evaluation, redaction checks, and report sealing inside
   the existing integration project without a dependency or lock change.
4. Add focused tests for split/hash freeze, matrix closure, three seeds/order,
   attempt retention, missing/failure/retry behavior, aggregation, report
   stability, schema strictness, redaction, and unavailable Benchmark handling.
5. Add a profile-only Compose W15 Development smoke and CI static gate.
6. Run all local static/unit/project checks, Compose config/health/migrations,
   W4-W14 regression, W13/W14 smokes, W15 Development smoke, and security/
   real-call-zero/sensitive-field gates.
7. Seal exact protocol/config/schema hashes, then execute the single frozen
   Reporting final and verify byte-identical regeneration without creating a
   second experimental attempt set.
8. Reconcile evidence, clean Compose, audit the exact allowlist and staged/
   unstaged diff, explicitly stage exact paths, create the sole local W15
   commit, and stop.

## Interpretation boundary

The shipped executor is a deterministic synthetic fake for evaluation-pipeline
acceptance under the existing no-real-provider boundary. Its scores are not a
real-model Benchmark, external-generalization result, production SLO, ROI,
security certification, or statistically significant study. WorkArena remains
unavailable and no substitute is fabricated.

## Stop condition

One local commit only:

~~~text
feat: add W15 evaluation and reporting
~~~

No push, PR, merge, tag, Release, workflow dispatch/rerun, W12 Validation,
external Benchmark, real provider, or W16 action.
