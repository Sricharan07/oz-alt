# fetchCache

**Kind:** constant
**Signature:** `* **`'auto'`** (default): The default option to cache as much as possible without preventing any components from opting into dynamic behavior.`
**Source:** https://nextjs.org/docs/llms-full.txt

## Example

```text
* **`'auto'`** (default): The default option to cache as much as possible without preventing any components from opting into dynamic behavior.
* **`'force-dynamic'`**: Force [dynamic rendering](/docs/app/glossary#dynamic-rendering), which will result in routes being rendered for each user at request time. This option is equivalent to:
  * Setting the option of every `fetch()` request in a layout or page to `{ cache: 'no-store', next: { revalidate: 0 } }`.
  * Setting the segment config to `export const fetchCache = 'force-no-store'`
* **`'error'`**: Force prerendering and cache the data of a layout or page by causing an error if any components use Request-time APIs or uncached data. This option is equivalent to:
  * `getStaticProps()` in the `pages` directory.
  * Setting the option of every `fetch()` request in a layout or page to `{ cache: 'force-cache' }`.
  * Setting the segment config to `fetchCache = 'only-cache'`.
* **`'force-static'`**: Force prerendering and cache the data of a layout or page by forcing [`cookies`](/docs/app/api-reference/functions/cookies), [`headers()`](/docs/app/api-reference/functions/headers) and [`useSearchParams()`](/docs/app/api-reference/functions/use-search-params) to return empty values. It is possible to [`revalidate`](#route-segment-config-revalidate), [`revalidatePath`](/docs/app/api-reference/functions/revalidatePath), or [`revalidateTag`](/docs/app/api-reference/functions/revalidateTag), in pages or layouts rendered with `force-static`.

#### `fetchCache`

This is an advanced option that should only be used if you specifically need to override the default behavior.

By default, Next.js **will cache** any `fetch()` requests that are reachable **before** any Request-time APIs are used and **will not cache** `fetch` requests that are discovered **after** Request-time APIs are used.

`fetchCache` allows you to override the default `cache` option of all `fetch` requests in a layout or page.
```
