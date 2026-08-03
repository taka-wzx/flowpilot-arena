# Week 13 plan - observability and replay

## Baseline

W12 is the published baseline at merge
`2c642a67341d0cd1c9c62b6bf883ad8df2853f40`, tag `w12-production`, and Release
`v0.3.0 - Production Control Plane`. W13 starts from latest `origin/main` on
`week/13-observability`.

## Scope

Implement deterministic local/CI observability for a single production run:

- append-only Control DB trace events;
- OTel-shaped deterministic trace/span IDs;
- closed failure taxonomy;
- fake cost counters with real cost fixed to zero;
- read-only single-run trace/replay export endpoint; and
- JSON dashboard artifact in W13 smoke evidence.

## Non-Goals

No W12 baseline rewrite; no W12 formal Validation rerun; no ordinal 4; no W15
Reporting; no real provider/IdP/model/OCR/VLM/embedding/billing/egress; no
Prometheus/Tempo/Grafana/collector service; no frontend implementation; no
trace-derived success; no business semantic change.

## Work Items

1. Update W13 contract, ADR, evidence skeleton, and allowlist.
2. Add Control migration/model/schema for append-only observability events.
3. Add Control API trace export and replay/dashboard builder.
4. Instrument admission, approval handoff, worker lease/dispatch/workflow,
   W8 result summaries, receipt, cost, audit, and terminal references.
5. Add focused Control and Workflow Worker tests.
6. Add a deterministic Compose W13 observability smoke that exports a JSON
   replay/dashboard artifact.
7. Run locally available gates, update evidence, stage exact allowlist paths,
   and create the single local W13 commit.

## Acceptance

A reviewer can start one synthetic production run, wait for terminal
`finished_ungraded` or failed, call the W13 trace endpoint, and reconstruct the
observed sequence from admission through terminal state using only opaque
references, hashes, closed statuses/reasons, durations/counts, synthetic fake
cost, and audit/receipt references.
