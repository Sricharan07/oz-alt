from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

from oz_crawler.normalize import NormalizedPage, clean_markdown
from oz_crawler.parsers import openapi_chunks
from oz_crawler.parsers.source_code import source_language_for_path, source_path_allowed
from oz_crawler.profiles import LibraryProfile, url_allowed_by_profile
from oz_crawler.crawl_runtime import CrawlRunState
from oz_crawler.security import assert_public_http_url
from oz_crawler.source_fetch import fetch_json, fetch_text, github_repo, parse_http_url
from oz_crawler.splitting import document_path, split_llms_full
from oz_crawler.text import decode_text_response

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceArtifact:
    path: str
    title: str
    source_url: str
    markdown: str
    source_type: str = "website_url"
    canonical_url: str | None = None
    source_priority: int = 50
    discovered_from: str | None = None
    metadata: dict[str, Any] | None = None


def collect_source_artifacts(
    seed_url: str,
    pages: list[NormalizedPage],
    *,
    profile: LibraryProfile | None = None,
    state: CrawlRunState | None = None,
    max_documents: int = 240,
) -> list[SourceArtifact]:
    manifest_urls = llms_manifest_urls(seed_url, profile=profile, state=state, limit=source_budget("llms_txt", max_documents))
    urls = prioritized_urls(
        seed_url,
        preferred_urls=profile.preferred_urls if profile else [],
        discovered_urls=[
            url
            for page in pages
            for url in extract_urls(page.markdown, base_url=page.source_url)
        ]
        + manifest_urls,
    )
    explicit_urls = prioritized_urls(
        seed_url,
        preferred_urls=profile.preferred_urls if profile else [],
        discovered_urls=manifest_urls,
    )
    urls = [url for url in urls if url_allowed_by_profile(url, profile)]
    explicit_urls = [url for url in explicit_urls if url_allowed_by_profile(url, profile)]
    artifacts: list[SourceArtifact] = []
    artifacts.extend(llms_artifacts(seed_url, profile=profile, state=state, limit=source_budget("llms_txt", max_documents)))
    artifacts.extend(markdown_url_artifacts(urls, profile=profile, state=state, limit=source_budget("website_url", max_documents)))
    artifacts.extend(openapi_artifacts(urls, profile=profile, state=state, limit=source_budget("openapi", max_documents)))
    artifacts.extend(source_file_url_artifacts(urls, profile=profile, state=state, limit=source_budget("github", max_documents)))
    artifacts.extend(github_docs_artifacts(explicit_urls, profile=profile, state=state, limit=source_budget("github", max_documents)))
    deduped = dedupe_artifacts(artifacts)
    selected = select_artifacts_by_priority(deduped, max_documents)
    if state is not None and len(selected) < len(deduped):
        state.record_dead_letter(
            seed_url,
            stage="source_cap",
            error=f"source artifact cap hit: selected {len(selected)} of {len(deduped)} artifacts",
            attempts=1,
            transient=False,
        )
    return selected


