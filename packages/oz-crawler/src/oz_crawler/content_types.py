from __future__ import annotations

import re
from urllib.parse import urlparse


CONFIG_LANGS = {"json", "yaml", "yml", "toml", "ini", "env"}
CLI_RE = re.compile(r"(?m)^\s*(?:\$|npx|npm|pnpm|yarn|cargo|pip|uv|docker|kubectl|aws|oz)\s+\S+")
ERROR_RE = re.compile(r"\b(?:ERR_[A-Z0-9_]+|[A-Z][A-Z0-9_]{3,}|[A-Z]?[a-z]+Error|[45]\d{2})\b")
API_HEADING_RE = re.compile(r"(?mi)^#{1,4}\s+.*\b(api|reference|parameters?|returns?|methods?|functions?|classes?)\b")
CODE_FENCE_RE = re.compile(r"(?ms)```([A-Za-z0-9_+.-]*)\n(.*?)```")
INDENTED_CODE_RE = re.compile(r"(?m)^(?: {4}|\t)(?:const|let|var|import|export|def|class|function|return|curl|npm|npx|pip|uv|docker)\b")
CONFIG_FILE_RE = re.compile(r"\b(?:package\.json|tsconfig\.json|next\.config\.[cm]?[jt]s|vite\.config\.[cm]?[jt]s|tailwind\.config\.[cm]?[jt]s|docker-compose\.ya?ml|\.env)\b", re.I)


def classify_content_type(source_url: str, markdown: str) -> str:
    lower_url = source_url.lower()
    lower_path = urlparse(source_url).path.lower()
    text_head = markdown[:1600]
    lower_head = text_head.lower()
    if lower_url.endswith("/llms.txt") or "index of all docs" in lower_head:
        return "index"
    if lower_url.endswith((".d.ts", ".pyi")) or "type definitions" in lower_head:
        return "api_reference"
    if any(token in lower_path for token in ("/api-reference", "/reference", "/api/")) or API_HEADING_RE.search(text_head):
        return "api_reference"
    if any(token in lower_path for token in ("/examples", "/example", "examples/")):
        return "code_example"
    if has_config_block(text_head):
        return "config"
    if CLI_RE.search(text_head):
        return "cli"
    if ERROR_RE.search(text_head) and any(term in lower_head for term in ("cause", "fix", "solution", "error")):
        return "error_ref"
    if CODE_FENCE_RE.search(text_head):
        return "code_example"
    return "prose"


def block_content_type(source_url: str, block: str, page_type: str) -> str:
    if page_type == "api_reference":
        return "api_reference"
    if has_config_block(block):
        return "config"
    if CLI_RE.search(block):
        return "cli"
    if ERROR_RE.search(block) and any(term in block.lower() for term in ("cause", "fix", "solution", "error")):
        return "error_ref"
    if CODE_FENCE_RE.search(block) or INDENTED_CODE_RE.search(block):
        return "code_example"
    if page_type in {"code_example", "config", "cli", "error_ref"}:
        return page_type
    return "prose"


def has_config_block(text: str) -> bool:
    for match in CODE_FENCE_RE.finditer(text):
        language = match.group(1).strip().lower()
        if language in CONFIG_LANGS:
            return True
    if CONFIG_FILE_RE.search(text):
        return True
    return looks_like_inline_json_or_yaml(text)


def looks_like_inline_json_or_yaml(text: str) -> bool:
    stripped = text.strip()
    if re.search(r"(?m)^\s{0,4}[A-Za-z_][\w.-]*:\s+[^:\n]+$", stripped) and len(stripped.splitlines()) >= 3:
        return True
    return bool(re.search(r"(?s)\{\s*\"[A-Za-z_][^\"]+\"\s*:", stripped))
