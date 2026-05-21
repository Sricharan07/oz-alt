from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from oz_api.llm_recipes import maybe_enrich_recipe
from oz_crawler.token_counting import token_count

TASK_KINDS = {
    "setup_auth",
    "quickstart",
    "create",
    "retrieve",
    "list",
    "update",
    "delete",
    "upload",
    "stream",
    "config",
    "error_handling",
    "testing",
    "production",
    "schema_reference",
    "concept",
    "operation",
}


def build_agent_recipes_from_surfaces(
    *,
    code_examples: list[dict[str, Any]],
    api_operations: list[dict[str, Any]],
    sdk_methods: list[dict[str, Any]],
    source_sections: list[dict[str, Any]],
    code_example_ids: dict[str, int],
    api_operation_ids: dict[str, int],
    sdk_method_ids: dict[str, int],
    source_section_ids: dict[str, int],
) -> list[dict[str, Any]]:
    recipes: list[dict[str, Any]] = []
    recipes.extend(
        compiled_recipes_from_evidence(
            code_examples=code_examples,
            api_operations=api_operations,
            sdk_methods=sdk_methods,
            source_sections=source_sections,
            code_example_ids=code_example_ids,
            api_operation_ids=api_operation_ids,
            sdk_method_ids=sdk_method_ids,
            source_section_ids=source_section_ids,
        )
    )
    for example in sorted(code_examples, key=lambda row: (-float(row.get("quality_score") or 1), -float(row.get("confidence") or 0))):
        recipes.append(recipe_from_code_example(example, code_example_ids))
    for operation in sorted(api_operations, key=lambda row: (-float(row.get("quality_score") or 1), str(row.get("operation_name") or ""))):
        recipes.append(recipe_from_api_operation(operation, api_operation_ids))
    for method in sorted(sdk_methods, key=lambda row: (-float(row.get("quality_score") or 1), str(row.get("symbol_name") or ""))):
        recipes.append(recipe_from_sdk_method(method, sdk_method_ids))
    for section in sorted(source_sections, key=lambda row: (-float(row.get("quality_score") or 1), int(row.get("start_line") or 1)))[: max_section_recipe_count()]:
        if section_recipe_candidate(section):
            recipes.append(recipe_from_source_section(section, source_section_ids))
    return dedupe_recipes(enrich_recipes(recipes, code_examples, api_operations, sdk_methods, source_sections))


