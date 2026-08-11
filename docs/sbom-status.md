# SBOM status

The machine-readable artifact is [docs/sbom.spdx.json](sbom.spdx.json), generated
by [scripts/generate_sbom.py](../scripts/generate_sbom.py) from frozen uv/npm
lockfiles, Dockerfile base-image declarations, and the W16 Helm chart.

The local generator is deterministic: inputs are sorted, SPDX creation time is
the fixed epoch 1970-01-01T00:00:00Z, and package checksums come only from
lockfile integrity/hash fields. Re-running the generator with unchanged inputs
must produce the same bytes and SHA-256.

The artifact explicitly records container_image_digest_coverage=unavailable.
The four release Dockerfiles now checksum-pin their linux/amd64 Docker Official
Image bases, but application-image digests and their registry-generated SBOMs
remain workflow artifacts rather than inputs to this repository generator.
Therefore this repository artifact remains a machine-readable partial
inventory, not a claim that a complete registry-image SBOM or cloud deployment
passed. Repeated remediation generation produced 355 packages and byte SHA-256
`a3e036f6ace6966df83f9d10c6a5133840a3496e367bb5f7caa78d6c07b038db`.

The first registry-backed run with jobs, 31308404308, generated four Private
digests and SPDX/Trivy artifacts. Its four images had zero secret findings but
120 HIGH/CRITICAL occurrences, so they are not releasable. The authorized
remediation rebuilt all four local `linux/amd64` images from checksum-pinned
Alpine 3.24 bases and updated the container-only uv installer. Syft 1.50.0
generated valid SPDX 2.3 documents with 1,117 control-api, 1,110 sandbox-api,
and 72 packages in each Web image. Trivy 0.73.0 with a freshly downloaded
database found zero HIGH/CRITICAL and zero secret findings in every remediated
local image. The final post-merge registry workflow 31316287397 reproduced
those results. Its four immutable image digests and paired Syft/Trivy artifacts
are recorded in `docs/evidence/week-16-release.md`; future digests are never
guessed or hand-written into this repository inventory.

The final registry SPDX artifacts contained 1,117, 1,110, 72, and 72 packages
for control-api, sandbox-api, control-web, and sandbox-web. Their declared
license fields were not uniformly authoritative: 1,051 backend packages and
one package in each Web image were `NOASSERTION` in Syft output. A post-release
audit traced 1,038 of each backend count to Rust components embedded in the
build-only `uv` executable that had been left in the runtime image. Six more
were pip's Windows launcher binaries, three came from uv cache metadata, and
the local project lacked PEP 621 license metadata. The post-release image
change removes system `uv` and pip after the locked environment is built,
disables uv cache persistence, and declares the repository's existing
Apache-2.0 license in both API project files. It does not hand-edit or infer
licenses in generated SBOM JSON.

The release workflow now separates `licenseDeclared` from
`licenseConcluded`. It gates unexpected declared `NOASSERTION` packages while
allowing only the base-image `.python-rundeps`, the Python binary package, and
the document-root image package. `licenseConcluded=NOASSERTION` remains an
honest statement that no independent legal conclusion was performed. Exact
post-release package counts and checksums are recorded only after the remote
registry workflow passes.

The repository became Public after run 31316287397. The post-release workflow
therefore adds GitHub native SLSA provenance to new builds and native SPDX 2.3
SBOM attestations to new and existing release digests through the immutable
`actions/attest` commit recorded in the W16 contract. Existing release images
receive SBOM attestations only; their original build provenance is never
retroactively claimed as GitHub-native.

No credential, private URL, machine path, or secret is present in the artifact.
