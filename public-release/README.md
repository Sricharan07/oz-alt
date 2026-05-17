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
oz login --api-url https://api.tryoz.dev
```

## Use

```bash
oz pull facebook/react@19
oz search "useEffect cleanup dependencies" facebook/react
oz context "useEffect cleanup dependencies" facebook/react --max-tokens 1200
```
