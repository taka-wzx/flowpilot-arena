# FlowPilot Arena agent guide

## Current phase and immutable baselines

This branch is the authorized W16 Private-image gate remediation on
`codex/w16-private-image-remediation`. The
authoritative W16 contract is `docs/agent-contract.md`; the roadmap is
`docs/project-roadmap.md`. W12-W15, the two security-maintenance merges, and
their tags/releases are immutable:

- W12 merge `2c642a67341d0cd1c9c62b6bf883ad8df2853f40`, tag `w12-production`.
- W13 merge `cedc5f26d41262c955b60854cc69ed4f28baded6`, tag `w13-observability`.
- W14 merge `6bd960a031069f262fe60fbbb8bf2c65a09e409b`, tag `w14-security`.
- W15 merge `94e5a8d74b970c93c9610725dad7cb352545f654`, tag `w15-evaluation`.
- PR 43 merge `697c8b8b9a6b4c25b571e7b0dbf6c01bcb82bbf3`.
- PR 44 merge/origin main `078eb22deb137191660a5511c496fd1dff2b74f3`.
- W16 PR 45 merge/origin main
  `d1b03993fc912179d3cdbef00b9f26f524ca9c52`.
- W16 closure PR 46 merge/origin main
  `aab7efed479ad208ced4786ff43f8e72e4f1c458`.
- W16 Private-workflow compatibility PR 47 merge/origin main
  `7661db412fde625ec0a6ff81261d26343cf53052`.

Do not rewrite, roll back, retag, rerelease, or otherwise modify those
objects. W15's report, protocol, configuration, schema, and all hashes remain
frozen. Work only on `codex/w16-private-image-remediation`, created from the
verified W16 compatibility merge on `origin/main` above.

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
change repository or package visibility, tag, or release. The user has
separately authorized this image-gate remediation branch, push, PR, normal CI,
squash merge, and one new Private GHCR candidate-image workflow dispatch after
merge. The remediation must remain pre-publication and must stop before any
`v1.0.0` tag or GitHub Release. The authorized repository mutation is one
commit with subject:

    fix: remediate W16 private image gates

The literal `%SystemDrive%/` path and every `code_review_agent` repository are
outside scope. Do not inspect, enumerate, scan, modify, delete, or stage them;
preserve unrelated `.tmp/` content.

## Exact Private-image-remediation allowlist

Only the following exact paths may be created or modified. Directory
wildcards are forbidden; add a path here before changing it.

~~~text
AGENTS.md
.github/workflows/release-images.yml
apps/control_api/Dockerfile
apps/control_web/Dockerfile
apps/sandbox_api/Dockerfile
apps/sandbox_web/Dockerfile
docs/agent-contract.md
docs/evidence/week-16-release.md
docs/release-notes-v1.0.0.md
docs/sbom-status.md
docs/sbom.spdx.json
~~~

The W15 frozen files are not modified or rerun in Reporting mode. No new
dependency, lockfile, service, database, migration, network capability, or
cloud resource may be added without separate user authorization. This
remediation is authorized to publish only four Private `linux/amd64` candidate
images in the `ghcr.io/taka-wzx` namespace: `flowpilot-arena-control-api`,
`flowpilot-arena-sandbox-api`, `flowpilot-arena-control-web`, and
`flowpilot-arena-sandbox-web`. Images use only `sha-<40-hex-merge-commit>`
tags; `latest` and `v1.0.0` are forbidden in this phase. The four release
Dockerfiles may change only to checksum-pin official linux/amd64 base images,
update the container-only uv installer, and clear the exact registry
HIGH/CRITICAL gate without a waiver. Buildx
`provenance: mode=max` and `sbom: true` remain mandatory. GitHub native
Artifact Attestations are `unavailable/private-plan`; do not request
`attestations: write`, `id-token: write`, or `actions/attest` in this Private
workflow. If an authorized Helm, kind, Syft, Trivy, or VHS verification cannot
execute, record `unavailable`; never claim it passed.

## Required verification

Run YAML parsing, actionlint, workflow policy checks, all four locked image
builds, non-root/read-only Web health, backend health, exact Trivy
HIGH/CRITICAL and secret gates, Syft/SPDX validation, Helm lint/render and
kind lifecycle where available, deterministic repository SBOM regeneration,
W15 hash immutability, detect-private-key, gitleaks, `git diff --check`, and
exact allowlist/staged review locally. Normal PR and main CI remain required
for the full repository suite. Do not run W15 frozen Reporting final, W12
formal Validation, an external Benchmark, or real cloud deployment.

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
After the single remediation commit, push/PR/CI/squash merge and the single
authorized new Private candidate-image dispatch may proceed. Stop and report
before any visibility change, tag, Release, or cloud action.
