# Week 07 evidence report - Bounded Planning DAG

- Status: local W7 implementation and all locally available gates complete
- Branch: `week/07-planning`
- Baseline: `1b239fc52173bc550f5601d34b8e87efc5dbf45f`
- Real model/provider/OCR/VLM: not run; 0 calls; 0 cost
- Validation tuning: not run; Validation was used only for deterministic schema,
  checksum, and Reset/Seed tests
- Reporting: generated, loaded, schema/checksum-validated, and frozen only; no
  Reset/Seed, grading, Agent run, result inspection, or result-driven change
- Remote write/CI: not run or authorized

## Startup and scope evidence

- Local `main`, `origin/main`, `HEAD`, and dereferenced annotated
  `w06-hybrid` matched the baseline before branch creation. The remote annotated
  tag object `19e74859cb6066837d6708d3ffc618be3b3e00ea` dereferenced to the same
  commit. The eligible worktree was clean.
- Work occurred only on `week/07-planning`. No push, PR, merge, tag, release,
  remote CI trigger, force-push, real-model call, or W8 work occurred.
- The final exact path audit compared Git status with the fenced allowlist in
  `docs/agent-contract.md`: 62 allowed paths, 62 changed paths, and 0 paths
  outside the contract. That allowlist is the exact W7 changed-file set.
- The literal `%SystemDrive%/` path and every `code_review_agent` repository
  remained outside inspection, scan, diff, staging, and modification.

## Architecture and isolation

- `apps/planning_agent` is an independent fake-only FastAPI service containing
  the one-shot deterministic Planner, tool matcher, step Verifier, executor,
  and one monotonic total ledger. It neither imports nor connects to Arena,
  Grader, Reset/Seed, Sandbox API, Postgres, Playwright, or a provider adapter.
- Each run creates exactly one W6 Hybrid Browser Worker session, preserving its
  single Browser/Context/Page for the immutable DAG. All execution uses current
  Worker-issued DOM observation IDs and element references. The session is
  closed from the unconditional `finally` path on terminal, failure,
  cancellation, and budget-exhaustion paths.
- Container inspection observed user `flowpilot-planning`, read-only rootfs,
  `cap_drop: ALL`, `no-new-privileges:true`, PID limit 64, no published port,
  no mount or Docker socket, bounded `noexec,nosuid` tmpfs, and no credential or
  model-key environment variable. Uvicorn access logging is disabled.
- The only attached network was internal, non-attachable `planning-worker`,
  containing only Planning Agent and Browser Worker. Browser Worker resolved;
  Sandbox API, Postgres, Control API, DOM Agent, Vision Agent, and Hybrid Agent
  did not. A bounded public-IP connection probe failed with `connect_ex=101`.

## Planning schemas, DAG, matching, and Verifier

- Strict, frozen, `extra=forbid`, versioned schemas cover plan request/result,
  DAG/step/dependency/conditions, tool match/rejection, plan validation,
  step execution, Verifier request/result, total budget/usage, and run/result.
- Frozen DAG maxima are 16 nodes, 24 edges, depth 8, width 8, 4 dependencies
  per node, and 32,768 canonical serialized bytes. Step objective is capped at
  240 characters and human brief at 4,000 characters. Pages, operations,
  actions, conditions, risk, retry, fallback, states, and reason codes are
  closed enums. Retry is only `no_retry`; fallback is only `stop` or
  `escalate`.
- Validation and smoke tests rejected cycles, self/unknown dependencies,
  duplicate IDs, multiple roots/unreachable nodes, a 17-node plan, cap
  breaches, operation/page/action mismatches, unknown fields, and out-of-order
  execution. Valid plans use lexical deterministic Kahn topology.
- Joiner topology has 6 nodes, 8 edges, depth 3, and width 4. Mover has 3
  nodes, 3 edges, depth 3, and width 1. Leaver has 6 nodes, 8 edges, depth 4,
  and width 3.
- Effective action authority is the intersection of the global closed set,
  current step actions, current page/modality plus Worker-issued actions, and
  remaining budget. Non-navigation actions additionally require the current
  page to equal `expected_page`. Unknown `shell`, step-disallowed actions, page
  mismatch, modality/Worker mismatch, and exhausted budgets fail closed.
