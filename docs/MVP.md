# MVP Build Slice

The PRD describes the full beta system. This implementation starts with a narrower tracer bullet:

- Rust workspace and CLI binary.
- Project initialization and dependency fingerprinting.
- Local content-addressed object store at `~/.codo/objects`.
- Pack-backed `oz pull <vendor>/<library>@<version>`, with fixture fallback.
- Catalog-backed `oz suggest`.
- Local Markdown search over `.codo/vendors`, with auto-pull from indexed fixtures when needed.
- `AGENTS.md` skill installation.
- Scrapling-based crawler package that can populate `registry/fixtures`.
- Local HTTP API for `/suggest`, `/search`, `/refs`, `/pack`, `/index-request`, and `/telemetry`.

## Deferred

- Hosted registry API.
- Device auth and telemetry.
- Hosted S3 pack transport and signed manifests.
- Semantic embeddings and LLM reranking.
- Multi-agent config detection.
- Admin dashboard and crawler queue.

## Next Build Step

Replace local registry services with hosted services:

1. Upload `.ozpack` files to S3.
2. Point `oz pull` at `/pack/...` when `api_url` is configured.
3. Add pgvector/OpenAI semantic ranking behind `/suggest` and `/search`.
4. Add auth and rate limits.
5. Run quality evals against at least 10 agent tasks.
