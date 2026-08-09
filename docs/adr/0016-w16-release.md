# ADR 0016: W16 release and reproducibility boundary

- Status: Accepted for local implementation only
- Date: 2026-08-09
- Decision owners: repository user and local agent

## Context

W1-W15 already define the Control Plane, synthetic Arena, independent
database-fact Grader, trace/replay, security boundaries, and frozen W15
Reporting evidence. W16 needs an unfamiliar-user path to reproduce the local
system without turning release artifacts into a new authority or implying a
cloud deployment.

## Decisions

1. Start from verified origin/main 078eb22... and work only on
   week/16-release.
2. Keep the chart disabled by default because the repository has no authorized
   registry/image publication and no frozen application-image digests. Enabled
   components require repository plus a 64-hex SHA-256 digest in values.
3. Use one chart with four optional local synthetic components (Control API,
   Sandbox API, Control Web, Sandbox Web). It creates no database, ingress,
   RBAC role, cloud object, or secret. The ServiceAccount has token automount
   disabled; NetworkPolicy is default-deny with no public egress.
4. Use a deterministic stdlib demo runner that emits only opaque references and
   closed events. Recording software and cloud deployment are evidence states,
   not hidden fallbacks.
5. Generate SPDX 2.3 from lockfile integrity/hash data and frozen source
   declarations with a normalized epoch timestamp. Missing image digest or
   external generator is recorded as unavailable rather than fabricated.

## Consequences

The chart can be linted and rendered with explicitly supplied local image
digests, but cannot be called a cloud deployment until a later authorization
specifies provider, account/project, region, cluster, domain, TLS, budget,
egress, secret source, lifecycle, and deletion policy. The demo proves wiring
and redaction only. The machine-readable W15 report and all prior release
objects remain byte- and history-stable.
