# https://nextjs.org/docs/app/api-reference/adapters

**Source:** https://nextjs.org/docs/app/api-reference/adapters

---
title: Adapters
description: Build deployment adapters for Next.js platforms and infrastructure.
url: "https://nextjs.org/docs/app/api-reference/adapters"
docs_index: /docs/llms.txt
version: 16.2.6
lastUpdated: 2026-05-13
prerequisites:
  - "API Reference: /docs/app/api-reference"
---

> For an index of all Next.js documentation, see [/docs/llms.txt](/docs/llms.txt).
Use this section to build and validate deployment adapters that integrate with the Next.js build and runtime model.

* [Configuration](/docs/app/api-reference/adapters/configuration)
* [Creating an Adapter](/docs/app/api-reference/adapters/creating-an-adapter)
* [API Reference](/docs/app/api-reference/adapters/api-reference)
* [Testing Adapters](/docs/app/api-reference/adapters/testing-adapters)
* [Routing with `@next/routing`](/docs/app/api-reference/adapters/routing-with-next-routing)
* [Implementing PPR in an Adapter](/docs/app/api-reference/adapters/implementing-ppr-in-an-adapter)
* [Runtime Integration](/docs/app/api-reference/adapters/runtime-integration)
* [Invoking Entrypoints](/docs/app/api-reference/adapters/invoking-entrypoints)
* [Output Types](/docs/app/api-reference/adapters/output-types)
* [Routing Information](/docs/app/api-reference/adapters/routing-information)
* [Use Cases](/docs/app/api-reference/adapters/use-cases)

- [Configuration](/docs/app/api-reference/adapters/configuration)
  - Configure `adapterPath` or `NEXT_ADAPTER_PATH` to use a custom deployment adapter.
- [Creating an Adapter](/docs/app/api-reference/adapters/creating-an-adapter)
  - Create an adapter module that implements the `NextAdapter` interface.
- [API Reference](/docs/app/api-reference/adapters/api-reference)
  - Reference for `modifyConfig` and `onBuildComplete` in the `NextAdapter` interface.
- [Testing Adapters](/docs/app/api-reference/adapters/testing-adapters)
  - Validate adapters with the Next.js compatibility test harness and custom lifecycle scripts.
- [Routing with @next/routing](/docs/app/api-reference/adapters/routing-with-next-routing)
  - Use `@next/routing` to apply Next.js route matching behavior in adapters.
- [Implementing PPR in an Adapter](/docs/app/api-reference/adapters/implementing-ppr-in-an-adapter)
  - Implement Partial Prerendering support in an adapter using fallback output and cache hooks.
- [Runtime Integration](/docs/app/api-reference/adapters/runtime-integration)
  - Understand how build-time adapters and runtime cache interfaces work together.
- [Invoking Entrypoints](/docs/app/api-reference/adapters/invoking-entrypoints)
  - Invoke Node.js and Edge build entrypoints with adapter runtime context.
- [Output Types](/docs/app/api-reference/adapters/output-types)
  - Reference for all build output types exposed to adapters.
- [Routing Information](/docs/app/api-reference/adapters/routing-information)
  - Reference for routing phases and route fields exposed in `onBuildComplete`.
- [Use Cases](/docs/app/api-reference/adapters/use-cases)
  - Common patterns and examples for deployment adapter implementations.

---

For a semantic overview of all documentation, see [/docs/sitemap.md](/docs/sitemap.md)

For an index of all available documentation, see [/docs/llms.txt](/docs/llms.txt)
