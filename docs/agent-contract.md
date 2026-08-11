# W16 agent contract — release and reproducible demo

## Authority and frozen history

This contract also governs the separately authorized W16 post-release
evidence closure on `codex/w16-post-release-evidence`. The branch starts at
the verified PR 53 merge on `origin/main`,
`14ad304ef64df638c9a61a898db5c3329021fd33`, which contains
the original W16 commit `23f546daa8298bfaed20a2574fa9378055d26090` and
W16 PR 45 merge `d1b03993fc912179d3cdbef00b9f26f524ca9c52`. W12
(`w12-production`), W13
(`w13-observability`), W14 (`w14-security`), and W15 (`w15-evaluation`) tags,
releases, merges, reports, protocols, schemas, catalogs, and hashes are
immutable. The repository, four GHCR packages, annotated `v1.0.0` tag, and
GitHub Release are already public and final. This follow-up authorizes the
exact post-release evidence changes, push, PR, normal CI, squash merge,
anonymous verification, and deployment to the previously authorized Aliyun
ACK target. The selected-actions policy addition and the two exact workflow
dispatches are complete and must not be repeated. It does not authorize history
rewrite, rollback, retag, rerelease, editing the existing GitHub Release, or
deployment to any other cloud target. Cloud mutation requires a concrete
authenticated ACK context and recoverable target values; credentials must
never be committed or printed.

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
external Benchmark, or real account/data may be introduced. Product behavior
is frozen. The two API Dockerfiles may remove only build-time `uv`/`pip` and
cache material from their final runtime images, while their project metadata
may declare the repository's existing Apache-2.0 license. Buildx-generated
maximum provenance and SBOM attestations remain required. GitHub native
Artifact Attestations use only the pinned action named in `AGENTS.md`.
Existing release digests receive SPDX SBOM attestations; signed build
provenance is generated only alongside a real new image build. Missing
authorized Helm, kind, Syft, Trivy, or cloud verification is recorded as
`unavailable`, never as passed.
Media is supplied only when produced by a real deterministic run; otherwise
the static fallback and unavailable record are required.

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

## Exact post-release evidence allowlist

Only these exact paths may be created or modified. There are no directory
wildcards:

~~~text
AGENTS.md
README.md
README.zh-CN.md
docs/agent-contract.md
docs/evidence/week-16-release.md
docs/sbom-status.md
~~~

## Verification and stop condition

Run the locally available post-release closure gates listed in `AGENTS.md`:
YAML parsing, W15 hash immutability, detect-private-key, gitleaks, diff check,
exact staged review, and README/link/command checks. Normal PR and main CI
provide the full repository regression suite. The final Private workflow
31316287397 already passed the image, SBOM/Trivy, DNS, and kind lifecycle
gates. Never run W15 frozen Reporting final, W12 formal Validation, or
external Benchmarks. The Aliyun deployment is limited to the recovered
authorized ACK context, namespace-scoped Helm resources, immutable image
digests, and synthetic demo settings.

After local evidence verification, explicitly stage only changed paths in this
allowlist and create the evidence commit:

    docs: record W16 post-release attestations

Push, PR, normal CI, and squash merge are authorized. Runs 31454356060 and
31454378571, their downloaded artifacts, and anonymous verification provide
the exact evidence; neither workflow may be rerun. The annotated `v1.0.0` tag
and existing Release remain immutable. Aliyun ACK execution remains pending
only because the current runtime has no kubeconfig or kubectl context; a later
cloud-evidence change is allowed after the authorized context is restored.
