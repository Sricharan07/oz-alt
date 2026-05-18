# Oz

Oz is a CLI that pulls version-pinned documentation packs for coding agents.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/Sricharan07/oz/main/scripts/install-release.sh | sh
```

Or with npm:

```bash
npm install -g @hiringbae/oz
```

## Connect

```bash
oz setup
```

## Use

```bash
oz search "useEffect cleanup dependencies" facebook/react
oz pull facebook/react@19
oz context "useEffect cleanup dependencies" facebook/react --max-tokens 1200
oz prune facebook/react
```

Browse indexed packs at https://tryoz.dev/libraries.

## MCP

Oz also ships a path-first MCP server:

```bash
oz mcp
```

The MCP tools return local file paths and line numbers by default, so agents still use normal read/search tools against `.codo/vendors`.

## GitHub Actions

Repositories can install and pre-pull docs in CI with the bundled `setup-oz` action. See `docs/GITHUB_ACTION.md`.
