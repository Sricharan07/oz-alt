from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from oz_api.jury import judge_search_check, jury_required, jury_requested
from oz_api.retrieval import RetrievalContext, context as retrieval_context_packet
from oz_api.retrieval_local import search_from_fixtures
from oz_api.storage import RegistryStorage
from oz_crawler.token_counting import token_count


def search_eval_report(
    storage: RegistryStorage,
    library: str,
    version: str,
    *,
    fixtures_root: Path | None = None,
) -> dict[str, Any] | None:
    spec = eval_spec_for_library(storage, library, version)
    if spec is None:
        return None
    checks = []
    hits = 0
    top1 = 0
    reciprocal = 0.0
    junk_failures = 0
    duplicate_failures = 0
    content_failures = 0
    jury_scores: list[float] = []
    use_jury = jury_requested() or jury_required()
    for check in spec.get("checks", []):
        query = str(check.get("query") or "")
        expected = [str(item) for item in check.get("expected_files", [])]
        banned_files = [str(item) for item in check.get("banned_files", [])]
        banned_paths = [str(item) for item in check.get("banned_paths", [])]
        banned_content = [str(item).lower() for item in check.get("banned_content", [])]
        banned_content.extend(str(item).lower() for item in check.get("must_not_include", []))
        required = [str(item).lower() for item in check.get("must_include", [])]
        patterns = [str(item) for item in check.get("patterns", [])]
        rows = search_from_fixtures(storage, query, library_scope=library, max_results=5, fixtures_root=fixtures_root)
        paths = [str(row.get("path") or "") for row in rows]
        ranks = [idx + 1 for idx, path in enumerate(paths) if any(path.endswith(item) for item in expected)]
        contents = fixture_result_contents(storage, paths, fixtures_root=fixtures_root)
        jury_result: dict[str, Any] = {}
        if use_jury:
            try:
                jury_result = judge_search_check(check, paths, contents)
                jury_scores.append(float(jury_result.get("score") or 0))
            except Exception as exc:
                if jury_required():
                    raise RuntimeError(f"jury search eval failed: {exc}") from exc
                jury_result = {"error": str(exc)[:500]}
        joined = "\n".join(contents).lower()
        junk_hit = path_junk_hit(paths, banned_files, banned_paths) or any(
            term in content.lower() for term in banned_content for content in contents
        )
        content_hit = content_requirement_hit(joined, required, patterns)
        duplicate_hit = len(paths) != len(set(paths))
        if ranks:
            hits += 1
            reciprocal += 1.0 / ranks[0]
            top1 += int(ranks[0] == 1)
        junk_failures += int(junk_hit)
        duplicate_failures += int(duplicate_hit)
        content_failures += int(required and not content_hit)
        checks.append(
            {
                "name": check.get("name", query),
                "query": query,
                "paths": paths,
                "expected_files": expected,
                "banned_files": banned_files,
                "banned_paths": banned_paths,
                "expected_file_hit": bool(ranks),
                "junk_top5": junk_hit,
                "duplicate_top5": duplicate_hit,
                "required_content_hit": content_hit,
                "jury": jury_result,
            }
        )
    total = len(checks)
    recall = hits / total if total else 0.0
    materialized = materialization_rate(storage, checks, fixtures_root=fixtures_root)
    junk_rate = junk_failures / total if total else 0.0
    duplicate_rate = duplicate_failures / total if total else 0.0
    content_rate = 1 - (content_failures / total if total else 0.0)
    jury_score = sum(jury_scores) / len(jury_scores) if jury_scores else 0.0
    passed = (
        recall >= 0.85
        and materialized == 1.0
        and junk_rate == 0
        and duplicate_rate == 0
        and content_rate == 1.0
        and (not jury_required() or jury_score >= float(os.environ.get("OZ_EVAL_MIN_JURY_SCORE", "0.75")))
    )
    return {
        "passed": passed,
        "precision_at_1": round(top1 / total if total else 0.0, 3),
        "expected_file_recall_at_5": round(recall, 3),
        "precision_at_5": round(recall, 3),
        "mrr": round(reciprocal / total if total else 0.0, 3),
        "materialization_rate": round(materialized, 3),
        "junk_top5_rate": round(junk_rate, 3),
        "duplicate_top5_rate": round(duplicate_rate, 3),
        "content_requirement_rate": round(content_rate, 3),
        "jury_score": round(jury_score, 3) if use_jury else None,
        "checks": checks,
    }


