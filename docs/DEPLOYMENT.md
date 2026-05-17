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

## Docker Production

```bash
docker compose build
docker compose --profile ops run --rm migrate
docker compose up -d postgres redis minio oz-web oz-api oz-worker oz-scheduler caddy
```

The Docker-first runtime is the primary production shape:

```text
caddy/nginx -> oz-web + oz-api
oz-web      -> user dashboard, admin dashboard, auth pages
oz-api      -> CLI/API endpoints
oz-worker   -> Redis crawl queue + Scrapling + Postgres + S3
oz-scheduler-> freshness policies + Redis crawl queue
```

Use real production values instead of the local compose defaults:

```bash
DATABASE_URL='postgresql://...'
OZ_REDIS_URL='redis://...'
OZ_PACKS_BUCKET='oz-packs-prod'
OZ_CATALOG_BUCKET='oz-packs-prod'
OZ_S3_ENDPOINT_URL='https://s3.amazonaws.com'
AWS_ACCESS_KEY_ID='...'
AWS_SECRET_ACCESS_KEY='...'
OZ_PUBLIC_BASE_URL='https://api.tryoz.dev'
OZ_APP_URL='https://app.tryoz.dev'
OZ_COOKIE_SECURE=1
OZ_COOKIE_DOMAIN='.tryoz.dev'
OZ_JWT_SECRET='use-a-long-random-secret'
OPENAI_API_KEY='...'
```

S3 is used only for immutable packs, catalog JSON, crawl artifacts, and backups.
Postgres is the product database. Redis owns queues, rate limits, short-lived
cache, and job locks. Do not store admin state in S3 JSONL in production.

## Backup And Restore

Production backups are `pg_dump -Fc` files uploaded to S3 and recorded in
Postgres `backup_runs`. Each beta-ready backup must also be restored into a
temporary database and queried before it is marked `verified`.

Run a verified backup from the Docker host:

```bash
OZ_VERIFY_BACKUP_RESTORE=1 bash scripts/backup-postgres-to-s3.sh
```

Install the EC2 systemd timer:

```bash
sudo cp infra/systemd/oz-backup.service /etc/systemd/system/oz-backup.service
sudo cp infra/systemd/oz-backup.timer /etc/systemd/system/oz-backup.timer
sudo cp infra/systemd/oz-enterprise-alerts.* /etc/systemd/system/
sudo cp infra/systemd/oz-slo-report.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now oz-backup.timer
sudo systemctl enable --now oz-enterprise-alerts.timer oz-slo-report.timer
```

## Enterprise Readiness Checks

Run these before inviting a larger beta group:

```bash
python3 scripts/security-smoke.py
python3 scripts/eval-search-quality.py --repo-root . --record-db
python3 scripts/enterprise-checks.py --api-url https://api.tryoz.dev --require-search-quality
python3 scripts/enterprise-alerts.py --api-url https://api.tryoz.dev --require-search-quality
python3 scripts/slo-report.py --window-hours 24
```

The same commands can run inside the production API container with `/app` as
the repo root. Results are recorded in Postgres and visible in the admin panel
under system checks, operations alerts, SLO reports, search quality runs, crawl
logs, quality runs, eval runs, pack builds, and backup runs. See
`docs/ENTERPRISE_READINESS.md` for the full operator checklist.

## Release Evidence

Every public CLI release should include:

- binaries for supported platforms
- `.sha256` checksum files
- `release-manifest.json`
- `sbom.spdx.json`
- GitHub build provenance attestation

Generate and verify release evidence locally:

```bash
python3 scripts/generate-release-manifest.py --dist dist --version 0.1.2
python3 scripts/verify-release-artifacts.py --dist dist
```

## AWS EC2 Production

The current production AWS shape is one Docker host plus S3:

```text
EC2 t4g.medium     oz-docker-prod
Elastic IP         52.73.3.54
S3 bucket          oz-prod-561303652534-us-east-1
Instance services  postgres, redis, oz-web, oz-api, oz-worker, oz-scheduler, caddy
```

The EC2 compose file is:

```bash
infra/docker/docker-compose.aws-ec2.yml
```

