"""Generate a deterministic SPDX 2.3 inventory from frozen local inputs.

The generator intentionally reports image-digest coverage separately. A Dockerfile
tag is not treated as an image checksum, and no registry is contacted.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "sbom.spdx.json"
FIXED_TIMESTAMP = "1970-01-01T00:00:00Z"
INPUTS = (
    "apps/control_api/uv.lock",
    "apps/sandbox_api/uv.lock",
    "apps/control_web/package-lock.json",
    "apps/sandbox_web/package-lock.json",
    "apps/browser_worker/Dockerfile",
    "apps/control_api/Dockerfile",
    "apps/control_web/Dockerfile",
    "apps/dom_agent/Dockerfile",
    "apps/hybrid_agent/Dockerfile",
    "apps/planning_agent/Dockerfile",
    "apps/recovery_worker/Dockerfile",
    "apps/sandbox_api/Dockerfile",
    "apps/sandbox_web/Dockerfile",
    "apps/vision_agent/Dockerfile",
    "apps/workflow_worker/Dockerfile",
    "deploy/helm/flowpilot-arena/Chart.yaml",
    "deploy/helm/flowpilot-arena/values.yaml",
    "deploy/helm/flowpilot-arena/values.schema.json",
    "deploy/helm/flowpilot-arena/templates/_helpers.tpl",
    "deploy/helm/flowpilot-arena/templates/configmap.yaml",
    "deploy/helm/flowpilot-arena/templates/deployment.yaml",
    "deploy/helm/flowpilot-arena/templates/networkpolicy.yaml",
    "deploy/helm/flowpilot-arena/templates/NOTES.txt",
    "deploy/helm/flowpilot-arena/templates/service.yaml",
    "deploy/helm/flowpilot-arena/templates/serviceaccount.yaml",
    "deploy/helm/flowpilot-arena/templates/tests/test-connection.yaml",
)
LOCAL_PROJECTS = ("apps/control_api", "apps/sandbox_api")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_source_paths(project: Path) -> list[Path]:
    return [
        project / "pyproject.toml",
        project / "Dockerfile",
        *sorted((project / "src").rglob("*.py")),
    ]


def input_paths() -> list[Path]:
    paths = [ROOT / relative for relative in INPUTS]
    for relative in LOCAL_PROJECTS:
        paths.extend(local_source_paths(ROOT / relative))
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def input_hash() -> str:
    digest = hashlib.sha256()
    for path in input_paths():
        relative = path.relative_to(ROOT).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def source_checksum(project: Path) -> str:
    digest = hashlib.sha256()
    for path in local_source_paths(project):
        digest.update(path.relative_to(project).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def spdx_package(
    package_id: str,
    name: str,
    version: str,
    purl: str,
    download: str,
    checksum: str | None,
    checksum_algorithm: str = "SHA256",
) -> dict[str, Any]:
    package: dict[str, Any] = {
        "SPDXID": package_id,
        "name": name,
        "versionInfo": version,
        "downloadLocation": download,
        "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "supplier": "NOASSERTION",
        "originator": "NOASSERTION",
        "externalRefs": [
            {
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": purl,
            }
        ],
    }
    if checksum is not None:
        package["checksums"] = [{"algorithm": checksum_algorithm, "checksumValue": checksum}]
    return package


def python_packages() -> list[dict[str, Any]]:
    packages: dict[tuple[str, str], dict[str, Any]] = {}
    for relative in ("apps/control_api/uv.lock", "apps/sandbox_api/uv.lock"):
        project = (ROOT / relative).parent
        lock = tomllib.loads((ROOT / relative).read_text(encoding="utf-8"))
        for entry in lock.get("package", []):
            name = str(entry["name"])
            version = str(entry["version"])
            wheel = next(iter(entry.get("wheels", [])), None)
            sdist = entry.get("sdist", {})
            artifact = wheel or sdist
            checksum = None
            download = "NOASSERTION"
            if artifact:
                download = str(artifact.get("url", "NOASSERTION"))
                raw_hash = str(artifact.get("hash", ""))
                checksum = raw_hash.removeprefix("sha256:") or None
            elif name.startswith("flowpilot-"):
                checksum = source_checksum(project)
            key = (name, version)
            packages[key] = spdx_package(
                f"SPDXRef-Py-{len(packages) + 1:04d}",
                name,
                version,
                f"pkg:pypi/{name}@{version}",
                download,
                checksum,
                "SHA256",
            )
    return list(packages.values())


def npm_packages() -> list[dict[str, Any]]:
    packages: dict[tuple[str, str], dict[str, Any]] = {}
    for relative in ("apps/control_web/package-lock.json", "apps/sandbox_web/package-lock.json"):
        lock = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        for path, entry in lock.get("packages", {}).items():
            if path == "" or "version" not in entry:
                continue
            name = str(entry.get("name") or path.rsplit("node_modules/", 1)[-1])
            version = str(entry["version"])
            integrity = str(entry.get("integrity", ""))
            checksum = None
            if integrity.startswith("sha512-"):
                import base64

                checksum = base64.b64decode(integrity[7:]).hex()
            key = (name, version)
            packages[key] = spdx_package(
                f"SPDXRef-Npm-{len(packages) + 1:04d}",
                name,
                version,
                f"pkg:npm/{quote(name, safe='')}@{version}",
                str(entry.get("resolved", "NOASSERTION")),
                checksum,
                "SHA512" if integrity.startswith("sha512-") else "SHA256",
            )
    return list(packages.values())


def image_declarations() -> list[str]:
    declarations: list[str] = []
    pattern = re.compile(r"^FROM\s+([^\s]+)", re.MULTILINE)
    for relative in INPUTS:
        if not relative.endswith("Dockerfile"):
            continue
        text = (ROOT / relative).read_text(encoding="utf-8")
        declarations.extend(pattern.findall(text))
    return sorted(set(declarations))


def build_document() -> dict[str, Any]:
    packages = sorted(
        python_packages() + npm_packages(),
        key=lambda item: (item["name"], item["versionInfo"]),
    )
    digest = input_hash()
    images = ",".join(image_declarations())
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "flowpilot-arena-w16-local-inputs",
        "documentNamespace": "https://flowpilot.invalid/spdx/w16/local-inputs",
        "creationInfo": {
            "created": FIXED_TIMESTAMP,
            "creators": ["Tool: flowpilot-sbom-generator/1.0"],
            "comment": (
                "Normalized epoch timestamp makes generation reproducible; "
                "artifact hashes are from frozen lockfile integrity data."
            ),
        },
        "documentDescribes": [package["SPDXID"] for package in packages],
        "packages": packages,
        "annotations": [
            {
                "annotationDate": FIXED_TIMESTAMP,
                "annotationType": "OTHER",
                "annotator": "Tool: flowpilot-sbom-generator/1.0",
                "comment": f"input_sha256={digest}",
            },
            {
                "annotationDate": FIXED_TIMESTAMP,
                "annotationType": "OTHER",
                "annotator": "Tool: flowpilot-sbom-generator/1.0",
                "comment": (
                    "container_image_digest_coverage=unavailable; "
                    f"dockerfile_from={images}; "
                    "tags are never promoted to image checksums"
                ),
            },
            {
                "annotationDate": FIXED_TIMESTAMP,
                "annotationType": "OTHER",
                "annotator": "Tool: flowpilot-sbom-generator/1.0",
                "comment": (
                    "helm_chart_reference=deploy/helm/flowpilot-arena; "
                    "enabled images require immutable digest values"
                ),
            },
        ],
    }


def main() -> int:
    document = build_document()
    OUTPUT.write_text(
        json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    summary = {
        "output": str(OUTPUT.relative_to(ROOT)),
        "sha256": sha256(OUTPUT.read_bytes()),
        "packages": len(document["packages"]),
        "image_digest_coverage": "unavailable",
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
