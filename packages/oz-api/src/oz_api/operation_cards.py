from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, replace
from typing import Any

from oz_api.llm_recipes import maybe_enrich_recipe
from oz_api.token_counting import token_count

FENCE_RE = re.compile(r"(?ms)^\s*(`{3,}|~{3,})([A-Za-z0-9_+.-]*)\n(?P<code>.*?)(?:^\s*\1\s*$)")
IDENT_RE = re.compile(r"\b[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)?\b")


@dataclass(frozen=True)
class AgentOperation:
    operation_key: str
    product: str
    operation_name: str
    operation_kind: str
    sdk_class: str
    sdk_method: str
    import_path: str
    language: str
    endpoint: str
    http_method: str
    route: str
    required_params: list[dict[str, Any]]
    optional_params: list[dict[str, Any]]
    request_schema: Any
    response_schema: Any
    errors: list[dict[str, Any]]
    auth_requirements: Any
    source_urls: list[str]
    source_chunk_ids: list[int]
    confidence: float
    quality_score: float
    content: str
    metadata_json: dict[str, Any]


@dataclass(frozen=True)
class AgentOperationExample:
    example_key: str
    operation_key: str | None
    product: str
    title: str
    language: str
    content: str
    source_url: str
    source_chunk_ids: list[int]
    token_count: int
    quality_score: float
    metadata_json: dict[str, Any]


@dataclass(frozen=True)
class AgentRecipe:
    recipe_key: str
    operation_key: str | None
    product: str
    title: str
    task_kind: str
    language: str
    content: str
    code: str | None
    info: str
    source_urls: list[str]
    source_chunk_ids: list[int]
    confidence: float
    quality_score: float
    token_count: int
    metadata_json: dict[str, Any]


def build_agent_operations(rows: list[dict[str, Any]]) -> list[AgentOperation]:
    grouped: dict[str, list[AgentOperation]] = {}
    for row in rows:
        operation = operation_from_row(row)
        if operation is None:
            continue
        grouped.setdefault(operation.operation_key, []).append(operation)
    output: list[AgentOperation] = []
    for key, group in grouped.items():
        output.append(merge_operations(key, group))
    return sorted(output, key=lambda item: (-item.quality_score, item.operation_kind, item.operation_name))


def build_agent_operation_examples(rows: list[dict[str, Any]], operations: list[AgentOperation]) -> list[AgentOperationExample]:
    output: list[AgentOperationExample] = []
    seen: set[str] = set()
    for row in rows:
        for index, block in enumerate(code_blocks(str(row.get("content") or ""))):
            if low_value_code(block["code"]):
                continue
            operation_key = best_operation_key_for_example(row, block["code"], operations)
            key = stable_key("example", str(row.get("path") or ""), str(row.get("start_line") or ""), str(index), block["code"][:300])
            if key in seen:
                continue
            seen.add(key)
            metadata = row_metadata(row)
            output.append(
                AgentOperationExample(
                    example_key=key,
                    operation_key=operation_key,
                    product=trusted_product(metadata),
                    title=title_for_example(row, block, operation_key, operations),
                    language=canonical_language(block["language"] or metadata.get("language") or ""),
                    content=f"```{block['language'] or ''}\n{block['code'].strip()}\n```",
                    source_url=source_ref(row),
                    source_chunk_ids=[int(row["id"])] if row.get("id") else [],
                    token_count=token_count(block["code"]),
                    quality_score=example_quality(row, block["code"]),
                    metadata_json=metadata,
                )
            )
    return sorted(output, key=lambda item: (-item.quality_score, item.title))[: max_examples_per_version()]


def build_agent_recipes(
    rows: list[dict[str, Any]],
    operations: list[AgentOperation],
    examples: list[AgentOperationExample],
) -> list[AgentRecipe]:
    examples_by_operation: dict[str | None, list[AgentOperationExample]] = {}
    for example in examples:
        examples_by_operation.setdefault(example.operation_key, []).append(example)
    recipes: list[AgentRecipe] = []
    for operation in operations:
        linked = sorted(examples_by_operation.get(operation.operation_key, []), key=lambda item: -item.quality_score)
        recipes.append(recipe_for_operation(operation, linked[:3]))
    for example in examples_by_operation.get(None, [])[: max_orphan_examples_per_version()]:
        recipes.append(recipe_for_example(example))
    return sorted(enrich_recipes(recipes, rows), key=lambda item: (-item.quality_score, item.title))


