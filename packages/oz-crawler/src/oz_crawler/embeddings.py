from __future__ import annotations

import json
import logging
import os
import time
from typing import Any
from urllib import request

from oz_crawler.token_counting import token_count

_OPENAI_API_KEY_CACHE: str | None = None
LOGGER = logging.getLogger(__name__)
DEFAULT_PROVIDER = "voyage"
DEFAULT_VOYAGE_MODEL = "voyage-code-3"
DEFAULT_OPENAI_MODEL = "text-embedding-3-large"
DEFAULT_JINA_MODEL = "jina-code-v2"
DEFAULT_DIMENSIONS = 1024
_REQUEST_TIMESTAMPS: list[float] = []
_TOKEN_TIMESTAMPS: list[tuple[float, int]] = []


def embeddings_for_texts(texts: list[str]) -> list[list[float] | None]:
    results: list[list[float] | None] = [None] * len(texts)
    pending: list[tuple[int, str]] = []
    for index, text in enumerate(texts):
        if text.strip():
            pending.append((index, text))

    for batch in embedding_batches(pending):
        batch_texts = [text for _, text in batch]
        throttle_sync_batch(sum(token_count(text) for text in batch_texts))
        embeddings = request_embeddings_for_provider(batch_texts)
        for (index, _), embedding in zip(batch, embeddings, strict=False):
            if embedding is None:
                continue
            results[index] = embedding
    return results


def embedding_batch_size() -> int:
    try:
        return max(1, min(int(os.environ.get("OZ_EMBEDDING_BATCH_SIZE", "128")), 128))
    except ValueError:
        return 128


def embedding_max_tokens_per_request() -> int:
    try:
        return max(1, int(os.environ.get("OZ_EMBEDDING_SYNC_MAX_TOKENS_PER_REQUEST", "100000")))
    except ValueError:
        return 100000


def embedding_batches(pending: list[tuple[int, str]]) -> list[list[tuple[int, str]]]:
    max_inputs = embedding_batch_size()
    max_tokens = embedding_max_tokens_per_request()
    batches: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    current_tokens = 0
    for item in pending:
        item_tokens = token_count(item[1])
        if current and (len(current) >= max_inputs or current_tokens + item_tokens > max_tokens):
            batches.append(current)
            current = []
            current_tokens = 0
        current.append(item)
        current_tokens += item_tokens
    if current:
        batches.append(current)
    return batches


def request_embeddings_for_provider(texts: list[str]) -> list[list[float] | None]:
    provider = embedding_provider()
    if provider == "voyage":
        return request_voyage_embeddings(voyage_api_key_from_env(), texts)
    if provider == "openai":
        return request_openai_embeddings(openai_api_key_from_env(), texts)
    if provider == "jina":
        return request_jina_embeddings(jina_api_key_from_env(), texts)
    return [None] * len(texts)


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


def throttle_sync_batch(tokens: int) -> None:
    rpm_limit = int_env("OZ_EMBEDDING_SYNC_RPM_LIMIT", 1500)
    tpm_limit = int_env("OZ_EMBEDDING_SYNC_TPM_LIMIT", 2500000)
    if rpm_limit <= 0 and tpm_limit <= 0:
        return
    while True:
        now = time.monotonic()
        prune_rate_windows(now)
        projected_requests = len(_REQUEST_TIMESTAMPS) + 1
        projected_tokens = sum(value for _, value in _TOKEN_TIMESTAMPS) + max(tokens, 0)
        if (rpm_limit <= 0 or projected_requests <= rpm_limit) and (tpm_limit <= 0 or projected_tokens <= tpm_limit):
            _REQUEST_TIMESTAMPS.append(now)
            _TOKEN_TIMESTAMPS.append((now, max(tokens, 0)))
            return
        sleep_for = min_sleep_until_window_moves(now)
        LOGGER.info("embedding throttle sleeping %.2fs for rpm/tpm headroom", sleep_for)
        time.sleep(sleep_for)


def prune_rate_windows(now: float) -> None:
    cutoff = now - 60
    while _REQUEST_TIMESTAMPS and _REQUEST_TIMESTAMPS[0] <= cutoff:
        del _REQUEST_TIMESTAMPS[0]
    while _TOKEN_TIMESTAMPS and _TOKEN_TIMESTAMPS[0][0] <= cutoff:
        del _TOKEN_TIMESTAMPS[0]


def min_sleep_until_window_moves(now: float) -> float:
    oldest = []
    if _REQUEST_TIMESTAMPS:
        oldest.append(_REQUEST_TIMESTAMPS[0])
    if _TOKEN_TIMESTAMPS:
        oldest.append(_TOKEN_TIMESTAMPS[0][0])
    if not oldest:
        return 1.0
    return max(1.0, 60.0 - (now - min(oldest)) + 0.05)


def int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        LOGGER.warning("invalid %s=%r", name, os.environ.get(name))
        return default


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
