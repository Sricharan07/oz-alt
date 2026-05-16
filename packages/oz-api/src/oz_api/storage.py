from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RegistryStorage:
    repo_root: Path
    packs_bucket: str | None = None
    catalog_bucket: str | None = None
    admin_bucket: str | None = None
    pack_prefix: str = "packs"
    pack_public_base_url: str | None = None
    catalog_key: str = "catalog.json"
    admin_prefix: str = "admin"

    @classmethod
    def from_env(cls, repo_root: Path) -> "RegistryStorage":
        packs_bucket = os.environ.get("OZ_PACKS_BUCKET")
        return cls(
            repo_root=repo_root,
            packs_bucket=packs_bucket,
            catalog_bucket=os.environ.get("OZ_CATALOG_BUCKET") or packs_bucket,
            admin_bucket=os.environ.get("OZ_ADMIN_BUCKET") or packs_bucket,
            pack_prefix=os.environ.get("OZ_PACK_PREFIX", "packs").strip("/"),
            pack_public_base_url=(os.environ.get("OZ_PACK_PUBLIC_BASE_URL") or "").rstrip("/") or None,
            catalog_key=os.environ.get("OZ_CATALOG_KEY", "catalog.json").strip("/"),
            admin_prefix=os.environ.get("OZ_ADMIN_PREFIX", "admin").strip("/"),
        )

    @property
    def registry_root(self) -> Path:
        return self.repo_root / "registry"

    @property
    def fixtures_root(self) -> Path:
        return self.registry_root / "fixtures"

    @property
    def packs_root(self) -> Path:
        return self.registry_root / "packs"

    @property
    def catalog_path(self) -> Path:
        return self.registry_root / "catalog.json"

    @property
    def admin_root(self) -> Path:
        return self.registry_root / "admin"

    def load_catalog_document(self) -> dict[str, Any]:
        if self.catalog_bucket:
            remote = self._get_s3_json(self.catalog_bucket, self.catalog_key)
            if remote is not None:
                return remote
        if self.catalog_path.exists():
            return json.loads(self.catalog_path.read_text(encoding="utf-8"))
        return {"schema_version": 1, "generated_at": None, "libraries": self.discover_catalog()}

    def load_catalog(self) -> list[dict[str, Any]]:
        return list(self.load_catalog_document().get("libraries", []))

    def catalog_generated_at(self) -> str | None:
        generated_at = self.load_catalog_document().get("generated_at")
        return str(generated_at) if generated_at else None

    def get_pack_bytes(self, vendor: str, library: str, version: str) -> bytes | None:
        if self.packs_bucket:
            for key in self._candidate_pack_keys(vendor, library, version):
                payload = self._get_s3_bytes(self.packs_bucket, key)
                if payload is not None:
                    return payload

        pack_path = self.packs_root / vendor / library / f"{version}.ozpack"
        if pack_path.exists():
            return pack_path.read_bytes()
        return None

    def get_pack_url(self, vendor: str, library: str, version: str) -> str | None:
        if not self.pack_public_base_url:
            return None
        return f"{self.pack_public_base_url}/{vendor}/{library}/{version}.ozpack"

    def put_pack_bytes(self, vendor: str, library: str, version: str, body: bytes) -> str:
        key = f"{self.pack_prefix}/{vendor}/{library}/{version}.ozpack"
        if self.packs_bucket:
            self._put_s3_bytes(
                self.packs_bucket,
                key,
                body,
                content_type="application/vnd.oz.pack",
                cache_control="public, max-age=31536000, immutable",
            )
            return key

        path = self.packs_root / vendor / library / f"{version}.ozpack"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return str(path.relative_to(self.repo_root))

    def put_catalog_document(self, document: dict[str, Any]) -> None:
        body = json.dumps(document, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        if self.catalog_bucket:
            self._put_s3_bytes(
                self.catalog_bucket,
                self.catalog_key,
                body,
                content_type="application/json",
                cache_control="public, max-age=300",
            )
            return

        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
        self.catalog_path.write_bytes(body)

    def append_admin_event(self, stream: str, event: dict[str, Any]) -> None:
        if self.admin_bucket:
            key = f"{self.admin_prefix}/{stream}.jsonl"
            existing = self._get_s3_bytes(self.admin_bucket, key) or b""
            body = existing.decode("utf-8")
            body += json.dumps(event, sort_keys=True) + "\n"
            self._put_s3_bytes(self.admin_bucket, key, body.encode("utf-8"))
            return

        path = self.admin_root / f"{stream}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, sort_keys=True) + "\n")

    def read_admin_events(self, stream: str) -> list[dict[str, Any]]:
        if self.admin_bucket:
            key = f"{self.admin_prefix}/{stream}.jsonl"
            body = self._get_s3_bytes(self.admin_bucket, key)
            if body is None:
                return []
            return read_jsonl_text(body.decode("utf-8"))

        path = self.admin_root / f"{stream}.jsonl"
        if not path.exists():
            return []
        return read_jsonl_text(path.read_text(encoding="utf-8"))

    def discover_catalog(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for fixture in self.fixtures_root.glob("*/*/*"):
            if not fixture.is_dir():
                continue
            vendor, library, version = fixture.parts[-3:]
            description = read_description(fixture, library)
            rows.append(
                {
                    "vendor": vendor,
                    "library": library,
                    "version": version,
                    "description": description,
                    "keywords": normalize_query(description),
                    "fixture_path": str(fixture.relative_to(self.repo_root)),
                    "pack_path": None,
                    "ref_sha": "local",
                }
            )
        return rows

    def _candidate_pack_keys(self, vendor: str, library: str, version: str) -> list[str]:
        keys = [
            f"{self.pack_prefix}/{vendor}/{library}/{version}.ozpack",
            f"{vendor}/{library}/{version}.ozpack",
        ]
        for entry in self.load_catalog():
            if (
                entry.get("vendor") == vendor
                and entry.get("library") == library
                and entry.get("version") == version
            ):
                pack_path = str(entry.get("pack_path") or "").strip("/")
                if pack_path:
                    keys.insert(0, pack_path.removeprefix("registry/"))
                    keys.insert(0, pack_path)
        output: list[str] = []
        for key in keys:
            key = key.strip("/")
            if key and key not in output:
                output.append(key)
        return output

    def _get_s3_json(self, bucket: str, key: str) -> dict[str, Any] | None:
        body = self._get_s3_bytes(bucket, key)
        if body is None:
            return None
        return json.loads(body.decode("utf-8"))

    def _get_s3_bytes(self, bucket: str, key: str) -> bytes | None:
        client = s3_client()
        if client is None:
            return None
        try:
            response = client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except Exception:
            return None

    def _put_s3_bytes(
        self,
        bucket: str,
        key: str,
        body: bytes,
        *,
        content_type: str | None = None,
        cache_control: str | None = None,
    ) -> None:
        client = s3_client()
        if client is None:
            return
        kwargs: dict[str, Any] = {"Bucket": bucket, "Key": key, "Body": body}
        if content_type:
            kwargs["ContentType"] = content_type
        if cache_control:
            kwargs["CacheControl"] = cache_control
        client.put_object(**kwargs)


def s3_client() -> Any | None:
    try:
        import boto3  # type: ignore
    except ImportError:
        return None
    return boto3.client("s3")


def read_jsonl_text(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_description(fixture: Path, library: str) -> str:
    readme = fixture / "README.md"
    if readme.exists():
        for line in readme.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped
    return f"{library} documentation"


def normalize_query(query: str) -> list[str]:
    terms: list[str] = []
    current: list[str] = []
    for char in query.lower():
        if char.isalnum() or char == "_":
            current.append(char)
        elif current:
            terms.append("".join(current))
            current.clear()
    if current:
        terms.append("".join(current))
    return terms
