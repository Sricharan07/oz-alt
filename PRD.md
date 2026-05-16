# Oz — Product Requirements Document

**Version:** 1.2 (MVP, cost-optimized, + semantic search)
**Status:** Draft for build
**Owner:** [you]
**Last updated:** May 15, 2026

---

## 1. Summary

Oz is a versioned documentation registry for software libraries, paired with a CLI that lets coding agents pull library docs into a project's local filesystem on demand. Agents then search those docs with their own native file tools (Read, Grep, Glob) — the same way they search source code. Oz replaces hallucinated API calls with version-pinned, byte-accurate library documentation, delivered through the most boring possible mechanism: files on disk.

The cloud is the registry. The CLI is the package manager. The agent's own tools are the search interface. There is no MCP server, no daemon, no mount, no proxy, no new tool surface for the agent to learn.

---

## 2. Problem

Coding agents fail on external library code because their training data is stale and they have no reliable mechanism to fetch current, version-accurate docs.

Existing solutions are inadequate:

- **Context7** ships an MCP tool that dumps a docs blob into context per call. It pollutes the agent's tool list, requires the magic phrase "use context7", offers no navigation, no symbol-level precision, no cross-library composition, and no session memory. Agents over-search and under-find.
- **Manual copy-paste from docs sites** breaks the agent's flow and is version-blind.
- **Local FUSE mounts (smfs)** are excellent UX but require kernel-level installation and per-machine storage costs that don't scale to broad developer adoption.
- **Browser-based research by the agent** is slow, expensive in tokens, and produces inconsistent results.

The gap: there is no way for an agent to access version-accurate library docs through its **own native tools**, without new tool surface, without ongoing local storage cost, and without server-roundtrip per search.

---

## 3. Solution

Oz treats library documentation the way npm treats library code:

- A central, versioned, content-addressed cloud registry of documentation.
- A CLI (`oz`) the developer installs once.
- A skill installed into the agent's config that teaches it: when you encounter an external library, run `oz pull <lib>` to fetch docs locally, then search those files with your normal tools.
- Pulled docs land in `.codo/vendors/<library>@<version>/` as predictable Markdown trees with a top-level `INDEX.md`, a `_symbols/` directory of per-API files, and structured `guides/`, `api-reference/`, `examples/` folders.
- Freshness checks happen automatically on every CLI call. Stale libraries get a stderr warning the agent reads.

The agent never learns a new search protocol. It searches docs the same way it searches the user's source code.

---

## 4. Goals & Non-goals

### Goals

1. Ship a public beta with 15+ indexed libraries within 8 weeks.
2. Zero new agent-facing tools or MCP servers; entire agent contract is one skill document.
3. Sub-200ms `oz pull` for libraries already cached in the user's global object store.
4. Cross-project deduplication: a library pulled in one project costs zero additional bytes when pulled in another.
5. Version pinning derived from the user's actual lockfile, not from prompt text.
6. Support Claude Code, Cursor, Codex, Cline, and Continue at launch.
7. Operate beta at < $250/mo all-in.

### Non-goals (v1)

1. Private or internal documentation hosting (designed-for, not built).
2. Real-time crawling on demand (unindexed libraries queue to admin dashboard).
3. Local mounting (FUSE/NFS) or background daemons.
4. An MCP server. Explicitly rejected.
5. A web UI for end users. Admin dashboard only.
6. IDE plugins. CLI + skill is the entire surface.
7. Multi-language support in suggest queries (English only at launch).
8. Multi-region deployment.

---

## 5. Users & use cases

### Primary user: the developer

A developer working in an AI coding agent (Claude Code, Cursor, etc.) on a project with external dependencies. They want their agent to write correct, version-accurate code without manual intervention.

**Their interaction with Oz, in full:**

```bash
# One-time setup
oz login
oz install        # writes skill into agent config(s)

# Per-project, once
cd my-project
oz init           # creates .codo/lock.json, updates .gitignore

# Everything else is handled by the agent
```

The developer does not learn the agent-facing commands. They appear in their terminal history as a side effect of the agent's work.

### Secondary user: the coding agent

The agent reads its skill, recognizes external libraries in tasks, runs:

```bash
oz suggest "<one-line description>"
oz pull <library>
```

Then searches `.codo/vendors/<library>@<version>/` with its native file tools.

### Tertiary user: Oz operators (you)

Internal admin dashboard for managing the crawler, handling index requests, monitoring registry health.

---

## 6. User stories

**US-1.** As a developer, I install Oz once with a single command and my coding agent immediately gets access to current library docs across every project I work in.

**US-2.** As a developer, I run `oz init` in any new project and my agent automatically scopes documentation to the libraries and versions actually in my lockfile.

