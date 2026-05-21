from __future__ import annotations

import ast
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
) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    chunks: list[dict[str, str]] = []
    for item in extracted_documented_blocks(text, language):
        name = item["name"]
        body = item["body"]
        chunks.append(
            {
                "path": f"api-reference/source/{slugify(name)}.md",
                "title": name,
                "source_url": f"{source_url}#{slugify(name)}",
                "markdown": f"# {name}\n\n```{language}\n{body.strip()}\n```\n",
                "metadata": {
                    "source_type": "github",
                    "document_role": "sdk_source",
                    "operation": {
                        "kind": infer_operation_kind(name, item.get("signature", ""), body),
                        "operation_name": name,
                        "sdk_class": item.get("class_name", ""),
                        "sdk_method": item.get("method_name") or name,
                        "import_path": item.get("import_path", ""),
                        "language": language,
                        "required_params": item.get("required_params", []),
                        "optional_params": item.get("optional_params", []),
                        "request_schema": item.get("signature", ""),
                        "response_schema": item.get("return_type", ""),
                        "auth_requirements": [],
                        "source_type": "github",
                    },
                },
            }
        )
        if len(chunks) >= limit:
            return chunks
    return chunks


def extracted_documented_blocks(text: str, language: str) -> list[dict[str, Any]]:
    if language in {"typescript", "javascript"}:
        return ts_js_blocks(text, language=language)
    if language == "python":
        return python_blocks(text)
    if language == "go":
        return go_blocks(text)
    if language == "rust":
        return rust_blocks(text)
    return []


def ts_js_blocks(text: str, *, language: str = "typescript") -> list[dict[str, Any]]:
    parsed = ts_js_blocks_tree_sitter(text, language=language)
    return parsed or ts_js_blocks_regex(text)


def ts_js_blocks_regex(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"(?ms)(/\*\*.*?\*/\s*(?:export\s+)?(?:async\s+)?(?:function|class|interface|type|const|let|var)\s+([A-Za-z_$][\w$]*).*?)(?=\n/\*\*|\Z)"
    )
    output: list[dict[str, Any]] = []
    for body, name in pattern.findall(text):
        signature = first_code_line_after_comment(body)
        output.append(
            {
                "name": name,
                "body": trim_block(body),
                "signature": signature,
                "method_name": name,
                "required_params": structured_signature_params(signature),
                "optional_params": structured_signature_params(signature, optional=True),
                "return_type": ts_return_type(signature),
            }
        )
    return output


def ts_js_blocks_tree_sitter(text: str, *, language: str) -> list[dict[str, Any]]:
    try:
        from tree_sitter_language_pack import get_parser  # type: ignore

        parser = get_parser("typescript" if language == "typescript" else "javascript")
        tree = parser.parse(text.encode("utf-8"))
    except Exception:
        return []
    lines = text.splitlines()
    comments = ts_js_doc_comments(tree.root_node, text)
    output: list[dict[str, Any]] = []

    def walk(node: Any, class_name: str = "") -> None:
        current_class = class_name
        if node.type == "class_declaration":
            current_class = node_name(node, text) or class_name
        if node.type in TS_JS_DECLARATION_NODES:
            comment = nearest_doc_comment(node, comments)
            if comment:
                name = node_name(node, text)
                if name:
                    node_text = text[node.start_byte : node.end_byte]
                    body = f"{comment['text']}\n{node_text}"
                    signature = first_code_line_after_comment(body)
                    method_name = name
                    display_name = f"{class_name}.{name}" if class_name and node.type == "method_definition" else name
                    output.append(
                        {
                            "name": display_name,
                            "body": trim_block(body),
                            "signature": signature,
                            "class_name": class_name if node.type == "method_definition" else (name if node.type == "class_declaration" else ""),
                            "method_name": method_name,
                            "required_params": structured_signature_params(signature),
                            "optional_params": structured_signature_params(signature, optional=True),
                            "return_type": ts_return_type(signature),
                        }
                    )
        for child in getattr(node, "children", []):
            walk(child, current_class)

    walk(tree.root_node)
    return dedupe_blocks(output)


