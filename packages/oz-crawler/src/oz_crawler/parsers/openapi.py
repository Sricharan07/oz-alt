from __future__ import annotations

import json
import re
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def openapi_chunks(text: str, source_url: str, *, limit: int) -> list[dict[str, Any]]:
    parsed = parse_openapi(text)
    if not parsed:
        return []
    title = nested_string(parsed, ["info", "title"]) or "OpenAPI"
    paths = parsed.get("paths")
    if not isinstance(paths, dict):
        return []
    components = parsed.get("components") if isinstance(parsed.get("components"), dict) else {}
    security = parsed.get("security") if isinstance(parsed.get("security"), list) else []
    output: list[dict[str, str]] = []
    for route, operations in sorted(paths.items()):
        if not isinstance(operations, dict):
            continue
        for method, operation in sorted(operations.items()):
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            output.append(endpoint_doc(title, method.upper(), str(route), operation, source_url, components=components, root_security=security))
            if len(output) >= limit:
                return output
    return output


def endpoint_doc(
    title: str,
    method: str,
    route: str,
    operation: dict[str, Any],
    source_url: str,
    *,
    components: dict[str, Any],
    root_security: list[Any],
) -> dict[str, Any]:
    summary = str(operation.get("summary") or operation.get("operationId") or "").strip()
    description = str(operation.get("description") or "").strip()
    params = operation.get("parameters") if isinstance(operation.get("parameters"), list) else []
    operation_id = str(operation.get("operationId") or "").strip()
    tags = [str(tag) for tag in operation.get("tags", []) if str(tag).strip()] if isinstance(operation.get("tags"), list) else []
    lines = [f"# {title}: {method} {route}", ""]
    if summary:
        lines.extend([summary, ""])
    if description:
        lines.extend([description, ""])
    if operation_id or tags:
        lines.extend(["## Metadata", ""])
        if operation_id:
            lines.append(f"- Operation ID: `{operation_id}`")
        if tags:
            lines.append(f"- Tags: {', '.join(f'`{tag}`' for tag in tags)}")
        lines.append("")
    security = operation.get("security") if isinstance(operation.get("security"), list) else root_security
    if security:
        lines.extend(["## Auth", "", "```json", json.dumps(security, indent=2, sort_keys=True)[:3000], "```", ""])
    structured_params = structured_parameters(params, components)
    if params:
        lines.extend(["## Parameters", ""])
        for param in params:
            param = resolve_schema(param, components)
            if isinstance(param, dict):
                name = str(param.get("name") or "")
                location = str(param.get("in") or "")
                required = " required" if param.get("required") else ""
                desc = str(param.get("description") or "").strip()
                schema = param.get("schema")
                type_name = schema_type(schema, components)
                suffix = f" `{type_name}`" if type_name else ""
                lines.append(f"- `{name}` ({location}{required}){suffix}: {desc}".strip())
        lines.append("")
    request_body = operation.get("requestBody")
    resolved_request_body: Any = None
    if isinstance(request_body, dict):
        request_body = resolve_schema(request_body, components)
        resolved_request_body = request_body
        lines.extend(["## Request Body", "", "```json", json.dumps(request_body, indent=2, sort_keys=True)[:4000], "```", ""])
    responses = operation.get("responses")
    structured_responses: list[dict[str, Any]] = []
    if isinstance(responses, dict):
        lines.extend(["## Responses", ""])
        for code, response in sorted(responses.items()):
            response = resolve_schema(response, components)
            desc = response.get("description") if isinstance(response, dict) else ""
            schema = response_schema(response, components) if isinstance(response, dict) else None
            type_name = schema_type(schema, components)
            structured_responses.append(
                {
                    "status": str(code),
                    "description": str(desc or ""),
                    "schema": schema,
                    "schema_type": type_name,
                }
            )
            suffix = f" `{type_name}`" if type_name else ""
            lines.append(f"- `{code}`{suffix}: {desc}")
        lines.append("")
    examples = extract_examples(operation)
    if examples:
        lines.extend(["## Examples", "", "```json", json.dumps(examples, indent=2, sort_keys=True)[:8000], "```", ""])
    slug = slugify(route)
    return {
        "path": f"api-reference/openapi/{method.lower()}-{slugify(route)}.md",
        "title": f"{method} {route}",
        "source_url": f"{source_url}#{method.lower()}-{slug}",
        "markdown": "\n".join(lines).strip() + "\n",
        "metadata": {
            "source_type": "openapi",
            "protocol": "rest",
            "method": method,
            "endpoint": route,
            "operation_id": operation_id,
            "tags": tags,
            "operation": {
                "kind": infer_operation_kind(method, operation_id, summary, route),
                "operation_name": operation_id or f"{method} {route}",
                "operation_id": operation_id,
                "http_method": method,
                "endpoint": route,
                "sdk_class": "",
                "sdk_method": "",
                "language": "",
                "required_params": [param for param in structured_params if param.get("required")],
                "optional_params": [param for param in structured_params if not param.get("required")],
                "request_schema": resolved_request_body,
                "response_schema": structured_responses,
                "auth_requirements": security,
                "source_type": "openapi",
            },
        },
    }


