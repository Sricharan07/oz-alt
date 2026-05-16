from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class LibraryProfile:
    vendor: str
    library: str
    allowed_hosts: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    denied_paths: list[str] = field(default_factory=list)
    preferred_urls: list[str] = field(default_factory=list)
    required_topics: list[str] = field(default_factory=list)
    expected_symbols: list[str] = field(default_factory=list)
    min_quality_score: float = 0.35
    min_documents: int = 2
    max_junk_ratio: float = 0.25

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
        required_topics=list_of_strings(row.get("required_topics")),
        expected_symbols=list_of_strings(row.get("expected_symbols")),
        min_quality_score=float(row.get("min_quality_score", 0.35)),
        min_documents=int(row.get("min_documents", 2)),
        max_junk_ratio=float(row.get("max_junk_ratio", 0.25)),
    )


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


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
    if profile.denied_paths and path_matches(path, profile.denied_paths):
        return False
    if profile.allowed_paths and not path_matches(path, profile.allowed_paths):
        return False
    return True


def host_matches(host: str, allowed_hosts: list[str]) -> bool:
    for allowed in allowed_hosts:
        allowed = allowed.lower()
        if host == allowed or host.endswith(f".{allowed}"):
            return True
    return False


def path_matches(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        normalized = pattern.lower().strip()
        if not normalized:
            continue
        if normalized == "/":
            if path == "/":
                return True
            continue
        if path.startswith(normalized):
            return True
    return False
