# Relations

**Source:** https://www.prisma.io/docs/orm/prisma-schema/data-model/relations

Relations | Prisma Documentation

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

Data ModelRelations
Relations
Copy MarkdownOpen

A relation is a connection between two models in the Prisma schema. This page explains how you can define one-to-one, one-to-many and many-to-many relations in Prisma
A relation is a connection between two models in the Prisma schema. For example, there is a one-to-many relation between User and Post because one user can have many blog posts:

model User {
  id    Int    @id @default(autoincrement())
  posts Post[]
}

model Post {
  id       Int  @id @default(autoincrement())
  author   User @relation(fields: [authorId], references: [id])
  authorId Int  // Foreign key connecting Post to User
  title    String
}

At a Prisma ORM level, the User / Post relation consists of:

Relation fields (author and posts): Define connections at Prisma ORM level, do not exist in the database

Relation scalar field (authorId): The foreign key that exists in the database

Relations in the database

Relational databases

In SQL, you use a foreign key to create a relation between two tables:

A foreign key column (authorId) in Post references the primary key (id) in User

author     User        @relation(fields: [authorId], references: [id])

Relations in the Prisma schema represent relationships that exist between tables in the database.

MongoDB

MongoDB uses a normalized data model design where documents reference each other by ID:

// User document
{ &quot;_id&quot;: { &quot;$oid&quot;: &quot;60d5922d00581b8f0062e3a8&quot; }, &quot;name&quot;: &quot;Ella&quot; }

// Post documents referencing the user
{ &quot;_id&quot;: &quot;...&quot;, &quot;title&quot;: &quot;How to make sushi&quot;, &quot;authorId&quot;: { &quot;$oid&quot;: &quot;60d5922d00581b8f0062e3a8&quot; } }

If using ObjectId, add @db.ObjectId to both the model ID and relation scalar field:

model Post {
  id       String @id @default(auto()) @map(&quot;_id&quot;) @db.ObjectId
  author   User   @relation(fields: [authorId], references: [id])
  authorId String @db.ObjectId
}

Relations in Prisma Client

Create records with nested relations

const userAndPosts = await prisma.user.create({
  data: {
    posts: {
      create: [{ title: &quot;Prisma Day 2020&quot; }, { title: &quot;How to write a Prisma schema&quot; }],
    },
  },
});

Retrieve records with related data

const getAuthor = await prisma.user.findUnique({
  where: { id: &quot;20&quot; },
  include: { posts: true },
});

Connect existing records

await prisma.user.update({
  where: { id: 20 },
  data: {
    posts: { connect: { id: 4 } },
  },
});

Types of relations

There are three different types (or cardinalities) of relations in Prisma ORM:

One-to-one (also called 1-1 relations)

One-to-many (also called 1-n relations)

Many-to-many (also called m-n relations)

The following Prisma schema includes every type of relation:

one-to-one: User ↔ Profile

one-to-many: User ↔ Post

many-to-many: Post ↔ Category

Relational databases
MongoDB

model User {
  id      Int      @id @default(autoincrement())
  posts   Post[]
  profile Profile?
}

model Profile {
  id     Int  @id @default(autoincrement())
  user   User @relation(fields: [userId], references: [id])
  userId Int  @unique // relation scalar field (used in the `@relation` attribute above)
}

model Post {
  id         Int        @id @default(autoincrement())
  author     User       @relation(fields: [authorId], references: [id])
  authorId   Int // relation scalar field  (used in the `@relation` attribute above)
  categories Category[]
}

model Category {
  id    Int    @id @default(autoincrement())
  posts Post[]
}

This schema is the same as the example data model but has all scalar fields removed (except for the required relation scalar fields) so you can focus on the relation fields.

This example uses implicit many-to-many relations. These relations do not require the @relation attribute unless you need to disambiguate relations.

Notice that the syntax is slightly different between relational databases and MongoDB - particularly for many-to-many relations.

For relational databases, the following entity relationship diagram represents the database that corresponds to the sample Prisma schema:

For MongoDB, Prisma ORM uses a normalized data model design, which means that documents reference each other by ID in a similar way to relational databases. See the MongoDB section for more details.

Implicit and explicit many-to-many relations

Many-to-many relations in relational databases can be modelled in two ways:

explicit many-to-many relations, where the relation table is represented as an explicit model in your Prisma schema

implicit many-to-many relations, where Prisma ORM manages the relation table and it does not appear in the Prisma schema.

Implicit many-to-many relations require both models to have a single @id. Be aware of the following:

You cannot use a multi-field ID

You cannot use a @unique in place of an @id

To use either of these features, you must set up an explicit many-to-many instead.

The implicit many-to-many relation still manifests in a relation table in the underlying database. However, Prisma ORM manages this relation table.

If you use an implicit many-to-many relation instead of an explicit one, it makes the Prisma Client API simpler (because, for example, you have one fewer level of nesting inside of nested writes).

If you&#x27;re not using Prisma Migrate but obtain your data model from introspection, you can still make use of implicit many-to-many relations by following Prisma ORM&#x27;s conventions for relation tables.

Relation fields

Relation fields are fields on a Prisma model whose type is another model (not a scalar type). Every relation needs exactly two relation fields, one on each model.

model User {
  id    Int    @id @default(autoincrement())
  posts Post[] // relation field
}

model Post {
  id       Int    @id @default(autoincrement())
  author   User   @relation(fields: [authorId], references: [id]) // annotated relation field
  authorId Int    // relation scalar field (foreign key)
}

Key concepts:

posts and author are relation fields (exist at Prisma ORM level only)

authorId is the relation scalar field (exists in the database as foreign key)

Annotated relation fields

Relations annotated with @relation attribute (one-to-one, one-to-many, and many-to-many for MongoDB) represent the side that stores the foreign key:

author     User    @relation(fields: [authorId], references: [id])
authorId   Int     // relation scalar field

Naming convention: Relation scalar fields typically use the pattern fieldName + Id (e.g., author → authorId).

The @relation attribute

The @relation attribute is required when:

Defining one-to-one or one-to-many relations

Disambiguating multiple relations between the same models

Defining self-relations

Defining many-to-many relations for MongoDB

Implicit many-to-many relations in relational databases do not require @relation.

Disambiguating relations

When you have two relations between the same models, use the name argument in @relation to disambiguate:

model User {
  id           Int     @id @default(autoincrement())
  writtenPosts Post[]  @relation(&quot;WrittenPosts&quot;)
  pinnedPost   Post?   @relation(&quot;PinnedPost&quot;)
}

model Post {
  id         Int     @id @default(autoincrement())
  author     User    @relation(&quot;WrittenPosts&quot;, fields: [authorId], references: [id])
  authorId   Int
  pinnedBy   User?   @relation(&quot;PinnedPost&quot;, fields: [pinnedById], references: [id])
  pinnedById Int?    @unique
}

The name must be the same on both sides of the relation.

Edit on GitHub
Models

Learn about the concepts for building your data model with Prisma: Models, scalar types, enums, attributes, functions, IDs, default values and more
One-to-one relations

How to define and work with one-to-one relations in Prisma.

On this page

Relations in the databaseRelational databasesMongoDBRelations in Prisma ClientCreate records with nested relationsRetrieve records with related dataConnect existing recordsTypes of relationsImplicit and explicit many-to-many relationsRelation fieldsAnnotated relation fieldsThe @relation attributeDisambiguating relations