**US-3.** As an agent, when I encounter `import { NextRequest } from 'next/server'`, I pull Next.js docs locally and use my Grep tool to find the exact `NextRequest.cookies.get` signature for the version pinned in `package.json`.

**US-4.** As an agent, when a user asks "add JWT auth to my Next.js app," I run `oz suggest "JWT authentication in Next.js"` and get back a ranked list of relevant libraries to pull.

**US-5.** As an agent, when the docs I'm relying on are stale, Oz tells me on stderr and I run `oz update` before proceeding.

**US-6.** As a developer, when my agent asks for a library that isn't indexed, Oz logs the request to the admin dashboard and my agent tells me "this library isn't indexed yet, request submitted."

**US-7.** As a developer with 20 projects on my laptop using overlapping libraries, my disk usage stays small because Oz deduplicates across projects via a global content-addressed store.

**US-8.** As an Oz operator, I see in the admin dashboard which libraries developers are asking for that I haven't indexed yet, sorted by request volume.

---

## 7. Functional requirements

### 7.1 CLI (`oz`)

**FR-1.1.** `oz login` — device-flow OAuth, stores credentials in OS keychain. Discloses telemetry policy inline; collects opt-out signal if user declines.

**FR-1.2.** `oz install` — detects coding agents installed (Claude Code, Cursor, Codex, Cline, Continue) by inspecting standard config paths. Writes the Oz skill into each detected agent's config. Idempotent. Re-running upgrades the skill.

**FR-1.3.** `oz install --<agent>` — explicit per-agent install. Useful when auto-detection fails.

**FR-1.4.** `oz init` — run once per project. Detects `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`. Writes `.codo/lock.json` (initially empty), appends `.codo/vendors/` to `.gitignore`, creates `.codo/.gitignore` for safety.

**FR-1.5.** `oz suggest "<query>"` — POSTs query + project fingerprint to `/suggest`. Prints ranked library names and one-line justifications. JSON output via `--json`.

**FR-1.6.** `oz search "<query>" [<library>]` — semantic file-path search. POSTs query + project fingerprint (+ optional library scope) to `/search`. Server returns ranked local file paths under `.codo/vendors/...` that best match the query. If any returned paths reference libraries not yet pulled, the CLI auto-pulls them before printing results, so every printed path is guaranteed to exist on disk. Output is one path per line in `<path>` or `<path>:<line>` format, ripgrep-style. JSON output via `--json`.

Example:
```bash
oz search "middleware jwt cookies" vercel/next.js
```
Output:
```
.codo/vendors/vercel/next.js@15/_symbols/NextRequest.md
.codo/vendors/vercel/next.js@15/guides/middleware.md
.codo/vendors/panva/jose@latest/_symbols/jwtVerify.md
```

The agent then uses its native Read and Grep on these paths. `oz search` is a coordinate-returning command, not a content-returning command — content always comes from local files read by the agent.

**FR-1.7.** `oz pull <library>` — resolves library@version against the project's lockfile, fetches the pack from `/pack/...`, unpacks into `~/.codo/objects/`, hardlinks into `.codo/vendors/<library>@<version>/`, updates `.codo/lock.json`. Atomic; resumable on interrupt.

**FR-1.8.** `oz update [<library>]` — refetches refs, identifies stale libraries, re-pulls. `oz update` with no argument updates all.

**FR-1.9.** Freshness check on every CLI call. Every `oz` command makes a single lightweight `GET /refs?fingerprint=<sha>` call. If any pulled library is stale, prints to stderr: `oz: <library>@<version> is stale (newer: <new-version>). Run 'oz update <library>'.`

**FR-1.10.** `oz gc` — removes objects from `~/.codo/objects/` not referenced by any project lockfile on the machine.

**FR-1.11.** `oz doctor` — validates installation: keychain access, object store integrity, skill version sync, network reachability.

**FR-1.12.** `oz status` — shows pulled libraries, versions, freshness, disk usage.

**FR-1.13.** `oz config` — `set`, `get`, `unset` for `telemetry`, `api_url`, `auto_update_skill`.

**FR-1.14.** Skill version sync. On every command, the CLI checks the installed skill version against its embedded current version. If different, the skill is rewritten silently (configurable via `oz config set auto_update_skill off`).

### 7.2 The skill (agent contract)

**FR-2.1.** A single Markdown document written into each agent's standard config file location.

**FR-2.2.** Exact content (locked):

