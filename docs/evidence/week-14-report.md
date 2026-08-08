# W14 evidence report - security suite and threat model

## Scope and baseline

- Branch: `week/14-security`
- Base: W13 merge `cedc5f26d41262c955b60854cc69ed4f28baded6`
- W12/W13 published baselines: unchanged
- Expected local commit: `feat: add W14 security suite and threat model`
- Formal W12 Validation ordinal 3 rerun: no
- Ordinal 4 created: no
- W15 Reporting/external benchmark: not executed
- Remote push/PR/merge/tag/Release/workflow action: not authorized

This report was initialized before implementation as required by the W14
contract and reconciled after the locally available gates below. An unavailable
entry is not a pass.

## Security evidence schema

Persisted W14 evidence is limited to closed outcome/category/reason codes,
fixture/content SHA-256 values, counts, HTTP statuses, bounded latencies,
versions, opaque security/run/trace/audit references, independent Grader boolean,
and real-call-zero counters. It contains no raw page, DOM, screenshot, model or
tool content; no Bearer/approval material, Cookie, password, private key, DSN,
personal data, real secret, URL query, or machine path.

## Implementation evidence

Status: implemented within the 19-path exact allowlist, with no dependency,
lockfile, migration, database, service, or W13 schema change.

- Closed taxonomy: 11 categories including `none` and
  `controlled_safe_stop`; closed source/reason/outcome enums; strict/frozen
  decision model with unknown fields rejected.
- Frozen fixture file SHA-256:
  `2e13739965e202e10102a3d7c39e60a54430426c28baeba2dcb2e2e062838fd2`.
- Normalized fixture content SHA-256:
  `f4feda4bcc3bc8ceedbffcb187ba4ac2221104f04bb527d56935c5ac30cb1902`.
- Fixture decision: `prompt_injection` / `instruction_override` / `safe_stop`;
  opaque reference `sec_b84d6547fad7e34c576b4460`;
  `business_side_effects=0`; `real_egress_calls=0`.
- Browser tests prove injection fill is rejected before any locator call;
  hostile-page observation closes the isolated session; forbidden host and
  redirect paths remain rejected; download and popup handlers are installed;
  distinct-session context and forged/stale-reference tests remain green.
- Redaction vectors cover authorization/cookie/password/key/DSN forms, URL
  userinfo/query/fragment, reserved-domain personal-data examples, canary
  fragments, and machine-path forms. Non-deliverable `.invalid` synthetic data
  remains usable so frozen normal fixtures are not altered.
- Control adversarial tests prove unknown identity/organization/role/approval/
  success body fields fail strict validation, an auditor cannot submit work,
  forwarding headers cannot select authority, claim-before-approval creates no
  outbox row, and cross-organization/missing reads remain uniform.
- The same Control test exports unchanged `w13-run-trace-export/1.0`, verifies
  its canonical export hash, and proves the runtime canary and sensitive field
  forms are absent.
- The W14 Compose smoke implementation additionally checks a normal frozen
  production run remains `finished_ungraded` until the independent Grader,
  along with W13 replay compatibility and real-call-zero. The passing run
  reported fixture reference `sec_e23af1463b7679c8c539626b`, injection
  reference `sec_7a2523388facb6aec826d804`, security latency `4933` ms,
  `security_business_side_effects=0`, and result hash
  `076b972c38152db69cb6d525bccf80ec884db430daab6db67d906904098b7860`.

## Local quality gates

