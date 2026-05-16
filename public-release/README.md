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
oz login --api-url https://zt994ghexl.execute-api.us-east-1.amazonaws.com/
```

## Use

```bash
oz pull facebook/react@19
oz search "useEffect cleanup dependencies" facebook/react
```