TS_JS_DECLARATION_NODES = {
    "class_declaration",
    "function_declaration",
    "method_definition",
    "interface_declaration",
    "type_alias_declaration",
    "lexical_declaration",
    "variable_declaration",
}


def ts_js_doc_comments(root: Any, text: str) -> list[dict[str, Any]]:
    comments: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if node.type == "comment":
            body = text[node.start_byte : node.end_byte]
            if body.lstrip().startswith("/**"):
                comments.append(
                    {
                        "start_byte": node.start_byte,
                        "end_byte": node.end_byte,
                        "start_line": point_row(node.start_point),
                        "end_line": point_row(node.end_point),
                        "text": body,
                    }
                )
        for child in getattr(node, "children", []):
            walk(child)

    walk(root)
    return comments


def nearest_doc_comment(node: Any, comments: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        comment
        for comment in comments
        if int(comment["end_byte"]) <= int(node.start_byte) and 0 <= point_row(node.start_point) - int(comment["end_line"]) <= 2
    ]
    return candidates[-1] if candidates else None


def node_name(node: Any, text: str) -> str:
    for child in getattr(node, "children", []):
        if child.type in {"identifier", "type_identifier", "property_identifier"}:
            return text[child.start_byte : child.end_byte]
        if child.type == "variable_declarator":
            nested = node_name(child, text)
            if nested:
                return nested
    return ""


def point_row(point: Any) -> int:
    if hasattr(point, "row"):
        return int(point.row)
    try:
        return int(point[0])
    except Exception:
        return 0


def dedupe_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for block in blocks:
        key = (str(block.get("name") or ""), str(block.get("signature") or ""))
        if key in seen:
            continue
        seen.add(key)
        output.append(block)
    return output


def python_blocks(text: str) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return python_blocks_regex(text)
    lines = text.splitlines()
    output: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not ast.get_docstring(node):
            continue
        class_name = parent_class_name(tree, node)
        name = f"{class_name}.{node.name}" if class_name and not isinstance(node, ast.ClassDef) else node.name
        start = max(int(getattr(node, "lineno", 1)) - 1, 0)
        end = min(int(getattr(node, "end_lineno", start + 1)), len(lines))
        signature = python_signature(node)
        output.append(
            {
                "name": name,
                "body": trim_block("\n".join(lines[start:end])),
                "signature": signature,
                "class_name": class_name if not isinstance(node, ast.ClassDef) else node.name,
                "method_name": node.name,
                "required_params": python_params(node, optional=False),
                "optional_params": python_params(node, optional=True),
                "return_type": python_return_type(node),
            }
        )
    return output


def python_blocks_regex(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"(?ms)((?:class|def)\s+([A-Za-z_]\w*)[^\n]*:\n\s+(?:\"\"\".*?\"\"\"|'''.*?''').*?)(?=\n(?:class|def)\s|\Z)"
    )
    return [{"name": name, "body": trim_block(body), "signature": body.splitlines()[0].strip(), "method_name": name} for body, name in pattern.findall(text)]