def operation_from_row(row: dict[str, Any]) -> AgentOperation | None:
    metadata = row_metadata(row)
    operation = metadata.get("operation") if isinstance(metadata.get("operation"), dict) else {}
    content = str(row.get("content") or "")
    content_type = str(row.get("content_type") or "")
    source_role = str(metadata.get("source_role") or metadata.get("source_type") or "")
    if not operation and content_type not in {"api_reference", "types", "code_example"} and source_role not in {"api_spec", "sdk_source"}:
        return None
    symbols = list_of_strings(row.get("symbols"))
    name = clean_operation_name(
        string_value(operation.get("operation_name")) or string_value(operation.get("operation_id")) or first_symbol(symbols) or heading_title(row)
    )
    endpoint = string_value(operation.get("endpoint"))
    http_method = string_value(operation.get("http_method") or operation.get("method")).upper()
    sdk_class = string_value(operation.get("sdk_class"))
    sdk_method = clean_operation_name(string_value(operation.get("sdk_method")) or method_from_content(content) or (name if not endpoint else ""))
    blocks = code_blocks(content)
    language = canonical_language(string_value(operation.get("language")) or (blocks[0]["language"] if blocks else ""))
    kind = canonical_kind(string_value(operation.get("kind")) or infer_kind(name, content, http_method))
    if not name or low_signal_operation(name, endpoint, sdk_method, content):
        return None
    key = operation_key(
        product=trusted_product(metadata),
        name=name,
        kind=kind,
        endpoint=endpoint,
        http_method=http_method,
        sdk_class=sdk_class,
        sdk_method=sdk_method,
        path=str(row.get("path") or ""),
    )
    required = param_list(operation.get("required_params"))
    optional = param_list(operation.get("optional_params"))
    source_urls = unique_strings([source_ref(row), str(row.get("source_url") or "")])
    row_id = int(row["id"]) if row.get("id") else None
    summary = operation_summary(
        name=name,
        kind=kind,
        endpoint=endpoint,
        http_method=http_method,
        sdk_class=sdk_class,
        sdk_method=sdk_method,
        required=required,
        optional=optional,
        content=content,
    )
    return AgentOperation(
        operation_key=key,
        product=trusted_product(metadata),
        operation_name=name,
        operation_kind=kind,
        sdk_class=sdk_class,
        sdk_method=sdk_method,
        import_path=string_value(operation.get("import_path")),
        language=language,
        endpoint=endpoint,
        http_method=http_method,
        route=endpoint,
        required_params=required,
        optional_params=optional,
        request_schema=jsonable(operation.get("request_schema")),
        response_schema=jsonable(operation.get("response_schema")),
        errors=error_list(content),
        auth_requirements=jsonable(operation.get("auth_requirements")),
        source_urls=source_urls,
        source_chunk_ids=[row_id] if row_id else [],
        confidence=operation_confidence(row, operation),
        quality_score=float(row.get("quality_score") or 1.0),
        content=summary,
        metadata_json=metadata,
    )


def merge_operations(key: str, group: list[AgentOperation]) -> AgentOperation:
    best = max(group, key=lambda item: (item.confidence, item.quality_score, len(item.content)))
    return replace(
        best,
        operation_key=key,
        required_params=merge_param_lists(item.required_params for item in group),
        optional_params=merge_param_lists(item.optional_params for item in group),
        errors=merge_dict_lists(item.errors for item in group),
        source_urls=unique_strings(source for item in group for source in item.source_urls),
        source_chunk_ids=unique_ints(chunk for item in group for chunk in item.source_chunk_ids),
        confidence=max(item.confidence for item in group),
        quality_score=max(item.quality_score for item in group),
        content="\n\n".join(unique_strings(item.content for item in group if item.content))[:6000],
        metadata_json=merge_metadata(*(item.metadata_json for item in group)),
    )


