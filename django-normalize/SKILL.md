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

**Partial implementations are gaps, not passes.** A project that has `apps/<app>/models/` as a package counts only if each model also lives in its own file and the abstract bases live in `abstracts/`. A project that has a `.pre-commit-config.yaml` counts only if it runs the full hook set listed below, not just ruff. A project that has an exception handler counts only if it lives in `exceptions/handler.py` with the standard envelope, not in `lib/`. If you find yourself thinking "well, it's *kind of* done", mark it as a gap.

### Convention checklist

**Project layout — every box must be present and complete:**
- `apps/<app>/models/`, `serializers/`, `views/`, `admin/` are **packages**, not single files.
- **One class per file**, named after the entity/concept (`worker.py`, `login.py`, `company_registration.py`) — a package containing grouped files (`worker_serializers.py` with three classes, `auth_views.py` with two) does **not** satisfy this; it's a gap, not a pass.
- `__init__.py` re-exports the public symbols so callers use the short import (`from apps.<app>.models import Worker`).
- **`abstracts/` subfolder in every layer that has a shared base**: `models/abstracts/` (UUID/managers/base), `serializers/abstracts/`, `views/abstracts/`, `admin/abstracts/`. Bases live there; never in `lib/`.
- **`lib/` is utilities only** (validators, helpers, formatters). Cross-cutting infrastructure with its own identity goes in its own named package: `exceptions/` (handler + domain), `authentication/` (auth classes), `pagination/`, `renderers/`, `middleware/`. The exception handler living in `lib/` is a gap.
- **No dead or empty packages.** A `viewsets/` folder containing only `__init__.py` is debt — delete it.

