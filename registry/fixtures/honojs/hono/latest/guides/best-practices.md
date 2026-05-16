# Best Practices ​

**Source:** https://hono.dev/docs/guides/best-practices

Best Practices - Hono

    Skip to contentMenuReturn to top

Best Practices ​
Hono is very flexible. You can write your app as you like. However, there are best practices that are better to follow.
Don&#39;t make &quot;Controllers&quot; when possible ​
When possible, you should not create &quot;Ruby on Rails-like Controllers&quot;.
ts// 🙁
// A RoR-like Controller
const booksList = (c: Context) => {
  return c.json(&#39;list books&#39;)
}

app.get(&#39;/books&#39;, booksList)
The issue is related to types. For example, the path parameter cannot be inferred in the Controller without writing complex generics.
ts// 🙁
// A RoR-like Controller
const bookPermalink = (c: Context) => {
  const id = c.req.param(&#39;id&#39;) // Can&#39;t infer the path param
  return c.json(`get ${id}`)
}
Therefore, you don&#39;t need to create RoR-like controllers and should write handlers directly after path definitions.
ts// 😃
app.get(&#39;/books/:id&#39;, (c) => {
  const id = c.req.param(&#39;id&#39;) // Can infer the path param
  return c.json(`get ${id}`)
})
factory.createHandlers() in hono/factory ​
If you still want to create a RoR-like Controller, use factory.createHandlers() in hono/factory. If you use this, type inference will work correctly.
tsimport { createFactory } from &#39;hono/factory&#39;
import { logger } from &#39;hono/logger&#39;

// ...

// 😃
const factory = createFactory()

const middleware = factory.createMiddleware(async (c, next) => {
  c.set(&#39;foo&#39;, &#39;bar&#39;)
  await next()
})

const handlers = factory.createHandlers(logger(), middleware, (c) => {
  return c.json(c.var.foo)
})

app.get(&#39;/api&#39;, ...handlers)
Building a larger application ​
Use app.route() to build a larger application without creating &quot;Ruby on Rails-like Controllers&quot;.
If your application has /authors and /books endpoints and you wish to separate files from index.ts, create authors.ts and books.ts.
ts// authors.ts
import { Hono } from &#39;hono&#39;

const app = new Hono()

app.get(&#39;/&#39;, (c) => c.json(&#39;list authors&#39;))
app.post(&#39;/&#39;, (c) => c.json(&#39;create an author&#39;, 201))
app.get(&#39;/:id&#39;, (c) => c.json(`get ${c.req.param(&#39;id&#39;)}`))

export default app
ts// books.ts
import { Hono } from &#39;hono&#39;

const app = new Hono()

app.get(&#39;/&#39;, (c) => c.json(&#39;list books&#39;))
app.post(&#39;/&#39;, (c) => c.json(&#39;create a book&#39;, 201))
app.get(&#39;/:id&#39;, (c) => c.json(`get ${c.req.param(&#39;id&#39;)}`))

export default app
Then, import them and mount on the paths /authors and /books with app.route().
ts// index.ts
import { Hono } from &#39;hono&#39;
import authors from &#39;./authors&#39;
import books from &#39;./books&#39;

const app = new Hono()

// 😃
app.route(&#39;/authors&#39;, authors)
app.route(&#39;/books&#39;, books)

export default app
If you want to use RPC features ​
The code above works well for normal use cases. However, if you want to use the RPC feature, you can get the correct type by chaining as follows.
ts// authors.ts
import { Hono } from &#39;hono&#39;

const app = new Hono()
  .get(&#39;/&#39;, (c) => c.json(&#39;list authors&#39;))
  .post(&#39;/&#39;, (c) => c.json(&#39;create an author&#39;, 201))
  .get(&#39;/:id&#39;, (c) => c.json(`get ${c.req.param(&#39;id&#39;)}`))

export default app
export type AppType = typeof app
If you pass the type of the app to hc, it will get the correct type.
tsimport type { AppType } from &#39;./authors&#39;
import { hc } from &#39;hono/client&#39;

// 😃
const client = hc<AppType>(&#39;http://localhost&#39;) // Typed correctly
For more detailed information, please see the RPC page.
HEAD Request Best Practices ​
Understanding Hono&#39;s HEAD Handling ​
Hono automatically handles HEAD requests by converting them to GET requests and stripping the response body. This behavior is built into the framework&#39;s dispatch layer and happens before route matching occurs.
✅ Do: Use GET Routes for HEAD Requests ​
typescript// GOOD: This GET route automatically handles HEAD requests
app.get(&#39;/api/users&#39;, async (c) => {
  const users = await getUsers()
  c.header(&#39;X-Total-Count&#39;, users.length.toString())
  return c.json(users)
})

// HEAD /api/users will return:
// - Same headers as GET (including X-Total-Count)
// - Status 200
// - No body (null)
✅ Do: Use Middleware for HEAD-Specific Logic ​
typescript// GOOD: Use middleware when HEAD needs different behavior
app.use(&#39;/api/resource&#39;, async (c, next) => {
  await next()

  // Add HEAD-specific headers after the handler
  if (c.req.method === &#39;HEAD&#39;) {
    c.header(&#39;X-HEAD-Processed&#39;, &#39;true&#39;)
    // Don&#39;t compute expensive body content for HEAD
    c.res = new Response(null, c.res)
  }
})
❌ Don&#39;t: Try to Create Dedicated HEAD Handlers ​
typescript// BAD: This won&#39;t work as expected
app.head(&#39;/api/users&#39;, (c) => {
  // This handler will NEVER be called
  c.header(&#39;X-Custom&#39;, &#39;value&#39;)
  return c.text(&#39;ignored&#39;)
})

// BAD: Using on() also won&#39;t work
app.on(&#39;HEAD&#39;, &#39;/api/users&#39;, (c) => {
  // Still converted to GET before route matching
})
Performance Considerations ​
Avoid expensive operations in GET handlers if you expect many HEAD requests: Use middleware to detect HEAD and skip body generation
Cache headers work identically: HEAD responses respect the same caching rules as GET
Middleware compatibility: Most middleware works with HEAD, but body-processing middleware (like compression) automatically skips HEAD requests
Testing HEAD Requests ​
typescript// Always test both GET and HEAD responses
it(&#39;handles HEAD requests correctly&#39;, async () => {
  const getRes = await app.request(&#39;/api/users&#39;)
  const headRes = await app.request(&#39;/api/users&#39;, { method: &#39;HEAD&#39; })

  expect(headRes.status).toBe(getRes.status)
  expect(headRes.headers.get(&#39;X-Total-Count&#39;)).toBe(
    getRes.headers.get(&#39;X-Total-Count&#39;)
  )
  expect(headRes.body).toBe(null)
})
Notes ​
The automatic HEAD conversion ensures consistent headers between GET and HEAD responses
This behavior is consistent across all Hono runtimes (Cloudflare Workers, Deno, Bun, Node.js)
If you need completely different logic for HEAD vs GET, consider using different endpoints rather than trying to override the framework&#39;s HEAD handling