It uses host-local Postgres and Redis volumes, AWS S3 for packs/catalog/artifacts,
Caddy for `app.tryoz.dev`, `admin.tryoz.dev`, and `api.tryoz.dev`.

Cloudflare records required:

```text
Type  Name   Value       Proxy
A     @      52.73.3.54  DNS only until Caddy certs issue
A     api    52.73.3.54  DNS only until Caddy certs issue
A     app    52.73.3.54  DNS only until Caddy certs issue
A     admin  52.73.3.54  DNS only until Caddy certs issue
```

## Database Schema

Apply migrations after deployment:

```bash
DATABASE_URL='postgres://...' bash scripts/apply-db-migrations.sh
```

The SQL schema is in `infra/sql`.

Load the generated catalog and chunk index into Postgres after migrations:

```bash
OZ_DATABASE_URL='postgres://...' OPENAI_API_KEY='sk-...' python3 scripts/index-registry-to-db.py
```

The importer writes vendors, libraries, latest refs, and chunk rows. If `_chunks.jsonl` rows contain 1536-dimensional embeddings, they are stored in `pgvector`; if they do not, the importer generates them when `OPENAI_API_KEY` is set. Without embeddings, the same rows remain searchable through Postgres full-text search.

## Auth

Production auth is owned by Oz. There is no Auth0, Cognito, or external OAuth provider in v1.

Web login:

```text
admin creates invite -> user sets password -> /login -> HttpOnly Secure oz_session cookie
```

CLI login:

```bash
oz login --api-url https://api.tryoz.dev
```

The CLI calls `/auth/device`, prints a `/device?code=...` URL, polls `/auth/token`, stores the short-lived access token and rotating refresh token in the OS keychain, and refreshes automatically after 401 responses.

Before beta, seed at least one admin and create a one-time password setup link:

```bash
DATABASE_URL='postgresql://...' \
OZ_JWT_SECRET='...' \
OZ_PUBLIC_BASE_URL='https://api.tryoz.dev' \
OZ_APP_URL='https://app.tryoz.dev' \
python3 scripts/seed-admin-user.py admin@tryoz.dev --invite
```

Users can also create normal accounts at `https://app.tryoz.dev/signup` unless
`OZ_SIGNUP_DISABLED=true` is configured.

## Admin

The deployed admin panel is served by the app/API container at:

```bash
https://admin.tryoz.dev/admin
```

Open the login page in a browser:

```bash
https://app.tryoz.dev/login
```

Log in at `https://app.tryoz.dev/login`, then open `https://admin.tryoz.dev/admin`.
Admin access requires the signed-in user's `role` to be `admin`. Use
`/admin/logout` to clear the browser session.

The admin panel is the only v1 catalog operation surface. It can:

- approve user index requests into crawler jobs
- queue direct crawls and recrawls
- create/update library freshness policies
- create/update production library profiles
- create beta user invites
- create password reset links
- disable or enable users
- show users, usage, auth audit logs, admin action logs, crawler jobs, catalog health, and promotion history
- expose JSON audit views under `/admin/index-requests`, `/admin/crawler-jobs`, `/admin/telemetry`, `/admin/usage`, `/admin/actions`, `/admin/promotions`, and `/admin/freshness`

The worker writes job start/failure/completion state, promotion records,
pack keys, refs, quality reports, and `last_crawled_at` back to Postgres.

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

Publish the generated catalog and packs to the configured S3-compatible packs bucket:

```bash
bash scripts/publish-registry-to-s3.sh s3://<packs-bucket-name>
```

The API/worker containers read:

- `OZ_CATALOG_BUCKET`
- `OZ_CATALOG_KEY`
- `OZ_PACKS_BUCKET`
- `OZ_PACK_PREFIX`
- `DATABASE_URL`
- `OZ_REDIS_URL`
- `OZ_PUBLIC_BASE_URL`
- `OZ_APP_URL`
- `OZ_COOKIE_DOMAIN`
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
bash scripts/release-local.sh 0.1.2
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

Run the production beta smoke from a clean npm install:

```bash
python3 scripts/beta-smoke-prod.py
```
