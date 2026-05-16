# cacheLife

**Kind:** heading
**Signature:** `cacheLife`
**Source:** https://nextjs.org/docs/app/getting-started/revalidating

## Example

```markdown
version: 16.2.6
---
# Revalidating

> This page covers revalidation with [Cache Components](/docs/app/api-reference/config/next-config-js/cacheComponents), enabled by setting [`cacheComponents: true`](/docs/app/api-reference/config/next-config-js/cacheComponents) in your `next.config.ts` file. If you're not using Cache Components, see the [Caching and Revalidating (Previous Model)](/docs/app/guides/caching-without-cache-components) guide.

Revalidation is the process of updating cached data. It lets you keep serving fast, cached responses while ensuring content stays fresh. There are two strategies:

* **Time-based revalidation**: Automatically refresh cached data after a set duration using [`cacheLife`](#cachelife).
* **On-demand revalidation**: Manually invalidate cached data after a mutation using [`revalidateTag`](#revalidatetag), [`updateTag`](#updatetag), or [`revalidatePath`](#revalidatepath).

## `cacheLife`

[`cacheLife`](/docs/app/api-reference/functions/cacheLife) controls how long cached data remains valid. Use it inside a [`use cache`](/docs/app/api-reference/directives/use-cache) scope to set the cache lifetime.

```tsx filename="app/lib/data.ts" highlight={1,4,5}
import { cacheLife } from 'next/cache'
```