- Verifier consumes only the current bounded step condition, current Worker
  observation generation/page, current action result, and the same ledger. Its
  outcomes are only `verified`, `not_verified`, or `inconclusive`; a forced
  inconclusive result terminated the run and was not promoted to success.
  Results contain no score, passed, or success field; finish remains
  `finished_ungraded` and independent database-fact grading remains external.

## Unified W6 and W7 budgets

- Planning, matching, Browser Worker actions, observation accounting,
  verification, and termination share one ledger created once per run from
  monotonic time. No route, step, probe, or terminal path creates a replacement
  ledger.
- The ledger retains W6 caps for 24 actions/model calls/DOM observations/images,
  2 switches, DOM/compressed/image/token/cost limits, and 300 monotonic seconds,
  while adding one plan generation, DAG metrics, 64 tool matches, 16 tool
  rejections, 16 verifier calls/probes, and 16 executed/blocked steps. Fake
  planning and Verifier calls charge the same model/token totals; all cost
  counters remained zero.

## JML catalog freeze and use

- Packaged generation produced exactly 30 templates and 90 stable instances:
  12 Joiner, 8 Mover, and 10 Leaver templates; three deterministic variants
  each; template splits 18 Development, 6 Validation, and 6 Reporting.
- Catalog checksum:
  `62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f`
- Split manifest checksum:
  `1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee`
- Reporting manifest checksum:
  `c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6`
- Two independent loads reproduced all 90 distinct instance IDs/checksums. All
  72 non-Reporting instances received two equal Reset/Seed results. The 18
  Reporting instances were generated and checksum-frozen only. The W3 catalog
  remained 10 tasks with checksum
  `e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9`
  and its released 6/2/2 split unchanged.
- Data is original Apache-2.0 synthetic FlowPilot content using `.invalid`
  addresses and `SYN-` identifiers. No real person, account, credential,
  endpoint, or business fact was introduced.

## Sandbox and database increment

- Database schema/migration increment: none. `alembic upgrade head`, `current`,
  and `check` observed existing revision `20260726_0002 (head)` and no drift.
  Therefore no downgrade/upgrade round-trip was applicable.
- Using existing typed fields only, Sandbox gained task-owned HRIS
  transfer/disable, ITSM close, IAM revoke, Asset release, and Mail disable
  API/UI transitions. There is no DELETE route, generic patch, arbitrary data
  update, physical deletion, or Planning Agent direct API/database access.
- Tests observed valid prior-state transitions, conflict on repeated or invalid
  transitions, unknown-field rejection, decoy preservation, task ownership,
  and independent Leaver grading after all five typed transitions.
- During development the newly visible transition controls caused the first W5
  geometric fake to select the wrong button. The bounded fix keeps transition
  forms collapsed behind a leading `Show transitions` button; W7 explicitly
  opens them. Final W4, W5, and W6 regressions all passed with unchanged API
  semantics.

## Deterministic fake baseline results

These results prove only deterministic wiring, validation, isolation, and fake
execution. They are not evidence of real planning, reasoning, Verifier, DOM,
Vision, Hybrid, OCR, or VLM capability.

- W4 DOM: `w3-joiner-001`, seed
  `c4f4cd863b43b93e6e131e9938e18f640c3036d188554d28f2058aaaa9445f07`;
  2 actions/steps, 2 fake model calls, 72 tokens, `finished_ungraded`;
  independent grade 30/100, `passed=false`.
- W5 Vision: untouched independent grade 30/100, `passed=false`; fresh
  completion 20 actions/steps, 20 fake calls, 960 tokens, 20 images, 599,834
  bytes, 10,368,000 pixels, 518 ms capture, 0 cost, `finished_ungraded`;
  independent grade 100/100, `passed=true`.
- W6 Hybrid: untouched immediate finish used 1 action/step, 1 fake call, one
  DOM observation (12,171 raw / 7,204 compressed bytes), no image/switch, and
  independently graded 30/100, `passed=false`. Fresh completion used 20
  actions/steps, 20 fake calls, 960 tokens, 2 DOM observations (24,463 raw /
  7,204 compressed bytes), 19 images (569,127 bytes / 9,849,600 pixels), 463
  ms capture, one actual DOM-to-Vision switch, and 0 cost; independent grade
  100/100, `passed=true`.
