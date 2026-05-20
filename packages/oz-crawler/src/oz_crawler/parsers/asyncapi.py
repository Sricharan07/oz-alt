from __future__ import annotations

import json
import re
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore


def asyncapi_chunks(text: str, source_url: str, *, limit: int) -> list[dict[str, Any]]:
    parsed = parse_asyncapi(text)
    if not parsed:
        return []
    title = nested_string(parsed, ["info", "title"]) or "AsyncAPI"
    channels = parsed.get("channels")
    if not isinstance(channels, dict):
        return []
    components = parsed.get("components") if isinstance(parsed.get("components"), dict) else {}
    output: list[dict[str, Any]] = []
    for channel_name, channel in sorted(channels.items()):
        if not isinstance(channel, dict):
            continue
        operations = channel_operations(channel, parsed)
        if not operations:
            operations = [("message", channel)]
        for action, operation in operations:
            doc = channel_doc(
                title,
                action,
                str(channel_name),
                operation,
                source_url,
                components=components,
            )
            if doc:
                output.append(doc)
            if len(output) >= limit:
                return output
    return output


def channel_operations(channel: dict[str, Any], root: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    output: list[tuple[str, dict[str, Any]]] = []
    for action in ("publish", "subscribe"):
        operation = resolve_ref(channel.get(action), root)
        if isinstance(operation, dict):
            output.append((action, operation))
    return output


def channel_doc(
    title: str,
    action: str,
    channel_name: str,
    operation: dict[str, Any],
    source_url: str,
    *,
    components: dict[str, Any],
) -> dict[str, Any] | None:
    summary = str(operation.get("summary") or operation.get("operationId") or "").strip()
    description = str(operation.get("description") or "").strip()
    message = resolve_message(operation.get("message"), components)
    message_name = str(message.get("name") or message.get("title") or "").strip() if isinstance(message, dict) else ""
    payload = message.get("payload") if isinstance(message, dict) else None
    headers = message.get("headers") if isinstance(message, dict) else None
    examples = message.get("examples") if isinstance(message, dict) else None

    lines = [f"# {title}: {action.title()} {channel_name}", ""]
    if summary:
        lines.extend([summary, ""])
    if description:
        lines.extend([description, ""])
    lines.extend(["## Channel", "", f"- Action: `{action}`", f"- Channel: `{channel_name}`", ""])
    if message_name:
        lines.extend(["## Message", "", f"- Name: `{message_name}`", ""])
    if headers:
        lines.extend(["## Headers", "", "```json", json.dumps(resolve_schema(headers, components), indent=2, sort_keys=True)[:5000], "```", ""])
    if payload:
        lines.extend(["## Payload", "", "```json", json.dumps(resolve_schema(payload, components), indent=2, sort_keys=True)[:8000], "```", ""])
    if examples:
        lines.extend(["## Examples", "", "```json", json.dumps(examples, indent=2, sort_keys=True)[:8000], "```", ""])
    content = "\n".join(lines).strip()
    if not content:
        return None
    slug = slugify(f"{action}-{channel_name}")
    return {
        "path": f"api-reference/asyncapi/{slug}.md",
        "title": f"{action.title()} {channel_name}",
        "source_url": f"{source_url}#{slug}",
        "markdown": content + "\n",
        "metadata": {
            "source_type": "asyncapi",
            "protocol": "websocket",
            "channel": channel_name,
            "action": action,
            "message": message_name,
        },
    }


def resolve_message(value: Any, components: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_component_ref(value, components)
    if isinstance(resolved, dict):
        if isinstance(resolved.get("oneOf"), list) and resolved["oneOf"]:
            first = resolve_component_ref(resolved["oneOf"][0], components)
            return first if isinstance(first, dict) else resolved
        return resolved
    return {}


def resolve_schema(value: Any, components: dict[str, Any], *, depth: int = 0) -> Any:
    if depth > 8:
        return value
    resolved = resolve_component_ref(value, components)
    if isinstance(resolved, dict):
        output: dict[str, Any] = {}
        for key, item in resolved.items():
            if key == "$ref":
                continue
            output[key] = resolve_schema(item, components, depth=depth + 1)
        return output
    if isinstance(resolved, list):
        return [resolve_schema(item, components, depth=depth + 1) for item in resolved[:20]]
    return resolved


def resolve_component_ref(value: Any, components: dict[str, Any]) -> Any:
    if not isinstance(value, dict):
        return value
    ref = value.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/components/"):
        return value
    current: Any = components
    for part in ref.removeprefix("#/components/").split("/"):
        if not isinstance(current, dict):
            return value
        current = current.get(part)
    return current if current is not None else value


def resolve_ref(value: Any, root: dict[str, Any]) -> Any:
    if not isinstance(value, dict):
        return value
    ref = value.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return value
    current: Any = root
    for part in ref.removeprefix("#/").split("/"):
        if not isinstance(current, dict):
            return value
        current = current.get(part)
    return current if current is not None else value


def parse_asyncapi(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) and "asyncapi" in value else None
    except json.JSONDecodeError:
        pass
    if yaml is not None:
        try:
            value = yaml.safe_load(text)
            return value if isinstance(value, dict) and "asyncapi" in value else None
        except Exception:
            return None
    return parse_yaml_like_asyncapi(text)


def parse_yaml_like_asyncapi(text: str) -> dict[str, Any] | None:
    channels: dict[str, dict[str, Any]] = {}
    current_channel = ""
    current_action = ""
    for raw in text.splitlines():
        channel_match = re.match(r"^\s{2}([^\\s].*?):\s*$", raw)
        if channel_match and "/" in channel_match.group(1):
            current_channel = channel_match.group(1).strip("'\"")
            channels.setdefault(current_channel, {})
            current_action = ""
            continue
        action_match = re.match(r"^\s{4}(publish|subscribe):\s*$", raw, re.I)
        if action_match and current_channel:
            current_action = action_match.group(1).lower()
            channels[current_channel].setdefault(current_action, {})
            continue
        field_match = re.match(r"^\s{6}(summary|operationId|description):\s*(.+)$", raw)
        if field_match and current_channel and current_action:
            channels[current_channel][current_action][field_match.group(1)] = field_match.group(2).strip("'\"")
    return {"asyncapi": "unknown", "channels": channels} if channels else None


def nested_string(value: dict[str, Any], path: list[str]) -> str:
    current: Any = value
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return current if isinstance(current, str) else ""


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug[:100] or "channel"
