---
name: react-spa
description: Expert for building React single-page applications with Vite — React-only, no Next.js. Use this skill whenever you set up or extend a React + Vite project: configuring the `@/*` path alias in both `tsconfig.json` and `vite.config.ts`, typing `import.meta.env` variables, organising the `src/` folder for a SPA (features / routes / lib / components), wiring `main.tsx` and `index.html`, choosing where state and side-effects live. Trigger this whenever a task touches `vite.config`, `import.meta.env.VITE_*`, the SPA `main.tsx` entry, or "this project is React without Next". For component and hook discipline see react-patterns; for routing see tanstack-router; for design tokens and Tailwind see tailwindcss-v4; for shadcn components see shadcn.
---

# React SPA (Vite)

How to set up and organise a React **single-page application** with Vite — for projects that deliberately don't use Next.js. The defaults here assume Vite + React 19 + TypeScript strict; the conventions for components, hooks, types and tests come from the layer skills.

The guiding idea: **a SPA pays for one entry, parsed once, on first load**. That makes the cost of initial bundle size and the layout of `src/` matter more than they do on the server. Keep the entry minimal, the folder structure flat-ish, and the alias resolved consistently across both TypeScript and the bundler so imports never break.

---

## Stack and minimum

- **Vite 5+** as build / dev server (`@vitejs/plugin-react`).
- **React 19+** (treats `ref` as a regular prop — no `forwardRef` needed; see react-patterns).
- **TypeScript** with `strict: true`. Use the strict tsconfig preset and add `"noUncheckedIndexedAccess": true` for safer array/object indexing.
- **`pnpm`** (or whichever the project uses, but stay consistent — a lockfile per repo, not a mix).

A starter from `npm create vite@latest` is fine; the work this skill does is everything *after* it.

---

## Mandatory: the `@/*` alias in BOTH places

The single most common silent break in a Vite + React project is an alias that the TypeScript compiler resolves but the Vite bundler doesn't (or vice versa). Configure it in **both files** and keep them in sync.

**`tsconfig.json` (or `tsconfig.app.json`)** — for TypeScript / editor / type checking:

```jsonc
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**`vite.config.ts`** — for the actual bundler resolution:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

If a project only has one of the two, imports like `@/components/Button` appear to work in the editor and then fail at `vite build`. Add the missing side as the first step of any task on the repo.

---

## Project structure for a SPA

A working layout that scales from one screen to many features without reshuffling:

```
src/
  main.tsx                 # entry: mounts <App /> into #root
  App.tsx                  # top-level shell — providers + router
  routes/                  # routing config (see tanstack-router)
  features/                # one folder per feature/domain
    <feature>/
      components/          # UI specific to this feature
      hooks/               # feature-specific hooks
      stores/              # Zustand stores (see frontend-data-layer)
      services/ (or api.ts) # HTTP calls (see fetch, frontend-data-layer)
      schemas/             # zod schemas + derived types
      types.ts             # shared types for the feature
      index.ts             # re-exports the feature's public surface
  components/
    ui/                    # shadcn components live here (see shadcn)
    <shared>.tsx           # cross-feature shared components
  hooks/                   # cross-feature hooks
  lib/
    axios.ts (or http.ts)  # single Axios instance (see frontend-data-layer)
    queryClient.ts         # QueryClient singleton (see frontend-data-layer)
    utils.ts               # cn() + small utilities
  styles/
    globals.css            # Tailwind entrypoint + @theme tokens
  types/                   # cross-feature types
  test/                    # vitest helpers (renderWithProviders, MSW server)
public/                    # static assets served as-is
index.html                 # the SPA shell — mount point + manifest links
```

A few rules that keep the structure honest:

- **A feature folder owns its components, hooks, stores and services.** Cross-feature shared things go up to `src/components/`, `src/hooks/`, `src/lib/` — never inside another feature.
- **`components/ui/`** is reserved for **shadcn** components (copied via the CLI, not hand-written). Treat it as machine-generated: don't put bespoke code there.
- **One `index.ts` per feature** re-exporting the public surface (`export { useInvoices } from "./hooks/use-invoices"`). Importing internals from another feature is a smell — the `index.ts` is what other features see.
- **No long relative paths.** Every cross-feature import goes through `@/`. If you see `../../`, refactor.

For routing-specific structure (`src/routes/...` with TanStack Router), see **tanstack-router**.

---

## `main.tsx` — keep it minimal

The SPA entry is loaded synchronously on first paint; it sets up the providers and mounts the app. Everything else loads on demand.

```tsx
// src/main.tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";

