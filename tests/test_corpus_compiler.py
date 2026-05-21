from __future__ import annotations

import json
import pytest

from oz_api.indexer import source_document_key_for_row
from oz_api.indexer_artifacts import source_document_rows
from oz_api.crawler_job_eval import product_requirement_hit, wrong_product_requirement_hit
from oz_api.recipe_compiler import build_agent_recipes_from_surfaces, validate_agent_recipes
from oz_crawler.chunks import (
    ContextualPrefixCache,
    MarkdownChunk,
    chunk_contextual_prefix,
    contextual_prefix_cache_key,
    source_document_key,
    write_chunks,
)
from oz_crawler.crawl import CrawlOptions, crawl_pages, dedupe_pages_by_source, discover_declared_doc_links
from oz_crawler.corpus_surfaces import (
    api_operation_for_page,
    api_operations_for_page,
    code_examples_for_page,
    normalize_source_type,
    normalized_metadata,
    sdk_method_for_page,
    sdk_methods_for_page,
    source_sections_for_page,
    write_corpus_surfaces,
)
from oz_crawler.normalize import NormalizedPage
from oz_crawler.profiles import LibraryProfile
from oz_crawler.splitting import assign_page_paths, split_llms_full
from oz_crawler.sources import SourceArtifact, collect_source_artifacts, dedupe_artifacts, github_file_artifacts, llms_manifest_urls
from oz_crawler.crawl_artifacts import write_source_documents
from oz_crawler.validation import is_policy_rejection, missing_expected_symbols, validate_fixture


def page(**kwargs):
    defaults = {
        "source_url": "https://docs.example.com/guide",
        "canonical_url": "https://docs.example.com/guide",
        "title": "Guide",
        "markdown": "# Guide\n\nUse this SDK.\n",
        "path": "guides/guide.md",
        "content_type": "prose",
        "symbols": [],
        "source_type": "website_url",
        "source_priority": 20,
        "source_metadata": {},
        "quality_score": 1.0,
    }
    defaults.update(kwargs)
    return NormalizedPage(**defaults)


def test_source_type_normalization_is_limited_to_locked_source_types() -> None:
    assert normalize_source_type("", "https://github.com/acme/sdk") == "github"
    assert normalize_source_type("", "https://docs.example.com/llms.txt") == "llms_txt"
    assert normalize_source_type("", "https://docs.example.com/openapi.json") == "openapi"
    assert normalize_source_type("", "https://docs.example.com/docs") == "website_url"
    assert normalize_source_type("unknown", "https://github.com/acme/sdk/blob/main/client.py") == "github"


def test_clean_document_surfaces_extract_sections_and_code_examples() -> None:
    p = page(
        markdown=(
            "# Quickstart\n\n"
            "Install and initialize the client.\n\n"
            "```python\n"
            "from acme import Client\n"
            "client = Client(api_key=ACME_API_KEY)\n"
            "client.create_widget(name='demo')\n"
            "```\n"
        ),
        source_metadata={"source_type": "website_url", "document_role": "guide", "product": "sdk", "product_confidence": 1.0},
    )

    sections = source_sections_for_page(p)
    examples = code_examples_for_page(p)

    assert sections
    assert sections[0]["document_role"] == "guide"
    assert sections[0]["source_anchor"].startswith("https://docs.example.com/guide#")
    assert examples
    assert examples[0]["language"] == "python"
    assert "Client" in examples[0]["symbols_json"]
    assert "ACME_API_KEY" in examples[0]["required_env_json"]
    assert examples[0]["document_role"] == "guide"


def test_canonical_sections_include_shape_flags_and_content_hash() -> None:
    p = page(
        markdown=(
            "# API\n\n"
            "POST /v1/widgets\n\n"
            "```python\n"
            "client.widgets.create(name='demo')\n"
            "```\n"
        ),
        source_metadata={"source_type": "website_url", "document_role": "api_reference"},
    )

    section = source_sections_for_page(p)[0]

    assert section["content_sha"]
    assert section["depth"] == 1
    assert section["has_code"] is True
    assert section["has_endpoint_shape"] is True
    assert section["has_signature_shape"] is True


