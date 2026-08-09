# W16 evidence — Release and Reproducibility

Status: W16 implementation, release closure, and Private-workflow
plan-compatibility fix are merged. Runs 31305954309 and 31307531363 ended in
`startup_failure` with zero jobs because the native attestation was unavailable
for the Private plan and the repository selected-actions policy initially
omitted the pinned release actions. The minimally extended action policy then
allowed run 31308404308 to publish four Private digests and generate SBOM/Trivy
evidence. That run honestly failed: it found 120 HIGH/CRITICAL occurrences and
its Web-only kind lifecycle omitted the Sandbox API DNS dependency. The
authorized remediation now passes four local builds, hardened runtime health,
zero HIGH/CRITICAL, zero secret findings, and the complete kind/Helm lifecycle.
A post-merge registry workflow must reproduce this result. No visibility
change, cloud deployment, tag, Release, or Demo media has been published.

## Baseline and immutable evidence

- Original branch/commit: week/16-release /
  23f546daa8298bfaed20a2574fa9378055d26090
- W16 PR 45 merge/origin main:
  d1b03993fc912179d3cdbef00b9f26f524ca9c52
- Closure branch: codex/w16-release-closure
- Closure commit: 77322b132f99518d7423d4a1ddeda5c627ed3e6e
- Closure PR 46 merge/origin main:
  aab7efed479ad208ced4786ff43f8e72e4f1c458
- Plan-compatibility branch: codex/w16-release-closure-attestation-fix
- Plan-compatibility starting origin/main:
  aab7efed479ad208ced4786ff43f8e72e4f1c458
- Plan-compatibility PR 47 merge/origin main:
  7661db412fde625ec0a6ff81261d26343cf53052
- Image-remediation branch: codex/w16-private-image-remediation
- Image-remediation starting origin/main:
  7661db412fde625ec0a6ff81261d26343cf53052
- Starting origin/main: 078eb22deb137191660a5511c496fd1dff2b74f3
- W15 merge: 94e5a8d74b970c93c9610725dad7cb352545f654
- PR 43 merge: 697c8b8b9a6b4c25b571e7b0dbf6c01bcb82bbf3
- PR 44 merge: 078eb22deb137191660a5511c496fd1dff2b74f3
- W15 report byte SHA-256:
  42058cc83d310b51011e4774909b32dab6f3e0370d546c3c7928a5518f86cc00
- W15 report internal report_hash:
  ef2f1690a662eb5119214fb1e4fef80c22b1879ad0a88603b1e3e520c5cd9d3e
- W15 protocol byte SHA-256:
  42d5439629be60727b7d69324fd5f1c76ba879d2e10fa6bb2d5ad2496901ae41
- W15 protocol hash:
  b5aa0ddd4d0d07dd3d4a26faac11c947c223b85d14ac5dbc316681edc6de1379
- W15 configuration hash:
  c9ea8d997e470a7b7584e40001e8dbff349bd9a73aa80cdbf1a32b84d81d7ec5
- W15 schema byte SHA-256:
  9a869a014f5ea34530230027dfbc780627ce0eed99ce753ff34ec897a8167962
- No W15 frozen file changed. Reporting final and W12 formal Validation were not
  run. WorkArena remains unavailable/local_assets_absent.

## Tool versions

| Tool | Version/status |
|---|---|
| Python | 3.13.0 |
| uv | 0.11.14 |
| Node.js / npm | 24.15.0 / 11.12.1 |
| Git | 2.54.0.windows.1 |
| Docker Engine / standalone Compose | 29.6.2 / 5.3.1 |
| kubectl client | 1.36.1 |
| Chart / appVersion | 1.0.0 / 1.0.0-local |
| SPDX generator / format | flowpilot-sbom-generator/1.0 / SPDX 2.3 |
| Helm | 4.2.0+g0646808, Windows/amd64 asset checksum verified |
| kind / k3d | kind 0.32.0; k3d not required (kind is the selected runner) |
| Syft / Trivy | 1.50.0 / 0.73.0, Windows/amd64 asset checksums verified |
| actionlint | 1.7.12, Windows/amd64 asset checksum verified |
| recording tool | unavailable/not installed |

## Exact changed paths

All 31 changed paths are inside the exact W16 contract allowlist:

~~~text
AGENTS.md
CONTRIBUTING.md
README.md
README.zh-CN.md
SECURITY.md
deploy/helm/flowpilot-arena/Chart.yaml
deploy/helm/flowpilot-arena/templates/NOTES.txt
deploy/helm/flowpilot-arena/templates/_helpers.tpl
deploy/helm/flowpilot-arena/templates/configmap.yaml
deploy/helm/flowpilot-arena/templates/deployment.yaml
deploy/helm/flowpilot-arena/templates/networkpolicy.yaml
deploy/helm/flowpilot-arena/templates/deployment.yaml
deploy/helm/flowpilot-arena/templates/service.yaml
deploy/helm/flowpilot-arena/templates/serviceaccount.yaml
deploy/helm/flowpilot-arena/templates/tests/test-connection.yaml
deploy/helm/flowpilot-arena/values.schema.json
deploy/helm/flowpilot-arena/values.yaml
docs/adr/0016-w16-release.md
docs/agent-contract.md
docs/architecture.md
docs/benchmark-card.md
docs/demo.md
docs/evidence/week-16-release.md
docs/model-card.md
docs/plans/week-16-release.md
docs/release-notes-v1.0.0.md
docs/sbom-status.md
docs/sbom.spdx.json
scripts/generate_sbom.py
tests/integration/test_w16_demo.py
tests/integration/w16_demo.py
tests/integration/w16_demo_smoke.py
~~~

The literal protected path was excluded from status/diff/scan operations.
Unrelated .tmp content was not staged or altered by source edits.

The closure changes only these exact paths:

~~~text
.github/workflows/release-images.yml
AGENTS.md
README.md
README.zh-CN.md
deploy/helm/flowpilot-arena/templates/networkpolicy.yaml
docs/agent-contract.md
docs/evidence/week-16-release.md
docs/plans/week-16-release.md
docs/release-notes-v1.0.0.md
docs/sbom-status.md
docs/sbom.spdx.json
~~~

The plan-compatibility fix changes only these exact paths:

~~~text
.github/workflows/release-images.yml
AGENTS.md
docs/agent-contract.md
docs/evidence/week-16-release.md
docs/release-notes-v1.0.0.md
~~~

The image-gate remediation changes only these exact paths:

~~~text
.github/workflows/release-images.yml
AGENTS.md
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

## Helm and Kubernetes

- Chart, values, and JSON schema parsed locally.
- Static security policy passed: non-root, read-only root filesystem,
  RuntimeDefault seccomp, no privilege escalation, capabilities drop ALL,
  requests/limits, startup/readiness/liveness probes, disabled ServiceAccount
  token automount, existingSecret-only injection, default-deny NetworkPolicy,
  and no privileged/host namespaces/hostPath/Docker socket/cluster-admin.
- Components are disabled by default. An enabled component requires an immutable
  repository plus sha256 digest. No default secret or tag-only image exists.
- Helm 4.2.0 strict lint passed with all four components enabled and immutable
  synthetic digest inputs. Two normalized renders were byte-identical:
  21,951 bytes, SHA-256
  `dbc83864ada799a2cd893543b9e2131d99d7fd0673f31f0ccd46aa46229f3211`.
- Trivy 0.73.0 found zero HIGH/CRITICAL Kubernetes misconfigurations in the
  enabled rendered manifests. The remote checks bundle refresh could not use
  the host Docker credential helper, so Trivy explicitly fell back to its
  versioned embedded checks; this limitation is not hidden.
- The first kind server-side install found and rejected a duplicate `Egress`
  entry in `NetworkPolicy.spec.policyTypes`. The separately authorized fix
  removed only that duplicate. On kind 0.32.0 with
  `kindest/node:v1.36.1@sha256:3489c7674813ba5d8b1a9977baea8a6e553784dab7b84759d1014dbd78f7ebd5`,
  install, upgrade, rollback, history, uninstall, and unconditional cluster
  cleanup then passed.
- A local Web container reproduced the chart's non-root/read-only runtime and
  initially failed to create `/run/nginx.pid`. The separately authorized
  Deployment fix adds Web-only memory-backed `/run`, `/var/cache/nginx`, and
  `/tmp` volumes plus the Kubernetes safe
  `net.ipv4.ip_unprivileged_port_start=0` sysctl. Nginx configuration and HTTP
  probes then passed under non-root, read-only, no-new-privileges, and drop-ALL
  constraints. The enabled four-component chart also passed kind server-side
  dry-run before the lifecycle cleanup.
- Registry run 31308404308 created the four digests but its Web-only lifecycle
  timed out with sandbox-web at Available 0/1. The image's static Nginx config
  resolves `sandbox-api:8001` at startup, while the test namespace omitted that
  DNS name. The remediation creates a no-endpoint ClusterIP Service solely for
  the Web health/lifecycle test and emits pods, events, descriptions, and
  sandbox-web logs on failure before unconditional cleanup.
