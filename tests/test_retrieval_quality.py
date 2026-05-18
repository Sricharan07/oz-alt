from __future__ import annotations

import unittest
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "oz-crawler" / "src"))

from scripts.worker import queue_has_items
from oz_api import admin_ops
from oz_api.intent import classify_query
from oz_api.embedding_jobs import batch_line, selected_embedding_mode, split_batch_rows, embedding_cache_key
from oz_api.queue import queued_crawler_job_event
from oz_api.rerank import boost_named_suggestions, boost_query_matches, parse_rerank_results, strip_private_fields, zeroentropy_scores
from oz_api.trust import github_repo_from_url, github_signal_score, trust_score_for_entry
from oz_crawler.chunks import chunk_markdown, write_chunks
from oz_crawler.content_types import classify_content_type
from oz_crawler.crawl import prepare_pages
from oz_crawler.normalize import NormalizedPage
from oz_crawler.profiles import BASELINE_DENIED_PATHS, LibraryProfile, url_allowed_by_profile
from oz_crawler.token_counting import token_count
from oz_crawler.validation import USEFUL_CONTENT_TYPES, true_junk_rejections


class RetrievalQualityTests(unittest.TestCase):
    def test_intent_classifier_routes_symbol_queries_to_api_reference(self) -> None:
        intent = classify_query("NextRequest cookies API parameters")
        self.assertEqual(intent.content_type, "api_reference")
        self.assertIn("NextRequest", intent.symbols)

    def test_intent_classifier_ignores_pronoun_symbols_for_examples(self) -> None:
        intent = classify_query("how do I read a cookie value")
        self.assertEqual(intent.content_type, "code_example")
        self.assertNotIn("I", intent.symbols)

    def test_content_type_classifier_detects_code_and_config(self) -> None:
        self.assertEqual(
            classify_content_type("https://example.com/docs/example", "```ts\nconst x = 1\n```"),
            "code_example",
        )
        self.assertEqual(
            classify_content_type("https://example.com/docs/config", "```json\n{\"x\": true}\n```"),
            "config",
        )

    def test_chunker_keeps_code_fence_with_snippet_metadata(self) -> None:
        chunks = chunk_markdown("# API\n\nUse it:\n\n```ts\nclient.responses.create({})\n```\n", source_url="https://docs.example/api", page_type="api_reference")
        self.assertTrue(any("```ts" in chunk.text and chunk.content_type == "api_reference" for chunk in chunks))
        self.assertTrue(any(chunk.chunk_key or chunk.parent_key for chunk in chunks))

    def test_chunker_skips_duplicate_parent_for_single_api_child(self) -> None:
        chunks = chunk_markdown(
            "# NextRequest\n\nReads cookies from the incoming request.",
            source_url="https://docs.example/api/next-request",
            page_type="api_reference",
        )

        self.assertEqual(len([chunk for chunk in chunks if chunk.chunk_key]), 0)
        self.assertEqual(len([chunk for chunk in chunks if chunk.parent_key]), 0)

    def test_token_counter_uses_tiktoken_encoding(self) -> None:
        self.assertEqual(token_count("hello world"), 2)

    def test_write_chunks_does_not_embed_inline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            page = NormalizedPage(title="Doc", markdown="# Doc\n\nUse it.", source_url="https://docs.example/doc", path="guides/doc.md")
            write_chunks(target, [page])
            row = next(json.loads(line) for line in (target / "_chunks.jsonl").read_text().splitlines() if line.strip())

        self.assertIn("chunk_sha", row)
        self.assertNotIn("embedding", row)
        self.assertNotIn("embedding_model", row)

    def test_prepare_pages_rejects_duplicate_source_content(self) -> None:
        markdown = "# useEffect\n\n" + "React effect cleanup dependencies example. " * 20
        pages = [
            NormalizedPage(title="useEffect", markdown=markdown, source_url="https://react.dev/reference/react/useEffect"),
            NormalizedPage(title="useEffect copy", markdown=markdown, source_url="https://react.dev/reference/react/useEffect"),
        ]

        accepted, rejected = prepare_pages(pages, profile=None, version="19")

        self.assertEqual(len(accepted), 1)
        self.assertEqual(len(rejected), 1)
        self.assertIn("duplicate content", rejected[0]["reasons"])

    def test_write_chunks_dedupes_exact_chunk_content_across_pages(self) -> None:
        markdown = "# Shared\n\n" + "Use the same setup sequence. " * 25
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "vendor" / "library" / "latest"
            target.mkdir(parents=True)
            write_chunks(
                target,
                [
                    NormalizedPage(title="One", markdown=markdown, source_url="https://docs.example/one", path="guides/one.md"),
                    NormalizedPage(title="Two", markdown=markdown, source_url="https://docs.example/two", path="guides/two.md"),
                ],
            )
            rows = [json.loads(line) for line in (target / "_chunks.jsonl").read_text().splitlines() if line.strip()]

        self.assertEqual(len(rows), 1)

    def test_validation_junk_ratio_excludes_policy_dedup_rejections(self) -> None:
        rows = [
            {"content_type": "duplicate", "reasons": ["duplicate content", "canonical source: https://docs.example/a"]},
            {"content_type": "junk", "reasons": ["marketing/login language"]},
        ]

        self.assertEqual(len(true_junk_rejections(rows)), 1)

    def test_validation_treats_all_retrieval_content_types_as_useful(self) -> None:
        self.assertIn("config", USEFUL_CONTENT_TYPES)
        self.assertIn("cli", USEFUL_CONTENT_TYPES)
        self.assertIn("error_ref", USEFUL_CONTENT_TYPES)

    def test_embedding_cache_key_includes_schema_and_input_type(self) -> None:
        with patch.dict("os.environ", {"OZ_EMBEDDING_CACHE_SCHEMA_VERSION": "v1"}, clear=False):
            first = embedding_cache_key("abc")
        with patch.dict("os.environ", {"OZ_EMBEDDING_CACHE_SCHEMA_VERSION": "v2"}, clear=False):
            second = embedding_cache_key("abc")

        self.assertNotEqual(first, second)

    def test_embedding_mode_auto_uses_batch_only_for_large_voyage_jobs(self) -> None:
        with patch.dict(
            "os.environ",
            {"OZ_EMBEDDING_PROVIDER": "voyage", "OZ_EMBEDDING_INDEX_MODE": "auto", "OZ_EMBEDDING_SYNC_THRESHOLD": "500"},
            clear=False,
        ):
            self.assertEqual(selected_embedding_mode(499, force_sync=False), "sync")
            self.assertEqual(selected_embedding_mode(500, force_sync=False), "batch")
            self.assertEqual(selected_embedding_mode(500, force_sync=True), "sync")

    def test_voyage_batch_rows_split_by_input_limit_and_use_chunk_sha_custom_ids(self) -> None:
        rows = [{"chunk_sha": f"sha-{index}", "content": f"content {index}"} for index in range(3)]
        with patch.dict("os.environ", {"OZ_VOYAGE_BATCH_MAX_INPUTS": "2", "OZ_VOYAGE_BATCH_MAX_BYTES": "1000000"}, clear=False):
            batches = split_batch_rows(rows)

        self.assertEqual([len(batch) for batch in batches], [2, 1])
        self.assertEqual(batch_line(rows[0])["custom_id"], "sha-0")
        self.assertEqual(batch_line(rows[0])["body"]["input"], ["content 0"])

    def test_worker_detects_pending_queue_before_idle_batch_poll(self) -> None:
        class FakeRedis:
            def __init__(self, depth: int) -> None:
                self.depth = depth

            def llen(self, _queue: str) -> int:
                return self.depth

        self.assertTrue(queue_has_items(FakeRedis(2), "oz:crawler:jobs"))
        self.assertFalse(queue_has_items(FakeRedis(0), "oz:crawler:jobs"))

    def test_requeued_crawler_job_preserves_db_id_and_profile(self) -> None:
        event = queued_crawler_job_event(
            {
                "id": 49,
                "vendor": "django",
                "library_name": "django",
                "source_url": "https://docs.djangoproject.com/en/stable/",
                "version": "latest",
                "max_pages": 256,
                "allowed_hosts": ["docs.djangoproject.com"],
                "allowed_paths": ["/en/stable/"],
                "denied_paths": ["/deprecated/"],
            }
        )

        self.assertEqual(event["db_job_id"], "49")
        self.assertEqual(event["profile"]["allowed_hosts"], ["docs.djangoproject.com"])
        self.assertEqual(event["profile"]["allowed_paths"], ["/en/stable/"])

    def test_catalog_promotion_does_not_record_empty_quality_failure(self) -> None:
        class FakeStore:
            def execute(self, *_args, **_kwargs) -> list[dict[str, object]]:
                return []

        entry = {
            "vendor": "vercel",
            "library": "next.js",
            "version": "15",
            "ref_sha": "abc",
            "pack_path": "packs/next.ozpack",
            "source_urls": ["https://nextjs.org/docs"],
        }
        job = {"db_job_id": "34"}
        with patch.object(admin_ops.AuthStore, "from_env", return_value=FakeStore()), patch.object(
            admin_ops, "record_pack_build"
        ), patch.object(admin_ops, "record_quality_run") as record_quality:
            admin_ops.record_catalog_promotion(entry, job, {})
            record_quality.assert_not_called()
            admin_ops.record_catalog_promotion(entry, job, {"passed": True})
            record_quality.assert_called_once()

    def test_baseline_profile_excludes_legacy_noise(self) -> None:
        profile = LibraryProfile(vendor="v", library="l", allowed_hosts=["docs.example.com"], allowed_paths=["/docs"])
        self.assertIn("deprecated", BASELINE_DENIED_PATHS)
        self.assertFalse(url_allowed_by_profile("https://docs.example.com/docs/legacy/v1/page", profile))

    def test_rerank_strips_private_fields_and_boosts_named_suggestions(self) -> None:
        rows = [{"vendor": "vercel", "library": "next.js", "version": "15", "score": 1, "_rerank_text": "secret"}]
        boosted = boost_named_suggestions("next.js", rows)
        self.assertGreater(boosted[0]["score"], 1)
        self.assertNotIn("_rerank_text", strip_private_fields(boosted)[0])

    def test_query_match_boost_keeps_exact_symbols_competitive_after_rerank(self) -> None:
        rows = [
            {
                "path": ".codo/vendors/vercel/next.js@15/guides/authentication.md",
                "matched_path": "guides/authentication.md",
                "symbols": [],
                "content_type": "guide",
                "score": 100,
            },
            {
                "path": ".codo/vendors/vercel/next.js@15/_symbols/NextRequest.md",
                "matched_path": "_symbols/NextRequest.md",
                "symbols": ["NextRequest"],
                "content_type": "api_reference",
                "score": 80,
            },
        ]

        boosted = boost_query_matches("NextRequest middleware cookies", rows)

        self.assertEqual(boosted[0]["path"], ".codo/vendors/vercel/next.js@15/_symbols/NextRequest.md")

    def test_zeroentropy_rerank_payload_uses_zerank_2(self) -> None:
        captured: dict[str, object] = {}

        def fake_request(url: str, payload: dict[str, object], headers: dict[str, str]):
            captured["url"] = url
            captured["payload"] = payload
            captured["headers"] = headers
            return [(1, 0.9)]

        with patch("oz_api.rerank.request_scores", fake_request), patch.dict(
            "os.environ",
            {"OZ_RERANK_MODEL": "zerank-2", "OZ_ZEROENTROPY_LATENCY": "fast"},
            clear=False,
        ):
            scores = zeroentropy_scores("ze-key", "query", ["doc a", "doc b"])

        self.assertEqual(scores, [(1, 0.9)])
        self.assertEqual(captured["url"], "https://api.zeroentropy.dev/v1/models/rerank")
        self.assertEqual(captured["payload"]["model"], "zerank-2")  # type: ignore[index]
        self.assertEqual(captured["payload"]["latency"], "fast")  # type: ignore[index]
        self.assertEqual(captured["headers"]["Authorization"], "Bearer ze-key")  # type: ignore[index]

    def test_rerank_response_parser_accepts_official_and_compatible_scores(self) -> None:
        self.assertEqual(
            parse_rerank_results(
                [
                    {"index": 2, "relevance_score": 0.7},
                    {"index": "1", "score": "0.6"},
                    {"index": 0, "rerank_score": 0.5},
                    {"index": True, "relevance_score": 0.1},
                ]
            ),
            [(2, 0.7), (1, 0.6), (0, 0.5)],
        )

    def test_trust_score_parses_github_and_uses_repo_signals(self) -> None:
        self.assertEqual(github_repo_from_url("https://github.com/vercel/next.js/tree/canary/docs"), ("vercel", "next.js"))
        score, signals = trust_score_for_entry(
            {
                "vendor": "vercel",
                "library": "next.js",
                "source_urls": ["https://github.com/vercel/next.js"],
                "keywords": ["next", "react", "docs"],
                "pack_path": "registry/packs/vercel/next.js/15.ozpack",
            }
        )
        self.assertGreater(score, 0.45)
        self.assertTrue(signals["official_source_signal"])

    def test_github_signal_score_rewards_popular_active_repos(self) -> None:
        score = github_signal_score(
            {
                "network_fetch": "ok",
                "stars": 120000,
                "forks": 26000,
                "license": True,
                "created_at": "2016-01-01T00:00:00Z",
                "pushed_at": "2026-05-01T00:00:00Z",
                "archived": False,
                "disabled": False,
            }
        )

        self.assertGreater(score, 0.35)


if __name__ == "__main__":
    unittest.main()
