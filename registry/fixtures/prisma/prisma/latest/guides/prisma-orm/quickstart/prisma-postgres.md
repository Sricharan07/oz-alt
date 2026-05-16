# Prisma Postgres

**Source:** https://www.prisma.io/docs/prisma-orm/quickstart/prisma-postgres

Quickstart: Prisma ORM with Prisma Postgres (5 min) | Prisma Documentation

Getting Started

Getting Started
Introduction to PrismaChoose a setup pathPrisma ORM
QuickstartPrisma PostgresSQLitePostgreSQLMySQLSQL ServerPlanetScaleCockroachDBMongoDB

Add to Existing Project
Prisma Postgres
Quickstart
Import from PostgreSQLImport from MySQLFrom the CLI

Quickstart
Prisma Postgres
Copy MarkdownOpen

Create a new TypeScript project from scratch by connecting Prisma ORM to Prisma Postgres and generating a Prisma Client for database access
Prisma Postgres is a fully managed PostgreSQL database that scales to zero and integrates smoothly with both Prisma ORM and Prisma Studio. In this guide, you will learn how to set up a new TypeScript project from scratch, connect it to Prisma Postgres using Prisma ORM, and generate a Prisma Client for easy, type-safe access to your database.

Prerequisites

1. Create a new project

mkdir hello-prisma
cd hello-prisma

Initialize a TypeScript project:

npm
pnpm
yarn
bun

npm init
npm install typescript tsx @types/node --save-dev
npx tsc --init

2. Install required dependencies

Install the packages needed for this quickstart:

npm
pnpm
yarn
bun

npm install prisma @types/pg --save-dev
npm install @prisma/client @prisma/adapter-pg pg dotenv

Here&#x27;s what each package does:

prisma - The Prisma CLI for running commands like prisma init, prisma migrate, and prisma generate

@prisma/client - The Prisma Client library for querying your database

@prisma/adapter-pg - The node-postgres driver adapter that connects Prisma Client to your database

pg - The node-postgres database driver

@types/pg - TypeScript type definitions for node-postgres

dotenv - Loads environment variables from your .env file

3. Configure ESM support

Update tsconfig.json for ESM compatibility:

tsconfig.json

{
  &quot;compilerOptions&quot;: {
    &quot;module&quot;: &quot;ESNext&quot;,
    &quot;moduleResolution&quot;: &quot;bundler&quot;,
    &quot;target&quot;: &quot;ES2023&quot;,
    &quot;strict&quot;: true,
    &quot;esModuleInterop&quot;: true,
    &quot;ignoreDeprecations&quot;: &quot;6.0&quot;
  }
}

Update package.json to enable ESM:

package.json

{
  &quot;type&quot;: &quot;module&quot;
}

4. Initialize Prisma ORM

You can now invoke the Prisma CLI by prefixing it with npx:

npm
pnpm
yarn
bun

npx prisma

Next, set up your Prisma ORM project by creating your Prisma Schema file with the following command:

npm
pnpm
yarn
bun

npx prisma init --output ../generated/prisma

prisma init creates the Prisma scaffolding and a local DATABASE_URL.

This command does a few things:

Creates a prisma/ directory with a schema.prisma file containing your database connection and schema models

Creates a .env file in the root directory for environment variables

Creates a prisma.config.ts file for Prisma configuration

The generated prisma.config.ts file looks like this:

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

The generated schema uses the ESM-first prisma-client generator with a custom output path:

prisma/schema.prisma

generator client {
  provider = &quot;prisma-client&quot;
  output   = &quot;../generated/prisma&quot;
}

datasource db {
  provider = &quot;postgresql&quot;
}

Create a Prisma Postgres database and replace the generated DATABASE_URL in your .env file with the postgres://... connection string from the CLI output:

npm
pnpm
yarn
bun

npx create-db

5. Define your data model

Open prisma/schema.prisma and add the following models:

prisma/schema.prisma

generator client {
  provider = &quot;prisma-client&quot;
  output   = &quot;../generated/prisma&quot;
}

datasource db {
  provider = &quot;postgresql&quot;
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
  content   String?
  published Boolean @default(false)
  author    User    @relation(fields: [authorId], references: [id])
  authorId  Int
}

6. Create and apply your first migration

Create your first migration to set up the database tables:

npm
pnpm
yarn
bun

npx prisma migrate dev --name init

This command creates the database tables based on your schema.

Now run the following command to generate the Prisma Client:

npm
pnpm
yarn
bun

npx prisma generate

7. Instantiate Prisma Client

Now that you have all the dependencies installed, you can instantiate Prisma Client. You need to pass an instance of the Prisma ORM driver adapter to the PrismaClient constructor:

lib/prisma.ts

import &quot;dotenv/config&quot;;
import { PrismaPg } from &quot;@prisma/adapter-pg&quot;;
import { PrismaClient } from &quot;../generated/prisma/client&quot;;

const connectionString = `${process.env.DATABASE_URL}`;

const adapter = new PrismaPg({ connectionString });
const prisma = new PrismaClient({ adapter });

export { prisma };

If you need to query your database via HTTP from an edge runtime (Cloudflare Workers, Vercel Edge Functions, etc.), use the Prisma Postgres serverless driver.

8. Write your first query

Create a script.ts file to test your setup:

script.ts

import { prisma } from &quot;./lib/prisma&quot;;

async function main() {
  // Create a new user with a post
  const user = await prisma.user.create({
    data: {
      name: &quot;Alice&quot;,
      email: &quot;alice@prisma.io&quot;,
      posts: {
        create: {
          title: &quot;Hello World&quot;,
          content: &quot;This is my first post!&quot;,
          published: true,
        },
      },
    },
    include: {
      posts: true,
    },
  });
  console.log(&quot;Created user:&quot;, user);

  // Fetch all users with their posts
  const allUsers = await prisma.user.findMany({
    include: {
      posts: true,
    },
  });
  console.log(&quot;All users:&quot;, JSON.stringify(allUsers, null, 2));
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });

Run the script:

npm
pnpm
yarn
bun

npx tsx script.ts

You should see the created user and all users printed to the console!

9. Explore your data with Prisma Studio

Prisma Studio is a visual editor for your database. Launch it with:

npx prisma studio

Next steps

You&#x27;ve successfully set up Prisma ORM. Here&#x27;s what you can explore next:

Learn more about Prisma Client: Explore the Prisma Client API for advanced querying, filtering, and relations

Database migrations: Learn about Prisma Migrate for evolving your database schema

Performance optimization: Discover query optimization techniques

Build a full application: Check out our framework guides to integrate Prisma ORM with Next.js, Express, and more

Join the community: Connect with other developers on Discord

More info

Prisma Postgres documentation

Prisma Config reference

Database connection management

Edit on GitHub
Choose a setup path

Choose the fastest path to start using Prisma ORM or Prisma Postgres in a new or existing project.
SQLite

Create a new TypeScript project from scratch by connecting Prisma ORM to SQLite and generating a Prisma Client for database access

On this page

Prerequisites1. Create a new project2. Install required dependencies3. Configure ESM support4. Initialize Prisma ORM5. Define your data model6. Create and apply your first migration7. Instantiate Prisma Client8. Write your first query9. Explore your data with Prisma StudioNext stepsMore info
