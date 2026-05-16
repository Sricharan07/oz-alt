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
