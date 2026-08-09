# SBOM status

The machine-readable artifact is [docs/sbom.spdx.json](sbom.spdx.json), generated
by [scripts/generate_sbom.py](../scripts/generate_sbom.py) from frozen uv/npm
lockfiles, Dockerfile base-image declarations, and the W16 Helm chart.

The local generator is deterministic: inputs are sorted, SPDX creation time is
the fixed epoch 1970-01-01T00:00:00Z, and package checksums come only from
lockfile integrity/hash fields. Re-running the generator with unchanged inputs
must produce the same bytes and SHA-256.

The artifact explicitly records container_image_digest_coverage=unavailable.
Dockerfiles currently declare build tags and no authorized immutable application
image has been published; no registry was contacted. Therefore this is a
machine-readable partial inventory plus an honest unavailable status, not a
claim that a complete image-inclusive SBOM or cloud deployment passed. Syft,
Trivy, CycloneDX CLI, Helm, and kind/k3d were not installed in this environment
when checked.

No credential, private URL, machine path, or secret is present in the artifact.
