# Deployment

## Verify Locally

```bash
bash scripts/e2e-local.sh
```

This verifies the local and API-backed flows, including login, suggest, search, auto-pull, pack download, materialization, admin routes, and JSON output.

## Build Seed Registry

```bash
OZ_SEED_MAX_PAGES=24 bash scripts/build-seed-registry.sh
```

The generated registry must contain at least 15 packs:

```bash
find registry/packs -name '*.ozpack' | wc -l
```

The crawler uses the vendored D4Vinci/Scrapling source under `third_party/Scrapling`. Install the crawler package dependencies before crawling:

```bash
pip install -e packages/oz-crawler
```

For browser-backed Scrapling modes, run Scrapling's browser install step in the runtime image before using `--fetcher dynamic` or `--fetcher stealth`.

## Deploy AWS Stack

```bash
cd infra/cdk
npm install
npm run build
npm run synth
npm run deploy -- --parameters BudgetAlertEmail=ops@example.com
```

The stack creates:

- API Gateway HTTP API
- API Lambda
- crawler Lambda
- S3 objects bucket with Intelligent-Tiering
- S3 packs/catalog bucket
- Aurora Serverless v2 Postgres with Data API enabled
- DynamoDB rerank cache table
- SQS crawler queue and DLQ
- EventBridge daily recrawl schedule
- Secrets Manager JWT secret
- AWS Budgets monthly $200 cost guardrail

## Database Schema

Apply migrations after deployment:

```bash
DATABASE_URL='postgres://...' bash scripts/apply-db-migrations.sh
```

The SQL schema is in `infra/sql`.

Load the generated catalog and chunk index into Postgres/Aurora after migrations:

```bash
OZ_DATABASE_URL='postgres://...' OPENAI_API_KEY='sk-...' python3 scripts/index-registry-to-db.py
```

For the deployed Aurora Data API path, use the stack outputs instead of `OZ_DATABASE_URL`:

```bash
OZ_DB_RESOURCE_ARN='arn:aws:rds:...' \
OZ_DB_SECRET_ARN='arn:aws:secretsmanager:...' \
OZ_DB_NAME='oz' \
OPENAI_API_KEY='sk-...' \
python3 scripts/index-registry-to-db.py
```

The importer writes vendors, libraries, latest refs, and chunk rows. If `_chunks.jsonl` rows contain 1536-dimensional embeddings, they are stored in `pgvector`; if they do not, the importer generates them when `OPENAI_API_KEY` is set. Without embeddings, the same rows remain searchable through Postgres full-text search.

## Publish Registry Packs

After CDK deploy, publish the generated catalog and packs to the packs bucket output:

```bash
bash scripts/publish-registry-to-s3.sh s3://<packs-bucket-name>
```

The API Lambda reads:

- `OZ_CATALOG_BUCKET`
- `OZ_CATALOG_KEY`
- `OZ_PACKS_BUCKET`
- `OZ_PACK_PREFIX`
- `OZ_DB_RESOURCE_ARN`
- `OZ_DB_SECRET_ARN`
- `OZ_RERANK_TABLE`

## Local API

```bash
PYTHONPATH=packages/oz-api/src python3 -m oz_api.server --repo-root . --host 127.0.0.1 --port 8765 --require-auth
```

```bash
oz login --api-url http://127.0.0.1:8765
oz suggest "JWT authentication in Next.js middleware"
oz search "middleware jwt cookies" vercel/next.js
```

## Release

```bash
bash scripts/release-local.sh 0.1.0
```

This creates a release tarball, SHA256 file, and Homebrew formula for the current platform. The npm wrapper lives under `packages/oz-npm`.

## Launch Eval

Run the 10-task representative agent loop before promoting a release:

```bash
bash scripts/eval-agent-tasks.sh
```
