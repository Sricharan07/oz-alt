# Architecture

## Local Flow

```text
registry/fixtures/<vendor>/<library>/<version>/
    -> oz registry build-packs
registry/packs/<vendor>/<library>/<version>.ozpack
    -> oz pull / oz search auto-pull
    -> ~/.codo/objects/blobs/<prefix>/<sha256>
    -> .codo/vendors/<vendor>/<library>@<version>/
    -> agent Read/Grep/Glob
```

`oz pull` verifies pack blob SHA-256 values and the tree manifest SHA before ingesting into the global object store. Materialization uses hardlinks and falls back to copies.

## Cloud Flow

```text
SQS / scheduled recrawl
    -> crawler Lambda
    -> registry fixtures/chunks/symbols in /tmp
    -> raw JSON .ozpack in S3
    -> catalog in S3 + metadata/chunks in Aurora
    -> API Gateway + Lambda
    -> oz CLI
```

The API uses the same handlers locally and in Lambda. `RegistryStorage` reads catalog, packs, and admin streams from local files or S3 depending on environment. Retrieval uses Aurora/Postgres Data API or `OZ_DATABASE_URL` when configured, then falls back to catalog/chunk files for local development.

## Storage

- Local CAS: `~/.codo/objects/blobs/<prefix>/<sha256>`.
- Pack transport: zstd-compressed JSON bundle with manifest and base64 blobs. Lambda-generated packs use the same JSON shape without zstd so the crawler can publish packs without native dependencies.
- Cloud objects: S3 objects bucket with Intelligent-Tiering.
- Cloud packs/catalog/admin streams: S3 packs bucket.
- Metadata/search: Aurora Serverless v2 Postgres with pgvector and Postgres FTS.
- Rerank cache: DynamoDB with 7-day TTL.

## Auth

`oz login` uses the device-flow-shaped `/auth/device` and `/auth/token` endpoints. Tokens are HMAC JWTs issued by the API. The CLI stores tokens in the OS keychain when available and falls back to `~/.codo/config.json` only when keychain access is unavailable or disabled for tests.

## Crawler

The crawler fetches docs with Scrapling when installed and uses a stdlib fetch/normalize fallback in Lambda. It discovers `/llms-full.txt`, `/llms.txt`, `/sitemap.xml`, and same-site links, then writes:

- `README.md`
- `INDEX.md`
- `guides/*.md`
- `api-reference/`
- `examples/`
- `_symbols/*.md`
- `_chunks.jsonl` with `chunk_sha` and optional embeddings
- `_meta.json`

Embeddings are SHA-cached and generated only when `OPENAI_API_KEY` is present.

In Lambda, each successful crawl is packed, uploaded to S3, upserted into `catalog.json`, and indexed into Aurora through the Data API. For local seed rebuilds, `scripts/index-registry-to-db.py` performs the same catalog/chunk import against either `OZ_DATABASE_URL` or the Aurora Data API env vars.

## Agent Contract

`oz install` writes the locked Oz skill into Codex, Claude Code, Cursor, Cline, and Continue project config files. On normal CLI commands, existing installed skill blocks are silently refreshed unless `auto_update_skill` is disabled.
