from __future__ import annotations

import re
from fnmatch import fnmatch
from typing import Any


SUPPORTED_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs")


def source_code_chunks(
    text: str,
    source_url: str,
    *,
    language: str,
    limit: int,
) -> list[dict[str, str]]:
    if limit <= 0:
        return []
    chunks: list[dict[str, str]] = []
    for name, body in extracted_documented_blocks(text, language):
        chunks.append(
            {
                "path": f"api-reference/source/{slugify(name)}.md",
                "title": name,
                "source_url": f"{source_url}#{slugify(name)}",
                "markdown": f"# {name}\n\n**Source:** {source_url}#{slugify(name)}\n\n```{language}\n{body.strip()}\n```\n",
            }
        )
        if len(chunks) >= limit:
            return chunks
    return chunks


def extracted_documented_blocks(text: str, language: str) -> list[tuple[str, str]]:
    if language in {"typescript", "javascript"}:
        return ts_js_blocks(text)
    if language == "python":
        return python_blocks(text)
    if language == "go":
        return go_blocks(text)
    if language == "rust":
        return rust_blocks(text)
    return []


def ts_js_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r"(?ms)(/\*\*.*?\*/\s*(?:export\s+)?(?:async\s+)?(?:function|class|interface|type|const|let|var)\s+([A-Za-z_$][\w$]*).*?)(?=\n/\*\*|\Z)"
    )
    return [(name, trim_block(body)) for body, name in pattern.findall(text)]


def python_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r"(?ms)((?:class|def)\s+([A-Za-z_]\w*)[^\n]*:\n\s+(?:\"\"\".*?\"\"\"|'''.*?''').*?)(?=\n(?:class|def)\s|\Z)"
    )
    return [(name, trim_block(body)) for body, name in pattern.findall(text)]


def go_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?ms)((?://[^\n]+\n)+func\s+([A-Za-z_]\w*)[^{]+{.*?)(?=\n(?://[^\n]+\n)+func\s|\Z)")
    return [(name, trim_block(body)) for body, name in pattern.findall(text)]


def rust_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?ms)(((?:///[^\n]+\n)+\s*pub\s+(?:async\s+)?(?:fn|struct|enum|trait)\s+([A-Za-z_]\w*)).*?)(?=\n(?:///[^\n]+\n)+\s*pub\s|\Z)")
    return [(name, trim_block(body)) for body, name in pattern.findall(text)]


def trim_block(text: str, max_lines: int = 120) -> str:
    lines = text.strip().splitlines()
    return "\n".join(lines[:max_lines])


def source_language_for_path(path: str) -> str:
    lower = path.lower()
    if lower.endswith((".ts", ".tsx")):
        return "typescript"
    if lower.endswith((".js", ".jsx")):
        return "javascript"
    if lower.endswith(".py"):
        return "python"
    if lower.endswith(".go"):
        return "go"
    if lower.endswith(".rs"):
        return "rust"
    return "text"


def source_path_allowed(path: str, patterns: list[str]) -> bool:
    lower = path.lower()
    if not lower.endswith(SUPPORTED_EXTENSIONS):
        return False
    if not patterns:
        return lower.startswith(("src/", "lib/", "packages/", "pkg/", "examples/")) or any(
            part in lower for part in ("/src/", "/lib/", "/packages/", "/pkg/", "/examples/")
        )
    return any(matches_pattern(lower, pattern.lower().strip()) for pattern in patterns if pattern.strip())


def matches_pattern(path: str, pattern: str) -> bool:
    if not pattern:
        return False
    if any(token in pattern for token in ("*", "?", "[")):
        return fnmatch(path, pattern)
    if pattern.startswith("*."):
        return path.endswith(pattern[1:])
    return pattern in path


def slugify(value: Any) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value).lower()).strip("-._")
    return slug[:100] or "source"
