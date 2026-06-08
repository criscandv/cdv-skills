---
name: tanstack-router
description: Expert for TanStack Router — the type-safe SPA router for React. Use whenever you set up routing or add routes to a React + Vite SPA without Next.js: file-based routing with the Vite plugin, `<RouterProvider>` wiring, route definitions, type-safe `<Link>` and `useNavigate`, search params validated with Zod, route loaders integrated with React Query, `beforeLoad` guards for auth, error and pending components. Trigger whenever a task touches `src/routes/`, `createFileRoute`, `RouterProvider`, `useNavigate`, `useSearch`, `useParams`, search params, route loaders, or "the router". **Always consults Context7 before answering** — TanStack Router's API moves between minor versions. Pairs with react-spa (the project setup that this skill plugs into), frontend-data-layer (React Query for loaders), and react-patterns.
---

# TanStack Router

The router for React SPAs that takes type safety seriously. The mental model: **routes are typed end-to-end** — params, search params, loader data, link `to`, `useNavigate` — and the compiler proves it. If the URL changes shape, every consumer fails at compile time, not at runtime.

This skill assumes a Vite + React 19 + TypeScript SPA (see **react-spa**) with React Query already wired (see **frontend-data-layer**). It covers the **router** specifically; component/hook discipline comes from **react-patterns**.

## Always consult Context7 before answering

TanStack Router is fast-moving — the file-based routing model, the `createFileRoute` API, the loader/staleTime integration with React Query, and the search params validators all see breaking-ish changes between minor versions. Recall is unreliable.

**Before answering any non-trivial routing question, fetch current docs through Context7:**

1. `mcp__context7__resolve-library-id` with `"@tanstack/react-router"` (or `"tanstack router"`).
2. `mcp__context7__query-docs` with the relevant topic (`"file-based routing"`, `"search params"`, `"loader"`, `"beforeLoad"`, `"pending component"`, `"error component"`).

If Context7 isn't connected, fetch `https://tanstack.com/router/latest/docs/framework/react` for the relevant page before proposing code. Never present uncertain router syntax as fact.

---

## Setup — the Vite plugin

The recommended path is file-based routing with the router plugin. Once per project:

```bash
pnpm add @tanstack/react-router
pnpm add -D @tanstack/router-plugin
```

Wire the plugin in `vite.config.ts` **before `@vitejs/plugin-react`**:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import path from "node:path";

export default defineConfig({
  plugins: [
    TanStackRouterVite(),  // must come BEFORE the react plugin
    react(),
  ],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
});
```

The plugin watches `src/routes/` and generates `src/routeTree.gen.ts` (a typed tree of every route). **Never edit `routeTree.gen.ts` by hand** — it's regenerated; add it to `.gitignore` if you prefer, or commit it to keep diffs visible.

Then mount the router in `main.tsx`:

```tsx
// src/main.tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createRouter } from "@tanstack/react-router";

import { queryClient } from "@/lib/query-client";
import { routeTree } from "./routeTree.gen";
import "@/styles/globals.css";

const router = createRouter({
  routeTree,
  context: { queryClient },           // makes queryClient available to loaders/beforeLoad
  defaultPreload: "intent",           // prefetch on hover/focus
});

// Register the router for type-safety across the app.
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
```

The `declare module` block is what makes `<Link>` and `useNavigate` type-safe across the whole app. Forget it and you lose the headline feature.

---

## File-based routing

A file under `src/routes/` becomes a route. Filename conventions:

| File | Route |
| --- | --- |
| `src/routes/__root.tsx` | The root layout (renders `<Outlet />`). Mandatory. |
| `src/routes/index.tsx` | `/` |
| `src/routes/about.tsx` | `/about` |
| `src/routes/users.tsx` | `/users` (layout for the segment if it has children) |
| `src/routes/users/$userId.tsx` | `/users/:userId` (dynamic param) |
| `src/routes/users/index.tsx` | `/users` (when `users.tsx` is a layout) |
| `src/routes/_authed.tsx` | **Pathless** layout (groups children without adding to the URL) |
| `src/routes/_authed/dashboard.tsx` | `/dashboard` — rendered inside the `_authed` guarded shell |

**Pathless layouts** (filename starts with `_`) are the cleanest way to group routes that share a layout *and* a guard — for example, every authenticated screen under one shell with a single `beforeLoad` that redirects to `/login` when there's no session.

### The root layout

```tsx
// src/routes/__root.tsx
import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import type { QueryClient } from "@tanstack/react-query";

