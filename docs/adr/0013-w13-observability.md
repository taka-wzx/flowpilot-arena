# ADR 0013: W13 local deterministic observability and replay

## Status

Accepted for W13 local implementation.

## Context

W13 must make a single production run traceable and reviewable while preserving
all W1-W12 business, security, approval, queue, lease, receipt, audit, and
grader semantics. The roadmap mentions OTel trace, cost statistics, dashboard,
failure classification, and replay, but the W13 authorization forbids real
provider billing, W15 Reporting, external observability services, new public
ingress, and broad service expansion.

## Decision

Implement observability as an append-only Control database table and a read-only
Control API trace export:

- W3C/OTel-shaped trace IDs and span IDs are deterministic hashes of
  organization-qualified run/event references.
- Workflow Worker writes only closed, opaque, fenced trace events to Control DB.
- Control API emits admission and approval-handoff trace events in the same
  transactions as the W12 run/audit mutations.
- The dashboard is a deterministic JSON summary embedded in the trace export
  and emitted by a W13 Compose smoke artifact.
- Cost statistics are synthetic/fake-provider counters from strict W8 usage;
  real cost is fixed at zero.

## Consequences

This choice gives reviewers a full local/CI replay path without adding a
telemetry collector, Grafana, Tempo, Prometheus, SaaS billing, or egress. It is
less visually rich than a live dashboard, but it is tighter for W13's boundary:
the replay is deterministic, tenant-qualified, schema-checked, and does not
become a business-success source.

W14+ may add richer security observability only with new authorization. W15 may
consume trace exports for external benchmark reporting, but W13 must not execute
Reporting.
