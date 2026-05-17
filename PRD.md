# Oz v1 Production PRD

## 1. Product Shape

Oz is a hosted documentation platform for coding agents.

The product surfaces are:

- `tryoz.dev` - public product site.
- `app.tryoz.dev` - user dashboard.
- `admin.tryoz.dev` - internal admin dashboard.
- `api.tryoz.dev` - CLI and platform API.
- `@hiringbae/oz`, GitHub releases, Homebrew, and curl installer - CLI distribution.

The agent workflow stays file-based:

```bash
oz login
oz init
oz search "middleware jwt cookies" vercel/next.js
oz pull vercel/next.js
rg "NextRequest" .codo/vendors/vercel/next.js@15/
cat .codo/vendors/vercel/next.js@15/_symbols/NextRequest.md
```

Oz does not ship an MCP server, chat assistant, private user indexing, library-owner claiming, or user-created API keys in v1.

## 2. Core Promise

Coding agents should stop guessing library APIs from stale training data.

Oz gives them:

- A CLI that authenticates to the hosted registry.
- Curated docs packs stored locally under `.codo/vendors`.
- Semantic path search that returns file coordinates, not injected documentation blobs.
- Local grep/read/glob workflows that fit existing agent behavior.
- Admin-controlled crawling, quality gates, freshness, and recrawl operations.

## 3. Architecture

Production is Docker-first with S3-compatible object storage.

Required services:

- `oz-api` - auth, CLI API, search, suggest, pull metadata, freshness, usage, admin APIs.
- `oz-web` - public site, user dashboard, admin dashboard.
- `oz-worker` - Scrapling crawl, normalize, chunk, symbol extraction, embedding, quality/eval, pack build, promotion.
- `oz-scheduler` - freshness checks, recrawl scheduling, cleanup, usage rollups.
- Postgres with pgvector - product state, auth state, catalog state, embeddings, logs.
- Redis - queues, rate limits, short-lived cache, job locks.
- S3 - signed `.ozpack` files, raw crawl snapshots, crawl artifacts, large logs, backups.
- Caddy or Nginx - TLS and routing for `tryoz.dev` subdomains.

Do not use Lambda, API Gateway, Aurora Data API, SQS, DynamoDB, EventBridge, Cognito, Auth0, or Clerk as production control-plane dependencies.

S3 is allowed because it stores large immutable artifacts behind a `BlobStore`/storage interface. Postgres is the source of truth for product state.

## 4. Auth

Oz owns auth in v1.

Web login:

- Email and password.
- Argon2 password hashing.
- Admin invite and reset links for controlled beta.
- Self-service signup can be enabled or disabled by environment flag.
- HttpOnly, Secure, SameSite cookies.
- CSRF protection on dashboard/admin mutations.

CLI login:

- OAuth-style device authorization flow.
- `oz login` prints a browser URL and user code.
- The user approves the CLI session from the same web account.
- CLI receives a short-lived access JWT and opaque refresh token.
- Refresh tokens are hashed in Postgres and stored locally in the OS keychain.
- Refresh tokens rotate and revoked/disabled users fail immediately.

Minimum auth tables:

- `users`
- `web_sessions`
- `password_reset_tokens`
- `device_codes`
- `cli_refresh_tokens`
- `auth_audit_logs`

Admin role is seeded manually only.

## 5. User Dashboard

Routes:

- `/signup`
- `/login`
- `/dashboard`
- `/device`
- `/account`

Users can:

- Create or access an account.
- View install and setup instructions.
- Approve CLI login devices.
- See current CLI sessions.
- Revoke CLI sessions.
- See their own usage.
- Change password and log out.

Users cannot:

- Add library sources.
- Crawl libraries.
- Upload private docs.
- Create API keys.
- Access admin tools.

## 6. Admin Dashboard

Routes must cover:

- Libraries
- Library profiles
- Sources
- Crawl jobs
- Crawl logs
- Quality runs
- Eval runs
- Pack builds
- Promotions and rollbacks
- Freshness policies
- Users
- Usage
- Audit logs
- System health

Admins can:

- Create vendor/library records.
- Add and edit library profiles.
- Add source URLs and source types.
- Configure allowed hosts/paths and denied paths.
- Configure required topics and expected symbols.
- Queue crawls.
- Watch job logs and errors.
- Run quality/eval gates.
- Promote a pack only when gates pass.
- Roll back a promotion.
- Configure freshness and recrawl intervals.
- Disable users and reset passwords.
- Inspect usage and zero-result search/suggest events.

Every admin mutation must write `admin_action_logs`.

## 7. Library Profiles

Every production crawl requires a profile.

Profile fields:

```json
{
  "vendor": "vercel",
  "library": "next.js",
  "source_url": "https://nextjs.org/docs",
  "allowed_hosts": ["nextjs.org", "github.com"],
  "allowed_paths": ["/docs", "/vercel/next.js/tree/canary/docs"],
  "denied_paths": ["/blog", "/showcase", "/marketing"],
  "source_priority": ["llms_txt", "official_docs", "github_docs", "type_defs", "openapi"],
  "required_topics": ["routing", "middleware", "cookies", "server actions"],
  "expected_symbols": ["NextRequest", "NextResponse", "cookies", "redirect"],
  "recrawl_interval_hours": 24
}
```

Crawler refuses production crawls without a matching profile.

## 8. Indexing Pipeline

Admin-controlled flow:

