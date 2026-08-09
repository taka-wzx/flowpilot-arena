# SBOM status

The machine-readable artifact is [docs/sbom.spdx.json](sbom.spdx.json), generated
by [scripts/generate_sbom.py](../scripts/generate_sbom.py) from frozen uv/npm
lockfiles, Dockerfile base-image declarations, and the W16 Helm chart.

The local generator is deterministic: inputs are sorted, SPDX creation time is
the fixed epoch 1970-01-01T00:00:00Z, and package checksums come only from
lockfile integrity/hash fields. Re-running the generator with unchanged inputs
must produce the same bytes and SHA-256.

The artifact explicitly records container_image_digest_coverage=unavailable.
Dockerfiles currently declare build tags and, at closure-commit time, no
immutable application image has been published. Therefore this repository
artifact remains a machine-readable partial inventory, not a claim that a
complete registry-image SBOM or cloud deployment passed.

The authorized closure used checksum-verified Syft 1.50.0 and Trivy 0.73.0,
built all four local `linux/amd64` images, and generated temporary per-image
SPDX documents. Trivy found no embedded secret findings, but every image failed the
HIGH/CRITICAL vulnerability gate. The post-merge manual workflow repeats these
checks against Private GHCR digests and uploads the reports as restricted
workflow artifacts. Those future registry digests are never guessed or written
into this pre-dispatch document.

No credential, private URL, machine path, or secret is present in the artifact.
