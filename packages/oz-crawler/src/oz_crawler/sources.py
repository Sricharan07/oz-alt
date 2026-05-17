from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

from oz_crawler.normalize import NormalizedPage
from oz_crawler.profiles import LibraryProfile, url_allowed_by_profile
from oz_crawler.security import assert_public_http_url, fetch_public_url
from oz_crawler.splitting import document_path, split_llms_full
from oz_crawler.text import decode_text_response

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceArtifact:
    path: str
    title: str
    source_url: str
    markdown: str


def collect_source_artifacts(
    seed_url: str,
    pages: list[NormalizedPage],
    *,
    profile: LibraryProfile | None = None,
    max_documents: int = 24,
) -> list[SourceArtifact]:
    urls = sorted(
        {
            seed_url,
            *(profile.preferred_urls if profile else []),
            *common_source_urls(seed_url),
            *(url for page in pages for url in extract_urls(page.markdown, base_url=page.source_url)),
        }
    )
    urls = [url for url in urls if url_allowed_by_profile(url, profile)]
    artifacts: list[SourceArtifact] = []
    artifacts.extend(llms_artifacts(seed_url, profile=profile, limit=max_documents))
    artifacts.extend(markdown_url_artifacts(urls, profile=profile, limit=max_documents))
    artifacts.extend(openapi_artifacts(urls, profile=profile, limit=max_documents))
    artifacts.extend(type_definition_artifacts(urls, profile=profile, limit=max_documents))
    artifacts.extend(github_docs_artifacts(urls, profile=profile, limit=max_documents))
    return dedupe_artifacts(artifacts)[:max_documents]


