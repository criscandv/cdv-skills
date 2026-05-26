---
name: project-docs
description: Create or update a project's operational documentation set under docs/ — ARCHITECTURE, WORKFLOW, COMMANDS, DESIGN and ONBOARDING — by interviewing the user about the project and writing the files from what they describe. Language- and framework-agnostic: works for any codebase (Python, Node, Go, mobile, monorepo, etc.). Use this skill when a project has no docs/ folder, when docs are stale or incomplete, or when another workflow (e.g. django-normalize) detects missing documentation. Trigger on "document this project", "create the docs folder", "we need an architecture/onboarding doc", "set up project documentation". This is a slash-invoked action.
disable-model-invocation: true
---

# /project-docs — the docs/ set, from an interview

A project's `docs/` folder is where its **specific** configuration lives — the things that are true of *this* repo and override any general convention: its stack, its layout, its commands, its process, its brand. This skill builds or refreshes that set by inspecting the repo and interviewing the user, then writing clean, accurate docs they'll actually keep.

It is deliberately **agnostic of language and framework**. The same five documents serve a Django API, a React app, a Go service or a mixed monorepo — only the content differs.

Communicate in Spanish (the user's preference). Write the documents in the language the user wants them in (default: match the team — often English for code-facing docs).

## The document set

```
docs/
  ARCHITECTURE.md   # how the pieces fit, where responsibilities live, code conventions
  WORKFLOW.md       # how we work: planning, branching, testing, verification, commits, PRs
  COMMANDS.md       # every command, grouped by component and task
  DESIGN.md         # brand/UI manual — ONLY if the project has a user interface
  ONBOARDING.md     # bootstrap a fresh clone to a running state
```

Plus a slim root pointer is useful: a short `CLAUDE.md` (or `README` section) that says what the project is and which doc to consult for what.

`DESIGN.md` is conditional — skip it for a pure backend, library or CLI with no UI.

## Workflow

### 1. Inspect first, ask second

Before interviewing, read what the repo already tells you so questions are informed, not lazy:

- Detect the stack from manifests: `pyproject.toml` / `requirements.txt`, `package.json`, `go.mod`, `Cargo.toml`, `Gemfile`, etc.
- Detect structure: top-level folders, whether it's a monorepo (multiple sub-projects), where source/tests live.
- Detect tooling: linters/formatters, test runners, `.pre-commit-config.yaml`, CI files, `Dockerfile` / `docker-compose`, `Makefile` / task runner.
- Note what `docs/` already exists — this skill **updates** rather than clobbers; preserve content that's still accurate.

Summarise what you inferred and confirm it with the user; that turns the interview into corrections rather than dictation.

### 2. Interview for the gaps

Ask only what you couldn't infer. Group questions; don't overwhelm. The information each document needs:

**For ARCHITECTURE** — what the project does (one paragraph); the components and how they communicate; the stack per component; the repo layout; key code conventions (naming, file organisation, language-specific rules) the team enforces.

**For WORKFLOW** — branching model and naming; whether planning/specs precede work; testing approach (TDD? coverage target?); how changes are verified before merge; commit message convention; PR and merge process; any hard "never do this" rules; whether external-docs lookups or specific agents/tools are part of the process.

**For COMMANDS** — setup/install, run (dev + prod), test, lint/format, build, database/migrations, deploy — the exact commands, per component and per run mode (native vs Docker).

**For DESIGN** (only with a UI) — typography, colour palette, design tokens, spacing/radius scales, key components, and where the source of truth lives (Figma, a tokens file).

**For ONBOARDING** — prerequisites and versions; clone-to-running steps for each supported mode (native, Docker); required env vars and where to get them; how to verify the setup works.

### 3. Write the documents

Write each file from the gathered facts — not generic boilerplate. Concrete commands, real folder names, the project's actual conventions. Each document below lists the sections to include; adapt to the project (drop sections that don't apply, add ones that do).

**ARCHITECTURE.md**: one-line purpose · system overview (components + a simple diagram of how they talk) · repo layout (annotated tree) · per-component stack table · responsibility boundaries · code conventions (general + per-language) · a short decisions log (notable choices and why).

**WORKFLOW.md**: a quick-map of the lifecycle (spec → branch → implement → test → verify → commit → PR → merge) · each step in detail · testing workflow · verification checklist before "done" · commit/PR/merge conventions · a "hard rules — non-negotiable" list.

**COMMANDS.md**: grouped command reference (Setup · Run · Test · Lint/Format · Database · Build · Deploy), with the exact invocation for each, separated by component and by native/Docker mode where both exist.

**DESIGN.md** (conditional): brand intro · typography · colour palette (with tokens/hex) · spacing & radius scales · component inventory · source-of-truth links.

**ONBOARDING.md**: prerequisites · bootstrap steps per mode · env var setup · first-run verification · troubleshooting common setup issues.

Keep them factual and scannable; these are reference docs, not prose essays. Cross-link between them (ARCHITECTURE points to COMMANDS for the actual commands, etc.).

### 4. Add the root pointer and verify

- The repo's agent entry-point files (`AGENTS.md` + `CLAUDE.md`) are what route into these docs. Creating or refreshing them is the **agent-instructions** skill's job — run it after the docs exist so its "when to consult each document" map is accurate. Don't duplicate that router here.
- Re-read each generated file for accuracy against the repo (do the commands exist? do the paths match?). Fix drift before handing off.
- Show the user the file list and a short summary of each, and invite corrections — docs are only useful if they're right.

## Notes

- **Update, don't overwrite.** If a doc already exists, merge new/corrected info and keep what's still true.
- **Don't invent.** If a command or value is unknown, ask — a wrong command in the docs is worse than a gap.
- These docs are the project's source of truth for project-specific config; general engineering conventions live in the relevant skills, and where a doc here is more specific, it takes precedence.
- When invoked by another skill (e.g. django-normalize found no `docs/`), focus on capturing the current reality of the project accurately, so the calling workflow can rely on it.
