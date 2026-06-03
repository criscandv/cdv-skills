---
name: frontend-normalize
description: Audit an existing JavaScript/TypeScript/React frontend project (Vite, Next.js, CRA, or similar) against the house conventions and bring it up to standard incrementally and safely. Use this skill when the user wants to modernise, standardise, normalise, refactor-to-convention or "clean up" an existing frontend codebase — introducing named exports, kebab-case file names, the @/ alias, a single Axios instance, the React Query / Zustand split, MSW-based tests, the typed config, removing `any`/casts, or migrating routing/state management. Trigger on "normalize this frontend", "apply our frontend conventions", "este front no sigue el estándar". Slash-invoked. For starting a new Next.js app use nextjs-new-app; to add a single feature use frontend-feature.
disable-model-invocation: true
---

# /frontend-normalize — bring an existing frontend up to standard, safely

Frontends drift in many small ways: a stray `default export`, a `MyComponent.tsx` next to `user-menu.tsx`, an `axios.get(...)` call bypassing the shared instance, server state mirrored into a Zustand store, an `as any` to make TS shut up. Each is harmless on its own and exhausting when they're everywhere. This skill **separates the safe fixes from the risky ones**, applies the safe ones with confidence, and never bulk-rewrites the codebase without a written plan and explicit sign-off.

Two rules govern everything:

- **Incremental, not a big-bang rewrite.** One concern per branch/commit, verified before the next. A PR that "normalises everything" is unreviewable and unrevertable.
- **The project's own docs win.** If `docs/`/`AGENTS.md` document a deliberate deviation (e.g. they intentionally use react-router instead of TanStack Router), respect it — surface it, don't silently override it.

Communicate progress in Spanish. All code is in English.

## Stage 0 — orient

Read before changing anything:

- Detect the **stack** from `package.json` and config: Vite vs Next vs CRA; React version; TypeScript or plain JS; router (TanStack Router / react-router / Next App Router); state libs (React Query, Zustand, Redux, …); testing (vitest/jest, Testing Library, MSW); styling (Tailwind, CSS Modules); package manager (npm/pnpm/yarn).
- Read `docs/` if it exists (`ARCHITECTURE.md`, `WORKFLOW.md`, `COMMANDS.md`, `DESIGN.md`, `ONBOARDING.md`). It may encode intentional choices that override the defaults. If `docs/` is missing, offer **project-docs** before auditing — capturing the actual setup first makes the gap report accurate.
- Identify the existing `package.json` scripts (`lint`, `format`, `typecheck`, `test`, `build`, `dev`) and the lint/format config — those are the verification gates.
- Confirm a clean working tree and create a working branch (`chore/normalize-<area>`); never work on `main`.

## Stage 1 — audit and report

Walk the checklist and produce a **gap report**: each item with its current state, whether it conforms, and the risk of fixing it. Don't change code yet — the report is this stage's deliverable.

### Convention checklist

Structure & tooling (additive / mechanical):
- `package.json` scripts include `lint`, `test`, and a typecheck path (`tsc --noEmit` for Vite/CRA; `next build` covers it on Next).
- ESLint + Prettier configured and runnable; pre-commit hook (`pre-commit` or `husky` + `lint-staged`).
- `tsconfig.json` with **`strict: true`**; path alias `@/*` mapped to `src/*` in both `tsconfig` and the bundler (`vite.config.ts` / `next.config.js`).
- No `any` types and no `as any`/`as unknown` casts in source.

Code style:
- **Named exports** everywhere except framework convention files (Next `page.tsx`/`layout.tsx`/`route.ts`, `React.lazy` targets).
- `function` declarations for components and event handlers; arrows only in inline callbacks.
- **kebab-case** file names; PascalCase components; `use*` hooks; `UPPER_SNAKE_CASE` module constants.
- `@/` alias for cross-directory imports — no long `../../../` chains.
- `clsx` / `cn` helper for conditional class names (no string concatenation).
- `type` over `interface`; string unions over `enum`; `import type` for type-only imports.

React & state:
- Hooks at top level; no unnecessary `useCallback`/`useMemo`; no effects that mirror props/state into other state (see **react-patterns**).
- React Query owns server state; Zustand only holds UI/client state — **server state is never duplicated into Zustand**.
- A **single Axios instance** with request/response interceptors (auth token, 401 → logout); features import that instance, never call `axios` directly.
- Env vars read in one typed config module, not scattered `process.env.X` / `import.meta.env.X` reads across files.

Data fetching & errors:
- HTTP calls go through query/mutation hooks with structured query keys.
- Cross-cutting failures (401, network) centralised in the Axios response interceptor and/or the QueryClient defaults.

Testing:
- vitest (or jest) + **@testing-library/react** + jsdom + user-event + **MSW**.
- Tests **colocated** with the source file (`x.ts` ↔ `x.test.ts`).
- HTTP mocked at the network with MSW — **no `vi.mock("axios")`** or stubs of internal `api.ts` files.

Feature layout:
- Code organised by **feature** under `src/features/<name>/` (`components/`, `hooks/`, `stores/`, `api.ts`, `types.ts`) when the app has grown past a handful of screens.

