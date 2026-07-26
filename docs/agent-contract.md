# W2 agent contract — Sandbox Foundation

## Authority and objective

This contract translates the W2 row of
[project-roadmap.md](project-roadmap.md) and the user-authorized W2 brief into a
bounded implementation agreement for `week/02-sandbox`.

The sole outcome is a local synthetic enterprise Sandbox in which a human can
create or confirm an employee, open an onboarding ticket, create a basic user
account, assign a device, create a mailbox, and inspect the resulting state in
five web modules. It is not an automated Arena or an Agent implementation.

## Baseline observed before W2 edits

- W1 is merged at `1c23f79` and tagged `w01-foundation`.
- `main` and `origin/main` were synchronized with `git pull --ff-only`.
- `week/02-sandbox` already existed at the synchronized W1 commit and was
  reused as the independent weekly branch.
- The only status entry was the pre-existing untracked `%SystemDrive%/`, which
  remains excluded and untouched.
- Python 3.13 is the user-authorized repository baseline.

## Recorded architecture assumptions

1. “One backend” means one new `apps/sandbox_api` service for all five modules,
   not five microservices and not an expansion of the W1 control API.
2. Five applications are represented as explicit `/hris`, `/itsm`, `/iam`,
   `/assets`, and `/mail` routes within one `apps/sandbox_web` build. Separate
   subdomains and module-specific authorization are deferred.
3. PostgreSQL is the local runtime database; SQLAlchemy 2 and Alembic own the
   schema. In-memory SQLite is permitted only for isolated unit tests.
4. W2 starts from an empty migrated database. The manual guide supplies fixed,
   obviously synthetic example values, but there is no generic Reset, task
   Seed, task specification, or grader. This example is not a W3 resettable
   Arena dataset.
5. W2 account and asset actions are direct manual Sandbox operations. The
   roadmap's approval and RBAC semantics remain W10/W11 concerns and are not
   simulated early.
6. CRUD breadth is limited to creation and listing needed for the frozen
   onboarding closure. Update/delete, mover/leaver flows, paging, search, and
   workflow orchestration are deferred.

## Exact W2 file allowlist

Only the following paths may be created or modified in W2:

```text
AGENTS.md
README.md
CHANGELOG.md

.github/dependabot.yml
.github/workflows/ci.yml

docs/agent-contract.md
docs/architecture.md
docs/threat-model.md
docs/adr/0002-w2-single-sandbox-postgres.md
docs/plans/week-02-sandbox.md
docs/evidence/week-02-report.md

apps/sandbox_api/.dockerignore
apps/sandbox_api/Dockerfile
apps/sandbox_api/alembic.ini
apps/sandbox_api/pyproject.toml
apps/sandbox_api/uv.lock
apps/sandbox_api/migrations/env.py
apps/sandbox_api/migrations/script.py.mako
apps/sandbox_api/migrations/versions/20260726_0001_sandbox_foundation.py
apps/sandbox_api/src/flowpilot_sandbox_api/__init__.py
apps/sandbox_api/src/flowpilot_sandbox_api/database.py
apps/sandbox_api/src/flowpilot_sandbox_api/main.py
apps/sandbox_api/src/flowpilot_sandbox_api/models.py
apps/sandbox_api/src/flowpilot_sandbox_api/schemas.py
apps/sandbox_api/tests/conftest.py
apps/sandbox_api/tests/test_api.py
apps/sandbox_api/tests/test_models.py

apps/sandbox_web/.dockerignore
apps/sandbox_web/Dockerfile
apps/sandbox_web/nginx.conf
apps/sandbox_web/eslint.config.js
apps/sandbox_web/index.html
apps/sandbox_web/package.json
apps/sandbox_web/package-lock.json
apps/sandbox_web/tsconfig.json
apps/sandbox_web/tsconfig.app.json
apps/sandbox_web/tsconfig.node.json
apps/sandbox_web/vite.config.ts
apps/sandbox_web/src/App.tsx
apps/sandbox_web/src/App.css
apps/sandbox_web/src/App.test.tsx
apps/sandbox_web/src/api.ts
apps/sandbox_web/src/index.css
apps/sandbox_web/src/main.tsx
apps/sandbox_web/src/setupTests.ts
apps/sandbox_web/src/types.ts
apps/sandbox_web/src/vite-env.d.ts
apps/sandbox_web/src/pages/HrisPage.tsx
apps/sandbox_web/src/pages/ItsmPage.tsx
apps/sandbox_web/src/pages/IamPage.tsx
apps/sandbox_web/src/pages/AssetPage.tsx
apps/sandbox_web/src/pages/MailPage.tsx

deploy/compose/compose.yaml
```

Any newly necessary file must be added here before it is changed. A path that
broadens the W2 objective requires user direction rather than an implicit
contract edit.

## Required data and observable closure

The minimum persistent entities are:

- HRIS employee profile;
- ITSM onboarding ticket linked to an employee;
- IAM ordinary account with one basic role linked to an employee;
- Asset device assignment linked to an employee;
- Mail mailbox linked to an employee.

The frozen manual closure is:

1. Create the synthetic HRIS employee and observe its numeric identifier.
2. Create an ITSM onboarding ticket for that identifier.
3. Create an active ordinary IAM account with the basic employee role.
4. Assign one synthetic laptop asset to the employee.
5. Create an active synthetic mailbox for the employee.
6. Revisit all five routes and confirm the linked records and statuses.

## Explicit prohibitions

W2 must not contain W3 task specs, general Reset/Seed, deterministic graders,
human-baseline tools, splits, faults, or Arena execution; W4 browser automation
or Agent behaviour; W5 vision/OCR/VLM; W7+ planning, verification, approval,
memory, recovery, Temporal, or workers; W10 identity, RBAC, tenant isolation;
real enterprise integrations, real accounts or personal data; paid model or
external API calls; arbitrary shell execution; queues, object storage,
Keycloak, or monitoring infrastructure.

## Handoff and Git rules

- Keep W1 control paths working and unchanged unless a regression fix is first
  added to this allowlist.
- Do not access `code_review_agent` or `%SystemDrive%/`.
- Do not push, create a PR, merge, or tag without explicit authorization.
- Create a local commit only after all available W2 acceptance gates pass and
  the evidence report is updated with observed facts.
- Stop at W2 completion.