```markdown
# Oz: Live documentation for external libraries

When this project uses an external library (anything from package.json,
requirements.txt, go.mod, Cargo.toml, or any SDK/framework you're integrating),
use Oz to get version-accurate docs before writing code.

DO NOT consult the web or your training memory for external library APIs
before trying Oz. Pull first, then read.

## Workflow

1. Identify the library you need. If unsure, run:
   `oz suggest "<one sentence describing what you're trying to do>"`
   This returns a ranked list of library names.

2. Pull the docs:
   `oz pull <library>`
   Docs land in `.codo/vendors/<library>@<version>/` as Markdown files.

3. Find the right files for your task. Two ways to search:

   **Semantic search (preferred when you don't know the file path):**
   `oz search "<query>" [<library>]`
   Returns a ranked list of local file paths under `.codo/vendors/...`.
   Auto-pulls any referenced libraries that aren't local yet.
   Example: `oz search "middleware jwt cookies" vercel/next.js`

   **Native file tools (preferred when you know roughly where to look):**
   Use your normal Glob, Grep, and Read tools on `.codo/vendors/...`, exactly
   as you would search source code in this repo:
   - Glob to discover structure: `.codo/vendors/<library>@<version>/**/*.md`
   - Grep for keywords, symbol names, error messages, concepts
   - Start with `INDEX.md` for an overview
   - Symbol lookup: `_symbols/` contains one file per public API,
     named by symbol (e.g. `_symbols/NextRequest.md`)

4. Read the files. After `oz search` returns paths, or after Glob/Grep
   locates files, use Read to load their contents. `oz search` only returns
   paths; content always comes from your Read tool.

5. If Oz prints "library X is stale" on stderr, run `oz update <library>`
   before continuing.

## Rules

- Pull before you guess. A 200ms pull beats a hallucinated API call.
- For unfamiliar libraries, start with `oz search` — it's a one-shot way to
  find the right files across multiple libraries at once.
- Version matters: Oz pins to this project's lockfile, your memory does not.
- If `oz suggest` returns nothing useful, tell the user the library isn't
  indexed yet (Oz has logged the request).
```

**FR-2.3.** Per-agent variants. Same content, formatted for each target:
- Claude Code → `CLAUDE.md` or `.claude/skills/oz.md`
- Cursor → `.cursorrules` or `.cursor/rules/oz.mdc`
- Codex → `AGENTS.md`
- Cline → `.clinerules`
- Continue → `.continuerc`

### 7.3 On-disk layout (the search target)

**FR-3.1.** Every pulled library produces this exact structure:

```
.codo/vendors/<vendor>/<library>@<version>/
├── INDEX.md                  table of contents, one line per topic
├── README.md                 library overview, when to use it
├── _meta.json                version, source URLs, indexed_at, ref_sha
├── _symbols/                 one file per public API
│   ├── <Symbol>.md
│   └── ...
├── guides/                   conceptual docs
├── api-reference/            exhaustive API surface
└── examples/                 runnable code samples
```

**FR-3.2.** Every file is plain Markdown. No frontmatter beyond standard YAML where needed. Code blocks are fenced and language-tagged. Headings are stable and grep-friendly.

**FR-3.3.** `_symbols/<SymbolName>.md` is the canonical entry for a public API. Format:

```markdown
# <SymbolName>

**Kind:** function | class | method | type | constant
**Signature:** `<exact signature>`
**Source:** <url>

## Description
...

## Example

​```code
...
​```

## See also
- [<RelatedSymbol>](./RelatedSymbol.md)
```

### 7.4 Cloud API

**FR-4.1.** `POST /suggest`
- Request: `{query: string, project_fingerprint: string, max_results?: number}`
- Response: `{results: [{library, vendor, version, score, reason}], stale_libraries: [...]}`
- Server runs hybrid retrieval (pgvector + BM25) over library metadata, INDEX.md, and chunk embeddings; reranks top 20 with `gpt-4o-mini` using the project fingerprint as context.
- **Rerank gating (cost optimization):** rerank is skipped when top-3 pgvector scores are all > 0.85 (clear winner). Rerank decisions cached for 7 days by `(query_hash, fingerprint_hash)` in DynamoDB.

**FR-4.2.** `POST /search`
- Request: `{query: string, project_fingerprint: string, library_scope?: string, max_results?: number}`
- Response: `{results: [{path: string, line?: number, score: number, library: string, version: string}], libraries_to_pull: [{vendor, library, version}], stale_libraries: [...]}`
- Server runs hybrid retrieval (pgvector + BM25) over **chunk-level embeddings** (not library-level as in `/suggest`). Returns ranked file paths in the canonical `.codo/vendors/<vendor>/<library>@<version>/<path>` form. The CLI is responsible for ensuring referenced libraries are pulled locally before printing paths — `libraries_to_pull` enumerates anything missing from the user's lockfile fingerprint.
- Reuses the same rerank gating + DynamoDB cache as `/suggest`, keyed on `(query_hash, fingerprint_hash, library_scope)`.
- `library_scope` constrains search to one library (e.g. `vercel/next.js`); omitted = cross-library search bounded by project fingerprint.

**FR-4.3.** `GET /refs/<vendor>/<library>` — returns the current commit ref for a library. Used for freshness checks.