def recipe_for_operation(operation: AgentOperation, examples: list[AgentOperationExample]) -> AgentRecipe:
    code = best_example_code(examples)
    info_lines = [
        f"Operation: {operation.operation_name}",
        f"Kind: {operation.operation_kind}",
    ]
    if operation.sdk_class or operation.sdk_method:
        info_lines.append("SDK: " + ".".join(part for part in (operation.sdk_class, operation.sdk_method) if part))
    if operation.http_method or operation.endpoint:
        info_lines.append(f"Endpoint: {' '.join(part for part in (operation.http_method, operation.endpoint) if part)}")
    if operation.required_params:
        info_lines.append("Required params: " + ", ".join(param["name"] for param in operation.required_params if param.get("name")))
    if operation.optional_params:
        info_lines.append("Optional params: " + ", ".join(param["name"] for param in operation.optional_params[:12] if param.get("name")))
    if operation.auth_requirements not in ({}, [], None, ""):
        info_lines.append("Auth: documented in source spec.")
    if operation.errors:
        info_lines.append("Errors: " + ", ".join(item.get("name") or item.get("status") or "documented error" for item in operation.errors[:5]))
    content_parts = [operation.content, "\n".join(info_lines)]
    if code:
        content_parts.append(f"```{examples[0].language if examples else operation.language}\n{code.strip()}\n```")
    title = recipe_title(operation)
    content = "\n\n".join(part for part in content_parts if part.strip())
    return AgentRecipe(
        recipe_key=stable_key("recipe", operation.operation_key),
        operation_key=operation.operation_key,
        product=operation.product,
        title=title,
        task_kind=operation.operation_kind,
        language=examples[0].language if examples else operation.language,
        content=content,
        code=code,
        info="\n".join(info_lines),
        source_urls=unique_strings([*operation.source_urls, *(example.source_url for example in examples)]),
        source_chunk_ids=unique_ints([*operation.source_chunk_ids, *(chunk for example in examples for chunk in example.source_chunk_ids)]),
        confidence=min(1.0, operation.confidence + (0.15 if code else 0)),
        quality_score=max([operation.quality_score, *(example.quality_score for example in examples)] or [1.0]),
        token_count=token_count(content),
        metadata_json={"operation_key": operation.operation_key, "source": "deterministic_operation_recipe"},
    )


def recipe_for_example(example: AgentOperationExample) -> AgentRecipe:
    content = f"{example.title}\n\n{example.content}"
    return AgentRecipe(
        recipe_key=stable_key("recipe-example", example.example_key),
        operation_key=None,
        product=example.product,
        title=example.title,
        task_kind="usage_recipe",
        language=example.language,
        content=content,
        code=strip_fence(example.content),
        info="Runnable example extracted from source-backed documentation.",
        source_urls=[example.source_url] if example.source_url else [],
        source_chunk_ids=example.source_chunk_ids,
        confidence=0.65,
        quality_score=example.quality_score,
        token_count=token_count(content),
        metadata_json={"example_key": example.example_key, "source": "deterministic_example_recipe"},
    )


