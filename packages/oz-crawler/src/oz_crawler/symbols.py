from __future__ import annotations

import re
from pathlib import Path

from oz_crawler.normalize import NormalizedPage
from oz_crawler.profiles import LibraryProfile

SYMBOL_STOP_WORDS = {"and", "as", "for", "from", "in", "is", "of", "or", "that", "the", "to", "with"}


class ExtractedSymbol:
    def __init__(self, *, name: str, kind: str, signature: str, example: str) -> None:
        self.name = name
        self.kind = kind
        self.signature = signature
        self.example = example

    def render(self, source_url: str, language: str) -> str:
        return "\n".join(
            [
                f"# {self.name}",
                "",
                f"**Kind:** {self.kind}",
                f"**Signature:** `{self.signature}`",
                f"**Source:** {source_url}",
                "",
                "## Example",
                "",
                f"```{language or 'text'}",
                self.example.strip(),
                "```",
                "",
            ]
        )


def write_symbols(target: Path, pages: list[NormalizedPage], *, profile: LibraryProfile | None = None) -> None:
    for symbol, payload in extract_symbols(pages, profile=profile).items():
        (target / "_symbols" / f"{symbol}.md").write_text(payload, encoding="utf-8")


def extract_symbols(pages: list[NormalizedPage], *, profile: LibraryProfile | None = None) -> dict[str, str]:
    output: dict[str, str] = {}
    seen_lower: set[str] = set()
    if profile is not None:
        for expected in profile.expected_symbols:
            payload = symbol_from_expected(pages, expected)
            if payload:
                output[expected] = payload
                seen_lower.add(expected.lower())
    for page in pages:
        for symbol, language in extract_page_symbols(page, profile=profile):
            if symbol.name.lower() in seen_lower:
                continue
            output.setdefault(symbol.name, symbol.render(page.source_url, language))
            seen_lower.add(symbol.name.lower())
    return output


def extract_page_symbol_names(page: NormalizedPage, *, profile: LibraryProfile | None = None) -> list[str]:
    names = [symbol.name for symbol, _language in extract_page_symbols(page, profile=profile)]
    if profile is not None:
        lower_text = page.markdown.lower()
        for expected in profile.expected_symbols:
            if expected.lower() in lower_text:
                names.append(expected)
    return sorted(set(names), key=lambda item: item.lower())


def extract_page_symbols(
    page: NormalizedPage,
    *,
    profile: LibraryProfile | None = None,
) -> list[tuple[ExtractedSymbol, str]]:
    if not is_symbol_source_page(page):
        return []
    output: list[tuple[ExtractedSymbol, str]] = []
    for language, code in code_blocks(page.markdown):
        for symbol in symbols_from_code(code, language):
            output.append((symbol, language))
    for symbol in symbols_from_markdown(page, profile=profile):
        output.append((symbol, "markdown"))
    return output


def is_symbol_source_page(page: NormalizedPage) -> bool:
    path = (page.path or "").lower()
    metadata = page.source_metadata if isinstance(page.source_metadata, dict) else {}
    source_type = str(metadata.get("source_type") or page.source_type).lower()
    document_role = str(metadata.get("document_role") or "").lower()
    if path.startswith("_symbols/") or path.startswith("api-reference/"):
        return True
    if source_type == "openapi" or document_role in {"api_reference", "sdk_source", "type_definition"}:
        return True
    if page.content_type == "api_reference" and "/api" in page.source_url.lower():
        return True
    return False


def symbols_from_code(code: str, language: str) -> list[ExtractedSymbol]:
    return dedupe_symbols([*tree_sitter_symbols(code, language), *regex_symbols(code)])


def tree_sitter_symbols(code: str, language: str) -> list[ExtractedSymbol]:
    parser = tree_sitter_parser(language)
    if parser is None:
        return []
    try:
        tree = parser.parse(code)
        source: str | bytes = code
    except TypeError:
        try:
            source = code.encode("utf-8")
            tree = parser.parse(source)
        except Exception:
            return []
    except Exception:
        return []
    output: list[ExtractedSymbol] = []
    walk_tree(tree.root_node, source, output)
    return output


def tree_sitter_parser(language: str):
    normalized = {"js": "javascript", "jsx": "javascript", "ts": "typescript", "tsx": "tsx", "py": "python"}.get(
        language.lower(), language.lower()
    )
    if normalized not in {"javascript", "typescript", "tsx", "python"}:
        return None
    try:
        from tree_sitter_language_pack import get_parser  # type: ignore
    except ImportError:
        return None
    try:
        return get_parser(normalized)
    except Exception:
        return None


