# FlowPilot Arena agent guide

## Current phase and immutable baselines

This branch is the authorized W16 Aliyun ECS cloud-evidence closure on
`codex/w16-aliyun-ecs-evidence`. The
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
- W16 public README PR 52 merge/origin main, annotated `v1.0.0` tag, and
  published GitHub Release
  `4795aefe15be66f2405a2b899db7e5764810b8ea`.
- W16 post-release compliance PR 53 merge/origin main
  `14ad304ef64df638c9a61a898db5c3329021fd33`.
- W16 post-release evidence PR 54 merge/origin main
  `66c71a5a5b47f1cae814092b6832006ac43fddca`.

Do not rewrite, roll back, retag, rerelease, or otherwise modify those
objects. W15's report, protocol, configuration, schema, and all hashes remain
frozen. Work only on `codex/w16-aliyun-ecs-evidence`, created from the verified
PR 54 merge on `origin/main` above. Never move or
replace the existing `v1.0.0` tag or edit/rerelease its GitHub Release.

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
certification. A separately authorized, temporary Aliyun ECS single-node K3s
validation has now completed; it was not an ACK managed-cluster deployment and
does not certify production. Only the operator-reported outcome may be recorded
here. The repository and four GHCR packages are already Public. Runs
31454356060 and 31454378571 passed; they must not be rerun. This branch
authorizes only the exact documentation change, push, PR, normal CI, and squash
merge. Do not redeploy, create ACK, open a public port, create paid resources,
or perform any further cloud mutation. Never invent cloud parameters or print
credentials. The evidence commit subject is:

    docs: record W16 Aliyun ECS validation

The literal `%SystemDrive%/` path and every `code_review_agent` repository are
outside scope. Do not inspect, enumerate, scan, modify, delete, or stage them;
preserve unrelated `.tmp/` content.

## Exact post-release evidence allowlist

Only the following exact paths may be created or modified. Directory
wildcards are forbidden; add a path here before changing it.

~~~text
AGENTS.md
README.md
README.zh-CN.md
docs/agent-contract.md
docs/evidence/week-16-release.md
docs/sbom-status.md
~~~

The W15 frozen files are not modified or rerun in Reporting mode. No new
dependency, lockfile, service, database, migration, or product network
capability may be added. The four existing Public `linux/amd64` images in the
`ghcr.io/taka-wzx` namespace are: `flowpilot-arena-control-api`,
`flowpilot-arena-sandbox-api`, `flowpilot-arena-control-web`, and
`flowpilot-arena-sandbox-web`. Images use only `sha-<40-hex-merge-commit>`
tags; `latest` and `v1.0.0` remain forbidden for image publication. Dockerfile
changes are limited to removing build-only `uv`/`pip` and cache content from
the two API runtime images; application code and behavior must not change.
Buildx `provenance: mode=max` and `sbom: true` remain mandatory. Because the
repository is now Public, GitHub native Artifact Attestations are authorized
through only `actions/attest@a1948c3f048ba23858d222213b7c278aabede763`.
Existing `v1.0.0` digests receive honest SPDX SBOM attestations only; never
backfill or imply build provenance that was not signed in the original build
job. New images must receive native SLSA provenance in their build job and
native SPDX SBOM attestations after registry scanning. If an authorized tool
or cloud verification cannot execute, record `unavailable`; never claim it
passed.

## Required verification

Run YAML parsing, W15 hash immutability, detect-private-key, gitleaks,
`git diff --check`, exact allowlist/staged review, and README/link/command
checks locally. The final pre-publication run 31316287397 already passed image,
SBOM/Trivy, DNS, and kind/Helm lifecycle gates. Do not run W15 frozen
Reporting final, W12 formal Validation, or an external Benchmark. The completed
Aliyun ECS validation must not be rerun; no ACK context or further deployment
is authorized.

Finish with local forms of:

~~~powershell
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
pre-commit run detect-private-key --all-files
gitleaks git --no-banner --redact --exit-code 1 .
git diff --check
git diff -- . ':(exclude)%SystemDrive%' ':(exclude).tmp'
git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%' ':(exclude).tmp'
~~~

Record unavailable tooling and unprovided cloud parameters honestly. The two
authorized workflows are complete and must not be dispatched again. After this
single cloud-evidence commit, push/PR/CI/squash merge may proceed. Stop before
all cloud mutation.
