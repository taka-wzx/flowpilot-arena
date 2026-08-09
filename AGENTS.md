# FlowPilot Arena agent guide

## Current phase and immutable baselines

This branch is W16: Release and Reproducibility on `week/16-release`. The
authoritative W16 contract is `docs/agent-contract.md`; the roadmap is
`docs/project-roadmap.md`. W12-W15, the two security-maintenance merges, and
their tags/releases are immutable:

- W12 merge `2c642a67341d0cd1c9c62b6bf883ad8df2853f40`, tag `w12-production`.
- W13 merge `cedc5f26d41262c955b60854cc69ed4f28baded6`, tag `w13-observability`.
- W14 merge `6bd960a031069f262fe60fbbb8bf2c65a09e409b`, tag `w14-security`.
- W15 merge `94e5a8d74b970c93c9610725dad7cb352545f654`, tag `w15-evaluation`.
- PR 43 merge `697c8b8b9a6b4c25b571e7b0dbf6c01bcb82bbf3`.
- PR 44 merge/origin main `078eb22deb137191660a5511c496fd1dff2b74f3`.

Do not rewrite, roll back, retag, rerelease, or otherwise modify those
objects. W15's report, protocol, configuration, schema, and all hashes remain
frozen. Work only on `week/16-release`, created from the verified
`origin/main` above.

## W16 authority boundary

W16 is limited to local release packaging, a namespace-scoped Helm chart,
deterministic synthetic-demo documentation/runner, bilingual documentation,
SBOM generation/status, release notes, and evidence. It does not change any
W1-W15 API, database, migration, identity, tenant, RBAC, approval, audit,
queue/rate/lease/fence, receipt/idempotency, trace/replay, security, Arena, or
independent-Grader semantics. `finished_ungraded` remains the Agent terminal
state and only the Sandbox database-fact Grader determines business success.

No real provider, IdP, model, OCR, VLM, embedding, billing, account, personal
data, secret, arbitrary URL/API/Shell/SQL/JavaScript capability, or external
Benchmark is allowed. WorkArena remains `unavailable/local_assets_absent`.
Helm rendering/local Compose is never cloud deployment or production
certification. Do not log in to a cloud, create resources/DNS/TLS, incur cost,
change repository visibility, push, open a PR, merge, tag, release, dispatch or
rerun CI. The only authorized repository mutation after validation is one
local commit with subject:

    feat: add W16 release and reproducible demo

The literal `%SystemDrive%/` path and every `code_review_agent` repository are
outside scope. Do not inspect, enumerate, scan, modify, delete, or stage them;
preserve unrelated `.tmp/` content.

## Exact W16 file allowlist

Only the following exact paths may be created or modified. Directory
wildcards are forbidden; add a path here before changing it.

~~~text
AGENTS.md
README.md
README.zh-CN.md
CONTRIBUTING.md
SECURITY.md

docs/agent-contract.md
docs/architecture.md
docs/benchmark-card.md
docs/demo.md
docs/model-card.md
docs/release-notes-v1.0.0.md
docs/sbom.spdx.json
docs/sbom-status.md
docs/adr/0016-w16-release.md
docs/plans/week-16-release.md
docs/evidence/week-16-release.md

deploy/helm/flowpilot-arena/Chart.yaml
deploy/helm/flowpilot-arena/values.yaml
deploy/helm/flowpilot-arena/values.schema.json
deploy/helm/flowpilot-arena/templates/_helpers.tpl
deploy/helm/flowpilot-arena/templates/configmap.yaml
deploy/helm/flowpilot-arena/templates/deployment.yaml
deploy/helm/flowpilot-arena/templates/networkpolicy.yaml
deploy/helm/flowpilot-arena/templates/NOTES.txt
deploy/helm/flowpilot-arena/templates/service.yaml
deploy/helm/flowpilot-arena/templates/serviceaccount.yaml
deploy/helm/flowpilot-arena/templates/tests/test-connection.yaml

scripts/generate_sbom.py
tests/integration/w16_demo.py
tests/integration/test_w16_demo.py
tests/integration/w16_demo_smoke.py
~~~

The W15 frozen files are not modified or rerun in Reporting mode. No new
dependency, lockfile, service, database, migration, network capability,
container image, or cloud resource may be added without separate user
authorization. If Helm, kind/k3d, SBOM, recording, or cloud tooling is absent,
record `unavailable` in the evidence; never claim it passed.

## Required verification

Run available locked dependency syncs, Ruff, format, strict mypy, pytest,
frontend npm checks, YAML/workflow policy checks, Helm lint/schema/deterministic
render and Kubernetes security scans, Compose config/build/up/health and
cleanup, migration empty upgrade/current/check/downgrade/upgrade, W4-W15
regression, W13/W14 smokes, the W15 Development-only smoke, W16 demo smoke,
W15 hash immutability, real-call/cost-zero and sensitive-field scans, SBOM
schema/checksum/license/secret checks, README/link/command checks,
detect-private-key, gitleaks, `git diff --check`, and exact allowlist/staged
review. Do not run W15 frozen Reporting final, W12 formal Validation, an
external Benchmark, or real cloud deployment.

Finish with local forms of:

~~~powershell
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
pre-commit run detect-private-key --all-files
gitleaks git --no-banner --redact --exit-code 1 .
git diff --check
git diff -- . ':(exclude)%SystemDrive%'
git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%'
~~~

Record unavailable tooling and unexecuted cloud/publication steps honestly.
After the single local commit, stop and report changed paths, reproduction
status, documentation/demo/SBOM/public-readiness results, verification,
unavailable items, and the separately authorized remote/cloud steps.