def test_chunks_carry_section_linkage_and_embedding_input_sha(tmp_path) -> None:
    p = page(
        markdown="# Quickstart\n\nInstall and initialize the SDK.\n",
        source_metadata={"source_type": "website_url", "document_role": "guide", "product": "sdk", "product_confidence": 1.0},
    )
    target = tmp_path / "acme" / "sdk" / "1.0.0"
    target.mkdir(parents=True)

    write_chunks(target, [p])

    row = json.loads((target / "_chunks.jsonl").read_text().splitlines()[0])
    assert row["metadata_json"]["source_section_key"]
    assert row["source_section_key"] == row["metadata_json"]["source_section_key"]
    assert row["contextual_prefix"].startswith("Document: Guide.")
    assert len(row["embedding_input_sha"]) == 64
    assert "source_type" not in row


def test_contextual_prefix_cache_reuses_saved_prefix_without_llm(tmp_path) -> None:
    target = tmp_path / "acme" / "sdk" / "1.0.0"
    target.mkdir(parents=True)
    cache = ContextualPrefixCache.create(target)
    p = page(markdown="# Quickstart\n\nUse the client.")
    chunk = MarkdownChunk(
        text="Use the client.",
        heading_path=["Quickstart"],
        start_line=3,
        end_line=3,
        content_type="prose",
    )
    actual_key = contextual_prefix_cache_key(p, "guides/guide.md", chunk)
    cache.set(actual_key, "Document: cached reusable prefix.")

    assert chunk_contextual_prefix(p, "guides/guide.md", chunk, cache) == "Document: cached reusable prefix."


def test_source_documents_preserve_raw_object_metadata(tmp_path) -> None:
    target = tmp_path / "fixture"
    target.mkdir()
    p = page(
        source_metadata={
            "source_type": "website_url",
            "raw_artifact_key": "oz/raw/doc.body",
            "raw_object_store": "local",
            "raw_object_sha256": "abc123",
        }
    )

    write_source_documents(target, [p])

    row = json.loads((target / "_sources.jsonl").read_text().splitlines()[0])
    assert row["raw_artifact_key"] == "oz/raw/doc.body"
    assert row["raw_object_store"] == "local"
    assert row["raw_object_sha256"] == "abc123"


def test_indexer_requires_canonical_sources_artifact(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="_sources.jsonl"):
        source_document_rows(tmp_path)


def test_wrong_product_gate_uses_context_result_metadata() -> None:
    packet = {
        "results": [
            {"source_metadata": {"product": "waves"}, "library": "waves", "vendor": "smallest-ai"},
        ],
        "codeSnippets": [{"source": "https://docs.example.com/waves"}],
    }

    assert product_requirement_hit(packet, "Waves setup", ["waves"])
    assert wrong_product_requirement_hit(packet, "Waves setup", ["atoms"], [])
    assert wrong_product_requirement_hit(packet, "Waves setup", [], ["waves"])


def test_openapi_page_emits_structured_api_operation() -> None:
    p = page(
        source_url="https://docs.example.com/openapi.json#post-widgets",
        source_type="openapi",
        path="api-reference/openapi/post-widgets.md",
        content_type="api_reference",
        markdown="# API: POST /widgets\n\nCreate a widget.\n",
        source_metadata={
            "source_type": "openapi",
            "document_role": "api_reference",
            "operation": {
                "kind": "create",
                "operation_name": "createWidget",
                "operation_id": "createWidget",
                "http_method": "POST",
                "endpoint": "/widgets",
                "required_params": [{"name": "name", "required": True}],
                "optional_params": [{"name": "metadata", "required": False}],
                "response_schema": [{"status": "200"}],
            },
        },
    )

    op = api_operation_for_page(p)

    assert op is not None
    assert op["operation_kind"] == "create"
    assert op["http_method"] == "POST"
    assert op["endpoint"] == "/widgets"
    assert op["required_params_json"] == [{"name": "name", "required": True}]


def test_docs_api_reference_emits_multiple_structured_operations() -> None:
    p = page(
        source_url="https://docs.example.com/api/widgets",
        path="api-reference/widgets.md",
        content_type="api_reference",
        markdown=(
            "# Widgets API\n\n"
            "## Create widget\n\n"
            "POST /v1/widgets\n\n"
            "| name | type | required | description |\n"
            "| --- | --- | --- | --- |\n"
            "| `name` | string | required | Widget name |\n\n"
            "## List widgets\n\n"
            "GET /v1/widgets\n\n"
            "Returns all widgets.\n"
        ),
        source_metadata={"source_type": "website_url", "document_role": "api_reference"},
    )

    operations = api_operations_for_page(p)

    assert [(op["http_method"], op["endpoint"]) for op in operations] == [
        ("POST", "/v1/widgets"),
        ("GET", "/v1/widgets"),
    ]
    assert operations[0]["required_params_json"][0]["name"] == "name"
    assert all(op["metadata_json"]["extraction"] == "documented_api" for op in operations)


