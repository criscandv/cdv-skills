---
name: nextjs-patterns
description: Deep reference for building Next.js applications with the App Router (Next 13+/15). Use this skill whenever you work in a Next.js project — creating routes, pages, layouts, route groups, API route handlers, deciding server vs client components, wiring metadata, handling env vars, or importing browser-only libraries. Trigger it whenever a task touches the app/ directory, "use client", server/client components, loading/error/not-found files, route handlers, or NEXT_PUBLIC_ env vars, even if Next.js is not named explicitly. It is the framework companion to frontend-conventions (the rulebook), react-patterns, typescript-patterns and frontend-data-layer.
---

# Next.js Patterns (App Router)

How we build with the Next.js App Router. General React/TS style lives in **react-patterns** and **typescript-patterns**; this skill is Next-specific structure and behaviour.

The guiding idea: **everything is a Server Component until it needs the browser.** Server Components keep JS off the client, run close to data, and never ship to the bundle. Add `"use client"` only at the boundary where interactivity, state, effects or browser APIs actually begin.

---

## app/ structure

```
app/
  layout.tsx              # root layout (required): <html>/<body>, providers
  page.tsx                # /
  (auth)/                 # route group — organises without affecting the URL
    login/page.tsx        # /login
  (with-header)/          # another group: a shared layout for authed pages
    layout.tsx            # wraps its children with the app header
    dashboard/page.tsx    # /dashboard
  api/
    <name>/route.ts       # route handler (GET/POST/...)
  loading.tsx             # route-level suspense fallback
  error.tsx               # route-level error boundary ("use client")
  not-found.tsx           # 404 UI
```

- **Route groups** `(name)/` organise routes and let a subtree share a layout **without** adding a path segment — use them to separate, e.g., public auth pages from the authenticated shell.
- **`page.tsx`, `layout.tsx`, route handlers (`route.ts`)** are loaded by convention and **require `export default`** (the one place the no-default-export rule doesn't apply — see frontend-conventions). Everything else stays named exports.
- **`loading.tsx` / `error.tsx` / `not-found.tsx`** are the framework's hooks for suspense, error boundaries and 404s; prefer them over hand-rolled equivalents. `error.tsx` must be a Client Component.

---

## Server vs Client Components

A file is a Server Component by default. Add `"use client"` at the top only when the component needs: state/effects (`useState`, `useEffect`), event handlers, browser-only APIs (`window`, `localStorage`), or a client-only library.

```tsx
// Server Component (default) — can be async, fetch directly, no client JS shipped
export default async function DashboardPage() {
  const stats = await getStats();
  return <StatsView stats={stats} />;
}
```

```tsx
"use client";

// Client Component — interactivity begins here
export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount((value) => value + 1)}>{count}</button>;
}
```

Push the `"use client"` boundary **down** the tree, as close to the interactive leaf as possible. A client component can render server-passed children, so wrapping an entire page in `"use client"` to make one button interactive needlessly ships the whole subtree to the browser.

---

## Data fetching

- **Server Components** fetch directly (`await fetch(...)` / a server-side data call) — no client library, no loading state plumbing.
- **Client Components** fetch through the data layer (React Query) — see **frontend-data-layer**. Don't `fetch` in a `useEffect` and hand-manage loading/error; that's what the query layer is for.
- When a client subtree needs server-fetched data, fetch on the server and pass it down as props, or prefetch into the React Query cache on the server and hydrate.

---

## Route handlers (app/api)

API route handlers live in `app/api/<name>/route.ts` and export named HTTP-method functions. Use them for server-only work the browser can't do directly (proxying with a secret, handling a provider callback, signing a request):

```ts
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const data = await loadServerData(request.nextUrl.searchParams);
  return NextResponse.json(data);
}
```

These are server code: safe to read server-only secrets, never bundled to the client.

---

## Environment variables

Next splits env vars by exposure, and getting this wrong leaks secrets or yields `undefined` in the browser:

- **`NEXT_PUBLIC_*`** are inlined into the client bundle at build time — use only for non-secret, browser-needed values (public API base URL, public client IDs, map tokens).
- **Everything else is server-only** — available in Server Components, route handlers and server config, never shipped to the client. Keep secrets (signing keys, OAuth client secrets, backend keys) here, with **no** `NEXT_PUBLIC_` prefix.

Read them via a typed config module rather than scattering `process.env.X` across the codebase, and never reference a non-public var in a Client Component.

---

## Browser-only libraries and SSR

A library that touches `window`/`document` at import time will crash during server rendering. Import it **dynamically inside an effect** (or via `next/dynamic` with `ssr: false`) so it loads only in the browser:

```tsx
"use client";

useEffect(() => {
  let cancelled = false;
  import("some-browser-only-lib").then((module) => {
    if (!cancelled) {
      module.init();
    }
  });
  return () => {
    cancelled = true;
  };
}, []);
```

This is the standard fix for PDF/canvas/editor libraries and anything that assumes a DOM at module load.

---

## Metadata

Use the App Router metadata API for titles, descriptions and Open Graph — a static `metadata` export or a `generateMetadata` function — rather than manually injecting `<head>` tags.

```ts
export const metadata = { title: "Dashboard", description: "..." };
```

---

## Common pitfalls

- **`"use client"` too high** — ships an entire subtree to the browser to make one leaf interactive; push the boundary down.
- **Fetching in `useEffect`** in a client component — use the data layer; in a server component, fetch directly.
- **A non-`NEXT_PUBLIC_` var read in the browser** — it's `undefined`; or worse, prefixing a secret with `NEXT_PUBLIC_` and leaking it.
- **Importing a browser-only lib at module top level** — crashes SSR; import dynamically in an effect.
- **Hand-rolled 404/loading/error UI** instead of `not-found.tsx` / `loading.tsx` / `error.tsx`.
- **Adding `export default` to non-convention files** — only `page`/`layout`/route handlers (and `React.lazy` targets) take a default export.
