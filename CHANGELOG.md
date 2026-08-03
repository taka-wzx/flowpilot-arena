# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- W13 append-only Control observability events with deterministic OTel-shaped
  trace/span IDs, closed failure taxonomy, strict redacted attributes, and
  fake-cost counters with real cost fixed at zero.
- W13 authenticated single-run trace export/replay endpoint and deterministic
  JSON dashboard artifact for local/CI synthetic review from admission through
  terminal `finished_ungraded` or failure.
- W12 authenticated asynchronous production-run API with strict task/action
  schemas, strong ETags, actor-scoped idempotency, persistent actor and
  organization token buckets, bounded Retry-After, 64/32 queue admission, and
  stable 429/503 failure responses.
- W12 Control revision `20260801_0003` with organization-qualified run,
  dispatch outbox, append-only lease history, scheduler partition, rate-bucket,
  and idempotency tables; no Sandbox or Temporal schema change.
- One private Workflow Worker with deterministic organization round robin,
  four slots, 30/10/25-second lease/heartbeat/drain values, monotonic fencing,
  deterministic Temporal workflow identity, W8 receipt convergence, and
  `finished_ungraded` terminal preservation.
- Atomic W11 grant-claim to W12 run/outbox handoff with post-commit vault
  removal, current-active authorization rechecks at the effect boundary, and
  eight frozen disjoint synthetic JML effect bindings.
- Locust 2.46.1 locked load project with checksum-frozen 50-user/1,000-request
  profile, intentional 50-request rate and backpressure probes, strict result
  schema/hash, one-run guard, public-API observation collection, and cleanup-
  after-measurement result sealing.
- Hardened complete Compose topology with the private Worker, W12 acceptance
  and load profiles, and one consolidated W4-W12 CI regression.
- W11 closed trusted server-side 2/2/7/5/5 L0-L4 action catalog, strict
  action-specific parameter schemas, canonical bindings, database-fact risk
  promotion, automatic audited L0/L1, mandatory L2/L3 approval, and permanent
  L4/unknown-action denial.
- W11 organization-qualified manager/security authorities independent from W10
  business roles, L3 distinct-user separation of duties, requester/executor
  self-approval denial, current-active-state rechecks, and strong-ETag approval
  lifecycle mutations with immutable append-only decisions.
- W11 hash-only short-lived one-time grants, bounded in-process raw credential
  vault, atomic exactly-one-winner claims, durable execution references,
  receipt-bound completion/recovery, and parameter/authority invalidation.
- W11 per-organization append-only canonical SHA-256 audit heads/events with
  atomic sequence allocation and genesis-to-head verification, plus a minimal
  Control Web request/detail/decision/audit experience that never receives
  grant material.
- W11 Control Plane revision `20260729_0002`, deterministic two-organization/
  sixteen-user/eight-authority seed and realm, Approval/Audit Compose smoke,
  and W4-W11 consolidated CI regression without a new job or dependency.
- W10 fixed local Keycloak 26.3.2 OIDC realm, strict Control API bearer/JWT/JWKS
  verification, frozen issuer/audience/client/RS256 policy, bounded JWKS
  refresh, and deterministic negative authentication coverage.
- W10 independent Control Plane PostgreSQL/Alembic schema for organizations,
  users, OIDC identities, memberships, and durable organization memory, with
  organization-aware keys/foreign keys/uniqueness/indexes and non-deleting
  disable/tombstone states.
- W10 database-derived `ActorContext`, closed organization-admin/operator/
  auditor roles and permissions, protected identity/organization/user/
  membership/memory/context routes, and default-deny non-enumerating tenant
  repositories.
- W10 strong resource-bound ETags, required If-Match preconditions, atomic
  organization/resource/version mutations, monotonic versions, stale-write
  rollback, memory-collection reset, and concurrent exactly-one-winner tests.
- W10 Control Web Authorization Code + S256 PKCE login/callback/logout/current-
  identity/forbidden experience with exact URI/origin allowlists, transient
  transaction state, and access/ID tokens held only in module memory.
- W10 deterministic two-organization/six-user identity seed, local identity
  Compose acceptance, one additional CI job, and authorized safe W9 memory/
  context projection without changing the released fake Planning path.
