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

- W16 PR 45 and the release-closure follow-ups through PR 51 are merged; the
  public evidence baseline is `bc5da480...` on `main`.
- Local chart: [deploy/helm/flowpilot-arena](deploy/helm/flowpilot-arena).
  Components remain disabled by default and may be enabled only with
  `repository@sha256:<64 hex>` plus an optional existing Secret.
- Candidate-image workflow:
  [.github/workflows/release-images.yml](.github/workflows/release-images.yml).
  It accepts only an exact main commit, publishes four `linux/amd64`
  `sha-<40-hex>` candidates, records SBOM/Trivy/provenance evidence, exercises
  a kind/Helm lifecycle, and never creates `latest` or `v1.0.0`.
- Final workflow run 31316287397 passed all four exact-digest image builds,
  zero HIGH/CRITICAL and zero secret findings, registry SPDX/Trivy evidence,
  sandbox-web DNS, and the complete kind/Helm lifecycle. Exact digests and
  artifact checksums are recorded in
  [docs/evidence/week-16-release.md](docs/evidence/week-16-release.md).
- Deterministic demo: [docs/demo.md](docs/demo.md), runner
  [tests/integration/w16_demo.py](tests/integration/w16_demo.py).
- Architecture: [docs/architecture.md](docs/architecture.md).
- Release notes: [docs/release-notes-v1.0.0.md](docs/release-notes-v1.0.0.md).
- SBOM: [docs/sbom.spdx.json](docs/sbom.spdx.json) and
  [docs/sbom-status.md](docs/sbom-status.md).
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

This repository is Public. There is no real cloud deployment, public ingress,
production identity, production
provider, arbitrary browser/API/code execution, physical delete, impersonation,
delegation, break-glass, external Benchmark, or production certification.
Synthetic success is not real model quality. WorkArena is unavailable because
no versioned local asset, licence material, or checksum exists. Helm 4.2.0 and
kind 0.32.0 validation passes after the NetworkPolicy, Web runtime, rollback,
and scoped CoreDNS corrections. The final registry run found zero
HIGH/CRITICAL and zero secret findings in all four images. Repository and
registry SPDX evidence are published with their exact limits: many package
license fields remain `NOASSERTION`, native GitHub Artifact Attestations are
unavailable on the Private-plan run, and recording/cloud deployment remain
unavailable. These limitations are disclosed rather than treated as waivers.

## Explicitly unsupported production operations

Do not use this release to modify real HR/IAM/ITSM/mail/asset systems, process
payroll or legal data, bypass approval, grant global administration, upload
real credentials, expose an endpoint, or treat Agent completion, Dashboard,
Reporting, Helm, or Demo output as business success.

See the [W16 plan](docs/plans/week-16-release.md),
[W16 contract](docs/agent-contract.md), and
[release evidence](docs/evidence/week-16-release.md) before changing the
repository. Public source verification is complete; package visibility,
`v1.0.0`, and GitHub Release are explicit release operations. Cloud actions
remain separately authorized and are not part of this release.
