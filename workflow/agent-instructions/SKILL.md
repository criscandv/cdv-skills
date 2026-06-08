---
name: agent-instructions
description: Create or update a repository's agent entry-point files — AGENTS.md (the canonical router) and CLAUDE.md (a thin pointer to it) — for any project that lacks them. AGENTS.md holds a slim project description plus a "when to consult each document" map into docs/ and any project directives; CLAUDE.md is short and defers to AGENTS.md, adding only Claude-specific directives. Use this skill when a repo has no CLAUDE.md or AGENTS.md, when those files are stale, or when setting up a new project for agentic work. Trigger on "create a CLAUDE.md", "set up AGENTS.md", "this repo needs agent instructions", "add agent entry-point files". Language- and framework-agnostic. Slash-invoked. Pairs with project-docs, which populates the docs/ that these files route into.
disable-model-invocation: true
---

# /agent-instructions — AGENTS.md (+ CLAUDE.md) entry points

Give a repository the entry-point files an agent reads first. The design avoids the duplication that causes drift: **AGENTS.md is the single source of truth** — a slim router that describes the project and points to the detailed docs — and **CLAUDE.md is a short file that defers to AGENTS.md**, carrying only Claude-specific directives. One canonical document, no two copies to keep in sync.

These files are routers, not encyclopedias. They orient an agent in a few seconds and send it to the right place (the `docs/` set, a specific skill, a command reference). Keep them slim; depth lives in `docs/` (see the `project-docs` skill).

Communicate in Spanish (the user's preference). Write the files in the team's code-facing language (default English).

## What it produces

```
AGENTS.md   # canonical: project description + "consult each document" map + directives
CLAUDE.md   # thin: one-line description + "instructions live in AGENTS.md" + Claude directives
```

## Workflow

### 1. Inspect, don't clobber

- Check whether `AGENTS.md` / `CLAUDE.md` already exist. If they do, **update** them — preserve content that's still accurate; don't overwrite wholesale.
- Read the repo to learn what to route to: the project's purpose (from README/manifests), whether it's a **monorepo** (multiple sub-projects, each with its own role and aliases), and what lives in `docs/` (`ARCHITECTURE.md`, `WORKFLOW.md`, `COMMANDS.md`, `DESIGN.md`, `ONBOARDING.md`, etc.).
- **Check for spec/workflow tooling installed in the repo** before drafting directives. The presence of these tools changes what the planning directive should say:
  - `openspec/config.yaml` (and `openspec/{specs,changes}/`) → the project uses **OpenSpec**. Planning is `/opsx:propose` → `/opsx:apply` → `/opsx:archive` with artefacts under `openspec/changes/<name>/`. **Do not** add a directive that points plans to `docs/specs/`; if one exists in CLAUDE.md/AGENTS.md, treat it as stale and replace it.
  - `.taskmaster/` / `.specstory/` / other planning tools — same logic: their workflow owns the planning directive, not generic "plans live in `docs/`" boilerplate.
- If `docs/` is missing or thin, the "consult each document" map will be sparse. Offer to run **project-docs** first to create the docs, then this skill routes into them. You can still generate a useful AGENTS.md now and enrich it later.

### 2. Gather the directives

Ask the user for the project's behavioural directives — the short, imperative rules an agent must follow. Common ones (offer, don't assume):

- How to push (e.g. "use the `gpush` skill", or a specific git flow).
- Whether plans must be approved before implementation, and where plans live. **If the inspection in step 1 found a spec workflow tool, the directive is fixed** — for OpenSpec, write: *"Spec-driven planning is OpenSpec. All non-trivial work flows through `/opsx:propose` → `/opsx:apply` → `/opsx:archive`. Proposals, designs and tasks live under `openspec/changes/<name>/`; long-lived specs under `openspec/specs/`. Do not implement a change until its artefacts are approved."* Add an explicit *"never use `docs/specs/`"* anti-rule when relevant — if any historical file or doc still points there, it will mislead future sessions.
- Any "never do this" rules (don't commit to `main`, don't run destructive migrations without confirmation, etc.).
- Which skills/agents to use for which domains.

Keep these to a handful of lines — directives, not documentation.

### 3. Write AGENTS.md (canonical)

Follow this structure; drop sections that don't apply (e.g. the sub-projects table for a single-package repo):

```markdown
# <Project name>

<One-paragraph description of what the project is and does.>

<For a monorepo, a short list/table of sub-projects with their role and the
aliases people use for each, e.g. "the api / el backend".>

## When to consult each document

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — stack, folder structure, code conventions.
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) — how we work: planning, testing, verification, Git.
- [`docs/COMMANDS.md`](docs/COMMANDS.md) — every command across the project.
- [`docs/DESIGN.md`](docs/DESIGN.md) — brand manual (only if the project has a UI).
- [`docs/ONBOARDING.md`](docs/ONBOARDING.md) — bootstrapping a fresh clone.

## Directives

- <directive 1>
- <directive 2>
```

Only list documents that actually exist. The links are relative so they work on GitHub and in editors.

### 4. Write CLAUDE.md (thin pointer)

CLAUDE.md stays short and points at the canonical file, adding only what's specific to Claude (skills to reach for, Claude-side workflow notes):

```markdown
# <Project name> — Claude

Agent instructions for this repo live in [`AGENTS.md`](AGENTS.md). Read it first.

## Claude-specific directives

- <e.g. "When the user asks to push, invoke the `gpush` skill.">
- <e.g. "When a plan is requested, do not implement until the user approves it.">
- <Any skills that apply to this project (e.g. django-* skills for a Django API).>
```

If the user picked a different relationship model (both files identical, or CLAUDE.md only), honour that instead — but the default and recommended shape is this pointer, so there's one source of truth.

### 5. Verify

- Confirm every `docs/...` link in AGENTS.md resolves to a real file; remove links to docs that don't exist yet.
- Confirm the description and sub-project list match the actual repo.
- Show the user both files and invite corrections.

## Notes

- **Slim by design.** These are routers; if a section grows past a few lines it probably belongs in a `docs/` file that AGENTS.md links to.
- **Single source of truth.** Keeping the full router only in AGENTS.md and pointing CLAUDE.md at it is what prevents the two files from drifting apart.
- **Update, don't overwrite.** Merge into existing files; never discard accurate content.
- **After a structural refactor, treat the existing files as suspect.** When this skill is run right after a workflow that reshapes the code (e.g. `/django-normalize` converting PK types, moving classes, renaming bases) or after a new tool was installed (e.g. OpenSpec replacing an old `docs/specs/` flow), assume the existing `CLAUDE.md` / `AGENTS.md` may contain claims that no longer match the codebase. Read each directive and routing line, and verify it against the current code and the current tooling — a stale fact ("this repo uses integer PKs", "plans live in `docs/specs/`", "AbstractBaseModelAdmin lives in admin/base_admin.py") will mislead every future agent that opens the repo. Drop or rewrite the obsolete lines; do not blindly preserve them.
- Composes with **project-docs** (creates the `docs/` these route into) and is commonly run by setup workflows for a fresh repo.