Classify each gap as **additive** (new code, no refactor), **structural** (file moves/renames, import churn, but no behaviour change) or **risky** (bulk style changes, framework/library migrations, JS→TS, casting removal that requires real type analysis).

## Stage 2 — agree the scope and order

Present the gap report. Agree what to tackle and in what order — default is ascending risk. Let the user defer or skip items. **Don't bundle a risky change with safe ones** in the same commit.

## Stage 3 — apply additive and structural fixes

One concern per branch/commit, each verified with `npm run lint`, the typecheck path, the test suite and `npm run dev` before moving on. Use the layer skills for the exact patterns:

- **Tooling additions** — ESLint + Prettier configs, a `lint-staged` + pre-commit setup, `tsconfig` `strict: true`, the `@/` alias in both `tsconfig` and the bundler config, scripts in `package.json`. See **frontend-conventions** for the rules and **python-tooling**-style discipline for the install commands (per the project's package manager).
- **HTTP plumbing** — introduce the single `lib/axios.ts` (or equivalent) instance with auth + 401 interceptors; migrate existing `axios.get(...)` call sites to the instance one feature at a time. See **frontend-data-layer**.
- **Data layer** — add the `QueryClientProvider` if missing; move ad-hoc `useEffect`+`fetch` patterns into `useQuery` / `useMutation` hooks with structured keys; introduce Zustand for actual UI state. See **frontend-data-layer**.
- **Testing** — add vitest + Testing Library + MSW config; create `test/handlers.ts` + `test/server.ts`; convert any `vi.mock("axios")` tests to MSW. See **frontend-testing**.
- **Feature module layout** — when the app is large enough, introduce `src/features/<name>/` and move code by feature; do this as a dedicated, well-titled commit so the move is reviewable.
- **kebab-case renames** — rename PascalCase files to kebab-case in batches. Use `git mv` to preserve history. On case-insensitive file systems (macOS default) rename via an intermediate name (`Foo.tsx → foo.tmp → foo.tsx`) so git sees the change. Update import paths in the same commit.

After each change: lint clean, typecheck green, suite passing, `npm run dev` boots without errors.

## Stage 4 — risky refactors (explicit confirmation each)

These need a written plan and the user's explicit "go" before touching code. Never auto-apply.

### default exports → named exports

A mechanical but wide refactor: every export site and every import site changes together. Use a codemod (`ts-morph` or `jscodeshift`) rather than hand-edits — and remember the framework exceptions (`page.tsx`, `layout.tsx`, route handlers, `React.lazy` targets must stay default). Run the codemod, run the suite, commit as a single dedicated change.

### Arrow components / handlers → `function` declarations

The convention forbids drive-by style flips in unrelated code (rule 7: no drive-by refactors), so this *only* happens as a deliberate normalisation commit, scoped to a clear path subset (e.g. `src/features/<name>/`), reviewed as such. Don't bundle it with anything else.

### Removing `as`/`as any`/`as unknown`

Each cast is a real type mismatch in disguise — don't bulk-delete them. Inventory the occurrences, address them one at a time by **fixing the type at the source or writing a type guard** (see **typescript-patterns**). Some casts will reveal real bugs in the process.

### Plain JS → TypeScript

A significant project of its own. Stage it: add `tsconfig.json` with `allowJs: true`, rename file-by-file (or feature-by-feature), let `strict` get tighter as coverage grows. Don't promise it as a "normalisation" pass; raise it as a separate decision.

### Routing or state-management migrations

Changing router (react-router → TanStack Router → Next App Router) or state store (Redux → Zustand) is its own project — touches public URLs, state shape, integrations, possibly tests. Treat it as an architectural decision (see **engineering:architecture** if available), get explicit sign-off, plan the migration end to end, and don't run it inside a "normalize" sweep.

### Mass `lint --fix` on long-untouched code

`eslint --fix` and `prettier` can produce huge diffs that hide subtle changes (e.g. autofix rules can rewrite logic, not just whitespace). Run them in a **single, isolated commit** titled "chore: apply lint/format" so future blames can skip past it cleanly.

## Stage 5 — re-verify and report

When the agreed scope is done:

```bash
npm run lint                # or the project's equivalent
npx tsc --noEmit            # Vite/CRA; on Next, `next build`
npm test                    # or `npm run test:run` if watch is the default
npm run dev                 # boot once, walk the golden path in the browser
```

Lint clean, typecheck green, tests passing, dev server boots without runtime errors. Report what was normalised, what was deliberately deferred (especially any risky items), and the recommended next steps.

## Guardrails

- **Never bulk-rewrite** the whole repo in one commit — incremental, verified, revertable.
- **Respect documented deviations** in the project's own `docs/`/`AGENTS.md`.
- **Casts are not whitespace** — treat each `as X` as a small bug investigation, not as text to delete.
- **Renaming is a structural change** — use `git mv`, update imports in the same commit, and beware case-insensitive file systems.
- **UI changes aren't done until verified in the browser** — type-check ≠ correctness. Walk the golden path and the error/empty/loading states after a refactor.
- **Keep the test suite green at every step** — a normalisation that breaks tests is not normalisation.
