---
name: fetch
description: Expert in HTTP requests with the Web Fetch API — building requests (URL, headers, body), parsing responses (JSON, text, FormData, streaming), handling errors correctly (network failures vs non-2xx responses), AbortController for timeouts and cancellation, retries with exponential backoff, auth headers (Bearer / X-API-Key), the difference between server-side and client-side context, parsing standard response envelopes, and typing everything with TypeScript. Use this skill whenever a task involves calling an HTTP endpoint, fetching data, uploading files, polling, streaming responses, or wrapping a REST API in a typed client. Trigger on any mention of fetch, axios, REST calls, API requests, or "load data from", even if the API is not named explicitly. Consults Context7 when the surface (cache, streaming, FormData edge cases) is uncertain.
---

# fetch

How to make HTTP requests well. The Web Fetch API is what every modern environment (browser, Node 18+, Bun, Deno, Astro frontmatter, Next Server Components, Cloudflare Workers) speaks; this skill is about using it correctly — and writing the small wrappers that turn it into a typed, error-aware client.

The guiding idea: **the network is hostile**. Endpoints time out, return 500s, send empty bodies, change shapes. The right wrapper assumes that and returns a discriminated outcome (`ok` data, typed error) instead of pretending nothing can fail.

## When to consult Context7

`fetch` is stable but a few corners move: the `cache` option semantics, FormData edge cases in Node, streaming with `ReadableStream`, the precise contract for `keepalive`, and the difference between platforms (browser, Node, edge runtimes). For non-trivial questions consult Context7 with `"fetch api"` / `"streams api"` / your runtime ("node fetch", "cloudflare workers fetch") before answering.

For the basic patterns below (status checks, JSON parsing, AbortController), the surface hasn't moved — Context7 isn't needed.

---

## The minimum every fetch call needs

```ts
const response = await fetch("https://api.example.com/users", {
  method: "GET",
  headers: { Accept: "application/json" },
});

if (!response.ok) {
  throw new Error(`Request failed: ${response.status} ${response.statusText}`);
}

const data = (await response.json()) as User[];
```

Four things — every single time:

1. **A method**, even when it's GET (explicit beats default).
2. **An `Accept` header** so the server knows what shape you want back.
3. **A status check on `response.ok`** before parsing.
4. **A typed parse** (or a guard) so downstream code sees the shape, not `unknown`.

---

## Status codes vs network errors — the single biggest trap

`fetch` resolves on **any HTTP response**, including 500s. It only **rejects** when the request couldn't be made at all (DNS failure, network down, CORS preflight rejected, request aborted). So:

```ts
// WRONG — assumes await succeeded means 200
const data = await (await fetch(url)).json();

// CORRECT — handle both axes
try {
  const response = await fetch(url);
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  const data = await response.json();
} catch (error) {
  if (error instanceof ApiError) { /* HTTP error */ }
  else { /* network error / abort */ }
}
```

A 4xx is **not** a thrown exception by default — it's a successful await with `ok: false`. Internalise this and every wrapper you write will be safer.

---

## Sending JSON

Set `Content-Type` explicitly and stringify the body:

```ts
await fetch("/api/users", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  body: JSON.stringify({ email: "user@example.com" }),
});
```

If the server returns no body on success (204), don't call `.json()` — check `response.status` first, or use `response.text().then(t => t ? JSON.parse(t) : null)`.

## Sending FormData (file uploads)

```ts
const form = new FormData();
form.append("file", fileInput.files[0]);
form.append("title", "Report");

await fetch("/api/uploads", {
  method: "POST",
  body: form,
});
```

**Do NOT set `Content-Type` manually** for FormData — the browser/runtime sets `multipart/form-data; boundary=…` with the correct boundary. Setting it by hand breaks the body parse on the server.

## Sending URL-encoded form data

```ts
const params = new URLSearchParams({ email: "u@example.com", password: "..." });

await fetch("/api/login", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: params,
});
```

## Parsing responses

| Method | Use for |
| --- | --- |
| `response.json()` | JSON bodies. Throws on invalid JSON — wrap if the server may return empty. |
| `response.text()` | Plain text, HTML, CSV. |
| `response.blob()` | Binary data (file downloads). |
| `response.arrayBuffer()` | Raw bytes when you need direct access. |
| `response.formData()` | When the response is itself multipart. |
| `response.body` (ReadableStream) | Streaming — see below. |

Each consumes the body once; you can't call two parsers on the same response.

---

## Cancellation and timeouts — AbortController

Every long-running request should be cancellable. `fetch` accepts a `signal`; an `AbortController` provides one:

```ts
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 5_000);

try {
  const response = await fetch(url, { signal: controller.signal });
  // ...
} finally {
  clearTimeout(timeout);
}
```

Two practical helpers worth having in `lib/`:

```ts
// Cancel after `ms` milliseconds.
async function fetchWithTimeout(url: string, init: RequestInit = {}, ms = 10_000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}
```

```ts
// Cancel in-flight requests when a component unmounts (React).
useEffect(() => {
  const controller = new AbortController();
  fetch("/api/data", { signal: controller.signal })
    .then((response) => response.json())
    .then(setData)
    .catch((error) => {
      if (error.name !== "AbortError") { throw error; }
    });
  return () => controller.abort();
}, []);
```

An aborted fetch throws `DOMException` with `name === "AbortError"` — don't surface it as a failure.

---

## Retries with backoff

