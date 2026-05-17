from __future__ import annotations

import re
from dataclasses import replace
from urllib.parse import urlparse

from oz_crawler.normalize import NormalizedPage


VERSION_RE = re.compile(r"^(?:v)?(\d+)(?:\.(\d+))?(?:\.(\d+))?$", re.I)
ARCHIVE_TOKENS = {"legacy", "deprecated", "old", "previous", "archive", "archives"}


def filter_current_version(
    pages: list[NormalizedPage],
    *,
    target_version: str,
) -> tuple[list[NormalizedPage], list[dict[str, object]]]:
    target_major = major_version(target_version)
    if target_major is None:
        return pages, []
    output: list[NormalizedPage] = []
    rejected: list[dict[str, object]] = []
    for page in pages:
        markers = version_markers(page)
        if should_reject(markers, target_major):
            rejected.append(
                {
                    "title": page.title,
                    "source_url": page.source_url,
                    "score": 0,
                    "reasons": [f"archived version markers {sorted(markers)} do not match {target_version}"],
                    "content_type": "archived_version",
                }
            )
            continue
        output.append(replace(page, markdown=page.markdown))
    return output, rejected


def should_reject(markers: set[str], target_major: int) -> bool:
    if markers & ARCHIVE_TOKENS:
        return True
    majors = {int(marker) for marker in markers if marker.isdigit()}
    return bool(majors and target_major not in majors)


def version_markers(page: NormalizedPage) -> set[str]:
    parsed = urlparse(page.source_url)
    parts = [part.lower() for part in parsed.path.split("/") if part]
    parts.extend(part.lower() for part in (page.path or "").split("/") if part)
    markers: set[str] = set()
    for part in parts:
        normalized = part.removesuffix(".md").removesuffix(".html")
        if normalized in ARCHIVE_TOKENS:
            markers.add(normalized)
            continue
        match = VERSION_RE.match(normalized)
        if match:
            markers.add(match.group(1))
    return markers


def major_version(version: str) -> int | None:
    match = re.search(r"\d+", version)
    if not match:
        return None
    return int(match.group(0))
