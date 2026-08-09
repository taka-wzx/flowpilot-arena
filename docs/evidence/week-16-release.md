# W16 evidence — Release and Reproducibility

Status: W16 implementation, release closure, Private-workflow
plan-compatibility fix, Private-image remediation, and rollback namespace fix
are merged. Runs
31305954309 and 31307531363 ended in
`startup_failure` with zero jobs because the native attestation was unavailable
for the Private plan and the repository selected-actions policy initially
omitted the pinned release actions. The minimally extended action policy then
allowed run 31308404308 to publish four Private digests and generate SBOM/Trivy
evidence. That run honestly failed: it found 120 HIGH/CRITICAL occurrences and
its Web-only kind lifecycle omitted the Sandbox API DNS dependency. The merged
remediation passes four local builds, hardened runtime health, zero
HIGH/CRITICAL, zero secret findings, and the complete local kind/Helm lifecycle.
Registry run 31312150260 reproduced the four zero-vulnerability/zero-secret
image gates and passed kind install, rollout, HTTP, and upgrade. Its sole
failure was a Helm rollback command that omitted `--namespace flowpilot-w16`.
PR 49 scoped that command correctly. Registry run 31313916608 then again
passed all four image publications and the registry SBOM/Trivy gate, but the
kind install exposed a separate chart defect: default-deny egress blocked the
sandbox-web lookup of the already-created `sandbox-api` Service. The current
authorized fix permits only kube-system CoreDNS TCP/UDP 53 egress. No
visibility change, cloud deployment, tag, Release, or Demo media has been
published.

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
- Image-remediation commit:
  64d61e1f1cd14449f86eff6b9def79ee11b95b9a
- Image-remediation PR 48 merge/origin main:
  f334441612f0c3508f197cecf8d0456296a771cf
- Rollback-namespace-fix branch: codex/w16-private-rollback-namespace
- Rollback-namespace-fix starting origin/main:
  f334441612f0c3508f197cecf8d0456296a771cf
- Rollback-namespace-fix commit:
  688dc2aff59a55fce39ae240d52c3d83b57fbce3
- Rollback-namespace-fix PR 49 merge/origin main:
  b62333492aea62a0d4b12147ce863ab76bda0133
- Scoped-DNS-egress-fix branch: codex/w16-private-dns-egress
- Scoped-DNS-egress-fix starting origin/main:
  b62333492aea62a0d4b12147ce863ab76bda0133
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

The rollback namespace fix changes only these exact paths:

~~~text
.github/workflows/release-images.yml
AGENTS.md
docs/agent-contract.md
docs/evidence/week-16-release.md
docs/release-notes-v1.0.0.md
~~~

The scoped DNS egress fix changes only these exact paths:

~~~text
AGENTS.md
deploy/helm/flowpilot-arena/templates/networkpolicy.yaml
docs/agent-contract.md
docs/evidence/week-16-release.md
docs/release-notes-v1.0.0.md
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
- Registry run 31312150260 used the merged remediation images and the Sandbox
  API DNS stub. It passed Helm install, both Web rollouts and in-container HTTP
  checks, and the two-replica upgrade. The next command ran
  `helm rollback flowpilot-w16 1 --wait --timeout 5m` without a namespace and
  failed with `Error: release: not found`; this is a workflow command scoping
  error, not a workload readiness failure. The authorized fix adds
  `--namespace flowpilot-w16`, matching the already-passing local lifecycle.
- Rollback namespace PR 49 merged as
  `b62333492aea62a0d4b12147ce863ab76bda0133`; PR CI 31312968413 and main CI
  31313862452 passed their required gates. Registry run 31313916608 used the
  corrected rollback command but timed out earlier during Helm install because
  sandbox-web could not resolve `sandbox-api`. The run had created the
  `sandbox-api` ClusterIP Service before Helm, and pod logs reported
  `host not found in upstream "sandbox-api"`. The chart selected all release
  pods with a default-deny Egress policy, while its internal policy neither
  declared `Egress` in `policyTypes` nor allowed kube-system CoreDNS. The
  current fix declares that policy type and permits only TCP/UDP 53 to pods
  labelled `k8s-app: kube-dns` in the `kube-system` namespace. It does not add
  arbitrary external egress.
- Helm 4.2.0 strict lint passed after the scoped DNS change. Two enabled
  four-component renders were byte-identical: 22,965 bytes, SHA-256
  `e640883828785d3d6bc8ec28659a5a1f15e86fc343b820285d3a9dd247612b10`.
  Trivy 0.73.0 embedded checks found zero HIGH/CRITICAL Kubernetes
  misconfigurations in the isolated rendered manifests.
