# cdv-skills

Personal collection of [Claude Code](https://docs.claude.com/en/docs/claude-code) skills.

Skills extend Claude Code with custom workflows. Each skill lives in its own directory with a `SKILL.md` file containing instructions and metadata.

## Structure
cdv-skills/
├── install.sh          # Symlinks each skill into ~/.claude/skills/
├── gpush/              # Smart git push with PR and merge support
└── ...                 # More skills added over time

## Installation

Clone the repo and run the installer:

```bash
git clone git@github.com:<your-username>/cdv-skills.git ~/Development/cdv-skills
cd ~/Development/cdv-skills
./install.sh
```

The installer creates a symlink from each skill directory to `~/.claude/skills/<skill-name>`. Edits in the repo are reflected instantly — no reinstall needed.

## Skills

### Git

| Skill | Slash command | Description |
|-------|---------------|-------------|
| `gpush` | `/gpush` | Stages changes, writes a Conventional Commits message in English, pushes the current branch, and offers PR or merge to base. |

### Django / DRF — references (auto-invoked)

These encode the conventions for building Django backends as REST APIs. They trigger automatically when relevant.

| Skill | Description |
|-------|-------------|
| `django-conventions` | The rulebook: UUID PKs, soft-delete BaseModel, abstracts/ folders, owner FK, middleware, exception handler + response envelope, custom pagination, dual auth, type hints, mandatory admin/tests/API docs. Points to the layer skills below. |
| `django-orm-patterns` | Models layer: abstract bases, managers, soft-delete, UUID, owner FK, queries, transactions/savepoints, safe migrations. |
| `django-rest-framework` | Serialization + API infra: serializers, validation, JWT + API-key auth, permissions, filtering, custom pagination, domain exceptions + global handler, consistent response renderer, drf-spectacular. |
| `django-cbv-patterns` | View layer: ViewSet vs APIView vs generics, base classes/mixins, `@action` with `url_path`, get_queryset/perform_create. |
| `django-testing` | pytest + factory-boy, fixtures, the TDD loop, what to assert per layer, coverage. |
| `python-tooling` | uv, ruff, pre-commit, pytest config, pyproject.toml. Language tooling, not Django-specific. |

### Frontend (JS / TS / React / Next.js) — references (auto-invoked)

Conventions for building frontends. They trigger automatically when relevant.

| Skill | Description |
|-------|-------------|
| `frontend-conventions` | The rulebook: named exports, function vs arrow, kebab-case, no casting, type over interface, string unions, object params, `@/` alias, clsx/cn, no drive-by refactors, brace/spacing rules. Points to the layer skills below. |
| `typescript-patterns` | type vs interface, type-only imports, unions over enums, guards over casts, `keyof typeof`, `ComponentProps`/`PropsWithChildren`, no speculative generics. |
| `react-patterns` | React 19 components/hooks, "you might not need an Effect", effect deps, `useMemo`/`useCallback` discipline, refs as props, keys, state shape. |
| `nextjs-patterns` | App Router: route groups, server vs client components, route handlers, `NEXT_PUBLIC_` env vars, dynamic imports for SSR-unsafe libs, metadata. |
| `frontend-data-layer` | React Query (server state) vs Zustand (UI state), the single Axios instance + interceptors, SSE streaming, auth/session, mitt events. |
| `frontend-testing` | vitest + Testing Library + jsdom + user-event + MSW, colocated tests, query by role/label, mock HTTP at the network. |

### Design & Content — references (auto-invoked)

| Skill | Description |
|-------|-------------|
| `ui-ux` | Design expert for screens with no mockup — hierarchy, palette (OKLCH + WCAG AA contrast), type scale, 4/8-pt spacing, layout patterns, states (default/hover/focus/loading/empty/error), accessibility, design tokens as the vocabulary that flows into Tailwind. Framework-agnostic. |
| `tailwindcss-v4` | Tailwind CSS v4 expert: CSS-first config via `@theme`, custom utilities/variants (`@utility`, `@custom-variant`), container queries, OKLCH colours, v3 → v4 migration. **Always consults Context7 before answering** — v4's API moved significantly. |
| `copywriting` | Microcopy expert: CTAs, error messages, empty states, headlines, onboarding. Writes in the language of the surrounding interface, picks voice/tone, follows length-by-surface caps, avoids filler and faux-friendly chatter. |

### Astro & HTTP — references (auto-invoked)

| Skill | Description |
|-------|-------------|
| `astro` | Astro web framework expert: pages, components, layouts, content collections, islands (`client:*`), SSR adapters, View Transitions, `astro:assets`, the CLI. **Always consults Context7 before answering** (Astro moves between minor releases). Ensures the `@/*` path alias is configured (creates it if missing). Defers styling to tailwindcss-v4 and HTTP requests to fetch. |
| `fetch` | HTTP requests with the Web Fetch API: request shape, response parsing, the status-vs-network-error distinction, AbortController for timeouts/cancellation, retries with exponential backoff, auth headers, server vs client context, the standard response envelope, TypeScript at the boundary. Works in browser, Astro frontmatter, Next Server Components, Node, edge runtimes. |

### Actions (slash-invoked)

| Skill | Slash command | Description |
|-------|---------------|-------------|
| `django-new-api` | `/django-new-api` | Scaffold a new Django + DRF API project from scratch with the full baseline wired (settings split, custom user, abstracts, middleware, exceptions, pagination, renderer, dual auth, drf-spectacular, ruff/pre-commit/pytest). |
| `django-feature` | `/django-feature` | Add a complete vertical slice for a new entity (model, admin, serializer, view, urls, factory, tests, migration) to an existing project, test-first. |
| `django-normalize` | `/django-normalize` | Audit an existing project against the conventions and bring it up to standard incrementally and safely (additive fixes first, data-risk migrations last with confirmation). |
| `frontend-normalize` | `/frontend-normalize` | Audit an existing JS/TS/React frontend (Vite/Next/CRA) against the conventions and normalize incrementally — additive fixes first (single Axios instance, MSW, alias, strict TS), structural moves (feature modules, kebab-case, named exports) confirmed, risky refactors (default→named codemod, JS→TS, routing/state migrations) only with explicit sign-off. |
| `project-docs` | `/project-docs` | Create or update a project's `docs/` set (ARCHITECTURE, WORKFLOW, COMMANDS, DESIGN, ONBOARDING) by interviewing the user. Language- and framework-agnostic. |
| `agent-instructions` | `/agent-instructions` | Create or update a repo's agent entry-point files: AGENTS.md (canonical router into `docs/`) and CLAUDE.md (thin pointer + Claude-specific directives). Language- and framework-agnostic. |

## Adding a new skill

1. Create a new directory at the repo root: `mkdir my-skill`
2. Add a `SKILL.md` with frontmatter (`name`, `description`, etc.) and instructions.
3. Run `./install.sh` to symlink it into `~/.claude/skills/`.
4. Commit and push.

## License

Personal use. Not licensed for redistribution.
