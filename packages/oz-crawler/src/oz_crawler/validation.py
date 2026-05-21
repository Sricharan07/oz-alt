from __future__ import annotations

import hashlib
import os
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oz_crawler.profiles import LibraryProfile

USEFUL_CONTENT_TYPES = {"api_reference", "code_example", "prose", "config", "cli", "error_ref", "types", "example"}
DOC_AUTHORING_PATH_RE = re.compile(
    r"(?:^|/)(?:community|contributing|contribution-guide|docs-contribution|docs-writing|style-guide|styleguides|authors|maintainers|governance|roadmap)(?:/|\.|$)",
    re.I,
)


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    errors: list[str]
    warnings: list[str]
    metrics: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


def validate_fixture(target: Path, profile: LibraryProfile | None) -> ValidationResult:
    pages = markdown_pages(target)
    rejected = rejected_pages(target)
    symbols = symbol_names(target)
    chunks = chunk_rows(target)
    sources = source_rows(target)
    sections = source_section_rows(target)
    code_examples = code_example_rows(target)
    api_operations = api_operation_rows(target)
    sdk_methods = sdk_method_rows(target)
    coverage = chunk_coverage_rows(target)
    crawl_errors = crawl_error_rows(target)
    errors: list[str] = []
    warnings: list[str] = []

    if profile is not None:
        if len(pages) < profile.min_documents:
            errors.append(f"only {len(pages)} useful docs; expected at least {profile.min_documents}")
        missing_topics = missing_required_topics(target, profile.required_topics)
        if missing_topics:
            errors.append("missing required topics: " + ", ".join(missing_topics))
        missing_symbols = missing_expected_symbols(symbols, profile.expected_symbols, corpus_text(target))
        if missing_symbols:
            errors.append("missing expected symbols: " + ", ".join(missing_symbols))
        junk_rejections = true_junk_rejections(rejected)
        total_seen = len(pages) + len(junk_rejections)
        junk_ratio = len(junk_rejections) / total_seen if total_seen else 1.0
        if junk_ratio > profile.max_junk_ratio:
            errors.append(f"junk ratio {junk_ratio:.2f} exceeds {profile.max_junk_ratio:.2f}")
    else:
        warnings.append("no library profile found")

    if not chunks:
        errors.append("no indexable chunks generated")
    duplicate_ratio = duplicate_chunk_ratio(chunks)
    if duplicate_ratio > 0.05:
        errors.append(f"duplicate chunk ratio {duplicate_ratio:.2f} exceeds 0.05")
    content_types = content_type_counts(chunks)
    if chunks and not any(content_types.get(kind, 0) for kind in USEFUL_CONTENT_TYPES):
        errors.append("chunks do not include useful documentation content")
    missing_anchors = sum(1 for row in chunks if not row.get("source_anchor"))
    if chunks and missing_anchors:
        errors.append(f"{missing_anchors} chunks are missing source anchors")
    missing_token_counts = sum(1 for row in chunks if int(row.get("token_count") or 0) <= 0)
    if chunks and missing_token_counts:
        errors.append(f"{missing_token_counts} chunks are missing token counts")
    missing_chunk_sections = sum(
        1
        for row in chunks
        if not ((row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}).get("source_section_key") or row.get("source_section_key"))
    )
    if chunks and missing_chunk_sections:
        errors.append(f"{missing_chunk_sections} chunks are missing source section linkage")
    missing_contextual_prefixes = sum(1 for row in chunks if not str(row.get("contextual_prefix") or "").strip())
    if chunks and missing_contextual_prefixes:
        errors.append(f"{missing_contextual_prefixes} chunks are missing contextual prefixes")
    frontmatter_chunks = sum(1 for row in chunks if has_frontmatter(str(row.get("text") or "")))
    if chunks and frontmatter_chunks:
        errors.append(f"{frontmatter_chunks} chunks contain frontmatter")
    max_allowed_tokens = max_chunk_tokens()
    oversized_chunks = sum(1 for row in chunks if int(row.get("token_count") or 0) > max_allowed_tokens)
    if chunks and oversized_chunks:
        errors.append(f"{oversized_chunks} chunks exceed {max_allowed_tokens} tokens")
    parent_child_chunks = sum(1 for row in chunks if row.get("parent_chunk_key"))
    long_source_anchors = sum(1 for row in chunks if len(str(row.get("source_anchor") or "")) > 240)
    if chunks and long_source_anchors:
        errors.append(f"{long_source_anchors} chunks have source anchors longer than 240 chars")
    long_heading_paths = sum(1 for row in chunks if any(len(str(item)) > 160 for item in row.get("heading_path") or []))
    if chunks and long_heading_paths:
        errors.append(f"{long_heading_paths} chunks have heading path entries longer than 160 chars")
    docs_authoring_chunks = sum(1 for row in chunks if DOC_AUTHORING_PATH_RE.search(str(row.get("path") or "")))
    if chunks and docs_authoring_chunks:
        errors.append(f"{docs_authoring_chunks} chunks come from docs-authoring paths")
    index_boilerplate_chunks = sum(1 for row in chunks if "index of all docs" in str(row.get("text") or "").lower())
    if chunks and index_boilerplate_chunks:
        errors.append(f"{index_boilerplate_chunks} chunks contain docs index boilerplate")
    duplicate_source_documents = duplicate_source_document_count(sources)
    if sources and duplicate_source_documents:
        errors.append(f"{duplicate_source_documents} duplicate canonical source documents")
    coverage_threshold = min_chunk_coverage_ratio()
    coverage_failures = [
        row
        for row in coverage
        if int(row.get("clean_line_count") or 0) > 0 and float(row.get("coverage_ratio") or 0) < coverage_threshold
    ]
    code_fence_coverage_failures = [
        row
        for row in coverage
        if int(row.get("code_fence_line_count") or 0) > 0 and float(row.get("code_fence_coverage_ratio") or 0) < 1.0
    ]
    if sources and not coverage:
        errors.append("chunk coverage report is missing")
    if chunks and not sections:
        errors.append("source section artifact is missing")
    if coverage_failures:
        sample = ", ".join(str(row.get("path") or row.get("source_url")) for row in coverage_failures[:3])
        errors.append(f"{len(coverage_failures)} source documents have chunk coverage below {coverage_threshold:.2f}: {sample}")
    if code_fence_coverage_failures:
        sample = ", ".join(str(row.get("path") or row.get("source_url")) for row in code_fence_coverage_failures[:3])
        errors.append(f"{len(code_fence_coverage_failures)} source documents have uncovered code fences: {sample}")
    section_errors = validate_section_extractions(sections, code_examples, api_operations, sdk_methods)
    errors.extend(section_errors)
    source_cap_errors = [row for row in crawl_errors if str(row.get("stage") or "") == "source_cap"]
    if source_cap_errors and not allow_partial_source_coverage():
        errors.append(f"source artifact cap was hit {len(source_cap_errors)} time(s); set explicit partial coverage approval to promote")

    metrics = {
        "documents": len(pages),
        "rejected_documents": len(rejected),
        "chunks": len(chunks),
        "symbols": len(symbols),
        "duplicate_chunk_ratio": round(duplicate_ratio, 4),
        "junk_documents": len(true_junk_rejections(rejected)),
        "policy_rejected_documents": len(rejected) - len(true_junk_rejections(rejected)),
        "content_types": content_types,
        "missing_source_anchors": missing_anchors,
        "missing_token_counts": missing_token_counts,
        "frontmatter_chunks": frontmatter_chunks,
        "oversized_chunks": oversized_chunks,
        "max_chunk_tokens": max_allowed_tokens,
        "parent_child_chunks": parent_child_chunks,
        "source_documents": len(sources),
        "duplicate_source_documents": duplicate_source_documents,
        "long_source_anchors": long_source_anchors,
        "long_heading_paths": long_heading_paths,
        "docs_authoring_chunks": docs_authoring_chunks,
        "index_boilerplate_chunks": index_boilerplate_chunks,
        "chunk_coverage_documents": len(coverage),
        "chunk_coverage_threshold": coverage_threshold,
        "chunk_coverage_min": min((float(row.get("coverage_ratio") or 0) for row in coverage), default=0),
        "chunk_coverage_failed_documents": len(coverage_failures),
        "code_fence_coverage_failed_documents": len(code_fence_coverage_failures),
        "source_sections": len(sections),
        "code_examples": len(code_examples),
        "api_operations": len(api_operations),
        "sdk_methods": len(sdk_methods),
        "crawl_errors": len(crawl_errors),
        "source_cap_errors": len(source_cap_errors),
        "missing_contextual_prefixes": missing_contextual_prefixes,
        "sections_with_code": sum(1 for row in sections if bool(row.get("has_code"))),
        "sections_with_endpoint_shape": sum(1 for row in sections if bool(row.get("has_endpoint_shape"))),
        "sections_with_signature_shape": sum(1 for row in sections if bool(row.get("has_signature_shape"))),
    }
    return ValidationResult(not errors, errors, warnings, metrics)


