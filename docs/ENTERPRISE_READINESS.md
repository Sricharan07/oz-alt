# Oz Enterprise Readiness

Oz remains a CLI + local `.codo` documentation system. Enterprise readiness means
the hosted platform is controlled, observable, recoverable, and auditable.

## Required Production Gates

- Every library has a production `library_profile`.
- Every latest library crawl is `completed`.
- Every promoted crawl has passing `quality_runs` and `eval_runs`.
- Every promoted pack has a signing key id.
- Every crawler job writes `crawl_job_logs`.
- At least one restore-verified backup exists inside the configured RPO window.
- Recent semantic search evals pass and are recorded in `search_quality_runs`.
- Admin/user/auth mutations write audit rows.
- Temporary smoke-test users are disabled after verification.

## Operator Commands

Run migrations:

```bash
docker compose -f infra/docker/docker-compose.aws-ec2.yml --profile ops run --rm migrate
```

Run system checks from the production API container:

```bash
docker exec docker-oz-api-1 python scripts/enterprise-checks.py \
  --api-url https://api.tryoz.dev \
  --require-search-quality
```

Run search-quality evals and record them:

```bash
docker exec docker-oz-api-1 python scripts/eval-search-quality.py \
  --repo-root /app \
  --record-db
```

Run crawler SSRF/security smoke locally before deploy:

```bash
python3 scripts/security-smoke.py
```

Run published-package production smoke:

```bash
python3 scripts/beta-smoke-prod.py \
  --library facebook/react \
  --query 'useEffect cleanup dependency array' \
  --grep 'useEffect|cleanup|dependency array'
```

## Dashboard Evidence

The admin dashboard must show:

- `System Checks`
- `Library Profiles`
- `Crawler Jobs`
- `Crawl Logs`
- `Quality Runs`
- `Eval Runs`
- `Search Quality Runs`
- `Pack Builds`
- `Promotion History`
- `Backup Runs`
- `Auth Audit Logs`
- `Admin Actions`

## Acceptance Targets

```txt
expected-path recall@5 >= 85%
semantic precision@5 >= 75%
materialization = 100%
junk top5 rate = 0%
duplicate top5 rate = 0%
latest completed crawls = catalog libraries
verified backup age <= 30h
pack signature coverage = 100%
```

## Non-Goals For V1

- MCP
- private user indexing
- user-submitted private repositories
- library owner claiming
- chat assistant
- API keys

