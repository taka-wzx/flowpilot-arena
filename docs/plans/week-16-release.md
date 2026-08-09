# W16 plan — Release and Reproducibility

## Objective

Package the already released W1-W15 local system for reproducible review. The
work is documentation, a closed namespace-scoped Helm chart, a deterministic
redacted demo trace, and a generated SPDX SBOM/status record. Product
authority, the W15 frozen report, and all remote publication state remain
unchanged.

## Frozen starting point

The local branch is created from origin/main at
078eb22deb137191660a5511c496fd1dff2b74f3. This contains W15 merge
94e5a8d74b970c93c9610725dad7cb352545f654 and the PR 43/44 security
maintenance merges 697c8b8b9a6b4c25b571e7b0dbf6c01bcb82bbf3 and
078eb22deb137191660a5511c496fd1dff2b74f3.

## Work packages

1. Freeze the exact W16 allowlist in AGENTS.md and docs/agent-contract.md;
   record the branch and immutable W15 hashes.
2. Add flowpilot-arena Helm packaging with disabled-by-default components,
   digest-only enabled images, strict security contexts, probes, fixed
   resources, existing-secret references, and default-deny network policy.
3. Add a stdlib-only deterministic demo runner and unit/smoke tests. The output
   is canonical JSON containing opaque synthetic references only.
4. Replace the stale W12 landing page with equivalent English and Chinese
   release/reproduction documentation; add architecture, demo, model card,
   release notes, benchmark status, and SBOM status links.
5. Generate the SPDX 2.3 document from frozen lockfiles and chart/Dockerfile
   inputs. If image digests or the generator are unavailable, preserve the
   machine-readable unavailable state.
6. Run all available local gates, record pass/fail/unavailable evidence, review
   exact paths, stage only the allowlist, and make one local commit.

## Explicit non-goals

No cloud login/resource, DNS/TLS, billable operation, repository visibility
change, push/PR/merge/tag/release, new dependency/service/database/migration,
external Benchmark, W15 Reporting rerun, W12 Validation, or product-code
change is permitted.

## Acceptance evidence

The evidence file must name every changed path, command and observed result,
W15 hash immutability, demo redaction/source status, chart/security checks,
Compose and regression status, SBOM checksum/status, public-readiness checks,
and every unavailable or unexecuted item. unavailable is never converted to
passed.
