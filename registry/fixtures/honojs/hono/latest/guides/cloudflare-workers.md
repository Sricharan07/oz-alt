# Cloudflare Workers ​

**Source:** https://hono.dev/getting-started/cloudflare-workers

Cloudflare Workers - Hono

    Skip to contentMenuReturn to top

Cloudflare Workers ​
Cloudflare Workers is a JavaScript edge runtime on Cloudflare CDN.
You can develop the application locally and publish it with a few commands using Wrangler. Wrangler includes transcompiler, so we can write the code with TypeScript.
Let’s make your first application for Cloudflare Workers with Hono.
1. Setup ​
A starter for Cloudflare Workers is available. Start your project with &quot;create-hono&quot; command. Select cloudflare-workers template for this example.
npmyarnpnpmbundeno
shnpm create hono@latest my-app
shyarn create hono my-app
shpnpm create hono my-app
shbun create hono@latest my-app
shdeno init --npm hono my-app

Move to my-app and install the dependencies.
npmyarnpnpmbun
shcd my-app
npm i
shcd my-app
yarn
shcd my-app
pnpm i
shcd my-app
bun i

2. Hello World ​
Edit src/index.ts like below.
tsimport { Hono } from &#39;hono&#39;
const app = new Hono()

app.get(&#39;/&#39;, (c) => c.text(&#39;Hello Cloudflare Workers!&#39;))

export default app
3. Run ​
Run the development server locally. Then, access http://localhost:8787 in your web browser.
npmyarnpnpmbun
shnpm run dev
shyarn dev
shpnpm dev
shbun run dev

Change port number ​
If you need to change the port number you can follow the instructions here to update wrangler.toml / wrangler.json / wrangler.jsonc files: Wrangler Configuration
Or, you can follow the instructions here to set CLI options: Wrangler CLI
4. Deploy ​
If you have a Cloudflare account, you can deploy to Cloudflare. In package.json, $npm_execpath needs to be changed to your package manager of choice.
npmyarnpnpmbun
shnpm run deploy
shyarn deploy
shpnpm run deploy
shbun run deploy

That&#39;s all!
Using Hono with other event handlers ​
You can integrate Hono with other event handlers (such as scheduled) in Module Worker mode.
To do this, export app.fetch as the module&#39;s fetch handler, and then implement other handlers as needed:
tsconst app = new Hono()

export default {
  fetch: app.fetch,
  scheduled: async (batch, env) => {},
}
Serve static files ​
If you want to serve static files, you can use the Static Assets feature of Cloudflare Workers. Specify the directory for the files in wrangler.toml:
tomlassets = { directory = &quot;public&quot; }
Then create the public directory and place the files there. For instance, ./public/static/hello.txt will be served as /static/hello.txt.
.
├── package.json
├── public
│   ├── favicon.ico
│   └── static
│       └── hello.txt
├── src
│   └── index.ts
└── wrangler.toml
Types ​
You have to install @cloudflare/workers-types if you want to have workers types.
npmyarnpnpmbun
shnpm i --save-dev @cloudflare/workers-types
shyarn add -D @cloudflare/workers-types
shpnpm add -D @cloudflare/workers-types
shbun add --dev @cloudflare/workers-types

Testing ​
For testing, we recommend using @cloudflare/vitest-pool-workers. Refer to examples for setting it up.
If there is the application below.
tsimport { Hono } from &#39;hono&#39;

const app = new Hono()
app.get(&#39;/&#39;, (c) => c.text(&#39;Please test me!&#39;))
We can test if it returns &quot;200 OK&quot; Response with this code.
tsdescribe(&#39;Test the application&#39;, () => {
  it(&#39;Should return 200 response&#39;, async () => {
    const res = await app.request(&#39;http://localhost/&#39;)
    expect(res.status).toBe(200)
  })
})
Bindings ​
In the Cloudflare Workers, we can bind the environment values, KV namespace, R2 bucket, or Durable Object. You can access them in c.env. It will have the types if you pass the &quot;type definition&quot; for the bindings to the Hono as generics.
tstype Bindings = {
  MY_BUCKET: R2Bucket
  USERNAME: string
  PASSWORD: string
}

const app = new Hono<{ Bindings: Bindings }>()

// Access to environment values
app.put(&#39;/upload/:key&#39;, async (c, next) => {
  const key = c.req.param(&#39;key&#39;)
  await c.env.MY_BUCKET.put(key, c.req.body)
  return c.text(`Put ${key} successfully!`)
})
Using Variables in Middleware ​
This is the only case for Module Worker mode. If you want to use Variables or Secret Variables in Middleware, for example, &quot;username&quot; or &quot;password&quot; in Basic Authentication Middleware, you need to write like the following.
tsimport { basicAuth } from &#39;hono/basic-auth&#39;

type Bindings = {
  USERNAME: string
  PASSWORD: string
}

const app = new Hono<{ Bindings: Bindings }>()

//...

app.use(&#39;/auth/*&#39;, async (c, next) => {
  const auth = basicAuth({
    username: c.env.USERNAME,
    password: c.env.PASSWORD,
  })
  return auth(c, next)
})
The same is applied to Bearer Authentication Middleware, JWT Authentication, or others.
Deploy from GitHub Actions ​
Before deploying code to Cloudflare via CI, you need a Cloudflare token. You can manage it from User API Tokens.
If it&#39;s a newly created token, select the Edit Cloudflare Workers template. If you already have another token, make sure the token has the corresponding permissions. (Note: token permissions are not shared between Cloudflare Pages and Cloudflare Workers).
then go to your GitHub repository settings dashboard: Settings->Secrets and variables->Actions->Repository secrets, and add a new secret with the name CLOUDFLARE_API_TOKEN.
then create .github/workflows/deploy.yml in your Hono project root folder, paste the following code:
ymlname: Deploy

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    name: Deploy
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
then edit wrangler.toml, and add this code after compatibility_date line.
tomlmain = &quot;src/index.ts&quot;
minify = true
Everything is ready! Now push the code and enjoy it.
Load env when local development ​
To configure the environment variables for local development, create a .dev.vars file or a .env file in the root directory of the project. These files should be formatted using the dotenv syntax. For example:
SECRET_KEY=value
API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
For more about this section you can find in the Cloudflare documentation: https://developers.cloudflare.com/workers/wrangler/configuration/#secrets
Then we use the c.env.* to get the environment variables in our code.
INFO
By default, process.env is not available in Cloudflare Workers, so it is recommended to get environment variables from c.env. If you want to use it, you need to enable nodejs_compat_populate_process_env flag. You can also import env from cloudflare:workers. For details, please see How to access env on Cloudflare docs

tstype Bindings = {
  SECRET_KEY: string
}

const app = new Hono<{ Bindings: Bindings }>()

app.get(&#39;/env&#39;, (c) => {
  const SECRET_KEY = c.env.SECRET_KEY
  return c.text(SECRET_KEY)
})
Before you deploy your project to Cloudflare, remember to set the environment variable/secrets in the Cloudflare Workers project&#39;s configuration.
For more about this section you can find in the Cloudflare documentation: https://developers.cloudflare.com/workers/configuration/environment-variables/#add-environment-variables-via-the-dashboard
