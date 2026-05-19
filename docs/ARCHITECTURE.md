# Architecture

## Local Flow

```text
registry/fixtures/<vendor>/<library>/<version>/
    -> oz dev registry build-packs
registry/packs/<vendor>/<library>/<version>.ozpack
    -> oz pull / oz search auto-pull
    -> ~/.codo/objects/blobs/<prefix>/<sha256>
    -> .codo/vendors/<vendor>/<library>@<version>/
    -> agent Read/Grep/Glob
```

`oz pull` verifies the pack manifest signature when verification is configured, then verifies pack blob SHA-256 values and the tree manifest SHA before ingesting into the global object store. Materialization uses hardlinks and falls back to copies.

## Production Flow

```text
admin action / scheduler
    -> Redis crawler queue
    -> oz-worker
    -> registry fixtures/chunks/symbols in /tmp
    -> signed .ozpack in S3-compatible object storage
    -> catalog in S3 + metadata/chunks/promotions in Postgres
    -> oz-api behind caddy/nginx
    -> oz CLI
```

The primary runtime is Docker-first: `oz-web`, `oz-api`, `oz-worker`,
`oz-scheduler`, Postgres/pgvector, Redis, S3-compatible object storage, and
caddy/nginx. `RegistryStorage` reads packs/catalog from local files or S3
depending on environment. Product state, admin state, auth, usage, crawl jobs,
profiles, quality runs, and promotions live in Postgres. Retrieval uses direct
Postgres/pgvector when `DATABASE_URL` or `OZ_DATABASE_URL` is configured, then
falls back to local catalog/chunk files for development.

## Storage

- Local CAS: `~/.codo/objects/blobs/<prefix>/<sha256>`.
- Pack transport: zstd-compressed JSON bundle with Ed25519-signed manifest and base64 blobs. Worker-generated packs use the same JSON shape without zstd so the crawler can publish packs without native dependencies.
- Cloud packs/catalog/artifacts: S3-compatible object storage.
- Product state/search: Postgres with pgvector and Postgres FTS.
- Queue/rate limits/cache: Redis.

## Auth

Oz v1 owns authentication. Web users create an account or accept an admin invite, then sign in through `/login` with email and password. Passwords are hashed with Argon2 and web sessions use an HttpOnly Secure `oz_session` cookie. CLI users run `oz login`, which calls `/auth/device`, opens `/device?code=...` in the same account session, then polls `/auth/token` for a short-lived access JWT and a rotating opaque refresh token. The CLI stores both tokens in the OS keychain when available and falls back to `~/.codo/config.json` only when keychain access is unavailable or disabled for tests.

Admin privileges are a `users.role = 'admin'` database flag seeded by an operator script; users cannot self-promote. Production disables local auth fallbacks by setting `OZ_ENV=production`.

## Dashboard And Admin

The user console is the React app in `frontend-main`. It shows CLI setup,
library catalog browsing, pack metadata, status, account entry points, and
device approval links. It does not expose private indexing, team spaces, API
keys, or chat. The console talks to backend JSON endpoints through same-origin
nginx proxying in production, so cookies and auth redirects stay on the Oz
domain.

The admin panel is the catalog control plane. Admins create library profiles,
approve index requests, queue crawls/recrawls, maintain freshness policies, and
inspect users, usage, telemetry, auth audit logs, admin action logs, crawler
jobs, crawl step logs, catalog health, search quality runs, quality runs,
system checks, backup runs, and promotion history. Admin mutations use the same
first-party session and CSRF checks as the dashboard. Crawler jobs write
start/completion/failure state and step logs back to Postgres, and successful
jobs create catalog promotion, quality, eval, and pack build records.

## Crawler

The crawler uses a vendored copy of D4Vinci/Scrapling under `third_party/Scrapling` as the primary crawler engine. Local and production jobs run through Scrapling's `Spider`, `FetcherSession`, `AsyncDynamicSession`, `AsyncStealthySession`, `response.follow()`, concurrency controls, optional robots.txt compliance, and optional checkpoint directories. A stdlib fetch fallback remains for runtimes that do not include browser dependencies.

It discovers `/llms-full.txt`, `/llms.txt`, `/sitemap.xml`, and same-site links, then writes:

- `README.md`
- `INDEX.md`
- `guides/*.md`
- `api-reference/`
- `examples/`
- `_symbols/*.md`
- `_chunks.jsonl` with `chunk_sha`, content type, token count, parent chunk key, and source anchor
- `_meta.json`

Embeddings are applied after chunks are durable in Postgres. The indexing job layer first checks a schema-versioned cache keyed by provider, model, dimensions, input type, and `chunk_sha`, then sends large uncached Voyage jobs through the Batch API and small changes through the synchronous embeddings API. Production defaults to `voyage-code-3` at 1024 dimensions. Jina or OpenAI can be selected explicitly through `OZ_EMBEDDING_PROVIDER`.

Each chunk has a deterministic `chunk_sha` derived from vendor, library, version, path, ordinal, and text. The indexer also computes the same value for older chunk files that do not contain it, resolves parent-child chunks, computes trust scores, and marks duplicate chunks so retrieval serves canonical paths.

In the worker, each successful crawl is packed, uploaded to S3-compatible object storage, indexed into Postgres, embedded, deduped, and then promoted into `catalog.json`. Large embedding jobs can pause promotion while the Voyage Batch API runs; the worker polls those jobs, retries partial or timed-out batches through the sync path, and only promotes after embeddings are applied. Scheduled recrawls use freshness policies first and fall back to seed libraries only when explicitly enabled. Production crawls require a library profile and fail before promotion when quality gates fail. Crawler fetches pass a network safety gate before any HTTP request; unless `OZ_CRAWLER_ALLOW_PRIVATE_NETWORKS=1` is set for a local test, URLs resolving to loopback, private, link-local, multicast, reserved, or unspecified addresses are rejected to prevent SSRF against instance metadata or internal services. For local seed rebuilds, `scripts/index-registry-to-db.py` performs the same catalog/chunk import against `OZ_DATABASE_URL` or `DATABASE_URL`.

## Agent Contract

`oz setup` is the low-friction onboarding path. It writes the API URL to
`~/.codo/config.json`, initializes `.codo`, installs the locked Oz skill into
Codex, Claude Code, Cursor, Cline, and Continue project config files, and adds
MCP configuration for clients with known project/global MCP config locations.
Today that means:

- `.mcp.json` for project-scoped MCP clients such as Claude Code.
- `.cursor/mcp.json` for Cursor.
- `.continue/mcpServers/oz.json` for Continue.
- Existing Cline MCP settings files when Cline is present.
- `$CODEX_HOME/config.toml` or `~/.codex/config.toml` for Codex.

On normal CLI commands, existing installed skill blocks and Oz MCP entries are
silently refreshed unless `auto_update_skill` is disabled.
