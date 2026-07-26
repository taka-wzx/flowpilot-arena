# Security policy

## W1 security posture

This repository is a Foundation-only scaffold. It contains no production
credentials, enterprise data, model credentials, or real system integrations.
The W1 API is deliberately stateless and its web page makes no network calls.

Security controls included in W1 are:

- `.gitignore` rules that reject local environment files and common credential
  containers;
- an `.env.example` file with no secret values;
- a pre-commit private-key detector;
- a GitHub Actions Gitleaks scan for repository history and changes;
- Dependabot configuration for declared package ecosystems;
- PR and evidence requirements that require a secret/data review.

Repository maintainers must also enable GitHub's native secret scanning,
push protection, Dependabot alerts, branch protection, and required CI checks
in repository settings. Those hosted settings cannot be asserted by files in
this repository.

## Reporting a vulnerability

Do not publish credentials, exploit details, or personal data in a public
issue. Prefer GitHub's private vulnerability-reporting flow when it is enabled
for this repository. If it is unavailable, open a minimal public issue asking
for a private reporting channel without including sensitive details.

Include:

- affected commit or release identifier;
- concise impact and reproduction summary;
- whether any secret, personal data, or external system could be affected;
- a safe remediation suggestion, if available.

## Handling secrets and data

- Never commit `.env`, API keys, tokens, private keys, certificates, cookies,
  real endpoints, screenshots with personal data, or production exports.
- Use obvious placeholders only when a format must be documented; do not use
  plausible-looking secret strings.
- Rotate and revoke any accidentally committed credential before trying to
  remove it from history.
- Keep real security reports outside the repository until a maintainer has
  supplied a suitable private channel.

## Supported versions

Until the first release, only the default branch and active weekly branch are
maintained. W1 is not a production deployment or a security certification.