- With both remediated local Web images loaded by digest into kind 0.32.0, the
  stub-backed Helm 4.2.0 strict lint, install, rollouts, in-container HTTP
  checks, upgrade to two replicas, rollback, history, uninstall, and cluster
  cleanup passed.
- GitHub native Artifact Attestations are `unavailable/private-plan`. Buildx
  maximum provenance and SBOM attestations remain enabled and registry-bound;
  the digest files and downloaded Syft/Trivy artifacts remain the independent
  workflow evidence surfaces.
- Cloud deployment is not executed and is not passed.

## Demo and documentation

- W16 demo Ruff/format/strict mypy passed; 2 pytest tests passed.
- Development smoke passed with trace hash
  acfb969c3be0f87bae66fb6a82090c92f61da39715cab1e98a6e1560df01f3f1.
- The trace contains 11 closed synthetic events, finished_ungraded,
  independent-Grader authority, real_calls=0 and real_cost_microusd=0.
- Redaction tests reject Bearer, Cookie, password, private-key, DSN, and nonce
  forms. No machine path or personal data is emitted.
- English/Chinese quickstart commands match; 12 W16 Markdown documents had all
  relative links resolved.
- No GIF/video/screenshot was added. Recording status is
  unavailable/recording-tool-not-installed; docs/demo.md is the static subtitle
  fallback. No AI-generated frame is presented as product output.
- No external link appears in the W16 landing documentation.

## SBOM

- scripts/generate_sbom.py passed Ruff and strict mypy.
- SPDX 2.3 generation produced 355 sorted Python/npm packages.
- Every package has version, purl, and an artifact or local-source checksum.
- Fixed timestamp: 1970-01-01T00:00:00Z.
- Repeated generation was byte-identical.
- Working-tree and staged SBOM bytes were identical after forcing LF output.
- Final generated byte SHA-256:
  `a3e036f6ace6966df83f9d10c6a5133840a3496e367bb5f7caa78d6c07b038db`
  after the image-remediation Dockerfile pins; repeated generation was
  byte-identical and still contained 355 packages.
- Machine-path/credential/private-key/Bearer/Cookie scan found no match.
- Syft 1.50.0 generated local-image SPDX 2.3 evidence in the system temporary
  directory. Package counts / SBOM SHA-256 were: control-api 1,181 /
  `c5b84112669cb0f656ab0f1473f54f72f27be0e1e6aee18d82a256b3780c0dfe`;
  sandbox-api 1,174 /
  `ae2b56eecddbffb2bc4b0720ea3c99ace2be5ffd9294d86f9880d1338a4874cf`;
  control-web 69 /
  `1b93a2d3fcbc7aba7061549903fbab9eeaf41c8615b705263c079f399233be42`;
  sandbox-web 69 /
  `8b5615a1387da8f595638977514d13de5d8f20ed5914643f37627778bde2a9e4`.
- Container Dockerfile declarations and Helm references are recorded, but
  repository `container_image_digest_coverage` remains unavailable because
  registry digests and per-image SBOMs are restricted workflow artifacts rather
  than generator inputs. Lockfiles contain no authoritative licence field, so
  package licences remain NOASSERTION.
  Consequently this is an honest partial machine-readable SBOM, not a passed
  complete image/licence SBOM.
- Remediated local Syft 1.50.0 SPDX package counts / byte SHA-256 were:
  control-api 1,117 /
  `7e920891be96b278732ec56c513cac76696a01a2afe74a7402776dc0070a2d73`;
  sandbox-api 1,110 /
  `beb789045795009e06981f777ad31e0a5f3e993aee2c0c9baf61c4cd0fa838c2`;
  control-web 72 /
  `fbc9d22e5686d8630869c26d0e0a7c6cc0f096fb71f1ef6d1159dc1a8c4ec320`;
  sandbox-web 72 /
  `ad1f73199a6fe03718d5a459bf761185bcad0fa1dd22f6a1359d01633aabc99a`.

## Local quality and regression

| Gate | Result |
|---|---|
| Sandbox/API locked sync | passed |
| Integration locked sync | passed |
| Control locked sync | passed in isolated W16 venv after existing venv file-lock failure |
| Control Ruff/format/mypy/pytest | passed; 38 formatted files, 18 typed source files, 68 tests |
| Sandbox Ruff/format/mypy/pytest | passed; 37 formatted files, 19 typed source files, 35 tests |
| W15+W16 Ruff/format/strict mypy/pytest | passed; 17 tests |
| Host frontend npm ci --offline | unavailable: existing node_modules/.vite-temp EPERM |
| Frontend lint/typecheck | passed for both |
| Frontend Vitest | passed with runner loader; Control 10, Sandbox 9 |
| Frontend build | passed with runner loader and isolated outDir |
| Compose config/build/up/health | passed; classic builder warned buildx absent |
| Control empty migration round-trip | passed at 20260803_0004; check clean |
| Sandbox empty migration round-trip | passed at 20260728_0003; check clean |
| W4-W13 Compose regression | passed, exit code zero for each profile |
| W14 deterministic security smoke | passed; no bypass/leak/side effect, all real calls zero |
| W15 Development-only smoke | passed; 33 attempts, Reporting/Validation/Benchmark false |
| Worker restart and post-restart health | passed |
| Compose cleanup | passed; no remaining project containers |

