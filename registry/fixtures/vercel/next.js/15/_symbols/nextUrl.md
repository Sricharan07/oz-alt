# nextUrl

**Kind:** heading
**Signature:** `nextUrl`
**Source:** https://nextjs.org/docs/app/api-reference/functions/next-request

## Example

```markdown
### `clear()`

Remove all cookies from the request.

```ts
request.cookies.clear()
```

## `nextUrl`

Extends the native [`URL`](https://developer.mozilla.org/docs/Web/API/URL) API with additional convenience methods, including Next.js specific properties.

```ts
// Given a request to /home, pathname is /home
request.nextUrl.pathname
// Given a request to /home?name=lee, searchParams is { 'name': 'lee' }
request.nextUrl.searchParams
```
