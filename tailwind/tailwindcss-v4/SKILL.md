---
name: tailwindcss-v4
description: Expert in Tailwind CSS v4 (the CSS-first generation). Use this skill whenever you write or configure Tailwind in a project — utility classes, theming via @theme, custom utilities (@utility), custom variants (@custom-variant), container queries, dark mode, plugins, the Vite/PostCSS setup, or migrating from v3. Trigger it whenever a task touches Tailwind classes, a styles.css with @theme, design tokens declared in CSS, "how do I do X in Tailwind", or anything that hints at Tailwind v3 → v4 differences, even if Tailwind is not named explicitly. Before answering, this skill always consults Context7 for current Tailwind v4 docs — its API moved significantly from v3 and getting it from training-data memory is unreliable.
---

# Tailwind CSS v4

The implementation layer for design decisions made in **ui-ux**. Tokens from ui-ux land in Tailwind's `@theme` block; components use the utilities that those tokens generate.

## Always consult Context7 before answering

Tailwind v4 is a generational rewrite — `@theme`/`@utility`/`@custom-variant`, no `tailwind.config.js` by default, OKLCH-native colours, container queries promoted to first-class, new gradient APIs, a different plugin model. Recalling v4 specifics from training data is unreliable; v3 muscle memory actively misleads.

**Before answering any non-trivial Tailwind v4 question, fetch current docs through Context7:**

1. `mcp__context7__resolve-library-id` with `"tailwindcss"` to get the library id.
2. `mcp__context7__query-docs` with that id and the relevant topic (e.g. `"@theme block"`, `"custom variants"`, `"container queries"`, `"upgrading from v3"`, `"plugin API"`).

Only after reading the current docs should you propose code. If the Context7 MCP isn't connected, say so to the user and either (a) ask them to enable it or (b) state explicitly that your answer is based on prior knowledge and may be out of date — never present uncertain v4 syntax as fact.

Skip Context7 only for the most basic mechanical questions (which utility means `padding`, what `gap-4` does) where v3 and v4 don't diverge.

---

## What v4 changed from v3 — the headline shifts

These are the structural shifts to keep in mind; verify exact syntax via Context7 before writing.

- **CSS-first config.** There is no `tailwind.config.js`. Theme tokens are declared in your CSS via an `@theme` block; that block both registers CSS custom properties and generates the matching utility classes.
- **Single-line install.** A typical setup imports Tailwind with `@import "tailwindcss";` in the entry CSS and uses the Vite plugin (`@tailwindcss/vite`) or the PostCSS plugin — no JS config file required for the common case.
- **OKLCH-native colours.** v4 uses OKLCH internally; declaring colours in OKLCH gives perceptually even ramps. v3 hex/rgb still works.
- **Container queries first-class.** The container query utilities ship in core (no plugin) and integrate with the same theme tokens.
- **Custom utilities and variants are CSS.** `@utility name { ... }` defines a new utility; `@custom-variant name (...)` defines a new variant (e.g. for dark mode or data-state hooks). The old JS plugin API still exists for complex cases but most needs are CSS-only now.
- **Renamed / reorganised utilities.** Several v3 utilities were renamed or absorbed; treat any class you "remember" from v3 as suspect until you've verified it in v4 docs.

For the precise upgrade path, query Context7 with `"upgrading from v3 to v4"` — the official upgrade guide lists every renamed token.

---

## Theming with `@theme` — the central pattern

Design tokens from **ui-ux** map directly here. The `@theme` block both publishes CSS variables and generates the corresponding utilities, so the same tokens drive styling and inline `var(--…)` use.

```css
/* src/styles.css */
@import "tailwindcss";

@theme {
  --color-brand-50:  oklch(0.97 0.02 250);
  --color-brand-500: oklch(0.62 0.18 250);  /* primary action */
  --color-brand-600: oklch(0.55 0.20 250);  /* hover */

  --color-neutral-50:  oklch(0.99 0.00 250);
  --color-neutral-900: oklch(0.20 0.01 250);

  --color-success-500: oklch(0.70 0.17 145);
  --color-danger-500:  oklch(0.62 0.20 25);

  --spacing-1: 0.25rem;
  --spacing-2: 0.5rem;
  --spacing-4: 1rem;
  --spacing-8: 2rem;

  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;

  --font-sans: "Inter", system-ui, sans-serif;
}
```

The above generates utilities like `bg-brand-500`, `text-neutral-900`, `p-4`, `rounded-md`, etc., **and** exposes the variables for hand-rolled CSS (`color: var(--color-brand-500)`). Verify the exact naming convention and namespace prefixes (`--color-*`, `--spacing-*`, etc.) in Context7 for the version you're on.

---

## Dark mode — as a custom variant

In v4, dark mode is wired through `@custom-variant` so you can pick the strategy that matches the app (media query, class on `<html>`, data attribute on a wrapper, etc.) and your tokens automatically support it. The exact syntax has nuances — check Context7 before wiring it the first time.

---

## Custom utilities and variants

When the design needs something Tailwind doesn't ship, prefer composing existing utilities first; reach for `@utility` only when the pattern is reused and worth a name.

