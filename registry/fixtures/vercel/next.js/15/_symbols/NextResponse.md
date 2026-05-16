# NextResponse

**Kind:** class
**Signature:** `class NextResponse extends Response`
**Source:** https://nextjs.org/docs/app/api-reference/functions/next-response

## Description

`NextResponse` extends the Web `Response` API with convenience helpers for Middleware, Proxy, and Route Handlers.

## Redirect

Use `NextResponse.redirect(url)` to return an HTTP redirect from middleware.

```ts
import { NextResponse, type NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const loginUrl = new URL('/login', request.url)
  return NextResponse.redirect(loginUrl)
}
```

## Cookies

`response.cookies.set(name, value)` writes a response cookie.

## See also

- [NextRequest](./NextRequest.md)
- [Middleware](../guides/middleware.md)

