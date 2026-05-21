from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from oz_crawler.chunks import markdown_blocks, section_blocks, source_anchor, source_document_key, source_path_for_page
from oz_crawler.content_types import block_content_type
from oz_crawler.normalize import NormalizedPage, clean_markdown
from oz_crawler.token_counting import token_count

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
    write_jsonl(target / "_source_sections.jsonl", dedupe_rows(sections, "section_key"))
    write_jsonl(target / "_code_examples.jsonl", dedupe_rows(examples, "example_key"))
    write_jsonl(target / "_api_operations.jsonl", dedupe_rows(api_operations, "operation_key"))
    write_jsonl(target / "_sdk_methods.jsonl", dedupe_rows(sdk_methods, "method_key"))


def source_sections_for_page(page: NormalizedPage) -> list[dict[str, Any]]:
    path = source_path_for_page(page)
    source_key = source_document_key(page.canonical_url or page.source_url or path)
    metadata = normalized_metadata(page)
    blocks = markdown_blocks(clean_markdown(page.markdown))
    output: list[dict[str, Any]] = []
    for index, section in enumerate(section_blocks(blocks), start=1):
        content = "\n\n".join(block[0] for block in section).strip()
        if not content:
            continue
        heading_path = next((block[3] for block in reversed(section) if block[3]), [])
        start_line = min(block[1] for block in section)
        end_line = max(block[2] for block in section)
        title = heading_path[-1] if heading_path else page.title or path.rsplit("/", 1)[-1]
        output.append(
            {
                "section_key": stable_key("section", path, str(start_line), title, content[:160]),
                "source_document_key": source_key,
                "path": path,
                "title": title,
                "heading_path": heading_path,
                "source_url": page.source_url,
                "source_anchor": source_anchor(page.canonical_url or page.source_url, heading_path, index),
                "document_role": metadata["document_role"],
                "content_type": block_content_type(page.source_url, content, page.content_type),
                "product": metadata["product"],
                "product_confidence": metadata["product_confidence"],
                "language": metadata["language"],
                "start_line": start_line,
                "end_line": end_line,
                "content": content,
                "token_count": token_count(content),
                "quality_score": page.quality_score,
                "metadata_json": metadata,
            }
        )
    return output