def test_sdk_method_filter_rejects_internal_generated_helpers() -> None:
    p = page(
        source_url="https://raw.githubusercontent.com/acme/sdk/main/acme/configuration.py",
        source_type="github",
        path="api-reference/source/configuration.md",
        markdown="# Configuration\n\n```python\nclass Configuration:\n    def get_default(self): ...\n```\n",
        source_metadata={
            "source_type": "github",
            "document_role": "sdk_source",
            "language": "python",
            "operation": {
                "kind": "config",
                "operation_name": "Configuration",
                "sdk_class": "Configuration",
                "sdk_method": "get_default",
                "request_schema": "def get_default(self)",
            },
        },
    )

    assert sdk_method_for_page(p) is None


def test_docs_examples_emit_documented_sdk_methods() -> None:
    p = page(
        markdown=(
            "# Quickstart\n\n"
            "Create a widget with the public client.\n\n"
            "```python\n"
            "from acme import Client\n"
            "client = Client(api_key=ACME_API_KEY)\n"
            "client.create_widget(name='demo')\n"
            "```\n"
        ),
        source_metadata={"source_type": "website_url", "document_role": "guide", "language": "python"},
    )

    methods = sdk_methods_for_page(p)

    assert any(method["sdk_method"] == "create_widget" for method in methods)
    create = next(method for method in methods if method["sdk_method"] == "create_widget")
    assert create["metadata_json"]["extraction"] == "documented_sdk"
    assert create["source_anchor"].startswith("https://docs.example.com/guide#")


def test_github_source_file_enters_as_canonical_markdown_not_fake_symbol_docs(monkeypatch) -> None:
    source = '''
class Client:
    """Public API client."""

    def create_widget(self, name: str) -> dict:
        """Create a widget by name."""
        return {"name": name}
'''

    monkeypatch.setattr("oz_crawler.sources.fetch_text", lambda url, *, state=None: source)

    artifacts = github_file_artifacts(
        "acme",
        "sdk",
        "src/acme/client.py",
        "https://raw.githubusercontent.com/acme/sdk/main/src/acme/client.py",
        profile=LibraryProfile(vendor="acme", library="sdk", include_source_files=True),
        state=None,
        limit=10,
    )

    assert len(artifacts) == 1
    assert artifacts[0].path.startswith("source/")
    assert "api-reference/source" not in artifacts[0].path
    assert artifacts[0].metadata["document_role"] == "sdk_source"
    assert artifacts[0].metadata["source_file_path"] == "src/acme/client.py"


def test_sdk_methods_are_extracted_from_canonical_source_document() -> None:
    p = page(
        source_url="https://raw.githubusercontent.com/acme/sdk/main/src/acme/client.py",
        source_type="github",
        path="source/src-acme-client-py.md",
        markdown=(
            "# Source file: src/acme/client.py\n\n"
            "```python\n"
            "class Client:\n"
            "    \"\"\"Public API client.\"\"\"\n\n"
            "    def create_widget(self, name: str) -> dict:\n"
            "        \"\"\"Create a widget by name.\"\"\"\n"
            "        return {\"name\": name}\n"
            "```\n"
        ),
        source_metadata={
            "source_type": "github",
            "document_role": "sdk_source",
            "language": "python",
            "source_file_path": "src/acme/client.py",
        },
    )

    assert code_examples_for_page(p) == []
    methods = sdk_methods_for_page(p)

    assert any(method["sdk_class"] == "Client" and method["sdk_method"] == "create_widget" for method in methods)
    create = next(method for method in methods if method["sdk_method"] == "create_widget")
    assert create["metadata_json"]["source_origin"] == "ast"
    assert create["required_params_json"] == [{"name": "name", "type": "str", "required": True}]