- W7 paired W3 baseline used the same task, brief, and seed checksum: W6 had
  one switch and grade 100; W7 immediate finish independently graded 30 with
  `passed=false`; W7 completion had 6 deterministic-topology steps, 22 Worker
  actions, 6 Verifier calls plus one probe, one rejected unknown tool, and
  independent grade 100 with `passed=true`. Both Agent completions returned
  `finished_ungraded`.
- W7 Development Joiner `w7-jml-joiner-001-v1`: checksum
  `47fbb29507e69a984d57ab9a73266d9e112572f37f72642d6014dd5f7712071a`,
  untouched 20, 22 actions, 6 Verifier calls, final independent grade 100.
- W7 Development Mover `w7-jml-mover-001-v1`: checksum
  `6402ff690adb72af7045643a206822687f901ee477d54920fec9850b26af1449`,
  untouched 60, 14 actions, 3 Verifier calls, final independent grade 100.
- W7 Development Leaver `w7-jml-leaver-001-v1`: checksum
  `a90b27cc7f2ee81e99f9aa83c11b9a01092008a852a2c063ef7750e91da6325d`,
  untouched 0, 23 actions, 6 Verifier calls, final independent grade 100.
- Every W7 completion returned `finished_ungraded`; each selected Development
  instance had two equal Reset/Seeds, an untouched `passed=false` grade, and a
  fresh independent 100/100 `passed=true` grade. External calls/cost were 0/0.

## Local gates

- Python 3.13 locked sync, Ruff, Ruff format, Mypy strict, and pytest passed for
  all seven services. Test counts: Control API 1, Sandbox API 33, Browser Worker
  39, DOM Agent 27, Vision Agent 20, Hybrid Agent 31, Planning Agent 24 (175
  total). Planning Agent was rerun after final matcher/logging hardening.
- Control Web and Sandbox Web `npm ci`, lint, typecheck, tests, and production
  build passed. Tests were 1 and 9 respectively; both npm audits found 0
  vulnerabilities. `npm.cmd` was used because local PowerShell policy blocks
  the `npm.ps1` shim.
- `docker compose` plugin was unavailable. Standalone `docker-compose` parsed
  the configuration, built and started all 10 default W1-W7 services, and all
  became healthy. Compose reported its Buildx plugin unavailable but completed
  every build with the classic builder; acceptance meaning was unchanged.
- W4 DOM, W5 Vision, W6 Hybrid, and W7 Planning Compose smokes all passed.
  W3 checksum/split and W7 catalog/split/checksum tests passed.
- Planning container and network inspection/probes passed as recorded above.
  Final `down -v --remove-orphans` completed; label-filtered inspection found 0
  project containers, 0 project networks, and 0 project volumes.
- Final post-commit `gitleaks git --no-banner --redact --exit-code 1 .`
  passed: 41 commits and approximately 2.21 MB scanned, no leaks found.
  `git diff --check` passed.
- `pre-commit` was unavailable on this host, so
  `pre-commit run detect-private-key --all-files` was not run and is not
  claimed as passed.
- Final exact allowlist audit passed (62/62, outside 0). Explicit staged and
  unstaged diff review passed with 62 staged paths, 0 unstaged paths, and no
  staged or unstaged whitespace error immediately before the local commit.
- No current remote GitHub Actions run was triggered or claimed. The known W6
  post-merge run remains historical baseline evidence only.

## Known limitations and W8 boundary

W7 is deterministic fake wiring over five fixed synthetic pages. It has no
runtime retry, partial replanning, checkpoint, recovery, idempotency, Temporal,
fault injection, memory/retrieval, identity/RBAC, approval/HITL, production
worker, observability platform, malicious-page suite, external benchmark,
real model, provider egress, enterprise integration, or ROI claim. Validation
was not tuned and Reporting was not executed. Those recovery capabilities begin
only under a separate W8 contract; this branch stops after W7.