def prioritized_urls(seed_url: str, *, preferred_urls: list[str], discovered_urls: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[tuple[int, int, str]] = []
    sources = [seed_url, *preferred_urls, *common_source_urls(seed_url), *discovered_urls]
    preferred = set(preferred_urls)
    for index, url in enumerate(sources):
        url = clean_candidate_url(url)
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        ordered.append((url_priority(url, preferred), index, url))
    ordered.sort(key=lambda item: (item[0], item[1]))
    return [url for _, _, url in ordered]


def url_priority(url: str, preferred_urls: set[str]) -> int:
    parsed = parse_http_url(url)
    if parsed is None:
        return 99
    lower = url.lower()
    path = parsed.path.lower()
    if url in preferred_urls:
        return 0
    if "llms-full.txt" in lower:
        return 1
    if lower.endswith("/llms.txt"):
        return 2
    if re.search(r"(openapi|swagger).*\.(json|ya?ml)$", path):
        return 3
    if path.endswith((".d.ts", ".pyi")):
        return 4
    if parsed.netloc.lower() in {"github.com", "raw.githubusercontent.com"}:
        return 5
    if path.endswith((".md", ".mdx")):
        return 6
    return 9


def source_budget(kind: str, max_documents: int) -> int:
    defaults = {
        "llms_txt": 2000,
        "website_url": 1200,
        "openapi": 2000,
        "github": 1200,
    }
    env_name = f"OZ_SOURCE_{kind.upper()}_LIMIT"
    try:
        configured = int(os.environ.get(env_name, str(defaults[kind])))
    except (KeyError, ValueError):
        configured = defaults.get(kind, max_documents)
    return max(0, min(configured, max(max_documents, configured)))


def select_artifacts_by_priority(artifacts: list[SourceArtifact], max_documents: int) -> list[SourceArtifact]:
    cap = max_source_artifacts(max_documents)
    ranked = sorted(enumerate(artifacts), key=lambda item: (artifact_priority(item[1]), item[0]))
    return [artifact for _, artifact in ranked[:cap]]


def max_source_artifacts(max_documents: int) -> int:
    try:
        configured = int(os.environ.get("OZ_SOURCE_MAX_ARTIFACTS", "2000"))
    except ValueError:
        configured = 2000
    return max(1, configured)


def artifact_priority(artifact: SourceArtifact) -> int:
    if artifact.source_priority >= 0:
        return artifact.source_priority
    path = artifact.path.lower()
    if path.startswith("api-reference/openapi/"):
        return 0
    if path.startswith("api-reference/types/") or path.startswith("api-reference/source/"):
        return 1
    if path.startswith("api-reference/"):
        return 2
    if path.startswith("examples/"):
        return 3
    if path.startswith("guides/"):
        return 4
    return 9


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


def is_llms_full_url(url: str) -> bool:
    return urlparse(url).path.lower().rstrip("/").endswith("/llms-full.txt")


def is_llms_manifest_url(url: str) -> bool:
    return urlparse(url).path.lower().rstrip("/").endswith("/llms.txt")


def llms_manifest_urls(seed_url: str, *, profile: LibraryProfile | None, state: CrawlRunState | None, limit: int) -> list[str]:
    parsed = urlparse(seed_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return []
    base = f"{parsed.scheme}://{parsed.netloc}"
    candidate_urls: list[str] = []
    if is_llms_manifest_url(seed_url):
        candidate_urls.append(seed_url)
    candidate_urls.extend(
        url
        for url in (profile.preferred_urls if profile else [])
        if is_llms_manifest_url(url)
    )
    candidate_urls.extend(base + name for name in ("/llms.txt", "/docs/llms.txt"))
    output: list[str] = []
    seen: set[str] = set()
    for url in unique_urls(candidate_urls):
        if not url_allowed_by_profile(url, profile):
            continue
        text = fetch_text(url, state=state)
        if not text or looks_like_html(text):
            continue
        for linked in extract_llms_manifest_links(text, base_url=url):
            if len(output) >= limit:
                return output
            if linked in seen or not url_allowed_by_profile(linked, profile):
                continue
            seen.add(linked)
            output.append(linked)
    return output


def llms_artifacts(seed_url: str, *, profile: LibraryProfile | None, state: CrawlRunState | None, limit: int) -> list[SourceArtifact]:
    parsed = urlparse(seed_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return []
    base = f"{parsed.scheme}://{parsed.netloc}"
    output: list[SourceArtifact] = []
    candidate_urls = [seed_url] if is_llms_full_url(seed_url) else []
    candidate_urls.extend(
        url
        for url in (profile.preferred_urls if profile else [])
        if is_llms_full_url(url)
    )
    candidate_urls.extend(base + name for name in ("/llms-full.txt", "/docs/llms-full.txt", "/llms.txt", "/docs/llms.txt"))
    for url in unique_urls(candidate_urls):
        if not url_allowed_by_profile(url, profile):
            continue
        text = fetch_text(url, state=state)
        if not text or looks_like_html(text):
            continue
        if "llms-full" not in url.lower():
            continue
        pages = split_llms_full(text, source_url=url)
        for page in pages:
            output.append(
                SourceArtifact(
                    path=document_path(page.source_url, page.title, "guide"),
                    title=page.title,
                    source_url=page.source_url,
                    markdown=artifact_markdown(page.title, page.markdown),
                    source_type="website_url",
                    canonical_url=page.canonical_url or page.source_url,
                    source_priority=source_priority_for(profile, "website_url", 20),
                    discovered_from=url,
                    metadata=source_metadata(
                        profile,
                        "website_url",
                        document_path(page.source_url, page.title, "guide"),
                        page.source_url,
                        extra={
                            **fetch_artifact_metadata(url, state),
                            "expanded_from": "llms_full",
                            "source_manifest_url": url,
                        },
                    ),
                )
            )
            if len(output) >= limit:
                return output
    return output


def markdown_url_artifacts(
    urls: list[str],
    *,
    profile: LibraryProfile | None,
    state: CrawlRunState | None,
    limit: int,
) -> list[SourceArtifact]:
    output: list[SourceArtifact] = []
    for url in urls:
        if not url_allowed_by_profile(url, profile):
            continue
        path = urlparse(url).path.lower()
        if not re.search(r"\.(md|mdx)$", path):
            continue
        text = fetch_text(url, state=state)
        if not text or looks_like_html(text):
            continue
        title = markdown_title(text) or url
        output.append(
            SourceArtifact(
                path=document_path(url, title, "guide"),
                title=title,
                source_url=url,
                markdown=artifact_markdown(title, text),
                source_type="website_url",
                canonical_url=url,
                source_priority=source_priority_for(profile, "website_url", 30),
                metadata=source_metadata(profile, "website_url", document_path(url, title, "guide"), url, extra=fetch_artifact_metadata(url, state)),
            )
        )
        if len(output) >= limit:
            break
    return output


def openapi_artifacts(urls: list[str], *, profile: LibraryProfile | None, state: CrawlRunState | None, limit: int) -> list[SourceArtifact]:
    output: list[SourceArtifact] = []
    for url in urls:
        if not url_allowed_by_profile(url, profile):
            continue
        path = urlparse(url).path.lower()
        if not re.search(r"(openapi|swagger).*\.(json|ya?ml)$", path):
            continue
        text = fetch_text(url, state=state)
        if not text or looks_like_html(text):
            continue
        structured = openapi_chunks(text, url, limit=limit - len(output))
        output.extend(
            SourceArtifact(
                **artifact_payload(item),
                source_type="openapi",
                canonical_url=str(item.get("source_url") or url),
                source_priority=source_priority_for(profile, "openapi", 10),
                discovered_from=url,
                metadata=source_metadata(
                    profile,
                    "openapi",
                    str(item.get("path") or ""),
                    url,
                    extra={**fetch_artifact_metadata(url, state), **(item.get("metadata") if isinstance(item.get("metadata"), dict) else {})},
                ),
            )
            for item in structured
        )
        if not structured:
            output.append(
                SourceArtifact(
                    path=f"api-reference/openapi-{slugify(url)}.md",
                    title="OpenAPI Reference",
                    source_url=url,
                    markdown=render_openapi(text, url),
                    source_type="openapi",
                    canonical_url=url,
                    source_priority=source_priority_for(profile, "openapi", 10),
                    metadata=source_metadata(profile, "openapi", f"api-reference/openapi-{slugify(url)}.md", url, extra=fetch_artifact_metadata(url, state)),
                )
            )
        if len(output) >= limit:
            break
    return output


def source_file_url_artifacts(urls: list[str], *, profile: LibraryProfile | None, state: CrawlRunState | None, limit: int) -> list[SourceArtifact]:
    output: list[SourceArtifact] = []
    for url in urls:
        if not url_allowed_by_profile(url, profile):
            continue
        parsed_path = urlparse(url).path
        lower_path = parsed_path.lower()
        if not direct_source_artifact_allowed(parsed_path, profile):
            continue
        text = fetch_text(url, state=state)
        if not text:
            continue
        artifact = source_file_artifact(
            path=parsed_path.lstrip("/") or lower_path,
            text=text,
            source_url=url,
            profile=profile,
            source_priority=source_priority_for(profile, "github", 12),
            discovered_from=url,
            state=state,
        )
        output.append(artifact)
        if len(output) >= limit:
            break
    return output


def github_docs_artifacts(urls: list[str], *, profile: LibraryProfile | None, state: CrawlRunState | None, limit: int) -> list[SourceArtifact]:
    repos = sorted({repo for url in urls for repo in github_repo(url)})
    output: list[SourceArtifact] = []
    roots = github_source_roots(profile)
    for owner, repo in repos:
        branch = github_default_branch(owner, repo, state=state)
        output.extend(github_root_artifacts(owner, repo, branch, profile=profile, state=state, limit=limit - len(output)))
        for folder in roots:
            remaining = limit - len(output)
            if remaining <= 0:
                return output
            output.extend(github_folder_artifacts(owner, repo, folder, branch=branch, profile=profile, state=state, limit=remaining))
    return output


def github_default_branch(owner: str, repo: str, *, state: CrawlRunState | None) -> str:
    value = fetch_json(f"https://api.github.com/repos/{owner}/{repo}", state=state)
    if isinstance(value, dict) and isinstance(value.get("default_branch"), str) and value["default_branch"].strip():
        return str(value["default_branch"]).strip()
    return "main"


def github_source_roots(profile: LibraryProfile | None) -> list[str]:
    roots = ["docs", "documentation", "examples", "example", "cookbook", "samples", "sample"]
    if profile:
        for root in profile.source_roots:
            normalized = root.strip().strip("/")
            if normalized and normalized not in roots:
                roots.append(normalized)
    return roots


def github_root_artifacts(
    owner: str,
    repo: str,
    branch: str,
    *,
    profile: LibraryProfile | None,
    state: CrawlRunState | None,
    limit: int,
) -> list[SourceArtifact]:
    output: list[SourceArtifact] = []
    for name in ("README.md", "api.md", "helpers.md"):
        if len(output) >= limit:
            break
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{name}"
        if not url_allowed_by_profile(url, profile):
            continue
        output.extend(github_file_artifacts(owner, repo, name, url, profile=profile, state=state, limit=limit - len(output)))
    return output


def github_folder_artifacts(
    owner: str,
    repo: str,
    folder: str,
    *,
    branch: str,
    profile: LibraryProfile | None,
    state: CrawlRunState | None,
    limit: int,
    depth: int = 0,
) -> list[SourceArtifact]:
    if limit <= 0 or depth > 3:
        return []
    listing = fetch_json(f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}?ref={branch}", state=state)
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
                    branch=branch,
                    profile=profile,
                    state=state,
                    limit=limit - len(output),
                    depth=depth + 1,
                )
            )
        else:
            output.extend(
                github_file_artifacts(
                    owner,
                    repo,
                    item_path,
                    item.get("download_url"),
                    profile=profile,
                    state=state,
                    limit=limit - len(output),
                )
            )
        if len(output) >= limit:
            return output
    return output


def github_file_artifacts(
    owner: str,
    repo: str,
    name: str,
    download_url: Any,
    *,
    profile: LibraryProfile | None,
    state: CrawlRunState | None,
    limit: int,
) -> list[SourceArtifact]:
    if not download_url or not github_artifact_path_allowed(name, profile):
        return []
    text = fetch_text(str(download_url), state=state)
    if not text:
        return []
    lower_name = name.lower()
    if re.search(r"(openapi|swagger).*\.(json|ya?ml)$", lower_name):
        structured = openapi_chunks(text, str(download_url), limit=limit)
        if structured:
            return [
                SourceArtifact(
                    **artifact_payload(item),
                    source_type="openapi",
                    canonical_url=str(item.get("source_url") or download_url),
                    source_priority=source_priority_for(profile, "openapi", 10),
                    discovered_from=f"https://github.com/{owner}/{repo}",
                    metadata=source_metadata(
                        profile,
                        "openapi",
                        str(item.get("path") or name),
                        str(download_url),
                        extra={**fetch_artifact_metadata(str(download_url), state), **(item.get("metadata") if isinstance(item.get("metadata"), dict) else {})},
                    ),
                )
                for item in structured
            ]
    if direct_source_artifact_allowed(name, profile):
        return [
            source_file_artifact(
                path=name,
                text=text,
                source_url=str(download_url),
                profile=profile,
                source_priority=source_priority_for(profile, "github", 15),
                discovered_from=f"https://github.com/{owner}/{repo}",
                state=state,
            )
        ][:limit]
    return [SourceArtifact(
        path=f"guides/github-{slugify(owner + '-' + repo + '-' + name)}.md",
        title=f"{owner}/{repo} {name}",
        source_url=str(download_url),
        markdown=markdown_for_github_file(name, text, str(download_url)),
        source_type="github",
        canonical_url=str(download_url),
        source_priority=source_priority_for(profile, "github", 25),
        discovered_from=f"https://github.com/{owner}/{repo}",
        metadata=source_metadata(profile, "github", name, str(download_url), extra=fetch_artifact_metadata(str(download_url), state)),
    )]


def render_openapi(text: str, source_url: str) -> str:
    parsed = parse_openapi(text)
    if not parsed:
        return code_artifact_markdown("OpenAPI Reference", "yaml", text)
    title = nested_string(parsed, ["info", "title"]) or "OpenAPI Reference"
    lines = ["# " + title, ""]
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
    if source_file_document_role(name) in {"sdk_source", "type_definition"}:
        language = source_language_for_path(name)
        return code_artifact_markdown(name, language, text)
    return artifact_markdown(name, text)


def source_file_artifact(
    *,
    path: str,
    text: str,
    source_url: str,
    profile: LibraryProfile | None,
    source_priority: int,
    discovered_from: str | None,
    state: CrawlRunState | None,
) -> SourceArtifact:
    language = source_language_for_path(path)
    role = source_file_document_role(path)
    artifact_path = f"source/{slugify(path)}.md"
    metadata_extra: dict[str, Any] = {
        "language": language,
        "document_role": role,
        "source_file_path": path,
        **fetch_artifact_metadata(source_url, state),
    }
    return SourceArtifact(
        path=artifact_path,
        title=f"Source file: {path}",
        source_url=source_url,
        markdown=code_artifact_markdown(f"Source file: {path}", language, text),
        source_type=origin_source_type(source_url),
        canonical_url=source_url,
        source_priority=source_priority,
        discovered_from=discovered_from,
        metadata=source_metadata(profile, origin_source_type(source_url), path, source_url, extra=metadata_extra),
    )


def direct_source_artifact_allowed(path: str, profile: LibraryProfile | None) -> bool:
    lower = path.lower()
    if lower.endswith((".d.ts", ".pyi")):
        return True
    return source_path_allowed(path, profile.source_file_patterns if profile else [])


def source_file_document_role(path: str) -> str:
    lower = path.lower()
    if lower.endswith((".d.ts", ".pyi")):
        return "type_definition"
    if re.search(r"(^|/)(tests?|specs?)(/|$)|[_-](test|spec)\.", lower):
        return "test"
    if re.search(r"(^|/)(examples?|samples?|cookbook|recipes?)(/|$)", lower):
        return "example"
    if lower.endswith((".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs")):
        return "sdk_source"
    return "unknown"


def source_priority_for(profile: LibraryProfile | None, kind: str, default: int) -> int:
    if profile is None:
        return default
    if kind in profile.source_priorities:
        return profile.source_priorities[kind]
    return default


def artifact_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(item.get("path") or "README.md"),
        "title": str(item.get("title") or item.get("path") or "Documentation"),
        "source_url": str(item.get("source_url") or ""),
        "markdown": str(item.get("markdown") or ""),
    }