def test_recipe_compiler_prefers_evidence_backed_examples_and_operations() -> None:
    examples = [
        {
            "example_key": "ex1",
            "title": "Create a widget",
            "description": "Creates a widget with the SDK.",
            "code": "from acme import Client\nclient = Client()\nclient.create_widget(name='demo')",
            "language": "python",
            "task_tags_json": ["create"],
            "source_anchor": "https://docs.example.com/quickstart#create",
            "quality_score": 1.3,
            "confidence": 0.9,
            "metadata_json": {"source_type": "website_url", "document_role": "guide"},
        }
    ]
    operations = [
        {
            "operation_key": "op1",
            "operation_name": "createWidget",
            "operation_kind": "create",
            "http_method": "POST",
            "endpoint": "/widgets",
            "required_params_json": [{"name": "name"}],
            "source_anchor": "https://docs.example.com/openapi#createWidget",
            "metadata_json": {"source_type": "openapi", "document_role": "api_reference"},
        }
    ]

    recipes = build_agent_recipes_from_surfaces(
        code_examples=examples,
        api_operations=operations,
        sdk_methods=[],
        source_sections=[],
        code_example_ids={"ex1": 10},
        api_operation_ids={"op1": 20},
        sdk_method_ids={},
        source_section_ids={},
    )

    assert any(recipe["source_code_example_ids_json"] == [10] for recipe in recipes)
    assert any(recipe["source_api_operation_ids_json"] == [20] for recipe in recipes)
    assert all("source_urls_json" in recipe for recipe in recipes)


def test_llms_full_seed_is_split_without_link_crawl(monkeypatch) -> None:
    text = """---
title: Quickstart
url: https://docs.example.com/quickstart
---
# Quickstart

Use the SDK.

---
title: Auth
url: https://docs.example.com/auth
---
# Auth

Set the API key.
"""

    def fail_link_crawl(*args, **kwargs):
        raise AssertionError("llms-full seeds must not enter linked website crawling")

    monkeypatch.setattr("oz_crawler.crawl.crawl_pages_with_scrapling", fail_link_crawl)
    monkeypatch.setattr("oz_crawler.crawl.crawl_pages_with_stdlib", fail_link_crawl)
    monkeypatch.setattr("oz_crawler.crawl.fetch_html_stdlib", lambda url, state=None: text)

    pages = crawl_pages(
        "https://docs.example.com/llms-full.txt",
        title=None,
        options=CrawlOptions(max_pages=500, fetcher="stdlib"),
    )

    assert [p.title for p in pages] == ["Quickstart", "Auth"]
    assert all(p.source_type == "website_url" for p in pages)
    assert pages[0].source_metadata["expanded_from"] == "llms_full"
    assert pages[0].source_url == "https://docs.example.com/quickstart"


def test_llms_full_without_frontmatter_splits_on_h1_headings() -> None:
    text = """> Complete docs for agents.

# Quickstart

Install and initialize the SDK.

```python
# This H1-looking line is inside code and must not split:
# Not A Page
```

# Authentication

Set the API key.

# Authentication

Rotate the API key.
"""

    pages = split_llms_full(text, source_url="https://docs.example.com/llms-full.txt")
    pages = assign_page_paths(pages)

    assert [p.title for p in pages] == ["Quickstart", "Authentication", "Authentication"]
    assert pages[0].source_url == "https://docs.example.com/llms-full.txt#quickstart"
    assert pages[1].source_url == "https://docs.example.com/llms-full.txt#authentication"
    assert pages[2].source_url == "https://docs.example.com/llms-full.txt#authentication-2"
    assert [p.path for p in pages] == [
        "guides/quickstart.md",
        "guides/authentication.md",
        "guides/authentication-2.md",
    ]


def test_virtual_llms_pages_are_not_deduped_by_base_source_url() -> None:
    pages = split_llms_full(
        "# Quickstart\n\nUse the SDK with a complete guide.\n\n# Auth\n\nSet the API key for requests.\n",
        source_url="https://docs.example.com/llms-full.txt",
    )

    accepted, rejected = dedupe_pages_by_source(pages)

    assert len(accepted) == 2
    assert rejected == []


def test_virtual_source_artifacts_are_not_deduped_by_base_source_url() -> None:
    artifacts = [
        SourceArtifact(
            path="api-reference/openapi/get-widget.md",
            title="GET /widget",
            source_url="https://docs.example.com/openapi.json#get-widget",
            markdown="# GET /widget\n",
            source_type="openapi",
            metadata={"source_type": "openapi"},
        ),
        SourceArtifact(
            path="api-reference/openapi/post-widget.md",
            title="POST /widget",
            source_url="https://docs.example.com/openapi.json#post-widget",
            markdown="# POST /widget\n",
            source_type="openapi",
            metadata={"source_type": "openapi"},
        ),
    ]

    assert len(dedupe_artifacts(artifacts)) == 2


