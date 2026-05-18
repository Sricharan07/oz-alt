from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegistryStorage:
    repo_root: Path
    packs_bucket: str | None = None
    catalog_bucket: str | None = None
    pack_prefix: str = "packs"
    pack_public_base_url: str | None = None
    catalog_key: str = "catalog.json"

    @classmethod
    def from_env(cls, repo_root: Path) -> "RegistryStorage":
        packs_bucket = os.environ.get("OZ_PACKS_BUCKET")
        return cls(
            repo_root=repo_root,
            packs_bucket=packs_bucket,
            catalog_bucket=os.environ.get("OZ_CATALOG_BUCKET") or packs_bucket,
            pack_prefix=os.environ.get("OZ_PACK_PREFIX", "packs").strip("/"),
            pack_public_base_url=(os.environ.get("OZ_PACK_PUBLIC_BASE_URL") or "").rstrip("/") or None,
            catalog_key=os.environ.get("OZ_CATALOG_KEY", "catalog.json").strip("/"),
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
                tags={"oz-role": "pack", "oz-canonical": "true", "oz-storage-tier": "hot"},
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
            raise RuntimeError("boto3 is required when S3 buckets are configured")
        try:
            response = client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except Exception as exc:
            code = getattr(getattr(exc, "response", {}), "get", lambda *_: {})("Error", {}).get("Code")
            if code in {"NoSuchKey", "404", "NotFound"}:
                return None
            raise

    def _put_s3_bytes(
        self,
        bucket: str,
        key: str,
        body: bytes,
        *,
        content_type: str | None = None,
        cache_control: str | None = None,
        tags: dict[str, str] | None = None,
        ) -> None:
        client = s3_client()
        if client is None:
            raise RuntimeError("boto3 is required when S3 buckets are configured")
        kwargs: dict[str, Any] = {"Bucket": bucket, "Key": key, "Body": body}
        if content_type:
            kwargs["ContentType"] = content_type
        if cache_control:
            kwargs["CacheControl"] = cache_control
        if tags:
            kwargs["Tagging"] = s3_tagging(tags)
        client.put_object(**kwargs)


def s3_client() -> Any | None:
    try:
        import boto3  # type: ignore
    except ImportError:
        return None
    kwargs: dict[str, Any] = {}
    endpoint_url = os.environ.get("OZ_S3_ENDPOINT_URL") or os.environ.get("AWS_ENDPOINT_URL_S3")
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    if os.environ.get("OZ_S3_FORCE_PATH_STYLE", "").lower() in {"1", "true", "yes", "on"}:
        try:
            from botocore.config import Config  # type: ignore

            kwargs["config"] = Config(s3={"addressing_style": "path"})
        except Exception as exc:
            LOGGER.warning("failed to configure S3 path-style addressing: %s", exc)
    return boto3.client("s3", **kwargs)


def s3_tagging(tags: dict[str, str]) -> str:
    return "&".join(f"{quote_plus(str(key))}={quote_plus(str(value))}" for key, value in sorted(tags.items()))


def database_configured() -> bool:
    return bool(os.environ.get("OZ_DATABASE_URL") or os.environ.get("DATABASE_URL"))


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
    seen: set[str] = set()
    for raw in re.findall(r"[A-Za-z0-9_]+", query):
        for term in query_term_variants(raw):
            if term and term not in seen:
                seen.add(term)
                terms.append(term)
    return terms


def query_term_variants(raw: str) -> list[str]:
    compact = re.sub(r"[^a-z0-9]+", "", raw.lower())
    split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", raw.replace("_", " "))
    variants = [compact]
    variants.extend(part.lower() for part in split.split())
    return variants