The W4 frozen DOM sample retained its independent-Grader passed=false result
while the smoke exited zero; it was not rewritten as success. Later profiles
reported their own frozen independent grades.

## Public readiness

- The closure baseline built four local `linux/amd64` images with the same
  application-directory contexts used by the release workflow.
- Historical closure Trivy 0.73.0 exact local-image scanning downloaded the
  then-current vulnerability database and found no secret findings, but the
  HIGH/CRITICAL gate failed:
  each backend image had 4 CRITICAL and 21 HIGH occurrences (24 unique; one
  unique fixable and 23 unique without a reported fix), while each web image
  had 2 CRITICAL and 33 HIGH occurrences (35 unique, all with reported fixed
  package versions). No exception or suppression was applied.
- Registry run 31308404308 reproduced those historical counts: control-api and
  sandbox-api each had 4 CRITICAL plus 21 HIGH, while each Web image had 2
  CRITICAL plus 33 HIGH, for 120 blocking occurrences and zero secret findings.
  Its immutable candidate digests were control-api
  `sha256:2fc99b9dd60cb0d23f46b3a9c583e2ef06331b8fdecc8bcddcc51a594c95ac3f`,
  sandbox-api
  `sha256:17ef76719286ac660cc1aa3f4a665ab7c6ca1fdbc7dade370829a25706c6d2fe`,
  control-web
  `sha256:7799c75507bb11c2e0e0d16dfaa69b6ef855686c51d92cb273e5be1680fb376f`,
  and sandbox-web
  `sha256:8792c3c2d36d84fda4f8cd06b5f092ff9bfb5538d83870069734b66352b5ea35`.
- The remediation checksum-pins Python 3.13.14 Alpine 3.24, Node 24 Alpine
  3.24, and Nginx 1.30.4 Alpine 3.24 linux/amd64 manifests and updates the
  image-only uv installer from 0.11.14 to 0.12.3. All four locked images built.
  Under non-root, read-only-root, no-new-privileges, and drop-ALL constraints,
  both API health endpoints and both Web HTTP endpoints returned 200.
- Trivy 0.73.0 then downloaded a fresh database and found zero HIGH/CRITICAL
  plus zero secret findings in every remediated local image. No ignore,
  suppression, or waiver was used. Registry reproduction remains required.
- Consequently a new Private candidate workflow must reproduce the local zero
  count, while repository/package public visibility, `v1.0.0`, and GitHub
  Release remain prohibited pending separate publication authorization.

- gitleaks full-history scan with the protected path excluded: 59 commits,
  approximately 5.13 MB, no leaks.
- detect-private-key over tracked files with the protected path excluded:
  passed.
- Final staged gitleaks scan covered approximately 380.36 KB and found no
  leaks; final staged detect-private-key passed.
- Current tracked tree has no file over 5 MiB, no .gitmodules, and no Git LFS
  tracking rule.
- Repository Apache-2.0 LICENSE exists. No W16 font, icon, screenshot, video,
  external Benchmark asset, or third-party data was added.
- Package licence and registry-digest closure are unavailable as recorded in
  the partial SBOM, so final public-readiness is not claimed passed.
- Anonymous clone/public README verification is not executed because the
  repository remains Private and visibility change is not authorized.
- Prior tags/releases are unchanged. Two planning runs had zero jobs; run
  31308404308 published only blocked Private candidates and restricted evidence.
  No tag, Release, or visibility change occurred.

## Unavailable and next authorization

Unavailable or blocked: GitHub native Artifact Attestations
(`unavailable/private-plan`), registry reproduction of the locally passing
image remediation, complete licence assertions, Demo GIF/video, real cloud
deployment, anonymous public clone, and final public-readiness approval.

The current authorization covers image-remediation push/PR/normal CI/squash
merge and one new Private candidate workflow dispatch. A later
authorization and a passing image vulnerability gate are still required for
repository/package visibility change, anonymous verification, annotated
v1.0.0 tag, and GitHub Release v1.0.0 - FlowPilot Arena. Cloud parameters
remain a separate scope.
