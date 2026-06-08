---
name: astro
description: Expert for building content-driven web sites with the Astro web framework. Use this skill whenever you create or edit Astro pages, components, layouts, content collections, API routes, integrations, or the astro config — anything involving .astro files, the src/pages router, islands architecture (client:* directives), the astro CLI (dev/build/check/sync/add), SSR adapters (Node/Vercel/Netlify/Cloudflare), View Transitions, or `astro:assets` / `astro:content` / `astro:db`. Trigger this skill on any task that touches an Astro repo, even if Astro is not named explicitly. Before answering, this skill always consults Context7 for current Astro docs (the API moves between minor releases) — and ensures the project's `@` path alias is configured, creating it if missing. For Tailwind specifics see tailwindcss-v4; for HTTP requests inside a page or endpoint see fetch.
---

# Astro

How to build with the Astro web framework. The goal is **content-driven, fast-by-default sites**: HTML is generated up front, JavaScript only ships when a specific island opts into hydration. Style decisions land in **tailwindcss-v4**; HTTP calls inside a page or endpoint land in **fetch**.

## Always consult Context7 before answering

Astro evolves fast between minor releases — `astro:content` types, the asset pipeline, view transitions, content layer, server islands, the adapters' option surfaces and the CLI all see meaningful changes from version to version. Recalling specifics from training data is unreliable.

**Before answering any non-trivial Astro question, fetch current docs through Context7:**

1. `mcp__context7__resolve-library-id` with `"astro"` to get the library id.
2. `mcp__context7__query-docs` with that id and the relevant topic (e.g. `"content collections"`, `"view transitions"`, `"server islands"`, `"@astrojs/node adapter"`, `"image component"`, `"middleware"`).

If Context7 isn't connected, say so to the user and fetch the relevant page on **docs.astro.build** (e.g. `https://docs.astro.build/en/guides/content-collections/`) via the web fetch tool before proposing code. Never present uncertain Astro syntax as fact.

Skip Context7 only for the most basic mechanical questions (what `.astro` looks like, how `Astro.props` is read) where the surface hasn't moved.

---

## Mandatory: the `@` path alias must be configured

Every Astro project this skill touches uses the **`@/*` alias** for cross-directory imports — never long relative paths like `../../../components/Foo.astro`. **Check this at the start of any task; if it's missing, set it up.**

Two files configure it together — both must agree:

**`tsconfig.json`** — register the alias for the TypeScript / editor side:

```jsonc
{
  "extends": "astro/tsconfigs/strict",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**`astro.config.mjs` (or `.ts`)** — expose the alias to Vite so the bundler resolves it the same way:

```ts
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://example.com",
  vite: {
    resolve: {
      alias: {
        "@": "/src",
      },
    },
  },
});
```

After adding either file, run `npx astro sync` so the editor picks up the new types/aliases.

If a project mixes `@/...` imports with `../../...` in the same file, normalise it as part of the task — that's drift waiting to become breakage.

---

## Project structure

Astro fixes the conventions; respect them:

```
src/
  pages/          # required — file-based routing (index.astro → /, about.astro → /about)
  layouts/        # reusable page shells
  components/     # .astro components, framework islands (React/Vue/Svelte/...) live here too
  content/        # content collections (Markdown/MDX + Zod schemas)
  styles/         # global CSS, Tailwind entrypoint
  assets/         # images/fonts processed by Vite (use astro:assets for images)
  middleware.ts   # request/response middleware (optional)
public/           # unprocessed assets copied 1:1 to dist/
astro.config.mjs  # framework config + adapters + integrations
tsconfig.json
package.json
```

Keep `src/components/` flat or one folder per feature — don't grow ad-hoc subfolders.

---

## Pages and routing

Routes come from file names under `src/pages/`:

- `src/pages/index.astro` → `/`
- `src/pages/about.astro` → `/about`
- `src/pages/blog/[slug].astro` → `/blog/:slug` (dynamic segment)
- `src/pages/[...slug].astro` → rest segment
- `src/pages/api/health.ts` → `/api/health` (API endpoint, see **API endpoints** below)

A minimal page:

```astro
---
// src/pages/index.astro — frontmatter runs server-side at build (or per request in SSR)
import Layout from "@/layouts/Base.astro";
import Card from "@/components/Card.astro";

