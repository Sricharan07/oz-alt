# Overview of Prisma Migrate

**Source:** https://www.prisma.io/docs/orm/prisma-migrate

Prisma Migrate: Database, Schema, SQL Migration Tool | Prisma Documentation

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

Overview of Prisma Migrate
Copy MarkdownOpen

Learn everything you need to know about Prisma Migrate
Prisma Migrate enables you to:

Keep your database schema in sync with your Prisma schema as it evolves

Maintain existing data in your database

Prisma Migrate generates a history of .sql migration files, and plays a role in both development and production.

Prisma Migrate can be considered a hybrid database schema migration tool, meaning it has both of declarative and imperative elements:

Declarative: The data model is described in a declarative way in the Prisma schema. Prisma Migrate generates SQL migration files from that data model.

Imperative: All generated SQL migration files are fully customizable. Prisma Migrate hence provides the flexibility of an imperative migration tool by enabling you to modify what and how migrations are executed (and allows you to run custom SQL to e.g. make use of native database feature, perform data migrations, ...).

If you are prototyping, consider using the db push command - see Schema prototyping with db push for examples.

See the Prisma Migrate reference for detailed information about the Prisma Migrate CLI commands.

Does not apply for MongoDBInstead of migrate dev and related commands, use db push for MongoDB.

Edit on GitHub
SafeQL & Prisma Client

Learn how to use SafeQL and Prisma Client extensions to work around features not natively supported by Prisma, such as PostGIS
Getting started with Prisma Migrate

Learn how to migrate your schema in a development environment using Prisma Migrate
