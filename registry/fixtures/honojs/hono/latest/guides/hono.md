# Hono ​

**Source:** https://hono.dev/docs/

Hono - Web framework built on Web Standards

    Skip to contentMenuReturn to top

Hono ​
Hono - means flame🔥 in Japanese - is a small, simple, and ultrafast web framework built on Web Standards. It works on any JavaScript runtime: Cloudflare Workers, Fastly Compute, Deno, Bun, Vercel, Netlify, AWS Lambda, Lambda@Edge, and Node.js.
Fast, but not only fast.
tsimport { Hono

 } from &#39;hono&#39;
const app

 = new Hono

()

app

.get

(&#39;/&#39;, (c

) => c

.text

(&#39;Hono!&#39;))

export default app

Quick Start ​
Just run this:
npmyarnpnpmbundeno
shnpm create hono@latest
shyarn create hono
shpnpm create hono@latest
shbun create hono@latest
shdeno init --npm hono@latest

Features ​
Ultrafast 🚀 - The router RegExpRouter is really fast. Not using linear loops. Fast.
Lightweight 🪶 - The hono/tiny preset is under 14kB. Hono has zero dependencies and uses only the Web Standards.
Multi-runtime 🌍 - Works on Cloudflare Workers, Fastly Compute, Deno, Bun, AWS Lambda, or Node.js. The same code runs on all platforms.
Batteries Included 🔋 - Hono has built-in middleware, custom middleware, third-party middleware, and helpers. Batteries included.
Delightful DX 😃 - Super clean APIs. First-class TypeScript support. Now, we&#39;ve got &quot;Types&quot;.
Use-cases ​
Hono is a simple web application framework similar to Express, without a frontend. But it runs on CDN Edges and allows you to construct larger applications when combined with middleware. Here are some examples of use-cases.
Building Web APIs
Proxy of backend servers
Front of CDN
Edge application
Base server for a library
Full-stack application
Who is using Hono? ​
ProjectPlatformWhat for?cdnjsCloudflare WorkersA free and open-source CDN service. Hono is used for the API server.Cloudflare D1Cloudflare WorkersServerless SQL databases. Hono is used for the internal API server.Cloudflare Workers KVCloudflare WorkersServerless key-value database. Hono is used for the internal API server.BaseAILocal AI ServerServerless AI agent pipes with memory. An open-source agentic AI framework for web. API server with Hono.UnkeyCloudflare WorkersAn open-source API authentication and authorization. Hono is used for the API server.OpenStatusBunAn open-source website & API monitoring platform. Hono is used for the API server.Deno BenchmarksDenoA secure TypeScript runtime built on V8. Hono is used for benchmarking.ClerkCloudflare WorkersAn open-source User Management Platform. Hono is used for the API server.And the following.
Drivly - Cloudflare Workers
repeat.dev - Cloudflare Workers
Do you want to see more? See Who is using Hono in production?.
Hono in 1 minute ​
A demonstration to create an application for Cloudflare Workers with Hono.

Ultrafast ​
Hono is the fastest, compared to other routers for Cloudflare Workers.
Hono x 402,820 ops/sec ±4.78% (80 runs sampled)
itty-router x 212,598 ops/sec ±3.11% (87 runs sampled)
sunder x 297,036 ops/sec ±4.76% (77 runs sampled)
worktop x 197,345 ops/sec ±2.40% (88 runs sampled)
Fastest is Hono
✨  Done in 28.06s.
See more benchmarks.
Lightweight ​
Hono is so small. With the hono/tiny preset, its size is under 14KB when minified. There are many middleware and adapters, but they are bundled only when used. For context, the size of Express is 572KB.
$ npx wrangler dev --minify ./src/index.ts
 ⛅️ wrangler 2.20.0
--------------------
⬣ Listening at http://0.0.0.0:8787
- http://127.0.0.1:8787
- http://192.168.128.165:8787
Total Upload: 11.47 KiB / gzip: 4.34 KiB
Multiple routers ​
Hono has multiple routers.
RegExpRouter is the fastest router in the JavaScript world. It matches the route using a single large Regex created before dispatch. With SmartRouter, it supports all route patterns.
LinearRouter registers the routes very quickly, so it&#39;s suitable for an environment that initializes applications every time. PatternRouter simply adds and matches the pattern, making it small.
See more information about routes.
Web Standards ​
Thanks to the use of the Web Standards, Hono works on a lot of platforms.
Cloudflare Workers
Cloudflare Pages
Fastly Compute
Deno
Bun
Vercel
AWS Lambda
Lambda@Edge
Others
And by using a Node.js adapter, Hono works on Node.js.
See more information about Web Standards.
Middleware & Helpers ​
Hono has many middleware and helpers. This makes &quot;Write Less, do more&quot; a reality.
Out of the box, Hono provides middleware and helpers for:
Basic Authentication
Bearer Authentication
Body Limit
Cache
Compress
Context Storage
Cookie
CORS
ETag
html
JSX
JWT Authentication
Logger
Language
Pretty JSON
Secure Headers
SSG
Streaming
GraphQL Server
Firebase Authentication
Sentry
Others!
For example, adding ETag and request logging only takes a few lines of code with Hono:
tsimport { Hono } from &#39;hono&#39;
import { etag } from &#39;hono/etag&#39;
import { logger } from &#39;hono/logger&#39;

const app = new Hono()
app.use(etag(), logger())
See more information about Middleware.
Developer Experience ​
Hono provides a delightful &quot;Developer Experience&quot;.
Easy access to Request/Response thanks to the Context object. Moreover, Hono is written in TypeScript. Hono has &quot;Types&quot;.
For example, the path parameters will be literal types.

And, the Validator and Hono Client hc enable the RPC mode. In RPC mode, you can use your favorite validator such as Zod and easily share server-side API specs with the client and build type-safe applications.
See Hono Stacks.
