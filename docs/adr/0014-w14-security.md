# ADR 0014: deterministic W14 security boundary

- Status: Accepted for W14 local implementation
- Date: 2026-08-08
- Decision scope: `week/14-security`

## Context

W1-W13 already provide typed Browser actions, isolated Playwright contexts,
fixed local origins, verified OIDC, organization-qualified SQL, closed RBAC,
strong ETags, risk/approval/grant checks, audit chains, durable admission and
fencing, receipts, independent grading, and redacted run trace/replay. W14 must
test and strengthen the boundary where untrusted page/tool/model content meets
those authorities without changing any normal business-success source.

The test environment is deterministic, local/CI, synthetic, and harmless. It
does not contact a real page, model, provider, identity system, account,
approver, person, billing system, or external network.

## Assets

- organization-qualified identity, membership, role, authority, approval,
  grant, run, outbox, lease, fence, receipt, audit, trace, replay, and dashboard
  state;
- Sandbox business state and independent Grader facts;
- Browser session/context isolation and the closed action allowlist;
- Bearer and W11 raw approval material confined to their existing authorities;
- W3/W7 catalog bindings and W8/W12/W13 frozen semantics;
- local security evidence integrity and absence of sensitive raw content.

## Actors

- authenticated synthetic HR/manager/security/auditor/organization-admin actors
  with only their existing closed RBAC permissions;
- Control API and its database-derived `ActorContext`;
- private Workflow and Browser workers;
- deterministic fake Agent/model output;
- independent Sandbox Grader;
- adversarial page, DOM, screenshot, tool-output, model-output, request-body,
  query, URL, and forwarding-header content;
- CI/local operator executing the fixed suite.

There is no global administrator, global approver, impersonator, delegate,
break-glass actor, real end user, or real attacker account in W14.

## Trust boundaries

1. **Caller to Control API:** only verified Authorization-header OIDC material
   plus current database rows establish actor and organization authority.
2. **Control API to Workflow Worker:** only admitted closed bindings, opaque
   approval references/hashes, run/fence state, and deterministic workflow IDs
   cross the private boundary.
3. **Agent/Planner to Browser Worker:** every model/tool action is untrusted and
   must satisfy a strict discriminated schema, current opaque reference,
   allowlisted action, budget, and fixed server policy.
4. **Browser Worker to Sandbox Web:** each run owns one isolated context; request
   routing permits only the exact configured local origin and fixed paths.
5. **Page/DOM/screenshot to Agent:** content is data, never policy or authority.
   Fixed server rules classify explicit hostile instructions before subsequent
   effects and redact credential-like forms.
6. **Run state to trace/replay/dashboard:** observation flows outward; no
   telemetry path flows back into authorization, receipt, terminal success, or
   Grader truth.
7. **Tests/evidence to repository:** only closed codes, hashes, counts, statuses,
   latencies, versions, opaque references, and zero-call counters may persist.

## Attacker capabilities and exclusions

The synthetic attacker may control page-visible text, DOM labels, tool/model
text, typed request fields, URL strings, and forwarding headers; may attempt
instruction override, privilege escalation, cross-organization reads, approval
bypass, credential exfiltration, dangerous navigation, downloads, new windows,
and cross-session references.

The attacker cannot execute a real payload, control server rules, create a new
action type, access the Control database from Browser/Planning/Sandbox/Grader,
obtain a real credential, call an external host, or change the frozen fixture at
runtime. Denial-of-service beyond existing bounded budgets and browser-engine
vulnerabilities are outside this deterministic suite.

## Attack paths, mitigations, and tests

| Attack path | Mitigation | Test mapping |
|---|---|---|
| Page says to ignore higher-priority instructions | frozen server rule priority; page hash only; controlled close | taxonomy/fixture unit tests; W14 Compose malicious-page refusal |
| Tool output impersonates system policy | source is always untrusted; fixed `untrusted_instruction` decision | strict decision and tool-source unit cases |
| Model emits injection into a field | typed action plus fixed pre-locator fill rule | policy/runtime tests verify zero locator calls; Compose fill refusal |
| Page/model requests admin role or cross-tenant access | page/model never supplies ActorContext; organization SQL qualifiers | Control adversarial tests and cross-tenant/missing uniform response |
| Page/model requests approval bypass | W11/W12 grant authority and binding remain unchanged | claim-before-approval test; zero outbox/business effect |
| Credential/canary appears in text/error/URL | reject explicit exposure and deterministically redact output | redaction unit vectors and trace/report forbidden-field scan |
| Navigate to other host, dangerous scheme, direct API, or redirect | exact local origin/path policy and request interception | URL-policy and runtime redirect tests; Compose external navigation refusal |
| Download, service worker, popup/new window | downloads/service workers disabled; no arbitrary JS/selector input; closed fixture classification | context-option/schema tests and sandbox fixture safe stop |
| Reuse another session's element/visual reference | per-context opaque references, generation/session checks | existing and W14 cross-session/forged-reference tests |
| Security event influences success or replay | decisions are refusal-only; W13 schema unchanged; Grader remains independent | normal W12 run + `finished_ungraded` + independent grade + W13 export check |

## Decision

Use a small dependency-free Browser Worker module with:

- closed `str` enums for source, category, reason, and outcome;
- strict/frozen Pydantic decision models with `extra=forbid`;
- a frozen ordered rule tuple whose first match deterministically wins;
- canonical sorted-key compact UTF-8 JSON and SHA-256-derived content hashes and
  opaque security references;
- bounded redaction shared by observation text and Browser result/error text;
- no raw-content field, logger call, database write, trace attribute, URL, or
  evidence output.

The DOM observation builder evaluates raw bounded text before returning a safe
observation. A rejection raises an internal closed violation. On a hostile page
reached by navigation, the Browser Runtime closes the isolated session and
returns an existing terminal `action_not_allowed` result with only an opaque
reference; no public W1-W13 response schema is changed. Model-derived fill text
is evaluated before locator invocation. Vision capture receives the same fixed
DOM safety precheck before screenshot generation, even though that content is
not exposed as a Vision observation.

The fixed public fixture is served by the existing Sandbox Web image on one
exact same-origin path. It contains inert text and inert links only: no script,
form submission, real domain, real secret, personal data, or network resource.

W14 adds no database or W13 schema. The normal production smoke proves W13
exports remain byte-contract compatible at schema level and remain an
observation-only record.

## Rejected alternatives

- A dynamic policy language or generic scanner would expand authority and make
  decisions caller/configuration dependent.
- A new security service, queue, or database table would enlarge deployment and
  tenant-query scope without W14 need.
- A real model, public malicious site, penetration tool, or real secret would
  violate deterministic/no-egress and evidence constraints.
- Recording raw DOM or model content for forensics would violate the redaction
  and replay boundary.
- Treating security events or traces as success facts would bypass the frozen
  receipt/terminal/Grader authorities.

## Residual risks

- Pattern rules cover only the closed synthetic taxonomy and do not detect all
  natural-language, obfuscated, multilingual, visual-only, or novel attacks.
- DOM safety inspection cannot prove a browser engine or third-party dependency
  free of vulnerabilities.
- Same-origin Sandbox application compromise and resource-exhaustion testing
  beyond existing budgets are not exhaustive.
- Redaction is defense in depth, not a substitute for preventing real secrets
  from entering the synthetic environment.
- Local/CI results do not establish production hardening, penetration-test
  coverage, legal compliance, certification, vulnerability severity, or a bug
  bounty conclusion.

These risks remain explicit non-claims and candidates for separately authorized
future work; they do not expand W14.
