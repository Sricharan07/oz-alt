from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib import request


def chunk_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def embedding_for_text(text: str) -> list[float] | None:
    sha = chunk_sha(text)
    cached = read_cached_embedding(sha)
    if cached is not None:
        return cached

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    embedding = request_openai_embedding(api_key, text)
    if embedding is not None:
        write_cached_embedding(sha, embedding)
    return embedding


def request_openai_embedding(api_key: str, text: str) -> list[float] | None:
    payload = {
        "model": os.environ.get("OZ_EMBEDDING_MODEL", "text-embedding-3-small"),
        "input": text,
    }
    req = request.Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
        embedding = body["data"][0]["embedding"]
        if isinstance(embedding, list):
            return [float(value) for value in embedding]
    except Exception:
        return None
    return None


def read_cached_embedding(sha: str) -> list[float] | None:
    path = cache_path(sha)
    if not path.exists():
        return None
    try:
        return [float(value) for value in json.loads(path.read_text(encoding="utf-8"))]
    except Exception:
        return None


def write_cached_embedding(sha: str, embedding: list[float]) -> None:
    path = cache_path(sha)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(embedding, separators=(",", ":")), encoding="utf-8")


def cache_path(sha: str) -> Path:
    root = Path(os.environ.get("OZ_EMBEDDING_CACHE", Path.home() / ".codo" / "embedding-cache"))
    return root / sha[:2] / f"{sha}.json"


def row_with_embedding(row: dict[str, Any], text: str) -> dict[str, Any]:
    row["chunk_sha"] = chunk_sha(text)
    embedding = embedding_for_text(text)
    if embedding is not None:
        row["embedding"] = embedding
    return row
