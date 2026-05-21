from __future__ import annotations

import re
from typing import Any

from oz_api.retrieval_packet_terms import canonical_language

FENCE_RE = re.compile(r"(?ms)^\s*(`{3,}|~{3,})[ \t]*([^\n`]*)\n(?P<code>.*?)(?:^\s*\1\s*$)")
FENCE_START_RE = re.compile(r"(?m)^\s*(`{3,}|~{3,})[ \t]*([^\n`]*)\n")


def extract_code_blocks(text: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    for match in FENCE_RE.finditer(text):
        code = match.group("code").strip()
        if not code:
            continue
        language = (match.group(2) or "").strip().split()
        blocks.append(
            {
                "language": language[0] if language else "",
                "code": code,
            }
        )
    if not blocks and "```" in text:
        blocks.extend(extract_partial_code_blocks(text))
    loose_source = FENCE_RE.sub("", text)
    blocks.extend(extract_loose_code_blocks(loose_source))
    return dedupe_code_blocks(blocks)


def dedupe_code_blocks(blocks: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[str] = set()
    for block in blocks:
        code = (block.get("code") or "").strip()
        if not code:
            continue
        key = re.sub(r"\s+", " ", code.lower())
        if key in seen:
            continue
        seen.add(key)
        output.append({"language": block.get("language") or "", "code": code})
    return output


def extract_partial_code_blocks(text: str) -> list[dict[str, str]]:
    """Recover fenced code when a context row was truncated before the close."""

    blocks: list[dict[str, str]] = []
    for match in FENCE_START_RE.finditer(text):
        fence = match.group(1)
        language = (match.group(2) or "").strip().split()
        start = match.end()
        close = re.search(rf"(?m)^\s*{re.escape(fence)}\s*$", text[start:])
        end = start + close.start() if close else len(text)
        code = text[start:end].strip()
        if code:
            blocks.append({"language": language[0] if language else "", "code": code})
    return blocks


def extract_loose_code_blocks(text: str) -> list[dict[str, str]]:
    """Extract short unfenced code runs from imperfect markdown.

    Some source docs lose fences during upstream llms-full generation. We only
    recover dense runs of code-like lines and stop before prose so these blocks
    can be used as source-backed implementation snippets without admitting
    normal paragraphs as code.
    """

    blocks: list[dict[str, str]] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if loose_code_line(stripped):
            current.append(line)
            continue
        if not stripped and current:
            current.append("")
            continue
        if current:
            block = "\n".join(current).strip()
            if loose_code_block(block):
                blocks.append({"language": infer_code_language(block), "code": block})
            current = []
    if current:
        block = "\n".join(current).strip()
        if loose_code_block(block):
            blocks.append({"language": infer_code_language(block), "code": block})
    return blocks[:4]


def loose_code_line(line: str) -> bool:
    if not line:
        return False
    if line.startswith(("#", ">", "|", "-", "*")):
        return False
    patterns = (
        r"^(from|import)\s+[\w.]+",
        r"^[A-Za-z_]\w*\s*=",
        r"^[A-Za-z_][\w.]*\s*=",
        r"^[A-Za-z_][\w.]*\s*\(",
        r"^(await|return|async\s+with|with|if|for|while)\b",
        r"^(const|let|var)\s+\w+\s*=",
        r"^(export\s+)?(async\s+)?function\s+\w+",
        r"^(pip|npm|pnpm|yarn|uv|curl)\s+",
        r"^(class|def|async\s+def)\s+\w+",
        r"^\w+\.\w+",
    )
    return any(re.search(pattern, line) for pattern in patterns)


def loose_code_block(code: str) -> bool:
    lines = [line for line in code.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    return sum(1 for line in lines if loose_code_line(line.strip())) >= 2 and code_like_block(code)


def code_like_block(code: str) -> bool:
    stripped = code.strip()
    if not stripped:
        return False
    markdown_noise = (
        "[`" in stripped
        or "](" in stripped
        or re.search(r"(?m)^\s*[-*]\s+\S", stripped) is not None
        or re.search(r"(?m)^\s{0,3}#{1,6}\s+\S", stripped) is not None
    )
    signals = [
        r"(?m)^\s*(from|import)\s+[\w.]+",
        r"(?m)^\s*(export\s+)?(async\s+)?function\s+\w+",
        r"(?m)^\s*(const|let|var)\s+\w+\s*=",
        r"(?m)^\s*class\s+\w+",
        r"(?m)^\s*(async\s+)?def\s+\w+\s*\(",
        r"(?m)^\s*(return|await)\s+",
        r"(?m)^\s*(pip|npm|pnpm|yarn|uv|curl)\s+",
        r"[A-Za-z_][\w.]*\s*\(",
        r"=>\s*[{(]",
        r"[{};]",
    ]
    signal_count = sum(1 for pattern in signals if re.search(pattern, stripped))
    if signal_count >= 2:
        return True
    if signal_count == 1 and not markdown_noise and len(stripped.splitlines()) <= 16:
        return True
    lowered_first = stripped.splitlines()[0].strip().lower()
    if lowered_first.startswith(("the ", "this ", "because ", "when ", "you ", "to ", "for ")):
        return False
    return signal_count > 0 and not markdown_noise


def infer_code_language(code: str) -> str:
    lowered = code.lower()
    if re.search(r"(?m)^\s*import\s+\w+\s+from\s+['\"]", code):
        return "typescript"
    if re.search(r"(?m)^\s*(const|let|var|export)\s+", code):
        return "typescript"
    if re.search(r"(?m)^\s*(from|import)\s+[\w.]+", code) or "os.getenv" in lowered or "print(" in lowered:
        return "python"
    if re.search(r"(?m)^\s*import\s+[{*]", code):
        return "typescript"
    if re.search(r"(?m)^\s*(pip|uv)\s+", code):
        return "bash"
    if re.search(r"(?m)^\s*(npm|pnpm|yarn)\s+", code):
        return "bash"
    return ""


def code_block_matches_requested_language(block: dict[str, str], code: str, languages: set[str]) -> bool:
    language = canonical_language(str(block.get("language") or ""))
    if not language:
        language = canonical_language(infer_code_language(code))
    if not language:
        return True
    if language in languages:
        return True
    if language == "typescript" and "javascript" in languages:
        return True
    if language == "javascript" and "typescript" in languages:
        return True
    return False
