# Oz

Oz is a versioned documentation registry for coding agents. The CLI pulls library docs into `.codo/vendors/...` so agents can use normal file tools instead of guessing external APIs from memory.

This repository contains the end-to-end beta product:

1. 15 launch libraries crawled into `registry/fixtures`.
2. Immutable `.ozpack` bundles in `registry/packs`.
3. A Rust CLI with `setup`, `login`, `install`, `init`, `suggest`, `search`, `context`, `pull`, `update`, `prune`, `mcp`, `doctor`, and `config`.
4. A Docker-first Python API that serves semantic `/suggest`, `/search`, `/refs`, `/pack`, auth, telemetry, user dashboard, and admin routes.
5. A crawler wired to D4Vinci/Scrapling's Spider/session APIs, with chunking, symbol extraction, and durable Postgres-backed indexing jobs.
6. Docker Compose production services for Postgres/pgvector, Redis, S3-compatible pack storage, API, worker, scheduler, and Caddy.

## Repository Layout

- `crates/oz-cli` - Rust CLI binary.
- `crates/oz-objects` - content-addressed local object store and pack verification.
- `packages/oz-crawler` - documentation crawler.
- `packages/oz-api` - Docker/Postgres/Redis registry API, worker, and scheduler control plane.
- `packages/oz-npm` - npm global wrapper package.
- `registry/fixtures` - 15 seeded documentation trees.
- `registry/packs` - generated `.ozpack` bundles.
- `infra/docker` - Caddy routing for the Docker runtime.
- `infra/sql` - Postgres/pgvector schema and indexes.
- `scripts` - e2e, seed build, S3 publish, migrations, install, release.

## Local Verification

```bash
bash scripts/e2e-local.sh
```

This runs Rust tests, Python compile checks, CLI local mode, local API mode, login, suggest, search auto-pull, pack download, status, doctor, admin, and JSON output.

Run the representative agent task eval:

```bash
bash scripts/eval-agent-tasks.sh
```

## Use The CLI Locally

```bash
cargo run -p oz -- dev registry build-packs
cargo run -p oz -- setup --skip-login
cargo run -p oz -- suggest "JWT authentication in Next.js middleware"
cargo run -p oz -- search "middleware jwt cookies" vercel/next.js
cargo run -p oz -- prune --stale
cargo run -p oz -- status
```

Pulled docs materialize under `.codo/vendors/<vendor>/<library>@<version>/`.
`oz install --codex` writes both project `AGENTS.md` instructions and a real Codex skill at
`$CODEX_HOME/skills/oz/SKILL.md` (default: `~/.codex/skills/oz/SKILL.md`).

## Local API

```bash
PYTHONPATH=packages/oz-api/src python3 -m oz_api.server --repo-root . --host 127.0.0.1 --port 8765 --require-auth
```

```bash
target/debug/oz login --api-url http://127.0.0.1:8765
target/debug/oz suggest "JWT authentication in Next.js middleware"
target/debug/oz search "middleware jwt cookies" vercel/next.js
target/debug/oz context "middleware jwt cookies" vercel/next.js --max-tokens 1200
```

Run the path-first MCP server for clients that support MCP:

```bash
target/debug/oz mcp
```

Browse indexed libraries and pack metadata at `/libraries` when the API is running.

## Seed Registry

```bash
OZ_SEED_MAX_PAGES=24 bash scripts/build-seed-registry.sh
```

This crawls the 15 launch libraries from `registry/seed_libraries.json`, writes fixture trees, rebuilds `.ozpack` bundles, and refreshes `registry/catalog.json`.

Scrapling is vendored under `third_party/Scrapling` with Git metadata removed, and the crawler imports that local source before looking at site packages. Use `--fetcher auto`, `--fetcher http`, `--fetcher dynamic`, or `--fetcher stealth` to select the Scrapling session path. Browser-backed modes require Scrapling's browser setup in the runtime image.

Index the generated chunks into Postgres for semantic API retrieval:

```bash
VOYAGE_API_KEY='...' OZ_DATABASE_URL='postgres://...' python3 scripts/index-registry-to-db.py
```

## Deployment

See `docs/DEPLOYMENT.md`.
