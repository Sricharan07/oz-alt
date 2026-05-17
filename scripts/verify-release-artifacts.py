#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Oz release manifest, checksums, and SBOM linkage.")
    parser.add_argument("--dist", default="dist")
    parser.add_argument("--manifest", default="dist/release-manifest.json")
    parser.add_argument("--sbom", default="dist/sbom.spdx.json")
    args = parser.parse_args()

    dist = Path(args.dist)
    manifest = read_json(Path(args.manifest))
    sbom = read_json(Path(args.sbom))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise SystemExit("release manifest has no artifacts")
    for artifact in artifacts:
        verify_artifact(dist, artifact)
    if manifest.get("sbom") != Path(args.sbom).name:
        raise SystemExit("manifest does not point at the expected SBOM")
    if sbom.get("spdxVersion") != "SPDX-2.3" or not sbom.get("packages"):
        raise SystemExit("SBOM is missing SPDX metadata or packages")
    print(json.dumps({"verified_artifacts": len(artifacts), "sbom_packages": len(sbom["packages"])}, sort_keys=True))
    return 0


def verify_artifact(dist: Path, artifact: dict[str, Any]) -> None:
    name = str(artifact.get("name") or "")
    if not name or "/" in name or name.startswith("."):
        raise SystemExit(f"invalid artifact name: {name}")
    path = dist / name
    if not path.exists():
        raise SystemExit(f"artifact missing: {name}")
    expected_size = int(artifact.get("bytes") or -1)
    if path.stat().st_size != expected_size:
        raise SystemExit(f"artifact size mismatch: {name}")
    digest = sha256_file(path)
    if digest != artifact.get("sha256"):
        raise SystemExit(f"artifact sha256 mismatch: {name}")
    sidecar = path.with_name(path.name + ".sha256")
    if sidecar.exists() and digest not in sidecar.read_text(encoding="utf-8"):
        raise SystemExit(f"artifact sha256 sidecar mismatch: {name}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} is not a JSON object")
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
