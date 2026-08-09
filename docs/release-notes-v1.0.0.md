# Release notes draft — v1.0.0 - FlowPilot Arena

This remains a W16 release draft pending the authorized publication commands.
W16 PR 45 is merged, and the authorized
closure adds a manual Private-candidate GHCR workflow with digest evidence,
SBOM, Trivy, Buildx maximum provenance, and kind/Helm lifecycle validation.
GitHub native Artifact Attestations are `unavailable/private-plan`; they are
not a release-readiness claim or a waiver. Repository/package visibility,
anonymous verification, the `v1.0.0` tag, and GitHub Release are authorized
after this evidence closure; cloud deployment remains out of scope.

## Included

- Closed namespace-scoped Helm chart with digest-only enabled image values.
- Deterministic redacted synthetic demo runner and smoke.
- Equivalent English/Chinese release documentation.
- Architecture, model card, benchmark status, SBOM and public-readiness evidence.
- Explicit Compose, cleanup, trace/replay and independent-Grader commands.
- Checksum-pinned release tooling and full-SHA-pinned GitHub Actions.
- Buildx `provenance: mode=max` and `sbom: true`; GitHub native Artifact
  Attestations remain `unavailable/private-plan` for this Private repository.
- Digest-only Private candidates for control-api, sandbox-api, control-web, and
  sandbox-web; no `latest` tag and no implicit promotion to `v1.0.0`.
- kind-validated NetworkPolicy syntax and Web-only memory-backed Nginx runtime
  paths while preserving non-root and read-only-root enforcement.
- Checksum-pinned Python 3.13.14, Node 24, and Nginx 1.30.4 linux/amd64 Docker
  Official Image bases, plus container-only uv 0.12.3.
- A Web-only kind DNS stub for the Sandbox API upstream and failure-first
  Kubernetes diagnostics before unconditional cluster cleanup.

## Preserved

W1-W15 product behavior, W15 frozen Reporting JSON/Markdown, protocol/config/schema
hashes, WorkArena unavailable status, security/identity/tenant/RBAC/approval/
audit/queue/lease/fence/receipt/idempotency/trace/replay semantics, and all prior
tags/releases are unchanged.

## Current release blocker

Historical registry run 31308404308 found 120 HIGH/CRITICAL occurrences and
omitted the Web-only test's `sandbox-api` DNS dependency. The merged image and
stub remediation corrected those blockers. Run 31312150260 reproduced zero
HIGH/CRITICAL and zero secret findings but exposed an unscoped Helm rollback;
PR 49 fixed that command. Run 31313916608 again passed all four image
publications and the registry SBOM/Trivy gate, but timed out during kind install
because the chart's default-deny egress prevented sandbox-web from querying
cluster DNS for the already-created `sandbox-api` Service. The authorized
minimal follow-up adds only TCP/UDP 53 egress to CoreDNS-selected pods in
`kube-system`; arbitrary egress remains denied. The final Private run
31316287397 passed all four image publications, zero HIGH/CRITICAL and zero
secret findings, registry SBOM/Trivy evidence, kind DNS/Web lifecycle,
namespace-scoped rollback, and the verification gate. The user has authorized
repository/package visibility change, anonymous verification, the annotated
`v1.0.0` tag, and GitHub Release. Package license fields with `NOASSERTION` and
native Artifact Attestations (`unavailable/private-plan`) remain explicitly
disclosed; cloud deployment is not part of this release.

## Deferred authorization

Cloud provider/account/region/cluster/domain/DNS/TLS/budget/egress/secret/
lifecycle details remain a separate authorization. No cloud deployment is
claimed by this release.
