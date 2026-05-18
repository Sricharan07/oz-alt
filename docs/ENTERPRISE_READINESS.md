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
- Enterprise alert checks run on a timer and write `ops_alerts`.
- SLO reports run on a timer and write `slo_reports`.
- Release builds produce checksums, a release manifest, an SPDX SBOM, and GitHub provenance attestation.
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

Run checks and open/resolve ops alerts:

```bash
docker exec docker-oz-api-1 python scripts/enterprise-alerts.py \
  --api-url https://api.tryoz.dev \
  --require-search-quality
```

Run and record an SLO report:

```bash
docker exec docker-oz-api-1 python scripts/slo-report.py --window-hours 24
```

Read protected Prometheus-style metrics:

```bash
curl -H "Authorization: Bearer $OZ_METRICS_TOKEN" https://api.tryoz.dev/metrics
```

Read customer-visible status JSON:

```bash
curl https://api.tryoz.dev/status.json
```

Enable production JSON logs and request sampling:

```bash
OZ_LOG_FORMAT=json
OZ_TRACE_SAMPLE_RATE=0.01
```

Load-test deployed retrieval before broad beta:

```bash
python3 scripts/load-test-retrieval.py \
  --url https://api.tryoz.dev/search \
  --library vercel/next.js \
  --query 'middleware cookies authentication' \
  --requests 100 \
  --concurrency 10
```

Install operational timers on the Docker host:

```bash
sudo cp infra/systemd/oz-enterprise-alerts.* /etc/systemd/system/
sudo cp infra/systemd/oz-slo-report.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now oz-enterprise-alerts.timer oz-slo-report.timer
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
- `Operations Alerts`
- `SLO Reports`
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
open critical alerts = 0
release manifest/SBOM/provenance generated for every public release
```

## Non-Goals For V1

- MCP
- private user indexing
- user-submitted private repositories
- library owner claiming
- chat assistant
- API keys