1. Create library.
2. Add source and profile.
3. Validate profile.
4. Enqueue crawl.
5. Scrapling fetches allowed sources.
6. Normalize HTML/Markdown.
7. Sanitize secrets and rejected junk.
8. Split into stable Markdown files.
9. Extract symbols.
10. Chunk docs with deterministic `chunk_sha`.
11. Embed chunks with cached OpenAI embeddings.
12. Write catalog and chunks to Postgres.
13. Run quality gate.
14. Run eval gate.
15. Build signed `.ozpack`.
16. Upload pack to S3.
17. Promote version and publish catalog ref.

Failed quality/eval runs cannot be promoted.

## 9. Source Discovery

Discovery order:

1. `llms-full.txt`
2. `llms.txt`
3. `sitemap.xml`
4. Official docs pages
5. GitHub docs/examples
6. Type definitions
7. OpenAPI specs

Strict filters run before fetch:

- Allowed host.
- Allowed path.
- Denied path.
- Source type allowed by profile.
- Robots/terms policy.

Rejection reasons are stored for every skipped page.

## 10. Pack Layout

Every pulled library materializes as:

```txt
.codo/vendors/<vendor>/<library>@<version>/
  INDEX.md
  README.md
  _meta.json
  _symbols/
    <Symbol>.md
  guides/
  api-reference/
  examples/
```

Every file is Markdown and grep-friendly.

## 11. Search

`oz search` returns local file paths, not documentation content.

Ranking combines:

- Postgres FTS/BM25.
- pgvector similarity.
- Symbol match.
- Heading match.
- Path match.
- Source priority.
- Quality score.
- Freshness score.
- Content type.

Retrieval shape:

```txt
vector top-K
+ FTS top-K
+ symbol/path candidates
-> union
-> aggregate to file-level score
-> dedupe by path
-> rerank unique paths when needed
-> return only materializable paths
```

If a result points to a library missing locally, the CLI auto-pulls it before printing paths.

## 12. Quality Gates

Promotion requires:

- Required topics covered: 100%.
- Required symbols covered: 100%.
- Expected-path recall@5: at least 85%.
- Semantic precision@5: at least 75%.
- Duplicate top-5 rate: 0%.
- Junk top-5 rate: 0%.
- Every returned path materializes after pull.
- Pack signature and hashes verify.

Eval types:

- Pull plus `rg` eval.
- Semantic search eval.
- Materialization eval.
- Junk-content eval.

## 13. Freshness

Default recrawl policies:

- Top 100 libraries: daily.
- Top 1,000 libraries: every 15 days.
- Top 5,000 libraries: every 30 days.
- Others: every 45 days.
- Admin override: anytime.

Recrawl only when:

- Library was requested recently or policy requires it.
- No crawl is already running.
- Source profile validates.
- The source has changed or freshness threshold elapsed.

CLI serves current local docs immediately and warns if stale.

## 14. Usage And Privacy

Track:

- Login events.
- CLI sessions.
- Pulls.
- Searches.
- Suggests.
- Pack downloads.
- Stale warnings.
- Crawl jobs.
- Quality runs.
- Eval runs.
- Pack promotions.
- Rollbacks.
- Admin actions.
- API errors.
- Rate limits.

Do not store:

- User code.
- Conversation history.
- Full raw query text by default.
- Secrets.
- Private local paths.

Store:

- `query_length`
- `query_hash`
- `library_scope`
- `result_count`
- `latency_ms`
- `user_id`
- `machine_id_hash`
- `project_fingerprint_hash`

## 15. Security

Minimum requirements:

- Argon2 password hashing.
- Opaque refresh tokens stored hashed.
- Refresh token rotation.
- Secure cookies.
- CSRF protection.
- Redis-backed rate limits.
- Structured audit logs.
- Disabled users immediately fail auth.
- Server-side telemetry allowlist.
- Signed pack manifests.
- CLI pack verification before unpack.

## 16. Observability

Required:

- Structured JSON logs.
- Request IDs.
- Job IDs.
- User IDs.
- Admin audit logs.
- Error dashboard.
- API latency/error dashboard.
- Queue-depth dashboard.
- Crawl and pack-build failure dashboard.
- Daily Postgres backups to S3.
- Backup restore test.
- Incident runbook.

## 17. Release

Release artifacts:

- GitHub release binaries.
- SHA256 files.
- npm wrapper.
- curl installer.
- Homebrew formula.

Release smoke tests:

- `npm install @hiringbae/oz`
- `oz --version`
- `oz login`
- `oz init`
- `oz pull facebook/react`
- `oz search "useEffect cleanup dependency array" facebook/react`
- Pack signature verification.

## 18. Launch Criteria

Public beta requires:

1. 15+ seed libraries indexed through the admin pipeline.
2. Production crawl, quality, eval, pack build, and promotion history exists.
3. CLI OAuth works on macOS, Linux, and Windows.
4. User dashboard works for signup/login/device/account/usage.
5. Admin dashboard works for profiles/crawls/jobs/quality/evals/promotions/freshness/users/audit.
6. Freshness scheduler has populated policies and proved at least one recrawl.
7. Search precision@5 and materialization evals pass.
8. Rate limits and audit logs are enabled.
9. Privacy, terms, status, and incident docs are published.
10. npm/GitHub/curl/Homebrew distribution smoke tests pass.

## 19. Explicitly Out Of Scope For v1

- MCP server.
- Private user indexing.
- User-submitted private repos.
- Library owner claiming.
- API keys.
- Billing.
- Teamspaces.
- Chat assistant.
- Browser extension.
- Multi-region deployment.
