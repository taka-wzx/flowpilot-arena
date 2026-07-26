# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

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

### Security

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
