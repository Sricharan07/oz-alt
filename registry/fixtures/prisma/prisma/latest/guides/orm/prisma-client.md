# Prisma Client

**Source:** https://www.prisma.io/docs/orm/prisma-client

Prisma Client overview | Prisma Documentation

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

Prisma Client
Copy MarkdownOpen

Prisma Client is Prisma ORM&#x27;s generated, type-safe query builder for Node.js, Bun, and Deno applications.
Prisma Client is Prisma ORM&#x27;s generated query builder. It is tailored to your schema, fully typed, and designed to make common database work feel like ordinary application code.

What Prisma Client gives you

Typed query methods based on your models

Autocomplete for filters, relations, ordering, and nested writes

Predictable plain JavaScript objects as query results

A single client API that works across PostgreSQL, MySQL, SQLite, MongoDB, and more

Quick start

1. Define a generator in your schema

schema.prisma

generator client {
  provider = &quot;prisma-client&quot;
  output   = &quot;./generated&quot;
}

2. Install Prisma Client

npm
pnpm
yarn
bun

npm install @prisma/client

3. Generate the client

npm
pnpm
yarn
bun

npx prisma generate

If you want more detail on this step, see Generating Prisma Client.

4. Import and use the generated client

import { PrismaClient } from &quot;./generated/client&quot;;

const prisma = new PrismaClient();

const users = await prisma.user.findMany();

Common tasks

Set up and configure Prisma Client

Generate Prisma Client

Run CRUD queries

Work with relations

Use transactions

Use raw SQL when you need it

Related reference docs

Prisma Client API reference

Prisma schema generators

Prisma CLI generate command

Edit on GitHub
PostgreSQL extensions

How to install and manage PostgreSQL extensions with Prisma ORM using customized migrations, and how to use them in Prisma Client
Introduction to Prisma Client

Learn how to set up and configure Prisma Client in your project

On this page

What Prisma Client gives youQuick start1. Define a generator in your schema2. Install Prisma Client3. Generate the client4. Import and use the generated clientCommon tasksRelated reference docs
