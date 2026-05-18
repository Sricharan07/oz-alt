from __future__ import annotations

import json
import logging
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.metrics import render_prometheus_metrics  # noqa: E402
from oz_api.observability import (  # noqa: E402
    JsonLogFormatter,
    histogram_metric_values,
    observe_histogram,
    should_sample,
    trace_context,
)


class ObservabilityTests(unittest.TestCase):
    def test_json_logs_include_request_id_and_structured_fields(self) -> None:
        formatter = JsonLogFormatter()
        record = logging.LogRecord("test", logging.INFO, __file__, 10, "hello %s", ("world",), None)
        record.library = "vercel/next.js"  # type: ignore[attr-defined]

        with trace_context("req-123", sampled=True):
            payload = json.loads(formatter.format(record))

        self.assertEqual(payload["request_id"], "req-123")
        self.assertTrue(payload["sampled"])
        self.assertEqual(payload["library"], "vercel/next.js")
        self.assertEqual(payload["message"], "hello world")

    def test_trace_sampling_is_deterministic_and_respects_explicit_flag(self) -> None:
        self.assertTrue(should_sample("anything", explicit=True))
        with patch.dict(os.environ, {"OZ_TRACE_SAMPLE_RATE": "0"}, clear=False):
            self.assertFalse(should_sample("abc"))
        with patch.dict(os.environ, {"OZ_TRACE_SAMPLE_RATE": "1"}, clear=False):
            self.assertTrue(should_sample("abc"))
            self.assertTrue(should_sample("abc"))

    def test_histograms_are_exported_with_prometheus_histogram_type(self) -> None:
        fake = FakeRedis()
        with patch("oz_api.observability.redis_client", return_value=fake), patch(
            "oz_api.metrics.redis_client", return_value=None
        ), patch("oz_api.metrics.AuthStore.from_env", return_value=None):
            observe_histogram("oz_test_duration_seconds", 0.12, {"route": "search"})
            values = histogram_metric_values()
            rendered = render_prometheus_metrics()

        labels = (("route", "search"),)
        self.assertEqual(values[("oz_test_duration_seconds_count", labels)], 1.0)
        self.assertIn("# TYPE oz_test_duration_seconds histogram", rendered)
        self.assertIn('oz_test_duration_seconds_bucket{le="0.25",route="search"} 1', rendered)


class FakeRedis:
    def __init__(self) -> None:
        self.hashes: dict[str, dict[str, str]] = {}

    def pipeline(self) -> "FakePipeline":
        return FakePipeline(self)

    def hgetall(self, key: str) -> dict[str, str]:
        return dict(self.hashes.get(key, {}))

    def scan_iter(self, pattern: str):
        prefix = pattern.rstrip("*")
        for key in sorted(self.hashes):
            if key.startswith(prefix):
                yield key


class FakePipeline:
    def __init__(self, redis: FakeRedis) -> None:
        self.redis = redis

    def _hash(self, key: str) -> dict[str, str]:
        return self.redis.hashes.setdefault(key, {})

    def hincrbyfloat(self, key: str, field: str, amount: float) -> None:
        data = self._hash(key)
        data[field] = str(float(data.get(field, "0")) + amount)

    def hincrby(self, key: str, field: str, amount: int) -> None:
        data = self._hash(key)
        data[field] = str(int(float(data.get(field, "0"))) + amount)

    def hset(self, key: str, field: str, value: str) -> None:
        self._hash(key)[field] = value

    def expire(self, _key: str, _seconds: int) -> None:
        return None

    def execute(self) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
