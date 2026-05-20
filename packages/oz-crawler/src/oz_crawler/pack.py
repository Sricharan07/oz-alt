from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
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
        if not pack_path_allowed(relative):
            continue
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
    sign_manifest(manifest)
    pack = {"manifest": manifest, "blobs": pack_blobs}
    return canonical_json(pack), manifest


def pack_path_allowed(relative: str) -> bool:
    if relative in {"INDEX.md", "README.md"}:
        return True
    if relative.startswith((".oz/", "guides/", "api-reference/", "examples/", "_symbols/")):
        return True
    return False


def canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sign_manifest(manifest: dict[str, Any]) -> None:
    key = os.environ.get("OZ_PACK_SIGNING_KEY")
    if not key:
        return
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as exc:  # pragma: no cover - depends on runtime packaging
        raise RuntimeError("OZ_PACK_SIGNING_KEY requires the cryptography package for Ed25519 signing") from exc

    payload = canonical_json({key_: value for key_, value in manifest.items() if key_ != "signature"})
    signing_key = Ed25519PrivateKey.from_private_bytes(decode_config_key(key, 32, "OZ_PACK_SIGNING_KEY"))
    signature = signing_key.sign(payload)
    manifest["signature"] = {
        "alg": "Ed25519",
        "key_id": os.environ.get("OZ_PACK_SIGNING_KEY_ID", "local"),
        "value": base64.urlsafe_b64encode(signature).decode("ascii").rstrip("="),
    }


def decode_config_key(value: str, expected_len: int, label: str) -> bytes:
    text = value.strip()
    if len(text) == expected_len * 2 and all(char in "0123456789abcdefABCDEF" for char in text):
        decoded = bytes.fromhex(text)
        if len(decoded) == expected_len:
            return decoded
    for decoder in (urlsafe_b64decode_unpadded, base64.b64decode):
        try:
            decoded = decoder(text)
        except (binascii.Error, ValueError):
            continue
        if len(decoded) == expected_len:
            return decoded
    raise ValueError(f"{label} must be {expected_len} bytes encoded as hex, base64url, or base64")


def urlsafe_b64decode_unpadded(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
