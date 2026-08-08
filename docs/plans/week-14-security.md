# W14 plan - deterministic security suite

## Outcome

W14 closes the roadmap security loop without changing any normal W8/W12/W13
business-success semantics. The deliverable is a fixed local/CI threat suite
that safely rejects hostile page/tool/model instructions before a subsequent
business action, redacts sensitive forms, verifies browser isolation and frozen
Control Plane authority, and proves an unchanged normal production run still
ends `finished_ungraded` before the independent Grader evaluates database facts.

## Frozen baselines

Development starts from `origin/main` at W13 merge
`cedc5f26d41262c955b60854cc69ed4f28baded6`. W12 and W13 commits, tags,
Releases, migrations, evidence, schemas, and normal behavior are immutable.
Formal W12 Validation ordinal 3 is not rerun; ordinal 4 and W15 Reporting are
not created or executed.

## Work packages

1. Freeze W14 authority in `AGENTS.md`, `docs/agent-contract.md`, this plan, the
   ADR, and the evidence shell before implementation.
2. Add a small dependency-free Browser Worker security module with closed
   enums, strict/frozen decisions, fixed rule priority, stable SHA-256 safe
   references, compact canonical JSON, and bounded redaction.
3. Integrate the guard with DOM observation and action-result sanitization.
   Reject model-derived injection text before locator execution; close the
   isolated session on hostile page observation before a subsequent action.
4. Add one exact harmless static Sandbox page containing synthetic hostile
   instructions. It runs only on the existing local Sandbox Web origin and has
   no script, form submission, external reference, credential, or real target.
5. Add Browser unit tests for taxonomy completeness, strict schemas, stable
   decisions, all closed classifications, redaction, URL/scheme/host/redirect
   limits, action precondition safety, context isolation, and controlled stop.
6. Add Control integration tests proving body/header content cannot select
   identity/organization/role, cross-organization/missing reads remain uniform,
   approval/RBAC cannot be bypassed, denied attempts have zero business side
   effect, and unchanged W13 trace/replay remains redacted and non-authoritative.
7. Add a deterministic Compose W14 smoke. It exercises the static hostile page,
   injection fill, forbidden navigation, denied approval claim, tenant
   isolation, one normal frozen production run, `finished_ungraded`, independent
   grading, unchanged W13 export schema, and all real-call counters fixed to
   zero.
8. Run all locally available gates, reconcile this evidence report, verify the
   exact allowlist, explicitly stage only its 19 paths, create the sole local
   commit, and stop before any remote action.

## Acceptance mapping

| Requirement | Implementation/evidence |
|---|---|
| Prompt injection and malicious page | fixed rule table, harmless static fixture, unit and Compose refusal |
| Tool/model output injection | strict typed actions plus pre-locator fill-text rule tests |
| Privilege/cross-tenant/approval bypass | existing authoritative Control routes plus W14 adversarial integration/smoke |
| Secret redaction | bounded redactor, observation/error tests, trace/replay/report forbidden-field scan |
| Browser sandbox | exact origin/path/scheme checks, redirect/request guard, no downloads/service workers, distinct contexts |
| No business side effect | locator call count and Sandbox grade/database-state checks before/after refusals |
| Controlled terminal | closed `safe_stop` decision and closed Browser session with opaque reference only |
| W13 compatibility | unchanged `w13-run-trace-export/1.0`, export hash verification, no schema migration |
| Real-call-zero | smoke report counters for model/provider/OCR/VLM/embedding/billing/egress |

## Validation plan

- `apps/browser_worker`: locked sync, Ruff, format check, mypy, full pytest.
- `apps/control_api`: locked sync, Ruff, format check, mypy, full pytest and
  migration lifecycle where locally available.
- `apps/sandbox_web`: `npm ci`, lint, typecheck, test, build.
- Workflow/YAML policy validation and Compose config.
- Compose build/up/health, W4-W13 deterministic regression, W13 observability
  smoke, then W14 security smoke.
- Sensitive-field scan, exact allowlist review, private-key detection, gitleaks,
  `git diff --check`, staged/unstaged review, and Compose cleanup.

Unavailable tools or infrastructure are recorded as unavailable; they are not
reported as passing. No real network/provider call, remote workflow, external
benchmark, Reporting execution, or formal W12 Validation is part of this plan.

## Stop condition

One local commit only:

~~~text
feat: add W14 security suite and threat model
~~~

Do not push, open a PR, merge, tag, create a Release, or dispatch/rerun CI.
