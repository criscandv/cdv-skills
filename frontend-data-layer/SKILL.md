---
name: frontend-data-layer
description: Deep reference for the data and state layer of a React/Next frontend — React Query (server state) vs Zustand (UI state), the single Axios instance and interceptors, Server-Sent Events streaming, the auth/session pattern, and ad-hoc cross-component events. Use this skill whenever you fetch or cache API data, add a Zustand store, wire the HTTP client, handle auth tokens, stream responses, or decide "where should this state live". Trigger it whenever a task touches React Query (useQuery/useMutation/query keys), Zustand, Axios, interceptors, SSE, sessions/tokens, or global UI state, even if not named explicitly. It is the data/state companion to frontend-conventions, react-patterns and nextjs-patterns.
---

# Frontend Data Layer

Where data and state live, and the boundaries between them. Component/hook mechanics are in **react-patterns**; this skill is the architecture of fetching, caching and sharing state.

The one rule that prevents most state bugs: **server state and UI state are different things with different owners.** Server state (anything that came from or goes to the backend) is owned by React Query. UI/client state (ephemeral, session, view-local) is owned by Zustand or component state. Never copy server data into Zustand — read it from the query cache, which is the single source of truth for it.

| Layer | Tool | Owns |
| --- | --- | --- |
| Server state | React Query (TanStack Query) | API data — fetching, caching, mutations |
| UI / global state | Zustand | ephemeral UI state, session flags |
| URL state | the router | route + search params |
| Form state | a form library (e.g. react-hook-form) | form values, validation |

---

## The single Axios instance

All HTTP goes through **one** Axios instance, configured once. Every feature's `api.ts` imports it — never call `axios` directly or spin up ad-hoc instances, or interceptors and base config won't apply uniformly.

```ts
// lib/axios.ts
import axios from "axios";

export const http = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

http.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      emitUnauthorized();  // trigger logout via the event bus (below)
    }

    return Promise.reject(error);
  },
);
```

The request interceptor attaches the auth token; the response interceptor centralises cross-cutting failures (401 → logout) so individual calls don't each reimplement it.

---

## React Query — server state

Feature data lives in hooks backed by `useQuery` / `useMutation`. Keep **query keys** structured and stable so caching and invalidation are predictable.

```ts
// features/invoices/hooks/use-invoices.ts
export function useInvoices(filters: InvoiceFilters) {
  return useQuery({
    queryKey: ["invoices", filters],
    queryFn: () => getInvoices(filters),
  });
}

export function useCreateInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createInvoice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
    },
  });
}
```

- Mutations **invalidate** the affected query keys on success so the UI reflects the change without manual refetch wiring.
- Don't mirror query results into `useState`/Zustand — read them where they're rendered; React Query already caches and shares them.
- In Next Server Components you can prefetch into the cache and hydrate; see **nextjs-patterns**.

---

## Zustand — UI / client state

Use Zustand for state that is genuinely client-side: open/closed UI, multi-step wizard position, session-derived flags, cross-component UI coordination. Stores are colocated per feature (`features/<name>/stores/`) or shared (`src/stores/`).

```ts
// features/chat/stores/use-composer-store.ts
import { create, type StateCreator } from "zustand";

type ComposerState = {
  draft: string;
  setDraft: (draft: string) => void;
  clear: () => void;
};

export const useComposerStore = create<ComposerState>((set) => ({
  draft: "",
  setDraft: (draft) => set({ draft }),
  clear: () => set({ draft: "" }),
}));
```

Use the `persist` middleware only when state must survive reloads (and never put server data there). Store setters are stable references — don't list them in effect deps (see **react-patterns**).

---

## Streaming — Server-Sent Events

For token-by-token / progressive responses (chat, simulations), consume an SSE stream rather than polling. Centralise the parsing in one helper and feed chunks into local state as they arrive:

```ts
// lib/sse.ts
export async function consumeSseStream(
  response: Response,
  onChunk: (text: string) => void,
): Promise<void> {
  const reader = response.body?.getReader();
  if (!reader) {
    return;
  }

  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    onChunk(decoder.decode(value, { stream: true }));
  }
}
```

Streaming responses don't fit React Query's request/response cache cleanly — drive them through local state in the feature hook, and use React Query for the surrounding non-streaming data.

---

## Auth / session

The common pattern: the backend issues a JWT on login; the frontend stores it via the session layer (e.g. NextAuth with a credentials provider and JWT strategy, verifying with a server-side secret); the Axios request interceptor attaches it as `Authorization: Bearer <token>`; and a `401` / "not authenticated" response triggers logout through the event bus. Session-shape and the exact provider are **project-specific** — read the project's `docs/`/`AGENTS.md`. The reusable rule: **token attachment and 401 handling live in the Axios interceptors**, not scattered across calls.

---

## Ad-hoc cross-component events

For one-off UI signals that don't justify shared state (a global "unauthorized" event, "open this dialog from anywhere"), a tiny event emitter (e.g. `mitt`) is cleaner than threading callbacks or over-growing a store.

```ts
// lib/events.ts
import mitt from "mitt";

type Events = { UNAUTHORIZED: void; OPEN_UPGRADE_DIALOG: void };

export const events = mitt<Events>();
```

Reserve this for genuinely cross-cutting, fire-and-forget signals — for anything stateful, prefer a store or the query cache.

---

## Common pitfalls

- **Copying server state into Zustand/`useState`** — React Query owns it; you'll get stale duplicates.
- **Calling `axios` directly** or making new instances — bypasses the interceptors (auth, 401).
- **Per-call 401 handling** — centralise it in the response interceptor.
- **Unstructured query keys** — makes targeted invalidation impossible.
- **Forcing a stream through React Query's cache** — drive streaming via local state.
- **`persist`-ing server data** — only persist genuine client/UI state.
