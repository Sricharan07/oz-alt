from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from oz_crawler.normalize import NormalizedPage, clean_markdown
from oz_crawler.parsers.source_code import extracted_documented_blocks, infer_operation_kind
from oz_crawler.sections import (
    source_anchor,
    source_document_key,
    source_path_for_page,
    source_section_key_for_line,
    source_sections_for_page,
)
from oz_crawler.token_counting import token_count
from oz_crawler.corpus_surface_utils import *  # noqa: F403

FENCE_RE = re.compile(r"(?ms)^\s*(`{3,}|~{3,})([A-Za-z0-9_+.#-]*)\n(?P<code>.*?)(?:^\s*\1\s*$)")
CLI_LINE_RE = re.compile(r"(?m)^\s*(?:\$|npx|npm|pnpm|yarn|pip|uv|curl|docker|kubectl|aws|gh|git)\s+\S+.*$")
ENV_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}(?:API_KEY|TOKEN|SECRET|KEY|HOST|URL)\b")
IMPORT_RE = re.compile(r"(?m)^\s*(?:from\s+[\w.]+\s+import\s+[\w.*, ]+|import\s+[\w., {}*]+|const\s+.*?=\s*require\([^)]+\))")
IDENT_RE = re.compile(r"\b[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)?\b")
HTTP_ENDPOINT_RE = re.compile(
    r"(?im)(?:^|[`\\s>])(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+"
    r"(?P<endpoint>(?:https?://[^\s`'\"<>)]+|/[A-Za-z0-9_./:{}?&=%+-]*))"
)
CURL_ENDPOINT_RE = re.compile(
    r"(?is)\bcurl\b(?P<args>[^`\n]*(?:\\\n[^`\n]*)*)"
)
FETCH_ENDPOINT_RE = re.compile(
    r"(?is)\bfetch\s*\(\s*[\"'](?P<endpoint>https?://[^\"']+|/[^\"']+)[\"'](?P<body>.*?)\)"
)
METHOD_OPTION_RE = re.compile(r"(?i)\bmethod\s*[:=]\s*[\"']?(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)[\"']?")
SDK_DOTTED_CALL_RE = re.compile(r"\b(?P<receiver>[A-Za-z_$][A-Za-z0-9_$]*)\.(?P<method>[A-Za-z_$][A-Za-z0-9_$]*)\s*\(")
PY_DEF_RE = re.compile(r"(?m)^\s*(?:async\s+)?def\s+(?P<method>[A-Za-z_][A-Za-z0-9_]*)\s*\((?P<params>[^)]*)\)")
JS_EXPORT_RE = re.compile(
    r"(?m)^\s*(?:export\s+)?(?:async\s+)?(?:function|const|let|var)\s+"
    r"(?P<method>[A-Za-z_$][A-Za-z0-9_$]*)\s*(?:=|\()(?P<params>[^)]*)"
)

VALID_SOURCE_TYPES = {"website_url", "github", "llms_txt", "openapi"}
DOCUMENT_ROLES = {
    "readme",
    "guide",
    "api_reference",
    "example",
    "test",
    "sdk_source",
    "type_definition",
    "changelog",
    "troubleshooting",
    "config",
    "unknown",
}
INTERNAL_METHODS = {
    "get_default",
    "set_default",
    "with_http_info",
    "request_factory",
    "response_deserialize",
    "deserialize",
    "serialize",
}
INTERNAL_CLASSES = {"Configuration", "ApiClient", "ApiResponse", "RESTResponse", "ApiException"}


def write_corpus_surfaces(target: Path, pages: list[NormalizedPage]) -> None:
    sections: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []
    api_operations: list[dict[str, Any]] = []
    sdk_methods: list[dict[str, Any]] = []
    for page in pages:
        sections.extend(source_sections_for_page(page))
        examples.extend(code_examples_for_page(page))
        api_operations.extend(api_operations_for_page(page))
        sdk_methods.extend(sdk_methods_for_page(page))
    sections = dedupe_rows(sections, "section_key")
    examples = canonicalize_code_examples(examples)
    api_operations = merge_api_operations(api_operations)
    sdk_methods = merge_sdk_methods(sdk_methods)
    write_jsonl(target / "_source_sections.jsonl", sections)
    write_jsonl(target / "_code_examples.jsonl", examples)
    write_jsonl(target / "_api_operations.jsonl", api_operations)
    write_jsonl(target / "_sdk_methods.jsonl", sdk_methods)


