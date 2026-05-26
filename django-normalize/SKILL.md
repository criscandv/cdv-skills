---
name: django-normalize
description: Audit an existing Django + DRF project against the house conventions and bring it up to standard incrementally and safely. Use this skill when the user wants to modernise, standardise, normalise, refactor-to-convention or "clean up" an existing Django backend — adding soft-delete, UUID PKs, the owner FK, request-context middleware, a global exception handler, a consistent response envelope, custom pagination, dual auth, mandatory admin, API docs, tests, or the uv/ruff/pre-commit toolchain. Trigger on "normalize this project", "apply our conventions to this repo", "este proyecto no sigue el estándar". This is a slash-invoked action. For a brand-new project use django-new-api; to add a single entity use django-feature.
disable-model-invocation: true
---

# /django-normalize — bring an existing project up to standard, safely

Existing projects rarely match the conventions in **django-conventions**, and the gap is uneven: some fixes are harmless additions, others rewrite primary keys on tables full of live data. The whole point of this skill is to **separate the safe from the dangerous**, apply the safe changes confidently, and never touch the dangerous ones without a written plan and explicit user sign-off.

Two rules govern everything:

- **Incremental, not a big-bang rewrite.** One concern per branch/commit, verified before the next. A pull request that "normalises everything" is unreviewable and unrevertable.
- **The project's own docs win.** If the repo documents a deliberate deviation (in its `ARCHITECTURE.md` / `WORKFLOW.md`), respect it — surface it, don't silently override it.

Communicate progress in Spanish. All code is in English.

## Stage 0 — orient

Read the project before changing anything:

- Look for `docs/` (`ARCHITECTURE.md`, `WORKFLOW.md`, `COMMANDS.md`, `DESIGN.md`, `ONBOARDING.md`). Read what exists — it may encode intentional choices that override the default conventions. **If `docs/` is missing, offer to run the `project-docs` skill** to interview the user and create it; capturing the project's real stack/process first makes the rest of the audit accurate.
- Identify the Django version, the apps, the package layout, and how the project is run/tested.
- Confirm you're on a clean working tree and create a working branch (`chore/normalize-<area>`); never work on `main`.

## Stage 1 — audit and report

Walk the checklist below and produce a **gap report**: for each item, its current state, whether it conforms, and the risk of fixing it. Don't change anything yet — the report is the deliverable of this stage.

### Convention checklist

Structure & tooling (additive / mechanical):
- `models.py` / `views.py` / `serializers.py` / `admin.py` are **packages**, not single files.
- One class per file; `__init__.py` re-exports; abstract bases under `abstracts/` (not `lib/`).
- `uv` + `pyproject.toml` (no `requirements.txt`); `ruff` configured; `pre-commit` installed; settings split under `config/settings/`.
- Type hints on public signatures; English-only identifiers/comments; no emojis.

API plumbing (additive — low risk):
- `RequestContextMiddleware` populating `request.current_user`.
- Global `EXCEPTION_HANDLER` + domain exceptions subclassing `APIException`.
- Standard response **renderer** (one envelope: `{success, message, data}` / `{success, message, errors}`).
- Custom **pagination** class set as default.
- Dual auth: JWT (simplejwt) **and** API-key authentication for public endpoints.
- Every model registered in the **admin** (ideally via a `BaseModelAdmin`).
- API docs via `drf-spectacular`.
- Class-based views with explicit `permission_classes`/`serializer_class`/`queryset`; every `@action` has `url_path`.

Tests:
- `pytest` + `pytest-django` + `factory-boy`; `tests/` package per app; coverage tracked (target ≥ 80%).

Data-model contract (risk varies — see Stage 4):
- **Soft-delete**: `BaseModel` with `deleted_at` + `active`, `ActiveManager` as default, `all_objects` escape hatch.
- **Owner FK**: every domain model has a FK to the user (except deliberate global data).
- **UUID PKs** instead of autoincrement.

Classify each gap as **additive** (new code, no schema change to existing data), **structural** (moves/renames, import churn, no data risk) or **data-risk** (schema/PK/constraint changes on populated tables).

## Stage 2 — agree the scope and order