interface RouterContext {
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
});

function RootLayout() {
  return (
    <>
      <Outlet />
    </>
  );
}
```

Typing the context here (`QueryClient`) is what makes it available with the right type in every loader/`beforeLoad` below.

### A typical leaf route

```tsx
// src/routes/users/$userId.tsx
import { createFileRoute } from "@tanstack/react-router";

import { userQueryOptions } from "@/features/users/hooks/use-user";

export const Route = createFileRoute("/users/$userId")({
  loader: ({ context: { queryClient }, params: { userId } }) =>
    queryClient.ensureQueryData(userQueryOptions(userId)),
  component: UserDetail,
  pendingComponent: () => <p>Cargando…</p>,
  errorComponent: ({ error }) => <p>Algo falló: {error.message}</p>,
});

function UserDetail() {
  const { userId } = Route.useParams();
  // The loader's data is cached by React Query; read via the hook in the feature.
  const { user } = useUser(userId);
  return <div>{user.email}</div>;
}
```

- **`Route.useParams()`** is typed — `userId` is a `string`, not `string | undefined`.
- **`loader` returns a promise** — the router awaits it before rendering. Pair it with React Query (`ensureQueryData`) so the cache is warm before the component renders.
- **`pendingComponent` / `errorComponent`** are per-route — keep loading/error UX colocated with the route they describe.

---

## Search params with Zod — the standout feature

URLs aren't just for paths; the **search params** (the `?foo=bar&page=2` part) are first-class. TanStack Router validates them with a schema, types them, and synchronises them with `useSearch` / `useNavigate`.

```tsx
// src/routes/invoices/index.tsx
import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

const searchSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  status: z.enum(["all", "draft", "sent", "paid"]).default("all"),
  q: z.string().optional(),
});

export const Route = createFileRoute("/invoices/")({
  validateSearch: searchSchema,
  loaderDeps: ({ search }) => ({ page: search.page, status: search.status, q: search.q }),
  loader: ({ deps, context: { queryClient } }) =>
    queryClient.ensureQueryData(invoicesQueryOptions(deps)),
  component: InvoicesList,
});

function InvoicesList() {
  const { page, status, q } = Route.useSearch();
  const navigate = Route.useNavigate();

  return (
    <div>
      <input
        value={q ?? ""}
        onChange={(e) => navigate({ search: (prev) => ({ ...prev, q: e.target.value, page: 1 }) })}
      />
      ...
    </div>
  );
}
```

- **`validateSearch`** runs the schema on every navigation; invalid params get coerced or fall back to defaults — no manual parsing, no `string | undefined` everywhere.
- **`loaderDeps`** is what the loader depends on; when those change, the loader re-runs (so filters and pagination naturally re-fetch).
- **`navigate({ search: prev => ... })`** updates the URL with a typed callback — the router infers the search type from `validateSearch`.

If you're using `useState` to hold a list filter, that's almost always a sign it should be a search param instead. The URL is the source of truth; the user can refresh, share, and back-button into the same view.

---

## Auth guards — `beforeLoad`

`beforeLoad` runs before the loader; it can read context, throw a redirect, or short-circuit:

```tsx
// src/routes/_authed.tsx
import { createFileRoute, redirect, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/_authed")({
  beforeLoad: ({ context: { queryClient }, location }) => {
    const session = queryClient.getQueryData(["session"]);
    if (!session) {
      throw redirect({
        to: "/login",
        search: { redirect: location.href },
      });
    }
  },
  component: AuthedLayout,
});

