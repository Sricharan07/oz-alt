from __future__ import annotations
# ruff: noqa: E402

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
from oz_api.crawler_jobs import (
    content_requirement_hit,
    embedding_result_is_terminal,
    pack_eval_report,
    path_junk_hit,
    search_eval_report,
    terminal_embedding_error,
)
from oz_api.intent import classify_query, plan_query
from oz_api.embedding_jobs import EmbeddingEnsureResult, batch_line, selected_embedding_mode, split_batch_rows, embedding_cache_key
from oz_api.indexer import chunk_rows, enrich_chunk_row, limit_to_token_budget
from oz_api.llm_recipes import grounded_generation, high_risk_api_tokens
from oz_api.ranking import local_chunk_score, planned_chunk_score
from oz_api.queue import queued_crawler_job_event
from oz_api.retrieval import code_blocks_satisfying_context_terms, context_packet, context_required_terms, context_source_text, leaf_code_blocks
from oz_api.rerank import (
    boost_named_suggestions,
    boost_query_matches,
    parse_rerank_results,
    rerank_cache_key,
    strip_private_fields,
    zeroentropy_scores,
)
from oz_api.trust import github_repo_from_url, github_signal_score, trust_score_for_entry
from oz_api.storage import RegistryStorage
from oz_api.versions import latest_entry, parse_versioned_scope, resolve_catalog_entry
from oz_crawler.chunks import chunk_markdown, content_hash, write_chunks
from oz_crawler.content_types import block_content_type, classify_content_type
from oz_crawler.crawl import is_crawlable_doc_url, prepare_pages
from oz_crawler.crawl_runtime import CrawlRunState
from oz_crawler.embeddings import embedding_batches
from oz_crawler.language import language_allowed
from oz_crawler.normalize import NormalizedPage
from oz_crawler.normalize import clean_markdown
from oz_crawler.parsers.source_code import extracted_documented_blocks, source_path_allowed
from oz_crawler.profiles import BASELINE_DENIED_PATHS, LibraryProfile, url_allowed_by_profile
from oz_crawler.pack import build_pack_bytes
from oz_crawler.splitting import document_path, split_llms_full
from oz_crawler.sources import artifact_markdown, extract_urls, prioritized_urls
from oz_crawler.token_counting import token_count
from oz_crawler.validation import USEFUL_CONTENT_TYPES, has_frontmatter, true_junk_rejections, validate_fixture


