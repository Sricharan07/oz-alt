# Oz

Oz is a versioned documentation registry for coding agents. The CLI pulls library docs into `.codo/vendors/...` so agents can use normal file tools instead of guessing external APIs from memory.

This repository contains the end-to-end beta product:

1. 15 launch libraries crawled into `registry/fixtures`.
2. Immutable `.ozpack` bundles in `registry/packs`.
3. A Rust CLI with `login`, `install`, `init`, `suggest`, `search`, `pull`, `update`, `gc`, `doctor`, and `config`.
4. A Python API that runs locally or in Lambda and serves semantic `/suggest`, `/search`, `/refs`, `/pack`, auth, telemetry, and admin routes.
5. A Scrapling-first crawler with stdlib fallback, chunking, symbol extraction, and optional OpenAI embedding generation.
6. CDK infrastructure for S3, Aurora Serverless v2/Postgres Data API, pgvector/FTS indexing, DynamoDB rerank cache, SQS crawler queue/DLQ, scheduled recrawls, API Gateway, Lambda, and budget guardrail.

## Repository Layout

- `crates/oz-cli` - Rust CLI binary.
- `crates/oz-objects` - content-addressed local object store and pack verification.
- `packages/oz-crawler` - documentation crawler and local worker.
- `packages/oz-api` - local/Lambda registry API.
- `packages/oz-admin` - static admin entry point.
- `packages/oz-npm` - npm global wrapper package.
- `registry/fixtures` - 15 seeded documentation trees.
- `registry/packs` - generated `.ozpack` bundles.
- `infra/cdk` - AWS deployment stack.
- `infra/sql` - Aurora/Postgres schema and indexes.
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
cargo run -p oz -- registry build-packs
cargo run -p oz -- init
cargo run -p oz -- install --codex
cargo run -p oz -- suggest "JWT authentication in Next.js middleware"
cargo run -p oz -- search "middleware jwt cookies" vercel/next.js
cargo run -p oz -- status
```

Pulled docs materialize under `.codo/vendors/<vendor>/<library>@<version>/`.

## Local API

```bash
PYTHONPATH=packages/oz-api/src python3 -m oz_api.server --repo-root . --host 127.0.0.1 --port 8765 --require-auth
```

```bash
target/debug/oz login --api-url http://127.0.0.1:8765
target/debug/oz suggest "JWT authentication in Next.js middleware"
target/debug/oz search "middleware jwt cookies" vercel/next.js
```

## Seed Registry

```bash
OZ_SEED_MAX_PAGES=24 bash scripts/build-seed-registry.sh
```

This crawls the 15 launch libraries from `registry/seed_libraries.json`, writes fixture trees, rebuilds `.ozpack` bundles, and refreshes `registry/catalog.json`.

Index the generated chunks into Postgres/Aurora for semantic API retrieval:

```bash
OPENAI_API_KEY='sk-...' OZ_DATABASE_URL='postgres://...' python3 scripts/index-registry-to-db.py
```

## Deployment

See `docs/DEPLOYMENT.md`.
