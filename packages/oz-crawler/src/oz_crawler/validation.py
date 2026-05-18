from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oz_crawler.profiles import LibraryProfile


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
    errors: list[str] = []
    warnings: list[str] = []

    if profile is not None:
        if len(pages) < profile.min_documents:
            errors.append(f"only {len(pages)} useful docs; expected at least {profile.min_documents}")
        missing_topics = missing_required_topics(target, profile.required_topics)
        if missing_topics:
            errors.append("missing required topics: " + ", ".join(missing_topics))
        missing_symbols = missing_expected_symbols(symbols, profile.expected_symbols)
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
    if chunks and not any(content_types.get(kind, 0) for kind in ("api_reference", "code_example", "prose")):
        errors.append("chunks do not include useful api_reference, code_example, or prose content")
    missing_anchors = sum(1 for row in chunks if not row.get("source_anchor"))
    if chunks and missing_anchors:
        errors.append(f"{missing_anchors} chunks are missing source anchors")
    missing_token_counts = sum(1 for row in chunks if int(row.get("token_count") or 0) <= 0)
    if chunks and missing_token_counts:
        errors.append(f"{missing_token_counts} chunks are missing token counts")

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
    }
    return ValidationResult(not errors, errors, warnings, metrics)


def write_validation(target: Path, result: ValidationResult) -> None:
    (target / "_quality.json").write_text(json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_pages(target: Path) -> list[Path]:
    pages: list[Path] = []
    for path in target.rglob("*.md"):
        relative = path.relative_to(target).as_posix()
        if relative.startswith("_symbols/") or relative in {"INDEX.md", "README.md"}:
            continue
        pages.append(path)
    return pages


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
        content_type in {"duplicate", "archived_version"}
        or any(reason.startswith("duplicate content") for reason in reasons)
        or any("version" in reason and ("archived" in reason or "target" in reason) for reason in reasons)
    )


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


def missing_required_topics(target: Path, topics: list[str]) -> list[str]:
    if not topics:
        return []
    haystack = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in markdown_pages(target)).lower()
    return [topic for topic in topics if topic.lower() not in haystack]


def missing_expected_symbols(actual: set[str], expected: list[str]) -> list[str]:
    normalized_actual = {symbol.lower() for symbol in actual}
    return [symbol for symbol in expected if symbol.lower() not in normalized_actual]


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
