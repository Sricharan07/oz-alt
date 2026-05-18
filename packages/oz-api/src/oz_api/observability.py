from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import logging
import os
import time
import uuid
from typing import Any, Iterator

from oz_api.redis_store import redis_client


REQUEST_ID: contextvars.ContextVar[str] = contextvars.ContextVar("oz_request_id", default="")
TRACE_SAMPLE: contextvars.ContextVar[bool] = contextvars.ContextVar("oz_trace_sample", default=False)

HISTOGRAM_BUCKETS_SECONDS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
RESERVED_LOG_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id
        if TRACE_SAMPLE.get():
            payload["sampled"] = True
        for key, value in record.__dict__.items():
            if key in RESERVED_LOG_ATTRS or key.startswith("_"):
                continue
            payload[key] = json_safe(value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def configure_logging() -> None:
    level = os.environ.get("OZ_LOG_LEVEL", "INFO").upper()
    log_format = os.environ.get("OZ_LOG_FORMAT", "json" if os.environ.get("OZ_ENV") == "production" else "text")
    handler = logging.StreamHandler()
    if log_format.lower() == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def new_request_id() -> str:
    return uuid.uuid4().hex


def get_request_id() -> str:
    return REQUEST_ID.get("")


def set_trace_context(request_id: str, *, sampled: bool = False) -> tuple[contextvars.Token[str], contextvars.Token[bool]]:
    return REQUEST_ID.set(request_id), TRACE_SAMPLE.set(sampled)


def reset_trace_context(tokens: tuple[contextvars.Token[str], contextvars.Token[bool]]) -> None:
    request_token, sample_token = tokens
    REQUEST_ID.reset(request_token)
    TRACE_SAMPLE.reset(sample_token)


@contextlib.contextmanager
def trace_context(request_id: str, *, sampled: bool = False) -> Iterator[None]:
    tokens = set_trace_context(request_id, sampled=sampled)
    try:
        yield
    finally:
        reset_trace_context(tokens)


def should_sample(identifier: str, explicit: bool = False) -> bool:
    if explicit:
        return True
    try:
        rate = float(os.environ.get("OZ_TRACE_SAMPLE_RATE", "0.0"))
    except ValueError:
        rate = 0.0
    if rate <= 0:
        return False
    if rate >= 1:
        return True
    digest = hashlib.sha256(identifier.encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
    return value < rate


def log_extra(**fields: Any) -> dict[str, Any]:
    clean = {key: json_safe(value) for key, value in fields.items() if value is not None}
    request_id = get_request_id()
    if request_id:
        clean.setdefault("request_id", request_id)
    return clean


@contextlib.contextmanager
def observe_duration(metric: str, labels: dict[str, str] | None = None) -> Iterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        observe_histogram(metric, time.perf_counter() - started, labels or {})


def observe_histogram(metric: str, elapsed_seconds: float, labels: dict[str, str] | None = None) -> None:
    client = redis_client()
    if client is None:
        return
    labels = sanitize_labels(labels or {})
    key = histogram_key(metric, labels)
    try:
        pipe = client.pipeline()
        pipe.hincrbyfloat(key, "sum", max(0.0, elapsed_seconds))
        pipe.hincrby(key, "count", 1)
        for bucket in HISTOGRAM_BUCKETS_SECONDS:
            if elapsed_seconds <= bucket:
                pipe.hincrby(key, f"bucket:{bucket}", 1)
        pipe.hincrby(key, "bucket:+Inf", 1)
        pipe.hset(key, "labels", json.dumps(labels, sort_keys=True, separators=(",", ":")))
        pipe.expire(key, int(os.environ.get("OZ_METRIC_TTL_SECONDS", str(7 * 24 * 60 * 60))))
        pipe.execute()
    except Exception:
        logging.getLogger(__name__).debug("histogram metric write failed", exc_info=True)


def histogram_metric_values() -> dict[tuple[str, tuple[tuple[str, str], ...]], float]:
    client = redis_client()
    if client is None:
        return {}
    output: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
    try:
        for key in client.scan_iter("oz:metrics:hist:*"):
            key_text = key.decode("utf-8") if isinstance(key, bytes) else str(key)
            metric = key_text.split(":", 3)[-1].split(":", 1)[0]
            values = client.hgetall(key)
            decoded = {decode(item_key): decode(item_value) for item_key, item_value in values.items()}
            labels = parse_labels(decoded.get("labels"))
            label_items = tuple(sorted(labels.items()))
            count = float(decoded.get("count") or 0)
            total = float(decoded.get("sum") or 0)
            output[(f"{metric}_count", label_items)] = count
            output[(f"{metric}_sum", label_items)] = total
            for bucket in [*HISTOGRAM_BUCKETS_SECONDS, "+Inf"]:
                output[(f"{metric}_bucket", (*label_items, ("le", str(bucket))))] = float(
                    decoded.get(f"bucket:{bucket}") or 0
                )
    except Exception:
        logging.getLogger(__name__).debug("histogram metric read failed", exc_info=True)
    return output


def histogram_key(metric: str, labels: dict[str, str]) -> str:
    safe_metric = safe_label(metric)
    digest = hashlib.sha256(json.dumps(labels, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:24]
    return f"oz:metrics:hist:{safe_metric}:{digest}"


def sanitize_labels(labels: dict[str, str]) -> dict[str, str]:
    return {safe_label(str(key)): safe_label(str(value)) for key, value in labels.items() if key}


def safe_label(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-", "."} else "_" for char in value)[:96] or "unknown"


def parse_labels(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): str(label_value) for key, label_value in parsed.items()}


def decode(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    return str(value)
