# W17 evidence — Portfolio Demo Console

## Baseline

- Repository: `taka-wzx/flowpilot-arena`.
- Branch: `codex/w17-portfolio-demo-console`.
- Local W17 start, `HEAD`, and `origin/main` were all verified as
  `1d54afc738cf34a6cec1ebb144368b47a7a4b2dd` before edits.
- Local `v1.0.0` resolves to
  `4795aefe15be66f2405a2b899db7e5764810b8ea`.
- GitHub CLI revalidation confirmed merged PR 55, successful PR CI run
  `31467351190`, successful post-merge main CI run `31468247367`, and the
  published, non-draft, non-prerelease `v1.0.0` Release.

## Implemented surface

- Visible `SYNTHETIC LOCAL DEMO` identity on signed-out and authenticated views.
- Overview for current opaque identity, organization/role, active and terminal
  runs, pending approvals, and audit-chain status.
- Fixed Joiner/Mover/Leaver submissions using existing production-run schema,
  local organization, `generate_plan`, synthetic task reference, and in-memory
  idempotency retry key.
- Strict run list/detail and trace/replay parsing with fail-closed unknown-field,
  taxonomy, ID, ordering, tenant, timestamp, and bound checks.
- Client-side all/active/terminal filter and explicit loading, empty, forbidden,
  failure, trace-unavailable, polling-failure, and stale/timeout states.
- Observe → plan → execute → recover → verify timeline derived only from API
  fields; missing evidence is marked `Not observed`.
- Existing strong-ETag approval flow, stale-decision notice, and audit verify.
- Five-second polling capped at two minutes with terminal, error, page-hide, and
  unmount cleanup plus manual refresh.
- Agent/Grader result separation; `finished_ungraded` is never business success.
- Separate-tab Sandbox link to `http://127.0.0.1:5174`; no iframe.
- Responsive layouts, native semantic controls, visible focus, labels, live
  status, and alert roles.

## Local verification

| Gate | Result | Evidence |
|---|---|---|
| `npm.cmd ci` | passed | 249 packages installed; audit found 0 vulnerabilities |
| `npm.cmd run lint` | passed | ESLint exit 0 |
| `npm.cmd run typecheck` | passed | both TypeScript projects exit 0 |
| `npm.cmd run test` | passed | 6 files, 27 tests |
| `npm.cmd run build` | passed | Vite 7.3.6 transformed 35 modules into repository `dist`; 0.52 kB HTML, 11.44 kB CSS, 244.82 kB JS |
| Compose `config --quiet` | unavailable | installed Docker CLI did not expose a working Compose subcommand and rejected Compose flags; no service was started |
| README command parity | passed | English and Chinese PowerShell blocks match |
| Relative-link check | passed | README English/Chinese and `docs/demo.md` targets exist |
| Required demo wording | passed | both READMEs contain 5173/5174, historical API, JML/Grader and ECS K3s/not-ACK boundaries |
| W12-W17 commit objects | passed | all 17 listed immutable/start commit objects resolve |
| W12-W15 tag targets | passed | exact frozen merge SHAs |
| W15 report byte SHA-256 | passed | `42058cc83d310b51011e4774909b32dab6f3e0370d546c3c7928a5518f86cc00` |
| W15 protocol byte SHA-256 | passed | `42d5439629be60727b7d69324fd5f1c76ba879d2e10fa6bb2d5ad2496901ae41` |
| WorkArena state | passed | remains `unavailable/local_assets_absent` |
| `gitleaks git --no-banner --redact --exit-code 1 .` | passed | 80 commits / 5.77 MB scanned; no leaks |
| `pre-commit run detect-private-key --all-files` | passed | pinned hook exit 0 |
| `git diff --check` | passed | exit 0 |
| Exact changed-path allowlist | passed | 20 changed/new paths, all explicitly authorized |

No W15 Reporting final, W12 formal Validation, external Benchmark, W16 release
workflow, ECS deployment, ACK creation, public ingress, or cloud mutation was
run.

## Changed-path record

~~~text
AGENTS.md
README.md
README.zh-CN.md
docs/agent-contract.md
docs/project-roadmap.md
docs/demo.md
docs/adr/0017-w17-portfolio-demo-console.md
docs/plans/week-17-portfolio-demo-console.md
docs/evidence/week-17-portfolio-demo-console.md
apps/control_web/src/App.tsx
apps/control_web/src/App.css
apps/control_web/src/App.test.tsx
apps/control_web/src/auth.ts
apps/control_web/src/auth.test.ts
apps/control_web/src/runs.ts
apps/control_web/src/runs.test.ts
apps/control_web/src/components/DemoConsole.tsx
apps/control_web/src/components/DemoConsole.test.tsx
apps/control_web/src/components/RunTimeline.tsx
apps/control_web/src/components/RunTimeline.test.tsx
~~~

Package manifests, lockfiles, backend, Compose, Helm, workflows, database, and
migrations are unchanged. Final staged review, PR/CI URLs, squash merge SHA,
post-merge main CI result, remote branch deletion, and final `v1.0.0`
resolution are recorded only after those operations actually complete.

## Unsupported capabilities

The console does not support real providers or accounts, personal data,
arbitrary JSON/URL/Shell/SQL/JavaScript, internal claim/lease/worker endpoints,
raw browser payloads, secrets, production deployment/certification, managed
ACK, production SLO/ROI, external Benchmark, or an independent Grader verdict
from the Control API surface.
