# ADR 0017: W17 Portfolio Demo Console

- Status: Accepted
- Date: 2026-08-11
- Scope: Control Web presentation only

## Context

FlowPilot Arena already has local OIDC identity, closed RBAC, approval with
strong ETag protection, tamper-evident audit, durable production-run admission,
and bounded observability trace/replay. Those capabilities existed as separate
surfaces. A portfolio review needed one coherent console without weakening the
authority and security boundaries established in W10-W16.

The backend schemas and routes are frozen. `finished_ungraded` is an Agent
terminal state; only the independent Sandbox database-fact Grader determines
business success. The Control API run/trace surface does not return that
independent verdict.

## Decision

Build the W17 console entirely in the existing Control Web with no new npm
dependency and no backend change.

1. Reuse current identity, approval, and audit clients.
2. Add only the public organization-qualified run list/submit/detail/trace
   routes to the browser allowlist. Keep internal claim, cancel, lease, and
   worker routes unavailable to the UI.
3. Parse run and trace JSON with exact key sets, schema versions, ID formats,
   closed taxonomies, UTC timestamps, bounds, identity matching, and ordered
   events/replay. Fail closed on any deviation.
4. Reduce parsed trace data to presentation-safe fields: phase, status, reason,
   failure category, order, and observed time. Do not retain raw attributes or
   expose internal hashes/references through component props.
5. Offer exactly three fixed submissions: Joiner, Mover, and Leaver. Each uses
   an existing development task ID, `generate_plan`, and its matching synthetic
   task reference. The idempotency key is generated and retained in memory for
   safe retry; no arbitrary parameter editor is present.
6. Poll a selected active run every five seconds for at most two minutes. Stop
   on terminal state, error, visibility loss, or unmount; provide manual refresh.
7. Link `waiting_approval` detail to the existing read-before-decide strong-ETag
   approval handler.
8. Always present Agent status and independent Grader result separately. Show
   `Grader result unavailable from this surface` when the API has no verdict.
9. Link to Sandbox Web in a separate tab. Do not iframe it or change isolation.

## Consequences

The console can present the existing synthetic evidence as one responsive,
keyboard-operable interface while preserving W10-W16 semantics. Unknown API
fields fail visibly rather than being silently ignored. Polling cannot continue
indefinitely or while hidden.

The console intentionally cannot claim real business success, accept arbitrary
work, expose raw traces, control workers, invoke providers, or show an
independent Grader verdict that is absent from the Control API. The historical
name `production-runs` remains visible in code and documentation but is not a
production claim.

## Rejected alternatives

- New backend aggregation endpoint: rejected because W17 cannot change backend
  semantics or expand the attack surface.
- Generic JSON task builder: rejected because it would create arbitrary input
  capability outside the fixed synthetic contract.
- Browser iframe for Sandbox: rejected because it would blur the existing
  isolation boundary.
- Treating `finished_ungraded` or trace `succeeded` as success: rejected because
  only the independent database-fact Grader has that authority.
- Persistent browser token or submission storage: rejected; access tokens and
  idempotency retry state remain in memory.