function AuthedLayout() {
  return (
    <>
      <Header />
      <Outlet />
    </>
  );
}
```

Every route under `_authed/` inherits this guard. `redirect()` is the right way — don't `navigate()` from inside `beforeLoad`, it bypasses the lifecycle.

For login + redirect-back, read the `redirect` search param on `/login`:

```tsx
export const Route = createFileRoute("/login")({
  validateSearch: z.object({ redirect: z.string().optional() }),
  component: LoginPage,
});
```

---

## Loaders + React Query — the recommended pattern

The router's loader runs server-side-style (well, on the client, but before render), and React Query owns the cache. The shape that scales:

```ts
// src/features/invoices/hooks/use-invoices.ts
import { queryOptions, useQuery } from "@tanstack/react-query";
import { fetchInvoices } from "../services/invoices-api";

export function invoicesQueryOptions(filters: InvoiceFilters) {
  return queryOptions({
    queryKey: ["invoices", filters],
    queryFn: () => fetchInvoices(filters),
    staleTime: 30_000,
  });
}

export function useInvoices(filters: InvoiceFilters) {
  return useQuery(invoicesQueryOptions(filters));
}
```

Then the loader uses `ensureQueryData(invoicesQueryOptions(...))` and the component reads via `useInvoices(...)`. The same query key drives both — the loader warms the cache, the component reads it instantly, and invalidations work normally.

See **frontend-data-layer** for the broader server-state-vs-UI-state split.

---

## Type-safe navigation

Once the `declare module` is in place, `<Link>` and `useNavigate` know every route. The compiler refuses to navigate to a route that doesn't exist or to omit a required param.

```tsx
import { Link, useNavigate } from "@tanstack/react-router";

<Link to="/users/$userId" params={{ userId: "42" }} search={{ tab: "overview" }}>
  View user
</Link>

const navigate = useNavigate();
navigate({ to: "/invoices", search: { page: 2, status: "paid" } });
```

If `tab` doesn't exist on the search schema of `/users/$userId`, this fails at `tsc`. That's the headline; lean into it. Don't `as` your way around a type error from the router — the type is telling you the URL shape is wrong somewhere.

---

## Defaults worth knowing

- **`defaultPreload: "intent"`** — prefetch a route on hover/focus. The cost is small; the perceived speed-up is large. Enable it project-wide.
- **`defaultPreloadStaleTime`** — how long the preloaded data stays fresh. Tune to your data volatility.
- **`scrollRestoration: true`** — restore scroll positions on back/forward. Off by default in some versions; turn on once and forget.

Verify the exact option names against Context7 — they've moved between versions.

---

## Common pitfalls

- **Recalling the API from training data.** Verify with Context7; the surface has changed in non-obvious ways across minor versions.
- **Editing `routeTree.gen.ts` by hand.** It's regenerated; edit the route files under `src/routes/` instead.
- **Forgetting the `declare module` registration** in `main.tsx`. Without it, `<Link>` and `useNavigate` lose type-safety silently.
- **`useState` for a list filter** when it should be a search param. The URL is the source of truth.
- **`navigate()` inside `beforeLoad`** instead of `throw redirect(...)`. Bypasses the lifecycle and skips loaders.
- **Loader without `loaderDeps`** when search params should drive the fetch — the loader doesn't re-run when filters change.
- **Same query key in two places with different shapes** between the loader and a component hook — cache misses where you don't expect them.
- **Plugin ordered after `@vitejs/plugin-react`** in `vite.config` — the generated tree is out of sync with the imports.
- **Top-level fallback in `__root.tsx` for everything** — per-route `pendingComponent`/`errorComponent` give better UX.
