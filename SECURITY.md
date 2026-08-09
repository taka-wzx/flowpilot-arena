# Security policy

## W16 posture

FlowPilot Arena remains a private, synthetic local evaluation and release
repository. W1-W15 identity, tenant isolation, RBAC, approval, audit, browser
isolation, trace/replay, and independent-Grader controls are frozen. W16 adds
only a closed namespace-scoped Helm packaging surface and redacted
reproducibility documentation.

The chart defaults to no enabled image, no public ingress, no ServiceAccount
token automount, no privilege escalation, read-only root filesystems,
RuntimeDefault seccomp, dropped capabilities, fixed resources, and
default-deny network policy. Secrets are existingSecret/runtime-injection
references only. This is not a cloud-production certification.

## Prohibited material

Do not commit real credentials, personal data, production DSNs, tokens, cookies,
approval material, private keys, screenshots, GIFs, videos, or arbitrary
provider/API/URL/Shell/SQL/JavaScript capability. The current Demo uses
deterministic-fake-provider/1.0 and makes zero real calls and zero real cost.
WorkArena is unavailable because no versioned local asset or licence checksum
is present.

## Reporting a vulnerability

Do not publish sensitive details in an issue. Use the repository's private
vulnerability-reporting channel when enabled; otherwise open a minimal issue
requesting a private channel without including exploit material. Include the
affected commit, impact, safe reproduction, and whether any secret or external
system is involved.

## Release boundary

Repository visibility, cloud resources, DNS/TLS, registry publication, push,
PR, merge, tag and GitHub Release are separate authorized steps. Do not hide
history, force-push, rewrite tags, or call unavailable checks passed.
