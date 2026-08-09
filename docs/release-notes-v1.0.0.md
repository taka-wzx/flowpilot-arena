# Release notes draft — v1.0.0 - FlowPilot Arena

This remains a pre-release W16 draft. W16 PR 45 is merged, and the authorized
closure adds a manual Private-candidate GHCR workflow with digest evidence,
SBOM, Trivy, Buildx maximum provenance, and kind/Helm lifecycle validation.
GitHub native Artifact Attestations are `unavailable/private-plan`; they are
not a release-readiness claim or a waiver. No v1.0.0 tag, GitHub Release,
package/repository visibility change, or cloud deployment is authorized in
this phase.

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
`kube-system`; arbitrary egress remains denied. One new post-merge Private
workflow must confirm install, rollout, HTTP, upgrade, rollback, and uninstall.
Public visibility, `v1.0.0`, and a GitHub Release remain blocked pending that
result and separate publication authorization.

## Deferred authorization

Repository/package visibility change, public-readiness final approval, cloud
provider/account/region/cluster/domain/DNS/TLS/budget/egress/secret/lifecycle
details, annotated tag, and GitHub Release require a separate user-authorized
step after all blocking gates pass.