def fetch_artifact_metadata(url: str, state: CrawlRunState | None) -> dict[str, Any]:
    if state is None:
        return {}
    meta = state.cache.metadata(url)
    if not meta:
        return {}
    output: dict[str, Any] = {
        "raw_artifact_key": state.cache.artifact_key(url),
        "raw_object_store": meta.get("raw_object_store"),
        "raw_object_sha256": meta.get("raw_object_sha256"),
        "etag": meta.get("etag"),
        "last_modified": meta.get("last_modified"),
        "content_type": meta.get("content_type"),
        "body_sha256": meta.get("body_sha256"),
    }
    return {key: value for key, value in output.items() if value not in ("", None)}


def source_metadata(
    profile: LibraryProfile | None,
    source_type_value: str,
    path: str,
    source_url: str,
    *,
    extra: Any = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if isinstance(extra, dict):
        metadata.update(extra)
    source_type = normalize_source_type(source_type_value, source_url)
    metadata["source_type"] = source_type
    product, confidence, signals = infer_product_with_confidence(profile, path, source_url)
    if product:
        metadata["product"] = product
    metadata["product_confidence"] = confidence
    if signals:
        metadata["product_signals"] = signals
    metadata["document_role"] = infer_document_role(source_type, path, source_url, metadata)
    metadata["deprecated"] = path_matches_any(path, source_url, generic_deprecated_patterns(profile))
    metadata["legacy"] = path_matches_any(path, source_url, generic_legacy_patterns(profile))
    metadata["current"] = not metadata["deprecated"] and not metadata["legacy"]
    if profile and profile.current_patterns:
        metadata["current"] = path_matches_any(path, source_url, profile.current_patterns)
    if "protocol" not in metadata:
        metadata["protocol"] = infer_protocol(source_type, path, source_url)
    return {key: value for key, value in metadata.items() if value not in ("", None, [], {})}


def normalize_source_type(source_type_value: str, source_url: str) -> str:
    raw = str(source_type_value or "").strip().lower().replace("-", "_")
    if raw in {"website_url", "github", "llms_txt", "openapi"}:
        return raw
    return origin_source_type(source_url)


def origin_source_type(source_url: str) -> str:
    parsed = urlparse(source_url)
    lower_url = source_url.lower()
    if lower_url.endswith(("/llms.txt", "/llms-full.txt")):
        return "llms_txt"
    if re.search(r"(openapi|swagger).*\.(json|ya?ml)$", parsed.path.lower()):
        return "openapi"
    if parsed.netloc.lower() in {"github.com", "raw.githubusercontent.com", "api.github.com"}:
        return "github"
    return "website_url"


def infer_product(profile: LibraryProfile | None, path: str, source_url: str) -> str:
    product, _, _ = infer_product_with_confidence(profile, path, source_url)
    return product


def infer_product_with_confidence(profile: LibraryProfile | None, path: str, source_url: str) -> tuple[str, float, list[str]]:
    if profile is None:
        return "", 0.0, []
    product = profile.library
    haystack = f"{path} {source_url}".lower()
    signals: list[str] = []
    confidence = 0.35
    if any(source_url.startswith(url.rstrip("/")) for url in profile.preferred_urls):
        confidence = max(confidence, 0.95)
        signals.append("preferred_url")
    for root in profile.source_roots:
        normalized = root.strip("/").lower()
        if normalized and re.search(rf"(^|/){re.escape(normalized)}(/|$)", haystack):
            confidence = max(confidence, 0.85)
            signals.append(f"source_root:{normalized}")
    for allowed in profile.allowed_paths:
        normalized = allowed.strip("/").lower()
        if normalized and re.search(rf"(^|/){re.escape(normalized)}(/|$)", haystack):
            confidence = max(confidence, 0.75)
            signals.append(f"allowed_path:{normalized}")
    for label in [profile.library, *profile.products, *profile.aliases]:
        normalized = label.strip().lower()
        if normalized and normalized in haystack:
            confidence = max(confidence, 0.9)
            signals.append(f"label:{normalized}")
    if not signals:
        signals.append("library_profile")
    return product, confidence, signals


def infer_document_role(source_type: str, path: str, source_url: str, metadata: dict[str, Any] | None = None) -> str:
    metadata = metadata or {}
    explicit = str(metadata.get("document_role") or "").strip().lower().replace("-", "_")
    if explicit == "cookbook":
        explicit = "example"
    if explicit == "api_spec":
        explicit = "api_reference"
    if explicit in {"readme", "guide", "api_reference", "example", "test", "sdk_source", "type_definition", "changelog", "troubleshooting", "config", "unknown"}:
        return explicit
    haystack = f"{source_type} {path} {source_url}".lower()
    if source_type == "openapi" or "openapi" in haystack or "swagger" in haystack:
        return "api_reference"
    if path.endswith((".d.ts", ".pyi")) or "type_definition" in haystack:
        return "type_definition"
    if re.search(r"(^|/)(src|lib|packages|pkg)(/|$)", haystack) and path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")):
        if re.search(r"(^|/)(test|tests|spec|specs)/|[_-](test|spec)\.", haystack):
            return "test"
        if re.search(r"(^|/)(example|examples|cookbook|samples?)/", haystack):
            return "example"
        return "sdk_source"
    if re.search(r"(^|/)(example|examples|cookbook|recipes?|samples?)/", haystack):
        return "example"
    if re.search(r"(^|/)(test|tests|spec|specs)/", haystack):
        return "test"
    if re.search(r"(^|/)(readme|index)\.(md|mdx|txt)$", haystack):
        return "readme"
    if re.search(r"(^|/)(api-reference|reference|api)(/|$)", haystack):
        return "api_reference"
    if "changelog" in haystack or "release" in haystack:
        return "changelog"
    if any(term in haystack for term in ("troubleshooting", "error", "errors", "exception")):
        return "troubleshooting"
    if any(term in haystack for term in (".env", "config", "configuration", "package.json", "tsconfig", "docker-compose")):
        return "config"
    if re.search(r"(^|/)(docs?|guides?|learn)(/|$)", haystack):
        return "guide"
    return "guide"


def infer_protocol(source_type: str, path: str, source_url: str) -> str:
    haystack = f"{source_type} {path} {source_url}".lower()
    if "websocket" in haystack or "ws/" in haystack:
        return "websocket"
    if "sse" in haystack or "server-sent" in haystack or "event-stream" in haystack:
        return "sse"
    if "openapi" in haystack or "swagger" in haystack:
        return "rest"
    if "cli" in haystack:
        return "cli"
    return ""


def generic_deprecated_patterns(profile: LibraryProfile | None) -> list[str]:
    values = ["deprecated", "deprecation", "obsolete", "sunset", "retired"]
    if profile:
        values.extend(profile.deprecated_patterns)
    return values


def generic_legacy_patterns(profile: LibraryProfile | None) -> list[str]:
    values = ["legacy", "old", "previous", "archive", "archives", "migration", "migrate"]
    if profile:
        values.extend(profile.legacy_patterns)
    return values


def path_matches_any(path: str, source_url: str, patterns: list[str]) -> bool:
    haystack = f"{path} {source_url}".lower()
    for pattern in patterns:
        pattern = str(pattern or "").strip().lower()
        if not pattern:
            continue
        if pattern in haystack:
            return True
    return False


def artifact_markdown(title: str, text: str) -> str:
    cleaned = clean_markdown(text)
    if not cleaned:
        return f"# {title.strip()}\n"
    first_heading = re.match(r"^#\s+", cleaned)
    if first_heading:
        return cleaned
    return f"# {title.strip()}\n\n{cleaned}".strip() + "\n"


def code_artifact_markdown(title: str, language: str, text: str) -> str:
    body = text.strip()
    return f"# {title.strip()}\n\n```{language}\n{body}\n```\n"


def markdown_title(text: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match:
            return match.group(1).strip()
    return ""


def extract_urls(text: str, *, base_url: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>\"]+", text)
    urls.extend(urljoin(base_url, link) for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text))
    cleaned: list[str] = []
    for url in urls:
        candidate = clean_candidate_url(url.split("#", 1)[0])
        if candidate:
            cleaned.append(candidate)
    return cleaned


def extract_llms_manifest_links(text: str, *, base_url: str) -> list[str]:
    links = extract_urls(text, base_url=base_url)
    links.extend(urljoin(base_url, value) for value in re.findall(r"(?m)^\s*[-*]\s+([^\s)]+)\s*$", text))
    output: list[str] = []
    seen: set[str] = set()
    for link in links:
        parsed = urlparse(link)
        if parsed.scheme not in {"http", "https"}:
            continue
        cleaned = clean_candidate_url(link)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        output.append(cleaned)
    return output


def clean_candidate_url(url: str) -> str:
    candidate = str(url or "").strip().strip("<>")
    candidate = candidate.rstrip(".,;")
    return candidate if parse_http_url(candidate) is not None else ""


def unique_urls(urls: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for url in urls:
        cleaned = clean_candidate_url(url)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        output.append(cleaned)
    return output


def dedupe_artifacts(artifacts: list[SourceArtifact]) -> list[SourceArtifact]:
    best_by_source: dict[str, SourceArtifact] = {}
    for artifact in sorted(artifacts, key=lambda item: (artifact_priority(item), item.path)):
        key = canonical_source_key(artifact)
        current = best_by_source.get(key)
        if current is None or artifact_priority(artifact) < artifact_priority(current):
            best_by_source[key] = artifact

    best_by_path: dict[str, SourceArtifact] = {}
    for artifact in sorted(best_by_source.values(), key=lambda item: (artifact_priority(item), item.path)):
        current = best_by_path.get(artifact.path)
        if current is None or artifact_priority(artifact) < artifact_priority(current):
            best_by_path[artifact.path] = artifact
    return list(best_by_path.values())


def canonical_source_key(artifact: SourceArtifact) -> str:
    key = artifact.canonical_url or artifact.source_url or artifact.path
    text = str(key).rstrip("/")
    if preserves_virtual_source_fragment(text, artifact):
        return text
    return text.split("#", 1)[0].rstrip("/")


def preserves_virtual_source_fragment(url: str, artifact: SourceArtifact) -> bool:
    parsed = urlparse(url)
    if not parsed.fragment:
        return False
    source_type = str((artifact.metadata or {}).get("source_type") or artifact.source_type or "").lower()
    if source_type in {"llms_txt", "openapi"}:
        return True
    return bool(re.search(r"(?:^|/)(?:llms|llms-full)\.txt$", parsed.path.lower()))


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug[:100] or "source"


def github_artifact_path_allowed(name: str, profile: LibraryProfile | None) -> bool:
    if re.search(r"\.(md|mdx|d\.ts|pyi)$", name, re.I):
        return True
    if re.search(r"(openapi|swagger).*\.(json|ya?ml)$", name, re.I):
        return True
    return bool(profile and profile.include_source_files and source_path_allowed(name, profile.source_file_patterns))
