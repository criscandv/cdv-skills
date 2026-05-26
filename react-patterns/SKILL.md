---
name: react-patterns
description: Deep reference for writing React (19+) components and hooks the house way. Use this skill whenever you build or edit a component, a custom hook, or anything involving state, effects, refs, memoization or rendering. Trigger it whenever a task touches useState/useEffect/useMemo/useCallback/useRef, component structure, props, event handlers, or "why is this re-rendering / this effect looping", even if React is not named explicitly. It is the React companion to frontend-conventions (the rulebook), typescript-patterns (typing), nextjs-patterns (App Router) and frontend-data-layer (state/data).
---

# React Patterns

How we write React (19+). Style rules (function declarations, named exports, `ComponentProps`) live in **frontend-conventions** and **typescript-patterns**; this skill is about component and hook behaviour.

The guiding idea: **most state and effects you reach for aren't needed.** Compute during render when you can, synchronise with external systems only when you must, and don't memoize without a measured reason. React is fast; premature `useMemo`/`useEffect` is where bugs and re-render loops come from.

---

## Components and handlers

`function` declarations for components and event handlers; arrows only for inline callbacks. Components are PascalCase, files kebab-case.

```tsx
// Correct
export function UserMenu({ userId }: { userId: string }) {
  function handleSelect(id: string) { ... }

  return <Menu onSelect={handleSelect} />;
}

// Avoid
const UserMenu = ({ userId }) => { ... };
```

Type props with `ComponentProps<"tag">` when spreading onto an element; React 19 passes `ref` as a normal prop, so no `forwardRef`. See **typescript-patterns**.

---

## You might not need an Effect

Before reaching for `useEffect`, check whether the value can be:

- **Computed during render** — derived data is just a variable, not state synced by an effect.
- **Derived with `useMemo`** — only if the computation is genuinely expensive.
- **Reset via a `key`** — to reset state when an identity changes, give the component a `key`, don't watch a prop in an effect.
- **Moved into the event handler** — logic that should run *because the user did something* belongs in the handler that fired, not in an effect reacting to the resulting state change.

Effects are for **synchronising with external systems** (the DOM, a subscription, a non-React widget, a network resource not owned by your data layer) — not for orchestrating internal data flow. Reference: [You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect).

```tsx
// Correct — derived during render
const fullName = `${first} ${last}`;

// Avoid — an effect mirroring props into state
const [fullName, setFullName] = useState("");
useEffect(() => { setFullName(`${first} ${last}`); }, [first, last]);
```

```tsx
// Correct — react to a user action in the handler
function onSubmit(values: FormValues) {
  save(values);
  track("form_submitted");
}

// Avoid — effect watching a flag the handler set
useEffect(() => {
  if (submitted) { track("form_submitted"); }
}, [submitted]);
```

---

## Effect dependencies

When you do need an effect, the dependency array lists the values whose change should re-run it — state, props, derived values. **Stable references don't belong there:** imported utilities, store setters (Zustand/`useState` setters are stable), and module-level functions never change between renders, so adding them is noise that can also mask the real triggers.

```tsx
// Correct
useEffect(() => {
  const socket = connect(roomId);
  return () => socket.close();
}, [roomId]);  // only the value that should re-subscribe

// Avoid — connect/close are stable; listing them adds nothing
useEffect(() => { ... }, [roomId, connect, close]);
```

Always return a cleanup function for subscriptions, timers and listeners — an effect that sets up without tearing down leaks.

---

## useMemo / useCallback — only with a reason

These have a cost (the deps array, the closure, the indirection) and exist for two concrete situations: a referentially-stable callback passed to a **memoized** child (`React.memo`), or a **genuinely expensive** computation. For a simple handler or a cheap derived value, a plain function/variable is faster to read and to run.

```tsx
// Correct — plain function and variable
function onOpenChange(isOpen: boolean) {
  setOpen(isOpen);
}

const label = `${count} items`;

// Avoid — memoizing trivial things
const onOpenChange = useCallback((isOpen: boolean) => setOpen(isOpen), []);
const label = useMemo(() => `${count} items`, [count]);
```

If you're adding `useCallback`/`useMemo`, be able to name the memoized consumer or the expense it avoids. If you can't, drop it.

---

## Hooks rules

- Call hooks at the **top level** of a component or custom hook — never inside conditions, loops or nested functions. The call order must be stable across renders.
- Custom hooks are `useThing` in a `use-thing.ts` file; they compose other hooks and return values/handlers, encapsulating reusable stateful logic.
- Keep components focused: extract complex stateful logic into a custom hook rather than growing a component body.

---

## Lists and keys

Give list items a **stable, unique `key`** from the data (an id), never the array index when the list can reorder, insert or delete — an index key makes React reuse the wrong element's state.

```tsx
{invoices.map((invoice) => (
  <InvoiceRow key={invoice.id} invoice={invoice} />
))}
```

---

## State shape

- Keep state **minimal**; derive everything you can during render instead of storing it.
- Don't duplicate server data into component state — read it from the data layer (React Query). See **frontend-data-layer**.
- Lift state only as high as the lowest common owner of the components that need it; co-locate otherwise.

---

## Common pitfalls

- **An effect that mirrors props/state into other state** — derive during render instead.
- **Effect dependency loops** — usually a stable function in the deps array, or state being set in an effect that re-triggers it.
- **Missing cleanup** — subscriptions/timers/listeners leak without a returned teardown.
- **`useMemo`/`useCallback` everywhere** — only with a memoized consumer or real expense.
- **Index as `key`** in a mutable list — causes state to attach to the wrong item.
- **Duplicating server state** in `useState`/Zustand — the data layer owns it.