**FR-4.4.** `GET /refs?fingerprint=<sha>` — bulk freshness check. Returns list of stale libraries given a lockfile SHA. Served directly from S3 with long Cache-Control headers (immutable per fingerprint+ref combo).

**FR-4.5.** `GET /pack/<vendor>/<library>/<version>` — returns a zstd-compressed pack containing all blobs and trees for that version. Verifiable by manifest SHA. Served as a direct S3 redirect with `Cache-Control: public, max-age=31536000, immutable` (packs are immutable by version).

**FR-4.6.** `POST /index-request` — `{library_name, vendor_hint, source_url_hint, requesting_user}`. Writes to admin queue. Rate-limited per user.

**FR-4.7.** `POST /telemetry` — anonymous event ingestion. Events: `suggest_query`, `search_query`, `pull_completed`, `update_run`, `index_request_filed`. Never includes query content for privacy; only query length, result count, library names involved.

**FR-4.8.** Authentication via JWT in `Authorization: Bearer <token>` header. Tokens issued by `oz login` device flow against a hand-rolled Lambda-based JWT issuer (no Cognito dependency).

### 7.5 Crawler and indexer

**FR-5.1.** Scrapling-based crawler service running on **Lambda** (SQS-driven). For libraries with docs sites exceeding the 15-minute Lambda timeout, jobs fail over to a single Fargate Spot task. Failover detection is automatic via SQS DLQ.

**FR-5.2.** Per source, fetches in order: `/llms.txt`, `/llms-full.txt`, `/sitemap.xml`, declared docs URLs, linked GitHub repo's `/docs` folder, OpenAPI specs, type definitions (`.d.ts`, `.pyi`).

**FR-5.3.** Normalizer converts HTML to clean Markdown, removing navigation and footer noise, preserving headings, code blocks, and source URLs.

**FR-5.4.** Chunker splits on H2/H3 boundaries, max ~1KB tokens per chunk.

**FR-5.5.** Symbol extractor uses tree-sitter on code blocks and adjacent type definitions to emit per-symbol files for `_symbols/`.

**FR-5.6.** INDEX.md generator produces a top-level table of contents per library, with one line per major topic and links into the tree.

**FR-5.7.** Embedding pipeline: every chunk embedded with `text-embedding-3-small`. Cached by chunk SHA; unchanged content costs zero on recrawl.

**FR-5.8.** Recrawl cadence: every 24 hours per library, scheduled via EventBridge. Diff-aware via content addressing.

**FR-5.9.** Seed library set (launch): Next.js, React, Vue, Svelte, Stripe, Supabase, Prisma, Tailwind, FastAPI, Django, Express, Hono, Vercel SDK, OpenAI SDK, Anthropic SDK. Minimum 15.

### 7.6 Admin dashboard

**FR-6.1.** Internal-only Next.js app, auth-gated. Hosted on Vercel free tier or as a single Lambda behind API Gateway — not on dedicated Fargate.

**FR-6.2.** Views:
- Index requests queue, sorted by request volume.
- One-click "approve + crawl" action.
- Library catalog with health: last_crawled, error rate, version count, total pull count.
- Top suggest queries with zero useful results.
- Crawler job status and failure logs.

### 7.7 Storage

**FR-7.1.** Content-addressed object store. Every blob keyed by SHA-256. Every tree (folder snapshot) keyed by SHA of its sorted children. Every commit keyed by SHA of `{tree, parent, timestamp, library, version}`.

**FR-7.2.** Cloud: S3 with **Intelligent-Tiering** enabled on the objects bucket. Two buckets: `oz-objects` (individual blobs) and `oz-packs` (per-version delta-compressed bundles). Intelligent-Tiering auto-moves cold blobs to IA/Glacier without manual lifecycle policies.

**FR-7.3.** Local: `~/.codo/objects/` mirrors the cloud structure on the user's machine. Pulled libraries materialize into `.codo/vendors/` via hardlinks where the filesystem supports them; file copies on Windows or cross-device situations.

**FR-7.4.** **Aurora Serverless v2 (Postgres)** holds registry metadata: vendors, libraries, versions, refs, commits, trees, blobs_meta, users, index_requests, telemetry_events, suggest_logs. Min 0.5 ACU (avoids cold-start), auto-scales up under load.

**FR-7.5.** pgvector extension on Aurora holds chunk embeddings. Postgres FTS handles BM25 (no separate Tantivy service).

**FR-7.6.** **DynamoDB** holds rerank cache (`query_hash` + `fingerprint_hash` → top-3 result, TTL 7 days). On-demand billing; effectively free at beta scale.

---

## 8. Non-functional requirements

