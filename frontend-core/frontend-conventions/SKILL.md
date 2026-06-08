---
name: frontend-conventions
description: The rulebook for building frontend applications with JavaScript, TypeScript, React and Next.js. Use this skill whenever you write or edit frontend code — components, hooks, stores, modules, styles, config — even if the user never says the word "conventions". It defines the mandatory house style (named exports, function declarations over arrows, kebab-case files, no type casting, type over interface, string unions over enums, object parameters, the @/ alias, no drive-by refactors, brace/spacing rules) that applies across JS/TS/React/Next. Consult it before writing any frontend code so the result is consistent. For deep topic detail it points to typescript-patterns, react-patterns, nextjs-patterns, frontend-data-layer and frontend-testing.
---

# Frontend Conventions — rulebook

The baseline for building frontend apps. The default stack is **TypeScript-first**, React (19+) and Next.js (App Router) for full apps; the rules here also apply to plain JavaScript where types aren't involved. This file is the *what* and the *why*; the deep *how* lives in companion skills — reach for them as you work:

- **`typescript-patterns`** — types vs interfaces, type-only imports, unions vs enums, guards over casts, `ComponentProps`/`PropsWithChildren`, deriving types.
- **`react-patterns`** — React 19 components and hooks, effects discipline, `useMemo`/`useCallback`, refs as props.
- **`nextjs-patterns`** — App Router: route groups, server vs client components, API routes, env vars, dynamic imports.
- **`frontend-data-layer`** — React Query vs Zustand, the Axios instance, SSE streaming, auth/session.
- **`frontend-testing`** — vitest + Testing Library + MSW, colocated tests.

Read those for depth. This is what you keep in your head on every task.

---

## Golden rules

Each rule prevents a recurring class of inconsistency or bug. If a task seems to need breaking one, surface it rather than silently deviating.

1. **Named exports, never default.** Default exports rename freely at the import site, which fragments the codebase and breaks find-all-references. Always `export function Thing()`. **Exception:** files a framework loads by convention — Next.js `page.tsx`, `layout.tsx`, route handlers, and modules consumed by `React.lazy(() => import(...))` — require `export default`.
2. **`function` declarations for components and event handlers; arrows only for inline callbacks.** Declarations hoist, read clearly, and give better stack traces. Reserve arrows for `setState(prev => ...)`, `.map()`, `.filter()` and the like.
3. **kebab-case file names.** `user-menu.tsx`, `use-current-user.ts`. Component names are PascalCase, hooks are `useThing`, module constants are `UPPER_SNAKE_CASE`.
4. **No type casting.** Never `as any`, `as unknown`, or any cast to silence the compiler. If types don't line up, fix the types or narrow with a type guard. Detail in `typescript-patterns`.
5. **`type` over `interface`; string unions over `enum`.** One consistent way to model data and choices; see `typescript-patterns`.
6. **Use the `@/` path alias** for cross-directory imports — never `../../../`. It keeps imports stable when files move.
7. **No drive-by refactors.** Only change code that the task requires. Don't rename, reformat, or "improve" surrounding code — and specifically don't flip existing arrow/function style or re-sort unrelated imports. Noise in a diff hides the real change.
8. **Object parameters for 2+ arguments.** A single named-field object makes call sites self-documenting and order-independent.
9. **Conditional class names via `clsx` / the `cn` helper** — never string concatenation. It handles falsy values and de-dupes Tailwind classes.
10. **English identifiers and comments, no emojis.** User-facing copy may be localised; code is English. Comments explain *why*, not *what*.

---

## Functions and exports

```tsx
// Correct
export function UserMenu() { ... }
function handleClick() { ... }

// Correct — framework convention files only
export default function DashboardPage() { ... }

// Avoid
const UserMenu = () => { ... };
export default UserMenu;
```

```ts
// Object params — correct
function createDocument({ templateId, payload }: { templateId: string; payload: Payload }) { ... }
createDocument({ templateId: "tpl-1", payload });

// Avoid — positional args
function createDocument(templateId: string, payload: Payload) { ... }
```

A single-use value read only once is accessed inline rather than bound to a throwaway variable. Use full, descriptive names (`index`, `element`, `button`, `error`), never `idx`/`el`/`btn`/`err`.

---

## Formatting

Braces on every conditional, body on its own line, and a blank line after the block so the next statement breathes:

```ts
// Correct
if (!element) {
  return;
}

const distanceFromBottom = element.scrollHeight - element.scrollTop - element.clientHeight;

// Avoid
if (!element) return;
const distanceFromBottom = element.scrollHeight - element.scrollTop - element.clientHeight;
```

---

## Naming reference

- **Component files:** kebab-case (`user-menu.tsx`); component names PascalCase (`UserMenu`).
- **Hooks:** kebab-case file (`use-current-user.ts`); function camelCase with `use` prefix (`useCurrentUser`).
- **Stores (Zustand):** colocated per feature or in a shared store dir; see `frontend-data-layer`.
- **Constants:** module-level immutable values `UPPER_SNAKE_CASE`.
- **Imports:** `@/` alias for cross-directory; relative only within the same folder.

---

## Verify before claiming equivalence

For delicate cases — data shape across multiple sources, source-priority decisions, invariants spanning code paths — confirm with `grep` before asserting two paths are equivalent. Don't infer from a shared helper ("both call `toX`, so the outputs match"): trace each consumer to see which fields it reads, then trace each pipeline to confirm those fields are produced. Pre/post-processing around shared helpers varies and leaves gaps that only surface in edge cases. The cost of confirming is low next to shipping a subtle bug.

---

## Project-specific configuration takes precedence

This skill is the project-independent baseline. Individual projects keep their own documentation — `docs/` (ARCHITECTURE, WORKFLOW, COMMANDS, DESIGN, ONBOARDING) plus the `AGENTS.md`/`CLAUDE.md` router — describing their stack versions, exact commands, folder layout, design tokens, env vars, auth flow and process. Those describe *this* project; when they are more specific than this skill, they win. Before starting in an unfamiliar repo, read them.

When you start a non-trivial frontend task, briefly state the plan (2–3 sentences plus bullet steps) before implementing, so the direction can be corrected early.