const title = "Centro Médico — Inicio";
---
<Layout title={title}>
  <h1>{title}</h1>
  <Card title="Consultas" body="Servicios disponibles esta semana." />
</Layout>
```

The fence (`---`) holds server code; outside the fence is the template. Anything between `{ }` in the template is JS interpolation.

For dynamic routes generated at build time, export `getStaticPaths()` and return the params + props for each path. Verify the current signature in Context7 — it changes with the content layer.

---

## Components and layouts

A `.astro` component is the default — server-rendered, zero JS unless you ask:

```astro
---
// src/components/Card.astro
type Props = { title: string; body: string };
const { title, body } = Astro.props as Props;
---
<article class="rounded-md border p-4">
  <h2 class="text-lg font-semibold">{title}</h2>
  <p class="text-sm text-neutral-600">{body}</p>
</article>
```

Use **slots** for content projection: `<slot />` (default), `<slot name="header" />` (named). A layout wraps every page:

```astro
---
// src/layouts/Base.astro
type Props = { title: string };
const { title } = Astro.props as Props;
---
<html lang="es">
  <head>
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <slot />
  </body>
</html>
```

Type `Props` explicitly when the component takes more than a couple of fields — it documents the contract and the editor surfaces autocompletion.

---

## Islands architecture — opt into JavaScript

Astro's default output is plain HTML. To run JS for a component on the client, mark it with a `client:*` directive. This is the **only** way JS reaches the browser; if you don't add a directive, nothing hydrates.

| Directive | When to use |
| --- | --- |
| `client:load` | Hydrate immediately on page load. Use for above-the-fold interactivity. |
| `client:idle` | Hydrate when the browser is idle. Use for non-critical interactivity. |
| `client:visible` | Hydrate when the element enters the viewport. Use for below-the-fold widgets. |
| `client:media="(max-width: 768px)"` | Hydrate only when a media query matches. |
| `client:only="react"` | Skip server rendering entirely, render only on the client. Last resort. |

```astro
---
import Counter from "@/components/Counter.tsx";  // a React island
---
<Counter client:visible />
```

The right default is **no directive**. If a button doesn't *need* JS to work (a link styled as a button is fine), don't ship JS for it. Every `client:load` is JS the user pays for on first paint.

For framework islands (React/Vue/Svelte/Solid/Preact), add the integration first: `npx astro add react`.

---

## Content collections — Markdown/MDX with types

The official way to manage content. Define schemas with Zod under `src/content/config.ts`; consume them from pages.

```ts
// src/content/config.ts
import { defineCollection, z } from "astro:content";

const posts = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    publishedAt: z.coerce.date(),
    description: z.string().max(160),
    draft: z.boolean().default(false),
  }),
});

export const collections = { posts };
```

```astro
---
// src/pages/blog/[slug].astro
import { getCollection, getEntry } from "astro:content";

export async function getStaticPaths() {
  const all = await getCollection("posts", ({ data }) => !data.draft);
  return all.map((entry) => ({ params: { slug: entry.slug }, props: { entry } }));
}

const { entry } = Astro.props;
const { Content } = await entry.render();
---
<article>
  <h1>{entry.data.title}</h1>
  <Content />
</article>
```

Run `npx astro sync` after changing the schema so types regenerate. The collection layer has evolved (Content Layer / loaders); verify in Context7 before shipping a non-trivial pattern.

---

## API endpoints

A `.ts`/`.js` file under `src/pages/api/` exports HTTP-method handlers:

```ts
// src/pages/api/health.ts
import type { APIRoute } from "astro";

export const GET: APIRoute = async () => {
  return new Response(JSON.stringify({ status: "ok" }), {
    headers: { "Content-Type": "application/json" },
  });
};
```

For fetching from an endpoint or page, see **fetch** for the request patterns (error handling, AbortController, retries, the standard response envelope).

---

## SSR / hybrid — adapters

Astro defaults to **static** (SSG). For SSR or hybrid (server-rendered pages alongside static), add an adapter and set `output`:

```bash
npx astro add node       # or vercel, netlify, cloudflare
```

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";
import node from "@astrojs/node";

export default defineConfig({
  output: "server",              // or "hybrid" — verify current values in Context7
  adapter: node({ mode: "standalone" }),
});
```