def code_examples_for_page(page: NormalizedPage) -> list[dict[str, Any]]:
    path = source_path_for_page(page)
    source_key = source_document_key(page.canonical_url or page.source_url or path)
    metadata = normalized_metadata(page)
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
    return {
        "operation_key": stable_key("api", method, endpoint, operation_id, name),
        "source_document_key": source_document_key(page.canonical_url or page.source_url or path),
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
        "source_anchor": page.source_url,
        "token_count": token_count(content),
        "quality_score": page.quality_score + 0.35,
        "confidence": 0.95,
        "metadata_json": metadata,
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


def sdk_methods_for_page(page: NormalizedPage) -> list[dict[str, Any]]:
    metadata = normalized_metadata(page)
    methods: list[dict[str, Any]] = []
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
        return documented_sdk_methods_for_page(page, metadata)
    content = clean_markdown(page.markdown)
    methods.append(
        {
        "method_key": stable_key("sdk", metadata["language"], sdk_class, method, symbol, signature),
        "source_document_key": source_document_key(page.canonical_url or page.source_url or path),
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
        "source_anchor": page.source_url,
        "source_chunk_ids_json": [],
        "public_api": True,
        "generated": generated,
        "quality_score": page.quality_score + (0.15 if not generated else -0.25),
        "confidence": 0.85 if not generated else 0.55,
        "metadata_json": metadata,
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
            output.append(sdk_method_row_from_candidate(page, metadata, key, receiver, method, signature, str(example.get("description") or example.get("caption") or ""), str(example.get("source_anchor") or page.source_url), generated, 0.68))
    for section in source_sections_for_page(page):
        content = str(section.get("content") or "")
        for receiver, method, signature in sdk_call_candidates(content, language=metadata["language"]):
            key = stable_key("sdk-doc-section", path, str(section.get("section_key")), receiver, method, signature)
            if key in seen:
                continue
            seen.add(key)
            if not public_sdk_method(method, receiver, method, path, generated):
                continue
            output.append(sdk_method_row_from_candidate(page, metadata, key, receiver, method, signature, first_prose(content, fallback=str(section.get("title") or method)), str(section.get("source_anchor") or page.source_url), generated, 0.62))
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
    source_type = normalize_source_type(metadata.get("source_type") or metadata.get("source_kind") or page.source_kind, page.source_url)
    document_role = normalize_document_role(metadata.get("document_role") or metadata.get("source_role"), source_type, page.path or "", page.source_url, page.markdown)
    metadata["source_type"] = source_type
    metadata["source_kind"] = source_type
    metadata["document_role"] = document_role
    metadata.pop("source_role", None)
    metadata.setdefault("product", "")
    try:
        metadata["product_confidence"] = float(metadata.get("product_confidence") or 0)
    except (TypeError, ValueError):
        metadata["product_confidence"] = 0.0
    metadata.setdefault("product_signals", [])
    metadata["language"] = canonical_language(str(metadata.get("language") or language_from_path(page.path or page.source_url) or ""))
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
    generated: bool,
    confidence: float,
) -> dict[str, Any]:
    path = source_path_for_page(page)
    return {
        "method_key": key,
        "source_document_key": source_document_key(page.canonical_url or page.source_url or path),
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
        "metadata_json": {**metadata, "extraction": "documented_sdk"},
    }


def params_from_signature(signature: str, *, required: bool) -> list[dict[str, Any]]:
    match = re.search(r"\((?P<params>[^)]*)\)", signature)
    if not match:
        return []
    output: list[dict[str, Any]] = []
    for raw in match.group("params").split(","):
        value = raw.strip()
        if not value or value in {"self", "cls", "..."}:
            continue
        name = re.split(r"[:=]", value, maxsplit=1)[0].strip().lstrip("*")
        if not re.match(r"^[A-Za-z_][\w.-]*$", name):
            continue
        is_optional = "=" in value or name.endswith("?")
        if is_optional == required:
            continue
        output.append({"name": name.rstrip("?"), "required": required, "description": value[:300]})
    return output[:50]


def normalize_source_type(value: Any, source_url: str) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in {"llms", "llms_full", "llms_txt"}:
        return "llms_txt"
    if raw in {"github", "source_code", "type_defs", "type_definition"}:
        parsed = urlparse(source_url)
        return "github" if "github" in parsed.netloc.lower() else "website_url"
    if raw in {"markdown", "website", "official_docs", "docs"}:
        return "website_url"
    if raw == "openapi":
        return "openapi"
    parsed = urlparse(source_url)
    lower = source_url.lower()
    if lower.endswith(("/llms.txt", "/llms-full.txt")):
        return "llms_txt"
    if re.search(r"(openapi|swagger).*\.(json|ya?ml)$", parsed.path.lower()):
        return "openapi"
    if "github.com" in parsed.netloc.lower() or "raw.githubusercontent.com" in parsed.netloc.lower():
        return "github"
    return raw if raw in VALID_SOURCE_TYPES else "website_url"


def normalize_document_role(value: Any, source_type: str, path: str, source_url: str, text: str) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw == "cookbook":
        raw = "example"
    if raw == "api_spec":
        raw = "api_reference"
    if raw in DOCUMENT_ROLES:
        return raw
    haystack = f"{path} {source_url}".lower()
    name = haystack.rsplit("/", 1)[-1]
    if re.search(r"(^|/)(readme|index)\.(md|mdx|txt)$", haystack) or name.startswith("readme"):
        return "readme"
    if re.search(r"(^|/)(examples?|samples?|cookbook|recipes?)(/|$)", haystack):
        return "example"
    if re.search(r"(^|/)(tests?|specs?)(/|$)|[_-](test|spec)\.", haystack):
        return "test"
    if re.search(r"(^|/)(api-reference|reference|api)(/|$)", haystack) or source_type == "openapi":
        return "api_reference"
    if path.endswith((".d.ts", ".pyi")) or "type definitions" in text[:1000].lower():
        return "type_definition"
    if re.search(r"(^|/)(src|lib|packages|pkg)(/|$)", haystack) and path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")):
        return "sdk_source"
    if "changelog" in haystack or "release" in haystack:
        return "changelog"
    if any(term in haystack for term in ("troubleshooting", "errors", "error-codes")):
        return "troubleshooting"
    if re.search(r"(\.env|config|configuration|package\.json|tsconfig|docker-compose)", haystack):
        return "config"
    if re.search(r"(^|/)(docs?|guides?|learn)(/|$)", haystack):
        return "guide"
    return "unknown"


def reject_code_example(code: str, language: str) -> bool:
    stripped = code.strip()
    if not stripped:
        return True
    if token_count(stripped) < 6:
        return True
    if language in {"json", "yaml", "yml"} and token_count(stripped) > 500:
        return True
    lowered = stripped.lower()
    if "request_factory" in lowered or "response_deserialize" in lowered or "with_http_info" in lowered:
        return True
    return False


def code_example_quality(code: str, document_role: str) -> float:
    score = 1.0
    lowered = code.lower()
    if document_role in {"example", "readme", "guide", "test"}:
        score += 0.35
    if IMPORT_RE.search(code):
        score += 0.2
    if re.search(r"\b\w*Client\s*\(", code) or "fetch(" in code or "curl " in lowered:
        score += 0.25
    if ENV_RE.search(code) or "api key" in lowered or "authorization" in lowered:
        score += 0.1
    if "todo" in lowered:
        score -= 0.2
    return max(0.1, min(score, 2.0))


def code_example_confidence(code: str, description: str, document_role: str) -> float:
    score = 0.45
    if description:
        score += 0.15
    if IMPORT_RE.search(code):
        score += 0.15
    if document_role in {"example", "readme", "guide", "test"}:
        score += 0.15
    return min(score, 0.95)


def public_sdk_method(symbol: str, sdk_class: str, method: str, path: str, generated: bool) -> bool:
    values = {symbol, sdk_class, method}
    lowered = {value.lower() for value in values if value}
    if not symbol or symbol.startswith("_") or method.startswith("_"):
        return False
    if lowered & INTERNAL_METHODS:
        return False
    if sdk_class in INTERNAL_CLASSES and method in {"", sdk_class, "__init__", "get_default", "set_default"}:
        return False
    if generated and (sdk_class in INTERNAL_CLASSES or method in INTERNAL_METHODS):
        return False
    if re.search(r"(^|/)(internal|generated|gen|model|models)(/|$)", path.lower()) and not method:
        return False
    return True


def generated_source(path: str, text: str) -> bool:
    haystack = f"{path}\n{text[:1000]}".lower()
    return any(term in haystack for term in ("generated by", "auto-generated", "autogenerated", "/generated/", "/gen/", "openapi generator"))


def imports_for_code(code: str) -> list[str]:
    return [match.group(0).strip() for match in IMPORT_RE.finditer(code)][:20]


def symbols_for_code(code: str) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in IDENT_RE.findall(code):
        if len(value) < 2 or value.lower() in {"const", "let", "var", "return", "async", "await", "import", "from"}:
            continue
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output[:80]


def task_tags_for_text(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, pattern in (
        ("setup_auth", r"\b(install|setup|quickstart|api key|auth|credential)\b"),
        ("create", r"\b(create|new|add|build)\b"),
        ("retrieve", r"\b(get|fetch|retrieve|read|details)\b"),
        ("list", r"\b(list|available|all|search)\b"),
        ("update", r"\b(update|edit|patch|modify)\b"),
        ("delete", r"\b(delete|remove|destroy)\b"),
        ("upload", r"\b(upload|file|pdf|document|image|audio)\b"),
        ("stream", r"\b(stream|realtime|websocket|sse|chunk)\b"),
        ("config", r"\b(config|env|host|base url|settings)\b"),
        ("error_handling", r"\b(error|exception|retry|failed|failure)\b"),
        ("testing", r"\b(test|mock|pytest|jest|spec)\b"),
    ):
        if re.search(pattern, lowered):
            tags.append(tag)
    return tags


def heading_path_before(lines: list[str], line_number: int) -> list[str]:
    headings: list[str] = []
    for line in lines[: max(line_number - 1, 0)]:
        match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if not match:
            continue
        level = len(match.group(1))
        title = re.sub(r"\s+#*$", "", match.group(2)).strip()
        headings = headings[: level - 1]
        headings.append(title)
    return headings


def source_section_key_for_line(sections: list[dict[str, Any]], line_number: int) -> str:
    for section in sections:
        if int(section.get("start_line") or 0) <= line_number <= int(section.get("end_line") or 0):
            return str(section.get("section_key") or "")
    return ""


def nearby_description(lines: list[str], line_number: int) -> str:
    selected: list[str] = []
    for line in reversed(lines[max(0, line_number - 8) : max(0, line_number - 1)]):
        stripped = line.strip()
        if not stripped:
            if selected:
                break
            continue
        if stripped.startswith("```") or re.match(r"^#{1,6}\s+", stripped):
            break
        selected.append(stripped.strip("- "))
        if len(selected) >= 2:
            break
    return " ".join(reversed(selected))[:500]


def first_prose(text: str, *, fallback: str = "") -> str:
    for line in text.splitlines():
        stripped = line.strip().strip("#- ")
        if stripped and not stripped.startswith("```") and len(stripped) > 8:
            return stripped[:900]
    return fallback


def canonical_language(value: Any) -> str:
    raw = str(value or "").strip().lower().removeprefix("language-")
    aliases = {"py": "python", "python3": "python", "ts": "typescript", "tsx": "typescript", "js": "javascript", "jsx": "javascript", "shell": "bash", "sh": "bash", "yml": "yaml"}
    return aliases.get(raw, raw)


def language_from_path(path: str) -> str:
    lower = path.lower()
    for suffix, language in (
        (".py", "python"),
        (".pyi", "python"),
        (".ts", "typescript"),
        (".tsx", "typescript"),
        (".js", "javascript"),
        (".jsx", "javascript"),
        (".go", "go"),
        (".rs", "rust"),
        (".json", "json"),
        (".yaml", "yaml"),
        (".yml", "yaml"),
        (".toml", "toml"),
    ):
        if lower.endswith(suffix):
            return language
    return ""


def canonical_task_kind(value: Any) -> str:
    raw = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
    return raw if raw in {"setup_auth", "quickstart", "create", "retrieve", "list", "update", "delete", "upload", "stream", "config", "error_handling", "testing", "production", "schema_reference", "concept", "operation", "auth", "test"} else "operation"


def param_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    output: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict) and item.get("name"):
            output.append({key: item[key] for key in item if key in {"name", "type", "schema_type", "in", "description", "required", "schema"}})
    return output[:100]


def error_list(text: str) -> list[dict[str, str]]:
    output = []
    seen = set()
    for match in re.finditer(r"\b(?:ERR_[A-Z0-9_]+|[A-Z][A-Za-z]+Error|HTTP\s+[45]\d{2}|[45]\d{2})\b", text):
        value = match.group(0)
        if value not in seen:
            seen.add(value)
            output.append({"name": value})
    return output[:25]


def jsonable(value: Any) -> Any:
    if value in (None, ""):
        return {}
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def list_of_strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def string_value(value: Any) -> str:
    return str(value or "").strip()


def stable_key(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:32]
    return f"{prefix}:{digest}"


def dedupe_rows(rows: list[dict[str, Any]], key_name: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        key = str(row.get(key_name) or "")
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
