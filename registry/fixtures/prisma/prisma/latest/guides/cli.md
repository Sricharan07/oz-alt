# CLI Overview

**Source:** https://www.prisma.io/docs/cli

Prisma CLI Reference | Commands for ORM, Migrate & Database | Prisma Documentation

CLI

Introduction
CLI OverviewStandalone commands
initgeneratevalidateformatstudiodebugversionMigrate commands
migratedevresetdeploystatusresolvediffDev commands
devlsrmstartstopDB commands
dbpullpushseedexecuteConsole commands
platformstatus

CLI Overview
Copy MarkdownOpen

The Prisma CLI is the command-line interface for Prisma ORM. Use it to initialize projects, generate Prisma Client, manage databases, run migrations, and more
The Prisma CLI provides commands for:

Project setup: Initialize new Prisma projects

Code generation: Generate Prisma Client and other artifacts

Database management: Pull schemas, push changes, seed data

Migrations: Create, apply, and manage database migrations

Development tools: Local database servers, schema validation, formatting

Installation

The Prisma CLI is available as an npm package. Install it as a development dependency:

npm
pnpm
yarn
bun

npm install prisma --save-dev

Usage

prisma [command]

Commands

CommandDescriptioninitSet up Prisma for your appdevStart a local Prisma Postgres server for developmentgenerateGenerate artifacts (e.g. Prisma Client)dbManage your database schema and lifecyclemigrateMigrate your databasestudioBrowse your data with Prisma StudiovalidateValidate your Prisma schemaformatFormat your Prisma schemaversionDisplay Prisma version infodebugDisplay Prisma debug info

Global flags

These flags are available for all commands:

FlagDescription--help, -hShow help information for a command--preview-featureRun Preview Prisma commands

Using a HTTP proxy

Prisma CLI supports custom HTTP proxies. This is useful when behind a corporate firewall.

Set one of these environment variables:

HTTP_PROXY or http_proxy: Proxy URL for HTTP traffic (e.g., http://localhost:8080)

HTTPS_PROXY or https_proxy: Proxy URL for HTTPS traffic (e.g., https://localhost:8080)

Edit on GitHub
init

Set up a new Prisma project in the current directory

On this page

InstallationUsageCommandsGlobal flagsUsing a HTTP proxy