def structured_parameters(params: list[Any], components: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in params:
        param = resolve_schema(item, components)
        if not isinstance(param, dict):
            continue
        schema = resolve_schema(param.get("schema"), components)
        output.append(
            {
                "name": str(param.get("name") or ""),
                "in": str(param.get("in") or ""),
                "required": bool(param.get("required")),
                "description": str(param.get("description") or ""),
                "schema": schema if isinstance(schema, dict) else None,
                "schema_type": schema_type(schema, components),
            }
        )
    return [param for param in output if param["name"]]


def infer_operation_kind(method: str, operation_id: str, summary: str, route: str) -> str:
    haystack = f"{method} {operation_id} {summary} {route}".lower()
    if method == "GET":
        return "list" if re.search(r"\b(list|search|all|index)\b", haystack) or route.endswith("s") else "retrieve"
    if method == "POST":
        if re.search(r"\b(upload|file|document|pdf|image|audio)\b", haystack):
            return "upload"
        if re.search(r"\b(stream|sse|websocket)\b", haystack):
            return "stream"
        return "create"
    if method in {"PUT", "PATCH"}:
        return "update"
    if method == "DELETE":
        return "delete"
    return "operation"


def parse_openapi(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass
    if yaml is not None:
        try:
            value = yaml.safe_load(text)
            return value if isinstance(value, dict) and ("openapi" in value or "swagger" in value) else None
        except Exception:
            return None
    return parse_yaml_like_openapi(text)


def resolve_schema(value: Any, components: dict[str, Any], *, depth: int = 0) -> Any:
    if depth > 8:
        return value
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/"):
            resolved = lookup_component(ref, components)
            if resolved is not None:
                return resolve_schema(resolved, components, depth=depth + 1)
        output: dict[str, Any] = {}
        for key, item in value.items():
            output[key] = resolve_schema(item, components, depth=depth + 1)
        return output
    if isinstance(value, list):
        return [resolve_schema(item, components, depth=depth + 1) for item in value[:40]]
    return value


def lookup_component(ref: str, components: dict[str, Any]) -> Any:
    current: Any = components
    for part in ref.removeprefix("#/components/").split("/"):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def schema_type(schema: Any, components: dict[str, Any]) -> str:
    schema = resolve_schema(schema, components)
    if not isinstance(schema, dict):
        return ""
    if isinstance(schema.get("type"), str):
        type_name = schema["type"]
        if schema.get("format"):
            return f"{type_name}:{schema['format']}"
        return type_name
    if isinstance(schema.get("enum"), list):
        return "enum"
    if isinstance(schema.get("oneOf"), list):
        return "oneOf"
    if isinstance(schema.get("anyOf"), list):
        return "anyOf"
    if isinstance(schema.get("allOf"), list):
        return "allOf"
    return ""


def response_schema(response: dict[str, Any], components: dict[str, Any]) -> Any:
    content = response.get("content")
    if not isinstance(content, dict):
        return None
    for media in ("application/json", "application/problem+json", "text/event-stream"):
        media_obj = content.get(media)
        if isinstance(media_obj, dict) and media_obj.get("schema"):
            return media_obj.get("schema")
    for media_obj in content.values():
        if isinstance(media_obj, dict) and media_obj.get("schema"):
            return media_obj.get("schema")
    return None


def extract_examples(operation: dict[str, Any]) -> list[Any]:
    examples: list[Any] = []
    for key in ("examples", "x-codeSamples", "x-code-samples"):
        value = operation.get(key)
        if isinstance(value, list):
            examples.extend(value[:10])
        elif isinstance(value, dict):
            examples.append(value)
    return examples[:10]


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