**Required apps/<app>/ packages (each with its `__init__.py` re-exports):**
- `models/abstracts/` with `uuid.py` (UUIDPrimaryKeyModel), `managers.py` (ActiveManager), `base.py` (BaseModel).
- `middleware/request_context.py` (RequestContextMiddleware) + registered last in `MIDDLEWARE`.
- `exceptions/` with `domain.py` (APIException subclasses) and `handler.py` (`api_exception_handler` producing `{success, message, errors}`).
- `authentication/api_key.py` (APIKeyAuthentication + APIKeyUser) + registered in `DEFAULT_AUTHENTICATION_CLASSES`. This is part of the **baseline** even if the project doesn't actively use the public path: leave `API_KEY` empty in env to disable; the class stays registered so future public endpoints don't need a settings change.
- `pagination/standard.py` (StandardPagination with `max_page_size`) + `DEFAULT_PAGINATION_CLASS`.
- `renderers/standard.py` (StandardJSONRenderer wrapping `{success, message, data}`) + `DEFAULT_RENDERER_CLASSES`.
- `admin/abstracts/base.py` (BaseModelAdmin) + every model registered in admin, inheriting it (except special cases like the user admin which extends Django's UserAdmin). The `BaseModelAdmin` must show the UUID `id` read-only on both the changelist and the change form (via `get_list_display` / `readonly_fields` / `get_fieldsets`); a stripped-down base that omits this is a gap. **Every concrete admin's ForeignKey fields are in `raw_id_fields`** — `autocomplete_fields` or the default `<select>` dropdown is a gap that becomes a performance problem in production.
- `tests/` package with `__init__.py`, `conftest.py`, `factories.py`, `test_*.py`.

**Settings split — every referenced module must exist:**
- `config/settings/` with `__init__.py`, `base.py`, `development.py`, `staging.py`, `production.py`, `testing.py` (the latter used by pytest).
- If `settings/__init__.py` selects a module via env var, **every branch must have a real file** — a missing `production.py` is a gap that only surfaces at deploy time.

**Tooling — `pyproject.toml` + ruff + pre-commit + pytest:**
- `uv` + `pyproject.toml` (no `requirements.txt`); `ruff` config with the standard rule set; `[tool.pytest.ini_options]` pointing at `config.settings.testing`.
- `pre-commit` installed with the **full hook set**, not just ruff: `ruff` (lint+format) **plus** `trailing-whitespace`, `end-of-file-fixer`, `check-merge-conflict`, `check-yaml`, `check-json`, `check-added-large-files`, and **`no-commit-to-branch`** with the project's protected branches (`main`, plus `develop` if the workflow uses Git Flow).

**API & response shape:**
- Global `EXCEPTION_HANDLER` set to the project's `apps.<app>.exceptions.api_exception_handler`.
- Domain exceptions subclass `APIException`, not bare `Exception`.
- Class-based views have explicit `permission_classes`/`serializer_class`/`queryset`; every `@action` has `url_path` **and** `url_name`.
- `drf-spectacular` installed, in `INSTALLED_APPS`, with `DEFAULT_SCHEMA_CLASS` and `/schema/` + `/docs/` (Swagger) + `/redoc/` URLs exposed.
- `AUTH_USER_MODEL` points at a custom user that inherits both Django auth (`AbstractUser` or `AbstractBaseUser + PermissionsMixin`) **and** `BaseModel`, with a manager that re-applies the soft-delete filter in `get_queryset()`.

**Testing baseline:**
- `pytest` + `pytest-django` + `pytest-cov` + `factory-boy` + `faker` in `[dependency-groups.dev]`.
- `tests/` package per app with `conftest.py` (fixtures: `api_client`, `user`, `auth_client`) and `factories.py`. Coverage target ≥ 80%.

**Code style:**
- Type hints on public signatures; English-only identifiers/comments; no emojis.

**Data-model contract (risk varies — see Stage 4):**
- **UUID PKs** instead of autoincrement (via `UUIDPrimaryKeyModel`).
- **Soft-delete**: `BaseModel` with `deleted_at` (DateTimeField, nullable, db_index) + `active` (BooleanField, db_index), `ActiveManager` as default, `all_objects` as escape hatch.
- **Owner FK**: every domain model has a FK to the user (except deliberate global data).

Classify each gap as **additive** (new code, no schema change to existing data), **structural** (moves/renames, import churn, no data risk) or **data-risk** (schema/PK/constraint changes on populated tables).

## Stage 2 — agree the scope and order

Present the gap report to the user and agree what to tackle and in what order. Default order is by ascending risk: tooling/plumbing first, structure next, data-model contract last. Let the user defer or skip items. **Do not bundle a data-risk change with safe ones** in the same commit.

## Stage 3 — apply additive and structural fixes

These carry no data risk. **The mode here is "apply", not "consider".** For every gap in the report that the user agreed to fix, the work has to land — noting it and moving on is failure. One concern per branch/commit, each verified with the test suite before the next. Use the layer skills for the exact code.

- **API plumbing — apply each missing piece in its target location:**
  - `middleware/request_context.py` + register last in `MIDDLEWARE`.
  - `exceptions/` package: create it if missing, **move** any handler currently sitting in `lib/` (e.g. `lib/exception_handler.py`) into `exceptions/handler.py`, and the domain exception classes into `exceptions/domain.py`. Update `EXCEPTION_HANDLER` in settings to the new path; delete the now-empty `lib/` files (or the relevant parts). The shape must be `{success, message, errors}`.
  - `pagination/standard.py` + `DEFAULT_PAGINATION_CLASS`.
  - `renderers/standard.py` + `DEFAULT_RENDERER_CLASSES`.
  - `authentication/api_key.py` (APIKeyAuthentication + APIKeyUser) + register the class in `DEFAULT_AUTHENTICATION_CLASSES` **even if the project doesn't currently expose public endpoints** — leave `API_KEY` empty in env to disable. The class is part of the baseline.
  - When the project already has an ad-hoc error helper (e.g. a `handle_exception()` called manually, or exceptions subclassing bare `Exception`), upgrade them to `APIException` subclasses + the global handler, but **keep existing call sites working** — migrate them in step.

- **Settings split — every branch of the selector must resolve.** If `config/settings/__init__.py` does `from .production import *` for one environment, the `production.py` file must exist (even as a minimal `from .base import *` + env-specific overrides). A missing module is a gap even when the current dev environment doesn't hit it.

- **Tooling — apply the full standard, not the partial one:**
  - `pyproject.toml` with the ruff rule set + `[tool.pytest.ini_options]` pointing at the test settings.
  - `.pre-commit-config.yaml` with the **whole hook list** (ruff + the hygiene block + `no-commit-to-branch`); a config that runs only ruff is a gap. Read the project's WORKFLOW.md to know which branches to protect (often `main` and `develop`).
  - Add testing deps: `pytest`, `pytest-django`, `pytest-cov`, `factory-boy`, `faker`.

- **Admin** — register any unregistered model; introduce `admin/abstracts/base.py` with `BaseModelAdmin` (the one that prepends `id` to `list_display`, includes it in `readonly_fields` and adds the "Identificador" fieldset on the change form) and point existing admins at it. For every concrete admin, **rewrite `autocomplete_fields = (...)` (and any default-dropdown FK) to `raw_id_fields = (...)`** — this is a mechanical sweep but it's part of the normalization, not a follow-up. **Special case**: the user admin (`WorkerAdmin`/equivalent) often extends Django's `UserAdmin` instead of `BaseModelAdmin`; that's fine, but it still has to add the UUID `id` to `list_display` + `readonly_fields` + an "Identificador" fieldset explicitly, and any FK on it still goes in `raw_id_fields`.

- **drf-spectacular** in `INSTALLED_APPS`, `DEFAULT_SCHEMA_CLASS`, and the `/schema/` + `/docs/` + `/redoc/` URLs in `apps/<app>/urls.py`.

- **Structural moves** — these are mechanical but high-churn; do each as an isolated commit, run the full suite after, and `grep` to confirm no import broke:
  - Convert any single-file `models.py`/`views.py`/`serializers.py`/`admin.py` into packages.
  - **Split grouped files** like `worker_serializers.py` (multiple classes) into one file per class (`worker.py`, `worker_registration.py`, …). Update the package `__init__.py` to re-export under the same names so external callers (urls.py, settings dotted paths like `SIMPLE_JWT.TOKEN_OBTAIN_SERIALIZER`) don't break.
  - Create the `abstracts/` subfolders that should have content (move `base_admin.py` → `admin/abstracts/base.py` and rename `AbstractBaseModelAdmin` → `BaseModelAdmin`; same for any other shared base classes living in the layer's root).
  - **Delete dead packages**: any folder that contains only an `__init__.py` and isn't a real abstracts/ placeholder is debt — `rm -rf` it.

- **Format pass** — run `ruff format` as its own dedicated commit titled "chore: apply ruff format", so future blames can skip past it cleanly and the diff stays reviewable.

After each change: `uv run python manage.py check`, the test suite, `ruff check`, `ruff format --check`. Green before the next. If you didn't run the verification, the change isn't applied yet.

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

## Stage 5 — re-verify, refresh docs, report

### Re-verify the code

When the agreed scope is done:

```bash
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest --cov=apps --cov-report=term-missing
uv run ruff check . && uv run ruff format --check .
uv run pre-commit run --all-files
```

All five must be green before the task is complete.

### Refresh the docs that now lie

A structural normalisation almost always invalidates statements in the project's `docs/`, `CLAUDE.md` and `AGENTS.md`. Scan them and update **any claim that no longer matches the code**:

- **Class names and paths** — if `AbstractBaseModelAdmin` was renamed to `BaseModelAdmin` and moved to `admin/abstracts/base.py`, every doc that referenced the old name/path is now stale.
- **PK type** — a sentence like "this repo uses integer PKs" after a UUID migration is actively misleading; future Claude sessions will trust it and propose wrong code.
- **Folder layout** — diagrams or trees that show the old structure (e.g. `viewsets/` alongside `views/`) need updating.
- **Commands** — if `pre-commit` grew new hooks, the COMMANDS.md examples may need a line; if `tsc --noEmit` or similar entered the workflow, document it.
- **Hard rules / directives** — if Git Flow protected branches changed, or new conventions landed (the response envelope, dual auth), update the directive list in AGENTS.md so its routing stays useful.

Either edit the docs in place where the change is small and obvious, or, when several files drift at once, **invoke `project-docs`** (to refresh `docs/`) and/or **`agent-instructions`** (to refresh `AGENTS.md` and the slim `CLAUDE.md` pointer) and let them re-interview the user against the new state of the code.

### Report

Tell the user, concisely:

- What was normalised (additive, structural, data-model — by group).
- What was deliberately deferred and why (especially any data-risk items the user chose to skip).
- Which docs were refreshed and which still need a pass.
- The recommended next steps (run the test suite locally, open a PR per the WORKFLOW.md branch flow, etc.).

## Guardrails

- **Partial implementations count as gaps**, not passes. A package that mixes multiple classes per file, a `pre-commit` config that runs only ruff, an exception handler stranded in `lib/`, a `production.py` referenced but absent — all of these fail the audit even though "something is there".
- **Stage 3 mode is apply, not consider.** A gap the user agreed to fix must land — moving on after only "noting" it is a defect of this skill.
- **After any structural change, refresh the docs that describe it.** `CLAUDE.md` / `AGENTS.md` / `docs/ARCHITECTURE.md` are not allowed to disagree with the code; out-of-date facts mislead the next session.
- Never run a destructive migration without explicit confirmation; always offer the multi-step alternative.
- Never bulk-rewrite the whole repo in one commit — incremental, verified, revertable.
- Respect documented deviations in the project's own `docs/`.
- Don't fabricate data (owners, defaults) to satisfy a constraint — ask when the value is a business decision.
- Keep the test suite green at every step; a normalisation that breaks tests is not normalisation.