Present the gap report to the user and agree what to tackle and in what order. Default order is by ascending risk: tooling/plumbing first, structure next, data-model contract last. Let the user defer or skip items. **Do not bundle a data-risk change with safe ones** in the same commit.

## Stage 3 — apply additive and structural fixes

These carry no data risk; apply them one concern per branch/commit, each verified with the test suite before moving on. Use the layer skills for the exact code:

- **Middleware, exception handler + domain exceptions, response renderer, custom pagination, API-key auth** → **django-rest-framework** (and the request-context pattern in **django-conventions**). These are pure additions: new modules + settings wiring. When the project already has an ad-hoc error helper (e.g. a `handle_exception()` called manually, or exceptions subclassing bare `Exception`), upgrade it to `APIException` subclasses + a global handler, but **keep existing call sites working** — migrate them in step, don't leave half the code raising the old type. This is exactly the case the user cares about: a project without proper exception handling/envelope gets it added here.
- **Admin registration** for any unregistered model; introduce `BaseModelAdmin` and point existing admins at it.
- **drf-spectacular** wiring + schema/docs URLs.
- **Tooling**: introduce `uv`/`pyproject.toml`, `ruff` config, `pre-commit`; run `ruff format` as its own dedicated commit so formatting noise doesn't drown real changes in later diffs.
- **Structural**: convert single-file modules to packages, split one-class-per-file, add `abstracts/`, fix `__init__` re-exports. Mechanical but high-churn — do it as an isolated commit, run the full suite, and rely on `grep` to confirm no import broke.

After each change: `uv run python manage.py check`, run the suite, `ruff check`. Green before the next.

## Stage 4 — data-model contract (handle with care)

These change the schema of tables that may hold live data. Each needs a written migration plan and **explicit user confirmation before `migrate`**. Never auto-apply.

### Soft-delete (medium risk)

Adding `deleted_at` (nullable) and `active` (default `True`) is additive at the column level. The risk is the **manager swap**: making `ActiveManager` the default hides any row not matching `active=True, deleted_at IS NULL`. Plan: add the fields → data-migration to set `active=True, deleted_at=NULL` on existing rows → then switch the default manager and add `all_objects`. Verify no existing query silently loses rows.

### Owner FK (medium–high risk)

Adding a required `user` FK to a populated table can't be done in one step — there's no value for existing rows. Plan: add the FK as `null=True` → backfill owners via a `RunPython` data migration (the rule for assigning owners is a business decision — ask) → enforce `null=False` in a follow-up migration. If ownership genuinely can't be reconstructed, flag it; don't invent owners.

### UUID primary keys (HIGH risk — default to NOT auto-converting)

Switching an existing table's PK from autoincrement to UUID is the most dangerous change here: it rewrites the PK and **every FK that references it**, breaks existing external references and URLs that use integer IDs, and on a large table is a long, locking migration. **Do not do this as a routine normalisation step.** Options, in order of preference:

1. **New tables only** — apply UUID PKs to models created from now on (via `BaseModel`); leave existing tables on their current PK. This is usually the right call.
2. If the user truly needs to convert an existing table, treat it as a dedicated project with its own plan: add a new UUID column → backfill → repoint FKs → swap → update every consumer (API, frontend, integrations). Spell out the blast radius and get explicit sign-off. Recommend the architecture/ADR workflow for the decision.

Always pause and confirm before running any destructive migration; offer the safer multi-step route.

## Stage 5 — re-verify and report

When the agreed scope is done:

```bash
uv run python manage.py check
uv run pytest --cov=apps --cov-report=term-missing
uv run ruff check . && uv run ruff format --check .
```

Report what was normalised, what was deliberately deferred (especially any data-risk items), and the recommended next steps. If `docs/` was created or should be updated to reflect the new conventions, note it.

## Guardrails

- Never run a destructive migration without explicit confirmation; always offer the multi-step alternative.
- Never bulk-rewrite the whole repo in one commit — incremental, verified, revertable.
- Respect documented deviations in the project's own `docs/`.
- Don't fabricate data (owners, defaults) to satisfy a constraint — ask when the value is a business decision.
- Keep the test suite green at every step; a normalisation that breaks tests is not normalisation.