def common_source_urls(seed_url: str) -> list[str]:
    parsed = urlparse(seed_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return []
    base = f"{parsed.scheme}://{parsed.netloc}"
    return [
        f"{base}/openapi.json",
        f"{base}/openapi.yaml",
        f"{base}/swagger.json",
        f"{base}/swagger.yaml",
    ]


def llms_artifacts(seed_url: str, *, profile: LibraryProfile | None, limit: int) -> list[SourceArtifact]:
    parsed = urlparse(seed_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return []
    base = f"{parsed.scheme}://{parsed.netloc}"
    output: list[SourceArtifact] = []
    for name in ("/llms-full.txt", "/docs/llms-full.txt", "/llms.txt", "/docs/llms.txt"):
        url = base + name
        if not url_allowed_by_profile(url, profile):
            continue
        text = fetch_text(url)
        if not text or looks_like_html(text):
            continue
        if "llms-full" not in name:
            continue
        pages = split_llms_full(text, source_url=url)
        for page in pages:
            output.append(
                SourceArtifact(
                    path=document_path(page.source_url, page.title, "guide"),
                    title=page.title,
                    source_url=page.source_url,
                    markdown=f"# {page.title}\n\n**Source:** {page.source_url}\n\n{page.markdown.strip()}\n",
                )
            )
            if len(output) >= limit:
                return output
    return output


def markdown_url_artifacts(
    urls: list[str],
    *,
    profile: LibraryProfile | None,
    limit: int,
) -> list[SourceArtifact]:
    output: list[SourceArtifact] = []
    for url in urls:
        if not url_allowed_by_profile(url, profile):
            continue
        path = urlparse(url).path.lower()
        if not re.search(r"\.(md|mdx)$", path):
            continue
        text = fetch_text(url)
        if not text or looks_like_html(text):
            continue
        title = markdown_title(text) or url
        output.append(
            SourceArtifact(
                path=document_path(url, title, "guide"),
                title=title,
                source_url=url,
                markdown=f"# {title}\n\n**Source:** {url}\n\n{text.strip()}\n",
            )
        )
        if len(output) >= limit:
            break
    return output


def openapi_artifacts(urls: list[str], *, profile: LibraryProfile | None, limit: int) -> list[SourceArtifact]:
    output: list[SourceArtifact] = []
    for url in urls:
        if not url_allowed_by_profile(url, profile):
            continue
        path = urlparse(url).path.lower()
        if not re.search(r"(openapi|swagger).*\.(json|ya?ml)$", path):
            continue
        text = fetch_text(url)
        if not text or looks_like_html(text):
            continue
        output.append(
            SourceArtifact(
                path=f"api-reference/openapi-{slugify(url)}.md",
                title="OpenAPI Reference",
                source_url=url,
                markdown=render_openapi(text, url),
            )
        )
        if len(output) >= limit:
            break
    return output


def type_definition_artifacts(urls: list[str], *, profile: LibraryProfile | None, limit: int) -> list[SourceArtifact]:
    output: list[SourceArtifact] = []
    for url in urls:
        if not url_allowed_by_profile(url, profile):
            continue
        path = urlparse(url).path.lower()
        if not (path.endswith(".d.ts") or path.endswith(".pyi")):
            continue
        text = fetch_text(url)
        if not text:
            continue
        language = "typescript" if path.endswith(".d.ts") else "python"
        output.append(
            SourceArtifact(
                path=f"api-reference/types-{slugify(url)}.md",
                title="Type Definitions",
                source_url=url,
                markdown=f"# Type Definitions\n\n**Source:** {url}\n\n```{language}\n{text.strip()}\n```\n",
            )
        )
        if len(output) >= limit:
            break
    return output


def github_docs_artifacts(urls: list[str], *, profile: LibraryProfile | None, limit: int) -> list[SourceArtifact]:
    repos = sorted({repo for url in urls for repo in github_repo(url)})
    output: list[SourceArtifact] = []
    for owner, repo in repos:
        output.extend(github_root_artifacts(owner, repo, profile=profile, limit=limit - len(output)))
        for folder in ("docs", "documentation"):
            remaining = limit - len(output)
            if remaining <= 0:
                return output
            output.extend(github_folder_artifacts(owner, repo, folder, profile=profile, limit=remaining))
    return output


def github_root_artifacts(
    owner: str,
    repo: str,
    *,
    profile: LibraryProfile | None,
    limit: int,
) -> list[SourceArtifact]:
    output: list[SourceArtifact] = []
    for name in ("README.md", "api.md", "helpers.md"):
        if len(output) >= limit:
            break
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{name}"
        if not url_allowed_by_profile(url, profile):
            continue
        artifact = github_file_artifact(owner, repo, name, url)
        if artifact:
            output.append(artifact)
    return output


def github_folder_artifacts(
    owner: str,
    repo: str,
    folder: str,
    *,
    profile: LibraryProfile | None,
    limit: int,
    depth: int = 0,
) -> list[SourceArtifact]:
    if limit <= 0 or depth > 3:
        return []
    listing = fetch_json(f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}")
    if not isinstance(listing, list):
        return []
    output: list[SourceArtifact] = []
    for item in listing:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        item_path = str(item.get("path") or name)
        if item.get("type") == "dir":
            output.extend(
                github_folder_artifacts(
                    owner,
                    repo,
                    item_path,
                    profile=profile,
                    limit=limit - len(output),
                    depth=depth + 1,
                )
            )
        else:
            artifact = github_file_artifact(owner, repo, name, item.get("download_url"))
            if artifact:
                output.append(artifact)
        if len(output) >= limit:
            return output
    return output


def github_file_artifact(owner: str, repo: str, name: str, download_url: Any) -> SourceArtifact | None:
    if not download_url or not re.search(r"\.(md|mdx|d\.ts|pyi)$", name, re.I):
        return None
    text = fetch_text(str(download_url))
    if not text:
        return None
    return SourceArtifact(
        path=f"guides/github-{slugify(owner + '-' + repo + '-' + name)}.md",
        title=f"{owner}/{repo} {name}",
        source_url=str(download_url),
        markdown=markdown_for_github_file(name, text, str(download_url)),
    )


def render_openapi(text: str, source_url: str) -> str:
    parsed = parse_openapi(text)
    if not parsed:
        return f"# OpenAPI Reference\n\n**Source:** {source_url}\n\n```yaml\n{text.strip()}\n```\n"
    title = nested_string(parsed, ["info", "title"]) or "OpenAPI Reference"
    lines = ["# " + title, "", f"**Source:** {source_url}", ""]
    paths = parsed.get("paths") if isinstance(parsed, dict) else None
    if isinstance(paths, dict):
        for route, operations in sorted(paths.items()):
            if not isinstance(operations, dict):
                continue
            for method, operation in sorted(operations.items()):
                if method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options"}:
                    continue
                summary = operation.get("summary") if isinstance(operation, dict) else ""
                operation_id = operation.get("operationId") if isinstance(operation, dict) else ""
                lines.extend([f"## {method.upper()} {route}", "", str(summary or operation_id or "").strip(), ""])
    return "\n".join(lines).strip() + "\n"


def parse_openapi(text: str) -> dict | None:
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return parse_yaml_like_openapi(text)


def parse_yaml_like_openapi(text: str) -> dict | None:
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
        field_match = re.match(r"^\s{6}(summary|operationId):\s*(.+)$", raw)
        if field_match and current_path and current_method:
            paths[current_path][current_method][field_match.group(1)] = field_match.group(2).strip("'\"")
    return {"paths": paths} if paths else None


def looks_like_html(text: str) -> bool:
    prefix = text.lstrip()[:128].lower()
    return prefix.startswith("<!doctype html") or prefix.startswith("<html") or "<body" in prefix


def nested_string(value: dict, path: list[str]) -> str:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return current if isinstance(current, str) else ""


def markdown_for_github_file(name: str, text: str, source_url: str) -> str:
    if re.search(r"\.(d\.ts|pyi)$", name, re.I):
        language = "typescript" if name.endswith(".d.ts") else "python"
        return f"# {name}\n\n**Source:** {source_url}\n\n```{language}\n{text.strip()}\n```\n"
    return f"**Source:** {source_url}\n\n{text.strip()}\n"


def markdown_title(text: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match:
            return match.group(1).strip()
    return ""


def extract_urls(text: str, *, base_url: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>\"]+", text)
    urls.extend(urljoin(base_url, link) for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text))
    return [url.split("#", 1)[0] for url in urls]


def github_repo(url: str) -> list[tuple[str, str]]:
    parsed = urlparse(url)
    if parsed.netloc.lower() != "github.com":
        return []
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2:
        return [(parts[0], parts[1].removesuffix(".git"))]
    return []


def fetch_json(url: str):
    text = fetch_text(url)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def fetch_text(url: str) -> str | None:
    try:
        assert_public_http_url(url)
        response = fetch_public_url(url, timeout=20)
        return decode_text_response(response.body, response.headers.get("content-type"))
    except Exception as exc:
        LOGGER.info("optional source fetch failed for %s: %s", url, exc)
        return None


def dedupe_artifacts(artifacts: list[SourceArtifact]) -> list[SourceArtifact]:
    seen: set[str] = set()
    output: list[SourceArtifact] = []
    for artifact in artifacts:
        key = artifact.source_url or artifact.path
        if key in seen or artifact.path in seen:
            continue
        seen.add(key)
        seen.add(artifact.path)
        output.append(artifact)
    return output


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug[:100] or "source"
