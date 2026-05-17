from __future__ import annotations

import re


EXPORT_RE = re.compile(
    r"(?ms)^(export\s+(?:declare\s+)?(?:class|interface|type|function|const|enum)\s+[A-Za-z_$][\w$]*.*?)(?=^export\s+(?:declare\s+)?(?:class|interface|type|function|const|enum)\s+|\Z)"
)
PYI_RE = re.compile(r"(?ms)^((?:class|def)\s+[A-Za-z_][\w_]*.*?)(?=^(?:class|def)\s+[A-Za-z_][\w_]*|\Z)")


def type_definition_chunks(text: str, source_url: str, *, language: str, limit: int) -> list[dict[str, str]]:
    pattern = EXPORT_RE if language == "typescript" else PYI_RE
    output: list[dict[str, str]] = []
    for match in pattern.finditer(text):
        body = match.group(1).strip()
        name = symbol_name(body)
        if not name:
            continue
        output.append(
            {
                "path": f"api-reference/types/{slugify(name)}.md",
                "title": name,
                "source_url": f"{source_url}#{slugify(name)}",
                "markdown": f"# {name}\n\n**Source:** {source_url}#{slugify(name)}\n\n```{language}\n{body}\n```\n",
            }
        )
        if len(output) >= limit:
            return output
    return output


def symbol_name(body: str) -> str:
    match = re.search(r"\b(?:class|interface|type|function|const|enum|def)\s+([A-Za-z_$][\w$]*)", body)
    return match.group(1) if match else ""


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug[:100] or "symbol"
