# Architecture

## Local Development Flow

```text
registry/fixtures/<vendor>/<library>/<version>/
    -> oz registry build-packs
registry/packs/<vendor>/<library>/<version>.ozpack
    -> oz pull / oz search auto-pull
    -> ~/.codo/objects/blobs/<prefix>/<sha256>
    -> .codo/vendors/<vendor>/<library>@<version>/
    -> agent Read/Grep/Glob
```

`oz pull` prefers local `.ozpack` files, verifies their tree and blob SHA-256 values, ingests blobs into the global object store, and then materializes the requested library into the project with hardlinks. If hardlinks are unavailable, it copies the object bytes.

## Object Store

The object store is content-addressed by SHA-256. `.ozpack` files are zstd-compressed JSON bundles containing a manifest and base64-encoded blobs. This is optimized for local development clarity; production can replace the transport format without changing the CLI materialization model.

## Crawler

`packages/oz-crawler` fetches pages with Scrapling, removes common non-content elements, converts the main document body to Markdown, extracts simple symbols from code fences, and writes an Oz-compatible fixture directory.

The crawler does not yet perform robust sitemap traversal or language-aware AST symbol extraction. Keep that work isolated behind fixture generation so the CLI remains independent from crawling complexity.

## Local API

`packages/oz-api` exposes a local HTTP registry:

- `POST /auth/device` and `POST /auth/token` provide a local device-flow-compatible login shim.
- `POST /suggest` ranks libraries from `registry/catalog.json`.
- `POST /search` returns local `.codo/vendors/...` coordinates.
- `GET /refs/<vendor>/<library>` returns the newest local catalog ref.
- `GET /pack/<vendor>/<library>/<version>` serves the immutable pack file.
- `POST /index-request` and `POST /telemetry` append JSONL events under `registry/admin/`.

When `oz config set api_url <url>` or `oz login --api-url <url>` is set, the CLI uses this API for suggest/search/pull. Without `api_url`, it uses local registry fixtures and packs directly.
