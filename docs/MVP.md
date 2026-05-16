# Beta Completion Snapshot

This repository now implements the PRD beta surface rather than only a tracer bullet.

Implemented:

- Rust workspace and CLI binary.
- Project initialization and dependency fingerprinting.
- Keychain-backed login with file fallback.
- Agent skill install for Codex, Claude Code, Cursor, Cline, and Continue.
- Local content-addressed object store at `~/.codo/objects`.
- Pack-backed `oz pull`, hardlink materialization, update, status, doctor, config, and machine-wide GC tracking initialized projects.
- Catalog-backed local `oz suggest` fallback.
- API-backed semantic `oz suggest` and `oz search`, with pgvector/FTS chunk retrieval, optional rerank, and auto-pull for returned coordinates.
- Local and S3-backed pack/catalog/admin storage.
- JWT auth issuer/verifier.
- Anonymous telemetry ingestion without query text.
- Admin dashboard with index request queue and approve-to-crawl action.
- 15 launch libraries crawled, chunked, indexed, and packed.
- Crawler queue worker, Lambda crawler entrypoint, scheduled recrawl queueing, pack publication, catalog upsert, and Aurora chunk indexing.
- Optional OpenAI embeddings and reranking with SHA/DynamoDB caching.
- Aurora/Postgres schema with pgvector, FTS, metadata, requests, telemetry, and crawler jobs.
- CDK stack for AWS beta deployment.
- Release scripts, npm wrapper, Homebrew formula generation, and curl-install source script.

Operational steps still required outside this codebase:

- Run `cdk deploy` in the target AWS account.
- Apply `infra/sql` migrations to the deployed Aurora database.
- Run `scripts/index-registry-to-db.py` after seed rebuilds or production recrawls when not using the crawler Lambda path.
- Publish `registry/catalog.json` and `registry/packs` to the deployed packs bucket.
- Build and upload release artifacts for every target OS/architecture.
- Publish public Privacy Policy, ToS, and status page content.