- On kind 0.32.0 / Kubernetes 1.36.1, the two previously verified local Web
  images were loaded and addressed by their immutable containerd manifest
  digests. With the stub Service and scoped CoreDNS egress, Helm install,
  both rollouts, both in-container HTTP checks, upgrade to two replicas,
  namespace-scoped rollback, history, uninstall, and unconditional cluster
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
- Downloaded registry-run 31312150260 Syft SPDX 2.3 package counts / byte
  SHA-256 were: control-api 1,117 /
  `ba9b74a96cab21967752f6bbcc24b5ee8116b1d9bd729997148d91ca4cce0998`;
  sandbox-api 1,110 /
  `479bd9f682e7ac9fd17ca98981ead979e21466b03488bfb64d6ab158ac8cc5d9`;
  control-web 72 /
  `f40a34fc84322a75a4cbbb6e1f9f10581b7cb3309c6d2bce08a8cf3d22727635`;
  sandbox-web 72 /
  `322c0576ac83aaec6a6d8e5ecbec98848b630c456f45d528edee5468a948b36a`.
  All four files parsed as SPDX 2.3; the paired downloaded Trivy JSON files
  independently parsed with zero HIGH/CRITICAL vulnerabilities and zero
  secret findings.
- Downloaded registry-run 31313916608 Syft SPDX 2.3 package counts / byte
  SHA-256 were: control-api 1,117 /
  `31536c12f833a8c75e7d97630995647e361b4bd1f6aa97b6f45cd5caa2959615`;
  sandbox-api 1,110 /
  `26e02af2293efe81a09c6ae5313b97665e7c99400aead0bd04734c5561cd1abf`;
  control-web 72 /
  `e932daf197e74dd48fa707584e9b6eae64fa1d134d255cf36bbb4f7eaa6bb9bc`;
  sandbox-web 72 /
  `02dc4e7d18ea4bebeccb46789d4c1212c970e4651fae9917212327be549a9626`.
  All four files parsed as SPDX 2.3; all four paired Trivy JSON files parsed
  with zero HIGH/CRITICAL vulnerabilities and zero secret findings.

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
  suppression, or waiver was used.
- Registry run 31312150260 reproduced zero HIGH/CRITICAL and zero secret
  findings for all four Private images. Its immutable candidate digests were
  control-api
  `sha256:7ece457fb04d92da2080b7fd2b9591a070ca615f56d348fa5636b8fa5777cd38`,
  sandbox-api
  `sha256:04a55382674c3a1fe8e2705e7bffa78ac338527a3eac4ccf190a02fe8b232bb2`,
  control-web
  `sha256:d350b81ee5e7be79a827401c0eda2cef4b5e29f093c16906832d8f2f09562f96`,
  and sandbox-web
  `sha256:d0abe347f78ff449b41e386cf1b7ebc6fab39585ac9d6285d07496d7b4cf5747`.
  Its digest, Syft SPDX, and Trivy artifacts were downloaded for restricted
  verification. The run failed only at the unscoped Helm rollback command.
- Registry run 31313916608 again reproduced zero HIGH/CRITICAL and zero secret
  findings for all four Private images. Its immutable candidate digests were
  control-api
  `sha256:f496507c61237f24bc77f570ce4acc9ab985cbacef34678d79b4c98466f62b9b`,
  sandbox-api
  `sha256:f8cb656a54e16dc1dbddb50317efa5ee6d25fcb55e6a8bc4bbe86f477025ccd7`,
  control-web
  `sha256:b933d0e23f0f207bce23e00dd3924aae96cef7290f92f870d0a1fa439fac95ce`,
  and sandbox-web
  `sha256:88eecc09967fe30ef6bcbf29332b648c0f78a3903844fac03a3c4615f1aa3f1f`.
  Named digest, Syft SPDX, and Trivy artifacts were downloaded and verified.
  The final gate failed only because default-deny egress prevented cluster DNS
  during the kind install; the run did not reach the corrected rollback.
- Consequently one new Private candidate workflow must confirm the corrected
  end-to-end lifecycle, while repository/package public visibility, `v1.0.0`,
  and GitHub Release remain prohibited pending separate publication
  authorization.

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
(`unavailable/private-plan`), a successful end-to-end registry workflow after
the scoped DNS egress correction, complete licence assertions, Demo GIF/video,
real cloud deployment, anonymous public clone, and final public-readiness
approval.

The current authorization covers the scoped DNS egress fix push/PR/normal
CI/squash merge and one new Private candidate workflow dispatch. A later
authorization is still required for repository/package visibility change,
anonymous verification, annotated v1.0.0 tag, and GitHub Release v1.0.0 -
FlowPilot Arena. Cloud parameters remain a separate scope.
