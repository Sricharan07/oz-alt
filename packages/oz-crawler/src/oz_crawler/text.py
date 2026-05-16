from __future__ import annotations

from urllib.parse import urlparse


TEXT_CONTENT_TYPES = {
    "application/json",
    "application/ld+json",
    "application/openapi+json",
    "application/x-yaml",
    "application/yaml",
    "application/xml",
    "text/html",
    "text/markdown",
    "text/plain",
    "text/x-markdown",
    "text/xml",
}

BINARY_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".eot",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".map",
    ".mjs",
    ".mp4",
    ".pdf",
    ".png",
    ".svg",
    ".tar",
    ".tgz",
    ".ttf",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}


def decode_text_response(data: bytes, content_type: str | None) -> str | None:
    if not is_text_content_type(content_type):
        return None
    if is_probably_binary_bytes(data):
        return None
    return data.decode("utf-8", errors="replace")


def is_text_content_type(content_type: str | None) -> bool:
    if not content_type:
        return True
    media_type = content_type.split(";", 1)[0].strip().lower()
    return (
        media_type in TEXT_CONTENT_TYPES
        or media_type.endswith("+json")
        or media_type.endswith("+xml")
        or media_type.endswith("+yaml")
    )


def is_textual_url_candidate(url: str) -> bool:
    path = urlparse(url).path.lower()
    return not any(path.endswith(extension) for extension in BINARY_EXTENSIONS)


def is_probably_binary_text(text: str) -> bool:
    if "\x00" in text:
        return True
    if not text:
        return False
    sample = text[:4096]
    replacement_count = sample.count("\ufffd")
    control_count = sum(1 for char in sample if ord(char) < 32 and char not in "\t\n\r")
    return (replacement_count + control_count) / max(len(sample), 1) > 0.05


def is_probably_binary_bytes(data: bytes) -> bool:
    if b"\x00" in data:
        return True
    if not data:
        return False
    sample = data[:4096]
    control_count = sum(1 for byte in sample if byte < 32 and byte not in (9, 10, 13))
    return control_count / max(len(sample), 1) > 0.05
