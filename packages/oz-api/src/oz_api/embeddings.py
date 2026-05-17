from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib import request

LOGGER = logging.getLogger(__name__)

DEFAULT_EMBEDDING_PROVIDER = "voyage"
DEFAULT_VOYAGE_MODEL = "voyage-code-3"
DEFAULT_VOYAGE_DIMENSIONS = 1024
DEFAULT_OPENAI_MODEL = "text-embedding-3-large"
DEFAULT_JINA_MODEL = "jina-code-v2"


def embedding_for_query(query: str) -> list[float] | None:
    return embedding_for_text(query, input_type="query")


def embedding_for_text(text: str, *, input_type: str = "document") -> list[float] | None:
    provider = embedding_provider()
    if provider == "voyage":
        return voyage_embedding(voyage_api_key(), text, input_type=input_type)
    if provider == "openai":
        return openai_embedding(openai_api_key(), text)
    if provider == "jina":
        return jina_embedding(jina_api_key(), text)
    return None


def embedding_provider() -> str:
    value = os.environ.get("OZ_EMBEDDING_PROVIDER", DEFAULT_EMBEDDING_PROVIDER).strip().lower()
    if value in {"voyage", "openai", "jina", "none"}:
        return value
    return DEFAULT_EMBEDDING_PROVIDER


def embedding_dimensions() -> int:
    try:
        configured = os.environ.get("OZ_EMBEDDING_DIMENSIONS")
        if configured:
            return int(configured)
    except ValueError:
        LOGGER.warning("invalid OZ_EMBEDDING_DIMENSIONS=%r", os.environ.get("OZ_EMBEDDING_DIMENSIONS"))
    return DEFAULT_VOYAGE_DIMENSIONS


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


def valid_embedding(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == embedding_dimensions()
        and all(isinstance(item, (int, float)) for item in value)
    )


def voyage_embedding(api_key: str | None, text: str, *, input_type: str) -> list[float] | None:
    if not api_key:
        return None
    payload = {
        "model": embedding_model(),
        "input": [text],
        "input_type": "query" if input_type == "query" else "document",
        "output_dimension": embedding_dimensions(),
        "output_dtype": "float",
    }
    return request_embedding(
        "https://api.voyageai.com/v1/embeddings",
        payload,
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        result_path=("data", 0, "embedding"),
    )


def openai_embedding(api_key: str | None, text: str) -> list[float] | None:
    if not api_key:
        return None
    payload: dict[str, Any] = {"model": embedding_model(), "input": text}
    if embedding_model().startswith("text-embedding-3"):
        payload["dimensions"] = embedding_dimensions()
    return request_embedding(
        "https://api.openai.com/v1/embeddings",
        payload,
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        result_path=("data", 0, "embedding"),
    )


def jina_embedding(api_key: str | None, text: str) -> list[float] | None:
    endpoint = os.environ.get("OZ_JINA_EMBEDDING_URL", "https://api.jina.ai/v1/embeddings")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {"model": embedding_model(), "input": [text]}
    return request_embedding(endpoint, payload, headers, result_path=("data", 0, "embedding"))


def request_embedding(
    endpoint: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    result_path: tuple[Any, ...],
) -> list[float] | None:
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=float(os.environ.get("OZ_EMBEDDING_TIMEOUT_SECONDS", "20"))) as response:
            body = json.loads(response.read().decode("utf-8"))
        embedding = nested_value(body, result_path)
        if isinstance(embedding, list):
            values = [float(value) for value in embedding]
            if len(values) == embedding_dimensions():
                return values
            LOGGER.warning(
                "embedding dimension mismatch provider=%s model=%s got=%s expected=%s",
                embedding_provider(),
                embedding_model(),
                len(values),
                embedding_dimensions(),
            )
    except Exception as exc:
        LOGGER.info("embedding request failed provider=%s model=%s: %s", embedding_provider(), embedding_model(), exc)
    return None


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


def voyage_api_key() -> str | None:
    return normalized_key(os.environ.get("VOYAGE_API_KEY") or os.environ.get("OZ_VOYAGE_API_KEY"))


def openai_api_key() -> str | None:
    return normalized_key(os.environ.get("OPENAI_API_KEY") or os.environ.get("OZ_OPENAI_API_KEY"))


def jina_api_key() -> str | None:
    return normalized_key(os.environ.get("JINA_API_KEY") or os.environ.get("OZ_JINA_API_KEY"))


def normalized_key(value: str | None) -> str | None:
    key = str(value or "").strip()
    return key or None