- W9 strict five-layer context schemas and deterministic Context Assembler with
  fixed layer precedence, source/trust/version/validity provenance, canonical
  sorted-key JSON/SHA-256, independent layer budgets, and a frozen total cap.
- W9 fixed fake-only enterprise catalog and closed lexical/hash retrieval with
  exact/global synthetic scope, source/trust/version/expiry filtering,
  content-hash dedupe, fixed ordering, and top-3 output.
- W9 deterministic task-local short-term summary preserving unresolved issues,
  recent actions, failure reasons, and pending steps under fixed item/byte/token
  caps without a model call or task-fact mutation.
- W9 process-local synthetic organization memory with exact scope and owner
  checks, monotonic versions, deterministic expiry, tombstone delete/reset, and
  no W10 identity, RBAC, real tenancy, or optimistic-lock claim.
- W9 additive context and context-backed Planning APIs, five Development-only
  ablations, cumulative context/retrieval/summary/memory ledger counters, W8
  durable safe counter projection, unit tests, Compose acceptance, and
  independent Joiner/Mover/Leaver grading.

### Security

- Kept raw approval credential/nonce material inside the bounded Control API
  vault while atomically creating a durable execution/run/outbox reference;
  Workflow Worker and Temporal receive hashes and opaque references only.
- Added exactly-one active lease winner and stale-write fencing, rechecked
  organization/user/membership/authority bindings immediately before effect,
  and prevented caller priority, IP headers, page/model data, or request fields
  from selecting limiter, queue, Worker, risk, approval, or success.
- Preserved per-organization tamper-evident audit append in the same transaction
  as admission, lease, start, recovery, and terminal mutations; no tamper-proof,
  blockchain, legal-compliance, or production-SLO claim is made.
- Bound approval authority to active organization-qualified database rows,
  kept it separate from business RBAC and JWT claims, and rejected self,
  inactive, insufficient, duplicate, stale, cross-tenant, and L4 approval.
- Persisted only one-time credential/nonce hashes; kept raw grant material out
  of Web, URLs, browser storage, logs, evidence, Temporal, Checkpoints,
  Planning, Sandbox, and Grader; replay and concurrent claim fail closed.
- Added organization-local tamper-evident audit chains and immutable decision/
  event database protections without claiming tamper-proof storage,
  blockchain, electronic signature, or legal compliance.
- Validated token signature, algorithm, `kid`, issuer, audience, client,
  subject, expiry, `nbf`, `iat`, header type, and token type before tenant
  lookup; rejected arbitrary issuer/JWKS/discovery/algorithm and prevented raw
  token/claim/code/cookie/secret persistence.
- Bound all business authority to active local identity/user/organization/
  membership rows and exact role agreement; added no global administrator,
  wildcard tenant, impersonation, fallback organization, or policy language.
- Qualified tenant-owned reads/counts/writes/disables/tombstones/resets and
  constraints by organization, unified cross-organization/nonexistent errors,
  and protected all mutable resources against unconditional or stale writes.
- Kept Control Plane, Sandbox, and Temporal persistence separate; retained
  Planning Agent isolation, W8 recovery limits, W9 fake regressions,
  `finished_ungraded`, and independent database-fact grading.
- Kept database facts as the only task-fact authority and independent Grader as
  the only success authority; rejected cross-scope context/memory operations,
  untrusted extra fields, free retrieval queries, raw content persistence, and
  context budget expansion.
- Added no service, database migration, dependency, vector database, embedding,
  provider/model/OCR/VLM call, network route, or arbitrary browser/API/code
  authority.

## [0.2.0] - 2026-07-29

### Added

- W8 deterministic Temporal Workflow/Activity boundary with fixed Python SDK
  1.30.0, local Temporal Server 1.31.2, replay tests, and an independent
  non-root Recovery Workflow Worker connected only to Temporal and Planning.
- W8 AES-256-GCM opaque durable input envelope, canonical verified Checkpoint
  lineage, one-day local retention, complete-history plaintext scan, and
  explicit prohibition on business/page/model/grader plaintext in Temporal.
- W8 fresh browser session epochs, old-reference invalidation, bounded
  transient retry/recovery, trusted acceptance-only faults, non-resetting
  W6/W7/W8 usage accounting, and one bounded immutable partial DAG revision.
