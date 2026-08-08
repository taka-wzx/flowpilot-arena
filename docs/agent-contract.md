# W14 agent contract - security suite and threat model

## Authority, immutable baselines, and stop condition

This contract translates the W14 roadmap row and the user-authorized W14 brief
into the sole implementation authority for `week/14-security`.

W12 and W13 are immutable published baselines:

- W12: PR 35, merge `2c642a67341d0cd1c9c62b6bf883ad8df2853f40`,
  feature/head `b00dff77b1626a3f347abfba485ac5a197b627a7`, tag
  `w12-production`, Release `v0.3.0 - Production Control Plane`.
- W13: PR 36, merge `cedc5f26d41262c955b60854cc69ed4f28baded6`,
  feature/head `902e4078e1ece0f401f1c5c3010e56a7ae62acf5`, tag
  `w13-observability`, Release `v0.4.0 - Observability and Replay`.

W14 has one local outcome: preserve every W1-W13 frozen boundary while adding a
deterministic closed security decision layer, fixed harmless malicious-page
fixtures, secret redaction, browser-boundary verification, a threat model, and
local/CI evidence. The later expected tag is `w14-security`.

Authorization stops after one local commit
`feat: add W14 security suite and threat model`. It does not authorize push,
PR, merge, tag, Release, remote workflow dispatch/rerun, W12 formal Validation
ordinal 3, ordinal 4, W15 Reporting, external benchmark, or any real provider,
IdP, model, OCR, VLM, embedding, billing, account, personal-data, or egress
call.

The literal `%SystemDrive%/` path is outside every read, enumeration, scan,
diff, status, staging, and modification operation. No `code_review_agent`
repository may be accessed.

## Preserved W1-W13 authority boundary

All W1-W13 public API success semantics, strict schemas, deterministic fake
results, released migrations, W3/W7 catalogs/checksums/splits, W8 workflow,
checkpoint, receipt, idempotency, recovery and `finished_ungraded`, W9 context
and ablation, W10 fixed OIDC/tenant/RBAC/database-derived ActorContext/ETag,
W11 risk/approval/grant/audit, W12 admission/outbox/rate/backpressure/queue/
lease/fence/four-slot cap, and W13 trace/replay/dashboard/cost/failure taxonomy
remain frozen.

Security decisions, events, fixtures, smoke results, trace, replay, and
dashboard data never authorize a task, select an organization, issue or consume
approval, change action/risk/rate/queue/lease policy, create a receipt, mutate
Sandbox business state, decide business success, or replace the independent
Grader. A security refusal may only prevent an untrusted action or close an
isolated browser session. Normal frozen tasks retain their existing behavior.

## W14 design choice

W14 adds one dependency-free Browser Worker module containing fixed closed
rules, strict/frozen security decision models, canonical compact JSON, stable
SHA-256 fixture/content references, and bounded redaction. It integrates at the
existing Browser observation/action boundary and reuses the existing same-origin
request guard and one-context-per-session isolation.

One static harmless page under the existing Sandbox Web service is the only
malicious-page fixture used by Compose. There is no new service, database table,
migration, network, public ingestion endpoint, dynamic policy, ABAC/DSL,
generic scanner, or caller-selected rule. Fixture text is untrusted input only;
the server-owned rule table is authoritative.

No W13 schema is extended. W13 compatibility is proved by exporting the
unchanged `w13-run-trace-export/1.0` after a normal frozen production run and by
checking that malicious-page/security content is absent. An optional security
reference remains opaque and is never a W13 business fact.

## Closed security taxonomy and decision

The closed taxonomy contains:

- `none`;
- `prompt_injection`;
- `untrusted_instruction`;
- `privilege_escalation`;
- `cross_tenant_attempt`;
- `approval_bypass`;
- `secret_exposure_redaction`;
- `forbidden_navigation`;
- `sandbox_violation`;
- `browser_isolation_failure`; and
- `controlled_safe_stop`.

Closed outcomes are `allow`, `reject`, and `safe_stop`. Rejections expose only
schema version, source class, content/fixture SHA-256, category, reason code,
opaque security reference, `business_side_effects=0`, and
`sensitive_fields_present=false`. Raw page/DOM/model/tool text is processed only
in bounded memory and is never logged, persisted, traced, replayed, exported,
placed in a URL, or written to evidence.

Rules are case-normalized fixed regular expressions for explicit instruction
override, page/tool/system-instruction impersonation, privilege escalation,
cross-organization access, approval bypass, credential/canary exposure,
dangerous navigation, arbitrary execution, download, and new-window signals.
The first rule in a frozen priority order wins, making decisions deterministic.
No page or model content can add, remove, reorder, or override a rule.

## Redaction and canary contract

