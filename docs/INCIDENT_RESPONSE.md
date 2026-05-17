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

1. Check caddy/nginx and `oz-api` 5xx rate.
2. Check `oz-api`, `oz-worker`, and `oz-scheduler` logs for auth, pack, crawl, and retrieval failures.
3. Check S3 pack and catalog object availability.
4. Check Postgres connectivity, pgvector indexes, and database capacity.
5. Check Redis queue/cache connectivity and queue depth.
6. Check worker health and failed crawl job records.
7. Disable rerank with missing `OPENAI_API_KEY` or model errors; lexical/FTS fallback remains available.
8. If pack integrity fails, remove the affected catalog entry and rebuild the pack from fixture source.

## Customer Communication

Use the status page for active incidents. Include affected endpoints, start time, current mitigation, and next update time. Do not include user identifiers, tokens, queries, or private project details.
