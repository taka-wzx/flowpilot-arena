# W16 agent contract — release and reproducible demo

## Authority and frozen history

This is the sole implementation authority for W16 on `week/16-release`. The
branch must start at `origin/main` `078eb22deb137191660a5511c496fd1dff2b74f3`,
which contains W15 merge `94e5a8d74b970c93c9610725dad7cb352545f654`, PR 43 merge
`697c8b8b9a6b4c25b571e7b0dbf6c01bcb82bbf3`, and PR 44 merge
`078eb22deb137191660a5511c496fd1dff2b74f3`. W12 (`w12-production`), W13
(`w13-observability`), W14 (`w14-security`), and W15 (`w15-evaluation`) tags,
releases, merges, reports, protocols, schemas, catalogs, and hashes are
immutable. No history rewrite, rollback, retag, rerelease, push, PR, merge,
visibility change, or v1.0.0 tag/release is authorized in this turn.

W15 frozen evidence is byte-identified before W16 work:

- `docs/evidence/week-15-report.json` byte SHA-256 is
  `42058cc83d310b51011e4774909b32dab6f3e0370d546c3c7928a5518f86cc00`;
  its self-excluding `report_hash` field is
  `ef2f1690a662eb5119214fb1e4fef80c22b1879ad0a88603b1e3e520c5cd9d3e`.
- `tests/integration/w15-reporting-protocol.json` has protocol hash
  `b5aa0ddd4d0d07dd3d4a26faac11c947c223b85d14ac5dbc316681edc6de1379`.
  Its byte SHA-256 is
  `42d5439629be60727b7d69324fd5f1c76ba879d2e10fa6bb2d5ad2496901ae41`.
- Its configuration hash is
  `c9ea8d997e470a7b7584e40001e8dbff349bd9a73aa80cdbf1a32b84d81d7ec5` and its
  schema hash is
  `9a869a014f5ea34530230027dfbc780627ce0eed99ce753ff34ec897a8167962`.
- WorkArena remains `unavailable/local_assets_absent`; no external content is
  downloaded, substituted, or executed.

## Scope and non-goals

W16 may add only deterministic local release/deployment packaging,
documentation, reproducible synthetic-demo evidence, SBOM generation/status,
and release notes. Existing product authority remains unchanged: Agent
completion is `finished_ungraded`; only the independent Sandbox database-fact
Grader determines business success. Helm, README, dashboard, reporting,
Compose, and cloud deployment are observation/documentation surfaces and can
never authorize work, select an organization, bypass Control Plane policy, or
write product state.

The chart is namespace-scoped and closed. It must not request cluster-admin,
automount a ServiceAccount token, use privileged/host namespaces/hostPath/
Docker socket, grant arbitrary egress, include default credentials, or claim
cloud-production certification. Secrets can only be referenced through an
existing Secret/runtime injection. Demo identities and data are synthetic.
Default-deny NetworkPolicy, non-root/read-only/seccomp RuntimeDefault,
no-privilege-escalation, dropped capabilities, fixed resources, and all probes
are mandatory for enabled components. Every enabled image must be supplied as
an immutable `repository@sha256:<64 hex>` reference; no tag-only default is
allowed.

No new dependency, lockfile, service, database, migration, provider, IdP,
model/OCR/VLM/embedding/billing call, arbitrary URL/API/Shell/SQL/JavaScript,
external Benchmark, cloud resource, DNS/TLS, or real account/data may be
introduced. Missing local Helm/SBOM/recording/kind/k3d tools are recorded as
`unavailable`, never as passed. Media is supplied only when produced by a real
local deterministic run; otherwise the static fallback and unavailable record
are required.

## Reproducible demo contract

`tests/integration/w16_demo.py` emits canonical, redacted JSON events for the
synthetic JML story: observe → plan → execute → recover → verify, DOM-to-vision
fallback, contradiction follow-up, cross-system plan, high-risk approval,
worker restart recovery, independent Verifier/Grader, and trace/replay. It
contains no page/DOM/screenshot/model/tool payload, secret, cookie, token,
nonce, DSN, machine path, URL query, or personal data. The smoke asserts stable
hash, synthetic account markers, `finished_ungraded`, independent grading, and
zero real calls/cost. It is not a product-success source or a claim about model
quality, production SLO, ROI, significance, or certification.

## SBOM contract

`scripts/generate_sbom.py` is the deterministic local generator. It reads only
the frozen Python/npm lockfiles, Dockerfile base-image declarations, and this
chart; normalizes the SPDX 2.3 timestamp to the fixed epoch and sorts all
components. `docs/sbom.spdx.json` is generated output and must have a stable
SHA-256 for unchanged inputs. Artifact checksums come from lockfile integrity
or package hashes. If a container digest or generator is unavailable, the
machine-readable status and evidence say so; no hand-written component list is
called a passed SBOM.

## Exact implementation allowlist

Only these exact paths may be created or modified. There are no directory
wildcards:

~~~text
AGENTS.md
README.md
README.zh-CN.md
CONTRIBUTING.md
SECURITY.md
docs/agent-contract.md
docs/architecture.md
docs/benchmark-card.md
docs/demo.md
docs/model-card.md
docs/release-notes-v1.0.0.md
docs/sbom.spdx.json
docs/sbom-status.md
docs/adr/0016-w16-release.md
docs/plans/week-16-release.md
docs/evidence/week-16-release.md
deploy/helm/flowpilot-arena/Chart.yaml
deploy/helm/flowpilot-arena/values.yaml
deploy/helm/flowpilot-arena/values.schema.json
deploy/helm/flowpilot-arena/templates/_helpers.tpl
deploy/helm/flowpilot-arena/templates/configmap.yaml
deploy/helm/flowpilot-arena/templates/deployment.yaml
deploy/helm/flowpilot-arena/templates/networkpolicy.yaml
deploy/helm/flowpilot-arena/templates/NOTES.txt
deploy/helm/flowpilot-arena/templates/service.yaml
deploy/helm/flowpilot-arena/templates/serviceaccount.yaml
deploy/helm/flowpilot-arena/templates/tests/test-connection.yaml
scripts/generate_sbom.py
tests/integration/w16_demo.py
tests/integration/test_w16_demo.py
tests/integration/w16_demo_smoke.py
~~~

## Verification and stop condition

Run all locally available gates listed in `AGENTS.md`: locked dependency sync,
Ruff/format/strict mypy/pytest, both frontend npm checks, YAML/workflow policy,
Helm lint/schema/deterministic render and Kubernetes security scans, Compose
config/build/up/health and cleanup, migration empty upgrade/current/check/
downgrade/upgrade, W4-W15 regression plus W13/W14 smokes, W15 Development-only
smoke, W16 demo smoke, W15 hash immutability, real-call/cost-zero and
sensitive-field scans, SBOM validation, bilingual README/link/command checks,
demo redaction/source checks, detect-private-key, gitleaks, diff check, and
exact staged review. Never run W15 frozen Reporting final, W12 formal
Validation, external Benchmarks, or cloud deployment.

After evidence reconciliation, explicitly stage only changed paths in this
allowlist and create exactly one local commit:

    feat: add W16 release and reproducible demo

Then stop. Remote delivery (push/PR/merge/main CI), public-readiness final
approval, repository visibility change, anonymous clone, cloud deployment,
annotated `v1.0.0` tag, and Release `v1.0.0 - FlowPilot Arena` require later,
separate user authorization.
