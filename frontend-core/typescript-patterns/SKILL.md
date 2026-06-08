---
name: typescript-patterns
description: Deep reference for writing TypeScript the house way. Use this skill whenever you write or edit TypeScript — declaring types, typing component props, modelling unions, narrowing unknown values, importing types, or deciding between type/interface/enum/generics. Trigger it whenever a task involves type annotations, type errors, casting, type guards, ComponentProps, generics, or "how should I type this", even if TypeScript is not named explicitly. It is the types companion to frontend-conventions (the rulebook), react-patterns, nextjs-patterns and frontend-data-layer.
---

# TypeScript Patterns

How we type things. The headline rules (`type` over `interface`, string unions over `enum`, no casting) live in **frontend-conventions** — this skill is the reasoning and the concrete patterns.

The guiding idea: **types describe what the code actually does, and the compiler proves it.** Casting defeats that proof; loose "just in case" types push impossible cases onto every caller. Write the tightest type that's true, and teach the compiler to narrow rather than silencing it.

---

## type over interface

Use `type` aliases by default. They cover everything `interface` does for object shapes, plus unions, intersections and mapped/conditional types, so one consistent tool models all data.

```ts
// Correct
type User = { id: string; name: string };
type Status = "pending" | "active" | "inactive";

// Avoid
interface User { id: string; name: string }
```

(`interface` has a niche use for declaration-merging public library types; that's rare in app code.)

## String unions over enum

A string union is simpler, fully erased at build time, and the values are their own literals — no `Status.Active` indirection, and they serialise directly to/from API JSON.

```ts
// Correct
type Status = "pending" | "active" | "inactive";

// Avoid — emits runtime code, awkward interop
enum Status { Pending = "pending", Active = "active" }
```

## Type-only imports

When an import is used only in type position, mark it `import type` (or inline `type`). It signals intent, is fully erased at build, and prevents accidental value/runtime dependencies on a module you only needed for its shapes.

```ts
// Correct
import type { Session } from "next-auth";
import { create, type StateCreator } from "zustand";  // mixed: inline type modifier

// Avoid — value import for a type-only use
import { Session } from "next-auth";
```

---

## No casting — narrow with guards

A cast (`as X`, `as any`, `as unknown`) tells the compiler "trust me" and switches off the very checking that makes TypeScript worth using. When a runtime check has happened but TS can't see the narrowed shape, write a **user-defined type guard** so the compiler learns the narrowing and applies it everywhere.

```ts
// Correct
function isErrorWithMessage(value: unknown): value is { message: string } {
  return typeof value === "object" && value !== null && "message" in value;
}

if (isErrorWithMessage(error)) {
  console.error(error.message);  // narrowed, no cast
}

// Avoid
console.error((error as { message: string }).message);
```

If types genuinely don't line up, fix the type at the source rather than casting at the use site — the mismatch is information, not noise.

---

## Type only what callers actually pass

Don't pad a type with `| null | undefined` or fallback variants "just in case" when no caller produces that shape. Overly loose types force every consumer to handle impossible cases, which spreads dead defensive code. Defensive guards belong at **system boundaries** (API responses, user input, `localStorage`), not inside internal helpers whose inputs you control.

```ts
// Correct — the helper's caller always passes a string
function slugify(title: string): string { ... }

// Avoid — no caller passes null; this just forces fake handling everywhere
function slugify(title: string | null | undefined): string { ... }
```

## No speculative generics

Add `<T>` only when a real caller needs to preserve input-specific type information in the output. A generic with one concrete call site is just indirection.

```ts
// Justified — output type tracks the input
function first<T>(items: T[]): T | undefined { return items[0]; }

// Speculative — there's only ever one shape; drop the generic
function parseUser<T>(raw: unknown): T { ... }
```

---

## Typing React props

### Spreading native element props — `ComponentProps`

When a component spreads `{...rest}` onto a native element, type props with `ComponentProps<"tag">`. In React 19 `ref` is a regular prop (no `forwardRef`), and `ComponentProps` already includes it with the correct type — so it's the default. Reach for `ComponentPropsWithoutRef` only to explicitly forbid a `ref`.

```tsx
// Correct — ref flows through naturally
type ButtonProps = ComponentProps<"button"> & { label: string };

function Button({ label, ...rest }: ButtonProps) {
  return <button {...rest}>{label}</button>;
}

// Avoid — hand-rolled prop list drifts from the real element API
type ButtonProps = { onClick?: () => void; className?: string; label: string };
```

### children — `PropsWithChildren`, never hand-typed

```tsx
// Correct — only children added
type CardProps = PropsWithChildren<{ title: string }>;

// Correct — spreading onto an element already covers children
type DivProps = ComponentProps<"div">;

// Avoid
type CardProps = { title: string; children: React.ReactNode };
```

---

## Derive types from runtime values

When a literal union mirrors an existing runtime constant, derive it with `keyof typeof` so the two can't drift apart.

```ts
// Correct
import { ROUTES } from "@/constants/routes";

type RouteKey = keyof typeof ROUTES;

// Avoid — hardcoded, silently stale when ROUTES changes
type RouteKey = "HOME" | "DASHBOARD" | "SETTINGS";
```

The same applies to deriving a value-union with `(typeof ARR)[number]` from a `const` array.

---

## Shared types live in one place

A type used by more than one module belongs in the domain types file (`features/<name>/types.ts`) or a shared `src/types/`, imported where needed — not copy-pasted into each helper. Duplicated types drift; a single declaration stays honest.

---

## Common pitfalls

- **Casting to silence an error** — fix the type or write a guard; a cast hides the real mismatch.
- **`interface` for app data** — use `type` for consistency and union support.
- **`enum`** — use a string union.
- **Value-importing a type-only symbol** — use `import type`.
- **Defensive `| null | undefined`** on internal helpers no caller feeds that shape.
- **Speculative generics** with a single concrete use.
- **Hand-rolled prop lists** instead of `ComponentProps<"tag">`.
- **Hardcoded unions** that mirror a runtime constant — derive with `keyof typeof`.