| Gate | Result | Closed evidence |
|---|---|---|
| Browser Worker locked sync/Ruff/format/mypy/pytest | passed | 56 passed; Ruff, format, and mypy clean; one pre-existing dependency deprecation warning |
| Control API locked sync/Ruff/format/mypy/pytest | passed | 68 passed; Ruff, format, and mypy clean; one pre-existing dependency deprecation warning |
| Integration smoke locked sync/Ruff/format/mypy | passed | W14 script locked, linted, formatted, and typed |
| Sandbox Web npm ci/lint/typecheck/test/build | passed with dependency warning | 9 passed; lint/typecheck/build passed; locked audit reported 2 high-severity dependency findings, not auto-fixed or lockfile-edited |
| YAML/workflow and Compose configuration | passed | both YAML files parsed; standalone Compose v5 configuration resolved |
| Compose build/up/health | passed with tooling warning | classic builder completed all images; all base services healthy; installed standalone Compose v5 warned that the buildx plugin was absent |
| Control empty upgrade/current/check/downgrade/upgrade | passed | W10 through W13 migrations reached `20260803_0004`; no W14 migration; both checks clean |
| W3/W7 catalog freezes | passed | 10 W3 tasks; 30 templates; 90 instances; 18/6/6 split; frozen checksums matched |
| W4-W13 backend unit regression | passed with two unavailable replay cases | Sandbox 35, DOM 27, Vision 20, Hybrid 31, Planning 53, bounded Recovery 12, Workflow 24; two Temporal replay cases require an external test-server binary and were not downloaded |
| W4-W13 Compose regression and W13 smoke | passed | W4 through W13 development/synthetic smokes exited zero; W13 produced 21 ordered events and replay steps, `finished_ungraded`, independent grade pass, and all real-call counters zero; formal W12 Validation was not rerun |
| W14 deterministic local security suite | passed | full Browser and Control suites plus 15 focused taxonomy/redaction/fixture tests passed |
| W14 deterministic Compose security smoke | passed after assertion and cold-start dependency corrections | fresh empty-stack run: hostile page/injection safely stopped; approval bypass and cross-tenant read false; business side effects zero; normal terminal `finished_ungraded`; independent Grader true; unchanged W13 export; sensitive fields false; all real-call counters zero |
| product real-call-zero proof | passed | W9, W10, W11, W12, W13, and W14 Compose outputs report zero real provider/model/OCR/VLM/embedding/billing/account/egress calls |
| exact sensitive-value scan | passed | zero committed value-pattern matches across W14 code/tests/fixture |
| detect-private-key | passed, exact W14 allowlist | scoped form used to preserve the prohibited literal-path boundary |
| gitleaks Git history | passed | 55 commits, approximately 4.06 MB, no leaks |
| exact allowlist and `git diff --check` | passed | exactly 19 W14 paths; no unexpected source path; whitespace check clean |
| worker restart/health and Compose cleanup | passed | Browser, Recovery, and Workflow workers restarted healthy; profile container, base containers, networks, and volumes removed |
| staged gitleaks and exact staged review | passed | exactly 19 allowlisted paths, no unstaged controlled-path drift, staged diff check clean; approximately 85 KB scanned with no leaks |

The sole local commit is intentionally created only after this final evidence
reconciliation is staged. Its completion is verified from local Git history
and reported in the handoff, rather than claimed here before the action occurs.

The Docker CLI lacked its `docker compose` plugin, so installed standalone
Compose v5 was used. Docker Desktop required a delayed startup and sandbox
escalation before its engine became available; after that, build, up/wait,
migrations, W4-W14 smokes, worker restart/health, and down/volume/orphan cleanup
all completed. The classic builder emitted a buildx-plugin warning but built
the images successfully.

The first W14 smoke attempt reached the approval-bypass check but asserted the
generic `conflict` code. The frozen W11/W12 authority correctly returned the
more specific closed code `grant_rejected`; only the smoke assertion was
corrected, and the second W14 attempt passed. No implementation or business
semantics changed in response to the failed development smoke.

A subsequent fresh-stack run exposed that the new W14 Compose profile waited
for Workflow Worker but did not start the existing Recovery Worker that owns
the Temporal activities used by the frozen normal production path. The W14
smoke dependency was corrected to require the existing healthy Recovery
Worker, which transitively starts its existing Planning/Temporal dependencies;
no W8-W13 service definition or success semantics changed. The first startup
after that correction encountered a stale stopped profile container referring
to a removed local Docker network because a non-profile cleanup did not remove
it. Profile-aware cleanup removed that local artifact. A genuinely empty-stack
rerun then passed in 4933 ms with zero security-path business side effects and
all real-call counters zero, followed by complete profile-aware cleanup.

The two Recovery replay failures were infrastructure-only: the Temporal SDK
requested an uncached external test-server binary while W14 external egress was
disabled. The remaining 12 Recovery tests passed in a bounded rerun. No attempt
was made to weaken the tests or enable real product egress.

## Limitations and non-claims

W14 is deterministic local/CI synthetic security testing. It is not a
production security certification, penetration test, legal/compliance
statement, third-party vulnerability assessment, vulnerability-bounty
conclusion, or proof against unknown/obfuscated attacks. Unavailable tools will
be listed explicitly without weakening a gate or claiming it passed.

The locked Sandbox Web dependency tree currently reports two high-severity
audit findings. W14 does not hand-edit the lockfile or run an unreviewed
automatic dependency fix; remote delivery should triage them as a separate,
reviewed dependency update before accepting the PR gate.