Pages opt out of pre-rendering per-page with `export const prerender = false` when needed. Adapters' options change; consult Context7 for the current shape.

---

## Styling

- **Global styles**: import a CSS file from the root layout once.
- **Scoped styles**: a `<style>` block inside a `.astro` file is automatically scoped to that component.
- **Tailwind v4**: integrate via `@tailwindcss/vite` in `astro.config.mjs` and `@import "tailwindcss";` in the entry CSS. Use the `@theme` block for tokens. Full pattern lives in **tailwindcss-v4** (Context7 mandatory there too — v4 has moved away from `tailwind.config.js`).

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  vite: {
    plugins: [tailwindcss()],
    resolve: { alias: { "@": "/src" } },
  },
});
```

---

## Images

Use `<Image />` from `astro:assets` for any image that lives in `src/` — it processes the asset, generates the right size and format, and emits modern `<picture>` markup:

```astro
---
import { Image } from "astro:assets";
import logo from "@/assets/logo.png";
---
<Image src={logo} alt="Logo" width={200} height={60} />
```

Files in `public/` are copied as-is and **not processed** — use them only for files that mustn't change (favicons, robots.txt, downloads).

---

## View Transitions

Smooth same-origin navigations with one line in the layout:

```astro
---
import { ViewTransitions } from "astro:transitions";
---
<html>
  <head><ViewTransitions /></head>
  <body><slot /></body>
</html>
```

Per-element transitions use `transition:name="…"`. The View Transitions API and Astro's wrapper still evolve — check Context7 for the current import path and supported directives.

---

## CLI commands

```bash
npx astro dev        # dev server with HMR
npx astro build      # production build to dist/
npx astro preview    # preview the built site
npx astro check      # type/diagnostic check (requires @astrojs/check)
npx astro sync       # regenerate types for content collections + env
npx astro add <name> # install + wire an integration (react, tailwind, node, vercel, ...)
```

Re-run `astro sync` after editing the content collection schema, `env.d.ts`, or installing a new integration. Re-run `astro check` before opening a PR — Astro's editor diagnostics catch a class of bugs `tsc` alone misses.

---

## Best practices

- **Server by default, JS by exception.** Every `client:*` directive is a deliberate cost; default to none.
- **Use the `@` alias.** Long relative imports rot when files move.
- **Type `Astro.props`.** A `type Props = { ... }` at the top of each component is documentation that can't go stale.
- **Tailwind tokens, not arbitrary values.** Conditional classes via `cn` (clsx + tailwind-merge); design decisions live in `@theme` (see tailwindcss-v4).
- **Prefer content collections** over hand-loaded Markdown. Types come for free; schemas are enforced.
- **Optimise images with `astro:assets`**. Don't ship raw PNGs from `public/` when they could be processed.
- **Run `astro sync` after schema or integration changes**, and `astro check` before a commit.
- **Don't over-fetch in `getStaticPaths`** — the body runs once per build per path; do the heavy lifting in a loader/util and cache it.
- **Honour the site config** (`site: "https://…"` in `astro.config`) — sitemaps and canonical URLs depend on it.

---

## Common pitfalls

- **Recalling Astro APIs from training data** — verify with Context7; the API moves.
- **Long relative imports** instead of `@/...` — set up the alias first.
- **Forgetting the alias in `astro.config`** — TS resolves it but Vite doesn't, builds fail in dev.
- **Hydrating everything with `client:load`** — pays the JS cost on every page.
- **Putting processed images in `public/`** — they skip the asset pipeline and ship unoptimised.
- **Schema changes without `astro sync`** — types stay stale and `astro check` complains misleadingly.
- **Mixing client-only code in server context** (`window`/`document` in the frontmatter) — wrap in a client island or guard with `import.meta.env.SSR`.
- **Hardcoded absolute URLs** instead of reading `Astro.site` / the `site` config — breaks sitemaps and previews.
