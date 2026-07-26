# Contributing to FlowPilot Arena

## Start with scope

Read [docs/project-roadmap.md](docs/project-roadmap.md),
[docs/agent-contract.md](docs/agent-contract.md), and the active weekly plan
before changing code. W1 work is restricted to the contract allowlist. Do not
turn a foundation task into a Sandbox, agent, browser, model, workflow, or
evaluation implementation.

## Local setup

Use Python 3.13 with `uv` for the API and Node.js 22.12+ with npm for the web
application.

```powershell
Push-Location apps/control_api
uv sync --locked --all-groups
Pop-Location

Push-Location apps/control_web
npm ci
Pop-Location
```

On Windows systems that block `npm.ps1`, use `npm.cmd` instead.

## Change workflow

1. Start from the relevant weekly branch; never develop directly on `main`.
2. Keep the change within that week's written contract. Amend the contract
   before adding a necessary W1 path; seek direction when the change broadens
   the milestone.
3. Make small, reviewable commits using a Conventional Commit-style message,
   for example `feat: add control API health check`.
4. Run the checks listed in the weekly plan and include the observed results in
   the evidence report.
5. Open a PR only after review is ready. Do not push, merge, force-push, or tag
   without the required authorization.

## Required review material

Every weekly PR must include:

- the weekly plan and task contract;
- an exact changed-file list;
- architecture/ADR rationale when the structure changes;
- lint, type-check, test, build, Compose, and secret-scan results;
- screenshots or traces only when the current week actually creates them;
- known limitations and items intentionally deferred to the next week;
- whether any paid model was used and its actual cost.

W1 must report zero paid-model calls and zero real enterprise-system calls.

## Code and data rules

- Keep Python type annotated and pass Ruff, mypy, and pytest.
- Keep TypeScript strict and pass ESLint, TypeScript, Vitest, and Vite build.
- Update both manifest and lockfile together.
- Never add credentials, personal data, private local paths, or generated
  dependency directories.
- Do not stage unrelated files. In particular, `%SystemDrive%/` is not part of
  this project and must remain untouched.

## Release convention

After an authorized PR merge to `main`, create the annotated tag named by the
roadmap (W1: `w01-foundation`). Pushing the branch or tag remains an explicit
authorization step.