def compiled_recipes_from_evidence(
    *,
    code_examples: list[dict[str, Any]],
    api_operations: list[dict[str, Any]],
    sdk_methods: list[dict[str, Any]],
    source_sections: list[dict[str, Any]],
    code_example_ids: dict[str, int],
    api_operation_ids: dict[str, int],
    sdk_method_ids: dict[str, int],
    source_section_ids: dict[str, int],
) -> list[dict[str, Any]]:
    recipes: list[dict[str, Any]] = []
    section_by_key = {str(row.get("section_key") or ""): row for row in source_sections if row.get("section_key")}
    for example in sorted(code_examples, key=lambda row: (-float(row.get("quality_score") or 1), -float(row.get("confidence") or 0))):
        example_key = str(example.get("example_key") or "")
        if not example_key or not code_example_ids.get(example_key):
            continue
        matched_operations = matching_api_operations(example, api_operations)[:3]
        matched_methods = matching_sdk_methods(example, sdk_methods)[:6]
        section_keys = evidence_section_keys([example, *matched_operations, *matched_methods])
        sections = [section_by_key[key] for key in section_keys if key in section_by_key][:4]
        if not (matched_operations or matched_methods or sections):
            continue

        evidence_rows = [example, *matched_operations, *matched_methods, *sections]
        operation_ids = [api_operation_ids[str(row.get("operation_key"))] for row in matched_operations if api_operation_ids.get(str(row.get("operation_key")))]
        method_ids = [sdk_method_ids[str(row.get("method_key"))] for row in matched_methods if sdk_method_ids.get(str(row.get("method_key")))]
        section_ids = [source_section_ids[str(row.get("section_key"))] for row in sections if source_section_ids.get(str(row.get("section_key")))]
        source_urls = sorted({url for row in evidence_rows for url in evidence_urls(row)})
        title = compiled_recipe_title(example, matched_operations, matched_methods)
        summary = str(example.get("description") or example.get("caption") or title).strip()[:900]
        info = compiled_recipe_info(matched_operations, matched_methods, sections)
        task = compiled_task_kind(example, matched_operations, matched_methods)
        required_params = merge_recipe_params([*matched_operations, *matched_methods, example])
        required_env = sorted({env for row in [example, *sections] for env in list_of_strings(row.get("required_env_json"))})
        confidence = recipe_confidence(evidence_rows)
        code = str(example.get("code") or "").strip()
        recipes.append(
            {
                "recipe_key": stable_key("recipe-compiled", example_key, operation_ids, method_ids, section_ids),
                "product": str(example.get("product") or first_value(matched_operations, matched_methods, sections, key="product") or ""),
                "product_confidence": max_float([example.get("product_confidence"), *(row.get("product_confidence") for row in evidence_rows)]),
                "title": title,
                "task_kind": task,
                "language": str(example.get("language") or first_value(matched_methods, key="language") or ""),
                "summary": summary,
                "code": code,
                "info": info,
                "required_env_json": required_env,
                "required_params_json": required_params,
                "source_api_operation_ids_json": operation_ids,
                "source_sdk_method_ids_json": method_ids,
                "source_code_example_ids_json": [code_example_ids[example_key]],
                "source_section_ids_json": section_ids,
                "source_chunk_ids_json": list_of_ints(example.get("source_chunk_ids_json")),
                "source_urls_json": source_urls,
                "evidence_hash": evidence_hash(code, info, source_urls, operation_ids, method_ids, section_ids),
                "llm_model": "",
                "llm_enriched": False,
                "confidence": confidence,
                "quality_score": max_float([row.get("quality_score") for row in evidence_rows]),
                "token_count": token_count("\n".join(part for part in (summary, code, info) if part)),
                "metadata_json": {
                    "surface": "compiled_recipe",
                    "evidence_count": len(evidence_rows),
                    "source_evidence": [surface_evidence(row) for row in evidence_rows],
                },
            }
        )
    return recipes


def recipe_from_code_example(row: dict[str, Any], ids: dict[str, int]) -> dict[str, Any]:
    key = str(row.get("example_key") or stable_key("example", row.get("source_anchor"), row.get("code")))
    task = primary_task(row.get("task_tags_json")) or task_from_text(f"{row.get('title')} {row.get('description')} {row.get('code')}")
    summary = str(row.get("description") or row.get("caption") or row.get("title") or "Source-backed code example").strip()
    source_url = str(row.get("source_anchor") or row.get("source_url") or "")
    code = str(row.get("code") or "").strip()
    return {
        "recipe_key": stable_key("recipe-example", key),
        "product": str(row.get("product") or ""),
        "product_confidence": float(row.get("product_confidence") or 0),
        "title": str(row.get("title") or "Use documented example"),
        "task_kind": task,
        "language": str(row.get("language") or ""),
        "summary": summary[:900],
        "code": code,
        "info": example_info(row),
        "required_env_json": list_of_strings(row.get("required_env_json")),
        "required_params_json": list_of_dicts(row.get("required_params_json")),
        "source_api_operation_ids_json": [],
        "source_sdk_method_ids_json": [],
        "source_code_example_ids_json": [ids[key]] if ids.get(key) else [],
        "source_section_ids_json": [],
        "source_chunk_ids_json": list_of_ints(row.get("source_chunk_ids_json")),
        "source_urls_json": [source_url] if source_url else [],
        "evidence_hash": evidence_hash(code, summary, source_url),
        "llm_model": "",
        "llm_enriched": False,
        "confidence": min(1.0, float(row.get("confidence") or 0.6) + 0.05),
        "quality_score": float(row.get("quality_score") or 1.0),
        "token_count": token_count("\n".join(part for part in (summary, code) if part)),
        "metadata_json": metadata(row, source="code_example"),
    }