def agent_context_eval_report(storage: RegistryStorage, library: str, version: str) -> dict[str, Any] | None:
    spec = eval_spec_for_library(storage, library, version)
    if spec is None:
        return None
    checks = []
    expected_hits = 0
    required_hits = 0
    grounded_hits = 0
    banned_failures = 0
    wrong_product_failures = 0
    over_budget = 0
    total_expected = 0
    total_required = 0
    ctx = RetrievalContext.from_env(storage)
    max_tokens = int(os.environ.get("OZ_AGENT_CONTEXT_EVAL_MAX_TOKENS", "2200"))
    for check in spec.get("checks", []):
        query = str(check.get("query") or "")
        if not query:
            continue
        expected_apis = [str(item) for item in check.get("expected_apis", []) or check.get("expected_symbols", [])]
        required_terms = [str(item) for item in check.get("required_terms", []) or check.get("must_include", [])]
        banned_terms = [str(item) for item in check.get("banned_terms", []) or check.get("must_not_include", []) or check.get("banned_content", [])]
        expected_products = list_of_strings(check.get("expected_products") or check.get("expected_product"))
        banned_products = list_of_strings(check.get("banned_products") or check.get("banned_product"))
        packet = retrieval_context_packet(
            ctx,
            query,
            library_scope=f"{library}@{version}",
            max_tokens=max_tokens,
            max_results=5,
            fingerprint="crawler-agent-context-eval",
        )
        text = packet_text(packet)
        sources = packet_sources(packet)
        tokens = token_count(text)
        expected_ok = compact_requirement_hit(text, expected_apis)
        required_ok = content_requirement_hit(text.lower(), [term.lower() for term in required_terms], [])
        banned_hit = any(term.lower() in text.lower() for term in banned_terms)
        grounded_ok = bool(sources)
        product_hit = product_requirement_hit(packet, text, expected_products)
        wrong_product_hit = wrong_product_requirement_hit(packet, text, expected_products, banned_products)
        total_expected += int(bool(expected_apis))
        total_required += int(bool(required_terms))
        expected_hits += int((not expected_apis) or expected_ok)
        required_hits += int((not required_terms) or required_ok)
        grounded_hits += int(grounded_ok)
        banned_failures += int(banned_hit)
        wrong_product_failures += int(wrong_product_hit)
        over_budget += int(tokens > max_tokens)
        checks.append(
            {
                "name": check.get("name", query),
                "query": query,
                "expected_apis": expected_apis,
                "required_terms": required_terms,
                "banned_terms": banned_terms,
                "expected_products": expected_products,
                "banned_products": banned_products,
                "expected_api_hit": expected_ok,
                "required_terms_hit": required_ok,
                "banned_hit": banned_hit,
                "expected_product_hit": product_hit,
                "wrong_product_hit": wrong_product_hit,
                "source_grounded": grounded_ok,
                "source_count": len(sources),
                "token_count": tokens,
                "code_snippets": len(packet.get("codeSnippets") or []),
                "info_snippets": len(packet.get("infoSnippets") or []),
            }
        )
    total = len(checks)
    if total == 0:
        return None
    expected_rate = expected_hits / total if total else 0
    required_rate = required_hits / total if total else 0
    grounded_rate = grounded_hits / total if total else 0
    banned_rate = banned_failures / total if total else 0
    wrong_product_rate = wrong_product_failures / total if total else 0
    budget_rate = over_budget / total if total else 0
    passed = (
        expected_rate >= float(os.environ.get("OZ_AGENT_CONTEXT_MIN_EXPECTED_API_RATE", "0.85"))
        and required_rate >= float(os.environ.get("OZ_AGENT_CONTEXT_MIN_REQUIRED_TERM_RATE", "1.0"))
        and grounded_rate >= float(os.environ.get("OZ_AGENT_CONTEXT_MIN_GROUNDING_RATE", "1.0"))
        and banned_rate == 0
        and wrong_product_rate <= float(os.environ.get("OZ_AGENT_CONTEXT_MAX_WRONG_PRODUCT_RATE", "0"))
        and budget_rate == 0
    )
    return {
        "passed": passed,
        "expected_api_rate": round(expected_rate, 3),
        "required_term_rate": round(required_rate, 3),
        "source_grounding_rate": round(grounded_rate, 3),
        "banned_hit_rate": round(banned_rate, 3),
        "wrong_product_rate": round(wrong_product_rate, 3),
        "over_budget_rate": round(budget_rate, 3),
        "checks": checks,
    }


