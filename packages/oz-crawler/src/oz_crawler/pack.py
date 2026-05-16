from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any


def write_pack(source_root: Path, destination: Path, vendor: str, library: str, version: str) -> dict[str, Any]:
    body, manifest = build_pack_bytes(source_root, vendor, library, version)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(body)
    return manifest


def build_pack_bytes(source_root: Path, vendor: str, library: str, version: str) -> tuple[bytes, dict[str, Any]]:
    tree_blobs: list[dict[str, Any]] = []
    pack_blobs: list[dict[str, Any]] = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source_root).as_posix()
        body = path.read_bytes()
        sha = sha256_hex(body)
        size = len(body)
        tree_blobs.append({"path": relative, "sha256": sha, "size": size})
        pack_blobs.append(
            {
                "path": relative,
                "sha256": sha,
                "size": size,
                "content_base64": base64.b64encode(body).decode("ascii"),
            }
        )

    tree_manifest = {"vendor": vendor, "library": library, "version": version, "blobs": tree_blobs}
    manifest = {
        "schema_version": 1,
        "vendor": vendor,
        "library": library,
        "version": version,
        "tree_sha256": sha256_hex(canonical_json(tree_manifest)),
        "blobs": tree_blobs,
    }
    pack = {"manifest": manifest, "blobs": pack_blobs}
    return canonical_json(pack), manifest


def canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()
