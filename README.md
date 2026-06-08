# cdv-skills

Personal collection of [Claude Code](https://docs.claude.com/en/docs/claude-code) skills, grouped by technology.

Skills extend Claude with custom workflows and domain knowledge. Each skill lives in its own directory with a `SKILL.md` containing metadata (frontmatter) and instructions.

## Installation

Install every skill in this repo with [Vercel's `npx skills` toolkit](https://github.com/vercel/skills):

```bash
npx skills add https://github.com/criscandv/cdv-skills.git
```

That walks the repo, finds every directory with a `SKILL.md`, and registers it. Re-run the command after a `git pull` to pick up updates.

## Structure

```
cdv-skills/
├── README.md
├── django/                  # Django + DRF backend conventions and actions
│   ├── django-conventions/
│   ├── django-orm-patterns/
│   ├── django-rest-framework/
│   ├── django-cbv-patterns/
│   ├── django-testing/
│   ├── django-new-api/
│   ├── django-feature/
│   └── django-normalize/
├── python/                  # Python ecosystem (uv, ruff, pre-commit, pytest)
│   └── python-tooling/
├── frontend-core/           # Framework-agnostic JS / TS / testing conventions
│   ├── frontend-conventions/
│   ├── frontend-data-layer/
│   ├── frontend-testing/
│   ├── frontend-normalize/
│   └── typescript-patterns/
├── react/                   # React ecosystem (React + Next.js + Vite SPA + TanStack Router)
│   ├── react-patterns/
│   ├── react-spa/
│   ├── nextjs-patterns/
│   └── tanstack-router/
├── astro/                   # Astro framework
│   └── astro/
├── tailwind/                # Tailwind CSS
│   └── tailwindcss-v4/
├── http/                    # HTTP / network requests
│   └── fetch/
├── design/                  # Design and content
│   ├── ui-ux/
│   └── copywriting/
└── workflow/                # Git, agent meta-files, project documentation
    ├── gpush/
    ├── agent-instructions/
    └── project-docs/
```

Categories with a single skill (`astro/astro/`, `tailwind/tailwindcss-v4/`, etc.) are deliberate placeholders — new skills for the same technology drop into the same folder without reorganising the repo.

## Skills

### `django/` — Django + DRF backend

| Skill | Description |
|-------|-------------|
| `django-conventions` | The Django rulebook: UUID PKs, soft-delete `BaseModel`, `abstracts/` folders, owner FK, custom pagination, dual auth, mandatory admin/tests/API docs. |
| `django-orm-patterns` | Models layer: abstract bases, managers, soft-delete, UUID, owner FK, queries, transactions/savepoints, safe migrations. |
| `django-rest-framework` | Serialization + API infra: serializers, validation, JWT + API-key auth, permissions, custom pagination, domain exceptions + global handler, consistent response renderer, drf-spectacular. |
| `django-cbv-patterns` | View layer: ViewSet vs APIView vs generics, base classes, `@action` with `url_path`. |
| `django-testing` | pytest + factory-boy, fixtures, the TDD loop, what to assert per layer. |
| `django-new-api` | `/django-new-api` — scaffold a new Django + DRF API from scratch with the full baseline wired. |
| `django-feature` | `/django-feature` — add a complete vertical slice (model + admin + serializer + view + urls + tests + migration), test-first. |
| `django-normalize` | `/django-normalize` — audit an existing project against the conventions and apply fixes incrementally and safely. |

### `python/` — Python ecosystem

| Skill | Description |
|-------|-------------|
| `python-tooling` | uv, ruff, pre-commit, pytest, `pyproject.toml`. Language tooling, not Django-specific. |

### `frontend-core/` — JS / TS / testing conventions

| Skill | Description |
|-------|-------------|
| `frontend-conventions` | The frontend rulebook: named exports, function vs arrow, kebab-case, no casting, `type` over `interface`, `@/` alias, no drive-by refactors. |
| `typescript-patterns` | `type` vs `interface`, type-only imports, unions over enums, guards over casts, `keyof typeof`, `ComponentProps`/`PropsWithChildren`. |
| `frontend-data-layer` | React Query (server state) vs Zustand (UI state), single Axios instance + interceptors, SSE streaming, auth/session, mitt events. |
| `frontend-testing` | vitest + Testing Library + jsdom + user-event + MSW, colocated tests, query by role/label, mock HTTP at the network. |
| `frontend-normalize` | `/frontend-normalize` — audit an existing JS/TS/React frontend (Vite/Next/CRA) and normalize incrementally. |

### `react/` — React ecosystem

| Skill | Description |
|-------|-------------|
| `react-patterns` | React 19 components/hooks, "you might not need an Effect", effect deps, `useMemo`/`useCallback` discipline, refs as props, keys, state shape. |
| `react-spa` | Vite + React SPA setup (no Next.js): `@/*` alias in both `tsconfig.json` AND `vite.config.ts`, typed `import.meta.env.VITE_*`, project structure (`src/features`, `src/routes`, `src/components/ui`, `src/lib`), `main.tsx` + `index.html` essentials. |
| `nextjs-patterns` | Next.js App Router: route groups, server vs client components, route handlers, `NEXT_PUBLIC_` env vars, dynamic imports for SSR-unsafe libs, metadata. |
| `tanstack-router` | Type-safe SPA router: file-based routing with the Vite plugin, `createFileRoute`, search params validated with Zod, route loaders integrated with React Query, `beforeLoad` auth guards, type-safe `<Link>`/`useNavigate`. **Always consults Context7 before answering**. |

### `astro/` — Astro framework

| Skill | Description |
|-------|-------------|
| `astro` | Astro expert: pages, components, layouts, content collections, islands (`client:*`), SSR adapters, View Transitions, `astro:assets`. **Always consults Context7 before answering** and ensures the `@/*` alias is configured. |

### `tailwind/` — Tailwind CSS

| Skill | Description |
|-------|-------------|
| `tailwindcss-v4` | Tailwind v4 expert: CSS-first config via `@theme`, custom utilities/variants, container queries, OKLCH colours, v3 → v4 migration. **Always consults Context7 before answering** — v4's API moved significantly. |

### `http/` — Network requests

| Skill | Description |
|-------|-------------|
| `fetch` | HTTP requests with the Web Fetch API: request shape, status-vs-network errors, AbortController for timeouts/cancellation, retries with exponential backoff, auth headers, server vs client context, standard response envelope, TypeScript at the boundary. |

### `design/` — Design and content

| Skill | Description |
|-------|-------------|
| `ui-ux` | Design expert for screens with no mockup — hierarchy, palette (OKLCH + WCAG AA), type scale, 4/8-pt spacing, layout patterns, states, accessibility, design tokens that flow into Tailwind. |
| `copywriting` | Microcopy expert: CTAs, errors, empty states, headlines, onboarding. Writes in the language of the surrounding interface; picks voice/tone; avoids filler and faux-friendly chatter. |

### `workflow/` — Git, agent meta-files, project docs

| Skill | Slash command | Description |
|-------|---------------|-------------|
| `gpush` | `/gpush` | Stages changes, writes a Conventional Commits message (with type heuristics, BREAKING CHANGE support, monorepo scope, footers and pre-commit hook re-stage), pushes the current branch, offers PR or merge to base. |
| `agent-instructions` | `/agent-instructions` | Create or update a repo's `AGENTS.md` (canonical router into `docs/`) and `CLAUDE.md` (thin pointer + Claude-specific directives). |
| `project-docs` | `/project-docs` | Create or update a project's `docs/` set (`ARCHITECTURE`, `WORKFLOW`, `COMMANDS`, `DESIGN`, `ONBOARDING`) by interviewing the user. Language- and framework-agnostic. |

## Adding a new skill

1. Pick the category folder where the skill belongs (or create a new one if no existing category fits).
2. Create a new directory inside it: `mkdir <category>/my-skill`.
3. Add `SKILL.md` with frontmatter (`name`, `description`, optional `disable-model-invocation`) and instructions. Keep `SKILL.md` under ~500 lines; move long reference material into separate files.
4. Optional: a `scripts/` subfolder for executable helpers, an `assets/` subfolder for templates.
5. Commit and push. After your next `git pull`, re-run `npx skills add https://github.com/criscandv/cdv-skills.git` on every machine to pick up the new skill.

## License

Personal use. Not licensed for redistribution.
