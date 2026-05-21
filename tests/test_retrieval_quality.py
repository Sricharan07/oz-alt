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
from oz_api.indexer import add_parent_chunks, chunk_rows, enrich_chunk_row, limit_to_token_budget
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
from oz_crawler.parsers.source_code import source_code_chunks, source_path_allowed
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

    def test_indexer_strips_source_index_boilerplate(self) -> None:
        row = enrich_chunk_row(
            {"vendor": "vercel", "library": "next.js", "version": "15"},
            {
                "path": "api-reference/config.md",
                "text": (
                    "Use this config.\n"
                    "For an index of all available documentation, see [/docs/llms.txt](/docs/llms.txt)"
                ),
                "start_line": 1,
            },
        )

        self.assertNotIn("index of all available documentation", row["text"])
        self.assertIn("Use this config.", row["text"])

    def test_indexer_includes_all_symbol_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / "registry" / "fixtures" / "vendor" / "lib" / "1"
            symbols = fixture / "_symbols"
            symbols.mkdir(parents=True)
            (fixture / "_chunks.jsonl").write_text("", encoding="utf-8")
            (symbols / "alpha.md").write_text("# alpha\n\n**Source:** https://docs.example/a\n\nAlpha API.", encoding="utf-8")
            (symbols / "beta.md").write_text("# beta\n\n**Source:** https://docs.example/b\n\nBeta API.", encoding="utf-8")
            rows = chunk_rows(
                RegistryStorage(root),
                {"vendor": "vendor", "library": "lib", "version": "1"},
            )

        paths = {row["path"] for row in rows}
        self.assertIn("_symbols/alpha.md", paths)
        self.assertIn("_symbols/beta.md", paths)

    def test_markdown_cleanup_strips_single_word_nav_boilerplate(self) -> None:
        markdown = clean_markdown("# Guide\n\nSponsor\n\nBlog\n\nUse computed refs.")

        self.assertNotIn("Sponsor", markdown)
        self.assertNotIn("Blog", markdown)
        self.assertIn("Use computed refs.", markdown)

    def test_markdown_cleanup_strips_source_index_boilerplate(self) -> None:
        markdown = clean_markdown(
            "> For an index of all Next.js documentation, see [/docs/pages/llms.txt](/docs/pages/llms.txt).\n"
            "NextResponse extends the Web Response API."
        )

        self.assertNotIn("index of all Next.js documentation", markdown)
        self.assertIn("NextResponse extends", markdown)

    def test_markdown_cleanup_strips_horizontal_rules_without_frontmatter_false_positive(self) -> None:
        markdown = clean_markdown("---\n## Reference\n\nUse `useState`.\n\n---\n## Usage\n")

        self.assertNotIn("---", markdown)
        self.assertTrue(markdown.startswith("## Reference"))
        self.assertFalse(has_frontmatter("---\n## Reference\n\nUse `useState`.\n\n---\n"))

    def test_llms_full_split_does_not_reemit_frontmatter(self) -> None:
        pages = split_llms_full(
            "---\ntitle: Routing\nurl: https://docs.example/routing\n---\n# Routing\n\nUse routes.",
            source_url="https://docs.example/llms-full.txt",
        )

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].title, "Routing")
        self.assertNotIn("title:", pages[0].markdown)

    def test_llms_full_split_ignores_frontmatter_inside_code_fences(self) -> None:
        pages = split_llms_full(
            "---\ntitle: Config Guide\nurl: https://docs.example/config\n---\n"
            "# Config Guide\n\n````md\n---\ntitle: Nested Example\n---\n````\n\nUse config.",
            source_url="https://docs.example/llms-full.txt",
        )

        self.assertEqual(len(pages), 1)
        self.assertIn("Nested Example", pages[0].markdown)

    def test_document_path_uses_canonical_url_not_content_type(self) -> None:
        path = document_path(
            "https://nextjs.org/docs/app/api-reference/functions/cookies",
            "cookies",
            "code_example",
        )

        self.assertEqual(path, "api-reference/app/api-reference/functions/cookies.md")

    def test_source_artifact_markdown_keeps_source_url_out_of_indexed_text(self) -> None:
        markdown = artifact_markdown("Routing", "---\ntitle: Routing\n---\n# Routing\n\nUse routes.")

        self.assertTrue(markdown.startswith("# Routing"))
        self.assertNotIn("**Source:**", markdown)
        self.assertNotIn("title:", markdown)

    def test_source_url_discovery_skips_malformed_urls(self) -> None:
        text = "Good https://docs.example/reference and malformed https://[bad]/docs should not crash."

        self.assertEqual(extract_urls(text, base_url="https://docs.example"), ["https://docs.example/reference"])
        self.assertEqual(
            prioritized_urls(
                "https://docs.example",
                preferred_urls=[],
                discovered_urls=["https://[bad]/docs", "https://docs.example/guide"],
            )[-1],
            "https://docs.example/guide",
        )

    def test_language_filter_rejects_non_target_prose_but_keeps_code_heavy_docs(self) -> None:
        spanish = " ".join(["el ejemplo para configurar la respuesta con los valores"] * 20)
        code_heavy = "```ts\n" + "\n".join(["export function readCookie() { return cookies.get('sid') }"] * 20) + "\n```"

        self.assertFalse(language_allowed(spanish, "en"))
        self.assertTrue(language_allowed(code_heavy, "en"))

    def test_source_code_parser_extracts_documented_exports(self) -> None:
        source = """/** Create a client. */\nexport function createClient(apiKey: string) {\n  return { apiKey };\n}\n"""

        chunks = source_code_chunks(source, "https://github.com/acme/sdk/blob/main/src/client.ts", language="typescript", limit=5)

        self.assertEqual(chunks[0]["path"], "api-reference/source/createclient.md")
        self.assertIn("Create a client", chunks[0]["markdown"])
        self.assertTrue(source_path_allowed("packages/sdk/src/client.ts", ["src/"]))
        self.assertTrue(source_path_allowed("django/forms/widgets.py", ["django/**/*.py"]))
        self.assertTrue(source_path_allowed("src/client.ts", []))

    def test_oversized_code_fence_is_split_under_chunk_cap(self) -> None:
        long_line = "const value = '" + ("x" * 7000) + "';"
        chunks = chunk_markdown(
            "# Config\n\n```ts\n" + long_line + "\n```",
            source_url="https://docs.example/config",
            page_type="code_example",
            max_tokens=250,
        )

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.text.startswith("```ts") and chunk.text.endswith("```") for chunk in chunks))
        self.assertTrue(all(token_count(chunk.text) <= 250 for chunk in chunks))

    def test_crawl_run_state_checkpoints_pages_and_dead_letters(self) -> None:
        progress: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = CrawlRunState.create(root, progress.append)
            state.record_page("https://docs.example/a", "<main>A</main>", "A")
            state.record_dead_letter(
                "https://docs.example/b",
                stage="page_fetch",
                error="HTTP 503",
                attempts=3,
                status=503,
                transient=True,
            )
            restored = CrawlRunState.create(root)

        self.assertEqual(restored.completed_urls, {"https://docs.example/a"})
        self.assertEqual(restored.restored_pages[0]["html"], "<main>A</main>")
        self.assertEqual(restored.dead_letters[0].status, 503)
        self.assertTrue(progress)
        self.assertEqual(progress[-1]["dead_letter_items"][0]["status"], 503)

    def test_pre_promotion_search_eval_uses_candidate_fixture_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            eval_root = repo / "registry" / "evals"
            eval_root.mkdir(parents=True)
            (eval_root / "widget.yaml").write_text(
                json.dumps(
                    {
                        "library": "acme/widget",
                        "version": "1",
                        "checks": [
                            {
                                "name": "candidate docs",
                                "query": "new target",
                                "expected_files": ["guides/new.md"],
                                "must_include": ["target"],
                                "must_not_include": ["old"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stale = repo / "registry" / "fixtures" / "acme" / "widget" / "1"
            stale.mkdir(parents=True)
            (stale / "_chunks.jsonl").write_text(
                json.dumps({"path": "guides/old.md", "text": "old target", "start_line": 1}) + "\n",
                encoding="utf-8",
            )
            candidate_root = repo / "candidate-fixtures"
            candidate = candidate_root / "acme" / "widget" / "1"
            (candidate / "guides").mkdir(parents=True)
            (candidate / "guides" / "new.md").write_text("new target", encoding="utf-8")
            (candidate / "_chunks.jsonl").write_text(
                json.dumps({"path": "guides/new.md", "text": "new target", "start_line": 1}) + "\n",
                encoding="utf-8",
            )

            report = search_eval_report(
                RegistryStorage(repo_root=repo),
                "acme/widget",
                "1",
                fixtures_root=candidate_root,
            )

        self.assertIsNotNone(report)
        assert report is not None
        self.assertTrue(report["passed"])
        self.assertEqual(report["checks"][0]["paths"], [".codo/vendors/acme/widget@1/guides/new.md"])

    def test_search_eval_content_requirements_support_pattern_alternatives(self) -> None:
        self.assertTrue(content_requirement_hit("useState updater function", ["set function"], ["set function|updater"]))
        self.assertFalse(content_requirement_hit("useState render", ["set function"], ["set function|updater"]))

    def test_search_eval_path_bans_do_not_flag_valid_content_words(self) -> None:
        self.assertFalse(path_junk_hit([".codo/vendors/vuejs/vue@3/guides/blog-example.md"], [], ["/blog$"]))
        self.assertTrue(path_junk_hit([".codo/vendors/vuejs/vue@3/guides/blog.md"], [], ["/blog\\.md$"]))

    def test_write_chunks_does_not_embed_inline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            page = NormalizedPage(title="Doc", markdown="# Doc\n\nUse it.", source_url="https://docs.example/doc", path="guides/doc.md")
            write_chunks(target, [page])
            row = next(json.loads(line) for line in (target / "_chunks.jsonl").read_text().splitlines() if line.strip())
            coverage = next(json.loads(line) for line in (target / "_chunk_coverage.jsonl").read_text().splitlines() if line.strip())

        self.assertIn("chunk_sha", row)
        self.assertIn("content_sha", row)
        self.assertIn("source_section_key", row)
        self.assertEqual(row["content_sha"], content_hash(row["text"]))
        self.assertNotIn("embedding", row)
        self.assertNotIn("embedding_model", row)
        self.assertEqual(coverage["coverage_ratio"], 1.0)
        self.assertEqual(coverage["uncovered_ranges"], [])

    def test_write_chunks_assigns_symbols_only_when_present_in_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "vendor" / "library" / "latest"
            target.mkdir(parents=True)
            write_chunks(
                target,
                [
                    NormalizedPage(
                        title="Hooks",
                        markdown="# Hooks\n\nUse `useEffect` for cleanup.\n\n## Other\n\nUse memoization carefully.",
                        source_url="https://react.dev/reference/react/hooks",
                        path="api-reference/react/hooks.md",
                        content_type="api_reference",
                        symbols=("useEffect", "useEffectEvent"),
                    )
                ],
            )
            rows = [json.loads(line) for line in (target / "_chunks.jsonl").read_text().splitlines() if line.strip()]

        effect_rows = [row for row in rows if "useEffect" in row["text"]]
        other_rows = [row for row in rows if "memoization" in row["text"]]
        self.assertTrue(effect_rows)
        self.assertEqual(effect_rows[0]["symbols"], ["useEffect"])
        self.assertTrue(other_rows)
        self.assertEqual(other_rows[0]["symbols"], [])

    def test_prepare_pages_rejects_duplicate_source_content(self) -> None:
        markdown = "# useEffect\n\n" + "React effect cleanup dependencies example. " * 20
        pages = [
            NormalizedPage(title="useEffect", markdown=markdown, source_url="https://react.dev/reference/react/useEffect"),
            NormalizedPage(title="useEffect copy", markdown=markdown, source_url="https://react.dev/reference/react/useEffect"),
        ]

        accepted, rejected = prepare_pages(pages, profile=None, version="19")

        self.assertEqual(len(accepted), 1)
        self.assertEqual(len(rejected), 1)
        self.assertIn("duplicate source", rejected[0]["reasons"])

    def test_pack_excludes_internal_indexing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "guides").mkdir()
            (root / ".oz").mkdir()
            (root / "INDEX.md").write_text("# Index\n", encoding="utf-8")
            (root / "guides" / "doc.md").write_text("Doc", encoding="utf-8")
            (root / ".oz" / "manifest.json").write_text("{}", encoding="utf-8")
            (root / "_chunks.jsonl").write_text("internal", encoding="utf-8")
            body, manifest = build_pack_bytes(root, "v", "l", "1")

        paths = {row["path"] for row in manifest["blobs"]}
        self.assertIn("INDEX.md", paths)
        self.assertIn("guides/doc.md", paths)
        self.assertIn(".oz/manifest.json", paths)
        self.assertNotIn("_chunks.jsonl", paths)
        self.assertNotIn(b"_chunks.jsonl", body)
        report = pack_eval_report(manifest)
        self.assertTrue(report["passed"])
        self.assertTrue(report["metrics"]["has_manifest"])

    def test_validation_blocks_long_anchors_and_docs_authoring_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "guides" / "community").mkdir(parents=True)
            (target / "guides" / "community" / "contribution-guide.md").write_text("Contribution guide", encoding="utf-8")
            (target / "_chunks.jsonl").write_text(
                json.dumps(
                    {
                        "path": "guides/community/contribution-guide.md",
                        "text": "For an index of all docs, read this.",
                        "source_anchor": "https://docs.example/" + ("x" * 260),
                        "heading_path": ["h" * 170],
                        "token_count": 12,
                        "content_type": "prose",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = validate_fixture(target, profile=None)

        self.assertFalse(result.passed)
        self.assertGreater(result.metrics["long_source_anchors"], 0)
        self.assertGreater(result.metrics["docs_authoring_chunks"], 0)
        self.assertGreater(result.metrics["index_boilerplate_chunks"], 0)

    def test_write_chunks_preserves_duplicate_content_across_source_paths_for_coverage(self) -> None:
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
            coverage = [json.loads(line) for line in (target / "_chunk_coverage.jsonl").read_text().splitlines() if line.strip()]

        self.assertEqual(len(rows), 2)
        self.assertEqual({row["path"] for row in rows}, {"guides/one.md", "guides/two.md"})
        self.assertTrue(all(row["coverage_ratio"] == 1.0 for row in coverage))

    def test_validation_junk_ratio_excludes_policy_dedup_rejections(self) -> None:
        rows = [
            {"content_type": "duplicate", "reasons": ["duplicate content", "canonical source: https://docs.example/a"]},
            {"content_type": "network_page_fetch", "reasons": ["crawler URL returned HTTP 404: https://docs.example/missing"]},
            {"content_type": "junk", "reasons": ["url rejected by library profile"]},
            {"content_type": "junk", "reasons": ["marketing/login language"]},
        ]

        self.assertEqual(len(true_junk_rejections(rows)), 1)

    def test_validation_treats_all_retrieval_content_types_as_useful(self) -> None:
        self.assertIn("config", USEFUL_CONTENT_TYPES)

    def test_api_reference_parent_chunks_respect_max_token_limit(self) -> None:
        markdown = "# Endpoint\n\n## Response\n\n" + "\n".join(f"- field_{idx}: lorem ipsum dolor sit amet" for idx in range(500))

        chunks = chunk_markdown(
            markdown,
            source_url="https://docs.example/reference",
            page_type="api_reference",
            max_tokens=300,
        )

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(token_count(chunk.text) <= 300 for chunk in chunks))
        self.assertIn("cli", USEFUL_CONTENT_TYPES)
        self.assertIn("error_ref", USEFUL_CONTENT_TYPES)

    def test_indexer_adds_parent_only_for_multiple_meaningful_api_children(self) -> None:
        entry = {"vendor": "v", "library": "l", "version": "1"}
        single = [
            {
                "path": "api-reference/widget.md",
                "chunk_key": "api-reference/widget.md#1",
                "content_type": "api_reference",
                "ordinal": 1,
                "text": "Widget reads request values, validates headers, applies cookie metadata, and returns response metadata for callers.",
            }
        ]
        multiple = [
            {
                "path": "api-reference/widget.md",
                "chunk_key": "api-reference/widget.md#1",
                "content_type": "api_reference",
                "ordinal": 1,
                "text": "Widget reads request values, validates headers, applies cookie metadata, and returns response metadata for callers.",
            },
            {
                "path": "api-reference/widget.md",
                "chunk_key": "api-reference/widget.md#2",
                "content_type": "api_reference",
                "ordinal": 2,
                "text": "Widget writes response headers, serializes body values, and preserves status information for middleware callers.",
            },
        ]

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(len(add_parent_chunks(entry, Path(tmp), single)), 1)
            parented = add_parent_chunks(entry, Path(tmp), multiple)

        self.assertEqual(len(parented), 3)
        self.assertTrue(any(row.get("chunk_key") == "api-reference/widget.md#parent-api-reference" for row in parented))

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
                "source_file_patterns": ["django/**/*.py"],
                "needs_js": True,
                "include_source_files": True,
                "target_language": "en",
            }
        )

        self.assertEqual(event["db_job_id"], "49")
        self.assertEqual(event["profile"]["allowed_hosts"], ["docs.djangoproject.com"])
        self.assertEqual(event["profile"]["allowed_paths"], ["/en/stable/"])
        self.assertEqual(event["profile"]["source_file_patterns"], ["django/**/*.py"])
        self.assertTrue(event["profile"]["needs_js"])
        self.assertTrue(event["profile"]["include_source_files"])
        self.assertEqual(event["profile"]["target_language"], "en")

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

    def test_absolute_allowed_paths_match_prefix_not_any_segment(self) -> None:
        profile = LibraryProfile(vendor="v", library="l", allowed_hosts=["example.com"], allowed_paths=["/docs"])

        self.assertTrue(url_allowed_by_profile("https://example.com/docs/reference/page", profile))
        self.assertFalse(url_allowed_by_profile("https://example.com/ui/docs/reference/page", profile))

    def test_crawler_rejects_malformed_markdown_urls(self) -> None:
        self.assertFalse(is_crawlable_doc_url("https://example.com/docs/guides/auth](https://example.com/docs/auth", "example.com"))
        self.assertFalse(is_crawlable_doc_url("https://example.com/ui/docs/widget'", "example.com"))

    def test_rerank_strips_private_fields_and_boosts_named_suggestions(self) -> None:
        rows = [{"vendor": "vercel", "library": "next.js", "version": "15", "score": 1, "_rerank_text": "secret"}]
        boosted = boost_named_suggestions("next.js", rows)
        self.assertGreater(boosted[0]["score"], 1)
        self.assertNotIn("_rerank_text", strip_private_fields(boosted)[0])

    def test_rerank_cache_key_changes_when_candidate_paths_change(self) -> None:
        first = rerank_cache_key("search:facebook/react", "hooks", "project", [{"path": "old.md"}])
        second = rerank_cache_key("search:facebook/react", "hooks", "project", [{"path": "new.md"}])

        self.assertNotEqual(first, second)

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

        def fake_request(url: str, payload: dict[str, object], headers: dict[str, str], **_kwargs: object):
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

    def test_markdown_chunking_handles_malformed_inputs_without_crashing(self) -> None:
        samples = [
            "---\ntitle: Broken",
            "# Heading\n\n```ts\nunterminated fence\nconst value = 1",
            "- item\n  ```json\n  {bad json\n  ```\n\n<table><tr><td>cell",
            "\x00\x01# Binary-ish\n\n" + ("word " * 400),
            "# Long paragraph\n\n" + ("configuration middleware cookies response headers " * 500),
        ]

        for sample in samples:
            with self.subTest(sample=sample[:24]):
                chunks = chunk_markdown(clean_markdown(sample), source_url="https://docs.example/fuzz", max_tokens=300)
                self.assertTrue(all(chunk.text.strip() for chunk in chunks))
                self.assertTrue(all(token_count(chunk.text) <= 1200 for chunk in chunks))








if __name__ == "__main__":
    unittest.main()