def packet_text(packet: dict[str, Any]) -> str:
    parts: list[str] = []
    for card in packet.get("codeSnippets") or []:
        parts.extend(str(card.get(key) or "") for key in ("codeTitle", "codeDescription", "pageTitle"))
        for item in card.get("codeList") or []:
            if isinstance(item, dict):
                parts.append(str(item.get("code") or ""))
    for card in packet.get("infoSnippets") or []:
        if isinstance(card, dict):
            parts.extend(str(card.get(key) or "") for key in ("title", "content", "pageTitle"))
    return "\n".join(part for part in parts if part)


def packet_sources(packet: dict[str, Any]) -> list[str]:
    output = []
    for group in ("codeSnippets", "infoSnippets"):
        for card in packet.get(group) or []:
            if isinstance(card, dict) and str(card.get("source") or "").strip():
                output.append(str(card["source"]))
    return output


def packet_products(packet: dict[str, Any]) -> list[str]:
    products: list[str] = []
    for row in packet.get("results") or []:
        if not isinstance(row, dict):
            continue
        for value in (row.get("library"), row.get("vendor")):
            add_product_value(products, value)
        metadata = row.get("source_metadata")
        if isinstance(metadata, dict):
            add_product_value(products, metadata.get("product"))
    return products


def add_product_value(products: list[str], value: Any) -> None:
    text = str(value or "").strip()
    if text and text not in products:
        products.append(text)


def product_requirement_hit(packet: dict[str, Any], text: str, expected_products: list[str]) -> bool:
    if not expected_products:
        return True
    haystack = product_haystack(packet, text)
    return any(compact_product(product) in haystack for product in expected_products if compact_product(product))


def wrong_product_requirement_hit(
    packet: dict[str, Any],
    text: str,
    expected_products: list[str],
    banned_products: list[str],
) -> bool:
    haystack = product_haystack(packet, text)
    if any(compact_product(product) in haystack for product in banned_products if compact_product(product)):
        return True
    observed = [compact_product(product) for product in packet_products(packet)]
    expected = [compact_product(product) for product in expected_products if compact_product(product)]
    if expected and observed and not any(product in expected for product in observed):
        return True
    return False


def product_haystack(packet: dict[str, Any], text: str) -> str:
    parts = [text, "\n".join(packet_sources(packet)), "\n".join(packet_products(packet))]
    return compact_product("\n".join(parts))


def compact_product(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def list_of_strings(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def compact_requirement_hit(text: str, expected: list[str]) -> bool:
    if not expected:
        return True
    compacted = re.sub(r"[^a-z0-9]+", "", text.lower())
    return all(re.sub(r"[^a-z0-9]+", "", item.lower()) in compacted for item in expected)


def content_requirement_hit(joined_content: str, required_terms: list[str], patterns: list[str]) -> bool:
    if patterns:
        return all(re.search(pattern, joined_content, re.I) for pattern in patterns)
    return all(term in joined_content for term in required_terms)


def path_junk_hit(paths: list[str], banned_files: list[str], banned_paths: list[str]) -> bool:
    for path in paths:
        if any(path.endswith(item) for item in banned_files):
            return True
        if any(re.search(pattern, path, re.I) for pattern in banned_paths):
            return True
    return False


def eval_spec_for_library(storage: RegistryStorage, library: str, version: str) -> dict[str, Any] | None:
    eval_root = storage.registry_root / "evals"
    for path in sorted(eval_root.glob("*.yaml")):
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if spec.get("library") == library and str(spec.get("version") or version) == version:
            return spec
    return None


def fixture_result_contents(
    storage: RegistryStorage,
    paths: list[str],
    *,
    fixtures_root: Path | None = None,
) -> list[str]:
    output: list[str] = []
    root = fixtures_root or storage.fixtures_root
    for result_path in paths:
        relative = result_path.removeprefix(".codo/vendors/")
        if "/" not in relative:
            continue
        vendor, rest = relative.split("/", 1)
        if "@" not in rest or "/" not in rest:
            continue
        library_version, doc_path = rest.split("/", 1)
        if "@" not in library_version:
            continue
        library, version = library_version.rsplit("@", 1)
        path = root / vendor / library / version / doc_path
        if path.exists():
            output.append(path.read_text(encoding="utf-8", errors="replace"))
    return output


def materialization_rate(
    storage: RegistryStorage,
    checks: list[dict[str, Any]],
    *,
    fixtures_root: Path | None = None,
) -> float:
    total = 0
    existing = 0
    for check in checks:
        for result_path in check.get("paths", []):
            total += 1
            existing += int(bool(fixture_result_contents(storage, [str(result_path)], fixtures_root=fixtures_root)))
    return existing / total if total else 1.0