def evidence_for_recipe(recipe: AgentRecipe, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = set(recipe.source_chunk_ids)
    output = []
    for row in rows:
        if row.get("id") in ids:
            output.append(
                {
                    "id": row.get("id"),
                    "path": row.get("path"),
                    "source_url": row.get("source_url"),
                    "content": str(row.get("content") or "")[:6000],
                    "metadata_json": row_metadata(row),
                }
            )
    return output[:8]


def operation_terms(operations: list[AgentOperation]) -> dict[str, set[str]]:
    output = {}
    for operation in operations:
        terms = {
            compact(operation.operation_name),
            compact(operation.sdk_class),
            compact(operation.sdk_method),
            compact(operation.endpoint),
            compact(operation.operation_kind),
        }
        for param in [*operation.required_params, *operation.optional_params]:
            terms.add(compact(str(param.get("name") or "")))
        output[operation.operation_key] = {term for term in terms if len(term) >= 3}
    return output


def best_operation_key_for_text(text: str, operations_by_terms: dict[str, set[str]]) -> str | None:
    compact_text = compact(text)
    scored = []
    for key, terms in operations_by_terms.items():
        hits = sum(1 for term in terms if term and term in compact_text)
        if hits:
            scored.append((hits, key))
    if not scored:
        return None
    return sorted(scored, reverse=True)[0][1]


def best_operation_key_for_example(row: dict[str, Any], text: str, operations: list[AgentOperation]) -> str | None:
    compact_text = compact("\n".join([text, str(row.get("path") or ""), str(row.get("source_title") or "")]))
    metadata = row_metadata(row)
    product = trusted_product(metadata)
    row_source = base_source_ref(source_ref(row))
    row_chunk_id = int(row["id"]) if row.get("id") else None
    scored: list[tuple[float, str]] = []
    for operation in operations:
        score = 0.0
        if row_chunk_id and row_chunk_id in operation.source_chunk_ids:
            score += 35.0
        if product and product == operation.product:
            score += 10.0
        if row_source and any(base_source_ref(source) == row_source for source in operation.source_urls):
            score += 18.0
        for value, weight in (
            (operation.sdk_class, 14.0),
            (operation.sdk_method, 18.0),
            (operation.operation_name, 16.0),
            (operation.endpoint, 18.0),
            (operation.import_path, 12.0),
            (operation.operation_kind, 6.0),
        ):
            term = compact(value)
            if len(term) >= 3 and term in compact_text:
                score += weight
        for param in [*operation.required_params, *operation.optional_params]:
            term = compact(str(param.get("name") or ""))
            if len(term) >= 3 and term in compact_text:
                score += 3.0
        if score >= 12.0:
            scored.append((score, operation.operation_key))
    if not scored:
        return best_operation_key_for_text(text, operation_terms(operations))
    return sorted(scored, reverse=True)[0][1]


def enrich_recipes(recipes: list[AgentRecipe], rows: list[dict[str, Any]]) -> list[AgentRecipe]:
    limit = llm_enrichment_limit()
    if limit <= 0:
        return recipes
    ordered = sorted(recipes, key=lambda item: (item.confidence, item.quality_score, bool(item.code)), reverse=True)
    enrich_keys = {recipe.recipe_key for recipe in ordered[:limit]}
    output = []
    for recipe in recipes:
        if recipe.recipe_key in enrich_keys:
            output.append(maybe_enrich_recipe(recipe, evidence_for_recipe(recipe, rows)))
        else:
            output.append(recipe)
    return output


def code_blocks(content: str) -> list[dict[str, str]]:
    return [{"language": match.group(2).strip(), "code": match.group("code").strip()} for match in FENCE_RE.finditer(content)]


def low_value_code(code: str) -> bool:
    stripped = code.strip()
    if token_count(stripped) < 20:
        return True
    lowered = stripped.lower()
    if lowered.count("\n") < 2 and not any(term in lowered for term in ("import", "client", "fetch", "curl", "http")):
        return True
    return False


def trusted_product(metadata: dict[str, Any]) -> str:
    try:
        confidence = float(metadata.get("product_confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0
    product = str(metadata.get("product") or "").strip()
    return product if product and confidence >= 0.5 else ""


def title_for_example(row: dict[str, Any], block: dict[str, str], operation_key: str | None, operations: list[AgentOperation]) -> str:
    if operation_key:
        operation = next((item for item in operations if item.operation_key == operation_key), None)
        if operation:
            return f"Example: {operation.operation_name}"
    heading = list_of_strings(row.get("heading_path"))
    if heading:
        return "Example: " + heading[-1]
    return "Example: " + str(row.get("path") or "usage")


def example_quality(row: dict[str, Any], code: str) -> float:
    score = float(row.get("quality_score") or 1.0)
    lowered = code.lower()
    if re.search(r"\b(from\s+[\w.]+\s+import|import\s+[\w.]+)", code):
        score += 0.25
    if re.search(r"\b\w*Client\s*\(", code):
        score += 0.25
    if any(term in lowered for term in ("api_key", "token", "authorization", "bearer")):
        score += 0.1
    if any(term in lowered for term in ("todo", "your_", "placeholder")):
        score -= 0.1
    return max(0.0, min(score, 2.0))


def best_example_code(examples: list[AgentOperationExample]) -> str | None:
    if not examples:
        return None
    return strip_fence(examples[0].content)


def strip_fence(content: str) -> str:
    match = FENCE_RE.search(content)
    return match.group("code").strip() if match else content.strip()


def recipe_title(operation: AgentOperation) -> str:
    subject = operation.operation_name
    if operation.operation_kind and operation.operation_kind != "operation":
        return f"{operation.operation_kind.replace('_', ' ').title()}: {subject}"
    return f"Use {subject}"


def operation_summary(**kwargs: Any) -> str:
    lines = [f"# {kwargs['name']}"]
    if kwargs["kind"]:
        lines.append(f"Task kind: {kwargs['kind']}")
    if kwargs["http_method"] or kwargs["endpoint"]:
        lines.append(f"HTTP: {' '.join(part for part in (kwargs['http_method'], kwargs['endpoint']) if part)}")
    if kwargs["sdk_class"] or kwargs["sdk_method"]:
        lines.append("SDK: " + ".".join(part for part in (kwargs["sdk_class"], kwargs["sdk_method"]) if part))
    if kwargs["required"]:
        lines.append("Required parameters: " + ", ".join(param["name"] for param in kwargs["required"] if param.get("name")))
    if kwargs["optional"]:
        lines.append("Optional parameters: " + ", ".join(param["name"] for param in kwargs["optional"][:12] if param.get("name")))
    prose = first_prose(kwargs["content"])
    if prose:
        lines.append(prose)
    return "\n".join(line for line in lines if line.strip())


def first_prose(content: str) -> str:
    text = FENCE_RE.sub("", content)
    lines = [line.strip("# -") for line in text.splitlines() if line.strip() and not line.strip().startswith("|")]
    return " ".join(lines[:4])[:800]


def row_metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata_json")
    return value if isinstance(value, dict) else {}


def source_ref(row: dict[str, Any]) -> str:
    return str(row.get("source_anchor") or row.get("source_url") or row.get("path") or "").strip()


def base_source_ref(value: str) -> str:
    return value.split("#", 1)[0].strip()


def heading_title(row: dict[str, Any]) -> str:
    heading = list_of_strings(row.get("heading_path"))
    if heading:
        return heading[-1]
    return str(row.get("source_title") or row.get("path") or "").rsplit("/", 1)[-1].replace(".md", "")


def first_symbol(symbols: list[str]) -> str:
    for symbol in symbols:
        if symbol and len(symbol) >= 2:
            return symbol
    return ""


def method_from_content(content: str) -> str:
    for ident in IDENT_RE.findall(content[:2000]):
        if keep_method(ident):
            return ident
    return ""


def keep_method(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"client", "request", "response", "string", "number", "boolean", "object", "array"}:
        return False
    return any(term in lowered for term in ("create", "delete", "update", "list", "get", "upload", "stream", "send", "fetch"))


def infer_kind(name: str, content: str, http_method: str) -> str:
    haystack = f"{name} {content[:1200]}".lower()
    if http_method == "GET":
        return "list" if re.search(r"\b(list|search|all)\b", haystack) else "retrieve"
    if http_method == "POST":
        if re.search(r"\b(upload|file|document|pdf|audio|image)\b", haystack):
            return "upload"
        if re.search(r"\b(stream|websocket|sse)\b", haystack):
            return "stream"
        return "create"
    if http_method in {"PUT", "PATCH"}:
        return "update"
    if http_method == "DELETE":
        return "delete"
    for kind, pattern in (
        ("delete", r"\b(delete|remove|destroy)\b"),
        ("update", r"\b(update|patch|modify|edit)\b"),
        ("create", r"\b(create|new|add|insert)\b"),
        ("upload", r"\b(upload|file|document|pdf|audio|image)\b"),
        ("stream", r"\b(stream|websocket|sse)\b"),
        ("list", r"\b(list|search|all)\b"),
        ("retrieve", r"\b(get|fetch|retrieve|read)\b"),
        ("auth", r"\b(auth|api key|token|credential)\b"),
        ("config", r"\b(config|settings|options)\b"),
        ("test", r"\b(test|mock|pytest|spec)\b"),
        ("production", r"\b(retry|timeout|logging|observability|deploy|production)\b"),
    ):
        if re.search(pattern, haystack):
            return kind
    return "operation"


def canonical_kind(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return normalized if normalized in {"create", "update", "delete", "list", "retrieve", "upload", "stream", "auth", "config", "test", "production", "operation", "usage_recipe"} else "operation"


def canonical_language(value: str) -> str:
    lowered = value.lower().strip()
    aliases = {"py": "python", "python3": "python", "ts": "typescript", "tsx": "typescript", "js": "javascript", "jsx": "javascript", "sh": "bash", "shell": "bash"}
    return aliases.get(lowered, lowered)


def operation_key(**kwargs: str) -> str:
    identity = "|".join(str(kwargs.get(key) or "") for key in ("product", "http_method", "endpoint", "sdk_class", "sdk_method", "kind", "name", "path"))
    return stable_key("operation", identity)


def stable_key(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:32]
    return f"{prefix}:{digest}"


def param_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    output = []
    for item in value:
        if isinstance(item, dict) and item.get("name"):
            output.append({key: item[key] for key in item if key in {"name", "type", "schema_type", "in", "description", "required"}})
    return output[:80]


def jsonable(value: Any) -> Any:
    if value in (None, ""):
        return {}
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def error_list(content: str) -> list[dict[str, Any]]:
    output = []
    for match in re.finditer(r"\b(?:ERR_[A-Z0-9_]+|[A-Z][A-Za-z]+Error|[45]\d\d)\b", content):
        output.append({"name": match.group(0)})
    return merge_dict_lists([output])[:20]


def operation_confidence(row: dict[str, Any], operation: dict[str, Any]) -> float:
    score = 0.35
    if operation:
        score += 0.3
    if operation.get("endpoint") or operation.get("sdk_method"):
        score += 0.2
    if code_blocks(str(row.get("content") or "")):
        score += 0.1
    if trusted_product(row_metadata(row)):
        score += 0.05
    return min(score, 1.0)


def low_signal_operation(name: str, endpoint: str, sdk_method: str, content: str) -> bool:
    if endpoint or sdk_method:
        return False
    compact_name = compact(name)
    if len(compact_name) < 3:
        return True
    return token_count(content) < 20


def merge_param_lists(values: Any) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for items in values:
        for item in items:
            key = compact(str(item.get("name") or ""))
            if key and key not in seen:
                seen.add(key)
                output.append(item)
    return output


def merge_dict_lists(values: Any) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for items in values:
        for item in items:
            key = compact(json.dumps(item, sort_keys=True))
            if key and key not in seen:
                seen.add(key)
                output.append(item)
    return output


def merge_metadata(*values: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for value in values:
        output.update(value)
    return output


def unique_strings(values: Any) -> list[str]:
    output = []
    seen: set[str] = set()
    for value in values:
        item = str(value or "").strip()
        if item and item not in seen:
            seen.add(item)
            output.append(item)
    return output[:80]


def unique_ints(values: Any) -> list[int]:
    output = []
    seen: set[int] = set()
    for value in values:
        try:
            item = int(value)
        except (TypeError, ValueError):
            continue
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output[:200]


def list_of_strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def string_value(value: Any) -> str:
    return str(value or "").strip()


def clean_operation_name(value: str) -> str:
    value = re.sub(r"[*`]+", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value[:180]


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def max_examples_per_version() -> int:
    try:
        return max(1, int(os.environ.get("OZ_AGENT_MAX_EXAMPLES_PER_VERSION", "1500")))
    except ValueError:
        return 1500


def max_orphan_examples_per_version() -> int:
    try:
        return max(0, int(os.environ.get("OZ_AGENT_MAX_ORPHAN_EXAMPLES_PER_VERSION", "250")))
    except ValueError:
        return 250


def llm_enrichment_limit() -> int:
    try:
        return max(0, int(os.environ.get("OZ_RECIPE_LLM_MAX_PER_VERSION", "25")))
    except ValueError:
        return 25