Retry **transient** failures (network errors, 5xx, 429), never 4xx (the client is wrong; retrying won't fix that). Exponential backoff with jitter avoids stampedes:

```ts
async function fetchWithRetry(
  url: string,
  init: RequestInit = {},
  { attempts = 3, baseMs = 250 } = {},
): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      const response = await fetch(url, init);
      if (response.ok || (response.status >= 400 && response.status < 500 && response.status !== 429)) {
        return response;  // success or non-retryable 4xx
      }
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;  // network / abort
    }

    if (attempt < attempts) {
      const delay = baseMs * 2 ** (attempt - 1) + Math.random() * baseMs;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}
```

For 429, prefer reading `Retry-After` if the server sends it instead of plain exponential backoff.

---

## Auth headers

The common patterns:

```ts
// Bearer token (JWT)
headers: { Authorization: `Bearer ${token}` }

// Shared API key (server-to-server)
headers: { "X-API-Key": apiKey }
```

If the API issues **refresh tokens**, intercept 401 once and retry after refresh — but only once per call, to avoid infinite loops. The interceptor lives in the shared client; never sprinkle refresh logic across call sites.

Never put secrets in client-side code. A `NEXT_PUBLIC_*` env var or `import.meta.env.PUBLIC_*` is **public** by definition. Server-only keys belong in server-only routes (Astro endpoints, Next route handlers, Express).

---

## Server-side vs client-side fetch

The same `fetch` API runs in many contexts; the consequences differ:

- **Browser (client)**: subject to **CORS**; requests carry cookies only with `credentials: "include"`; relative URLs resolve against `window.location.origin`.
- **Astro frontmatter, Next Server Components, Node, Cloudflare Workers**: **no CORS**; no cookies unless you forward them; relative URLs **don't work** — pass an absolute URL or read the configured base from env.
- **Edge runtimes (Cloudflare Workers, Vercel Edge)**: a subset of Node — `URL`, `fetch`, `crypto` exist; many Node-only APIs (filesystem, raw TCP) don't. Verify per runtime.

Decide *where* a fetch runs (server or client) before you write it. A 200ms fetch on the server is invisible; the same fetch on the client costs JS to ship, time to start, and a CORS round-trip.

---

## Parse the standard response envelope coherently

Many of our APIs return the standard envelope (`{success, message, data}` on success, `{success, message, errors}` on error). A tiny parser keeps every call site honest:

```ts
type Envelope<T> = { success: true; message: string | null; data: T };
type ErrorEnvelope = { success: false; message: string; errors: unknown };

class ApiError extends Error {
  constructor(public status: number, public errors: unknown, message: string) {
    super(message);
  }
}

async function api<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  const body = (await response.json()) as Envelope<T> | ErrorEnvelope;

  if (!response.ok || !body.success) {
    const error = body as ErrorEnvelope;
    throw new ApiError(response.status, error.errors, error.message);
  }

  return body.data;
}
```

Now every call is `const user = await api<User>("/api/me")` — typed at the boundary, with a single error type the UI can match on.

---

## Caching

`fetch` has a `cache` option:

| Value | Effect |
| --- | --- |
| `default` | Follow standard HTTP caching headers. |
| `no-store` | Don't read or write the cache. |
| `reload` | Don't read, but write the response. |
| `force-cache` | Read from cache if any match exists, even stale. |
| `only-if-cached` | Read from cache or fail. |

For client-side data that should always be fresh (user-specific dashboards), use `cache: "no-store"`. For static reference data, `force-cache` or HTTP caching headers from the server are usually better than rolling your own.

Server-runtime caching (Next's data cache, the Astro build) sits on top of `fetch` differently; consult Context7 for the runtime-specific contract.

---

## Streaming responses

For large bodies or progressive responses (chat, log tail), consume the body as a stream rather than awaiting `.text()`:

```ts
const response = await fetch(url);
const reader = response.body?.getReader();
if (!reader) return;

const decoder = new TextDecoder();
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  onChunk(decoder.decode(value, { stream: true }));
}
```

For Server-Sent Events specifically, the React/data-layer pattern lives in **frontend-data-layer** (`consumeSseStream` helper).

---

## TypeScript — type the boundary, narrow inside

```ts
// Generic helper — caller specifies T at the call site
async function api<T>(url: string, init?: RequestInit): Promise<T> { ... }

const user = await api<User>("/api/me");      // user is User
const orders = await api<Order[]>("/api/orders");
```

Don't `as` the JSON to silence the compiler — at the network boundary you genuinely don't know the shape, so the cast is honest only at the moment you parse. Validate with **zod** (or similar) when the shape matters:

```ts
import { z } from "zod";

const UserSchema = z.object({ id: z.string(), email: z.string() });
type User = z.infer<typeof UserSchema>;

const json = await response.json();
const user = UserSchema.parse(json);  // throws if the server lied
```

---

## Common pitfalls

- **Assuming `await fetch(...)` means success.** It only means a response arrived. Check `response.ok`.
- **Manually setting `Content-Type` for FormData.** Let the runtime add the boundary.
- **Calling `response.json()` on a 204 No Content.** Throws on empty body; check status first.
- **`fetch` with a relative URL on the server.** Doesn't resolve — pass an absolute URL.
- **Retrying 4xx errors.** The client is wrong; retry won't help.
- **Refresh-token logic scattered across call sites.** Centralise in one wrapper.
- **Putting an `apiKey` in client code via `NEXT_PUBLIC_*` / `PUBLIC_*`.** It ships to the browser. Server-only or nothing.
- **Forgetting AbortController on unmount.** Stale fetches set state on a dead component (React warns; the data may be wrong).
- **Casting JSON with `as`** instead of validating with a schema. The first time the server lies, you get a confusing crash three frames deep.
