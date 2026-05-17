from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from oz_crawler.content_types import classify_content_type
from oz_crawler.normalize import NormalizedPage
from oz_crawler.profiles import LibraryProfile, url_allowed_by_profile


MARKETING_TERMS = {
    "pricing",
    "customer story",
    "gartner",
    "enterprise",
    "sales",
    "sign up",
    "log in",
    "try for free",
    "contact us",
    "newsletter",
}

DOC_TERMS = {
    "api",
    "reference",
    "guide",
    "example",
    "install",
    "configure",
    "function",
    "class",
    "method",
    "parameter",
    "request",
    "response",
}


@dataclass(frozen=True)
class QualityResult:
    score: float
    accepted: bool
    reasons: list[str]
    content_type: str


def score_page(page: NormalizedPage, profile: LibraryProfile | None) -> QualityResult:
    text = page.markdown.strip()
    lower = text.lower()
    reasons: list[str] = []
    score = 0.0

    if not url_allowed_by_profile(page.source_url, profile):
        return QualityResult(0.0, False, ["url rejected by library profile"], "junk")
    if page.source_url.lower().endswith(("/sitemap.xml", "/sitemap_index.xml")):
        return QualityResult(0.0, False, ["sitemap is discovery input, not documentation"], "junk")

    word_count = len(re.findall(r"\w+", lower))
    heading_count = len(re.findall(r"(?m)^#{1,4}\s+", text))
    code_blocks = len(re.findall(r"```", text)) // 2
    links = len(re.findall(r"\[[^\]]+\]\([^)]+\)", text))
    required_hits = required_topic_hits(lower, profile)
    marketing_hits = sum(1 for term in MARKETING_TERMS if term in lower)
    doc_hits = sum(1 for term in DOC_TERMS if term in lower)

    if word_count < 80:
        score -= 0.35
        reasons.append("too little documentation text")
    else:
        score += min(word_count / 1800, 0.35)

    if heading_count:
        score += min(heading_count * 0.035, 0.2)
    else:
        reasons.append("no headings")

    if code_blocks:
        score += min(code_blocks * 0.08, 0.24)

    if doc_hits:
        score += min(doc_hits * 0.035, 0.2)

    if required_hits:
        score += min(required_hits * 0.09, 0.3)

    if marketing_hits:
        score -= min(marketing_hits * 0.09, 0.45)
        reasons.append("marketing/login language")

    if nav_repetition_ratio(text) > 0.35:
        score -= 0.25
        reasons.append("navigation-heavy repeated text")

    generic_homepage = looks_like_generic_homepage(page)
    if generic_homepage:
        score -= 0.45
        reasons.append("generic homepage/search page")

    content_type = classify_content_type(page.source_url, text)
    if content_type in {"api_reference", "code_example", "config", "cli", "error_ref"}:
        score += 0.12
    if content_type == "index":
        score -= 0.1

    threshold = profile.min_quality_score if profile is not None else 0.18
    accepted = score >= threshold and not generic_homepage
    if not accepted and not reasons:
        reasons.append(f"quality score below {threshold:.2f}")
    return QualityResult(round(score, 4), accepted, reasons, content_type)


def required_topic_hits(lower: str, profile: LibraryProfile | None) -> int:
    if profile is None:
        return 0
    return sum(1 for topic in profile.required_topics if topic.lower() in lower)


def nav_repetition_ratio(text: str) -> float:
    lines = [line.strip().lower() for line in text.splitlines() if len(line.strip()) > 8]
    if not lines:
        return 0.0
    counts: dict[str, int] = {}
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
    repeated = sum(count for count in counts.values() if count > 2)
    return repeated / len(lines)


def looks_like_generic_homepage(page: NormalizedPage) -> bool:
    parsed = urlparse(page.source_url)
    path = parsed.path.strip("/")
    title = page.title.lower()
    lower = page.markdown.lower()
    if parsed.netloc == "github.com" and len(path.split("/")) <= 2:
        return True
    if "search code, repositories" in title or "search code, repositories" in lower[:400]:
        return True
    if "enter your email" in lower[:1200] and "sign up" in lower[:1200]:
        return True
    return False
