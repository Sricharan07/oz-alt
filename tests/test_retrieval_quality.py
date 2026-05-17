from __future__ import annotations

import unittest
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "oz-crawler" / "src"))

from oz_api.intent import classify_query
from oz_api.rerank import boost_named_suggestions, boost_query_matches, parse_rerank_results, strip_private_fields, zeroentropy_scores
from oz_api.trust import github_repo_from_url, github_signal_score, trust_score_for_entry
from oz_crawler.chunks import chunk_markdown
from oz_crawler.content_types import classify_content_type
from oz_crawler.profiles import BASELINE_DENIED_PATHS, LibraryProfile, url_allowed_by_profile
from oz_crawler.token_counting import token_count


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