**NFR-1. Performance.**
- `oz pull` for a cached library: < 200ms (zero network).
- `oz pull` for a new library: < 5s for 95th percentile library size (~10MB).
- `oz suggest` API call: < 1s P95.
- `GET /refs` freshness check: < 100ms P95, served from S3 with long cache headers.
- Lambda cold starts on suggest API: < 1.5s. Mitigated by provisioned concurrency on the suggest function (1 instance) if needed.

**NFR-2. Scale (beta).**
- 10K daily active developers.
- 100K daily `suggest` calls.
- 1M daily `pull`/freshness calls (cached aggressively via S3 immutable headers).

**NFR-3. Reliability.**
- 99.5% API uptime in beta.
- CLI works offline for already-pulled libraries.
- Atomic pulls: a failed pull never leaves a partial `.codo/vendors/` directory.

**NFR-4. Security.**
- All API calls authenticated via JWT.
- Tokens stored in OS keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service).
- Pack manifests signed; CLI verifies SHA before unpacking.
- No user code or query contents ever transmitted in telemetry.

**NFR-5. Privacy.**
- Telemetry on by default, disclosed at `oz login`, opt-out via `oz config set telemetry off`.
- Telemetry events: command name, library names, anonymized user ID, query length (not content), result count. No file paths, no source code, no query text.

**NFR-6. Portability.**
- CLI ships for macOS arm64/x64, Linux arm64/x64, Windows x64.
- Distribution: GitHub Releases, Homebrew, `curl | sh`, npm global package.

**NFR-7. Cost discipline (operator).**
- Beta-scale (10K DAU) AWS + OpenAI spend target: **< $250/mo**.
- Stretch floor: ~$190/mo with all optimizations applied (see §11).
- See §11 for detailed cost breakdown.

---

## 9. Architecture

### 9.1 High-level

```
┌── AWS (single region) ──────────────────────────────────────────┐
│                                                                 │
│  Scrapling crawlers (Lambda + SQS, Fargate Spot failover)       │
│        │                                                        │
│        ▼                                                        │
│  Normalizer → Chunker → Symbol extractor (Lambda)               │
│        │                                                        │
│        ▼                                                        │
│  OpenAI embeddings (text-embedding-3-small, SHA-cached)         │
│        │                                                        │
│        ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Aurora Serverless v2 Postgres (0.5 ACU min)            │    │
│  │   ├─ pgvector (embeddings)                              │    │
│  │   ├─ Postgres FTS (BM25)                                │    │
│  │   └─ Registry metadata                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  S3: oz-objects (Intelligent-Tiering), oz-packs (hot)   │    │
│  │  Public read for /pack with long immutable cache        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  DynamoDB: rerank cache (7-day TTL, on-demand)          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  API (Lambda via Web Adapter, outside VPC, no NAT):             │
│   POST /suggest    (library-level rec + gated rerank)           │
│   POST /search     (file-path rec + gated rerank)               │
│   GET  /refs       (S3-served, immutable cache)                 │
│   GET  /pack       (S3 redirect, immutable cache)               │
│   POST /index-request                                           │
│   POST /telemetry                                               │
│   POST /auth/device, POST /auth/token (hand-rolled JWT)         │
│                                                                 │
│  CloudWatch: logs + minimal metrics                             │
│  EventBridge: 24h recrawl scheduler                             │
└─────────────────────────────────────────────────────────────────┘

┌── USER MACHINE ──────────────────────────────────────────┐
│  oz CLI (Rust)                                           │
│    login / install / init                                │
│    suggest / search / pull / update                      │
│    gc / doctor / status / config                         │
│                                                          │
│  ~/.codo/objects/   (CAS, dedup across all projects)     │
│                                                          │
│  <repo>/.codo/                                           │
│    ├─ vendors/<vendor>/<library>@<version>/  (hardlinks) │
│    │   ├─ INDEX.md                                       │
│    │   ├─ _symbols/                                      │
│    │   └─ guides/, api-reference/, examples/             │
│    ├─ lock.json   (committed)                            │
│    └─ .gitignore                                         │
│                                                          │
│  AGENTS.md / CLAUDE.md / .cursorrules  (skill installed) │
└──────────────────────────────────────────────────────────┘
```

### 9.2 Key architectural decisions (cost-driven)