class RetrievalQualityTests(unittest.TestCase):
    def test_version_resolution_uses_semver_not_string_sort(self) -> None:
        entries = [{"version": version} for version in ["v9.0.0", "v10.0.0", "v11.0.0", "v2.0.0", "v15.1.8"]]

        self.assertEqual(latest_entry(entries)["version"], "v15.1.8")
        self.assertEqual(resolve_catalog_entry(entries, "15")["version"], "v15.1.8")

    def test_versioned_scope_accepts_at_and_path_forms(self) -> None:
        at_scope = parse_versioned_scope("vercel/next.js@15.1.8")
        path_scope = parse_versioned_scope("/vercel/next.js/v15.1.8")

        self.assertEqual((at_scope.vendor, at_scope.library, at_scope.version), ("vercel", "next.js", "15.1.8"))
        self.assertEqual((path_scope.vendor, path_scope.library, path_scope.version), ("vercel", "next.js", "v15.1.8"))

    def test_intent_classifier_routes_symbol_queries_to_api_reference(self) -> None:
        intent = classify_query("NextRequest cookies API parameters")
        self.assertEqual(intent.content_type, "api_reference")
        self.assertIn("NextRequest", intent.symbols)

    def test_intent_classifier_ignores_pronoun_symbols_for_examples(self) -> None:
        intent = classify_query("how do I read a cookie value")
        self.assertEqual(intent.content_type, "code_example")
        self.assertNotIn("I", intent.symbols)

    def test_intent_classifier_detects_lower_camel_api_symbols(self) -> None:
        intent = classify_query("useState set state updater function")
        self.assertEqual(intent.content_type, "api_reference")
        self.assertIn("useState", intent.symbols)

    def test_query_plan_does_not_treat_client_as_cli_or_json_as_config(self) -> None:
        client = plan_query("How do I navigate on the client and read search params with useRouter?")
        route = plan_query("How does a route handler read a POST body and return JSON?")

        self.assertNotEqual(client.content_type, "cli")
        self.assertIn("useRouter", client.symbols)
        self.assertNotEqual(route.content_type, "config")
        self.assertIn("route handler", route.phrases)

    def test_query_plan_removes_stopwords_but_keeps_phrases_and_symbols(self) -> None:
        plan = plan_query("How do fetch cache options, revalidate, and cache tags work in Next.js?")

        self.assertNotIn("how", plan.important_terms)
        self.assertNotIn("next", plan.important_terms)
        self.assertIn("cache tags", plan.phrases)
        self.assertIn("cache-tags", plan.slugs)

    def test_query_plan_turns_single_entities_into_exact_path_slugs(self) -> None:
        plan = plan_query("When should I use redirect, notFound, unauthorized, and forbidden in Next.js?")

        self.assertIn("redirect", plan.slugs)
        self.assertIn("notfound", plan.slugs)
        self.assertIn("unauthorized", plan.slugs)
        self.assertIn("forbidden", plan.slugs)

    def test_local_eval_ranking_prefers_exact_api_reference_over_examples(self) -> None:
        terms = ["useeffect", "cleanup", "dependency", "array"]
        api_row = {
            "path": "api-reference/react/useeffect.md",
            "text": "useEffect cleanup dependency array",
            "content_type": "api_reference",
            "symbols": ["useEffect"],
        }
        example_row = {
            "path": "examples/react/useeffect.md",
            "text": "useEffect cleanup dependency array " * 5,
            "content_type": "code_example",
            "symbols": ["useEffect"],
        }

        self.assertGreater(local_chunk_score(api_row, terms), local_chunk_score(example_row, terms))


    def test_llm_recipe_grounding_allows_prose_but_rejects_invented_api(self) -> None:
        evidence = [
            {
                "content": "Use the Python SDK with Client. Call client.create_knowledge_base(name=\"Docs\") after setting SMALLEST_API_KEY."
            }
        ]
        grounded = {
            "content": "Create a knowledge base with the Python SDK.",
            "code": "```python\nclient.create_knowledge_base(name=\"Docs\")\n```",
            "info": "Requires SMALLEST_API_KEY.",
        }
        invented = {
            "content": "Create a knowledge base with the Python SDK.",
            "code": "```python\nclient.magic_create_index(project_id=\"x\")\n```",
            "info": "Requires SMALLEST_API_KEY.",
        }

        self.assertTrue(grounded_generation(grounded, evidence))
        self.assertFalse(grounded_generation(invented, evidence))
        self.assertNotIn("Python", high_risk_api_tokens(grounded["content"]))

    def test_planned_ranking_demotes_cli_for_non_cli_query(self) -> None:
        query = "How does a Next.js App Router route handler read a POST body and return JSON?"
        route_row = {
            "path": "api-reference/app/api-reference/file-conventions/route.md",
            "text": "Route Handlers allow you to create custom request handlers for a given route using the Web Request and Response APIs. export async function POST(request: Request) { return Response.json({ ok: true }) }",
            "content_type": "api_reference",
            "heading_path": ["Route Handlers"],
            "symbols": [],
        }
        cli_row = {
            "path": "api-reference/app/api-reference/cli/next.md",
            "text": "The Next.js CLI has commands and options for route handlers, JSON output, build, dev, and POST examples.",
            "content_type": "cli",
            "heading_path": ["Next CLI"],
            "symbols": [],
        }

        self.assertGreater(planned_chunk_score(route_row, query), planned_chunk_score(cli_row, query))

    def test_planned_ranking_prefers_canonical_docs_over_symbol_page_for_config_query(self) -> None:
        query = "How do I configure next/image remotePatterns for external image domains?"
        docs_row = {
            "path": "api-reference/app/api-reference/components/image.md",
            "text": "Configure next/image remotePatterns in next.config.js for external image domains.",
            "content_type": "api_reference",
            "heading_path": ["Image", "remotePatterns"],
            "symbols": ["remotePatterns"],
        }
        symbol_row = {
            "path": "_symbols/remotePatterns.md",
            "text": "remotePatterns config option.",
            "content_type": "api_reference",
            "heading_path": ["remotePatterns"],
            "symbols": ["remotePatterns"],
        }

        self.assertGreater(planned_chunk_score(docs_row, query), planned_chunk_score(symbol_row, query))

    def test_planned_ranking_prefers_app_router_docs_over_pages_by_default(self) -> None:
        query = "How do I navigate on the client and read search params with useRouter and useSearchParams?"
        app_row = {
            "path": "api-reference/app/api-reference/functions/use-search-params.md",
            "text": "useSearchParams is a Client Component hook in the App Router.",
            "content_type": "api_reference",
            "heading_path": ["useSearchParams"],
            "symbols": ["useSearchParams"],
        }
        pages_row = {
            "path": "api-reference/pages/api-reference/functions/use-search-params.md",
            "text": "useSearchParams can be used in a Pages Router client component.",
            "content_type": "api_reference",
            "heading_path": ["useSearchParams"],
            "symbols": ["useSearchParams"],
        }

        self.assertGreater(planned_chunk_score(app_row, query), planned_chunk_score(pages_row, query))

    def test_planned_ranking_penalizes_upgrade_pages_when_query_is_not_upgrade(self) -> None:
        query = "How do I implement authentication in Next.js middleware using cookies and NextRequest?"
        docs_row = {
            "path": "guides/app/guides/authentication.md",
            "text": "Authentication can use Proxy, cookies, and NextRequest.",
            "content_type": "prose",
            "heading_path": ["Authentication"],
            "symbols": ["NextRequest"],
        }
        upgrade_row = {
            "path": "guides/messages/middleware-upgrade-guide.md",
            "text": "Middleware upgrade guide mentions cookies and NextRequest.",
            "content_type": "prose",
            "heading_path": ["Middleware upgrade guide"],
            "symbols": ["NextRequest"],
        }

        self.assertGreater(planned_chunk_score(docs_row, query), planned_chunk_score(upgrade_row, query))

    def test_planned_ranking_prefers_server_action_workflow_over_narrow_cache_reference(self) -> None:
        query = "How do Server Actions mutate data and revalidate a path or cache tag?"
        guide_row = {
            "path": "guides/app/getting-started/mutating-data.md",
            "text": "Server Actions mutate data and can revalidatePath or revalidateTag after a mutation.",
            "content_type": "prose",
            "heading_path": ["Mutating data", "Server Actions"],
            "symbols": ["revalidatePath", "revalidateTag"],
        }
        reference_row = {
            "path": "api-reference/app/api-reference/functions/cachetag.md",
            "text": "cacheTag marks cached data with tags for later revalidation.",
            "content_type": "api_reference",
            "heading_path": ["cacheTag"],
            "symbols": ["cacheTag"],
        }

        self.assertGreater(planned_chunk_score(guide_row, query), planned_chunk_score(reference_row, query))

    def test_content_type_classifier_detects_code_and_config(self) -> None:
        self.assertEqual(
            classify_content_type("https://example.com/docs/example", "```ts\nconst x = 1\n```"),
            "code_example",
        )
        self.assertEqual(
            classify_content_type("https://example.com/docs/config", "```json\n{\"x\": true}\n```"),
            "config",
        )
        self.assertEqual(
            block_content_type("https://example.com/api-reference/widget", "```ts\nclient.create()\n```", "api_reference"),
            "code_example",
        )
        self.assertEqual(
            block_content_type("https://example.com/docs", "Setup: instructions\nNote: continue\nTip: read this", "prose"),
            "prose",
        )
        self.assertEqual(
            block_content_type("https://example.com/docs", "JSON API URL fix solution", "prose"),
            "prose",
        )
        self.assertEqual(
            block_content_type(
                "https://nextjs.org/docs/app/building-your-application/routing/middleware",
                "import { NextResponse } from 'next/server'\nexport function proxy(request) { return NextResponse.next() }",
                "prose",
            ),
            "code_example",
        )
        self.assertEqual(
            block_content_type(
                "https://nextjs.org/docs/pages/api-reference/functions/next-response",
                "NextResponse extends the Web Response API. The URL can be used for redirects.",
                "api_reference",
            ),
            "api_reference",
        )
        self.assertEqual(
            classify_content_type("https://nextjs.org/docs/app/api-reference/config/next-config-js/redirects", "Redirects config"),
            "config",
        )

    def test_chunker_keeps_code_fence_with_snippet_metadata(self) -> None:
        chunks = chunk_markdown("# API\n\nUse it:\n\n```ts\nclient.responses.create({})\n```\n", source_url="https://docs.example/api", page_type="api_reference")
        self.assertTrue(any("```ts" in chunk.text and chunk.content_type == "code_example" for chunk in chunks))
        self.assertEqual(len([chunk for chunk in chunks if "client.responses.create" in chunk.text]), 1)

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

    def test_indexer_caps_generated_parent_content_by_real_token_count(self) -> None:
        text = "\n".join(f"line {index} `someSymbolCall({index})` with explanation" for index in range(1000))
        capped = limit_to_token_budget(text, 1200)

        self.assertLessEqual(token_count(capped), 1200)
        self.assertIn("line 0", capped)

    def test_embedding_sync_batches_respect_token_budget(self) -> None:
        rows = [(index, "token " * 400) for index in range(10)]
        with patch.dict("os.environ", {"OZ_EMBEDDING_BATCH_SIZE": "128", "OZ_EMBEDDING_SYNC_MAX_TOKENS_PER_REQUEST": "1000"}):
            batches = embedding_batches(rows)

        self.assertGreater(len(batches), 1)
        for batch in batches:
            self.assertLessEqual(sum(token_count(text) for _, text in batch), 1000)

    def test_terminal_embedding_statuses_block_promotion(self) -> None:
        failed = EmbeddingEnsureResult(
            status="failed",
            mode="sync",
            job_id=10,
            version_id=20,
            total_chunks=100,
            pending_chunks=5,
            cached_chunks=0,
            embedded_chunks=95,
            failed_chunks=5,
        )
        waiting = EmbeddingEnsureResult(
            status="batch_running",
            mode="batch",
            job_id=11,
            version_id=21,
            total_chunks=100,
            pending_chunks=100,
            cached_chunks=0,
            embedded_chunks=0,
        )

        self.assertTrue(embedding_result_is_terminal(failed))
        self.assertFalse(embedding_result_is_terminal(waiting))
        self.assertEqual(terminal_embedding_error({"embedding_status": "failed", "embedding_error": "128 chunks failed"}), "128 chunks failed")

    def test_markdown_cleanup_strips_frontmatter(self) -> None:
        markdown = clean_markdown("---\ntitle: Middleware\n---\n# Middleware\n\nUse cookies.")

        self.assertNotIn("title: Middleware", markdown)
        self.assertTrue(markdown.startswith("# Middleware"))

    def test_context_strips_source_index_boilerplate(self) -> None:
        text = (
            "> For an index of all Next.js documentation, see [/docs/pages/llms.txt](/docs/pages/llms.txt).\n"
            "NextResponse extends the Web Response API."
        )
        row = {"_matched_text": text, "content_type": "api_reference", "symbols": ["NextResponse"]}

        self.assertEqual(context_source_text(row), "NextResponse extends the Web Response API.")

    def test_context_does_not_emit_code_blocks_that_miss_required_terms(self) -> None:
        rows = [
            {
                "score": 100,
                "retrieval_mode": "code_example",
                "title": "Webhook",
                "matched_path": "guides/webhooks.md",
                "source_anchor": "https://docs.example/webhooks",
                "_matched_text": "Webhook setup\n\n```python\nclient.background.run()\n```",
                "snippet": "Webhook setup\n\n```python\nclient.background.run()\n```",
            },
            {
                "score": 90,
                "retrieval_mode": "agent_recipe",
                "title": "Managing Webhooks",
                "matched_path": "guides/webhooks.md",
                "source_anchor": "https://docs.example/webhooks#manage",
                "_matched_text": "Create and manage webhooks from the dashboard. Add the endpoint URL, choose events, save the webhook, and then attach it to the agent settings before testing delivery.",
                "snippet": "Create and manage webhooks from the dashboard. Add the endpoint URL, choose events, save the webhook, and then attach it to the agent settings before testing delivery.",
            },
        ]

        packet = context_packet(rows, query="create a webhook tool", max_tokens=800, max_results=4)

        self.assertEqual(packet["codeSnippets"], [])
        self.assertTrue(packet["infoSnippets"])
        self.assertIn("webhook", packet["infoSnippets"][0]["content"].lower())

    def test_required_terms_filter_individual_code_blocks(self) -> None:
        blocks = [
            {"language": "python", "code": "client.background.run()"},
            {"language": "python", "code": "client.webhooks.create(url='https://example.com/hook')"},
        ]

        filtered = code_blocks_satisfying_context_terms(blocks, {"webhook"})

        self.assertEqual(filtered, [blocks[1]])

    def test_context_flattens_markdown_wrapper_code_blocks_before_filtering(self) -> None:
        blocks = [
            {
                "language": "markdown",
                "code": (
                    "Webhook use case prose.\n\n"
                    "```python\n"
                    "client.background.run()\n"
                    "```\n"
                ),
            }
        ]

        self.assertEqual(leaf_code_blocks(blocks), [{"language": "python", "code": "client.background.run()"}])
        self.assertEqual(code_blocks_satisfying_context_terms(blocks, {"webhook"}), [])

    def test_context_recovers_partial_fence_and_drops_prose_wrapper(self) -> None:
        rows = [
            {
                "score": 100,
                "retrieval_mode": "code_example",
                "title": "Accessing Request Object",
                "matched_path": "guides/app-router.md",
                "source_anchor": "https://docs.example/app-router#request",
                "_matched_text": (
                    "The `app` directory exposes new read-only functions to retrieve request data:\n\n"
                    "* [`cookies`](/docs/app/api-reference/functions/cookies): read cookies.\n\n"
                    "```tsx filename=\"app/page.tsx\" switcher\n"
                    "import { cookies } from 'next/headers'\n\n"
                    "export default async function Page() {\n"
                    "  const theme = (await cookies()).get('theme')\n"
                    "  return '...'\n"
                    "}"
                ),
                "snippet": (
                    "The `app` directory exposes new read-only functions to retrieve request data:\n\n"
                    "* [`cookies`](/docs/app/api-reference/functions/cookies): read cookies.\n\n"
                    "```tsx filename=\"app/page.tsx\" switcher\n"
                    "import { cookies } from 'next/headers'\n\n"
                    "export default async function Page() {\n"
                    "  const theme = (await cookies()).get('theme')\n"
                    "  return '...'\n"
                    "}"
                ),
            }
        ]

        packet = context_packet(rows, query="read cookies in a Next.js server component", max_tokens=900, max_results=3)

        self.assertEqual(len(packet["codeSnippets"]), 1)
        code = packet["codeSnippets"][0]["codeList"][0]["code"]
        self.assertTrue(code.startswith("import { cookies }"))
        self.assertNotIn("The `app` directory", code)
        self.assertNotIn("```", code)

    def test_context_extracts_unfenced_operation_code(self) -> None:
        rows = [
            {
                "score": 110,
                "retrieval_mode": "code_example",
                "title": "Deploy an agent",
                "matched_path": "guides/deploy-agent.md",
                "source_anchor": "https://docs.example/deploy-agent",
                "_matched_text": (
                    "```bash\n"
                    "$ smallestai agent-crew deploy --agent-id agent_123\n"
                    "✓ Package created\n"
                    "```\n"
                ),
                "snippet": (
                    "```bash\n"
                    "$ smallestai agent-crew deploy --agent-id agent_123\n"
                    "✓ Package created\n"
                    "```\n"
                ),
            },
            {
                "score": 100,
                "retrieval_mode": "source_section",
                "title": "Create agent",
                "matched_path": "guides/create-agent.md",
                "source_anchor": "https://docs.example/create-agent",
                "_matched_text": (
                    "# not SMALLEST_API_KEY.\n"
                    "client = SmallestAI(token=os.getenv(\"SMALLEST_API_KEY\"))\n"
                    "response = client.atoms.agents.create_a_new_agent(name=\"my-test-agent\")\n"
                    "agent_id = response.data\n"
                    "print(agent_id)\n\n"
                    "Prompts for your API key and writes credentials."
                ),
                "snippet": (
                    "# not SMALLEST_API_KEY.\n"
                    "client = SmallestAI(token=os.getenv(\"SMALLEST_API_KEY\"))\n"
                    "response = client.atoms.agents.create_a_new_agent(name=\"my-test-agent\")\n"
                    "agent_id = response.data\n"
                    "print(agent_id)\n\n"
                    "Prompts for your API key and writes credentials."
                ),
            },
            {
                "score": 90,
                "retrieval_mode": "code_example",
                "title": "Connect to existing agent",
                "matched_path": "guides/connect-agent.md",
                "source_anchor": "https://docs.example/connect-agent",
                "_matched_text": "```typescript\nconst agent = new AtomsAgent({ apiKey: 'sk_...', agentId: 'agent_123' })\nawait agent.connect()\n```",
                "snippet": "```typescript\nconst agent = new AtomsAgent({ apiKey: 'sk_...', agentId: 'agent_123' })\nawait agent.connect()\n```",
            },
            {
                "score": 88,
                "retrieval_mode": "code_example",
                "title": "Using Groq",
                "matched_path": "guides/groq.md",
                "source_anchor": "https://docs.example/groq",
                "_matched_text": (
                    "```python\n"
                    "from smallestai.atoms.models import CreateAgentRequest\n"
                    "agent = CreateAgentRequest(name=\"SupportAgent\", synthesizer={})\n"
                    "```\n"
                ),
                "snippet": (
                    "```python\n"
                    "from smallestai.atoms.models import CreateAgentRequest\n"
                    "agent = CreateAgentRequest(name=\"SupportAgent\", synthesizer={})\n"
                    "```\n"
                ),
            },
            {
                "score": 80,
                "retrieval_mode": "code_example",
                "title": "Headers only",
                "matched_path": "guides/headers.md",
                "source_anchor": "https://docs.example/headers",
                "_matched_text": "```python\nAPI_KEY = os.environ[\"SMALLEST_API_KEY\"]\nHEADERS = {\"Authorization\": f\"Bearer {API_KEY}\"}\n```",
                "snippet": "```python\nAPI_KEY = os.environ[\"SMALLEST_API_KEY\"]\nHEADERS = {\"Authorization\": f\"Bearer {API_KEY}\"}\n```",
            },
        ]

        packet = context_packet(rows, query="create a new Atoms agent with API key in Python", max_tokens=900, max_results=4)

        self.assertTrue(packet["codeSnippets"])
        code = packet["codeSnippets"][0]["codeList"][0]["code"]
        self.assertIn("create_a_new_agent", code)
        self.assertNotIn("agent-crew deploy", code)
        self.assertNotIn("Package created", code)
        self.assertNotIn("CreateAgentRequest", "\n".join(item["code"] for card in packet["codeSnippets"] for item in card["codeList"]))
        self.assertNotEqual(code.strip(), "API_KEY = os.environ[\"SMALLEST_API_KEY\"]")

    def test_context_honors_requested_code_language(self) -> None:
        rows = [
            {
                "score": 100,
                "retrieval_mode": "code_example",
                "title": "TypeScript streaming",
                "matched_path": "guides/stream-ts.md",
                "source_anchor": "https://docs.example/stream-ts",
                "_matched_text": (
                    "```typescript\n"
                    "import WebSocket from \"ws\"\n"
                    "const ws = new WebSocket(\"wss://api.example/stream\")\n"
                    "ws.on(\"open\", () => ws.send(JSON.stringify({ text: \"Hello\" })))\n"
                    "```\n"
                ),
                "snippet": (
                    "```typescript\n"
                    "import WebSocket from \"ws\"\n"
                    "const ws = new WebSocket(\"wss://api.example/stream\")\n"
                    "ws.on(\"open\", () => ws.send(JSON.stringify({ text: \"Hello\" })))\n"
                    "```\n"
                ),
            },
            {
                "score": 90,
                "retrieval_mode": "code_example",
                "title": "Python streaming",
                "matched_path": "guides/stream-python.md",
                "source_anchor": "https://docs.example/stream-python",
                "_matched_text": (
                    "```python\n"
                    "from smallestai.waves import WavesStreamingTTS, TTSConfig\n"
                    "config = TTSConfig(api_key=\"SMALLEST_API_KEY\")\n"
                    "tts = WavesStreamingTTS(config)\n"
                    "tts.stream(text=\"Hello\")\n"
                    "```\n"
                ),
                "snippet": (
                    "```python\n"
                    "from smallestai.waves import WavesStreamingTTS, TTSConfig\n"
                    "config = TTSConfig(api_key=\"SMALLEST_API_KEY\")\n"
                    "tts = WavesStreamingTTS(config)\n"
                    "tts.stream(text=\"Hello\")\n"
                    "```\n"
                ),
            },
        ]

        packet = context_packet(rows, query="stream text to speech in Python", max_tokens=900, max_results=4)

        self.assertTrue(packet["codeSnippets"])
        joined = "\n".join(item["code"] for card in packet["codeSnippets"] for item in card["codeList"])
        self.assertIn("WavesStreamingTTS", joined)
        self.assertNotIn("WebSocket", joined)

    def test_context_recipe_cards_do_not_fallback_to_unusable_raw_code(self) -> None:
        rows = [
            {
                "score": 100,
                "retrieval_mode": "agent_recipe",
                "title": "Webhook background example",
                "matched_path": "AGENT_RECIPES.md",
                "source_anchor": "https://docs.example/webhook-background",
                "_matched_text": (
                    "Webhook use case prose.\n\n"
                    "### Background node\n\n"
                    "```markdown\n"
                    "Webhook analytics example.\n\n"
                    "```python\n"
                    "client.background.run()\n"
                    "```\n"
                    "```"
                ),
                "snippet": (
                    "Webhook use case prose.\n\n"
                    "### Background node\n\n"
                    "```markdown\n"
                    "Webhook analytics example.\n\n"
                    "```python\n"
                    "client.background.run()\n"
                    "```\n"
                    "```"
                ),
            },
            {
                "score": 80,
                "retrieval_mode": "source_section",
                "title": "Managing Webhooks",
                "matched_path": "guides/webhooks.md",
                "source_anchor": "https://docs.example/webhooks",
                "_matched_text": "Manage webhooks from the dashboard, add the endpoint URL, choose the relevant event subscriptions, save the webhook, and attach it to an agent before running a delivery test.",
                "snippet": "Manage webhooks from the dashboard, add the endpoint URL, choose the relevant event subscriptions, save the webhook, and attach it to an agent before running a delivery test.",
            },
        ]

        packet = context_packet(rows, query="create a webhook tool", max_tokens=900, max_results=6)

        self.assertEqual(packet["codeSnippets"], [])
        self.assertTrue(packet["infoSnippets"])

    def test_specific_required_terms_survive_after_candidate_narrowing(self) -> None:
        rows = [
            {"_matched_text": "Webhook setup and dashboard details."},
            {"_matched_text": "Webhook delivery events and subscriptions."},
            {"_matched_text": "Webhook troubleshooting and retry notes."},
            {"_matched_text": "Webhook headers and endpoint URL."},
        ]

        self.assertEqual(context_required_terms("create an agent webhook tool", rows), {"webhook"})
