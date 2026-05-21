from __future__ import annotations

import re
from typing import Any


EXPORT_RE = re.compile(
    r"(?ms)^(export\s+(?:declare\s+)?(?:class|interface|type|function|const|enum)\s+[A-Za-z_$][\w$]*.*?)(?=^export\s+(?:declare\s+)?(?:class|interface|type|function|const|enum)\s+|\Z)"
)
PYI_RE = re.compile(r"(?ms)^((?:class|def)\s+[A-Za-z_][\w_]*.*?)(?=^(?:class|def)\s+[A-Za-z_][\w_]*|\Z)")


def type_definition_chunks(text: str, source_url: str, *, language: str, limit: int) -> list[dict[str, Any]]:
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
                "markdown": f"# {name}\n\n```{language}\n{body}\n```\n",
                "metadata": {
                    "source_type": "github",
                    "document_role": "type_definition",
                    "operation": {
                        "kind": operation_kind(body),
                        "operation_name": name,
                        "sdk_class": class_name(body),
                        "sdk_method": name if callable_type(body) else "",
                        "import_path": "",
                        "language": language,
                        "required_params": signature_params(body, optional=False),
                        "optional_params": signature_params(body, optional=True),
                        "request_schema": body[:4000],
                        "response_schema": return_type(body),
                        "auth_requirements": [],
                        "source_type": "github",
                    },
                },
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


def callable_type(body: str) -> bool:
    return bool(re.search(r"\b(function|def)\b|\([^)]*\)\s*(?:=>|:|->)", body))


def class_name(body: str) -> str:
    match = re.search(r"\bclass\s+([A-Za-z_$][\w$]*)", body)
    return match.group(1) if match else ""


def operation_kind(body: str) -> str:
    lowered = body.lower()
    if re.search(r"\b(delete|remove|destroy)\b", lowered):
        return "delete"
    if re.search(r"\b(update|patch|modify|edit)\b", lowered):
        return "update"
    if re.search(r"\b(create|new|add|insert)\b", lowered):
        return "create"
    if re.search(r"\b(list|search|find|getall|get_all)\b", lowered):
        return "list"
    if re.search(r"\b(get|fetch|retrieve|read)\b", lowered):
        return "retrieve"
    if re.search(r"\b(config|options|settings)\b", lowered):
        return "config"
    return "operation"


def signature_params(body: str, *, optional: bool) -> list[dict[str, Any]]:
    match = re.search(r"\((?P<params>[^)]*)\)", body)
    if not match:
        return []
    output: list[dict[str, Any]] = []
    for raw in match.group("params").split(","):
        part = raw.strip()
        if not part or part in {"self", "cls"}:
            continue
        is_optional = "?" in part.split(":", 1)[0] or "=" in part
        if optional != is_optional:
            continue
        name = re.sub(r"[^A-Za-z0-9_$].*$", "", part.split(":", 1)[0].strip()).strip()
        type_name = part.split(":", 1)[1].split("=", 1)[0].strip() if ":" in part else ""
        if name:
            output.append({"name": name, "type": type_name, "required": not optional})
    return output


def return_type(body: str) -> str:
    match = re.search(r"\)\s*(?:=>|:|->)\s*([^;{\n]+)", body)
    return match.group(1).strip() if match else ""