- **Lambda over Fargate** for API and most crawl jobs. Beta traffic is bursty; Fargate's always-on pricing loses to Lambda's per-invocation pricing below ~50K DAU. Single Fargate Spot task on standby for crawl jobs exceeding 15-minute Lambda timeout.
- **No NAT Gateway.** Lambdas run outside VPC; database access uses RDS Proxy with IAM auth or whitelisted Lambda CIDR. Saves ~$35/mo.
- **No CloudFront.** S3 serves `/pack` and `/refs` directly with `Cache-Control: public, max-age=31536000, immutable` headers. Packs are content-addressed and immutable by version, so caching is trivial. Saves ~$25/mo.
- **No Cognito.** Hand-rolled JWT issuer in Lambda (~50 lines). Saves $10/mo and removes a dependency.
- **Postgres FTS over Tantivy.** Same Aurora instance handles BM25 via Postgres FTS, removing the need for a separate search service.
- **Aurora Serverless v2 (min 0.5 ACU).** Auto-scales with traffic but never goes fully cold (0 ACU adds ~10s cold start on first query). 0.5 ACU minimum costs ~$45/mo vs. $120 for fixed RDS.
- **S3 Intelligent-Tiering** auto-tiers cold blobs without manual lifecycle policies. Halves storage cost over time.
- **Rerank gating.** `gpt-4o-mini` rerank is skipped when top-3 pgvector scores all exceed 0.85, and results are cached for 7 days in DynamoDB by `(query_hash, fingerprint_hash)`. Cuts rerank cost by ~60%.

---

## 10. Build phases (8 weeks)

### Phase 1 — Foundations (Week 1)

- Rust workspace: `oz-objects` (CAS, SHA-256, zstd packs), `oz-cli` (subcommand stubs).
- TypeScript API service scaffold deployed as Lambda. Health check + `/refs/:vendor/:lib` returning hardcoded data.
- AWS infra via CDK: Aurora Serverless v2 (Postgres + pgvector), S3 (`oz-objects`, `oz-packs`), Lambda functions, SQS queues, DynamoDB rerank cache, CloudWatch.
- Aurora schema: `vendors`, `libraries`, `versions`, `refs`, `commits`, `trees`, `blobs_meta`, `index_requests`, `users`, `telemetry_events`.

**Done:** `oz --version` runs locally; API responds; AWS stack deploys clean; ~$50/mo idle cost.

### Phase 2 — Object store + tracer-bullet library (Week 2)

- Object store roundtrip: hash → put → pack → fetch → unpack → verify.
- Manually crawl Next.js 15 docs, normalize, chunk, write commit to store.
- `oz pull vercel/next.js@15` works end-to-end against real S3.

**Done:** clean machine runs `oz pull`, gets a real `.codo/vendors/vercel/next.js@15.4.2/` folder full of Markdown.

### Phase 3 — Crawler service + 15 seed libraries (Weeks 3–4)

- Scrapling-based crawler on Lambda, SQS-driven. Fargate Spot failover for long-running jobs.
- Normalizer, chunker, tree-sitter symbol extractor, INDEX.md generator.
- Embedding pipeline with SHA-keyed caching.
- Seed all 15 libraries.

**Done:** all 15 libraries pullable. `.codo/vendors/<any>/` produces a grep-friendly Markdown tree.

### Phase 4 — Suggest & Search APIs (Week 4–5)

- `POST /suggest` (library-level) and `POST /search` (file-path-level) with hybrid pgvector + Postgres FTS retrieval.
- Rerank gating logic: skip when top scores > 0.85; otherwise `gpt-4o-mini` rerank top 20.
- DynamoDB rerank cache with 7-day TTL, keyed for both endpoints.
- `oz search` CLI command: calls `/search`, auto-pulls any missing libraries returned in `libraries_to_pull`, then prints local paths.
- `POST /index-request` writes to admin queue.

**Done:** `oz suggest "add jwt auth to nextjs"` returns Next.js + JWT lib + auth helpers with reasoning. `oz search "middleware jwt cookies" vercel/next.js` returns local file paths the agent can immediately Read.

### Phase 5 — Pull, lockfile, update, freshness (Week 5–6)

- `oz init`, `oz pull`, `oz update`, `oz gc`, `oz doctor`, `oz status`.
- Freshness check on every CLI call (`GET /refs?fingerprint=<sha>`).
- Global object store at `~/.codo/objects/` with hardlink materialization.

**Done:** Full local agent loop works: agent runs `oz suggest` (or `oz search`), then `oz pull` (or auto-pull via search), then uses its own Read/Grep/Glob on `.codo/vendors/`.

### Phase 6 — Login, skill install, distribution (Week 6–7)

- `oz login` device-flow OAuth against Lambda JWT issuer.
- `oz install` detects agents, writes skill, version-syncs on subsequent runs.
- Distribution: GitHub Releases (prebuilt binaries), Homebrew tap, `curl | sh` script, `npm i -g oz` wrapper.
- Telemetry on by default with inline disclosure and opt-out.

**Done:** Single command install on any platform.

### Phase 7 — Admin dashboard + indexing ops (Week 7)

- Internal Next.js admin app (hosted on Vercel free tier or single Lambda).
- Index request queue with one-click approve + crawl.
- Library catalog health view.
- EventBridge-scheduled 24h recrawl, diff-aware.

**Done:** Operator can add a new library without touching the codebase.

### Phase 8 — Hardening + launch (Week 8)

