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

## Preserved

W1-W15 product behavior, W15 frozen Reporting JSON/Markdown, protocol/config/schema
hashes, WorkArena unavailable status, security/identity/tenant/RBAC/approval/
audit/queue/lease/fence/receipt/idempotency/trace/replay semantics, and all prior
tags/releases are unchanged.

## Current release blocker

Local Trivy 0.73.0 scans found no image secret findings, but every candidate
contains HIGH/CRITICAL vulnerability occurrences. Public visibility,
`v1.0.0`, and a GitHub Release are blocked until separately authorized image
remediation clears the same registry-digest gate. No waiver is implied.

## Deferred authorization

Repository/package visibility change, public-readiness final approval, cloud
provider/account/region/cluster/domain/DNS/TLS/budget/egress/secret/lifecycle
details, annotated tag, and GitHub Release require a separate user-authorized
step after all blocking gates pass.
