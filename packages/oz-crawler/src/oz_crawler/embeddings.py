from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any
from urllib import request

_OPENAI_API_KEY_CACHE: str | None = None
LOGGER = logging.getLogger(__name__)
DEFAULT_PROVIDER = "voyage"
DEFAULT_VOYAGE_MODEL = "voyage-code-3"
DEFAULT_OPENAI_MODEL = "text-embedding-3-large"
DEFAULT_JINA_MODEL = "jina-code-v2"
DEFAULT_DIMENSIONS = 1024


def chunk_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def embedding_cache_key(text: str) -> str:
    payload = "\0".join([embedding_provider(), embedding_model(), str(embedding_dimensions()), text])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def embedding_for_text(text: str) -> list[float] | None:
    embeddings = embeddings_for_texts([text])
    return embeddings[0] if embeddings else None


def embeddings_for_texts(texts: list[str]) -> list[list[float] | None]:
    results: list[list[float] | None] = [None] * len(texts)
    pending: list[tuple[int, str, str]] = []
    for index, text in enumerate(texts):
        sha = embedding_cache_key(text)
        cached = read_cached_embedding(sha)
        if cached is not None:
            results[index] = cached
        elif text.strip():
            pending.append((index, sha, text))

    batch_size = embedding_batch_size()
    for offset in range(0, len(pending), batch_size):
        batch = pending[offset : offset + batch_size]
        embeddings = request_embeddings_for_provider([text for _, _, text in batch])
        for (index, sha, _), embedding in zip(batch, embeddings, strict=False):
            if embedding is None:
                continue
            results[index] = embedding
            write_cached_embedding(sha, embedding)
    return results


def embedding_batch_size() -> int:
    try:
        return max(1, min(int(os.environ.get("OZ_EMBEDDING_BATCH_SIZE", "64")), 128))
    except ValueError:
        return 64


def request_embedding_for_provider(text: str) -> list[float] | None:
    embeddings = request_embeddings_for_provider([text])
    return embeddings[0] if embeddings else None


def request_embeddings_for_provider(texts: list[str]) -> list[list[float] | None]:
    provider = embedding_provider()
    if provider == "voyage":
        return request_voyage_embeddings(voyage_api_key_from_env(), texts)
    if provider == "openai":
        return request_openai_embeddings(openai_api_key_from_env(), texts)
    if provider == "jina":
        return request_jina_embeddings(jina_api_key_from_env(), texts)
    return [None] * len(texts)


def request_voyage_embedding(api_key: str | None, text: str) -> list[float] | None:
    embeddings = request_voyage_embeddings(api_key, [text])
    return embeddings[0] if embeddings else None


def request_voyage_embeddings(api_key: str | None, texts: list[str]) -> list[list[float] | None]:
    if not api_key:
        return [None] * len(texts)
    return request_embeddings(
        "https://api.voyageai.com/v1/embeddings",
        {
            "model": embedding_model(),
            "input": texts,
            "input_type": "document",
            "output_dimension": embedding_dimensions(),
            "output_dtype": "float",
        },
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        expected_count=len(texts),
    )


def request_openai_embedding(api_key: str | None, text: str) -> list[float] | None:
    embeddings = request_openai_embeddings(api_key, [text])
    return embeddings[0] if embeddings else None


def request_openai_embeddings(api_key: str | None, texts: list[str]) -> list[list[float] | None]:
    if not api_key:
        return [None] * len(texts)
    payload: dict[str, Any] = {"model": embedding_model(), "input": texts}
    if embedding_model().startswith("text-embedding-3"):
        payload["dimensions"] = embedding_dimensions()
    return request_embeddings(
        "https://api.openai.com/v1/embeddings",
        payload,
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        expected_count=len(texts),
    )


def request_jina_embedding(api_key: str | None, text: str) -> list[float] | None:
    embeddings = request_jina_embeddings(api_key, [text])
    return embeddings[0] if embeddings else None


def request_jina_embeddings(api_key: str | None, texts: list[str]) -> list[list[float] | None]:
    endpoint = os.environ.get("OZ_JINA_EMBEDDING_URL", "https://api.jina.ai/v1/embeddings")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return request_embeddings(
        endpoint,
        {"model": embedding_model(), "input": texts},
        headers,
        expected_count=len(texts),
    )


