# ADR 0002: One Sandbox backend with PostgreSQL

- Status: Accepted for W2
- Date: 2026-07-26

## Context

W2 must expose basic HRIS, ITSM, IAM, Asset, and Mail pages and persist enough
synthetic data for a human onboarding flow. The roadmap describes five logical
enterprise applications but explicitly warns against spending the milestone on
five microservices. W1's stateless control API must also remain a narrow health
path rather than absorbing unrelated Sandbox responsibility.

## Decision

Create one `apps/sandbox_api` FastAPI service for all five logical modules and
one `apps/sandbox_web` React/Vite application with five explicit routes. Use
separate relational entities and module-specific endpoints, but one deployment
and one database connection boundary.

Use PostgreSQL as the local Compose database, SQLAlchemy 2 for typed persistence,
and Alembic for a single auditable foundation migration. Unit tests may replace
PostgreSQL with an isolated in-memory SQLite engine to stay deterministic and
fast; runtime and migration acceptance must still use PostgreSQL.

Start a new migrated database empty. Document fixed synthetic values for human
development acceptance rather than adding a generic reset/seed service. This
fixture recipe is not a W3 Arena dataset.

## Consequences

- The five modules are visibly separate at the route, page, endpoint, and table
  levels without multiplying services, builds, or deployment coordination.
- PostgreSQL and Alembic establish the intended persistence semantics early,
  while SQLite-only unit tests do not substitute for the Compose runtime check.
- Sandbox failures cannot change the W1 control API contract.
- W2 deliberately has no authentication, authorization, tenancy, update/delete,
  workflow orchestration, reset semantics, task metadata, or grading.

## Rejected alternatives

- **Five backend services:** too much operational surface for W2 and contrary
  to the roadmap's risk control.
- **Put Sandbox routes in `control_api`:** couples evaluation-environment data
  to the future production control-plane boundary and breaks the W1 stateless
  contract.
- **In-memory-only persistence:** cannot prove migration or durable local state.
- **Generic fixture reset/seed endpoint:** belongs to W3 Arena semantics and
  would prematurely create evaluation behaviour.
