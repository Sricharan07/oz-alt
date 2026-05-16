# redirect

**Kind:** expected
**Signature:** `redirect`
**Source:** https://nextjs.org/docs/app/api-reference/functions/next-response

## Example

```markdown
```js filename="app/api/route.js" switcher
import { NextResponse } from 'next/server'

export async function GET(request) {
  return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
}
```

## `redirect()`

Produce a response that redirects to a [URL](https://developer.mozilla.org/docs/Web/API/URL).

```ts
import { NextResponse } from 'next/server'

return NextResponse.redirect(new URL('/new', request.url))
```
```
