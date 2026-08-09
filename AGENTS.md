# FlowPilot Arena agent guide

## Current phase and immutable baselines

This branch is the authorized W16 public README alignment on
`codex/w16-public-readme-closure`. The
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
- W16 Private-image remediation PR 48 merge/origin main
  `f334441612f0c3508f197cecf8d0456296a771cf`.
- W16 rollback namespace PR 49 merge/origin main
  `b62333492aea62a0d4b12147ce863ab76bda0133`.
- W16 scoped DNS egress PR 50 merge/origin main
  `5f37b49a3eb30b63c7aed7fe91676708a28721ac`.
- W16 public-release evidence PR 51 merge/origin main
  `bc5da48060b999e85553d9d2db6d03b16303d5c9`.

Do not rewrite, roll back, retag, rerelease, or otherwise modify those
objects. W15's report, protocol, configuration, schema, and all hashes remain
frozen. Work only on `codex/w16-public-readme-closure`, created from the
verified W16 public-release evidence merge on `origin/main` above.

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
separately authorized this public README alignment branch, push, PR,
normal CI, and squash merge. The user also authorized repository/package
visibility change, anonymous public verification, the annotated `v1.0.0` tag,
and GitHub Release `v1.0.0 - FlowPilot Arena`. Cloud deployment, provider,
account, region, cluster, DNS, TLS, budget, egress, and secret parameters
remain outside this authorization. The authorized repository mutation is one
commit with subject:

    docs: align public W16 README

The literal `%SystemDrive%/` path and every `code_review_agent` repository are
outside scope. Do not inspect, enumerate, scan, modify, delete, or stage them;
preserve unrelated `.tmp/` content.

## Exact public-README-alignment allowlist

Only the following exact paths may be created or modified. Directory
wildcards are forbidden; add a path here before changing it.

~~~text
AGENTS.md
README.md
README.zh-CN.md
docs/agent-contract.md
docs/evidence/week-16-release.md
~~~

The W15 frozen files are not modified or rerun in Reporting mode. No new
dependency, lockfile, service, database, migration, network capability, or
cloud resource may be added. The four existing Private `linux/amd64` candidate
images in the `ghcr.io/taka-wzx` namespace are: `flowpilot-arena-control-api`,
`flowpilot-arena-sandbox-api`, `flowpilot-arena-control-web`, and
`flowpilot-arena-sandbox-web`. Images use only `sha-<40-hex-merge-commit>`
tags; `latest` and `v1.0.0` remain forbidden for image publication. No
Dockerfile or image content may change in this follow-up. Buildx
`provenance: mode=max` and `sbom: true` remain mandatory. GitHub native
Artifact Attestations are `unavailable/private-plan`; do not request
`attestations: write`, `id-token: write`, or `actions/attest` in this Private
workflow. If an authorized Helm, kind, Syft, Trivy, or VHS verification cannot
execute, record `unavailable`; never claim it passed.

## Required verification

Run YAML parsing, W15 hash immutability, detect-private-key, gitleaks,
`git diff --check`, exact allowlist/staged review, and README/link/command
checks locally. The final Private run 31316287397 already passed image,
SBOM/Trivy, DNS, and kind/Helm lifecycle gates. Do not run W15 frozen
Reporting final, W12 formal Validation, an external Benchmark, or cloud
deployment.

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
After the single public README alignment commit, push/PR/CI/squash merge may
proceed. Then perform the authorized visibility, anonymous verification, tag,
and Release steps. Stop before any cloud action.