def recipe_from_api_operation(row: dict[str, Any], ids: dict[str, int]) -> dict[str, Any]:
    key = str(row.get("operation_key") or stable_key("api", row.get("http_method"), row.get("endpoint")))
    method = str(row.get("http_method") or "").strip()
    endpoint = str(row.get("endpoint") or "").strip()
    title = str(row.get("operation_name") or "API operation")
    info = operation_info(row)
    source_url = str(row.get("source_anchor") or row.get("source_url") or "")
    return {
        "recipe_key": stable_key("recipe-api", key),
        "product": str(row.get("product") or ""),
        "product_confidence": float(row.get("product_confidence") or 0),
        "title": title,
        "task_kind": canonical_task(row.get("operation_kind")),
        "language": "",
        "summary": str(row.get("summary") or row.get("description") or f"{method} {endpoint}").strip()[:900],
        "code": None,
        "info": info,
        "required_env_json": [],
        "required_params_json": list_of_dicts(row.get("required_params_json")),
        "source_api_operation_ids_json": [ids[key]] if ids.get(key) else [],
        "source_sdk_method_ids_json": [],
        "source_code_example_ids_json": [],
        "source_section_ids_json": [],
        "source_chunk_ids_json": [],
        "source_urls_json": [source_url] if source_url else [],
        "evidence_hash": evidence_hash(title, info, source_url),
        "llm_model": "",
        "llm_enriched": False,
        "confidence": float(row.get("confidence") or 0.85),
        "quality_score": float(row.get("quality_score") or 1.0),
        "token_count": token_count("\n".join([title, info])),
        "metadata_json": metadata(row, source="api_operation"),
    }


def recipe_from_sdk_method(row: dict[str, Any], ids: dict[str, int]) -> dict[str, Any]:
    key = str(row.get("method_key") or stable_key("sdk", row.get("symbol_name"), row.get("signature")))
    title = str(row.get("symbol_name") or row.get("sdk_method") or "SDK method")
    info = sdk_info(row)
    source_url = str(row.get("source_anchor") or row.get("source_url") or "")
    return {
        "recipe_key": stable_key("recipe-sdk", key),
        "product": str(row.get("product") or ""),
        "product_confidence": float(row.get("product_confidence") or 0),
        "title": title,
        "task_kind": task_from_text(f"{title} {row.get('signature')} {row.get('description')}"),
        "language": str(row.get("language") or ""),
        "summary": str(row.get("description") or row.get("signature") or title).strip()[:900],
        "code": None,
        "info": info,
        "required_env_json": [],
        "required_params_json": list_of_dicts(row.get("required_params_json")),
        "source_api_operation_ids_json": [],
        "source_sdk_method_ids_json": [ids[key]] if ids.get(key) else [],
        "source_code_example_ids_json": [],
        "source_section_ids_json": [],
        "source_chunk_ids_json": list_of_ints(row.get("source_chunk_ids_json")),
        "source_urls_json": [source_url] if source_url else [],
        "evidence_hash": evidence_hash(title, info, source_url),
        "llm_model": "",
        "llm_enriched": False,
        "confidence": float(row.get("confidence") or 0.75),
        "quality_score": float(row.get("quality_score") or 1.0),
        "token_count": token_count("\n".join([title, info])),
        "metadata_json": metadata(row, source="sdk_method"),
    }


def recipe_from_source_section(row: dict[str, Any], ids: dict[str, int]) -> dict[str, Any]:
    key = str(row.get("section_key") or stable_key("section", row.get("path"), row.get("title")))
    source_url = str(row.get("source_anchor") or row.get("source_url") or "")
    content = str(row.get("content") or "")
    return {
        "recipe_key": stable_key("recipe-section", key),
        "product": str(row.get("product") or ""),
        "product_confidence": float(row.get("product_confidence") or 0),
        "title": str(row.get("title") or "Documentation section"),
        "task_kind": task_from_text(content),
        "language": str(row.get("language") or ""),
        "summary": first_sentences(content),
        "code": None,
        "info": content[:1800],
        "required_env_json": [],
        "required_params_json": [],
        "source_api_operation_ids_json": [],
        "source_sdk_method_ids_json": [],
        "source_code_example_ids_json": [],
        "source_section_ids_json": [ids[key]] if ids.get(key) else [],
        "source_chunk_ids_json": [],
        "source_urls_json": [source_url] if source_url else [],
        "evidence_hash": evidence_hash(content, source_url),
        "llm_model": "",
        "llm_enriched": False,
        "confidence": 0.45,
        "quality_score": float(row.get("quality_score") or 1.0),
        "token_count": token_count(content),
        "metadata_json": metadata(row, source="source_section"),
    }


