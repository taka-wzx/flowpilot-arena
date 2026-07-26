# Product brief

## Product intent

FlowPilot Arena is planned as an enterprise computer-use system that can be
verified, recovered, and governed by human approval, plus a resettable Arena
for deterministic evaluation. The target problem domain is Joiner / Mover /
Leaver work across enterprise web software.

The two planned product surfaces have different roles:

- **FlowPilot Control Plane** will coordinate safe, multi-user task execution.
- **FlowPilot Arena** will simulate enterprise applications and measure the
  system without claiming production outcomes.

## W1 product position

W1 is deliberately not a user-facing automation release. It establishes a
small, reproducible repository baseline so later product claims can be backed
by tests, evidence, and a controlled delivery process.

The only W1 runtime behaviour is:

- a stateless API health endpoint; and
- a static web page that identifies the repository and its current scope.

Neither surface accepts business data, authenticates users, invokes a model,
or connects to an enterprise system.

## W1 success criteria

1. A new contributor can understand the product's intended boundary in under a
   minute from the README and governance documents.
2. The API smoke endpoint and static web page can be built from committed,
   locked dependencies.
3. The local Compose configuration is reproducible without adding future
   infrastructure.
4. Quality, secret detection, evidence, and branch discipline are present
   before business functionality begins.

## Product guardrails

- No real enterprise systems or personal data are permitted in W1.
- No paid model, model provider, agent loop, browser automation, or workflow
  is permitted in W1.
- The Arena is an evaluation facility, not a production product surface.
- Future automation must preserve the roadmap's human-approval and
  independently verified-result principles; W1 does not implement them yet.

## Deferred capabilities

Sandbox applications, Arena task definitions and grading, browser execution,
multimodal observation, planning, recovery, identity, persistence,
observability, and external benchmark work are explicitly deferred to their
named roadmap weeks. Their absence is intentional, not a known defect.