- Rate limits (token bucket in DynamoDB).
- Pack signature verification.
- Crawler retry/backoff.
- Cost monitoring + AWS Budgets alerts at $200/mo threshold.
- Telemetry dashboard.
- Onboard 10 friendly beta users.

**Done:** Public beta.

---

## 11. Cost

### 11.1 Operating cost (monthly, beta scale ~10K DAU)

| Bucket | Cost | Notes |
|---|---|---|
| Aurora Serverless v2 Postgres (min 0.5 ACU) | $45 | Auto-scales; never cold |
| Lambda (API + crawler) | $30 | ~100K invocations/day at beta |
| S3 (Intelligent-Tiering enabled) | $20 | Auto-tiers cold blobs |
| Misc AWS (SQS, CloudWatch, Secrets) | $25 | No NAT Gateway |
| DynamoDB (rerank cache, on-demand) | $5 | Negligible at beta scale |
| OpenAI embeddings (`text-embedding-3-small`) | $20 | SHA-cached, zero waste on recrawl |
| OpenAI rerank (`gpt-4o-mini`, gated + cached) | $35 | Covers both /suggest and /search; 60% cut via gating + DynamoDB cache |
| Domain + monitoring (CloudWatch only) | $15 | No Datadog |
| Auth (hand-rolled JWT in Lambda) | $0 | No Cognito |
| **Total (target)** | **~$195/mo** | |
| **Headroom for spikes / unexpected** | $55 | Buffer to $250/mo |

### 11.2 One-time costs

- Initial crawl + embed of 15 seed libraries: **~$30** (mostly OpenAI embeddings).
- Codex 5.5 build budget (8 weeks, heavy agent use): **~$1,500–3,000**.
- Domain registration + initial brand assets: **~$50**.
- **Total upfront to public beta: ~$2,000–3,500.**

### 11.3 Cost scaling

| Scale | Monthly cost | Primary driver |
|---|---|---|
| 10K DAU (beta) | $195 | — |
| 50K DAU | ~$700 | Aurora ACU scaling + Lambda invocations |
| 250K DAU | ~$3K | OpenAI rerank dominates; move to fixed Fargate |
| 1M DAU | ~$12K | Self-host reranker; provisioned Aurora |

### 11.4 Cost levers for further cuts

1. Drop `gpt-4o-mini` rerank entirely → save $35/mo, lose ~15% suggest/search quality.
2. Aurora min ACU 0 (instead of 0.5) → save $30/mo, accept 10s cold start on idle.
3. Reserved capacity / savings plans after 6 months of stable traffic → save 20–30%.
4. Floor scenario with all cuts: **~$130/mo**.

### 11.5 Unit economics

- Cost per DAU per month (beta): **~$0.020**.
- OpenAI is ~25% of marginal cost and scales linearly with active usage.
- AWS is ~75% and scales sub-linearly until ~50K DAU.

---

## 12. Success metrics

**Primary metrics (MVP success = all three):**

1. **Adoption:** 1,000 weekly active developers within 8 weeks of public launch.
2. **Agent usage rate:** ≥ 70% of `oz pull` calls are made by an agent (not a human), measured via telemetry user-agent.
3. **Pull-to-search ratio:** average ≥ 3 file reads per pull (proves the agent is actually searching, not just pulling and ignoring).

**Secondary metrics:**

- Median time between `oz suggest` (or `oz search`) and first `oz pull`/file Read: < 30 seconds.
- `oz search` precision@5: ≥ 60% of returned paths get a follow-up Read by the agent (proves the search results are usable).
- Stale library detection accuracy: < 1% false-stale rate.
- Index request fulfillment time: median < 7 days from request to first crawl.
- Cross-project dedup ratio: average bytes saved per machine via global object store.
- Seed library coverage: 15+ libraries indexed at launch, 50+ within 90 days.
- Operating cost: ≤ $250/mo at 10K DAU.

**Anti-metrics (watch for these failing):**

- Hallucinated API rate in user code post-Oz install. Hard to measure directly; proxy via user reports and a manual eval suite.
- CLI install-to-first-use friction. Track install → login → init → first pull. Median < 5 minutes.

---

## 13. Risks & mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Crawler produces low-quality chunks for a popular library | High | 40% of build effort on normalizer + symbol extractor; per-library QA review before launch |
| Agent ignores skill, falls back to training memory | High | Skill phrased as forbidding rule, not suggestion; track "did agent run oz before generating library code" via beta-user observation |
| Lambda cold starts hurt suggest UX | Medium | Provisioned concurrency on suggest Lambda (1 instance) if P95 exceeds 1.5s |
| Aurora Serverless v2 cold start at 0 ACU | Medium | Min 0.5 ACU floor avoids this; costs $30/mo extra and worth it |
| Version resolution edge cases (monorepos, pre-releases) | Medium | Start strict (exact match only); broaden based on real failures |
| MCP-style competitors copy the approach | Medium | Moat is crawler quality and library coverage, not architecture; invest in those continuously |
| `gpt-4o-mini` rerank costs balloon at scale | Medium | Gating + caching cuts ~60%; downgrade to pure pgvector if cost exceeds budget |
| Index request spam | Low | Rate-limit per user; require login; flag bot-like patterns in dashboard |
| Hardlink failures on Windows or networked filesystems | Low | Fallback to file copies; detect and warn in `oz doctor` |
| Telemetry policy generates user backlash | Low-Med | Loud disclosure at login; one-flag opt-out; never log query content; publish telemetry schema publicly |