def request_embedding(
    endpoint: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    result_path: tuple[Any, ...],
) -> list[float] | None:
    embeddings = request_embeddings(endpoint, payload, headers, expected_count=1)
    return embeddings[0] if embeddings else None


def request_embeddings(
    endpoint: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    expected_count: int,
) -> list[list[float] | None]:
    output: list[list[float] | None] = [None] * expected_count
    req = request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list):
            return output
        for fallback_index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            index = item.get("index")
            if not isinstance(index, int):
                index = fallback_index
            if not 0 <= index < expected_count:
                continue
            embedding = item.get("embedding")
            if isinstance(embedding, list):
                values = [float(value) for value in embedding]
                if len(values) == embedding_dimensions():
                    output[index] = values
                else:
                    LOGGER.warning("embedding dimension mismatch got=%s expected=%s", len(values), embedding_dimensions())
    except Exception as exc:
        LOGGER.info("embedding request failed provider=%s model=%s: %s", embedding_provider(), embedding_model(), exc)
    return output


def nested_value(value: Any, path: tuple[Any, ...]) -> Any:
    current = value
    for key in path:
        if isinstance(key, int):
            if not isinstance(current, list) or key >= len(current):
                return None
            current = current[key]
        else:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
    return current


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
        row["embedding_model"] = embedding_model()
        row["embedding_dimensions"] = embedding_dimensions()
    return row


def embedding_provider() -> str:
    provider = os.environ.get("OZ_EMBEDDING_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    return provider if provider in {"voyage", "openai", "jina", "none"} else DEFAULT_PROVIDER


def embedding_model() -> str:
    configured = os.environ.get("OZ_EMBEDDING_MODEL", "").strip()
    if configured:
        return configured
    provider = embedding_provider()
    if provider == "openai":
        return DEFAULT_OPENAI_MODEL
    if provider == "jina":
        return DEFAULT_JINA_MODEL
    return DEFAULT_VOYAGE_MODEL


def embedding_dimensions() -> int:
    try:
        configured = os.environ.get("OZ_EMBEDDING_DIMENSIONS")
        if configured:
            return int(configured)
    except ValueError:
        LOGGER.warning("invalid OZ_EMBEDDING_DIMENSIONS=%r", os.environ.get("OZ_EMBEDDING_DIMENSIONS"))
    return DEFAULT_DIMENSIONS


def voyage_api_key_from_env() -> str | None:
    return normalized_api_key(os.environ.get("VOYAGE_API_KEY") or os.environ.get("OZ_VOYAGE_API_KEY"))


def jina_api_key_from_env() -> str | None:
    return normalized_api_key(os.environ.get("JINA_API_KEY") or os.environ.get("OZ_JINA_API_KEY"))


def normalized_api_key(value: Any) -> str | None:
    key = str(value or "").strip()
    return key or None


def openai_api_key_from_env() -> str | None:
    direct = normalized_openai_api_key(os.environ.get("OPENAI_API_KEY"))
    if direct:
        return direct

    secret_arn = os.environ.get("OPENAI_API_KEY_SECRET_ARN") or os.environ.get("OZ_OPENAI_API_KEY_SECRET_ARN")
    if not secret_arn:
        return None

    global _OPENAI_API_KEY_CACHE
    if _OPENAI_API_KEY_CACHE is not None:
        return _OPENAI_API_KEY_CACHE

    try:
        import boto3  # type: ignore

        response = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
    except Exception:
        return None

    value = secret_value_text(response)
    key = normalized_openai_api_key(value)
    if not key:
        key = normalized_openai_api_key_from_json(value)
    if key:
        _OPENAI_API_KEY_CACHE = key
    return key


def secret_value_text(response: dict[str, Any]) -> str:
    if response.get("SecretString"):
        return str(response["SecretString"])
    binary = response.get("SecretBinary")
    if isinstance(binary, bytes):
        return binary.decode("utf-8", errors="replace")
    return ""


def normalized_openai_api_key(value: Any) -> str | None:
    key = str(value or "").strip()
    return key if key.startswith("sk-") else None


def normalized_openai_api_key_from_json(value: str) -> str | None:
    try:
        payload = json.loads(value)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    for field in ("OPENAI_API_KEY", "openai_api_key", "api_key"):
        key = normalized_openai_api_key(payload.get(field))
        if key:
            return key
    return None
