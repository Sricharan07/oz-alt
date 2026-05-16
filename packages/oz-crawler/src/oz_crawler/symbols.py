from __future__ import annotations

import re
from pathlib import Path

from oz_crawler.normalize import NormalizedPage

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


def write_symbols(target: Path, pages: list[NormalizedPage]) -> None:
    for symbol, payload in extract_symbols(pages).items():
        (target / "_symbols" / f"{symbol}.md").write_text(payload, encoding="utf-8")


def extract_symbols(pages: list[NormalizedPage]) -> dict[str, str]:
    output: dict[str, str] = {}
    for page in pages:
        for language, code in code_blocks(page.markdown):
            for symbol in symbols_from_code(code, language):
                output.setdefault(symbol.name, symbol.render(page.source_url, language))
    return output


def symbols_from_code(code: str, language: str) -> list[ExtractedSymbol]:
    return dedupe_symbols([*tree_sitter_symbols(code, language), *regex_symbols(code)])


def tree_sitter_symbols(code: str, language: str) -> list[ExtractedSymbol]:
    parser = tree_sitter_parser(language)
    if parser is None:
        return []
    tree = parser.parse(code.encode("utf-8"))
    source = code.encode("utf-8")
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


def walk_tree(node, source: bytes, output: list[ExtractedSymbol]) -> None:
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


def node_text(node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


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
