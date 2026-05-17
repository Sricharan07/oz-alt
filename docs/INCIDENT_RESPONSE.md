# Incident Response

## Severity

- SEV-1: Registry API unavailable for most authenticated users, token issuer broken, or pack integrity failure.
- SEV-2: Search/suggest degraded, crawler queue stalled, admin dashboard unavailable, or one launch library unavailable.
- SEV-3: Individual crawl failures, delayed telemetry, non-critical admin defects.

## Response Targets

- SEV-1: acknowledge within 30 minutes, update status every 30 minutes.
- SEV-2: acknowledge within 4 hours, update status every 2 hours.
- SEV-3: triage within 2 business days.

## Runbook

1. Open `https://admin.tryoz.dev/admin` and check `System Checks`, `Operations Alerts`, `SLO Reports`, crawler jobs, search quality, backup runs, and promotion history.
2. Check caddy/nginx and `oz-api` 5xx rate through host/container logs.
3. Check protected metrics:
   `curl -H "Authorization: Bearer $OZ_METRICS_TOKEN" https://api.tryoz.dev/metrics`.
4. Check `oz-api`, `oz-worker`, and `oz-scheduler` logs for auth, pack, crawl, and retrieval failures.
5. Check S3 pack and catalog object availability.
6. Check Postgres connectivity, pgvector indexes, and database capacity.
7. Check Redis queue/cache connectivity and queue depth.
8. Check worker health and failed crawl job records.
9. Disable rerank with missing `ZEROENTROPY_API_KEY`/`JINA_API_KEY`/`COHERE_API_KEY` or model errors; lexical/FTS/vector fallback remains available.
10. If pack integrity fails, remove the affected catalog entry and rebuild the pack from fixture source.
11. After mitigation, run:
    `docker exec docker-oz-api-1 python /app/scripts/enterprise-alerts.py --api-url https://api.tryoz.dev --require-search-quality`.
12. Write a short postmortem for SEV-1/SEV-2 with timeline, cause, fix, prevention, and owner.

## Customer Communication

Use the status page for active incidents. Include affected endpoints, start time, current mitigation, and next update time. Do not include user identifiers, tokens, queries, or private project details.
