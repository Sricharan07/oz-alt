# cacheTag

**Kind:** heading
**Signature:** `cacheTag`
**Source:** https://nextjs.org/docs/app/getting-started/revalidating

## Example

```markdown
expire: 86400, // 1 day until expired
})
```

> **Good to know:** A cache is considered "short-lived" when it uses the `seconds` profile, `revalidate: 0`, or `expire` under 5 minutes. Short-lived caches are automatically excluded from prerenders and become dynamic holes instead. See [Prerendering behavior](/docs/app/api-reference/functions/cacheLife#prerendering-behavior) for details.

See the [`cacheLife` API reference](/docs/app/api-reference/functions/cacheLife) for all profiles and custom configuration options.

## `cacheTag`

[`cacheTag`](/docs/app/api-reference/functions/cacheTag) lets you tag cached data so it can be invalidated on-demand. Use it inside a [`use cache`](/docs/app/api-reference/directives/use-cache) scope:

```tsx filename="app/lib/data.ts" switcher
import { cacheTag } from 'next/cache'

export async function getProducts() {
  'use cache'
```
