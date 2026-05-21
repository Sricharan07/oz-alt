from __future__ import annotations

import json

from oz_api.indexer import source_document_key_for_row
from oz_api.recipe_compiler import build_agent_recipes_from_surfaces
from oz_crawler.chunks import source_document_key
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
)
from oz_crawler.normalize import NormalizedPage
from oz_crawler.profiles import LibraryProfile
from oz_crawler.splitting import assign_page_paths, split_llms_full
from oz_crawler.sources import SourceArtifact, collect_source_artifacts, dedupe_artifacts
from oz_crawler.validation import is_policy_rejection, missing_expected_symbols


def page(**kwargs):
    defaults = {
        "source_url": "https://docs.example.com/guide",
        "canonical_url": "https://docs.example.com/guide",
        "title": "Guide",
        "markdown": "# Guide\n\nUse this SDK.\n",
        "path": "guides/guide.md",
        "content_type": "prose",
        "symbols": [],
        "source_kind": "website_url",
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
    assert normalize_source_type("source_code", "https://github.com/acme/sdk/blob/main/client.py") == "github"


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


def test_openapi_page_emits_structured_api_operation() -> None:
    p = page(
        source_url="https://docs.example.com/openapi.json#post-widgets",
        source_kind="openapi",
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
        source_kind="github",
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
    assert all(p.source_kind == "llms_txt" for p in pages)
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
            source_kind="openapi",
            metadata={"source_type": "openapi"},
        ),
        SourceArtifact(
            path="api-reference/openapi/post-widget.md",
            title="POST /widget",
            source_url="https://docs.example.com/openapi.json#post-widget",
            markdown="# POST /widget\n",
            source_kind="openapi",
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
        source_kind="llms_txt",
    )

    monkeypatch.setattr("oz_crawler.sources.markdown_url_artifacts", lambda *args, **kwargs: [])
    monkeypatch.setattr("oz_crawler.sources.openapi_artifacts", lambda *args, **kwargs: [])
    monkeypatch.setattr("oz_crawler.sources.type_definition_artifacts", lambda *args, **kwargs: [])

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
    assert not is_policy_rejection(
        {
            "source_url": "https://docs.example.com/llms-full.txt#signup",
            "reasons": ["too little documentation text", "marketing/login language"],
            "content_type": "prose",
        }
    )
