from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from oz_crawler.token_counting import token_count

ENV_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}(?:API_KEY|TOKEN|SECRET|KEY|HOST|URL)\b")
IMPORT_RE = re.compile(r"(?m)^\s*(?:from\s+[\w.]+\s+import\s+[\w.*, ]+|import\s+[\w., {}*]+|const\s+.*?=\s*require\([^)]+\))")
IDENT_RE = re.compile(r"\b[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)?\b")
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

def evidence_bonus(rows: list[dict[str, Any]]) -> float:
    evidence_types = {
        str((row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}).get("source_origin") or row.get("source_type") or "")
        for row in rows
    }
    return min(0.12, 0.03 * max(0, len(rows) - 1) + 0.02 * max(0, len(evidence_types) - 1))


def merged_metadata(rows: list[dict[str, Any]], *, base: Any, surface: str) -> dict[str, Any]:
    output = dict(base) if isinstance(base, dict) else {}
    output.pop("source_type", None)
    output["surface"] = surface
    output["source_evidence"] = [surface_evidence(row) for row in rows]
    output["evidence_count"] = len(rows)
    output["source_types"] = sorted(
        {
            source_type
            for row in rows
            for source_type in [str(row.get("source_type") or surface_metadata(row).get("source_type") or "")]
            if source_type
        }
    )
    return output


def surface_evidence(row: dict[str, Any]) -> dict[str, Any]:
    metadata = surface_metadata(row)
    return {
        key: value
        for key, value in {
            "source_document_key": row.get("source_document_key"),
            "source_section_key": row.get("source_section_key") or metadata.get("source_section_key"),
            "source_url": row.get("source_url"),
            "source_anchor": row.get("source_anchor"),
            "source_type": row.get("source_type") or metadata.get("source_type"),
            "document_role": row.get("document_role") or metadata.get("document_role"),
            "source_origin": metadata.get("source_origin") or metadata.get("extraction") or row.get("source_type"),
            "confidence": row.get("confidence"),
        }.items()
        if value not in (None, "", [], {})
    }


def merged_source_origin(rows: list[dict[str, Any]], *, openapi_label: str, docs_label: str) -> str:
    origins = {source_origin_for_row(row) for row in rows}
    if len(rows) > 1 and any(origin == openapi_label for origin in origins) and any(origin in {docs_label, "documented_api", "documented_sdk"} for origin in origins):
        return "mixed"
    if any(origin == openapi_label for origin in origins):
        return openapi_label
    if any(origin == "ast" for origin in origins):
        return "ast"
    return docs_label


def source_origin_for_row(row: dict[str, Any]) -> str:
    metadata = surface_metadata(row)
    origin = str(metadata.get("source_origin") or metadata.get("extraction") or "").lower()
    if origin:
        if origin == "documented_sdk" and str(metadata.get("document_role") or row.get("document_role") or "").lower() in {"sdk_source", "type_definition"}:
            return "ast"
        return origin
    source_type = str(row.get("source_type") or metadata.get("source_type") or "").lower()
    if source_type == "openapi":
        return "openapi"
    if source_type == "github" and str(metadata.get("document_role") or row.get("document_role") or "").lower() in {"sdk_source", "type_definition"}:
        return "ast"
    return source_type


def best_text(rows: list[dict[str, Any]], key: str, *, longest: bool = False) -> str:
    candidates = [str(row.get(key) or "").strip() for row in rows if str(row.get(key) or "").strip()]
    if not candidates:
        return ""
    return max(candidates, key=len) if longest else candidates[0]


def best_task_kind(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        kind = canonical_task_kind(row.get("operation_kind"))
        if kind not in {"operation", "concept"}:
            return kind
    return canonical_task_kind(rows[0].get("operation_kind") if rows else "")


def first_non_empty(values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return ""


def max_float(values: Any) -> float:
    numbers: list[float] = []
    for value in values:
        try:
            numbers.append(float(value or 0))
        except (TypeError, ValueError):
            continue
    return max(numbers, default=0.0)


def merged_list_values(values: Any) -> list[Any]:
    output: list[Any] = []
    seen: set[str] = set()
    for value in values:
        items = value if isinstance(value, list) else ([] if value in (None, "") else [value])
        for item in items:
            key = json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
            if not key or key in seen:
                continue
            seen.add(key)
            output.append(item)
    return output


def merge_dict_lists(values: Any) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict):
                continue
            key = str(item.get("name") or item.get("status") or item.get("type") or json.dumps(item, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            output.append(item)
    return output


def merge_param_lists(values: Any) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for value in values:
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            name = str(item["name"])
            current = by_name.get(name)
            if current is None or len(str(item.get("description") or "")) > len(str(current.get("description") or "")):
                by_name[name] = dict(item)
    return list(by_name.values())[:100]


def best_json_object(rows: list[dict[str, Any]], key: str) -> Any:
    for row in rows:
        value = row.get(key)
        if value not in (None, "", [], {}):
            return value
    return {}


def normalized_surface_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def surface_metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata_json")
    return metadata if isinstance(metadata, dict) else {}


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
    if raw in VALID_SOURCE_TYPES:
        return raw
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


def source_block_description(text: str, *, fallback: str = "") -> str:
    lines: list[str] = []
    in_docstring = False
    for raw in text.splitlines()[:40]:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith(("/**", "*", "///", "//")):
            cleaned = re.sub(r"^/?\*+/?\s?|^///?\s?", "", stripped).strip(" */")
            if cleaned and not cleaned.startswith("@"):
                lines.append(cleaned)
            continue
        if stripped.startswith(('"""', "'''")):
            in_docstring = not in_docstring or stripped.count(stripped[:3]) == 1
            cleaned = stripped.strip("\"'")
            if cleaned:
                lines.append(cleaned)
            continue
        if in_docstring:
            cleaned = stripped.strip("\"'")
            if cleaned:
                lines.append(cleaned)
            continue
        if lines:
            break
    return " ".join(lines)[:900] or fallback


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
