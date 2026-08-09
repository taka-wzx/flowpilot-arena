# Contributing to FlowPilot Arena

## Scope first

Read docs/project-roadmap.md, docs/agent-contract.md, and
docs/plans/week-16-release.md before editing. W16 permits only the exact
allowlist in the contract. Preserve W1-W15 product and evidence semantics.

## Local setup

Use Python 3.13 with uv and Node.js 24/npm. Run locked syncs from each project
before its checks; never hand-edit uv.lock or npm lockfiles.

## Review workflow

1. Work only on week/16-release, based on the verified origin/main commit.
2. Amend the contract before adding a path; do not use directory wildcards.
3. Run the listed lint, type, test, Compose, Helm, SBOM, redaction and secret
   checks. Record unavailable tooling honestly.
4. Review staged paths against the exact allowlist and keep unrelated .tmp/
   content untouched.
5. This turn permits one local commit only:
   feat: add W16 release and reproducible demo

Do not push, open a PR, merge, tag, create a Release, change visibility, log in
to a cloud, or run an external Benchmark without separate authorization.

## Data and security

Never add real accounts, personal data, credentials, cookies, Bearer material,
private keys, DSNs, machine paths, arbitrary endpoints, or generated dependency
directories. The Demo uses synthetic values and deterministic-fake-provider/1.0;
real provider/model/OCR/VLM/embedding/billing calls remain zero. The independent
Sandbox database-fact Grader is the sole success authority.
