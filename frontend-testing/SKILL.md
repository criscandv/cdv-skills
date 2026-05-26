---
name: frontend-testing
description: The testing discipline for a React/Next frontend — vitest, @testing-library/react, jsdom, user-event and MSW for HTTP mocking. Use this skill whenever you write or run frontend tests, set up the test environment, add a test for a hook/component/helper, mock a network call, or decide what is worth testing. Trigger it whenever a task involves vitest, Testing Library, jsdom, MSW, colocated .test files, or "how do I test this hook/component", even if not named explicitly. It is the testing companion to frontend-conventions, react-patterns, nextjs-patterns and frontend-data-layer.
---

# Frontend Testing

How we test a React/Next frontend. The stack is **vitest** + **@testing-library/react** + **jsdom** + **@testing-library/user-event** + **MSW** (Mock Service Worker). Config lives in `vitest.config.ts` and `vitest.setup.ts`.

The guiding idea: **test behaviour the user can observe, against the real network boundary.** Query the DOM the way a user finds things (by role and label), drive interactions through `user-event`, and intercept HTTP at the network with MSW rather than mocking your own modules. A test that mocks `axios` or a hook tests the mock; a test that renders the component and intercepts the request tests the system.

---

## Layout and naming

Test files are **colocated** with the source, kebab-case, with a `.test.ts(x)` suffix:

```
use-chat-auto-scroll.ts ↔ use-chat-auto-scroll.test.ts
user-menu.tsx           ↔ user-menu.test.tsx
```

Colocation keeps the test next to what it covers, so it moves and is found with the source. Globals may be enabled (`describe`/`it`/`expect` without imports); importing them explicitly from `vitest` is also fine and some teams prefer it for clarity — match the project.

---

## What's worth testing

Coverage doesn't need to be exhaustive; pin down the things whose correctness matters and that are easy to get subtly wrong:

- **Hooks** with real logic (scroll math, derived state, retry/debounce, parsing).
- **Helpers / pure functions** (formatters, validators, mappers) — cheap, high-value.
- **Constants/derived data** whose shape other code depends on.
- **Components** with meaningful behaviour: conditional rendering, user interactions, loading/empty/error states.

Add tests when you touch any of these. Don't chase a coverage number on trivial passthrough components.

---

## Querying — by role and label, not test ids

Prefer queries that mirror how a user (and assistive tech) finds things: `getByRole`, `getByLabelText`, `getByText`, `getByPlaceholderText`. Reach for `getByTestId` only when there's genuinely no accessible handle — overusing it tests structure, not behaviour.

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

test("submits the entered email", async () => {
  render(<LoginForm />);

  await userEvent.type(screen.getByLabelText(/email/i), "user@example.com");
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

  expect(await screen.findByText(/welcome/i)).toBeInTheDocument();
});
```

- Use **`findBy*`** for the first assertion after an async update (it retries until the element appears), then `getBy*` is safe.
- Drive interactions with **`user-event`**, not `fireEvent` — it simulates real event sequences (focus, key events) closer to a user.

---

## Mock HTTP at the network with MSW

Never `vi.mock("axios")` or stub your own `api.ts`. Intercept at the network layer with MSW so the real Axios instance, interceptors and serialisation all run — the test exercises the actual data path.

```ts
// test/handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("*/invoices", () => HttpResponse.json({ results: [], count: 0 })),
];
```

```ts
// test/server.ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

Wire `server.listen()` / `resetHandlers()` / `close()` in `vitest.setup.ts`. Override per test for the case under exam:

```ts
server.use(
  http.post("*/login", () => HttpResponse.json({ message: "bad credentials" }, { status: 401 })),
);
```

Mock only true external boundaries (HTTP, time, `crypto`, browser APIs). Mocking your own hooks/components means you're no longer testing them.

---

## Rendering with providers

Components that depend on React Query or routing need their providers. Wrap them with a shared render helper rather than repeating boilerplate:

```tsx
// test/utils.tsx
export function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}
```

Disable query retries in tests so an error case fails fast instead of retrying. Create a fresh `QueryClient` per render (or reset between tests) so cache doesn't leak across cases.

---

## State between tests

Reset shared state in `beforeEach` so tests don't bleed into each other: reset MSW handlers (`server.resetHandlers()`), clear persisted Zustand stores, and clear timers/mocks. A test that passes only because a previous test ran is worse than no test.

---

## Commands

```bash
npm test            # run once (vitest)
npm run test:watch  # watch mode during development
```

Before reporting a task done, run the suite if any tested code was touched, and lint the touched paths. In many Next setups there's no separate typecheck — `next build` performs it.

---

## Common pitfalls

- **`vi.mock("axios")` or stubbing your own `api.ts`** — use MSW; otherwise you test the mock, not the code.
- **Querying by test id or class** when a role/label exists — tests structure instead of behaviour.
- **`getBy*` for an async result** — use `findBy*` (it retries) for the first post-update assertion.
- **`fireEvent` for user flows** — use `user-event` for realistic interaction sequences.
- **Shared `QueryClient` / un-reset stores / leftover MSW overrides** across tests — reset in `beforeEach`.
- **Retries left on** in the test `QueryClient` — error tests hang or slow down.
