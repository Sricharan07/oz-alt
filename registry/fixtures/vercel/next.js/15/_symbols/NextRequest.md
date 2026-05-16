# NextRequest

**Kind:** class
**Signature:** `class NextRequest extends Request`
**Source:** https://nextjs.org/docs/app/api-reference/functions/next-request

## Description

`NextRequest` extends the Web `Request` API with Next.js-specific helpers used in Middleware, Proxy, and Route Handlers.

## Cookies

`request.cookies.get(name)` returns the matching request cookie when present.

```ts
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  return token
}
```

## URL

`request.nextUrl` exposes the parsed URL with Next.js routing metadata.

## See also

- [NextResponse](./NextResponse.md)
- [Middleware](../guides/middleware.md)

