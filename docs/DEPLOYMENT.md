# Deployment

## Local Production Parity

```bash
bash scripts/e2e-local.sh
```

This verifies local and API-backed flows, including login, suggest, search, pack download, materialization, admin, and JSON output.

## API

Run locally:

```bash
PYTHONPATH=packages/oz-api/src python3 -m oz_api.server --repo-root . --host 127.0.0.1 --port 8765 --require-auth
```

Login and use remote mode:

```bash
oz login --api-url http://127.0.0.1:8765
oz suggest "JWT authentication in Next.js middleware"
oz search "middleware jwt cookies" vercel/next.js
```

## AWS CDK

```bash
cd infra/cdk
npm install
npm run build
npm run synth
npm run deploy
```

The stack creates:

- API Gateway HTTP API
- Lambda API function
- S3 objects bucket
- S3 packs bucket
- DynamoDB rerank cache table
- SQS crawler queue

## Registry Operations

Build packs:

```bash
oz registry build-packs
```

Queue seed crawls:

```bash
python3 scripts/enqueue-seed-crawls.py
PYTHONPATH=packages/oz-crawler/src python3 -m oz_crawler.cli worker --max-pages 8
oz registry build-packs
```

## Release

```bash
bash scripts/release-local.sh 0.1.0
```

