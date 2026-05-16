# Oz

Oz is a local-first documentation registry for coding agents. This repo now contains a runnable local version of the PRD flow:

1. Initialize a project with `oz init`.
2. Build immutable local registry packs with `oz registry build-packs`.
3. Suggest an indexed library with `oz suggest`.
4. Pull a versioned docs tree with `oz pull`, or let `oz search` auto-pull it.
5. Let agents read files under `.codo/vendors/...` with their normal file tools.

The AWS deployment, device OAuth, hosted S3 packs, OpenAI reranking, and production telemetry storage are still implementation targets. The product loop itself is runnable locally.

## Repository Layout

- `crates/oz-cli` - Rust CLI binary.
- `crates/oz-objects` - content-addressed local object store and tree materialization.
- `packages/oz-crawler` - Python Scrapling crawler that writes Oz fixture trees.
- `packages/oz-api` - local HTTP API exposing PRD-shaped endpoints.
- `packages/oz-admin` - static admin entry point.
- `registry/fixtures` - local development registry used by `oz pull`.
- `registry/packs` - local `.ozpack` bundles generated from fixtures.
- `registry/catalog.json` - machine-readable registry catalog.
- `infra/cdk` - AWS CDK deployment stack.
- `PRD.md` - product requirements.

## Try The Local Loop

```bash
cargo run -p oz -- registry build-packs
cargo run -p oz -- init
cargo run -p oz -- suggest "JWT authentication in Next.js middleware"
cargo run -p oz -- search "middleware jwt cookies" vercel/next.js
cargo run -p oz -- status
```

`oz search` auto-pulls indexed docs when needed. The pulled docs materialize under `.codo/vendors/vercel/next.js@15/`.

Run the full local smoke test:

```bash
bash scripts/e2e-local.sh
```

Deployment instructions are in `docs/DEPLOYMENT.md`.

## Local API

```bash
PYTHONPATH=packages/oz-api/src python3 -m oz_api.server --repo-root . --host 127.0.0.1 --port 8765
```

Point the CLI at the API and use the remote pack/search path:

```bash
target/debug/oz login --api-url http://127.0.0.1:8765
target/debug/oz suggest "JWT authentication in Next.js middleware"
target/debug/oz search "middleware jwt cookies" vercel/next.js
```

Useful endpoints:

- `GET /health`
- `POST /auth/device`
- `POST /auth/token`
- `POST /suggest`
- `POST /search`
- `GET /refs/<vendor>/<library>`
- `GET /pack/<vendor>/<library>/<version>`
- `POST /index-request`
- `POST /telemetry`
- `GET /admin/index-requests`
- `GET /admin/telemetry`

## Crawler

The crawler uses Scrapling from `https://github.com/D4Vinci/Scrapling.git` and emits registry fixtures:

```bash
python -m pip install -e packages/oz-crawler
oz-crawl crawl https://nextjs.org/docs --vendor vercel --library next.js --version 15
```

The crawler writes Oz-compatible fixture trees with `README.md`, `INDEX.md`, `guides/`, `_symbols/`, and `_meta.json`. Deep sitemap traversal, embedding, and hosted pack upload come next.
