# Middleware

Middleware runs before a request is completed and can redirect, rewrite, modify headers, or inspect cookies before rendering.

## JWT Cookie Auth

Read a JWT from the incoming `NextRequest` cookies, verify it with your auth library, and redirect unauthenticated users.

```ts
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const jwt = request.cookies.get('session')?.value

  if (!jwt) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}
```

## Matcher

Use `config.matcher` to restrict middleware to specific routes.

```ts
export const config = {
  matcher: ['/dashboard/:path*'],
}
```