def write_validation(target: Path, result: ValidationResult) -> None:
    (target / "_quality.json").write_text(json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_pages(target: Path) -> list[Path]:
    pages: list[Path] = []
    for path in target.rglob("*.md"):
        relative = path.relative_to(target).as_posix()
        if relative.startswith("_symbols/") or relative in {"INDEX.md", "README.md", "api-reference/README.md", "examples/README.md"}:
            continue
        pages.append(path)
    return pages


def source_section_rows(target: Path) -> list[dict[str, Any]]:
    return jsonl_file_rows(target / "_source_sections.jsonl")


def code_example_rows(target: Path) -> list[dict[str, Any]]:
    return jsonl_file_rows(target / "_code_examples.jsonl")


def api_operation_rows(target: Path) -> list[dict[str, Any]]:
    return jsonl_file_rows(target / "_api_operations.jsonl")


def sdk_method_rows(target: Path) -> list[dict[str, Any]]:
    return jsonl_file_rows(target / "_sdk_methods.jsonl")


def crawl_error_rows(target: Path) -> list[dict[str, Any]]:
    return jsonl_file_rows(target / "_crawl_errors.jsonl")


def jsonl_file_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def rejected_pages(target: Path) -> list[dict[str, Any]]:
    path = target / "_rejected.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def true_junk_rejections(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not is_policy_rejection(row)]


def is_policy_rejection(row: dict[str, Any]) -> bool:
    reasons = [str(reason).lower() for reason in row.get("reasons") or []]
    content_type = str(row.get("content_type") or "").lower()
    return (
        content_type in {"duplicate", "duplicate_source", "archived_version", "network_page_fetch", "network_source_fetch"}
        or any(reason.startswith("duplicate content") for reason in reasons)
        or any("url rejected by library profile" in reason for reason in reasons)
        or any("version" in reason and ("archived" in reason or "target" in reason) for reason in reasons)
        or is_benign_virtual_fragment_rejection(row, reasons)
    )


def is_benign_virtual_fragment_rejection(row: dict[str, Any], reasons: list[str]) -> bool:
    """Do not treat harmless skipped fragments from compiled sources as junk.

    llms-full and OpenAPI sources can split into many small virtual documents.
    Dropping a short fragment is normal; the junk gate should fail on harmful
    crawled pages, not on intentionally skipped fragments from a trusted source.
    """

    source_url = str(row.get("source_url") or "").lower()
    if not (
        re.search(r"(?:^|/)(?:llms|llms-full)\.txt#", source_url)
        or re.search(r"(?:openapi|swagger)\.(?:json|ya?ml)#", source_url)
    ):
        return False
    harmful = {
        "marketing/login language",
        "generic homepage/search page",
        "navigation-heavy repeated text",
        "language does not match target",
    }
    if any(any(marker in reason for marker in harmful) for reason in reasons):
        return False
    benign_prefixes = ("too little documentation text", "quality score below", "no headings")
    return bool(reasons) and all(reason.startswith(benign_prefixes) for reason in reasons)


def symbol_names(target: Path) -> set[str]:
    root = target / "_symbols"
    if not root.exists():
        return set()
    return {path.stem for path in root.glob("*.md")}


def chunk_rows(target: Path) -> list[dict[str, Any]]:
    path = target / "_chunks.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def source_rows(target: Path) -> list[dict[str, Any]]:
    path = target / "_sources.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def chunk_coverage_rows(target: Path) -> list[dict[str, Any]]:
    path = target / "_chunk_coverage.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def validate_section_extractions(
    sections: list[dict[str, Any]],
    code_examples: list[dict[str, Any]],
    api_operations: list[dict[str, Any]],
    sdk_methods: list[dict[str, Any]],
) -> list[str]:
    if not sections:
        return []
    errors: list[str] = []
    section_keys = {str(row.get("section_key") or "") for row in sections if row.get("section_key")}
    missing_content_sha = sum(1 for row in sections if not row.get("content_sha"))
    if missing_content_sha:
        errors.append(f"{missing_content_sha} source sections are missing content_sha")
    examples_by_section = linked_surface_keys(code_examples)
    operations_by_section = linked_surface_keys(api_operations)
    methods_by_section = linked_surface_keys(sdk_methods)
    missing_example_sections = [
        row
        for row in sections
        if bool(row.get("has_code"))
        and str(row.get("document_role") or "") not in {"sdk_source", "type_definition"}
        and str(row.get("section_key") or "") not in examples_by_section
    ]
    missing_operation_sections = [
        row for row in sections if bool(row.get("has_endpoint_shape")) and str(row.get("section_key") or "") not in operations_by_section
    ]
    missing_method_sections = [
        row
        for row in sections
        if bool(row.get("has_signature_shape"))
        and str(row.get("section_key") or "") not in methods_by_section
        and str(row.get("section_key") or "") not in operations_by_section
    ]
    dangling_examples = sorted(linked_surface_keys(code_examples) - section_keys)
    dangling_operations = sorted(linked_surface_keys(api_operations) - section_keys)
    dangling_methods = sorted(linked_surface_keys(sdk_methods) - section_keys)
    missing_example_evidence = missing_surface_evidence(code_examples, "code_examples")
    missing_operation_evidence = missing_surface_evidence(api_operations, "api_operations")
    missing_method_evidence = missing_surface_evidence(sdk_methods, "sdk_methods")
    if missing_example_sections:
        errors.append(f"{len(missing_example_sections)} code-shaped sections emitted no code_examples: {section_sample(missing_example_sections)}")
    if missing_operation_sections:
        errors.append(f"{len(missing_operation_sections)} endpoint-shaped sections emitted no api_operations: {section_sample(missing_operation_sections)}")
    if missing_method_sections:
        errors.append(f"{len(missing_method_sections)} signature-shaped sections emitted no sdk_methods: {section_sample(missing_method_sections)}")
    if dangling_examples:
        errors.append(f"{len(dangling_examples)} code_examples reference missing source sections")
    if dangling_operations:
        errors.append(f"{len(dangling_operations)} api_operations reference missing source sections")
    if dangling_methods:
        errors.append(f"{len(dangling_methods)} sdk_methods reference missing source sections")
    if missing_example_evidence:
        errors.append(f"{missing_example_evidence} code_examples are missing source evidence")
    if missing_operation_evidence:
        errors.append(f"{missing_operation_evidence} api_operations are missing source evidence")
    if missing_method_evidence:
        errors.append(f"{missing_method_evidence} sdk_methods are missing source evidence")
    return errors


