from __future__ import annotations

import json
import re
from typing import Any


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def openapi_chunks(text: str, source_url: str, *, limit: int) -> list[dict[str, str]]:
    parsed = parse_openapi(text)
    if not parsed:
        return []
    title = nested_string(parsed, ["info", "title"]) or "OpenAPI"
    paths = parsed.get("paths")
    if not isinstance(paths, dict):
        return []
    output: list[dict[str, str]] = []
    for route, operations in sorted(paths.items()):
        if not isinstance(operations, dict):
            continue
        for method, operation in sorted(operations.items()):
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            output.append(endpoint_doc(title, method.upper(), str(route), operation, source_url))
            if len(output) >= limit:
                return output
    return output


def endpoint_doc(title: str, method: str, route: str, operation: dict[str, Any], source_url: str) -> dict[str, str]:
    summary = str(operation.get("summary") or operation.get("operationId") or "").strip()
    description = str(operation.get("description") or "").strip()
    params = operation.get("parameters") if isinstance(operation.get("parameters"), list) else []
    lines = [f"# {title}: {method} {route}", ""]
    if summary:
        lines.extend([summary, ""])
    if description:
        lines.extend([description, ""])
    if params:
        lines.extend(["## Parameters", ""])
        for param in params:
            if isinstance(param, dict):
                name = param.get("name", "")
                location = param.get("in", "")
                required = " required" if param.get("required") else ""
                desc = str(param.get("description") or "").strip()
                lines.append(f"- `{name}` ({location}{required}): {desc}".strip())
        lines.append("")
    request_body = operation.get("requestBody")
    if isinstance(request_body, dict):
        lines.extend(["## Request Body", "", "```json", json.dumps(request_body, indent=2, sort_keys=True)[:4000], "```", ""])
    responses = operation.get("responses")
    if isinstance(responses, dict):
        lines.extend(["## Responses", ""])
        for code, response in sorted(responses.items()):
            desc = response.get("description") if isinstance(response, dict) else ""
            lines.append(f"- `{code}`: {desc}")
        lines.append("")
    return {
        "path": f"api-reference/openapi/{method.lower()}-{slugify(route)}.md",
        "title": f"{method} {route}",
        "source_url": f"{source_url}#{method.lower()}-{slugify(route)}",
        "markdown": "\n".join(lines).strip() + "\n",
    }


def parse_openapi(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return parse_yaml_like_openapi(text)


def parse_yaml_like_openapi(text: str) -> dict[str, Any] | None:
    paths: dict[str, dict[str, dict[str, str]]] = {}
    current_path = ""
    current_method = ""
    for raw in text.splitlines():
        path_match = re.match(r"^\s{2}(/[^\s:]+):\s*$", raw)
        if path_match:
            current_path = path_match.group(1)
            paths.setdefault(current_path, {})
            continue
        method_match = re.match(r"^\s{4}(get|post|put|patch|delete|head|options):\s*$", raw, re.I)
        if method_match and current_path:
            current_method = method_match.group(1).lower()
            paths[current_path].setdefault(current_method, {})
            continue
        field_match = re.match(r"^\s{6}(summary|operationId|description):\s*(.+)$", raw)
        if field_match and current_path and current_method:
            paths[current_path][current_method][field_match.group(1)] = field_match.group(2).strip("'\"")
    return {"paths": paths} if paths else None


def nested_string(value: dict[str, Any], path: list[str]) -> str:
    current: Any = value
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return current if isinstance(current, str) else ""


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug[:100] or "endpoint"