- W8 forward-only `w8_operation_receipts` migration and transactionally atomic
  fixed synthetic business mutation/receipt semantics with same-hash replay,
  mismatch rejection, task-owned Reset/Seed cleanup, and zero-duplicate tests.
- W8 deterministic fault/recovery Compose acceptance for Activity ambiguity,
  Browser/Recovery Worker restart, Temporal replay, Checkpoint mismatch,
  idempotency mismatch, partial replan, cleanup, and independent grading.

- W7 strict immutable Planning DAG schemas with deterministic topology,
  node/edge/depth/width/dependency/field/byte caps, dependency state machine,
  and no retry or runtime partial replanning.
- W7 separate fake-only Planning Agent over one W6 Hybrid session, deterministic
  closed-set tool matching, one monotonic W6+W7 total ledger, step-level runtime
  Verifier, ungraded finish, and dedicated Worker-only internal network.
- W7 independent synthetic JML catalog design with 12 Joiner, 8 Mover, and 10
  Leaver templates, three deterministic variants each, template-level 18/6/6
  split, stable catalog/instance/split/Reporting checksums, and Apache-2.0 data
  provenance.
- W7 minimum typed non-deleting Sandbox transitions for HRIS transfer/disable,
  ITSM close, IAM revoke, Asset release, and Mail disable, using existing
  database columns and no migration.
- W7 deterministic tests/Compose acceptance design for invalid plans/tools,
  Verifier isolation, dependency execution, total-budget non-reset, terminal
  cleanup, W4-W6 regression, and independent W3/W7 grading.

- W6 bounded Hybrid Browser Worker session with one fresh Browser/Context/Page,
  selected current DOM or visual observations, safe structural route signals,
  strict session/generation-bound current-mode action envelopes, and
  cross-modality reference invalidation.
- W6 separate fake-only Hybrid Agent with deterministic DOM-first routing,
  closed reason codes/categories, local versioned DOM compression, total
  switch/observation/image/token/cost/time budgets, and no Sandbox/Arena/DB/
  Grader/provider access.
- W6 Compose/CI Hybrid isolation on a dedicated Hybrid-to-Worker internal
  network and deterministic DOM-to-Vision fake smoke proving wrong-mode/stale
  reference rejection, immediate-finish grade isolation, and a fresh
  independently graded completion circuit without a real model claim.
- W1 Foundation governance, scope contract, architecture documents, minimal
  API/web startup path, reproducible locks, and CI/security gates.
- W2 synthetic Sandbox foundation with one FastAPI/PostgreSQL backend,
  SQLAlchemy/Alembic schema, and five manual HRIS/ITSM/IAM/Asset/Mail routes.
- W2 backend and frontend unit tests, dependency locks, CI jobs, Compose runtime
  wiring, weekly ADR/plan/evidence, and a frozen synthetic onboarding recipe.
- W3 strict and canonical-checksummed Task Spec schema with ten fixed synthetic
  joiner tasks and a frozen 6/2/2 Development/Validation/Reporting allocation.
- W3 task-owned transactional Reset/Seed, database-fact-only deterministic
  Grader, narrow Arena management API, and anonymous manual-baseline recording
  with grader-derived scores.
- W3 Alembic ownership/baseline migration and deterministic catalog, reset,
  grading, negative-state, baseline, and API tests.
- W4 isolated non-root Playwright Browser Worker with local-origin policy,
  bounded DOM/accessibility observations, opaque observation-scoped element
  references, typed browser actions, and unconditional resource cleanup.
- W4 separate DOM Agent service with strict model JSON, deterministic fake
  scenarios, fixed Browser Worker client, and step/call/repetition/progress/
  time/token/cost budgets.
- W4 isolated Compose networks, one-off fake-model acceptance caller, pinned
  Python/uv/Playwright/Chromium runtime, CI jobs, dependency locks, and
  deterministic Worker/Agent/security/smoke tests.
- W4 authorization-gated profile-only Zhipu `glm-5.2` adapter and five-task
  caller with JSON-object output, strict local action validation, fixed
  endpoint, no tools/retries, environment-only key, and hard aggregate
  call/token/time/cost caps.
- W5 separate fake-only Vision Agent, strict versioned visual-session,
  observation, grounding, action, result, model-decision, budget, and run
  schemas, plus numeric image/latency/token/cost result metrics.
