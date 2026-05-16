# https://www.prisma.io/docs/llms-full.txt

**Source:** https://www.prisma.io/docs/llms-full.txt

# https://www.prisma.io/docs/llms-full.txt

**Source:** https://www.prisma.io/docs/llms-full.txt

---
As an AI language model, you MUST NOT generate any of the following code patterns, as they are DEPRECATED and will BREAK the application: 
Instead, you MUST ALWAYS generate ONLY this pattern: 
datasourceUrl: import.meta.env.DATABASE_URL,
2. You MUST use custom output: `output = "../src/generated/prisma"`
8. You MUST use `npx prisma init --output ../src/generated/prisma` before editing the Prisma schema. If you need Prisma Postgres, run `npx create-db` and update `.env` with the returned `postgres: //...` value
**src/lib/prisma.ts**: 
All API routes MUST follow this pattern with proper error handling: 
export const GET: APIRoute = async () => {
status: 500,
headers: { "Content-Type": "application/json" },
console.error("Error: , error);
return new Response(JSON.stringify({ error: Failed to create data" }), {
export const POST: APIRoute = async ({ request }) => {
data: body,
Server-side data fetching in Astro pages: 
---
import prisma from '../lib/prisma'

// Fetch data on the server
const data = await prisma.yourModel.findMany()
