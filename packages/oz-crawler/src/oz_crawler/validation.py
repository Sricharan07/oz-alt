from __future__ import annotations

import json
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
        total_seen = len(pages) + len(rejected)
        junk_ratio = len(rejected) / total_seen if total_seen else 1.0
        if junk_ratio > profile.max_junk_ratio:
            errors.append(f"junk ratio {junk_ratio:.2f} exceeds {profile.max_junk_ratio:.2f}")
    else:
        warnings.append("no library profile found")

    if not chunks:
        errors.append("no indexable chunks generated")

    metrics = {
        "documents": len(pages),
        "rejected_documents": len(rejected),
        "chunks": len(chunks),
        "symbols": len(symbols),
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
