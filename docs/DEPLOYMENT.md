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

The crawler package requires Python 3.11 or newer. The vendored Scrapling source is imported from `third_party/Scrapling` before site packages so the crawler does not silently drift to another Scrapling release.

For browser-backed Scrapling modes, run Scrapling's browser install step in the runtime image before using `--fetcher dynamic` or `--fetcher stealth`.

## Deploy AWS Stack

```bash
cd infra/cdk
npm install
npm run build
npm run synth
npm run deploy -- \
  --parameters BudgetAlertEmail=ops@example.com \
  --parameters RequireOAuth=true \
  --parameters OAuthDeviceAuthUrl=https://idp.example.com/oauth/device/code \
  --parameters OAuthTokenUrl=https://idp.example.com/oauth/token \
  --parameters OAuthClientId=oz-cli \
  --parameters PackSigningKey=<ed25519-signing-seed> \
  --parameters PackVerifyKey=<ed25519-public-key>
```

To deploy Oz behind your own API hostname, set these before `npm run synth` or
`npm run deploy`:

```bash
export OZ_CUSTOM_DOMAIN_NAME=api.yourdomain.com
export OZ_CUSTOM_DOMAIN_CERT_ARN=arn:aws:acm:us-east-1:123456789012:certificate/...
```

When that is set, the stack creates an API Gateway custom domain and outputs:

- `ApiUrl` for the URL the CLI should use
- `CloudflareCnameTarget` for the Cloudflare DNS record value
- `CloudflareHostedZoneId` for the API Gateway regional hosted zone ID

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

## Auth

Local development uses the built-in device-code fallback. Production should require a real OAuth device provider:

```bash
OZ_REQUIRE_OAUTH=1
OZ_OAUTH_DEVICE_AUTH_URL='https://idp.example.com/oauth/device/code'
OZ_OAUTH_TOKEN_URL='https://idp.example.com/oauth/token'
OZ_OAUTH_CLIENT_ID='oz-cli'
OZ_OAUTH_SCOPE='openid profile email'
```

`/auth/device` proxies the provider's device authorization response. `/auth/token` exchanges the device code with the provider and issues the Oz JWT used by the CLI.

## Pack Signing

Set the Ed25519 signing seed wherever packs are built:

```bash
OZ_PACK_SIGNING_KEY='<32-byte Ed25519 signing seed as hex/base64url/base64>'
OZ_PACK_SIGNING_KEY_ID='prod-2026-05'
```

Set the Ed25519 public verification key for any production client or API process that ingests packs:

```bash
OZ_PACK_VERIFY_KEY='<32-byte Ed25519 public key as hex/base64url/base64>'
OZ_PACK_REQUIRE_SIGNATURE=1
```

Unsigned local packs still work unless verification is configured or signatures are required.

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
- `OZ_OAUTH_DEVICE_AUTH_URL`
- `OZ_OAUTH_TOKEN_URL`
- `OZ_OAUTH_CLIENT_ID`
- `OZ_PACK_SIGNING_KEY`
- `OZ_PACK_SIGNING_KEY_ID`
- `OZ_PACK_VERIFY_KEY`

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

The source repository can remain private. Public installers and GitHub release
assets are published to `Sricharan07/oz`, which contains only a minimal README,
the curl installer, and release artifacts.

Sync the public installer repo first:

```bash
bash scripts/sync-public-release-repo.sh
```

```bash
bash scripts/release-local.sh 0.1.0
```

This creates a raw binary asset, SHA256 files, a release tarball, and a Homebrew formula for the current platform. The npm wrapper downloads the raw binary asset for the user's platform.

Tagged releases are built by `.github/workflows/release.yml` and publish Linux, macOS, and Windows assets to the public release repo. Add a `PUBLIC_RELEASE_TOKEN` GitHub Actions secret with write access to `Sricharan07/oz`; the default private-repo `GITHUB_TOKEN` cannot publish to a different repo.

The npm package name is `@hiringbae/oz` and keeps the executable command as `oz`.

The curl installer uses those release assets:

```bash
curl -fsSL https://raw.githubusercontent.com/Sricharan07/oz/main/scripts/install-release.sh | sh
```

## Launch Eval

Run the 10-task representative agent loop before promoting a release:

```bash
bash scripts/eval-agent-tasks.sh
```