def code_examples_for_page(page: NormalizedPage) -> list[dict[str, Any]]:
    path = source_path_for_page(page)
    source_key = source_document_key(page.canonical_url or page.source_url or path)
    metadata = normalized_metadata(page)
    if metadata["document_role"] in {"sdk_source", "type_definition"} and metadata.get("source_file_path"):
        return []
    markdown = clean_markdown(page.markdown)
    lines = markdown.splitlines()
    sections = source_sections_for_page(page)
    output: list[dict[str, Any]] = []
    for index, match in enumerate(FENCE_RE.finditer(markdown), start=1):
        code = match.group("code").strip()
        language = canonical_language(match.group(2).strip()) or metadata["language"]
        if reject_code_example(code, language):
            continue
        start_line = markdown[: match.start()].count("\n") + 1
        end_line = start_line + match.group(0).count("\n")
        heading_path = heading_path_before(lines, start_line)
        caption = heading_path[-1] if heading_path else page.title or "Example"
        description = nearby_description(lines, start_line)
        source = source_anchor(page.canonical_url or page.source_url, heading_path, index)
        output.append(
            {
                "example_key": stable_key("example", path, str(start_line), code[:240]),
                "source_document_key": source_key,
                "path": path,
                "source_type": metadata["source_type"],
                "document_role": metadata["document_role"],
                "product": metadata["product"],
                "product_confidence": metadata["product_confidence"],
                "language": language,
                "title": caption,
                "description": description,
                "caption": caption,
                "code": code,
                "imports_json": imports_for_code(code),
                "symbols_json": symbols_for_code(code),
                "task_tags_json": task_tags_for_text(f"{caption}\n{description}\n{code}"),
                "required_env_json": sorted(set(ENV_RE.findall(code))),
                "required_params_json": [],
                "source_url": page.source_url,
                "source_anchor": source,
                "source_section_key": source_section_key_for_line(sections, start_line),
                "source_chunk_ids_json": [],
                "token_count": token_count(code),
                "quality_score": code_example_quality(code, metadata["document_role"]),
                "confidence": code_example_confidence(code, description, metadata["document_role"]),
                "metadata_json": {**metadata, "path": path, "start_line": start_line, "end_line": end_line},
            }
        )
    for index, line_match in enumerate(CLI_LINE_RE.finditer(markdown), start=1):
        command = line_match.group(0).strip().removeprefix("$").strip()
        if not command:
            continue
        start_line = markdown[: line_match.start()].count("\n") + 1
        heading_path = heading_path_before(lines, start_line)
        caption = heading_path[-1] if heading_path else "Command"
        source = source_anchor(page.canonical_url or page.source_url, heading_path, 10000 + index)
        output.append(
            {
                "example_key": stable_key("example-cli", path, str(start_line), command),
                "source_document_key": source_key,
                "path": path,
                "source_type": metadata["source_type"],
                "document_role": metadata["document_role"],
                "product": metadata["product"],
                "product_confidence": metadata["product_confidence"],
                "language": "bash",
                "title": caption,
                "description": nearby_description(lines, start_line),
                "caption": caption,
                "code": command,
                "imports_json": [],
                "symbols_json": [],
                "task_tags_json": task_tags_for_text(f"{caption}\n{command}"),
                "required_env_json": sorted(set(ENV_RE.findall(command))),
                "required_params_json": [],
                "source_url": page.source_url,
                "source_anchor": source,
                "source_section_key": source_section_key_for_line(sections, start_line),
                "source_chunk_ids_json": [],
                "token_count": token_count(command),
                "quality_score": code_example_quality(command, metadata["document_role"]),
                "confidence": 0.75,
                "metadata_json": {**metadata, "path": path, "start_line": start_line, "end_line": start_line},
            }
        )
    return output


def api_operation_for_page(page: NormalizedPage) -> dict[str, Any] | None:
    operations = api_operations_for_page(page)
    return operations[0] if operations else None


def api_operations_for_page(page: NormalizedPage) -> list[dict[str, Any]]:
    metadata = normalized_metadata(page)
    operation = metadata.get("operation") if isinstance(metadata.get("operation"), dict) else {}
    if metadata["source_type"] == "openapi" and operation:
        structured = openapi_api_operation_for_page(page, metadata, operation)
        return [structured] if structured else []
    return documented_api_operations_for_page(page, metadata)


def openapi_api_operation_for_page(page: NormalizedPage, metadata: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any] | None:
    metadata = normalized_metadata(page)
    endpoint = string_value(operation.get("endpoint"))
    method = string_value(operation.get("http_method") or operation.get("method")).upper()
    operation_id = string_value(operation.get("operation_id"))
    name = string_value(operation.get("operation_name") or operation_id or f"{method} {endpoint}")
    if not (endpoint or operation_id or name):
        return None
    content = clean_markdown(page.markdown)
    path = source_path_for_page(page)
    sections = source_sections_for_page(page)
    section = sections[0] if sections else {}
    section_key = str(section.get("section_key") or "")
    anchor = str(section.get("source_anchor") or page.source_url)
    return {
        "operation_key": stable_key("api", method, endpoint, operation_id, name),
        "source_document_key": source_document_key(page.canonical_url or page.source_url or path),
        "source_section_key": section_key,
        "product": metadata["product"],
        "product_confidence": metadata["product_confidence"],
        "operation_id": operation_id,
        "operation_name": name,
        "operation_kind": canonical_task_kind(operation.get("kind")),
        "http_method": method,
        "endpoint": endpoint,
        "route": endpoint,
        "tags_json": list_of_strings(metadata.get("tags")),
        "summary": first_prose(content, fallback=name),
        "description": content[:4000],
        "required_params_json": param_list(operation.get("required_params")),
        "optional_params_json": param_list(operation.get("optional_params")),
        "request_schema_json": jsonable(operation.get("request_schema")),
        "response_schema_json": jsonable(operation.get("response_schema")),
        "errors_json": error_list(content),
        "auth_requirements_json": jsonable(operation.get("auth_requirements")),
        "source_url": page.source_url,
        "source_anchor": anchor,
        "token_count": token_count(content),
        "quality_score": page.quality_score + 0.35,
        "confidence": 0.95,
        "metadata_json": {**metadata, "source_section_key": section_key},
    }