Redaction is bounded and deterministic across Browser observation text,
action/error messages, test serialization, W13 export assertions, evidence, and
URLs. It removes credential-bearing Authorization/Cookie/password/key/DSN
forms, URL userinfo/query/fragment, email-like personal data, private-key
markers, and Windows/POSIX machine-path forms. Low-risk canaries are synthetic
and assembled from short low-entropy fragments in tests/smoke where a complete
marker is required.

Bearer tokens and W11 approval credentials/nonces remain confined to their
existing authorities. They never enter the fixture, Browser Worker, trace,
replay, dashboard, audit helper fields, report, or URL.

## Browser sandbox contract

Every Browser session continues to own a distinct Playwright context. The
existing Browser Worker has no public host port and reaches only the fixed local
`sandbox-web` origin through an internal Compose network. W14 keeps credentials,
query strings, fragments, dangerous schemes, other hosts, redirect escapes, and
direct Sandbox API requests blocked. Downloads and service workers stay
disabled; extra-page/new-window attempts and arbitrary selector/coordinate/
JavaScript inputs remain rejected by closed schemas and tests.

The W14 fixture path is a single exact same-origin local path. Its observation
is classified before a subsequent business action; the session closes in a
controlled terminal rejection and returns only a safe reference. Injection
text submitted as a model-derived fill is rejected before locator execution.
Normal W4-W13 paths and actions are unchanged.

## Threat and test mapping

The ADR is authoritative for assets, actors, trust boundaries, attacker
capabilities, attack paths, mitigations, tests, and residual risk. At minimum,
tests cover taxonomy closure/strictness/hash stability, every malicious fixture
decision, secret redaction, URL/browser boundaries, same-run context isolation,
page/tool/model injection, tenant and RBAC spoofing, approval bypass, zero
business side effects, controlled terminal state, unchanged normal task
behavior, W13 export compatibility, and real-call-zero.

W14 is deterministic local/CI synthetic security testing only. It is not a
production security certification, penetration test, legal/compliance
statement, vulnerability assessment of third parties, or bounty conclusion.

## Explicit non-goals

No new service, database, migration, dependency, real page/account/secret/
approver/data, provider/model/OCR/VLM/embedding/billing/egress, malicious
payload execution, public scanner, external benchmark, Reporting, Helm/cloud,
physical deletion, impersonation/delegation/break-glass/global administrator,
L4 override, dynamic policy/ABAC/DSL, arbitrary Shell/SQL/JavaScript/code/URL/
API capability, production certification, penetration-test claim, or generic
future framework is in W14.

## Exact W14 file allowlist

Only the following exact paths may be created or modified. There are no
directory wildcards. A new path must first be added here; any scope expansion
listed in the non-goals requires new user direction.

~~~text
AGENTS.md
.github/workflows/ci.yml

docs/agent-contract.md
docs/adr/0014-w14-security.md
docs/plans/week-14-security.md
docs/evidence/week-14-report.md

apps/browser_worker/src/flowpilot_browser_worker/security.py
apps/browser_worker/src/flowpilot_browser_worker/policy.py
apps/browser_worker/src/flowpilot_browser_worker/observation.py
apps/browser_worker/src/flowpilot_browser_worker/runtime.py
apps/browser_worker/tests/test_security.py
apps/browser_worker/tests/test_policy.py
apps/browser_worker/tests/test_observation.py
apps/browser_worker/tests/test_runtime.py

apps/control_api/tests/test_w14_security.py
apps/sandbox_web/public/w14-malicious.html

deploy/compose/compose.yaml
tests/integration/Dockerfile
tests/integration/w14_security_compose_smoke.py
~~~

The allowlist contains 19 exact paths. Existing migrations, lockfiles, Control
implementation, Workflow Worker, Planning, Recovery, Grader, released fixtures,
frontends other than the one static file, load files, realm, and W1-W13 evidence
remain unchanged.

## Required local completion

Run every locally available quality gate named by `AGENTS.md`, including the
changed Browser Worker and Control API Python gates, Sandbox Web frontend gates,
workflow/YAML policy checks, Compose config/build/up/health, relevant migration
verification, W4-W13 regression, W13 observability smoke, W14 deterministic
security smoke, real-call-zero and sensitive-field proofs, exact allowlist and
diff review, private-key/gitleaks checks, and Compose cleanup. Record unavailable
tools factually without claiming success.

After gates and evidence reconciliation, explicitly stage only the 19 paths
above; never use broad staging. Create one local commit
`feat: add W14 security suite and threat model` and stop. Do not push, create a
PR, merge, tag, Release, dispatch/rerun CI, call a real provider, rerun W12
formal Validation ordinal 3, create ordinal 4, execute W15 Reporting, or begin
W15 implementation.
