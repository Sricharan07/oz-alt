from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

BASELINE_DENIED_PATHS = [
    "changelog",
    "changes",
    "license",
    "code-of-conduct",
    "conduct",
    "archive",
    "old",
    "deprecated",
    "legacy",
    "previous",
    "outdated",
    "superseded",
    "community",
    "contributing",
    "contribution-guide",
    "docs-contribution",
    "docs-writing",
    "style-guide",
    "styleguides",
    "authors",
    "maintainers",
    "governance",
    "roadmap",
    "/i18n/",
    "/translations/",
    "/locales/",
    "/zh/",
    "/ja/",
    "/ko/",
    "/ru/",
    "/fr/",
    "/de/",
    "/es/",
    "/pt/",
    "/it/",
]


@dataclass(frozen=True)
class LibraryProfile:
    vendor: str
    library: str
    allowed_hosts: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    denied_paths: list[str] = field(default_factory=list)
    preferred_urls: list[str] = field(default_factory=list)
    source_roots: list[str] = field(default_factory=list)
    source_priorities: dict[str, int] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    products: list[str] = field(default_factory=list)
    current_patterns: list[str] = field(default_factory=list)
    deprecated_patterns: list[str] = field(default_factory=list)
    legacy_patterns: list[str] = field(default_factory=list)
    version_strategy: str = "semver"
    required_topics: list[str] = field(default_factory=list)
    expected_symbols: list[str] = field(default_factory=list)
    source_file_patterns: list[str] = field(default_factory=list)
    min_quality_score: float = 0.35
    min_documents: int = 2
    max_junk_ratio: float = 0.25
    needs_js: bool = False
    include_source_files: bool = False
    target_language: str = "en"

    @property
    def key(self) -> str:
        return f"{self.vendor}/{self.library}"


def load_profile(registry_root: Path, vendor: str, library: str) -> LibraryProfile | None:
    profiles_path = profile_path_for_registry_root(registry_root)
    if not profiles_path.exists():
        return None
    data = json.loads(profiles_path.read_text(encoding="utf-8"))
    profiles = data.get("libraries", data)
    if not isinstance(profiles, list):
        return None
    key = f"{vendor}/{library}"
    for row in profiles:
        if not isinstance(row, dict) or row.get("library") != key:
            continue
        return profile_from_row(row, vendor=vendor, library=library)
    return None


def profile_path_for_registry_root(registry_root: Path) -> Path:
    if registry_root.name == "fixtures":
        return registry_root.parent / "library_profiles.json"
    return registry_root / "library_profiles.json"


def profile_from_row(row: dict[str, Any], *, vendor: str, library: str) -> LibraryProfile:
    return LibraryProfile(
        vendor=vendor,
        library=library,
        allowed_hosts=list_of_strings(row.get("allowed_hosts")),
        allowed_paths=list_of_strings(row.get("allowed_paths")),
        denied_paths=list_of_strings(row.get("denied_paths")),
        preferred_urls=list_of_strings(row.get("preferred_urls")),
        source_roots=list_of_strings(row.get("source_roots")),
        source_priorities=dict_of_ints(row.get("source_priorities")),
        aliases=list_of_strings(row.get("aliases")),
        products=list_of_strings(row.get("products")),
        current_patterns=list_of_strings(row.get("current_patterns")),
        deprecated_patterns=list_of_strings(row.get("deprecated_patterns")),
        legacy_patterns=list_of_strings(row.get("legacy_patterns")),
        version_strategy=str(row.get("version_strategy") or "semver").strip().lower() or "semver",
        required_topics=list_of_strings(row.get("required_topics")),
        expected_symbols=list_of_strings(row.get("expected_symbols")),
        source_file_patterns=list_of_strings(row.get("source_file_patterns")),
        min_quality_score=float(row.get("min_quality_score", 0.35)),
        min_documents=int(row.get("min_documents", 2)),
        max_junk_ratio=float(row.get("max_junk_ratio", 0.25)),
        needs_js=bool_value(row.get("needs_js")),
        include_source_files=bool_value(row.get("include_source_files")),
        target_language=str(row.get("target_language") or "en").strip().lower() or "en",
    )


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def dict_of_ints(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    output: dict[str, int] = {}
    for key, item in value.items():
        try:
            output[str(key)] = int(item)
        except (TypeError, ValueError):
            continue
    return output


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def url_allowed_by_profile(url: str, profile: LibraryProfile | None) -> bool:
    if profile is None:
        return True
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    host = parsed.netloc.lower()
    path = parsed.path.lower() or "/"
    if parsed.scheme not in {"http", "https"} or not host:
        return False
    if profile.allowed_hosts and not host_matches(host, profile.allowed_hosts):
        return False
    denied_paths = [*BASELINE_DENIED_PATHS, *profile.denied_paths]
    if denied_paths and path_matches(path, denied_paths, root_matches_all=False):
        return False
    if profile.allowed_paths and not path_matches(path, profile.allowed_paths, root_matches_all=True):
        return False
    return True


def host_matches(host: str, allowed_hosts: list[str]) -> bool:
    for allowed in allowed_hosts:
        allowed = allowed.lower()
        if host == allowed or host.endswith(f".{allowed}"):
            return True
    return False


def path_matches(path: str, patterns: list[str], *, root_matches_all: bool) -> bool:
    for pattern in patterns:
        normalized = pattern.lower().strip()
        if not normalized:
            continue
        if normalized == "/":
            if root_matches_all or path == "/":
                return True
            continue
        if normalized.startswith("/"):
            if path == normalized or path.startswith(normalized.rstrip("/") + "/"):
                return True
            continue
        if normalized.strip("/") in path.strip("/").split("/"):
            return True
        if normalized in path:
            return True
    return False