```css
@utility scrollbar-thin {
  scrollbar-width: thin;
}
```

`@custom-variant` adds new variants for state hooks: data attributes, ARIA states, framework-specific selectors. Useful pairings include `data-[state=open]`, `aria-[expanded=true]`, and Radix/Headless UI state attributes.

For both, query Context7 with `"@utility"` / `"@custom-variant"` for the canonical syntax and edge cases.

---

## Animations — `--animate-*` + `@keyframes` in `@theme`

v4 brings keyframe animations into the same `@theme`-driven workflow as colours and spacing. The plugin you may have been used to (`tailwindcss-animate`) is **not needed**: declare an animation token, declare its `@keyframes` alongside, and the matching `animate-<name>` utility class is generated automatically.

```css
@theme {
  --animate-fade-in:   fade-in   0.2s ease-out;
  --animate-fade-out:  fade-out  0.2s ease-in;
  --animate-slide-in:  slide-in  0.3s ease-out;
  --animate-slide-out: slide-out 0.3s ease-in;

  @keyframes fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
  @keyframes fade-out {
    from { opacity: 1; }
    to   { opacity: 0; }
  }
  @keyframes slide-in {
    from { transform: translateY(-0.5rem); opacity: 0; }
    to   { transform: translateY(0);       opacity: 1; }
  }
  @keyframes slide-out {
    from { transform: translateY(0);       opacity: 1; }
    to   { transform: translateY(-0.5rem); opacity: 0; }
  }
}
```

Use them like any utility: `<div class="animate-fade-in">…</div>`.

Notes:

- **Declare the `@keyframes` rules inside (or right next to) the `@theme` block** so they're emitted into the bundle when the corresponding `--animate-*` token is referenced.
- **Name the token after the motion, not the use case** — `slide-in` reads well in components; `dialog-enter` over-couples the token to a single consumer.
- **Pair with `@starting-style`** for entry animations on elements that mount (popovers, dialogs). Verify the exact syntax in Context7 — it landed late in v4 and may evolve.
- **Respect `prefers-reduced-motion`** at the component level (a small media-query guard or a `motion-safe:animate-fade-in` pattern); see **ui-ux** for the accessibility rationale.
- **Drop `tailwindcss-animate`** if you migrated from v3 — it's redundant under v4 and the two systems will fight if both are loaded.

---

## Patterns that hold across versions

- **Compose, don't abstract prematurely.** A button with `inline-flex items-center gap-2 rounded-md bg-brand-500 px-4 py-2 text-white hover:bg-brand-600 focus-visible:ring-2 focus-visible:ring-brand-500` is fine; only extract a component or a utility when the same string repeats in 3+ places with meaningful identity.
- **Use the design tokens you defined.** Off-token values (`p-[17px]`, `text-[#3b82f6]`) defeat the system. They're fine for genuine one-offs; if they appear repeatedly, either lift them to `@theme` or you found a missing token.
- **Conditional class composition** via the `cn` helper (clsx + tailwind-merge) — never string concatenation. `tailwind-merge` de-dupes conflicting utilities (the last one wins), which keeps overrides clean.
- **`focus-visible` over `focus`.** Keyboard-only focus rings, not blue boxes for mouse users.
- **Container queries** when a component should respond to its container width, not the viewport. `@container` paired with `@sm:`, `@md:` etc.

---

## Tooling

- **Vite**: `@tailwindcss/vite` is the recommended plugin in v4 (CSS-first); the older PostCSS plugin remains for non-Vite stacks. Verify the current package names and config in Context7 before wiring a fresh project.
- **Editor**: install the Tailwind CSS IntelliSense extension. Configure it to read the project's CSS (where `@theme` now lives) — v3 muscle memory expects `tailwind.config.js`.
- **Formatting**: Prettier's `prettier-plugin-tailwindcss` enforces canonical class ordering — install and configure it; it removes a whole class of code-review friction.

---

## When the user pastes a v3 snippet

A common case: a v3 config or class set comes in and "just needs to be converted". Don't translate from memory — query Context7 with `"upgrading from v3 to v4"` and apply the documented mappings (renamed tokens, removed utilities, the JS-config → `@theme` move). Some constructs have direct equivalents; some have moved into `@utility`/`@custom-variant`; a few were removed entirely.

---

## Common pitfalls

- **Recalling v4 syntax from training data instead of checking Context7** — the API moved enough that recall is unsafe.
- **Reaching for a `tailwind.config.js`** — there is no JS config in the default v4 setup; tokens go in `@theme` in CSS.
- **Off-token values everywhere** (`p-[17px]`, `text-[#3b82f6]`) — defeats the system; either fix the design or add the token.
- **String concatenation for conditional classes** — use `cn` so `tailwind-merge` resolves conflicts.
- **`focus:` instead of `focus-visible:`** — gives mouse users a ring they didn't ask for.
- **Forgetting to install the formatter plugin** — class order drifts and reviews argue over it.
- **Treating dark mode as colour inversion** — design dark with its own surfaces (see **ui-ux**), then wire the variant.
