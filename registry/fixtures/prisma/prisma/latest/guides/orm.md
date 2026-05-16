# Prisma ORM

**Source:** https://www.prisma.io/docs/orm

What is Prisma ORM? (Overview) | Prisma Documentation

ORM

Latest

Introduction
Prisma ORMCore Concepts
Data modelingSupported databases
API patternsPrisma Schema
Overview
Data Model
What is introspection?PostgreSQL extensionsPrisma Client
Prisma ClientSetup and Configuration
Queries
Client Extensions
Deployment
Observability and Logging
Debugging and Troubleshooting
Special Fields and Types
Testing
Type Safety
Using Raw SQL
Prisma Migrate
Overview of Prisma MigrateGetting started with Prisma MigrateUnderstanding MigrationsMigration historiesAbout the shadow databaseLimitations and known issuesWorkflows
Reference
Prisma CLI referencePrisma Client APISchema APIConfig APIConnection URLsEnvironment VariablesDatabase FeaturesSupported databasesSystem requirementsError ReferencePrisma Error ReferencePrisma Client & Prisma schemaPrisma CLI Preview featuresMore
Best practicesORM releases and maturity levelsComparisons
Dev environment
Troubleshooting

Prisma ORM
Copy MarkdownOpen

Prisma ORM is a next-generation Node.js and TypeScript ORM that provides type-safe database access, migrations, and a visual data editor.
Prisma ORM is open-source and consists of:

Prisma Client: Auto-generated, type-safe ORM interface

Prisma Migrate: Database migration system

Prisma Studio: GUI to view and edit your data

Prisma Client works with any Node.js or TypeScript backend, whether you&#x27;re deploying to traditional servers, serverless functions, or microservices.

Why Prisma ORM

Traditional database tools force a tradeoff between productivity and control. Raw SQL gives full control but is error-prone and lacks type safety. Traditional ORMs improve productivity but abstract too much, leading to the object-relational impedance mismatch and performance pitfalls like the n+1 problem.

Prisma takes a different approach:

Type-safe queries validated at compile time with full autocompletion

Thinking in objects without the complexity of mapping relational data

Plain JavaScript objects returned from queries, not complex model instances

Single source of truth in the Prisma schema for database and application models

Healthy constraints that prevent common pitfalls and anti-patterns

When to use Prisma

Prisma is a good fit if you:

Build server-side applications (REST, GraphQL, gRPC, serverless)

Value type safety and developer experience

Work in a team and want a clear, declarative schema

Need migrations, querying, and data modeling in one toolkit

Consider alternatives if you:

Need full control over every SQL query (use raw SQL drivers)

Want a no-code backend (use a BaaS like Supabase or Firebase)

Need an auto-generated CRUD GraphQL API (use Hasura or PostGraphile)

How it works

1. Define your schema

The Prisma schema defines your data models and database connection:

datasource db {
  provider = &quot;postgresql&quot;
}

generator client {
  provider = &quot;prisma-client&quot;
  output   = &quot;./generated&quot;
}

model User {
  id    Int     @id @default(autoincrement())
  email String  @unique
  name  String?
  posts Post[]
}

model Post {
  id        Int     @id @default(autoincrement())
  title     String
  published Boolean @default(false)
  author    User?   @relation(fields: [authorId], references: [id])
  authorId  Int?
}

2. Configure your connection

Create a prisma.config.ts file in your project root:

prisma.config.ts

import &quot;dotenv/config&quot;;
import { defineConfig, env } from &quot;prisma/config&quot;;

export default defineConfig({
  schema: &quot;prisma/schema.prisma&quot;,
  migrations: {
    path: &quot;prisma/migrations&quot;,
  },
  datasource: {
    url: env(&quot;DATABASE_URL&quot;),
  },
});

3. Run migrations

Use Prisma Migrate to create and apply migrations:

npm
pnpm
yarn
bun

npx prisma migrate dev

Or introspect an existing database:

npm
pnpm
yarn
bun

npx prisma db pull

4. Query with Prisma Client

Generate and use the type-safe client:

npm
pnpm
yarn
bun

npm install @prisma/client
npx prisma generate

import { PrismaClient } from &quot;./generated/client&quot;;
// Import the driver adapter for your specific database (example uses PostgreSQL)
import { PrismaPg } from &quot;@prisma/adapter-pg&quot;;

// Initialize the adapter according to your driver&#x27;s requirements
const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });

// Pass the adapter instance to PrismaClient
const prisma = new PrismaClient({ adapter });

// Find all users with their posts
const users = await prisma.user.findMany({
  include: { posts: true },
});

// Create a user with a post
const user = await prisma.user.create({
  data: {
    email: &quot;alice@prisma.io&quot;,
    posts: {
      create: { title: &quot;Hello World&quot; },
    },
  },
});

Prisma 7 Connection Requirements
Starting with Prisma 7, providing a driver adapter is mandatory for direct database connections. This change standardizes database connectivity across Node.js, Serverless, and Edge environments.
If you use Prisma Accelerate, instantiate Prisma Client with accelerateUrl and the Accelerate extension instead of a driver adapter.
To ensure compatibility:

Install an adapter: Use the specific package for your database (e.g., @prisma/adapter-pg, @prisma/adapter-mysql, etc.).

Enable ESM: Your package.json must include &quot;type&quot;: &quot;module&quot;.

For detailed instructions, see the V7 Upgrade Guide.

Next steps

Prisma schema - Learn the schema language

Prisma Client - Explore the query API

Edit on GitHub
Data modeling

Learn how data modeling with Prisma differs from data modeling with SQL or ORMs. Prisma uses a declarative data modeling language to describe a database schema

On this page

Why Prisma ORMWhen to use PrismaHow it works1. Define your schema2. Configure your connection3. Run migrations4. Query with Prisma ClientPrisma 7 Connection RequirementsNext steps
