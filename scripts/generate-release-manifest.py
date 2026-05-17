#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Oz release manifest and SPDX-like SBOM.")
    parser.add_argument("--dist", default="dist")
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", default="dist/release-manifest.json")
    parser.add_argument("--sbom", default="dist/sbom.spdx.json")
    args = parser.parse_args()

    dist = Path(args.dist)
    artifacts = artifact_entries(dist)
    manifest = {
        "schema_version": 1,
        "name": "oz",
        "version": args.version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git": git_metadata(),
        "artifacts": artifacts,
        "sbom": Path(args.sbom).name,
    }
    sbom = build_sbom(args.version, artifacts)
    write_json(Path(args.output), manifest)
    write_json(Path(args.sbom), sbom)
    print(json.dumps({"artifacts": len(artifacts), "manifest": args.output, "sbom": args.sbom}, sort_keys=True))
    return 0


def artifact_entries(dist: Path) -> list[dict[str, Any]]:
    entries = []
    ignored = {"release-manifest.json", "sbom.spdx.json"}
    for path in sorted(dist.glob("*")):
        if not path.is_file() or path.name in ignored:
            continue
        if path.name.endswith(".sha256"):
            continue
        digest = sha256_file(path)
        sidecar = path.with_name(path.name + ".sha256")
        if sidecar.exists():
            sidecar_text = sidecar.read_text(encoding="utf-8").strip()
            if digest not in sidecar_text:
                raise SystemExit(f"sha256 sidecar mismatch for {path.name}")
        entries.append({"name": path.name, "sha256": digest, "bytes": path.stat().st_size})
    if not entries:
        raise SystemExit(f"no release artifacts found in {dist}")
    return entries


def build_sbom(version: str, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"oz-{version}",
        "documentNamespace": f"https://tryoz.dev/sbom/oz-{version}",
        "creationInfo": {
            "created": datetime.now(timezone.utc).isoformat(),
            "creators": ["Tool: oz-generate-release-manifest"],
        },
        "packages": release_packages(version, artifacts),
    }


def release_packages(version: str, artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packages = [
        {
            "name": artifact["name"],
            "SPDXID": f"SPDXRef-Artifact-{idx}",
            "versionInfo": version,
            "downloadLocation": "NOASSERTION",
            "checksums": [{"algorithm": "SHA256", "checksumValue": artifact["sha256"]}],
            "filesAnalyzed": False,
        }
        for idx, artifact in enumerate(artifacts, start=1)
    ]
    packages.extend(cargo_packages())
    packages.extend(pyproject_packages())
    packages.extend(npm_packages())
    return packages


def cargo_packages() -> list[dict[str, Any]]:
    try:
        output = subprocess.check_output(["cargo", "metadata", "--format-version", "1", "--locked"], text=True)
        metadata = json.loads(output)
    except Exception:
        return []
    packages = []
    for idx, package in enumerate(metadata.get("packages", []), start=1):
        packages.append(
            {
                "name": package.get("name"),
                "SPDXID": f"SPDXRef-Cargo-{idx}",
                "versionInfo": package.get("version"),
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
            }
        )
    return packages


def pyproject_packages() -> list[dict[str, Any]]:
    packages = []
    for idx, path in enumerate(sorted(Path("packages").glob("*/pyproject.toml")), start=1):
        project = parse_pyproject(path.read_text(encoding="utf-8"))
        packages.append(
            {
                "name": project.get("name") or path.parent.name,
                "SPDXID": f"SPDXRef-Python-{idx}",
                "versionInfo": project.get("version", "0.0.0"),
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "externalRefs": [
                    {"referenceType": "purl", "referenceLocator": f"pkg:pypi/{dep}"}
                    for dep in project.get("dependencies", [])
                ],
            }
        )
    return packages


def parse_pyproject(text: str) -> dict[str, Any]:
    project: dict[str, Any] = {"dependencies": []}
    in_project = False
    in_dependencies = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_project = line == "[project]"
            in_dependencies = False
            continue
        if not in_project:
            continue
        if in_dependencies:
            if line.startswith("]"):
                in_dependencies = False
                continue
            if line.startswith('"') or line.startswith("'"):
                project["dependencies"].append(line.strip(",").strip('"').strip("'"))
            continue
        if line.startswith("dependencies") and "=" in line and line.endswith("["):
            in_dependencies = True
            continue
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if key in {"name", "version"}:
            project[key] = value.strip('"').strip("'")
    return project


def npm_packages() -> list[dict[str, Any]]:
    path = Path("packages/oz-npm/package.json")
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            "name": data.get("name"),
            "SPDXID": "SPDXRef-Npm-Wrapper",
            "versionInfo": data.get("version"),
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
        }
    ]


def git_metadata() -> dict[str, str]:
    return {
        "sha": env_or_command("GITHUB_SHA", ["git", "rev-parse", "HEAD"]),
        "ref": os.environ.get("GITHUB_REF_NAME", ""),
        "repository": os.environ.get("GITHUB_REPOSITORY", ""),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
    }


def env_or_command(env_name: str, command: list[str]) -> str:
    value = os.environ.get(env_name)
    if value:
        return value
    try:
        return subprocess.check_output(command, text=True).strip()
    except Exception:
        return ""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
