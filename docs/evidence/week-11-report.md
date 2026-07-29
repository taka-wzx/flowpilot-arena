# Week 11 evidence report - HITL, risk, one-time approval, and audit

- Status: local implementation and all required local gates complete
- Branch: `week/11-approval`
- W10 baseline: `9bbb0303c6bc795468b094df676a86dfcbc69dcb`
- Maintenance baseline: `b90cd44ec440eef2d69f12d03890bae57c845e37`
- Maintenance PR #33: open/blocked; run `30440647089`, attempt 1, fourteen zero-step failures from exhausted Actions quota
- Local W11 commit: created after this evidence freeze; final SHA is recorded in the handoff
- W11 remote push/PR/CI/merge/tag/Release: not run
- Real IdP/account/data calls: 0
- Real model/provider/OCR/VLM/embedding calls: 0; cost 0
- Validation: run exactly once; passed
- Reporting execution: false

## Implemented boundary

Control revision `20260729_0002` adds organization-qualified approval
authorities, requests, immutable decisions, hash-only grants/execution claims,
audit heads, and immutable audit events. Closed risk mapping is 2/2/7/5/5 for
L0-L4. L2 requires manager; L3 requires manager plus a different security user;
L4 and unknown actions are permanently denied. Raw grant material is bounded to
Control API memory and is absent from public responses and durable stores.

The synthetic seed is 2 organizations, 16 users/identities/memberships, and 8
authority rows. Realm import SHA-256 is
`b0f11d87a0cce0c78eb324035870060cd675e5134364c85a421f03fd024f1e53`.
Control, Sandbox, and Temporal databases remain separate. Planning, Browser,
and Recovery receive no Control database credential or raw grant material.

## Development observations

Control API passed Ruff, format, strict Mypy, and 57/57 tests after final core
hardening. Control Web passed lint, typecheck, and 10/10 tests. Its locked
install required the executable shim because the PowerShell script shim was
blocked; Vite temp-file creation required the permitted host execution path.

The first W11 Development Compose run built the final images and reached one
incorrect smoke expectation: the stable 422 code is `schema_rejected`. The
smoke expectation was corrected without changing product code or weakening the
gate. The next Development run passed with this closed summary:

| Measure | Observation |
|---|---:|
| risk allow / deny / schema reject | 4 / 2 / 1 |
| approval requests | 4 |
| manager approve / reject | 3 / 1 |
| security approve | 1 |
| self / inactive-or-missing / cross-org reject | 1 / 3 / 1 |
| parameter invalidation | 1 |
| grants issued / claimed / rejected | 3 / 2 / 5 |
| concurrent exactly-one-winner | true |
| pre-approval / duplicate effects | 0 / 0 |
| audit events added | 36 (before final rejection-audit hardening) |
| audit chain / sensitive scan | valid / passed |
| real IdP/model calls / cost | 0 / 0 / 0 |
| Validation / Reporting | false / false |

The Development run started after an earlier partial run had appended 10 valid
events, so its observed head sequence was 46 and its opaque head hash was
`c04f6a3bd8671b2a8202df7fea2fadccb4303831a50f252a8833752e62552655`.
The asserted result is the 36-event delta and verified canonical chain; the
final hardening adds one `grant_rejected` event for an in-organization request
with no grant, so the frozen clean expectation is now 37. The final clean
Validation head is recorded below. The disposable stack was then removed with
its volumes.

## Frozen Validation observation

The only W11 Validation run executed after action/risk schemas, authority,
state/expiry, grant/claim/recovery, audit schema, seed, realm checksum, Compose
profile, and expected counts froze. It passed on its first and only attempt:

| Measure | Validation observation |
|---|---:|
| organizations / users / authorities | 2 / 16 / 8 |
| L0/L1/L2/L3/L4 action counts | 2 / 2 / 7 / 5 / 5 |
| risk allow / deny / schema reject | 4 / 2 / 1 |
| approval requests / decisions | 4 / 5 |
| manager approve / reject | 3 / 1 |
| security approve / reject | 1 / 0 |
| self / inactive-or-missing / cross-org reject | 1 / 3 / 1 |
| parameter-change invalidation | 1 |
| grants issued / claimed / consumed / rejected | 3 / 2 / 0 / 5 |
| concurrent exactly-one-winner | true |
| pre-approval / duplicate side effects | 0 / 0 |
| audit events / head sequence | 37 / 37 |
| audit head hash | `7e8272dcd50c4854273c153c64d72990269a6f56288367c333b1cafcad84eda3` |
| audit verification / sensitive scan | valid / passed |
| real IdP / model calls / cost | 0 / 0 / 0 |
| Validation / Reporting | true / false |