def missing_surface_evidence(rows: list[dict[str, Any]], _surface_name: str) -> int:
    missing = 0
    for row in rows:
        metadata = row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}
        if not str(row.get("source_document_key") or metadata.get("source_document_key") or "").strip():
            missing += 1
            continue
        if not str(row.get("source_anchor") or metadata.get("source_anchor") or "").strip():
            missing += 1
            continue
        if not str(row.get("source_section_key") or metadata.get("source_section_key") or "").strip():
            missing += 1
    return missing


def linked_surface_keys(rows: list[dict[str, Any]]) -> set[str]:
    keys: set[str] = set()
    for row in rows:
        metadata = row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}
        key = str(row.get("source_section_key") or metadata.get("source_section_key") or "")
        if key:
            keys.add(key)
    return keys


def section_sample(rows: list[dict[str, Any]]) -> str:
    return ", ".join(str(row.get("path") or row.get("source_url") or row.get("section_key")) for row in rows[:3])


def duplicate_source_document_count(rows: list[dict[str, Any]]) -> int:
    seen: set[str] = set()
    duplicates = 0
    for row in rows:
        key = source_document_duplicate_key(row)
        if not key:
            continue
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


def source_document_duplicate_key(row: dict[str, Any]) -> str:
    value = str(row.get("canonical_url") or row.get("source_url") or row.get("path") or "").rstrip("/")
    if not value:
        return ""
    metadata = row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}
    source_type = str(row.get("source_type") or metadata.get("source_type") or "").lower()
    if "#" in value and (
        source_type in {"llms_txt", "openapi"}
        or re.search(r"(?:^|/)(?:llms|llms-full)\.txt#", value.lower())
    ):
        return value
    return value.split("#", 1)[0].rstrip("/")


