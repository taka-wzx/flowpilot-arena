# Architecture — W16 current state

W16 packages the unchanged W1-W15 Control Plane and synthetic Arena. Release
artifacts observe the system and cannot authorize work or replace the
independent database-fact Grader.

~~~mermaid
flowchart LR
  User["Synthetic local user"] --> ControlWeb["Control Web"]
  ControlWeb --> ControlAPI["Control API"]
  ControlAPI --> Identity["Fixed local OIDC"]
  ControlAPI --> ControlDB["Control PostgreSQL"]
  ControlAPI --> Worker["Private fenced Workflow Worker"]
  Worker --> Temporal["Temporal + Recovery Worker"]
  Worker --> Planner["Planning Agent"]
  Planner --> Browser["Isolated Browser Worker"]
  Browser --> Sandbox["Synthetic Sandbox apps"]
  Sandbox --> SandboxDB["Sandbox PostgreSQL"]
  SandboxDB --> Grader["Independent database-fact Grader"]
  ControlAPI --> Trace["Opaque W13 trace/replay"]
  Helm["W16 namespace-scoped Helm"] -. packaging only .-> ControlAPI
~~~

## Authority boundaries

Identity, tenant isolation, RBAC, approval, audit, admission, queue/rate,
lease/fence, receipt/idempotency, trace/replay, browser isolation, and Grader
semantics are frozen at the W15 merge. The Agent terminal state is
finished_ungraded. Only the Sandbox database-fact Grader decides a task
outcome. Dashboard, Reporting, README, Demo, Helm, and cloud surfaces are
observation/documentation only.

## Local deployment surfaces

Compose remains the authoritative local topology. It builds the existing
services, publishes only loopback ports, uses synthetic Keycloak/Sandbox data,
and provides health checks plus acceptance profiles. The W16 chart is a
separate minimal packaging surface with four optional components:
Control API, Sandbox API, Control Web, and Sandbox Web. All components are
disabled by default because no authorized immutable application image is
published. Enabled images require repository@sha256:<64 hex> values.

The chart creates no database, migration, ingress, cloud object, RBAC role,
secret, or public egress. Its ServiceAccount does not automount a token;
containers run non-root with a read-only root filesystem, RuntimeDefault
seccomp, dropped capabilities, fixed resources, and startup/readiness/liveness
probes. NetworkPolicy is default-deny; only traffic among same-release chart
pods on ports 80, 8000, and 8001 is allowed, with no public egress.

## Reproduction path

Use the five-minute commands in the English or Chinese README. Run the W16
demo smoke for the redacted canonical trace, then the existing Compose
acceptance/observability/security smokes. A future authorized recording may
capture a local run; this environment has no recording tool, so the static
demo fallback is the only claimed media.