def enrich_recipes(
    recipes: list[dict[str, Any]],
    code_examples: list[dict[str, Any]],
    api_operations: list[dict[str, Any]],
    sdk_methods: list[dict[str, Any]],
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    limit = llm_limit()
    if limit <= 0:
        return recipes
    evidence = [*code_examples, *api_operations, *sdk_methods, *sections]
    enriched: list[dict[str, Any]] = []
    selected = {row["recipe_key"] for row in sorted(recipes, key=lambda item: (float(item.get("confidence") or 0), float(item.get("quality_score") or 0), bool(item.get("code"))), reverse=True)[:limit]}
    for recipe in recipes:
        if recipe["recipe_key"] not in selected:
            enriched.append(recipe)
            continue
        candidate = RecipeAdapter(recipe)
        result = maybe_enrich_recipe(candidate, evidence_for_recipe(recipe, evidence))
        enriched.append(result.data if isinstance(result, RecipeAdapter) else recipe)
    return enriched


def validate_agent_recipes(
    recipes: list[dict[str, Any]],
    *,
    code_example_ids: dict[str, int],
    api_operation_ids: dict[str, int],
    sdk_method_ids: dict[str, int],
    source_section_ids: dict[str, int],
) -> None:
    valid_code_examples = set(code_example_ids.values())
    valid_api_operations = set(api_operation_ids.values())
    valid_sdk_methods = set(sdk_method_ids.values())
    valid_sections = set(source_section_ids.values())
    errors: list[str] = []
    for recipe in recipes:
        key = str(recipe.get("recipe_key") or "")
        evidence_count = 0
        for field, valid_ids in (
            ("source_code_example_ids_json", valid_code_examples),
            ("source_api_operation_ids_json", valid_api_operations),
            ("source_sdk_method_ids_json", valid_sdk_methods),
            ("source_section_ids_json", valid_sections),
        ):
            ids = list_of_ints(recipe.get(field))
            evidence_count += len(ids)
            dangling = [value for value in ids if value not in valid_ids]
            if dangling:
                errors.append(f"{key or '<missing>'} references missing {field}: {dangling[:5]}")
        if evidence_count == 0:
            errors.append(f"{key or '<missing>'} has no source evidence ids")
        if not list_of_strings(recipe.get("source_urls_json")):
            errors.append(f"{key or '<missing>'} has no source URLs")
    if errors:
        raise RuntimeError("agent recipe evidence validation failed: " + "; ".join(errors[:12]))


class RecipeAdapter:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.recipe_key = str(data.get("recipe_key") or "")
        self.title = str(data.get("title") or "")
        self.task_kind = str(data.get("task_kind") or "")
        self.content = "\n\n".join(str(data.get(key) or "") for key in ("summary", "info"))
        self.code = data.get("code")
        self.info = str(data.get("info") or "")
        self.metadata_json = dict(data.get("metadata_json") or {})

    def __replace__(self, **changes: Any) -> "RecipeAdapter":
        data = dict(self.data)
        if "content" in changes:
            data["summary"] = str(changes["content"] or "")
        if "code" in changes:
            data["code"] = changes["code"]
        if "info" in changes:
            data["info"] = str(changes["info"] or "")
        if "metadata_json" in changes:
            metadata = dict(changes["metadata_json"] or {})
            data["metadata_json"] = metadata
            data["llm_enriched"] = bool(metadata.get("llm_enriched"))
            data["llm_model"] = str(metadata.get("llm_model") or "")
        return RecipeAdapter(data)


def evidence_for_recipe(recipe: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    urls = set(list_of_strings(recipe.get("source_urls_json")))
    output = []
    for row in rows:
        source = str(row.get("source_anchor") or row.get("source_url") or "")
        if source and source in urls:
            output.append(row)
    return output[:8]


def matching_api_operations(example: dict[str, Any], operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored: list[tuple[tuple[int, float, str], dict[str, Any]]] = []
    for operation in operations:
        score = operation_match_score(example, operation)
        if score <= 0:
            continue
        scored.append(((score, float(operation.get("confidence") or 0), str(operation.get("operation_key") or "")), operation))
    scored.sort(key=lambda item: (-item[0][0], -item[0][1], item[0][2]))
    return [row for _, row in scored]


def matching_sdk_methods(example: dict[str, Any], methods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored: list[tuple[tuple[int, float, str], dict[str, Any]]] = []
    for method in methods:
        score = method_match_score(example, method)
        if score <= 0:
            continue
        scored.append(((score, float(method.get("confidence") or 0), str(method.get("method_key") or "")), method))
    scored.sort(key=lambda item: (-item[0][0], -item[0][1], item[0][2]))
    return [row for _, row in scored]


def operation_match_score(example: dict[str, Any], operation: dict[str, Any]) -> int:
    text = evidence_text(example).lower()
    score = shared_evidence_score(example, operation)
    endpoint = str(operation.get("endpoint") or "").lower()
    if endpoint and endpoint in text:
        score += 6
    method = str(operation.get("http_method") or "").lower()
    if method and endpoint and f"{method} {endpoint}" in text:
        score += 4
    for key in ("operation_id", "operation_name"):
        token = str(operation.get(key) or "").strip().lower()
        if token and token in text:
            score += 4
    if canonical_task(operation.get("operation_kind")) == primary_task(example.get("task_tags_json")):
        score += 1
    return score


def method_match_score(example: dict[str, Any], method: dict[str, Any]) -> int:
    text = evidence_text(example)
    lowered = text.lower()
    score = shared_evidence_score(example, method)
    for key in ("sdk_method", "symbol_name", "sdk_class"):
        token = str(method.get(key) or "").strip()
        if token and re.search(rf"(?<![A-Za-z0-9_$]){re.escape(token)}(?![A-Za-z0-9_$])", text):
            score += 5
        elif token and token.lower() in lowered:
            score += 2
    signature = str(method.get("signature") or "")
    if signature and signature.split("(", 1)[0].strip().lower() in lowered:
        score += 3
    return score


def shared_evidence_score(left: dict[str, Any], right: dict[str, Any]) -> int:
    score = 0
    if str(left.get("source_section_key") or "") and str(left.get("source_section_key") or "") == str(right.get("source_section_key") or ""):
        score += 5
    if str(left.get("source_document_key") or "") and str(left.get("source_document_key") or "") == str(right.get("source_document_key") or ""):
        score += 2
    return score


def evidence_text(row: dict[str, Any]) -> str:
    return "\n".join(
        str(row.get(key) or "")
        for key in (
            "title",
            "caption",
            "description",
            "summary",
            "operation_name",
            "operation_id",
            "sdk_class",
            "sdk_method",
            "symbol_name",
            "signature",
            "endpoint",
            "code",
            "content",
        )
    )


def evidence_section_keys(rows: list[dict[str, Any]]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for row in rows:
        metadata = row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}
        key = str(row.get("source_section_key") or metadata.get("source_section_key") or "")
        if key and key not in seen:
            seen.add(key)
            output.append(key)
    return output


def compiled_recipe_title(example: dict[str, Any], operations: list[dict[str, Any]], methods: list[dict[str, Any]]) -> str:
    title = str(example.get("title") or example.get("caption") or "").strip()
    if title:
        return title
    if operations:
        return str(operations[0].get("operation_name") or operations[0].get("endpoint") or "API implementation")
    if methods:
        return str(methods[0].get("symbol_name") or methods[0].get("sdk_method") or "SDK implementation")
    return "Source-backed implementation"


def compiled_recipe_info(operations: list[dict[str, Any]], methods: list[dict[str, Any]], sections: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for operation in operations[:3]:
        info = operation_info(operation)
        if info:
            parts.append(info)
    for method in methods[:5]:
        info = sdk_info(method)
        if info:
            parts.append(info)
    for section in sections[:2]:
        content = str(section.get("content") or "").strip()
        if content:
            parts.append(first_sentences(content))
    return "\n\n".join(dedupe_strings(parts))[:3000]


def compiled_task_kind(example: dict[str, Any], operations: list[dict[str, Any]], methods: list[dict[str, Any]]) -> str:
    for candidate in [primary_task(example.get("task_tags_json")), *(canonical_task(row.get("operation_kind")) for row in operations)]:
        if candidate and candidate != "operation":
            return candidate
    return task_from_text("\n".join([evidence_text(example), *(evidence_text(row) for row in [*operations, *methods])]))


def merge_recipe_params(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        for param in list_of_dicts(row.get("required_params_json")):
            name = str(param.get("name") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            output.append(param)
    return output


def recipe_confidence(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    confidences = [float(row.get("confidence") or 0.55) for row in rows]
    evidence_types = {
        str((row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}).get("surface") or row.get("source_type") or "")
        for row in rows
    }
    base = sum(confidences) / len(confidences)
    coverage_bonus = min(1.0, len(evidence_types) / 3) * 0.25
    quantity_bonus = min(1.0, len(rows) / 10) * 0.15
    return min(1.0, base * 0.6 + coverage_bonus + quantity_bonus)


def surface_evidence(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}
    return {
        key: value
        for key, value in {
            "source_document_key": row.get("source_document_key"),
            "source_section_key": row.get("source_section_key") or metadata.get("source_section_key"),
            "source_url": row.get("source_url"),
            "source_anchor": row.get("source_anchor"),
            "surface": metadata.get("surface"),
            "source_type": row.get("source_type") or metadata.get("source_type"),
            "confidence": row.get("confidence"),
        }.items()
        if value not in (None, "", [], {})
    }


def evidence_urls(row: dict[str, Any]) -> list[str]:
    values = [row.get("source_anchor"), row.get("source_url")]
    return [str(value) for value in values if str(value or "").strip()]


def first_value(*groups: list[dict[str, Any]], key: str) -> str:
    for group in groups:
        for row in group:
            value = str(row.get(key) or "").strip()
            if value:
                return value
    return ""


def max_float(values: Any) -> float:
    output = 0.0
    for value in values if isinstance(values, list) else list(values):
        try:
            output = max(output, float(value or 0))
        except (TypeError, ValueError):
            continue
    return output


def dedupe_strings(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = re.sub(r"\s+", " ", value).strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(value)
    return output


def section_recipe_candidate(row: dict[str, Any]) -> bool:
    role = str(row.get("document_role") or "")
    text = str(row.get("content") or "")
    return role in {"readme", "guide", "troubleshooting", "config"} and token_count(text) >= 80


def operation_info(row: dict[str, Any]) -> str:
    lines = []
    method = str(row.get("http_method") or "")
    endpoint = str(row.get("endpoint") or "")
    if method or endpoint:
        lines.append(f"Endpoint: {' '.join(part for part in (method, endpoint) if part)}")
    params = list_of_dicts(row.get("required_params_json"))
    if params:
        lines.append("Required params: " + ", ".join(str(param.get("name") or "") for param in params if param.get("name")))
    optional = list_of_dicts(row.get("optional_params_json"))
    if optional:
        lines.append("Optional params: " + ", ".join(str(param.get("name") or "") for param in optional[:20] if param.get("name")))
    errors = list_of_dicts(row.get("errors_json"))
    if errors:
        lines.append("Errors: " + ", ".join(str(item.get("name") or item.get("status") or "") for item in errors[:12]))
    description = str(row.get("description") or "")
    if description:
        lines.append(description[:1200])
    return "\n".join(line for line in lines if line.strip())


def sdk_info(row: dict[str, Any]) -> str:
    lines = []
    signature = str(row.get("signature") or "")
    if signature:
        lines.append(f"Signature: {signature}")
    params = list_of_dicts(row.get("required_params_json"))
    if params:
        lines.append("Required params: " + ", ".join(str(param.get("name") or "") for param in params if param.get("name")))
    optional = list_of_dicts(row.get("optional_params_json"))
    if optional:
        lines.append("Optional params: " + ", ".join(str(param.get("name") or "") for param in optional[:20] if param.get("name")))
    return_type = str(row.get("return_type") or "")
    if return_type:
        lines.append(f"Returns: {return_type}")
    description = str(row.get("description") or "")
    if description:
        lines.append(description[:1200])
    return "\n".join(line for line in lines if line.strip())


def example_info(row: dict[str, Any]) -> str:
    lines = []
    env = list_of_strings(row.get("required_env_json"))
    if env:
        lines.append("Required environment: " + ", ".join(env))
    description = str(row.get("description") or "")
    if description:
        lines.append(description)
    source = str(row.get("source_anchor") or row.get("source_url") or "")
    if source:
        lines.append(f"Source: {source}")
    return "\n".join(lines)


def task_from_text(text: str) -> str:
    lowered = text.lower()
    for kind, pattern in (
        ("setup_auth", r"\b(install|setup|quickstart|api key|auth|credential|environment)\b"),
        ("create", r"\b(create|new|add|build)\b"),
        ("list", r"\b(list|available|all|search)\b"),
        ("retrieve", r"\b(get|fetch|retrieve|read|details)\b"),
        ("update", r"\b(update|edit|patch|modify)\b"),
        ("delete", r"\b(delete|remove|destroy)\b"),
        ("upload", r"\b(upload|file|pdf|document|image|audio)\b"),
        ("stream", r"\b(stream|realtime|websocket|sse|chunk)\b"),
        ("config", r"\b(config|env|host|base url|settings)\b"),
        ("error_handling", r"\b(error|exception|retry|failed|failure)\b"),
        ("testing", r"\b(test|mock|pytest|jest|spec)\b"),
        ("production", r"\b(production|deploy|timeout|logging|monitoring)\b"),
    ):
        if re.search(pattern, lowered):
            return kind
    return "concept"


def primary_task(value: Any) -> str:
    for item in list_of_strings(value):
        kind = canonical_task(item)
        if kind != "operation":
            return kind
    return ""


def canonical_task(value: Any) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
    return normalized if normalized in TASK_KINDS else "operation"


def first_sentences(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip())
    match = re.match(r"(.{80,900}?[.!?])(?:\s|$)", normalized)
    return (match.group(1) if match else normalized[:900]).strip()


def evidence_hash(*values: Any) -> str:
    return hashlib.sha256("\0".join(str(value or "") for value in values).encode("utf-8")).hexdigest()


def stable_key(prefix: str, *parts: Any) -> str:
    return f"{prefix}:{evidence_hash(*parts)[:32]}"


def metadata(row: dict[str, Any], *, source: str) -> dict[str, Any]:
    value = row.get("metadata_json")
    output = dict(value) if isinstance(value, dict) else {}
    output["surface"] = source
    return output


def dedupe_recipes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    seen = set()
    for row in rows:
        key = str(row.get("recipe_key") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output[:max_recipe_count()]


def list_of_strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def list_of_ints(value: Any) -> list[int]:
    output = []
    for item in value if isinstance(value, list) else []:
        try:
            output.append(int(item))
        except (TypeError, ValueError):
            continue
    return output


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def llm_limit() -> int:
    try:
        return max(0, int(__import__("os").environ.get("OZ_RECIPE_LLM_MAX_PER_VERSION", "25")))
    except ValueError:
        return 25


def max_recipe_count() -> int:
    try:
        return max(1, int(__import__("os").environ.get("OZ_AGENT_MAX_RECIPES_PER_VERSION", "2500")))
    except ValueError:
        return 2500


def max_section_recipe_count() -> int:
    try:
        return max(0, int(__import__("os").environ.get("OZ_AGENT_SECTION_RECIPE_LIMIT", "250")))
    except ValueError:
        return 250