import { queryClient } from "@/lib/query-client";
import { router } from "@/routes/router";
import "@/styles/globals.css";

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

- **Throw if `#root` is missing**, don't `as` it. A real error beats a confusing crash three frames deep.
- **`StrictMode` always on** — it surfaces effect double-runs and other React 19 issues in dev.
- **Don't add a top-level error boundary in `main.tsx`** — let the router handle per-route errors; a SPA-wide fallback is for genuinely unrecoverable cases.

---

## `index.html` — the SPA shell

```html
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>tprealestate · backoffice</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- `lang="es"` (or whatever the audience speaks) — accessibility tools and screen readers depend on it.
- One `#root`. No SSR markup. Vite injects the script.
- Add `<link rel="icon">`, the title, and `<meta>` description here — they're static at build time.

---

## Env vars — `import.meta.env.VITE_*` (typed)

Vite exposes env vars to the client only when their name starts with **`VITE_`**. Everything else is server/build-only and doesn't reach the bundle. Type them so the editor knows what exists:

```ts
// src/env.d.ts (or include in vite-env.d.ts)
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_API_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

Now `import.meta.env.VITE_API_URL` is `string`, not `string | undefined`. Read every env var through one typed config module instead of scattering `import.meta.env.X` across files:

```ts
// src/lib/config.ts
export const config = {
  apiUrl: import.meta.env.VITE_API_URL,
  apiKey: import.meta.env.VITE_API_KEY ?? null,
} as const;
```

Never put a secret in a `VITE_*` var — by definition it ships to the browser.

---

## What goes where (quick map)

| Concern | Where | Skill to consult |
| --- | --- | --- |
| Component / hook discipline | `features/*/components`, `hooks/` | **react-patterns** |
| TypeScript rules and typing | everywhere | **typescript-patterns** |
| Naming, exports, style | everywhere | **frontend-conventions** |
| Routing (file-based, type-safe) | `src/routes/` | **tanstack-router** |
| Server state, Zustand, Axios | `features/*/services`, `lib/axios.ts`, `lib/query-client.ts` | **frontend-data-layer** |
| Components from shadcn | `src/components/ui/` | **shadcn** |
| Tailwind tokens (`@theme`) | `src/styles/globals.css` | **tailwindcss-v4** |
| HTTP requests | `features/*/services`, `lib/` | **fetch** |
| Tests (vitest + RTL + MSW) | colocated `.test.ts(x)` | **frontend-testing** |
| Microcopy (UI text) | wherever copy lives | **copywriting** |
| Visual hierarchy / colour / contrast | wherever the UI is | **ui-ux** |

A SPA has many moving parts; the value of this layout is that each skill knows exactly where it operates.

---

## Verification (after any setup change)

```bash
pnpm install
pnpm dev               # boot the dev server, walk the golden path in the browser
pnpm exec tsc --noEmit # typecheck the project (Vite doesn't do this on build by default)
pnpm lint              # if eslint configured
pnpm test              # vitest, once
pnpm build             # production build — catches a different class of errors
```

`tsc --noEmit` is **not optional** — Vite's `build` only fails on a subset of type errors, while `tsc` checks the whole project. Add a script for it (`"typecheck": "tsc --noEmit"`) and run it before pushing.

---

## Common pitfalls

- **Alias configured in only one place** — works in the editor, breaks at build (or vice versa). Both files, every time.
- **Env var without `VITE_` prefix** read from the browser — silently `undefined`.
- **Putting a secret in a `VITE_*` var** — ships to the client.
- **Casting `document.getElementById("root")`** with `as HTMLElement` — throw instead; if `#root` is missing, you want a clear error.
- **Bespoke components in `src/components/ui/`** — that folder is for shadcn; everything else goes in `src/components/` or the feature.
- **Long relative imports** (`../../../`) — use `@/...` and the alias resolves them.
- **No top-level `tsc --noEmit` step** — Vite's build won't catch everything; you'll find out in production.
- **Importing internals from another feature** — go through the feature's `index.ts` re-exports, or your feature isolation is gone.
