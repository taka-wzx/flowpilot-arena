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

### Security

- Added ignored secret-file patterns, pre-commit private-key detection, and a
  CI Gitleaks scan.
- Restricted W2 email fields to `.invalid`, asset tags to `SYN-`, IAM roles to
  ordinary `employee`, and the API surface to non-destructive create/list calls.
