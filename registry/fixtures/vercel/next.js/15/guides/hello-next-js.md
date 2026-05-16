# Hello, Next.js!

**Source:** https://nextjs.org/docs/llms-full.txt

# Next.js Documentation

> Index of all docs: /docs/llms.txt

@doc-version: >=v16.2.6
@doc-version-notes: Some features may have extended or refined behavior in minor or patch releases
@router: App Router
@router-note: Unless otherwise noted in each section, these documents apply to the App Router

---
title: Getting Started
description: Learn how to create full-stack web applications with the Next.js App Router.
url: "https://nextjs.org/docs/app/getting-started"
version: 16.2.6
---

# Getting Started

Welcome to the Next.js documentation!

This **Getting Started** section will help you create your first Next.js app and learn the core features you'll use in every project.

## Pre-requisite knowledge

Our documentation assumes some familiarity with web development. Before getting started, it'll help if you're comfortable with:

* HTML
* CSS
* JavaScript
* React

If you're new to React or need a refresher, we recommend starting with our [React Foundations course](/learn/react-foundations), and the [Next.js Foundations course](/learn/dashboard-app) that has you building an application as you learn.

## Next Steps

 - [Installation](/docs/app/getting-started/installation)
 - [Project Structure](/docs/app/getting-started/project-structure)
 - [Layouts and Pages](/docs/app/getting-started/layouts-and-pages)
 - [Linking and Navigating](/docs/app/getting-started/linking-and-navigating)
 - [Server and Client Components](/docs/app/getting-started/server-and-client-components)
 - [Fetching Data](/docs/app/getting-started/fetching-data)
 - [Mutating Data](/docs/app/getting-started/mutating-data)
 - [Caching](/docs/app/getting-started/caching)
 - [Revalidating](/docs/app/getting-started/revalidating)
 - [Error Handling](/docs/app/getting-started/error-handling)
 - [CSS](/docs/app/getting-started/css)
 - [Image Optimization](/docs/app/getting-started/images)
 - [Font Optimization](/docs/app/getting-started/fonts)
 - [Metadata and OG images](/docs/app/getting-started/metadata-and-og-images)
 - [Route Handlers](/docs/app/getting-started/route-handlers)
 - [Proxy](/docs/app/getting-started/proxy)
 - [Deploying](/docs/app/getting-started/deploying)
 - [Upgrading](/docs/app/getting-started/upgrading)

---
title: Installation
description: "Learn how to create a new Next.js application with the `create-next-app` CLI, and set up TypeScript, ESLint, and Module Path Aliases."
url: "https://nextjs.org/docs/app/getting-started/installation"
version: 16.2.6
---

# Installation

Create a new Next.js app and run it locally.

## Quick start

1. Create a new Next.js app named `my-app`
2. `cd my-app` and start the dev server.
3. Visit `http://localhost:3000`.

```bash package="pnpm"
pnpm create next-app@latest my-app --yes
cd my-app
pnpm dev
```

```bash package="npm"
npx create-next-app@latest my-app --yes
cd my-app
npm run dev
```

```bash package="yarn"
yarn create next-app@latest my-app --yes
cd my-app
yarn dev
```

```bash package="bun"
bun create next-app@latest my-app --yes
cd my-app
bun dev
```

* `--yes` skips prompts using saved preferences or defaults. The default setup enables TypeScript, Tailwind CSS, ESLint, App Router, and Turbopack, with import alias `@/*`, and includes `AGENTS.md` (with a `CLAUDE.md` that references it) to guide coding agents to write up-to-date Next.js code.

## System requirements

Before you begin, make sure your development environment meets the following requirements:

* Minimum Node.js version: [20.9](https://nodejs.org/)
* Operating systems: macOS, Windows (including WSL), and Linux.

## Supported browsers

Next.js supports modern browsers with zero configuration.

* Chrome 111+
* Edge 111+
* Firefox 111+
* Safari 16.4+

Learn more about [browser support](/docs/architecture/supported-browsers), including how to configure polyfills and target specific browsers.

## Create with the CLI

The quickest way to create a new Next.js app is using [`create-next-app`](/docs/app/api-reference/cli/create-next-app), which sets up everything automatically for you. To create a project, run:

```bash package="pnpm"
pnpm create next-app
```

```bash package="npm"
npx create-next-app@latest
```

```bash package="yarn"
yarn create next-app
```

```bash package="bun"
bun create next-app
```

On installation, you'll see the following prompts:

```txt filename="Terminal"
What is your project named? my-app
Would you like to use the recommended Next.js defaults?
    Yes, use recommended defaults - TypeScript, ESLint, Tailwind CSS, App Router, AGENTS.md
    No, reuse previous settings
    No, customize settings - Choose your own preferences
```

If you choose to `customize settings`, you'll see the following prompts:

```txt filename="Terminal"
Would you like to use TypeScript? No / Yes
Which linter would you like to use? ESLint / Biome / None
Would you like to use React Compiler? No / Yes
Would you like to use Tailwind CSS? No / Yes
Would you like your code inside a `src/` directory? No / Yes
Would you like to use App Router? (recommended) No / Yes
Would you like to customize the import alias (`@/*` by default)? No / Yes
What import alias would you like configured? @/*
Would you like to include AGENTS.md to guide coding agents to write up-to-date Next.js code? No / Yes
```

After the prompts, [`create-next-app`](/docs/app/api-reference/cli/create-next-app) will create a folder with your project name and install the required dependencies.

## Manual installation

To manually create a new Next.js app, install the required packages:

```bash package="pnpm"
pnpm i next@latest react@latest react-dom@latest
```

```bash package="npm"
npm i next@latest react@latest react-dom@latest
```

```bash package="yarn"
yarn add next@latest react@latest react-dom@latest
```

```bash package="bun"
bun add next@latest react@latest react-dom@latest
```

> **Good to know**:
>
> * The `App Router` uses [React canary releases](https://react.dev/blog/2023/05/03/react-canaries) built-in, which include all the stable React 19 changes, as well as newer features being validated in frameworks, but you should still declare react and react-dom in package.json for tooling and ecosystem compatibility.
> * The `Pages Router` uses the React version from your `package.json`.

Then, add the following scripts to your `package.json` file:

```json filename="package.json"
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint",
    "lint:fix": "eslint --fix"
  }
}
```

These scripts refer to the different stages of developing an application:

* `next dev`: Starts the development server using Turbopack (default bundler).
* `next build`: Builds the application for production.
* `next start`: Starts the production server.
* `eslint`: Runs ESLint.

Turbopack is now the default bundler. To use Webpack run `next dev --webpack` or `next build --webpack`. See the [Turbopack docs](/docs/app/api-reference/turbopack) for configuration details.

### Create the `app` directory

Next.js uses file-system routing, which means the routes in your application are determined by how you structure your files.

Create an `app` folder. Then, inside `app`, create a `layout.tsx` file. This file is the [root layout](/docs/app/api-reference/file-conventions/layout#root-layout). It's required and must contain the `` and `` tags.

```tsx filename="app/layout.tsx" switcher
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (

      {children}

  )
}
```

```jsx filename="app/layout.js" switcher
export default function RootLayout({ children }) {
  return (

      {children}

  )
}
```

Create a home page `app/page.tsx` with some initial content:

```tsx filename="app/page.tsx" switcher
export default function Page() {
  return Hello, Next.js!

}
```

```jsx filename="app/page.js" switcher
export default function Page() {
  return Hello, Next.js!

}
```

Both `layout.tsx` and `page.tsx` will be rendered when the user visits the root of your application (`/`).

![App Folder Structure](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/app-getting-started.png)

> **Good to know**:
>
> * If you forget to create the root layout, Next.js will automatically create this file when running the development server with `next dev`.
> * You can optionally use a [`src` folder](/docs/app/api-reference/file-conventions/src-folder) in the root of your project to separate your application's code from configuration files.

### Create the `public` folder (optional)

Create a [`public` folder](/docs/app/api-reference/file-conventions/public-folder) at the root of your project to store static assets such as images, fonts, etc. Files inside `public` can then be referenced by your code starting from the base URL (`/`).

You can then reference these assets using the root path (`/`). For example, `public/profile.png` can be referenced as `/profile.png`:

```tsx filename="app/page.tsx" highlight={4} switcher
import Image from 'next/image'

export default function Page() {
  return
}
```

```jsx filename="app/page.js" highlight={4} switcher
import Image from 'next/image'

export default function Page() {
  return
}
```

## Run the development server

1. Run `npm run dev` to start the development server.
2. Visit `http://localhost:3000` to view your application.
3. Edit the `app/page.tsx` file and save it to see the updated result in your browser.

## Set up TypeScript

> Minimum TypeScript version: `v5.1.0`

Next.js comes with built-in TypeScript support. To add TypeScript to your project, rename a file to `.ts` / `.tsx` and run `next dev`. Next.js will automatically install the necessary dependencies and add a `tsconfig.json` file with the recommended config options.

### IDE Plugin

Next.js includes a custom TypeScript plugin and type checker, which VSCode and other code editors can use for advanced type-checking and auto-completion.

You can enable the plugin in VS Code by:

1. Opening the command palette (`Ctrl/⌘` + `Shift` + `P`)
2. Searching for "TypeScript: Select TypeScript Version"
3. Selecting "Use Workspace Version"

![TypeScript Command Palette](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/typescript-command-palette.png)

See the [TypeScript reference](/docs/app/api-reference/config/typescript) page for more information.

## Set up linting

Next.js supports linting with either ESLint or Biome. Choose a linter and run it directly via `package.json` scripts.

* Use **ESLint** (comprehensive rules):

```json filename="package.json"
{
  "scripts": {
    "lint": "eslint",
    "lint:fix": "eslint --fix"
  }
}
```

* Or use **Biome** (fast linter + formatter):

```json filename="package.json"
{
  "scripts": {
    "lint": "biome check",
    "format": "biome format --write"
  }
}
```

If your project previously used `next lint`, migrate your scripts to the ESLint CLI with the codemod:

```bash filename="Terminal"
npx @next/codemod@canary next-lint-to-eslint-cli .
```

If you use ESLint, create an explicit config (recommended `eslint.config.mjs`). ESLint supports both [the legacy `.eslintrc.*` and the newer `eslint.config.mjs` formats](https://eslint.org/docs/latest/use/configure/configuration-files#configuring-eslint). See the [ESLint API reference](/docs/app/api-reference/config/eslint#with-core-web-vitals) for a recommended setup.

> **Good to know**: Starting with Next.js 16, `next build` no longer runs the linter automatically. Instead, you can run your linter through NPM scripts.

See the [ESLint Plugin](/docs/app/api-reference/config/eslint) page for more information.

## Set up Absolute Imports and Module Path Aliases

Next.js has in-built support for the `"paths"` and `"baseUrl"` options of `tsconfig.json` and `jsconfig.json` files.

These options allow you to alias project directories to absolute paths, making it easier and cleaner to import modules. For example:

```jsx
// Before
import { Button } from '../../../components/button'

// After
import { Button } from '@/components/button'
```

To configure absolute imports, add the `baseUrl` configuration option to your `tsconfig.json` or `jsconfig.json` file. For example:

```json filename="tsconfig.json or jsconfig.json"
{
  "compilerOptions": {
    "baseUrl": "src/"
  }
}
```

In addition to configuring the `baseUrl` path, you can use the `"paths"` option to `"alias"` module paths.

For example, the following configuration maps `@/components/*` to `components/*`:

```json filename="tsconfig.json or jsconfig.json"
{
  "compilerOptions": {
    "baseUrl": "src/",
    "paths": {
      "@/styles/*": ["styles/*"],
      "@/components/*": ["components/*"]
    }
  }
}
```

Each of the `"paths"` are relative to the `baseUrl` location.

---
title: Project Structure
description: Learn the folder and file conventions in Next.js, and how to organize your project.
url: "https://nextjs.org/docs/app/getting-started/project-structure"
version: 16.2.6
---

# Project Structure

This page provides an overview of **all** the folder and file conventions in Next.js, and recommendations for organizing your project.

## Folder and file conventions

### Top-level folders

Top-level folders are used to organize your application's code and static assets.

![Route segments to path segments](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/top-level-folders.png)

|                                                                    |                                    |
| ------------------------------------------------------------------ | ---------------------------------- |
| [`app`](/docs/app)                                                 | App Router                         |
| [`pages`](/docs/pages/building-your-application/routing)           | Pages Router                       |
| [`public`](/docs/app/api-reference/file-conventions/public-folder) | Static assets to be served         |
| [`src`](/docs/app/api-reference/file-conventions/src-folder)       | Optional application source folder |

### Top-level files

Top-level files are used to configure your application, manage dependencies, run proxy, integrate monitoring tools, and define environment variables.

|                                                                              |                                                                                    |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **Next.js**                                                                  |                                                                                    |
| [`next.config.js`](/docs/app/api-reference/config/next-config-js)            | Configuration file for Next.js                                                     |
| [`package.json`](/docs/app/getting-started/installation#manual-installation) | Project dependencies and scripts                                                   |
| [`instrumentation.ts`](/docs/app/guides/instrumentation)                     | OpenTelemetry and Instrumentation file                                             |
| [`proxy.ts`](/docs/app/api-reference/file-conventions/proxy)                 | Next.js request proxy                                                              |
| [`.env`](/docs/app/guides/environment-variables)                             | Environment variables (should not be tracked by version control)                   |
| [`.env.local`](/docs/app/guides/environment-variables)                       | Local environment variables (should not be tracked by version control)             |
| [`.env.production`](/docs/app/guides/environment-variables)                  | Production environment variables (should not be tracked by version control)        |
| [`.env.development`](/docs/app/guides/environment-variables)                 | Development environment variables (should not be tracked by version control)       |
| [`eslint.config.mjs`](/docs/app/api-reference/config/eslint)                 | Configuration file for ESLint                                                      |
| `.gitignore`                                                                 | Git files and folders to ignore                                                    |
| [`next-env.d.ts`](/docs/app/api-reference/config/typescript#next-envdts)     | TypeScript declaration file for Next.js (should not be tracked by version control) |
| `tsconfig.json`                                                              | Configuration file for TypeScript                                                  |
| `jsconfig.json`                                                              | Configuration file for JavaScript                                                  |

### Routing Files

Add `page` to expose a route, `layout` for shared UI such as header, nav, or footer, `loading` for skeletons, `error` for error boundaries, and `route` for APIs.

|                                                                               |                     |                              |
| ----------------------------------------------------------------------------- | ------------------- | ---------------------------- |
| [`layout`](/docs/app/api-reference/file-conventions/layout)                   | `.js` `.jsx` `.tsx` | Layout                       |
| [`page`](/docs/app/api-reference/file-conventions/page)                       | `.js` `.jsx` `.tsx` | Page                         |
| [`loading`](/docs/app/api-reference/file-conventions/loading)                 | `.js` `.jsx` `.tsx` | Loading UI                   |
| [`not-found`](/docs/app/api-reference/file-conventions/not-found)             | `.js` `.jsx` `.tsx` | Not found UI                 |
| [`error`](/docs/app/api-reference/file-conventions/error)                     | `.js` `.jsx` `.tsx` | Error UI                     |
| [`global-error`](/docs/app/api-reference/file-conventions/error#global-error) | `.js` `.jsx` `.tsx` | Global error UI              |
| [`route`](/docs/app/api-reference/file-conventions/route)                     | `.js` `.ts`         | API endpoint                 |
| [`template`](/docs/app/api-reference/file-conventions/template)               | `.js` `.jsx` `.tsx` | Re-rendered layout           |
| [`default`](/docs/app/api-reference/file-conventions/default)                 | `.js` `.jsx` `.tsx` | Parallel route fallback page |

### Nested routes

Folders define URL segments. Nesting folders nests segments. Layouts at any level wrap their child segments. A route becomes public when a `page` or `route` file exists.

| Path                        | URL pattern     | Notes                         |
| --------------------------- | --------------- | ----------------------------- |
| `app/layout.tsx`            | —               | Root layout wraps all routes  |
| `app/blog/layout.tsx`       | —               | Wraps `/blog` and descendants |
| `app/page.tsx`              | `/`             | Public route                  |
| `app/blog/page.tsx`         | `/blog`         | Public route                  |
| `app/blog/authors/page.tsx` | `/blog/authors` | Public route                  |

### Dynamic routes

Parameterize segments with square brackets. Use `[segment]` for a single param, `[...segment]` for catch‑all, and `[[...segment]]` for optional catch‑all. Access values via the [`params`](/docs/app/api-reference/file-conventions/page#params-optional) prop.

| Path                            | URL pattern                                                          |
| ------------------------------- | -------------------------------------------------------------------- |
| `app/blog/[slug]/page.tsx`      | `/blog/my-first-post`                                                |
| `app/shop/[...slug]/page.tsx`   | `/shop/clothing`, `/shop/clothing/shirts`                            |
| `app/docs/[[...slug]]/page.tsx` | `/docs`, `/docs/layouts-and-pages`, `/docs/api-reference/use-router` |

### Route groups and private folders

Organize code without changing URLs with route groups [`(group)`](/docs/app/api-reference/file-conventions/route-groups#convention), and colocate non-routable files with private folders [`_folder`](#private-folders).

| Path                            | URL pattern | Notes                                     |
| ------------------------------- | ----------- | ----------------------------------------- |
| `app/(marketing)/page.tsx`      | `/`         | Group omitted from URL                    |
| `app/(shop)/cart/page.tsx`      | `/cart`     | Share layouts within `(shop)`             |
| `app/blog/_components/Post.tsx` | —           | Not routable; safe place for UI utilities |
| `app/blog/_lib/data.ts`         | —           | Not routable; safe place for utils        |

### Parallel and Intercepted Routes

These features fit specific UI patterns, such as slot-based layouts or modal routing.

Use `@slot` for named slots rendered by a parent layout. Use intercept patterns to render another route inside the current layout without changing the URL, for example, to show a details view as a modal over a list.

| Pattern (docs)                                                                              | Meaning              | Typical use case                         |
| ------------------------------------------------------------------------------------------- | -------------------- | ---------------------------------------- |
| [`@folder`](/docs/app/api-reference/file-conventions/parallel-routes#slots)                 | Named slot           | Sidebar + main content                   |
| [`(.)folder`](/docs/app/api-reference/file-conventions/intercepting-routes#convention)      | Intercept same level | Preview sibling route in a modal         |
| [`(..)folder`](/docs/app/api-reference/file-conventions/intercepting-routes#convention)     | Intercept parent     | Open a child of the parent as an overlay |
| [`(..)(..)folder`](/docs/app/api-reference/file-conventions/intercepting-routes#convention) | Intercept two levels | Deeply nested overlay                    |
| [`(...)folder`](/docs/app/api-reference/file-conventions/intercepting-routes#convention)    | Intercept from root  | Show arbitrary route in current view     |

### Metadata file conventions

#### App icons

|                                                                                                                 |                                     |                          |
| --------------------------------------------------------------------------------------------------------------- | ----------------------------------- | ------------------------ |
| [`favicon`](/docs/app/api-reference/file-conventions/metadata/app-icons#favicon)                                | `.ico`                              | Favicon file             |
| [`icon`](/docs/app/api-reference/file-conventions/metadata/app-icons#icon)                                      | `.ico` `.jpg` `.jpeg` `.png` `.svg` | App Icon file            |
| [`icon`](/docs/app/api-reference/file-conventions/metadata/app-icons#generate-icons-using-code-js-ts-tsx)       | `.js` `.ts` `.tsx`                  | Generated App Icon       |
| [`apple-icon`](/docs/app/api-reference/file-conventions/metadata/app-icons#apple-icon)                          | `.jpg` `.jpeg`, `.png`              | Apple App Icon file      |
| [`apple-icon`](/docs/app/api-reference/file-conventions/metadata/app-icons#generate-icons-using-code-js-ts-tsx) | `.js` `.ts` `.tsx`                  | Generated Apple App Icon |

#### Open Graph and Twitter images

|                                                                                                                             |                              |                            |
| --------------------------------------------------------------------------------------------------------------------------- | ---------------------------- | -------------------------- |
| [`opengraph-image`](/docs/app/api-reference/file-conventions/metadata/opengraph-image#opengraph-image)                      | `.jpg` `.jpeg` `.png` `.gif` | Open Graph image file      |
| [`opengraph-image`](/docs/app/api-reference/file-conventions/metadata/opengraph-image#generate-images-using-code-js-ts-tsx) | `.js` `.ts` `.tsx`           | Generated Open Graph image |
| [`twitter-image`](/docs/app/api-reference/file-conventions/metadata/opengraph-image#twitter-image)                          | `.jpg` `.jpeg` `.png` `.gif` | Twitter image file         |
| [`twitter-image`](/docs/app/api-reference/file-conventions/metadata/opengraph-image#generate-images-using-code-js-ts-tsx)   | `.js` `.ts` `.tsx`           | Generated Twitter image    |

#### SEO

|                                                                                                              |             |                       |
| ------------------------------------------------------------------------------------------------------------ | ----------- | --------------------- |
| [`sitemap`](/docs/app/api-reference/file-conventions/metadata/sitemap#sitemap-files-xml)                     | `.xml`      | Sitemap file          |
| [`sitemap`](/docs/app/api-reference/file-conventions/metadata/sitemap#generating-a-sitemap-using-code-js-ts) | `.js` `.ts` | Generated Sitemap     |
| [`robots`](/docs/app/api-reference/file-conventions/metadata/robots#static-robotstxt)                        | `.txt`      | Robots file           |
| [`robots`](/docs/app/api-reference/file-conventions/metadata/robots#generate-a-robots-file)                  | `.js` `.ts` | Generated Robots file |

## Organizing your project

Next.js is **unopinionated** about how you organize and colocate your project files. But it does provide several features to help you organize your project.

### Component hierarchy

The components defined in special files are rendered in a specific hierarchy:

* `layout.js`
* `template.js`
* `error.js` (React error boundary)
* `loading.js` (React suspense boundary)
* `not-found.js` (React error boundary for "not found" UI)
* `page.js` or nested `layout.js`

![Component Hierarchy for File Conventions](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/file-conventions-component-hierarchy.png)

The components are rendered recursively in nested routes, meaning the components of a route segment will be nested **inside** the components of its parent segment.

![Nested File Conventions Component Hierarchy](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/nested-file-conventions-component-hierarchy.png)

### Colocation

In the `app` directory, nested folders define route structure. Each folder represents a route segment that is mapped to a corresponding segment in a URL path.

However, even though route structure is defined through folders, a route is **not publicly accessible** until a `page.js` or `route.js` file is added to a route segment.

![A diagram showing how a route is not publicly accessible until a page.js or route.js file is added to a route segment.](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/project-organization-not-routable.png)

And, even when a route is made publicly accessible, only the **content returned** by `page.js` or `route.js` is sent to the client.

![A diagram showing how page.js and route.js files make routes publicly accessible.](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/project-organization-routable.png)

This means that **project files** can be **safely colocated** inside route segments in the `app` directory without accidentally being routable.

![A diagram showing colocated project files are not routable even when a segment contains a page.js or route.js file.](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/project-organization-colocation.png)

> **Good to know**: While you **can** colocate your project files in `app` you don't **have** to. If you prefer, you can [keep them outside the `app` directory](#store-project-files-outside-of-app).

### Private folders

Private folders can be created by prefixing a folder with an underscore: `_folderName`

This indicates the folder is a private implementation detail and should not be considered by the routing system, thereby **opting the folder and all its subfolders** out of routing.

![An example folder structure using private folders](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/project-organization-private-folders.png)

Since files in the `app` directory can be [safely colocated by default](#colocation), private folders are not required for colocation. However, they can be useful for:

* Separating UI logic from routing logic.
* Consistently organizing internal files across a project and the Next.js ecosystem.
* Sorting and grouping files in code editors.
* Avoiding potential naming conflicts with future Next.js file conventions.

> **Good to know**:
>
> * While not a framework convention, you might also consider marking files outside private folders as "private" using the same underscore pattern.
> * You can create URL segments that start with an underscore by prefixing the folder name with `%5F` (the URL-encoded form of an underscore): `%5FfolderName`.
> * If you don't use private folders, it would be helpful to know Next.js [special file conventions](/docs/app/getting-started/project-structure#routing-files) to prevent unexpected naming conflicts.

### Route groups

Route groups can be created by wrapping a folder in parenthesis: `(folderName)`

This indicates the folder is for organizational purposes and should **not be included** in the route's URL path.

![An example folder structure using route groups](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/project-organization-route-groups.png)

Route groups are useful for:

* Organizing routes by site section, intent, or team. e.g. marketing pages, admin pages, etc.
* Enabling nested layouts in the same route segment level:
  * [Creating multiple nested layouts in the same segment, including multiple root layouts](#creating-multiple-root-layouts)
  * [Adding a layout to a subset of routes in a common segment](#opting-specific-segments-into-a-layout)

### `src` folder

Next.js supports storing application code (including `app`) inside an optional [`src` folder](/docs/app/api-reference/file-conventions/src-folder). This separates application code from project configuration files which mostly live in the root of a project.

![An example folder structure with the src folder](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/project-organization-src-directory.png)

## Examples

The following section lists a very high-level overview of common strategies. The simplest takeaway is to choose a strategy that works for you and your team and be consistent across the project.

> **Good to know**: In our examples below, we're using `components` and `lib` folders as generalized placeholders, their naming has no special framework significance and your projects might use other folders like `ui`, `utils`, `hooks`, `styles`, etc.

### Store project files outside of `app`

This strategy stores all application code in shared folders in the **root of your project** and keeps the `app` directory purely for routing purposes.

![An example folder structure with project files outside of app](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/project-organization-project-root.png)

### Store project files in top-level folders inside of `app`

This strategy stores all application code in shared folders in the **root of the `app` directory**.

![An example folder structure with project files inside app](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/project-organization-app-root.png)

### Split project files by feature or route

This strategy stores globally shared application code in the root `app` directory and **splits** more specific application code into the route segments that use them.

![An example folder structure with project files split by feature or route](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/project-organization-app-root-split.png)

### Organize routes without affecting the URL path

To organize routes without affecting the URL, create a group to keep related routes together. The folders in parenthesis will be omitted from the URL (e.g. `(marketing)` or `(shop)`).

![Organizing Routes with Route Groups](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/route-group-organisation.png)

Even though routes inside `(marketing)` and `(shop)` share the same URL hierarchy, you can create a different layout for each group by adding a `layout.js` file inside their folders.

![Route Groups with Multiple Layouts](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/route-group-multiple-layouts.png)

### Opting specific segments into a layout

To opt specific routes into a layout, create a new route group (e.g. `(shop)`) and move the routes that share the same layout into the group (e.g. `account` and `cart`). The routes outside of the group will not share the layout (e.g. `checkout`).

![Route Groups with Opt-in Layouts](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/route-group-opt-in-layouts.png)

### Opting for loading skeletons on a specific route

To apply a [loading skeleton](/docs/app/api-reference/file-conventions/loading) via a `loading.js` file to a specific route, create a new route group (e.g., `/(overview)`) and then move your `loading.tsx` inside that route group.

![Folder structure showing a loading.tsx and a page.tsx inside the route group](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/route-group-loading.png)

Now, the `loading.tsx` file will only apply to your dashboard → overview page instead of all your dashboard pages without affecting the URL path structure.

### Creating multiple root layouts

To create multiple [root layouts](/docs/app/api-reference/file-conventions/layout#root-layout), remove the top-level `layout.js` file, and add a `layout.js` file inside each route group. This is useful for partitioning an application into sections that have a completely different UI or experience. The `` and `` tags need to be added to each root layout.

![Route Groups with Multiple Root Layouts](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/route-group-multiple-root-layouts.png)

In the example above, both `(marketing)` and `(shop)` have their own root layout.

---
title: Layouts and Pages
description: Learn how to create your first pages and layouts, and link between them with the Link component.
url: "https://nextjs.org/docs/app/getting-started/layouts-and-pages"
version: 16.2.6
---

# Layouts and Pages

Next.js uses **file-system based routing**, meaning you can use folders and files to define routes. This page will guide you through how to create layouts and pages, and link between them.

## Creating a page

A **page** is UI that is rendered on a specific route. To create a page, add a [`page` file](/docs/app/api-reference/file-conventions/page) inside the `app` directory and default export a React component. For example, to create an index page (`/`):

![page.js special file](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/page-special-file.png)

```tsx filename="app/page.tsx" switcher
export default function Page() {
  return Hello Next.js!

}
```

```jsx filename="app/page.js" switcher
export default function Page() {
  return Hello Next.js!

}
```

## Creating a layout

A layout is UI that is **shared** between multiple pages. On navigation, layouts preserve state, remain interactive, and do not rerender.

You can define a layout by default exporting a React component from a [`layout` file](/docs/app/api-reference/file-conventions/layout). The component should accept a `children` prop which can be a page or another [layout](#nesting-layouts).

For example, to create a layout that accepts your index page as child, add a `layout` file inside the `app` directory:

![layout.js special file](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/layout-special-file.png)

```tsx filename="app/layout.tsx" switcher
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (

        {/* Layout UI */}
        {/* Place children where you want to render a page or nested layout */}
        {children}

  )
}
```

```jsx filename="app/layout.js" switcher
export default function DashboardLayout({ children }) {
  return (

        {/* Layout UI */}
        {/* Place children where you want to render a page or nested layout */}
        {children}

  )
}
```

The layout above is called a [root layout](/docs/app/api-reference/file-conventions/layout#root-layout) because it's defined at the root of the `app` directory. The root layout is **required** and must contain `html` and `body` tags.

## Creating a nested route

A nested route is a route composed of multiple URL segments. For example, the `/blog/[slug]` route is composed of three segments:

* `/` (Root Segment)
* `blog` (Segment)
* `[slug]` (Leaf Segment)

In Next.js:

* **Folders** are used to define the route segments that map to URL segments.
* **Files** (like `page` and `layout`) are used to create UI that is shown for a segment.

To create nested routes, you can nest folders inside each other. For example, to add a route for `/blog`, create a folder called `blog` in the `app` directory. Then, to make `/blog` publicly accessible, add a `page.tsx` file:

![File hierarchy showing blog folder and a page.js file](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/blog-nested-route.png)

```tsx filename="app/blog/page.tsx" switcher
// Dummy imports
import { getPosts } from '@/lib/posts'
import { Post } from '@/ui/post'

export default async function Page() {
  const posts = await getPosts()

  return (

      {posts.map((post) => (

      ))}

  )
}
```

```jsx filename="app/blog/page.js" switcher
// Dummy imports
import { getPosts } from '@/lib/posts'
import { Post } from '@/ui/post'

export default async function Page() {
  const posts = await getPosts()

  return (

      {posts.map((post) => (

      ))}

  )
}
```

You can continue nesting folders to create nested routes. For example, to create a route for a specific blog post, create a new `[slug]` folder inside `blog` and add a `page` file:

![File hierarchy showing blog folder with a nested slug folder and a page.js file](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/blog-post-nested-route.png)

```tsx filename="app/blog/[slug]/page.tsx" switcher
function generateStaticParams() {}

export default function Page() {
  return Hello, Blog Post Page!

}
```

```jsx filename="app/blog/[slug]/page.js" switcher
function generateStaticParams() {}

export default function Page() {
  return Hello, Blog Post Page!

}
```

Wrapping a folder name in square brackets (e.g. `[slug]`) creates a [dynamic route segment](/docs/app/api-reference/file-conventions/dynamic-routes) which is used to generate multiple pages from data. e.g. blog posts, product pages, etc.

## Nesting layouts

By default, layouts in the folder hierarchy are also nested, which means they wrap child layouts via their `children` prop. You can nest layouts by adding `layout` inside specific route segments (folders).

For example, to create a layout for the `/blog` route, add a new `layout` file inside the `blog` folder.

![File hierarchy showing root layout wrapping the blog layout](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/nested-layouts.png)

```tsx filename="app/blog/layout.tsx" switcher
export default function BlogLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return {children}

}
```

```jsx filename="app/blog/layout.js" switcher
export default function BlogLayout({ children }) {
  return {children}

}
```

If you were to combine the two layouts above, the root layout (`app/layout.js`) would wrap the blog layout (`app/blog/layout.js`), which would wrap the blog (`app/blog/page.js`) and blog post page (`app/blog/[slug]/page.js`).

## Creating a dynamic segment

[Dynamic segments](/docs/app/api-reference/file-conventions/dynamic-routes) allow you to create routes that are generated from data. For example, instead of manually creating a route for each individual blog post, you can create a dynamic segment to generate the routes based on blog post data.

To create a dynamic segment, wrap the segment (folder) name in square brackets: `[segmentName]`. For example, in the `app/blog/[slug]/page.tsx` route, the `[slug]` is the dynamic segment.

```tsx filename="app/blog/[slug]/page.tsx" switcher
export default async function BlogPostPage({
  params,
}: {
  params: Promise
}) {
  const { slug } = await params
  const post = await getPost(slug)

  return (

      {post.title}

      {post.content}

  )
}
```

```jsx filename="app/blog/[slug]/page.js" switcher
export default async function BlogPostPage({ params }) {
  const { slug } = await params
  const post = await getPost(slug)

  return (

      {post.title}

      {post.content}

  )
}
```

Learn more about [Dynamic Segments](/docs/app/api-reference/file-conventions/dynamic-routes) and the [`params`](/docs/app/api-reference/file-conventions/page#params-optional) props.

Nested [layouts within Dynamic Segments](/docs/app/api-reference/file-conventions/layout#params-optional), can also access the `params` props.

## Rendering with search params

In a Server Component **page**, you can access search parameters using the [`searchParams`](/docs/app/api-reference/file-conventions/page#searchparams-optional) prop:

```tsx filename="app/page.tsx" switcher
export default async function Page({
  searchParams,
}: {
  searchParams: Promise
}) {
  const filters = (await searchParams).filters
}
```

```jsx filename="app/page.jsx" switcher
export default async function Page({ searchParams }) {
  const filters = (await searchParams).filters
}
```

Using `searchParams` opts your page into [**dynamic rendering**](/docs/app/glossary#dynamic-rendering) because it requires an incoming request to read the search parameters from.

Client Components can read search params using the [`useSearchParams`](/docs/app/api-reference/functions/use-search-params) hook.

Learn more about `useSearchParams` in [prerendered](/docs/app/api-reference/functions/use-search-params#prerendering) and [dynamically rendered](/docs/app/api-reference/functions/use-search-params#dynamic-rendering) routes.

### What to use and when

* Use the `searchParams` prop when you need search parameters to **load data for the page** (e.g. pagination, filtering from a database).
* Use `useSearchParams` when search parameters are used **only on the client** (e.g. filtering a list already loaded via props).
* As a small optimization, you can use `new URLSearchParams(window.location.search)` in **callbacks or event handlers** to read search params without triggering re-renders.

## Linking between pages

You can use the [`` component](/docs/app/api-reference/components/link) to navigate between routes. `` is a built-in Next.js component that extends the HTML `` tag to provide [prefetching](/docs/app/getting-started/linking-and-navigating#prefetching) and [client-side navigation](/docs/app/getting-started/linking-and-navigating#client-side-transitions).

For example, to generate a list of blog posts, import `` from `next/link` and pass a `href` prop to the component:

```tsx filename="app/ui/post.tsx" highlight={1,10} switcher
import Link from 'next/link'

export default async function Post({ post }) {
  const posts = await getPosts()

  return (

      {posts.map((post) => (

          {post.title}

      ))}

  )
}
```

```jsx filename="app/ui/post.js" highlight={1,10}  switcher
import Link from 'next/link'

export default async function Post({ post }) {
  const posts = await getPosts()

  return (

      {posts.map((post) => (

          {post.title}

      ))}

  )
}
```

> **Good to know**: `` is the primary way to navigate between routes in Next.js. You can also use the [`useRouter` hook](/docs/app/api-reference/functions/use-router) for more advanced navigation.

## Route Props Helpers

Next.js exposes utility types that infer `params` and named slots from your route structure:

* [**PageProps**](/docs/app/api-reference/file-conventions/page#page-props-helper): Props for `page` components, including `params` and `searchParams`.
* [**LayoutProps**](/docs/app/api-reference/file-conventions/layout#layout-props-helper): Props for `layout` components, including `children` and any named slots (e.g. folders like `@analytics`).

These are globally available helpers, generated when running either `next dev`, `next build` or [`next typegen`](/docs/app/api-reference/cli/next#next-typegen-options).

```tsx filename="app/blog/[slug]/page.tsx"
export default async function Page(props: PageProps) {
  const { slug } = await props.params
  return Blog post: {slug}

}
```

```tsx filename="app/dashboard/layout.tsx"
export default function Layout(props: LayoutProps) {
  return (

      {props.children}
      {/* If you have app/dashboard/@analytics, it appears as a typed slot: */}
      {/* {props.analytics} */}

  )
}
```

> **Good to know**
>
> * Static routes resolve `params` to `{}`.
> * `PageProps`, `LayoutProps` are global helpers — no imports required.
> * Types are generated during `next dev`, `next build` or `next typegen`.
## API Reference

Learn more about the features mentioned in this page by reading the API Reference.

- [Linking and Navigating](/docs/app/getting-started/linking-and-navigating)
  - Learn how the built-in navigation optimizations work, including prefetching, prerendering, and client-side navigation, and how to optimize navigation for dynamic routes and slow networks.
- [layout.js](/docs/app/api-reference/file-conventions/layout)
  - API reference for the layout.js file.
- [page.js](/docs/app/api-reference/file-conventions/page)
  - API reference for the page.js file.
- [Link Component](/docs/app/api-reference/components/link)
  - Enable fast client-side navigation with the built-in `next/link` component.
- [Dynamic Segments](/docs/app/api-reference/file-conventions/dynamic-routes)
  - Dynamic Route Segments can be used to programmatically generate route segments from dynamic data.

---
title: Linking and Navigating
description: Learn how the built-in navigation optimizations work, including prefetching, prerendering, and client-side navigation, and how to optimize navigation for dynamic routes and slow networks.
url: "https://nextjs.org/docs/app/getting-started/linking-and-navigating"
version: 16.2.6
---

# Linking and Navigating

In Next.js, routes are rendered on the server by default. This often means the client has to wait for a server response before a new route can be shown. Next.js comes with built-in [prefetching](#prefetching), [streaming](#streaming), and [client-side transitions](#client-side-transitions) ensuring navigation stays fast and responsive.

This guide explains how navigation works in Next.js and how you can optimize it for [dynamic routes](#dynamic-routes-without-loadingtsx) and [slow networks](#slow-networks).

## How navigation works

To understand how navigation works in Next.js, it helps to be familiar with the following concepts:

* [Server Rendering](#server-rendering)
* [Prefetching](#prefetching)
* [Streaming](#streaming)
* [Client-side transitions](#client-side-transitions)

### Server Rendering

In Next.js, [Layouts and Pages](/docs/app/getting-started/layouts-and-pages) are [React Server Components](https://react.dev/reference/rsc/server-components) by default. On initial and subsequent navigations, the [Server Component Payload](/docs/app/getting-started/server-and-client-components#how-do-server-and-client-components-work-in-nextjs) is generated on the server before being sent to the client.

There are two types of server rendering, based on *when* it happens:

* **Prerendering** happens at build time or during [revalidation](/docs/app/getting-started/revalidating) and the result is cached.
* **Dynamic Rendering** happens at request time in response to a client request.

The trade-off of server rendering is that the client must wait for the server to respond before the new route can be shown. Next.js addresses this delay by [prefetching](#prefetching) routes the user is likely to visit and performing [client-side transitions](#client-side-transitions).

> **Good to know**: HTML is also generated for the initial visit.

### Prefetching

Prefetching is the process of loading a route in the background before the user navigates to it. This makes navigation between routes in your application feel instant, because by the time a user clicks on a link, the data to render the next route is already available client side.

Next.js automatically prefetches routes linked with the [`` component](/docs/app/api-reference/components/link) when they enter the user's viewport.

```tsx filename="app/layout.tsx" switcher
import Link from 'next/link'

export default function Layout({ children }: { children: React.ReactNode }) {
  return (

        {children}

  )
}
```

```jsx filename="app/layout.js" switcher
import Link from 'next/link'

export default function Layout() {
  return (

        {children}

  )
}
```

How much of the route is prefetched depends on whether it's static or dynamic:

* **Static Route**: the full route is prefetched.
* **Dynamic Route**: prefetching is skipped, or the route is partially prefetched if [`loading.tsx`](/docs/app/api-reference/file-conventions/loading) is present.

By skipping or partially prefetching dynamic routes, Next.js avoids unnecessary work on the server for routes the users may never visit. However, waiting for a server response before navigation can give the users the impression that the app is not responding.

![Server Rendering without Streaming](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/server-rendering-without-streaming.png)

To improve the navigation experience to dynamic routes, you can use [streaming](#streaming).

### Streaming

Streaming allows the server to send parts of a dynamic route to the client as soon as they're ready, rather than waiting for the entire route to be rendered. This means users see something sooner, even if parts of the page are still loading. See the [Streaming guide](/docs/app/guides/streaming) for a deep dive into how streaming works in Next.js.

For dynamic routes, it means they can be **partially prefetched**. That is, shared layouts and loading skeletons can be requested ahead of time.

![How Server Rendering with Streaming Works](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/server-rendering-with-streaming.png)

To use streaming, create a `loading.tsx` in your route folder:

![loading.js special file](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/loading-special-file.png)

```tsx filename="app/dashboard/loading.tsx" switcher
export default function Loading() {
  // Add fallback UI that will be shown while the route is loading.
  return
}
```

```jsx filename="app/dashboard/loading.js" switcher
export default function Loading() {
  // Add fallback UI that will be shown while the route is loading.
  return
}
```

Behind the scenes, Next.js will automatically wrap the `page.tsx` contents in a `` boundary. The prefetched fallback UI will be shown while the route is loading, and swapped for the actual content once ready.

> **Good to know**: You can also use [``](https://react.dev/reference/react/Suspense) to create loading UI for nested components.

Benefits of `loading.tsx`:

* Immediate navigation and visual feedback for the user.
* Shared layouts remain interactive and navigation is interruptible.
* Improved Core Web Vitals: [TTFB](https://web.dev/articles/ttfb), [FCP](https://web.dev/articles/fcp), and [TTI](https://web.dev/articles/tti).

To further improve the navigation experience, Next.js performs a [client-side transition](#client-side-transitions) with the `` component.

### Client-side transitions

Traditionally, navigation to a server-rendered page triggers a full page load. This clears state, resets scroll position, and blocks interactivity.

Next.js avoids this with client-side transitions using the `` component. Instead of reloading the page, it updates the content dynamically by:

* Keeping any shared layouts and UI.
* Replacing the current page with the prefetched loading state or a new page if available.

Client-side transitions are what makes a server-rendered apps *feel* like client-rendered apps. And when paired with [prefetching](#prefetching) and [streaming](#streaming), it enables fast transitions, even for dynamic routes.

Next.js also handles [scrolling to the top of the page](/docs/app/api-reference/components/link#scroll) during client-side transitions. If content scrolls behind a sticky or fixed header after navigation, you can fix this with CSS [`scroll-padding-top`](/docs/app/api-reference/components/link#scroll-offset-with-sticky-headers).

## What can make transitions slow?

These Next.js optimizations make navigation fast and responsive. However, under certain conditions, transitions can still *feel* slow. Here are some common causes and how to improve the user experience:

### Dynamic routes without `loading.tsx`

When navigating to a dynamic route, the client must wait for the server response before showing the result. This can give the users the impression that the app is not responding.

We recommend adding `loading.tsx` to dynamic routes to enable partial prefetching, trigger immediate navigation, and display a loading UI while the route renders.

```tsx filename="app/blog/[slug]/loading.tsx" switcher
export default function Loading() {
  return
}
```

```jsx filename="app/blog/[slug]/loading.js" switcher
export default function Loading() {
  return
}
```

> **Good to know**: In development mode, you can use the Next.js Devtools to identify if the route is static or dynamic. See [`devIndicators`](/docs/app/api-reference/config/next-config-js/devIndicators) for more information.

### Dynamic segments without `generateStaticParams`

If a [dynamic segment](/docs/app/api-reference/file-conventions/dynamic-routes) could be prerendered but isn't because it's missing [`generateStaticParams`](/docs/app/api-reference/functions/generate-static-params), the route will fallback to dynamic rendering at request time.

Ensure the route is statically generated at build time by adding `generateStaticParams`:

```tsx filename="app/blog/[slug]/page.tsx" switcher
export async function generateStaticParams() {
  const posts = await fetch('https://.../posts').then((res) => res.json())

  return posts.map((post) => ({
    slug: post.slug,
  }))
}

export default async function Page({
  params,
}: {
  params: Promise
}) {
  const { slug } = await params
  // ...
}
```

```jsx filename="app/blog/[slug]/page.js" switcher
export async function generateStaticParams() {
  const posts = await fetch('https://.../posts').then((res) => res.json())

  return posts.map((post) => ({
    slug: post.slug,
  }))
}

export default async function Page({ params }) {
  const { slug } = await params
  // ...
}
```

### Slow networks

On slow or unstable networks, prefetching may not finish before the user clicks a link. This can affect both static and dynamic routes. In these cases, the `loading.js` fallback may not appear immediately because it hasn't been prefetched yet.

To improve perceived performance, you can use the [`useLinkStatus` hook](/docs/app/api-reference/functions/use-link-status) to show immediate feedback while the transition is in progress.

```tsx filename="app/ui/loading-indicator.tsx" switcher
'use client'

import { useLinkStatus } from 'next/link'

export default function LoadingIndicator() {
  const { pending } = useLinkStatus()
  return (

  )
}
```

```jsx filename="app/ui/loading-indicator.js" switcher
'use client'

import { useLinkStatus } from 'next/link'

export default function LoadingIndicator() {
  const { pending } = useLinkStatus()
  return (

  )
}
```

You can "debounce" the hint by adding an initial animation delay (e.g. 100ms) and starting as invisible (e.g. `opacity: 0`). This means the loading indicator will only be shown if the navigation takes longer than the specified delay. See the [`useLinkStatus` reference](/docs/app/api-reference/functions/use-link-status#gracefully-handling-fast-navigation) for a CSS example.

> **Good to know**: You can use other visual feedback patterns like a progress bar. View an example [here](https://github.com/vercel/react-transition-progress).

### Disabling prefetching

You can opt out of prefetching by setting the `prefetch` prop to `false` on the `` component. This is useful to avoid unnecessary usage of resources when rendering large lists of links (e.g. an infinite scroll table).

```tsx

  Blog

```

However, disabling prefetching comes with trade-offs:

* **Static routes** will only be fetched when the user clicks the link.
* **Dynamic routes** will need to be rendered on the server first before the client can navigate to it.

To reduce resource usage without fully disabling prefetch, you can prefetch only on hover. This limits prefetching to routes the user is more *likely* to visit, rather than all links in the viewport.

```tsx filename="app/ui/hover-prefetch-link.tsx" switcher
'use client'

import Link from 'next/link'
import { useState } from 'react'

function HoverPrefetchLink({
  href,
  children,
}: {
  href: string
  children: React.ReactNode
}) {
  const [active, setActive] = useState(false)

  return (
     setActive(true)}
    >
      {children}

  )
}
```

```jsx filename="app/ui/hover-prefetch-link.js" switcher
'use client'

import Link from 'next/link'
import { useState } from 'react'

function HoverPrefetchLink({ href, children }) {
  const [active, setActive] = useState(false)

  return (
     setActive(true)}
    >
      {children}

  )
}
```

### Hydration not completed

`` is a Client Component and must be hydrated before it can prefetch routes. On the initial visit, large JavaScript bundles can delay hydration, preventing prefetching from starting right away.

React mitigates this with Selective Hydration and you can further improve this by:

* Using the [`@next/bundle-analyzer`](/docs/app/guides/package-bundling#nextbundle-analyzer-for-webpack) plugin to identify and reduce bundle size by removing large dependencies.
* Moving logic from the client to the server where possible. See the [Server and Client Components](/docs/app/getting-started/server-and-client-components) docs for guidance.

## Examples

### Native History API

Next.js allows you to use the native [`window.history.pushState`](https://developer.mozilla.org/en-US/docs/Web/API/History/pushState) and [`window.history.replaceState`](https://developer.mozilla.org/en-US/docs/Web/API/History/replaceState) methods to update the browser's history stack without reloading the page.

`pushState` and `replaceState` calls integrate into the Next.js Router, allowing you to sync with [`usePathname`](/docs/app/api-reference/functions/use-pathname) and [`useSearchParams`](/docs/app/api-reference/functions/use-search-params).

#### `window.history.pushState`

Use it to add a new entry to the browser's history stack. The user can navigate back to the previous state. For example, to sort a list of products:

```tsx fileName="app/ui/sort-products.tsx" switcher
'use client'

import { useSearchParams } from 'next/navigation'

export default function SortProducts() {
  const searchParams = useSearchParams()

  function updateSorting(sortOrder: string) {
    const params = new URLSearchParams(searchParams.toString())
    params.set('sort', sortOrder)
    window.history.pushState(null, '', `?${params.toString()}`)
  }

  return (
    <>
       updateSorting('asc')}>Sort Ascending
       updateSorting('desc')}>Sort Descending

  )
}
```

```jsx fileName="app/ui/sort-products.js" switcher
'use client'

import { useSearchParams } from 'next/navigation'

export default function SortProducts() {
  const searchParams = useSearchParams()

  function updateSorting(sortOrder) {
    const params = new URLSearchParams(searchParams.toString())
    params.set('sort', sortOrder)
    window.history.pushState(null, '', `?${params.toString()}`)
  }

  return (
    <>
       updateSorting('asc')}>Sort Ascending
       updateSorting('desc')}>Sort Descending

  )
}
```

#### `window.history.replaceState`

Use it to replace the current entry on the browser's history stack. The user is not able to navigate back to the previous state. For example, to switch the application's locale:

```tsx fileName="app/ui/locale-switcher.tsx" switcher
'use client'

import { usePathname } from 'next/navigation'

export function LocaleSwitcher() {
  const pathname = usePathname()

  function switchLocale(locale: string) {
    // e.g. '/en/about' or '/fr/contact'
    const newPath = `/${locale}${pathname}`
    window.history.replaceState(null, '', newPath)
  }

  return (
    <>
       switchLocale('en')}>English
       switchLocale('fr')}>French

  )
}
```

```jsx fileName="app/ui/locale-switcher.js" switcher
'use client'

import { usePathname } from 'next/navigation'

export function LocaleSwitcher() {
  const pathname = usePathname()

  function switchLocale(locale) {
    // e.g. '/en/about' or '/fr/contact'
    const newPath = `/${locale}${pathname}`
    window.history.replaceState(null, '', newPath)
  }

  return (
    <>
       switchLocale('en')}>English
       switchLocale('fr')}>French

  )
}
```
- [Link Component](/docs/app/api-reference/components/link)
  - Enable fast client-side navigation with the built-in `next/link` component.
- [loading.js](/docs/app/api-reference/file-conventions/loading)
  - API reference for the loading.js file.
- [Prefetching](/docs/app/guides/prefetching)
  - Learn how to configure prefetching in Next.js

---
title: Server and Client Components
description: Learn how you can use React Server and Client Components to render parts of your application on the server or the client.
url: "https://nextjs.org/docs/app/getting-started/server-and-client-components"
version: 16.2.6
---

# Server and Client Components

By default, layouts and pages are [Server Components](https://react.dev/reference/rsc/server-components), which lets you fetch data and render parts of your UI on the server, optionally cache the result, and stream it to the client. When you need interactivity or browser APIs, you can use [Client Components](https://react.dev/reference/rsc/use-client) to layer in functionality.

This page explains how Server and Client Components work in Next.js and when to use them, with examples of how to compose them together in your application.

## When to use Server and Client Components?

The client and server environments have different capabilities. Server and Client components allow you to run logic in each environment depending on your use case.

Use **Client Components** when you need:

* [State](https://react.dev/learn/managing-state) and [event handlers](https://react.dev/learn/responding-to-events). E.g. `onClick`, `onChange`.
* [Lifecycle logic](https://react.dev/learn/lifecycle-of-reactive-effects). E.g. `useEffect`.
* Browser-only APIs. E.g. `localStorage`, `window`, `Navigator.geolocation`, etc.
* [Custom hooks](https://react.dev/learn/reusing-logic-with-custom-hooks).

Use **Server Components** when you need:

* Fetch data from databases or APIs close to the source.
* Use API keys, tokens, and other secrets without exposing them to the client.
* Reduce the amount of JavaScript sent to the browser.
* Improve the [First Contentful Paint (FCP)](https://web.dev/fcp/), and stream content progressively to the client.

For example, the `` component is a Server Component that fetches data about a post, and passes it as props to the `` which handles client-side interactivity.

```tsx filename="app/[id]/page.tsx" highlight={1,17} switcher
import LikeButton from '@/app/ui/like-button'
import { getPost } from '@/lib/data'

export default async function Page({
  params,
}: {
  params: Promise
}) {
  const { id } = await params
  const post = await getPost(id)

  return (

        {post.title}

        {/* ... */}

  )
}
```

```jsx filename="app/[id]/page.js" highlight={1,12} switcher
import LikeButton from '@/app/ui/like-button'
import { getPost } from '@/lib/data'

export default async function Page({ params }) {
  const post = await getPost(params.id)

  return (

        {post.title}

        {/* ... */}

  )
}
```

```tsx filename="app/ui/like-button.tsx" highlight={1} switcher
'use client'

import { useState } from 'react'

export default function LikeButton({ likes }: { likes: number }) {
  // ...
}
```

```jsx filename="app/ui/like-button.js" highlight={1} switcher
'use client'

import { useState } from 'react'

export default function LikeButton({ likes }) {
  // ...
}
```

## How do Server and Client Components work in Next.js?

### On the server

On the server, Next.js uses React's APIs to orchestrate rendering. The rendering work is split into chunks, by individual route segments ([layouts and pages](/docs/app/getting-started/layouts-and-pages)):

* **Server Components** are rendered into a special data format called the React Server Component Payload (RSC Payload).
* **Client Components** and the RSC Payload are used to [prerender](/docs/app/glossary#prerendering) HTML.

> **What is the React Server Component Payload (RSC)?**
>
> The RSC Payload is a compact binary representation of the rendered React Server Components tree. It's used by React on the client to update the browser's DOM. The RSC Payload contains:
>
> * The rendered result of Server Components
> * Placeholders for where Client Components should be rendered and references to their JavaScript files
> * Any props passed from a Server Component to a Client Component

### On the client (first load)

Then, on the client:

1. **HTML** is used to immediately show a fast non-interactive preview of the route to the user.
2. **RSC Payload** is used to reconcile the Client and Server Component trees.
3. **JavaScript** is used to hydrate Client Components and make the application interactive.

> **What is hydration?**
>
> Hydration is React's process for attaching [event handlers](https://react.dev/learn/responding-to-events) to the DOM, to make the static HTML interactive.

### Subsequent Navigations

On subsequent navigations:

* The **RSC Payload** is prefetched and cached for instant navigation.
* **Client Components** are rendered entirely on the client, without the server-rendered HTML.

## Examples

### Using Client Components

You can create a Client Component by adding the [`"use client"`](https://react.dev/reference/react/use-client) directive at the top of the file, above your imports.

```tsx filename="app/ui/counter.tsx" highlight={1} switcher
'use client'

import { useState } from 'react'

export default function Counter() {
  const [count, setCount] = useState(0)

  return (

      {count} likes

       setCount(count + 1)}>Click me

  )
}
```

```jsx filename="app/ui/counter.js" highlight={1} switcher
'use client'

import { useState } from 'react'

export default function Counter() {
  const [count, setCount] = useState(0)

  return (

      {count} likes

       setCount(count + 1)}>Click me

  )
}
```

`"use client"` is used to declare a **boundary** between the Server and Client module graphs (trees).

Once a file is marked with `"use client"`, **all of its imports and the components it directly renders are included in the client bundle**. This means you don’t need to add the directive to every component that is intended for the client.

This behavior applies to components that are part of the Client Component’s [module graph](/docs/app/glossary#module-graph), which includes the modules it imports and the components it renders directly. It does not apply to Server Components passed as children or other props. Those components are not imported into the Client Component’s module graph. They are rendered on the server and passed to the Client Component as rendered output.

See [Interleaving Server and Client Components](/docs/app/getting-started/server-and-client-components#interleaving-server-and-client-components) for how Server and Client Components can be combined.

### Reducing JS bundle size

To reduce the size of your client JavaScript bundles, add `'use client'` to specific interactive components instead of marking large parts of your UI as Client Components.

For example, the `` component contains mostly static elements like a logo and navigation links, but includes an interactive search bar. `` is interactive and needs to be a Client Component, however, the rest of the layout can remain a Server Component.

```tsx filename="app/layout.tsx" highlight={12} switcher
// Client Component
import Search from './search'
// Server Component
import Logo from './logo'

// Layout is a Server Component by default
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <>

      {children}

  )
}
```

```jsx filename="app/layout.js" highlight={12} switcher
// Client Component
import Search from './search'
// Server Component
import Logo from './logo'

// Layout is a Server Component by default
export default function Layout({ children }) {
  return (
    <>

      {children}

  )
}
```

```tsx filename="app/ui/search.tsx" highlight={1} switcher
'use client'

export default function Search() {
  // ...
}
```

```jsx filename="app/ui/search.js" highlight={1} switcher
'use client'

export default function Search() {
  // ...
}
```

### Passing data from Server to Client Components

You can pass data from Server Components to Client Components using props.

```tsx filename="app/[id]/page.tsx" highlight={1,12} switcher
import LikeButton from '@/app/ui/like-button'
import { getPost } from '@/lib/data'

export default async function Page({
  params,
}: {
  params: Promise
}) {
  const { id } = await params
  const post = await getPost(id)

  return
}
```

```jsx filename="app/[id]/page.js" highlight={1,7} switcher
import LikeButton from '@/app/ui/like-button'
import { getPost } from '@/lib/data'

export default async function Page({ params }) {
  const post = await getPost(params.id)

  return
}
```

```tsx filename="app/ui/like-button.tsx" highlight={1} switcher
'use client'

export default function LikeButton({ likes }: { likes: number }) {
  // ...
}
```

```jsx filename="app/ui/like-button.js" highlight={1} switcher
'use client'

export default function LikeButton({ likes }) {
  // ...
}
```

Alternatively, you can stream data from a Server Component to a Client Component with the [`use` API](https://react.dev/reference/react/use). See an [example](/docs/app/getting-started/fetching-data#streaming-data-with-the-use-api).

> **Good to know**: Props passed to Client Components need to be [serializable](https://react.dev/reference/react/use-server#serializable-parameters-and-return-values) by React.

### Interleaving Server and Client Components

You can pass Server Components as a prop to a Client Component. This allows you to visually nest server-rendered UI within Client components.

A common pattern is to use `children` to create a *slot* in a ``. For example, a `` component that fetches data on the server, inside a `` component that uses client state to toggle visibility.

```tsx filename="app/ui/modal.tsx" switcher
'use client'

export default function Modal({ children }: { children: React.ReactNode }) {
  return {children}

}
```

```jsx filename="app/ui/modal.js" switcher
'use client'

export default function Modal({ children }) {
  return {children}

}
```

Then, in a parent Server Component (e.g.``), you can pass a `` as the child of the ``:

```tsx filename="app/page.tsx"  highlight={7} switcher
import Modal from './ui/modal'
import Cart from './ui/cart'

export default function Page() {
  return (

  )
}
```

```jsx filename="app/page.js" highlight={7} switcher
import Modal from './ui/modal'
import Cart from './ui/cart'

export default function Page() {
  return (

  )
}
```

In this pattern, Server Components are rendered on the server ahead of time, even when passed as props to Client Components. The React Server Component Payload contains the rendered result of those Server Components, plus placeholders for where Client Components should be rendered and references to their JavaScript files.

### Context providers

[React context](https://react.dev/learn/passing-data-deeply-with-context) is commonly used to share global state like the current theme. However, React context is not supported in Server Components.

To use context, create a Client Component that accepts `children`:

```tsx filename="app/theme-provider.tsx" switcher
'use client'

import { createContext } from 'react'

export const ThemeContext = createContext({})

export default function ThemeProvider({
  children,
}: {
  children: React.ReactNode
}) {
  return {children}
}
```

```jsx filename="app/theme-provider.js" switcher
'use client'

import { createContext } from 'react'

export const ThemeContext = createContext({})

export default function ThemeProvider({ children }) {
  return {children}
}
```

Then, import it into a Server Component (e.g. `layout`):

```tsx filename="app/layout.tsx" switcher
import ThemeProvider from './theme-provider'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (

        {children}

  )
}
```

```jsx filename="app/layout.js" switcher
import ThemeProvider from './theme-provider'

export default function RootLayout({ children }) {
  return (

        {children}

  )
}
```

Your Server Component will now be able to directly render your provider, and all other Client Components throughout your app will be able to consume this context.

> **Good to know**: You should render providers as deep as possible in the tree – notice how `ThemeProvider` only wraps `{children}` instead of the entire `` document. This makes it easier for Next.js to optimize the static parts of your Server Components.

### Third-party components

When using a third-party component that relies on client-only features, you can wrap it in a Client Component to ensure it works as expected.

For example, the `` can be imported from the `acme-carousel` package. This component uses `useState`, but it doesn't yet have the `"use client"` directive.

If you use `` within a Client Component, it will work as expected:

```tsx filename="app/gallery.tsx" switcher
'use client'

import { useState } from 'react'
import { Carousel } from 'acme-carousel'

export default function Gallery() {
  const [isOpen, setIsOpen] = useState(false)

  return (

       setIsOpen(true)}>View pictures
      {/* Works, since Carousel is used within a Client Component */}
      {isOpen && }

  )
}
```

```jsx filename="app/gallery.js" switcher
'use client'

import { useState } from 'react'
import { Carousel } from 'acme-carousel'

export default function Gallery() {
  const [isOpen, setIsOpen] = useState(false)

  return (

       setIsOpen(true)}>View pictures
      {/*  Works, since Carousel is used within a Client Component */}
      {isOpen && }

  )
}
```

However, if you try to use it directly within a Server Component, you'll see an error. This is because Next.js doesn't know `` is using client-only features.

To fix this, you can wrap third-party components that rely on client-only features in your own Client Components:

```tsx filename="app/carousel.tsx" switcher
'use client'

import { Carousel } from 'acme-carousel'

export default Carousel
```

```jsx filename="app/carousel.js" switcher
'use client'

import { Carousel } from 'acme-carousel'

export default Carousel
```

Now, you can use `` directly within a Server Component:

```tsx filename="app/page.tsx" switcher
import Carousel from './carousel'

export default function Page() {
  return (

      View pictures

      {/*  Works, since Carousel is a Client Component */}

  )
}
```

```jsx filename="app/page.js" switcher
import Carousel from './carousel'

export default function Page() {
  return (

      View pictures

      {/*  Works, since Carousel is a Client Component */}

  )
}
```

> **Advice for Library Authors**
>
> If you’re building a component library, add the `"use client"` directive to entry points that rely on client-only features. This lets your users import components into Server Components without needing to create wrappers.
>
> It's worth noting some bundlers might strip out `"use client"` directives. You can find an example of how to configure esbuild to include the `"use client"` directive in the [React Wrap Balancer](https://github.com/shuding/react-wrap-balancer/blob/main/tsup.config.ts#L10-L13) and [Vercel Analytics](https://github.com/vercel/analytics/blob/main/packages/web/tsup.config.js#L26-L30) repositories.

### Preventing environment poisoning

JavaScript modules can be shared between both Server and Client Components modules. This means it's possible to accidentally import server-only code into the client. For example, consider the following function:

```ts filename="lib/data.ts" switcher
export async function getData() {
  const res = await fetch('https://external-service.com/data', {
    headers: {
      authorization: process.env.API_KEY,
    },
  })

  return res.json()
}
```

```js filename="lib/data.js" switcher
export async function getData() {
  const res = await fetch('https://external-service.com/data', {
    headers: {
      authorization: process.env.API_KEY,
    },
  })

  return res.json()
}
```

This function contains an `API_KEY` that should never be exposed to the client.

In Next.js, only environment variables prefixed with `NEXT_PUBLIC_` are included in the client bundle. If variables are not prefixed, Next.js replaces them with an empty string.

As a result, even though `getData()` can be imported and executed on the client, it won't work as expected.

To prevent accidental usage in Client Components, you can use the [`server-only` package](https://www.npmjs.com/package/server-only).

Then, import the package into a file that contains server-only code:

```js filename="lib/data.js"
import 'server-only'

export async function getData() {
  const res = await fetch('https://external-service.com/data', {
    headers: {
      authorization: process.env.API_KEY,
    },
  })

  return res.json()
}
```

Now, if you try to import the module into a Client Component, there will be a build-time error.

The corresponding [`client-only` package](https://www.npmjs.com/package/client-only) can be used to mark modules that contain client-only logic like code that accesses the `window` object.

In Next.js, installing `server-only` or `client-only` is **optional**. However, if your linting rules flag extraneous dependencies, you may install them to avoid issues.

```bash package="npm"
npm install server-only
```

```bash package="yarn"
yarn add server-only
```

```bash package="pnpm"
pnpm add server-only
```

```bash package="bun"
bun add server-only
```

Next.js handles `server-only` and `client-only` imports internally to provide clearer error messages when a module is used in the wrong environment. The contents of these packages from NPM are not used by Next.js.

Next.js also provides its own type declarations for `server-only` and `client-only`, for TypeScript configurations where [`noUncheckedSideEffectImports`](https://www.typescriptlang.org/tsconfig/#noUncheckedSideEffectImports) is active.
## Next Steps

Learn more about the APIs mentioned in this page.

- [use client](/docs/app/api-reference/directives/use-client)
  - Learn how to use the use client directive to render a component on the client.

---
title: Fetching Data
description: Learn how to fetch data and stream content that depends on data.
url: "https://nextjs.org/docs/app/getting-started/fetching-data"
version: 16.2.6
---

# Fetching Data

This page will walk you through how you can fetch data in [Server](#server-components) and [Client](#client-components) Components, and how to [stream](#streaming) components that depend on uncached data.

## Fetching data

### Server Components

You can fetch data in Server Components using any asynchronous I/O, such as:

1. The [`fetch` API](#with-the-fetch-api)
2. An [ORM or database](#with-an-orm-or-database)

#### With the `fetch` API

To fetch data with the `fetch` API, turn your component into an asynchronous function, and await the `fetch` call. For example:

```tsx filename="app/blog/page.tsx" switcher
export default async function Page() {
  const data = await fetch('https://api.vercel.app/blog')
  const posts = await data.json()
  return (

      {posts.map((post) => (
        {post.title}

      ))}

  )
}
```

```jsx filename="app/blog/page.js" switcher
export default async function Page() {
  const data = await fetch('https://api.vercel.app/blog')
  const posts = await data.json()
  return (

      {posts.map((post) => (
        {post.title}

      ))}

  )
}
```

> **Good to know:**
>
> * Identical `fetch` requests in a React component tree are [memoized](/docs/app/glossary#memoization) by default, so you can fetch data in the component that needs it instead of drilling props.
> * `fetch` requests are not cached by default and will block the page from rendering until the request is complete. Use the [`use cache`](/docs/app/api-reference/directives/use-cache) directive to cache results, or wrap the fetching component in [``](/docs/app/getting-started/caching#streaming-uncached-data) to stream fresh data at request time. See [caching](/docs/app/getting-started/caching) for details.
> * During development, you can log `fetch` calls for better visibility and debugging. See the [`logging` API reference](/docs/app/api-reference/config/next-config-js/logging).

#### With an ORM or database

Since Server Components are rendered on the server, credentials and query logic will not be included in the client bundle so you can safely make database queries using an ORM or database client.

```tsx filename="app/blog/page.tsx" switcher
import { db, posts } from '@/lib/db'

export default async function Page() {
  const allPosts = await db.select().from(posts)
  return (

      {allPosts.map((post) => (
        {post.title}

      ))}

  )
}
```

```jsx filename="app/blog/page.js" switcher
import { db, posts } from '@/lib/db'

export default async function Page() {
  const allPosts = await db.select().from(posts)
  return (

      {allPosts.map((post) => (
        {post.title}

      ))}

  )
}
```

You should still ensure requests are properly authenticated and authorized. For best practices on securing server-side data access, see the [data security guide](/docs/app/guides/data-security).

### Streaming

When you fetch data in Server Components, the data is fetched and rendered on the server for each request. If you have any slow data requests, the whole route will be blocked from rendering until all the data is fetched.

To improve the initial load time and user experience, you can break the page into smaller *chunks* and progressively send those chunks from the server to the client. This is called streaming. See the [Streaming guide](/docs/app/guides/streaming) for a deeper look at how streaming works, including the HTTP contract, infrastructure considerations, and performance trade-offs.

![How Server Rendering with Streaming Works](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/server-rendering-with-streaming.png)

There are two ways you can use streaming in your application:

1. Wrapping a page with a [`loading.js` file](#with-loadingjs)
2. Wrapping a component with [``](#with-suspense)

#### With `loading.js`

You can create a `loading.js` file in the same folder as your page to stream the **entire page** while the data is being fetched. For example, to stream `app/blog/page.js`, add the file inside the `app/blog` folder.

![Blog folder structure with loading.js file](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/loading-file.png)

```tsx filename="app/blog/loading.tsx" switcher
export default function Loading() {
  // Define the Loading UI here
  return Loading...

}
```

```jsx filename="app/blog/loading.js" switcher
export default function Loading() {
  // Define the Loading UI here
  return Loading...

}
```

On navigation, the user will immediately see the layout and a [loading state](#creating-meaningful-loading-states) while the page is being rendered. The new content will then be automatically swapped in once rendering is complete.

![Loading UI](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/loading-ui.png)

Behind the scenes, `loading.js` will be [nested inside `layout.js`](/docs/app/getting-started/project-structure#component-hierarchy), and will automatically wrap the `page.js` file and any children below in a `` boundary.

![loading.js overview](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/loading-overview.png)

Because of this, a layout that accesses uncached or runtime data (e.g. `cookies()`, `headers()`, or uncached fetches) does not fall back to a same route segment `loading.js`. Instead, it blocks navigation until the layout finishes rendering. [Cache Components](/docs/app/getting-started/caching) prevents this by guiding you with a build-time error.

To fix this, wrap the uncached access in its own [``](#with-suspense) boundary with a fallback, or move the data fetching into `page.js` where `loading.js` can cover it. See [`loading.js`](/docs/app/api-reference/file-conventions/loading) for more details.

This is why, while `loading.js` works well for streaming route segments, using `` closer to the runtime or uncached data access is recommended.

#### With ``

`` allows you to be more granular about what parts of the page to stream. For example, you can immediately show any page content that falls outside of the `` boundary, and stream in the list of blog posts inside the boundary.

```tsx filename="app/blog/page.tsx" switcher
import { Suspense } from 'react'
import BlogList from '@/components/BlogList'
import BlogListSkeleton from '@/components/BlogListSkeleton'

export default function BlogPage() {
  return (

      {/* This content will be sent to the client immediately */}

        {/* If there's any dynamic content inside this boundary, it will be streamed in */}
        }>

  )
}
```

```jsx filename="app/blog/page.js" switcher
import { Suspense } from 'react'
import BlogList from '@/components/BlogList'
import BlogListSkeleton from '@/components/BlogListSkeleton'

export default function BlogPage() {
  return (

      {/* This content will be sent to the client immediately */}

        {/* If there's any dynamic content inside this boundary, it will be streamed in */}
        }>

  )
}
```

#### Creating meaningful loading states

An instant loading state is fallback UI that is shown immediately to the user after navigation. For the best user experience, we recommend designing loading states that are meaningful and help users understand the app is responding. For example, you can use skeletons and spinners, or a small but meaningful part of future screens such as a cover photo, title, etc.

In development, you can preview and inspect the loading state of your components using the [React Devtools](https://react.dev/learn/react-developer-tools).

### Client Components

There are two ways to fetch data in Client Components, using:

1. React's [`use` API](https://react.dev/reference/react/use)
2. A community library like [SWR](https://swr.vercel.app/) or [React Query](https://tanstack.com/query/latest)

#### Streaming data with the `use` API

You can use React's [`use` API](https://react.dev/reference/react/use) to [stream](#streaming) data from the server to client. Start by fetching data in your Server component, and pass the promise to your Client Component as prop:

```tsx filename="app/blog/page.tsx" switcher
import Posts from '@/app/ui/posts'
import { Suspense } from 'react'

export default function Page() {
  // Don't await the data fetching function
  const posts = getPosts()

  return (
    Loading...
}>

  )
}
```

```jsx filename="app/blog/page.js" switcher
import Posts from '@/app/ui/posts'
import { Suspense } from 'react'

export default function Page() {
  // Don't await the data fetching function
  const posts = getPosts()

  return (
    Loading...
}>

  )
}
```

Then, in your Client Component, use the `use` API to read the promise:

```tsx filename="app/ui/posts.tsx" switcher
'use client'
import { use } from 'react'

export default function Posts({
  posts,
}: {
  posts: Promise
}) {
  const allPosts = use(posts)

  return (

      {allPosts.map((post) => (
        {post.title}

      ))}

  )
}
```

```jsx filename="app/ui/posts.js" switcher
'use client'
import { use } from 'react'

export default function Posts({ posts }) {
  const allPosts = use(posts)

  return (

      {allPosts.map((post) => (
        {post.title}

      ))}

  )
}
```

In the example above, the `` component is wrapped in a [`` boundary](https://react.dev/reference/react/Suspense). This means the fallback will be shown while the promise is being resolved. Learn more about [streaming](#streaming).

#### Community libraries

You can use a community library like [SWR](https://swr.vercel.app/) or [React Query](https://tanstack.com/query/latest) to fetch data in Client Components. These libraries have their own semantics for caching, streaming, and other features. For example, with SWR:

```tsx filename="app/blog/page.tsx" switcher
'use client'
import useSWR from 'swr'

const fetcher = (url) => fetch(url).then((r) => r.json())

export default function BlogPage() {
  const { data, error, isLoading } = useSWR(
    'https://api.vercel.app/blog',
    fetcher
  )

  if (isLoading) return Loading...

  if (error) return Error: {error.message}

  return (

      {data.map((post: { id: string; title: string }) => (
        {post.title}

      ))}

  )
}
```

```jsx filename="app/blog/page.js" switcher
'use client'

import useSWR from 'swr'

const fetcher = (url) => fetch(url).then((r) => r.json())

export default function BlogPage() {
  const { data, error, isLoading } = useSWR(
    'https://api.vercel.app/blog',
    fetcher
  )

  if (isLoading) return Loading...

  if (error) return Error: {error.message}

  return (

      {data.map((post) => (
        {post.title}

      ))}

  )
}
```

## Examples

### Sequential data fetching

Sequential data fetching happens when one request depends on data from another.

For example, `` can only fetch data after `` completes because it needs the `artistID`:

```tsx filename="app/artist/[username]/page.tsx" switcher
export default async function Page({
  params,
}: {
  params: Promise
}) {
  const { username } = await params
  // Get artist information
  const artist = await getArtist(username)

  return (
    <>
      {artist.name}

      {/* Show fallback UI while the Playlists component is loading */}
      Loading...
}>
        {/* Pass the artist ID to the Playlists component */}

  )
}

async function Playlists({ artistID }: { artistID: string }) {
  // Use the artist ID to fetch playlists
  const playlists = await getArtistPlaylists(artistID)

  return (

      {playlists.map((playlist) => (
        {playlist.name}

      ))}

  )
}
```

```jsx filename="app/artist/[username]/page.js" switcher
export default async function Page({ params }) {
  const { username } = await params
  // Get artist information
  const artist = await getArtist(username)

  return (
    <>
      {artist.name}

      {/* Show fallback UI while the Playlists component is loading */}
      Loading...
}>
        {/* Pass the artist ID to the Playlists component */}

  )
}

async function Playlists({ artistID }) {
  // Use the artist ID to fetch playlists
  const playlists = await getArtistPlaylists(artistID)

  return (

      {playlists.map((playlist) => (
        {playlist.name}

      ))}

  )
}
```

In this example, `` allows the playlists to stream in after the artist data loads. However, the page still waits for the artist data before displaying anything. To prevent this, you can wrap the entire page component in a `` boundary (for example, using a [`loading.js` file](#with-loadingjs)) to show a loading state immediately.

Ensure your data source can resolve the first request quickly, as it blocks everything else. If you can't optimize the request further, consider [caching](/docs/app/getting-started/caching) the result if the data changes infrequently.

### Parallel data fetching

Parallel data fetching happens when data requests in a route are eagerly initiated and start at the same time.

By default, [layouts and pages](/docs/app/getting-started/layouts-and-pages) are rendered in parallel. So each segment starts fetching data as soon as possible.

However, within *any* component, multiple `async`/`await` requests can still be sequential if placed after the other. For example, `getAlbums` will be blocked until `getArtist` is resolved:

```tsx filename="app/artist/[username]/page.tsx" switcher
import { getArtist, getAlbums } from '@/app/lib/data'

export default async function Page({ params }) {
  // These requests will be sequential
  const { username } = await params
  const artist = await getArtist(username)
  const albums = await getAlbums(username)
  return {artist.name}

}
```

Start multiple requests by calling `fetch`, then await them with [`Promise.all`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all). Requests begin as soon as `fetch` is called.

```tsx filename="app/artist/[username]/page.tsx" highlight={3,8,24} switcher
import Albums from './albums'

async function getArtist(username: string) {
  const res = await fetch(`https://api.example.com/artist/${username}`)
  return res.json()
}

async function getAlbums(username: string) {
  const res = await fetch(`https://api.example.com/artist/${username}/albums`)
  return res.json()
}

export default async function Page({
  params,
}: {
  params: Promise
}) {
  const { username } = await params

  // Initiate requests
  const artistData = getArtist(username)
  const albumsData = getAlbums(username)

  const [artist, albums] = await Promise.all([artistData, albumsData])

  return (
    <>
      {artist.name}

  )
}
```

```jsx filename="app/artist/[username]/page.js" highlight={3,8,20} switcher
import Albums from './albums'

async function getArtist(username) {
  const res = await fetch(`https://api.example.com/artist/${username}`)
  return res.json()
}

async function getAlbums(username) {
  const res = await fetch(`https://api.example.com/artist/${username}/albums`)
  return res.json()
}

export default async function Page({ params }) {
  const { username } = await params

  // Initiate requests
  const artistData = getArtist(username)
  const albumsData = getAlbums(username)

  const [artist, albums] = await Promise.all([artistData, albumsData])

  return (
    <>
      {artist.name}

  )
}
```

> **Good to know:** If one request fails when using `Promise.all`, the entire operation will fail. To handle this, you can use the [`Promise.allSettled`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled) method instead.

### Sharing data with context and `React.cache`

You can share fetched data across both Server and Client Components by combining [`React.cache`](https://react.dev/reference/react/cache) with context providers.

Create a cached function that fetches data:

```ts filename="app/lib/user.ts" switcher
import { cache } from 'react'

export const getUser = cache(async () => {
  const res = await fetch('https://api.example.com/user')
  return res.json()
})
```

```js filename="app/lib/user.js" switcher
import { cache } from 'react'

export const getUser = cache(async () => {
  const res = await fetch('https://api.example.com/user')
  return res.json()
})
```

Create a context provider that stores the promise:

```tsx filename="app/user-provider.tsx" switcher
'use client'

import { createContext } from 'react'

type User = {
  id: string
  name: string
}

export const UserContext = createContext | null>(null)

export default function UserProvider({
  children,
  userPromise,
}: {
  children: React.ReactNode
  userPromise: Promise
}) {
  return {children}
}
```

```jsx filename="app/user-provider.js" switcher
'use client'

import { createContext } from 'react'

export const UserContext = createContext(null)

export default function UserProvider({ children, userPromise }) {
  return {children}
}
```

In a layout, pass the promise to the provider without awaiting:

```tsx filename="app/layout.tsx" switcher
import UserProvider from './user-provider'
import { getUser } from './lib/user'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const userPromise = getUser() // Don't await

  return (

        {children}

  )
}
```

```jsx filename="app/layout.js" switcher
import UserProvider from './user-provider'
import { getUser } from './lib/user'

export default function RootLayout({ children }) {
  const userPromise = getUser() // Don't await

  return (

        {children}

  )
}
```

Client Components use [`use()`](https://react.dev/reference/react/use) to resolve the promise from context, wrapped in `` for fallback UI:

```tsx filename="app/ui/profile.tsx" switcher
'use client'

import { use, useContext } from 'react'
import { UserContext } from '../user-provider'

export function Profile() {
  const userPromise = useContext(UserContext)
  if (!userPromise) {
    throw new Error('useContext must be used within a UserProvider')
  }
  const user = use(userPromise)
  return Welcome, {user.name}

}
```

```jsx filename="app/ui/profile.js" switcher
'use client'

import { use, useContext } from 'react'
import { UserContext } from '../user-provider'

export function Profile() {
  const userPromise = useContext(UserContext)
  if (!userPromise) {
    throw new Error('useContext must be used within a UserProvider')
  }
  const user = use(userPromise)
  return Welcome, {user.name}

}
```

```tsx filename="app/page.tsx" switcher
import { Suspense } from 'react'
import { Profile } from './ui/profile'

export default function Page() {
  return (
    Loading profile...
}>

  )
}
```

```jsx filename="app/page.js" switcher
import { Suspense } from 'react'
import { Profile } from './ui/profile'

export default function Page() {
  return (
    Loading profile...
}>

  )
}
```

Server Components can also call `getUser()` directly:

```tsx filename="app/dashboard/page.tsx" switcher
import { getUser } from '../lib/user'

export default async function DashboardPage() {
  const user = await getUser() // Cached - same request, no duplicate fetch
  return Dashboard for {user.name}

}
```

```jsx filename="app/dashboard/page.js" switcher
import { getUser } from '../lib/user'

export default async function DashboardPage() {
  const user = await getUser() // Cached - same request, no duplicate fetch
  return Dashboard for {user.name}

}
```

Since `getUser` is wrapped with `React.cache`, multiple calls within the same request return the same memoized result, whether called directly in Server Components or resolved via context in Client Components.

> **Good to know**: `React.cache` is scoped to the current request only. Each request gets its own memoization scope with no sharing between requests.
## API Reference

Learn more about the features mentioned in this page by reading the API Reference.

- [Data Security](/docs/app/guides/data-security)
  - Learn the built-in data security features in Next.js and learn best practices for protecting your application's data.
- [fetch](/docs/app/api-reference/functions/fetch)
  - API reference for the extended fetch function.
- [loading.js](/docs/app/api-reference/file-conventions/loading)
  - API reference for the loading.js file.
- [logging](/docs/app/api-reference/config/next-config-js/logging)
  - Configure logging behavior in the terminal when running Next.js in development mode, including fetch logging, incoming requests, and forwarding browser console logs to the terminal.
- [taint](/docs/app/api-reference/config/next-config-js/taint)
  - Enable tainting Objects and Values.

---
title: Mutating Data
description: Learn how to mutate data using Server Functions and Server Actions in Next.js.
url: "https://nextjs.org/docs/app/getting-started/mutating-data"
version: 16.2.6
---

# Mutating Data

You can mutate data in Next.js using [React Server Functions](https://react.dev/reference/rsc/server-functions). This page will go through how you can [create](#creating-server-functions) and [invoke](#invoking-server-functions) Server Functions.

## What are Server Functions?

A **Server Function** is an asynchronous function that runs on the server. You can call them from the client through a network request, which is why they must be asynchronous.

In an `action` or mutation context, they are also called **Server Actions**.

By convention, a Server Action is an async function used with [`startTransition`](https://react.dev/reference/react/startTransition). This happens automatically when the function is:

* Passed to a `` using the `action` prop.
* Passed to a `` using the `formAction` prop.

When an action is invoked, Next.js can return both the updated UI and new data in a single server roundtrip.

Behind the scenes, actions use the `POST` method, and only this HTTP method can invoke them.

> \[!WARNING]
> Server Functions are reachable via direct POST requests, not just through your application's UI. Always verify authentication and authorization inside every Server Function. See the [Data Security guide](/docs/app/guides/data-security#authentication-and-authorization) for recommended patterns.

> **Good to know:** A Server Action is a Server Function used in a specific way (for handling form submissions and mutations). Server Function is the broader term.

## Creating Server Functions

A Server Function can be defined by using the [`use server`](https://react.dev/reference/rsc/use-server) directive. You can place the directive at the top of an **asynchronous** function to mark the function as a Server Function, or at the top of a separate file to mark all exports of that file.

```ts filename="app/lib/actions.ts" switcher
import { auth } from '@/lib/auth'

export async function createPost(formData: FormData) {
  'use server'
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  const title = formData.get('title')
  const content = formData.get('content')

  // Mutate data
  // Revalidate cache
}

export async function deletePost(formData: FormData) {
  'use server'
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  const id = formData.get('id')

  // Verify the user owns this resource before deleting
  // Mutate data
  // Revalidate cache
}
```

```js filename="app/lib/actions.js" switcher
import { auth } from '@/lib/auth'

export async function createPost(formData) {
  'use server'
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  const title = formData.get('title')
  const content = formData.get('content')

  // Mutate data
  // Revalidate cache
}

export async function deletePost(formData) {
  'use server'
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  const id = formData.get('id')

  // Verify the user owns this resource before deleting
  // Mutate data
  // Revalidate cache
}
```

### Server Components

Server Functions can be inlined in Server Components by adding the `"use server"` directive to the top of the function body:

```tsx filename="app/page.tsx" switcher
export default function Page() {
  // Server Action
  async function createPost(formData: FormData) {
    'use server'
    // ...
  }

  return <>
}
```

```jsx filename="app/page.js" switcher
export default function Page() {
  // Server Action
  async function createPost(formData) {
    'use server'
    // ...
  }

  return <>
}
```

> **Good to know:** Server Components support progressive enhancement by default, meaning forms that call Server Actions will be submitted even if JavaScript hasn't loaded yet or is disabled.

### Client Components

It's not possible to define Server Functions in Client Components. However, you can invoke them in Client Components by importing them from a file that has the `"use server"` directive at the top of it:

```ts filename="app/actions.ts" switcher
'use server'

export async function createPost() {}
```

```js filename="app/actions.js" switcher
'use server'

export async function createPost() {}
```

```tsx filename="app/ui/button.tsx" switcher
'use client'

import { createPost } from '@/app/actions'

export function Button() {
  return Create
}
```

```jsx filename="app/ui/button.js" switcher
'use client'

import { createPost } from '@/app/actions'

export function Button() {
  return Create
}
```

> **Good to know:** In Client Components, forms invoking Server Actions will queue submissions if JavaScript isn't loaded yet, and will be prioritized for hydration. After hydration, the browser does not refresh on form submission.

### Passing actions as props

You can also pass an action to a Client Component as a prop:

```jsx

```

```tsx filename="app/client-component.tsx" switcher
'use client'

export default function ClientComponent({
  updateItemAction,
}: {
  updateItemAction: (formData: FormData) => void
}) {
  return {/* ... */}
}
```

```jsx filename="app/client-component.js" switcher
'use client'

export default function ClientComponent({ updateItemAction }) {
  return {/* ... */}
}
```

## Invoking Server Functions

There are two main ways you can invoke a Server Function:

1. [Forms](#forms) in Server and Client Components
2. [Event Handlers](#event-handlers) and [useEffect](#useeffect) in Client Components

> **Good to know:** Server Functions are designed for server-side mutations. The client currently dispatches and awaits them one at a time. This is an implementation detail and may change. If you need parallel data fetching, use [data fetching](/docs/app/getting-started/fetching-data#server-components) in Server Components, or perform parallel work inside a single Server Function or [Route Handler](/docs/app/guides/backend-for-frontend#manipulating-data).

### Forms

React extends the HTML [``](https://react.dev/reference/react-dom/components/form) element to allow a Server Function to be invoked with the HTML `action` prop.

When invoked in a form, the function automatically receives the [`FormData`](https://developer.mozilla.org/docs/Web/API/FormData/FormData) object. You can extract the data using the native [`FormData` methods](https://developer.mozilla.org/en-US/docs/Web/API/FormData#instance_methods):

```tsx filename="app/ui/form.tsx" switcher
import { createPost } from '@/app/actions'

export function Form() {
  return (

      Create

  )
}
```

```jsx filename="app/ui/form.js" switcher
import { createPost } from '@/app/actions'

export function Form() {
  return (

      Create

  )
}
```

```ts filename="app/actions.ts" switcher
'use server'

import { auth } from '@/lib/auth'

export async function createPost(formData: FormData) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  const title = formData.get('title')
  const content = formData.get('content')

  // Mutate data
  // Revalidate cache
}
```

```js filename="app/actions.js" switcher
'use server'

import { auth } from '@/lib/auth'

export async function createPost(formData) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  const title = formData.get('title')
  const content = formData.get('content')

  // Mutate data
  // Revalidate cache
}
```

### Event Handlers

You can invoke a Server Function in a Client Component by using event handlers such as `onClick`.

```tsx filename="app/like-button.tsx" switcher
'use client'

import { incrementLike } from './actions'
import { useState } from 'react'

export default function LikeButton({ initialLikes }: { initialLikes: number }) {
  const [likes, setLikes] = useState(initialLikes)

  return (
    <>
      Total Likes: {likes}

       {
          const updatedLikes = await incrementLike()
          setLikes(updatedLikes)
        }}
      >
        Like

  )
}
```

```jsx filename="app/like-button.js" switcher
'use client'

import { incrementLike } from './actions'
import { useState } from 'react'

export default function LikeButton({ initialLikes }) {
  const [likes, setLikes] = useState(initialLikes)

  return (
    <>
      Total Likes: {likes}

       {
          const updatedLikes = await incrementLike()
          setLikes(updatedLikes)
        }}
      >
        Like

  )
}
```

## Examples

### Showing a pending state

While executing a Server Function, you can show a loading indicator with React's [`useActionState`](https://react.dev/reference/react/useActionState) hook. This hook returns a `pending` boolean:

```tsx filename="app/ui/button.tsx" switcher
'use client'

import { useActionState, startTransition } from 'react'
import { createPost } from '@/app/actions'
import { LoadingSpinner } from '@/app/ui/loading-spinner'

export function Button() {
  const [state, action, pending] = useActionState(createPost, false)

  return (
     startTransition(action)}>
      {pending ?  : 'Create Post'}

  )
}
```

```jsx filename="app/ui/button.js" switcher
'use client'

import { useActionState, startTransition } from 'react'
import { createPost } from '@/app/actions'
import { LoadingSpinner } from '@/app/ui/loading-spinner'

export function Button() {
  const [state, action, pending] = useActionState(createPost, false)

  return (
     startTransition(action)}>
      {pending ?  : 'Create Post'}

  )
}
```

### Refresh data

After a mutation, you may want to refresh the current page to show the latest data. You can do this by calling [`refresh`](/docs/app/api-reference/functions/refresh) from `next/cache` in a Server Action:

```ts filename="app/lib/actions.ts" switcher
'use server'

import { auth } from '@/lib/auth'
import { refresh } from 'next/cache'

export async function updatePost(formData: FormData) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }
  // Mutate data
  // ...

  refresh()
}
```

```js filename="app/lib/actions.js" switcher
'use server'

import { auth } from '@/lib/auth'
import { refresh } from 'next/cache'

export async function updatePost(formData) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }
  // Mutate data
  // ...

  refresh()
}
```

This refreshes the client router, ensuring the UI reflects the latest state. The `refresh()` function does not revalidate tagged data. To revalidate tagged data, use [`updateTag`](/docs/app/api-reference/functions/updateTag) or [`revalidateTag`](/docs/app/api-reference/functions/revalidateTag) instead.

### Revalidate data

After performing a mutation, you can revalidate the Next.js cache and show the updated data by calling [`revalidatePath`](/docs/app/api-reference/functions/revalidatePath) or [`revalidateTag`](/docs/app/api-reference/functions/revalidateTag) within the Server Function:

```ts filename="app/lib/actions.ts" switcher
import { auth } from '@/lib/auth'
import { revalidatePath } from 'next/cache'

export async function createPost(formData: FormData) {
  'use server'
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }
  // Mutate data
  // ...

  revalidatePath('/posts')
}
```

```js filename="app/actions.js" switcher
import { auth } from '@/lib/auth'
import { revalidatePath } from 'next/cache'

export async function createPost(formData) {
  'use server'
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }
  // Mutate data
  // ...
  revalidatePath('/posts')
}
```

### Redirect after a mutation

You may want to redirect the user to a different page after a mutation. You can do this by calling [`redirect`](/docs/app/api-reference/functions/redirect) within the Server Function.

```ts filename="app/lib/actions.ts" switcher
'use server'

import { auth } from '@/lib/auth'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

export async function createPost(formData: FormData) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }
  // Mutate data
  // ...

  revalidatePath('/posts')
  redirect('/posts')
}
```

```js filename="app/actions.js" switcher
'use server'

import { auth } from '@/lib/auth'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

export async function createPost(formData) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }
  // Mutate data
  // ...

  revalidatePath('/posts')
  redirect('/posts')
}
```

Calling `redirect` [throws](/docs/app/api-reference/functions/redirect#behavior) a framework handled control-flow exception. Any code after it won't execute. If you need fresh data, call [`revalidatePath`](/docs/app/api-reference/functions/revalidatePath) or [`revalidateTag`](/docs/app/api-reference/functions/revalidateTag) beforehand.

### Cookies

You can `get`, `set`, and `delete` cookies inside a Server Action using the [`cookies`](/docs/app/api-reference/functions/cookies) API.

When you [set or delete](/docs/app/api-reference/functions/cookies#understanding-cookie-behavior-in-server-functions) a cookie in a Server Action, Next.js re-renders the current page and its layouts on the server so the **UI reflects the new cookie value**.

> **Good to know**: The server update applies to the current React tree, re-rendering, mounting, or unmounting components, as needed. Client state is preserved for re-rendered components, and effects re-run if their dependencies changed.

```ts filename="app/actions.ts" switcher
'use server'

import { cookies } from 'next/headers'

export async function exampleAction() {
  const cookieStore = await cookies()

  // Get cookie
  cookieStore.get('name')?.value

  // Set cookie
  cookieStore.set('name', 'Delba')

  // Delete cookie
  cookieStore.delete('name')
}
```

```js filename="app/actions.js" switcher
'use server'

import { cookies } from 'next/headers'

export async function exampleAction() {
  // Get cookie
  const cookieStore = await cookies()

  // Get cookie
  cookieStore.get('name')?.value

  // Set cookie
  cookieStore.set('name', 'Delba')

  // Delete cookie
  cookieStore.delete('name')
}
```

### useEffect

You can use the React [`useEffect`](https://react.dev/reference/react/useEffect) hook to invoke a Server Action when the component mounts or a dependency changes. This is useful for mutations that depend on global events or need to be triggered automatically. For example, `onKeyDown` for app shortcuts, an intersection observer hook for infinite scrolling, or when the component mounts to update a view count:

```tsx filename="app/view-count.tsx" switcher
'use client'

import { incrementViews } from './actions'
import { useState, useEffect, useTransition } from 'react'

export default function ViewCount({ initialViews }: { initialViews: number }) {
  const [views, setViews] = useState(initialViews)
  const [isPending, startTransition] = useTransition()

  useEffect(() => {
    startTransition(async () => {
      const updatedViews = await incrementViews()
      setViews(updatedViews)
    })
  }, [])

  // You can use `isPending` to give users feedback
  return Total Views: {views}

}
```

```jsx filename="app/view-count.js" switcher
'use client'

import { incrementViews } from './actions'
import { useState, useEffect, useTransition } from 'react'

export default function ViewCount({ initialViews }) {
  const [views, setViews] = useState(initialViews)
  const [isPending, startTransition] = useTransition()

  useEffect(() => {
    startTransition(async () => {
      const updatedViews = await incrementViews()
      setViews(updatedViews)
    })
  }, [])

  // You can use `isPending` to give users feedback
  return Total Views: {views}

}
```
## API Reference

Learn more about the features mentioned in this page by reading the API Reference.

- [revalidatePath](/docs/app/api-reference/functions/revalidatePath)
  - API Reference for the revalidatePath function.
- [revalidateTag](/docs/app/api-reference/functions/revalidateTag)
  - API Reference for the revalidateTag function.
- [redirect](/docs/app/api-reference/functions/redirect)
  - API Reference for the redirect function.

---
title: Caching
description: Learn how to cache data and UI in Next.js
url: "https://nextjs.org/docs/app/getting-started/caching"
version: 16.2.6
---

# Caching

> This page covers caching with [Cache Components](/docs/app/api-reference/config/next-config-js/cacheComponents), enabled by setting [`cacheComponents: true`](/docs/app/api-reference/config/next-config-js/cacheComponents) in your `next.config.ts` file. If you're not using Cache Components, see the [Caching and Revalidating (Previous Model)](/docs/app/guides/caching-without-cache-components) guide.

Caching is a technique for storing the result of data fetching and other computations so that future requests for the same data can be served faster, without doing the work again.

## Enabling Cache Components

You can enable Cache Components by adding the [`cacheComponents`](/docs/app/api-reference/config/next-config-js/cacheComponents) option to your Next config file:

```ts filename="next.config.ts" highlight={4} switcher
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  cacheComponents: true,
}

export default nextConfig
```

```js filename="next.config.js" highlight={3} switcher
/** @type {import('next').NextConfig} */
const nextConfig = {
  cacheComponents: true,
}

module.exports = nextConfig
```

> **Good to know:** When Cache Components is enabled, `GET` Route Handlers follow the same prerendering model as pages. See [Route Handlers with Cache Components](/docs/app/getting-started/route-handlers#with-cache-components) for details.

## Usage

The [`use cache`](/docs/app/api-reference/directives/use-cache) directive caches the return value of async functions and components. You can apply it at two levels:

* **Data-level**: Cache a function that fetches or computes data (e.g., `getProducts()`, `getUser(id)`)
* **UI-level**: Cache an entire component or page (e.g., `async function BlogPosts()`)

> Arguments and any closed-over values from parent scopes automatically become part of the [cache key](/docs/app/api-reference/directives/use-cache#cache-keys), which means different inputs will produce separate cache entries. This enables personalized or parameterized cached content. See [serialization requirements and constraints](/docs/app/api-reference/directives/use-cache#constraints) for details on what can be cached and how arguments work.

### Data-level caching

To cache an asynchronous function that fetches data, add the `use cache` directive at the top of the function body:

```tsx filename="app/lib/data.ts" highlight={3,4,5}
import { cacheLife } from 'next/cache'

export async function getUsers() {
  'use cache'
  cacheLife('hours')
  return db.query('SELECT * FROM users')
}
```

Data-level caching is useful when the same data is used across multiple components, or when you want to cache the data independently from the UI.

### UI-level caching

To cache an entire component, page, or layout, add the `use cache` directive at the top of the component or page body:

```tsx filename="app/page.tsx" highlight={1,4,5}
import { cacheLife } from 'next/cache'

export default async function Page() {
  'use cache'
  cacheLife('hours')

  const users = await db.query('SELECT * FROM users')

  return (

      {users.map((user) => (
        {user.name}

      ))}

  )
}
```

> If you add "`use cache`" at the top of a file, all exported functions in the file will be cached.

### Streaming uncached data

For components that fetch data from an asynchronous source such as an API, a database, or any other async operation, and require fresh data on every request, do not use `"use cache"`.

Instead, wrap the component in [``](https://react.dev/reference/react/Suspense) and provide a fallback UI. At request time, React renders the fallback first, then streams in the resolved content once the async work completes.

```tsx filename="page.tsx"
import { Suspense } from 'react'

async function LatestPosts() {
  const data = await fetch('https://api.example.com/posts')
  const posts = await data.json()
  return (

      {posts.map((post) => (
        {post.title}

      ))}

  )
}

export default function Page() {
  return (
    <>
      My Blog

      Loading posts...
}>

  )
}
```

The fallback (`Loading posts...
`) is included in the static shell, while the component's content streams in at request time.

`` provides a fallback UI while async work completes, but it does not itself opt a component into dynamic rendering. If a component only performs synchronous work, it will complete during prerendering regardless of whether it is wrapped in ``.

## Working with runtime APIs

Runtime APIs require information that is only available when a user makes a request. These include:

* [`cookies`](/docs/app/api-reference/functions/cookies) - User's cookie data
* [`headers`](/docs/app/api-reference/functions/headers) - Request headers
* [`searchParams`](/docs/app/api-reference/file-conventions/page#searchparams-optional) - URL query parameters
* [`params`](/docs/app/api-reference/file-conventions/page#params-optional) - Dynamic route parameters (unless at least one sample is provided via [`generateStaticParams`](/docs/app/api-reference/functions/generate-static-params)).

Components that access runtime APIs should be wrapped in ``:

```tsx filename="page.tsx"
import { cookies } from 'next/headers'
import { Suspense } from 'react'

async function UserGreeting() {
  const cookieStore = await cookies()
  const theme = cookieStore.get('theme')?.value || 'light'
  return Your theme: {theme}

}

export default function Page() {
  return (
    <>
      Dashboard

      Loading...
}>

  )
}
```

### Passing runtime values to cached functions

You can extract values from runtime APIs and pass them as arguments to cached functions:

```tsx filename="app/profile/page.tsx"
import { cookies } from 'next/headers'
import { Suspense } from 'react'

export default function Page() {
  return (
    Loading...
}>

  )
}

// Component (not cached) reads runtime data
async function ProfileContent() {
  const session = (await cookies()).get('session')?.value
  return
}

// Cached component receives extracted value as a prop
async function CachedContent({ sessionId }: { sessionId: string }) {
  'use cache'
  // sessionId becomes part of the cache key
  const data = await fetchUserData(sessionId)
  return {data}

}
```

At request time, `CachedContent` executes if no matching cache entry is found, and stores the result for future requests with the same `sessionId`.

By default, `use cache` stores entries [in-memory](/docs/app/api-reference/directives/use-cache#runtime-caching-considerations). In serverless environments where memory doesn't persist across requests, `CachedContent` may re-evaluate on every request. Consider [`'use cache: remote'`](/docs/app/api-reference/directives/use-cache-remote) for durable, shared caching.

## Working with non-deterministic operations

Operations like `Math.random()`, `Date.now()`, or `crypto.randomUUID()` produce different values each time they execute. Cache Components requires you to explicitly handle these.

**To generate unique values per request**, defer to request time by calling [`connection()`](/docs/app/api-reference/functions/connection) before these operations, and wrap the component in ``:

```tsx filename="page.tsx"
import { connection } from 'next/server'
import { Suspense } from 'react'

async function UniqueContent() {
  await connection()
  const uuid = crypto.randomUUID()
  return Request ID: {uuid}

}

export default function Page() {
  return (
    Loading...
}>

  )
}
```

Alternatively, you can **cache the result** so all users see the same value until revalidation:

```tsx filename="page.tsx"
export default async function Page() {
  'use cache'
  const buildId = crypto.randomUUID()
  return Build ID: {buildId}

}
```

## Working with deterministic operations

Operations like synchronous I/O, module imports, and pure computations can complete during prerendering. Components using only these operations have their rendered output automatically included in the static HTML shell.

```tsx filename="page.tsx"
import fs from 'node:fs'

export default async function Page() {
  const content = fs.readFileSync('./config.json', 'utf-8')
  const constants = await import('./constants.json')
  const processed = JSON.parse(content).items.map((item) => item.value * 2)

  return (

      {constants.appName}

        {processed.map((value, i) => (
          {value}

        ))}

  )
}
```

> **Good to know:** This includes queries to embedded databases with synchronous APIs, such as `better-sqlite3` or Node.js's built-in [`node:sqlite`](https://nodejs.org/api/sqlite.html). If you need per-request data from a synchronous source, call [`connection()`](/docs/app/api-reference/functions/connection) before the query.

## How rendering works

At build time, Next.js renders your route's component tree. How each component is handled depends on the APIs it uses:

* [`use cache`](#usage): the result is cached and included in the static shell
* [``](#streaming-uncached-data): fallback UI is included in the static shell while the content streams at request time
* [Deterministic operations](#working-with-deterministic-operations): like pure computations and module imports are automatically included in the static shell

This generates a static shell consisting of HTML for initial page loads and a serialized [RSC Payload](/docs/app/getting-started/server-and-client-components#on-the-server) for client-side navigation, ensuring the browser receives fully rendered content instantly whether users navigate directly to the URL or transition from another page.

![Partially re-rendered Product Page showing static nav and product information, and dynamic cart and recommended products](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/learn/light/thinking-in-ppr.png)

This rendering approach is called **Partial Prerendering (PPR)**, and it's the default behavior with Cache Components.

> You can verify that a route was fully prerendered by checking the [build output summary](/docs/app/api-reference/cli/next#next-build-options). Alternatively, see what content was added to the static shell of any page by viewing the page source in your browser.

![Diagram showing partially rendered page on the client, with loading UI for chunks that are being streamed.](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/server-rendering-with-streaming.png)

Next.js requires you to explicitly handle components that can't complete during prerendering. If they aren't wrapped in `` or marked with `use cache`, you'll see an [`Uncached data was accessed outside of `](https://nextjs.org/docs/messages/blocking-route) error during development and build time.

> **🎥 Watch:** Why Partial Prerendering and how it works → [YouTube (10 minutes)](https://www.youtube.com/watch?v=MTcPrTIBkpA).

### Opting out of the static shell

Placing a `` boundary with an empty fallback above the document body in your Root Layout causes the entire app to defer to request time. Because the fallback is empty, there is no static shell to send immediately, so every request blocks until the page is fully rendered. To limit this to specific routes, use [multiple root layouts](/docs/app/api-reference/file-conventions/layout#root-layout).

```tsx filename="app/layout.tsx" highlight={1,10-12}
import { Suspense } from 'react'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (

        {children}

  )
}
```

> **Good to know**: This same pattern applies when `generateViewport` accesses uncached dynamic data. See [Viewport with Cache Components](/docs/app/api-reference/functions/generate-viewport#with-cache-components) for a detailed example.

### Putting it all together

Here's a complete example showing static content, cached dynamic content, and streaming dynamic content working together on a single page:

```tsx filename="app/blog/page.tsx"
import { Suspense } from 'react'
import { cookies } from 'next/headers'
import { cacheLife, cacheTag, updateTag } from 'next/cache'
import Link from 'next/link'

export default function BlogPage() {
  return (
    <>
      {/* Static content - prerendered automatically */}

      {/* Cached dynamic content - included in the static shell */}

      {/* Runtime dynamic content - streams at request time */}
      Loading your preferences...
}>

      {/* Mutation - server action that revalidates the cache */}
      Loading...
}>

  )
}

// Everyone sees the same blog posts (revalidated every hour)
async function BlogPosts() {
  'use cache'
  cacheLife('hours')
  cacheTag('posts')

  const res = await fetch('https://api.vercel.app/blog')
  const posts = await res.json()

  return (

      Latest Posts

        {posts.slice(0, 5).map((post: any) => (

            {post.title}

              By {post.author} on {post.date}

        ))}

  )
}

// Personalized per user based on their cookie
async function UserPreferences() {
  const theme = (await cookies()).get('theme')?.value || 'light'
  const favoriteCategory = (await cookies()).get('category')?.value

  return (

      Your theme: {theme}

      {favoriteCategory && Favorite category: {favoriteCategory}
}

  )
}

// Admin-only form that creates a post and revalidates the cache
async function CreatePost() {
  const isAdmin = (await cookies()).get('role')?.value === 'admin'
  if (!isAdmin) return null

  async function createPost(formData: FormData) {
    'use server'
    await db.post.create({ data: { title: formData.get('title') } })
    updateTag('posts')
  }

  return (

      Publish

  )
}
```

During prerendering, the header (static) and blog posts (cached with `use cache`) become part of the static shell along with the fallback UI for user preferences. Only the personalized preferences stream in at request time. When an admin publishes a new post, the [`updateTag`](/docs/app/getting-started/revalidating#updatetag) call immediately expires the blog posts cache so the next visitor sees it.

> **Good to know:** `generateMetadata` and `generateViewport` track runtime data access separately from the page. See [Metadata with Cache Components](/docs/app/api-reference/functions/generate-metadata#with-cache-components) and [Viewport with Cache Components](/docs/app/api-reference/functions/generate-viewport#with-cache-components) for how to handle this.
## Next Steps

Learn more about revalidation and the APIs mentioned on this page.

- [Revalidating](/docs/app/getting-started/revalidating)
  - Learn how to revalidate cached data using time-based and on-demand strategies.
- [use cache](/docs/app/api-reference/directives/use-cache)
  - Learn how to use the "use cache" directive to cache data in your Next.js application.
- [cacheComponents](/docs/app/api-reference/config/next-config-js/cacheComponents)
  - Learn how to enable the cacheComponents flag in Next.js.
- [Preserving UI state](/docs/app/guides/preserving-ui-state)
  - Learn how React's Activity component preserves UI state across navigations in Next.js and how to control what resets.

---
title: Revalidating
description: Learn how to revalidate cached data using time-based and on-demand strategies.
url: "https://nextjs.org/docs/app/getting-started/revalidating"
version: 16.2.6
---

# Revalidating

> This page covers revalidation with [Cache Components](/docs/app/api-reference/config/next-config-js/cacheComponents), enabled by setting [`cacheComponents: true`](/docs/app/api-reference/config/next-config-js/cacheComponents) in your `next.config.ts` file. If you're not using Cache Components, see the [Caching and Revalidating (Previous Model)](/docs/app/guides/caching-without-cache-components) guide.

Revalidation is the process of updating cached data. It lets you keep serving fast, cached responses while ensuring content stays fresh. There are two strategies:

* **Time-based revalidation**: Automatically refresh cached data after a set duration using [`cacheLife`](#cachelife).
* **On-demand revalidation**: Manually invalidate cached data after a mutation using [`revalidateTag`](#revalidatetag), [`updateTag`](#updatetag), or [`revalidatePath`](#revalidatepath).

## `cacheLife`

[`cacheLife`](/docs/app/api-reference/functions/cacheLife) controls how long cached data remains valid. Use it inside a [`use cache`](/docs/app/api-reference/directives/use-cache) scope to set the cache lifetime.

```tsx filename="app/lib/data.ts" highlight={1,4,5}
import { cacheLife } from 'next/cache'

export async function getProducts() {
  'use cache'
  cacheLife('hours')
  return db.query('SELECT * FROM products')
}
```

`cacheLife` accepts a profile name or a custom configuration object:

| Profile   | `stale` | `revalidate` | `expire`    |
| --------- | ------- | ------------ | ----------- |
| `seconds` | 0       | 1s           | 60s         |
| `minutes` | 5m      | 1m           | 1h          |
| `hours`   | 5m      | 1h           | 1d          |
| `days`    | 5m      | 1d           | 1w          |
| `weeks`   | 5m      | 1w           | 30d         |
| `max`     | 5m      | 30d          | ~indefinite |

For fine-grained control, pass an object:

```tsx highlight={2-6}
'use cache'
cacheLife({
  stale: 3600, // 1 hour until considered stale
  revalidate: 7200, // 2 hours until revalidated
  expire: 86400, // 1 day until expired
})
```

> **Good to know:** A cache is considered "short-lived" when it uses the `seconds` profile, `revalidate: 0`, or `expire` under 5 minutes. Short-lived caches are automatically excluded from prerenders and become dynamic holes instead. See [Prerendering behavior](/docs/app/api-reference/functions/cacheLife#prerendering-behavior) for details.

See the [`cacheLife` API reference](/docs/app/api-reference/functions/cacheLife) for all profiles and custom configuration options.

## `cacheTag`

[`cacheTag`](/docs/app/api-reference/functions/cacheTag) lets you tag cached data so it can be invalidated on-demand. Use it inside a [`use cache`](/docs/app/api-reference/directives/use-cache) scope:

```tsx filename="app/lib/data.ts" switcher
import { cacheTag } from 'next/cache'

export async function getProducts() {
  'use cache'
  cacheTag('products')
  return db.query('SELECT * FROM products')
}
```

```jsx filename="app/lib/data.js" switcher
import { cacheTag } from 'next/cache'

export async function getProducts() {
  'use cache'
  cacheTag('products')
  return db.query('SELECT * FROM products')
}
```

Once tagged, invalidate the cache using [`revalidateTag`](#revalidatetag) or [`updateTag`](#updatetag).

See the [`cacheTag` API reference](/docs/app/api-reference/functions/cacheTag) to learn more.

## `revalidateTag`

`revalidateTag` invalidates cache entries by tag using stale-while-revalidate semantics — stale content is served immediately while fresh content loads in the background. This is ideal for content where a slight delay in updates is acceptable, like blog posts or product catalogs.

```tsx filename="app/lib/actions.ts" highlight={1,5} switcher
import { revalidateTag } from 'next/cache'

export async function updateUser(id: string) {
  // Mutate data
  revalidateTag('user', 'max') // Recommended: stale-while-revalidate
}
```

```jsx filename="app/lib/actions.js" highlight={1,5} switcher
import { revalidateTag } from 'next/cache'

export async function updateUser(id) {
  // Mutate data
  revalidateTag('user', 'max') // Recommended: stale-while-revalidate
}
```

You can reuse the same tag in multiple functions to revalidate them all at once. Call `revalidateTag` in a [Server Action](/docs/app/getting-started/mutating-data) or [Route Handler](/docs/app/api-reference/file-conventions/route).

> **Good to know:** The second argument sets how long stale content can be served while fresh content generates in the background. Once it expires, subsequent requests block until fresh content is ready. Using `'max'` gives the longest stale window.

See the [`revalidateTag` API reference](/docs/app/api-reference/functions/revalidateTag) to learn more.

## `updateTag`

`updateTag` immediately expires cached data for read-your-own-writes scenarios — the user sees their change right away instead of stale content. Unlike `revalidateTag`, it can only be used in [Server Actions](/docs/app/getting-started/mutating-data).

```tsx filename="app/lib/actions.ts" highlight={1,12} switcher
import { updateTag } from 'next/cache'
import { redirect } from 'next/navigation'

export async function createPost(formData: FormData) {
  const post = await db.post.create({
    data: {
      title: formData.get('title'),
      content: formData.get('content'),
    },
  })

  updateTag('posts')
  redirect(`/posts/${post.id}`)
}
```

```jsx filename="app/lib/actions.js" highlight={1,12} switcher
import { updateTag } from 'next/cache'
import { redirect } from 'next/navigation'

export async function createPost(formData) {
  const post = await db.post.create({
    data: {
      title: formData.get('title'),
      content: formData.get('content'),
    },
  })

  updateTag('posts')
  redirect(`/posts/${post.id}`)
}
```

|              | `updateTag`                                   | `revalidateTag`                      |
| ------------ | --------------------------------------------- | ------------------------------------ |
| **Where**    | Server Actions only                           | Server Actions and Route Handlers    |
| **Behavior** | Immediately expires cache                     | Stale-while-revalidate               |
| **Use case** | Read-your-own-writes (user sees their change) | Background refresh (slight delay OK) |

See the [`updateTag` API reference](/docs/app/api-reference/functions/updateTag) to learn more.

## `revalidatePath`

`revalidatePath` invalidates all cached data for a specific route path. Use it when you want to revalidate a route without knowing which tags are associated with it.

```tsx filename="app/lib/actions.ts" highlight={1,5} switcher
import { revalidatePath } from 'next/cache'

export async function updateUser(id: string) {
  // Mutate data
  revalidatePath('/profile')
}
```

```jsx filename="app/lib/actions.js" highlight={1,5} switcher
import { revalidatePath } from 'next/cache'

export async function updateUser(id) {
  // Mutate data
  revalidatePath('/profile')
}
```

> **Good to know**: Prefer tag-based revalidation (`revalidateTag`/`updateTag`) over path-based when possible — it's more precise and avoids over-invalidating.

See the [`revalidatePath` API reference](/docs/app/api-reference/functions/revalidatePath) to learn more.

## What should I cache?

Cache data that doesn't depend on [runtime data](/docs/app/getting-started/caching#working-with-runtime-apis) and that you're OK serving from cache for a period of time. Use `use cache` with `cacheLife` to describe that behavior.

For content management systems with update mechanisms, use tags with longer cache durations and rely on `revalidateTag` to refresh content when it actually changes, rather than expiring the cache preemptively.

> **Good to know:** In serverless environments, in-memory cache entries may not persist across revalidations. See [runtime caching considerations](/docs/app/api-reference/directives/use-cache#runtime-caching-considerations) for details.
## API Reference

Learn more about the APIs mentioned on this page.

- [cacheLife](/docs/app/api-reference/functions/cacheLife)
  - Learn how to use the cacheLife function to set the cache expiration time for a cached function or component.
- [cacheTag](/docs/app/api-reference/functions/cacheTag)
  - Learn how to use the cacheTag function to manage cache invalidation in your Next.js application.
- [revalidateTag](/docs/app/api-reference/functions/revalidateTag)
  - API Reference for the revalidateTag function.
- [updateTag](/docs/app/api-reference/functions/updateTag)
  - API Reference for the updateTag function.
- [revalidatePath](/docs/app/api-reference/functions/revalidatePath)
  - API Reference for the revalidatePath function.

---
title: Error Handling
description: Learn how to display expected errors and handle uncaught exceptions.
url: "https://nextjs.org/docs/app/getting-started/error-handling"
version: 16.2.6
---

# Error Handling

Errors can be divided into two categories: [expected errors](#handling-expected-errors) and [uncaught exceptions](#handling-uncaught-exceptions). This page will walk you through how you can handle these errors in your Next.js application.

## Handling expected errors

Expected errors are those that can occur during the normal operation of the application, such as those from [server-side form validation](/docs/app/guides/forms) or failed requests. These errors should be handled explicitly and returned to the client.

### Server Functions

You can use the [`useActionState`](https://react.dev/reference/react/useActionState) hook to handle expected errors in [Server Functions](https://react.dev/reference/rsc/server-functions).

For these errors, avoid using `try`/`catch` blocks and throw errors. Instead, model expected errors as return values.

```ts filename="app/actions.ts" switcher
'use server'

export async function createPost(prevState: any, formData: FormData) {
  const title = formData.get('title')
  const content = formData.get('content')

  const res = await fetch('https://api.vercel.app/posts', {
    method: 'POST',
    body: { title, content },
  })
  const json = await res.json()

  if (!res.ok) {
    return { message: 'Failed to create post' }
  }
}
```

```js filename="app/actions.js" switcher
'use server'

export async function createPost(prevState, formData) {
  const title = formData.get('title')
  const content = formData.get('content')

  const res = await fetch('https://api.vercel.app/posts', {
    method: 'POST',
    body: { title, content },
  })
  const json = await res.json()

  if (!res.ok) {
    return { message: 'Failed to create post' }
  }
}
```

You can pass your action to the `useActionState` hook and use the returned `state` to display an error message.

```tsx filename="app/ui/form.tsx" highlight={11,19} switcher
'use client'

import { useActionState } from 'react'
import { createPost } from '@/app/actions'

const initialState = {
  message: '',
}

export function Form() {
  const [state, formAction, pending] = useActionState(createPost, initialState)

  return (

      Title

      Content

      {state?.message && {state.message}
}
      Create Post

  )
}
```

```jsx filename="app/ui/form.js" highlight={11,19} switcher
'use client'

import { useActionState } from 'react'
import { createPost } from '@/app/actions'

const initialState = {
  message: '',
}

export function Form() {
  const [state, formAction, pending] = useActionState(createPost, initialState)

  return (

      Title

      Content

      {state?.message && {state.message}
}
      Create Post

  )
}
```

### Server Components

When fetching data inside of a Server Component, you can use the response to conditionally render an error message or [`redirect`](/docs/app/api-reference/functions/redirect).

```tsx filename="app/page.tsx" switcher
export default async function Page() {
  const res = await fetch(`https://...`)
  const data = await res.json()

  if (!res.ok) {
    return 'There was an error.'
  }

  return '...'
}
```

```jsx filename="app/page.js" switcher
export default async function Page() {
  const res = await fetch(`https://...`)
  const data = await res.json()

  if (!res.ok) {
    return 'There was an error.'
  }

  return '...'
}
```

### Not found

You can call the [`notFound`](/docs/app/api-reference/functions/not-found) function within a route segment and use the [`not-found.js`](/docs/app/api-reference/file-conventions/not-found) file to show a 404 UI.

```tsx filename="app/blog/[slug]/page.tsx" switcher
import { notFound } from 'next/navigation'
import { getPostBySlug } from '@/lib/posts'

export default async function Page({
  params,
}: {
  params: Promise
}) {
  const { slug } = await params
  const post = getPostBySlug(slug)

  if (!post) {
    notFound()
  }

  return {post.title}

}
```

```jsx filename="app/blog/[slug]/page.js" switcher
import { notFound } from 'next/navigation'
import { getPostBySlug } from '@/lib/posts'

export default async function Page({ params }) {
  const { slug } = await params
  const post = getPostBySlug(slug)

  if (!post) {
    notFound()
  }

  return {post.title}

}
```

```tsx filename="app/blog/[slug]/not-found.tsx" switcher
export default function NotFound() {
  return 404 - Page Not Found

}
```

```jsx filename="app/blog/[slug]/not-found.js" switcher
export default function NotFound() {
  return 404 - Page Not Found

}
```

## Handling uncaught exceptions

Uncaught exceptions are unexpected errors that indicate bugs or issues that should not occur during the normal flow of your application. These should be handled by throwing errors, which will then be caught by error boundaries.

### Nested error boundaries

Next.js uses error boundaries to handle uncaught exceptions. Error boundaries catch errors in their child components and display a fallback UI instead of the component tree that crashed.

Create an error boundary by adding an [`error.js`](/docs/app/api-reference/file-conventions/error) file inside a route segment and exporting a React component:

```tsx filename="app/dashboard/error.tsx" switcher
'use client' // Error boundaries must be Client Components

import { useEffect } from 'react'

export default function ErrorPage({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error)
  }, [error])

  return (

      Something went wrong!

       unstable_retry()
        }
      >
        Try again

  )
}
```

```jsx filename="app/dashboard/error.js" switcher
'use client' // Error boundaries must be Client Components

import { useEffect } from 'react'

export default function ErrorPage({ error, unstable_retry }) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error)
  }, [error])

  return (

      Something went wrong!

       unstable_retry()
        }
      >
        Try again

  )
}
```

Errors will bubble up to the nearest parent error boundary. This allows for granular error handling by placing `error.tsx` files at different levels in the [route hierarchy](/docs/app/getting-started/project-structure#component-hierarchy).

![Nested Error Component Hierarchy](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/nested-error-component-hierarchy.png)

For component-level error recovery, the [`unstable_catchError`](/docs/app/api-reference/functions/catchError) function lets you create error boundaries that can wrap any part of your component tree:

```tsx filename="app/custom-error-boundary.tsx" switcher
'use client'

import { unstable_catchError as catchError, type ErrorInfo } from 'next/error'

function ErrorFallback(
  props: { title: string },
  { error, unstable_retry }: ErrorInfo
) {
  return (

      {props.title}

      {error.message}

       unstable_retry()}>Try again

  )
}

export default catchError(ErrorFallback)
```

```jsx filename="app/custom-error-boundary.js" switcher
'use client'

import { unstable_catchError as catchError } from 'next/error'

function ErrorFallback(props, { error, unstable_retry }) {
  return (

      {props.title}

      {error.message}

       unstable_retry()}>Try again

  )
}

export default catchError(ErrorFallback)
```

Then use the returned component as a wrapper in any layout or page:

```tsx filename="app/some-component.tsx" switcher
import ErrorBoundary from './custom-error-boundary'

export default function Component({ children }: { children: React.ReactNode }) {
  return {children}
}
```

```jsx filename="app/some-component.js" switcher
import ErrorBoundary from './custom-error-boundary'

export default function Component({ children }) {
  return {children}
}
```

Error boundaries don't catch errors inside event handlers. They're designed to catch errors [during rendering](https://react.dev/reference/react/Component#static-getderivedstatefromerror) to show a **fallback UI** instead of crashing the whole app.

In general, errors in event handlers or async code aren’t handled by error boundaries because they run after rendering.

To handle these cases, catch the error manually and store it using `useState` or `useReducer`, then update the UI to inform the user.

```tsx
'use client'

import { useState } from 'react'

export function Button() {
  const [error, setError] = useState(null)

  const handleClick = () => {
    try {
      // do some work that might fail
      throw new Error('Exception')
    } catch (reason) {
      setError(reason)
    }
  }

  if (error) {
    /* render fallback UI */
  }

  return (

      Click me

  )
}
```

Note that unhandled errors inside `startTransition` from `useTransition`, will bubble up to the nearest error boundary.

```tsx
'use client'

import { useTransition } from 'react'

export function Button() {
  const [pending, startTransition] = useTransition()

  const handleClick = () =>
    startTransition(() => {
      throw new Error('Exception')
    })

  return (

      Click me

  )
}
```

### Global errors

While less common, you can handle errors in the root layout using the [`global-error.js`](/docs/app/api-reference/file-conventions/error#global-error) file, located in the root app directory, even when leveraging [internationalization](/docs/app/guides/internationalization). Global error UI must define its own `` and `` tags, since it is replacing the root layout or template when active.

```tsx filename="app/global-error.tsx" switcher
'use client' // Error boundaries must be Client Components

export default function GlobalError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  return (
    // global-error must include html and body tags

        Something went wrong!

         unstable_retry()}>Try again

  )
}
```

```jsx filename="app/global-error.js" switcher
'use client' // Error boundaries must be Client Components

export default function GlobalError({ error, unstable_retry }) {
  return (
    // global-error must include html and body tags

        Something went wrong!

         unstable_retry()}>Try again

  )
}
```
## API Reference

Learn more about the features mentioned in this page by reading the API Reference.

- [redirect](/docs/app/api-reference/functions/redirect)
  - API Reference for the redirect function.
- [error.js](/docs/app/api-reference/file-conventions/error)
  - API reference for the error.js special file.
- [unstable_catchError](/docs/app/api-reference/functions/catchError)
  - API Reference for the unstable_catchError function.
- [notFound](/docs/app/api-reference/functions/not-found)
  - API Reference for the notFound function.
- [not-found.js](/docs/app/api-reference/file-conventions/not-found)
  - API reference for the not-found.js file.

---
title: CSS
description: Learn about the different ways to add CSS to your application, including Tailwind CSS, CSS Modules, Global CSS, and more.
url: "https://nextjs.org/docs/app/getting-started/css"
version: 16.2.6
---

# CSS

Next.js provides several ways to style your application using CSS, including:

* [Tailwind CSS](#tailwind-css)
* [CSS Modules](#css-modules)
* [Global CSS](#global-css)
* [External Stylesheets](#external-stylesheets)
* [Sass](/docs/app/guides/sass)
* [CSS-in-JS](/docs/app/guides/css-in-js)

## Tailwind CSS

[Tailwind CSS](https://tailwindcss.com/) is a utility-first CSS framework that provides low-level utility classes to build custom designs.

Install Tailwind CSS:

```bash package="pnpm"
pnpm add -D tailwindcss @tailwindcss/postcss
```

```bash package="npm"
npm install -D tailwindcss @tailwindcss/postcss
```

```bash package="yarn"
yarn add -D tailwindcss @tailwindcss/postcss
```

```bash package="bun"
bun add -D tailwindcss @tailwindcss/postcss
```

Add the PostCSS plugin to your `postcss.config.mjs` file:

```js filename="postcss.config.mjs"
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
}
```

Import Tailwind in your global CSS file:

```css filename="app/globals.css"
@import 'tailwindcss';
```

Import the CSS file in your root layout:

```tsx filename="app/layout.tsx" switcher
import './globals.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (

      {children}

  )
}
```

```jsx filename="app/layout.js" switcher
import './globals.css'

export default function RootLayout({ children }) {
  return (

      {children}

  )
}
```

Now you can start using Tailwind's utility classes in your application:

```tsx filename="app/page.tsx" switcher
export default function Page() {
  return (

      Welcome to Next.js!

  )
}
```

```jsx filename="app/page.js" switcher
export default function Page() {
  return (

      Welcome to Next.js!

  )
}
```

> **Good to know:** If you need broader browser support for very old browsers, see the [Tailwind CSS v3 setup instructions](/docs/app/guides/tailwind-v3-css).

## CSS Modules

CSS Modules locally scope CSS by generating unique class names. This allows you to use the same class in different files without worrying about naming collisions.

To start using CSS Modules, create a new file with the extension `.module.css` and import it into any component inside the `app` directory:

```css filename="app/blog/blog.module.css"
.blog {
  padding: 24px;
}
```

```tsx filename="app/blog/page.tsx" switcher
import styles from './blog.module.css'

export default function Page() {
  return
}
```

```jsx filename="app/blog/page.js" switcher
import styles from './blog.module.css'

export default function Page() {
  return
}
```

## Global CSS

You can use global CSS to apply styles across your application.

Create a `app/global.css` file and import it in the root layout to apply the styles to **every route** in your application:

```css filename="app/global.css"
body {
  padding: 20px 20px 60px;
  max-width: 680px;
  margin: 0 auto;
}
```

```tsx filename="app/layout.tsx" switcher
// These styles apply to every route in the application
import './global.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (

      {children}

  )
}
```

```jsx filename="app/layout.js" switcher
// These styles apply to every route in the application
import './global.css'

export default function RootLayout({ children }) {
  return (

      {children}

  )
}
```

> **Good to know:** Global styles can be imported into any layout, page, or component inside the `app` directory. However, since Next.js uses React's built-in support for stylesheets to integrate with Suspense, this currently does not remove stylesheets as you navigate between routes which can lead to conflicts. We recommend using global styles for *truly* global CSS (like Tailwind's base styles), [Tailwind CSS](#tailwind-css) for component styling, and [CSS Modules](#css-modules) for custom scoped CSS when needed.

## External stylesheets

Stylesheets published by external packages can be imported anywhere in the `app` directory, including colocated components:

```tsx filename="app/layout.tsx" switcher
import 'bootstrap/dist/css/bootstrap.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (

      {children}

  )
}
```

```jsx filename="app/layout.js" switcher
import 'bootstrap/dist/css/bootstrap.css'

export default function RootLayout({ children }) {
  return (

      {children}

  )
}
```

> **Good to know:** In React 19, `` can also be used. See the [React `link` documentation](https://react.dev/reference/react-dom/components/link) for more information.

## Ordering and Merging

Next.js optimizes CSS during production builds by automatically chunking (merging) stylesheets. The **order of your CSS** depends on the **order you import styles in your code**.

For example, `base-button.module.css` will be ordered before `page.module.css` since `` is imported before `page.module.css`:

```tsx filename="page.tsx" switcher
import { BaseButton } from './base-button'
import styles from './page.module.css'

export default function Page() {
  return
}
```

```jsx filename="page.js" switcher
import { BaseButton } from './base-button'
import styles from './page.module.css'

export default function Page() {
  return
}
```

```tsx filename="base-button.tsx" switcher
import styles from './base-button.module.css'

export function BaseButton() {
  return
}
```

```jsx filename="base-button.js" switcher
import styles from './base-button.module.css'

export function BaseButton() {
  return
}
```

### Recommendations

To keep CSS ordering predictable:

* Try to contain CSS imports to a single JavaScript or TypeScript entry file
* Import global styles and Tailwind stylesheets in the root of your application.
* **Use Tailwind CSS** for most styling needs as it covers common design patterns with utility classes.
* Use CSS Modules for component-specific styles when Tailwind utilities aren't sufficient.
* Use a consistent naming convention for your CSS modules. For example, using `.module.css` over `.tsx`.
* Extract shared styles into shared components to avoid duplicate imports.
* Turn off linters or formatters that auto-sort imports like ESLint’s [`sort-imports`](https://eslint.org/docs/latest/rules/sort-imports).
* You can use the [`cssChunking`](/docs/app/api-reference/config/next-config-js/cssChunking) option in `next.config.js` to control how CSS is chunked.

## Development vs Production

* In development (`next dev`), CSS updates apply instantly with [Fast Refresh](/docs/architecture/fast-refresh).
* In production (`next build`), all CSS files are automatically concatenated into **many minified and code-split** `.css` files, ensuring the minimal amount of CSS is loaded for a route.
* CSS still loads with JavaScript disabled in production, but JavaScript is required in development for Fast Refresh.
* CSS ordering can behave differently in development, always ensure to check the build (`next build`) to verify the final CSS order.
## Next Steps

Learn more about the alternatives ways you can use CSS in your application.

- [Tailwind CSS v3](/docs/app/guides/tailwind-v3-css)
  - Style your Next.js Application using Tailwind CSS v3 for broader browser support.
- [Sass](/docs/app/guides/sass)
  - Style your Next.js application using Sass.
- [CSS-in-JS](/docs/app/guides/css-in-js)
  - Use CSS-in-JS libraries with Next.js

---
title: Image Optimization
description: Learn how to optimize images in Next.js
url: "https://nextjs.org/docs/app/getting-started/images"
version: 16.2.6
---

# Image Optimization

The Next.js [``](/docs/app/api-reference/components/image) component extends the HTML `` element to provide:

* **Size optimization:** Automatically serving correctly sized images for each device, using modern image formats like WebP.
* **Visual stability:** Preventing [layout shift](https://web.dev/articles/cls) automatically when images are loading.
* **Faster page loads:** Only loading images when they enter the viewport using native browser lazy loading, with optional blur-up placeholders.
* **Asset flexibility:** Resizing images on-demand, even images stored on remote servers.

To start using ``, import it from `next/image` and render it within your component.

```tsx filename="app/page.tsx" switcher
import Image from 'next/image'

export default function Page() {
  return
}
```

```jsx filename="app/page.js" switcher
import Image from 'next/image'

export default function Page() {
  return
}
```

The `src` property can be a [local](#local-images) or [remote](#remote-images) image.

> **🎥 Watch:** Learn more about how to use `next/image` → [YouTube (9 minutes)](https://youtu.be/IU_qq_c_lKA).

## Local images

You can store static files, like images and fonts, under a folder called [`public`](/docs/app/api-reference/file-conventions/public-folder) in the root directory. Files inside `public` can then be referenced by your code starting from the base URL (`/`).

![Folder structure showing app and public folders](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/public-folder.png)

```tsx filename="app/page.tsx" switcher
import Image from 'next/image'

export default function Page() {
  return (

  )
}
```

```jsx filename="app/page.js" switcher
import Image from 'next/image'

export default function Page() {
  return (

  )
}
```

If the image is statically imported, Next.js will automatically determine the intrinsic [`width`](/docs/app/api-reference/components/image#width-and-height) and [`height`](/docs/app/api-reference/components/image#width-and-height). These values are used to determine the image ratio and prevent [Cumulative Layout Shift](https://web.dev/articles/cls) while your image is loading.

```tsx filename="app/page.tsx" switcher
import Image from 'next/image'
import ProfileImage from './profile.png'

export default function Page() {
  return (

  )
}
```

```jsx filename="app/page.js" switcher
import Image from 'next/image'
import ProfileImage from './profile.png'

export default function Page() {
  return (

  )
}
```

### Images without static imports

If you can't use a static `import` for your images, you can use a dynamic `import()` in a Server Component to still get automatic `width`, `height`, and `blurDataURL`:

```tsx filename="app/blog/[slug]/page.tsx" switcher
import Image from 'next/image'

async function PostImage({
  imageFilename,
  alt,
}: {
  imageFilename: string
  alt: string
}) {
  const { default: image } = await import(
    `../content/blog/images/${imageFilename}`
  )
  // image contains width, height, and blurDataURL
  return
}
```

```jsx filename="app/blog/[slug]/page.js" switcher
import Image from 'next/image'

async function PostImage({ imageFilename, alt }) {
  const { default: image } = await import(
    `../content/blog/images/${imageFilename}`
  )
  // image contains width, height, and blurDataURL
  return
}
```

If you have a [path alias](https://www.typescriptlang.org/tsconfig/#paths) configured (e.g. `@/`), you can use it instead of a relative path:

```tsx
const { default: image } = await import(
  `@/content/blog/images/${imageFilename}`
)
```

The path must include a static prefix (like `../content/blog/images/`). Be as specific as possible, since **all** files matching that prefix are bundled. Only files in your specified directory are included, so external input cannot reach outside of it.

## Remote images

To use a remote image, you can provide a URL string for the `src` property.

```tsx filename="app/page.tsx" switcher
import Image from 'next/image'

export default function Page() {
  return (

  )
}
```

```jsx filename="app/page.js" switcher
import Image from 'next/image'

export default function Page() {
  return (

  )
}
```

Since Next.js does not have access to remote files during the build process, you'll need to provide the [`width`](/docs/app/api-reference/components/image#width-and-height), [`height`](/docs/app/api-reference/components/image#width-and-height) and optional [`blurDataURL`](/docs/app/api-reference/components/image#blurdataurl) props manually. The `width` and `height` are used to infer the correct aspect ratio of image and avoid layout shift from the image loading in. Alternatively, you can use the [`fill` property](/docs/app/api-reference/components/image#fill) to make the image fill the size of the parent element.

To safely allow images from remote servers, you need to define a list of supported URL patterns in [`next.config.js`](/docs/app/api-reference/config/next-config-js). Be as specific as possible to prevent malicious usage. For example, the following configuration will only allow images from a specific AWS S3 bucket:

```ts filename="next.config.ts" switcher
import type { NextConfig } from 'next'

const config: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 's3.amazonaws.com',
        port: '',
        pathname: '/my-bucket/**',
        search: '',
      },
    ],
  },
}

export default config
```

```js filename="next.config.js" switcher
module.exports = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 's3.amazonaws.com',
        port: '',
        pathname: '/my-bucket/**',
        search: '',
      },
    ],
  },
}
```
## API Reference

See the API Reference for the full feature set of Next.js Image.

- [Image Component](/docs/app/api-reference/components/image)
  - Optimize Images in your Next.js Application using the built-in `next/image` Component.

---
title: Font Optimization
description: Learn how to optimize fonts in Next.js
url: "https://nextjs.org/docs/app/getting-started/fonts"
version: 16.2.6
---

# Font Optimization

The [`next/font`](/docs/app/api-reference/components/font) module automatically optimizes your fonts and removes external network requests for improved privacy and performance.

It includes **built-in self-hosting** for any font file. This means you can optimally load web fonts with no layout shift.

To start using `next/font`, import it from [`next/font/local`](#local-fonts) or [`next/font/google`](#google-fonts), call it as a function with the appropriate options, and set the `className` of the element you want to apply the font to. For example:

```tsx filename="app/layout.tsx" highlight={1,3-5,9} switcher
import { Geist } from 'next/font/google'

const geist = Geist({
  subsets: ['latin'],
})

export default function Layout({ children }: { children: React.ReactNode }) {
  return (

      {children}

  )
}
```

```jsx filename="app/layout.js" highlight={1,3-5,9} switcher
import { Geist } from 'next/font/google'

const geist = Geist({
  subsets: ['latin'],
})

export default function Layout({ children }) {
  return (

      {children}

  )
}
```

Fonts are scoped to the component they're used in. To apply a font to your entire application, add it to the [Root Layout](/docs/app/api-reference/file-conventions/layout#root-layout).

## Google fonts

You can automatically self-host any Google Font. Fonts are included stored as static assets and served from the same domain as your deployment, meaning no requests are sent to Google by the browser when the user visits your site.

To start using a Google Font, import your chosen font from `next/font/google`:

```tsx filename="app/layout.tsx" switcher
import { Geist } from 'next/font/google'

const geist = Geist({
  subsets: ['latin'],
})

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (

      {children}

  )
}
```

```jsx filename="app/layout.js" switcher
import { Geist } from 'next/font/google'

const geist = Geist({
  subsets: ['latin'],
})

export default function RootLayout({ children }) {
  return (

      {children}

  )
}
```

We recommend using [variable fonts](https://fonts.google.com/variablefonts) for the best performance and flexibility. But if you can't use a variable font, you will need to specify a weight:

```tsx filename="app/layout.tsx" highlight={4} switcher
import { Roboto } from 'next/font/google'

const roboto = Roboto({
  weight: '400',
  subsets: ['latin'],
})

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (

      {children}

  )
}
```

```jsx filename="app/layout.js"  highlight={4} switcher
import { Roboto } from 'next/font/google'

const roboto = Roboto({
  weight: '400',
  subsets: ['latin'],
})

export default function RootLayout({ children }) {
  return (

      {children}

  )
}
```

## Local fonts

To use a local font, import the `localFont` function from `next/font/local` and specify the [`src`](/docs/app/api-reference/components/font#src) of your local font file. The path is resolved relative to the file where `localFont` is called. Fonts can be stored anywhere in the project, including the [`public`](/docs/app/api-reference/file-conventions/public-folder) folder or co-located inside the `app` folder. For example, to use a font stored in `app/fonts/`:

```tsx filename="app/layout.tsx" switcher
import localFont from 'next/font/local'

const myFont = localFont({
  src: './my-font.woff2',
})

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (

      {children}

  )
}
```

```jsx filename="app/layout.js" switcher
import localFont from 'next/font/local'

const myFont = localFont({
  src: './my-font.woff2',
})

export default function RootLayout({ children }) {
  return (

      {children}

  )
}
```

If you want to use multiple files for a single font family, `src` can be an array:

```js
const roboto = localFont({
  src: [
    {
      path: './Roboto-Regular.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: './Roboto-Italic.woff2',
      weight: '400',
      style: 'italic',
    },
    {
      path: './Roboto-Bold.woff2',
      weight: '700',
      style: 'normal',
    },
    {
      path: './Roboto-BoldItalic.woff2',
      weight: '700',
      style: 'italic',
    },
  ],
})
```
## API Reference

See the API Reference for the full feature set of Next.js Font

- [Font](/docs/app/api-reference/components/font)
  - Optimizing loading web fonts with the built-in `next/font` loaders.

---
title: Metadata and OG images
description: Learn how to add metadata to your pages and create dynamic OG images.
url: "https://nextjs.org/docs/app/getting-started/metadata-and-og-images"
version: 16.2.6
---

# Metadata and OG images

The Metadata APIs can be used to define your application metadata for improved SEO and web shareability and include:

1. [The static `metadata` object](#static-metadata)
2. [The dynamic `generateMetadata` function](#generated-metadata)
3. Special [file conventions](/docs/app/api-reference/file-conventions/metadata) that can be used to add static or dynamically generated [favicons](#favicons) and [OG images](#static-open-graph-images).

With all the options above, Next.js will automatically generate the relevant `` tags for your page, which can be inspected in the browser's developer tools.

The `metadata` object and `generateMetadata` function exports are only supported in Server Components.

## Default fields

There are two default `meta` tags that are always added even if a route doesn't define metadata:

* The [meta charset tag](https://developer.mozilla.org/docs/Web/HTML/Element/meta#attr-charset) sets the character encoding for the website.
* The [meta viewport tag](https://developer.mozilla.org/docs/Web/HTML/Viewport_meta_tag) sets the viewport width and scale for the website to adjust for different devices.

```html

```

The other metadata fields can be defined with the `Metadata` object (for [static metadata](#static-metadata)) or the `generateMetadata` function (for [generated metadata](#generated-metadata)).

## Static metadata

To define static metadata, export a [`Metadata` object](/docs/app/api-reference/functions/generate-metadata#metadata-object) from a static [`layout.js`](/docs/app/api-reference/file-conventions/layout) or [`page.js`](/docs/app/api-reference/file-conventions/page) file. For example, to add a title and description to the blog route:

```tsx filename="app/blog/layout.tsx" switcher
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'My Blog',
  description: '...',
}

export default function Layout() {}
```

```jsx filename="app/blog/layout.js" switcher
export const metadata = {
  title: 'My Blog',
  description: '...',
}

export default function Layout() {}
```

You can view a full list of available options, in the [`generateMetadata` documentation](/docs/app/api-reference/functions/generate-metadata#metadata-fields).

## Generated metadata

You can use [`generateMetadata`](/docs/app/api-reference/functions/generate-metadata) function to `fetch` metadata that depends on data. For example, to fetch the title and description for a specific blog post:

```tsx filename="app/blog/[slug]/page.tsx" switcher
import type { Metadata, ResolvingMetadata } from 'next'

type Props = {
  params: Promise
  searchParams: Promise
}

export async function generateMetadata(
  { params, searchParams }: Props,
  parent: ResolvingMetadata
): Promise {
  const slug = (await params).slug

  // fetch post information
  const post = await fetch(`https://api.vercel.app/blog/${slug}`).then((res) =>
    res.json()
  )

  return {
    title: post.title,
    description: post.description,
  }
}

export default function Page({ params, searchParams }: Props) {}
```

```jsx filename="app/blog/[slug]/page.js" switcher
export async function generateMetadata({ params, searchParams }, parent) {
  const slug = (await params).slug

  // fetch post information
  const post = await fetch(`https://api.vercel.app/blog/${slug}`).then((res) =>
    res.json()
  )

  return {
    title: post.title,
    description: post.description,
  }
}

export default function Page({ params, searchParams }) {}
```

### Streaming metadata

For dynamically rendered pages, Next.js streams metadata separately, injecting it into the HTML once `generateMetadata` resolves, without blocking UI rendering.

Streaming metadata improves perceived performance by allowing visual content to stream first.

Streaming metadata is **disabled for bots and crawlers** that expect metadata to be in the `` tag (e.g. `Twitterbot`, `Slackbot`, `Bingbot`). These are detected by using the User Agent header from the incoming request.

You can customize or **disable** streaming metadata completely, with the [`htmlLimitedBots`](/docs/app/api-reference/config/next-config-js/htmlLimitedBots#disabling) option in your Next.js config file.

Prerendered pages don’t use streaming since metadata is resolved at build time.

Learn more about [streaming metadata](/docs/app/api-reference/functions/generate-metadata#streaming-metadata).

### Memoizing data requests

There may be cases where you need to fetch the **same** data for metadata and the page itself. To avoid duplicate requests, you can use React's [`cache` function](https://react.dev/reference/react/cache) to memoize the return value and only fetch the data once. For example, to fetch the blog post information for both the metadata and the page:

```ts filename="app/lib/data.ts" highlight={5} switcher
import { cache } from 'react'
import { db } from '@/app/lib/db'

// getPost will be used twice, but execute only once
export const getPost = cache(async (slug: string) => {
  const res = await db.query.posts.findFirst({ where: eq(posts.slug, slug) })
  return res
})
```

```js filename="app/lib/data.js" highlight={5} switcher
import { cache } from 'react'
import { db } from '@/app/lib/db'

// getPost will be used twice, but execute only once
export const getPost = cache(async (slug) => {
  const res = await db.query.posts.findFirst({ where: eq(posts.slug, slug) })
  return res
})
```

```tsx filename="app/blog/[slug]/page.tsx" switcher
import { getPost } from '@/app/lib/data'

export async function generateMetadata({
  params,
}: {
  params: { slug: string }
}) {
  const post = await getPost(params.slug)
  return {
    title: post.title,
    description: post.description,
  }
}

export default async function Page({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug)
  return {post.title}

}
```

```jsx filename="app/blog/[slug]/page.js" switcher
import { getPost } from '@/app/lib/data'

export async function generateMetadata({ params }) {
  const post = await getPost(params.slug)
  return {
    title: post.title,
    description: post.description,
  }
}

export default async function Page({ params }) {
  const post = await getPost(params.slug)
  return {post.title}

}
```

## File-based metadata

The following special files are available for metadata:

* [favicon.ico, apple-icon.jpg, and icon.jpg](/docs/app/api-reference/file-conventions/metadata/app-icons)
* [opengraph-image.jpg and twitter-image.jpg](/docs/app/api-reference/file-conventions/metadata/opengraph-image)
* [robots.txt](/docs/app/api-reference/file-conventions/metadata/robots)
* [sitemap.xml](/docs/app/api-reference/file-conventions/metadata/sitemap)

You can use these for static metadata, or you can programmatically generate these files with code.

## Favicons

Favicons are small icons that represent your site in bookmarks and search results. To add a favicon to your application, create a `favicon.ico` and add to the root of the app folder.

![Favicon Special File inside the App Folder with sibling layout and page files](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/favicon-ico.png)

> You can also programmatically generate favicons using code. See the [favicon docs](/docs/app/api-reference/file-conventions/metadata/app-icons) for more information.

## Static Open Graph images

Open Graph (OG) images are images that represent your site in social media. To add a static OG image to your application, create a `opengraph-image.jpg` file in the root of the app folder.

![OG image special file inside the App folder with sibling layout and page files](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/opengraph-image.png)

You can also add OG images for specific routes by creating a `opengraph-image.jpg` deeper down the folder structure. For example, to create an OG image specific to the `/blog` route, add a `opengraph-image.jpg` file inside the `blog` folder.

![OG image special file inside the blog folder](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/opengraph-image-blog.png)

The more specific image will take precedence over any OG images above it in the folder structure.

> Other image formats such as `jpeg`, `png`, and `gif` are also supported. See the [Open Graph Image docs](/docs/app/api-reference/file-conventions/metadata/opengraph-image) for more information.

## Generated Open Graph images

The [`ImageResponse` constructor](/docs/app/api-reference/functions/image-response) allows you to generate dynamic images using JSX and CSS. This is useful for OG images that depend on data.

For example, to generate a unique OG image for each blog post, add a `opengraph-image.tsx` file inside the `blog` folder, and import the `ImageResponse` constructor from `next/og`:

```tsx filename="app/blog/[slug]/opengraph-image.tsx" switcher
import { ImageResponse } from 'next/og'
import { getPost } from '@/app/lib/data'

// Image metadata
export const size = {
  width: 1200,
  height: 630,
}

export const contentType = 'image/png'

// Image generation
export default async function Image({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug)

  return new ImageResponse(
    (
      // ImageResponse JSX element

        {post.title}

    )
  )
}
```

```jsx filename="app/blog/[slug]/opengraph-image.js" switcher
import { ImageResponse } from 'next/og'
import { getPost } from '@/app/lib/data'

// Image metadata
export const size = {
  width: 1200,
  height: 630,
}

export const contentType = 'image/png'

// Image generation
export default async function Image({ params }) {
  const post = await getPost(params.slug)

  return new ImageResponse(
    (
      // ImageResponse JSX element

        {post.title}

    )
  )
}
```

`ImageResponse` supports common CSS properties including flexbox and absolute positioning, custom fonts, text wrapping, centering, and nested images. [See the full list of supported CSS properties](/docs/app/api-reference/functions/image-response).

> **Good to know**:
>
> * Examples are available in the [Vercel OG Playground](https://og-playground.vercel.app/).
> * `ImageResponse` uses [`@vercel/og`](https://vercel.com/docs/og-image-generation), [`satori`](https://github.com/vercel/satori), and `resvg` to convert HTML and CSS into PNG.
> * Only flexbox and a subset of CSS properties are supported. Advanced layouts (e.g. `display: grid`) will not work.
## API Reference

Learn more about the Metadata APIs mentioned in this page.

- [generateMetadata](/docs/app/api-reference/functions/generate-metadata)
  - Learn how to add Metadata to your Next.js application for improved search engine optimization (SEO) and web shareability.
- [generateViewport](/docs/app/api-reference/functions/generate-viewport)
  - API Reference for the generateViewport function.
- [ImageResponse](/docs/app/api-reference/functions/image-response)
  - API Reference for the ImageResponse constructor.
- [Metadata Files](/docs/app/api-reference/file-conventions/metadata)
  - API documentation for the metadata file conventions.
- [favicon, icon, and apple-icon](/docs/app/api-reference/file-conventions/metadata/app-icons)
  - API Reference for the Favicon, Icon and Apple Icon file conventions.
- [opengraph-image and twitter-image](/docs/app/api-reference/file-conventions/metadata/opengraph-image)
  - API Reference for the Open Graph Image and Twitter Image file conventions.
- [robots.txt](/docs/app/api-reference/file-conventions/metadata/robots)
  - API Reference for robots.txt file.
- [sitemap.xml](/docs/app/api-reference/file-conventions/metadata/sitemap)
  - API Reference for the sitemap.xml file.
- [htmlLimitedBots](/docs/app/api-reference/config/next-config-js/htmlLimitedBots)
  - Specify a list of user agents that should receive blocking metadata.

---
title: Route Handlers
description: Learn how to use Route Handlers
url: "https://nextjs.org/docs/app/getting-started/route-handlers"
version: 16.2.6
---

# Route Handlers

## Route Handlers

Route Handlers allow you to create custom request handlers for a given route using the Web [Request](https://developer.mozilla.org/docs/Web/API/Request) and [Response](https://developer.mozilla.org/docs/Web/API/Response) APIs.

![Route.js Special File](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/route-special-file.png)

> **Good to know**: Route Handlers are only available inside the `app` directory. They are the equivalent of [API Routes](/docs/pages/building-your-application/routing/api-routes) inside the `pages` directory meaning you **do not** need to use API Routes and Route Handlers together.

### Convention

Route Handlers are defined in a [`route.js|ts` file](/docs/app/api-reference/file-conventions/route) inside the `app` directory:

```ts filename="app/api/route.ts" switcher
export async function GET(request: Request) {}
```

```js filename="app/api/route.js" switcher
export async function GET(request) {}
```

Route Handlers can be nested anywhere inside the `app` directory, similar to `page.js` and `layout.js`. But there **cannot** be a `route.js` file at the same route segment level as `page.js`.

### Supported HTTP Methods

The following [HTTP methods](https://developer.mozilla.org/docs/Web/HTTP/Methods) are supported: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, and `OPTIONS`. If an unsupported method is called, Next.js will return a `405 Method Not Allowed` response.

### Extended `NextRequest` and `NextResponse` APIs

In addition to supporting the native [Request](https://developer.mozilla.org/docs/Web/API/Request) and [Response](https://developer.mozilla.org/docs/Web/API/Response) APIs, Next.js extends them with [`NextRequest`](/docs/app/api-reference/functions/next-request) and [`NextResponse`](/docs/app/api-reference/functions/next-response) to provide convenient helpers for advanced use cases.

### Caching

Route Handlers are not cached by default. You can, however, opt into caching for `GET` methods. Other supported HTTP methods are **not** cached. To cache a `GET` method, use a [route config option](/docs/app/guides/caching-without-cache-components#dynamic) such as `export const dynamic = 'force-static'` in your Route Handler file.

```ts filename="app/items/route.ts" switcher
export const dynamic = 'force-static'

export async function GET() {
  const res = await fetch('https://data.mongodb-api.com/...', {
    headers: {
      'Content-Type': 'application/json',
      'API-Key': process.env.DATA_API_KEY,
    },
  })
  const data = await res.json()

  return Response.json({ data })
}
```

```js filename="app/items/route.js" switcher
export const dynamic = 'force-static'

export async function GET() {
  const res = await fetch('https://data.mongodb-api.com/...', {
    headers: {
      'Content-Type': 'application/json',
      'API-Key': process.env.DATA_API_KEY,
    },
  })
  const data = await res.json()

  return Response.json({ data })
}
```

> **Good to know**: Other supported HTTP methods are **not** cached, even if they are placed alongside a `GET` method that is cached, in the same file.

#### With Cache Components

When [Cache Components](/docs/app/getting-started/caching) is enabled, `GET` Route Handlers follow the same model as normal UI routes in your application. They run at request time by default, can be prerendered when they don't access uncached or runtime data, and you can use `use cache` to include uncached data in the static response.

**Static example** - doesn't access uncached or runtime data, so it will be prerendered at build time:

```tsx filename="app/api/project-info/route.ts"
export async function GET() {
  return Response.json({
    projectName: 'Next.js',
  })
}
```

**Dynamic example** - accesses non-deterministic operations. During the build, prerendering stops when `Math.random()` is called, deferring to request-time rendering:

```tsx filename="app/api/random-number/route.ts"
export async function GET() {
  return Response.json({
    randomNumber: Math.random(),
  })
}
```

**Runtime data example** - accesses request-specific data. Prerendering terminates when runtime APIs like `headers()` are called:

```tsx filename="app/api/user-agent/route.ts"
import { headers } from 'next/headers'

export async function GET() {
  const headersList = await headers()
  const userAgent = headersList.get('user-agent')

  return Response.json({ userAgent })
}
```

> **Good to know**: Prerendering stops if the `GET` handler accesses network requests, database queries, async file system operations, request object properties (like `req.url`, `request.headers`, `request.cookies`, `request.body`), runtime APIs like [`cookies()`](/docs/app/api-reference/functions/cookies), [`headers()`](/docs/app/api-reference/functions/headers), [`connection()`](/docs/app/api-reference/functions/connection), or non-deterministic operations.

**Cached example** - accesses uncached data (database query) but caches it with `use cache`, allowing it to be included in the prerendered response:

```tsx filename="app/api/products/route.ts"
import { cacheLife } from 'next/cache'

export async function GET() {
  const products = await getProducts()
  return Response.json(products)
}

async function getProducts() {
  'use cache'
  cacheLife('hours')

  return await db.query('SELECT * FROM products')
}
```

> **Good to know**: `use cache` cannot be used directly inside a Route Handler body; extract it to a helper function. Cached responses revalidate according to `cacheLife` when a new request arrives.

### Special Route Handlers

Special Route Handlers like [`sitemap.ts`](/docs/app/api-reference/file-conventions/metadata/sitemap), [`opengraph-image.tsx`](/docs/app/api-reference/file-conventions/metadata/opengraph-image), and [`icon.tsx`](/docs/app/api-reference/file-conventions/metadata/app-icons), and other [metadata files](/docs/app/api-reference/file-conventions/metadata) remain static by default unless they use Request-time APIs or dynamic config options.

### Route Resolution

You can consider a `route` the lowest level routing primitive.

* They **do not** participate in layouts or client-side navigations like `page`.
* There **cannot** be a `route.js` file at the same route as `page.js`.

| Page                 | Route              | Result                       |
| -------------------- | ------------------ | ---------------------------- |
| `app/page.js`        | `app/route.js`     | ✗ Conflict |
| `app/page.js`        | `app/api/route.js` | ✓ Valid    |
| `app/[user]/page.js` | `app/api/route.js` | ✓ Valid    |

Each `route.js` or `page.js` file takes over all HTTP verbs for that route.

```ts filename="app/page.ts" switcher
export default function Page() {
  return Hello, Next.js!

}

// Conflict
// `app/route.ts`
export async function POST(request: Request) {}
```

```js filename="app/page.js" switcher
export default function Page() {
  return Hello, Next.js!

}

// Conflict
// `app/route.js`
export async function POST(request) {}
```

Read more about how Route Handlers [complement your frontend application](/docs/app/guides/backend-for-frontend), or explore the Route Handlers [API Reference](/docs/app/api-reference/file-conventions/route).

### Route Context Helper

In TypeScript, you can type the `context` parameter for Route Handlers with the globally available [`RouteContext`](/docs/app/api-reference/file-conventions/route#route-context-helper) helper:

```ts filename="app/users/[id]/route.ts" switcher
import type { NextRequest } from 'next/server'

export async function GET(_req: NextRequest, ctx: RouteContext) {
  const { id } = await ctx.params
  return Response.json({ id })
}
```

> **Good to know**
>
> * Types are generated during `next dev`, `next build` or `next typegen`.
## API Reference

Learn more about Route Handlers

- [route.js](/docs/app/api-reference/file-conventions/route)
  - API reference for the route.js special file.
- [Backend for Frontend](/docs/app/guides/backend-for-frontend)
  - Learn how to use Next.js as a backend framework

---
title: Proxy
description: Learn how to use Proxy
url: "https://nextjs.org/docs/app/getting-started/proxy"
version: 16.2.6
---

# Proxy

## Proxy

> **Good to know**: Starting with Next.js 16, Middleware is now called Proxy to better reflect its purpose. The functionality remains the same.

Proxy allows you to run code before a request is completed. Then, based on the incoming request, you can modify the response by rewriting, redirecting, modifying the request or response headers, or responding directly.

### Use cases

Some common scenarios where Proxy is effective include:

* Modifying headers for all pages or a subset of pages
* Rewriting to different pages based on A/B tests or experiments
* Programmatic redirects based on incoming request properties

For simple redirects, consider using the [`redirects`](/docs/app/api-reference/config/next-config-js/redirects) configuration in `next.config.ts` first. Proxy should be used when you need access to request data or more complex logic.

Proxy is *not* intended for slow data fetching. While Proxy can be helpful for [optimistic checks](/docs/app/guides/authentication#optimistic-checks-with-proxy-optional) such as permission-based redirects, it should not be used as a full session management or authorization solution.

Using fetch with `options.cache`, `options.next.revalidate`, or `options.next.tags`, has no effect in Proxy.

### Convention

Create a `proxy.ts` (or `.js`) file in the project root, or inside `src` if applicable, so that it is located at the same level as `pages` or `app`.

> **Note**: While only one `proxy.ts` file is supported per project, you can still organize your proxy logic into modules. Break out proxy functionalities into separate `.ts` or `.js` files and import them into your main `proxy.ts` file. This allows for cleaner management of route-specific proxy, aggregated in the `proxy.ts` for centralized control. By enforcing a single proxy file, it simplifies configuration, prevents potential conflicts, and optimizes performance by avoiding multiple proxy layers.

### Example

You can export your proxy function as either a default export or a named `proxy` export:

```ts filename="proxy.ts" switcher
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// This function can be marked `async` if using `await` inside
export function proxy(request: NextRequest) {
  return NextResponse.redirect(new URL('/home', request.url))
}

// Alternatively, you can use a default export:
// export default function proxy(request: NextRequest) { ... }

export const config = {
  matcher: '/about/:path*',
}
```

```js filename="proxy.js" switcher
import { NextResponse } from 'next/server'

// This function can be marked `async` if using `await` inside
export function proxy(request) {
  return NextResponse.redirect(new URL('/home', request.url))
}

// Alternatively, you can use a default export:
// export default function proxy(request) { ... }

export const config = {
  matcher: '/about/:path*',
}
```

The `matcher` config allows you to filter Proxy to run on specific paths. See the [Matcher](/docs/app/api-reference/file-conventions/proxy#matcher) documentation for more details on path matching.

Read more about [using `proxy`](/docs/app/guides/backend-for-frontend#proxy), or refer to the `proxy` [API reference](/docs/app/api-reference/file-conventions/proxy).
## API Reference

Learn more about Proxy

- [proxy.js](/docs/app/api-reference/file-conventions/proxy)
  - API reference for the proxy.js file.
- [Backend for Frontend](/docs/app/guides/backend-for-frontend)
  - Learn how to use Next.js as a backend framework

---
title: Deploying
description: Learn how to deploy your Next.js application.
url: "https://nextjs.org/docs/app/getting-started/deploying"
version: 16.2.6
---

# Deploying

Next.js can be deployed as a Node.js server, Docker container, static export, or adapted to run on different platforms.

| Deployment Option                | Feature Support                                                     |
| -------------------------------- | ------------------------------------------------------------------- |
| [Node.js server](#nodejs-server) | All                                                                 |
| [Docker container](#docker)      | All                                                                 |
| [Static export](#static-export)  | Limited                                                             |
| [Adapters](#adapters)            | Varies ([verified](#verified-adapters) adapters run the test suite) |

## Node.js server

Next.js can be deployed to any provider that supports Node.js. Ensure your `package.json` has the `"build"` and `"start"` scripts:

```json filename="package.json"
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

Then, run `npm run build` to build your application and `npm run start` to start the Node.js server. This server supports all Next.js features. If needed, you can also eject to a [custom server](/docs/app/guides/custom-server).

Node.js deployments support all Next.js features. Learn how to [configure them](/docs/app/guides/self-hosting) for your infrastructure.

### Templates

* [Flightcontrol](https://github.com/nextjs/deploy-flightcontrol)
* [Railway](https://github.com/nextjs/deploy-railway)
* [Replit](https://github.com/nextjs/deploy-replit)
* [Hostinger](https://github.com/hostinger/deploy-nextjs)

## Docker

Next.js can be deployed to any provider that supports [Docker](https://www.docker.com/) containers. This includes container orchestrators like Kubernetes or a cloud provider that runs Docker. For containerization best practices, see the [Docker guide for React.js](https://docs.docker.com/guides/reactjs/).

Docker deployments support all Next.js features. Learn how to [configure them](/docs/app/guides/self-hosting) for your infrastructure.

> **Note for development:** While Docker is excellent for production deployments, consider using local development (`npm run dev`) instead of Docker during development on Mac and Windows for better performance. [Learn more about optimizing local development](/docs/app/guides/local-development).

### Templates

The following examples demonstrate best practices for containerizing Next.js applications:

* [Docker Standalone Output](https://github.com/vercel/next.js/tree/canary/examples/with-docker) - Deploy a Next.js application using `output: "standalone"` to generate a minimal, production-ready Docker image with only the required runtime files and dependencies.
* [Docker Export Output](https://github.com/vercel/next.js/tree/canary/examples/with-docker-export-output) - Deploy a fully static Next.js application using `output: "export"` to generate optimized HTML files that can be served from a lightweight container or any static hosting environment.
* [Docker Multi-Environment](https://github.com/vercel/next.js/tree/canary/examples/with-docker-multi-env) - Manage separate Docker configurations for development, staging, and production environments with different environment variables.

Additionally, hosting providers offer guidance on deploying Next.js:

* [DigitalOcean](https://github.com/nextjs/deploy-digitalocean)
* [Fly.io](https://github.com/nextjs/deploy-fly)
* [Google Cloud Run](https://github.com/nextjs/deploy-google-cloud-run)
* [Render](https://github.com/nextjs/deploy-render)
* [SST](https://github.com/nextjs/deploy-sst)

## Static export

Next.js enables starting as a static site or [Single-Page Application (SPA)](/docs/app/guides/single-page-applications), then later optionally upgrading to use features that require a server.

Since Next.js supports [static exports](/docs/app/guides/static-exports), it can be deployed and hosted on any web server that can serve HTML/CSS/JS static assets. This includes tools like AWS S3, Nginx, or Apache.

Running as a [static export](/docs/app/guides/static-exports) **does not** support Next.js features that require a server. [Learn more](/docs/app/guides/static-exports#unsupported-features).

### Templates

* [GitHub Pages](https://github.com/nextjs/deploy-github-pages)

## Adapters

Next.js can be adapted to run on different platforms to support their infrastructure capabilities. The [Deployment Adapter API](/docs/app/api-reference/config/next-config-js/adapterPath) lets platforms customize how Next.js applications are built and deployed.

### Verified Adapters

Verified adapters are open source, run the full [Next.js compatibility test suite](/docs/app/api-reference/adapters/testing-adapters), and are hosted under the [Next.js GitHub organization](https://github.com/nextjs). The Next.js team coordinates testing with these platforms before major releases. Publicly visible test results for each adapter are coming soon. [Learn more about verified adapters](/docs/app/guides/deploying-to-platforms#verified-adapters).

* [Vercel](https://vercel.com/docs/frameworks/nextjs)
* [Bun](https://bun.com/docs/guides/ecosystem/nextjs)

Cloudflare and Netlify are working on verified adapters built on the Adapter API. In the meantime, they offer their own Next.js integrations (see below).

### Other Platforms

The following platforms offer their own Next.js integrations. These are not built on the public [Adapter API](/docs/app/api-reference/config/next-config-js/adapterPath) and are not verified by the Next.js team, so feature support and compatibility may vary. Refer to each provider's documentation for details:

* [Appwrite Sites](https://appwrite.io/docs/products/sites/quick-start/nextjs)
* [AWS Amplify Hosting](https://docs.amplify.aws/nextjs/start/quickstart/nextjs-app-router-client-components)
* [Cloudflare](https://developers.cloudflare.com/workers/frameworks/framework-guides/nextjs)
* [Deno Deploy](https://docs.deno.com/examples/next_tutorial)
* [Firebase App Hosting](https://firebase.google.com/docs/app-hosting/get-started)
* [Netlify](https://docs.netlify.com/frameworks/next-js/overview/#next-js-support-on-netlify)

For details on which Next.js features require specific platform capabilities, see [Deploying to Platforms](/docs/app/guides/deploying-to-platforms).

---
title: Upgrading
description: Learn how to upgrade your Next.js application to the latest version or canary.
url: "https://nextjs.org/docs/app/getting-started/upgrading"
version: 16.2.6
---

# Upgrading

## Latest version

To update to the latest version of Next.js, you can use the `upgrade` command:

```bash package="pnpm"
pnpm next upgrade
```

```bash package="npm"
npx next upgrade
```

```bash package="yarn"
yarn next upgrade
```

```bash package="bun"
bunx next upgrade
```

Versions before Next.js 16.1.0 do not support the `upgrade` command and need to use a separate package instead:

```bash filename="Terminal"
npx @next/codemod@canary upgrade latest
```

If you prefer to upgrade manually, install the latest Next.js and React versions:

```bash package="pnpm"
pnpm i next@latest react@latest react-dom@latest eslint-config-next@latest
```

```bash package="npm"
npm i next@latest react@latest react-dom@latest eslint-config-next@latest
```

```bash package="yarn"
yarn add next@latest react@latest react-dom@latest eslint-config-next@latest
```

```bash package="bun"
bun add next@latest react@latest react-dom@latest eslint-config-next@latest
```

## Canary version

To update to the latest canary, make sure you're on the latest version of Next.js and everything is working as expected. Then, run the following command:

```bash package="pnpm"
pnpm add next@canary
```

```bash package="npm"
npm i next@canary
```

```bash package="yarn"
yarn add next@canary
```

```bash package="bun"
bun add next@canary
```

### Features available in canary

The following features are currently available in canary:

**Authentication**:

* [`forbidden`](/docs/app/api-reference/functions/forbidden)
* [`unauthorized`](/docs/app/api-reference/functions/unauthorized)
* [`forbidden.js`](/docs/app/api-reference/file-conventions/forbidden)
* [`unauthorized.js`](/docs/app/api-reference/file-conventions/unauthorized)
* [`authInterrupts`](/docs/app/api-reference/config/next-config-js/authInterrupts)
## Version guides

See the version guides for in-depth upgrade instructions.

- [Version 16](/docs/app/guides/upgrading/version-16)
  - Upgrade your Next.js Application from Version 15 to 16.
- [Version 15](/docs/app/guides/upgrading/version-15)
  - Upgrade your Next.js Application from Version 14 to 15.
- [Version 14](/docs/app/guides/upgrading/version-14)
  - Upgrade your Next.js Application from Version 13 to 14.

---
title: Guides
description: Learn how to implement common patterns and real-world use cases using Next.js
url: "https://nextjs.org/docs/app/guides"
version: 16.2.6
---

# Guides

 - [AI Coding Agents](/docs/app/guides/ai-agents)
 - [Analytics](/docs/app/guides/analytics)
 - [Authentication](/docs/app/guides/authentication)
 - [Backend for Frontend](/docs/app/guides/backend-for-frontend)
 - [Caching (Previous Model)](/docs/app/guides/caching-without-cache-components)
 - [CDN Caching](/docs/app/guides/cdn-caching)
 - [CI Build Caching](/docs/app/guides/ci-build-caching)
 - [Content Security Policy](/docs/app/guides/content-security-policy)
 - [CSS-in-JS](/docs/app/guides/css-in-js)
 - [Custom Server](/docs/app/guides/custom-server)
 - [Data Security](/docs/app/guides/data-security)
 - [Debugging](/docs/app/guides/debugging)
 - [Deploying to Platforms](/docs/app/guides/deploying-to-platforms)
 - [Draft Mode](/docs/app/guides/draft-mode)
 - [Environment Variables](/docs/app/guides/environment-variables)
 - [Forms](/docs/app/guides/forms)
 - [How Revalidation Works](/docs/app/guides/how-revalidation-works)
 - [ISR](/docs/app/guides/incremental-static-regeneration)
 - [Instrumentation](/docs/app/guides/instrumentation)
 - [Internationalization](/docs/app/guides/internationalization)
 - [JSON-LD](/docs/app/guides/json-ld)
 - [Lazy Loading](/docs/app/guides/lazy-loading)
 - [Development Environment](/docs/app/guides/local-development)
 - [Next.js MCP Server](/docs/app/guides/mcp)
 - [MDX](/docs/app/guides/mdx)
 - [Memory Usage](/docs/app/guides/memory-usage)
 - [Migrating](/docs/app/guides/migrating)
 - [Migrating to Cache Components](/docs/app/guides/migrating-to-cache-components)
 - [Multi-tenant](/docs/app/guides/multi-tenant)
 - [Multi-zones](/docs/app/guides/multi-zones)
 - [OpenTelemetry](/docs/app/guides/open-telemetry)
 - [Package Bundling](/docs/app/guides/package-bundling)
 - [PPR Platform Guide](/docs/app/guides/ppr-platform-guide)
 - [Prefetching](/docs/app/guides/prefetching)
 - [Preserving UI state](/docs/app/guides/preserving-ui-state)
 - [Preventing Flash](/docs/app/guides/preventing-flash-before-hydration)
 - [Production](/docs/app/guides/production-checklist)
 - [PWAs](/docs/app/guides/progressive-web-apps)
 - [Public pages](/docs/app/guides/public-static-pages)
 - [Redirecting](/docs/app/guides/redirecting)
 - [Rendering Philosophy](/docs/app/guides/rendering-philosophy)
 - [Sass](/docs/app/guides/sass)
 - [Scripts](/docs/app/guides/scripts)
 - [Self-Hosting](/docs/app/guides/self-hosting)
 - [SPAs](/docs/app/guides/single-page-applications)
 - [Static Exports](/docs/app/guides/static-exports)
 - [Streaming](/docs/app/guides/streaming)
 - [Tailwind CSS v3](/docs/app/guides/tailwind-v3-css)
 - [Testing](/docs/app/guides/testing)
 - [Third Party Libraries](/docs/app/guides/third-party-libraries)
 - [Upgrading](/docs/app/guides/upgrading)
 - [Videos](/docs/app/guides/videos)
 - [View transitions](/docs/app/guides/view-transitions)

---
title: AI Coding Agents
description: Learn how to configure your Next.js project so AI coding agents use up-to-date documentation instead of outdated training data.
url: "https://nextjs.org/docs/app/guides/ai-agents"
version: 16.2.6
---

# AI Coding Agents

Next.js ships version-matched documentation inside the `next` package, allowing AI coding agents to reference accurate, up-to-date APIs and patterns. An `AGENTS.md` file at the root of your project directs agents to these bundled docs instead of their training data.

## How it works

When you install `next`, the Next.js documentation is bundled at `node_modules/next/dist/docs/`. The bundled docs mirror the structure of the [Next.js documentation site](https://nextjs.org/docs):

```txt
node_modules/next/dist/docs/
├── 01-app/
│   ├── 01-getting-started/
│   ├── 02-guides/
│   └── 03-api-reference/
├── 02-pages/
├── 03-architecture/
└── index.mdx
```

This means agents always have access to docs that match your installed version — no network request or external lookup required.

The `AGENTS.md` file at the root of your project tells agents to read these bundled docs before writing any code. Most AI coding agents — including Claude Code, Cursor, GitHub Copilot, and others — automatically read `AGENTS.md` when they start a session.

## Getting started

### New projects

[`create-next-app`](/docs/app/api-reference/cli/create-next-app) generates `AGENTS.md` and `CLAUDE.md` automatically. No additional setup is needed:

```bash package="pnpm"
pnpm create next-app@canary
```

```bash package="npm"
npx create-next-app@canary
```

```bash package="yarn"
yarn create next-app@canary
```

```bash package="bun"
bun create next-app@canary
```

If you don't want the agent files, pass `--no-agents-md`:

```bash
npx create-next-app@canary --no-agents-md
```

### Existing projects

Ensure you are on Next.js `v16.2.0-canary.37` or later, then add the following files to the root of your project.

`AGENTS.md` contains the instructions that agents will read:

```md filename="AGENTS.md"

# Next.js: ALWAYS read docs before coding

Before any Next.js work, find and read the relevant doc in `node_modules/next/dist/docs/`. Your training data is outdated — the docs are the source of truth.

```

`CLAUDE.md` uses the `@` import syntax to include `AGENTS.md`, so [Claude Code](https://docs.anthropic.com/en/docs/claude-code) users get the same instructions without duplicating content:

```md filename="CLAUDE.md"
@AGENTS.md
```

For earlier versions

On version 16.1 and earlier, use the codemod to generate these files automatically:

```bash
npx @next/codemod@latest agents-md
```

The codemod outputs the bundled docs to `.next-docs/` in the project root instead of `node_modules/next/dist/docs/`, and the generated agent files will point to that directory.

## Understanding AGENTS.md

The default `AGENTS.md` contains a single, focused instruction: **read the bundled docs before writing code**. This is intentionally minimal — the goal is to redirect agents from stale training data to the accurate, version-matched documentation in `node_modules/next/dist/docs/`.

The `` and `` comment markers delimit the Next.js-managed section. You can add your own project-specific instructions outside these markers without worrying about them being overwritten by future updates.

The bundled docs include guides, API references, and file conventions for the App Router and Pages Router. When an agent encounters a task involving routing, data fetching, or any other Next.js feature, it can look up the correct API in the bundled docs rather than relying on potentially outdated training data.

> **Good to know:** To see how bundled docs and `AGENTS.md` improve agent performance on real-world Next.js tasks, visit the [benchmark results](https://nextjs.org/evals).
## Next Steps- [Next.js MCP Server](/docs/app/guides/mcp)
  - Learn how to use Next.js MCP support to allow coding agents access to your application state

---
title: Analytics
description: Measure and track page performance using Next.js Speed Insights
url: "https://nextjs.org/docs/app/guides/analytics"
version: 16.2.6
---

# Analytics

Next.js has built-in support for measuring and reporting performance metrics. You can either use the [`useReportWebVitals`](/docs/app/api-reference/functions/use-report-web-vitals) hook to manage reporting yourself, or alternatively, Vercel provides a [managed service](https://vercel.com/analytics?utm_source=next-site\&utm_medium=docs\&utm_campaign=next-website) to automatically collect and visualize metrics for you.

## Client Instrumentation

For more advanced analytics and monitoring needs, Next.js provides a `instrumentation-client.js|ts` file that runs before your application's frontend code starts executing. This is ideal for setting up global analytics, error tracking, or performance monitoring tools.

To use it, create an `instrumentation-client.js` or `instrumentation-client.ts` file in your application's root directory:

```js filename="instrumentation-client.js"
// Initialize analytics before the app starts
console.log('Analytics initialized')

// Set up global error tracking
window.addEventListener('error', (event) => {
  // Send to your error tracking service
  reportError(event.error)
})
```

## Build Your Own

```jsx filename="app/_components/web-vitals.js"
'use client'

import { useReportWebVitals } from 'next/web-vitals'

export function WebVitals() {
  useReportWebVitals((metric) => {
    console.log(metric)
  })
}
```

```jsx filename="app/layout.js"
import { WebVitals } from './_components/web-vitals'

export default function Layout({ children }) {
  return (

        {children}

  )
}
```

> Since the `useReportWebVitals` hook requires the `'use client'` directive, the most performant approach is to create a separate component that the root layout imports. This confines the client boundary exclusively to the `WebVitals` component.

View the [API Reference](/docs/app/api-reference/functions/use-report-web-vitals) for more information.

## Web Vitals

[Web Vitals](https://web.dev/vitals/) are a set of useful metrics that aim to capture the user
experience of a web page. The following web vitals are all included:

* [Time to First Byte](https://developer.mozilla.org/docs/Glossary/Time_to_first_byte) (TTFB)
* [First Contentful Paint](https://developer.mozilla.org/docs/Glossary/First_contentful_paint) (FCP)
* [Largest Contentful Paint](https://web.dev/lcp/) (LCP)
* [First Input Delay](https://web.dev/fid/) (FID)
* [Cumulative Layout Shift](https://web.dev/cls/) (CLS)
* [Interaction to Next Paint](https://web.dev/inp/) (INP)

You can handle all the results of these metrics using the `name` property.

```tsx filename="app/_components/web-vitals.tsx" switcher
'use client'

import { useReportWebVitals } from 'next/web-vitals'

export function WebVitals() {
  useReportWebVitals((metric) => {
    switch (metric.name) {
      case 'FCP': {
        // handle FCP results
      }
      case 'LCP': {
        // handle LCP results
      }
      // ...
    }
  })
}
```

```jsx filename="app/_components/web-vitals.js" switcher
'use client'

import { useReportWebVitals } from 'next/web-vitals'

export function WebVitals() {
  useReportWebVitals((metric) => {
    switch (metric.name) {
      case 'FCP': {
        // handle FCP results
      }
      case 'LCP': {
        // handle LCP results
      }
      // ...
    }
  })
}
```

## Sending results to external systems

You can send results to any endpoint to measure and track
real user performance on your site. For example:

```js
useReportWebVitals((metric) => {
  const body = JSON.stringify(metric)
  const url = 'https://example.com/analytics'

  // Use `navigator.sendBeacon()` if available, falling back to `fetch()`.
  if (navigator.sendBeacon) {
    navigator.sendBeacon(url, body)
  } else {
    fetch(url, { body, method: 'POST', keepalive: true })
  }
})
```

> **Good to know**: If you use [Google Analytics](https://analytics.google.com/analytics/web/), using the
> `id` value can allow you to construct metric distributions manually (to calculate percentiles,
> etc.)

> ```js
> useReportWebVitals((metric) => {
>   // Use `window.gtag` if you initialized Google Analytics as this example:
>   // https://github.com/vercel/next.js/blob/canary/examples/with-google-analytics
>   window.gtag('event', metric.name, {
>     value: Math.round(
>       metric.name === 'CLS' ? metric.value * 1000 : metric.value
>     ), // values must be integers
>     event_label: metric.id, // id unique to current page load
>     non_interaction: true, // avoids affecting bounce rate.
>   })
> })
> ```
>
> Read more about [sending results to Google Analytics](https://github.com/GoogleChrome/web-vitals#send-the-results-to-google-analytics).

---
title: Authentication
description: Learn how to implement authentication in your Next.js application.
url: "https://nextjs.org/docs/app/guides/authentication"
version: 16.2.6
---

# Authentication

Understanding authentication is crucial for protecting your application's data. This page will guide you through what React and Next.js features to use to implement auth.

Before starting, it helps to break down the process into three concepts:

1. **[Authentication](#authentication)**: Verifies if the user is who they say they are. It requires the user to prove their identity with something they have, such as a username and password.
2. **[Session Management](#session-management)**: Tracks the user's auth state across requests.
3. **[Authorization](#authorization)**: Decides what routes and data the user can access.

This diagram shows the authentication flow using React and Next.js features:

![Diagram showing the authentication flow with React and Next.js features](https://h8DxKfmAPhn8O0p3.public.blob.vercel-storage.com/docs/light/authentication-overview.png)

The examples on this page walk through basic username and password auth for educational purposes. While you can implement a custom auth solution, for increased security and simplicity, we recommend using an authentication library. These offer built-in solutions for authentication, session management, and authorization, as well as additional features such as social logins, multi-factor authentication, and role-based access control. You can find a list in the [Auth Libraries](#auth-libraries) section.

## Authentication

### Sign-up and login functionality

You can use the [``](https://react.dev/reference/react-dom/components/form) element with React's [Server Actions](/docs/app/getting-started/mutating-data) and `useActionState` to capture user credentials, validate form fields, and call your Authentication Provider's API or database.

Since Server Actions always execute on the server, they provide a secure environment for handling authentication logic.

Here are the steps to implement signup/login functionality:

#### 1. Capture user credentials

To capture user credentials, create a form that invokes a Server Action on submission. For example, a signup form that accepts the user's name, email, and password:

```tsx filename="app/ui/signup-form.tsx" switcher
import { signup } from '@/app/actions/auth'

export function SignupForm() {
  return (

        Name

        Email

        Password

      Sign Up

  )
}
```

```jsx filename="app/ui/signup-form.js" switcher
import { signup } from '@/app/actions/auth'

export function SignupForm() {
  return (

        Name

        Email

        Password

      Sign Up

  )
}
```

```tsx filename="app/actions/auth.ts" switcher
export async function signup(formData: FormData) {}
```

```jsx filename="app/actions/auth.js" switcher
export async function signup(formData) {}
```

#### 2. Validate form fields on the server

Use the Server Action to validate the form fields on the server. If your authentication provider doesn't provide form validation, you can use a schema validation library like [Zod](https://zod.dev/) or [Yup](https://github.com/jquense/yup).

Using Zod as an example, you can define a form schema with appropriate error messages:

```ts filename="app/lib/definitions.ts" switcher
import * as z from 'zod'

export const SignupFormSchema = z.object({
  name: z
    .string()
    .min(2, { error: 'Name must be at least 2 characters long.' })
    .trim(),
  email: z.email({ error: 'Please enter a valid email.' }).trim(),
  password: z
    .string()
    .min(8, { error: 'Be at least 8 characters long' })
    .regex(/[a-zA-Z]/, { error: 'Contain at least one letter.' })
    .regex(/[0-9]/, { error: 'Contain at least one number.' })
    .regex(/[^a-zA-Z0-9]/, {
      error: 'Contain at least one special character.',
    })
    .trim(),
})

export type FormState =
  | {
      errors?: {
        name?: string[]
        email?: string[]
        password?: string[]
      }
      message?: string
    }
  | undefined
```

```js filename="app/lib/definitions.js" switcher
import * as z from 'zod'

export const SignupFormSchema = z.object({
  name: z
    .string()
    .min(2, { error: 'Name must be at least 2 characters long.' })
    .trim(),
  email: z.email({ error: 'Please enter a valid email.' }).trim(),
  password: z
    .string()
    .min(8, { error: 'Be at least 8 characters long' })
    .regex(/[a-zA-Z]/, { error: 'Contain at least one letter.' })
    .regex(/[0-9]/, { error: 'Contain at least one number.' })
    .regex(/[^a-zA-Z0-9]/, {
      error: 'Contain at least one special character.',
    })
    .trim(),
})
```

To prevent unnecessary calls to your authentication provider's API or database, you can `return` early in the Server Action if any form fields do not match the defined schema.

```ts filename="app/actions/auth.ts" switcher
import { SignupFormSchema, FormState } from '@/app/lib/definitions'

export async function signup(state: FormState, formData: FormData) {
  // Validate form fields
  const validatedFields = SignupFormSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
    password: formData.get('password'),
  })

  // If any form fields are invalid, return early
  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
    }
  }

  // Call the provider or db to create a user...
}
```

```js filename="app/actions/auth.js" switcher
import { SignupFormSchema } from '@/app/lib/definitions'

export async function signup(state, formData) {
  // Validate form fields
  const validatedFields = SignupFormSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
    password: formData.get('password'),
  })

  // If any form fields are invalid, return early
  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
    }
  }

  // Call the provider or db to create a user...
}
```

Back in your ``, you can use React's `useActionState` hook to display validation errors while the form is submitting:

```tsx filename="app/ui/signup-form.tsx" switcher highlight={7,15,21,27-36}
'use client'

import { signup } from '@/app/actions/auth'
import { useActionState } from 'react'

export default function SignupForm() {
  const [state, action, pending] = useActionState(signup, undefined)

  return (

        Name

      {state?.errors?.name && {state.errors.name}
}

        Email

      {state?.errors?.email && {state.errors.email}
}

        Password

      {state?.errors?.password && (

          Password must:

            {state.errors.password.map((error) => (
              - {error}

            ))}

      )}

        Sign Up

  )
}
```

```jsx filename="app/ui/signup-form.js" switcher highlight={7,15,21,27-36}
'use client'

import { signup } from '@/app/actions/auth'
import { useActionState } from 'react'

export default function SignupForm() {
  const [state, action, pending] = useActionState(signup, undefined)

  return (

        Name

      {state?.errors?.name && {state.errors.name}
}

        Email

      {state?.errors?.email && {state.errors.email}
}

        Password

      {state?.errors?.password && (

          Password must:

            {state.errors.password.map((error) => (
              - {error}

            ))}

      )}

        Sign Up

  )
}
```

> **Good to know:**
>
> * In React 19, `useFormStatus` includes additional keys on the returned object, like data, method, and action. If you are not using React 19, only the `pending` key is available.
> * Before mutating data, you should always ensure a user is also authorized to perform the action. See [Authentication and Authorization](#authorization).

#### 3. Create a user or check user credentials

After validating form fields, you can create a new user account or check if the user exists by calling your authentication provider's API or database.

Continuing from the previous example:

```tsx filename="app/actions/auth.tsx" switcher
export async function signup(state: FormState, formData: FormData) {
  // 1. Validate form fields
  // ...

  // 2. Prepare data for insertion into database
  const { name, email, password } = validatedFields.data
  // e.g. Hash the user's password before storing it
  const hashedPassword = await bcrypt.hash(password, 10)

  // 3. Insert the user into the database or call an Auth Library's API
  const data = await db
    .insert(users)
    .values({
      name,
      email,
      password: hashedPassword,
    })
    .returning({ id: users.id })

  const user = data[0]

  if (!user) {
    return {
      message: 'An error occurred while creating your account.',
    }
  }

  // TODO:
  // 4. Create user session
  // 5. Redirect user
}
```

```jsx filename="app/actions/auth.js" switcher
export async function signup(state, formData) {
  // 1. Validate form fields
  // ...

  // 2. Prepare data for insertion into database
  const { name, email, password } = validatedFields.data
  // e.g. Hash the user's password before storing it
  const hashedPassword = await bcrypt.hash(password, 10)

  // 3. Insert the user into the database or call an Library API
  const data = await db
    .insert(users)
    .values({
      name,
      email,
      password: hashedPassword,
    })
    .returning({ id: users.id })

  const user = data[0]

  if (!user) {
    return {
      message: 'An error occurred while creating your account.',
    }
  }

  // TODO:
  // 4. Create user session
  // 5. Redirect user
}
```

After successfully creating the user account or verifying the user credentials, you can create a session to manage the user's auth state. Depending on your session management strategy, the session can be stored in a cookie or database, or both. Continue to the [Session Management](#session-management) section to learn more.

> **Tips:**
>
> * The example above is verbose since it breaks down the authentication steps for the purpose of education. This highlights that implementing your own secure solution can quickly become complex. Consider using an [Auth Library](#auth-libraries) to simplify the process.
> * To improve the user experience, you may want to check for duplicate emails or usernames earlier in the registration flow. For example, as the user types in a username or the input field loses focus. This can help prevent unnecessary form submissions and provide immediate feedback to the user. You can debounce requests with libraries such as [use-debounce](https://www.npmjs.com/package/use-debounce) to manage the frequency of these checks.

## Session Management

Session management ensures that the user's authenticated state is preserved across requests. It involves creating, storing, refreshing, and deleting sessions or tokens.

There are two types of sessions:

1. [**Stateless**](#stateless-sessions): Session data (or a token) is stored in the browser's cookies. The cookie is sent with each request, allowing the session to be verified on the server. This method is simpler, but can be less secure if not implemented correctly.
2. [**Database**](#database-sessions): Session data is stored in a database, with the user's browser only receiving the encrypted session ID. This method is more secure, but can be complex and use more server resources.

> **Good to know:** While you can use either method, or both, we recommend using a session management library such as [iron-session](https://github.com/vvo/iron-session) or [Jose](https://github.com/panva/jose).

### Stateless Sessions

To create and manage stateless sessions, there are a few steps you need to follow:

1. Generate a secret key, which will be used to sign your session, and store it as an [environment variable](/docs/app/guides/environment-variables).
2. Write logic to encrypt/decrypt session data using a session management library.
3. Manage cookies using the Next.js [`cookies`](/docs/app/api-reference/functions/cookies) API.

In addition to the above, consider adding functionality to [update (or refresh)](#updating-or-refreshing-sessions) the session when the user returns to the application, and [delete](#deleting-the-session) the session when the user logs out.

> **Good to know:** Check if your [auth library](#auth-libraries) includes session management.

#### 1. Generating a secret key

There are a few ways you can generate secret key to sign your session. For example, you may choose to use the `openssl` command in your terminal:

```bash filename="terminal"
openssl rand -base64 32
```

This command generates a 32-character random string that you can use as your secret key and store in your [environment variables file](/docs/app/guides/environment-variables):

```bash filename=".env"
SESSION_SECRET=your_secret_key
```

You can then reference this key in your session management logic:

```js filename="app/lib/session.js"
const secretKey = process.env.SESSION_SECRET
```

#### 2. Encrypting and decrypting sessions

Next, you can use your preferred [session management library](#session-management-libraries) to encrypt and decrypt sessions. Continuing from the previous example, we'll use [Jose](https://www.npmjs.com/package/jose) (compatible with the [Edge Runtime](/docs/app/api-reference/edge)) and React's [`server-only`](https://www.npmjs.com/package/server-only) package to ensure that your session management logic is only executed on the server.

```tsx filename="app/lib/session.ts" switcher
import 'server-only'
import { SignJWT, jwtVerify } from 'jose'
import { SessionPayload } from '@/app/lib/definitions'

const secretKey = process.env.SESSION_SECRET
const encodedKey = new TextEncoder().encode(secretKey)

export async function encrypt(payload: SessionPayload) {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(encodedKey)
}

export async function decrypt(session: string | undefined = '') {
  try {
    const { payload } = await jwtVerify(session, encodedKey, {
      algorithms: ['HS256'],
    })
    return payload
  } catch (error) {
    console.log('Failed to verify session')
  }
}
```

```jsx filename="app/lib/session.js" switcher
import 'server-only'
import { SignJWT, jwtVerify } from 'jose'

const secretKey = process.env.SESSION_SECRET
const encodedKey = new TextEncoder().encode(secretKey)

export async function encrypt(payload) {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(encodedKey)
}

export async function decrypt(session) {
  try {
    const { payload } = await jwtVerify(session, encodedKey, {
      algorithms: ['HS256'],
    })
    return payload
  } catch (error) {
    console.log('Failed to verify session')
  }
}
```

> **Tips**:
>
> * The payload should contain the **minimum**, unique user data that'll be used in subsequent requests, such as the user's ID, role, etc. It should not contain personally identifiable information like phone number, email address, credit card information, etc, or sensitive data like passwords.

#### 3. Setting cookies (recommended options)

To store the session in a cookie, use the Next.js [`cookies`](/docs/app/api-reference/functions/cookies) API. The cookie should be set on the server, and include the recommended options:

* **HttpOnly**: Prevents client-side JavaScript from accessing the cookie.
* **Secure**: Use https to send the cookie.
* **SameSite**: Specify whether the cookie can be sent with cross-site requests.
* **Max-Age or Expires**: Delete the cookie after a certain period.
* **Path**: Define the URL path for the cookie.

Please refer to [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies) for more information on each of these options.

```ts filename="app/lib/session.ts" switcher
import 'server-only'
import { cookies } from 'next/headers'

export async function createSession(userId: string) {
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  const session = await encrypt({ userId, expiresAt })
  const cookieStore = await cookies()

  cookieStore.set('session', session, {
    httpOnly: true,
    secure: true,
    expires: expiresAt,
    sameSite: 'lax',
    path: '/',
  })
}
```

```js filename="app/lib/session.js" switcher
import 'server-only'
import { cookies } from 'next/headers'

export async function createSession(userId) {
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  const session = await encrypt({ userId, expiresAt })
  const cookieStore = await cookies()

  cookieStore.set('session', session, {
    httpOnly: true,
    secure: true,
    expires: expiresAt,
    sameSite: 'lax',
    path: '/',
  })
}
```

Back in your Server Action, you can invoke the `createSession()` function, and use the [`redirect()`](/docs/app/guides/redirecting) API to redirect the user to the appropriate page:

```ts filename="app/actions/auth.ts" switcher
import { createSession } from '@/app/lib/session'

export async function signup(state: FormState, formData: FormData) {
  // Previous steps:
  // 1. Validate form fields
  // 2. Prepare data for insertion into database
  // 3. Insert the user into the database or call an Library API

  // Current steps:
  // 4. Create user session
  await createSession(user.id)
  // 5. Redirect user
  redirect('/profile')
}
```

```js filename="app/actions/auth.js" switcher
import { createSession } from '@/app/lib/session'

export async function signup(state, formData) {
  // Previous steps:
  // 1. Validate form fields
  // 2. Prepare data for insertion into database
  // 3. Insert the user into the database or call an Library API

  // Current steps:
  // 4. Create user session
  await createSession(user.id)
  // 5. Redirect user
  redirect('/profile')
}
```

> **Tips**:
>
> * **Cookies should be set on the server** to prevent client-side tampering.
> * 🎥 Watch: Learn more about stateless sessions and authentication with Next.js → [YouTube (11 minutes)](https://www.youtube.com/watch?v=DJvM2lSPn6w).

#### Updating (or refreshing) sessions

You can also extend the session's expiration time. This is useful for keeping the user logged in after they access the application again. For example:

```ts filename="app/lib/session.ts" switcher
import 'server-only'
import { cookies } from 'next/headers'
import { decrypt } from '@/app/lib/session'

export async function updateSession() {
  const session = (await cookies()).get('session')?.value
  const payload = await decrypt(session)

  if (!session || !payload) {
    return null
  }

  const expires = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)

  const cookieStore = await cookies()
  cookieStore.set('session', session, {
    httpOnly: true,
    secure: true,
    expires: expires,
    sameSite: 'lax',
    path: '/',
  })
}
```

```js filename="app/lib/session.js" switcher
import 'server-only'
import { cookies } from 'next/headers'
import { decrypt } from '@/app/lib/session'

export async function updateSession() {
  const session = (await cookies()).get('session')?.value
  const payload = await decrypt(session)

  if (!session || !payload) {
    return null
  }

  const expires = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)(
    await cookies()
  ).set('session', session, {
    httpOnly: true,
    secure: true,
    expires: expires,
    sameSite: 'lax',
    path: '/',
  })
}
```

> **Tip:** Check if your auth library supports refresh tokens, which can be used to extend the user's session.

#### Deleting the session

To delete the session, you can delete the cookie:

```ts filename="app/lib/session.ts" switcher
import 'server-only'
import { cookies } from 'next/headers'

export async function deleteSession() {
  const cookieStore = await cookies()
  cookieStore.delete('session')
}
```

```js filename="app/lib/session.js" switcher
import 'server-only'
import { cookies } from 'next/headers'

export async function deleteSession() {
  const cookieStore = await cookies()
  cookieStore.delete('session')
}
```

Then you can reuse the `deleteSession()` function in your application, for example, on logout:

```ts filename="app/actions/auth.ts" switcher
import { cookies } from 'next/headers'
import { deleteSession } from '@/app/lib/session'

export async function logout() {
  await deleteSession()
  redirect('/login')
}
```

```js filename="app/actions/auth.js" switcher
import { cookies } from 'next/headers'
import { deleteSession } from '@/app/lib/session'

export async function logout() {
  await deleteSession()
  redirect('/login')
}
```

### Database Sessions

To create and manage database sessions, you'll need to follow these steps:

1. Create a table in your database to store session and data (or check if your Auth Library handles this).
2. Implement functionality to insert, update, and delete sessions
3. Encrypt the session ID before storing it in the user's browser, and ensure the database and cookie stay in sync (this is optional, but recommended for optimistic auth checks in [Proxy](#optimistic-checks-with-proxy-optional)).

For example:

```ts filename="app/lib/session.ts" switcher
import cookies from 'next/headers'
import { db } from '@/app/lib/db'
import { encrypt } from '@/app/lib/session'

export async function createSession(id: number) {
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)

  // 1. Create a session in the database
  const data = await db
    .insert(sessions)
    .values({
      userId: id,
      expiresAt,
    })
    // Return the session ID
    .returning({ id: sessions.id })

  const sessionId = data[0].id

  // 2. Encrypt the session ID
  const session = await encrypt({ sessionId, expiresAt })

  // 3. Store the session in cookies for optimistic auth checks
  const cookieStore = await cookies()
  cookieStore.set('session', session, {
    httpOnly: true,
    secure: true,
    expires: expiresAt,
    sameSite: 'lax',
    path: '/',
  })
}
```

```js filename="app/lib/session.js" switcher
import cookies from 'next/headers'
import { db } from '@/app/lib/db'
import { encrypt } from '@/app/lib/session'

export async function createSession(id) {
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)

  // 1. Create a session in the database
  const data = await db
    .insert(sessions)
    .values({
      userId: id,
      expiresAt,
    })
    // Return the session ID
    .returning({ id: sessions.id })

  const sessionId = data[0].id

  // 2. Encrypt the session ID
  const session = await encrypt({ sessionId, expiresAt })

  // 3. Store the session in cookies for optimistic auth checks
  const cookieStore = await cookies()
  cookieStore.set('session', session, {
    httpOnly: true,
    secure: true,
    expires: expiresAt,
    sameSite: 'lax',
    path: '/',
  })
}
```

> **Tips**:
>
> * For faster access, you may consider adding server caching for the lifetime of the session. You can also keep the session data in your primary database, and combine data requests to reduce the number of queries.
> * You may opt to use database sessions for more advanced use cases, such as keeping track of the last time a user logged in, or number of active devices, or give users the ability to log out of all devices.

After implementing session management, you'll need to add authorization logic to control what users can access and do within your application. Continue to the [Authorization](#authorization) section to learn more.

## Authorization

Once a user is authenticated and a session is created, you can implement authorization to control what the user can access and do within your application.

There are two main types of authorization checks:

1. **Optimistic**: Checks if the user is authorized to access a route or perform an action using the session data stored in the cookie. These checks are useful for quick operations, such as showing/hiding UI elements or redirecting users based on permissions or roles.
2. **Secure**: Checks if the user is authorized to access a route or perform an action using the session data stored in the database. These checks are more secure and are used for operations that require access to sensitive data or actions.

For both cases, we recommend:

* Creating a [Data Access Layer](#creating-a-data-access-layer-dal) to centralize your authorization logic
* Using [Data Transfer Objects (DTO)](#using-data-transfer-objects-dto) to only return the necessary data
* Optionally use [Proxy](#optimistic-checks-with-proxy-optional) to perform optimistic checks.

### Optimistic checks with Proxy (Optional)

There are some cases where you may want to use [Proxy](/docs/app/api-reference/file-conventions/proxy) and redirect users based on permissions:

* To perform optimistic checks. Since Proxy runs on every route, it's a good way to centralize redirect logic and pre-filter unauthorized users.
* To protect static routes that share data between users (e.g. content behind a paywall).

However, since Proxy runs on every route, including [prefetched](/docs/app/getting-started/linking-and-navigating#prefetching) routes, it's important to only read the session from the cookie (optimistic checks), and avoid database checks to prevent performance issues.

For example:

```tsx filename="proxy.ts" switcher
import { NextRequest, NextResponse } from 'next/server'
import { decrypt } from '@/app/lib/session'
import { cookies } from 'next/headers'

// 1. Specify protected and public routes
const protectedRoutes = ['/dashboard']
const publicRoutes = ['/login', '/signup', '/']

export default async function proxy(req: NextRequest) {
  // 2. Check if the current route is protected or public
  const path = req.nextUrl.pathname
  const isProtectedRoute = protectedRoutes.includes(path)
  const isPublicRoute = publicRoutes.includes(path)

  // 3. Decrypt the session from the cookie
  const cookie = (await cookies()).get('session')?.value
  const session = await decrypt(cookie)

  // 4. Redirect to /login if the user is not authenticated
  if (isProtectedRoute && !session?.userId) {
    return NextResponse.redirect(new URL('/login', req.nextUrl))
  }

  // 5. Redirect to /dashboard if the user is authenticated
  if (
    isPublicRoute &&
    session?.userId &&
    !req.nextUrl.pathname.startsWith('/dashboard')
  ) {
    return NextResponse.redirect(new URL('/dashboard', req.nextUrl))
  }

  return NextResponse.next()
}

// Routes Proxy should not run on
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|.*\\.png$).*)'],
}
```

```js filename="proxy.js" switcher
import { NextResponse } from 'next/server'
import { decrypt } from '@/app/lib/session'
import { cookies } from 'next/headers'

// 1. Specify protected and public routes
const protectedRoutes = ['/dashboard']
const publicRoutes = ['/login', '/signup', '/']

export default async function proxy(req) {
  // 2. Check if the current route is protected or public
  const path = req.nextUrl.pathname
  const isProtectedRoute = protectedRoutes.includes(path)
  const isPublicRoute = publicRoutes.includes(path)

  // 3. Decrypt the session from the cookie
  const cookie = (await cookies()).get('session')?.value
  const session = await decrypt(cookie)

  // 5. Redirect to /login if the user is not authenticated
  if (isProtectedRoute && !session?.userId) {
    return NextResponse.redirect(new URL('/login', req.nextUrl))
  }

  // 6. Redirect to /dashboard if the user is authenticated
  if (
    isPublicRoute &&
    session?.userId &&
    !req.nextUrl.pathname.startsWith('/dashboard')
  ) {
    return NextResponse.redirect(new URL('/dashboard', req.nextUrl))
  }

  return NextResponse.next()
}

// Routes Proxy should not run on
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|.*\\.png$).*)'],
}
```

While Proxy can be useful for initial checks, it should not be your only line of defense in protecting your data. The majority of security checks should be performed as close as possible to your data source, see [Data Access Layer](#creating-a-data-access-layer-dal) for more information.

> **Tips**:
>
> * In Proxy, you can also read cookies using `req.cookies.get('session').value`.
> * Proxy uses the Node.js runtime, check if your Auth library and session management library are compatible. You may need to use [Middleware](https://github.com/vercel/next.js/blob/v15.5.6/docs/01-app/03-api-reference/03-file-conventions/middleware.mdx) if your Auth library only supports [Edge Runtime](/docs/app/api-reference/edge)
> * You can use the `matcher` property in the Proxy to specify which routes Proxy should run on. Although, for auth, it's recommended Proxy runs on all routes.

### Creating a Data Access Layer (DAL)

We recommend creating a DAL to centralize your data requests and authorization logic.

The DAL should include a function that verifies the user's session as they interact with your application. At the very least, the function should check if the session is valid, then redirect or return the user information needed to make further requests.

For example, create a separate file for your DAL that includes a `verifySession()` function. Then use React's [cache](https://react.dev/reference/react/cache) API to memoize the return value of the function during a React render pass:

```tsx filename="app/lib/dal.ts" switcher
import 'server-only'

import { cookies } from 'next/headers'
import { decrypt } from '@/app/lib/session'

export const verifySession = cache(async () => {
  const cookie = (await cookies()).get('session')?.value
  const session = await decrypt(cookie)

  if (!session?.userId) {
    redirect('/login')
  }

  return { isAuth: true, userId: session.userId }
})
```

```js filename="app/lib/dal.js" switcher
import 'server-only'

import { cookies } from 'next/headers'
import { decrypt } from '@/app/lib/session'

export const verifySession = cache(async () => {
  const cookie = (await cookies()).get('session')?.value
  const session = await decrypt(cookie)

  if (!session.userId) {
    redirect('/login')
  }

  return { isAuth: true, userId: session.userId }
})
```

You can then invoke the `verifySession()` function in your data requests, Server Actions, Route Handlers:

```tsx filename="app/lib/dal.ts" switcher
export const getUser = cache(async () => {
  const session = await verifySession()
  if (!session) return null

  try {
    const data = await db.query.users.findMany({
      where: eq(users.id, session.userId),
      // Explicitly return the columns you need rather than the whole user object
      columns: {
        id: true,
        name: true,
        email: true,
      },
    })

    const user = data[0]

    return user
  } catch (error) {
    console.log('Failed to fetch user')
    return null
  }
})
```

```jsx filename="app/lib/dal.js" switcher
export const getUser = cache(async () => {
  const session = await verifySession()
  if (!session) return null

  try {
    const data = await db.query.users.findMany({
      where: eq(users.id, session.userId),
      // Explicitly return the columns you need rather than the whole user object
      columns: {
        id: true,
        name: true,
        email: true,
      },
    })

    const user = data[0]

    return user
  } catch (error) {
    console.log('Failed to fetch user')
    return null
  }
})
```

> **Tip**:
>
> * A DAL can be used to protect data fetched at request time. However, for static routes that share data between users, data will be fetched at build time and not at request time. Use [Proxy](#optimistic-checks-with-proxy-optional) to protect static routes.
> * For secure checks, you can check if the session is valid by comparing the session ID with your database. Use React's [cache](https://react.dev/reference/react/cache) function to avoid unnecessary duplicate requests to the database during a render pass.
> * You may wish to consolidate related data requests in a JavaScript class that runs `verifySession()` before any methods.

### Using Data Transfer Objects (DTO)

When retrieving data, it's recommended you return only the necessary data that will be used in your application, and not entire objects. For example, if you're fetching user data, you might only return the user's ID and name, rather than the entire user object which could contain passwords, phone numbers, etc.

However, if you have no control over the returned data structure, or are working in a team where you want to avoid whole objects being passed to the client, you can use strategies such as specifying what fields are safe to be exposed to the client.

```tsx filename="app/lib/dto.ts" switcher
import 'server-only'
import { getUser } from '@/app/lib/dal'

function canSeeUsername(viewer: User) {
  return true
}

function canSeePhoneNumber(viewer: User, team: string) {
  return viewer.isAdmin || team === viewer.team
}

export async function getProfileDTO(slug: string) {
  const data = await db.query.users.findMany({
    where: eq(users.slug, slug),
    // Return specific columns here
  })
  const user = data[0]

  const currentUser = await getUser(user.id)

  // Or return only what's specific to the query here
  return {
    username: canSeeUsername(currentUser) ? user.username : null,
    phonenumber: canSeePhoneNumber(currentUser, user.team)
      ? user.phonenumber
      : null,
  }
}
```

```js filename="app/lib/dto.js" switcher
import 'server-only'
import { getUser } from '@/app/lib/dal'

function canSeeUsername(viewer) {
  return true
}

function canSeePhoneNumber(viewer, team) {
  return viewer.isAdmin || team === viewer.team
}

export async function getProfileDTO(slug) {
  const data = await db.query.users.findMany({
    where: eq(users.slug, slug),
    // Return specific columns here
  })
  const user = data[0]

  const currentUser = await getUser(user.id)

  // Or return only what's specific to the query here
  return {
    username: canSeeUsername(currentUser) ? user.username : null,
    phonenumber: canSeePhoneNumber(currentUser, user.team)
      ? user.phonenumber
      : null,
  }
}
```

By centralizing your data requests and authorization logic in a DAL and using DTOs, you can ensure that all data requests are secure and consistent, making it easier to maintain, audit, and debug as your application scales.

> **Good to know**:
>
> * There are a couple of different ways you can define a DTO, from using `toJSON()`, to individual functions like the example above, or JS classes. Since these are JavaScript patterns and not a React or Next.js feature, we recommend doing some research to find the best pattern for your application.
> * Learn more about security best practices in our [Security in Next.js article](/blog/security-nextjs-server-components-actions).

### Server Components

Auth check in [Server Components](/docs/app/getting-started/server-and-client-components) are useful for role-based access. For example, to conditionally render components based on the user's role:

```tsx filename="app/dashboard/page.tsx" switcher
import { verifySession } from '@/app/lib/dal'

export default async function Dashboard() {
  const session = await verifySession()
  const userRole = session?.user?.role // Assuming 'role' is part of the session object

  if (userRole === 'admin') {
    return
  } else if (userRole === 'user') {
    return
  } else {
    redirect('/login')
  }
}
```

```jsx filename="app/dashboard/page.jsx" switcher
import { verifySession } from '@/app/lib/dal'

export default async function Dashboard() {
  const session = await verifySession()
  const userRole = session?.user?.role // Assuming 'role' is part of the session object

  if (userRole === 'admin') {
    return
  } else if (userRole === 'user') {
    return
  } else {
    redirect('/login')
  }
}
```

In the example, we use the `verifySession()` function from our DAL to check for 'admin', 'user', and unauthorized roles. This pattern ensures that each user interacts only with components appropriate to their role.

### Layouts and auth checks

Due to [Partial Rendering](/docs/app/getting-started/linking-and-navigating#client-side-transitions), be cautious when doing checks in [Layouts](/docs/app/api-reference/file-conventions/layout) as these don't re-render on navigation, meaning the user session won't be checked on every route change.

Instead, you should do the checks close to your data source or the component that'll be conditionally rendered.

For example, consider a shared layout that fetches the user data and displays the user image in a nav. Instead of doing the auth check in the layout, you should fetch the user data (`getUser()`) in the layout and do the auth check in your DAL.

This guarantees that wherever `getUser()` is called within your application, the auth check is performed, and prevents developers forgetting to check the user is authorized to access the data.

#### Auth checks in page components

For example, in a dashboard page, you can verify the user session and fetch the user data:

```tsx filename="app/dashboard/page.tsx" switcher
import { verifySession } from '@/app/lib/dal'

export default async function DashboardPage() {
  const session = await verifySession()

  // Fetch user-specific data from your database or data source
  const user = await getUserData(session.userId)

  return (

      Welcome, {user.name}

      {/* Dashboard content */}

  )
}
```

```jsx filename="app/dashboard/page.jsx" switcher
import { verifySession } from '@/app/lib/dal'

export default async function DashboardPage() {
  const session = await verifySession()

  // Fetch user-specific data from your database or data source
  const user = await getUserData(session.userId)

  return (

      Welcome, {user.name}

      {/* Dashboard content */}

  )
}
```

#### Auth checks in leaf components

You can also perform auth checks in leaf components that conditionally render UI elements based on user permissions. For example, a component that displays admin-only actions:

```tsx filename="app/ui/admin-actions.tsx" switcher
import { verifySession } from '@/app/lib/dal'

export default async function AdminActions() {
  const session = await verifySession()
  const userRole = session?.user?.role

  if (userRole !== 'admin') {
    return null
  }

  return (

      Delete User
      Edit Settings

  )
}
```

```jsx filename="app/ui/admin-actions.jsx" switcher
import { verifySession } from '@/app/lib/dal'

export default async function AdminActions() {
  const session = await verifySession()
  const userRole = session?.user?.role

  if (userRole !== 'admin') {
    return null
  }

  return (

      Delete User
      Edit Settings

  )
}
```

This pattern allows you to show or hide UI elements based on user permissions while ensuring the auth check happens at render time in each component.

> **Good to know:**
>
> * A common pattern in SPAs is to `return null` in a layout or a top-level component if a user is not authorized. This pattern is **not recommended** since Next.js applications have multiple entry points, which will not prevent nested route segments and Server Actions from being accessed.
> * Ensure that any Server Actions called from these components also perform their own authorization checks, as client-side UI restrictions alone are not sufficient for security.

### Server Actions

Treat [Server Actions](/docs/app/getting-started/mutating-data) with the same security considerations as public-facing API endpoints, and verify if the user is allowed to perform a mutation.

In the example below, we check the user's role before allowing the action to proceed:

```ts filename="app/lib/actions.ts" switcher
'use server'
import { verifySession } from '@/app/lib/dal'

export async function serverAction(formData: FormData) {
  const session = await verifySession()
  const userRole = session?.user?.role

  // Return early if user is not authorized to perform the action
  if (userRole !== 'admin') {
    return null
  }

  // Proceed with the action for authorized users
}
```

```js filename="app/lib/actions.js" switcher
'use server'
import { verifySession } from '@/app/lib/dal'

export async function serverAction() {
  const session = await verifySession()
  const userRole = session.user.role

  // Return early if user is not authorized to perform the action
  if (userRole !== 'admin') {
    return null
  }

  // Proceed with the action for authorized users
}
```

### Route Handlers

Treat [Route Handlers](/docs/app/api-reference/file-conventions/route) with the same security considerations as public-facing API endpoints, and verify if the user is allowed to access the Route Handler.

For example:

```ts filename="app/api/route.ts" switcher
import { verifySession } from '@/app/lib/dal'

export async function GET() {
  // User authentication and role verification
  const session = await verifySession()

  // Check if the user is authenticated
  if (!session) {
    // User is not authenticated
    return new Response(null, { status: 401 })
  }

  // Check if the user has the 'admin' role
  if (session.user.role !== 'admin') {
    // User is authenticated but does not have the right permissions
    return new Response(null, { status: 403 })
  }

  // Continue for authorized users
}
```

```js filename="app/api/route.js" switcher
import { verifySession } from '@/app/lib/dal'

export async function GET() {
  // User authentication and role verification
  const session = await verifySession()

  // Check if the user is authenticated
  if (!session) {
    // User is not authenticated
    return new Response(null, { status: 401 })
  }

  // Check if the user has the 'admin' role
  if (session.user.role !== 'admin') {
    // User is authenticated but does not have the right permissions
    return new Response(null, { status: 403 })
  }

  // Continue for authorized users
}
```

The example above demonstrates a Route Handler with a two-tier security check. It first checks for an active session, and then verifies if the logged-in user is an 'admin'.

## Context Providers

Using context providers for auth works due to [interleaving](/docs/app/getting-started/server-and-client-components#interleaving-server-and-client-components). However, React `context` is not supported in Server Components, making them only applicable to Client Components.

This works, but any child Server Components will be rendered on the server first, and will not have access to the context provider’s session data:

```tsx filename="app/layout.ts" switcher
import { ContextProvider } from 'auth-lib'

export default function RootLayout({ children }) {
  return (

        {children}

  )
}
```

```tsx filename="app/ui/profile.ts switcher
'use client';

import { useSession } from "auth-lib";

export default function Profile() {
  const { userId } = useSession();
  const { data } = useSWR(`/api/user/${userId}`, fetcher)

  return (
    // ...
  );
}
```

```jsx filename="app/ui/profile.js switcher
'use client';

import { useSession } from "auth-lib";

export default function Profile() {
  const { userId } = useSession();
  const { data } = useSWR(`/api/user/${userId}`, fetcher)

  return (
    // ...
  );
}
```

If session data is needed in Client Components (e.g. for client-side data fetching), use React’s [`taintUniqueValue`](https://react.dev/reference/react/experimental_taintUniqueValue) API to prevent sensitive session data from being exposed to the client.

## Resources

Now that you've learned about authentication in Next.js, here are Next.js-compatible libraries and resources to help you implement secure authentication and session management:

### Auth Libraries

* [Auth0](https://auth0.com/docs/quickstart/webapp/nextjs)
* [Better Auth](https://www.better-auth.com/docs/integrations/next)
* [Clerk](https://clerk.com/docs/quickstarts/nextjs)
* [Descope](https://docs.descope.com/getting-started/nextjs)
* [Kinde](https://kinde.com/docs/developer-tools/nextjs-sdk)
* [Logto](https://docs.logto.io/quick-starts/next-app-router)
* [NextAuth.js](https://authjs.dev/getting-started/installation?framework=next.js)
* [Ory](https://www.ory.sh/docs/getting-started/integrate-auth/nextjs)
* [Stack Auth](https://docs.stack-auth.com/getting-started/setup)
* [Supabase](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)
* [Stytch](https://stytch.com/docs/guides/quickstarts/nextjs)
* [WorkOS](https://workos.com/docs/user-management/nextjs)

### Session Management Libraries

* [Iron Session](https://github.com/vvo/iron-session)
* [Jose](https://github.com/panva/jose)

## Further Reading

To continue learning about authentication and security, check out the following resources:

* [How to think about security in Next.js](/blog/security-nextjs-server-components-actions)
* [Understanding XSS Attacks](https://vercel.com/guides/understanding-xss-attacks)
* [Understanding CSRF Attacks](https://vercel.com/guides/understanding-csrf-attacks)
* [The Copenhagen Book](https://thecopenhagenbook.com/)

---
title: Backend for Frontend
description: Learn how to use Next.js as a backend framework
url: "https://nextjs.org/docs/app/guides/backend-for-frontend"
version: 16.2.6
---

# Backend for Frontend

Next.js supports the "Backend for Frontend" pattern. This lets you create public endpoints to handle HTTP requests and return any content type—not just HTML. You can also access data sources and perform side effects like updating remote data.

If you are starting a new project, using `create-next-app` with the `--api` flag automatically includes an example `route.ts` in your new project's `app/` folder, demonstrating how to create an API endpoint.

```bash package="pnpm"
pnpm create next-app --api
```

```bash package="npm"
npx create-next-app@latest --api
```

```bash package="yarn"
yarn create next-app --api
```

```bash package="bun"
bun create next-app --api
```

> **Good to know**: Next.js backend capabilities are not a full backend replacement. They serve as an API layer that:
>
> * is publicly reachable
> * handles any HTTP request
> * can return any content type

To implement this pattern, use:

* [Route Handlers](/docs/app/api-reference/file-conventions/route)
* [`proxy`](/docs/app/api-reference/file-conventions/proxy)
* In Pages Router, [API Routes](/docs/pages/building-your-application/routing/api-routes)

## Public Endpoints

Route Handlers are public HTTP endpoints. Any client can access them.

Create a Route Handler using the `route.ts` or `route.js` file convention:

```ts filename="/app/api/route.ts" switcher
export function GET(request: Request) {}
```

```js filename="/app/api/route.js" switcher
export function GET(request) {}
```

This handles `GET` requests sent to `/api`.

Use `try/catch` blocks for operations that may throw an exception:

```ts filename="/app/api/route.ts" switcher
import { submit } from '@/lib/submit'

export async function POST(request: Request) {
  try {
    await submit(request)
    return new Response(null, { status: 204 })
  } catch (reason) {
    const message =
      reason instanceof Error ? reason.message : 'Unexpected error'

    return new Response(message, { status: 500 })
  }
}
```

```js filename="/app/api/route.js" switcher
import { submit } from '@/lib/submit'

export async function POST(request) {
  try {
    await submit(request)
    return new Response(null, { status: 204 })
  } catch (reason) {
    const message =
      reason instanceof Error ? reason.message : 'Unexpected error'

    return new Response(message, { status: 500 })
  }
}
```

Avoid exposing sensitive information in error messages sent to the client.

To restrict access, implement authentication and authorization. See [Authentication](/docs/app/guides/authentication).

## Content types

Route Handlers let you serve non-UI responses, including JSON, XML, images, files, and plain text.

Next.js uses file conventions for common endpoints:

* [`sitemap.xml`](/docs/app/api-reference/file-conventions/metadata/sitemap)
* [`opengraph-image.jpg`, `twitter-image`](/docs/app/api-reference/file-conventions/metadata/opengraph-image)
* [favicon, app icon, and apple-icon](/docs/app/api-reference/file-conventions/metadata/app-icons)
* [`manifest.json`](/docs/app/api-reference/file-conventions/metadata/manifest)
* [`robots.txt`](/docs/app/api-reference/file-conventions/metadata/robots)

You can also define custom ones, such as:

* `llms.txt`
* `rss.xml`
* `.well-known`

For example, `app/rss.xml/route.ts` creates a Route Handler for `rss.xml`.

```ts filename="/app/rss.xml/route.ts" switcher
export async function GET(request: Request) {
  const rssResponse = await fetch(/* rss endpoint */)
  const rssData = await rssResponse.json()

  const rssFeed = `

 ${rssData.title}
 ${rssData.description}
 ${rssData.link}
 ${rssData.copyright}
 ${rssData.items.map((item) => {
   return `
    ${item.title}
    ${item.description}
    ${item.link}
    ${item.publishDate}
    ${item.guid}
 `
 })}

`

  const headers = new Headers({ 'content-type': 'application/xml' })

  return new Response(rssFeed, { headers })
}
```

```js filename="/app/rss.xml/route.js" switcher
export async function GET(request) {
  const rssResponse = await fetch(/* rss endpoint */)
  const rssData = await rssResponse.json()

  const rssFeed = `

 ${rssData.title}
 ${rssData.description}
 ${rssData.link}
 ${rssData.copyright}
 ${rssData.items.map((item) => {
   return `
    ${item.title}
    ${item.description}
    ${item.link}
    ${item.publishDate}
    ${item.guid}
 `
 })}

`

  const headers = new Headers({ 'content-type': 'application/xml' })

  return new Response(rssFeed, { headers })
}
```

Sanitize any input used to generate markup.

### Content negotiation

You can use [rewrites](/docs/app/api-reference/config/next-config-js/rewrites) with header matching to serve different content types from the same URL based on the request's `Accept` header. This is known as [content negotiation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation).

For example, a documentation site might serve HTML pages to browsers and raw Markdown to AI agents from the same `/docs/…` URLs.

**1. Configure a rewrite that matches the `Accept` header:**

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      {
        source: '/docs/:slug*',
        destination: '/docs/md/:slug*',
        has: [
          {
            type: 'header',
            key: 'accept',
            value: '(.*)text/markdown(.*)',
          },
        ],
      },
    ]
  },
}
```

When a request to `/docs/getting-started` includes `Accept: text/markdown`, the rewrite routes it to `/docs/md/getting-started`. A Route Handler at that path returns the Markdown response. Clients that do not send `text/markdown` in their `Accept` header continue to receive the normal HTML page.

**2. Create a Route Handler for the Markdown response:**

```ts filename="app/docs/md/[...slug]/route.ts" switcher
import { getDocsMd, generateDocsStaticParams } from '@/lib/docs'

export async function generateStaticParams() {
  return generateDocsStaticParams()
}

export async function GET(_: Request, ctx: RouteContext) {
  const { slug } = await ctx.params
  const mdDoc = await getDocsMd({ slug })

  if (mdDoc == null) {
    return new Response(null, { status: 404 })
  }

  return new Response(mdDoc, {
    headers: {
      'Content-Type': 'text/markdown; charset=utf-8',
      Vary: 'Accept',
    },
  })
}
```

```js filename="app/docs/md/[...slug]/route.js" switcher
import { getDocsMd, generateDocsStaticParams } from '@/lib/docs'

export async function generateStaticParams() {
  return generateDocsStaticParams()
}

export async function GET(_, { params }) {
  const { slug } = await params
  const mdDoc = await getDocsMd({ slug })

  if (mdDoc == null) {
    return new Response(null, { status: 404 })
  }

  return new Response(mdDoc, {
    headers: {
      'Content-Type': 'text/markdown; charset=utf-8',
      Vary: 'Accept',
    },
  })
}
```

The [`Vary: Accept`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Vary) response header tells caches that the response body depends on the `Accept` request header. Without it, a shared cache could serve a cached Markdown response to a browser (or vice versa). Most hosting providers already include the `Accept` header in their cache key, but setting `Vary` explicitly ensures correct behavior across all CDNs and proxy caches.

`generateStaticParams` lets you pre-render the Markdown variants at build time so they can be served from the edge without hitting the origin server on every request.

**3. Test it with `curl`:**

```bash
# Returns Markdown
curl -H "Accept: text/markdown" https://example.com/docs/getting-started

# Returns the normal HTML page
curl https://example.com/docs/getting-started
```

> **Good to know:**
>
> * The `/docs/md/...` route is still directly accessible without the rewrite. If you want to restrict it to only serve via the rewrite, use [`proxy`](/docs/app/api-reference/file-conventions/proxy) to block direct requests that don't include the expected `Accept` header.
> * For more advanced negotiation logic, you can use [`proxy`](/docs/app/api-reference/file-conventions/proxy) instead of rewrites for more flexibility.

### Consuming request payloads

Use Request [instance methods](https://developer.mozilla.org/en-US/docs/Web/API/Request#instance_methods) like `.json()`, `.formData()`, or `.text()` to access the request body.

`GET` and `HEAD` requests don’t carry a body.

```ts filename="/app/api/echo-body/route.ts" switcher
export async function POST(request: Request) {
  const res = await request.json()
  return Response.json({ res })
}
```

```js filename="/app/api/echo-body/route.js" switcher
export async function POST(request) {
  const res = await request.json()
  return Response.json({ res })
}
```

> **Good to know**: Validate data before passing it to other systems

```ts filename="/app/api/send-email/route.ts" switcher
import { sendMail, validateInputs } from '@/lib/email-transporter'

export async function POST(request: Request) {
  const formData = await request.formData()
  const email = formData.get('email')
  const contents = formData.get('contents')

  try {
    await validateInputs({ email, contents })
    const info = await sendMail({ email, contents })

    return Response.json({ messageId: info.messageId })
  } catch (reason) {
    const message =
      reason instanceof Error ? reason.message : 'Unexpected exception'

    return new Response(message, { status: 500 })
  }
}
```

```js filename="/app/api/send-email/route.js" switcher
import { sendMail, validateInputs } from '@/lib/email-transporter'

export async function POST(request) {
  const formData = await request.formData()
  const email = formData.get('email')
  const contents = formData.get('contents')

  try {
    await validateInputs({ email, contents })
    const info = await sendMail({ email, contents })

    return Response.json({ messageId: info.messageId })
  } catch (reason) {
    const message =
      reason instanceof Error ? reason.message : 'Unexpected exception'

    return new Response(message, { status: 500 })
  }
}
```

You can only read the request body once. Clone the request if you need to read it again:

```ts filename="/app/api/clone/route.ts" switcher
export async function POST(request: Request) {
  try {
    const clonedRequest = request.clone()

    await request.body()
    await clonedRequest.body()
    await request.body() // Throws error

    return new Response(null, { status: 204 })
  } catch {
    return new Response(null, { status: 500 })
  }
}
```

```js filename="/app/api/clone/route.js" switcher
export async function POST(request) {
  try {
    const clonedRequest = request.clone()

    await request.body()
    await clonedRequest.body()
    await request.body() // Throws error

    return new Response(null, { status: 204 })
  } catch {
    return new Response(null, { status: 500 })
  }
}
```

## Manipulating data

Route Handlers can transform, filter, and aggregate data from one or more sources. This keeps logic out of the frontend and avoids exposing internal systems.

You can also offload heavy computations to the server and reduce client battery and data usage.

```ts file="/app/api/weather/route.ts" switcher
import { parseWeatherData } from '@/lib/weather'

export async function POST(request: Request) {
  const body = await request.json()
  const searchParams = new URLSearchParams({ lat: body.lat, lng: body.lng })

  try {
    const weatherResponse = await fetch(`${weatherEndpoint}?${searchParams}`)

    if (!weatherResponse.ok) {
      /* handle error */
    }

    const weatherData = await weatherResponse.text()
    const payload = parseWeatherData.asJSON(weatherData)

    return new Response(payload, { status: 200 })
  } catch (reason) {
    const message =
      reason instanceof Error ? reason.message : 'Unexpected exception'

    return new Response(message, { status: 500 })
  }
}
```

```js file="/app/api/weather/route.js" switcher
import { parseWeatherData } from '@/lib/weather'

export async function POST(request) {
  const body = await request.json()
  const searchParams = new URLSearchParams({ lat: body.lat, lng: body.lng })

  try {
    const weatherResponse = await fetch(`${weatherEndpoint}?${searchParams}`)

    if (!weatherResponse.ok) {
      /* handle error */
    }

    const weatherData = await weatherResponse.text()
    const payload = parseWeatherData.asJSON(weatherData)

    return new Response(payload, { status: 200 })
  } catch (reason) {
    const message =
      reason instanceof Error ? reason.message : 'Unexpected exception'

    return new Response(message, { status: 500 })
  }
}
```

> **Good to know**: This example uses `POST` to avoid putting geo-location data in the URL. `GET` requests may be cached or logged, which could expose sensitive info.

## Proxying to a backend

You can use a Route Handler as a `proxy` to another backend. Add validation logic before forwarding the request.

```ts filename="/app/api/[...slug]/route.ts" switcher
import { isValidRequest } from '@/lib/utils'

export async function POST(request: Request, { params }) {
  const clonedRequest = request.clone()
  const isValid = await isValidRequest(clonedRequest)

  if (!isValid) {
    return new Response(null, { status: 400, statusText: 'Bad Request' })
  }

  const { slug } = await params
  const pathname = slug.join('/')
  const proxyURL = new URL(pathname, 'https://nextjs.org')
  const proxyRequest = new Request(proxyURL, request)

  try {
    return fetch(proxyRequest)
  } catch (reason) {
    const message =
      reason instanceof Error ? reason.message : 'Unexpected exception'

    return new Response(message, { status: 500 })
  }
}
```

```js filename="/app/api/[...slug]/route.js" switcher
import { isValidRequest } from '@/lib/utils'

export async function POST(request, { params }) {
  const clonedRequest = request.clone()
  const isValid = await isValidRequest(clonedRequest)

  if (!isValid) {
    return new Response(null, { status: 400, statusText: 'Bad Request' })
  }

  const { slug } = await params
  const pathname = slug.join('/')
  const proxyURL = new URL(pathname, 'https://nextjs.org')
  const proxyRequest = new Request(proxyURL, request)

  try {
    return fetch(proxyRequest)
  } catch (reason) {
    const message =
      reason instanceof Error ? reason.message : 'Unexpected exception'

    return new Response(message, { status: 500 })
  }
}
```

Or use:

* `proxy` [rewrites](#proxy)
* [`rewrites`](/docs/app/api-reference/config/next-config-js/rewrites) in `next.config.js`.

## NextRequest and NextResponse

Next.js extends the [`Request`](https://developer.mozilla.org/en-US/docs/Web/API/Request) and [`Response`](https://developer.mozilla.org/en-US/docs/Web/API/Response) Web APIs with methods that simplify common operations. These extensions are available in both Route Handlers and Proxy.

Both provide methods for reading and manipulating cookies.

`NextRequest` includes the [`nextUrl`](/docs/app/api-reference/functions/next-request#nexturl) property, which exposes parsed values from the incoming request, for example, it makes it easier to access request pathname and search params.

`NextResponse` provides helpers like `next()`, `json()`, `redirect()`, and `rewrite()`.

You can pass `NextRequest` to any function expecting `Request`. Likewise, you can return `NextResponse` where a `Response` is expected.

```ts filename="/app/echo-pathname/route.ts" switcher
import { type NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const nextUrl = request.nextUrl

  if (nextUrl.searchParams.get('redirect')) {
    return NextResponse.redirect(new URL('/', request.url))
  }

  if (nextUrl.searchParams.get('rewrite')) {
    return NextResponse.rewrite(new URL('/', request.url))
  }

  return NextResponse.json({ pathname: nextUrl.pathname })
}
```

```js filename="/app/echo-pathname/route.js" switcher
import { NextResponse } from 'next/server'

export async function GET(request) {
  const nextUrl = request.nextUrl

  if (nextUrl.searchParams.get('redirect')) {
    return NextResponse.redirect(new URL('/', request.url))
  }

  if (nextUrl.searchParams.get('rewrite')) {
    return NextResponse.rewrite(new URL('/', request.url))
  }

  return NextResponse.json({ pathname: nextUrl.pathname })
}
```

Learn more about [`NextRequest`](/docs/app/api-reference/functions/next-request) and [`NextResponse`](/docs/app/api-reference/functions/next-response).

## Webhooks and callback URLs

Use Route Handlers to receive event notifications from third-party applications.

For example, revalidate a route when content changes in a CMS. Configure the CMS to call a specific endpoint on changes.

```ts filename="/app/webhook/route.ts" switcher
import { type NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get('token')

  if (token !== process.env.REVALIDATE_SECRET_TOKEN) {
    return NextResponse.json({ success: false }, { status: 401 })
  }

  const tag = request.nextUrl.searchParams.get('tag')

  if (!tag) {
    return NextResponse.json({ success: false }, { status: 400 })
  }

  revalidateTag(tag)

  return NextResponse.json({ success: true })
}
```

```js filename="/app/webhook/route.js" switcher
import { NextResponse } from 'next/server'

export async function GET(request) {
  const token = request.nextUrl.searchParams.get('token')

  if (token !== process.env.REVALIDATE_SECRET_TOKEN) {
    return NextResponse.json({ success: false }, { status: 401 })
  }

  const tag = request.nextUrl.searchParams.get('tag')

  if (!tag) {
    return NextResponse.json({ success: false }, { status: 400 })
  }

  revalidateTag(tag)

  return NextResponse.json({ success: true })
}
```

Callback URLs are another use case. When a user completes a third-party flow, the third party sends them to a callback URL. Use a Route Handler to verify the response and decide where to redirect the user.

```ts filename="/app/auth/callback/route.ts" switcher
import { type NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get('session_token')
  const redirectUrl = request.nextUrl.searchParams.get('redirect_url')

  const response = NextResponse.redirect(new URL(redirectUrl, request.url))

  response.cookies.set({
    value: token,
    name: '_token',
    path: '/',
    secure: true,
    httpOnly: true,
    expires: undefined, // session cookie
  })

  return response
}
```

```js filename="/app/auth/callback/route.js" switcher
import { NextResponse } from 'next/server'

export async function GET(request) {
  const token = request.nextUrl.searchParams.get('session_token')
  const redirectUrl = request.nextUrl.searchParams.get('redirect_url')

  const response = NextResponse.redirect(new URL(redirectUrl, request.url))

  response.cookies.set({
    value: token,
    name: '_token',
    path: '/',
    secure: true,
    httpOnly: true,
    expires: undefined, // session cookie
  })

  return response
}
```

## Redirects

```ts filename="app/api/route.ts" switcher
import { redirect } from 'next/navigation'

export async function GET(request: Request) {
  redirect('https://nextjs.org/')
}
```

```js filename="app/api/route.js" switcher
import { redirect } from 'next/navigation'

export async function GET(request) {
  redirect('https://nextjs.org/')
}
```

Learn more about redirects in [`redirect`](/docs/app/api-reference/functions/redirect) and [`permanentRedirect`](/docs/app/api-reference/functions/permanentRedirect)

## Proxy

Only one `proxy` file is allowed per project. Use `config.matcher` to target specific paths. Learn more about [`proxy`](/docs/app/api-reference/file-conventions/proxy).

Use `proxy` to generate a response before the request reaches a route path.

```ts filename="proxy.ts" switcher
import { isAuthenticated } from '@lib/auth'

export const config = {
  matcher: '/api/:function*',
}

export function proxy(request: Request) {
  if (!isAuthenticated(request)) {
    return Response.json(
      { success: false, message: 'authentication failed' },
      { status: 401 }
    )
  }
}
```

```js filename="proxy.js" switcher
import { isAuthenticated } from '@lib/auth'

export const config = {
  matcher: '/api/:function*',
}

export function proxy(request) {
  if (!isAuthenticated(request)) {
    return Response.json(
      { success: false, message: 'authentication failed' },
      { status: 401 }
    )
  }
}
```

You can also proxy requests using `proxy`:

```ts filename="proxy.ts" switcher
import { NextResponse } from 'next/server'

export function proxy(request: Request) {
  if (request.nextUrl.pathname === '/proxy-this-path') {
    const rewriteUrl = new URL('https://nextjs.org')
    return NextResponse.rewrite(rewriteUrl)
  }
}
```

```js filename="proxy.js" switcher
import { NextResponse } from 'next/server'

export function proxy(request) {
  if (request.nextUrl.pathname === '/proxy-this-path') {
    const rewriteUrl = new URL('https://nextjs.org')
    return NextResponse.rewrite(rewriteUrl)
  }
}
```

Another type of response `proxy` can produce are redirects:

```ts filename="proxy.ts" switcher
import { NextResponse } from 'next/server'

export function proxy(request: Request) {
  if (request.nextUrl.pathname === '/v1/docs') {
    request.nextUrl.pathname = '/v2/docs'
    return NextResponse.redirect(request.nextUrl)
  }
}
```

```js filename="proxy.js" switcher
import { NextResponse } from 'next/server'

export function proxy(request) {
  if (request.nextUrl.pathname === '/v1/docs') {
    request.nextUrl.pathname = '/v2/docs'
    return NextResponse.redirect(request.nextUrl)
  }
}
```

## Security

### Working with headers

Be deliberate about where headers go, and avoid directly passing incoming request headers to the outgoing response.

* **Upstream request headers**: In Proxy, `NextResponse.next({ request: { headers } })` modifies the headers your server receives and does not expose them to the client.
* **Response headers**: `new Response(..., { headers })`, `NextResponse.json(..., { headers })`, `NextResponse.next({ headers })`, or `response.headers.set(...)` send headers back to the client. If sensitive values were appended to these headers, they will be visible to clients.

Learn more in [NextResponse headers in Proxy](/docs/app/api-reference/functions/next-response#next).

### Rate limiting

You can implement rate limiting in your Next.js backend. In addition to code-based checks, enable any rate limiting features provided by your host.

```ts filename="/app/resource/route.ts" switcher
import { NextResponse } from 'next/server'
import { checkRateLimit } from '@/lib/rate-limit'

export async function POST(request: Request) {
  const { rateLimited } = await checkRateLimit(request)

  if (rateLimited) {
    return NextResponse.json({ error: 'Rate limit exceeded' }, { status: 429 })
  }

  return new Response(null, { status: 204 })
}
```

```js filename="/app/resource/route.js" switcher
import { NextResponse } from 'next/server'
import { checkRateLimit } from '@/lib/rate-limit'

export async function POST(request) {
  const { rateLimited } = await checkRateLimit(request)

  if (rateLimited) {
    return NextResponse.json({ error: 'Rate limit exceeded' }, { status: 429 })
  }

  return new Response(null, { status: 204 })
}
```

### Verify payloads

Never trust incoming request data. Validate content type and size, and sanitize against XSS before use.

Use timeouts to prevent abuse and protect server resources.

Store user-generated static assets in dedicated services. When possible, upload them from the browser and store the returned URI in your database to reduce request size.

### Access to protected resources

Always verify credentials before granting access. Do not rely on proxy alone for authentication and authorization.

Remove sensitive or unnecessary data from responses and backend logs.

Rotate credentials and API keys regularly.

## Preflight Requests

Preflight requests use the `OPTIONS` method to ask the server if a request is allowed based on origin, method, and headers.

If `OPTIONS` is not defined, Next.js adds it automatically and sets the `Allow` header based on the other defined methods.

* [CORS](/docs/app/api-reference/file-conventions/route#cors)

## Library patterns

Community libraries often use the factory pattern for Route Handlers.

```ts filename="/app/api/[...path]/route.ts"
import { createHandler } from 'third-party-library'

const handler = createHandler({
  /* library-specific options */
})

export const GET = handler
// or
export { handler as POST }
```

This creates a shared handler for `GET` and `POST` requests. The library customizes behavior based on the `method` and `pathname` in the request.

Libraries can also provide a `proxy` factory.

```ts filename="proxy.ts"
import { createMiddleware } from 'third-party-library'

export default createMiddleware()
```

> **Good to know**: Third-party libraries may still refer to `proxy` as `middleware`.

## More examples

See more examples on using [Router Handlers](/docs/app/api-reference/file-conventions/route#examples) and the [`proxy`](/docs/app/api-reference/file-conventions/proxy#examples) API references.

These examples include, working with [Cookies](/docs/app/api-reference/file-conventions/route#cookies), [Headers](/docs/app/api-reference/file-conventions/route#headers), [Streaming](/docs/app/api-reference/file-conventions/route#streaming), Proxy [negative matching](/docs/app/api-reference/file-conventions/proxy#negative-matching), and other useful code snippets.

## Caveats

### Server Components

Fetch data in Server Components directly from its source, not via Route Handlers.

For Server Components prerendered at build time, using Route Handlers will fail the build step. This is because, while building there is no server listening for these requests.

For Server Components rendered on demand, fetching from Route Handlers is slower due to the extra HTTP round trip between the handler and the render process.

> A server side `fetch` request uses absolute URLs. This implies an HTTP round trip, to an external server. During development, your own development server acts as the external server. At build time there is no server, and at runtime, the server is available through your public facing domain.

Server Components cover most data-fetching needs. However, fetching data client side might be necessary for:

* Data that depends on client-only Web APIs:
  * Geo-location API
  * Storage API
  * Audio API
  * File API
* Frequently polled data

For these, use community libraries like [`swr`](https://swr.vercel.app/) or [`react-query`](https://tanstack.com/query/latest/docs/framework/react/overview).

### Server Actions

Server Actions let you run server-side code from the client. Their primary purpose is to mutate data from your frontend client.

Server Actions are queued. Using them for data fetching introduces sequential execution.

### `export` mode

`export` mode outputs a static site without a runtime server. Features that require the Next.js runtime are [not supported](/docs/app/guides/static-exports#unsupported-features), because this mode produces a static site, and no runtime server.

In `export mode`, only `GET` Route Handlers are supported, in combination with the [`dynamic`](/docs/app/guides/caching-without-cache-components#dynamic) route segment config, set to `'force-static'`.

This can be used to generate static HTML, JSON, TXT, or other files.

```js filename="app/hello-world/route.ts"
export const dynamic = 'force-static'

export function GET() {
  return new Response('Hello World', { status: 200 })
}
```

### Deployment environment

Some hosts deploy Route Handlers as lambda functions. This means:

* Route Handlers cannot share data between requests.
* The environment may not support writing to File System.
* Long-running handlers may be terminated due to timeouts.
* WebSockets won’t work because the connection closes on timeout, or after the response is generated.
## API Reference

Learn more about Route Handlers, Proxy, and Rewrites

- [route.js](/docs/app/api-reference/file-conventions/route)
  - API reference for the route.js special file.
- [proxy.js](/docs/app/api-reference/file-conventions/proxy)
  - API reference for the proxy.js file.
- [rewrites](/docs/app/api-reference/config/next-config-js/rewrites)
  - Add rewrites to your Next.js app.

---
title: Caching (Previous Model)
description: Learn how to cache and revalidate data using fetch options, unstable_cache, and route segment configs for projects not using Cache Components.
url: "https://nextjs.org/docs/app/guides/caching-without-cache-components"
version: 16.2.6
---

# Caching (Previous Model)

> This guide assumes you are **not** using [Cache Components](/docs/app/getting-started/caching) which was introduced in version 16 under the [`cacheComponents` flag](/docs/app/api-reference/config/next-config-js/cacheComponents).

## Caching `fetch` requests

By default, [`fetch`](/docs/app/api-reference/functions/fetch) requests are not cached. You can cache individual requests by setting the `cache` option to `'force-cache'`.

```tsx filename="app/page.tsx" switcher
export default async function Page() {
  const data = await fetch('https://...', { cache: 'force-cache' })
}
```

```jsx filename="app/page.jsx" switcher
export default async function Page() {
  const data = await fetch('https://...', { cache: 'force-cache' })
}
```

See the [`fetch` API reference](/docs/app/api-reference/functions/fetch) to learn more.

### `unstable_cache` for non-`fetch` functions

`unstable_cache` allows you to cache the result of database queries and other async functions that don't use `fetch`. Wrap `unstable_cache` around the function:

```ts filename="app/lib/data.ts" switcher
import { unstable_cache } from 'next/cache'
import { db } from '@/lib/db'

export const getCachedUser = unstable_cache(
  async (id: string) => {
    return db
      .select()
      .from(users)
      .where(eq(users.id, id))
      .then((res) => res[0])
  },
  ['user'], // cache key prefix
  {
    tags: ['user'],
    revalidate: 3600,
  }
)
```

```js filename="app/lib/data.js" switcher
import { unstable_cache } from 'next/cache'
import { db } from '@/lib/db'

export const getCachedUser = unstable_cache(
  async (id) => {
    return db
      .select()
      .from(users)
      .where(eq(users.id, id))
      .then((res) => res[0])
  },
  ['user'], // cache key prefix
  {
    tags: ['user'],
    revalidate: 3600,
  }
)
```

The third argument accepts:

* `tags`: an array of tags for on-demand revalidation with `revalidateTag`.
* `revalidate`: the number of seconds before the cache is revalidated.

See the [`unstable_cache` API reference](/docs/app/api-reference/functions/unstable_cache) to learn more.

### Route segment config

You can configure caching behavior at the route level by exporting config options from a [Page](/docs/app/api-reference/file-conventions/page), [Layout](/docs/app/api-reference/file-conventions/layout), or [Route Handler](/docs/app/api-reference/file-conventions/route).

#### `dynamic`

Change the dynamic behavior of a layout or page to fully static or fully dynamic.

```tsx filename="layout.tsx | page.tsx | route.ts" switcher
export const dynamic = 'auto'
// 'auto' | 'force-dynamic' | 'error' | 'force-static'
```

```jsx filename="layout.js | page.js | route.js" switcher
export const dynamic = 'auto'
// 'auto' | 'force-dynamic' | 'error' | 'force-static'
```

* **`'auto'`** (default): The default option to cache as much as possible without preventing any components from opting into dynamic behavior.
* **`'force-dynamic'`**: Force [dynamic rendering](/docs/app/glossary#dynamic-rendering), which will result in routes being rendered for each user at request time. This option is equivalent to:
  * Setting the option of every `fetch()` request in a layout or page to `{ cache: 'no-store', next: { revalidate: 0 } }`.
  * Setting the segment config to `export const fetchCache = 'force-no-store'`
* **`'error'`**: Force prerendering and cache the data of a layout or page by causing an error if any components use Request-time APIs or uncached data. This option is equivalent to:
  * `getStaticProps()` in the `pages` directory.
  * Setting the option of every `fetch()` request in a layout or page to `{ cache: 'force-cache' }`.
  * Setting the segment config to `fetchCache = 'only-cache'`.
* **`'force-static'`**: Force prerendering and cache the data of a layout or page by forcing [`cookies`](/docs/app/api-reference/functions/cookies), [`headers()`](/docs/app/api-reference/functions/headers) and [`useSearchParams()`](/docs/app/api-reference/functions/use-search-params) to return empty values. It is possible to [`revalidate`](#route-segment-config-revalidate), [`revalidatePath`](/docs/app/api-reference/functions/revalidatePath), or [`revalidateTag`](/docs/app/api-reference/functions/revalidateTag), in pages or layouts rendered with `force-static`.

#### `fetchCache`

This is an advanced option that should only be used if you specifically need to override the default behavior.

By default, Next.js **will cache** any `fetch()` requests that are reachable **before** any Request-time APIs are used and **will not cache** `fetch` requests that are discovered **after** Request-time APIs are used.

`fetchCache` allows you to override the default `cache` option of all `fetch` requests in a layout or page.

```tsx filename="layout.tsx | page.tsx | route.ts" switcher
export const fetchCache = 'auto'
// 'auto' | 'default-cache' | 'only-cache'
// 'force-cache' | 'force-no-store' | 'default-no-store' | 'only-no-store'
```

```jsx filename="layout.js | page.js | route.js" switcher
export const fetchCache = 'auto'
// 'auto' | 'default-cache' | 'only-cache'
// 'force-cache' | 'force-no-store' | 'default-no-store' | 'only-no-store'
```

* **`'auto'`** (default): The default option to cache `fetch` requests before Request-time APIs with the `cache` option they provide and not cache `fetch` requests after Request-time APIs.
* **`'default-cache'`**: Allow any `cache` option to be passed to `fetch` but if no option is provided then set the `cache` option to `'force-cache'`. This means that even `fetch` requests after Request-time APIs are considered static.
* **`'only-cache'`**: Ensure all `fetch` requests opt into caching by changing the default to `cache: 'force-cache'` if no option is provided and causing an error if any `fetch` requests use `cache: 'no-store'`.
* **`'force-cache'`**: Ensure all `fetch` requests opt into caching by setting the `cache` option of all `fetch` requests to `'force-cache'`.
* **`'default-no-store'`**: Allow any `cache` option to be passed to `fetch` but if no option is provided then set the `cache` option to `'no-store'`. This means that even `fetch` requests before Request-time APIs are considered dynamic.
* **`'only-no-store'`**: Ensure all `fetch` requests opt out of caching by changing the default to `cache: 'no-store'` if no option is provided and causing an error if any `fetch` requests use `cache: 'force-cache'`
* **`'force-no-store'`**: Ensure all `fetch` requests opt out of caching by setting the `cache` option of all `fetch` requests to `'no-store'`. This forces all `fetch` requests to be re-fetched every request even if they provide a `'force-cache'` option.

##### Cross-route segment behavior

* Any options set across each layout and page of a single route need to be compatible with each other.
  * If both the `'only-cache'` and `'force-cache'` are provided, then `'force-cache'` wins. If both `'only-no-store'` and `'force-no-store'` are provided, then `'force-no-store'` wins. The force option changes the behavior across the route so a single segment with `'force-*'` would prevent any errors caused by `'only-*'`.
  * The intention of the `'only-*'` and `'force-*'` options is to guarantee the whole route is either fully static or fully dynamic. This means:
    * A combination of `'only-cache'` and `'only-no-store'` in a single route is not allowed.
    * A combination of `'force-cache'` and `'force-no-store'` in a single route is not allowed.
  * A parent cannot provide `'default-no-store'` if a child provides `'auto'` or `'*-cache'` since that could make the same fetch have different behavior.
* It is generally recommended to leave shared parent layouts as `'auto'` and customize the options where child segments diverge.

## Time-based revalidation

Use the `next.revalidate` option on `fetch` to revalidate data after a specified number of seconds:

```tsx filename="app/page.tsx" switcher
export default async function Page() {
  const data = await fetch('https://...', { next: { revalidate: 3600 } })
}
```

```jsx filename="app/page.jsx" switcher
export default async function Page() {
  const data = await fetch('https://...', { next: { revalidate: 3600 } })
}
```

For non-`fetch` functions, `unstable_cache` accepts a `revalidate` option in its configuration (see [example above](#unstable_cache-for-non-fetch-functions)).

### Route segment config `revalidate`

Set the default revalidation time for a layout or page. This option does not override the `revalidate` value set by individual `fetch` requests.

```tsx filename="layout.tsx | page.tsx | route.ts" switcher
export const revalidate = false
// false | 0 | number
```

```jsx filename="layout.js | page.js | route.js" switcher
export const revalidate = false
// false | 0 | number
```

* **`false`** (default): The default heuristic to cache any `fetch` requests that set their `cache` option to `'force-cache'` or are discovered before a Request-time API is used. Semantically equivalent to `revalidate: Infinity` which effectively means the resource should be cached indefinitely. It is still possible for individual `fetch` requests to use `cache: 'no-store'` or `revalidate: 0` to avoid being cached and make the route dynamically rendered. Or set `revalidate` to a positive number lower than the route default to increase the revalidation frequency of a route.
* **`0`**: Ensure a layout or page is always dynamically rendered even if no Request-time APIs or uncached data fetches are discovered. This option changes the default of `fetch` requests that do not set a `cache` option to `'no-store'` but leaves `fetch` requests that opt into `'force-cache'` or use a positive `revalidate` as is.
* **`number`**: (in seconds) Set the default revalidation frequency of a layout or page to `n` seconds.

> **Good to know**:
>
> * The revalidate value needs to be statically analyzable. For example `revalidate = 600` is valid, but `revalidate = 60 * 10` is not.
> * The revalidate value is not available when using `runtime = 'edge'`.
> * In Development, Pages are *always* rendered on-demand and are never cached. This allows you to see changes immediately without waiting for a revalidation period to pass.

#### Revalidation frequency

* The lowest `revalidate` across each layout and page of a single route will determine the revalidation frequency of the *entire* route. This ensures that child pages are revalidated as frequently as their parent layouts.
* Individual `fetch` requests can set a lower `revalidate` than the route's default `revalidate` to increase the revalidation frequency of the entire route. This allows you to dynamically opt-in to more frequent revalidation for certain routes based on some criteria.

## On-demand revalidation

To revalidate cached data after an event, use [`revalidateTag`](/docs/app/api-reference/functions/revalidateTag) or [`revalidatePath`](/docs/app/api-reference/functions/revalidatePath) in a [Server Action](/docs/app/getting-started/mutating-data) or [Route Handler](/docs/app/api-reference/file-conventions/route).

### Tagging cached data

Tag `fetch` requests with `next.tags` to enable on-demand cache invalidation:

```tsx filename="app/lib/data.ts" switcher
export async function getUserById(id: string) {
  const data = await fetch(`https://...`, {
    next: { tags: ['user'] },
  })
}
```

```jsx filename="app/lib/data.js" switcher
export async function getUserById(id) {
  const data = await fetch(`https://...`, {
    next: { tags: ['user'] },
  })
}
```

For non-`fetch` functions, `unstable_cache` also accepts a `tags` option (see [example above](#unstable_cache-for-non-fetch-functions)).

### `revalidateTag`

Invalidate cached data by tag using [`revalidateTag`](/docs/app/api-reference/functions/revalidateTag):

```tsx filename="app/lib/actions.ts" switcher
import { revalidateTag } from 'next/cache'

export async function updateUser(id: string) {
  // Mutate data
  revalidateTag('user')
}
```

```jsx filename="app/lib/actions.js" switcher
import { revalidateTag } from 'next/cache'

export async function updateUser(id) {
  // Mutate data
  revalidateTag('user')
}
```

### `revalidatePath`

Invalidate all cached data for a specific route path using [`revalidatePath`](/docs/app/api-reference/functions/revalidatePath):

```tsx filename="app/lib/actions.ts" switcher
import { revalidatePath } from 'next/cache'

export async function updateUser(id: string) {
  // Mutate data
  revalidatePath('/profile')
}
```

```jsx filename="app/lib/actions.js" switcher
import { revalidatePath } from 'next/cache'

export async function updateUser(id) {
  // Mutate data
  revalidatePath('/profile')
}
```

## Deduplicating requests

If you are not using `fetch` (which is [automatically memoized](/docs/app/api-reference/functions/fetch#memoization)), and instead using an ORM or database directly, you can wrap your data access with the [React `cache`](https://react.dev/reference/react/cache) function to deduplicate requests within a single render pass:

```tsx filename="app/lib/data.ts" switcher
import { cache } from 'react'
import { db, posts, eq } from '@/lib/db'

export const getPost = cache(async (id: string) => {
  const post = await db.query.posts.findFirst({
    where: eq(posts.id, parseInt(id)),
  })
})
```

```jsx filename="app/lib/data.js" switcher
import { cache } from 'react'
import { db, posts, eq } from '@/lib/db'

export const getPost = cache(async (id) => {
  const post = await db.query.posts.findFirst({
    where: eq(posts.id, parseInt(id)),
  })
})
```

## Preloading data

You can preload data by creating a utility function that you eagerly call above blocking requests. This lets you initiate data fetching early, so the data is already available by the time the component renders.

Combine the [`server-only` package](https://www.npmjs.com/package/server-only) with React's [`cache`](https://react.dev/reference/react/cache) to create a reusable preload utility:

```ts filename="utils/get-item.ts" switcher
import { cache } from 'react'
import 'server-only'

export const getItem = cache(async (id: string) => {
  // ...
})

export const preload = (id: string) => {
  void getItem(id)
}
```

```js filename="utils/get-item.js" switcher
import { cache } from 'react'
import 'server-only'

export const getItem = cache(async (id) => {
  // ...
})

export const preload = (id) => {
  void getItem(id)
}
```

Then call `preload()` before any blocking work so the data starts loading immediately:

```tsx filename="app/item/[id]/page.tsx" switcher
import { getItem, preload, checkIsAvailable } from '@/lib/data'

export default async function Page({
  params,
}: {
  params: Promise
}) {
  const { id } = await params
  // Start loading item data
  preload(id)
  // Perform another asynchronous task
  const isAvailable = await checkIsAvailable()

  return isAvailable ?  : null
}

async function Item({ id }: { id: string }) {
  const result = await getItem(id)
  // ...
}
```

```jsx filename="app/item/[id]/page.js" switcher
import { getItem, preload, checkIsAvailable } from '@/lib/data'

export default async function Page({ params }) {
  const { id } = await params
  // Start loading item data
  preload(id)
  // Perform another asynchronous task
  const isAvailable = await checkIsAvailable()

  return isAvailable ?  : null
}

async function Item({ id }) {
  const result = await getItem(id)
  // ...
}
```

---
title: CDN Caching
description: Learn how CDN caching works with Next.js, including what works today, cache variability, and the direction toward pathname-based cache keying.
url: "https://nextjs.org/docs/app/guides/cdn-caching"
version: 16.2.6
---

# CDN Caching

Next.js sets standard `Cache-Control` headers that CDNs can use to cache responses at the edge. This page covers what works today, where CDN caching is challenging, and the direction toward eliminating custom-header dependencies.

## What Works Today

### Cache-Control headers

Next.js sets `Cache-Control` headers based on the rendering strategy of each route:

* **Static pages** (no revalidation): `s-maxage=31536000` (one year)
* **ISR pages** (time-based revalidation): `s-maxage={revalidate}, stale-while-revalidate={expire - revalidate}`. The default `expire` is one year, so `stale-while-revalidate` is included in the response header by default. You can customize this with [`cacheLife`](/docs/app/api-reference/functions/cacheLife).
* **Dynamic pages** (no caching): `private, no-cache, no-store, max-age=0, must-revalidate`

CDNs that respect `s-maxage` and `stale-while-revalidate` can cache static and ISR pages at the edge. However, CDN-level caching alone does not support on-demand revalidation ([`revalidateTag()`](/docs/app/api-reference/functions/revalidateTag) / [`revalidatePath()`](/docs/app/api-reference/functions/revalidatePath)): those calls invalidate the Next.js server cache, but the CDN will continue serving its cached copy until the `s-maxage` TTL expires. To propagate on-demand revalidation to the CDN, trigger CDN purges alongside your revalidation call. A common pattern is: call `revalidateTag()`/`revalidatePath()` to invalidate the Next.js server cache, then call your CDN purge API for the affected keys (including both HTML and RSC variants).

### Static assets

Static assets (JavaScript, CSS, images, fonts) served from `/_next/static/` include content hashes in their filenames and have a 1 year `max-age` and `immutable` directive: `public,max-age=31536000,immutable`

You can use [`assetPrefix`](/docs/app/api-reference/config/next-config-js/assetPrefix) to serve static assets from a different domain or CDN origin.

### Static prefetches (PPR-enabled routes)

When a route has Partial Prerendering enabled and the `next-router-prefetch` header is set (indicating a static prefetch), the response is deterministic: it returns the same prerendered content regardless of the client's router state. The `next-router-state-tree` header is not parsed for these requests, so it does not affect the response.

For PPR-enabled routes, a CDN can cache static prefetch responses if it:

1. Includes the `_rsc` search parameter in the cache key (to distinguish prefetch variants from HTML responses).
2. Respects the `Cache-Control` headers Next.js sets on the response.

> **Good to know:** For routes without PPR, the `next-router-state-tree` header is read during prefetch requests to determine which segments to include, which increases cache `vary` as it passes the current router state. When Cache Components is enabled, segment-level prefetches already use pathname-based routes (for example, `/page.segments/_tree.segment.rsc`), and CDNs can cache these with standard pathname-based cache keys.

## Where CDN Caching Is Challenging

App Router responses can vary based on several custom request headers. Next.js sets a `Vary` header on responses to signal this to CDNs:

* `rsc` — whether the request should return a React Server Components (RSC) payload instead of HTML
* `next-router-state-tree` — the client's current router state, used for targeted segment updates during dynamic navigations
* `next-router-prefetch` — whether this is a prefetch request
* `next-router-segment-prefetch` — the specific segment being prefetched
* `next-url` — added only for routes that use [interception routes](/docs/app/api-reference/file-conventions/intercepting-routes), carries the URL being intercepted

> **Good to know:** [`proxy.js`](/docs/app/api-reference/file-conventions/proxy) (previously Middleware) should run before the CDN cache so it remains the source of truth for auth, redirects, and rewrites. If your deployment places `proxy.js` behind the CDN, configure the cache layer to bypass caching for routes that depend on `proxy.js` decisions.

Many CDNs don't support `Vary` without additional configuration. Next.js addresses this with the `_rsc` search parameter: a hash of the relevant request header values that acts as a cache-key, ensuring different response variants get different cache keys. This ensures correct responses even on CDNs that ignore `Vary`.

## Handling Headers at the CDN

### What you can safely ignore

These headers can be omitted in specific cases without causing protocol errors. The server still returns a parseable response, but it may be larger or less targeted to the specific navigation:

**`next-router-state-tree`**: when omitted on non-prefetch RSC requests, the server returns a full payload instead of a targeted segment update.

**`next-router-segment-prefetch`**: when omitted on prefetch requests, the server falls back to a broader prefetch payload instead of a segment-specific one.

**`next-url`**: used for [interception routes](/docs/app/api-reference/file-conventions/intercepting-routes) to vary the response based on the referring page. If omitted, interception routes are not supported as the server doesn't know what original path to match against. The response returned is for regular navigation when `next-url` is omitted: the user sees the target page instead of the intercepted target page.

### What you must preserve

**The `rsc` header** must be forwarded from the client to the server. This header tells the server to return an RSC payload instead of HTML. If a CDN strips it, the server returns HTML when the client-side router expects RSC data, which breaks client-side navigation, causing browser navigations instead. The `Vary` header and `_rsc` parameter exist specifically to prevent CDNs from serving a cached HTML response to an RSC request (or vice versa).

**When `next-router-prefetch` is present, preserve both the prefetch header and the `_rsc` search parameter.** For prefetch flows, `_rsc` is a required cache-busting discriminator and should be treated as mandatory.

**The `_rsc` search parameter** must be included in the cache key. It distinguishes response variants (HTML vs. RSC, different prefetch types). Ensure your CDN does not strip query parameters from cache keys, as some CDNs do this by default. When the `experimental.validateRSCRequestHeaders` option is enabled and a RSC request arrives without the correct `_rsc` value, the server responds with a **307 redirect** to the URL with the correct hash. CDNs should follow this redirect. Platforms that compute the hash upstream can rewrite requests to include the correct `_rsc` before forwarding to avoid an extra round trip.

> **Good to know:** Today, `next-url` is included in the `_rsc` hash even during static prefetches. This means you cannot safely ignore it under the current scheme without potentially getting cache misses. The pathname-based direction described below resolves this gap.

## Direction: Pathname-Based Cache Keying

The Next.js team is working on moving all cache-affecting inputs into the URL pathname, eliminating the need for `Vary` on custom headers and removing the `_rsc` search parameter. This resolves the CDN caching challenges described above.

### How it works

The approach extends the routing scheme that [`output: 'export'`](/docs/app/guides/static-exports) and segment prefetches already use today. File extensions in the pathname identify the response type:

* **Full page RSC**: `/my/page.rsc` returns the RSC payload for the entire page
* **Segment RSC**: `/my/page.segments/path/to/segment.segment.rsc` returns the RSC payload for a specific segment

Under this model:

* **The pathname determines the cache key.** Anything in the pathname affects which response variant is returned.
* **Search parameters can be safely dropped** without affecting returned responses.
* **Standard HTTP cache headers** (`Cache-Control`, `max-age`, etc.) are respected as usual.
* **No `Vary` support needed** from the CDN.

A CDN would cache Next.js responses by using the pathname as the cache key, ignoring search parameters, and respecting standard `Cache-Control` headers. No need to understand `Vary`, inspect custom headers, or program edge logic.

### What changes for interception routes

Under the current scheme, `next-url` contributes to the `_rsc` hash, so dropping it causes cache misses. Under the pathname-based scheme, interception variability would be encoded in a search parameter (not the pathname):

* If a CDN preserves search params, interception works correctly.
* If a CDN drops search params, interception is not supported. It would gracefully degrade to the non-intercepted page, client-side navigations won't break.

This makes interception route support an opt-in CDN capability rather than a requirement.

### Current status

This direction extends patterns that are already operational in the codebase (segment prefetch paths, `output: 'export'` mode). It is in active design.

## CDN Feature Compatibility

For a full table showing the infrastructure primitives available on every major CDN (edge compute, key-value storage, blob storage, PPR resuming), see [Deploying to Platforms](/docs/app/guides/deploying-to-platforms#cdn-infrastructure-compatibility).

Related guides and references.

- [Deploying to Platforms](/docs/app/guides/deploying-to-platforms)
  - Understand which Next.js features require specific platform capabilities and how to choose the right deployment target.
- [Self-Hosting](/docs/app/guides/self-hosting)
  - Learn how to self-host your Next.js application on a Node.js server, Docker image, or static HTML files (static exports).
- [Streaming](/docs/app/guides/streaming)
  - Learn how streaming works in Next.js and how to use it to progressively render UI as data becomes available.
- [assetPrefix](/docs/app/api-reference/config/next-config-js/assetPrefix)
  - Learn how to use the assetPrefix config option to configure your CDN.

---
title: CI Build Caching
description: Learn how to configure CI to cache Next.js builds
url: "https://nextjs.org/docs/app/guides/ci-build-caching"
version: 16.2.6
---

# CI Build Caching

To improve build performance, Next.js saves a cache to `.next/cache` that is shared between builds.

To take advantage of this cache in Continuous Integration (CI) environments, your CI workflow will need to be configured to correctly persist the cache between builds.

> If your CI is not configured to persist `.next/cache` between builds, you may see a [No Cache Detected](/docs/messages/no-cache) error.

Here are some example cache configurations for common CI providers:

## Vercel

Next.js caching is automatically configured for you. There's no action required on your part. If you are using Turborepo on Vercel, [learn more here](https://vercel.com/docs/monorepos/turborepo).

## CircleCI

Edit your `save_cache` step in `.circleci/config.yml` to include `.next/cache`:

```yaml
steps:
  - save_cache:
      key: dependency-cache-{{ checksum "yarn.lock" }}
      paths:
        - ./node_modules
        - ./.next/cache
```

If you do not have a `save_cache` key, please follow CircleCI's [documentation on setting up build caching](https://circleci.com/docs/2.0/caching/).

## Travis CI

Add or merge the following into your `.travis.yml`:

```yaml
cache:
  directories:
    - $HOME/.cache/yarn
    - node_modules
    - .next/cache
```

## GitLab CI

Add or merge the following into your `.gitlab-ci.yml`:

```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - node_modules/
    - .next/cache/
```

## Netlify CI

Use [Netlify Plugins](https://www.netlify.com/products/build/plugins/) with [`@netlify/plugin-nextjs`](https://www.npmjs.com/package/@netlify/plugin-nextjs).

## AWS CodeBuild

Add (or merge in) the following to your `buildspec.yml`:

```yaml
cache:
  paths:
    - 'node_modules/**/*' # Cache `node_modules` for faster `yarn` or `npm i`
    - '.next/cache/**/*' # Cache Next.js for faster application rebuilds
```

## GitHub Actions

Using GitHub's [actions/cache](https://github.com/actions/cache), add the following step in your workflow file:

```yaml
uses: actions/cache@v4
with:
  # See here for caching with `yarn`, `bun` or other package managers https://github.com/actions/cache/blob/main/examples.md or you can leverage caching with actions/setup-node https://github.com/actions/setup-node
  path: |
    ~/.npm
    ${{ github.workspace }}/.next/cache
  # Generate a new cache whenever packages or source files change.
  key: ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx') }}
  # If source files changed but packages didn't, rebuild from a prior cache.
  restore-keys: |
    ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-
```

## Bitbucket Pipelines

Add or merge the following into your `bitbucket-pipelines.yml` at the top level (same level as `pipelines`):

```yaml
definitions:
  caches:
    nextcache: .next/cache
```

Then reference it in the `caches` section of your pipeline's `step`:

```yaml
- step:
    name: your_step_name
    caches:
      - node
      - nextcache
```

## Heroku

Using Heroku's [custom cache](https://devcenter.heroku.com/articles/nodejs-support#custom-caching), add a `cacheDirectories` array in your top-level package.json:

```javascript
"cacheDirectories": [".next/cache"]
```

## Azure Pipelines

Using Azure Pipelines' [Cache task](https://docs.microsoft.com/en-us/azure/devops/pipelines/tasks/utility/cache), add the following task to your pipeline yaml file somewhere prior to the task that executes `next build`:

```yaml
- task: Cache@2
  displayName: 'Cache .next/cache'
  inputs:
    key: next | $(Agent.OS) | yarn.lock
    path: '$(System.DefaultWorkingDirectory)/.next/cache'
```

## Jenkins (Pipeline)

Using Jenkins' [Job Cacher](https://www.jenkins.io/doc/pipeline/steps/jobcacher/) plugin, add the following build step to your `Jenkinsfile` where you would normally run `next build` or `npm install`:

```yaml
stage("Restore npm packages") {
    steps {
        // Writes lock-file to cache based on the GIT_COMMIT hash
        writeFile file: "next-lock.cache", text: "$GIT_COMMIT"

        cache(caches: [
            arbitraryFileCache(
                path: "node_modules",
                includes: "**/*",
                cacheValidityDecidingFile: "package-lock.json"
            )
        ]) {
            sh "npm install"
        }
    }
}
stage("Build") {
    steps {
        // Writes lock-file to cache based on the GIT_COMMIT hash
        writeFile file: "next-lock.cache", text: "$GIT_COMMIT"

        cache(caches: [
            arbitraryFileCache(
                path: ".next/cache",
                includes: "**/*",
                cacheValidityDecidingFile: "next-lock.cache"
            )
        ]) {
            // aka `next build`
            sh "npm run build"
        }
    }
}
```

---
title: Content Security Policy
description: Learn how to set a Content Security Policy (CSP) for your Next.js application.
url: "https://nextjs.org/docs/app/guides/content-security-policy"
version: 16.2.6
---

# Content Security Policy

[Content Security Policy (CSP)](https://developer.mozilla.org/docs/Web/HTTP/CSP) is important to guard your Next.js application against various security threats such as cross-site scripting (XSS), clickjacking, and other code injection attacks.

By using CSP, developers can specify which origins are permissible for content sources, scripts, stylesheets, images, fonts, objects, media (audio, video), iframes, and more.

Examples

* [Strict CSP](https://github.com/vercel/next.js/tree/canary/examples/with-strict-csp)

## Nonces

A [nonce](https://developer.mozilla.org/docs/Web/HTML/Global_attributes/nonce) is a unique, random string of characters created for a one-time use. It is used in conjunction with CSP to selectively allow certain inline scripts or styles to execute, bypassing strict CSP directives.

### Why use a nonce?

CSP can block both inline and external scripts to prevent attacks. A nonce lets you safely allow specific scripts to run—only if they include the matching nonce value.

If an attacker wanted to load a script into your page, they'd need to guess the nonce value. That's why the nonce must be unpredictable and unique for every request.

### Adding a nonce with Proxy

[Proxy](/docs/app/api-reference/file-conventions/proxy) enables you to add headers and generate nonces before the page renders.

Every time a page is viewed, a fresh nonce should be generated. This means that you **must use [dynamic rendering](/docs/app/glossary#dynamic-rendering) to add nonces**.

For example:

> **Good to know**: In development, `'unsafe-eval'` is required because React uses `eval` to provide enhanced debugging information, such as reconstructing server-side error stacks in the browser. `unsafe-eval` is not required for production. Neither React nor Next.js use `eval` in production by default.

```ts filename="proxy.ts" switcher
import { NextRequest, NextResponse } from 'next/server'

export function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')
  const isDev = process.env.NODE_ENV === 'development'
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ''};
    style-src 'self' 'nonce-${nonce}';
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
`
  // Replace newline characters and spaces
  const contentSecurityPolicyHeaderValue = cspHeader
    .replace(/\s{2,}/g, ' ')
    .trim()

  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)

  requestHeaders.set(
    'Content-Security-Policy',
    contentSecurityPolicyHeaderValue
  )

  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  })
  response.headers.set(
    'Content-Security-Policy',
    contentSecurityPolicyHeaderValue
  )

  return response
}
```

```js filename="proxy.js" switcher
import { NextResponse } from 'next/server'

export function proxy(request) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')
  const isDev = process.env.NODE_ENV === 'development'
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ''};
    style-src 'self' 'nonce-${nonce}';
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
`
  // Replace newline characters and spaces
  const contentSecurityPolicyHeaderValue = cspHeader
    .replace(/\s{2,}/g, ' ')
    .trim()

  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)
  requestHeaders.set(
    'Content-Security-Policy',
    contentSecurityPolicyHeaderValue
  )

  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  })
  response.headers.set(
    'Content-Security-Policy',
    contentSecurityPolicyHeaderValue
  )

  return response
}
```

By default, Proxy runs on all requests. You can filter Proxy to run on specific paths using a [`matcher`](/docs/app/api-reference/file-conventions/proxy#matcher).

We recommend ignoring matching prefetches (from `next/link`) and static assets that don't need the CSP header.

```ts filename="proxy.ts" switcher
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    {
      source: '/((?!api|_next/static|_next/image|favicon.ico).*)',
      missing: [
        { type: 'header', key: 'next-router-prefetch' },
        { type: 'header', key: 'purpose', value: 'prefetch' },
      ],
    },
  ],
}
```

```js filename="proxy.js" switcher
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    {
      source: '/((?!api|_next/static|_next/image|favicon.ico).*)',
      missing: [
        { type: 'header', key: 'next-router-prefetch' },
        { type: 'header', key: 'purpose', value: 'prefetch' },
      ],
    },
  ],
}
```

### How nonces work in Next.js

To use a nonce, your page must be **dynamically rendered**. This is because Next.js applies nonces during **server-side rendering**, based on the CSP header present in the request. Static pages are generated at build time, when no request or response headers exist—so no nonce can be injected.

Here’s how nonce support works in a dynamically rendered page:

1. **Proxy generates a nonce**: Your proxy creates a unique nonce for the request, adds it to your `Content-Security-Policy` header, and also sets it in a custom `x-nonce` header.
2. **Next.js extracts the nonce**: During rendering, Next.js parses the `Content-Security-Policy` header and extracts the nonce using the `'nonce-{value}'` pattern.
3. **Nonce is applied automatically**: Next.js attaches the nonce to:
   * Framework scripts (React, Next.js runtime)
   * Page-specific JavaScript bundles
   * Inline styles and scripts generated by Next.js
   * Any `
```

Or by using the `dangerouslySetInnerHTML` property:

```jsx

```

Or by using the `dangerouslySetInnerHTML` property:

```jsx

```

> **Warning**: An `id` property must be assigned for inline scripts in order for Next.js to track and optimize the script.

### Executing Additional Code

Event handlers can be used with the Script component to execute additional code after a certain event occurs:

* `onLoad`: Execute code after the script has finished loading.
* `onReady`: Execute code after the script has finished loading and every time the component is mounted.
* `onError`: Execute code if the script fails to load.

These handlers will only work when `next/script` is imported and used inside of a [Client Component](/docs/app/getting-started/server-and-client-components) where `"use client"` is defined as the first line of code:

```tsx filename="pages/index.tsx" switcher
import Script from 'next/script'

export default function Page() {
  return (
    <>
       {
          console.log('Script has loaded')
        }}
      />

  )
}
```

```jsx filename="pages/index.js" switcher
import Script from 'next/script'

export default function Page() {
  return (
    <>
       {
          console.log('Script has loaded')
        }}
      />

  )
}
```

Refer to the [`next/script`](/docs/pages/api-reference/components/script#onload) API reference to learn more about each event handler and view examples.

### Additional Attributes

There are many DOM attributes that can be assigned to a `` element that are not used by the Script component, like [`nonce`](https://developer.mozilla.org/docs/Web/HTML/Global_attributes/nonce) or [custom data attributes](https://developer.mozilla.org/docs/Web/HTML/Global_attributes/data-*). Including any additional attributes will automatically forward it to the final, optimized `` element that is included in the HTML.

```tsx filename="pages/index.tsx" switcher
import Script from 'next/script'

export default function Page() {
  return (
    <>

  )
}
```

```jsx filename="pages/index.js" switcher
import Script from 'next/script'

export default function Page() {
  return (
    <>

  )
}
```
## API Reference

Learn more about the next/script API.

- [Script Component](/docs/app/api-reference/components/script)
  - Optimize third-party scripts in your Next.js application using the built-in `next/script` Component.

---
title: Self-Hosting
description: Learn how to self-host your Next.js application on a Node.js server, Docker image, or static HTML files (static exports).
url: "https://nextjs.org/docs/pages/guides/self-hosting"
version: 16.2.6
router: Pages Router
---

# Self-Hosting

When [deploying](/docs/app/getting-started/deploying) your Next.js app, you may want to configure how different features are handled based on your infrastructure.

> **🎥 Watch:** Learn more about self-hosting Next.js → [YouTube (45 minutes)](https://www.youtube.com/watch?v=sIVL4JMqRfc).

## Reverse Proxy

When self-hosting, it's recommended to use a reverse proxy (like nginx) in front of your Next.js server rather than exposing it directly to the internet. A reverse proxy can handle malformed requests, slow connection attacks, payload size limits, rate limiting, and other security concerns, offloading these tasks from the Next.js server. This allows the server to dedicate its resources to rendering rather than request validation.

## Image Optimization

[Image Optimization](/docs/app/api-reference/components/image) through `next/image` works self-hosted with zero configuration when deploying using `next start`. If you would prefer to have a separate service to optimize images, you can [configure an image loader](/docs/app/api-reference/components/image#loader).

Image Optimization can be used with a [static export](/docs/app/guides/static-exports#image-optimization) by defining a custom image loader in `next.config.js`. Note that images are optimized at runtime, not during the build.

> **Good to know:**
>
> * On glibc-based Linux systems, Image Optimization may require [additional configuration](https://sharp.pixelplumbing.com/install#linux-memory-allocator) to prevent excessive memory usage.
> * Learn more about the [caching behavior of optimized images](/docs/app/api-reference/components/image#minimumcachettl) and how to configure the TTL.
> * You can also [disable Image Optimization](/docs/app/api-reference/components/image#unoptimized) and still retain other benefits of using `next/image` if you prefer. For example, if you are optimizing images yourself separately.

## Proxy

[Proxy](/docs/app/api-reference/file-conventions/proxy) works self-hosted with zero configuration when deploying using `next start`. Since it requires access to the incoming request, it is not supported when using a [static export](/docs/app/guides/static-exports).

Proxy uses the [Edge runtime](/docs/app/api-reference/edge), a subset of all available Node.js APIs to help ensure low latency, since it may run in front of every route or asset in your application. If you do not want this, you can use the [full Node.js runtime](/blog/next-15-2#nodejs-middleware-experimental) to run Proxy.

If you are looking to add logic (or use an external package) that requires all Node.js APIs, you might be able to move this logic to a [layout](/docs/app/api-reference/file-conventions/layout) as a [Server Component](/docs/app/getting-started/server-and-client-components). For example, checking [headers](/docs/app/api-reference/functions/headers) and [redirecting](/docs/app/api-reference/functions/redirect). You can also use headers, cookies, or query parameters to [redirect](/docs/app/api-reference/config/next-config-js/redirects#header-cookie-and-query-matching) or [rewrite](/docs/app/api-reference/config/next-config-js/rewrites#header-cookie-and-query-matching) through `next.config.js`. If that does not work, you can also use a [custom server](/docs/pages/guides/custom-server).

## Environment Variables

Next.js can support both build time and runtime environment variables.

**By default, environment variables are only available on the server**. To expose an environment variable to the browser, it must be prefixed with `NEXT_PUBLIC_`. However, these public environment variables will be inlined into the JavaScript bundle during `next build`.

To read runtime environment variables, we recommend using `getServerSideProps` or [incrementally adopting the App Router](/docs/app/guides/migrating/app-router-migration).

This allows you to use a singular Docker image that can be promoted through multiple environments with different values.

> **Good to know:**
>
> * You can run code on server startup using the [`register` function](/docs/app/guides/instrumentation).

## Caching and ISR

Next.js can cache responses, generated static pages, build outputs, and other static assets like images, fonts, and scripts.

Caching and revalidating pages (with [Incremental Static Regeneration](/docs/app/guides/incremental-static-regeneration)) use the **same Next.js server cache**. By default, this cache is stored on the local filesystem (on disk) of each Next.js server instance.

This works automatically for a single self-hosted `next start` instance with persistent local disk. If you run multiple instances, use ephemeral compute, or place a CDN/reverse proxy in front of Next.js, also review [Configuring Caching](#configuring-caching), [Multi-Instance Cache Coordination](#multi-instance-cache-coordination), and [Usage with CDNs](#usage-with-cdns).

You can configure the Next.js cache location if you want to persist cached pages and data to durable storage, or share the cache across multiple containers or instances of your Next.js application.

### Automatic Caching

* Next.js sets the `Cache-Control` header of `public, max-age=31536000, immutable` to truly immutable assets. It cannot be overridden. These immutable files contain a SHA-hash in the file name, so they can be safely cached indefinitely. For example, [Static Image Imports](/docs/app/getting-started/images#local-images). You can [configure the TTL](/docs/app/api-reference/components/image#minimumcachettl) for images.
* Incremental Static Regeneration (ISR) sets the `Cache-Control` header of `s-maxage: , stale-while-revalidate`. This revalidation time is defined in your [`getStaticProps` function](/docs/pages/building-your-application/data-fetching/get-static-props) in seconds. If you set `revalidate: false`, it will default to a one-year cache duration. To leverage this at the CDN layer, your CDN/reverse proxy must respect these directives and cache-key variability ([CDN Caching](/docs/app/guides/cdn-caching)); otherwise, responses may bypass CDN caching or serve stale/mismatched variants during client-side navigation.
* Dynamically rendered pages set a `Cache-Control` header of `private, no-cache, no-store, max-age=0, must-revalidate` to prevent user-specific data from being cached. This applies to both the App Router and Pages Router. This also includes [Draft Mode](/docs/app/guides/draft-mode).

### Static Assets

If you want to host static assets on a different domain or CDN, you can use the `assetPrefix` [configuration](/docs/app/api-reference/config/next-config-js/assetPrefix) in `next.config.js`. Next.js will use this asset prefix when retrieving JavaScript or CSS files. Separating your assets to a different domain does come with the downside of extra time spent on DNS and TLS resolution.

[Learn more about `assetPrefix`](/docs/app/api-reference/config/next-config-js/assetPrefix).

### Configuring Caching

By default, generated cache assets will be stored in memory (defaults to 50mb) and on disk. On ephemeral compute platforms (common serverless setups), local disk is often non-persistent or unavailable, so this cache is effectively short-lived and per-instance. If you are hosting Next.js using a container orchestration platform like Kubernetes, each pod will have a copy of the cache. To prevent stale data from being shown since the cache is not shared between pods by default, you can configure the Next.js cache to provide a cache handler and disable in-memory caching.

To configure the cache location when self-hosting, you can configure a custom handler in your `next.config.js` file:

For production deployments, use this as a starting point and extend it with durable storage, eviction policies, error handling, and distributed tag coordination. See [Custom Next.js Cache Handler](/docs/app/api-reference/config/next-config-js/incrementalCacheHandlerPath) and the [Redis `cacheHandler` example](https://github.com/vercel/next.js/tree/canary/examples/cache-handler-redis). If you are configuring backends for `'use cache'` directives, use [`cacheHandlers`](/docs/app/api-reference/config/next-config-js/cacheHandlers).

```jsx filename="next.config.js"
module.exports = {
  cacheHandler: require.resolve('./cache-handler.js'),
  cacheMaxMemorySize: 0, // disable default in-memory caching
}
```

Then, create `cache-handler.js` in the root of your project, for example:

```jsx filename="cache-handler.js"
const cache = new Map()

module.exports = class CacheHandler {
  constructor(options) {
    this.options = options
  }

  async get(key) {
    // This could be stored anywhere, like durable storage
    return cache.get(key)
  }

  async set(key, data, ctx) {
    // This could be stored anywhere, like durable storage
    cache.set(key, {
      value: data,
      lastModified: Date.now(),
      tags: ctx.tags,
    })
  }

  async revalidateTag(tags) {
    // tags is either a string or an array of strings
    tags = [tags].flat()
    // Iterate over all entries in the cache
    for (let [key, value] of cache) {
      // If the value's tags include the specified tag, delete this entry
      if (value.tags.some((tag) => tags.includes(tag))) {
        cache.delete(key)
      }
    }
  }

  // If you want to have temporary in memory cache for a single request that is reset
  // before the next request you can leverage this method
  resetRequestCache() {}
}
```

Using a custom cache handler will allow you to ensure consistency across all pods hosting your Next.js application. For instance, you can save the cached values anywhere, like [Redis](https://github.com/vercel/next.js/tree/canary/examples/cache-handler-redis) or AWS S3.

> **Good to know:**
>
> * `revalidatePath` is a convenience layer on top of cache tags. Calling `revalidatePath` will call the `revalidateTag` function with a special default tag for the provided page.

## Build Cache

Next.js generates an ID during `next build` to identify which version of your application is being served. The same build should be used and boot up multiple containers.

If you are rebuilding for each stage of your environment, you will need to generate a consistent build ID to use between containers. Use the `generateBuildId` command in `next.config.js`:

```jsx filename="next.config.js"
module.exports = {
  generateBuildId: async () => {
    // This could be anything, using the latest git hash
    return process.env.GIT_HASH
  },
}
```

## Multi-Server Deployments

When running Next.js across multiple server instances (for example, containers behind a load balancer), there are additional considerations to ensure consistent behavior.

### Server Functions encryption key

Next.js encrypts [Server Function](/docs/app/getting-started/mutating-data) closure variables before sending them to the client. By default, a unique encryption key is generated for each build.

When running multiple server instances, all instances must use the same encryption key. Otherwise, a Server Function encrypted by one instance cannot be decrypted by another, causing "Failed to find Server Action" errors.

Set a consistent encryption key using the `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` environment variable. The key must be a base64-encoded value with a valid AES key length (16, 24, or 32 bytes). Next.js generates 32-byte keys by default.

```bash
NEXT_SERVER_ACTIONS_ENCRYPTION_KEY=your-generated-key next build
```

The key is embedded in the build output and used automatically at runtime. Learn more in the [Data Security guide](/docs/app/guides/data-security#overwriting-encryption-keys-advanced).

### Deployment identifier

Configure a [`deploymentId`](/docs/app/api-reference/config/next-config-js/deploymentId) to enable version skew protection during rolling deployments. This ensures clients always receive assets from a consistent deployment version.

### Shared cache

By default, Next.js uses an in-memory cache that is not shared across instances. For consistent caching behavior, use [`'use cache: remote'`](/docs/app/api-reference/directives/use-cache-remote) with a [custom cache handler](/docs/app/api-reference/config/next-config-js/cacheHandlers) that stores data in external storage.

## Version Skew

When self-hosting across multiple instances or doing rolling deployments, [version skew](/docs/app/glossary#version-skew) can cause:

* **Missing assets**: The client requests JavaScript or CSS files that no longer exist on the server
* **Server Function mismatches**: The client invokes a Server Function using an ID from a previous build that the server no longer recognizes
* **Navigation failures**: Prefetched page data from an old deployment is incompatible with the new server

Next.js uses the [`deploymentId`](/docs/app/api-reference/config/next-config-js/deploymentId) to detect and handle version skew. When a deployment ID is configured:

* Static assets include a `?dpl=` query parameter
* Client-side navigation requests include an `x-deployment-id` header
* The server compares the client's deployment ID with its own

If a mismatch is detected, Next.js triggers a hard navigation (full page reload) instead of a client-side navigation. This ensures the client fetches assets from a consistent deployment version.

```js filename="next.config.js"
module.exports = {
  deploymentId: process.env.DEPLOYMENT_VERSION,
}
```

> **Good to know:** When the application is reloaded, there may be a loss of application state if it's not designed to persist between page navigations. URL state or local storage would persist, but component state like `useState` would be lost.

## Manual Graceful Shutdowns

When self-hosting, you might want to run code when the server shuts down on `SIGTERM` or `SIGINT` signals.

You can set the env variable `NEXT_MANUAL_SIG_HANDLE` to `true` and then register a handler for that signal inside your `_document.js` file. You will need to register the environment variable directly in the `package.json` script, and not in the `.env` file.

> **Good to know**: Manual signal handling is not available in `next dev`.

```json filename="package.json"
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "NEXT_MANUAL_SIG_HANDLE=true next start"
  }
}
```

```js filename="pages/_document.js"
if (process.env.NEXT_MANUAL_SIG_HANDLE) {
  process.on('SIGTERM', () => {
    console.log('Received SIGTERM: cleaning up')
    process.exit(0)
  })
  process.on('SIGINT', () => {
    console.log('Received SIGINT: cleaning up')
    process.exit(0)
  })
}
```

---
title: Static Exports
description: Next.js enables starting as a static site or Single-Page Application (SPA), then later optionally upgrading to use features that require a server.
url: "https://nextjs.org/docs/pages/guides/static-exports"
version: 16.2.6
router: Pages Router
---

# Static Exports

Next.js enables starting as a static site or Single-Page Application (SPA), then later optionally upgrading to use features that require a server.

When running `next build`, Next.js generates an HTML file per route. By breaking a strict SPA into individual HTML files, Next.js can avoid loading unnecessary JavaScript code on the client-side, reducing the bundle size and enabling faster page loads.

Since Next.js supports this static export, it can be deployed and hosted on any web server that can serve HTML/CSS/JS static assets.

## Configuration

To enable a static export, change the output mode inside `next.config.js`:

```js filename="next.config.js" highlight={5}
/**
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  output: 'export',

  // Optional: Change links `/me` -> `/me/` and emit `/me.html` -> `/me/index.html`
  // trailingSlash: true,

  // Optional: Prevent automatic `/me` -> `/me/`, instead preserve `href`
  // skipTrailingSlashRedirect: true,

  // Optional: Change the output directory `out` -> `dist`
  // distDir: 'dist',
}

module.exports = nextConfig
```

After running `next build`, Next.js will create an `out` folder with the HTML/CSS/JS assets for your application.

You can utilize [`getStaticProps`](/docs/pages/building-your-application/data-fetching/get-static-props) and [`getStaticPaths`](/docs/pages/building-your-application/data-fetching/get-static-paths) to generate an HTML file for each page in your `pages` directory (or more for [dynamic routes](/docs/app/api-reference/file-conventions/dynamic-routes)).

## Supported Features

The majority of core Next.js features needed to build a static site are supported, including:

* [Dynamic Routes when using `getStaticPaths`](/docs/app/api-reference/file-conventions/dynamic-routes)
* Prefetching with `next/link`
* Preloading JavaScript
* [Dynamic Imports](/docs/pages/guides/lazy-loading)
* Any styling options (e.g. CSS Modules, styled-jsx)
* [Client-side data fetching](/docs/pages/building-your-application/data-fetching/client-side)
* [`getStaticProps`](/docs/pages/building-your-application/data-fetching/get-static-props)
* [`getStaticPaths`](/docs/pages/building-your-application/data-fetching/get-static-paths)

### Image Optimization

[Image Optimization](/docs/app/api-reference/components/image) through `next/image` can be used with a static export by defining a custom image loader in `next.config.js`. For example, you can optimize images with a service like Cloudinary:

```js filename="next.config.js"
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    loader: 'custom',
    loaderFile: './my-loader.ts',
  },
}

module.exports = nextConfig
```

This custom loader will define how to fetch images from a remote source. For example, the following loader will construct the URL for Cloudinary:

```ts filename="my-loader.ts" switcher
export default function cloudinaryLoader({
  src,
  width,
  quality,
}: {
  src: string
  width: number
  quality?: number
}) {
  const params = ['f_auto', 'c_limit', `w_${width}`, `q_${quality || 'auto'}`]
  return `https://res.cloudinary.com/demo/image/upload/${params.join(
    ','
  )}${src}`
}
```

```js filename="my-loader.js" switcher
export default function cloudinaryLoader({ src, width, quality }) {
  const params = ['f_auto', 'c_limit', `w_${width}`, `q_${quality || 'auto'}`]
  return `https://res.cloudinary.com/demo/image/upload/${params.join(
    ','
  )}${src}`
}
```

You can then use `next/image` in your application, defining relative paths to the image in Cloudinary:

```tsx filename="app/page.tsx" switcher
import Image from 'next/image'

export default function Page() {
  return
}
```

```jsx filename="app/page.js" switcher
import Image from 'next/image'

export default function Page() {
  return
}
```

## Unsupported Features

Features that require a Node.js server, or dynamic logic that cannot be computed during the build process, are **not** supported:

* [Internationalized Routing](/docs/pages/guides/internationalization)
* [API Routes](/docs/pages/building-your-application/routing/api-routes)
* [Rewrites](/docs/pages/api-reference/config/next-config-js/rewrites)
* [Redirects](/docs/pages/api-reference/config/next-config-js/redirects)
* [Headers](/docs/pages/api-reference/config/next-config-js/headers)
* [Proxy](/docs/pages/api-reference/file-conventions/proxy)
* [Incremental Static Regeneration](/docs/pages/guides/incremental-static-regeneration)
* [Image Optimization](/docs/pages/api-reference/components/image) with the default `loader`
* [Draft Mode](/docs/pages/guides/draft-mode)
* [`getStaticPaths` with `fallback: true`](/docs/pages/api-reference/functions/get-static-paths#fallback-true)
* [`getStaticPaths` with `fallback: 'blocking'`](/docs/pages/api-reference/functions/get-static-paths#fallback-blocking)
* [`getServerSideProps`](/docs/pages/building-your-application/data-fetching/get-server-side-props)

## Deploying

With a static export, Next.js can be deployed and hosted on any web server that can serve HTML/CSS/JS static assets.

When running `next build`, Next.js generates the static export into the `out` folder. For example, let's say you have the following routes:

* `/`
* `/blog/[id]`

After running `next build`, Next.js will generate the following files:

* `/out/index.html`
* `/out/404.html`
* `/out/blog/post-1.html`
* `/out/blog/post-2.html`

If you are using a static host like Nginx, you can configure rewrites from incoming requests to the correct files:

```nginx filename="nginx.conf"
server {
  listen 80;
  server_name acme.com;

  root /var/www/out;

  location / {
      try_files $uri $uri.html $uri/ =404;
  }

  # This is necessary when `trailingSlash: false`.
  # You can omit this when `trailingSlash: true`.
  location /blog/ {
      rewrite ^/blog/(.*)$ /blog/$1.html break;
  }

  error_page 404 /404.html;
  location = /404.html {
      internal;
  }
}
```

## Version History

| Version   | Changes                                                                                                              |
| --------- | -------------------------------------------------------------------------------------------------------------------- |
| `v14.0.0` | `next export` has been removed in favor of `"output": "export"`                                                      |
| `v13.4.0` | App Router (Stable) adds enhanced static export support, including using React Server Components and Route Handlers. |
| `v13.3.0` | `next export` is deprecated and replaced with `"output": "export"`                                                   |

---
title: Tailwind CSS
description: Style your Next.js Application using Tailwind CSS.
url: "https://nextjs.org/docs/pages/guides/tailwind-v3-css"
version: 16.2.6
router: Pages Router
---

# Tailwind CSS

This guide will walk you through how to install [Tailwind CSS v3](https://v3.tailwindcss.com/) in your Next.js application.

> **Good to know:** For the latest Tailwind 4 setup, see the [Tailwind CSS setup instructions](/docs/app/getting-started/css#tailwind-css).

## Installing Tailwind v3

Install Tailwind CSS and its peer dependencies, then run the `init` command to generate both `tailwind.config.js` and `postcss.config.js` files:

```bash package="pnpm"
pnpm add -D tailwindcss@^3 postcss autoprefixer
npx tailwindcss init -p
```

```bash package="npm"
npm install -D tailwindcss@^3 postcss autoprefixer
npx tailwindcss init -p
```

```bash package="yarn"
yarn add -D tailwindcss@^3 postcss autoprefixer
npx tailwindcss init -p
```

```bash package="bun"
bun add -D tailwindcss@^3 postcss autoprefixer
bunx tailwindcss init -p
```

## Configuring Tailwind v3

Configure your template paths in your `tailwind.config.js` file:

```js filename="tailwind.config.js"
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Add the Tailwind directives to your global CSS file:

```css filename="styles/globals.css"
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Import the CSS file in your `pages/_app.js` file:

```jsx filename="pages/_app.js"
import '@/styles/globals.css'

export default function MyApp({ Component, pageProps }) {
  return
}
```

## Using classes

After installing Tailwind CSS and adding the global styles, you can use Tailwind's utility classes in your application.

```tsx filename="pages/index.tsx" switcher
export default function Page() {
  return Hello, Next.js!

}
```

```jsx filename="pages/index.js" switcher
export default function Page() {
  return Hello, Next.js!

}
```

## Usage with Turbopack

As of Next.js 13.1, Tailwind CSS and PostCSS are supported with [Turbopack](https://turbo.build/pack/docs/features/css#tailwind-css).

---
title: Testing
description: Learn how to set up Next.js with three commonly used testing tools — Cypress, Playwright, Vitest, and Jest.
url: "https://nextjs.org/docs/pages/guides/testing"
version: 16.2.6
router: Pages Router
---

# Testing

In React and Next.js, there are a few different types of tests you can write, each with its own purpose and use cases. This page provides an overview of types and commonly used tools you can use to test your application.

## Types of tests

* **Unit Testing** involves testing individual units (or blocks of code) in isolation. In React, a unit can be a single function, hook, or component.
* **Component Testing** is a more focused version of unit testing where the primary subject of the tests is React components. This may involve testing how components are rendered, their interaction with props, and their behavior in response to user events.
* **Integration Testing** involves testing how multiple units work together. This can be a combination of components, hooks, and functions.
* **End-to-End (E2E) Testing** involves testing user flows in an environment that simulates real user scenarios, like the browser. This means testing specific tasks (e.g. signup flow) in a production-like environment.
* **Snapshot Testing** involves capturing the rendered output of a component and saving it to a snapshot file. When tests run, the current rendered output of the component is compared against the saved snapshot. Changes in the snapshot are used to indicate unexpected changes in behavior.

## Guides

See the guides below to learn how to set up Next.js with these commonly used testing tools:

 - [Cypress](/docs/pages/guides/testing/cypress)
 - [Jest](/docs/pages/guides/testing/jest)
 - [Playwright](/docs/pages/guides/testing/playwright)
 - [Vitest](/docs/pages/guides/testing/vitest)

---
title: Cypress
description: Learn how to set up Next.js with Cypress for End-to-End (E2E) and Component Testing.
url: "https://nextjs.org/docs/pages/guides/testing/cypress"
version: 16.2.6
router: Pages Router
---

# Cypress

[Cypress](https://www.cypress.io/) is a test runner used for **End-to-End (E2E)** and **Component Testing**. This page will show you how to set up Cypress with Next.js and write your first tests.

> **Warning:**
>
> * Cypress versions below 13.6.3 do not support [TypeScript version 5](https://github.com/cypress-io/cypress/issues/27731) with `moduleResolution:"bundler"`. However, this issue has been resolved in Cypress version 13.6.3 and later. [cypress v13.6.3](https://docs.cypress.io/guides/references/changelog#13-6-3)

## Manual setup

To manually set up Cypress, install `cypress` as a dev dependency:

```bash package="pnpm"
pnpm add -D cypress
```

```bash package="npm"
npm install -D cypress
```

```bash package="yarn"
yarn add -D cypress
```

```bash package="bun"
bun add -D cypress
```

Add the Cypress `open` command to the `package.json` scripts field:

```json filename="package.json"
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint",
    "cypress:open": "cypress open"
  }
}
```

Run Cypress for the first time to open the Cypress testing suite:

```bash package="pnpm"
pnpm cypress:open
```

```bash package="npm"
npm run cypress:open
```

```bash package="yarn"
yarn cypress:open
```

```bash package="bun"
bun run cypress:open
```

You can choose to configure **E2E Testing** and/or **Component Testing**. Selecting any of these options will automatically create a `cypress.config.js` file and a `cypress` folder in your project.

## Creating your first Cypress E2E test

Ensure your `cypress.config` file has the following configuration:

```ts filename="cypress.config.ts" switcher
import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    setupNodeEvents(on, config) {},
  },
})
```

```js filename="cypress.config.js" switcher
const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    setupNodeEvents(on, config) {},
  },
})
```

Then, create two new Next.js files:

```jsx filename="pages/index.js"
import Link from 'next/link'

export default function Home() {
  return (

      Home

      About

  )
}
```

```jsx filename="pages/about.js"
import Link from 'next/link'

export default function About() {
  return (

      About

      Home

  )
}
```

Add a test to check your navigation is working correctly:

```js filename="cypress/e2e/app.cy.js"
describe('Navigation', () => {
  it('should navigate to the about page', () => {
    // Start from the index page
    cy.visit('http://localhost:3000/')

    // Find a link with an href attribute containing "about" and click it
    cy.get('a[href*="about"]').click()

    // The new url should include "/about"
    cy.url().should('include', '/about')

    // The new page should contain an h1 with "About"
    cy.get('h1').contains('About')
  })
})
```

### Running E2E Tests

Cypress will simulate a user navigating your application, this requires your Next.js server to be running. We recommend running your tests against your production code to more closely resemble how your application will behave.

Run `npm run build && npm run start` to build your Next.js application, then run `npm run cypress:open` in another terminal window to start Cypress and run your E2E Testing suite.

> **Good to know:**
>
> * You can use `cy.visit("/")` instead of `cy.visit("http://localhost:3000/")` by adding `baseUrl: 'http://localhost:3000'` to the `cypress.config.js` configuration file.
> * Alternatively, you can install the [`start-server-and-test`](https://www.npmjs.com/package/start-server-and-test) package to run the Next.js production server in conjunction with Cypress. After installation, add `"test": "start-server-and-test start http://localhost:3000 cypress"` to your `package.json` scripts field. Remember to rebuild your application after new changes.

## Creating your first Cypress component test

Component tests build and mount a specific component without having to bundle your whole application or start a server.

Select **Component Testing** in the Cypress app, then select **Next.js** as your front-end framework. A `cypress/component` folder will be created in your project, and a `cypress.config.js` file will be updated to enable Component Testing.

Ensure your `cypress.config` file has the following configuration:

```ts filename="cypress.config.ts" switcher
import { defineConfig } from 'cypress'

export default defineConfig({
  component: {
    devServer: {
      framework: 'next',
      bundler: 'webpack',
    },
  },
})
```

```js filename="cypress.config.js" switcher
const { defineConfig } = require('cypress')

module.exports = defineConfig({
  component: {
    devServer: {
      framework: 'next',
      bundler: 'webpack',
    },
  },
})
```

Assuming the same components from the previous section, add a test to validate a component is rendering the expected output:

```jsx filename="cypress/component/about.cy.js"
import AboutPage from '../../pages/about'

describe('', () => {
  it('should render and display expected content', () => {
    // Mount the React component for the About page
    cy.mount()

    // The new page should contain an h1 with "About page"
    cy.get('h1').contains('About')

    // Validate that a link with the expected URL is present
    // *Following* the link is better suited to an E2E test
    cy.get('a[href="/"]').should('be.visible')
  })
})
```

> **Good to know**:
>
> * Cypress currently doesn't support Component Testing for `async` Server Components. We recommend using E2E testing.
> * Since component tests do not require a Next.js server, features like `` that rely on a server being available may not function out-of-the-box.

### Running Component Tests

Run `npm run cypress:open` in your terminal to start Cypress and run your Component Testing suite.

## Continuous Integration (CI)

In addition to interactive testing, you can also run Cypress headlessly using the `cypress run` command, which is better suited for CI environments:

```json filename="package.json"
{
  "scripts": {
    //...
    "e2e": "start-server-and-test dev http://localhost:3000 \"cypress open --e2e\"",
    "e2e:headless": "start-server-and-test dev http://localhost:3000 \"cypress run --e2e\"",
    "component": "cypress open --component",
    "component:headless": "cypress run --component"
  }
}
```

You can learn more about Cypress and Continuous Integration from these resources:

* [Next.js with Cypress example](https://github.com/vercel/next.js/tree/canary/examples/with-cypress)
* [Cypress Continuous Integration Docs](https://docs.cypress.io/guides/continuous-integration/introduction)
* [Cypress GitHub Actions Guide](https://on.cypress.io/github-actions)
* [Official Cypress GitHub Action](https://github.com/cypress-io/github-action)
* [Cypress Discord](https://discord.com/invite/cypress)

---
title: Jest
description: Learn how to set up Next.js with Jest for Unit Testing.
url: "https://nextjs.org/docs/pages/guides/testing/jest"
version: 16.2.6
router: Pages Router
---

# Jest

Jest and React Testing Library are frequently used together for **Unit Testing** and **Snapshot Testing**. This guide will show you how to set up Jest with Next.js and write your first tests.

> **Good to know:** Since `async` Server Components are new to the React ecosystem, Jest currently does not support them. While you can still run **unit tests** for synchronous Server and Client Components, we recommend using an **E2E tests** for `async` components.

## Quickstart

You can use `create-next-app` with the Next.js [with-jest](https://github.com/vercel/next.js/tree/canary/examples/with-jest) example to quickly get started:

```bash package="pnpm"
pnpm create next-app --example with-jest with-jest-app
```

```bash package="npm"
npx create-next-app@latest --example with-jest with-jest-app
```

```bash package="yarn"
yarn create next-app --example with-jest with-jest-app
```

```bash package="bun"
bun create next-app --example with-jest with-jest-app
```

## Manual setup

Since the release of [Next.js 12](https://nextjs.org/blog/next-12), Next.js now has built-in configuration for Jest.

To set up Jest, install `jest` and the following packages as dev dependencies:

```bash package="pnpm"
pnpm add -D jest jest-environment-jsdom @testing-library/react @testing-library/dom @testing-library/jest-dom ts-node @types/jest
```

```bash package="npm"
npm install -D jest jest-environment-jsdom @testing-library/react @testing-library/dom @testing-library/jest-dom ts-node @types/jest
```

```bash package="yarn"
yarn add -D jest jest-environment-jsdom @testing-library/react @testing-library/dom @testing-library/jest-dom ts-node @types/jest
```

```bash package="bun"
bun add -D jest jest-environment-jsdom @testing-library/react @testing-library/dom @testing-library/jest-dom ts-node @types/jest
```

Generate a basic Jest configuration file by running the following command:

```bash package="pnpm"
pnpm create jest@latest
```

```bash package="npm"
npm init jest@latest
```

```bash package="yarn"
yarn create jest@latest
```

```bash package="bun"
bun create jest@latest
```

This will take you through a series of prompts to setup Jest for your project, including automatically creating a `jest.config.ts|js` file.

Update your config file to use `next/jest`. This transformer has all the necessary configuration options for Jest to work with Next.js:

```ts filename="jest.config.ts" switcher
import type { Config } from 'jest'
import nextJest from 'next/jest.js'

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const config: Config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  // Add more setup options before each test is run
  // setupFilesAfterEnv: ['/jest.setup.ts'],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
export default createJestConfig(config)
```

```js filename="jest.config.js" switcher
const nextJest = require('next/jest')

/** @type {import('jest').Config} */
const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  // Add more setup options before each test is run
  // setupFilesAfterEnv: ['/jest.setup.ts'],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(config)
```

Under the hood, `next/jest` is automatically configuring Jest for you, including:

* Setting up `transform` using the [Next.js Compiler](/docs/architecture/nextjs-compiler).
* Auto mocking stylesheets (`.css`, `.module.css`, and their scss variants), image imports and [`next/font`](/docs/app/api-reference/components/font).
* Loading `.env` (and all variants) into `process.env`.
* Ignoring `node_modules` from test resolving and transforms.
* Ignoring `.next` from test resolving.
* Loading `next.config.js` for flags that enable SWC transforms.

> **Good to know**: To test environment variables directly, load them manually in a separate setup script or in your `jest.config.ts` file. For more information, please see [Test Environment Variables](/docs/app/guides/environment-variables#test-environment-variables).

## Setting up Jest (with Babel)

If you opt out of the [Next.js Compiler](/docs/architecture/nextjs-compiler) and use Babel instead, you will need to manually configure Jest and install `babel-jest` and `identity-obj-proxy` in addition to the packages above.

Here are the recommended options to configure Jest for Next.js:

```js filename="jest.config.js"
module.exports = {
  collectCoverage: true,
  // on node 14.x coverage provider v8 offers good speed and more or less good report
  coverageProvider: 'v8',
  collectCoverageFrom: [
    '**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!/out/**',
    '!/.next/**',
    '!/*.config.js',
    '!/coverage/**',
  ],
  moduleNameMapper: {
    // Handle CSS imports (with CSS modules)
    // https://jestjs.io/docs/webpack#mocking-css-modules
    '^.+\\.module\\.(css|sass|scss)$': 'identity-obj-proxy',

    // Handle CSS imports (without CSS modules)
    '^.+\\.(css|sass|scss)$': '/__mocks__/styleMock.js',

    // Handle image imports
    // https://jestjs.io/docs/webpack#handling-static-assets
    '^.+\\.(png|jpg|jpeg|gif|webp|avif|ico|bmp|svg)$': `/__mocks__/fileMock.js`,

    // Handle module aliases
    '^@/components/(.*)$': '/components/$1',

    // Handle @next/font
    '@next/font/(.*)': `/__mocks__/nextFontMock.js`,
    // Handle next/font
    'next/font/(.*)': `/__mocks__/nextFontMock.js`,
    // Disable server-only
    'server-only': `/__mocks__/empty.js`,
  },
  // Add more setup options before each test is run
  // setupFilesAfterEnv: ['/jest.setup.js'],
  testPathIgnorePatterns: ['/node_modules/', '/.next/'],
  testEnvironment: 'jsdom',
  transform: {
    // Use babel-jest to transpile tests with the next/babel preset
    // https://jestjs.io/docs/configuration#transform-objectstring-pathtotransformer--pathtotransformer-object
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },
  transformIgnorePatterns: [
    '/node_modules/',
    '^.+\\.module\\.(css|sass|scss)$',
  ],
}
```

You can learn more about each configuration option in the [Jest docs](https://jestjs.io/docs/configuration). We also recommend reviewing [`next/jest` configuration](https://github.com/vercel/next.js/blob/e02fe314dcd0ae614c65b505c6daafbdeebb920e/packages/next/src/build/jest/jest.ts) to see how Next.js configures Jest.

### Handling stylesheets and image imports

Stylesheets and images aren't used in the tests but importing them may cause errors, so they will need to be mocked.

Create the mock files referenced in the configuration above - `fileMock.js` and `styleMock.js` - inside a `__mocks__` directory:

```js filename="__mocks__/fileMock.js"
module.exports = 'test-file-stub'
```

```js filename="__mocks__/styleMock.js"
module.exports = {}
```

For more information on handling static assets, please refer to the [Jest Docs](https://jestjs.io/docs/webpack#handling-static-assets).

## Handling Fonts

To handle fonts, create the `nextFontMock.js` file inside the `__mocks__` directory, and add the following configuration:

```js filename="__mocks__/nextFontMock.js"
module.exports = new Proxy(
  {},
  {
    get: function getter() {
      return () => ({
        className: 'className',
        variable: 'variable',
        style: { fontFamily: 'fontFamily' },
      })
    },
  }
)
```

## Optional: Handling Absolute Imports and Module Path Aliases

If your project is using [Module Path Aliases](/docs/app/getting-started/installation#set-up-absolute-imports-and-module-path-aliases), you will need to configure Jest to resolve the imports by matching the paths option in the `jsconfig.json` file with the `moduleNameMapper` option in the `jest.config.js` file. For example:

```json filename="tsconfig.json or jsconfig.json"
{
  "compilerOptions": {
    "module": "esnext",
    "moduleResolution": "bundler",
    "baseUrl": "./",
    "paths": {
      "@/components/*": ["components/*"]
    }
  }
}
```

```js filename="jest.config.js"
moduleNameMapper: {
  // ...
  '^@/components/(.*)$': '/components/$1',
}
```

## Optional: Extend Jest with custom matchers

`@testing-library/jest-dom` includes a set of convenient [custom matchers](https://github.com/testing-library/jest-dom#custom-matchers) such as `.toBeInTheDocument()` making it easier to write tests. You can import the custom matchers for every test by adding the following option to the Jest configuration file:

```ts filename="jest.config.ts" switcher
setupFilesAfterEnv: ['/jest.setup.ts']
```

```js filename="jest.config.js" switcher
setupFilesAfterEnv: ['/jest.setup.js']
```

Then, inside `jest.setup`, add the following import:

```ts filename="jest.setup.ts" switcher
import '@testing-library/jest-dom'
```

```js filename="jest.setup.js" switcher
import '@testing-library/jest-dom'
```

> **Good to know:** [`extend-expect` was removed in `v6.0`](https://github.com/testing-library/jest-dom/releases/tag/v6.0.0), so if you are using `@testing-library/jest-dom` before version 6, you will need to import `@testing-library/jest-dom/extend-expect` instead.

If you need to add more setup options before each test, you can add them to the `jest.setup` file above.

## Add a test script to `package.json`

Finally, add a Jest `test` script to your `package.json` file:

```json filename="package.json" highlight={6-7}
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "jest",
    "test:watch": "jest --watch"
  }
}
```

`jest --watch` will re-run tests when a file is changed. For more Jest CLI options, please refer to the [Jest Docs](https://jestjs.io/docs/cli#reference).

### Creating your first test

Your project is now ready to run tests. Create a folder called `__tests__` in your project's root directory.

For example, we can add a test to check if the `` component successfully renders a heading:

```jsx filename="pages/index.js
export default function Home() {
  return Home

}
```

```jsx filename="__tests__/index.test.js"
import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Home from '../pages/index'

describe('Home', () => {
  it('renders a heading', () => {
    render()

    const heading = screen.getByRole('heading', { level: 1 })

    expect(heading).toBeInTheDocument()
  })
})
```

Optionally, add a [snapshot test](https://jestjs.io/docs/snapshot-testing) to keep track of any unexpected changes in your component:

```jsx filename="__tests__/snapshot.js"
import { render } from '@testing-library/react'
import Home from '../pages/index'

it('renders homepage unchanged', () => {
  const { container } = render()
  expect(container).toMatchSnapshot()
})
```

> **Good to know**: Test files should not be included inside the Pages Router because any files inside the Pages Router are considered routes.

## Running your tests

Then, run the following command to run your tests:

```bash package="pnpm"
pnpm test
```

```bash package="npm"
npm run test
```

```bash package="yarn"
yarn test
```

```bash package="bun"
bun run test
```

## Additional Resources

For further reading, you may find these resources helpful:

* [Next.js with Jest example](https://github.com/vercel/next.js/tree/canary/examples/with-jest)
* [Jest Docs](https://jestjs.io/docs/getting-started)
* [React Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro/)
* [Testing Playground](https://testing-playground.com/) - use good testing practices to match elements.

---
title: Playwright
description: Learn how to set up Next.js with Playwright for End-to-End (E2E) and Integration testing.
url: "https://nextjs.org/docs/pages/guides/testing/playwright"
version: 16.2.6
router: Pages Router
---

# Playwright

Playwright is a testing framework that lets you automate Chromium, Firefox, and WebKit with a single API. You can use it to write **End-to-End (E2E)** testing. This guide will show you how to set up Playwright with Next.js and write your first tests.

## Quickstart

The fastest way to get started is to use `create-next-app` with the [with-playwright example](https://github.com/vercel/next.js/tree/canary/examples/with-playwright). This will create a Next.js project complete with Playwright configured.

```bash package="pnpm"
pnpm create next-app --example with-playwright with-playwright-app
```

```bash package="npm"
npx create-next-app@latest --example with-playwright with-playwright-app
```

```bash package="yarn"
yarn create next-app --example with-playwright with-playwright-app
```

```bash package="bun"
bun create next-app --example with-playwright with-playwright-app
```

## Manual setup

To install Playwright, run the following command:

```bash package="pnpm"
pnpm create playwright
```

```bash package="npm"
npm init playwright
```

```bash package="yarn"
yarn create playwright
```

```bash package="bun"
bun create playwright
```

This will take you through a series of prompts to setup and configure Playwright for your project, including adding a `playwright.config.ts` file. Please refer to the [Playwright installation guide](https://playwright.dev/docs/intro#installation) for the step-by-step guide.

## Creating your first Playwright E2E test

Create two new Next.js pages:

```tsx filename="pages/index.ts"
import Link from 'next/link'

export default function Home() {
  return (

      Home

      About

  )
}
```

```tsx filename="pages/about.ts"
import Link from 'next/link'

export default function About() {
  return (

      About

      Home

  )
}
```

Then, add a test to verify that your navigation is working correctly:

```ts filename="tests/example.spec.ts"
import { test, expect } from '@playwright/test'

test('should navigate to the about page', async ({ page }) => {
  // Start from the index page (the baseURL is set via the webServer in the playwright.config.ts)
  await page.goto('http://localhost:3000/')
  // Find an element with the text 'About' and click on it
  await page.click('text=About')
  // The new URL should be "/about" (baseURL is used there)
  await expect(page).toHaveURL('http://localhost:3000/about')
  // The new page should contain an h1 with "About"
  await expect(page.locator('h1')).toContainText('About')
})
```

> **Good to know**: You can use `page.goto("/")` instead of `page.goto("http://localhost:3000/")`, if you add [`"baseURL": "http://localhost:3000"`](https://playwright.dev/docs/api/class-testoptions#test-options-base-url) to the `playwright.config.ts` [configuration file](https://playwright.dev/docs/test-configuration).

### Running your Playwright tests

Playwright will simulate a user navigating your application using three browsers: Chromium, Firefox and Webkit, this requires your Next.js server to be running. We recommend running your tests against your production code to more closely resemble how your application will behave.

Run `npm run build` and `npm run start`, then run `npx playwright test` in another terminal window to run the Playwright tests.

> **Good to know**: Alternatively, you can use the [`webServer`](https://playwright.dev/docs/test-webserver/) feature to let Playwright start the development server and wait until it's fully available.

### Running Playwright on Continuous Integration (CI)

Playwright will by default run your tests in the [headless mode](https://playwright.dev/docs/ci#running-headed). To install all the Playwright dependencies, run `npx playwright install-deps`.

You can learn more about Playwright and Continuous Integration from these resources:

* [Next.js with Playwright example](https://github.com/vercel/next.js/tree/canary/examples/with-playwright)
* [Playwright on your CI provider](https://playwright.dev/docs/ci)
* [Playwright Discord](https://discord.com/invite/playwright-807756831384403968)

---
title: Vitest
description: Learn how to set up Next.js with Vitest and React Testing Library - two popular unit testing libraries.
url: "https://nextjs.org/docs/pages/guides/testing/vitest"
version: 16.2.6
router: Pages Router
---

# Vitest

Vitest and React Testing Library are frequently used together for **Unit Testing**. This guide will show you how to setup Vitest with Next.js and write your first tests.

> **Good to know:** Since `async` Server Components are new to the React ecosystem, Vitest currently does not support them. While you can still run **unit tests** for synchronous Server and Client Components, we recommend using **E2E tests** for `async` components.

## Quickstart

You can use `create-next-app` with the Next.js [with-vitest](https://github.com/vercel/next.js/tree/canary/examples/with-vitest) example to quickly get started:

```bash package="pnpm"
pnpm create next-app --example with-vitest with-vitest-app
```

```bash package="npm"
npx create-next-app@latest --example with-vitest with-vitest-app
```

```bash package="yarn"
yarn create next-app --example with-vitest with-vitest-app
```

```bash package="bun"
bun create next-app --example with-vitest with-vitest-app
```

## Manual Setup

To manually set up Vitest, install `vitest` and the following packages as dev dependencies:

```bash package="pnpm"
# Using TypeScript
pnpm add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom vite-tsconfig-paths
# Using JavaScript
pnpm add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom
```

```bash package="npm"
# Using TypeScript
npm install -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom vite-tsconfig-paths
# Using JavaScript
npm install -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom
```

```bash package="yarn"
# Using TypeScript
yarn add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom vite-tsconfig-paths
# Using JavaScript
yarn add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom
```

```bash package="bun"
# Using TypeScript
bun add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom vite-tsconfig-paths
# Using JavaScript
bun add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom
```

Create a `vitest.config.mts|js` file in the root of your project, and add the following options:

```ts filename="vitest.config.mts" switcher
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: 'jsdom',
  },
})
```

```js filename="vitest.config.js" switcher
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
  },
})
```

For more information on configuring Vitest, please refer to the [Vitest Configuration](https://vitest.dev/config/#configuration) docs.

Then, add a `test` script to your `package.json`:

```json filename="package.json"
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest"
  }
}
```

When you run `npm run test`, Vitest will **watch** for changes in your project by default.

## Creating your first Vitest Unit Test

Check that everything is working by creating a test to check if the `` component successfully renders a heading:

```tsx filename="pages/index.tsx" switcher
import Link from 'next/link'

export default function Page() {
  return (

      Home

      About

  )
}
```

```jsx filename="pages/index.jsx" switcher
import Link from 'next/link'

export default function Page() {
  return (

      Home

      About

  )
}
```

```tsx filename="__tests__/index.test.tsx" switcher
import { expect, test } from 'vitest'
import { render, screen } from '@testing-library/react'
import Page from '../pages/index'

test('Page', () => {
  render()
  expect(screen.getByRole('heading', { level: 1, name: 'Home' })).toBeDefined()
})
```

```jsx filename="__tests__/index.test.jsx" switcher
import { expect, test } from 'vitest'
import { render, screen } from '@testing-library/react'
import Page from '../pages/index'

test('Page', () => {
  render()
  expect(screen.getByRole('heading', { level: 1, name: 'Home' })).toBeDefined()
})
```

## Running your tests

Then, run the following command to run your tests:

```bash package="pnpm"
pnpm test
```

```bash package="npm"
npm run test
```

```bash package="yarn"
yarn test
```

```bash package="bun"
bun run test
```

## Additional Resources

You may find these resources helpful:

* [Next.js with Vitest example](https://github.com/vercel/next.js/tree/canary/examples/with-vitest)
* [Vitest Docs](https://vitest.dev/guide/)
* [React Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro/)

---
title: Third Party Libraries
description: "Optimize the performance of third-party libraries in your application with the `@next/third-parties` package."
url: "https://nextjs.org/docs/pages/guides/third-party-libraries"
version: 16.2.6
router: Pages Router
---

# Third Party Libraries

**`@next/third-parties`** is a library that provides a collection of components and utilities that improve the performance and developer experience of loading popular third-party libraries in your Next.js application.

All third-party integrations provided by `@next/third-parties` have been optimized for performance and ease of use.

## Getting Started

To get started, install the `@next/third-parties` library:

```bash package="pnpm"
pnpm add @next/third-parties@latest next@latest
```

```bash package="npm"
npm install @next/third-parties@latest next@latest
```

```bash package="yarn"
yarn add @next/third-parties@latest next@latest
```

```bash package="bun"
bun add @next/third-parties@latest next@latest
```

`@next/third-parties` is currently an **experimental** library under active development. We recommend installing it with the **latest** or **canary** flags while we work on adding more third-party integrations.

## Google Third-Parties

All supported third-party libraries from Google can be imported from `@next/third-parties/google`.

### Google Tag Manager

The `GoogleTagManager` component can be used to instantiate a [Google Tag Manager](https://developers.google.com/tag-platform/tag-manager) container to your page. By default, it fetches the original inline script after hydration occurs on the page.

To load Google Tag Manager for all routes, include the component directly in your custom `_app` and
pass in your GTM container ID:

```jsx filename="pages/_app.js"
import { GoogleTagManager } from '@next/third-parties/google'

export default function MyApp({ Component, pageProps }) {
  return (
    <>

  )
}
```

To load Google Tag Manager for a single route, include the component in your page file:

```jsx filename="pages/index.js"
import { GoogleTagManager } from '@next/third-parties/google'

export default function Page() {
  return
}
```

#### Sending Events

The `sendGTMEvent` function can be used to track user interactions on your page by sending events
using the `dataLayer` object. For this function to work, the `` component must be
included in either a parent layout, page, or component, or directly in the same file.

```jsx filename="pages/index.js"
import { sendGTMEvent } from '@next/third-parties/google'

export function EventButton() {
  return (

       sendGTMEvent({ event: 'buttonClicked', value: 'xyz' })}
      >
        Send Event

  )
}
```

Refer to the Tag Manager [developer
documentation](https://developers.google.com/tag-platform/tag-manager/datalayer) to learn about the
different variables and events that can be passed into the function.

#### Server-side Tagging

If you're using a server-side tag manager and serving `gtm.js` scripts from your tagging server you can
use `gtmScriptUrl` option to specify the URL of the script.

#### Options

Options to pass to the Google Tag Manager. For a full list of options, read the [Google Tag Manager
docs](https://developers.google.com/tag-platform/tag-manager/datalayer).

| Name            | Type       | Description                                                              |
| --------------- | ---------- | ------------------------------------------------------------------------ |
| `gtmId`         | Required\* | Your GTM container ID. Usually starts with `GTM-`.                       |
| `gtmScriptUrl`  | Optional\* | GTM script URL. Defaults to `https://www.googletagmanager.com/gtm.js`.   |
| `dataLayer`     | Optional   | Data layer object to instantiate the container with.                     |
| `dataLayerName` | Optional   | Name of the data layer. Defaults to `dataLayer`.                         |
| `auth`          | Optional   | Value of authentication parameter (`gtm_auth`) for environment snippets. |
| `preview`       | Optional   | Value of preview parameter (`gtm_preview`) for environment snippets.     |

\*`gtmId` can be omitted when `gtmScriptUrl` is provided to support [Google tag gateway for advertisers](https://developers.google.com/tag-platform/tag-manager/gateway/setup-guide?setup=manual).

### Google Analytics

The `GoogleAnalytics` component can be used to include [Google Analytics
4](https://developers.google.com/analytics/devguides/collection/ga4) to your page via the Google tag
(`gtag.js`). By default, it fetches the original scripts after hydration occurs on the page.

> **Recommendation**: If Google Tag Manager is already included in your application, you can
> configure Google Analytics directly using it, rather than including Google Analytics as a separate
> component. Refer to the
> [documentation](https://developers.google.com/analytics/devguides/collection/ga4/tag-options#what-is-gtm)
> to learn more about the differences between Tag Manager and `gtag.js`.

To load Google Analytics for all routes, include the component directly in your custom `_app` and
pass in your measurement ID:

```jsx filename="pages/_app.js"
import { GoogleAnalytics } from '@next/third-parties/google'

export default function MyApp({ Component, pageProps }) {
  return (
    <>

  )
}
```

To load Google Analytics for a single route, include the component in your page file:

```jsx filename="pages/index.js"
import { GoogleAnalytics } from '@next/third-parties/google'

export default function Page() {
  return
}
```

#### Sending Events

The `sendGAEvent` function can be used to measure user interactions on your page by sending events
using the `dataLayer` object. For this function to work, the `` component must be
included in either a parent layout, page, or component, or directly in the same file.

```jsx filename="pages/index.js"
import { sendGAEvent } from '@next/third-parties/google'

export function EventButton() {
  return (

       sendGAEvent('event', 'buttonClicked', { value: 'xyz' })}
      >
        Send Event

  )
}
```

Refer to the Google Analytics [developer
documentation](https://developers.google.com/analytics/devguides/collection/ga4/event-parameters) to learn
more about event parameters.

#### Tracking Pageviews

Google Analytics automatically tracks pageviews when the browser history state changes. This means
that client-side navigations between Next.js routes will send pageview data without any configuration.

To ensure that client-side navigations are being measured correctly, verify that the [*“Enhanced
Measurement”*](https://support.google.com/analytics/answer/9216061#enable_disable) property is
enabled in your Admin panel and the *“Page changes based on browser history events”* checkbox is
selected.

> **Note**: If you decide to manually send pageview events, make sure to disable the default
> pageview measurement to avoid having duplicate data. Refer to the Google Analytics [developer
> documentation](https://developers.google.com/analytics/devguides/collection/ga4/views?client_type=gtag#manual_pageviews)
> to learn more.

#### Options

Options to pass to the `` component.

| Name            | Type     | Description                                                                                            |
| --------------- | -------- | ------------------------------------------------------------------------------------------------------ |
| `gaId`          | Required | Your [measurement ID](https://support.google.com/analytics/answer/12270356). Usually starts with `G-`. |
| `dataLayerName` | Optional | Name of the data layer. Defaults to `dataLayer`.                                                       |
| `nonce`         | Optional | A [nonce](/docs/app/guides/content-security-policy#nonces).                                            |

### Google Maps Embed

The `GoogleMapsEmbed` component can be used to add a [Google Maps
Embed](https://developers.google.com/maps/documentation/embed/embedding-map) to your page. By
default, it uses the `loading` attribute to lazy-load the embed below the fold.

```jsx filename="pages/index.js"
import { GoogleMapsEmbed } from '@next/third-parties/google'

export default function Page() {
  return (

  )
}
```

#### Options

Options to pass to the Google Maps Embed. For a full list of options, read the [Google Map Embed
docs](https://developers.google.com/maps/documentation/embed/embedding-map).

| Name              | Type     | Description                                                                                         |
| ----------------- | -------- | --------------------------------------------------------------------------------------------------- |
| `apiKey`          | Required | Your api key.                                                                                       |
| `mode`            | Required | [Map mode](https://developers.google.com/maps/documentation/embed/embedding-map#choosing_map_modes) |
| `height`          | Optional | Height of the embed. Defaults to `auto`.                                                            |
| `width`           | Optional | Width of the embed. Defaults to `auto`.                                                             |
| `style`           | Optional | Pass styles to the iframe.                                                                          |
| `allowfullscreen` | Optional | Property to allow certain map parts to go full screen.                                              |
| `loading`         | Optional | Defaults to lazy. Consider changing if you know your embed will be above the fold.                  |
| `q`               | Optional | Defines map marker location. *This may be required depending on the map mode*.                      |
| `center`          | Optional | Defines the center of the map view.                                                                 |
| `zoom`            | Optional | Sets initial zoom level of the map.                                                                 |
| `maptype`         | Optional | Defines type of map tiles to load.                                                                  |
| `language`        | Optional | Defines the language to use for UI elements and for the display of labels on map tiles.             |
| `region`          | Optional | Defines the appropriate borders and labels to display, based on geo-political sensitivities.        |

### YouTube Embed

The `YouTubeEmbed` component can be used to load and display a YouTube embed. This component loads
faster by using [`lite-youtube-embed`](https://github.com/paulirish/lite-youtube-embed) under the
hood.

```jsx filename="pages/index.js"
import { YouTubeEmbed } from '@next/third-parties/google'

export default function Page() {
  return
}
```

#### Options

| Name        | Type     | Description                                                                                                                                                                                                  |
| ----------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `videoid`   | Required | YouTube video id.                                                                                                                                                                                            |
| `width`     | Optional | Width of the video container. Defaults to `auto`                                                                                                                                                             |
| `height`    | Optional | Height of the video container. Defaults to `auto`                                                                                                                                                            |
| `playlabel` | Optional | A visually hidden label for the play button for accessibility.                                                                                                                                               |
| `params`    | Optional | The video player params defined [here](https://developers.google.com/youtube/player_parameters#Parameters).  Params are passed as a query param string.  Eg: `params="controls=0&start=10&end=30"` |
| `style`     | Optional | Used to apply styles to the video container.                                                                                                                                                                 |

---
title: Upgrading
description: Learn how to upgrade to the latest versions of Next.js.
url: "https://nextjs.org/docs/pages/guides/upgrading"
version: 16.2.6
router: Pages Router
---

# Upgrading

Learn how to upgrade to the latest versions of Next.js following the versions-specific guides:

 - [Codemods](/docs/pages/guides/upgrading/codemods)
 - [Version 10](/docs/pages/guides/upgrading/version-10)
 - [Version 11](/docs/pages/guides/upgrading/version-11)
 - [Version 12](/docs/pages/guides/upgrading/version-12)
 - [Version 13](/docs/pages/guides/upgrading/version-13)
 - [Version 14](/docs/pages/guides/upgrading/version-14)
 - [Version 9](/docs/pages/guides/upgrading/version-9)

---
title: Codemods
description: Use codemods to upgrade your Next.js codebase when new features are released.
url: "https://nextjs.org/docs/pages/guides/upgrading/codemods"
version: 16.2.6
router: Pages Router
---

# Codemods

Codemods are transformations that run on your codebase programmatically. This allows a large number of changes to be programmatically applied without having to manually go through every file.

Next.js provides Codemod transformations to help upgrade your Next.js codebase when an API is updated or deprecated.

## Usage

In your terminal, navigate (`cd`) into your project's folder, then run:

```bash filename="Terminal"
npx @next/codemod
```

Replacing `` and `` with appropriate values.

* `transform` - name of transform
* `path` - files or directory to transform
* `--dry` Do a dry-run, no code will be edited
* `--print` Prints the changed output for comparison

## Upgrade

Upgrades your Next.js application, automatically running codemods and updating Next.js, React, and React DOM.

```bash filename="Terminal"
npx @next/codemod upgrade [revision]
```

### Options

* `revision` (optional): Specify the upgrade type (`patch`, `minor`, `major`), an NPM dist tag (e.g. `latest`, `canary`, `rc`), or an exact version (e.g. `15.0.0`). Defaults to `minor` for stable versions.
* `--verbose`: Show more detailed output during the upgrade process.

For example:

```bash filename="Terminal"
# Upgrade to the latest patch (e.g. 16.0.7 -> 16.0.8)
npx @next/codemod upgrade patch

# Upgrade to the latest minor (e.g. 15.3.7 -> 15.4.8). This is the default.
npx @next/codemod upgrade minor

# Upgrade to the latest major (e.g. 15.5.7 -> 16.0.7)
npx @next/codemod upgrade major

# Upgrade to a specific version
npx @next/codemod upgrade 16

# Upgrade to the canary release
npx @next/codemod upgrade canary
```

> **Good to know**:
>
> * If the target version is the same as or lower than your current version, the command exits without making changes.
> * During the upgrade, you may be prompted to choose which Next.js codemods to apply and run React 19 codemods if upgrading React.

## Codemods

### 16.0

#### Remove `experimental_ppr` Route Segment Config from App Router pages and layouts

##### `remove-experimental-ppr`

```bash filename="Terminal"
npx @next/codemod@latest remove-experimental-ppr .
```

This codemod removes the `experimental_ppr` Route Segment Config from App Router pages and layouts.

```diff filename="app/page.tsx"
- export const experimental_ppr = true;
```

#### Remove `unstable_` prefix from stabilized API

##### `remove-unstable-prefix`

```bash filename="Terminal"
npx @next/codemod@latest remove-unstable-prefix .
```

This codemod removes the `unstable_` prefix from stabilized API.

For example:

```ts
import { unstable_cacheTag as cacheTag } from 'next/cache'

cacheTag()
```

Transforms into:

```ts
import { cacheTag } from 'next/cache'

cacheTag()
```

#### Migrate from deprecated `middleware` convention to `proxy`

##### `middleware-to-proxy`

```bash filename="Terminal"
npx @next/codemod@latest middleware-to-proxy .
```

This codemod migrates projects from using the deprecated `middleware` convention to using the `proxy` convention. It:

* Renames `middleware.` to `proxy.` (e.g. `middleware.ts` to `proxy.ts`)
* Renames named export `middleware` to `proxy`
* Renames Next.js config property `experimental.middlewarePrefetch` to `experimental.proxyPrefetch`
* Renames Next.js config property `experimental.middlewareClientMaxBodySize` to `experimental.proxyClientMaxBodySize`
* Renames Next.js config property `experimental.externalMiddlewareRewritesResolve` to `experimental.externalProxyRewritesResolve`
* Renames Next.js config property `skipMiddlewareUrlNormalize` to `skipProxyUrlNormalize`

For example:

```ts filename="middleware.ts"
import { NextResponse } from 'next/server'

export function middleware() {
  return NextResponse.next()
}
```

Transforms into:

```ts filename="proxy.ts"
import { NextResponse } from 'next/server'

export function proxy() {
  return NextResponse.next()
}
```

#### Migrate from `next lint` to ESLint CLI

##### `next-lint-to-eslint-cli`

```bash filename="Terminal"
npx @next/codemod@canary next-lint-to-eslint-cli .
```

This codemod migrates projects from using `next lint` to using the ESLint CLI with your local ESLint config. It:

* Creates an `eslint.config.mjs` file with Next.js recommended configurations
* Updates `package.json` scripts to use `eslint .` instead of `next lint`
* Adds necessary ESLint dependencies to `package.json`
* Preserves existing ESLint configurations when found

For example:

```json filename="package.json"
{
  "scripts": {
    "lint": "next lint"
  }
}
```

Becomes:

```json filename="package.json"
{
  "scripts": {
    "lint": "eslint ."
  }
}
```

And creates:

```js filename="eslint.config.mjs"
import { dirname } from 'path'
import { fileURLToPath } from 'url'
import { FlatCompat } from '@eslint/eslintrc'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const compat = new FlatCompat({
  baseDirectory: __dirname,
})

const eslintConfig = [
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    ignores: [
      'node_modules/**',
      '.next/**',
      'out/**',
      'build/**',
      'next-env.d.ts',
    ],
  },
]

export default eslintConfig
```

### 15.0

#### Transform App Router Route Segment Config `runtime` value from `experimental-edge` to `edge`

##### `app-dir-runtime-config-experimental-edge`

> **Note**: This codemod is App Router specific.

```bash filename="Terminal"
npx @next/codemod@latest app-dir-runtime-config-experimental-edge .
```

This codemod transforms [Route Segment Config `runtime`](https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/runtime) value `experimental-edge` to `edge`.

For example:

```ts
export const runtime = 'experimental-edge'
```

Transforms into:

```ts
export const runtime = 'edge'
```

#### Migrate to async Dynamic APIs

APIs that opted into dynamic rendering that previously supported synchronous access are now asynchronous. You can read more about this breaking change in the [upgrade guide](/docs/app/guides/upgrading/version-15).

##### `next-async-request-api`

```bash filename="Terminal"
npx @next/codemod@latest next-async-request-api .
```

This codemod will transform dynamic APIs (`cookies()`, `headers()` and `draftMode()` from `next/headers`) that are now asynchronous to be properly awaited or wrapped with `React.use()` if applicable.
When an automatic migration isn't possible, the codemod will either add a typecast (if a TypeScript file) or a comment to inform the user that it needs to be manually reviewed & updated.

For example:

```tsx
import { cookies, headers } from 'next/headers'
const token = cookies().get('token')

function useToken() {
  const token = cookies().get('token')
  return token
}

export default function Page() {
  const name = cookies().get('name')
}

function getHeader() {
  return headers().get('x-foo')
}
```

Transforms into:

```tsx
import { use } from 'react'
import {
  cookies,
  headers,
  type UnsafeUnwrappedCookies,
  type UnsafeUnwrappedHeaders,
} from 'next/headers'
const token = (cookies() as unknown as UnsafeUnwrappedCookies).get('token')

function useToken() {
  const token = use(cookies()).get('token')
  return token
}

export default async function Page() {
  const name = (await cookies()).get('name')
}

function getHeader() {
  return (headers() as unknown as UnsafeUnwrappedHeaders).get('x-foo')
}
```

When we detect property access on the `params` or `searchParams` props in the page / route entries (`page.js`, `layout.js`, `route.js`, or `default.js`) or the `generateMetadata` / `generateViewport` APIs,
it will attempt to transform the callsite from a sync to an async function, and await the property access. If it can't be made async (such as with a Client Component), it will use `React.use` to unwrap the promise .

For example:

```tsx
// page.tsx
export default function Page({
  params,
  searchParams,
}: {
  params: { slug: string }
  searchParams: { [key: string]: string | string[] | undefined }
}) {
  const { value } = searchParams
  if (value === 'foo') {
    // ...
  }
}

export function generateMetadata({ params }: { params: { slug: string } }) {
  const { slug } = params
  return {
    title: `My Page - ${slug}`,
  }
}
```

Transforms into:

```tsx
// page.tsx
export default async function Page(props: {
  params: Promise
  searchParams: Promise
}) {
  const searchParams = await props.searchParams
  const { value } = searchParams
  if (value === 'foo') {
    // ...
  }
}

export async function generateMetadata(props: {
  params: Promise
}) {
  const params = await props.params
  const { slug } = params
  return {
    title: `My Page - ${slug}`,
  }
}
```

> **Good to know:** When this codemod identifies a spot that might require manual intervention, but we aren't able to determine the exact fix, it will add a comment or typecast to the code to inform the user that it needs to be manually updated. These comments are prefixed with **@next/codemod**, and typecasts are prefixed with `UnsafeUnwrapped`.
> Your build will error until these comments are explicitly removed. [Read more](/docs/messages/sync-dynamic-apis).

#### Replace `geo` and `ip` properties of `NextRequest` with `@vercel/functions`

##### `next-request-geo-ip`

```bash filename="Terminal"
npx @next/codemod@latest next-request-geo-ip .
```

This codemod installs `@vercel/functions` and transforms `geo` and `ip` properties of `NextRequest` with corresponding `@vercel/functions` features.

For example:

```ts
import type { NextRequest } from 'next/server'

export function GET(req: NextRequest) {
  const { geo, ip } = req
}
```

Transforms into:

```ts
import type { NextRequest } from 'next/server'
import { geolocation, ipAddress } from '@vercel/functions'

export function GET(req: NextRequest) {
  const geo = geolocation(req)
  const ip = ipAddress(req)
}
```

### 14.0

#### Migrate `ImageResponse` imports

##### `next-og-import`

```bash filename="Terminal"
npx @next/codemod@latest next-og-import .
```

This codemod moves transforms imports from `next/server` to `next/og` for usage of [Dynamic OG Image Generation](/docs/app/getting-started/metadata-and-og-images#generated-open-graph-images).

For example:

```js
import { ImageResponse } from 'next/server'
```

Transforms into:

```js
import { ImageResponse } from 'next/og'
```

#### Use `viewport` export

##### `metadata-to-viewport-export`

```bash filename="Terminal"
npx @next/codemod@latest metadata-to-viewport-export .
```

This codemod migrates certain viewport metadata to `viewport` export.

For example:

```js
export const metadata = {
  title: 'My App',
  themeColor: 'dark',
  viewport: {
    width: 1,
  },
}
```

Transforms into:

```js
export const metadata = {
  title: 'My App',
}

export const viewport = {
  width: 1,
  themeColor: 'dark',
}
```

### 13.2

#### Use Built-in Font

##### `built-in-next-font`

```bash filename="Terminal"
npx @next/codemod@latest built-in-next-font .
```

This codemod uninstalls the `@next/font` package and transforms `@next/font` imports into the built-in `next/font`.

For example:

```js
import { Inter } from '@next/font/google'
```

Transforms into:

```js
import { Inter } from 'next/font/google'
```

### 13.0

#### Rename Next Image Imports

##### `next-image-to-legacy-image`

```bash filename="Terminal"
npx @next/codemod@latest next-image-to-legacy-image .
```

Safely renames `next/image` imports in existing Next.js 10, 11, or 12 applications to `next/legacy/image` in Next.js 13. Also renames `next/future/image` to `next/image`.

For example:

```jsx filename="pages/index.js"
import Image1 from 'next/image'
import Image2 from 'next/future/image'

export default function Home() {
  return (

  )
}
```

Transforms into:

```jsx filename="pages/index.js"
// 'next/image' becomes 'next/legacy/image'
import Image1 from 'next/legacy/image'
// 'next/future/image' becomes 'next/image'
import Image2 from 'next/image'

export default function Home() {
  return (

  )
}
```

#### Migrate to the New Image Component

##### `next-image-experimental`

```bash filename="Terminal"
npx @next/codemod@latest next-image-experimental .
```

Dangerously migrates from `next/legacy/image` to the new `next/image` by adding inline styles and removing unused props.

* Removes `layout` prop and adds `style`.
* Removes `objectFit` prop and adds `style`.
* Removes `objectPosition` prop and adds `style`.
* Removes `lazyBoundary` prop.
* Removes `lazyRoot` prop.

#### Remove `` Tags From Link Components

##### `new-link`

```bash filename="Terminal"
npx @next/codemod@latest new-link .
```

Remove `` tags inside [Link Components](/docs/pages/api-reference/components/link).

For example:

```jsx

  About

// transforms into

  About

   console.log('clicked')}>About

// transforms into
 console.log('clicked')}>
  About

```

### 11

#### Migrate from CRA

##### `cra-to-next`

```bash filename="Terminal"
npx @next/codemod cra-to-next
```

Migrates a Create React App project to Next.js; creating a Pages Router and necessary config to match behavior. Client-side only rendering is leveraged initially to prevent breaking compatibility due to `window` usage during SSR and can be enabled seamlessly to allow the gradual adoption of Next.js specific features.

Please share any feedback related to this transform [in this discussion](https://github.com/vercel/next.js/discussions/25858).

### 10

#### Add React imports

##### `add-missing-react-import`

```bash filename="Terminal"
npx @next/codemod add-missing-react-import
```

Transforms files that do not import `React` to include the import in order for the new [React JSX transform](https://reactjs.org/blog/2020/09/22/introducing-the-new-jsx-transform.html) to work.

For example:

```jsx filename="my-component.js"
export default class Home extends React.Component {
  render() {
    return Hello World

  }
}
```

Transforms into:

```jsx filename="my-component.js"
import React from 'react'
export default class Home extends React.Component {
  render() {
    return Hello World

  }
}
```

### 9

#### Transform Anonymous Components into Named Components

##### `name-default-component`

```bash filename="Terminal"
npx @next/codemod name-default-component
```

**Versions 9 and above.**

Transforms anonymous components into named components to make sure they work with [Fast Refresh](https://nextjs.org/blog/next-9-4#fast-refresh).

For example:

```jsx filename="my-component.js"
export default function () {
  return Hello World

}
```

Transforms into:

```jsx filename="my-component.js"
export default function MyComponent() {
  return Hello World

}
```

The component will have a camel-cased name based on the name of the file, and it also works with arrow functions.

### 8

> **Note**: Built-in AMP support and this codemod have been removed in Next.js 16.

#### Transform AMP HOC into page config

##### `withamp-to-config`

```bash filename="Terminal"
npx @next/codemod withamp-to-config
```

Transforms the `withAmp` HOC into Next.js 9 page configuration.

For example:

```js
// Before
import { withAmp } from 'next/amp'

function Home() {
  return My AMP Page

}

export default withAmp(Home)
```

```js
// After
export default function Home() {
  return My AMP Page

}

export const config = {
  amp: true,
}
```

### 6

#### Use `withRouter`

##### `url-to-withrouter`

```bash filename="Terminal"
npx @next/codemod url-to-withrouter
```

Transforms the deprecated automatically injected `url` property on top level pages to using `withRouter` and the `router` property it injects. Read more here: [https://nextjs.org/docs/messages/url-deprecated](/docs/messages/url-deprecated)

For example:

```js filename="From"
import React from 'react'
export default class extends React.Component {
  render() {
    const { pathname } = this.props.url
    return Current pathname: {pathname}

  }
}
```

```js filename="To"
import React from 'react'
import { withRouter } from 'next/router'
export default withRouter(
  class extends React.Component {
    render() {
      const { pathname } = this.props.router
      return Current pathname: {pathname}

    }
  }
)
```

This is one case. All the cases that are transformed (and tested) can be found in the [`__testfixtures__` directory](https://github.com/vercel/next.js/tree/canary/packages/next-codemod/transforms/__testfixtures__/url-to-withrouter).

---
title: Version 10
description: Upgrade your Next.js Application from Version 9 to Version 10.
url: "https://nextjs.org/docs/pages/guides/upgrading/version-10"
version: 16.2.6
router: Pages Router
---

# Version 10

There were no breaking changes between versions 9 and 10.

To upgrade to version 10, run the following command:

```bash filename="Terminal"
npm i next@10
```

```bash filename="Terminal"
yarn add next@10
```

```bash filename="Terminal"
pnpm up next@10
```

```bash filename="Terminal"
bun add next@10
```

> **Good to know:** If you are using TypeScript, ensure you also upgrade `@types/react` and `@types/react-dom` to their corresponding versions.

---
title: Version 11
description: Upgrade your Next.js Application from Version 10 to Version 11.
url: "https://nextjs.org/docs/pages/guides/upgrading/version-11"
version: 16.2.6
router: Pages Router
---

# Version 11

To upgrade to version 11, run the following command:

```bash filename="Terminal"
npm i next@11 react@17 react-dom@17
```

```bash filename="Terminal"
yarn add next@11 react@17 react-dom@17
```

```bash filename="Terminal"
pnpm up next@11 react@17 react-dom@17
```

```bash filename="Terminal"
bun add next@11 react@17 react-dom@17
```

> **Good to know:** If you are using TypeScript, ensure you also upgrade `@types/react` and `@types/react-dom` to their corresponding versions.

### Webpack 5

Webpack 5 is now the default for all Next.js applications. If you did not have a custom webpack configuration, your application is already using webpack 5. If you do have a custom webpack configuration, you can refer to the [Next.js webpack 5 documentation](/docs/messages/webpack5) for upgrade guidance.

### Cleaning the `distDir` is now a default

The build output directory (defaults to `.next`) is now cleared by default except for the Next.js caches. You can refer to [the cleaning `distDir` RFC](https://github.com/vercel/next.js/discussions/6009) for more information.

If your application was relying on this behavior previously you can disable the new default behavior by adding the `cleanDistDir: false` flag in `next.config.js`.

### `PORT` is now supported for `next dev` and `next start`

Next.js 11 supports the `PORT` environment variable to set the port the application runs on. Using `-p`/`--port` is still recommended but if you were prohibited from using `-p` in any way you can now use `PORT` as an alternative:

Example:

```
PORT=4000 next start
```

### `next.config.js` customization to import images

Next.js 11 supports static image imports with `next/image`. This new feature relies on being able to process image imports. If you previously added the `next-images` or `next-optimized-images` packages you can either move to the new built-in support using `next/image` or disable the feature:

```js filename="next.config.js"
module.exports = {
  images: {
    disableStaticImages: true,
  },
}
```

### Remove `super.componentDidCatch()` from `pages/_app.js`

The `next/app` component's `componentDidCatch` was deprecated in Next.js 9 as it's no longer needed and has since been a no-op. In Next.js 11, it was removed.

If your `pages/_app.js` has a custom `componentDidCatch` method you can remove `super.componentDidCatch` as it is no longer needed.

### Remove `Container` from `pages/_app.js`

This export was deprecated in Next.js 9 as it's no longer needed and has since been a no-op with a warning during development. In Next.js 11 it was removed.

If your `pages/_app.js` imports `Container` from `next/app` you can remove `Container` as it was removed. Learn more in [the documentation](/docs/messages/app-container-deprecated).

### Remove `props.url` usage from page components

This property was deprecated in Next.js 4 and has since shown a warning during development. With the introduction of `getStaticProps` / `getServerSideProps` these methods already disallowed the usage of `props.url`. In Next.js 11, it was removed completely.

You can learn more in [the documentation](/docs/messages/url-deprecated).

### Remove `unsized` property on `next/image`

The `unsized` property on `next/image` was deprecated in Next.js 10.0.1. You can use `layout="fill"` instead. In Next.js 11 `unsized` was removed.

### Remove `modules` property on `next/dynamic`

The `modules` and `render` option for `next/dynamic` were deprecated in Next.js 9.5. This was done in order to make the `next/dynamic` API closer to `React.lazy`. In Next.js 11, the `modules` and `render` options were removed.

This option hasn't been mentioned in the documentation since Next.js 8 so it's less likely that your application is using it.

If your application does use `modules` and `render` you can refer to [the documentation](/docs/messages/next-dynamic-modules).

### Remove `Head.rewind`

`Head.rewind` has been a no-op since Next.js 9.5, in Next.js 11 it was removed. You can safely remove your usage of `Head.rewind`.

### Moment.js locales excluded by default

Moment.js includes translations for a lot of locales by default. Next.js now automatically excludes these locales by default to optimize bundle size for applications using Moment.js.

To load a specific locale use this snippet:

```js
import moment from 'moment'
import 'moment/locale/ja'

moment.locale('ja')
```

You can opt-out of this new default by adding `excludeDefaultMomentLocales: false` to `next.config.js` if you do not want the new behavior, do note it's highly recommended to not disable this new optimization as it significantly reduces the size of Moment.js.

### Update usage of `router.events`

In case you're accessing `router.events` during rendering, in Next.js 11 `router.events` is no longer provided during prerendering. Ensure you're accessing `router.events` in `useEffect`:

```js
useEffect(() => {
  const handleRouteChange = (url, { shallow }) => {
    console.log(
      `App is changing to ${url} ${
        shallow ? 'with' : 'without'
      } shallow routing`
    )
  }

  router.events.on('routeChangeStart', handleRouteChange)

  // If the component is unmounted, unsubscribe
  // from the event with the `off` method:
  return () => {
    router.events.off('routeChangeStart', handleRouteChange)
  }
}, [router])
```

If your application uses `router.router.events` which was an internal property that was not public please make sure to use `router.events` as well.

## React 16 to 17

React 17 introduced a new [JSX Transform](https://reactjs.org/blog/2020/09/22/introducing-the-new-jsx-transform.html) that brings a long-time Next.js feature to the wider React ecosystem: Not having to `import React from 'react'` when using JSX. When using React 17 Next.js will automatically use the new transform. This transform does not make the `React` variable global, which was an unintended side-effect of the previous Next.js implementation. A [codemod is available](/docs/pages/guides/upgrading/codemods#add-missing-react-import) to automatically fix cases where you accidentally used `React` without importing it.

Most applications already use the latest version of React, with Next.js 11 the minimum React version has been updated to 17.0.2.

To upgrade you can run the following command:

```
npm install react@latest react-dom@latest
```

Or using `yarn`:

```
yarn add react@latest react-dom@latest
```

---
title: Version 12
description: Upgrade your Next.js Application from Version 11 to Version 12.
url: "https://nextjs.org/docs/pages/guides/upgrading/version-12"
version: 16.2.6
router: Pages Router
---

# Version 12

To upgrade to version 12, run the following command:

```bash filename="Terminal"
npm i next@12 react@17 react-dom@17 eslint-config-next@12
```

```bash filename="Terminal"
yarn add next@12 react@17 react-dom@17 eslint-config-next@12
```

```bash filename="Terminal"
pnpm up next@12 react@17 react-dom@17 eslint-config-next@12
```

```bash filename="Terminal"
bun add next@12 react@17 react-dom@17 eslint-config-next@12
```

> **Good to know:** If you are using TypeScript, ensure you also upgrade `@types/react` and `@types/react-dom` to their corresponding versions.

### Upgrading to 12.2

[Middleware](/docs/messages/middleware-upgrade-guide) - If you were using Middleware prior to `12.2`, please see the [upgrade guide](/docs/messages/middleware-upgrade-guide) for more information.

### Upgrading to 12.0

[Minimum Node.js Version](https://nodejs.org/en/) - The minimum Node.js version has been bumped from `12.0.0` to `12.22.0` which is the first version of Node.js with native ES Modules support.

[Minimum React Version](https://react.dev/learn/add-react-to-an-existing-project) - The minimum required React version is `17.0.2`. To upgrade you can run the following command in the terminal:

```bash filename="Terminal"
npm install react@latest react-dom@latest

yarn add react@latest react-dom@latest

pnpm update react@latest react-dom@latest

bun add react@latest react-dom@latest
```

#### SWC replacing Babel

Next.js now uses the Rust-based compiler [SWC](https://swc.rs/) to compile JavaScript/TypeScript. This new compiler is up to 17x faster than Babel when compiling individual files and up to 5x faster Fast Refresh.

Next.js provides full backward compatibility with applications that have [custom Babel configuration](/docs/pages/guides/babel). All transformations that Next.js handles by default like styled-jsx and tree-shaking of `getStaticProps` / `getStaticPaths` / `getServerSideProps` have been ported to Rust.

When an application has a custom Babel configuration, Next.js will automatically opt-out of using SWC for compiling JavaScript/Typescript and will fall back to using Babel in the same way that it was used in Next.js 11.

Many of the integrations with external libraries that currently require custom Babel transformations will be ported to Rust-based SWC transforms in the near future. These include but are not limited to:

* Styled Components
* Emotion
* Relay

In order to prioritize transforms that will help you adopt SWC, please provide your `.babelrc` on [this feedback thread](https://github.com/vercel/next.js/discussions/30174).

#### SWC replacing Terser for minification

You can opt-in to replacing Terser with SWC for minifying JavaScript up to 7x faster using a flag in `next.config.js`:

```js filename="next.config.js"
module.exports = {
  swcMinify: true,
}
```

Minification using SWC is an opt-in flag to ensure it can be tested against more real-world Next.js applications before it becomes the default in Next.js 12.1. If you have feedback about minification, please leave it on [this feedback thread](https://github.com/vercel/next.js/discussions/30237).

#### Improvements to styled-jsx CSS parsing

On top of the Rust-based compiler we've implemented a new CSS parser based on the one used for the styled-jsx Babel transform. This new parser has improved handling of CSS and now errors when invalid CSS is used that would previously slip through and cause unexpected behavior.

Because of this change invalid CSS will throw an error during development and `next build`. This change only affects styled-jsx usage.

#### `next/image` changed wrapping element

`next/image` now renders the `` inside a `` instead of ``.

If your application has specific CSS targeting span such as `.container span`, upgrading to Next.js 12 might incorrectly match the wrapping element inside the `` component. You can avoid this by restricting the selector to a specific class such as `.container span.item` and updating the relevant component with that className, such as ``.

If your application has specific CSS targeting the `next/image` `` tag, for example `.container div`, it may not match anymore. You can update the selector `.container span`, or preferably, add a new `` wrapping the `` component and target that instead such as `.container .wrapper`.

The `className` prop is unchanged and will still be passed to the underlying `` element.

See the [documentation](/docs/pages/api-reference/components/image#styling-images) for more info.

#### HMR connection now uses a WebSocket

Previously, Next.js used a [server-sent events](https://developer.mozilla.org/docs/Web/API/Server-sent_events) connection to receive HMR events. Next.js 12 now uses a WebSocket connection.

In some cases when proxying requests to the Next.js dev server, you will need to ensure the upgrade request is handled correctly. For example, in `nginx` you would need to add the following configuration:

```nginx
location /_next/webpack-hmr {
    proxy_pass http://localhost:3000/_next/webpack-hmr;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

If you are using Apache (2.x), you can add the following configuration to enable web sockets to the server. Review the port, host name and server names.

```

 # ServerName yourwebsite.local
 ServerName "${WEBSITE_SERVER_NAME}"
 ProxyPass / http://localhost:3000/
 ProxyPassReverse / http://localhost:3000/
 # Next.js 12 uses websocket

    RewriteEngine On
    RewriteCond %{QUERY_STRING} transport=websocket [NC]
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule /(.*) ws://localhost:3000/_next/webpack-hmr/$1 [P,L]
    ProxyPass ws://localhost:3000/_next/webpack-hmr retry=0 timeout=30
    ProxyPassReverse ws://localhost:3000/_next/webpack-hmr

```

For custom servers, such as `express`, you may need to use `app.all` to ensure the request is passed correctly, for example:

```js
app.all('/_next/webpack-hmr', (req, res) => {
  nextjsRequestHandler(req, res)
})
```

#### Webpack 4 support has been removed

If you are already using webpack 5 you can skip this section.

Next.js has adopted webpack 5 as the default for compilation in Next.js 11. As communicated in the [webpack 5 upgrading documentation](/docs/messages/webpack5) Next.js 12 removes support for webpack 4.

If your application is still using webpack 4 using the opt-out flag, you will now see an error linking to the [webpack 5 upgrading documentation](/docs/messages/webpack5).

#### `target` option deprecated

If you do not have `target` in `next.config.js` you can skip this section.

The target option has been deprecated in favor of built-in support for tracing what dependencies are needed to run a page.

During `next build`, Next.js will automatically trace each page and its dependencies to determine all of the files that are needed for deploying a production version of your application.

If you are currently using the `target` option set to `serverless`, please read the [documentation on how to leverage the new output](/docs/pages/api-reference/config/next-config-js/output).

---
title: Version 13
description: Upgrade your Next.js Application from Version 12 to 13.
url: "https://nextjs.org/docs/pages/guides/upgrading/version-13"
version: 16.2.6
router: Pages Router
---

# Version 13

## Upgrading from 12 to 13

To update to Next.js version 13, run the following command using your preferred package manager:

```bash filename="Terminal"
npm i next@13 react@latest react-dom@latest eslint-config-next@13
```

```bash filename="Terminal"
yarn add next@13 react@latest react-dom@latest eslint-config-next@13
```

```bash filename="Terminal"
pnpm i next@13 react@latest react-dom@latest eslint-config-next@13
```

```bash filename="Terminal"
bun add next@13 react@latest react-dom@latest eslint-config-next@13
```

> **Good to know:** If you are using TypeScript, ensure you also upgrade `@types/react` and `@types/react-dom` to their latest versions.

### v13 Summary

* The [Supported Browsers](/docs/architecture/supported-browsers) have been changed to drop Internet Explorer and target modern browsers.
* The minimum Node.js version has been bumped from 12.22.0 to 16.14.0, since 12.x and 14.x have reached end-of-life.
* The minimum React version has been bumped from 17.0.2 to 18.2.0.
* The `swcMinify` configuration property was changed from `false` to `true`. See [Next.js Compiler](/docs/architecture/nextjs-compiler) for more info.
* The `next/image` import was renamed to `next/legacy/image`. The `next/future/image` import was renamed to `next/image`. A [codemod is available](/docs/pages/guides/upgrading/codemods#next-image-to-legacy-image) to safely and automatically rename your imports.
* The `next/link` child can no longer be ``. Add the `legacyBehavior` prop to use the legacy behavior or remove the `` to upgrade. A [codemod is available](/docs/pages/guides/upgrading/codemods#new-link) to automatically upgrade your code.
* The `target` configuration property has been removed and superseded by [Output File Tracing](/docs/pages/api-reference/config/next-config-js/output).

## Migrating shared features

Next.js 13 introduces a new [`app` directory](/docs/app) with new features and conventions. However, upgrading to Next.js 13 does **not** require using the new `app` Router.

You can continue using `pages` with new features that work in both directories, such as the updated [Image component](#image-component), [Link component](#link-component), [Script component](#script-component), and [Font optimization](#font-optimization).

### `` Component

Next.js 12 introduced many improvements to the Image Component with a temporary import: `next/future/image`. These improvements included less client-side JavaScript, easier ways to extend and style images, better accessibility, and native browser lazy loading.

Starting in Next.js 13, this new behavior is now the default for `next/image`.

There are two codemods to help you migrate to the new Image Component:

* [next-image-to-legacy-image](/docs/pages/guides/upgrading/codemods#next-image-to-legacy-image): This codemod will safely and automatically rename `next/image` imports to `next/legacy/image` to maintain the same behavior as Next.js 12. We recommend running this codemod to quickly update to Next.js 13 automatically.
* [next-image-experimental](/docs/pages/guides/upgrading/codemods#next-image-experimental): After running the previous codemod, you can optionally run this experimental codemod to upgrade `next/legacy/image` to the new `next/image`, which will remove unused props and add inline styles. Please note this codemod is experimental and only covers static usage (such as ``) but not dynamic usage (such as ``).

Alternatively, you can manually update by following the [migration guide](/docs/pages/guides/upgrading/codemods#next-image-experimental) and also see the [legacy comparison](/docs/pages/api-reference/components/image-legacy#comparison).

### `` Component

The [`` Component](/docs/pages/api-reference/components/link) no longer requires manually adding an `` tag as a child. This behavior was added as an experimental option in [version 12.2](https://nextjs.org/blog/next-12-2) and is now the default. In Next.js 13, `` always renders `` and allows you to forward props to the underlying tag.

For example:

```jsx
import Link from 'next/link'

// Next.js 12: `` has to be nested otherwise it's excluded

  About

// Next.js 13: `` always renders `` under the hood

  About

```

To upgrade your links to Next.js 13, you can use the [`new-link` codemod](/docs/pages/guides/upgrading/codemods#new-link).

### `` Component

The behavior of [`next/script`](/docs/pages/api-reference/components/script) has been updated to support both `pages` and `app`. If incrementally adopting `app`, read the [upgrade guide](/docs/pages/guides/upgrading).

### Font Optimization

Previously, Next.js helped you optimize fonts by inlining font CSS. Version 13 introduces the new [`next/font`](/docs/pages/api-reference/components/font) module which gives you the ability to customize your font loading experience while still ensuring great performance and privacy.

See [Optimizing Fonts](/docs/pages/api-reference/components/font) to learn how to use `next/font`.

---
title: Version 14
description: Upgrade your Next.js Application from Version 13 to 14.
url: "https://nextjs.org/docs/pages/guides/upgrading/version-14"
version: 16.2.6
router: Pages Router
---

# Version 14

## Upgrading from 13 to 14

To update to Next.js version 14, run the following command using your preferred package manager:

```bash filename="Terminal"
npm i next@next-14 react@18 react-dom@18 && npm i eslint-config-next@next-14 -D
```

```bash filename="Terminal"
yarn add next@next-14 react@18 react-dom@18 && yarn add eslint-config-next@next-14 -D
```

```bash filename="Terminal"
pnpm i next@next-14 react@18 react-dom@18 && pnpm i eslint-config-next@next-14 -D
```

```bash filename="Terminal"
bun add next@next-14 react@18 react-dom@18 && bun add eslint-config-next@next-14 -D
```

> **Good to know:** If you are using TypeScript, ensure you also upgrade `@types/react` and `@types/react-dom` to their latest versions.

### v14 Summary

* The minimum Node.js version has been bumped from 16.14 to 18.17, since 16.x has reached end-of-life.
* The `next export` command has been removed in favor of `output: 'export'` config. Please see the [docs](https://nextjs.org/docs/app/guides/static-exports) for more information.
* The `next/server` import for `ImageResponse` was renamed to `next/og`. A [codemod is available](/docs/app/guides/upgrading/codemods#next-og-import) to safely and automatically rename your imports.
* The `@next/font` package has been fully removed in favor of the built-in `next/font`. A [codemod is available](/docs/app/guides/upgrading/codemods#built-in-next-font) to safely and automatically rename your imports.
* The WASM target for `next-swc` has been removed.

---
title: Version 9
description: Upgrade your Next.js Application from Version 8 to Version 9.
url: "https://nextjs.org/docs/pages/guides/upgrading/version-9"
version: 16.2.6
router: Pages Router
---

# Version 9

To upgrade to version 9, run the following command:

```bash filename="Terminal"
npm i next@9
```

```bash filename="Terminal"
yarn add next@9
```

```bash filename="Terminal"
pnpm up next@9
```

```bash filename="Terminal"
bun add next@9
```

> **Good to know:** If you are using TypeScript, ensure you also upgrade `@types/react` and `@types/react-dom` to their corresponding versions.

## Check your Custom App File (`pages/_app.js`)

If you previously copied the [Custom ``](/docs/pages/building-your-application/routing/custom-app) example, you may be able to remove your `getInitialProps`.

Removing `getInitialProps` from `pages/_app.js` (when possible) is important to leverage new Next.js features!

The following `getInitialProps` does nothing and may be removed:

```js
class MyApp extends App {
  // Remove me, I do nothing!
  static async getInitialProps({ Component, ctx }) {
    let pageProps = {}

    if (Component.getInitialProps) {
      pageProps = await Component.getInitialProps(ctx)
    }

    return { pageProps }
  }

  render() {
    // ... etc
  }
}
```

## Breaking Changes

### `@zeit/next-typescript` is no longer necessary

Next.js will now ignore usage `@zeit/next-typescript` and warn you to remove it. Please remove this plugin from your `next.config.js`.

Remove references to `@zeit/next-typescript/babel` from your custom `.babelrc` (if present).

The usage of [`fork-ts-checker-webpack-plugin`](https://github.com/Realytics/fork-ts-checker-webpack-plugin/issues) should also be removed from your `next.config.js`.

TypeScript Definitions are published with the `next` package, so you need to uninstall `@types/next` as they would conflict.

The following types are different:

> This list was created by the community to help you upgrade, if you find other differences please send a pull-request to this list to help other users.

From:

```tsx
import { NextContext } from 'next'
import { NextAppContext, DefaultAppIProps } from 'next/app'
import { NextDocumentContext, DefaultDocumentIProps } from 'next/document'
```

to

```tsx
import { NextPageContext } from 'next'
import { AppContext, AppInitialProps } from 'next/app'
import { DocumentContext, DocumentInitialProps } from 'next/document'
```

### The `config` key is now an export on a page

You may no longer export a custom variable named `config` from a page (i.e. `export { config }` / `export const config ...`).
This exported variable is now used to specify page-level Next.js configuration like Opt-in AMP and API Route features.

You must rename a non-Next.js-purposed `config` export to something different.

### `next/dynamic` no longer renders "loading..." by default while loading

Dynamic components will not render anything by default while loading. You can still customize this behavior by setting the `loading` property:

```jsx
import dynamic from 'next/dynamic'

const DynamicComponentWithCustomLoading = dynamic(
  () => import('../components/hello2'),
  {
    loading: () => Loading
,
  }
)
```

### `withAmp` has been removed in favor of an exported configuration object

Next.js now has the concept of page-level configuration, so the `withAmp` higher-order component has been removed for consistency.

This change can be **automatically migrated by running the following commands in the root of your Next.js project:**

```bash filename="Terminal"
curl -L https://github.com/vercel/next-codemod/archive/master.tar.gz | tar -xz --strip=2 next-codemod-master/transforms/withamp-to-config.js npx jscodeshift -t ./withamp-to-config.js pages/**/*.js
```

To perform this migration by hand, or view what the codemod will produce, see below:

**Before**

```jsx
import { withAmp } from 'next/amp'

function Home() {
  return My AMP Page

}

export default withAmp(Home)
// or
export default withAmp(Home, { hybrid: true })
```

**After**

```jsx
export default function Home() {
  return My AMP Page

}

export const config = {
  amp: true,
  // or
  amp: 'hybrid',
}
```

### `next export` no longer exports pages as `index.html`

Previously, exporting `pages/about.js` would result in `out/about/index.html`. This behavior has been changed to result in `out/about.html`.

You can revert to the previous behavior by creating a `next.config.js` with the following content:

```js filename="next.config.js"
module.exports = {
  trailingSlash: true,
}
```

### `pages/api/` is treated differently

Pages in `pages/api/` are now considered [API Routes](https://nextjs.org/blog/next-9#api-routes).
Pages in this directory will no longer contain a client-side bundle.

## Deprecated Features

### `next/dynamic` has deprecated loading multiple modules at once

The ability to load multiple modules at once has been deprecated in `next/dynamic` to be closer to React's implementation (`React.lazy` and `Suspense`).

Updating code that relies on this behavior is relatively straightforward! We've provided an example of a before/after to help you migrate your application:

**Before**

```jsx
import dynamic from 'next/dynamic'

const HelloBundle = dynamic({
  modules: () => {
    const components = {
      Hello1: () => import('../components/hello1').then((m) => m.default),
      Hello2: () => import('../components/hello2').then((m) => m.default),
    }

    return components
  },
  render: (props, { Hello1, Hello2 }) => (

      {props.title}

  ),
})

function DynamicBundle() {
  return
}

export default DynamicBundle
```

**After**

```jsx
import dynamic from 'next/dynamic'

const Hello1 = dynamic(() => import('../components/hello1'))
const Hello2 = dynamic(() => import('../components/hello2'))

function HelloBundle({ title }) {
  return (

      {title}

  )
}

function DynamicBundle() {
  return
}

export default DynamicBundle
```

---
title: Building Your Application
description: Learn how to use Next.js features to build your application.
url: "https://nextjs.org/docs/pages/building-your-application"
version: 16.2.6
router: Pages Router
---

# Building Your Application

 - [Routing](/docs/pages/building-your-application/routing)
 - [Rendering](/docs/pages/building-your-application/rendering)
 - [Data Fetching](/docs/pages/building-your-application/data-fetching)
 - [Configuring](/docs/pages/building-your-application/configuring)

---
title: Routing
description: Learn the fundamentals of routing for front-end applications with the Pages Router.
url: "https://nextjs.org/docs/pages/building-your-application/routing"
version: 16.2.6
router: Pages Router
---

# Routing

The Pages Router has a file-system based router built on concepts of pages. When a file is added to the `pages` directory it's automatically available as a route. Learn more about routing in the Pages Router:

 - [Pages and Layouts](/docs/pages/building-your-application/routing/pages-and-layouts)
 - [Dynamic Routes](/docs/pages/building-your-application/routing/dynamic-routes)
 - [Linking and Navigating](/docs/pages/building-your-application/routing/linking-and-navigating)
 - [Custom App](/docs/pages/building-your-application/routing/custom-app)
 - [Custom Document](/docs/pages/building-your-application/routing/custom-document)
 - [API Routes](/docs/pages/building-your-application/routing/api-routes)
 - [Custom Errors](/docs/pages/building-your-application/routing/custom-error)

---
title: Pages and Layouts
description: Create your first page and shared layout with the Pages Router.
url: "https://nextjs.org/docs/pages/building-your-application/routing/pages-and-layouts"
version: 16.2.6
router: Pages Router
---

# Pages and Layouts

The Pages Router has a file-system based router built on the concept of pages.

When a file is added to the `pages` directory, it's automatically available as a route.

In Next.js, a **page** is a [React Component](https://react.dev/learn/your-first-component) exported from a `.js`, `.jsx`, `.ts`, or `.tsx` file in the `pages` directory. Each page is associated with a route based on its file name.

**Example**: If you create `pages/about.js` that exports a React component like below, it will be accessible at `/about`.

```jsx
export default function About() {
  return About

}
```

## Index routes

The router will automatically route files named `index` to the root of the directory.

* `pages/index.js` → `/`
* `pages/blog/index.js` → `/blog`

## Nested routes

The router supports nested files. If you create a nested folder structure, files will automatically be routed in the same way still.

* `pages/blog/first-post.js` → `/blog/first-post`
* `pages/dashboard/settings/username.js` → `/dashboard/settings/username`

## Pages with Dynamic Routes

Next.js supports pages with dynamic routes. For example, if you create a file called `pages/posts/[id].js`, then it will be accessible at `posts/1`, `posts/2`, etc.

> To learn more about dynamic routing, check the [Dynamic Routing documentation](/docs/pages/building-your-application/routing/dynamic-routes).

## Layout Pattern

The React model allows us to deconstruct a [page](/docs/pages/building-your-application/routing/pages-and-layouts) into a series of components. Many of these components are often reused between pages. For example, you might have the same navigation bar and footer on every page.

```jsx filename="components/layout.js"
import Navbar from './navbar'
import Footer from './footer'

export default function Layout({ children }) {
  return (
    <>

  }

  return
}
```

```jsx filename="components/breadcrumb.js" switcher
import { useParams } from 'next/navigation'

// This component works in both pages/ and app/
export function Breadcrumb() {
  const params = useParams()

  if (!params) {
    // Fallback for Pages Router during prerendering
    return
  }

  return
}
```

> **Good to know**: When using this component in the App Router, `useParams` never returns `null`, so the fallback branch will not be rendered.

## Version History

| Version   | Changes                 |
| --------- | ----------------------- |
| `v13.3.0` | `useParams` introduced. |

---
title: useReportWebVitals
description: useReportWebVitals
url: "https://nextjs.org/docs/pages/api-reference/functions/use-report-web-vitals"
version: 16.2.6
router: Pages Router
---

# useReportWebVitals

The `useReportWebVitals` hook allows you to report [Core Web Vitals](https://web.dev/vitals/), and can be used in combination with your analytics service.

New functions passed to `useReportWebVitals` are called with the available metrics up to that point. To prevent reporting duplicated data, ensure that the callback function reference does not change (as shown in the code examples below).

```jsx filename="pages/_app.js"
import { useReportWebVitals } from 'next/web-vitals'

const logWebVitals = (metric) => {
  console.log(metric)
}

function MyApp({ Component, pageProps }) {
  useReportWebVitals(logWebVitals)

  return
}
```

## useReportWebVitals

The `metric` object passed as the hook's argument consists of a number of properties:

* `id`: Unique identifier for the metric in the context of the current page load
* `name`: The name of the performance metric. Possible values include names of [Web Vitals](#web-vitals) metrics (TTFB, FCP, LCP, FID, CLS) specific to a web application.
* `delta`: The difference between the current value and the previous value of the metric. The value is typically in milliseconds and represents the change in the metric's value over time.
* `entries`: An array of [Performance Entries](https://developer.mozilla.org/docs/Web/API/PerformanceEntry) associated with the metric. These entries provide detailed information about the performance events related to the metric.
* `navigationType`: Indicates the navigation type that triggered metric collection. Values are derived from [PerformanceNavigationTiming.type](https://developer.mozilla.org/docs/Web/API/PerformanceNavigationTiming/type) and may include `"navigate"`, `"reload"`, `"prerender"`, `"back-forward"` (normalized from `"back_forward"`), `"back-forward-cache"` (BFCache restore), and `"restore"` (page restored after discard).
* `rating`: A qualitative rating of the metric value, providing an assessment of the performance. Possible values are `"good"`, `"needs-improvement"`, and `"poor"`. The rating is typically determined by comparing the metric value against predefined thresholds that indicate acceptable or suboptimal performance.
* `value`: The actual value or duration of the performance entry, typically in milliseconds. The value provides a quantitative measure of the performance aspect being tracked by the metric. The source of the value depends on the specific metric being measured and can come from various [Performance API](https://developer.mozilla.org/docs/Web/API/Performance_API)s.

## Web Vitals

[Web Vitals](https://web.dev/vitals/) are a set of useful metrics that aim to capture the user
experience of a web page. The following web vitals are all included:

* [Time to First Byte](https://developer.mozilla.org/docs/Glossary/Time_to_first_byte) (TTFB)
* [First Contentful Paint](https://developer.mozilla.org/docs/Glossary/First_contentful_paint) (FCP)
* [Largest Contentful Paint](https://web.dev/lcp/) (LCP)
* [First Input Delay](https://web.dev/fid/) (FID)
* [Cumulative Layout Shift](https://web.dev/cls/) (CLS)
* [Interaction to Next Paint](https://web.dev/inp/) (INP)

You can handle all the results of these metrics using the `name` property.

```jsx filename="pages/_app.js"
import { useReportWebVitals } from 'next/web-vitals'

const handleWebVitals = (metric) => {
  switch (metric.name) {
    case 'FCP': {
      // handle FCP results
    }
    case 'LCP': {
      // handle LCP results
    }
    // ...
  }
}

function MyApp({ Component, pageProps }) {
  useReportWebVitals(handleWebVitals)

  return
}
```

## Custom Metrics

In addition to the core metrics listed above, there are some additional custom metrics that
measure the time it takes for the page to hydrate and render:

* `Next.js-hydration`: Length of time it takes for the page to start and finish hydrating (in ms)
* `Next.js-route-change-to-render`: Length of time it takes for a page to start rendering after a
  route change (in ms)
* `Next.js-render`: Length of time it takes for a page to finish render after a route change (in ms)

You can handle all the results of these metrics separately:

```jsx filename="pages/_app.js"
import { useReportWebVitals } from 'next/web-vitals'

function handleCustomMetrics(metric) {
  switch (metric.name) {
    case 'Next.js-hydration':
      // handle hydration results
      break
    case 'Next.js-route-change-to-render':
      // handle route-change to render results
      break
    case 'Next.js-render':
      // handle render results
      break
    default:
      break
  }
}

function MyApp({ Component, pageProps }) {
  useReportWebVitals(handleCustomMetrics)

  return
}
```

These metrics work in all browsers that support the [User Timing API](https://caniuse.com/#feat=user-timing).

## Sending results to external systems

You can send results to any endpoint to measure and track
real user performance on your site. For example:

```js
function postWebVitals(metric) {
  const body = JSON.stringify(metric)
  const url = 'https://example.com/analytics'

  // Use `navigator.sendBeacon()` if available, falling back to `fetch()`.
  if (navigator.sendBeacon) {
    navigator.sendBeacon(url, body)
  } else {
    fetch(url, { body, method: 'POST', keepalive: true })
  }
}

useReportWebVitals(postWebVitals)
```

> **Good to know**: If you use [Google Analytics](https://analytics.google.com/analytics/web/), using the
> `id` value can allow you to construct metric distributions manually (to calculate percentiles,
> etc.)

> ```js
> useReportWebVitals(metric => {
>   // Use `window.gtag` if you initialized Google Analytics as this example:
>   // https://github.com/vercel/next.js/blob/canary/examples/with-google-analytics
>   window.gtag('event', metric.name, {
>     value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value), // values must be integers
>     event_label: metric.id, // id unique to current page load
>     non_interaction: true, // avoids affecting bounce rate.
>   });
> }
> ```
>
> Read more about [sending results to Google Analytics](https://github.com/GoogleChrome/web-vitals#send-the-results-to-google-analytics).

---
title: useRouter
description: Learn more about the API of the Next.js Router, and access the router instance in your page with the useRouter hook.
url: "https://nextjs.org/docs/pages/api-reference/functions/use-router"
version: 16.2.6
router: Pages Router
---

# useRouter

If you want to access the [`router` object](#router-object) inside any function component in your app, you can use the `useRouter` hook, take a look at the following example:

```jsx
import { useRouter } from 'next/router'

function ActiveLink({ children, href }) {
  const router = useRouter()
  const style = {
    marginRight: 10,
    color: router.asPath === href ? 'red' : 'black',
  }

  const handleClick = (e) => {
    e.preventDefault()
    router.push(href)
  }

  return (

      {children}

  )
}

export default ActiveLink
```

> `useRouter` is a [React Hook](https://react.dev/learn#using-hooks), meaning it cannot be used with classes. You can either use [withRouter](#withrouter) or wrap your class in a function component.

## `router` object

The following is the definition of the `router` object returned by both [`useRouter`](#top) and [`withRouter`](#withrouter):

* `pathname`: `String` - The path for current route file that comes after `/pages`. Therefore, `basePath`, `locale` and trailing slash (`trailingSlash: true`) are not included.
* `query`: `Object` - The query string parsed to an object, including [dynamic route](/docs/pages/building-your-application/routing/dynamic-routes) parameters. It will be an empty object during prerendering if the page doesn't use [Server-side Rendering](/docs/pages/building-your-application/data-fetching/get-server-side-props). Defaults to `{}`
* `asPath`: `String` - The path as shown in the browser including the search params and respecting the `trailingSlash` configuration. `basePath` and `locale` are not included.
* `isFallback`: `boolean` - Whether the current page is in [fallback mode](/docs/pages/api-reference/functions/get-static-paths#fallback-true).
* `basePath`: `String` - The active [basePath](/docs/app/api-reference/config/next-config-js/basePath) (if enabled).
* `locale`: `String` - The active locale (if enabled).
* `locales`: `String[]` - All supported locales (if enabled).
* `defaultLocale`: `String` - The current default locale (if enabled).
* `domainLocales`: `Array` - Any configured domain locales.
* `isReady`: `boolean` - Whether the router fields are updated client-side and ready for use. Should only be used inside of `useEffect` methods and not for conditionally rendering on the server. See related docs for use case with [automatically statically optimized pages](/docs/pages/building-your-application/rendering/automatic-static-optimization)
* `isPreview`: `boolean` - Whether the application is currently in [preview mode](/docs/pages/guides/preview-mode).

> Using the `asPath` field may lead to a mismatch between client and server if the page is rendered using server-side rendering or [automatic static optimization](/docs/pages/building-your-application/rendering/automatic-static-optimization). Avoid using `asPath` until the `isReady` field is `true`.

The following methods are included inside `router`:

### router.push

Handles client-side transitions, this method is useful for cases where [`next/link`](/docs/pages/api-reference/components/link) is not enough.

```js
router.push(url, as, options)
```

* `url`: `UrlObject | String` - The URL to navigate to (see [Node.JS URL module documentation](https://nodejs.org/api/url.html#legacy-urlobject) for `UrlObject` properties).
* `as`: `UrlObject | String` - Optional decorator for the path that will be shown in the browser URL bar. Before Next.js 9.5.3 this was used for dynamic routes.
* `options` - Optional object with the following configuration options:
  * `scroll` - Optional boolean, controls scrolling to the top of the page after navigation. Defaults to `true`
  * [`shallow`](/docs/pages/building-your-application/routing/linking-and-navigating#shallow-routing): Update the path of the current page without rerunning [`getStaticProps`](/docs/pages/building-your-application/data-fetching/get-static-props), [`getServerSideProps`](/docs/pages/building-your-application/data-fetching/get-server-side-props) or [`getInitialProps`](/docs/pages/api-reference/functions/get-initial-props). Defaults to `false`
  * `locale` - Optional string, indicates locale of the new page

> You don't need to use `router.push` for external URLs. [window.location](https://developer.mozilla.org/docs/Web/API/Window/location) is better suited for those cases.

Navigating to `pages/about.js`, which is a predefined route:

```jsx
import { useRouter } from 'next/router'

export default function Page() {
  const router = useRouter()

  return (
     router.push('/about')}>
      Click me

  )
}
```

Navigating `pages/post/[pid].js`, which is a dynamic route:

```jsx
import { useRouter } from 'next/router'

export default function Page() {
  const router = useRouter()

  return (
     router.push('/post/abc')}>
      Click me

  )
}
```

Redirecting the user to `pages/login.js`, useful for pages behind [authentication](/docs/pages/guides/authentication):

```jsx
import { useEffect } from 'react'
import { useRouter } from 'next/router'

// Here you would fetch and return the user
const useUser = () => ({ user: null, loading: false })

export default function Page() {
  const { user, loading } = useUser()
  const router = useRouter()

  useEffect(() => {
    if (!(user || loading)) {
      router.push('/login')
    }
  }, [user, loading])

  return Redirecting...

}
```

#### Resetting state after navigation

When navigating to the same page in Next.js, the page's state **will not** be reset by default as React does not unmount unless the parent component has changed.

```jsx filename="pages/[slug].js"
import Link from 'next/link'
import { useState } from 'react'
import { useRouter } from 'next/router'

export default function Page(props) {
  const router = useRouter()
  const [count, setCount] = useState(0)
  return (

      Page: {router.query.slug}

      Count: {count}

       setCount(count + 1)}>Increase count
      one two

  )
}
```

In the above example, navigating between `/one` and `/two` **will not** reset the count . The `useState` is maintained between renders because the top-level React component, `Page`, is the same.

If you do not want this behavior, you have a couple of options:

* Manually ensure each state is updated using `useEffect`. In the above example, that could look like:

  ```jsx
  useEffect(() => {
    setCount(0)
  }, [router.query.slug])
  ```

* Use a React `key` to [tell React to remount the component](https://react.dev/learn/rendering-lists#keeping-list-items-in-order-with-key). To do this for all pages, you can use a custom app:

  ```jsx filename="pages/_app.js"
  import { useRouter } from 'next/router'

  export default function MyApp({ Component, pageProps }) {
    const router = useRouter()
    return
  }
  ```

#### With URL object

You can use a URL object in the same way you can use it for [`next/link`](/docs/pages/api-reference/components/link#passing-a-url-object). Works for both the `url` and `as` parameters:

```jsx
import { useRouter } from 'next/router'

export default function ReadMore({ post }) {
  const router = useRouter()

  return (
     {
        router.push({
          pathname: '/post/[pid]',
          query: { pid: post.id },
        })
      }}
    >
      Click here to read more

  )
}
```

### router.replace

Similar to the `replace` prop in [`next/link`](/docs/pages/api-reference/components/link), `router.replace` will prevent adding a new URL entry into the `history` stack.

```js
router.replace(url, as, options)
```

* The API for `router.replace` is exactly the same as the API for [`router.push`](#routerpush).

Take a look at the following example:

```jsx
import { useRouter } from 'next/router'

export default function Page() {
  const router = useRouter()

  return (
     router.replace('/home')}>
      Click me

  )
}
```

### router.prefetch

Prefetch pages for faster client-side transitions. This method is only useful for navigations without [`next/link`](/docs/pages/api-reference/components/link), as `next/link` takes care of prefetching pages automatically.

> This is a production only feature. Next.js doesn't prefetch pages in development.

```js
router.prefetch(url, as, options)
```

* `url` - The URL to prefetch, including explicit routes (e.g. `/dashboard`) and dynamic routes (e.g. `/product/[id]`)
* `as` - Optional decorator for `url`. Before Next.js 9.5.3 this was used to prefetch dynamic routes.
* `options` - Optional object with the following allowed fields:
  * `locale` - allows providing a different locale from the active one. If `false`, `url` has to include the locale as the active locale won't be used.

Let's say you have a login page, and after a login, you redirect the user to the dashboard. For that case, we can prefetch the dashboard to make a faster transition, like in the following example:

```jsx
import { useCallback, useEffect } from 'react'
import { useRouter } from 'next/router'

export default function Login() {
  const router = useRouter()
  const handleSubmit = useCallback((e) => {
    e.preventDefault()

    fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        /* Form data */
      }),
    }).then((res) => {
      // Do a fast client-side transition to the already prefetched dashboard page
      if (res.ok) router.push('/dashboard')
    })
  }, [])

  useEffect(() => {
    // Prefetch the dashboard page
    router.prefetch('/dashboard')
  }, [router])

  return (

      {/* Form fields */}
      Login

  )
}
```

### router.beforePopState

In some cases (for example, if using a [Custom Server](/docs/pages/guides/custom-server)), you may wish to listen to [popstate](https://developer.mozilla.org/docs/Web/API/Window/popstate_event) and do something before the router acts on it.

```js
router.beforePopState(cb)
```

* `cb` - The function to run on incoming `popstate` events. The function receives the state of the event as an object with the following props:
  * `url`: `String` - the route for the new state. This is usually the name of a `page`
  * `as`: `String` - the url that will be shown in the browser
  * `options`: `Object` - Additional options sent by [router.push](#routerpush)

If `cb` returns `false`, the Next.js router will not handle `popstate`, and you'll be responsible for handling it in that case. See [Disabling file-system routing](/docs/pages/guides/custom-server#disabling-file-system-routing).

You could use `beforePopState` to manipulate the request, or force a SSR refresh, as in the following example:

```jsx
import { useEffect } from 'react'
import { useRouter } from 'next/router'

export default function Page() {
  const router = useRouter()

  useEffect(() => {
    router.beforePopState(({ url, as, options }) => {
      // I only want to allow these two routes!
      if (as !== '/' && as !== '/other') {
        // Have SSR render bad routes as a 404.
        window.location.href = as
        return false
      }

      return true
    })
  }, [router])

  return Welcome to the page

}
```

### router.back

Navigate back in history. Equivalent to clicking the browser’s back button. It executes `window.history.back()`.

```jsx
import { useRouter } from 'next/router'

export default function Page() {
  const router = useRouter()

  return (
     router.back()}>
      Click here to go back

  )
}
```

### router.reload

Reload the current URL. Equivalent to clicking the browser’s refresh button. It executes `window.location.reload()`.

```jsx
import { useRouter } from 'next/router'

export default function Page() {
  const router = useRouter()

  return (
     router.reload()}>
      Click here to reload

  )
}
```

### router.events

You can listen to different events happening inside the Next.js Router. Here's a list of supported events:

* `routeChangeStart(url, { shallow })` - Fires when a route starts to change
* `routeChangeComplete(url, { shallow })` - Fires when a route changed completely
* `routeChangeError(err, url, { shallow })` - Fires when there's an error when changing routes, or a route load is cancelled
  * `err.cancelled` - Indicates if the navigation was cancelled
* `beforeHistoryChange(url, { shallow })` - Fires before changing the browser's history
* `hashChangeStart(url, { shallow })` - Fires when the hash will change but not the page
* `hashChangeComplete(url, { shallow })` - Fires when the hash has changed but not the page

> **Good to know**: Here `url` is the URL shown in the browser, including the [`basePath`](/docs/app/api-reference/config/next-config-js/basePath).

For example, to listen to the router event `routeChangeStart`, open or create `pages/_app.js` and subscribe to the event, like so:

```jsx
import { useEffect } from 'react'
import { useRouter } from 'next/router'

export default function MyApp({ Component, pageProps }) {
  const router = useRouter()

  useEffect(() => {
    const handleRouteChange = (url, { shallow }) => {
      console.log(
        `App is changing to ${url} ${
          shallow ? 'with' : 'without'
        } shallow routing`
      )
    }

    router.events.on('routeChangeStart', handleRouteChange)

    // If the component is unmounted, unsubscribe
    // from the event with the `off` method:
    return () => {
      router.events.off('routeChangeStart', handleRouteChange)
    }
  }, [router])

  return
}
```

> We use a [Custom App](/docs/pages/building-your-application/routing/custom-app) (`pages/_app.js`) for this example to subscribe to the event because it's not unmounted on page navigations, but you can subscribe to router events on any component in your application.

Router events should be registered when a component mounts ([useEffect](https://react.dev/reference/react/useEffect) or [componentDidMount](https://react.dev/reference/react/Component#componentdidmount) / [componentWillUnmount](https://react.dev/reference/react/Component#componentwillunmount)) or imperatively when an event happens.

If a route load is cancelled (for example, by clicking two links rapidly in succession), `routeChangeError` will fire. And the passed `err` will contain a `cancelled` property set to `true`, as in the following example:

```jsx
import { useEffect } from 'react'
import { useRouter } from 'next/router'

export default function MyApp({ Component, pageProps }) {
  const router = useRouter()

  useEffect(() => {
    const handleRouteChangeError = (err, url) => {
      if (err.cancelled) {
        console.log(`Route to ${url} was cancelled!`)
      }
    }

    router.events.on('routeChangeError', handleRouteChangeError)

    // If the component is unmounted, unsubscribe
    // from the event with the `off` method:
    return () => {
      router.events.off('routeChangeError', handleRouteChangeError)
    }
  }, [router])

  return
}
```

## The `next/compat/router` export

This is the same `useRouter` hook, but can be used in both `app` and `pages` directories.

It differs from `next/router` in that it does not throw an error when the pages router is not mounted, and instead has a return type of `NextRouter | null`.
This allows developers to convert components to support running in both `app` and `pages` as they transition to the `app` router.

A component that previously looked like this:

```jsx
import { useRouter } from 'next/router'
const MyComponent = () => {
  const { isReady, query } = useRouter()
  // ...
}
```

Will error when converted over to `next/compat/router`, as `null` cannot be destructured. Instead, developers will be able to take advantage of new hooks:

```jsx
import { useEffect } from 'react'
import { useRouter } from 'next/compat/router'
import { useSearchParams } from 'next/navigation'
const MyComponent = () => {
  const router = useRouter() // may be null or a NextRouter instance
  const searchParams = useSearchParams()
  useEffect(() => {
    if (router && !router.isReady) {
      return
    }
    // In `app/`, searchParams will be ready immediately with the values, in
    // `pages/` it will be available after the router is ready.
    const search = searchParams.get('search')
    // ...
  }, [router, searchParams])
  // ...
}
```

This component will now work in both `pages` and `app` directories. When the component is no longer used in `pages`, you can remove the references to the compat router:

```jsx
import { useSearchParams } from 'next/navigation'
const MyComponent = () => {
  const searchParams = useSearchParams()
  // As this component is only used in `app/`, the compat router can be removed.
  const search = searchParams.get('search')
  // ...
}
```

### Using `useRouter` outside of Next.js context in pages

Another specific use case is when rendering components outside of a Next.js application context, such as inside `getServerSideProps` on the `pages` directory. In this case, the compat router can be used to avoid errors:

```jsx
import { renderToString } from 'react-dom/server'
import { useRouter } from 'next/compat/router'
const MyComponent = () => {
  const router = useRouter() // may be null or a NextRouter instance
  // ...
}
export async function getServerSideProps() {
  const renderedComponent = renderToString()
  return {
    props: {
      renderedComponent,
    },
  }
}
```

## Potential ESLint errors

Certain methods accessible on the `router` object return a Promise. If you have the ESLint rule, [no-floating-promises](https://typescript-eslint.io/rules/no-floating-promises) enabled, consider disabling it either globally, or for the affected line.

If your application needs this rule, you should either `void` the promise – or use an `async` function, `await` the Promise, then void the function call. **This is not applicable when the method is called from inside an `onClick` handler**.

The affected methods are:

* `router.push`
* `router.replace`
* `router.prefetch`

### Potential solutions

```jsx
import { useEffect } from 'react'
import { useRouter } from 'next/router'

// Here you would fetch and return the user
const useUser = () => ({ user: null, loading: false })

export default function Page() {
  const { user, loading } = useUser()
  const router = useRouter()

  useEffect(() => {
    // disable the linting on the next line - This is the cleanest solution
    // eslint-disable-next-line no-floating-promises
    router.push('/login')

    // void the Promise returned by router.push
    if (!(user || loading)) {
      void router.push('/login')
    }
    // or use an async function, await the Promise, then void the function call
    async function handleRouteChange() {
      if (!(user || loading)) {
        await router.push('/login')
      }
    }
    void handleRouteChange()
  }, [user, loading])

  return Redirecting...

}
```

## withRouter

If [`useRouter`](#router-object) is not the best fit for you, `withRouter` can also add the same [`router` object](#router-object) to any component.

### Usage

```jsx
import { withRouter } from 'next/router'

function Page({ router }) {
  return {router.pathname}

}

export default withRouter(Page)
```

### TypeScript

To use class components with `withRouter`, the component needs to accept a router prop:

```tsx
import React from 'react'
import { withRouter, NextRouter } from 'next/router'

interface WithRouterProps {
  router: NextRouter
}

interface MyComponentProps extends WithRouterProps {}

class MyComponent extends React.Component {
  render() {
    return {this.props.router.pathname}

  }
}

export default withRouter(MyComponent)
```

---
title: useSearchParams
description: API Reference for the useSearchParams hook in the Pages Router.
url: "https://nextjs.org/docs/pages/api-reference/functions/use-search-params"
version: 16.2.6
router: Pages Router
---

# useSearchParams

`useSearchParams` is a hook that lets you read the current URL's **query string**.

`useSearchParams` returns a **read-only** version of the [`URLSearchParams`](https://developer.mozilla.org/docs/Web/API/URLSearchParams) interface.

```tsx filename="pages/dashboard.tsx" switcher
import { useSearchParams } from 'next/navigation'

export default function Dashboard() {
  const searchParams = useSearchParams()

  if (!searchParams) {
    // Render fallback UI while search params are not yet available
    return null
  }

  const search = searchParams.get('search')

  // URL -> `/dashboard?search=my-project`
  // `search` -> 'my-project'
  return <>Search: {search}
}
```

```jsx filename="pages/dashboard.js" switcher
import { useSearchParams } from 'next/navigation'

export default function Dashboard() {
  const searchParams = useSearchParams()

  if (!searchParams) {
    // Render fallback UI while search params are not yet available
    return null
  }

  const search = searchParams.get('search')

  // URL -> `/dashboard?search=my-project`
  // `search` -> 'my-project'
  return <>Search: {search}
}
```

## Parameters

```tsx
const searchParams = useSearchParams()
```

`useSearchParams` does not take any parameters.

## Returns

`useSearchParams` returns a **read-only** version of the [`URLSearchParams`](https://developer.mozilla.org/docs/Web/API/URLSearchParams) interface, or `null` during [prerendering](#behavior-during-prerendering).

The interface includes utility methods for reading the URL's query string:

* [`URLSearchParams.get()`](https://developer.mozilla.org/docs/Web/API/URLSearchParams/get): Returns the first value associated with the search parameter. For example:

  | URL                  | `searchParams.get("a")`                                                                                         |
  | -------------------- | --------------------------------------------------------------------------------------------------------------- |
  | `/dashboard?a=1`     | `'1'`                                                                                                           |
  | `/dashboard?a=`      | `''`                                                                                                            |
  | `/dashboard?b=3`     | `null`                                                                                                          |
  | `/dashboard?a=1&a=2` | `'1'` *- use [`getAll()`](https://developer.mozilla.org/docs/Web/API/URLSearchParams/getAll) to get all values* |

* [`URLSearchParams.has()`](https://developer.mozilla.org/docs/Web/API/URLSearchParams/has): Returns a boolean value indicating if the given parameter exists. For example:

  | URL              | `searchParams.has("a")` |
  | ---------------- | ----------------------- |
  | `/dashboard?a=1` | `true`                  |
  | `/dashboard?b=3` | `false`                 |

* Learn more about other **read-only** methods of [`URLSearchParams`](https://developer.mozilla.org/docs/Web/API/URLSearchParams), including the [`getAll()`](https://developer.mozilla.org/docs/Web/API/URLSearchParams/getAll), [`keys()`](https://developer.mozilla.org/docs/Web/API/URLSearchParams/keys), [`values()`](https://developer.mozilla.org/docs/Web/API/URLSearchParams/values), [`entries()`](https://developer.mozilla.org/docs/Web/API/URLSearchParams/entries), [`forEach()`](https://developer.mozilla.org/docs/Web/API/URLSearchParams/forEach), and [`toString()`](https://developer.mozilla.org/docs/Web/API/URLSearchParams/toString).

> **Good to know**: `useSearchParams` is a [React Hook](https://react.dev/learn#using-hooks) and cannot be used with classes.

## Behavior

### Behavior during prerendering

For pages that are [statically optimized](/docs/pages/building-your-application/rendering/automatic-static-optimization) (not using `getServerSideProps`), `useSearchParams` will return `null` during prerendering. After hydration, the value will be updated to the actual search params.

This is because search params cannot be known during static generation as they depend on the request.

```tsx filename="pages/dashboard.tsx" switcher
import { useSearchParams } from 'next/navigation'

export default function Dashboard() {
  const searchParams = useSearchParams()

  if (!searchParams) {
    // Return a fallback UI while search params are loading
    // This prevents hydration mismatches
    return
  }

  const search = searchParams.get('search')

  return <>Search: {search}
}
```

```jsx filename="pages/dashboard.js" switcher
import { useSearchParams } from 'next/navigation'

export default function Dashboard() {
  const searchParams = useSearchParams()

  if (!searchParams) {
    // Return a fallback UI while search params are loading
    // This prevents hydration mismatches
    return
  }

  const search = searchParams.get('search')

  return <>Search: {search}
}
```

### Using with `getServerSideProps`

When using [`getServerSideProps`](/docs/pages/building-your-application/data-fetching/get-server-side-props), the page is server-rendered on each request and `useSearchParams` will return the actual search params immediately:

```tsx filename="pages/dashboard.tsx" switcher
import { useSearchParams } from 'next/navigation'

export default function Dashboard() {
  const searchParams = useSearchParams()

  // With getServerSideProps, this fallback is never rendered because
  // searchParams is always available on the server. However, keeping
  // the fallback allows this component to be reused on other pages
  // that may not use getServerSideProps.
  if (!searchParams) {
    return null
  }

  const search = searchParams.get('search')

  return <>Search: {search}
}

export async function getServerSideProps() {
  return { props: {} }
}
```

```jsx filename="pages/dashboard.js" switcher
import { useSearchParams } from 'next/navigation'

export default function Dashboard() {
  const searchParams = useSearchParams()

  // With getServerSideProps, this fallback is never rendered because
  // searchParams is always available on the server. However, keeping
  // the fallback allows this component to be reused on other pages
  // that may not use getServerSideProps.
  if (!searchParams) {
    return null
  }

  const search = searchParams.get('search')

  return <>Search: {search}
}

export async function getServerSideProps() {
  return { props: {} }
}
```

## Examples

### Updating search params

You can use the [`useRouter`](/docs/pages/api-reference/functions/use-router) hook to update search params:

```tsx filename="pages/dashboard.tsx" switcher
import { useRouter } from 'next/router'
import { useSearchParams } from 'next/navigation'
import { useCallback } from 'react'

export default function Dashboard() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const createQueryString = useCallback(
    (name: string, value: string) => {
      const params = new URLSearchParams(searchParams?.toString())
      params.set(name, value)
      return params.toString()
    },
    [searchParams]
  )

  if (!searchParams) {
    return null
  }

  return (
    <>
      Sort By

       {
          router.push(router.pathname + '?' + createQueryString('sort', 'asc'))
        }}
      >
        ASC

       {
          router.push(router.pathname + '?' + createQueryString('sort', 'desc'))
        }}
      >
        DESC

  )
}
```

```jsx filename="pages/dashboard.js" switcher
import { useRouter } from 'next/router'
import { useSearchParams } from 'next/navigation'
import { useCallback } from 'react'

export default function Dashboard() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const createQueryString = useCallback(
    (name, value) => {
      const params = new URLSearchParams(searchParams?.toString())
      params.set(name, value)
      return params.toString()
    },
    [searchParams]
  )

  if (!searchParams) {
    return null
  }

  return (
    <>
      Sort By

       {
          router.push(router.pathname + '?' + createQueryString('sort', 'asc'))
        }}
      >
        ASC

       {
          router.push(router.pathname + '?' + createQueryString('sort', 'desc'))
        }}
      >
        DESC

  )
}
```

### Sharing components with App Router

`useSearchParams` from `next/navigation` works in both the Pages Router and App Router. This allows you to create shared components that work in either context:

```tsx filename="components/search-bar.tsx" switcher
import { useSearchParams } from 'next/navigation'

// This component works in both pages/ and app/
export function SearchBar() {
  const searchParams = useSearchParams()

  if (!searchParams) {
    // Fallback for Pages Router during prerendering
    return
  }

  const search = searchParams.get('search') ?? ''

  return
}
```

```jsx filename="components/search-bar.js" switcher
import { useSearchParams } from 'next/navigation'

// This component works in both pages/ and app/
export function SearchBar() {
  const searchParams = useSearchParams()

  if (!searchParams) {
    // Fallback for Pages Router during prerendering
    return
  }

  const search = searchParams.get('search') ?? ''

  return
}
```

> **Good to know**: When using this component in the App Router, wrap it in a `` boundary for [prerendering](/docs/app/api-reference/functions/use-search-params#prerendering) support.

## Version History

| Version   | Changes                       |
| --------- | ----------------------------- |
| `v13.0.0` | `useSearchParams` introduced. |

---
title: userAgent
description: The userAgent helper extends the Web Request API with additional properties and methods to interact with the user agent object from the request.
url: "https://nextjs.org/docs/pages/api-reference/functions/userAgent"
version: 16.2.6
router: Pages Router
---

# userAgent

The `userAgent` helper extends the [Web Request API](https://developer.mozilla.org/docs/Web/API/Request) with additional properties and methods to interact with the user agent object from the request.

```ts filename="proxy.ts" switcher
import { NextRequest, NextResponse, userAgent } from 'next/server'

export function proxy(request: NextRequest) {
  const url = request.nextUrl
  const { device } = userAgent(request)

  // device.type can be: 'mobile', 'tablet', 'console', 'smarttv',
  // 'wearable', 'embedded', or undefined (for desktop browsers)
  const viewport = device.type || 'desktop'

  url.searchParams.set('viewport', viewport)
  return NextResponse.rewrite(url)
}
```

```js filename="proxy.js" switcher
import { NextResponse, userAgent } from 'next/server'

export function proxy(request) {
  const url = request.nextUrl
  const { device } = userAgent(request)

  // device.type can be: 'mobile', 'tablet', 'console', 'smarttv',
  // 'wearable', 'embedded', or undefined (for desktop browsers)
  const viewport = device.type || 'desktop'

  url.searchParams.set('viewport', viewport)
  return NextResponse.rewrite(url)
}
```

## `isBot`

A boolean indicating whether the request comes from a known bot.

## `browser`

An object containing information about the browser used in the request.

* `name`: A string representing the browser's name, or `undefined` if not identifiable.
* `version`: A string representing the browser's version, or `undefined`.

## `device`

An object containing information about the device used in the request.

* `model`: A string representing the model of the device, or `undefined`.
* `type`: A string representing the type of the device, such as `console`, `mobile`, `tablet`, `smarttv`, `wearable`, `embedded`, or `undefined`.
* `vendor`: A string representing the vendor of the device, or `undefined`.

## `engine`

An object containing information about the browser's engine.

* `name`: A string representing the engine's name. Possible values include: `Amaya`, `Blink`, `EdgeHTML`, `Flow`, `Gecko`, `Goanna`, `iCab`, `KHTML`, `Links`, `Lynx`, `NetFront`, `NetSurf`, `Presto`, `Tasman`, `Trident`, `w3m`, `WebKit` or `undefined`.
* `version`: A string representing the engine's version, or `undefined`.

## `os`

An object containing information about the operating system.

* `name`: A string representing the name of the OS, or `undefined`.
* `version`: A string representing the version of the OS, or `undefined`.

## `cpu`

An object containing information about the CPU architecture.

* `architecture`: A string representing the architecture of the CPU. Possible values include: `68k`, `amd64`, `arm`, `arm64`, `armhf`, `avr`, `ia32`, `ia64`, `irix`, `irix64`, `mips`, `mips64`, `pa-risc`, `ppc`, `sparc`, `sparc64` or `undefined`

---
title: Configuration
description: Learn how to configure your Next.js application.
url: "https://nextjs.org/docs/pages/api-reference/config"
version: 16.2.6
router: Pages Router
---

# Configuration

 - [next.config.js Options](/docs/pages/api-reference/config/next-config-js)
 - [TypeScript](/docs/pages/api-reference/config/typescript)
 - [ESLint](/docs/pages/api-reference/config/eslint)

---
title: next.config.js Options
description: Learn about the options available in next.config.js for the Pages Router.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js"
version: 16.2.6
router: Pages Router
---

# next.config.js Options

Next.js can be configured through a `next.config.js` file in the root of your project directory (for example, by `package.json`) with a default export.

```js filename="next.config.js"
// @ts-check

/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
}

module.exports = nextConfig
```

## ECMAScript Modules

`next.config.js` is a regular Node.js module, not a JSON file. It gets used by the Next.js server and build phases, and it's not included in the browser build.

If you need [ECMAScript modules](https://nodejs.org/api/esm.html), you can use `next.config.mjs`:

```js filename="next.config.mjs"
// @ts-check

/**
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  /* config options here */
}

export default nextConfig
```

> **Good to know**: `next.config` with the `.cjs` or `.cts` extensions are currently **not** supported.

## Configuration as a Function

You can also use a function:

```js filename="next.config.mjs"
// @ts-check

export default (phase, { defaultConfig }) => {
  /**
   * @type {import('next').NextConfig}
   */
  const nextConfig = {
    /* config options here */
  }
  return nextConfig
}
```

### Async Configuration

Since Next.js 12.1.0, you can use an async function:

```js filename="next.config.js"
// @ts-check

module.exports = async (phase, { defaultConfig }) => {
  /**
   * @type {import('next').NextConfig}
   */
  const nextConfig = {
    /* config options here */
  }
  return nextConfig
}
```

### Phase

`phase` is the current context in which the configuration is loaded. You can see the [available phases](https://github.com/vercel/next.js/blob/5e6b008b561caf2710ab7be63320a3d549474a5b/packages/next/shared/lib/constants.ts#L19-L23). Phases can be imported from `next/constants`:

```js filename="next.config.js"
// @ts-check

const { PHASE_DEVELOPMENT_SERVER } = require('next/constants')

module.exports = (phase, { defaultConfig }) => {
  if (phase === PHASE_DEVELOPMENT_SERVER) {
    return {
      /* development only config options here */
    }
  }

  return {
    /* config options for all phases except development here */
  }
}
```

## TypeScript

If you are using TypeScript in your project, you can use `next.config.ts` to use TypeScript in your configuration:

```ts filename="next.config.ts"
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  /* config options here */
}

export default nextConfig
```

The commented lines are the place where you can put the configs allowed by `next.config.js`, which are [defined in this file](https://github.com/vercel/next.js/blob/canary/packages/next/src/server/config-shared.ts).

However, none of the configs are required, and it's not necessary to understand what each config does. Instead, search for the features you need to enable or modify in this section and they will show you what to do.

> Avoid using new JavaScript features not available in your target Node.js version. `next.config.js` will not be parsed by Webpack or Babel.

This page documents all the available configuration options:

## Unit Testing (experimental)

Starting in Next.js 15.1, the `next/experimental/testing/server` package contains utilities to help unit test `next.config.js` files.

The `unstable_getResponseFromNextConfig` function runs the [`headers`](/docs/app/api-reference/config/next-config-js/headers), [`redirects`](/docs/app/api-reference/config/next-config-js/redirects), and [`rewrites`](/docs/app/api-reference/config/next-config-js/rewrites) functions from `next.config.js` with the provided request information and returns `NextResponse` with the results of the routing.

> The response from `unstable_getResponseFromNextConfig` only considers `next.config.js` fields and does not consider proxy or filesystem routes, so the result in production may be different than the unit test.

```js
import {
  getRedirectUrl,
  unstable_getResponseFromNextConfig,
} from 'next/experimental/testing/server'

const response = await unstable_getResponseFromNextConfig({
  url: 'https://nextjs.org/test',
  nextConfig: {
    async redirects() {
      return [{ source: '/test', destination: '/test2', permanent: false }]
    },
  },
})
expect(response.status).toEqual(307)
expect(getRedirectUrl(response)).toEqual('https://nextjs.org/test2')
```

 - [adapterPath](/docs/pages/api-reference/config/next-config-js/adapterPath)
 - [allowedDevOrigins](/docs/pages/api-reference/config/next-config-js/allowedDevOrigins)
 - [assetPrefix](/docs/pages/api-reference/config/next-config-js/assetPrefix)
 - [basePath](/docs/pages/api-reference/config/next-config-js/basePath)
 - [bundlePagesRouterDependencies](/docs/pages/api-reference/config/next-config-js/bundlePagesRouterDependencies)
 - [compress](/docs/pages/api-reference/config/next-config-js/compress)
 - [crossOrigin](/docs/pages/api-reference/config/next-config-js/crossOrigin)
 - [deploymentId](/docs/pages/api-reference/config/next-config-js/deploymentId)
 - [devIndicators](/docs/pages/api-reference/config/next-config-js/devIndicators)
 - [distDir](/docs/pages/api-reference/config/next-config-js/distDir)
 - [env](/docs/pages/api-reference/config/next-config-js/env)
 - [exportPathMap](/docs/pages/api-reference/config/next-config-js/exportPathMap)
 - [generateBuildId](/docs/pages/api-reference/config/next-config-js/generateBuildId)
 - [generateEtags](/docs/pages/api-reference/config/next-config-js/generateEtags)
 - [headers](/docs/pages/api-reference/config/next-config-js/headers)
 - [httpAgentOptions](/docs/pages/api-reference/config/next-config-js/httpAgentOptions)
 - [images](/docs/pages/api-reference/config/next-config-js/images)
 - [logging](/docs/pages/api-reference/config/next-config-js/logging)
 - [onDemandEntries](/docs/pages/api-reference/config/next-config-js/onDemandEntries)
 - [optimizePackageImports](/docs/pages/api-reference/config/next-config-js/optimizePackageImports)
 - [output](/docs/pages/api-reference/config/next-config-js/output)
 - [pageExtensions](/docs/pages/api-reference/config/next-config-js/pageExtensions)
 - [poweredByHeader](/docs/pages/api-reference/config/next-config-js/poweredByHeader)
 - [productionBrowserSourceMaps](/docs/pages/api-reference/config/next-config-js/productionBrowserSourceMaps)
 - [experimental.proxyClientMaxBodySize](/docs/pages/api-reference/config/next-config-js/proxyClientMaxBodySize)
 - [reactStrictMode](/docs/pages/api-reference/config/next-config-js/reactStrictMode)
 - [redirects](/docs/pages/api-reference/config/next-config-js/redirects)
 - [rewrites](/docs/pages/api-reference/config/next-config-js/rewrites)
 - [serverExternalPackages](/docs/pages/api-reference/config/next-config-js/serverExternalPackages)
 - [trailingSlash](/docs/pages/api-reference/config/next-config-js/trailingSlash)
 - [transpilePackages](/docs/pages/api-reference/config/next-config-js/transpilePackages)
 - [turbopack](/docs/pages/api-reference/config/next-config-js/turbopack)
 - [typescript](/docs/pages/api-reference/config/next-config-js/typescript)
 - [urlImports](/docs/pages/api-reference/config/next-config-js/urlImports)
 - [useLightningcss](/docs/pages/api-reference/config/next-config-js/useLightningcss)
 - [webpack](/docs/pages/api-reference/config/next-config-js/webpack)
 - [webVitalsAttribution](/docs/pages/api-reference/config/next-config-js/webVitalsAttribution)

---
title: adapterPath
description: Configure a custom adapter for Next.js to hook into the build process.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/adapterPath"
version: 16.2.6
router: Pages Router
---

# adapterPath

Next.js provides a built-in adapters API. It allows deployment platforms or build systems to integrate with the Next.js build process.

For a full reference implementation, see the [`nextjs/adapter-vercel`](https://github.com/nextjs/adapter-vercel) adapter.

## Configuration

To use an adapter, specify the path to your adapter module in `adapterPath`:

```js filename="next.config.js"
/** @type {import('next').NextConfig} */
const nextConfig = {
  adapterPath: require.resolve('./my-adapter.js'),
}

module.exports = nextConfig
```

Alternatively `NEXT_ADAPTER_PATH` can be set to enable zero-config usage in deployment platforms.

## Adapters

For full adapter implementation details, use the dedicated Adapters section:

* [Configuration](/docs/app/api-reference/adapters/configuration)
* [Creating an Adapter](/docs/app/api-reference/adapters/creating-an-adapter)
* [API Reference](/docs/app/api-reference/adapters/api-reference)
* [Testing Adapters](/docs/app/api-reference/adapters/testing-adapters)
* [Routing with `@next/routing`](/docs/app/api-reference/adapters/routing-with-next-routing)
* [Implementing PPR in an Adapter](/docs/app/api-reference/adapters/implementing-ppr-in-an-adapter)
* [Runtime Integration](/docs/app/api-reference/adapters/runtime-integration)
* [Invoking Entrypoints](/docs/app/api-reference/adapters/invoking-entrypoints)
* [Output Types](/docs/app/api-reference/adapters/output-types)
* [Routing Information](/docs/app/api-reference/adapters/routing-information)
* [Use Cases](/docs/app/api-reference/adapters/use-cases)

## Creating an Adapter

See [Creating an Adapter](/docs/app/api-reference/adapters/creating-an-adapter).

## API Reference

See [API Reference](/docs/app/api-reference/adapters/api-reference).

## Testing Adapters

See [Testing Adapters](/docs/app/api-reference/adapters/testing-adapters).

## Routing with `@next/routing`

See [Routing with `@next/routing`](/docs/app/api-reference/adapters/routing-with-next-routing).

## Implementing PPR in an Adapter

See [Implementing PPR in an Adapter](/docs/app/api-reference/adapters/implementing-ppr-in-an-adapter).

## Runtime Integration

See [Runtime Integration](/docs/app/api-reference/adapters/runtime-integration).

## Invoking Entrypoints

See [Invoking Entrypoints](/docs/app/api-reference/adapters/invoking-entrypoints).

## Output Types

See [Output Types](/docs/app/api-reference/adapters/output-types).

## Routing Information

See [Routing Information](/docs/app/api-reference/adapters/routing-information).

## Use Cases

See [Use Cases](/docs/app/api-reference/adapters/use-cases).

---
title: allowedDevOrigins
description: "Use `allowedDevOrigins` to configure additional origins that can request the dev server."
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/allowedDevOrigins"
version: 16.2.6
router: Pages Router
---

# allowedDevOrigins

Next.js blocks cross-origin requests to dev-only assets and endpoints during development by default to prevent unauthorized access.

To configure a Next.js application to allow requests from origins other than the hostname the server was initialized with (`localhost` by default), use the `allowedDevOrigins` config option.

`allowedDevOrigins` lets you set additional origins that can request the dev server in development mode. For example, to use `local-origin.dev` instead of only `localhost`, open `next.config.js` and add the `allowedDevOrigins` config:

```js filename="next.config.js"
module.exports = {
  allowedDevOrigins: ['local-origin.dev', '*.local-origin.dev'],
}
```

---
title: assetPrefix
description: Learn how to use the assetPrefix config option to configure your CDN.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/assetPrefix"
version: 16.2.6
router: Pages Router
---

# assetPrefix

> **Attention**: [Deploying to Vercel](/docs/pages/getting-started/deploying) automatically configures a global CDN for your Next.js project.
> You do not need to manually setup an Asset Prefix.

> **Good to know**: Next.js 9.5+ added support for a customizable [Base Path](/docs/app/api-reference/config/next-config-js/basePath), which is better
> suited for hosting your application on a sub-path like `/docs`.
> We do not suggest you use a custom Asset Prefix for this use case.

## Set up a CDN

To set up a [CDN](https://en.wikipedia.org/wiki/Content_delivery_network), you can set up an asset prefix and configure your CDN's origin to resolve to the domain that Next.js is hosted on.

Open `next.config.mjs` and add the `assetPrefix` config based on the [phase](/docs/app/api-reference/config/next-config-js#async-configuration):

```js filename="next.config.mjs"
// @ts-check
import { PHASE_DEVELOPMENT_SERVER } from 'next/constants'

export default (phase) => {
  const isDev = phase === PHASE_DEVELOPMENT_SERVER
  /**
   * @type {import('next').NextConfig}
   */
  const nextConfig = {
    assetPrefix: isDev ? undefined : 'https://cdn.mydomain.com',
  }
  return nextConfig
}
```

Next.js will automatically use your asset prefix for the JavaScript and CSS files it loads from the `/_next/` path (`.next/static/` folder). For example, with the above configuration, the following request for a JS chunk:

```
/_next/static/chunks/4b9b41aaa062cbbfeff4add70f256968c51ece5d.4d708494b3aed70c04f0.js
```

Would instead become:

```
https://cdn.mydomain.com/_next/static/chunks/4b9b41aaa062cbbfeff4add70f256968c51ece5d.4d708494b3aed70c04f0.js
```

The exact configuration for uploading your files to a given CDN will depend on your CDN of choice. The only folder you need to host on your CDN is the contents of `.next/static/`, which should be uploaded as `_next/static/` as the above URL request indicates. **Do not upload the rest of your `.next/` folder**, as you should not expose your server code and other configuration to the public.

While `assetPrefix` covers requests to `_next/static`, it does not influence the following paths:

* Files in the [public](/docs/pages/api-reference/file-conventions/public-folder) folder; if you want to serve those assets over a CDN, you'll have to introduce the prefix yourself
* `/_next/data/` requests for `getServerSideProps` pages. These requests will always be made against the main domain since they're not static.
* `/_next/data/` requests for `getStaticProps` pages. These requests will always be made against the main domain to support [Incremental Static Generation](/docs/pages/guides/incremental-static-regeneration), even if you're not using it (for consistency).

---
title: basePath
description: "Use `basePath` to deploy a Next.js application under a sub-path of a domain."
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/basePath"
version: 16.2.6
router: Pages Router
---

# basePath

To deploy a Next.js application under a sub-path of a domain you can use the `basePath` config option.

`basePath` allows you to set a path prefix for the application. For example, to use `/docs` instead of `''` (an empty string, the default), open `next.config.js` and add the `basePath` config:

```js filename="next.config.js"
module.exports = {
  basePath: '/docs',
}
```

> **Good to know**: This value must be set at build time and cannot be changed without re-building as the value is inlined in the client-side bundles.

### Links

When linking to other pages using `next/link` and `next/router` the `basePath` will be automatically applied.

For example, using `/about` will automatically become `/docs/about` when `basePath` is set to `/docs`.

```js
export default function HomePage() {
  return (
    <>
      About Page

  )
}
```

Output html:

```html
About Page
```

This makes sure that you don't have to change all links in your application when changing the `basePath` value.

### Images

When using the [`next/image`](/docs/pages/api-reference/components/image) component, you will need to add the `basePath` in front of `src`.

For example, using `/docs/me.png` will properly serve your image when `basePath` is set to `/docs`.

```jsx
import Image from 'next/image'

function Home() {
  return (
    <>
      My Homepage

      Welcome to my homepage!

  )
}

export default Home
```

---
title: bundlePagesRouterDependencies
description: Enable automatic dependency bundling for Pages Router
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/bundlePagesRouterDependencies"
version: 16.2.6
router: Pages Router
---

# bundlePagesRouterDependencies

Enable automatic server-side dependency bundling for Pages Router applications. Matches the automatic dependency bundling in App Router.

```js filename="next.config.js"
/** @type {import('next').NextConfig} */
const nextConfig = {
  bundlePagesRouterDependencies: true,
}

module.exports = nextConfig
```

Explicitly opt-out certain packages from being bundled using the [`serverExternalPackages`](/docs/pages/api-reference/config/next-config-js/serverExternalPackages) option.

## Version History

| Version   | Changes                                                                                                   |
| --------- | --------------------------------------------------------------------------------------------------------- |
| `v15.0.0` | Moved from experimental to stable. Renamed from `bundlePagesExternals` to `bundlePagesRouterDependencies` |

---
title: compress
description: Next.js provides gzip compression to compress rendered content and static files, it only works with the server target. Learn more about it here.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/compress"
version: 16.2.6
router: Pages Router
---

# compress

By default, Next.js uses `gzip` to compress rendered content and static files when using `next start` or a custom server. This is an optimization for applications that do not have compression configured. If compression is *already* configured in your application via a custom server, Next.js will not add compression.

You can check if compression is enabled and which algorithm is used by looking at the [`Accept-Encoding`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Encoding) (browser accepted options) and [`Content-Encoding`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Encoding) (currently used) headers in the response.

## Disabling compression

To disable **compression**, set the `compress` config option to `false`:

```js filename="next.config.js"
module.exports = {
  compress: false,
}
```

We **do not recommend disabling compression** unless you have compression configured on your server, as compression reduces bandwidth usage and improves the performance of your application. For example, you're using [nginx](https://nginx.org/) and want to switch to `brotli`, set the `compress` option to `false` to allow nginx to handle compression.

---
title: crossOrigin
description: "Use the `crossOrigin` option to add a crossOrigin tag on the `script` tags generated by `next/script` and `next/head`."
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/crossOrigin"
version: 16.2.6
router: Pages Router
---

# crossOrigin

Use the `crossOrigin` option to add a [`crossOrigin` attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/crossorigin) in all `` tags generated by the  [`next/script`](/docs/pages/guides/scripts) and [`next/head`](/docs/pages/api-reference/components/head)components, and define how cross-origin requests should be handled.

```js filename="next.config.js"
module.exports = {
  crossOrigin: 'anonymous',
}
```

## Options

* `'anonymous'`: Adds [`crossOrigin="anonymous"`](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/crossorigin#anonymous) attribute.
* `'use-credentials'`: Adds [`crossOrigin="use-credentials"`](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/crossorigin#use-credentials).

---
title: deploymentId
description: Configure a deployment identifier used for version skew protection and cache busting.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/deploymentId"
version: 16.2.6
router: Pages Router
---

# deploymentId

The `deploymentId` option allows you to set an identifier for your deployment. This identifier is used for [version skew](/docs/app/guides/self-hosting#version-skew) protection and cache busting during rolling deployments.

```js filename="next.config.js"
module.exports = {
  deploymentId: 'my-deployment-id',
}
```

You can also set the deployment ID using the `NEXT_DEPLOYMENT_ID` environment variable:

```bash
NEXT_DEPLOYMENT_ID=my-deployment-id next build
```

> **Good to know:** If both are set, the `deploymentId` value in `next.config.js` takes precedence over the `NEXT_DEPLOYMENT_ID` environment variable.

## How it works

When a `deploymentId` is configured, Next.js:

1. Appends `?dpl=` to static asset URLs (JavaScript, CSS, images)
2. Adds an `x-deployment-id` header to client-side navigation requests
3. Adds an `x-nextjs-deployment-id` header to navigation responses
4. Injects a `data-dpl-id` attribute on the `` element

When the client detects a mismatch between its deployment ID and the server's (via the response header), it triggers a hard navigation (full page reload) instead of a client-side navigation. This ensures users always receive assets  from a consistent deployment version.

> **Good to know:** Next.js does not read the `?dpl=` query parameter on incoming requests. The query parameter is for cache busting (ensuring browsers and CDNs fetch fresh assets), not for routing. If you need version-aware routing, consult your hosting provider or CDN's documentation for implementing deployment-based routing.

## Use cases

### Rolling deployments

During a rolling deployment, some server instances may be running the new version while others are still running the old version. Without a deployment ID, users might receive a mix of old and new assets, causing errors.

Setting a consistent `deploymentId` per deployment ensures:

* Clients always request assets from a matching deployment version
* Mismatches trigger a full reload to fetch the correct assets

### Multi-server environments

When running multiple instances of your Next.js application behind a load balancer, all instances for the same deployment should use the same `deploymentId`.

```js filename="next.config.js"
module.exports = {
  deploymentId: process.env.DEPLOYMENT_VERSION || process.env.GIT_SHA,
}
```

## Version History

| Version    | Changes                                               |
| ---------- | ----------------------------------------------------- |
| `v14.1.4`  | `deploymentId` stabilized as top-level config option. |
| `v13.4.10` | `experimental.deploymentId` introduced.               |

## Related

* [Self-Hosting - Version Skew](/docs/app/guides/self-hosting#version-skew)
* [generateBuildId](/docs/app/api-reference/config/next-config-js/generateBuildId)

---
title: devIndicators
description: "Optimized pages include an indicator to let you know if it's being statically optimized. You can opt-out of it here."
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/devIndicators"
version: 16.2.6
router: Pages Router
---

# devIndicators

`devIndicators` allows you to configure the on-screen indicator that gives context about the current route you're viewing during development.

Open `next.config.ts` and set `position` to choose where the indicator renders. The default is `bottom-left`.

```ts filename="next.config.ts"
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  devIndicators: {
    position: 'bottom-right', // 'bottom-left' | 'bottom-right' | 'top-left' | 'top-right'
  },
}

export default nextConfig
```

To hide the indicator entirely, set `devIndicators` to `false`. Next.js will still surface any compile or runtime errors that were encountered.

```ts filename="next.config.ts"
const nextConfig: NextConfig = {
  devIndicators: false,
}

export default nextConfig
```

## Troubleshooting

### Indicator not marking a route as static

If you expect a route to be static and the indicator has marked it as dynamic, it's likely the route has opted out of prerendering.

You can confirm if a route is [prerendered](/docs/app/glossary#prerendering) or [dynamically rendered](/docs/app/glossary#dynamic-rendering) by building your application using `next build --debug`, and checking the output in your terminal. Static (or prerendered) routes will display a `○` symbol, whereas dynamic routes will display a `ƒ` symbol. For example:

```bash filename="Build Output"
Route (app)
┌ ○ /_not-found
└ ƒ /products/[id]

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```

When exporting [`getServerSideProps`](/docs/pages/building-your-application/data-fetching/get-server-side-props) or [`getInitialProps`](/docs/pages/api-reference/functions/get-initial-props) from a page, it will be marked as dynamic.

## Version History

| Version   | Changes                                                                                                                                             |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `v16.0.0` | `appIsrStatus`, `buildActivity`, and `buildActivityPosition` options have been removed.                                                             |
| `v15.2.0` | Improved on-screen indicator with new `position` option. `appIsrStatus`, `buildActivity`, and `buildActivityPosition` options have been deprecated. |
| `v15.0.0` | Static on-screen indicator added with `appIsrStatus` option.                                                                                        |

---
title: distDir
description: Set a custom build directory to use instead of the default .next directory.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/distDir"
version: 16.2.6
router: Pages Router
---

# distDir

You can specify a name to use for a custom build directory to use instead of `.next`.

Open `next.config.js` and add the `distDir` config:

```js filename="next.config.js"
module.exports = {
  distDir: 'build',
}
```

Now if you run `next build` Next.js will use `build` instead of the default `.next` folder.

> `distDir` **should not** leave your project directory. For example, `../build` is an **invalid** directory.

---
title: env
description: Learn to add and access environment variables in your Next.js application at build time.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/env"
version: 16.2.6
router: Pages Router
---

# env

> This is a legacy API and no longer recommended. It's still supported for backward compatibility.

> Since the release of [Next.js 9.4](https://nextjs.org/blog/next-9-4) we now have a more intuitive and ergonomic experience for [adding environment variables](/docs/pages/guides/environment-variables). Give it a try!

> **Good to know**: environment variables specified in this way will **always** be included in the JavaScript bundle, prefixing the environment variable name with `NEXT_PUBLIC_` only has an effect when specifying them [through the environment or .env files](/docs/pages/guides/environment-variables).

To add environment variables to the JavaScript bundle, open `next.config.js` and add the `env` config:

```js filename="next.config.js"
module.exports = {
  env: {
    customKey: 'my-value',
  },
}
```

Now you can access `process.env.customKey` in your code. For example:

```jsx
function Page() {
  return The value of customKey is: {process.env.customKey}

}

export default Page
```

Next.js will replace `process.env.customKey` with `'my-value'` at build time. Trying to destructure `process.env` variables won't work due to the nature of webpack [DefinePlugin](https://webpack.js.org/plugins/define-plugin/).

For example, the following line:

```jsx
return The value of customKey is: {process.env.customKey}

```

Will end up being:

```jsx
return The value of customKey is: {'my-value'}

```

---
title: exportPathMap
description: "Customize the pages that will be exported as HTML files when using `next export`."
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/exportPathMap"
version: 16.2.6
router: Pages Router
---

# exportPathMap

> This is a legacy API and no longer recommended. It's still supported for backward compatibility.

> This feature is exclusive to `next export` and currently **deprecated** in favor of `getStaticPaths` with `pages` or `generateStaticParams` with `app`.

`exportPathMap` allows you to specify a mapping of request paths to page destinations, to be used during export. Paths defined in `exportPathMap` will also be available when using [`next dev`](/docs/app/api-reference/cli/next#next-dev-options).

Let's start with an example, to create a custom `exportPathMap` for an app with the following pages:

* `pages/index.js`
* `pages/about.js`
* `pages/post.js`

Open `next.config.js` and add the following `exportPathMap` config:

```js filename="next.config.js"
module.exports = {
  exportPathMap: async function (
    defaultPathMap,
    { dev, dir, outDir, distDir, buildId }
  ) {
    return {
      '/': { page: '/' },
      '/about': { page: '/about' },
      '/p/hello-nextjs': { page: '/post', query: { title: 'hello-nextjs' } },
      '/p/learn-nextjs': { page: '/post', query: { title: 'learn-nextjs' } },
      '/p/deploy-nextjs': { page: '/post', query: { title: 'deploy-nextjs' } },
    }
  },
}
```

> **Good to know**: the `query` field in `exportPathMap` cannot be used with [automatically statically optimized pages](/docs/pages/building-your-application/rendering/automatic-static-optimization) or [`getStaticProps` pages](/docs/pages/building-your-application/data-fetching/get-static-props) as they are rendered to HTML files at build-time and additional query information cannot be provided during `next export`.

The pages will then be exported as HTML files, for example, `/about` will become `/about.html`.

`exportPathMap` is an `async` function that receives 2 arguments: the first one is `defaultPathMap`, which is the default map used by Next.js. The second argument is an object with:

* `dev` - `true` when `exportPathMap` is being called in development. `false` when running `next export`. In development `exportPathMap` is used to define routes.
* `dir` - Absolute path to the project directory
* `outDir` - Absolute path to the `out/` directory ([configurable with `-o`](#customizing-the-output-directory)). When `dev` is `true` the value of `outDir` will be `null`.
* `distDir` - Absolute path to the `.next/` directory (configurable with the [`distDir`](/docs/pages/api-reference/config/next-config-js/distDir) config)
* `buildId` - The generated build id

The returned object is a map of pages where the `key` is the `pathname` and the `value` is an object that accepts the following fields:

* `page`: `String` - the page inside the `pages` directory to render
* `query`: `Object` - the `query` object passed to `getInitialProps` when prerendering. Defaults to `{}`

> The exported `pathname` can also be a filename (for example, `/readme.md`), but you may need to set the `Content-Type` header to `text/html` when serving its content if it is different than `.html`.

## Adding a trailing slash

It is possible to configure Next.js to export pages as `index.html` files and require trailing slashes, `/about` becomes `/about/index.html` and is routable via `/about/`. This was the default behavior prior to Next.js 9.

To switch back and add a trailing slash, open `next.config.js` and enable the `trailingSlash` config:

```js filename="next.config.js"
module.exports = {
  trailingSlash: true,
}
```

## Customizing the output directory

[`next export`](/docs/pages/guides/static-exports) will use `out` as the default output directory, you can customize this using the `-o` argument, like so:

```bash filename="Terminal"
next export -o outdir
```

> **Warning**: Using `exportPathMap` is deprecated and is overridden by `getStaticPaths` inside `pages`. We don't recommend using them together.

---
title: generateBuildId
description: Configure the build id, which is used to identify the current build in which your application is being served.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/generateBuildId"
version: 16.2.6
router: Pages Router
---

# generateBuildId

Next.js generates an ID during `next build` to identify which version of your application is being served. The same build should be used and boot up multiple containers.

If you are rebuilding for each stage of your environment, you will need to generate a consistent build ID to use between containers. Use the `generateBuildId` command in `next.config.js`:

```jsx filename="next.config.js"
module.exports = {
  generateBuildId: async () => {
    // This could be anything, using the latest git hash
    return process.env.GIT_HASH
  },
}
```

---
title: generateEtags
description: Next.js will generate etags for every page by default. Learn more about how to disable etag generation here.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/generateEtags"
version: 16.2.6
router: Pages Router
---

# generateEtags

Next.js will generate [etags](https://en.wikipedia.org/wiki/HTTP_ETag) for every page by default. You may want to disable etag generation for HTML pages depending on your cache strategy.

Open `next.config.js` and disable the `generateEtags` option:

```js filename="next.config.js"
module.exports = {
  generateEtags: false,
}
```

---
title: headers
description: Add custom HTTP headers to your Next.js app.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/headers"
version: 16.2.6
router: Pages Router
---

# headers

Headers allow you to set custom HTTP headers on the response to an incoming request on a given path.

To set custom HTTP headers you can use the `headers` key in `next.config.js`:

```js filename="next.config.js"
module.exports = {
  async headers() {
    return [
      {
        source: '/about',
        headers: [
          {
            key: 'x-custom-header',
            value: 'my custom header value',
          },
          {
            key: 'x-another-custom-header',
            value: 'my other custom header value',
          },
        ],
      },
    ]
  },
}
```

`headers` is an async function that expects an array to be returned holding objects with `source` and `headers` properties:

* `source` is the incoming request path pattern.
* `headers` is an array of response header objects, with `key` and `value` properties.
* `basePath`: `false` or `undefined` - if false the basePath won't be included when matching, can be used for external rewrites only.
* `locale`: `false` or `undefined` - whether the locale should not be included when matching.
* `has` is an array of [has objects](#header-cookie-and-query-matching) with the `type`, `key` and `value` properties.
* `missing` is an array of [missing objects](#header-cookie-and-query-matching) with the `type`, `key` and `value` properties.

Headers are checked before the filesystem which includes pages and `/public` files.

## Header Overriding Behavior

If two headers match the same path and set the same header key, the last header key will override the first. Using the below headers, the path `/hello` will result in the header `x-hello` being `world` due to the last header value set being `world`.

```js filename="next.config.js"
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'x-hello',
            value: 'there',
          },
        ],
      },
      {
        source: '/hello',
        headers: [
          {
            key: 'x-hello',
            value: 'world',
          },
        ],
      },
    ]
  },
}
```

## Path Matching

Path matches are allowed, for example `/blog/:slug` will match `/blog/first-post` (no nested paths):

```js filename="next.config.js"
module.exports = {
  async headers() {
    return [
      {
        source: '/blog/:slug',
        headers: [
          {
            key: 'x-slug',
            value: ':slug', // Matched parameters can be used in the value
          },
          {
            key: 'x-slug-:slug', // Matched parameters can be used in the key
            value: 'my other custom header value',
          },
        ],
      },
    ]
  },
}
```

The pattern `/blog/:slug` matches `/blog/first-post` and `/blog/post-1` but not a nested path like `/blog/a/b`. Patterns are anchored to the start, `/blog/:slug` will not match `/archive/blog/first-post`.

You can use modifiers on parameters: `*` (zero or more), `+` (one or more), `?` (zero or one). For example, `/blog/:slug*` matches `/blog`, `/blog/a`, and `/blog/a/b/c`.

Read more details on [path-to-regexp](https://github.com/pillarjs/path-to-regexp) documentation.

### Wildcard Path Matching

To match a wildcard path you can use `*` after a parameter, for example `/blog/:slug*` will match `/blog/a/b/c/d/hello-world`:

```js filename="next.config.js"
module.exports = {
  async headers() {
    return [
      {
        source: '/blog/:slug*',
        headers: [
          {
            key: 'x-slug',
            value: ':slug*', // Matched parameters can be used in the value
          },
          {
            key: 'x-slug-:slug*', // Matched parameters can be used in the key
            value: 'my other custom header value',
          },
        ],
      },
    ]
  },
}
```

### Regex Path Matching

To match a regex path you can wrap the regex in parenthesis after a parameter, for example `/blog/:slug(\\d{1,})` will match `/blog/123` but not `/blog/abc`:

```js filename="next.config.js"
module.exports = {
  async headers() {
    return [
      {
        source: '/blog/:post(\\d{1,})',
        headers: [
          {
            key: 'x-post',
            value: ':post',
          },
        ],
      },
    ]
  },
}
```

The following characters `(`, `)`, `{`, `}`, `:`, `*`, `+`, `?` are used for regex path matching, so when used in the `source` as non-special values they must be escaped by adding `\\` before them:

```js filename="next.config.js"
module.exports = {
  async headers() {
    return [
      {
        // this will match `/english(default)/something` being requested
        source: '/english\\(default\\)/:slug',
        headers: [
          {
            key: 'x-header',
            value: 'value',
          },
        ],
      },
    ]
  },
}
```

## Header, Cookie, and Query Matching

To only apply a header when header, cookie, or query values also match the `has` field or don't match the `missing` field can be used. Both the `source` and all `has` items must match and all `missing` items must not match for the header to be applied.

`has` and `missing` items can have the following fields:

* `type`: `String` - must be either `header`, `cookie`, `host`, or `query`.
* `key`: `String` - the key from the selected type to match against.
* `value`: `String` or `undefined` - the value to check for, if undefined any value will match. A regex like string can be used to capture a specific part of the value, e.g. if the value `first-(?.*)` is used for `first-second` then `second` will be usable in the destination with `:paramName`.

```js filename="next.config.js"
module.exports = {
  async headers() {
    return [
      // if the header `x-add-header` is present,
      // the `x-another-header` header will be applied
      {
        source: '/:path*',
        has: [
          {
            type: 'header',
            key: 'x-add-header',
          },
        ],
        headers: [
          {
            key: 'x-another-header',
            value: 'hello',
          },
        ],
      },
      // if the header `x-no-header` is not present,
      // the `x-another-header` header will be applied
      {
        source: '/:path*',
        missing: [
          {
            type: 'header',
            key: 'x-no-header',
          },
        ],
        headers: [
          {
            key: 'x-another-header',
            value: 'hello',
          },
        ],
      },
      // if the source, query, and cookie are matched,
      // the `x-authorized` header will be applied
      {
        source: '/specific/:path*',
        has: [
          {
            type: 'query',
            key: 'page',
            // the page value will not be available in the
            // header key/values since value is provided and
            // doesn't use a named capture group e.g. (?home)
            value: 'home',
          },
          {
            type: 'cookie',
            key: 'authorized',
            value: 'true',
          },
        ],
        headers: [
          {
            key: 'x-authorized',
            value: ':authorized',
          },
        ],
      },
      // if the header `x-authorized` is present and
      // contains a matching value, the `x-another-header` will be applied
      {
        source: '/:path*',
        has: [
          {
            type: 'header',
            key: 'x-authorized',
            value: '(?yes|true)',
          },
        ],
        headers: [
          {
            key: 'x-another-header',
            value: ':authorized',
          },
        ],
      },
      // if the host is `example.com`,
      // this header will be applied
      {
        source: '/:path*',
        has: [
          {
            type: 'host',
            value: 'example.com',
          },
        ],
        headers: [
          {
            key: 'x-another-header',
            value: ':authorized',
          },
        ],
      },
    ]
  },
}
```

## Headers with basePath support

When leveraging [`basePath` support](/docs/app/api-reference/config/next-config-js/basePath) with headers each `source` is automatically prefixed with the `basePath` unless you add `basePath: false` to the header:

```js filename="next.config.js"
module.exports = {
  basePath: '/docs',

  async headers() {
    return [
      {
        source: '/with-basePath', // becomes /docs/with-basePath
        headers: [
          {
            key: 'x-hello',
            value: 'world',
          },
        ],
      },
      {
        source: '/without-basePath', // is not modified since basePath: false is set
        headers: [
          {
            key: 'x-hello',
            value: 'world',
          },
        ],
        basePath: false,
      },
    ]
  },
}
```

## Headers with i18n support

When leveraging [`i18n` support](/docs/pages/guides/internationalization) with headers each `source` is automatically prefixed to handle the configured `locales` unless you add `locale: false` to the header. If `locale: false` is used you must prefix the `source` with a locale for it to be matched correctly.

```js filename="next.config.js"
module.exports = {
  i18n: {
    locales: ['en', 'fr', 'de'],
    defaultLocale: 'en',
  },

  async headers() {
    return [
      {
        source: '/with-locale', // automatically handles all locales
        headers: [
          {
            key: 'x-hello',
            value: 'world',
          },
        ],
      },
      {
        // does not handle locales automatically since locale: false is set
        source: '/nl/with-locale-manual',
        locale: false,
        headers: [
          {
            key: 'x-hello',
            value: 'world',
          },
        ],
      },
      {
        // this matches '/' since `en` is the defaultLocale
        source: '/en',
        locale: false,
        headers: [
          {
            key: 'x-hello',
            value: 'world',
          },
        ],
      },
      {
        // this gets converted to /(en|fr|de)/(.*) so will not match the top-level
        // `/` or `/fr` routes like /:path* would
        source: '/(.*)',
        headers: [
          {
            key: 'x-hello',
            value: 'world',
          },
        ],
      },
    ]
  },
}
```

## Cache-Control

Next.js sets the `Cache-Control` header of `public, max-age=31536000, immutable` for truly immutable assets. It cannot be overridden. These immutable files contain a SHA-hash in the file name, so they can be safely cached indefinitely. For example, [Static Image Imports](/docs/app/getting-started/images#local-images). You cannot set `Cache-Control` headers in `next.config.js` for these assets.

However, you can set `Cache-Control` headers for other responses or data.

If you need to revalidate the cache of a page that has been [statically generated](/docs/pages/building-your-application/rendering/static-site-generation), you can do so by setting the `revalidate` prop in the page's [`getStaticProps`](/docs/pages/building-your-application/data-fetching/get-static-props) function.

To cache the response from an [API Route](/docs/pages/building-your-application/routing/api-routes), you can use `res.setHeader`:

```ts filename="pages/api/hello.ts" switcher
import type { NextApiRequest, NextApiResponse } from 'next'

type ResponseData = {
  message: string
}

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  res.setHeader('Cache-Control', 's-maxage=86400')
  res.status(200).json({ message: 'Hello from Next.js!' })
}
```

```js filename="pages/api/hello.js" switcher
export default function handler(req, res) {
  res.setHeader('Cache-Control', 's-maxage=86400')
  res.status(200).json({ message: 'Hello from Next.js!' })
}
```

You can also use caching headers (`Cache-Control`) inside `getServerSideProps` to cache dynamic responses. For example, using [`stale-while-revalidate`](https://web.dev/stale-while-revalidate/).

```ts filename="pages/index.tsx" switcher
import { GetStaticProps, GetStaticPaths, GetServerSideProps } from 'next'

// This value is considered fresh for ten seconds (s-maxage=10).
// If a request is repeated within the next 10 seconds, the previously
// cached value will still be fresh. If the request is repeated before 59 seconds,
// the cached value will be stale but still render (stale-while-revalidate=59).
//
// In the background, a revalidation request will be made to populate the cache
// with a fresh value. If you refresh the page, you will see the new value.
export const getServerSideProps = (async (context) => {
  context.res.setHeader(
    'Cache-Control',
    'public, s-maxage=10, stale-while-revalidate=59'
  )

  return {
    props: {},
  }
}) satisfies GetServerSideProps
```

```js filename="pages/index.js" switcher
// This value is considered fresh for ten seconds (s-maxage=10).
// If a request is repeated within the next 10 seconds, the previously
// cached value will still be fresh. If the request is repeated before 59 seconds,
// the cached value will be stale but still render (stale-while-revalidate=59).
//
// In the background, a revalidation request will be made to populate the cache
// with a fresh value. If you refresh the page, you will see the new value.
export async function getServerSideProps({ req, res }) {
  res.setHeader(
    'Cache-Control',
    'public, s-maxage=10, stale-while-revalidate=59'
  )

  return {
    props: {},
  }
}
```

## Options

### CORS

[Cross-Origin Resource Sharing (CORS)](https://developer.mozilla.org/docs/Web/HTTP/CORS) is a security feature that allows you to control which sites can access your resources. You can set the `Access-Control-Allow-Origin` header to allow a specific origin to access your API Endpoints.

```js
async headers() {
    return [
      {
        source: "/api/:path*",
        headers: [
          {
            key: "Access-Control-Allow-Origin",
            value: "*", // Set your origin
          },
          {
            key: "Access-Control-Allow-Methods",
            value: "GET, POST, PUT, DELETE, OPTIONS",
          },
          {
            key: "Access-Control-Allow-Headers",
            value: "Content-Type, Authorization",
          },
        ],
      },
    ];
  },
```

### X-DNS-Prefetch-Control

[This header](https://developer.mozilla.org/docs/Web/HTTP/Headers/X-DNS-Prefetch-Control) controls DNS prefetching, allowing browsers to proactively perform domain name resolution on external links, images, CSS, JavaScript, and more. This prefetching is performed in the background, so the [DNS](https://developer.mozilla.org/docs/Glossary/DNS) is more likely to be resolved by the time the referenced items are needed. This reduces latency when the user clicks a link.

```js
{
  key: 'X-DNS-Prefetch-Control',
  value: 'on'
}
```

### Strict-Transport-Security

[This header](https://developer.mozilla.org/docs/Web/HTTP/Headers/Strict-Transport-Security) informs browsers it should only be accessed using HTTPS, instead of using HTTP. Using the configuration below, all present and future subdomains will use HTTPS for a `max-age` of 2 years. This blocks access to pages or subdomains that can only be served over HTTP.

```js
{
  key: 'Strict-Transport-Security',
  value: 'max-age=63072000; includeSubDomains; preload'
}
```

### X-Frame-Options

[This header](https://developer.mozilla.org/docs/Web/HTTP/Headers/X-Frame-Options) indicates whether the site should be allowed to be displayed within an `iframe`. This can prevent against clickjacking attacks.

**This header has been superseded by CSP's `frame-ancestors` option**, which has better support in modern browsers (see [Content Security Policy](/docs/app/guides/content-security-policy) for configuration details).

```js
{
  key: 'X-Frame-Options',
  value: 'SAMEORIGIN'
}
```

### Permissions-Policy

[This header](https://developer.mozilla.org/docs/Web/HTTP/Headers/Permissions-Policy) allows you to control which features and APIs can be used in the browser. It was previously named `Feature-Policy`.

```js
{
  key: 'Permissions-Policy',
  value: 'camera=(), microphone=(), geolocation=(), browsing-topics=()'
}
```

### X-Content-Type-Options

[This header](https://developer.mozilla.org/docs/Web/HTTP/Headers/X-Content-Type-Options) prevents the browser from attempting to guess the type of content if the `Content-Type` header is not explicitly set. This can prevent XSS exploits for websites that allow users to upload and share files.

For example, a user trying to download an image, but having it treated as a different `Content-Type` like an executable, which could be malicious. This header also applies to downloading browser extensions. The only valid value for this header is `nosniff`.

```js
{
  key: 'X-Content-Type-Options',
  value: 'nosniff'
}
```

### Referrer-Policy

[This header](https://developer.mozilla.org/docs/Web/HTTP/Headers/Referrer-Policy) controls how much information the browser includes when navigating from the current website (origin) to another.

```js
{
  key: 'Referrer-Policy',
  value: 'origin-when-cross-origin'
}
```

### Content-Security-Policy

Learn more about adding a [Content Security Policy](/docs/app/guides/content-security-policy) to your application.

## Version History

| Version   | Changes          |
| --------- | ---------------- |
| `v13.3.0` | `missing` added. |
| `v10.2.0` | `has` added.     |
| `v9.5.0`  | Headers added.   |

---
title: httpAgentOptions
description: Next.js will automatically use HTTP Keep-Alive by default. Learn more about how to disable HTTP Keep-Alive here.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/httpAgentOptions"
version: 16.2.6
router: Pages Router
---

# httpAgentOptions

In Node.js versions prior to 18, Next.js automatically polyfills `fetch()` with [undici](/docs/architecture/supported-browsers#polyfills) and enables [HTTP Keep-Alive](https://developer.mozilla.org/docs/Web/HTTP/Headers/Keep-Alive) by default.

To disable HTTP Keep-Alive for all `fetch()` calls on the server-side, open `next.config.js` and add the `httpAgentOptions` config:

```js filename="next.config.js"
module.exports = {
  httpAgentOptions: {
    keepAlive: false,
  },
}
```

---
title: images
description: Custom configuration for the next/image loader
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/images"
version: 16.2.6
router: Pages Router
---

# images

If you want to use a cloud provider to optimize images instead of using the Next.js built-in Image Optimization API, you can configure `next.config.js` with the following:

```js filename="next.config.js"
module.exports = {
  images: {
    loader: 'custom',
    loaderFile: './my/image/loader.js',
  },
}
```

This `loaderFile` must point to a file relative to the root of your Next.js application. The file must export a default function that returns a string, for example:

```js filename="my/image/loader.js"
export default function myImageLoader({ src, width, quality }) {
  return `https://example.com/${src}?w=${width}&q=${quality || 75}`
}
```

Alternatively, you can use the [`loader` prop](/docs/pages/api-reference/components/image#loader) to pass the function to each instance of `next/image`.

To learn more about configuring the behavior of the built-in [Image Optimization API](/docs/pages/api-reference/components/image) and the [Image Component](/docs/pages/api-reference/components/image), see [Image Configuration Options](/docs/pages/api-reference/components/image#configuration-options) for available options.

## Example Loader Configuration

* [Akamai](#akamai)
* [AWS CloudFront](#aws-cloudfront)
* [Cloudinary](#cloudinary)
* [Cloudflare](#cloudflare)
* [Contentful](#contentful)
* [Fastly](#fastly)
* [Gumlet](#gumlet)
* [ImageEngine](#imageengine)
* [Imgix](#imgix)
* [PixelBin](#pixelbin)
* [Sanity](#sanity)
* [Sirv](#sirv)
* [Supabase](#supabase)
* [Thumbor](#thumbor)
* [Imagekit](#imagekitio)
* [Nitrogen AIO](#nitrogen-aio)

### Akamai

```js
// Docs: https://techdocs.akamai.com/ivm/reference/test-images-on-demand
export default function akamaiLoader({ src, width, quality }) {
  return `https://example.com/${src}?imwidth=${width}`
}
```

### AWS CloudFront

```js
// Docs: https://aws.amazon.com/developer/application-security-performance/articles/image-optimization
export default function cloudfrontLoader({ src, width, quality }) {
  const url = new URL(`https://example.com${src}`)
  url.searchParams.set('format', 'auto')
  url.searchParams.set('width', width.toString())
  url.searchParams.set('quality', (quality || 75).toString())
  return url.href
}
```

### Cloudinary

```js
// Demo: https://res.cloudinary.com/demo/image/upload/w_300,c_limit,q_auto/turtles.jpg
export default function cloudinaryLoader({ src, width, quality }) {
  const params = ['f_auto', 'c_limit', `w_${width}`, `q_${quality || 'auto'}`]
  return `https://example.com/${params.join(',')}${src}`
}
```

### Cloudflare

```js
// Docs: https://developers.cloudflare.com/images/transform-images
export default function cloudflareLoader({ src, width, quality }) {
  const params = [`width=${width}`, `quality=${quality || 75}`, 'format=auto']
  return `https://example.com/cdn-cgi/image/${params.join(',')}/${src}`
}
```

### Contentful

```js
// Docs: https://www.contentful.com/developers/docs/references/images-api/
export default function contentfulLoader({ src, width, quality }) {
  const url = new URL(`https://example.com${src}`)
  url.searchParams.set('fm', 'webp')
  url.searchParams.set('w', width.toString())
  url.searchParams.set('q', (quality || 75).toString())
  return url.href
}
```

### Fastly

```js
// Docs: https://developer.fastly.com/reference/io/
export default function fastlyLoader({ src, width, quality }) {
  const url = new URL(`https://example.com${src}`)
  url.searchParams.set('auto', 'webp')
  url.searchParams.set('width', width.toString())
  url.searchParams.set('quality', (quality || 75).toString())
  return url.href
}
```

### Gumlet

```js
// Docs: https://docs.gumlet.com/reference/image-transform-size
export default function gumletLoader({ src, width, quality }) {
  const url = new URL(`https://example.com${src}`)
  url.searchParams.set('format', 'auto')
  url.searchParams.set('w', width.toString())
  url.searchParams.set('q', (quality || 75).toString())
  return url.href
}
```

### ImageEngine

```js
// Docs: https://support.imageengine.io/hc/en-us/articles/360058880672-Directives
export default function imageengineLoader({ src, width, quality }) {
  const compression = 100 - (quality || 50)
  const params = [`w_${width}`, `cmpr_${compression}`)]
  return `https://example.com${src}?imgeng=/${params.join('/')`
}
```

### Imgix

```js
// Demo: https://static.imgix.net/daisy.png?format=auto&fit=max&w=300
export default function imgixLoader({ src, width, quality }) {
  const url = new URL(`https://example.com${src}`)
  const params = url.searchParams
  params.set('auto', params.getAll('auto').join(',') || 'format')
  params.set('fit', params.get('fit') || 'max')
  params.set('w', params.get('w') || width.toString())
  params.set('q', (quality || 50).toString())
  return url.href
}
```

### PixelBin

```js
// Doc (Resize): https://www.pixelbin.io/docs/transformations/basic/resize/#width-w
// Doc (Optimise): https://www.pixelbin.io/docs/optimizations/quality/#image-quality-when-delivering
// Doc (Auto Format Delivery): https://www.pixelbin.io/docs/optimizations/format/#automatic-format-selection-with-f_auto-url-parameter
export default function pixelBinLoader({ src, width, quality }) {
  const name = ''
  const opt = `t.resize(w:${width})~t.compress(q:${quality || 75})`
  return `https://cdn.pixelbin.io/v2/${name}/${opt}/${src}?f_auto=true`
}
```

### Sanity

```js
// Docs: https://www.sanity.io/docs/image-urls
export default function sanityLoader({ src, width, quality }) {
  const prj = 'zp7mbokg'
  const dataset = 'production'
  const url = new URL(`https://cdn.sanity.io/images/${prj}/${dataset}${src}`)
  url.searchParams.set('auto', 'format')
  url.searchParams.set('fit', 'max')
  url.searchParams.set('w', width.toString())
  if (quality) {
    url.searchParams.set('q', quality.toString())
  }
  return url.href
}
```

### Sirv

```js
// Docs: https://sirv.com/help/articles/dynamic-imaging/
export default function sirvLoader({ src, width, quality }) {
  const url = new URL(`https://example.com${src}`)
  const params = url.searchParams
  params.set('format', params.getAll('format').join(',') || 'optimal')
  params.set('w', params.get('w') || width.toString())
  params.set('q', (quality || 85).toString())
  return url.href
}
```

### Supabase

```js
// Docs: https://supabase.com/docs/guides/storage/image-transformations#nextjs-loader
export default function supabaseLoader({ src, width, quality }) {
  const url = new URL(`https://example.com${src}`)
  url.searchParams.set('width', width.toString())
  url.searchParams.set('quality', (quality || 75).toString())
  return url.href
}
```

### Thumbor

```js
// Docs: https://thumbor.readthedocs.io/en/latest/
export default function thumborLoader({ src, width, quality }) {
  const params = [`${width}x0`, `filters:quality(${quality || 75})`]
  return `https://example.com${params.join('/')}${src}`
}
```

### ImageKit.io

```js
// Docs: https://imagekit.io/docs/image-transformation
export default function imageKitLoader({ src, width, quality }) {
  const params = [`w-${width}`, `q-${quality || 80}`]
  return `https://ik.imagekit.io/your_imagekit_id/${src}?tr=${params.join(',')}`
}
```

### Nitrogen AIO

```js
// Docs: https://docs.n7.io/aio/intergrations/
export default function aioLoader({ src, width, quality }) {
  const url = new URL(src, window.location.href)
  const params = url.searchParams
  const aioParams = params.getAll('aio')
  aioParams.push(`w-${width}`)
  if (quality) {
    aioParams.push(`q-${quality.toString()}`)
  }
  params.set('aio', aioParams.join(';'))
  return url.href
}
```

---
title: logging
description: Configure logging behavior in the terminal when running Next.js in development mode.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/logging"
version: 16.2.6
router: Pages Router
---

# logging

## Options

### Incoming Requests

By default all the incoming requests will be logged in the console during development. You can use the `incomingRequests` option to decide which requests to ignore.
Since this is only logged in development, this option doesn't affect production builds.

```js filename="next.config.js"
module.exports = {
  logging: {
    incomingRequests: {
      ignore: [/\api\/v1\/health/],
    },
  },
}
```

Or you can disable incoming request logging by setting `incomingRequests` to `false`.

```js filename="next.config.js"
module.exports = {
  logging: {
    incomingRequests: false,
  },
}
```

### Browser Console Logs

You can forward browser console logs (such as `console.log`, `console.warn`, `console.error`) to the terminal during development. This is useful for debugging client-side code without needing to check the browser's developer tools.

```js filename="next.config.js"
module.exports = {
  logging: {
    browserToTerminal: true,
  },
}
```

#### Options

The `browserToTerminal` option accepts the following values:

| Value     | Description                                         |
| --------- | --------------------------------------------------- |
| `'warn'`  | Forward only warnings and errors, by default        |
| `'error'` | Forward only errors                                 |
| `true`    | Forward all console output (log, info, warn, error) |
| `false`   | Disable browser log forwarding                      |

```js filename="next.config.js"
module.exports = {
  logging: {
    browserToTerminal: 'warn',
  },
}
```

#### Source Location

When enabled, browser logs include source location information (file path and line number) by default. For example:

```tsx filename="pages/index.tsx" highlight={6}
export default function Home() {
  return (
     {
        console.log('Hello World')
      }}
    >
      Click me

  )
}
```

Clicking the button prints this message to the terminal:

```bash filename="Terminal"
[browser] Hello World (pages/index.tsx:6:17)
```

### Disabling Logging

In addition, you can disable the development logging by setting `logging` to `false`.

```js filename="next.config.js"
module.exports = {
  logging: false,
}
```

## Version History

| Version   | Changes                                                                          |
| --------- | -------------------------------------------------------------------------------- |
| `v16.2.0` | `browserToTerminal` added (moved from `experimental.browserDebugInfoInTerminal`) |
| `v15.4.0` | `experimental.browserDebugInfoInTerminal` introduced                             |
| `v15.2.0` | `incomingRequests` added                                                         |
| `v15.0.0` | `logging: false` option added, `fetches.hmrRefreshes` added for App Router       |
| `v14.0.0` | `logging.fetches` moved to stable for App Router                                 |

---
title: onDemandEntries
description: Configure how Next.js will dispose and keep in memory pages created in development.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/onDemandEntries"
version: 16.2.6
router: Pages Router
---

# onDemandEntries

Next.js exposes some options that give you some control over how the server will dispose or keep in memory built pages in development.

To change the defaults, open `next.config.js` and add the `onDemandEntries` config:

```js filename="next.config.js"
module.exports = {
  onDemandEntries: {
    // period (in ms) where the server will keep pages in the buffer
    maxInactiveAge: 25 * 1000,
    // number of pages that should be kept simultaneously without being disposed
    pagesBufferLength: 2,
  },
}
```

---
title: optimizePackageImports
description: API Reference for optimizePackageImports Next.js Config Option
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/optimizePackageImports"
version: 16.2.6
router: Pages Router
---

# optimizePackageImports

> This feature is currently experimental and subject to change, it's not recommended for production. Try it out and share your feedback on [GitHub](https://github.com/vercel/next.js/issues).

Some packages can export hundreds or thousands of modules, which can cause performance issues in development and production.

Adding a package to `experimental.optimizePackageImports` will only load the modules you are actually using, while still giving you the convenience of writing import statements with many named exports.

```js filename="next.config.js"
module.exports = {
  experimental: {
    optimizePackageImports: ['package-name'],
  },
}
```

The following libraries are optimized by default:

* `lucide-react`
* `date-fns`
* `lodash-es`
* `ramda`
* `antd`
* `react-bootstrap`
* `ahooks`
* `@ant-design/icons`
* `@headlessui/react`
* `@headlessui-float/react`
* `@heroicons/react/20/solid`
* `@heroicons/react/24/solid`
* `@heroicons/react/24/outline`
* `@visx/visx`
* `@tremor/react`
* `rxjs`
* `@mui/material`
* `@mui/icons-material`
* `recharts`
* `react-use`
* `@material-ui/core`
* `@material-ui/icons`
* `@tabler/icons-react`
* `mui-core`
* `react-icons/*`
* `effect`
* `@effect/*`

---
title: output
description: Next.js automatically traces which files are needed by each page to allow for easy deployment of your application. Learn how it works here.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/output"
version: 16.2.6
router: Pages Router
---

# output

During a build, Next.js will automatically trace each page and its dependencies to determine all of the files that are needed for deploying a production version of your application.

This feature helps reduce the size of deployments drastically. Previously, when deploying with Docker you would need to have all files from your package's `dependencies` installed to run `next start`. Starting with Next.js 12, you can leverage Output File Tracing in the `.next/` directory to only include the necessary files.

Furthermore, this removes the need for the deprecated `serverless` target which can cause various issues and also creates unnecessary duplication.

## How it Works

During `next build`, Next.js will use [`@vercel/nft`](https://github.com/vercel/nft) to statically analyze `import`, `require`, and `fs` usage to determine all files that a page might load.

Next.js' production server is also traced for its needed files and output at `.next/next-server.js.nft.json` which can be leveraged in production.

To leverage the `.nft.json` files emitted to the `.next` output directory, you can read the list of files in each trace that are relative to the `.nft.json` file and then copy them to your deployment location.

## Automatically Copying Traced Files

Next.js can automatically create a `standalone` folder that copies only the necessary files for a production deployment including select files in `node_modules`.

To leverage this automatic copying you can enable it in your `next.config.js`:

```js filename="next.config.js"
module.exports = {
  output: 'standalone',
}
```

This will create a folder at `.next/standalone` which can then be deployed on its own without installing `node_modules`.

Additionally, a minimal `server.js` file is also output which can be used instead of `next start`. This minimal server does not copy the `public` or `.next/static` folders by default as these should ideally be handled by a CDN instead, although these folders can be copied to the `standalone/public` and `standalone/.next/static` folders manually, after which `server.js` file will serve these automatically.

To copy these manually, you can use the `cp` command-line tool after you `next build`:

```bash filename="Terminal"
cp -r public .next/standalone/ && cp -r .next/static .next/standalone/.next/
```

To start your minimal `server.js` file locally, run the following command:

```bash filename="Terminal"
node .next/standalone/server.js
```

> **Good to know**:
>
> * `next.config.js` is read during `next build` and serialized into the `server.js` output file.
> * If your project needs to listen to a specific port or hostname, you can define `PORT` or `HOSTNAME` environment variables before running `server.js`. For example, run `PORT=8080 HOSTNAME=0.0.0.0 node server.js` to start the server on `http://0.0.0.0:8080`.

## Caveats

* While tracing in monorepo setups, the project directory is used for tracing by default. For `next build packages/web-app`, `packages/web-app` would be the tracing root and any files outside of that folder will not be included. To include files outside of this folder you can set `outputFileTracingRoot` in your `next.config.js`.

```js filename="packages/web-app/next.config.js"
const path = require('path')

module.exports = {
  // this includes files from the monorepo base two directories up
  outputFileTracingRoot: path.join(__dirname, '../../'),
}
```

* There are some cases in which Next.js might fail to include required files, or might incorrectly include unused files. In those cases, you can leverage `outputFileTracingExcludes` and `outputFileTracingIncludes` respectively in `next.config.js`. Each option accepts an object whose keys are **route globs** (matched with [picomatch](https://www.npmjs.com/package/picomatch#basic-globbing) against the route path, e.g. `/api/hello`) and whose values are **glob patterns resolved from the project root** that specify files to include or exclude in the trace.

> **Good to know**:
> In a monorepo, `project root` refers to the Next.js project root (the folder containing next.config.js, e.g., packages/web-app), not necessarily the monorepo root.

```js filename="next.config.js"
module.exports = {
  outputFileTracingExcludes: {
    '/api/hello': ['./un-necessary-folder/**/*'],
  },
  outputFileTracingIncludes: {
    '/api/another': ['./necessary-folder/**/*'],
    '/api/login/\\[\\[\\.\\.\\.slug\\]\\]': [
      './node_modules/aws-crt/dist/bin/**/*',
    ],
  },
}
```

Using a `src/` directory does not change how you write these options:

* **Keys** still match the route path (`'/api/hello'`, `'/products/[id]'`, etc.).
* **Values** can reference paths under `src/` since they are resolved relative to the project root.

```js filename="next.config.js"
module.exports = {
  outputFileTracingIncludes: {
    '/products/*': ['src/lib/payments/**/*'],
    '/*': ['src/config/runtime/**/*.json'],
  },
  outputFileTracingExcludes: {
    '/api/*': ['src/temp/**/*', 'public/large-logs/**/*'],
  },
}
```

You can also target all routes using a global key like `'/*'`:

```js filename="next.config.js"
module.exports = {
  outputFileTracingIncludes: {
    '/*': ['src/i18n/locales/**/*.json'],
  },
}
```

These options are applied to server traces and do not affect routes that do not produce a server trace file:

* Edge Runtime routes are not affected.
* Fully static pages are not affected.

In monorepos or when you need to include files outside the app folder, combine `outputFileTracingRoot` with includes:

```js filename="next.config.js"
const path = require('path')

module.exports = {
  // Trace from the monorepo root
  outputFileTracingRoot: path.join(__dirname, '../../'),
  outputFileTracingIncludes: {
    '/route1': ['../shared/assets/**/*'],
  },
}
```

> **Good to know**:
>
> * Prefer forward slashes (`/`) in patterns for cross-platform compatibility.
> * Keep patterns as narrow as possible to avoid oversized traces (avoid `**/*` at the repo root).

Common include patterns for native/runtime assets:

```js filename="next.config.js"
module.exports = {
  outputFileTracingIncludes: {
    '/*': ['node_modules/sharp/**/*', 'node_modules/aws-crt/dist/bin/**/*'],
  },
}
```

---
title: pageExtensions
description: Extend the default page extensions used by Next.js when resolving pages in the Pages Router.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/pageExtensions"
version: 16.2.6
router: Pages Router
---

# pageExtensions

You can extend the default Page extensions (`.tsx`, `.ts`, `.jsx`, `.js`) used by Next.js. Inside `next.config.js`, add the `pageExtensions` config:

```js filename="next.config.js"
module.exports = {
  pageExtensions: ['mdx', 'md', 'jsx', 'js', 'tsx', 'ts'],
}
```

Changing these values affects *all* Next.js pages, including the following:

* [`proxy.js`](/docs/pages/api-reference/file-conventions/proxy)
* [`instrumentation.js`](/docs/pages/guides/instrumentation)
* `pages/_document.js`
* `pages/_app.js`
* `pages/api/`

For example, if you reconfigure `.ts` page extensions to `.page.ts`, you would need to rename pages like `proxy.page.ts`, `instrumentation.page.ts`, `_app.page.ts`.

## Including non-page files in the `pages` directory

You can colocate test files or other files used by components in the `pages` directory. Inside `next.config.js`, add the `pageExtensions` config:

```js filename="next.config.js"
module.exports = {
  pageExtensions: ['page.tsx', 'page.ts', 'page.jsx', 'page.js'],
}
```

Then, rename your pages to have a file extension that includes `.page` (e.g. rename `MyPage.tsx` to `MyPage.page.tsx`). Ensure you rename *all* Next.js pages, including the files mentioned above.

---
title: poweredByHeader
description: "Next.js will add the `x-powered-by` header by default. Learn to opt-out of it here."
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/poweredByHeader"
version: 16.2.6
router: Pages Router
---

# poweredByHeader

By default Next.js will add the `x-powered-by` header. To opt-out of it, open `next.config.js` and disable the `poweredByHeader` config:

```js filename="next.config.js"
module.exports = {
  poweredByHeader: false,
}
```

---
title: productionBrowserSourceMaps
description: Enables browser source map generation during the production build.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/productionBrowserSourceMaps"
version: 16.2.6
router: Pages Router
---

# productionBrowserSourceMaps

Source Maps are enabled by default during development. During production builds, they are disabled to prevent you leaking your source on the client, unless you specifically opt-in with the configuration flag.

Next.js provides a configuration flag you can use to enable browser source map generation during the production build:

```js filename="next.config.js"
module.exports = {
  productionBrowserSourceMaps: true,
}
```

When the `productionBrowserSourceMaps` option is enabled, the source maps will be output in the same directory as the JavaScript files. Next.js will automatically serve these files when requested.

* Adding source maps can increase `next build` time
* Increases memory usage during `next build`

---
title: experimental.proxyClientMaxBodySize
description: Configure the maximum request body size when using proxy.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/proxyClientMaxBodySize"
version: 16.2.6
router: Pages Router
---

# experimental.proxyClientMaxBodySize

> This feature is currently experimental and subject to change, it's not recommended for production. Try it out and share your feedback on [GitHub](https://github.com/vercel/next.js/issues).

When proxy is used, Next.js automatically clones the request body and buffers it in memory to enable multiple reads - both in proxy and the underlying route handler. To prevent excessive memory usage, this configuration option sets a size limit on the buffered body.

By default, the maximum body size is **10MB**. If a request body exceeds this limit, the body will only be buffered up to the limit, and a warning will be logged indicating which route exceeded the limit.

## Options

### String format (recommended)

Specify the size using a human-readable string format:

```ts filename="next.config.ts" switcher
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: {
    proxyClientMaxBodySize: '1mb',
  },
}

export default nextConfig
```

```js filename="next.config.js" switcher
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    proxyClientMaxBodySize: '1mb',
  },
}

module.exports = nextConfig
```

Supported units: `b`, `kb`, `mb`, `gb`

### Number format

Alternatively, specify the size in bytes as a number:

```ts filename="next.config.ts" switcher
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: {
    proxyClientMaxBodySize: 1048576, // 1MB in bytes
  },
}

export default nextConfig
```

```js filename="next.config.js" switcher
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    proxyClientMaxBodySize: 1048576, // 1MB in bytes
  },
}

module.exports = nextConfig
```

## Behavior

When a request body exceeds the configured limit:

1. Next.js will buffer only the first N bytes (up to the limit)
2. A warning will be logged to the console indicating the route that exceeded the limit
3. The request will continue processing normally, but only the partial body will be available
4. The request will **not** fail or return an error to the client

If your application needs to process the full request body, you should either:

* Increase the `proxyClientMaxBodySize` limit
* Handle the partial body gracefully in your application logic

## Example

```ts filename="proxy.ts"
import { NextRequest, NextResponse } from 'next/server'

export async function proxy(request: NextRequest) {
  // Next.js automatically buffers the body with the configured size limit
  // You can read the body in proxy...
  const body = await request.text()

  // If the body exceeded the limit, only partial data will be available
  console.log('Body size:', body.length)

  return NextResponse.next()
}
```

```ts filename="app/api/upload/route.ts"
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  // ...and the body is still available in your route handler
  const body = await request.text()

  console.log('Body in route handler:', body.length)

  return NextResponse.json({ received: body.length })
}
```

## Good to know

* This setting only applies when proxy is used in your application
* The default limit of 10MB is designed to balance memory usage and typical use cases
* The limit applies per-request, not globally across all concurrent requests
* For applications handling large file uploads, consider increasing the limit accordingly

---
title: reactStrictMode
description: The complete Next.js runtime is now Strict Mode-compliant, learn how to opt-in
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/reactStrictMode"
version: 16.2.6
router: Pages Router
---

# reactStrictMode

> **Good to know**: Since Next.js 13.5.1, Strict Mode is `true` by default with `app` router, so the above configuration is only necessary for `pages`. You can still disable Strict Mode by setting `reactStrictMode: false`.

> **Suggested**: We strongly suggest you enable Strict Mode in your Next.js application to better prepare your application for the future of React.

React's [Strict Mode](https://react.dev/reference/react/StrictMode) is a development mode only feature for highlighting potential problems in an application. It helps to identify unsafe lifecycles, legacy API usage, and a number of other features.

The Next.js runtime is Strict Mode-compliant. To opt-in to Strict Mode, configure the following option in your `next.config.js`:

```js filename="next.config.js"
module.exports = {
  reactStrictMode: true,
}
```

If you or your team are not ready to use Strict Mode in your entire application, that's OK! You can incrementally migrate on a page-by-page basis using ``.

---
title: redirects
description: Add redirects to your Next.js app.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/redirects"
version: 16.2.6
router: Pages Router
---

# redirects

Redirects allow you to redirect an incoming request path to a different destination path.

To use redirects you can use the `redirects` key in `next.config.js`:

```js filename="next.config.js"
module.exports = {
  async redirects() {
    return [
      {
        source: '/about',
        destination: '/',
        permanent: true,
      },
    ]
  },
}
```

`redirects` is an async function that expects an array to be returned holding objects with `source`, `destination`, and `permanent` properties:

* `source` is the incoming request path pattern.
* `destination` is the path you want to route to.
* `permanent` `true` or `false` - if `true` will use the 308 status code which instructs clients/search engines to cache the redirect forever, if `false` will use the 307 status code which is temporary and is not cached.

> **Why does Next.js use 307 and 308?** Traditionally a 302 was used for a temporary redirect, and a 301 for a permanent redirect, but many browsers changed the request method of the redirect to `GET`, regardless of the original method. For example, if the browser made a request to `POST /v1/users` which returned status code `302` with location `/v2/users`, the subsequent request might be `GET /v2/users` instead of the expected `POST /v2/users`. Next.js uses the 307 temporary redirect, and 308 permanent redirect status codes to explicitly preserve the request method used.

* `basePath`: `false` or `undefined` - if false the `basePath` won't be included when matching, can be used for external redirects only.
* `locale`: `false` or `undefined` - whether the locale should not be included when matching.
* `has` is an array of [has objects](#header-cookie-and-query-matching) with the `type`, `key` and `value` properties.
* `missing` is an array of [missing objects](#header-cookie-and-query-matching) with the `type`, `key` and `value` properties.

Redirects are checked before the filesystem which includes pages and `/public` files.

When using the Pages Router, redirects are not applied to client-side routing (`Link`, `router.push`) unless [Proxy](/docs/app/api-reference/file-conventions/proxy) is present and matches the path.

When a redirect is applied, any query values provided in the request will be passed through to the redirect destination. For example, see the following redirect configuration:

```js
{
  source: '/old-blog/:path*',
  destination: '/blog/:path*',
  permanent: false
}
```

> **Good to know**: Remember to include the forward slash `/` before the colon `:` in path parameters of the `source` and `destination` paths, otherwise the path will be treated as a literal string and you run the risk of causing infinite redirects.

When `/old-blog/post-1?hello=world` is requested, the client will be redirected to `/blog/post-1?hello=world`.

## Path Matching

Path matches are allowed, for example `/old-blog/:slug` will match `/old-blog/first-post` (no nested paths):

```js filename="next.config.js"
module.exports = {
  async redirects() {
    return [
      {
        source: '/old-blog/:slug',
        destination: '/news/:slug', // Matched parameters can be used in the destination
        permanent: true,
      },
    ]
  },
}
```

The pattern `/old-blog/:slug` matches `/old-blog/first-post` and `/old-blog/post-1` but not `/old-blog/a/b` (no nested paths). Patterns are anchored to the start: `/old-blog/:slug` will not match `/archive/old-blog/first-post`.

You can use modifiers on parameters: `*` (zero or more), `+` (one or more), `?` (zero or one). For example, `/blog/:slug*` matches `/blog`, `/blog/a`, and `/blog/a/b/c`.

Read more details on [path-to-regexp](https://github.com/pillarjs/path-to-regexp) documentation.

### Wildcard Path Matching

To match a wildcard path you can use `*` after a parameter, for example `/blog/:slug*` will match `/blog/a/b/c/d/hello-world`:

```js filename="next.config.js"
module.exports = {
  async redirects() {
    return [
      {
        source: '/blog/:slug*',
        destination: '/news/:slug*', // Matched parameters can be used in the destination
        permanent: true,
      },
    ]
  },
}
```

### Regex Path Matching

To match a regex path you can wrap the regex in parentheses after a parameter, for example `/post/:slug(\\d{1,})` will match `/post/123` but not `/post/abc`:

```js filename="next.config.js"
module.exports = {
  async redirects() {
    return [
      {
        source: '/post/:slug(\\d{1,})',
        destination: '/news/:slug', // Matched parameters can be used in the destination
        permanent: false,
      },
    ]
  },
}
```

The following characters `(`, `)`, `{`, `}`, `:`, `*`, `+`, `?` are used for regex path matching, so when used in the `source` as non-special values they must be escaped by adding `\\` before them:

```js filename="next.config.js"
module.exports = {
  async redirects() {
    return [
      {
        // this will match `/english(default)/something` being requested
        source: '/english\\(default\\)/:slug',
        destination: '/en-us/:slug',
        permanent: false,
      },
    ]
  },
}
```

## Header, Cookie, and Query Matching

To only match a redirect when header, cookie, or query values also match the `has` field or don't match the `missing` field can be used. Both the `source` and all `has` items must match and all `missing` items must not match for the redirect to be applied.

`has` and `missing` items can have the following fields:

* `type`: `String` - must be either `header`, `cookie`, `host`, or `query`.
* `key`: `String` - the key from the selected type to match against.
* `value`: `String` or `undefined` - the value to check for, if undefined any value will match. A regex like string can be used to capture a specific part of the value, e.g. if the value `first-(?.*)` is used for `first-second` then `second` will be usable in the destination with `:paramName`.

```js filename="next.config.js"
module.exports = {
  async redirects() {
    return [
      // if the header `x-redirect-me` is present,
      // this redirect will be applied
      {
        source: '/:path((?!another-page$).*)',
        has: [
          {
            type: 'header',
            key: 'x-redirect-me',
          },
        ],
        permanent: false,
        destination: '/another-page',
      },
      // if the header `x-do-not-redirect` is present,
      // this redirect will NOT be applied
      {
        source: '/:path((?!another-page$).*)',
        missing: [
          {
            type: 'header',
            key: 'x-do-not-redirect',
          },
        ],
        permanent: false,
        destination: '/another-page',
      },
      // if the source, query, and cookie are matched,
      // this redirect will be applied
      {
        source: '/specific/:path*',
        has: [
          {
            type: 'query',
            key: 'page',
            // the page value will not be available in the
            // destination since value is provided and doesn't
            // use a named capture group e.g. (?home)
            value: 'home',
          },
          {
            type: 'cookie',
            key: 'authorized',
            value: 'true',
          },
        ],
        permanent: false,
        destination: '/another/:path*',
      },
      // if the header `x-authorized` is present and
      // contains a matching value, this redirect will be applied
      {
        source: '/',
        has: [
          {
            type: 'header',
            key: 'x-authorized',
            value: '(?yes|true)',
          },
        ],
        permanent: false,
        destination: '/home?authorized=:authorized',
      },
      // if the host is `example.com`,
      // this redirect will be applied
      {
        source: '/:path((?!another-page$).*)',
        has: [
          {
            type: 'host',
            value: 'example.com',
          },
        ],
        permanent: false,
        destination: '/another-page',
      },
    ]
  },
}
```

### Redirects with basePath support

When leveraging [`basePath` support](/docs/app/api-reference/config/next-config-js/basePath) with redirects each `source` and `destination` is automatically prefixed with the `basePath` unless you add `basePath: false` to the redirect:

```js filename="next.config.js"
module.exports = {
  basePath: '/docs',

  async redirects() {
    return [
      {
        source: '/with-basePath', // automatically becomes /docs/with-basePath
        destination: '/another', // automatically becomes /docs/another
        permanent: false,
      },
      {
        // does not add /docs since basePath: false is set
        source: '/without-basePath',
        destination: 'https://example.com',
        basePath: false,
        permanent: false,
      },
    ]
  },
}
```

### Redirects with i18n support

When leveraging [`i18n` support](/docs/pages/guides/internationalization) with redirects each `source` and `destination` is automatically prefixed to handle the configured `locales` unless you add `locale: false` to the redirect. If `locale: false` is used you must prefix the `source` and `destination` with a locale for it to be matched correctly.

```js filename="next.config.js"
module.exports = {
  i18n: {
    locales: ['en', 'fr', 'de'],
    defaultLocale: 'en',
  },

  async redirects() {
    return [
      {
        source: '/with-locale', // automatically handles all locales
        destination: '/another', // automatically passes the locale on
        permanent: false,
      },
      {
        // does not handle locales automatically since locale: false is set
        source: '/nl/with-locale-manual',
        destination: '/nl/another',
        locale: false,
        permanent: false,
      },
      {
        // this matches '/' since `en` is the defaultLocale
        source: '/en',
        destination: '/en/another',
        locale: false,
        permanent: false,
      },
      // it's possible to match all locales even when locale: false is set
      {
        source: '/:locale/page',
        destination: '/en/newpage',
        permanent: false,
        locale: false,
      },
      {
        // this gets converted to /(en|fr|de)/(.*) so will not match the top-level
        // `/` or `/fr` routes like /:path* would
        source: '/(.*)',
        destination: '/another',
        permanent: false,
      },
    ]
  },
}
```

In some rare cases, you might need to assign a custom status code for older HTTP Clients to properly redirect. In these cases, you can use the `statusCode` property instead of the `permanent` property, but not both. To ensure IE11 compatibility, a `Refresh` header is automatically added for the 308 status code.

## Other Redirects

* Inside [API Routes](/docs/pages/building-your-application/routing/api-routes) and [Route Handlers](/docs/app/api-reference/file-conventions/route), you can redirect based on the incoming request.
* Inside [`getStaticProps`](/docs/pages/building-your-application/data-fetching/get-static-props) and [`getServerSideProps`](/docs/pages/building-your-application/data-fetching/get-server-side-props), you can redirect specific pages at request-time.

## Version History

| Version   | Changes            |
| --------- | ------------------ |
| `v13.3.0` | `missing` added.   |
| `v10.2.0` | `has` added.       |
| `v9.5.0`  | `redirects` added. |

---
title: rewrites
description: Add rewrites to your Next.js app.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/rewrites"
version: 16.2.6
router: Pages Router
---

# rewrites

Rewrites allow you to map an incoming request path to a different destination path.

Rewrites act as a URL proxy and mask the destination path, making it appear the user hasn't changed their location on the site. In contrast, [redirects](/docs/pages/api-reference/config/next-config-js/redirects) will reroute to a new page and show the URL changes.

To use rewrites you can use the `rewrites` key in `next.config.js`:

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      {
        source: '/about',
        destination: '/',
      },
    ]
  },
}
```

Rewrites are applied to client-side routing. In the example above, navigating to `` will serve content from `/` while keeping the URL as `/about`.

`rewrites` is an async function that expects to return either an array or an object of arrays (see below) holding objects with `source` and `destination` properties:

* `source`: `String` - is the incoming request path pattern.
* `destination`: `String` is the path you want to route to.
* `basePath`: `false` or `undefined` - if false the basePath won't be included when matching, can be used for external rewrites only.
* `locale`: `false` or `undefined` - whether the locale should not be included when matching.
* `has` is an array of [has objects](#header-cookie-and-query-matching) with the `type`, `key` and `value` properties.
* `missing` is an array of [missing objects](#header-cookie-and-query-matching) with the `type`, `key` and `value` properties.

When the `rewrites` function returns an array, rewrites are applied after checking the filesystem (pages and `/public` files) and before dynamic routes. When the `rewrites` function returns an object of arrays with a specific shape, this behavior can be changed and more finely controlled, as of `v10.1` of Next.js:

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return {
      beforeFiles: [
        // These rewrites are checked after headers/redirects
        // and before all files including _next/public files which
        // allows overriding page files
        {
          source: '/some-page',
          destination: '/somewhere-else',
          has: [{ type: 'query', key: 'overrideMe' }],
        },
      ],
      afterFiles: [
        // These rewrites are checked after pages/public files
        // are checked but before dynamic routes
        {
          source: '/non-existent',
          destination: '/somewhere-else',
        },
      ],
      fallback: [
        // These rewrites are checked after both pages/public files
        // and dynamic routes are checked
        {
          source: '/:path*',
          destination: `https://my-old-site.com/:path*`,
        },
      ],
    }
  },
}
```

> **Good to know**: rewrites in `beforeFiles` do not check the filesystem/dynamic routes immediately after matching a source, they continue until all `beforeFiles` have been checked.

The order Next.js routes are checked is:

1. [headers](/docs/pages/api-reference/config/next-config-js/headers) are checked/applied
2. [redirects](/docs/pages/api-reference/config/next-config-js/redirects) are checked/applied
3. `beforeFiles` rewrites are checked/applied
4. static files from the [public directory](/docs/pages/api-reference/file-conventions/public-folder), `_next/static` files, and non-dynamic pages are checked/served
5. `afterFiles` rewrites are checked/applied, if one of these rewrites is matched we check dynamic routes/static files after each match
6. `fallback` rewrites are checked/applied, these are applied before rendering the 404 page and after dynamic routes/all static assets have been checked. If you use [fallback: true/'blocking'](/docs/pages/api-reference/functions/get-static-paths#fallback-true) in `getStaticPaths`, the fallback `rewrites` defined in your `next.config.js` will *not* be run.

## Rewrite parameters

When using parameters in a rewrite the parameters will be passed in the query by default when none of the parameters are used in the `destination`.

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      {
        source: '/old-about/:path*',
        destination: '/about', // The :path parameter isn't used here so will be automatically passed in the query
      },
    ]
  },
}
```

If a parameter is used in the destination none of the parameters will be automatically passed in the query.

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      {
        source: '/docs/:path*',
        destination: '/:path*', // The :path parameter is used here so will not be automatically passed in the query
      },
    ]
  },
}
```

You can still pass the parameters manually in the query if one is already used in the destination by specifying the query in the `destination`.

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      {
        source: '/:first/:second',
        destination: '/:first?second=:second',
        // Since the :first parameter is used in the destination the :second parameter
        // will not automatically be added in the query although we can manually add it
        // as shown above
      },
    ]
  },
}
```

> **Good to know**: Static pages from [Automatic Static Optimization](/docs/pages/building-your-application/rendering/automatic-static-optimization) or [prerendering](/docs/pages/building-your-application/data-fetching/get-static-props) params from rewrites will be parsed on the client after hydration and provided in the query.

## Path Matching

Path matches are allowed, for example `/blog/:slug` will match `/blog/first-post` (no nested paths):

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      {
        source: '/blog/:slug',
        destination: '/news/:slug', // Matched parameters can be used in the destination
      },
    ]
  },
}
```

The pattern `/blog/:slug` matches `/blog/first-post` and `/blog/post-1` but not `/blog/a/b` (no nested paths). Patterns are anchored to the start: `/blog/:slug` will not match `/archive/blog/first-post`.

You can use modifiers on parameters: `*` (zero or more), `+` (one or more), `?` (zero or one). For example, `/blog/:slug*` matches `/blog`, `/blog/a`, and `/blog/a/b/c`.

Read more details on [path-to-regexp](https://github.com/pillarjs/path-to-regexp) documentation.

### Wildcard Path Matching

To match a wildcard path you can use `*` after a parameter, for example `/blog/:slug*` will match `/blog/a/b/c/d/hello-world`:

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      {
        source: '/blog/:slug*',
        destination: '/news/:slug*', // Matched parameters can be used in the destination
      },
    ]
  },
}
```

### Regex Path Matching

To match a regex path you can wrap the regex in parenthesis after a parameter, for example `/blog/:slug(\\d{1,})` will match `/blog/123` but not `/blog/abc`:

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      {
        source: '/old-blog/:post(\\d{1,})',
        destination: '/blog/:post', // Matched parameters can be used in the destination
      },
    ]
  },
}
```

The following characters `(`, `)`, `{`, `}`, `[`, `]`, `|`, `\`, `^`, `.`, `:`, `*`, `+`, `-`, `?`, `$` are used for regex path matching, so when used in the `source` as non-special values they must be escaped by adding `\\` before them:

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      {
        // this will match `/english(default)/something` being requested
        source: '/english\\(default\\)/:slug',
        destination: '/en-us/:slug',
      },
    ]
  },
}
```

## Header, Cookie, and Query Matching

To only match a rewrite when header, cookie, or query values also match the `has` field or don't match the `missing` field can be used. Both the `source` and all `has` items must match and all `missing` items must not match for the rewrite to be applied.

`has` and `missing` items can have the following fields:

* `type`: `String` - must be either `header`, `cookie`, `host`, or `query`.
* `key`: `String` - the key from the selected type to match against.
* `value`: `String` or `undefined` - the value to check for, if undefined any value will match. A regex like string can be used to capture a specific part of the value, e.g. if the value `first-(?.*)` is used for `first-second` then `second` will be usable in the destination with `:paramName`.

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      // if the header `x-rewrite-me` is present,
      // this rewrite will be applied
      {
        source: '/:path*',
        has: [
          {
            type: 'header',
            key: 'x-rewrite-me',
          },
        ],
        destination: '/another-page',
      },
      // if the header `x-rewrite-me` is not present,
      // this rewrite will be applied
      {
        source: '/:path*',
        missing: [
          {
            type: 'header',
            key: 'x-rewrite-me',
          },
        ],
        destination: '/another-page',
      },
      // if the source, query, and cookie are matched,
      // this rewrite will be applied
      {
        source: '/specific/:path*',
        has: [
          {
            type: 'query',
            key: 'page',
            // the page value will not be available in the
            // destination since value is provided and doesn't
            // use a named capture group e.g. (?home)
            value: 'home',
          },
          {
            type: 'cookie',
            key: 'authorized',
            value: 'true',
          },
        ],
        destination: '/:path*/home',
      },
      // if the header `x-authorized` is present and
      // contains a matching value, this rewrite will be applied
      {
        source: '/:path*',
        has: [
          {
            type: 'header',
            key: 'x-authorized',
            value: '(?yes|true)',
          },
        ],
        destination: '/home?authorized=:authorized',
      },
      // if the host is `example.com`,
      // this rewrite will be applied
      {
        source: '/:path*',
        has: [
          {
            type: 'host',
            value: 'example.com',
          },
        ],
        destination: '/another-page',
      },
    ]
  },
}
```

## Rewriting to an external URL

Examples

* [Using Multiple Zones](https://github.com/vercel/next.js/tree/canary/examples/with-zones)

Rewrites allow you to rewrite to an external URL. This is especially useful for incrementally adopting Next.js. The following is an example rewrite for redirecting the `/blog` route of your main app to an external site.

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return [
      {
        source: '/blog',
        destination: 'https://example.com/blog',
      },
      {
        source: '/blog/:slug',
        destination: 'https://example.com/blog/:slug', // Matched parameters can be used in the destination
      },
    ]
  },
}
```

If you're using `trailingSlash: true`, you also need to insert a trailing slash in the `source` parameter. If the destination server is also expecting a trailing slash it should be included in the `destination` parameter as well.

```js filename="next.config.js"
module.exports = {
  trailingSlash: true,
  async rewrites() {
    return [
      {
        source: '/blog/',
        destination: 'https://example.com/blog/',
      },
      {
        source: '/blog/:path*/',
        destination: 'https://example.com/blog/:path*/',
      },
    ]
  },
}
```

### Incremental adoption of Next.js

You can also have Next.js fall back to proxying to an existing website after checking all Next.js routes.

This way you don't have to change the rewrites configuration when migrating more pages to Next.js

```js filename="next.config.js"
module.exports = {
  async rewrites() {
    return {
      fallback: [
        {
          source: '/:path*',
          destination: `https://custom-routes-proxying-endpoint.vercel.app/:path*`,
        },
      ],
    }
  },
}
```

### Rewrites with basePath support

When leveraging [`basePath` support](/docs/app/api-reference/config/next-config-js/basePath) with rewrites each `source` and `destination` is automatically prefixed with the `basePath` unless you add `basePath: false` to the rewrite:

```js filename="next.config.js"
module.exports = {
  basePath: '/docs',

  async rewrites() {
    return [
      {
        source: '/with-basePath', // automatically becomes /docs/with-basePath
        destination: '/another', // automatically becomes /docs/another
      },
      {
        // does not add /docs to /without-basePath since basePath: false is set
        // Note: this cannot be used for internal rewrites e.g. `destination: '/another'`
        source: '/without-basePath',
        destination: 'https://example.com',
        basePath: false,
      },
    ]
  },
}
```

### Rewrites with i18n support

When leveraging [`i18n` support](/docs/pages/guides/internationalization) with rewrites each `source` and `destination` is automatically prefixed to handle the configured `locales` unless you add `locale: false` to the rewrite. If `locale: false` is used you must prefix the `source` and `destination` with a locale for it to be matched correctly.

```js filename="next.config.js"
module.exports = {
  i18n: {
    locales: ['en', 'fr', 'de'],
    defaultLocale: 'en',
  },

  async rewrites() {
    return [
      {
        source: '/with-locale', // automatically handles all locales
        destination: '/another', // automatically passes the locale on
      },
      {
        // does not handle locales automatically since locale: false is set
        source: '/nl/with-locale-manual',
        destination: '/nl/another',
        locale: false,
      },
      {
        // this matches '/' since `en` is the defaultLocale
        source: '/en',
        destination: '/en/another',
        locale: false,
      },
      {
        // it's possible to match all locales even when locale: false is set
        source: '/:locale/api-alias/:path*',
        destination: '/api/:path*',
        locale: false,
      },
      {
        // this gets converted to /(en|fr|de)/(.*) so will not match the top-level
        // `/` or `/fr` routes like /:path* would
        source: '/(.*)',
        destination: '/another',
      },
    ]
  },
}
```

## Version History

| Version   | Changes          |
| --------- | ---------------- |
| `v13.3.0` | `missing` added. |
| `v10.2.0` | `has` added.     |
| `v9.5.0`  | Headers added.   |

---
title: serverExternalPackages
description: "Opt-out specific dependencies from the dependency bundling enabled by `bundlePagesRouterDependencies`."
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/serverExternalPackages"
version: 16.2.6
router: Pages Router
---

# serverExternalPackages

Opt-out specific dependencies from being included in the automatic bundling of the [`bundlePagesRouterDependencies`](/docs/pages/api-reference/config/next-config-js/bundlePagesRouterDependencies) option.

These pages will then use native Node.js `require` to resolve the dependency.

```js filename="next.config.js"
/** @type {import('next').NextConfig} */
const nextConfig = {
  serverExternalPackages: ['@acme/ui'],
}

module.exports = nextConfig
```

Next.js includes a [short list of popular packages](https://github.com/vercel/next.js/blob/canary/packages/next/src/lib/server-external-packages.jsonc) that currently are working on compatibility and automatically opt-ed out:

* `@alinea/generated`
* `@appsignal/nodejs`
* `@aws-sdk/client-s3`
* `@aws-sdk/s3-presigned-post`
* `@blockfrost/blockfrost-js`
* `@highlight-run/node`
* `@huggingface/transformers`
* `@jpg-store/lucid-cardano`
* `@libsql/client`
* `@mikro-orm/core`
* `@mikro-orm/knex`
* `@node-rs/argon2`
* `@node-rs/bcrypt`
* `@prisma/client`
* `@react-pdf/renderer`
* `@sentry/profiling-node`
* `@sparticuz/chromium`
* `@sparticuz/chromium-min`
* `@statsig/statsig-node-core`
* `@swc/core`
* `@xenova/transformers`
* `@zenstackhq/runtime`
* `argon2`
* `autoprefixer`
* `aws-crt`
* `bcrypt`
* `better-sqlite3`
* `canvas`
* `chromadb-default-embed`
* `config`
* `cpu-features`
* `cypress`
* `dd-trace`
* `eslint`
* `express`
* `firebase-admin`
* `htmlrewriter`
* `import-in-the-middle`
* `isolated-vm`
* `jest`
* `jsdom`
* `keyv`
* `libsql`
* `mdx-bundler`
* `mongodb`
* `mongoose`
* `newrelic`
* `next-mdx-remote`
* `next-seo`
* `node-cron`
* `node-pty`
* `node-web-audio-api`
* `onnxruntime-node`
* `oslo`
* `pg`
* `pino`
* `pino-pretty`
* `pino-roll`
* `playwright`
* `playwright-core`
* `postcss`
* `prettier`
* `prisma`
* `puppeteer-core`
* `puppeteer`
* `ravendb`
* `require-in-the-middle`
* `rimraf`
* `sharp`
* `shiki`
* `sqlite3`
* `thread-stream`
* `ts-morph`
* `ts-node`
* `typescript`
* `vscode-oniguruma`
* `webpack`
* `websocket`
* `zeromq`

---
title: trailingSlash
description: Configure Next.js pages to resolve with or without a trailing slash.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/trailingSlash"
version: 16.2.6
router: Pages Router
---

# trailingSlash

By default Next.js will redirect URLs with trailing slashes to their counterpart without a trailing slash. For example `/about/` will redirect to `/about`. You can configure this behavior to act the opposite way, where URLs without trailing slashes are redirected to their counterparts with trailing slashes.

Open `next.config.js` and add the `trailingSlash` config:

```js filename="next.config.js"
module.exports = {
  trailingSlash: true,
}
```

With this option set, URLs like `/about` will redirect to `/about/`.

When using `trailingSlash: true`, certain URLs are exceptions and will not have a trailing slash appended:

* Static file URLs, such as files with extensions.
* Any paths under `.well-known/`.

For example, the following URLs will remain unchanged: `/file.txt`, `images/photos/picture.png`, and `.well-known/subfolder/config.json`.

When used with [`output: "export"`](/docs/app/guides/static-exports) configuration, the `/about` page will output `/about/index.html` (instead of the default `/about.html`).

## Version History

| Version  | Changes                |
| -------- | ---------------------- |
| `v9.5.0` | `trailingSlash` added. |

---
title: transpilePackages
description: "Automatically transpile and bundle dependencies from local packages (like monorepos) or from external dependencies (`node_modules`)."
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/transpilePackages"
version: 16.2.6
router: Pages Router
---

# transpilePackages

Next.js can automatically transpile and bundle dependencies from local packages (like monorepos) or from external dependencies (`node_modules`). This replaces the `next-transpile-modules` package.

```js filename="next.config.js"
/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['package-name'],
}

module.exports = nextConfig
```

## Version History

| Version   | Changes                    |
| --------- | -------------------------- |
| `v13.0.0` | `transpilePackages` added. |

---
title: turbopack
description: Configure Next.js with Turbopack-specific options
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/turbopack"
version: 16.2.6
router: Pages Router
---

# turbopack

The `turbopack` option lets you customize [Turbopack](/docs/app/api-reference/turbopack) to transform different files and change how modules are resolved.

> **Good to know**: The `turbopack` option was previously named `experimental.turbo` in Next.js versions 13.0.0 to 15.2.x. The `experimental.turbo` option will be removed in Next.js 16.
>
> If you are using an older version of Next.js, run `npx @next/codemod@latest next-experimental-turbo-to-turbopack .` to automatically migrate your configuration.

```ts filename="next.config.ts" switcher
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  turbopack: {
    // ...
  },
}

export default nextConfig
```

```js filename="next.config.js" switcher
/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    // ...
  },
}

module.exports = nextConfig
```

> **Good to know**:
>
> * Turbopack for Next.js does not require loaders or loader configuration for built-in functionality. Turbopack has built-in support for CSS and compiling modern JavaScript, so there's no need for `css-loader`, `postcss-loader`, or `babel-loader` if you're using `@babel/preset-env`.

## Reference

### Options

The following options are available for the `turbopack` configuration:

| Option              | Description                                                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `root`              | Sets the application root directory. Should be an absolute path.                                                                         |
| `rules`             | List of supported webpack loaders to apply when running with Turbopack.                                                                  |
| `resolveAlias`      | Map aliased imports to modules to load in their place.                                                                                   |
| `resolveExtensions` | List of extensions to resolve when importing files.                                                                                      |
| `debugIds`          | Enable generation of [debug IDs](https://github.com/tc39/ecma426/blob/main/proposals/debug-id.md) in JavaScript bundles and source maps. |

### Supported loaders

The following loaders have been tested to work with Turbopack's webpack loader implementation, but many other webpack loaders should work as well even if not listed here:

* [`babel-loader`](https://www.npmjs.com/package/babel-loader) [*(Configured automatically if a Babel configuration file is found)*](/docs/app/api-reference/turbopack#language-features)
* [`@svgr/webpack`](https://www.npmjs.com/package/@svgr/webpack)
* [`svg-inline-loader`](https://www.npmjs.com/package/svg-inline-loader)
* [`yaml-loader`](https://www.npmjs.com/package/yaml-loader)
* [`string-replace-loader`](https://www.npmjs.com/package/string-replace-loader)
* [`raw-loader`](https://www.npmjs.com/package/raw-loader)
* [`sass-loader`](https://www.npmjs.com/package/sass-loader) [*(Configured automatically)*](/docs/app/api-reference/turbopack#css-and-styling)
* [`graphql-tag/loader`](https://www.npmjs.com/package/graphql-tag)

#### Missing Webpack loader features

Turbopack uses the [`loader-runner`](https://github.com/webpack/loader-runner) library to execute webpack loaders, which provides most of the standard loader API. However, some features are not supported:

**Module loading:**

* [`importModule`](https://webpack.js.org/api/loaders/#thisimportmodule) - No support
* [`loadModule`](https://webpack.js.org/api/loaders/#thisloadmodule) - No support

**File system and output:**

* [`fs`](https://webpack.js.org/api/loaders/#thisfs) - Partial support: only `fs.readFile` is currently implemented.
* [`emitFile`](https://webpack.js.org/api/loaders/#thisemitfile) - No support

**Context properties:**

* [`version`](https://webpack.js.org/api/loaders/#thisversion) - No support
* [`mode`](https://webpack.js.org/api/loaders/#thismode) - No support
* [`target`](https://webpack.js.org/api/loaders/#thistarget) - No support

**Utilities:**

* [`utils`](https://webpack.js.org/api/loaders/#thisutils) - No support
* [`resolve`](https://webpack.js.org/api/loaders/#thisresolve) - No support (use [`getResolve`](https://webpack.js.org/api/loaders/#thisgetresolve) instead)

If you have a loader that is critically dependent upon one of these features please file an issue.

## Examples

### Root directory

Turbopack uses the root directory to resolve modules. Files outside of the project root are not resolved.

The reason files are not resolved outside of the project root is to improve cache validation, reduce filesystem watching overhead, and reduce the number of resolving steps needed.

Next.js automatically detects the root directory of your project. It does so by looking for one of these files:

* `pnpm-lock.yaml`
* `package-lock.json`
* `yarn.lock`
* `bun.lock`
* `bun.lockb`

If you have a different project structure, for example if you don't use workspaces, you can manually set the `root` option:

```js filename="next.config.js"
const path = require('path')
module.exports = {
  turbopack: {
    root: path.join(__dirname, '..'),
  },
}
```

To resolve files from linked dependencies outside the project root (via `npm link`, `yarn link`, `pnpm link`, etc.), you must configure the `turbopack.root` to the parent directory of both the project and the linked dependencies.

While this expands the scope of filesystem watching, it's typically only necessary during development when actively working on linked packages.

### Configuring webpack loaders

If you need loader support beyond what's built in, many webpack loaders already work with Turbopack. There are currently some limitations:

* Only a core subset of the webpack loader API is implemented. Currently, there is enough coverage for some popular loaders, and we'll expand our API support in the future.
* Only loaders that return JavaScript code are supported. Loaders that transform files like stylesheets or images are not currently supported.
* Options passed to webpack loaders must be plain JavaScript primitives, objects, and arrays. For example, it's not possible to pass `require()` plugin modules as option values.

To configure loaders, add the names of the loaders you've installed and any options in `next.config.js`, mapping file extensions to a list of loaders. Rules are evaluated in order.

Here is an example below using the [`@svgr/webpack`](https://www.npmjs.com/package/@svgr/webpack) loader, which enables importing `.svg` files and rendering them as React components.

```js filename="next.config.js"
module.exports = {
  turbopack: {
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
  },
}
```

> **Good to know**: Globs used in the `rules` object match based on file name, unless the glob contains a `/` character, which will cause it to match based on the full project-relative file path. Windows file paths are normalized to use unix-style `/` path separators.
>
> Turbopack uses a modified version of the [Rust `globset` library](https://docs.rs/globset/latest/globset/).

For loaders that require configuration options, you can use an object format instead of a string:

```js filename="next.config.js"
module.exports = {
  turbopack: {
    rules: {
      '*.svg': {
        loaders: [
          {
            loader: '@svgr/webpack',
            options: {
              icon: true,
            },
          },
        ],
        as: '*.js',
      },
    },
  },
}
```

> **Good to know**: Prior to Next.js version 13.4.4, `turbopack.rules` was named `turbo.loaders` and only accepted file extensions like `.mdx` instead of `*.mdx`.

### Advanced webpack loader conditions

You can further restrict where a loader runs using the advanced `condition` syntax:

```js filename="next.config.js"
module.exports = {
  turbopack: {
    rules: {
      // '*' will match all file paths, but we restrict where our
      // rule runs with a condition.
      '*': {
        condition: {
          all: [
            // 'foreign' is a built-in condition.
            { not: 'foreign' },
            // 'path' can be a RegExp or a glob string. A RegExp matches
            // anywhere in the full project-relative file path.
            { path: /^img\/[0-9]{3}\// },
            {
              any: [
                { path: '*.svg' },
                // 'query' matches anywhere in the full query string,
                // which can be empty, or start with `?`.
                { query: /[?&]svgr(?=&|$)/ },
                // 'content' is always a RegExp, and can match
                // anywhere in the file.
                { content: /\ **Good to know**: All matching rules are executed in order.

### Module types

You can set the module type directly without using a loader. This is useful for changing how files are processed, similar to webpack's [`type`](https://webpack.js.org/configuration/module/#ruletype) option.

```js filename="next.config.js"
module.exports = {
  turbopack: {
    rules: {
      '*.svg': {
        type: 'asset',
      },
    },
  },
}
```

When using `type: 'asset'`, importing the file returns its URL:

```tsx filename="app/page.tsx"
import svgUrl from './icon.svg'

export default function Page() {
  return
}
```

The `type` option can be combined with `loaders` - loaders run first, then the result is processed according to the specified type.

Available module types:

| Type         | Description                                              |
| ------------ | -------------------------------------------------------- |
| `asset`      | Emit file and return URL (like webpack `asset/resource`) |
| `ecmascript` | Process as JavaScript                                    |
| `typescript` | Process as TypeScript                                    |
| `css`        | Process as CSS                                           |
| `css-module` | Process as CSS module                                    |
| `wasm`       | Process as WebAssembly                                   |
| `raw`        | Return raw contents as string                            |
| `bytes`      | Inline contents as bytes                                 |

### Inline loader configuration with import attributes

You can apply a Turbopack loader to an individual import using the `with` clause (import attributes). This is specified per-import rather than globally via `turbopack.rules`.

This is useful when you want to apply a loader to a specific import without affecting all files of that type.

```tsx filename="app/page.tsx"
// Apply a raw loader to import a .txt file as a JavaScript module
import rawText from '../data.txt' with { turbopackLoader: 'raw-loader', turbopackAs: '*.js' }

export default function Page() {
  return {rawText}

}
```

The following import attributes are supported:

| Attribute                | Description                                                                                                                   |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `turbopackLoader`        | The loader to apply (e.g. `'raw-loader'`).                                                                                    |
| `turbopackLoaderOptions` | JSON string of loader options (e.g. `'{"search":"X","replace":"Y"}'`).                                                        |
| `turbopackAs`            | Rename pattern for the output (same as `turbopack.rules[].as`). For example, `'*.js'` treats the loader output as JavaScript. |
| `turbopackModuleType`    | Set the module type for the output (same as `turbopack.rules[].type`).                                                        |

Loaders with options pass a JSON-encoded string via `turbopackLoaderOptions`:

```tsx filename="app/page.tsx"
import value from '../data.js' with { turbopackLoader: 'string-replace-loader', turbopackLoaderOptions: '{"search":"PLACEHOLDER","replace":"replaced value"}' }
```

> **Good to know**: Import attributes with `turbopackLoader` are Turbopack-specific and are not supported by webpack. This feature requires the `with` keyword (not `assert`) in your import statements.

### Resolving aliases

Turbopack can be configured to modify module resolution through aliases, similar to webpack's [`resolve.alias`](https://webpack.js.org/configuration/resolve/#resolvealias) configuration.

To configure resolve aliases, map imported patterns to their new destination in `next.config.js`:

```js filename="next.config.js"
module.exports = {
  turbopack: {
    resolveAlias: {
      underscore: 'lodash',
      mocha: { browser: 'mocha/browser-entry.js' },
    },
  },
}
```

This aliases imports of the `underscore` package to the `lodash` package. In other words, `import underscore from 'underscore'` will load the `lodash` module instead of `underscore`.

Turbopack also supports conditional aliasing through this field, similar to Node.js' [conditional exports](https://nodejs.org/docs/latest-v18.x/api/packages.html#conditional-exports). At the moment only the `browser` condition is supported. In the case above, imports of the `mocha` module will be aliased to `mocha/browser-entry.js` when Turbopack targets browser environments.

### Resolving custom extensions

Turbopack can be configured to resolve modules with custom extensions, similar to webpack's [`resolve.extensions`](https://webpack.js.org/configuration/resolve/#resolveextensions) configuration.

To configure resolve extensions, use the `resolveExtensions` field in `next.config.js`:

```js filename="next.config.js"
module.exports = {
  turbopack: {
    resolveExtensions: ['.mdx', '.tsx', '.ts', '.jsx', '.js', '.mjs', '.json'],
  },
}
```

This overwrites the original resolve extensions with the provided list. Make sure to include the default extensions.

For more information and guidance for how to migrate your app to Turbopack from webpack, see [Turbopack's documentation on webpack compatibility](https://turbo.build/pack/docs/migrating-from-webpack).

### Debug IDs

Turbopack can be configured to generate [debug IDs](https://github.com/tc39/ecma426/blob/main/proposals/debug-id.md) in JavaScript bundles and source maps.

To configure debug IDs, use the `debugIds` field in `next.config.js`:

```js filename="next.config.js"
module.exports = {
  turbopack: {
    debugIds: true,
  },
}
```

The option automatically adds a polyfill for debug IDs to the JavaScript bundle to ensure compatibility. The debug IDs are available in the `globalThis._debugIds` global variable.

## Version History

| Version  | Changes                                              |
| -------- | ---------------------------------------------------- |
| `16.2.0` | `turbopackLoader` import attributes were added.      |
| `16.2.0` | `turbopack.rules.*.type` was added.                  |
| `16.2.0` | `turbopack.rules.*.condition.contentType` was added. |
| `16.2.0` | `turbopack.rules.*.condition.query` was added.       |
| `16.0.0` | `turbopack.debugIds` was added.                      |
| `16.0.0` | `turbopack.rules.*.condition` was added.             |
| `15.3.0` | `experimental.turbo` is changed to `turbopack`.      |
| `13.0.0` | `experimental.turbo` introduced.                     |

---
title: typescript
description: Next.js reports TypeScript errors by default. Learn to opt-out of this behavior here.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/typescript"
version: 16.2.6
router: Pages Router
---

# typescript

Configure TypeScript behavior with the `typescript` option in `next.config.js`:

```js filename="next.config.js"
module.exports = {
  typescript: {
    ignoreBuildErrors: false,
    tsconfigPath: 'tsconfig.json',
  },
}
```

## Options

| Option              | Type      | Default           | Description                                                      |
| ------------------- | --------- | ----------------- | ---------------------------------------------------------------- |
| `ignoreBuildErrors` | `boolean` | `false`           | Allow production builds to complete even with TypeScript errors. |
| `tsconfigPath`      | `string`  | `'tsconfig.json'` | Path to a custom `tsconfig.json` file.                           |

## `ignoreBuildErrors`

Next.js fails your **production build** (`next build`) when TypeScript errors are present in your project.

If you'd like Next.js to dangerously produce production code even when your application has errors, you can disable the built-in type checking step.

Note that this completely skips the TypeScript type checking step. It does not run TypeScript and suppress errors, it bypasses the check entirely.

If disabled, be sure you are running type checks as part of your build or deploy process, otherwise this can be very dangerous.

```js filename="next.config.js"
module.exports = {
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    // !! WARN !!
    ignoreBuildErrors: true,
  },
}
```

## `tsconfigPath`

Use a different TypeScript configuration file for builds or tooling:

```js filename="next.config.js"
module.exports = {
  typescript: {
    tsconfigPath: 'tsconfig.build.json',
  },
}
```

See the [TypeScript configuration](/docs/app/api-reference/config/typescript#custom-tsconfig-path) page for more details.

---
title: urlImports
description: Configure Next.js to allow importing modules from external URLs.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/urlImports"
version: 16.2.6
router: Pages Router
---

# urlImports

> This feature is currently experimental and subject to change, it's not recommended for production. Try it out and share your feedback on [GitHub](https://github.com/vercel/next.js/issues).

URL imports are an experimental feature that allows you to import modules directly from external servers (instead of from the local disk).

> **Warning**: Only use domains that you trust to download and execute on your machine. Please exercise discretion, and caution until the feature is flagged as stable.

To opt-in, add the allowed URL prefixes inside `next.config.js`:

```js filename="next.config.js"
module.exports = {
  experimental: {
    urlImports: ['https://example.com/assets/', 'https://cdn.skypack.dev'],
  },
}
```

Then, you can import modules directly from URLs:

```js
import { a, b, c } from 'https://example.com/assets/some/module.js'
```

URL Imports can be used everywhere normal package imports can be used.

## Security Model

This feature is being designed with **security as the top priority**. To start, we added an experimental flag forcing you to explicitly allow the domains you accept URL imports from. We're working to take this further by limiting URL imports to execute in the browser sandbox using the [Edge Runtime](/docs/app/api-reference/edge).

## Lockfile

When using URL imports, Next.js will create a `next.lock` directory containing a lockfile and fetched assets.
This directory **must be committed to Git**, not ignored by `.gitignore`.

* When running `next dev`, Next.js will download and add all newly discovered URL Imports to your lockfile.
* When running `next build`, Next.js will use only the lockfile to build the application for production.

Typically, no network requests are needed and any outdated lockfile will cause the build to fail.
One exception is resources that respond with `Cache-Control: no-cache`.
These resources will have a `no-cache` entry in the lockfile and will always be fetched from the network on each build.

## Examples

### Skypack

```js
import confetti from 'https://cdn.skypack.dev/canvas-confetti'
import { useEffect } from 'react'

export default () => {
  useEffect(() => {
    confetti()
  })
  return Hello

}
```

### Static Image Imports

```js
import Image from 'next/image'
import logo from 'https://example.com/assets/logo.png'

export default () => (

)
```

### URLs in CSS

```css
.className {
  background: url('https://example.com/assets/hero.jpg');
}
```

### Asset Imports

```js
const logo = new URL('https://example.com/assets/file.txt', import.meta.url)

console.log(logo.pathname)

// prints "/_next/static/media/file.a9727b5d.txt"
```

---
title: useLightningcss
description: Enable experimental support for Lightning CSS.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/useLightningcss"
version: 16.2.6
router: Pages Router
---

# useLightningcss

> This feature is currently experimental and subject to change, it's not recommended for production. Try it out and share your feedback on [GitHub](https://github.com/vercel/next.js/issues).

Experimental support for using [Lightning CSS](https://lightningcss.dev) with webpack. Lightning CSS is a fast CSS transformer and minifier, written in Rust.

If this option is not set, Next.js on webpack uses [PostCSS](https://postcss.org/) with [`postcss-preset-env`](https://www.npmjs.com/package/postcss-preset-env) by default.

Turbopack uses Lightning CSS by default since Next 14.2. This configuration option has no effect on Turbopack. Turbopack always uses Lightning CSS.

```ts filename="next.config.ts" switcher
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: {
    useLightningcss: false, // default, ignored on Turbopack
  },
}

export default nextConfig
```

```js filename="next.config.js" switcher
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    useLightningcss: true, // disables PostCSS on webpack
  },
}

module.exports = nextConfig
```

## `lightningCssFeatures`

By default, Lightning CSS decides which CSS features to transpile based on your [browserslist](https://browsersl.ist/) targets. The `lightningCssFeatures` option lets you override this by forcing specific features to always be transpiled (`include`) or never be transpiled (`exclude`), regardless of browser support.

This applies to both webpack (when `useLightningcss` is enabled) and Turbopack.

```ts filename="next.config.ts" switcher
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: {
    useLightningcss: true,
    lightningCssFeatures: {
      // Always transpile these features, even if targets support them
      include: ['light-dark', 'oklab-colors'],
      // Never transpile these features, even if targets don't support them
      exclude: ['nesting'],
    },
  },
}

export default nextConfig
```

```js filename="next.config.js" switcher
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    useLightningcss: true,
    lightningCssFeatures: {
      // Always transpile these features, even if targets support them
      include: ['light-dark', 'oklab-colors'],
      // Never transpile these features, even if targets don't support them
      exclude: ['nesting'],
    },
  },
}

module.exports = nextConfig
```

### Options

| Option    | Type       | Description                                                                |
| --------- | ---------- | -------------------------------------------------------------------------- |
| `include` | `string[]` | Features to always transpile, regardless of browser targets.               |
| `exclude` | `string[]` | Features to never transpile, even when browser targets would require them. |

### Available features

Individual features:

| Feature name                        | Description                                          |
| ----------------------------------- | ---------------------------------------------------- |
| `nesting`                           | [CSS Nesting](https://drafts.csswg.org/css-nesting/) |
| `not-selector-list`                 | `:not` with multiple selectors                       |
| `dir-selector`                      | `:dir()` selector                                    |
| `lang-selector-list`                | `:lang()` with multiple languages                    |
| `is-selector`                       | `:is()` selector                                     |
| `text-decoration-thickness-percent` | Percentage values in `text-decoration-thickness`     |
| `media-interval-syntax`             | Media query range interval syntax                    |
| `media-range-syntax`                | Media query range syntax (`width >= 600px`)          |
| `custom-media-queries`              | `@custom-media` rules                                |
| `clamp-function`                    | `clamp()` function                                   |
| `color-function`                    | `color()` function                                   |
| `oklab-colors`                      | `oklab()` and `oklch()` colors                       |
| `lab-colors`                        | `lab()` and `lch()` colors                           |
| `p3-colors`                         | Display P3 colors                                    |
| `hex-alpha-colors`                  | 4 and 8 digit hex colors with alpha                  |
| `space-separated-color-notation`    | Space-separated color notation (`rgb(0 0 0)`)        |
| `font-family-system-ui`             | `system-ui` font family                              |
| `double-position-gradients`         | Double-position gradient stops                       |
| `vendor-prefixes`                   | Vendor-prefixed properties and values                |
| `logical-properties`                | Logical properties and values                        |
| `light-dark`                        | `light-dark()` color function                        |

Composite groups (shorthand for enabling multiple features at once):

| Group name      | Includes                                                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `selectors`     | `nesting`, `not-selector-list`, `dir-selector`, `lang-selector-list`, `is-selector`                                             |
| `media-queries` | `media-interval-syntax`, `media-range-syntax`, `custom-media-queries`                                                           |
| `colors`        | `color-function`, `oklab-colors`, `lab-colors`, `p3-colors`, `hex-alpha-colors`, `space-separated-color-notation`, `light-dark` |

## Version History

| Version  | Changes                                                                                                                                                                                      |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `16.2.0` | `lightningCssFeatures` added.                                                                                                                                                                |
| `15.1.0` | Support for `useSwcCss` was removed from Turbopack.                                                                                                                                          |
| `14.2.0` | Turbopack's default CSS processor was changed from `@swc/css` to Lightning CSS. `useLightningcss` became ignored on Turbopack, and a legacy `experimental.turbo.useSwcCss` option was added. |

---
title: webpack
description: Learn how to customize the webpack config used by Next.js
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/webpack"
version: 16.2.6
router: Pages Router
---

# webpack

> **Good to know**: changes to webpack config are not covered by semver so proceed at your own risk

Before continuing to add custom webpack configuration to your application make sure Next.js doesn't already support your use-case:

* [CSS imports](/docs/app/getting-started/css)
* [CSS modules](/docs/app/getting-started/css)
* [Sass/SCSS imports](/docs/pages/guides/sass)
* [Sass/SCSS modules](/docs/pages/guides/sass)
* [Customizing babel configuration](/docs/pages/guides/babel)

Some commonly asked for features are available as plugins:

* [@next/mdx](https://github.com/vercel/next.js/tree/canary/packages/next-mdx)
* [@next/bundle-analyzer](https://github.com/vercel/next.js/tree/canary/packages/next-bundle-analyzer)

In order to extend our usage of `webpack`, you can define a function that extends its config inside `next.config.js`, like so:

```js filename="next.config.js"
module.exports = {
  webpack: (
    config,
    { buildId, dev, isServer, defaultLoaders, nextRuntime, webpack }
  ) => {
    // Important: return the modified config
    return config
  },
}
```

> The `webpack` function is executed three times, twice for the server (nodejs / edge runtime) and once for the client. This allows you to distinguish between client and server configuration using the `isServer` property.

The second argument to the `webpack` function is an object with the following properties:

* `buildId`: `String` - The build id, used as a unique identifier between builds.
* `dev`: `Boolean` - Indicates if the compilation will be done in development.
* `isServer`: `Boolean` - It's `true` for server-side compilation, and `false` for client-side compilation.
* `nextRuntime`: `String | undefined` - The target runtime for server-side compilation; either `"edge"` or `"nodejs"`, it's `undefined` for client-side compilation.
* `defaultLoaders`: `Object` - Default loaders used internally by Next.js:
  * `babel`: `Object` - Default `babel-loader` configuration.

Example usage of `defaultLoaders.babel`:

```js
// Example config for adding a loader that depends on babel-loader
// This source was taken from the @next/mdx plugin source:
// https://github.com/vercel/next.js/tree/canary/packages/next-mdx
module.exports = {
  webpack: (config, options) => {
    config.module.rules.push({
      test: /\.mdx/,
      use: [
        options.defaultLoaders.babel,
        {
          loader: '@mdx-js/loader',
          options: pluginOptions.options,
        },
      ],
    })

    return config
  },
}
```

#### `nextRuntime`

Notice that `isServer` is `true` when `nextRuntime` is `"edge"` or `"nodejs"`, `nextRuntime` `"edge"` is currently for proxy and Server Components in edge runtime only.

---
title: webVitalsAttribution
description: Learn how to use the webVitalsAttribution option to pinpoint the source of Web Vitals issues.
url: "https://nextjs.org/docs/pages/api-reference/config/next-config-js/webVitalsAttribution"
version: 16.2.6
router: Pages Router
---

# webVitalsAttribution

> This feature is currently experimental and subject to change, it's not recommended for production. Try it out and share your feedback on [GitHub](https://github.com/vercel/next.js/issues).

When debugging issues related to Web Vitals, it is often helpful if we can pinpoint the source of the problem.
For example, in the case of Cumulative Layout Shift (CLS), we might want to know the first element that shifted when the single largest layout shift occurred.
Or, in the case of Largest Contentful Paint (LCP), we might want to identify the element corresponding to the LCP for the page.
If the LCP element is an image, knowing the URL of the image resource can help us locate the asset we need to optimize.

Pinpointing the biggest contributor to the Web Vitals score, aka [attribution](https://github.com/GoogleChrome/web-vitals/blob/4ca38ae64b8d1e899028c692f94d4c56acfc996c/README.md#attribution),
allows us to obtain more in-depth information like entries for [PerformanceEventTiming](https://developer.mozilla.org/docs/Web/API/PerformanceEventTiming), [PerformanceNavigationTiming](https://developer.mozilla.org/docs/Web/API/PerformanceNavigationTiming) and [PerformanceResourceTiming](https://developer.mozilla.org/docs/Web/API/PerformanceResourceTiming).

Attribution is disabled by default in Next.js but can be enabled **per metric** by specifying the following in `next.config.js`.

```js filename="next.config.js"
module.exports = {
  experimental: {
    webVitalsAttribution: ['CLS', 'LCP'],
  },
}
```

Valid attribution values are all `web-vitals` metrics specified in the [`NextWebVitalsMetric`](https://github.com/vercel/next.js/blob/442378d21dd56d6e769863eb8c2cb521a463a2e0/packages/next/shared/lib/utils.ts#L43) type.

---
title: TypeScript
description: Next.js provides a TypeScript-first development experience for building your React application.
url: "https://nextjs.org/docs/pages/api-reference/config/typescript"
version: 16.2.6
router: Pages Router
---

# TypeScript

Next.js comes with built-in TypeScript, automatically installing the necessary packages and configuring the proper settings when you create a new project with `create-next-app`.

To add TypeScript to an existing project, rename a file to `.ts` / `.tsx`. Run `next dev` and `next build` to automatically install the necessary dependencies and add a `tsconfig.json` file with the recommended config options.

> **Good to know**: If you already have a `jsconfig.json` file, copy the `paths` compiler option from the old `jsconfig.json` into the new `tsconfig.json` file, and delete the old `jsconfig.json` file.

## `next-env.d.ts`

Next.js generates a `next-env.d.ts` file in your project root. This file references Next.js type definitions, allowing TypeScript to recognize non-code imports (images, stylesheets, etc.) and Next.js-specific types.

Running `next dev`, `next build`, or [`next typegen`](/docs/app/api-reference/cli/next#next-typegen-options) regenerates this file.

> **Good to know**:
>
> * We recommend adding `next-env.d.ts` to your `.gitignore` file.
> * The file must be in your `tsconfig.json` `include` array (`create-next-app` does this automatically).

## Examples

### Type Checking Next.js Configuration Files

You can use TypeScript and import types in your Next.js configuration by using `next.config.ts`.

```ts filename="next.config.ts"
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  /* config options here */
}

export default nextConfig
```

Module resolution in `next.config.ts` is currently limited to CommonJS. However, ECMAScript Modules (ESM) syntax is available when [using Node.js native TypeScript resolver](#using-nodejs-native-typescript-resolver-for-nextconfigts) for Node.js v22.10.0 and higher.

When using the `next.config.js` file, you can add some type checking in your IDE using JSDoc as below:

```js filename="next.config.js"
// @ts-check

/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
}

module.exports = nextConfig
```

### Using Node.js Native TypeScript Resolver for `next.config.ts`

> **Note**: Available on Node.js v22.10.0+ and only when the feature is enabled. Next.js does not enable it.

Next.js detects the [Node.js native TypeScript resolver](https://nodejs.org/api/typescript.html) via [`process.features.typescript`](https://nodejs.org/api/process.html#processfeaturestypescript), added in **v22.10.0**. When present, `next.config.ts` can use native ESM, including top‑level `await` and dynamic `import()`. This mechanism inherits the capabilities and limitations of Node's resolver.

In Node.js versions **v22.18.0+**, `process.features.typescript` is enabled by default. For versions between **v22.10.0** and **22.17.x**, opt in with `NODE_OPTIONS=--experimental-transform-types`:

```bash filename="Terminal"
NODE_OPTIONS=--experimental-transform-types next
```

#### For CommonJS Projects (Default)

Although `next.config.ts` supports native ESM syntax in CommonJS projects, Node.js will still assume `next.config.ts` is a CommonJS file by default, resulting in Node.js reparsing the file as ESM when module syntax is detected. Therefore, we recommend using the `next.config.mts` file for CommonJS projects to explicitly indicate it's an ESM module:

```ts filename="next.config.mts"
import type { NextConfig } from 'next'

// Top-level await and dynamic import are supported
const flags = await import('./flags.js').then((m) => m.default ?? m)

const nextConfig: NextConfig = {
  /* config options here */
  typedRoutes: Boolean(flags?.typedRoutes),
}

export default nextConfig
```

#### For ESM Projects

When `"type"` is set to `"module"` in `package.json`, your project uses ESM. Learn more about this setting [in the Node.js docs](https://nodejs.org/api/packages.html#type). In this case, you can write `next.config.ts` directly with ESM syntax.

> **Good to know**: When using `"type": "module"` in your `package.json`, all `.js` and `.ts` files in your project are treated as ESM modules by default. You may need to rename files with CommonJS syntax to `.cjs` or `.cts` extensions if needed.

### Statically Typed Links

Next.js can statically type links to prevent typos and other errors when using `next/link`, improving type safety when navigating between pages.

Works in both the Pages and App Router for the `href` prop in `next/link`. In the App Router, it also types `next/navigation` methods like `push`, `replace`, and `prefetch`. It does not type `next/router` methods in Pages Router.

Literal `href` strings are validated, while non-literal `href`s may require a cast with `as Route`.

To opt-into this feature, `typedRoutes` needs to be enabled and the project needs to be using TypeScript.

```ts filename="next.config.ts"
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  typedRoutes: true,
}

export default nextConfig
```

Next.js will generate a link definition in `.next/types` that contains information about all existing routes in your application, which TypeScript can then use to provide feedback in your editor about invalid links.

> **Good to know**: If you set up your project without `create-next-app`, ensure the generated Next.js types are included by adding `.next/types/**/*.ts` to the `include` array in your `tsconfig.json`:

```json filename="tsconfig.json" highlight={4}
{
  "include": [
    "next-env.d.ts",
    ".next/types/**/*.ts",
    "**/*.ts",
    "**/*.tsx"
  ],
  "exclude": ["node_modules"]
}
```

Currently, support includes any string literal, including dynamic segments. For non-literal strings, you need to manually cast with `as Route`. The example below shows both `next/link` and `next/navigation` usage:

```tsx filename="app/example-client.tsx"
'use client'

import type { Route } from 'next'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function Example() {
  const router = useRouter()
  const slug = 'nextjs'

  return (
    <>
      {/* Link: literal and dynamic */}

      {/* TypeScript error if href is not a valid route */}

      {/* Router: literal and dynamic strings are validated */}
       router.push('/about')}>Push About
       router.replace(`/blog/${slug}`)}>
        Replace Blog

       router.prefetch('/contact')}>
        Prefetch Contact

      {/* For non-literal strings, cast to Route */}
       router.push(('/blog/' + slug) as Route)}>
        Push Non-literal Blog

  )
}
```

The same applies for redirecting routes defined by proxy:

```ts filename="proxy.ts"
import { NextRequest, NextResponse } from 'next/server'

export function proxy(request: NextRequest) {
  if (request.nextUrl.pathname === '/proxy-redirect') {
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}
```

```tsx filename="app/some/page.tsx"
import type { Route } from 'next'

export default function Page() {
  return Link Text
}
```

To accept `href` in a custom component wrapping `next/link`, use a generic:

```tsx
import type { Route } from 'next'
import Link from 'next/link'

function Card({ href }: { href: Route | URL }) {
  return (

      My Card

  )
}
```

You can also type a simple data structure and iterate to render links:

```ts filename="components/nav-items.ts"
import type { Route } from 'next'

type NavItem = {
  href: T
  label: string
}

export const navItems: NavItem[] = [
  { href: '/', label: 'Home' },
  { href: '/about', label: 'About' },
  { href: '/blog', label: 'Blog' },
]
```

Then, map over the items to render `Link`s:

```tsx filename="components/nav.tsx"
import Link from 'next/link'
import { navItems } from './nav-items'

export function Nav() {
  return (

  )
}
```

> **How does it work?**
>
> When running `next dev` or `next build`, Next.js generates a hidden `.d.ts` file inside `.next` that contains information about all existing routes in your application (all valid routes as the `href` type of `Link`). This `.d.ts` file is included in `tsconfig.json` and the TypeScript compiler will check that `.d.ts` and provide feedback in your editor about invalid links.

### Type IntelliSense for Environment Variables

During development, Next.js generates a `.d.ts` file in `.next/types` that contains information about the loaded environment variables for your editor's IntelliSense. If the same environment variable key is defined in multiple files, it is deduplicated according to the [Environment Variable Load Order](/docs/app/guides/environment-variables#environment-variable-load-order).

To opt-into this feature, `experimental.typedEnv` needs to be enabled and the project needs to be using TypeScript.

```ts filename="next.config.ts"
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: {
    typedEnv: true,
  },
}

export default nextConfig
```

> **Good to know**: Types are generated based on the environment variables loaded at development runtime, which excludes variables from `.env.production*` files by default. To include production-specific variables, run `next dev` with `NODE_ENV=production`.

### Static Generation and Server-side Rendering

For [`getStaticProps`](/docs/pages/api-reference/functions/get-static-props), [`getStaticPaths`](/docs/pages/api-reference/functions/get-static-paths), and [`getServerSideProps`](/docs/pages/api-reference/functions/get-server-side-props), you can use the `GetStaticProps`, `GetStaticPaths`, and `GetServerSideProps` types respectively:

```tsx filename="pages/blog/[slug].tsx"
import type { GetStaticProps, GetStaticPaths, GetServerSideProps } from 'next'

export const getStaticProps = (async (context) => {
  // ...
}) satisfies GetStaticProps

export const getStaticPaths = (async () => {
  // ...
}) satisfies GetStaticPaths

export const getServerSideProps = (async (context) => {
  // ...
}) satisfies GetServerSideProps
```

> **Good to know:** `satisfies` was added to TypeScript in [4.9](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html). We recommend upgrading to the latest version of TypeScript.

### With API Routes

The following is an example of how to use the built-in types for API routes:

```ts filename="pages/api/hello.ts"
import type { NextApiRequest, NextApiResponse } from 'next'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json({ name: 'John Doe' })
}
```

You can also type the response data:

```ts filename="pages/api/hello.ts"
import type { NextApiRequest, NextApiResponse } from 'next'

type Data = {
  name: string
}

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  res.status(200).json({ name: 'John Doe' })
}
```

### With custom `App`

If you have a [custom `App`](/docs/pages/building-your-application/routing/custom-app), you can use the built-in type `AppProps` and change file name to `./pages/_app.tsx` like so:

```ts
import type { AppProps } from 'next/app'

export default function MyApp({ Component, pageProps }: AppProps) {
  return
}
```

### Incremental type checking

Since `v10.2.1` Next.js supports [incremental type checking](https://www.typescriptlang.org/tsconfig#incremental) when enabled in your `tsconfig.json`, this can help speed up type checking in larger applications.

### Custom `tsconfig` path

In some cases, you might want to use a different TypeScript configuration for builds or tooling. To do that, set `typescript.tsconfigPath` in `next.config.ts` to point Next.js to another `tsconfig` file.

```ts filename="next.config.ts"
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  typescript: {
    tsconfigPath: 'tsconfig.build.json',
  },
}

export default nextConfig
```

For example, switch to a different config for production builds:

```ts filename="next.config.ts"
import type { NextConfig } from 'next'

const isProd = process.env.NODE_ENV === 'production'

const nextConfig: NextConfig = {
  typescript: {
    tsconfigPath: isProd ? 'tsconfig.build.json' : 'tsconfig.json',
  },
}

export default nextConfig
```

Why you might use a separate `tsconfig` for builds

You might need to relax checks in scenarios like monorepos, where the build also validates shared dependencies that don't match your project's standards, or when loosening checks in CI to continue delivering while migrating locally to stricter TypeScript settings (and still wanting your IDE to highlight misuse).

For example, if your project uses `useUnknownInCatchVariables` but some monorepo dependencies still assume `any`:

```json filename="tsconfig.build.json"
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "useUnknownInCatchVariables": false
  }
}
```

This keeps your editor strict via `tsconfig.json` while allowing the production build to use relaxed settings.

> **Good to know**:
>
> * IDEs typically read `tsconfig.json` for diagnostics and IntelliSense, so you can still see IDE warnings while production builds use the alternate config. Mirror critical options if you want parity in the editor.
> * In development, only `tsconfig.json` is watched for changes. If you edit a different file name via `typescript.tsconfigPath`, restart the dev server to apply changes.
> * The configured file is used in `next dev`, `next build`, and `next typegen`.

### Disabling TypeScript errors in production

Next.js fails your **production build** (`next build`) when TypeScript errors are present in your project.

If you'd like Next.js to dangerously produce production code even when your application has errors, you can disable the built-in type checking step.

If disabled, be sure you are running type checks as part of your build or deploy process, otherwise this can be very dangerous.

Open `next.config.ts` and enable the `ignoreBuildErrors` option in the [`typescript`](/docs/app/api-reference/config/next-config-js/typescript) config:

```ts filename="next.config.ts"
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    // !! WARN !!
    ignoreBuildErrors: true,
  },
}

export default nextConfig
```

> **Good to know**: You can run `tsc --noEmit` to check for TypeScript errors yourself before building. This is useful for CI/CD pipelines where you'd like to check for TypeScript errors before deploying.

### Custom type declarations

When you need to declare custom types, you might be tempted to modify `next-env.d.ts`. However, this file is automatically generated, so any changes you make will be overwritten. Instead, you should create a new file, let's call it `new-types.d.ts`, and reference it in your `tsconfig.json`:

```json filename="tsconfig.json"
{
  "compilerOptions": {
    "skipLibCheck": true
    //...truncated...
  },
  "include": [
    "new-types.d.ts",
    "next-env.d.ts",
    ".next/types/**/*.ts",
    "**/*.ts",
    "**/*.tsx"
  ],
  "exclude": ["node_modules"]
}
```

## Version Changes

| Version   | Changes                                                                                                                              |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `v15.0.0` | [`next.config.ts`](#type-checking-nextjs-configuration-files) support added for TypeScript projects.                                 |
| `v13.2.0` | Statically typed links are available in beta.                                                                                        |
| `v12.0.0` | [SWC](/docs/architecture/nextjs-compiler) is now used by default to compile TypeScript and TSX for faster builds.                    |
| `v10.2.1` | [Incremental type checking](https://www.typescriptlang.org/tsconfig#incremental) support added when enabled in your `tsconfig.json`. |

---
title: ESLint
description: Next.js reports ESLint errors and warnings during builds by default. Learn how to opt-out of this behavior here.
url: "https://nextjs.org/docs/pages/api-reference/config/eslint"
version: 16.2.6
router: Pages Router
---

# ESLint

Next.js provides an ESLint configuration package, [`eslint-config-next`](https://www.npmjs.com/package/eslint-config-next), that makes it easy to catch common issues in your application. It includes the [`@next/eslint-plugin-next`](https://www.npmjs.com/package/@next/eslint-plugin-next) plugin along with recommended rule-sets from [`eslint-plugin-react`](https://www.npmjs.com/package/eslint-plugin-react) and [`eslint-plugin-react-hooks`](https://www.npmjs.com/package/eslint-plugin-react-hooks).

The package provides two main configurations:

* **`eslint-config-next`**: Base configuration with Next.js, React, and React Hooks rules. Supports both JavaScript and TypeScript files.
* **`eslint-config-next/core-web-vitals`**: Includes everything from the base config, plus upgrades rules that impact [Core Web Vitals](https://web.dev/vitals/) from warnings to errors. Recommended for most projects.

Additionally, for TypeScript projects:

* **`eslint-config-next/typescript`**: Adds TypeScript-specific linting rules from [`typescript-eslint`](https://typescript-eslint.io/). Use this alongside the base or core-web-vitals config.

## Setup ESLint

Get linting working quickly with the ESLint CLI (flat config):

1. Install ESLint and the Next.js config:

   ```bash package="pnpm"
   pnpm add -D eslint eslint-config-next
   ```

   ```bash package="npm"
   npm i -D eslint eslint-config-next
   ```

   ```bash package="yarn"
   yarn add --dev eslint eslint-config-next
   ```

   ```bash package="bun"
   bun add -d eslint eslint-config-next
   ```

2. Create `eslint.config.mjs` with the Next.js config:

   ```js filename="eslint.config.mjs"
   import { defineConfig, globalIgnores } from 'eslint/config'
   import nextVitals from 'eslint-config-next/core-web-vitals'

   const eslintConfig = defineConfig([
     ...nextVitals,
     // Override default ignores of eslint-config-next.
     globalIgnores([
       // Default ignores of eslint-config-next:
       '.next/**',
       'out/**',
       'build/**',
       'next-env.d.ts',
     ]),
   ])

   export default eslintConfig
   ```

3. Run ESLint:

   ```bash package="pnpm"
   pnpm exec eslint .
   ```

   ```bash package="npm"
   npx eslint .
   ```

   ```bash package="yarn"
   yarn eslint .
   ```

   ```bash package="bun"
   bunx eslint .
   ```

## Reference

The `eslint-config-next` package includes the `recommended` rule-sets from the following ESLint plugins:

* [`eslint-plugin-react`](https://www.npmjs.com/package/eslint-plugin-react)
* [`eslint-plugin-react-hooks`](https://www.npmjs.com/package/eslint-plugin-react-hooks)
* [`@next/eslint-plugin-next`](https://www.npmjs.com/package/@next/eslint-plugin-next)

### Rules

The `@next/eslint-plugin-next` rules included are:

| Enabled in recommended config | Rule                                                                                                                     | Description                                                                                                      |
| :---------------------------: | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
|      ✓      | [@next/next/google-font-display](/docs/messages/google-font-display)                                                     | Enforce font-display behavior with Google Fonts.                                                                 |
|      ✓      | [@next/next/google-font-preconnect](/docs/messages/google-font-preconnect)                                               | Ensure `preconnect` is used with Google Fonts.                                                                   |
|      ✓      | [@next/next/inline-script-id](/docs/messages/inline-script-id)                                                           | Enforce `id` attribute on `next/script` components with inline content.                                          |
|      ✓      | [@next/next/next-script-for-ga](/docs/messages/next-script-for-ga)                                                       | Prefer `next/script` component when using the inline script for Google Analytics.                                |
|      ✓      | [@next/next/no-assign-module-variable](/docs/messages/no-assign-module-variable)                                         | Prevent assignment to the `module` variable.                                                                     |
|      ✓      | [@next/next/no-async-client-component](/docs/messages/no-async-client-component)                                         | Prevent Client Components from being async functions.                                                            |
|      ✓      | [@next/next/no-before-interactive-script-outside-document](/docs/messages/no-before-interactive-script-outside-document) | Prevent usage of `next/script`'s `beforeInteractive` strategy outside of `pages/_document.js`.                   |
|      ✓      | [@next/next/no-css-tags](/docs/messages/no-css-tags)                                                                     | Prevent manual stylesheet tags.                                                                                  |
|      ✓      | [@next/next/no-document-import-in-page](/docs/messages/no-document-import-in-page)                                       | Prevent importing `next/document` outside of `pages/_document.js`.                                               |
|      ✓      | [@next/next/no-duplicate-head](/docs/messages/no-duplicate-head)                                                         | Prevent duplicate usage of `` in `pages/_document.js`.                                                     |
|      ✓      | [@next/next/no-head-element](/docs/messages/no-head-element)                                                             | Prevent usage of `` element.                                                                               |
|      ✓      | [@next/next/no-head-import-in-document](/docs/messages/no-head-import-in-document)                                       | Prevent usage of `next/head` in `pages/_document.js`.                                                            |
|      ✓      | [@next/next/no-html-link-for-pages](/docs/messages/no-html-link-for-pages)                                               | Prevent usage of `` elements to navigate to internal Next.js pages.                                           |
|      ✓      | [@next/next/no-img-element](/docs/messages/no-img-element)                                                               | Prevent usage of `` element due to slower LCP and higher bandwidth.                                         |
|      ✓      | [@next/next/no-page-custom-font](/docs/messages/no-page-custom-font)                                                     | Prevent page-only custom fonts.                                                                                  |
|      ✓      | [@next/next/no-script-component-in-head](/docs/messages/no-script-component-in-head)                                     | Prevent usage of `next/script` in `next/head` component.                                                         |
|      ✓      | [@next/next/no-styled-jsx-in-document](/docs/messages/no-styled-jsx-in-document)                                         | Prevent usage of `styled-jsx` in `pages/_document.js`.                                                           |
|      ✓      | [@next/next/no-sync-scripts](/docs/messages/no-sync-scripts)                                                             | Prevent synchronous scripts.                                                                                     |
|      ✓      | [@next/next/no-title-in-document-head](/docs/messages/no-title-in-document-head)                                         | Prevent usage of `` with `Head` component from `next/document`.                                           |
|      ✓      | @next/next/no-typos                                                                                                      | Prevent common typos in [Next.js's data fetching functions](/docs/pages/building-your-application/data-fetching) |
|      ✓      | [@next/next/no-unwanted-polyfillio](/docs/messages/no-unwanted-polyfillio)                                               | Prevent duplicate polyfills from Polyfill.io.                                                                    |

We recommend using an appropriate [integration](https://eslint.org/docs/user-guide/integrations#editors) to view warnings and errors directly in your code editor during development.

`next lint` removal

Starting with Next.js 16, `next lint` is removed.

As part of the removal, the `eslint` option in your Next config file is no longer needed and can be safely removed.

## Examples

### Specifying a root directory within a monorepo

If you're using `@next/eslint-plugin-next` in a project where Next.js isn't installed in your root directory (such as a monorepo), you can tell `@next/eslint-plugin-next` where to find your Next.js application using the `settings` property in your `eslint.config.mjs`:

```js filename="eslint.config.mjs"
import { defineConfig } from 'eslint/config'
import eslintNextPlugin from '@next/eslint-plugin-next'

const eslintConfig = defineConfig([
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    plugins: {
      next: eslintNextPlugin,
    },
    settings: {
      next: {
        rootDir: 'packages/my-app/',
      },
    },
  },
])

export default eslintConfig
```

`rootDir` can be a path (relative or absolute), a glob (i.e. `"packages/*/"`), or an array of paths and/or globs.

### Disabling rules

If you would like to modify or disable any rules provided by the supported plugins (`react`, `react-hooks`, `next`), you can directly change them using the `rules` property in your `eslint.config.mjs`:

```js filename="eslint.config.mjs"
import { defineConfig, globalIgnores } from 'eslint/config'
import nextVitals from 'eslint-config-next/core-web-vitals'

const eslintConfig = defineConfig([
  ...nextVitals,
  {
    rules: {
      'react/no-unescaped-entities': 'off',
      '@next/next/no-page-custom-font': 'off',
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    '.next/**',
    'out/**',
    'build/**',
    'next-env.d.ts',
  ]),
])

export default eslintConfig
```

### With Core Web Vitals

Enable the `eslint-config-next/core-web-vitals` configuration in your ESLint config.

```js filename="eslint.config.mjs"
import { defineConfig, globalIgnores } from 'eslint/config'
import nextVitals from 'eslint-config-next/core-web-vitals'

const eslintConfig = defineConfig([
  ...nextVitals,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    '.next/**',
    'out/**',
    'build/**',
    'next-env.d.ts',
  ]),
])

export default eslintConfig
```

`eslint-config-next/core-web-vitals` upgrades certain lint rules in `@next/eslint-plugin-next` from warnings to errors to help improve your [Core Web Vitals](https://web.dev/vitals/) metrics.

> The `eslint-config-next/core-web-vitals` configuration is automatically included for new applications built with [Create Next App](/docs/app/api-reference/cli/create-next-app).

### With TypeScript

In addition to the Next.js ESLint rules, `create-next-app --typescript` will also add TypeScript-specific lint rules with `eslint-config-next/typescript` to your config:

```js filename="eslint.config.mjs"
import { defineConfig, globalIgnores } from 'eslint/config'
import nextVitals from 'eslint-config-next/core-web-vitals'
import nextTs from 'eslint-config-next/typescript'

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    '.next/**',
    'out/**',
    'build/**',
    'next-env.d.ts',
  ]),
])

export default eslintConfig
```

Those rules are based on [`plugin:@typescript-eslint/recommended`](https://typescript-eslint.io/linting/configs#recommended).
See [typescript-eslint > Configs](https://typescript-eslint.io/linting/configs) for more details.

### With Prettier

ESLint also contains code formatting rules, which can conflict with your existing [Prettier](https://prettier.io/) setup. We recommend including [eslint-config-prettier](https://github.com/prettier/eslint-config-prettier) in your ESLint config to make ESLint and Prettier work together.

First, install the dependency:

```bash package="pnpm"
pnpm add -D eslint-config-prettier
```

```bash package="npm"
npm i -D eslint-config-prettier
```

```bash package="yarn"
yarn add --dev eslint-config-prettier
```

```bash package="bun"
bun add -d eslint-config-prettier
```

Then, add `prettier` to your existing ESLint config:

```js filename="eslint.config.mjs"
import { defineConfig, globalIgnores } from 'eslint/config'
import nextVitals from 'eslint-config-next/core-web-vitals'
import prettier from 'eslint-config-prettier/flat'

const eslintConfig = defineConfig([
  ...nextVitals,
  prettier,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    '.next/**',
    'out/**',
    'build/**',
    'next-env.d.ts',
  ]),
])

export default eslintConfig
```

### Running lint on staged files

If you would like to use ESLint with [lint-staged](https://github.com/okonet/lint-staged) to run the linter on staged git files, add the following to the `.lintstagedrc.js` file in the root of your project:

```js filename=".lintstagedrc.js"
const path = require('path')

const buildEslintCommand = (filenames) =>
  `eslint --fix ${filenames
    .map((f) => `"${path.relative(process.cwd(), f)}"`)
    .join(' ')}`

module.exports = {
  '*.{js,jsx,ts,tsx}': [buildEslintCommand],
}
```

## Migrating existing config

If you already have ESLint configured in your application, there are two approaches to integrate Next.js linting rules, depending on your setup.

#### Using the plugin directly

Use `@next/eslint-plugin-next` directly if you have any of the following already configured:

* Conflicting plugins installed separately or through another config (such as `airbnb` or `react-app`):
  * `react`
  * `react-hooks`
  * `jsx-a11y`
  * `import`
* Custom `parserOptions` different from Next.js defaults (only if you have [customized your Babel configuration](/docs/pages/guides/babel))
* `eslint-plugin-import` with custom Node.js and/or TypeScript [resolvers](https://github.com/benmosher/eslint-plugin-import#resolvers)

In these cases, use `@next/eslint-plugin-next` directly to avoid conflicts:

First, install the plugin:

```bash package="pnpm"
pnpm add -D @next/eslint-plugin-next
```

```bash package="npm"
npm i -D @next/eslint-plugin-next
```

```bash package="yarn"
yarn add --dev @next/eslint-plugin-next
```

```bash package="bun"
bun add -d @next/eslint-plugin-next
```

Then add it to your ESLint config:

```js filename="eslint.config.mjs"
import { defineConfig } from 'eslint/config'
import nextPlugin from '@next/eslint-plugin-next'

const eslintConfig = defineConfig([
  // Your other configurations...
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    plugins: {
      '@next/next': nextPlugin,
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
    },
  },
])

export default eslintConfig
```

This approach eliminates the risk of collisions or errors that can occur when the same plugins or parsers are imported across multiple configurations.

#### Adding to existing config

If you're adding Next.js to an existing ESLint setup, spread the Next.js config into your array:

```js filename="eslint.config.mjs"
import nextConfig from 'eslint-config-next/core-web-vitals'
// Your other config imports...

const eslintConfig = [
  // Your other configurations...
  ...nextConfig,
]

export default eslintConfig
```

When you spread `...nextConfig`, you're adding multiple config objects that include file patterns, plugins, rules, ignores, and parser settings. ESLint applies configs in order, so later rules can override earlier ones for matching files.

> **Good to know:** This approach works well for straightforward setups. If you have a complex existing config with specific file patterns or plugin configurations that conflict, consider using the plugin directly (as shown above) for more granular control.

| Version   | Changes                                                                                                                                                                                                             |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `v16.0.0` | `next lint` and the `eslint` next.config.js option were removed in favor of the ESLint CLI. A [codemod](/docs/app/guides/upgrading/codemods#migrate-from-next-lint-to-eslint-cli) is available to help you migrate. |

---
title: CLI
description: API Reference for the Next.js Command Line Interface (CLI) tools.
url: "https://nextjs.org/docs/pages/api-reference/cli"
version: 16.2.6
router: Pages Router
---

# CLI

Next.js comes with **two** Command Line Interface (CLI) tools:

* **`create-next-app`**: Quickly create a new Next.js application using the default template or an [example](https://github.com/vercel/next.js/tree/canary/examples) from a public GitHub repository.
* **`next`**: Run the Next.js development server, build your application, and more.

 - [create-next-app CLI](/docs/pages/api-reference/cli/create-next-app)
 - [next CLI](/docs/pages/api-reference/cli/next)

---
title: create-next-app CLI
description: Create Next.js apps using one command with the create-next-app CLI.
url: "https://nextjs.org/docs/pages/api-reference/cli/create-next-app"
version: 16.2.6
router: Pages Router
---

# create-next-app CLI

The `create-next-app` CLI allow you to create a new Next.js application using the default template or an [example](https://github.com/vercel/next.js/tree/canary/examples) from a public GitHub repository. It is the easiest way to get started with Next.js.

Basic usage:

```bash package="pnpm"
pnpm create next-app [project-name] [options]
```

```bash package="npm"
npx create-next-app@latest [project-name] [options]
```

```bash package="yarn"
yarn create next-app [project-name] [options]
```

```bash package="bun"
bun create next-app [project-name] [options]
```

## Reference

The following options are available:

| Options                                 | Description                                                           |
| --------------------------------------- | --------------------------------------------------------------------- |
| `-h` or `--help`                        | Show all available options                                            |
| `-v` or `--version`                     | Output the version number                                             |
| `--no-*`                                | Negate default options. E.g. `--no-ts`                                |
| `--ts` or `--typescript`                | Initialize as a TypeScript project (default)                          |
| `--js` or `--javascript`                | Initialize as a JavaScript project                                    |
| `--tailwind`                            | Initialize with Tailwind CSS config (default)                         |
| `--react-compiler`                      | Initialize with React Compiler enabled                                |
| `--eslint`                              | Initialize with ESLint config                                         |
| `--biome`                               | Initialize with Biome config                                          |
| `--no-linter`                           | Skip linter configuration                                             |
| `--app`                                 | Initialize as an App Router project                                   |
| `--api`                                 | Initialize a project with only route handlers                         |
| `--src-dir`                             | Initialize inside a `src/` directory                                  |
| `--turbopack`                           | Force enable Turbopack in generated package.json (enabled by default) |
| `--webpack`                             | Force enable Webpack in generated package.json                        |
| `--import-alias `   | Specify import alias to use (default "@/\*")                          |
| `--empty`                               | Initialize an empty project                                           |
| `--use-npm`                             | Explicitly tell the CLI to bootstrap the application using npm        |
| `--use-pnpm`                            | Explicitly tell the CLI to bootstrap the application using pnpm       |
| `--use-yarn`                            | Explicitly tell the CLI to bootstrap the application using Yarn       |
| `--use-bun`                             | Explicitly tell the CLI to bootstrap the application using Bun        |
| `-e` or `--example [name] [github-url]` | An example to bootstrap the app with                                  |
| `--example-path `      | Specify the path to the example separately                            |
| `--reset-preferences`                   | Explicitly tell the CLI to reset any stored preferences               |
| `--skip-install`                        | Explicitly tell the CLI to skip installing packages                   |
| `--disable-git`                         | Explicitly tell the CLI to disable git initialization                 |
| `--agents-md`                           | Include `AGENTS.md` and `CLAUDE.md` to guide coding agents (default)  |
| `--yes`                                 | Use previous preferences or defaults for all options                  |

## Examples

### With the default template

To create a new app using the default template, run the following command in your terminal:

```bash package="pnpm"
pnpm create next-app
```

```bash package="npm"
npx create-next-app@latest
```

```bash package="yarn"
yarn create next-app
```

```bash package="bun"
bun create next-app
```

On installation, you'll see the following prompts:

```txt filename="Terminal"
What is your project named? my-app
Would you like to use the recommended Next.js defaults?
    Yes, use recommended defaults - TypeScript, ESLint, Tailwind CSS, App Router, AGENTS.md
    No, reuse previous settings
    No, customize settings - Choose your own preferences
```

If you choose to `customize settings`, you'll see the following prompts:

```txt filename="Terminal"
Would you like to use TypeScript? No / Yes
Which linter would you like to use? ESLint / Biome / None
Would you like to use React Compiler? No / Yes
Would you like to use Tailwind CSS? No / Yes
Would you like your code inside a `src/` directory? No / Yes
Would you like to use App Router? (recommended) No / Yes
Would you like to customize the import alias (`@/*` by default)? No / Yes
What import alias would you like configured? @/*
Would you like to include AGENTS.md to guide coding agents to write up-to-date Next.js code? No / Yes
```

After the prompts, `create-next-app` will create a folder with your project name and install the required dependencies.

### Linter Options

**ESLint**: The traditional and most popular JavaScript linter. Includes Next.js-specific rules from `@next/eslint-plugin-next`.

**Biome**: A fast, modern linter and formatter that combines the functionality of ESLint and Prettier. Includes built-in Next.js and React domain support for optimal performance.

**None**: Skip linter configuration entirely. You can always add a linter later.

Once you've answered the prompts, a new project will be created with your chosen configuration.

### With an official Next.js example

To create a new app using an official Next.js example, use the `--example` flag. For example:

```bash package="pnpm"
pnpm create next-app --example [example-name] [your-project-name]
```

```bash package="npm"
npx create-next-app@latest --example [example-name] [your-project-name]
```

```bash package="yarn"
yarn create next-app --example [example-name] [your-project-name]
```

```bash package="bun"
bun create next-app --example [example-name] [your-project-name]
```

You can view a list of all available examples along with setup instructions in the [Next.js repository](https://github.com/vercel/next.js/tree/canary/examples).

### With any public GitHub example

To create a new app using any public GitHub example, use the `--example` option with the GitHub repo's URL. For example:

```bash package="pnpm"
pnpm create next-app --example "https://github.com/.../" [your-project-name]
```

```bash package="npm"
npx create-next-app@latest --example "https://github.com/.../" [your-project-name]
```

```bash package="yarn"
yarn create next-app --example "https://github.com/.../" [your-project-name]
```

```bash package="bun"
bun create next-app --example "https://github.com/.../" [your-project-name]
```

---
title: next CLI
description: Learn how to run and build your application with the Next.js CLI.
url: "https://nextjs.org/docs/pages/api-reference/cli/next"
version: 16.2.6
router: Pages Router
---

# next CLI

The Next.js CLI allows you to develop, build, start your application, and more.

Basic usage:

```bash package="pnpm"
pnpm next [command] [options]
```

```bash package="npm"
npx next [command] [options]
```

```bash package="yarn"
yarn next [command] [options]
```

```bash package="bun"
bunx next [command] [options]
```

> **Good to know**: With `npm run`, use `--` before CLI flags so npm forwards them to `next`. This is not required for `pnpm`, `yarn`, or `bun`.

## Reference

The following options are available:

| Options             | Description                        |
| ------------------- | ---------------------------------- |
| `-h` or `--help`    | Shows all available options        |
| `-v` or `--version` | Outputs the Next.js version number |

### Commands

The following commands are available:

| Command                                                      | Description                                                                                                   |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| [`dev`](#next-dev-options)                                   | Starts Next.js in development mode with Hot Module Reloading, error reporting, and more.                      |
| [`build`](#next-build-options)                               | Creates an optimized production build of your application. Displaying information about each route.           |
| [`start`](#next-start-options)                               | Starts Next.js in production mode. The application should be compiled with `next build` first.                |
| [`info`](#next-info-options)                                 | Prints relevant details about the current system which can be used to report Next.js bugs.                    |
| [`telemetry`](#next-telemetry-options)                       | Allows you to enable or disable Next.js' completely anonymous telemetry collection.                           |
| [`typegen`](#next-typegen-options)                           | Generates TypeScript definitions for routes, pages, layouts, and route handlers without running a full build. |
| [`upgrade`](#next-upgrade-options)                           | Upgrades your Next.js application to the latest version.                                                      |
| [`experimental-analyze`](#next-experimental-analyze-options) | Analyzes bundle output using Turbopack. Does not produce build artifacts.                                     |

> **Good to know**: Running `next` without a command is an alias for `next dev`.

### `next dev` options

`next dev` starts the application in development mode with Hot Module Reloading (HMR), error reporting, and more.

> **Good to know**: Development builds output to `.next/dev` instead of `.next`. This allows you to run `next dev` and `next build` concurrently without conflicts.

The following options are available when running `next dev`:

| Option                                   | Description                                                                                                                                          |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-h, --help`                             | Show all available options.                                                                                                                          |
| `[directory]`                            | A directory in which to build the application. If not provided, current directory is used.                                                           |
| `--turbopack`                            | Force enable [Turbopack](/docs/app/api-reference/turbopack) (enabled by default). Also available as `--turbo`.                                       |
| `--webpack`                              | Use Webpack instead of the default [Turbopack](/docs/app/api-reference/turbopack) bundler for development.                                           |
| `-p` or `--port `                  | Specify a port number on which to start the application. Default: 3000, env: PORT                                                                    |
| `-H`or `--hostname `           | Specify a hostname on which to start the application. Useful for making the application available for other devices on the network. Default: 0.0.0.0 |
| `--experimental-https`                   | Starts the server with HTTPS and generates a self-signed certificate.                                                                                |
| `--experimental-https-key `        | Path to a HTTPS key file.                                                                                                                            |
| `--experimental-https-cert `       | Path to a HTTPS certificate file.                                                                                                                    |
| `--experimental-https-ca `         | Path to a HTTPS certificate authority file.                                                                                                          |
| `--experimental-upload-trace ` | Reports a subset of the debugging trace to a remote HTTP URL.                                                                                        |
| `--experimental-cpu-prof`                | Enables CPU profiling using V8's inspector. Profiles are saved to `.next/cpu-profiles/` on exit.                                                     |

### `next build` options

`next build` creates an optimized production build of your application. The output displays information about each route. For example:

```bash filename="Terminal"
Route (app)
┌ ○ /_not-found
└ ƒ /products/[id]

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```

The following options are available for the `next build` command:

| Option                             | Description                                                                                                                                                                        |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-h, --help`                       | Show all available options.                                                                                                                                                        |
| `[directory]`                      | A directory on which to build the application. If not provided, the current directory will be used.                                                                                |
| `--turbopack`                      | Force enable [Turbopack](/docs/app/api-reference/turbopack) (enabled by default). Also available as `--turbo`.                                                                     |
| `--webpack`                        | Build using Webpack.                                                                                                                                                               |
| `-d` or `--debug`                  | Enables a more verbose build output. With this flag enabled additional build output like rewrites, redirects, and headers will be shown.                                           |
|                                    |
| `--profile`                        | Enables production [profiling for React](https://react.dev/reference/react/Profiler).                                                                                              |
| `--no-lint`                        | Disables linting. *Note: linting will be removed from `next build` in Next 16. If you're using Next 15.5+ with a linter other than `eslint`, linting during build will not occur.* |
| `--no-mangling`                    | Disables [mangling](https://en.wikipedia.org/wiki/Name_mangling). This may affect performance and should only be used for debugging purposes.                                      |
| `--experimental-app-only`          | Builds only App Router routes.                                                                                                                                                     |
| `--experimental-build-mode [mode]` | Uses an experimental build mode. (choices: "compile", "generate", default: "default")                                                                                              |
| `--debug-prerender`                | Debug prerender errors in development.                                                                                                                                             |
| `--debug-build-paths=`   | Build only specific routes for debugging.                                                                                                                                          |
| `--experimental-cpu-prof`          | Enables CPU profiling using V8's inspector. Profiles are saved to `.next/cpu-profiles/` on exit.                                                                                   |

### `next start` options

`next start` starts the application in production mode. The application should be compiled with [`next build`](#next-build-options) first.

The following options are available for the `next start` command:

| Option                                  | Description                                                                                                     |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `-h` or `--help`                        | Show all available options.                                                                                     |
| `[directory]`                           | A directory on which to start the application. If no directory is provided, the current directory will be used. |
| `-p` or `--port `                 | Specify a port number on which to start the application. (default: 3000, env: PORT)                             |
| `-H` or `--hostname `         | Specify a hostname on which to start the application (default: 0.0.0.0).                                        |
| `--keepAliveTimeout ` | Specify the maximum amount of milliseconds to wait before closing the inactive connections.                     |
| `--experimental-cpu-prof`               | Enables CPU profiling using V8's inspector. Profiles are saved to `.next/cpu-profiles/` on exit.                |

### `next info` options

`next info` prints relevant details about the current system which can be used to report Next.js bugs when opening a [GitHub issue](https://github.com/vercel/next.js/issues). This information includes Operating System platform/arch/version, Binaries (Node.js, npm, Yarn, pnpm), package versions (`next`, `react`, `react-dom`), and more.

The output should look like this:

```bash filename="Terminal"
Operating System:
  Platform: darwin
  Arch: arm64
  Version: Darwin Kernel Version 23.6.0
  Available memory (MB): 65536
  Available CPU cores: 10
Binaries:
  Node: 20.12.0
  npm: 10.5.0
  Yarn: 1.22.19
  pnpm: 9.6.0
Relevant Packages:
  next: 15.0.0-canary.115 // Latest available version is detected (15.0.0-canary.115).
  eslint-config-next: 14.2.5
  react: 19.0.0-rc
  react-dom: 19.0.0
  typescript: 5.5.4
Next.js Config:
  output: N/A
```

The following options are available for the `next info` command:

| Option           | Description                                    |
| ---------------- | ---------------------------------------------- |
| `-h` or `--help` | Show all available options                     |
| `--verbose`      | Collects additional information for debugging. |

### `next telemetry` options

Next.js collects **completely anonymous** telemetry data about general usage. Participation in this anonymous program is optional, and you can opt-out if you prefer not to share information.

The following options are available for the `next telemetry` command:

| Option       | Description                             |
| ------------ | --------------------------------------- |
| `-h, --help` | Show all available options.             |
| `--enable`   | Enables Next.js' telemetry collection.  |
| `--disable`  | Disables Next.js' telemetry collection. |

Learn more about [Telemetry](/telemetry).

### `next typegen` options

`next typegen` generates TypeScript definitions for your application's routes without performing a full build. This is useful for IDE autocomplete and CI type-checking of route usage.

Previously, route types were only generated during `next dev` or `next build`, which meant running `tsc --noEmit` directly wouldn't validate your route types. Now you can generate types independently and validate them externally:

```bash filename="Terminal"
# Generate route types first, then validate with TypeScript
next typegen && tsc --noEmit

# Or in CI workflows for type checking without building
next typegen && npm run type-check
```

The following options are available for the `next typegen` command:

| Option        | Description                                                                                  |
| ------------- | -------------------------------------------------------------------------------------------- |
| `-h, --help`  | Show all available options.                                                                  |
| `[directory]` | A directory on which to generate types. If not provided, the current directory will be used. |

Output files are written to `/types` (typically: `.next/dev/types` in development or `.next/types` in production):

```bash filename="Terminal"
next typegen
# or for a specific app
next typegen ./apps/web
```

Additionally, `next typegen` generates a `next-env.d.ts` file. We recommend adding `next-env.d.ts` to your `.gitignore` file.

The `next-env.d.ts` file is included into your `tsconfig.json` file, to make Next.js types available to your project.

To ensure `next-env.d.ts` is present before type-checking run `next typegen`. The commands `next dev` and `next build` also generate the `next-env.d.ts` file, but it is often undesirable to run these just to type-check, for example in CI/CD environments.

> **Good to know**: `next typegen` loads your Next.js config (`next.config.js`, `next.config.mjs`, or `next.config.ts`) using the production build phase. Ensure any required environment variables and dependencies are available so the config can load correctly.

### `next upgrade` options

`next upgrade` upgrades your Next.js application to the latest version.

The following options are available for the `next upgrade` command:

| Option                  | Description                                                                                                                                        |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-h, --help`            | Show all available options.                                                                                                                        |
| `[directory]`           | A directory with the Next.js application to upgrade. If not provided, the current directory will be used.                                          |
| `--revision ` | Specify a Next.js version or tag to upgrade to (e.g., `latest`, `canary`, `15.0.0`). Defaults to the release channel you have currently installed. |
| `--verbose`             | Show verbose output during the upgrade process.                                                                                                    |

### `next experimental-analyze` options

`next experimental-analyze` analyzes your application's bundle output using [Turbopack](/docs/app/api-reference/turbopack). This command helps you understand the size and composition of your bundles, including JavaScript, CSS, and other assets. This command doesn't produce an application build.

```bash package="pnpm"
pnpm next experimental-analyze
```

```bash package="npm"
npx next experimental-analyze
```

```bash package="yarn"
yarn next experimental-analyze
```

```bash package="bun"
bunx next experimental-analyze
```

By default, the command starts a local server after analysis completes, allowing you to explore your bundle composition in the browser. The analyzer lets you:

* Filter bundles by route and switch between client and server views
* View the full import chain showing why a module is included
* Trace imports across server-to-client component boundaries and dynamic imports

See [Package Bundling](/docs/app/guides/package-bundling#optimizing-large-bundles) for optimization strategies.

To write the analysis output to disk without starting the server, use the `--output` flag. The output is written to `.next/diagnostics/analyze` and contains static files that can be copied elsewhere or shared with others:

```bash filename="Terminal"
# Write output to .next/diagnostics/analyze
npx next experimental-analyze --output

# Copy the output for comparison with a future analysis
cp -r .next/diagnostics/analyze ./analyze-before-refactor
```

The following options are available for the `next experimental-analyze` command:

| Option          | Description                                                                                                                                   |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `-h, --help`    | Show all available options.                                                                                                                   |
| `[directory]`   | A directory on which to analyze the application. If not provided, the current directory will be used.                                         |
| `--no-mangling` | Disables [mangling](https://en.wikipedia.org/wiki/Name_mangling). This may affect performance and should only be used for debugging purposes. |
| `--profile`     | Enables production [profiling for React](https://react.dev/reference/react/Profiler). This may affect performance.                            |
| `-o, --output`  | Write analysis files to disk without starting the server. Output is written to `.next/diagnostics/analyze`.                                   |
| `--port ` | Specify a port number to serve the analyzer on. (default: 4000, env: PORT)                                                                    |

## Examples

### Debugging prerender errors

If you encounter prerendering errors during `next build`, you can pass the `--debug-prerender` flag to get more detailed output:

```bash filename="Terminal"
next build --debug-prerender
```

This enables several experimental options to make debugging easier:

* Disables server code minification:
  * `experimental.serverMinification = false`
  * `experimental.turbopackMinify = false`
* Generates source maps for server bundles:
  * `experimental.serverSourceMaps = true`
* Enables source map consumption in child processes used for prerendering:
  * `enablePrerenderSourceMaps = true`
* Continues building even after the first prerender error, so you can see all issues at once:
  * `experimental.prerenderEarlyExit = false`

This helps surface more readable stack traces and code frames in the build output.

> **Warning**: `--debug-prerender` is for debugging in development only. Do not deploy builds generated with `--debug-prerender` to production, as it may impact performance.

### Building specific routes

You can build only specific routes in the App and Pages Routers using the `--debug-build-paths` option. This is useful for faster debugging when working with large applications. The `--debug-build-paths` option accepts comma-separated file paths and supports glob patterns:

```bash filename="Terminal"
# Build a specific route
next build --debug-build-paths="app/page.tsx"

# Build more than one route
next build --debug-build-paths="app/page.tsx,pages/index.tsx"

# Include route group folders in the path
next build --debug-build-paths="app/(marketing)/about/page.tsx"

# Use glob patterns
next build --debug-build-paths="app/**/page.tsx"
next build --debug-build-paths="pages/*.tsx"
```

### Changing the default port

By default, Next.js uses `http://localhost:3000` during development and with `next start`. The default port can be changed with the `-p` option, like so:

```bash filename="Terminal"
next dev -p 4000
```

Or using the `PORT` environment variable:

```bash filename="Terminal"
PORT=4000 next dev
```

> **Good to know**: `PORT` cannot be set in `.env` as booting up the HTTP server happens before any other code is initialized.

### Using HTTPS during development

For certain use cases like webhooks or authentication, you can use [HTTPS](https://developer.mozilla.org/en-US/docs/Glossary/HTTPS) to have a secure environment on `localhost`. Next.js can generate a self-signed certificate with `next dev` using the `--experimental-https` flag:

```bash filename="Terminal"
next dev --experimental-https
```

With the generated certificate, the Next.js development server will exist at `https://localhost:3000`. The default port `3000` is used unless a port is specified with `-p`, `--port`, or `PORT`.

You can also provide a custom certificate and key with `--experimental-https-key` and `--experimental-https-cert`. Optionally, you can provide a custom CA certificate with `--experimental-https-ca` as well.

```bash filename="Terminal"
next dev --experimental-https --experimental-https-key ./certificates/localhost-key.pem --experimental-https-cert ./certificates/localhost.pem
```

`next dev --experimental-https` is only intended for development and creates a locally trusted certificate with [`mkcert`](https://github.com/FiloSottile/mkcert). In production, use properly issued certificates from trusted authorities.

### Configuring a timeout for downstream proxies

When deploying Next.js behind a downstream proxy (e.g. a load-balancer like AWS ELB/ALB), it's important to configure Next's underlying HTTP server with [keep-alive timeouts](https://nodejs.org/api/http.html#http_server_keepalivetimeout) that are *larger* than the downstream proxy's timeouts. Otherwise, once a keep-alive timeout is reached for a given TCP connection, Node.js will immediately terminate that connection without notifying the downstream proxy. This results in a proxy error whenever it attempts to reuse a connection that Node.js has already terminated.

To configure the timeout values for the production Next.js server, pass `--keepAliveTimeout` (in milliseconds) to `next start`, like so:

```bash filename="Terminal"
next start --keepAliveTimeout 70000
```

### Passing Node.js arguments

You can pass any [node arguments](https://nodejs.org/api/cli.html#cli_node_options_options) to `next` commands. For example:

```bash filename="Terminal"
NODE_OPTIONS='--throw-deprecation' next
NODE_OPTIONS='-r esm' next
NODE_OPTIONS='--inspect' next
```

### CPU profiling

You can capture CPU profiles to analyze performance bottlenecks in your Next.js application. The `--experimental-cpu-prof` flag enables V8's built-in CPU profiler and saves profiles to `.next/cpu-profiles/` when the process exits:

```bash filename="Terminal"
# Profile the build process
next build --experimental-cpu-prof

# Profile the dev server (profile saved on Ctrl+C or SIGTERM)
next dev --experimental-cpu-prof

# Profile the production server
next start --experimental-cpu-prof
```

The generated `.cpuprofile` files can be opened in Chrome DevTools (Performance tab → Load profile) or other V8-compatible profiling tools.

> **Good to know**: Profile files are named with a descriptive prefix and timestamp. The profiles generated depend on the command:
>
> **`next dev`:**
>
> * `dev-main-*` - Parent process (dev server orchestration)
> * `dev-server-*` - Child server process (request handling and rendering) - this is typically what you want to analyze
>
> **`next build` (Turbopack):**
>
> * `build-main-*` - Main build orchestration process
> * `build-turbopack-*` - Turbopack compilation worker
>
> **`next build` (Webpack):**
>
> * `build-main-*` - Main build orchestration process
> * `build-webpack-client-*` - Client bundle compilation worker
> * `build-webpack-server-*` - Server bundle compilation worker
> * `build-webpack-edge-server-*` - Edge runtime compilation worker
>
> **`next start`:**
>
> * `start-main-*` - Production server process

| Version   | Changes                                                                         |
| --------- | ------------------------------------------------------------------------------- |
| `v16.1.0` | Add the `next upgrade` command                                                  |
| `v16.1.0` | Add the `next experimental-analyze` command                                     |
| `v16.0.0` | The JS bundle size metrics have been removed from `next build`                  |
| `v15.5.0` | Add the `next typegen` command                                                  |
| `v15.4.0` | Add `--debug-prerender` option for `next build` to help debug prerender errors. |

---
title: Adapters
description: Build deployment adapters for Next.js platforms and infrastructure.
url: "https://nextjs.org/docs/pages/api-reference/adapters"
version: 16.2.6
router: Pages Router
---

# Adapters

Use this section to build and validate deployment adapters that integrate with the Next.js build and runtime model.

* [Configuration](/docs/app/api-reference/adapters/configuration)
* [Creating an Adapter](/docs/app/api-reference/adapters/creating-an-adapter)
* [API Reference](/docs/app/api-reference/adapters/api-reference)
* [Testing Adapters](/docs/app/api-reference/adapters/testing-adapters)
* [Routing with `@next/routing`](/docs/app/api-reference/adapters/routing-with-next-routing)
* [Implementing PPR in an Adapter](/docs/app/api-reference/adapters/implementing-ppr-in-an-adapter)
* [Runtime Integration](/docs/app/api-reference/adapters/runtime-integration)
* [Invoking Entrypoints](/docs/app/api-reference/adapters/invoking-entrypoints)
* [Output Types](/docs/app/api-reference/adapters/output-types)
* [Routing Information](/docs/app/api-reference/adapters/routing-information)
* [Use Cases](/docs/app/api-reference/adapters/use-cases)

 - [Configuration](/docs/pages/api-reference/adapters/configuration)
 - [Creating an Adapter](/docs/pages/api-reference/adapters/creating-an-adapter)
 - [API Reference](/docs/pages/api-reference/adapters/api-reference)
 - [Testing Adapters](/docs/pages/api-reference/adapters/testing-adapters)
 - [Routing with @next/routing](/docs/pages/api-reference/adapters/routing-with-next-routing)
 - [Implementing PPR in an Adapter](/docs/pages/api-reference/adapters/implementing-ppr-in-an-adapter)
 - [Runtime Integration](/docs/pages/api-reference/adapters/runtime-integration)
 - [Invoking Entrypoints](/docs/pages/api-reference/adapters/invoking-entrypoints)
 - [Output Types](/docs/pages/api-reference/adapters/output-types)
 - [Routing Information](/docs/pages/api-reference/adapters/routing-information)
 - [Use Cases](/docs/pages/api-reference/adapters/use-cases)

---
title: Configuration
description: "Configure `adapterPath` or `NEXT_ADAPTER_PATH` to use a custom deployment adapter."
url: "https://nextjs.org/docs/pages/api-reference/adapters/configuration"
version: 16.2.6
router: Pages Router
---

# Configuration

To use an adapter, specify the path to your adapter module in `adapterPath`:

```js filename="next.config.js"
/** @type {import('next').NextConfig} */
const nextConfig = {
  adapterPath: require.resolve('./my-adapter.js'),
}

module.exports = nextConfig
```

Alternatively `NEXT_ADAPTER_PATH` can be set to enable zero-config usage in deployment platforms.

---
title: Creating an Adapter
description: "Create an adapter module that implements the `NextAdapter` interface."
url: "https://nextjs.org/docs/pages/api-reference/adapters/creating-an-adapter"
version: 16.2.6
router: Pages Router
---

# Creating an Adapter

An adapter is a module that exports an object implementing the `NextAdapter` interface.

The interface can be imported from the `next` package:

```typescript
import type { NextAdapter } from 'next'
```

The interface is defined as follows:

```typescript
type Route = {
  source?: string
  sourceRegex: string
  destination?: string
  headers?: Record
  has?: RouteHas[]
  missing?: RouteHas[]
  status?: number
  priority?: boolean
}

export interface AdapterOutputs {
  pages: Array
  middleware?: AdapterOutput['MIDDLEWARE']
  appPages: Array
  pagesApi: Array
  appRoutes: Array
  prerenders: Array
  staticFiles: Array
}

export interface NextAdapter {
  name: string
  modifyConfig?: (
    config: NextConfigComplete,
    ctx: {
      phase: PHASE_TYPE
      nextVersion: string
    }
  ) => Promise | NextConfigComplete
  onBuildComplete?: (ctx: {
    routing: {
      beforeMiddleware: Array
      beforeFiles: Array
      afterFiles: Array
      dynamicRoutes: Array
      onMatch: Array
      fallback: Array
      shouldNormalizeNextData: boolean
      rsc: RoutesManifest['rsc']
    }
    outputs: AdapterOutputs
    projectDir: string
    repoRoot: string
    distDir: string
    config: NextConfigComplete
    nextVersion: string
    buildId: string
  }) => Promise | void
}
```

## Basic Adapter Structure

Here's a minimal adapter example:

```js filename="my-adapter.js"
/** @type {import('next').NextAdapter} */
const adapter = {
  name: 'my-custom-adapter',

  async modifyConfig(config, { phase }) {
    // Modify the Next.js config based on the build phase
    if (phase === 'phase-production-build') {
      return {
        ...config,
        // Add your modifications
      }
    }
    return config
  },

  async onBuildComplete({
    routing,
    outputs,
    projectDir,
    repoRoot,
    distDir,
    config,
    nextVersion,
    buildId,
  }) {
    // Process the build output
    console.log('Build completed with', outputs.pages.length, 'pages')
    console.log('Build ID:', buildId)
    console.log('Dynamic routes:', routing.dynamicRoutes.length)

    // Access emitted output entries
    for (const page of outputs.pages) {
      console.log('Page:', page.pathname, 'at', page.filePath)
    }

    for (const apiRoute of outputs.pagesApi) {
      console.log('API Route:', apiRoute.pathname, 'at', apiRoute.filePath)
    }

    for (const appPage of outputs.appPages) {
      console.log('App Page:', appPage.pathname, 'at', appPage.filePath)
    }

    for (const prerender of outputs.prerenders) {
      console.log('Prerendered:', prerender.pathname)
    }
  },
}

module.exports = adapter
```

---
title: API Reference
description: "Reference for `modifyConfig` and `onBuildComplete` in the `NextAdapter` interface."
url: "https://nextjs.org/docs/pages/api-reference/adapters/api-reference"
version: 16.2.6
router: Pages Router
---

# API Reference

## `async modifyConfig(config, context)`

Called for any CLI command that loads the `next.config.js` file to allow modification of the configuration.

**Parameters:**

* `config`: The complete Next.js configuration object
* `context.phase`: The current build phase (see [phases](/docs/app/api-reference/config/next-config-js#phase))
* `context.nextVersion`: Version of Next.js being used

**Returns:** The modified configuration object (can be async)

## `async onBuildComplete(context)`

Called after the build process completes with detailed information about routes and outputs.

**Parameters:**

* `context.routing`: Object containing Next.js routing phases and metadata
  * `routing.beforeMiddleware`: Routes executed before middleware (includes header and redirect handling)
  * `routing.beforeFiles`: Rewrite routes checked before filesystem route matching
  * `routing.afterFiles`: Rewrite routes checked after filesystem route matching
  * `routing.dynamicRoutes`: Dynamic route matching table
  * `routing.onMatch`: Routes applied after a successful match (for example immutable static asset cache headers)
  * `routing.fallback`: Final rewrite fallback routes
  * `routing.shouldNormalizeNextData`: Whether `/_next/data//...` URLs should be normalized during matching
  * `routing.rsc`: Route metadata used for React Server Components routing behavior
* `context.outputs`: Detailed information about all build outputs organized by type
* `context.projectDir`: Absolute path to the Next.js project directory
* `context.repoRoot`: Absolute path to the detected repository root
* `context.distDir`: Absolute path to the build output directory
* `context.config`: The final Next.js configuration (with `modifyConfig` applied)
* `context.nextVersion`: Version of Next.js being used
* `context.buildId`: Unique identifier for the current build

---
title: Testing Adapters
description: Validate adapters with the Next.js compatibility test harness and custom lifecycle scripts.
url: "https://nextjs.org/docs/pages/api-reference/adapters/testing-adapters"
version: 16.2.6
router: Pages Router
---

# Testing Adapters

Next.js provides a test harness for validating adapters. Running the end-to-end tests for deployment.

Example GitHub Actions workflow:

```yaml filename=".github/workflows/test-e2e-deploy.yml"
name: test-e2e-deploy

on:
  workflow_dispatch:
    inputs:
      nextjsRef:
        description: 'Next.js repo ref (branch/tag/SHA)'
        default: 'canary'
        type: string
  # schedule:
  #   - cron: '0 2 * * *'

jobs:
  build:
    name: Build Next.js + adapter
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with:
          path: adapter

      - uses: actions/checkout@v4
        with:
          repository: vercel/next.js
          ref: ${{ inputs.nextjsRef || 'canary' }}
          path: nextjs
          fetch-depth: 25

      - uses: actions/setup-node@v4
        with: { node-version: '20' }

      - name: Setup pnpm
        run: npm i -g corepack@0.31 && corepack enable

      - name: Install & build Next.js
        working-directory: nextjs
        run: pnpm install && pnpm build && pnpm install

      - name: Install Playwright
        working-directory: nextjs
        run: pnpm playwright install --with-deps chromium

      - name: Build adapter
        working-directory: adapter
        run: pnpm install && pnpm build

      - uses: actions/cache/save@v4
        with:
          path: |
            nextjs
            adapter
            ~/.cache/ms-playwright
          key: build-${{ github.sha }}-${{ github.run_id }}

  test:
    name: Tests (${{ matrix.group }})
    needs: build
    runs-on: ubuntu-latest
    timeout-minutes: 60
    strategy:
      fail-fast: false
      matrix:
        group:
          [
            1/16,
            2/16,
            3/16,
            4/16,
            5/16,
            6/16,
            7/16,
            8/16,
            9/16,
            10/16,
            11/16,
            12/16,
            13/16,
            14/16,
            15/16,
            16/16,
          ]
    steps:
      - uses: actions/cache/restore@v4
        with:
          path: |
            nextjs
            adapter
            ~/.cache/ms-playwright
          key: build-${{ github.sha }}-${{ github.run_id }}

      - uses: actions/setup-node@v4
        with: { node-version: '20' }

      - name: Setup pnpm
        run: npm i -g corepack@0.31 && corepack enable

      - name: Ensure Playwright browser
        working-directory: nextjs
        run: pnpm playwright install chromium

      - name: Make scripts executable
        run: chmod +x adapter/scripts/e2e-deploy.sh
          adapter/scripts/e2e-logs.sh
          adapter/scripts/e2e-cleanup.sh

      - name: Run deploy tests
        working-directory: nextjs
        env:
          NEXT_TEST_MODE: deploy
          NEXT_E2E_TEST_TIMEOUT: 240000
          NEXT_EXTERNAL_TESTS_FILTERS: test/deploy-tests-manifest.json
          ADAPTER_DIR: ${{ github.workspace }}/adapter
          IS_TURBOPACK_TEST: 1
          NEXT_TEST_JOB: 1
          NEXT_TELEMETRY_DISABLED: 1

          # Change these to your adapter's scripts
          # Keep as-is if the scripts are in the adapter repository `scripts` directory
          NEXT_TEST_DEPLOY_SCRIPT_PATH: ${{ github.workspace }}/adapter/scripts/e2e-deploy.sh
          NEXT_TEST_DEPLOY_LOGS_SCRIPT_PATH: ${{ github.workspace }}/adapter/scripts/e2e-logs.sh
          NEXT_TEST_CLEANUP_SCRIPT_PATH: ${{ github.workspace }}/adapter/scripts/e2e-cleanup.sh
        run: node run-tests.js --timings -g ${{ matrix.group }} -c 2 --type e2e
```

The test harness looks for these environment variables:

* `NEXT_TEST_DEPLOY_SCRIPT_PATH`: Path to the executable that builds and deploys the isolated test app
* `NEXT_TEST_DEPLOY_LOGS_SCRIPT_PATH`: Path to the executable that returns build and runtime logs for that deployment
* `NEXT_TEST_CLEANUP_SCRIPT_PATH`: Path to the optional executable that tears the deployment down after the test run

## Custom deploy script contract

The deploy script `NEXT_TEST_DEPLOY_SCRIPT_PATH` is executed with `cwd` set to the isolated temporary app created by the Next.js test harness.

The deploy script must follow this contract:

* Exit with a non-zero code on failure.
* Print the deployment URL to `stdout`. This will be used to verify the deployment. Avoid writing anything else to `stdout`.
* Write diagnostic output to `stderr` or to files inside the working directory.

Because the deploy script and logs script run as separate processes, any data you want to use later, such as build IDs or server logs, should be persisted to files inside the working directory.

Example deploy script:

```bash filename="scripts/e2e-deploy.sh"
#!/usr/bin/env bash
set -euo pipefail

# Install the adapter, build the app, and deploy or start it.
node -e "
const pkg=JSON.parse(require('fs').readFileSync('package.json','utf8'));
pkg.dependencies=pkg.dependencies||{};
pkg.dependencies['adapter']='file:${ADAPTER_DIR}';
require('fs').writeFileSync('package.json',JSON.stringify(pkg,null,2));
" >&2

# Set the adapter path so that the app uses it.
export NEXT_ADAPTER_PATH="${ADAPTER_DIR}/dist/index.js"

# Build the app
pnpm build

# Write any metadata needed later to files in the working directory.
BUILD_ID="$(cat .next/BUILD_ID)"
DEPLOYMENT_ID="my-adapter-local"
# If your adapter generates an immutable asset token, set it here.
# Otherwise use "undefined" to indicate there is none.
IMMUTABLE_ASSET_TOKEN="undefined"

{
  echo "BUILD_ID: $BUILD_ID"
  echo "DEPLOYMENT_ID: $DEPLOYMENT_ID"
  echo "IMMUTABLE_ASSET_TOKEN: $IMMUTABLE_ASSET_TOKEN"
} >> .adapter-build.log

# Start or deploy the app. Capture the URL at this point or make the script output the URL to stdout.
provider-cli-to-deploy

# Example URL output:
# echo "http://127.0.0.1:3000"
```

## Custom logs script contract

The logs script `NEXT_TEST_DEPLOY_LOGS_SCRIPT_PATH` is executed with `cwd` set to the isolated temporary app created by the Next.js test harness.

Additionally it receives `NEXT_TEST_DIR` and `NEXT_TEST_DEPLOY_URL` as environment variables.

Its output must include lines starting with:

* `BUILD_ID:`
* `DEPLOYMENT_ID:`
* `IMMUTABLE_ASSET_TOKEN:` (use the value `undefined` if your adapter does not produce one)

After those markers, the logs script can print any additional build or server logs that would help debug failures.

```bash filename="scripts/e2e-logs.sh"
#!/usr/bin/env bash
set -euo pipefail

if [ -f ".adapter-build.log" ]; then
  cat ".adapter-build.log"
fi

if [ -f ".adapter-server.log" ]; then
  echo "=== .adapter-server.log ==="
  cat ".adapter-server.log"
fi
```

One pattern is to have the deploy script write `.adapter-build.log` and `.adapter-server.log`, then have the logs script replay those files so the harness can extract the required markers. This is one option, each platform has different ways to get the logs.

## Custom cleanup script contract

The cleanup script `NEXT_TEST_CLEANUP_SCRIPT_PATH` is executed with `cwd` set to the isolated temporary app created by the Next.js test harness.

Additionally it receives `NEXT_TEST_DIR` and `NEXT_TEST_DEPLOY_URL` as environment variables.

The cleanup script can be used to clean up any resources created by the deploy script. It runs after the tests have completed.

---
title: "Routing with @next/routing"
description: "Use `@next/routing` to apply Next.js route matching behavior in adapters."
url: "https://nextjs.org/docs/pages/api-reference/adapters/routing-with-next-routing"
version: 16.2.6
router: Pages Router
---

# Routing with @next/routing

You can use [`@next/routing`](https://www.npmjs.com/package/@next/routing) to reproduce Next.js route matching behavior with data from `onBuildComplete`.

> \[!NOTE]
> `@next/routing` is experimental and will stabilize with the adapters API.

```typescript
import { resolveRoutes } from '@next/routing'

const pathnames = [
  ...outputs.pages,
  ...outputs.pagesApi,
  ...outputs.appPages,
  ...outputs.appRoutes,
  ...outputs.staticFiles,
].map((output) => output.pathname)

const result = await resolveRoutes({
  url: new URL(requestUrl),
  buildId,
  basePath: config.basePath || '',
  i18n: config.i18n,
  headers: new Headers(requestHeaders),
  requestBody, // ReadableStream
  pathnames,
  routes: routing,
  invokeMiddleware: async (ctx) => {
    // platform-specific middleware invocation
    return {}
  },
})

if (result.resolvedPathname) {
  console.log('Resolved pathname:', result.resolvedPathname)
  console.log('Resolved query:', result.resolvedQuery)
  console.log('Invocation target:', result.invocationTarget)
}
```

`resolveRoutes()` returns:

* `middlewareResponded`: `true` when middleware already sent a response (the adapter should not invoke an entrypoint).
* `externalRewrite`: A `URL` when routing resolved to an external rewrite destination.
* `redirect`: An object with `url` (`URL`) and `status` when the request should be redirected.
* `resolvedPathname`: The route pathname selected by Next.js routing. For dynamic routes, this is the matched route template such as `/blog/[slug]`.
* `resolvedQuery`: The final query after rewrites or middleware have added or replaced search params.
* `invocationTarget`: The concrete pathname and query to invoke for the matched route.
* `resolvedHeaders`: A `Headers` object containing any headers added or modified during routing.
* `status`: An HTTP status code set by routing (for example from a redirect or rewrite rule).
* `routeMatches`: A record of named matches extracted from dynamic route segments.

For example, if `/blog/post-1?draft=1` matches `/blog/[slug]?slug=post-1`, `resolvedPathname` is `/blog/[slug]` while `invocationTarget.pathname` is `/blog/post-1`.

---
title: Implementing PPR in an Adapter
description: Implement Partial Prerendering support in an adapter using fallback output and cache hooks.
url: "https://nextjs.org/docs/pages/api-reference/adapters/implementing-ppr-in-an-adapter"
version: 16.2.6
router: Pages Router
---

# Implementing PPR in an Adapter

For partially prerendered app routes, `onBuildComplete` gives you the data needed to seed and resume PPR:

* `outputs.prerenders[].fallback.filePath`: path to the generated fallback shell (for example HTML)
* `outputs.prerenders[].fallback.postponedState`: serialized postponed state used to resume rendering

## 1. Seed shell + postponed state at build time

```ts filename="my-adapter.ts"
import { readFile } from 'node:fs/promises'

async function seedPprEntries(outputs: AdapterOutputs) {
  for (const prerender of outputs.prerenders) {
    const fallback = prerender.fallback
    if (!fallback?.filePath || !fallback.postponedState) continue

    const shell = await readFile(fallback.filePath, 'utf8')
    await platformCache.set(prerender.pathname, {
      shell,
      postponedState: fallback.postponedState,
      initialHeaders: fallback.initialHeaders,
      initialStatus: fallback.initialStatus,
      initialRevalidate: fallback.initialRevalidate,
      initialExpiration: fallback.initialExpiration,
    })
  }
}
```

## 2. Runtime flow: serve cached shell and resume in background

At request time, you can stream a single response that is the concatenation of:

1. cached HTML shell stream
2. resumed render stream (generated after invoking `handler` with postponed state)

```text
Client
  | GET /ppr-route
  v
Adapter Router
  |
  |-- read cached shell + postponedState ---> Platform Cache
  | Client (first bytes)
  |
  |-- invoke handler(req, res, { requestMeta: { postponed } })
  |   -------------------------------------> Entrypoint (handler)
  |    \[!NOTE]
>
> * `requestMeta.onCacheEntry` still works, but is deprecated.
> * Prefer `requestMeta.onCacheEntryV2`.
> * If your adapter uses an internal `onCacheCallback` abstraction, wire it to `requestMeta.onCacheEntryV2`.

```ts filename="my-adapter.ts"
await handler(req, res, {
  waitUntil,
  requestMeta: {
    postponed: cachedPprEntry?.postponedState,
    onCacheEntryV2: async (cacheEntry, meta) => {
      if (cacheEntry.value?.kind === 'APP_PAGE') {
        const html =
          cacheEntry.value.html &&
          typeof cacheEntry.value.html.toUnchunkedString === 'function'
            ? cacheEntry.value.html.toUnchunkedString()
            : null

        await platformCache.set(meta.url || req.url || '/', {
          shell: html,
          postponedState: cacheEntry.value.postponed,
          headers: cacheEntry.value.headers,
          status: cacheEntry.value.status,
          cacheControl: cacheEntry.cacheControl,
        })
      }

      // Return true only if your adapter already wrote the response itself.
      return false
    },
  },
})
```

```text
Entrypoint (handler)
  | onCacheEntryV2(cacheEntry, { url })
  v
requestMeta.onCacheEntryV2 callback
  |
  |-- if APP_PAGE ---> persist html + postponedState + headers ---> Platform Cache
  |
  '-- return false: continue normal Next.js response flow
      return true:  adapter already handled response (short-circuit)
```

---
title: Runtime Integration
description: Understand how build-time adapters and runtime cache interfaces work together.
url: "https://nextjs.org/docs/pages/api-reference/adapters/runtime-integration"
version: 16.2.6
router: Pages Router
---

# Runtime Integration

The Deployment Adapter API is a **build-time** interface. It tells your platform what was built and how to route requests. **Runtime** behavior (request handling, streaming, caching) is handled by the Next.js server itself and by the cache interfaces [`cacheHandler`](/docs/app/api-reference/config/next-config-js/incrementalCacheHandlerPath) and [`cacheHandlers`](/docs/app/api-reference/config/next-config-js/cacheHandlers).

Together, the adapter and cache interfaces form the complete platform integration surface:

* **Adapter** (build-time): processes build outputs, configures routing, and sets up platform-specific infrastructure.
* **Cache Interfaces** (runtime): `cacheHandler` manages ISR/server cache storage and revalidation across instances; `cacheHandlers` configures `'use cache'` directive backends and tag coordination.

## Handler Context

When invoking entrypoints, adapters pass a `ctx` object to the Next.js handler. Key fields include:

* **`ctx.waitUntil`**: a function that accepts a promise. Use this to keep the serverless function alive after the response is sent, allowing background work like cache revalidation to complete.
* **`requestMeta.onCacheEntryV2`** (set via `addRequestMeta`): a callback that fires when a cache entry is generated or looked up. Use this to observe all cache operations (not just PPR) and propagate cache updates to your platform's storage backend. This callback fires on the instance that handled the request. For multi-instance deployments, your adapter should propagate updates to shared storage. See [How Revalidation Works](/docs/app/guides/how-revalidation-works) for coordination patterns.

## PPR Chain Headers

In the [prerenders output type](/docs/app/api-reference/adapters/output-types#prerenders-outputsprerenders), `pprChain.headers` contains the headers needed for the [resume protocol](/docs/app/api-reference/adapters/implementing-ppr-in-an-adapter). Specifically, it contains `{ 'next-resume': '1' }`.

When your adapter detects a PPR-enabled route with a cached static shell:

1. Set the `pprChain.headers` on the internal request to the Next.js handler.
2. Send the request as a **POST** with the `postponedState` as the request body.
3. The handler will render only the deferred Suspense boundaries and stream the result.

> **Good to know:** In standard `next start`, the server handles both the shell and dynamic render in a single pass automatically. The resume protocol is useful for adapter-based deployments and CDN-to-origin architectures that want to serve the shell separately. See the [PPR Platform Guide](/docs/app/guides/ppr-platform-guide) for the full implementation context.

---
title: Invoking Entrypoints
description: Invoke Node.js and Edge build entrypoints with adapter runtime context.
url: "https://nextjs.org/docs/pages/api-reference/adapters/invoking-entrypoints"
version: 16.2.6
router: Pages Router
---

# Invoking Entrypoints

Build output entrypoints use a `handler(..., ctx)` interface, with runtime-specific request/response types.

## Node.js runtime (`runtime: 'nodejs'`)

Node.js entrypoints use the following interface:

```typescript
handler(
  req: IncomingMessage,
  res: ServerResponse,
  ctx: {
    waitUntil?: (promise: Promise) => void
    requestMeta?: RequestMeta
  }
): Promise
```

When invoking Node.js entrypoints directly, adapters can pass helpers directly on `requestMeta` instead of relying on internals. Some of the supported fields are `hostname`,
`revalidate`, and `render404`:

```ts
await handler(req, res, {
  requestMeta: {
    // Relative path from process.cwd() to the Next.js project directory.
    relativeProjectDir: '.',
    // Optional hostname used by route handlers when constructing absolute URLs.
    hostname: '127.0.0.1',
    // Optional internal revalidate function to avoid revalidating over the network
    revalidate: async ({ urlPath, headers, opts }) => {
      // platform-specific revalidate implementation
    },
    // Optional function to render the 404 page for pages router `notFound: true`
    render404: async (req, res, parsedUrl, setHeaders) => {
      // platform-specific 404 rendering implementation
    },
  },
})
```

Relevant files in the Next.js core:

* [`packages/next/src/build/templates/app-page.ts`](https://github.com/vercel/next.js/blob/canary/packages/next/src/build/templates/app-page.ts)
* [`packages/next/src/build/templates/app-route.ts`](https://github.com/vercel/next.js/blob/canary/packages/next/src/build/templates/app-route.ts)
* and [`packages/next/src/build/templates/pages-api.ts`](https://github.com/vercel/next.js/blob/canary/packages/next/src/build/templates/pages-api.ts)

## Edge runtime (`runtime: 'edge'`)

Edge entrypoints use the following interface:

```typescript
handler(
  request: Request,
  ctx: {
    waitUntil?: (prom: Promise) => void
    signal?: AbortSignal
    requestMeta?: RequestMeta
  }
): Promise
```

The shape is aligned around `handler(..., ctx)`, but Node.js and Edge runtimes use different request/response primitives.

For outputs with `runtime: 'edge'`, Next.js also provides `output.edgeRuntime` with the canonical metadata needed to invoke the entrypoint:

```typescript
{
  modulePath: string // Absolute path to the module registered in the edge runtime
  entryKey: string // Canonical key used by the edge entry registry
  handlerExport: string // Export name to invoke, currently 'handler'
}
```

After your edge runtime loads and evaluates the chunks for `modulePath`, use `entryKey` to read the registered entry from the global edge entry registry (`globalThis._ENTRIES`), then invoke `handlerExport` from that entry:

```ts
const entry = await globalThis._ENTRIES[output.edgeRuntime.entryKey]
const handler = entry[output.edgeRuntime.handlerExport]
await handler(request, ctx)
```

Use `edgeRuntime` instead of deriving registry keys or handler names from filenames.

Relevant files in the Next.js core:

* [`packages/next/src/build/templates/edge-ssr.ts`](https://github.com/vercel/next.js/blob/canary/packages/next/src/build/templates/edge-ssr.ts)
* [`packages/next/src/build/templates/edge-app-route.ts`](https://github.com/vercel/next.js/blob/canary/packages/next/src/build/templates/edge-app-route.ts)
* [`packages/next/src/build/templates/pages-edge-api.ts`](https://github.com/vercel/next.js/blob/canary/packages/next/src/build/templates/pages-edge-api.ts)
* and [`packages/next/src/build/templates/middleware.ts`](https://github.com/vercel/next.js/blob/canary/packages/next/src/build/templates/middleware.ts)

---
title: Output Types
description: Reference for all build output types exposed to adapters.
url: "https://nextjs.org/docs/pages/api-reference/adapters/output-types"
version: 16.2.6
router: Pages Router
---

# Output Types

The `outputs` object contains arrays of build output types:

* `outputs.pages`: React pages from the `pages/` directory
* `outputs.pagesApi`: API routes from `pages/api/`
* `outputs.appPages`: React pages from the `app/` directory
* `outputs.appRoutes`: API and metadata routes from `app/`
* `outputs.prerenders`: ISR-enabled routes and static prerenders
* `outputs.staticFiles`: Static assets and auto-statically optimized pages
* `outputs.middleware`: Middleware function (if present)

> **Note:** When `config.output` is set to `'export'`, only `outputs.staticFiles` is populated. All other arrays (`pages`, `appPages`, `pagesApi`, `appRoutes`, `prerenders`) will be empty since the entire application is exported as static files.

For any route output with `runtime: 'edge'`, `edgeRuntime` is included and contains the canonical entry metadata for invoking that output in your edge runtime.

## Pages (`outputs.pages`)

React pages from the `pages/` directory:

```typescript
{
  type: 'PAGES'
  id: string           // Route identifier
  filePath: string     // Path to the built file
  pathname: string     // URL pathname
  sourcePage: string   // Original source file path in pages/ directory
  runtime: 'nodejs' | 'edge'
  assets: Record  // Traced dependencies (key: relative path from repo root, value: absolute path)
  wasmAssets?: Record  // Bundled wasm files (key: name, value: absolute path)
  edgeRuntime?: {
    modulePath: string    // Absolute path to the module registered in the edge runtime
    entryKey: string      // Canonical key used by the edge entry registry
    handlerExport: string // Export name to invoke, currently 'handler'
  }
  config: {
    maxDuration?: number  // Maximum duration of the route in seconds
    preferredRegion?: string | string[]  // Preferred deployment region
    env?: Record  // Environment variables (edge runtime only)
  }
}
```

## API Routes (`outputs.pagesApi`)

API routes from `pages/api/`:

```typescript
{
  type: 'PAGES_API'
  id: string           // Route identifier
  filePath: string     // Path to the built file
  pathname: string     // URL pathname
  sourcePage: string   // Original relative source file path
  runtime: 'nodejs' | 'edge'
  assets: Record  // Traced dependencies (key: relative path from repo root, value: absolute path)
  wasmAssets?: Record  // Bundled wasm files (key: name, value: absolute path)
  edgeRuntime?: {
    modulePath: string    // Absolute path to the module registered in the edge runtime
    entryKey: string      // Canonical key used by the edge entry registry
    handlerExport: string // Export name to invoke, currently 'handler'
  }
  config: {
    maxDuration?: number  // Maximum duration of the route in seconds
    preferredRegion?: string | string[]  // Preferred deployment region
    env?: Record  // Environment variables (edge runtime only)
  }
}
```

## App Pages (`outputs.appPages`)

React pages from the `app/` directory:

```typescript
{
  type: 'APP_PAGE'
  id: string           // Route identifier
  filePath: string     // Path to the built file
  pathname: string     // URL pathname. Includes .rsc suffix for RSC routes
  sourcePage: string   // Original relative source file path
  runtime: 'nodejs' | 'edge' // Runtime the route is built for
  assets: Record  // Traced dependencies (key: relative path from repo root, value: absolute path)
  wasmAssets?: Record  // Bundled wasm files (key: name, value: absolute path)
  edgeRuntime?: {
    modulePath: string    // Absolute path to the module registered in the edge runtime
    entryKey: string      // Canonical key used by the edge entry registry
    handlerExport: string // Export name to invoke, currently 'handler'
  }
  config: {
    maxDuration?: number  // Maximum duration of the route in seconds
    preferredRegion?: string | string[]  // Preferred deployment region
    env?: Record  // Environment variables (edge runtime only)
  }
}
```

## App Routes (`outputs.appRoutes`)

API and metadata routes from the `app/` directory:

```typescript
{
  type: 'APP_ROUTE'
  id: string           // Route identifier
  filePath: string     // Path to the built file
  pathname: string     // URL pathname
  sourcePage: string   // Original relative source file path
  runtime: 'nodejs' | 'edge' // Runtime the route is built for
  assets: Record  // Traced dependencies (key: relative path from repo root, value: absolute path)
  wasmAssets?: Record  // Bundled wasm files (key: name, value: absolute path)
  edgeRuntime?: {
    modulePath: string    // Absolute path to the module registered in the edge runtime
    entryKey: string      // Canonical key used by the edge entry registry
    handlerExport: string // Export name to invoke, currently 'handler'
  }
  config: {
    maxDuration?: number  // Maximum duration of the route in seconds
    preferredRegion?: string | string[]  // Preferred deployment region
    env?: Record  // Environment variables (edge runtime only)
  }
}
```

## Prerenders (`outputs.prerenders`)

ISR-enabled routes and static prerenders:

```typescript
{
  type: 'PRERENDER'
  id: string           // Route identifier
  pathname: string     // URL pathname
  parentOutputId: string  // ID of the source page/route
  groupId: number        // Revalidation group identifier (prerenders with same groupId revalidate together)
  pprChain?: {
    headers: Record  // PPR chain headers (e.g., 'next-resume': '1')
  }
  parentFallbackMode?: false | null | string  // false: no additional paths (fallback: false), null: blocking render, string: path to HTML fallback
  fallback?: {
    filePath: string | undefined  // Path to the fallback file (HTML, JSON, or RSC)
    initialStatus?: number  // Initial status code
    initialHeaders?: Record  // Initial headers
    initialExpiration?: number  // Initial expiration time in seconds
    initialRevalidate?: number | false  // Initial revalidate time in seconds, or false for fully static
    postponedState: string | undefined  // Serialized PPR state used for resuming rendering
  }
  config: {
    allowQuery?: string[]     // Allowed query parameters considered for the cache key
    allowHeader?: string[]    // Allowed headers for ISR
    bypassFor?: RouteHas[]    // Cache bypass conditions
    renderingMode?: 'STATIC' | 'PARTIALLY_STATIC'  // STATIC: fully static, PARTIALLY_STATIC: PPR-enabled
    partialFallback?: boolean  // Serves a partial fallback shell that should be upgraded to a full route in the background
    bypassToken?: string      // Generated token that signals the prerender cache should be bypassed
  }
}
```

## Static Files (`outputs.staticFiles`)

Static assets and auto-statically optimized pages:

```typescript
{
  type: 'STATIC_FILE'
  id: string // Route identifier
  filePath: string // Path to the built file
  pathname: string // URL pathname
  immutableHash: string | undefined // Content hash when the filename contains a hash, indicating the file is immutable
}
```

## Middleware (`outputs.middleware`)

`middleware.ts` (`.js`/`.ts`) or `proxy.ts` (`.js`/`.ts`) function (if present):

```typescript
{
  type: 'MIDDLEWARE'
  id: string           // Route identifier
  filePath: string     // Path to the built file
  pathname: string      // Always '/_middleware'
  sourcePage: string    // Always 'middleware'
  runtime: 'nodejs' | 'edge' // Runtime the route is built for
  assets: Record  // Traced dependencies (key: relative path from repo root, value: absolute path)
  wasmAssets?: Record  // Bundled wasm files (key: name, value: absolute path)
  edgeRuntime?: {
    modulePath: string    // Absolute path to the module registered in the edge runtime
    entryKey: string      // Canonical key used by the edge entry registry
    handlerExport: string // Export name to invoke, currently 'handler'
  }
  config: {
    maxDuration?: number  // Maximum duration of the route in seconds
    preferredRegion?: string | string[]  // Preferred deployment region
    env?: Record  // Environment variables (edge runtime only)
    matchers?: Array
  }
}
```

---
title: Routing Information
description: "Reference for routing phases and route fields exposed in `onBuildComplete`."
url: "https://nextjs.org/docs/pages/api-reference/adapters/routing-information"
version: 16.2.6
router: Pages Router
---

# Routing Information

The `routing` object in `onBuildComplete` provides complete routing information with processed patterns ready for deployment:

## `routing.beforeMiddleware`

Routes applied before middleware execution. These include generated header and redirect behavior.

## `routing.beforeFiles`

Rewrite routes checked before filesystem route matching.

## `routing.afterFiles`

Rewrite routes checked after filesystem route matching.

## `routing.dynamicRoutes`

Dynamic matchers generated from route segments such as `[slug]` and catch-all routes.

## `routing.onMatch`

Routes that apply after a successful match, such as immutable cache headers for hashed static assets.

## `routing.fallback`

Final rewrite routes checked when earlier phases did not produce a match.

## Common Route Fields

Each route entry can include:

* `source`: Original route pattern (optional for generated internal rules)
* `sourceRegex`: Compiled regex for matching requests
* `destination`: Internal destination or redirect destination
* `headers`: Headers to apply
* `has`: Positive matching conditions
* `missing`: Negative matching conditions
* `status`: Redirect status code
* `priority`: Internal route priority flag

---
title: Use Cases
description: Common patterns and examples for deployment adapter implementations.
url: "https://nextjs.org/docs/pages/api-reference/adapters/use-cases"
version: 16.2.6
router: Pages Router
---

# Use Cases

Common use cases for adapters include:

* **Deployment Platform Integration**: Automatically configure build outputs for specific hosting platforms
* **Asset Processing**: Transform or optimize build outputs
* **Monitoring Integration**: Collect build metrics and route information
* **Custom Bundling**: Package outputs in platform-specific formats
* **Build Validation**: Ensure outputs meet specific requirements
* **Route Generation**: Use processed route information to generate platform-specific routing configs

---
title: Edge Runtime
description: API Reference for the Edge Runtime.
url: "https://nextjs.org/docs/pages/api-reference/edge"
version: 16.2.6
router: Pages Router
---

# Edge Runtime

Next.js has two server runtimes you can use in your application:

* The **Node.js Runtime** (default), which has access to all Node.js APIs and is used for rendering your application.
* The **Edge Runtime** which contains a more limited [set of APIs](#reference), used in [Proxy](/docs/app/api-reference/file-conventions/proxy).

## Caveats

* The Edge Runtime does not support all Node.js APIs. Some packages may not work as expected.
* The Edge Runtime does not support Incremental Static Regeneration (ISR).
* Both runtimes can support [streaming](/docs/app/api-reference/file-conventions/loading) depending on your deployment adapter.

## Reference

The Edge Runtime supports the following APIs:

### Network APIs

| API                                                                             | Description                       |
| ------------------------------------------------------------------------------- | --------------------------------- |
| [`Blob`](https://developer.mozilla.org/docs/Web/API/Blob)                       | Represents a blob                 |
| [`fetch`](https://developer.mozilla.org/docs/Web/API/Fetch_API)                 | Fetches a resource                |
| [`FetchEvent`](https://developer.mozilla.org/docs/Web/API/FetchEvent)           | Represents a fetch event          |
| [`File`](https://developer.mozilla.org/docs/Web/API/File)                       | Represents a file                 |
| [`FormData`](https://developer.mozilla.org/docs/Web/API/FormData)               | Represents form data              |
| [`Headers`](https://developer.mozilla.org/docs/Web/API/Headers)                 | Represents HTTP headers           |
| [`Request`](https://developer.mozilla.org/docs/Web/API/Request)                 | Represents an HTTP request        |
| [`Response`](https://developer.mozilla.org/docs/Web/API/Response)               | Represents an HTTP response       |
| [`URLSearchParams`](https://developer.mozilla.org/docs/Web/API/URLSearchParams) | Represents URL search parameters  |
| [`WebSocket`](https://developer.mozilla.org/docs/Web/API/WebSocket)             | Represents a websocket connection |

### Encoding APIs

| API                                                                                 | Description                        |
| ----------------------------------------------------------------------------------- | ---------------------------------- |
| [`atob`](https://developer.mozilla.org/en-US/docs/Web/API/atob)                     | Decodes a base-64 encoded string   |
| [`btoa`](https://developer.mozilla.org/en-US/docs/Web/API/btoa)                     | Encodes a string in base-64        |
| [`TextDecoder`](https://developer.mozilla.org/docs/Web/API/TextDecoder)             | Decodes a Uint8Array into a string |
| [`TextDecoderStream`](https://developer.mozilla.org/docs/Web/API/TextDecoderStream) | Chainable decoder for streams      |
| [`TextEncoder`](https://developer.mozilla.org/docs/Web/API/TextEncoder)             | Encodes a string into a Uint8Array |
| [`TextEncoderStream`](https://developer.mozilla.org/docs/Web/API/TextEncoderStream) | Chainable encoder for streams      |

### Stream APIs

| API                                                                                                     | Description                             |
| ------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| [`ReadableStream`](https://developer.mozilla.org/docs/Web/API/ReadableStream)                           | Represents a readable stream            |
| [`ReadableStreamBYOBReader`](https://developer.mozilla.org/docs/Web/API/ReadableStreamBYOBReader)       | Represents a reader of a ReadableStream |
| [`ReadableStreamDefaultReader`](https://developer.mozilla.org/docs/Web/API/ReadableStreamDefaultReader) | Represents a reader of a ReadableStream |
| [`TransformStream`](https://developer.mozilla.org/docs/Web/API/TransformStream)                         | Represents a transform stream           |
| [`WritableStream`](https://developer.mozilla.org/docs/Web/API/WritableStream)                           | Represents a writable stream            |
| [`WritableStreamDefaultWriter`](https://developer.mozilla.org/docs/Web/API/WritableStreamDefaultWriter) | Represents a writer of a WritableStream |

### Crypto APIs

| API                                                                       | Description                                                                                         |
| ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| [`crypto`](https://developer.mozilla.org/docs/Web/API/Window/crypto)      | Provides access to the cryptographic functionality of the platform                                  |
| [`CryptoKey`](https://developer.mozilla.org/docs/Web/API/CryptoKey)       | Represents a cryptographic key                                                                      |
| [`SubtleCrypto`](https://developer.mozilla.org/docs/Web/API/SubtleCrypto) | Provides access to common cryptographic primitives, like hashing, signing, encryption or decryption |

### Web Standard APIs

| API                                                                                                                   | Description                                                                                                                                                                                          |
| --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`AbortController`](https://developer.mozilla.org/docs/Web/API/AbortController)                                       | Allows you to abort one or more DOM requests as and when desired                                                                                                                                     |
| [`Array`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Array)                           | Represents an array of values                                                                                                                                                                        |
| [`ArrayBuffer`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/ArrayBuffer)               | Represents a generic, fixed-length raw binary data buffer                                                                                                                                            |
| [`Atomics`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Atomics)                       | Provides atomic operations as static methods                                                                                                                                                         |
| [`BigInt`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/BigInt)                         | Represents a whole number with arbitrary precision                                                                                                                                                   |
| [`BigInt64Array`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/BigInt64Array)           | Represents a typed array of 64-bit signed integers                                                                                                                                                   |
| [`BigUint64Array`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/BigUint64Array)         | Represents a typed array of 64-bit unsigned integers                                                                                                                                                 |
| [`Boolean`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Boolean)                       | Represents a logical entity and can have two values: `true` and `false`                                                                                                                              |
| [`clearInterval`](https://developer.mozilla.org/docs/Web/API/WindowOrWorkerGlobalScope/clearInterval)                 | Cancels a timed, repeating action which was previously established by a call to `setInterval()`                                                                                                      |
| [`clearTimeout`](https://developer.mozilla.org/docs/Web/API/WindowOrWorkerGlobalScope/clearTimeout)                   | Cancels a timed, repeating action which was previously established by a call to `setTimeout()`                                                                                                       |
| [`console`](https://developer.mozilla.org/docs/Web/API/Console)                                                       | Provides access to the browser's debugging console                                                                                                                                                   |
| [`DataView`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/DataView)                     | Represents a generic view of an `ArrayBuffer`                                                                                                                                                        |
| [`Date`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Date)                             | Represents a single moment in time in a platform-independent format                                                                                                                                  |
| [`decodeURI`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/decodeURI)                   | Decodes a Uniform Resource Identifier (URI) previously created by `encodeURI` or by a similar routine                                                                                                |
| [`decodeURIComponent`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/decodeURIComponent) | Decodes a Uniform Resource Identifier (URI) component previously created by `encodeURIComponent` or by a similar routine                                                                             |
| [`DOMException`](https://developer.mozilla.org/docs/Web/API/DOMException)                                             | Represents an error that occurs in the DOM                                                                                                                                                           |
| [`encodeURI`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/encodeURI)                   | Encodes a Uniform Resource Identifier (URI) by replacing each instance of certain characters by one, two, three, or four escape sequences representing the UTF-8 encoding of the character           |
| [`encodeURIComponent`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/encodeURIComponent) | Encodes a Uniform Resource Identifier (URI) component by replacing each instance of certain characters by one, two, three, or four escape sequences representing the UTF-8 encoding of the character |
| [`Error`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Error)                           | Represents an error when trying to execute a statement or accessing a property                                                                                                                       |
| [`EvalError`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/EvalError)                   | Represents an error that occurs regarding the global function `eval()`                                                                                                                               |
| [`Float32Array`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Float32Array)             | Represents a typed array of 32-bit floating point numbers                                                                                                                                            |
| [`Float64Array`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Float64Array)             | Represents a typed array of 64-bit floating point numbers                                                                                                                                            |
| [`Function`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Function)                     | Represents a function                                                                                                                                                                                |
| [`Infinity`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Infinity)                     | Represents the mathematical Infinity value                                                                                                                                                           |
| [`Int8Array`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Int8Array)                   | Represents a typed array of 8-bit signed integers                                                                                                                                                    |
| [`Int16Array`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Int16Array)                 | Represents a typed array of 16-bit signed integers                                                                                                                                                   |
| [`Int32Array`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Int32Array)                 | Represents a typed array of 32-bit signed integers                                                                                                                                                   |
| [`Intl`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Intl)                             | Provides access to internationalization and localization functionality                                                                                                                               |
| [`isFinite`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/isFinite)                     | Determines whether a value is a finite number                                                                                                                                                        |
| [`isNaN`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/isNaN)                           | Determines whether a value is `NaN` or not                                                                                                                                                           |
| [`JSON`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/JSON)                             | Provides functionality to convert JavaScript values to and from the JSON format                                                                                                                      |
| [`Map`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Map)                               | Represents a collection of values, where each value may occur only once                                                                                                                              |
| [`Math`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Math)                             | Provides access to mathematical functions and constants                                                                                                                                              |
| [`Number`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Number)                         | Represents a numeric value                                                                                                                                                                           |
| [`Object`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Object)                         | Represents the object that is the base of all JavaScript objects                                                                                                                                     |
| [`parseFloat`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/parseFloat)                 | Parses a string argument and returns a floating point number                                                                                                                                         |
| [`parseInt`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/parseInt)                     | Parses a string argument and returns an integer of the specified radix                                                                                                                               |
| [`Promise`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Promise)                       | Represents the eventual completion (or failure) of an asynchronous operation, and its resulting value                                                                                                |
| [`Proxy`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Proxy)                           | Represents an object that is used to define custom behavior for fundamental operations (e.g. property lookup, assignment, enumeration, function invocation, etc)                                     |
| [`queueMicrotask`](https://developer.mozilla.org/docs/Web/API/queueMicrotask)                                         | Queues a microtask to be executed                                                                                                                                                                    |
| [`RangeError`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/RangeError)                 | Represents an error when a value is not in the set or range of allowed values                                                                                                                        |
| [`ReferenceError`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/ReferenceError)         | Represents an error when a non-existent variable is referenced                                                                                                                                       |
| [`Reflect`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Reflect)                       | Provides methods for interceptable JavaScript operations                                                                                                                                             |
| [`RegExp`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/RegExp)                         | Represents a regular expression, allowing you to match combinations of characters                                                                                                                    |
| [`Set`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Set)                               | Represents a collection of values, where each value may occur only once                                                                                                                              |
| [`setInterval`](https://developer.mozilla.org/docs/Web/API/setInterval)                                               | Repeatedly calls a function, with a fixed time delay between each call                                                                                                                               |
| [`setTimeout`](https://developer.mozilla.org/docs/Web/API/setTimeout)                                                 | Calls a function or evaluates an expression after a specified number of milliseconds                                                                                                                 |
| [`SharedArrayBuffer`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer)   | Represents a generic, fixed-length raw binary data buffer                                                                                                                                            |
| [`String`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/String)                         | Represents a sequence of characters                                                                                                                                                                  |
| [`structuredClone`](https://developer.mozilla.org/docs/Web/API/Web_Workers_API/Structured_clone_algorithm)            | Creates a deep copy of a value                                                                                                                                                                       |
| [`Symbol`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Symbol)                         | Represents a unique and immutable data type that is used as the key of an object property                                                                                                            |
| [`SyntaxError`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/SyntaxError)               | Represents an error when trying to interpret syntactically invalid code                                                                                                                              |
| [`TypeError`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/TypeError)                   | Represents an error when a value is not of the expected type                                                                                                                                         |
| [`Uint8Array`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Uint8Array)                 | Represents a typed array of 8-bit unsigned integers                                                                                                                                                  |
| [`Uint8ClampedArray`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Uint8ClampedArray)   | Represents a typed array of 8-bit unsigned integers clamped to 0-255                                                                                                                                 |
| [`Uint32Array`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Uint32Array)               | Represents a typed array of 32-bit unsigned integers                                                                                                                                                 |
| [`URIError`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/URIError)                     | Represents an error when a global URI handling function was used in a wrong way                                                                                                                      |
| [`URL`](https://developer.mozilla.org/docs/Web/API/URL)                                                               | Represents an object providing static methods used for creating object URLs                                                                                                                          |
| [`URLPattern`](https://developer.mozilla.org/docs/Web/API/URLPattern)                                                 | Represents a URL pattern                                                                                                                                                                             |
| [`URLSearchParams`](https://developer.mozilla.org/docs/Web/API/URLSearchParams)                                       | Represents a collection of key/value pairs                                                                                                                                                           |
| [`WeakMap`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/WeakMap)                       | Represents a collection of key/value pairs in which the keys are weakly referenced                                                                                                                   |
| [`WeakSet`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/WeakSet)                       | Represents a collection of objects in which each object may occur only once                                                                                                                          |
| [`WebAssembly`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/WebAssembly)               | Provides access to WebAssembly                                                                                                                                                                       |

### Next.js Specific Polyfills

* [`AsyncLocalStorage`](https://nodejs.org/api/async_context.html#class-asynclocalstorage)

### Environment Variables

You can use `process.env` to access [Environment Variables](/docs/app/guides/environment-variables) for both `next dev` and `next build`.

### Unsupported APIs

The Edge Runtime has some restrictions including:

* Native Node.js APIs **are not supported**. For example, you can't read or write to the filesystem.
* `node_modules` *can* be used, as long as they implement ES Modules and do not use native Node.js APIs.
* Calling `require` directly is **not allowed**. Use ES Modules instead.

The following JavaScript language features are disabled, and **will not work:**

| API                                                                                                                             | Description                                                         |
| ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| [`eval`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/eval)                                       | Evaluates JavaScript code represented as a string                   |
| [`new Function(evalString)`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Function)               | Creates a new function with the code provided as an argument        |
| [`WebAssembly.compile`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/WebAssembly/compile)         | Compiles a WebAssembly module from a buffer source                  |
| [`WebAssembly.instantiate`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/WebAssembly/instantiate) | Compiles and instantiates a WebAssembly module from a buffer source |

In rare cases, your code could contain (or import) some dynamic code evaluation statements which *cannot be reached at runtime* and which cannot be removed by treeshaking.
You can relax the check to allow specific files with your Proxy configuration:

```javascript filename="proxy.ts"
export const config = {
  unstable_allowDynamic: [
    // allows a single file
    '/lib/utilities.js',
    // use a glob to allow anything in the function-bind 3rd party module
    '**/node_modules/function-bind/**',
  ],
}
```

`unstable_allowDynamic` is a [glob](https://github.com/micromatch/micromatch#matching-features), or an array of globs, ignoring dynamic code evaluation for specific files. The globs are relative to your application root folder.

Be warned that if these statements are executed on the Edge, *they will throw and cause a runtime error*.

---
title: Turbopack
description: Turbopack is an incremental bundler optimized for JavaScript and TypeScript, written in Rust, and built into Next.js.
url: "https://nextjs.org/docs/pages/api-reference/turbopack"
version: 16.2.6
router: Pages Router
---

# Turbopack

Turbopack is an **incremental bundler** optimized for JavaScript and TypeScript, written in Rust, and built into **Next.js**. You can use Turbopack with both the Pages and App Router for a **much faster** local development experience.

## Why Turbopack?

We built Turbopack to push the performance of Next.js, including:

* **Unified Graph:** Next.js supports multiple output environments (e.g., client and server). Managing multiple compilers and stitching bundles together can be tedious. Turbopack uses a **single, unified graph** for all environments.
* **Bundling vs Native ESM:** Some tools skip bundling in development and rely on the browser's native ESM. This works well for small apps but can slow down large apps due to excessive network requests. Turbopack **bundles** in dev, but in an optimized way to keep large apps fast.
* **Incremental Computation:** Turbopack parallelizes work across cores and **caches** results down to the function level. Once a piece of work is done, Turbopack won’t repeat it.
* **Lazy Bundling:** Turbopack only bundles what is actually requested by the dev server. This lazy approach can reduce initial compile times and memory usage.

## Supported platforms

Turbopack requires platform-specific native bindings. The following platforms are currently supported:

| Platform       | Architecture |
| -------------- | ------------ |
| macOS (Darwin) | x64, ARM64   |
| Windows        | x64, ARM64   |
| Linux (glibc)  | x64, ARM64   |
| Linux (musl)   | x64, ARM64   |

On platforms without native bindings (e.g. FreeBSD, OpenBSD), Next.js falls back to WebAssembly (WASM) bindings. WASM bindings support core SWC features like compilation and minification, but **do not support Turbopack**. On these platforms, use the `--webpack` flag:

```bash
next dev --webpack
next build --webpack
```

## Getting started

Turbopack is now the **default bundler** in Next.js. No configuration is needed to use Turbopack:

```json filename="package.json" highlight={3}
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

### Using Webpack instead

If you need to use Webpack instead of Turbopack, you can opt-in with the `--webpack` flag:

```json filename="package.json"
{
  "scripts": {
    "dev": "next dev --webpack",
    "build": "next build --webpack",
    "start": "next start"
  }
}
```

## Supported features

Turbopack in Next.js has **zero-configuration** for the common use cases. Below is a summary of what is supported out of the box, plus some references to how you can configure Turbopack further when needed.

### Language features

| Feature                     | Status        | Notes                                                                                                                                                                                                                                                                                                                                                                                                                   |
| --------------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **JavaScript & TypeScript** | **Supported** | Uses SWC under the hood. Type-checking is not done by Turbopack (run `tsc --watch` or rely on your IDE for type checks).                                                                                                                                                                                                                                                                                                |
| **ECMAScript (ESNext)**     | **Supported** | Turbopack supports the latest ECMAScript features, matching SWC’s coverage.                                                                                                                                                                                                                                                                                                                                             |
| **CommonJS**                | **Supported** | `require()` syntax is handled out of the box.                                                                                                                                                                                                                                                                                                                                                                           |
| **ESM**                     | **Supported** | Static and dynamic `import` are fully supported.                                                                                                                                                                                                                                                                                                                                                                        |
| **Babel**                   | **Supported** | Starting in Next.js 16, Turbopack uses Babel automatically if it detects [a configuration file][babel-config]. Unlike in webpack, SWC is always used for Next.js's internal transforms and downleveling to older ECMAScript revisions. Next.js with webpack disables SWC if a Babel configuration file is present. Files in `node_modules` are excluded, unless you [manually configure `babel-loader`][manual-loader]. |

[babel-config]: https://babeljs.io/docs/config-files

[manual-loader]: /docs/app/api-reference/config/next-config-js/turbopack#configuring-webpack-loaders

### Framework and React features

| Feature                           | Status        | Notes                                                                                                                  |
| --------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **JSX / TSX**                     | **Supported** | SWC handles JSX/TSX compilation.                                                                                       |
| **Fast Refresh**                  | **Supported** | No configuration needed.                                                                                               |
| **React Server Components (RSC)** | **Supported** | For the Next.js App Router. Turbopack ensures correct server/client bundling.                                          |
| **Root layout creation**          | Unsupported   | Automatic creation of a root layout in App Router is not supported. Turbopack will instruct you to create it manually. |

### CSS and styling

| Feature            | Status                  | Notes                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------ | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Global CSS**     | **Supported**           | Import `.css` files directly in your application.                                                                                                                                                                                                                                                                                                                     |
| **CSS Modules**    | **Supported**           | `.module.css` files work natively (Lightning CSS).                                                                                                                                                                                                                                                                                                                    |
| **CSS Nesting**    | **Supported**           | Lightning CSS supports [modern CSS nesting](https://lightningcss.dev/).                                                                                                                                                                                                                                                                                               |
| **@import syntax** | **Supported**           | Combine multiple CSS files.                                                                                                                                                                                                                                                                                                                                           |
| **PostCSS**        | **Supported**           | Automatically processes PostCSS config files (`postcss.config.js`, `.mjs`, `.cjs`, `.ts`, `.mts`, `.cts`) in a Node.js worker pool. Useful for Tailwind, Autoprefixer, etc.                                                                                                                                                                                           |
| **Sass / SCSS**    | **Supported** (Next.js) | For Next.js, Sass is supported out of the box. Custom Sass functions (`sassOptions.functions`) are not supported because Turbopack's Rust-based architecture cannot directly execute JavaScript functions, unlike webpack's Node.js environment. Use webpack if you need this feature. In the future, Turbopack standalone usage will likely require a loader config. |
| **Less**           | Planned via plugins     | Not yet supported by default. Will likely require a loader config once custom loaders are stable.                                                                                                                                                                                                                                                                     |
| **Lightning CSS**  | **In Use**              | Handles CSS transformations. Some low-usage CSS Modules features (like `:local/:global` as standalone pseudo-classes) are not yet supported. [See below for more details.](#unsupported-and-unplanned-features)                                                                                                                                                       |

### Assets

| Feature                           | Status        | Notes                                                                                                                      |
| --------------------------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Static Assets** (images, fonts) | **Supported** | Importing `import img from './img.png'` works out of the box. In Next.js, returns an object for the `` component. |
| **JSON Imports**                  | **Supported** | Named or default imports from `.json` are supported.                                                                       |

### Module resolution

| Feature               | Status              | Notes                                                                                                                                                           |
| --------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Path Aliases**      | **Supported**       | Reads `tsconfig.json`'s `paths` and `baseUrl`, matching Next.js behavior.                                                                                       |
| **Manual Aliases**    | **Supported**       | [Configure `resolveAlias` in `next.config.js`](/docs/app/api-reference/config/next-config-js/turbopack#resolving-aliases) (similar to `webpack.resolve.alias`). |
| **Custom Extensions** | **Supported**       | [Configure `resolveExtensions` in `next.config.js`](/docs/app/api-reference/config/next-config-js/turbopack#resolving-custom-extensions).                       |
| **AMD**               | Partially Supported | Basic transforms work; advanced AMD usage is limited.                                                                                                           |

### Performance and Fast Refresh

| Feature                  | Status        | Notes                                                                                    |
| ------------------------ | ------------- | ---------------------------------------------------------------------------------------- |
| **Fast Refresh**         | **Supported** | Updates JavaScript, TypeScript, and CSS without a full refresh.                          |
| **Incremental Bundling** | **Supported** | Turbopack lazily builds only what's requested by the dev server, speeding up large apps. |

### Magic Comments

Turbopack supports webpack-compatible magic comments for controlling import behavior. These comments work with dynamic `import()`, `require()`, `require.resolve()`, and `new Worker()` expressions (not static `import` statements).

| Comment                   | Webpack | Turbopack | Description                    |
| ------------------------- | ------- | --------- | ------------------------------ |
| `webpackIgnore: true`     | ✓       | ✓         | Skip bundling, preserve import |
| `turbopackIgnore: true`   | ✗       | ✓         | Skip bundling (Turbopack-only) |
| `turbopackOptional: true` | ✗       | ✓         | Suppress resolve errors        |
| `webpackOptional: true`   | ✗       | ✗         | Not supported                  |

See [Lazy Loading](/docs/app/guides/lazy-loading#magic-comments) for usage examples.

## Known gaps with webpack

There are a number of non-trivial behavior differences between webpack and Turbopack that are important to be aware of when migrating an application. Generally, these are less of a concern for new applications.

### Filesystem Root

Turbopack uses the root directory to resolve modules. Files outside of the project root are not resolved.

For example, when linking dependencies outside the project root (via `npm link`, `yarn link`, `pnpm link`, etc.), those linked files will not be resolved by default. To resolve these files, you must configure the root option to the parent directory of both the project and the linked dependencies.

You can configure the filesystem root using [turbopack.root](/docs/app/api-reference/config/next-config-js/turbopack#root-directory) option in `next.config.js`.

### CSS Module Ordering

Turbopack will follow JS import order to order [CSS modules](/docs/app/getting-started/css#css-modules) which are not otherwise ordered. For example:

```jsx filename="components/BlogPost.jsx"
import utilStyles from './utils.module.css'
import buttonStyles from './button.module.css'
export default function BlogPost() {
  return (

      Click me

  )
}
```

In this example, Turbopack will ensure that `utils.module.css` will appear before `button.module.css` in the produced CSS chunk, following the import order

Webpack generally does this as well, but there are cases where it will ignore JS inferred ordering, for example if it infers the JS file is side-effect-free.

This can lead to subtle rendering changes when adopting Turbopack, if applications have come to rely on an arbitrary ordering. Generally, the solution is easy, e.g. have `button.module.css` `@import utils.module.css` to force the ordering, or identify the conflicting rules and change them to not target the same properties.

### Sass node\_modules imports

Turbopack supports importing `node_modules` Sass files out of the box. Webpack supports a legacy tilde `~` syntax for this, which is not supported by Turbopack.

From:

```scss filename="styles/globals.scss"
@import '~bootstrap/dist/css/bootstrap.min.css';
```

To:

```scss filename="styles/globals.scss"
@import 'bootstrap/dist/css/bootstrap.min.css';
```

If you can't update the imports, you can add a `turbopack.resolveAlias` configuration to map the `~` syntax to the actual path:

```js filename="next.config.js"
module.exports = {
  turbopack: {
    resolveAlias: {
      '~*': '*',
    },
  },
}
```

### Build Caching

Webpack supports [disk build caching](https://webpack.js.org/configuration/cache/#cache) to improve build performance. Turbopack provides a similar feature, currently in beta. Starting with Next 16, you can enable Turbopack’s filesystem cache by setting the following experimental flags:

* [`experimental.turbopackFileSystemCacheForDev`](/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache) is enabled by default
* [`experimental.turbopackFileSystemCacheForBuild`](/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache) is currently opt-in

> **Good to know:** For this reason, when comparing webpack and Turbopack performance, make sure to delete the `.next` folder between builds to see a fair cold build comparison or enable the turbopack filesystem cache feature to compare warm builds.

### Webpack plugins

Turbopack does not support webpack plugins. This affects third-party tools that rely on webpack's plugin system for integration. We do support [webpack loaders](/docs/app/api-reference/config/next-config-js/turbopack#configuring-webpack-loaders). If you depend on webpack plugins, you'll need to find Turbopack-compatible alternatives or continue using webpack until equivalent functionality is available.

## Unsupported and unplanned features

Some features are not yet implemented or not planned:

* **Legacy CSS Modules features**
  * Standalone `:local` and `:global` pseudo-classes (only the function variant `:global(...)` is supported).
  * The `@value` rule (superseded by CSS variables).
  * `:import` and `:export` ICSS rules.
  * `composes` in `.module.css` composing a `.css` file. In webpack this would treat the `.css` file as a CSS Module, with Turbopack the `.css` file will always be global. This means that if you want to use `composes` in a CSS Module, you need to change the `.css` file to a `.module.css` file.
  * `@import` in CSS Modules importing `.css` as a CSS Module. In webpack this would treat the `.css` file as a CSS Module, with Turbopack the `.css` file will always be global. This means that if you want to use `@import` in a CSS Module, you need to change the `.css` file to a `.module.css` file.
* **`sassOptions.functions`**
  Custom Sass functions defined in `sassOptions.functions` are not supported. This feature allows defining JavaScript functions that can be called from Sass code during compilation. Turbopack's Rust-based architecture cannot directly execute JavaScript functions passed through `sassOptions.functions`, unlike webpack's Node.js-based sass-loader which runs entirely in JavaScript. If you're using custom Sass functions, you'll need to use webpack instead of Turbopack.
* **`webpack()` configuration** in `next.config.js`
  Turbopack replaces webpack, so `webpack()` configs are not recognized. Use the [`turbopack` config](/docs/app/api-reference/config/next-config-js/turbopack) instead.
* **Yarn PnP**
  Not planned for Turbopack support in Next.js.
* **`experimental.urlImports`**
  Not planned for Turbopack.
* **`experimental.esmExternals`**
  Not planned. Turbopack does not support the legacy `esmExternals` configuration in Next.js.
* **Some Next.js Experimental Flags**
  * `experimental.nextScriptWorkers`
  * `experimental.fallbackNodePolyfills`
    We plan to implement these in the future.

For a full, detailed breakdown of each feature flag and its status, see the [Turbopack API Reference](/docs/app/api-reference/config/next-config-js/turbopack).

## Configuration

Turbopack can be configured via `next.config.js` (or `next.config.ts`) under the `turbopack` key. Configuration options include:

* **`rules`**
  Define additional [webpack loaders](/docs/app/api-reference/config/next-config-js/turbopack#configuring-webpack-loaders) for file transformations.
* **`resolveAlias`**
  Create manual aliases (like `resolve.alias` in webpack).
* **`resolveExtensions`**
  Change or extend file extensions for module resolution.
* **[`ignoreIssue`](/docs/app/api-reference/config/next-config-js/turbopackIgnoreIssue)**
  Suppress specific Turbopack errors and warnings from the CLI output and error overlay.

Additionally, the following experimental options are available under `experimental` in `next.config.js`:

| Option                                                                                                       | Description                                                                            | Default (dev) | Default (build)               |
| ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- | ------------- | ----------------------------- |
| [`turbopackFileSystemCacheForDev`](/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache)   | Enable filesystem cache for the dev server.                                            | `true`        | N/A                           |
| [`turbopackFileSystemCacheForBuild`](/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache) | Enable filesystem cache for builds.                                                    | N/A           | `false`                       |
| `turbopackMinify`                                                                                            | Enable minification.                                                                   | `false`       | `true`                        |
| `turbopackSourceMaps`                                                                                        | Enable source maps.                                                                    | `true`        | `productionBrowserSourceMaps` |
| `turbopackInputSourceMaps`                                                                                   | Enable extraction of source maps from input files.                                     | `true`        | `true`                        |
| `turbopackTreeShaking`                                                                                       | Use advanced module-fragments tree shaking instead of the default reexports-only mode. | `false`       | `false`                       |
| `turbopackRemoveUnusedImports`                                                                               | Enable removing unused imports. Requires `turbopackRemoveUnusedExports`.               | `false`       | `true`                        |
| `turbopackRemoveUnusedExports`                                                                               | Enable removing unused exports.                                                        | `false`       | `true`                        |
| `turbopackInferModuleSideEffects`                                                                            | Enable local analysis to infer side-effect-free modules for better tree shaking.       | `true`        | `true`                        |
| `turbopackScopeHoisting`                                                                                     | Enable scope hoisting. Always disabled in dev mode.                                    | `false`       | `true`                        |
| `turbopackClientSideNestedAsyncChunking`                                                                     | Enable nested async chunking for client-side assets.                                   | `false`       | `true`                        |
| `turbopackServerSideNestedAsyncChunking`                                                                     | Enable nested async chunking for server-side assets.                                   | `false`       | `false`                       |
| `turbopackImportTypeBytes`                                                                                   | Enable support for `with {type: "bytes"}` for ESM imports.                             | `false`       | `false`                       |
| `turbopackUseBuiltinBabel`                                                                                   | Enable automatic Babel loader configuration when a Babel config file is present.       | `true`        | `true`                        |
| `turbopackUseBuiltinSass`                                                                                    | Enable automatic Sass loader configuration.                                            | `true`        | `true`                        |
| `turbopackModuleIds`                                                                                         | Module ID strategy: `'named'` or `'deterministic'`.                                    | `'named'`     | `'deterministic'`             |

```js filename="next.config.js"
module.exports = {
  turbopack: {
    // Example: adding an alias and custom file extension
    resolveAlias: {
      underscore: 'lodash',
    },
    resolveExtensions: ['.mdx', '.tsx', '.ts', '.jsx', '.js', '.json'],
  },
}
```

For more in-depth configuration examples, see the [Turbopack config documentation](/docs/app/api-reference/config/next-config-js/turbopack).

## Generating trace files for performance debugging

If you encounter performance or memory issues and want to help the Next.js team diagnose them, you can generate a trace file by appending `NEXT_TURBOPACK_TRACING=1` to your dev command:

```bash
NEXT_TURBOPACK_TRACING=1 next dev
```

This will produce a `.next/dev/trace-turbopack` file. Include that file when creating a GitHub issue on the [Next.js repo](https://github.com/vercel/next.js) to help us investigate.

By default the development server outputs to `.next/dev`.

## Summary

Turbopack is a **Rust-based**, **incremental** bundler designed to make local development and builds fast—especially for large applications. It is integrated into Next.js, offering zero-config CSS, React, and TypeScript support.

## Version Changes

| Version   | Changes                                                                                                            |
| --------- | ------------------------------------------------------------------------------------------------------------------ |
| `v16.0.0` | Turbopack becomes the default bundler for Next.js. Automatic support for Babel when a configuration file is found. |
| `v15.5.0` | Turbopack support for `build` beta                                                                                 |
| `v15.3.0` | Experimental support for `build`                                                                                   |
| `v15.0.0` | Turbopack for `dev` stable                                                                                         |

---
title: Architecture
description: How Next.js Works
url: "https://nextjs.org/docs/architecture"
version: 16.2.6
---

# Architecture

Learn about the Next.js architecture and how it works under the hood.

 - [Accessibility](/docs/architecture/accessibility)
 - [Fast Refresh](/docs/architecture/fast-refresh)
 - [Next.js Compiler](/docs/architecture/nextjs-compiler)
 - [Supported Browsers](/docs/architecture/supported-browsers)

---
title: Accessibility
description: The built-in accessibility features of Next.js.
url: "https://nextjs.org/docs/architecture/accessibility"
version: 16.2.6
---

# Accessibility

The Next.js team is committed to making Next.js accessible to all developers (and their end-users). By adding accessibility features to Next.js by default, we aim to make the Web more inclusive for everyone.

## Route Announcements

When transitioning between pages rendered on the server (e.g. using the `` tag) screen readers and other assistive technology announce the page title when the page loads so that users understand that the page has changed.

In addition to traditional page navigations, Next.js also supports client-side transitions for improved performance (using `next/link`). To ensure that client-side transitions are also announced to assistive technology, Next.js includes a route announcer by default.

The Next.js route announcer looks for the page name to announce by first inspecting `document.title`, then the `` element, and finally the URL pathname. For the most accessible user experience, ensure that each page in your application has a unique and descriptive title.

## Linting

Next.js provides an [integrated ESLint experience](/docs/pages/api-reference/config/eslint) out of the box, including custom rules for Next.js. By default, Next.js includes `eslint-plugin-jsx-a11y` to help catch accessibility issues early, including warning on:

* [aria-props](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y/blob/HEAD/docs/rules/aria-props.md?rgh-link-date=2021-06-04T02%3A10%3A36Z)
* [aria-proptypes](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y/blob/HEAD/docs/rules/aria-proptypes.md?rgh-link-date=2021-06-04T02%3A10%3A36Z)
* [aria-unsupported-elements](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y/blob/HEAD/docs/rules/aria-unsupported-elements.md?rgh-link-date=2021-06-04T02%3A10%3A36Z)
* [role-has-required-aria-props](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y/blob/HEAD/docs/rules/role-has-required-aria-props.md?rgh-link-date=2021-06-04T02%3A10%3A36Z)
* [role-supports-aria-props](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y/blob/HEAD/docs/rules/role-supports-aria-props.md?rgh-link-date=2021-06-04T02%3A10%3A36Z)

For example, this plugin helps ensure you add alt text to `img` tags, use correct `aria-*` attributes, use correct `role` attributes, and more.

## Accessibility Resources

* [WebAIM WCAG checklist](https://webaim.org/standards/wcag/checklist)
* [WCAG 2.2 Guidelines](https://www.w3.org/TR/WCAG22/)
* [The A11y Project](https://www.a11yproject.com/)
* Check [color contrast ratios](https://developer.mozilla.org/docs/Web/Accessibility/Understanding_WCAG/Perceivable/Color_contrast) between foreground and background elements
* Use [`prefers-reduced-motion`](https://web.dev/prefers-reduced-motion/) when working with animations

---
title: Fast Refresh
description: Fast Refresh is a hot module reloading experience that gives you instantaneous feedback on edits made to your React components.
url: "https://nextjs.org/docs/architecture/fast-refresh"
version: 16.2.6
---

# Fast Refresh

Fast refresh is a React feature integrated into Next.js that allows you to live reload the browser page while maintaining temporary client-side state when you save changes to a file. It's enabled by default in all Next.js applications on **9.4 or newer**. With Fast Refresh enabled, most edits should be visible within a second.

## How It Works

* If you edit a file that **only exports React component(s)**, Fast Refresh will
  update the code only for that file, and re-render your component. You can edit
  anything in that file, including styles, rendering logic, event handlers, or
  effects.
* If you edit a file with exports that *aren't* React components, Fast Refresh
  will re-run both that file, and the other files importing it. So if both
  `Button.js` and `Modal.js` import `theme.js`, editing `theme.js` will update
  both components.
* Finally, if you **edit a file** that's **imported by files outside of the
  React tree**, Fast Refresh **will fall back to doing a full reload**. You
  might have a file which renders a React component but also exports a value
  that is imported by a **non-React component**. For example, maybe your
  component also exports a constant, and a non-React utility file imports it. In
  that case, consider migrating the constant to a separate file and importing it
  into both files. This will re-enable Fast Refresh to work. Other cases can
  usually be solved in a similar way.

## Error Resilience

### Syntax Errors

If you make a syntax error during development, you can fix it and save the file
again. The error will disappear automatically, so you won't need to reload the
app. **You will not lose component state**.

### Runtime Errors

If you make a mistake that leads to a runtime error inside your component,
you'll be greeted with a contextual overlay. Fixing the error will automatically
dismiss the overlay, without reloading the app.

Component state will be retained if the error did not occur during rendering. If
the error did occur during rendering, React will remount your application using
the updated code.

If you have [error boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
in your app (which is a good idea for graceful failures in production), they
will retry rendering on the next edit after a rendering error. This means having
an error boundary can prevent you from always getting reset to the root app
state. However, keep in mind that error boundaries shouldn't be *too* granular.
They are used by React in production, and should always be designed
intentionally.

## Limitations

Fast Refresh tries to preserve local React state in the component you're
editing, but only if it's safe to do so. Here's a few reasons why you might see
local state being reset on every edit to a file:

* Local state is not preserved for class components (only function components
  and Hooks preserve state).
* The file you're editing might have *other* exports in addition to a React
  component.
* Sometimes, a file would export the result of calling a higher-order component
  like `HOC(WrappedComponent)`. If the returned component is a
  class, its state will be reset.
* Anonymous arrow functions like `export default () => ;` cause Fast Refresh to not preserve local component state. For large codebases you can use our [`name-default-component` codemod](/docs/pages/guides/upgrading/codemods#name-default-component).

As more of your codebase moves to function components and Hooks, you can expect
state to be preserved in more cases.

## Tips

* Fast Refresh preserves React local state in function components (and Hooks) by
  default.
* Sometimes you might want to *force* the state to be reset, and a component to
  be remounted. For example, this can be handy if you're tweaking an animation
  that only happens on mount. To do this, you can add `// @refresh reset`
  anywhere in the file you're editing. This directive is local to the file, and
  instructs Fast Refresh to remount components defined in that file on every
  edit.
* You can put `console.log` or `debugger;` into the components you edit during
  development.
* Remember that imports are case sensitive. Both fast and full refresh can fail,
  when your import doesn't match the actual filename.
  For example, `'./header'` vs `'./Header'`.

## Fast Refresh and Hooks

When possible, Fast Refresh attempts to preserve the state of your component
between edits. In particular, `useState` and `useRef` preserve their previous
values as long as you don't change their arguments or the order of the Hook
calls.

Hooks with dependencies—such as `useEffect`, `useMemo`, and `useCallback`—will
*always* update during Fast Refresh. Their list of dependencies will be ignored
while Fast Refresh is happening.

For example, when you edit `useMemo(() => x * 2, [x])` to
`useMemo(() => x * 10, [x])`, it will re-run even though `x` (the dependency)
has not changed. If React didn't do that, your edit wouldn't reflect on the
screen!

Sometimes, this can lead to unexpected results. For example, even a `useEffect`
with an empty array of dependencies would still re-run once during Fast Refresh.

However, writing code resilient to occasional re-running of `useEffect` is a good practice even
without Fast Refresh. It will make it easier for you to introduce new dependencies to it later on
and it's enforced by [React Strict Mode](/docs/pages/api-reference/config/next-config-js/reactStrictMode),
which we highly recommend enabling.

---
title: Next.js Compiler
description: Next.js Compiler, written in Rust, which transforms and minifies your Next.js application.
url: "https://nextjs.org/docs/architecture/nextjs-compiler"
version: 16.2.6
---

# Next.js Compiler

The Next.js Compiler, written in Rust using [SWC](https://swc.rs/), allows Next.js to transform and minify your JavaScript code for production. This replaces Babel for individual files and Terser for minifying output bundles.

Compilation using the Next.js Compiler is 17x faster than Babel and enabled by default since Next.js version 12. If you have an existing Babel configuration or are using [unsupported features](#unsupported-features), your application will opt-out of the Next.js Compiler and continue using Babel.

## Why SWC?

[SWC](https://swc.rs/) is an extensible Rust-based platform for the next generation of fast developer tools.

SWC can be used for compilation, minification, bundling, and more – and is designed to be extended. It's something you can call to perform code transformations (either built-in or custom). Running those transformations happens through higher-level tools like Next.js.

We chose to build on SWC for a few reasons:

* **Extensibility:** SWC can be used as a Crate inside Next.js, without having to fork the library or workaround design constraints.
* **Performance:** We were able to achieve ~3x faster Fast Refresh and ~5x faster builds in Next.js by switching to SWC, with more room for optimization still in progress.
* **WebAssembly:** Rust's support for WASM is essential for supporting all possible platforms and taking Next.js development everywhere.
* **Community:** The Rust community and ecosystem are amazing and still growing.

## Supported Features

### Styled Components

We're working to port `babel-plugin-styled-components` to the Next.js Compiler.

First, update to the latest version of Next.js: `npm install next@latest`. Then, update your `next.config.js` file:

```js filename="next.config.js"
module.exports = {
  compiler: {
    styledComponents: true,
  },
}
```

For advanced use cases, you can configure individual properties for styled-components compilation.

> Note: `ssr` and `displayName` transforms are the main requirement for using `styled-components` in Next.js.

```js filename="next.config.js"
module.exports = {
  compiler: {
    // see https://styled-components.com/docs/tooling#babel-plugin for more info on the options.
    styledComponents: {
      // Enabled by default in development, disabled in production to reduce file size,
      // setting this will override the default for all environments.
      displayName?: boolean,
      // Enabled by default.
      ssr?: boolean,
      // Enabled by default.
      fileName?: boolean,
      // Empty by default.
      topLevelImportPaths?: string[],
      // Defaults to ["index"].
      meaninglessFileNames?: string[],
      // Enabled by default.
      minify?: boolean,
      // Enabled by default.
      transpileTemplateLiterals?: boolean,
      // Empty by default.
      namespace?: string,
      // Disabled by default.
      pure?: boolean,
      // Enabled by default.
      cssProp?: boolean,
    },
  },
}
```

### Jest

The Next.js Compiler transpiles your tests and simplifies configuring Jest together with Next.js including:

* Auto mocking of `.css`, `.module.css` (and their `.scss` variants), and image imports
* Automatically sets up `transform` using SWC
* Loading `.env` (and all variants) into `process.env`
* Ignores `node_modules` from test resolving and transforms
* Ignoring `.next` from test resolving
* Loads `next.config.js` for flags that enable experimental SWC transforms

First, update to the latest version of Next.js: `npm install next@latest`. Then, update your `jest.config.js` file:

```js filename="jest.config.js"
const nextJest = require('next/jest')

// Providing the path to your Next.js app which will enable loading next.config.js and .env files
const createJestConfig = nextJest({ dir: './' })

// Any custom config you want to pass to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['/jest.setup.js'],
}

// createJestConfig is exported in this way to ensure that next/jest can load the Next.js configuration, which is async
module.exports = createJestConfig(customJestConfig)
```

### Relay

To enable [Relay](https://relay.dev/) support:

```js filename="next.config.js"
module.exports = {
  compiler: {
    relay: {
      // This should match relay.config.js
      src: './',
      artifactDirectory: './__generated__',
      language: 'typescript',
      eagerEsModules: false,
    },
  },
}
```

> **Good to know**: In Next.js, all JavaScript files in `pages` directory are considered routes. So, for `relay-compiler` you'll need to specify `artifactDirectory` configuration settings outside of the `pages`, otherwise `relay-compiler` will generate files next to the source file in the `__generated__` directory, and this file will be considered a route, which will break production builds.

### Remove React Properties

Allows to remove JSX properties. This is often used for testing. Similar to `babel-plugin-react-remove-properties`.

To remove properties matching the default regex `^data-test`:

```js filename="next.config.js"
module.exports = {
  compiler: {
    reactRemoveProperties: true,
  },
}
```

To remove custom properties:

```js filename="next.config.js"
module.exports = {
  compiler: {
    // The regexes defined here are processed in Rust so the syntax is different from
    // JavaScript `RegExp`s. See https://docs.rs/regex.
    reactRemoveProperties: { properties: ['^data-custom$'] },
  },
}
```

### Remove Console

This transform allows for removing all `console.*` calls in application code (not `node_modules`). Similar to `babel-plugin-transform-remove-console`.

Remove all `console.*` calls:

```js filename="next.config.js"
module.exports = {
  compiler: {
    removeConsole: true,
  },
}
```

Remove `console.*` output except `console.error`:

```js filename="next.config.js"
module.exports = {
  compiler: {
    removeConsole: {
      exclude: ['error'],
    },
  },
}
```

### Legacy Decorators

Next.js will automatically detect `experimentalDecorators` in `jsconfig.json` or `tsconfig.json`. Legacy decorators are commonly used with older versions of libraries like `mobx`.

This flag is only supported for compatibility with existing applications. We do not recommend using legacy decorators in new applications.

First, update to the latest version of Next.js: `npm install next@latest`. Then, update your `jsconfig.json` or `tsconfig.json` file:

```js
{
  "compilerOptions": {
    "experimentalDecorators": true
  }
}
```

### importSource

Next.js will automatically detect `jsxImportSource` in `jsconfig.json` or `tsconfig.json` and apply that. This is commonly used with libraries like [Theme UI](https://theme-ui.com).

First, update to the latest version of Next.js: `npm install next@latest`. Then, update your `jsconfig.json` or `tsconfig.json` file:

```js
{
  "compilerOptions": {
    "jsxImportSource": "theme-ui"
  }
}
```

### Emotion

We're working to port `@emotion/babel-plugin` to the Next.js Compiler.

First, update to the latest version of Next.js: `npm install next@latest`. Then, update your `next.config.js` file:

```js filename="next.config.js"

module.exports = {
  compiler: {
    emotion: boolean | {
      // default is true. It will be disabled when build type is production.
      sourceMap?: boolean,
      // default is 'dev-only'.
      autoLabel?: 'never' | 'dev-only' | 'always',
      // default is '[local]'.
      // Allowed values: `[local]` `[filename]` and `[dirname]`
      // This option only works when autoLabel is set to 'dev-only' or 'always'.
      // It allows you to define the format of the resulting label.
      // The format is defined via string where variable parts are enclosed in square brackets [].
      // For example labelFormat: "my-classname--[local]", where [local] will be replaced with the name of the variable the result is assigned to.
      labelFormat?: string,
      // default is undefined.
      // This option allows you to tell the compiler what imports it should
      // look at to determine what it should transform so if you re-export
      // Emotion's exports, you can still use transforms.
      importMap?: {
        [packageName: string]: {
          [exportName: string]: {
            canonicalImport?: [string, string],
            styledBaseImport?: [string, string],
          }
        }
      },
    },
  },
}
```

### Minification

Next.js' swc compiler is used for minification by default since v13. This is 7x faster than Terser.

> **Good to know:** Starting with v15, minification cannot be customized using `next.config.js`. Support for the `swcMinify` flag has been removed.

### Module Transpilation

Next.js can automatically transpile and bundle dependencies from local packages (like monorepos) or from external dependencies (`node_modules`). This replaces the `next-transpile-modules` package.

```js filename="next.config.js"
module.exports = {
  transpilePackages: ['@acme/ui', 'lodash-es'],
}
```

### Modularize Imports

This option has been superseded by [`optimizePackageImports`](/docs/app/api-reference/config/next-config-js/optimizePackageImports) in Next.js 13.5. We recommend upgrading to use the new option that does not require manual configuration of import paths.

### Define (Replacing variables during build)

The `define` option allows you to statically replace variables in your code at build-time.
The option takes an object as key-value pairs, where the keys are the variables that should be replaced with the corresponding values.

Use the `compiler.define` field in `next.config.js` to define variables for all environments (server, edge, and client). Or, use `compiler.defineServer` to define variables only for server-side (server and edge) code:

```js filename="next.config.js"
module.exports = {
  compiler: {
    define: {
      MY_VARIABLE: 'my-string',
      'process.env.MY_ENV_VAR': 'my-env-var',
    },
    defineServer: {
      MY_SERVER_VARIABLE: 'my-server-var',
    },
  },
}
```

### Build Lifecycle Hooks

The Next.js Compiler supports lifecycle hooks that allow you to run custom code at specific points during the build process. Currently, the following hook is supported:

#### runAfterProductionCompile

A hook function that executes after production build compilation finishes, but before running post-compilation tasks such as type checking and static page generation. This hook provides access to project metadata including the project directory and build output directory, making it useful for third-party tools to collect build outputs like sourcemaps.

```js filename="next.config.js"
module.exports = {
  compiler: {
    runAfterProductionCompile: async ({ distDir, projectDir }) => {
      // Your custom code here
    },
  },
}
```

The hook receives an object with the following properties:

* `distDir`: The build output directory (defaults to `.next`)
* `projectDir`: The root directory of the project

## Experimental Features

### SWC Trace profiling

You can generate SWC's internal transform traces as chromium's [trace event format](https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview?mode=html#%21=).

```js filename="next.config.js"
module.exports = {
  experimental: {
    swcTraceProfiling: true,
  },
}
```

Once enabled, swc will generate trace named as `swc-trace-profile-${timestamp}.json` under `.next/`. Chromium's trace viewer (chrome://tracing/, https://ui.perfetto.dev/), or compatible flamegraph viewer (https://www.speedscope.app/) can load & visualize generated traces.

### SWC Plugins (experimental)

You can configure swc's transform to use SWC's experimental plugin support written in wasm to customize transformation behavior.

```js filename="next.config.js"
module.exports = {
  experimental: {
    swcPlugins: [
      [
        'plugin',
        {
          ...pluginOptions,
        },
      ],
    ],
  },
}
```

`swcPlugins` accepts an array of tuples for configuring plugins. A tuple for the plugin contains the path to the plugin and an object for plugin configuration. The path to the plugin can be an npm module package name or an absolute path to the `.wasm` binary itself.

## Unsupported Features

When your application has a `.babelrc` file, Next.js will automatically fall back to using Babel for transforming individual files. This ensures backwards compatibility with existing applications that leverage custom Babel plugins.

If you're using a custom Babel setup, [please share your configuration](https://github.com/vercel/next.js/discussions/30174). We're working to port as many commonly used Babel transformations as possible, as well as supporting plugins in the future.

## Version History

| Version   | Changes                                                                                                                                                                                                  |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `v13.1.0` | [Module Transpilation](https://nextjs.org/blog/next-13-1#built-in-module-transpilation-stable) and [Modularize Imports](https://nextjs.org/blog/next-13-1#import-resolution-for-smaller-bundles) stable. |
| `v13.0.0` | SWC Minifier enabled by default.                                                                                                                                                                         |
| `v12.3.0` | SWC Minifier [stable](https://nextjs.org/blog/next-12-3#swc-minifier-stable).                                                                                                                            |
| `v12.2.0` | [SWC Plugins](#swc-plugins-experimental) experimental support added.                                                                                                                                     |
| `v12.1.0` | Added support for Styled Components, Jest, Relay, Remove React Properties, Legacy Decorators, Remove Console, and jsxImportSource.                                                                       |
| `v12.0.0` | Next.js Compiler [introduced](https://nextjs.org/blog/next-12).                                                                                                                                          |

---
title: Supported Browsers
description: Browser support and which JavaScript features are supported by Next.js.
url: "https://nextjs.org/docs/architecture/supported-browsers"
version: 16.2.6
---

# Supported Browsers

Next.js supports **modern browsers** with zero configuration.

* Chrome 111+
* Edge 111+
* Firefox 111+
* Safari 16.4+

## Browserslist

If you would like to target specific browsers or features, Next.js supports [Browserslist](https://browsersl.ist) configuration in your `package.json` file. Next.js uses the following Browserslist configuration by default:

```json filename="package.json"
{
  "browserslist": ["chrome 111", "edge 111", "firefox 111", "safari 16.4"]
}
```

## Polyfills

We inject [widely used polyfills](https://github.com/vercel/next.js/blob/canary/packages/next-polyfill-nomodule/src/index.js), including:

* [**fetch()**](https://developer.mozilla.org/docs/Web/API/Fetch_API) — Replacing: `whatwg-fetch` and `unfetch`.
* [**URL**](https://developer.mozilla.org/docs/Web/API/URL) — Replacing: the [`url` package (Node.js API)](https://nodejs.org/api/url.html).
* [**Object.assign()**](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Object/assign) — Replacing: `object-assign`, `object.assign`, and `core-js/object/assign`.

If any of your dependencies include these polyfills, they’ll be eliminated automatically from the production build to avoid duplication.

In addition, to reduce bundle size, Next.js will only load these polyfills for browsers that require them. The majority of the web traffic globally will not download these polyfills.

### Custom Polyfills

If your own code or any external npm dependencies require features not supported by your target browsers (such as IE 11), you need to add polyfills yourself.

#### In App Router

To include polyfills, you can import them into the [`instrumentation-client.js` file](/docs/app/api-reference/file-conventions/instrumentation-client).

```ts filename="instrumentation-client.ts"
import './polyfills'
```

#### In Pages Router

In this case, you should add a top-level import for the **specific polyfill** you need in your [Custom ``](/docs/pages/building-your-application/routing/custom-app) or the individual component.

```tsx filename="pages/_app.tsx" switcher
import './polyfills'

import type { AppProps } from 'next/app'

export default function MyApp({ Component, pageProps }: AppProps) {
  return
}
```

```jsx filename="pages/_app.jsx" switcher
import './polyfills'

export default function MyApp({ Component, pageProps }) {
  return
}
```

#### Conditionally loading polyfills

The best approach is to isolate unsupported features to specific UI sections and conditionally load the polyfill if needed.

```ts filename="hooks/analytics.ts" switcher
import { useCallback } from 'react'

export const useAnalytics = () => {
  const tracker = useCallback(async (data: unknown) => {
    if (!('structuredClone' in globalThis)) {
      import('polyfills/structured-clone').then((mod) => {
        globalThis.structuredClone = mod.default
      })
    }

    /* Do some work that uses structured clone */
  }, [])

  return tracker
}
```

```js filename="hooks/analytics.js" switcher
import { useCallback } from 'react'

export const useAnalytics = () => {
  const tracker = useCallback(async (data) => {
    if (!('structuredClone' in globalThis)) {
      import('polyfills/structured-clone').then((mod) => {
        globalThis.structuredClone = mod.default
      })
    }

    /* Do some work that uses structured clone */
  }, [])

  return tracker
}
```

## JavaScript Language Features

Next.js allows you to use the latest JavaScript features out of the box. In addition to [ES6 features](https://github.com/lukehoban/es6features), Next.js also supports:

* [Async/await](https://github.com/tc39/ecmascript-asyncawait) (ES2017)
* [Object Rest/Spread Properties](https://github.com/tc39/proposal-object-rest-spread) (ES2018)
* [Dynamic `import()`](https://github.com/tc39/proposal-dynamic-import) (ES2020)
* [Optional Chaining](https://github.com/tc39/proposal-optional-chaining) (ES2020)
* [Nullish Coalescing](https://github.com/tc39/proposal-nullish-coalescing) (ES2020)
* [Class Fields](https://github.com/tc39/proposal-class-fields) and [Static Properties](https://github.com/tc39/proposal-static-class-features) (ES2022)
* and more!

### TypeScript Features

Next.js has built-in TypeScript support. [Learn more here](/docs/pages/api-reference/config/typescript).

### Customizing Babel Config (Advanced)

You can customize babel configuration. [Learn more here](/docs/pages/guides/babel).

---
title: Community
description: Get involved in the Next.js community.
url: "https://nextjs.org/docs/community"
version: 16.2.6
---

# Community

With over 5 million weekly downloads, Next.js has a large and active community of developers across the world. Here's how you can get involved in our community:

## Contributing

There are a couple of ways you can contribute to the development of Next.js:

* [Documentation](/docs/community/contribution-guide): Suggest improvements or even write new sections to help our users understand how to use Next.js.
* [Examples](https://github.com/vercel/next.js/tree/canary/examples): Help developers integrate Next.js with other tools and services by creating a new example or improving an existing one.
* [Codebase](https://github.com/vercel/next.js/tree/canary/contributing/core): Learn more about the underlying architecture, contribute to bug fixes, errors, and suggest new features.

## Discussions

If you have a question about Next.js, or want to help others, you're always welcome to join the conversation:

* [GitHub Discussions](https://github.com/vercel/next.js/discussions)
* [Discord](https://discord.com/invite/bUG2bvbtHy)
* [Reddit](https://www.reddit.com/r/nextjs)

## Social Media

Follow Next.js on [Twitter](https://x.com/nextjs) for the latest updates, and subscribe to the [Vercel YouTube channel](https://www.youtube.com/@VercelHQ) for Next.js videos.

## Code of Conduct

We believe in creating an inclusive, welcoming community. As such, we ask all members to adhere to our [Code of Conduct](https://github.com/vercel/next.js/blob/canary/CODE_OF_CONDUCT.md). This document outlines our expectations for participant behavior. We invite you to read it and help us maintain a safe and respectful environment.

 - [Contribution Guide](/docs/community/contribution-guide)
 - [Rspack](/docs/community/rspack)

---
title: Contribution Guide
description: Learn how to contribute to Next.js Documentation
url: "https://nextjs.org/docs/community/contribution-guide"
version: 16.2.6
---

# Contribution Guide

Welcome to the Next.js Docs Contribution Guide! We're excited to have you here.

This page provides instructions on how to edit the Next.js documentation. Our goal is to ensure that everyone in the community feels empowered to contribute and improve our docs.

## Why Contribute?

Open-source work is never done, and neither is documentation. Contributing to docs is a good way for beginners to get involved in open-source and for experienced developers to clarify more complex topics while sharing their knowledge with the community.

By contributing to the Next.js docs, you're helping us build a more robust learning resource for all developers. Whether you've found a typo, a confusing section, or you've realized that a particular topic is missing, your contributions are welcomed and appreciated.

## How to Contribute

The docs content can be found on the [Next.js repo](https://github.com/vercel/next.js/tree/canary/docs). To contribute, you can edit the files directly on GitHub or clone the repo and edit the files locally.

### GitHub Workflow

If you're new to GitHub, we recommend reading the [GitHub Open Source Guide](https://opensource.guide/how-to-contribute/#opening-a-pull-request) to learn how to fork a repository, create a branch, and submit a pull request.

> **Good to know**: The underlying docs code lives in a private codebase that is synced to the Next.js public repo. This means that you can't preview the docs locally. However, you'll see your changes on [nextjs.org](https://nextjs.org/docs) after merging a pull request.

### Writing MDX

The docs are written in [MDX](https://mdxjs.com/), a markdown format that supports JSX syntax. This allows us to embed React components in the docs. See the [GitHub Markdown Guide](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) for a quick overview of markdown syntax.

### VSCode

#### Previewing Changes Locally

VSCode has a built-in markdown previewer that you can use to see your edits locally. To enable the previewer for MDX files, you'll need to add a configuration option to your user settings.

Open the command palette (`⌘ + ⇧ + P` on Mac or `Ctrl + Shift + P` on Windows) and search from `Preferences: Open User Settings (JSON)`.

Then, add the following line to your `settings.json` file:

```json filename="settings.json"
{
  "files.associations": {
    "*.mdx": "markdown"
  }
}
```

Next, open the command palette again, and search for `Markdown: Preview File` or `Markdown: Open Preview to the Side`. This will open a preview window where you can see your formatted changes.

#### Extensions

We also recommend the following extensions for VSCode users:

* [MDX](https://marketplace.visualstudio.com/items?itemName=unifiedjs.vscode-mdx): Intellisense and syntax highlighting for MDX.
* [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode): Format MDX files on save.

### Review Process

Once you've submitted your contribution, the Next.js or Developer Experience teams will review your changes, provide feedback, and merge the pull request when it's ready.

Please let us know if you have any questions or need further assistance in your PR's comments. Thank you for contributing to the Next.js docs and being a part of our community!

> **Tip:** Run `pnpm prettier-fix` to run Prettier before submitting your PR.

## File Structure

The docs use **file-system routing**. Each folder and files inside [`/docs`](https://github.com/vercel/next.js/tree/canary/docs) represent a route segment. These segments are used to generate the URL paths, navigation, and breadcrumbs.

The file structure reflects the navigation that you see on the site, and by default, navigation items are sorted alphabetically. However, we can change the order of the items by prepending a two-digit number (`00-`) to the folder or file name.

For example, in the [functions API Reference](/docs/app/api-reference/functions), the pages are sorted alphabetically because it makes it easier for developers to find a specific function:

```txt
04-functions
├── after.mdx
├── cacheLife.mdx
├── cacheTag.mdx
└── ...
```

But, in the [app router section](/docs/app), the files are prefixed with a two-digit number, sorted in the order developers should learn these concepts:

```txt
01-getting-started
├── 01-installation.mdx
├── 02-project-structure.mdx
├── 03-layouts-and-pages.mdx
└── ...
```

To quickly find a page, you can use `⌘ + P` (Mac) or `Ctrl + P` (Windows) to open the search bar on VSCode. Then, type the slug of the page you're looking for. E.g. `installation`

> **Why not use a manifest?**
>
> We considered using a manifest file (another popular way to generate the docs navigation), but we found that a manifest would quickly get out of sync with the files. File-system routing forces us to think about the structure of the docs and feels more native to Next.js.

## Metadata

Each page has a metadata block at the top of the file separated by three dashes.

### Required Fields

The following fields are **required**:

| Field         | Description                                                                  |
| ------------- | ---------------------------------------------------------------------------- |
| `title`       | The page's `` title, used for SEO and OG Images.                         |
| `description` | The page's description, used in the `` tag for SEO. |

```yaml filename="required-fields.mdx"
---
title: Page Title
description: Page Description
---
```

It's good practice to limit the page title to 2-3 words (e.g. Optimizing Images) and the description to 1-2 sentences (e.g. Learn how to optimize images in Next.js).

### Optional Fields

The following fields are **optional**:

| Field       | Description                                                                                                                                        |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `nav_title` | Overrides the page's title in the navigation. This is useful when the page's title is too long to fit. If not provided, the `title` field is used. |
| `source`    | Pulls content into a shared page. See [Shared Pages](#shared-pages).                                                                               |
| `related`   | A list of related pages at the bottom of the document. These will automatically be turned into cards. See [Related Links](#related-links).         |
| `version`   | A stage of development. e.g. `experimental`,`legacy`,`unstable`,`RC`                                                                               |

```yaml filename="optional-fields.mdx"
---
nav_title: Nav Item Title
source: app/building-your-application/optimizing/images
related:
  description: See the image component API reference.
  links:
    - app/api-reference/components/image
version: experimental
---
```

## `App` and `Pages` Docs

Since most of the features in the **App Router** and **Pages Router** are completely different, their docs for each are kept in separate sections (`02-app` and `03-pages`). However, there are a few features that are shared between them.

### Shared Pages

To avoid content duplication and risk the content becoming out of sync, we use the `source` field to pull content from one page into another. For example, the `` component behaves *mostly* the same in **App** and **Pages**. Instead of duplicating the content, we can pull the content from `app/.../link.mdx` into `pages/.../link.mdx`:

```mdx filename="app/.../link.mdx"
---
title:
description: API reference for the  component.
---

This API reference will help you understand how to use the props
and configuration options available for the Link Component.
```

```mdx filename="pages/.../link.mdx"
---
title:
description: API reference for the  component.
source: app/api-reference/components/link
---

{/* DO NOT EDIT THIS PAGE. */}
{/* The content of this page is pulled from the source above. */}
```

We can therefore edit the content in one place and have it reflected in both sections.

### Shared Content

In shared pages, sometimes there might be content that is **App Router** or **Pages Router** specific. For example, the `` component has a `shallow` prop that is only available in **Pages** but not in **App**.

To make sure the content only shows in the correct router, we can wrap content blocks in an `` or `` components:

```mdx filename="app/.../link.mdx"
This content is shared between App and Pages.

This content will only be shown on the Pages docs.

This content is shared between App and Pages.
```

You'll likely use these components for examples and code blocks.

## Code Blocks

Code blocks should contain a minimum working example that can be copied and pasted. This means that the code should be able to run without any additional configuration.

For example, if you're showing how to use the `` component, you should include the `import` statement and the `` component itself.

```tsx filename="app/page.tsx"
import Link from 'next/link'

export default function Page() {
  return About
}
```

Always run examples locally before committing them. This will ensure that the code is up-to-date and working.

### Language and Filename

Code blocks should have a header that includes the language and the `filename`. For example:

````mdx filename="code-example.mdx"
```tsx filename="app/page.tsx"
export default function Page() {
  return Hello, Next.js!

}
```
````

For CLI commands, use the `package` prop to show the command for each package manager:

````mdx filename="code-example.mdx"
```bash package="pnpm"
pnpm create next-app
```

```bash package="npm"
npx create-next-app@latest
```

```bash package="yarn"
yarn create next-app
```

```bash package="bun"
bun create next-app
```
````

Most examples in the docs are written in `tsx` and `jsx`, and a few in `bash`. However, you can use any supported language, here's the [full list](https://github.com/shikijs/shiki/blob/main/docs/languages.md#all-languages).

When writing JavaScript code blocks, we use the following language and extension combinations.

|                                | Language   | Extension |
| ------------------------------ | ---------- | --------- |
| JavaScript files with JSX code | ` ```jsx ` | .js       |
| JavaScript files without JSX   | ` ```js `  | .js       |
| TypeScript files with JSX      | ` ```tsx ` | .tsx      |
| TypeScript files without JSX   | ` ```ts `  | .ts       |

> **Good to know**:
>
> * Make sure to use **`.js`** extension for JavaScript files with **JSX** code.
> * For example, ` ```jsx filename="app/layout.js" `

### TS and JS Switcher

Add a language switcher to toggle between TypeScript and JavaScript. Code blocks should be TypeScript first with a JavaScript version to accommodate users.

Currently, we write TS and JS examples one after the other, and link them with `switcher` prop:

````mdx filename="code-example.mdx"
```tsx filename="app/page.tsx" switcher

```

```jsx filename="app/page.js" switcher

```
````

> **Good to know**: We plan to automatically compile TypeScript snippets to JavaScript in the future. In the meantime, you can use [transform.tools](https://transform.tools/typescript-to-javascript).

### Line Highlighting

Code lines can be highlighted. This is useful when you want to draw attention to a specific part of the code. You can highlight lines by passing a number to the `highlight` prop.

**Single Line:** `highlight={1}`

```tsx filename="app/page.tsx" {1}
import Link from 'next/link'

export default function Page() {
  return About
}
```

**Multiple Lines:** `highlight={1,3}`

```tsx filename="app/page.tsx" highlight={1,3}
import Link from 'next/link'

export default function Page() {
  return About
}
```

**Range of Lines:** `highlight={1-5}`

```tsx filename="app/page.tsx" highlight={1-5}
import Link from 'next/link'

export default function Page() {
  return About
}
```

## Icons

The following icons are available for use in the docs:

```mdx filename="mdx-icon.mdx"

```

**Output:**

✓

✗

We do not use emojis in the docs.

## Notes

For information that is important but not critical, use notes. Notes are a good way to add information without distracting the user from the main content.

```mdx filename="notes.mdx"
> **Good to know**: This is a single line note.

> **Good to know**:
>
> - We also use this format for multi-line notes.
> - There are sometimes multiple items worth knowing or keeping in mind.
```

**Output:**

> **Good to know**: This is a single line note.

> **Good to know**:
>
> * We also use this format for multi-line notes.
> * There are sometimes multiple items worth knowing or keeping in mind.

## Related Links

Related Links guide the user's learning journey by adding links to logical next steps.

* Links will be displayed in cards under the main content of the page.
* Links will be automatically generated for pages that have child pages.

Create related links using the `related` field in the page's metadata.

```yaml filename="example.mdx"
---
related:
  description: Learn how to quickly get started with your first application.
  links:
    - app/building-your-application/routing/defining-routes
    - app/building-your-application/data-fetching
    - app/api-reference/file-conventions/page
---
```

### Nested Fields

| Field         | Required? | Description                                                                                                                                               |
| ------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`       | Optional  | The title of the card list. Defaults to **Next Steps**.                                                                                                   |
| `description` | Optional  | The description of the card list.                                                                                                                         |
| `links`       | Required  | A list of links to other doc pages. Each list item should be a relative URL path (without a leading slash) e.g. `app/api-reference/file-conventions/page` |

## Diagrams

Diagrams are a great way to explain complex concepts. We use [Figma](https://www.figma.com/) to create diagrams, following Vercel's design guide.

The diagrams currently live in the `/public` folder in our private Next.js site. If you'd like to update or add a diagram, please open a [GitHub issue](https://github.com/vercel/next.js/issues/new?assignees=\&labels=template%3A+documentation\&projects=\&template=4.docs_request.yml\&title=Docs%3A+) with your ideas.

## Custom Components and HTML

These are the React Components available for the docs: `` (next/image), ``, ``, ``, and ``. We do not allow raw HTML in the docs besides the `` tag.

If you have ideas for new components, please open a [GitHub issue](https://github.com/vercel/next.js/issues/new/choose).

## Style Guide

This section contains guidelines for writing docs for those who are new to technical writing.

### Page Templates

While we don't have a strict template for pages, there are page sections you'll see repeated across the docs:

* **Overview:** The first paragraph of a page should tell the user what the feature is and what it's used for. Followed by a minimum working example or its API reference.
* **Convention:** If the feature has a convention, it should be explained here.
* **Examples**: Show how the feature can be used with different use cases.
* **API Tables**: API Pages should have an overview table at the of the page with jump-to-section links (when possible).
* **Next Steps (Related Links)**: Add links to related pages to guide the user's learning journey.

Feel free to add these sections as needed.

### Page Types

Docs pages are also split into two categories: Conceptual and Reference.

* **Conceptual** pages are used to explain a concept or feature. They are usually longer and contain more information than reference pages. In the Next.js docs, conceptual pages are found in the **Building Your Application** section.
* **Reference** pages are used to explain a specific API. They are usually shorter and more focused. In the Next.js docs, reference pages are found in the **API Reference** section.

> **Good to know**: Depending on the page you're contributing to, you may need to follow a different voice and style. For example, conceptual pages are more instructional and use the word *you* to address the user. Reference pages are more technical, they use more imperative words like "create, update, accept" and tend to omit the word *you*.

### Voice

Here are some guidelines to maintain a consistent style and voice across the docs:

* Write clear, concise sentences. Avoid tangents.
  * If you find yourself using a lot of commas, consider breaking the sentence into multiple sentences or use a list.
  * Swap out complex words for simpler ones. For example, *use* instead of *utilize*.
* Be mindful with the word *this*. It can be ambiguous and confusing, don't be afraid to repeat the subject of the sentence if unclear.
  * For example, *Next.js uses React* instead of *Next.js uses this*.
* Use an active voice instead of passive. An active sentence is easier to read.
  * For example, *Next.js uses React* instead of *React is used by Next.js*. If you find yourself using words like *was* and *by* you may be using a passive voice.
* Avoid using words like *easy*, *quick*, *simple*, *just*, etc. This is subjective and can be discouraging to users.
* Avoid negative words like *don't*, *can't*, *won't*, etc. This can be discouraging to readers.
  * For example, *"You can use the `Link` component to create links between pages"* instead of *"Don't use the `` tag to create links between pages"*.
* Write in second person (you/your). This is more personal and engaging.
* Use gender-neutral language. Use *developers*, *users*, or *readers*, when referring to the audience.
* If adding code examples, ensure they are properly formatted and working.

While these guidelines are not exhaustive, they should help you get started. If you'd like to dive deeper into technical writing, check out the [Google Technical Writing Course](https://developers.google.com/tech-writing/overview).

***

Thank you for contributing to the docs and being part of the Next.js community!

---
title: Rspack
description: "Use the `next-rspack` plugin to bundle your Next.js with Rspack."
url: "https://nextjs.org/docs/community/rspack"
version: 16.2.6
---

# Rspack

> This feature is currently experimental and subject to change, it's not recommended for production. Try it out and share your feedback on [GitHub](https://github.com/vercel/next.js/issues).

The Rspack team has created a community plugin for Next.js, which is part of a [partnering effort](https://rspack.rs/blog/rspack-next-partner) with the Rspack team.

This plugin is currently experimental. Please use this [discussion thread](https://github.com/vercel/next.js/discussions/77800) to give feedback on any issues you encounter.

Learn more on the [Rspack docs](https://rspack.rs/guide/tech/next) and try out [this example](https://github.com/vercel/next.js/tree/canary/examples/with-rspack).