def missing_required_topics(target: Path, topics: list[str]) -> list[str]:
    if not topics:
        return []
    haystack = corpus_text(target).lower()
    return [topic for topic in topics if topic.lower() not in haystack]


def corpus_text(target: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in markdown_pages(target))


def missing_expected_symbols(actual: set[str], expected: list[str], haystack: str = "") -> list[str]:
    normalized_actual = {symbol.lower() for symbol in actual}
    normalized_haystack = normalized_symbol_text(haystack)
    missing: list[str] = []
    for symbol in expected:
        variants = expected_symbol_variants(symbol)
        if any(variant in normalized_actual for variant in variants):
            continue
        if normalized_haystack and any(variant in normalized_haystack for variant in variants):
            continue
        missing.append(symbol)
    return missing


def expected_symbol_variants(symbol: str) -> set[str]:
    raw = symbol.strip()
    if not raw:
        return set()
    phrase = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", raw)
    phrase = re.sub(r"[-_./\\]+", " ", phrase)
    phrase = re.sub(r"\s+", " ", phrase).strip().lower()
    compact = re.sub(r"[^a-z0-9]+", "", phrase)
    variants = {raw.lower(), phrase}
    if compact:
        variants.add(compact)
    return variants


def normalized_symbol_text(text: str) -> str:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    spaced = re.sub(r"[-_./\\]+", " ", spaced)
    return re.sub(r"\s+", " ", spaced).lower()