def test_virtual_source_keys_are_preserved_across_chunk_and_indexer_layers() -> None:
    llms_url = "https://docs.example.com/llms-full.txt#quickstart"
    openapi_url = "https://docs.example.com/openapi.json#get-widget"

    assert source_document_key(llms_url) == llms_url
    assert source_document_key(openapi_url) == openapi_url
    assert source_document_key_for_row({"source_document_key": llms_url, "source_type": "llms_txt"}) == llms_url
    assert source_document_key_for_row({"source_url": openapi_url, "source_type": "openapi"}) == openapi_url
    assert source_document_key_for_row({"source_url": "https://docs.example.com/guide#section"}) == "https://docs.example.com/guide"


def test_llms_txt_expands_manifest_links_without_becoming_a_document(monkeypatch) -> None:
    def fake_fetch_text(url, *, state=None):
        if url.endswith("/llms.txt"):
            return "- [Guide](https://docs.example.com/guide.md)\n- https://docs.example.com/openapi.json\n"
        return ""

    monkeypatch.setattr("oz_crawler.sources.fetch_text", fake_fetch_text)

    links = llms_manifest_urls("https://docs.example.com/llms.txt", profile=None, state=None, limit=10)

    assert links == ["https://docs.example.com/guide.md", "https://docs.example.com/openapi.json"]


def test_declared_doc_links_do_not_expand_llms_full(monkeypatch) -> None:
    calls: list[str] = []

    def fake_fetch(url: str, *, fetcher: str = "auto") -> str | None:
        calls.append(url)
        if url.endswith("/llms.txt"):
            return "[Guide](https://docs.example.com/guide)"
        if url.endswith("/sitemap.xml"):
            return ""
        raise AssertionError("llms-full should not be fetched for link-frontier discovery")

    monkeypatch.setattr("oz_crawler.crawl.fetch_text_optional", fake_fetch)

    links = discover_declared_doc_links("https://docs.example.com/start", fetcher="stdlib")

    assert links == ["https://docs.example.com/guide"]
    assert "https://docs.example.com/llms-full.txt" not in calls


def test_discovered_github_links_are_not_expanded_as_source_roots(monkeypatch) -> None:
    captured_urls: list[str] = []
    profile = LibraryProfile(
        vendor="acme",
        library="docs",
        allowed_hosts=["docs.example.com", "github.com", "raw.githubusercontent.com"],
        allowed_paths=["/"],
        preferred_urls=["https://docs.example.com/llms-full.txt"],
    )
    p = page(
        source_url="https://docs.example.com/guide",
        markdown="[External repo](https://github.com/other/product)",
        source_type="llms_txt",
    )

    monkeypatch.setattr("oz_crawler.sources.markdown_url_artifacts", lambda *args, **kwargs: [])
    monkeypatch.setattr("oz_crawler.sources.openapi_artifacts", lambda *args, **kwargs: [])
    monkeypatch.setattr("oz_crawler.sources.source_file_url_artifacts", lambda *args, **kwargs: [])

    def fake_github_docs_artifacts(urls, *args, **kwargs):
        captured_urls.extend(urls)
        return []

    monkeypatch.setattr("oz_crawler.sources.github_docs_artifacts", fake_github_docs_artifacts)

    collect_source_artifacts(
        "https://docs.example.com/llms-full.txt",
        [p],
        profile=profile,
        max_documents=100,
    )

    assert "https://github.com/other/product" not in captured_urls
    assert all("github.com/other/product" not in url for url in captured_urls)


def test_expected_symbol_validation_accepts_identifier_phrases() -> None:
    assert missing_expected_symbols(set(), ["KnowledgeBase"], "Upload a Knowledge Base file.") == []
    assert missing_expected_symbols({"NextRequest"}, ["NextRequest"], "") == []
    assert missing_expected_symbols(set(), ["MissingClient"], "No matching concept here.") == ["MissingClient"]


def test_short_virtual_llms_fragments_do_not_count_as_true_junk() -> None:
    assert is_policy_rejection(
        {
            "source_url": "https://docs.example.com/llms-full.txt#step-1",
            "reasons": ["too little documentation text"],
            "content_type": "prose",
        }
    )


