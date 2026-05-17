from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib import parse, request


def trust_score_for_entry(entry: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    urls = [str(url) for url in entry.get("source_urls", []) if str(url).strip()]
    source = first_source_url(entry) or ""
    source_count = len(urls)
    keyword_count = len(entry.get("keywords") or [])
    has_pack = bool(entry.get("pack_path"))
    https_sources = sum(1 for url in urls if parse.urlparse(url).scheme == "https")
    official_signal = official_source_signal(entry, urls)

    value = 0.22
    value += min(source_count, 4) * 0.05
    value += min(keyword_count, 20) * 0.004
    value += 0.08 if https_sources == source_count and source_count > 0 else 0.0
    value += 0.14 if official_signal else 0.0
    value += 0.08 if has_pack else 0.0

    github_url = next((url for url in urls if github_repo_from_url(url)), None)
    github_repo = github_repo_from_url(github_url or "")
    github_signals: dict[str, Any] = {}
    if github_repo:
        github_signals = github_repo_signals(github_repo)
        value += github_signal_score(github_signals)

    value = max(0.0, min(round(value, 4), 1.0))
    return value, {
        "source_count": source_count,
        "first_source_url": source,
        "https_source_count": https_sources,
        "official_source_signal": official_signal,
        "has_pack": has_pack,
        "keyword_count": keyword_count,
        "github_repo": "/".join(github_repo) if github_repo else None,
        "github": github_signals,
    }


def first_source_url(entry: dict[str, Any]) -> str | None:
    urls = entry.get("source_urls")
    if isinstance(urls, list) and urls:
        return str(urls[0])
    source = entry.get("source_url")
    return str(source) if source else None


def official_source_signal(entry: dict[str, Any], urls: list[str]) -> bool:
    vendor = normalize_name(str(entry.get("vendor") or ""))
    library = normalize_name(str(entry.get("library") or ""))
    for url in urls:
        parsed = parse.urlparse(url)
        host = normalize_name(parsed.netloc.removeprefix("www."))
        repo = github_repo_from_url(url)
        if repo:
            owner, name = (normalize_name(repo[0]), normalize_name(repo[1]))
            if owner == vendor or name == library or library.startswith(name) or name.startswith(library):
                return True
        if vendor and vendor in host:
            return True
        if library and library.replace("js", "") in host:
            return True
    return False


def github_repo_from_url(url: str) -> tuple[str, str] | None:
    parsed = parse.urlparse(url)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    owner = clean_repo_part(parts[0])
    repo = clean_repo_part(parts[1])
    if not owner or not repo:
        return None
    return owner, repo


def clean_repo_part(value: str) -> str:
    return re.sub(r"\.git$", "", value.strip())


def github_repo_signals(repo: tuple[str, str]) -> dict[str, Any]:
    if os.environ.get("OZ_TRUST_FETCH_GITHUB", "").strip().lower() not in {"1", "true", "yes"}:
        return {"network_fetch": "disabled"}
    owner, name = repo
    endpoint = f"https://api.github.com/repos/{parse.quote(owner)}/{parse.quote(name)}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "oz-indexer"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("OZ_GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(endpoint, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=float(os.environ.get("OZ_TRUST_HTTP_TIMEOUT_SECONDS", "8"))) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"network_fetch": "failed", "error": exc.__class__.__name__}
    if not isinstance(body, dict):
        return {"network_fetch": "invalid"}
    return {
        "network_fetch": "ok",
        "stars": numeric_int(body.get("stargazers_count")),
        "forks": numeric_int(body.get("forks_count")),
        "watchers": numeric_int(body.get("subscribers_count") or body.get("watchers_count")),
        "open_issues": numeric_int(body.get("open_issues_count")),
        "created_at": body.get("created_at"),
        "pushed_at": body.get("pushed_at"),
        "archived": bool(body.get("archived")),
        "disabled": bool(body.get("disabled")),
        "license": bool(body.get("license")),
    }


def github_signal_score(signals: dict[str, Any]) -> float:
    if signals.get("network_fetch") != "ok":
        return 0.0
    score = 0.0
    score += min(math.log10(int(signals.get("stars") or 0) + 1) / 6.0, 1.0) * 0.22
    score += min(math.log10(int(signals.get("forks") or 0) + 1) / 5.0, 1.0) * 0.07
    score += 0.04 if signals.get("license") else 0.0
    score += age_score(str(signals.get("created_at") or ""))
    score += recency_score(str(signals.get("pushed_at") or ""))
    if signals.get("archived") or signals.get("disabled"):
        score -= 0.30
    return score


def age_score(created_at: str) -> float:
    age_days = days_since(created_at)
    if age_days is None:
        return 0.0
    if age_days >= 365 * 3:
        return 0.06
    if age_days >= 365:
        return 0.04
    return 0.02


def recency_score(pushed_at: str) -> float:
    age_days = days_since(pushed_at)
    if age_days is None:
        return 0.0
    if age_days <= 180:
        return 0.08
    if age_days <= 730:
        return 0.04
    return 0.0


def days_since(value: str) -> int | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - parsed).days


def numeric_int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())