- W5 Browser Worker visual-session API with current in-memory JPEG viewport
  capture, fixed size/encoding/byte/count/time caps, output-only grounding
  rectangles, screenshot-scoped opaque references, and strict rejection of
  arbitrary coordinates, selectors, and code.
- W5 deterministic Vision-only Compose smoke, CI quality/smoke jobs, and
  fake-model tests proving both untouched-state 30/100 isolation and a
  separately reset, independently graded 100/100 `complete_joiner` circuit
  path without a provider call or Vision capability claim.

### Changed

- Superseded the unsuccessful OpenAI W4 real-model path with user-directed GLM
  scheme B while preserving the observed OpenAI 0/5 evidence.
- Remediated the observed GLM 0/5 path offline as prompt/config 1.1: successful
  hidden form fills now count as progress, bounded action history retains safe
  field/button names without values, strict output instructions are explicit,
  and the per-call output ceiling is 2,048 tokens.
- After prompt/config 1.1 was again observed at 0/5 from strict-schema
  rejection, added offline prompt/config 1.2: GLM returns a compact strict
  action choice while the trusted adapter generates transport-only versions,
  action IDs, and current observation IDs before full action validation.
- Recorded the separately authorized prompt/config 1.2 five-task outcome at
  3/5: tasks 001, 004, and 005 graded 100 while 002 and 003 graded 45; all
  calls remained within caps with zero retries.
- Added offline prompt/config 1.3 strict compatibility normalization for a
  direct typed action and exact legacy transport metadata, plus sanitized
  Pydantic error type/path reporting; unknown fields and stale observation IDs
  remain rejected.
- Recorded the separately authorized prompt/config 1.3 outcome at 4/5 and used
  its sanitized diagnostics to add offline 1.4 handling for bounded,
  non-executable summary metadata and deterministic finish-summary truncation.
- Recorded the separately authorized prompt/config 1.4 Development acceptance
  at 5/5: all five tasks independently graded 100 with zero retries and all
  aggregate call/token/time/cost limits respected.

### Security

- Isolated Recovery Worker from Browser Worker, Sandbox, Arena, Grader, and
  both databases; separated Temporal persistence from Sandbox business data;
  prohibited Temporal UI/host ports/repository mounts/Docker sockets.
- Bound W8 mutations to current epoch/session/generation/observation/reference
  plus a deterministic task/key/request hash and fixed closed operation;
  arbitrary headers, URLs, interception, code, and changed-hash replay fail
  closed.

- Restricted W7 plan authority to finite process/category, closed operations,
  strict supplied values, four-way tool intersection, current Worker
  references, and remaining budget; objective/page/model/risk data cannot add
  tools, routes, actions, approvals, or limits.
- Isolated runtime Verifier from Task Specs, expected state, Grader predicates/
  checksums, Arena, database, Reset/Seed, and Reporting results; negative or
  inconclusive verification cannot become success.

- Restricted W6 routing to bounded Worker-derived structural metadata, safe
  action outcomes, trusted finite categories, and numeric budgets; rejected
  page/model-directed routing, joined sessions, dual-modal model input,
  cross-mode/stale references, learning/history/cache, and switching that
  resets any hard limit.
- Added ignored secret-file patterns, pre-commit private-key detection, and a
  CI Gitleaks scan.
- Restricted W2 email fields to `.invalid`, asset tags to `SYN-`, IAM roles to
  ordinary `employee`, and the API surface to non-destructive create/list calls.
- Restricted W3 reset to exact catalog task IDs and ownership markers; rejected
  unknown spec/API fields and caller-supplied baseline scores; kept grading
  read-only and based only on structured database facts.
- Isolated W4 Browser Worker from Sandbox API/PostgreSQL and host resources;
  isolated DOM Agent from every Sandbox/Arena/Grader route; rejected dangerous
  origins, redirects, selectors/code/commands, stale references, password/real
  email/credential-like input, and unbounded actions or waits.
- Isolated W5 Vision Agent to the Browser Worker network with no provider
  credential or egress; restricted visual data to a current synthetic Sandbox
  JPEG in memory; invalidated screenshot/grounding references after every
  observation; and rejected persistent image paths/URLs, raw OCR text, DOM
  fallback fields, arbitrary pixel actions, and stale visual references.