def go_blocks(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(r"(?ms)((?://[^\n]+\n)+func\s+([A-Za-z_]\w*)[^{]+{.*?)(?=\n(?://[^\n]+\n)+func\s|\Z)")
    return [{"name": name, "body": trim_block(body), "signature": first_matching_line(body, r"\bfunc\b"), "method_name": name} for body, name in pattern.findall(text)]


def rust_blocks(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(r"(?ms)(((?:///[^\n]+\n)+\s*pub\s+(?:async\s+)?(?:fn|struct|enum|trait)\s+([A-Za-z_]\w*)).*?)(?=\n(?:///[^\n]+\n)+\s*pub\s|\Z)")
    return [{"name": name, "body": trim_block(body), "signature": first_matching_line(body, r"\b(?:fn|struct|enum|trait)\b"), "method_name": name} for body, name in pattern.findall(text)]


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


def first_code_line_after_comment(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("*", "/*", "//")):
            continue
        return stripped.rstrip("{")
    return ""


def first_matching_line(body: str, pattern: str) -> str:
    for line in body.splitlines():
        if re.search(pattern, line):
            return line.strip().rstrip("{")
    return ""


def structured_signature_params(signature: str, *, optional: bool = False) -> list[dict[str, Any]]:
    match = re.search(r"\((?P<params>[^)]*)\)", signature)
    if not match:
        return []
    output: list[dict[str, Any]] = []
    for raw in match.group("params").split(","):
        part = raw.strip()
        if not part:
            continue
        is_optional = "?" in part.split(":", 1)[0] or "=" in part
        if is_optional != optional:
            continue
        name = re.sub(r"[^A-Za-z0-9_$].*$", "", part.split(":", 1)[0].strip()).strip()
        type_name = part.split(":", 1)[1].split("=", 1)[0].strip() if ":" in part else ""
        if name:
            output.append({"name": name, "type": type_name, "required": not optional})
    return output


def ts_return_type(signature: str) -> str:
    match = re.search(r"\)\s*:\s*([^={;]+)", signature)
    return match.group(1).strip() if match else ""


def parent_class_name(tree: ast.AST, target: ast.AST) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for child in ast.walk(node):
            if child is target:
                return node.name
    return ""


def python_signature(node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    if isinstance(node, ast.ClassDef):
        bases = ", ".join(ast.unparse(base) for base in node.bases)
        return f"class {node.name}({bases})" if bases else f"class {node.name}"
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    params = ", ".join(python_arg_signature(arg) for arg in node.args.args)
    if node.args.vararg:
        params = ", ".join(part for part in (params, "*" + node.args.vararg.arg) if part)
    if node.args.kwarg:
        params = ", ".join(part for part in (params, "**" + node.args.kwarg.arg) if part)
    returns = f" -> {ast.unparse(node.returns)}" if node.returns is not None else ""
    return f"{prefix} {node.name}({params}){returns}"


def python_arg_signature(arg: ast.arg) -> str:
    annotation = f": {ast.unparse(arg.annotation)}" if arg.annotation is not None else ""
    return f"{arg.arg}{annotation}"


def python_params(node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef, *, optional: bool) -> list[dict[str, Any]]:
    if isinstance(node, ast.ClassDef):
        return []
    args = [arg for arg in node.args.args if arg.arg not in {"self", "cls"}]
    defaults = list(node.args.defaults)
    required_count = max(len(args) - len(defaults), 0)
    selected = args[required_count:] if optional else args[:required_count]
    output = []
    for arg in selected:
        output.append(
            {
                "name": arg.arg,
                "type": ast.unparse(arg.annotation) if arg.annotation is not None else "",
                "required": not optional,
            }
        )
    return output


def python_return_type(node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns is not None:
        return ast.unparse(node.returns)
    return ""


def infer_operation_kind(name: str, signature: str, body: str) -> str:
    haystack = f"{name} {signature} {body[:800]}".lower()
    for kind, pattern in (
        ("delete", r"\b(delete|remove|destroy)\b"),
        ("update", r"\b(update|patch|modify|edit|set_)\b"),
        ("create", r"\b(create|new_|insert|add|make)\b"),
        ("upload", r"\b(upload|file|document|pdf|image|audio)\b"),
        ("stream", r"\b(stream|websocket|sse|subscribe)\b"),
        ("list", r"\b(list|search|find|get_all)\b"),
        ("retrieve", r"\b(get|fetch|retrieve|read)\b"),
        ("auth", r"\b(auth|token|api_key|credential)\b"),
        ("config", r"\b(config|configure|settings|options)\b"),
        ("test", r"\b(test|mock|pytest|spec)\b"),
    ):
        if re.search(pattern, haystack):
            return kind
    return "operation"