def test_corpus_surfaces_merge_openapi_and_docs_operations(tmp_path) -> None:
    openapi_page = page(
        source_url="https://docs.example.com/openapi.json#get-widgets",
        source_type="openapi",
        path="api-reference/openapi/get-widgets.md",
        content_type="api_reference",
        markdown="# GET /v1/widgets\n\nList widgets.\n",
        source_metadata={
            "source_type": "openapi",
            "document_role": "api_reference",
            "operation": {
                "kind": "list",
                "operation_name": "listWidgets",
                "operation_id": "listWidgets",
                "http_method": "GET",
                "endpoint": "/v1/widgets",
            },
        },
    )
    docs_page = page(
        source_url="https://docs.example.com/api/widgets",
        path="api-reference/widgets.md",
        content_type="api_reference",
        markdown="# Widgets\n\nGET /v1/widgets\n\nUse this endpoint to list widgets.\n",
        source_metadata={"source_type": "website_url", "document_role": "api_reference"},
    )
    target = tmp_path / "fixture"
    target.mkdir()

    write_corpus_surfaces(target, [openapi_page, docs_page])

    operations = [json.loads(line) for line in (target / "_api_operations.jsonl").read_text().splitlines()]
    assert len(operations) == 1
    assert operations[0]["http_method"] == "GET"
    assert operations[0]["endpoint"] == "/v1/widgets"
    assert operations[0]["metadata_json"]["source_origin"] == "mixed"
    assert operations[0]["metadata_json"]["evidence_count"] == 2


def test_corpus_surfaces_merge_ast_and_documented_sdk_methods(tmp_path) -> None:
    source_page = page(
        source_url="https://raw.githubusercontent.com/acme/sdk/main/src/acme/client.py",
        source_type="github",
        path="source/client.md",
        markdown="# Source file: src/acme/client.py\n\n```python\nclass Client:\n    def create_widget(self, name: str):\n        return {}\n```\n",
        source_metadata={
            "source_type": "github",
            "document_role": "sdk_source",
            "language": "python",
            "source_file_path": "src/acme/client.py",
        },
    )
    docs_page = page(
        markdown="# Quickstart\n\n```python\nfrom acme import Client\nclient = Client()\nclient.create_widget(name='demo')\n```\n",
        source_metadata={"source_type": "website_url", "document_role": "guide", "language": "python"},
    )
    target = tmp_path / "fixture"
    target.mkdir()

    write_corpus_surfaces(target, [source_page, docs_page])

    methods = [json.loads(line) for line in (target / "_sdk_methods.jsonl").read_text().splitlines()]
    create = [row for row in methods if row["sdk_method"] == "create_widget"]
    assert len(create) == 1
    assert create[0]["metadata_json"]["source_origin"] == "mixed"
    assert create[0]["metadata_json"]["evidence_count"] >= 2


def test_validation_fails_on_source_cap_without_explicit_partial_approval(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OZ_ALLOW_PARTIAL_SOURCE_COVERAGE", raising=False)
    target = tmp_path / "fixture"
    target.mkdir()
    (target / "_crawl_errors.jsonl").write_text(
        json.dumps({"url": "https://docs.example.com", "stage": "source_cap", "error": "source artifact cap hit"}) + "\n",
        encoding="utf-8",
    )

    result = validate_fixture(target, None)

    assert any("source artifact cap was hit" in error for error in result.errors)


def test_validation_fails_chunks_without_contextual_prefix(tmp_path) -> None:
    target = tmp_path / "fixture"
    target.mkdir()
    (target / "_chunks.jsonl").write_text(
        json.dumps(
            {
                "chunk_key": "c1",
                "path": "guides/a.md",
                "text": "Useful docs",
                "content_type": "prose",
                "source_anchor": "https://docs.example.com/a#page",
                "token_count": 2,
                "metadata_json": {"source_section_key": "s1"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = validate_fixture(target, None)

    assert any("missing contextual prefixes" in error for error in result.errors)


def test_recipe_validation_rejects_dangling_evidence() -> None:
    try:
        validate_agent_recipes(
            [
                {
                    "recipe_key": "bad",
                    "source_code_example_ids_json": [99],
                    "source_api_operation_ids_json": [],
                    "source_sdk_method_ids_json": [],
                    "source_section_ids_json": [],
                    "source_urls_json": ["https://docs.example.com"],
                }
            ],
            code_example_ids={"ex1": 1},
            api_operation_ids={},
            sdk_method_ids={},
            source_section_ids={},
        )
    except RuntimeError as exc:
        assert "references missing source_code_example_ids_json" in str(exc)
    else:
        raise AssertionError("dangling recipe evidence should fail validation")
    assert not is_policy_rejection(
        {
            "source_url": "https://docs.example.com/llms-full.txt#signup",
            "reasons": ["too little documentation text", "marketing/login language"],
            "content_type": "prose",
        }
    )