---

## 14. Open questions

1. Should `oz pull` accept multiple libraries in one call (`oz pull next stripe prisma`)? Likely yes, but defer to user testing.
2. How should `oz` handle a `package.json` change after init? Auto-detect and warn, or require explicit `oz sync`?
3. Should `_symbols/` files cross-reference via wiki-style links (`[[OtherSymbol]]`) or relative Markdown links? Markdown is more agent-grep-friendly.
4. Long-term: should Oz host a discoverable web catalog of indexed libraries? Out of scope for v1 but useful for SEO and developer trust.
5. Pricing model? v1 is free. Likely future: free tier + paid for private/internal docs hosting + paid for org analytics.

---

## 15. Out of scope (explicit)

- An MCP server. Rejected; product is built around its absence.
- Local FUSE mounts. Rejected for storage cost reasons.
- Background daemons or watchers.
- A web search interface for end users.
- Editor extensions, plugins, or proprietary integrations beyond writing skills into existing config files.
- Multi-tenancy for private documentation in v1.
- Non-English suggest queries.
- Documentation for languages without strong type-extraction tooling (limits seed library set to TS/JS/Python/Go/Rust).
- Multi-region AWS deployment.

---

## 16. Launch criteria

Oz ships public beta when **all** of the following are true:

1. 15+ seed libraries are indexed with passing quality review.
2. `oz install` works on Claude Code, Cursor, Codex, Cline, and Continue.
3. End-to-end loop verified manually on 10 representative tasks (e.g., "add Stripe webhooks to Express app," "set up Prisma migrations," "implement Next.js middleware auth").
4. CLI distributed via Homebrew, npm, `curl | sh`, and GitHub Releases on all target platforms.
5. Admin dashboard operational; index request queue functional.
6. Telemetry pipeline operational; opt-out tested.
7. Auth flow tested across all three target platforms.
8. AWS Budgets alert configured at $200/mo threshold.
9. Status page and basic incident response documented.
10. Privacy policy and ToS published.

---

## 17. Appendix

### A. Glossary

- **Library:** A documented external package (e.g., `vercel/next.js`).
- **Pack:** A zstd-compressed bundle of one library@version, downloaded by `oz pull`.
- **Object store:** Content-addressed local cache at `~/.codo/objects/`, shared across all projects on a machine.
- **Working copy:** A project's `.codo/vendors/` directory, materialized from the object store via hardlinks.
- **Fingerprint:** SHA of the project's lockfile dependency tree, used to scope suggest queries to relevant versions.
- **Skill:** The Markdown file written into agent configs that defines Oz's contract with the agent.
- **Rerank gating:** Skipping the `gpt-4o-mini` rerank step when top pgvector scores are decisive (> 0.85), saving cost without hurting quality.

### B. The fundamental design choice, restated

Oz exists at the intersection of three architectural decisions that competitors do not jointly make:

1. **Documentation lives as files on disk, not behind an RPC.** This is what makes the agent's native tools (Read, Grep, Glob) sufficient.
2. **Local storage is cheap because it's content-addressed and globally deduplicated.** This is what makes "files on disk" not actually expensive per developer.
3. **The agent learns one new behavior, not one new tool.** This is what makes the integration zero-overhead in the agent's context window.
4. **Cloud-side search returns coordinates, not content.** `oz search` returns local file paths, never docs. The agent reads those files itself. This preserves the "files on disk" invariant even when semantic ranking is server-side.

Every other decision in this PRD follows from those four.

### C. Cost decisions, restated

The product runs at ~$190/mo on AWS at beta scale because:

1. **Serverless everything that's bursty** (Lambda API, Aurora Serverless v2, on-demand DynamoDB). Beta traffic is too low to justify always-on compute.
2. **No NAT, no CloudFront, no Cognito.** Each was a $25–35/mo line item replaceable with simpler primitives at this scale.
3. **S3 Intelligent-Tiering and immutable cache headers** push storage and bandwidth costs near zero for read-heavy, immutable content.
4. **Rerank gating + 7-day cache** cuts the largest variable line item (OpenAI rerank) by ~60% without measurable quality loss.

---

**End of PRD.**