The `consumed` path is exercised in the unit recovery matrix rather than the
public acceptance route: claim, durable resume, receipt completion, and repeat
completion rejection leave one consumed grant at version 3 with one receipt.
The same matrix explicitly covers persistence while Browser/Recovery processes
are absent, pre-claim vault loss, post-claim parameter mismatch, authority
disable before recovery, recovery resume, and receipt replay. W8's complete
crash/retry/Checkpoint/receipt matrix also passed with duplicate side effects 0.

The tamper matrix detected mutation, deletion, insertion, reorder, wrong
previous hash, and truncated/mismatched head. Independent organization chains,
sensitive payload rejection, contiguous genesis/sequence, concurrent one-head
append, immutable decision/event triggers, and cross-tenant list/head/verify
rejection are covered. The result is tamper-evident, not tamper-proof.

## Migration, regression, and application gates

Online Sandbox remained at `20260728_0003 (head)` and online Control reported
`20260729_0002 (head)`; both Alembic checks found no operations. A separate
empty Control PostgreSQL database passed upgrade/current/check, downgrade to
`20260729_0001`, second upgrade/current/check, then was removed. Schema
inspection observed 6 W11 tables, 10 organization-qualified foreign keys, 38
checks, 6 explicit indexes, and two immutable triggers covering both update and
delete. A transaction rollback left 0 rows. Sandbox and Temporal each had 0
W11 tables.

All eight Python applications passed locked sync, Ruff, Ruff format, strict
Mypy, and pytest:

| Application | Tests |
|---|---:|
| Control API | 57 |
| Sandbox API | 35 |
| Browser Worker | 41 |
| DOM Agent | 27 |
| Vision Agent | 20 |
| Hybrid Agent | 31 |
| Planning Agent | 47 |
| Recovery Worker | 12 |

Control Web and Sandbox Web passed locked install, lint, typecheck, tests, and
production build; test counts were 10 and 9. No Python/frontend manifest or
lockfile changed.

The complete stack built and all 15 long-running services were healthy; both
Temporal setup services exited 0. The first full start used a runtime test key
with invalid Base64 padding, so only Recovery Worker exited. The value was
corrected, only that service was recreated, and health plus the entire W8
matrix passed; no code/config/security rule changed. Browser and Recovery were
then restarted together and returned healthy as required.

W4-W11 smokes passed in release order. W4 retained `finished_ungraded` and the
independent grade-30 baseline. W5/W6 remained grade 100 at zero cost. W7 kept
30 templates/90 instances, 18/6/6 split, three Development J/M/L grade-100
results, and frozen catalog/split/Reporting checksums. W8 kept all caps,
`finished_ungraded`, receipt replay, and zero duplicate effects. W9 kept nine
records, five exact ablation hashes, three grade-100 results, and zero provider/
OCR/VLM/embedding calls. W10 kept 4/1 authentication allow/reject, 5/3
authorization allow/reject, 7 cross-organization rejects, one optimistic
winner/one stale rejection, and one safe context projection.

Released Sandbox migrations, W3 catalog, W7 catalog/split/Reporting data, and
W9 context files were byte-identical to the maintenance baseline. The realm
hash matched the frozen W11 value. Compose config passed. CI retained 14 jobs,
added no action dependency or new job, and runs W11 last in the single W4-W11
consolidated job.

## Security, path, remote, and cleanup ledger

The Docker Compose plugin was unavailable; compatible standalone
`docker-compose 5.3.1` was used. The optional buildx plugin was unavailable;
the classic builder completed every build. The global `pre-commit` command was
unavailable, so an isolated pinned runner executed `detect-private-key` and
passed. Gitleaks scanned 48 committed revisions with no leak. PowerShell blocked
the npm script shim, so the same installed `npm.cmd` executable was used.

The contract has 43 exact allowlist paths. Final source/evidence reconciliation
found 42 changed/created paths, 1 allowlisted unchanged path, and 0 outside.
The literal excluded path and every `code_review_agent` repository remained
unaccessed. Final diff, status, staged/unstaged, private-key, Gitleaks, and exact
path checks are rerun after the evidence is staged.

Final `down -v --remove-orphans` removed all disposable services and data.
Project-label enumeration returned containers/networks/volumes = 0/0/0.

No W11 remote push, PR, CI run/job, rerun, workflow dispatch, merge, tag, or
Release occurred. The only referenced remote state is maintenance PR #33 and
its already-existing run `30440647089`, attempt 1, with fourteen quota-caused
zero-step failures. The current Release remains `v0.2.0 - Hybrid + Recovery` /
`w08-recovery`; W10 tag remains `w10-identity`; W11 tag `w11-approval` was not
created.

## Interpretation and W12 boundary

W11 evidence is deterministic synthetic evidence only. It does not establish
real enterprise approval security, legal/compliance audit, tamper-proof
storage, malicious-page resistance, external benchmark quality, production
load/availability/SLO, or ROI. No W12 production worker/API split, load,
release, tag, or Release work has begun.
