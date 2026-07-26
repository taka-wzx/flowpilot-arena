# ADR 0001: Start with only runnable W1 application roots

- Status: Accepted
- Date: 2026-07-26
- Decision owner: W1 Foundation

## Context

The roadmap describes a broad long-term monorepo topology: Control Plane,
Sandbox, Arena, workers, packages, infrastructure, tests, and benchmarks. Its
W1 row, however, requires a runnable empty system, governance, CI, Compose,
and documentation while explicitly warning against early Agent-loop work.

Creating the full directory tree in W1 would suggest ownership of future
components and invite placeholder implementations that cannot yet be tested.

## Decision

Create only these runnable application roots in W1:

- `apps/control_api` for a stateless FastAPI health endpoint;
- `apps/control_web` for a static React/Vite landing page;
- `deploy/compose` for their local two-service configuration.

Keep Python and frontend manifests/locks beside the applications they build.
Put cross-cutting governance and delivery rules at repository root and in
`docs/`/`.github`. Document future topology without creating it.

## Consequences

### Positive

- W1 has a real, small end-to-end startup path to validate.
- Toolchains can be independently locked and checked in CI.
- Future weekly contracts have clear ownership boundaries.
- The repository does not falsely imply Sandbox, Agent, workflow, browser, or
  evaluation capabilities.

### Negative

- The initial directory tree is intentionally incomplete relative to the
  roadmap diagram.
- Later weeks must make explicit structural changes and update the relevant
  contracts/ADRs.
- There is no shared package or infrastructure abstraction in W1.

## Alternatives considered

1. **Create all roadmap directories with `.gitkeep` files.** Rejected because
   empty future subsystems look implemented and invite scope creep.
2. **Create one combined web/API application.** Rejected because the roadmap
   specifies separate backend and frontend stacks, and independent locks make
   CI/reproducibility clearer.
3. **Add database, identity, queue, or observability containers now.** Rejected
   because they have no W1 behaviour and belong to later roadmap milestones.