def documented_api_operations_for_page(page: NormalizedPage, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    if metadata["document_role"] not in {"api_reference", "guide", "readme", "example", "troubleshooting", "unknown"}:
        return []
    operations: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for section_index, section in enumerate(source_sections_for_page(page), start=1):
        content = str(section.get("content") or "")
        if not api_like_section(content, str(section.get("title") or ""), metadata["document_role"]):
            continue
        for index, candidate in enumerate(api_endpoint_candidates(content), start=1):
            method = candidate["method"]
            endpoint = candidate["endpoint"]
            dedupe_key = (method, endpoint, str(section.get("section_key") or ""))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            title = str(section.get("title") or f"{method} {endpoint}").strip()
            summary = first_prose(content, fallback=f"{method} {endpoint}")
            operations.append(
                {
                    "operation_key": stable_key("api-doc", source_path_for_page(page), str(section_index), str(index), method, endpoint),
                    "source_document_key": source_document_key(page.canonical_url or page.source_url or source_path_for_page(page)),
                    "source_section_key": str(section.get("section_key") or ""),
                    "product": metadata["product"],
                    "product_confidence": metadata["product_confidence"],
                    "operation_id": operation_id_from_title(title, method, endpoint),
                    "operation_name": title if title else f"{method} {endpoint}",
                    "operation_kind": operation_kind_from_text(f"{title}\n{content}", method),
                    "http_method": method,
                    "endpoint": endpoint,
                    "route": endpoint,
                    "tags_json": task_tags_for_text(f"{title}\n{content}"),
                    "summary": summary,
                    "description": content[:4000],
                    "required_params_json": params_from_text(content, required=True),
                    "optional_params_json": params_from_text(content, required=False),
                    "request_schema_json": schema_snippets_from_text(content, "request"),
                    "response_schema_json": schema_snippets_from_text(content, "response"),
                    "errors_json": error_list(content),
                    "auth_requirements_json": auth_requirements_from_text(content),
                    "source_url": page.source_url,
                    "source_anchor": str(section.get("source_anchor") or page.source_url),
                    "token_count": token_count(content),
                    "quality_score": page.quality_score + (0.25 if metadata["document_role"] == "api_reference" else 0.1),
                    "confidence": 0.78 if metadata["document_role"] == "api_reference" else 0.66,
                    "metadata_json": {**metadata, "extraction": "documented_api", "source_section_key": section.get("section_key")},
                }
            )
    return operations


def sdk_method_for_page(page: NormalizedPage) -> dict[str, Any] | None:
    methods = sdk_methods_for_page(page)
    return methods[0] if methods else None


def source_file_sdk_methods_for_page(page: NormalizedPage, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    if metadata["document_role"] not in {"sdk_source", "type_definition"}:
        return []
    language = metadata["language"]
    if language not in {"python", "typescript", "javascript", "go", "rust"}:
        return []
    markdown = clean_markdown(page.markdown)
    code_blocks = [
        match.group("code")
        for match in FENCE_RE.finditer(markdown)
        if canonical_language(match.group(2).strip()) in {language, ""} or not match.group(2).strip()
    ]
    if not code_blocks:
        return []
    code = "\n\n".join(code_blocks)
    path = source_path_for_page(page)
    generated = generated_source(path, code)
    sections = source_sections_for_page(page)
    section_key = str(sections[0].get("section_key") or "") if sections else ""
    source_anchor_value = str(sections[0].get("source_anchor") or page.source_url) if sections else page.source_url
    output: list[dict[str, Any]] = []
    for block in extracted_documented_blocks(code, language):
        symbol = string_value(block.get("name"))
        method = string_value(block.get("method_name") or symbol)
        sdk_class = string_value(block.get("class_name"))
        signature = string_value(block.get("signature"))
        if not public_sdk_method(symbol, sdk_class, method, path, generated):
            continue
        description = source_block_description(str(block.get("body") or ""), fallback=symbol)
        output.append(
            {
                "method_key": stable_key("sdk-ast", path, language, sdk_class, method, symbol, signature),
                "source_document_key": source_document_key(page.canonical_url or page.source_url or path),
                "source_section_key": section_key,
                "product": metadata["product"],
                "product_confidence": metadata["product_confidence"],
                "language": language,
                "import_path": string_value(block.get("import_path")),
                "module_path": path,
                "sdk_class": sdk_class,
                "sdk_method": method,
                "symbol_name": symbol,
                "signature": signature,
                "description": description,
                "required_params_json": param_list(block.get("required_params")),
                "optional_params_json": param_list(block.get("optional_params")),
                "return_type": string_value(block.get("return_type")),
                "errors_json": error_list(str(block.get("body") or "")),
                "source_url": page.source_url,
                "source_anchor": source_anchor_value,
                "source_chunk_ids_json": [],
                "public_api": True,
                "generated": generated,
                "quality_score": page.quality_score + (0.2 if not generated else -0.25),
                "confidence": 0.9 if not generated else 0.55,
                "metadata_json": {**metadata, "source_section_key": section_key, "source_origin": "ast", "operation_kind": infer_operation_kind(symbol, signature, str(block.get("body") or ""))},
            }
        )
    return output


def sdk_methods_for_page(page: NormalizedPage) -> list[dict[str, Any]]:
    metadata = normalized_metadata(page)
    methods: list[dict[str, Any]] = []
    methods.extend(source_file_sdk_methods_for_page(page, metadata))
    if metadata["document_role"] not in {"sdk_source", "type_definition"}:
        methods.extend(documented_sdk_methods_for_page(page, metadata))
        return dedupe_sdk_method_rows(methods)
    operation = metadata.get("operation") if isinstance(metadata.get("operation"), dict) else {}
    if not operation:
        methods.extend(documented_sdk_methods_for_page(page, metadata))
        return dedupe_sdk_method_rows(methods)
    method = string_value(operation.get("sdk_method"))
    sdk_class = string_value(operation.get("sdk_class"))
    symbol = string_value(operation.get("operation_name") or method or sdk_class)
    signature = string_value(operation.get("request_schema"))
    path = source_path_for_page(page)
    generated = generated_source(path, page.markdown)
    if not public_sdk_method(symbol, sdk_class, method, path, generated):
        methods.extend(documented_sdk_methods_for_page(page, metadata))
        return dedupe_sdk_method_rows(methods)
    content = clean_markdown(page.markdown)
    sections = source_sections_for_page(page)
    section = sections[0] if sections else {}
    section_key = str(section.get("section_key") or "")
    anchor = str(section.get("source_anchor") or page.source_url)
    methods.append(
        {
            "method_key": stable_key("sdk", metadata["language"], sdk_class, method, symbol, signature),
            "source_document_key": source_document_key(page.canonical_url or page.source_url or path),
            "source_section_key": section_key,
            "product": metadata["product"],
            "product_confidence": metadata["product_confidence"],
            "language": metadata["language"] or canonical_language(operation.get("language")),
            "import_path": string_value(operation.get("import_path")),
            "module_path": path,
            "sdk_class": sdk_class,
            "sdk_method": method,
            "symbol_name": symbol,
            "signature": signature,
            "description": first_prose(content, fallback=symbol),
            "required_params_json": param_list(operation.get("required_params")),
            "optional_params_json": param_list(operation.get("optional_params")),
            "return_type": string_value(operation.get("response_schema")),
            "errors_json": error_list(content),
            "source_url": page.source_url,
            "source_anchor": anchor,
            "source_chunk_ids_json": [],
            "public_api": True,
            "generated": generated,
            "quality_score": page.quality_score + (0.15 if not generated else -0.25),
            "confidence": 0.85 if not generated else 0.55,
            "metadata_json": {**metadata, "source_section_key": section_key, "source_origin": "metadata"},
        }
    )
    methods.extend(documented_sdk_methods_for_page(page, metadata))
    return dedupe_sdk_method_rows(methods)


def documented_sdk_methods_for_page(page: NormalizedPage, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    if metadata["document_role"] not in {"sdk_source", "type_definition", "api_reference", "guide", "readme", "example", "test", "unknown"}:
        return []
    path = source_path_for_page(page)
    generated = generated_source(path, page.markdown)
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    examples = code_examples_for_page(page)
    for example in examples:
        code = str(example.get("code") or "")
        for receiver, method, signature in sdk_call_candidates(code, language=str(example.get("language") or metadata["language"])):
            key = stable_key("sdk-doc-call", path, str(example.get("example_key")), receiver, method, signature)
            if key in seen:
                continue
            seen.add(key)
            if not public_sdk_method(method, receiver, method, path, generated):
                continue
            output.append(
                sdk_method_row_from_candidate(
                    page,
                    metadata,
                    key,
                    receiver,
                    method,
                    signature,
                    str(example.get("description") or example.get("caption") or ""),
                    str(example.get("source_anchor") or page.source_url),
                    str(example.get("source_section_key") or ""),
                    generated,
                    0.68,
                )
            )
    for section in source_sections_for_page(page):
        content = str(section.get("content") or "")
        for receiver, method, signature in sdk_call_candidates(content, language=metadata["language"]):
            key = stable_key("sdk-doc-section", path, str(section.get("section_key")), receiver, method, signature)
            if key in seen:
                continue
            seen.add(key)
            if not public_sdk_method(method, receiver, method, path, generated):
                continue
            output.append(
                sdk_method_row_from_candidate(
                    page,
                    metadata,
                    key,
                    receiver,
                    method,
                    signature,
                    first_prose(content, fallback=str(section.get("title") or method)),
                    str(section.get("source_anchor") or page.source_url),
                    str(section.get("section_key") or ""),
                    generated,
                    0.62,
                )
            )
    return output


def dedupe_sdk_method_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (
            str(row.get("sdk_class") or "").lower(),
            str(row.get("sdk_method") or row.get("symbol_name") or "").lower(),
            re.sub(r"\s+", " ", str(row.get("signature") or "")).strip().lower(),
        )
        current = best.get(key)
        if current is None or float(row.get("confidence") or 0) > float(current.get("confidence") or 0):
            best[key] = row
    return list(best.values())


def normalized_metadata(page: NormalizedPage) -> dict[str, Any]:
    metadata = dict(page.source_metadata or {})
    source_type = normalize_source_type(metadata.get("source_type") or page.source_type, page.source_url)
    document_role = normalize_document_role(metadata.get("document_role"), source_type, page.path or "", page.source_url, page.markdown)
    metadata["source_type"] = source_type
    metadata["document_role"] = document_role
    metadata.setdefault("product", "")
    try:
        metadata["product_confidence"] = float(metadata.get("product_confidence") or 0)
    except (TypeError, ValueError):
        metadata["product_confidence"] = 0.0
    metadata.setdefault("product_signals", [])
    metadata["language"] = canonical_language(str(metadata.get("language") or language_from_path(page.path or page.source_url) or ""))
    metadata["source_priority"] = int(metadata.get("source_priority") or page.source_priority or 50)
    return metadata


def api_like_section(content: str, title: str, document_role: str) -> bool:
    haystack = f"{title}\n{content}".lower()
    if api_endpoint_candidates(content):
        return True
    if document_role == "api_reference" and any(term in haystack for term in ("endpoint", "request", "response", "parameter", "curl")):
        return True
    return False


def api_endpoint_candidates(text: str) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for match in HTTP_ENDPOINT_RE.finditer(text):
        add_api_candidate(output, seen, match.group("method"), match.group("endpoint"))
    for match in FETCH_ENDPOINT_RE.finditer(text):
        body = match.group("body") or ""
        method_match = METHOD_OPTION_RE.search(body)
        method = method_match.group(1) if method_match else "GET"
        add_api_candidate(output, seen, method, match.group("endpoint"))
    for match in CURL_ENDPOINT_RE.finditer(text):
        args = re.sub(r"\\\n\s*", " ", match.group("args") or "")
        method_match = re.search(r"(?:-X|--request)\s+([A-Za-z]+)", args)
        url_match = re.search(r"(https?://[^\s'\"`<>]+|/[A-Za-z0-9_./:{}?&=%+-]+)", args)
        if url_match:
            add_api_candidate(output, seen, method_match.group(1) if method_match else "GET", url_match.group(1))
    return output[:50]


def add_api_candidate(output: list[dict[str, str]], seen: set[tuple[str, str]], method: str, endpoint: str) -> None:
    normalized_method = method.upper().strip()
    normalized_endpoint = normalize_endpoint(endpoint)
    if not normalized_method or not normalized_endpoint:
        return
    key = (normalized_method, normalized_endpoint)
    if key in seen:
        return
    seen.add(key)
    output.append({"method": normalized_method, "endpoint": normalized_endpoint})


def normalize_endpoint(value: str) -> str:
    endpoint = value.strip().strip("`'\".,)")
    parsed = urlparse(endpoint)
    if parsed.scheme and parsed.netloc:
        endpoint = parsed.path or "/"
        if parsed.query:
            endpoint += "?" + parsed.query
    if not endpoint.startswith("/"):
        return ""
    if endpoint in {"/", "//"}:
        return ""
    return endpoint[:500]


def operation_id_from_title(title: str, method: str, endpoint: str) -> str:
    text = re.sub(r"(?i)\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b", "", title).strip()
    text = text or f"{method.lower()} {endpoint}"
    words = re.findall(r"[A-Za-z0-9]+", text)
    if not words:
        return f"{method.lower()}_{endpoint.strip('/').replace('/', '_')}"
    first, *rest = words[:8]
    return first[:1].lower() + first[1:] + "".join(word[:1].upper() + word[1:] for word in rest)


def operation_kind_from_text(text: str, method: str) -> str:
    lowered = text.lower()
    if method == "POST" or re.search(r"\b(create|new|generate|submit|start)\b", lowered):
        return "create"
    if method == "GET" and re.search(r"\b(list|all|search)\b", lowered):
        return "list"
    if method == "GET":
        return "retrieve"
    if method in {"PUT", "PATCH"} or re.search(r"\b(update|edit|modify)\b", lowered):
        return "update"
    if method == "DELETE" or re.search(r"\b(delete|remove)\b", lowered):
        return "delete"
    if re.search(r"\b(upload|file|document|pdf|image|audio)\b", lowered):
        return "upload"
    if re.search(r"\b(stream|realtime|websocket|sse)\b", lowered):
        return "stream"
    if re.search(r"\b(auth|api key|token|credential)\b", lowered):
        return "setup_auth"
    return "operation"


def params_from_text(text: str, *, required: bool) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    table_rows = re.findall(r"(?m)^\|\s*`?([A-Za-z_][\w.-]*)`?\s*\|([^|\n]*)\|([^|\n]*)\|?([^|\n]*)", text)
    for name, col2, col3, col4 in table_rows:
        row_text = " ".join([col2, col3, col4])
        is_required = bool(re.search(r"\brequired\b", row_text, re.I)) and not re.search(r"\boptional\b", row_text, re.I)
        if is_required != required:
            continue
        add_param(output, seen, name, row_text, required)
    bullet_rows = re.findall(r"(?m)^\s*[-*]\s+`([A-Za-z_][\w.-]*)`(?:\s*\(([^)]*)\))?\s*[:\-]\s*(.+)$", text)
    for name, meta, description in bullet_rows:
        row_text = f"{meta or ''} {description}"
        is_required = bool(re.search(r"\brequired\b", row_text, re.I)) and not re.search(r"\boptional\b", row_text, re.I)
        if is_required != required:
            continue
        add_param(output, seen, name, row_text, required)
    return output[:100]


def add_param(output: list[dict[str, Any]], seen: set[str], name: str, description: str, required: bool) -> None:
    if name in seen:
        return
    seen.add(name)
    type_match = re.search(r"\b(string|number|integer|boolean|object|array|file|uuid|url)\b", description, re.I)
    output.append(
        {
            "name": name,
            "required": required,
            "type": type_match.group(1).lower() if type_match else "",
            "description": re.sub(r"\s+", " ", description).strip()[:500],
        }
    )


def schema_snippets_from_text(text: str, kind: str) -> dict[str, Any]:
    pattern = re.compile(rf"(?is)\b{kind}\b.*?(```[a-zA-Z0-9_-]*\n.*?\n```)")
    matches = [match.group(1)[:1500] for match in pattern.finditer(text)]
    return {"examples": matches[:5]} if matches else {}


def auth_requirements_from_text(text: str) -> list[dict[str, str]]:
    lowered = text.lower()
    output: list[dict[str, str]] = []
    if "authorization" in lowered or "bearer" in lowered:
        output.append({"type": "authorization_header"})
    if "api key" in lowered or ENV_RE.search(text):
        output.append({"type": "api_key"})
    return output


def sdk_call_candidates(text: str, *, language: str) -> list[tuple[str, str, str]]:
    output: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for match in SDK_DOTTED_CALL_RE.finditer(text):
        receiver = match.group("receiver")
        method = match.group("method")
        if receiver in {"console", "JSON", "Math", "Object", "Array", "String", "response", "res", "req"}:
            continue
        signature = dotted_signature(text, match.start(), receiver, method)
        add_sdk_candidate(output, seen, receiver, method, signature)
    for match in PY_DEF_RE.finditer(text):
        method = match.group("method")
        params = match.group("params")
        add_sdk_candidate(output, seen, "", method, f"def {method}({params})")
    if language in {"typescript", "javascript", ""}:
        for match in JS_EXPORT_RE.finditer(text):
            method = match.group("method")
            params = (match.group("params") or "").strip()
            add_sdk_candidate(output, seen, "", method, f"{method}({params})")
    return output[:80]


def add_sdk_candidate(output: list[tuple[str, str, str]], seen: set[tuple[str, str, str]], receiver: str, method: str, signature: str) -> None:
    if method.startswith("_") or method in INTERNAL_METHODS:
        return
    key = (receiver, method, signature)
    if key in seen:
        return
    seen.add(key)
    output.append(key)


def dotted_signature(text: str, start: int, receiver: str, method: str) -> str:
    snippet = text[start : start + 300]
    depth = 0
    end = 0
    for index, char in enumerate(snippet):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth <= 0:
                end = index + 1
                break
    value = snippet[:end] if end else f"{receiver}.{method}(...)"
    return re.sub(r"\s+", " ", value).strip()[:500]


def sdk_method_row_from_candidate(
    page: NormalizedPage,
    metadata: dict[str, Any],
    key: str,
    receiver: str,
    method: str,
    signature: str,
    description: str,
    source_anchor_value: str,
    source_section_key: str,
    generated: bool,
    confidence: float,
) -> dict[str, Any]:
    path = source_path_for_page(page)
    return {
        "method_key": key,
        "source_document_key": source_document_key(page.canonical_url or page.source_url or path),
        "source_section_key": source_section_key,
        "product": metadata["product"],
        "product_confidence": metadata["product_confidence"],
        "language": metadata["language"],
        "import_path": "",
        "module_path": path,
        "sdk_class": receiver,
        "sdk_method": method,
        "symbol_name": method,
        "signature": signature,
        "description": description[:1200],
        "required_params_json": params_from_signature(signature, required=True),
        "optional_params_json": params_from_signature(signature, required=False),
        "return_type": "",
        "errors_json": error_list(description),
        "source_url": page.source_url,
        "source_anchor": source_anchor_value,
        "source_chunk_ids_json": [],
        "public_api": True,
        "generated": generated,
        "quality_score": page.quality_score + (0.1 if not generated else -0.25),
        "confidence": confidence if not generated else min(confidence, 0.45),
        "metadata_json": {**metadata, "extraction": "documented_sdk", "source_section_key": source_section_key},
    }


def canonicalize_code_examples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate exact code examples while preserving broad citation evidence."""

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            product_scope(row),
            str(row.get("language") or "").lower(),
            normalized_surface_text(str(row.get("code") or "")),
        )
        if not key[2]:
            continue
        grouped.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    for group in grouped.values():
        ordered = sorted(group, key=surface_rank)
        canonical = dict(ordered[0])
        canonical["example_key"] = stable_key(
            "example-canonical",
            product_scope(canonical),
            str(canonical.get("language") or ""),
            str(canonical.get("code") or ""),
        )
        metadata = merged_metadata(ordered, base=canonical.get("metadata_json"), surface="code_example")
        canonical["metadata_json"] = metadata
        canonical["source_anchor"] = str(canonical.get("source_anchor") or first_non_empty(row.get("source_anchor") for row in ordered))
        canonical["source_url"] = str(canonical.get("source_url") or first_non_empty(row.get("source_url") for row in ordered))
        canonical["source_chunk_ids_json"] = merged_list_values(row.get("source_chunk_ids_json") for row in ordered)
        canonical["task_tags_json"] = merged_list_values(row.get("task_tags_json") for row in ordered)
        canonical["imports_json"] = merged_list_values(row.get("imports_json") for row in ordered)
        canonical["symbols_json"] = merged_list_values(row.get("symbols_json") for row in ordered)
        canonical["required_env_json"] = merged_list_values(row.get("required_env_json") for row in ordered)
        canonical["quality_score"] = max_float(row.get("quality_score") for row in ordered)
        canonical["confidence"] = min(1.0, max_float(row.get("confidence") for row in ordered) + evidence_bonus(ordered))
        output.append(canonical)
    return sorted(output, key=lambda row: (surface_rank(row), str(row.get("example_key") or "")))


def merge_api_operations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    loose: list[dict[str, Any]] = []
    for row in rows:
        key = api_operation_identity(row)
        if not key:
            loose.append(row)
            continue
        grouped.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    for key, group in grouped.items():
        ordered = sorted(group, key=surface_rank)
        canonical = dict(ordered[0])
        product, method, endpoint, operation_id = key
        canonical["operation_key"] = stable_key("api-canonical", product, method, endpoint, operation_id)
        canonical["http_method"] = method
        canonical["endpoint"] = endpoint
        canonical["route"] = endpoint
        canonical["operation_id"] = str(canonical.get("operation_id") or operation_id)
        canonical["operation_name"] = best_text(ordered, "operation_name") or f"{method} {endpoint}".strip() or operation_id
        canonical["summary"] = best_text(ordered, "summary")
        canonical["description"] = best_text(ordered, "description", longest=True)
        canonical["operation_kind"] = best_task_kind(ordered)
        canonical["tags_json"] = merged_list_values(row.get("tags_json") for row in ordered)
        canonical["required_params_json"] = merge_param_lists(row.get("required_params_json") for row in ordered)
        canonical["optional_params_json"] = merge_param_lists(row.get("optional_params_json") for row in ordered)
        canonical["request_schema_json"] = best_json_object(ordered, "request_schema_json")
        canonical["response_schema_json"] = best_json_object(ordered, "response_schema_json")
        canonical["errors_json"] = merge_dict_lists(row.get("errors_json") for row in ordered)
        canonical["auth_requirements_json"] = merge_dict_lists(row.get("auth_requirements_json") for row in ordered)
        canonical["source_chunk_ids_json"] = merged_list_values(row.get("source_chunk_ids_json") for row in ordered)
        canonical["source_anchor"] = str(first_non_empty(row.get("source_anchor") for row in ordered) or "")
        canonical["source_url"] = str(first_non_empty(row.get("source_url") for row in ordered) or "")
        canonical["quality_score"] = max_float(row.get("quality_score") for row in ordered)
        canonical["confidence"] = min(1.0, max_float(row.get("confidence") for row in ordered) + evidence_bonus(ordered))
        canonical["token_count"] = token_count(
            "\n".join(
                str(canonical.get(key_name) or "")
                for key_name in ("operation_name", "summary", "description", "http_method", "endpoint")
            )
        )
        canonical["metadata_json"] = {
            **merged_metadata(ordered, base=canonical.get("metadata_json"), surface="api_operation"),
            "source_origin": merged_source_origin(ordered, openapi_label="openapi", docs_label="docs_inferred"),
        }
        output.append(canonical)

    output.extend(dedupe_rows(loose, "operation_key"))
    return sorted(output, key=lambda row: (surface_rank(row), str(row.get("operation_key") or "")))


def merge_sdk_methods(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    loose: list[dict[str, Any]] = []
    for row in rows:
        key = sdk_method_identity(row)
        if not key:
            loose.append(row)
            continue
        grouped.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    for key, group in grouped.items():
        ordered = sorted(group, key=surface_rank)
        canonical = dict(ordered[0])
        product, language, sdk_class, sdk_method, symbol = key
        canonical["method_key"] = stable_key("sdk-canonical", product, language, sdk_class, sdk_method, symbol)
        canonical["language"] = language
        canonical["sdk_class"] = best_text(ordered, "sdk_class") or sdk_class
        canonical["sdk_method"] = best_text(ordered, "sdk_method") or sdk_method
        canonical["symbol_name"] = best_text(ordered, "symbol_name") or symbol or sdk_method or sdk_class
        canonical["signature"] = best_text(ordered, "signature")
        canonical["description"] = best_text(ordered, "description", longest=True)
        canonical["import_path"] = best_text(ordered, "import_path")
        canonical["module_path"] = best_text(ordered, "module_path")
        canonical["required_params_json"] = merge_param_lists(row.get("required_params_json") for row in ordered)
        canonical["optional_params_json"] = merge_param_lists(row.get("optional_params_json") for row in ordered)
        canonical["return_type"] = best_text(ordered, "return_type")
        canonical["errors_json"] = merge_dict_lists(row.get("errors_json") for row in ordered)
        canonical["source_chunk_ids_json"] = merged_list_values(row.get("source_chunk_ids_json") for row in ordered)
        canonical["source_anchor"] = str(first_non_empty(row.get("source_anchor") for row in ordered) or "")
        canonical["source_url"] = str(first_non_empty(row.get("source_url") for row in ordered) or "")
        canonical["public_api"] = any(bool(row.get("public_api", True)) for row in ordered)
        canonical["generated"] = all(bool(row.get("generated", False)) for row in ordered)
        canonical["quality_score"] = max_float(row.get("quality_score") for row in ordered)
        canonical["confidence"] = min(1.0, max_float(row.get("confidence") for row in ordered) + evidence_bonus(ordered))
        canonical["metadata_json"] = {
            **merged_metadata(ordered, base=canonical.get("metadata_json"), surface="sdk_method"),
            "source_origin": merged_source_origin(ordered, openapi_label="ast", docs_label="docs_inferred"),
        }
        output.append(canonical)

    output.extend(dedupe_sdk_method_rows(loose))
    return sorted(output, key=lambda row: (surface_rank(row), str(row.get("method_key") or "")))


def api_operation_identity(row: dict[str, Any]) -> tuple[str, str, str, str] | None:
    method = str(row.get("http_method") or "").upper().strip()
    endpoint = normalize_endpoint(str(row.get("endpoint") or row.get("route") or ""))
    operation_id = str(row.get("operation_id") or "").strip().lower()
    if method and endpoint:
        return (product_scope(row), method, endpoint, "")
    if operation_id:
        return (product_scope(row), "", "", operation_id)
    return None


def sdk_method_identity(row: dict[str, Any]) -> tuple[str, str, str, str, str] | None:
    language = str(row.get("language") or "").lower()
    sdk_class = str(row.get("sdk_class") or "").strip().lower()
    sdk_method = str(row.get("sdk_method") or "").strip().lower()
    symbol = str(row.get("symbol_name") or "").strip().lower()
    if not (sdk_method or symbol or sdk_class):
        return None
    method_identity = sdk_method or symbol or sdk_class
    symbol_identity = symbol if symbol and symbol == method_identity else method_identity
    return (product_scope(row), language, "", method_identity, symbol_identity)


def product_scope(row: dict[str, Any]) -> str:
    try:
        confidence = float(row.get("product_confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    return str(row.get("product") or "").strip().lower() if confidence >= 0.55 else ""


def surface_rank(row: dict[str, Any]) -> tuple[int, float, float, int, str]:
    metadata = row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}
    source_type = str(row.get("source_type") or metadata.get("source_type") or "").lower()
    origin = str(metadata.get("source_origin") or metadata.get("extraction") or "").lower()
    role = str(row.get("document_role") or metadata.get("document_role") or "").lower()
    source_priority = int(metadata.get("source_priority") or row.get("source_priority") or 50)
    if source_type == "openapi" or origin == "openapi":
        source_rank = 0
    elif origin == "ast" or role in {"sdk_source", "type_definition"}:
        source_rank = 1
    elif role in {"example", "test", "readme", "guide"}:
        source_rank = 2
    elif role == "api_reference":
        source_rank = 3
    else:
        source_rank = 5
    return (
        source_rank,
        -float(row.get("confidence") or 0),
        -float(row.get("quality_score") or 0),
        source_priority,
        str(row.get("source_anchor") or row.get("source_url") or ""),
    )