def walk_tree(node, source: str | bytes, output: list[ExtractedSymbol]) -> None:
    node_type = str(getattr(node, "type", ""))
    name_node = node.child_by_field_name("name") if hasattr(node, "child_by_field_name") else None
    if name_node is not None and node_type in SYMBOL_NODE_KINDS:
        name = node_text(name_node, source)
        if is_symbol_name(name):
            output.append(
                ExtractedSymbol(
                    name=name,
                    kind=SYMBOL_NODE_KINDS[node_type],
                    signature=first_line(node_text(node, source)),
                    example=node_text(node, source),
                )
            )
    for child in getattr(node, "children", []):
        walk_tree(child, source, output)


SYMBOL_NODE_KINDS = {
    "class_declaration": "class",
    "function_declaration": "function",
    "interface_declaration": "type",
    "method_definition": "method",
    "type_alias_declaration": "type",
    "lexical_declaration": "constant",
}


def node_text(node, source: str | bytes) -> str:
    if isinstance(source, bytes):
        return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
    return source[node.start_byte : node.end_byte]


def regex_symbols(code: str) -> list[ExtractedSymbol]:
    patterns = [
        ("function", r"export\s+(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"),
        ("class", r"(?:export\s+)?class\s+([A-Z][A-Za-z0-9_$]*)"),
        ("type", r"(?:export\s+)?(?:interface|type)\s+([A-Z][A-Za-z0-9_$]*)"),
        ("constant", r"export\s+const\s+([A-Za-z_$][\w$]*)"),
        ("function", r"def\s+([A-Za-z_][\w]*)\s*\("),
        ("class", r"class\s+([A-Z][A-Za-z0-9_]*)\s*[:(]"),
    ]
    symbols: list[ExtractedSymbol] = []
    for kind, pattern in patterns:
        for match in re.finditer(pattern, code):
            name = match.group(1)
            if is_symbol_name(name):
                symbols.append(ExtractedSymbol(name=name, kind=kind, signature=first_line(code), example=code))
    return symbols


def symbols_from_markdown(
    page: NormalizedPage,
    *,
    profile: LibraryProfile | None = None,
) -> list[ExtractedSymbol]:
    output: list[ExtractedSymbol] = []
    expected = expected_symbol_lookup(profile)
    for line in page.markdown.splitlines():
        match = re.match(r"^#{1,4}\s+(`?)([A-Za-z_$][A-Za-z0-9_.$-]*)`?", line.strip())
        if not match:
            continue
        fenced = bool(match.group(1))
        name = match.group(2).strip("`")
        normalized = safe_symbol_name(name).lower()
        if is_symbol_name(name) and looks_like_public_symbol(name, fenced=fenced, expected=normalized in expected):
            output.append(
                ExtractedSymbol(
                    name=safe_symbol_name(name),
                    kind="heading",
                    signature=name,
                    example=context_for_symbol(page.markdown, name),
                )
            )
    return output


def expected_symbol_lookup(profile: LibraryProfile | None) -> set[str]:
    if profile is None:
        return set()
    return {safe_symbol_name(symbol).lower() for symbol in profile.expected_symbols}


def symbol_from_expected(pages: list[NormalizedPage], expected: str) -> str | None:
    needle = expected.lower()
    for page in pages:
        if needle not in page.markdown.lower():
            continue
        symbol = ExtractedSymbol(
            name=expected,
            kind="expected",
            signature=expected,
            example=context_for_symbol(page.markdown, expected),
        )
        return symbol.render(page.source_url, "markdown")
    return None


def context_for_symbol(markdown: str, symbol: str, *, radius: int = 8) -> str:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if symbol.lower() in line.lower():
            start = max(0, index - radius)
            end = min(len(lines), index + radius + 1)
            return "\n".join(lines[start:end]).strip()
    return symbol


def looks_like_public_symbol(name: str, *, fenced: bool = False, expected: bool = False) -> bool:
    if expected:
        return True
    if fenced and re.search(r"[A-Z_$]|\.", name):
        return True
    if name.startswith("use") and len(name) > 3 and name[3].isupper():
        return True
    return bool(re.search(r"[.$]", name))


def safe_symbol_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-") or "symbol"


def dedupe_symbols(symbols: list[ExtractedSymbol]) -> list[ExtractedSymbol]:
    seen: set[str] = set()
    output: list[ExtractedSymbol] = []
    for symbol in symbols:
        if symbol.name in seen:
            continue
        seen.add(symbol.name)
        output.append(symbol)
    return output


def is_symbol_name(name: str) -> bool:
    return bool(name) and name.lower() not in SYMBOL_STOP_WORDS


def code_blocks(markdown: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"```([A-Za-z0-9_-]*)\n(.*?)```", re.DOTALL)
    return [(match.group(1), match.group(2)) for match in pattern.finditer(markdown)]


def first_line(code: str) -> str:
    for line in code.splitlines():
        if line.strip():
            return line.strip()
    return ""