def duplicate_chunk_ratio(chunks: list[dict[str, Any]]) -> float:
    if not chunks:
        return 0.0
    seen: set[str] = set()
    duplicates = 0
    for row in chunks:
        key = hashlib.sha256(normalized_content(str(row.get("text") or "")).encode("utf-8")).hexdigest()
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates / len(chunks)


def normalized_content(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def content_type_counts(chunks: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in chunks:
        key = str(row.get("content_type") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def has_frontmatter(text: str) -> bool:
    stripped = text.lstrip()
    for marker in ("---", "+++"):
        if not stripped.startswith(marker + "\n"):
            continue
        end = stripped.find("\n" + marker + "\n", len(marker) + 1)
        if end < 0:
            continue
        payload = stripped[len(marker) + 1 : end]
        lines = [line.strip() for line in payload.splitlines() if line.strip()]
        if lines and not any(line.startswith(("#", "```")) for line in lines):
            return any(re.match(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:", line) for line in lines)
    return False


def max_chunk_tokens() -> int:
    try:
        return int(os.environ.get("OZ_MAX_CHUNK_TOKENS", "1200"))
    except ValueError:
        return 1200


def min_chunk_coverage_ratio() -> float:
    try:
        return max(0.0, min(1.0, float(os.environ.get("OZ_MIN_CHUNK_COVERAGE_RATIO", "0.98"))))
    except ValueError:
        return 0.98


def allow_partial_source_coverage() -> bool:
    return os.environ.get("OZ_ALLOW_PARTIAL_SOURCE_COVERAGE", "").lower() in {"1", "true", "yes", "on"}
