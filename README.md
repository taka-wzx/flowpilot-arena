# FlowPilot Arena

> A governed enterprise computer-use Agent paired with a resettable synthetic
> Arena. W16 packages the local system for reproducible review.

## One-minute overview

FlowPilot coordinates bounded Joiner/Mover/Leaver work across synthetic
enterprise applications. An Agent is useful because it can observe changing
pages, plan typed actions across systems, recover from interruptions, and stop
for human approval at high risk. It never becomes the authority: the Control
Plane enforces identity, tenant/RBAC, approval, audit, queue/lease/fence and
receipt/idempotency rules, while the independent Sandbox database-fact Grader
decides business success.

The governed loop is:

observe -> plan -> execute -> recover -> verify

The released local Demo uses synthetic data and a deterministic fake provider.
Real provider/model/OCR/VLM/embedding calls and real cost are exactly zero.

## Architecture

~~~mermaid
flowchart LR
  U["Local synthetic user"] --> Web["Control Web"]
  Web --> API["Control API"]
  API --> ID["Keycloak + Control PostgreSQL"]
  API --> WF["Private Workflow Worker"]
  WF --> T["Temporal + Recovery"]
  WF --> PA["Planning / DOM / Vision / Hybrid"]
  PA --> BW["Isolated Browser Worker"]
  BW --> SB["Synthetic Sandbox"]
  SB --> G["Independent database-fact Grader"]
  API --> TR["Opaque trace/replay"]
~~~

The components retain the W1-W15 boundaries documented in
[docs/architecture.md](docs/architecture.md) and
[docs/threat-model.md](docs/threat-model.md). W16 Helm is a closed,
namespace-scoped packaging surface; it is not a new control path.

## Five-minute local quickstart

Requirements: Python 3.13, uv, Node.js 24/npm, and Docker Compose. No cloud
account, registry credential, or external benchmark is required.

~~~powershell
$env:RECOVERY_ENVELOPE_KEY = '<runtime-only local key>'
docker compose -f deploy/compose/compose.yaml config
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
docker compose -f deploy/compose/compose.yaml --profile acceptance run --build --rm acceptance-smoke
python tests/integration/w16_demo_smoke.py
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
Remove-Item Env:RECOVERY_ENVELOPE_KEY
~~~

The Compose acceptance profiles also cover vision, hybrid planning, recovery,
context, identity, approval, production, observability, security, and
development-only W15 evaluation. A reset is the local Compose volume cleanup
above; it never authorizes a product delete. Health endpoints are /healthz for
APIs and / for web containers. Trace/replay and the independent Grader are
exercised by the existing observability/acceptance smokes.

## W16 release and reproducibility

- W16 PR 45 and the release/post-release follow-ups through PR 54 are merged;
  the attestation source is `14ad304e...` and the post-release evidence
  baseline is `66c71a5...` on `main`.
- Local chart: [deploy/helm/flowpilot-arena](deploy/helm/flowpilot-arena).
  Components remain disabled by default and may be enabled only with
  `repository@sha256:<64 hex>` plus an optional existing Secret.
- Release-image workflow:
  [.github/workflows/release-images.yml](.github/workflows/release-images.yml).
  It accepts only an exact main commit, publishes four `linux/amd64`
  `sha-<40-hex>` images, signs native SLSA provenance and SPDX 2.3 SBOM
  attestations, records SBOM/Trivy evidence, exercises a kind/Helm lifecycle,
  and never creates `latest` or `v1.0.0`.
- Post-release workflow run 31454378571 passed all four exact-digest builds,
  native provenance/SBOM verification, zero HIGH/CRITICAL and zero secret
  findings, declared-license gating, sandbox-web DNS, and the complete
  kind/Helm lifecycle. Run 31454356060 also checksum-verified and attached
  native SPDX SBOM attestations to the four immutable `v1.0.0` image digests.
  Exact digests and artifact checksums are recorded in
  [docs/evidence/week-16-release.md](docs/evidence/week-16-release.md).
- Deterministic demo: [docs/demo.md](docs/demo.md), runner
  [tests/integration/w16_demo.py](tests/integration/w16_demo.py).
- Architecture: [docs/architecture.md](docs/architecture.md).
- Release notes: [docs/release-notes-v1.0.0.md](docs/release-notes-v1.0.0.md).
- SBOM: [docs/sbom.spdx.json](docs/sbom.spdx.json) and
  [docs/sbom-status.md](docs/sbom-status.md).
- Aliyun cloud validation: a temporary ECS single-node K3s check of the two Web
  images is recorded in
  [the release evidence](docs/evidence/week-16-release.md). It was not an ACK
  deployment; the [ACK runbook](docs/deploy-aliyun-ack.md) was not executed.
- Model card: [docs/model-card.md](docs/model-card.md).
- Contributions/security/license:
  [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) ·
  [LICENSE](LICENSE).

W15 frozen synthetic Reporting results, matrix, hashes, and WorkArena
availability are in [docs/evidence/week-15-report.md](docs/evidence/week-15-report.md)
and [docs/benchmark-card.md](docs/benchmark-card.md). Three repetitions do
not support significance, real-cost, SLO, ROI, or security-certification
claims.

## Demo media

A GIF/video must come from a real local deterministic run and be redacted for
cookies, bearer material, nonce, DSN, machine paths, personal data, secrets,
and debug output. The recording tool is not installed in this environment, so
media is honestly marked unavailable; [docs/demo.md](docs/demo.md) is the
static fallback with subtitles and step-by-step output. AI-generated frames
are not used.

## Security boundary and known limitations

This repository is Public. Cloud evidence is limited to a temporary Aliyun ECS
single-node K3s validation of the two Web images. It was not ACK or production,
used no public ingress, and was removed after the checks. There is no managed
cluster deployment, production identity, production provider, arbitrary
browser/API/code execution, physical delete, impersonation, delegation,
break-glass, external Benchmark, or production certification.
Synthetic success is not real model quality. WorkArena is unavailable because
no versioned local asset, licence material, or checksum exists. Helm 4.2.0 and
kind 0.32.0 validation passes after the NetworkPolicy, Web runtime, rollback,
and scoped CoreDNS corrections. The post-release registry run found zero
HIGH/CRITICAL and zero secret findings in all four images. Removing build-only
uv/pip content reduced API SBOMs from 1,117/1,110 packages to 65/58; declared
`NOASSERTION` is now limited to 3/3/1/1 expected base/image-root packages, with
zero unexpected declarations. GitHub native provenance and SPDX SBOM
attestations verify anonymously for the new digests, and the four `v1.0.0`
digests have native SPDX SBOM attestations. `licenseConcluded=NOASSERTION`
still records the absence of an independent legal conclusion. Recording and
managed ACK deployment remain unavailable/not performed; the limited ECS check
does not waive these boundaries.

## Explicitly unsupported production operations

Do not use this release to modify real HR/IAM/ITSM/mail/asset systems, process
payroll or legal data, bypass approval, grant global administration, upload
real credentials, expose an endpoint, or treat Agent completion, Dashboard,
Reporting, Helm, or Demo output as business success.

See the [W16 plan](docs/plans/week-16-release.md),
[W16 contract](docs/agent-contract.md), and
[release evidence](docs/evidence/week-16-release.md) before changing the
repository. Public source verification is complete; package visibility,
`v1.0.0`, and GitHub Release are explicit release operations. The separately
authorized ECS/K3s validation is complete, cleaned up, and not part of this
release; no further cloud action is authorized here.
