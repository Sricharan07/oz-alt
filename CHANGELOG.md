# Changelog

All notable Oz product and release changes are tracked here.

## Unreleased

## 0.1.7

- Add compact agent-oriented search output with bounded line ranges via `oz search --compact-json`.
- Return line ranges through `oz search` text output and the path-first MCP `oz_search` tool.
- Update generated Oz agent instructions to prefer compact semantic search plus narrow local file reads.
- Add a 30-case benchmark harness for Next.js, React, and FastAPI with filesystem read-window token accounting.
- Fix local pull behavior for macOS dataless `.ozpack` files by falling back to materialized fixture sources.

## 0.1.6

- Make `oz setup` the one-command agent onboarding path by always writing the default registry API URL, even when login is skipped.
- Add automatic Oz MCP configuration for detected Codex, Cursor, and project-scoped MCP clients.
- Refresh installed Oz agent instructions to prefer Oz before Context7, web search, model memory, or other doc tools, with fallback only when Oz has no indexed docs.
- Document path-first MCP tools (`oz_search`, `oz_pull`, `oz_status`) in setup and generated skills.

## 0.1.5

- Add monorepo-aware `oz init` dependency discovery.
- Add path-first `oz mcp` server for agent clients that speak MCP without returning large snippet blobs by default.
- Add public library browser and pack detail pages.
- Add a reusable GitHub Action for installing Oz and pre-pulling documentation packs in CI.
- Harden search-first UX around suggested libraries and auto-pull behavior.

## 0.1.4

- Ship production retrieval hardening, version-aware search, reranking, observability, and release artifact verification.
