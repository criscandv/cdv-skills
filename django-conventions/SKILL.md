---
name: django-conventions
description: The rulebook for building Django backends as REST APIs. Use this skill whenever you touch a Django project — creating or editing models, serializers, views/viewsets, admin, middleware, permissions, pagination, migrations, settings or tests — even if the user never says the word "conventions". It defines mandatory standards (UUID primary keys, soft-delete BaseModel, abstracts/ folders, mandatory user FK, custom pagination, global exception handler, request-context middleware, type hints everywhere, mandatory admin, mandatory API docs and tests). Consult it before writing any Django code so the result is consistent. For deep layer-specific patterns it points to django-orm-patterns, django-rest-framework, django-cbv-patterns and python-tooling.
---

# Django Conventions — rulebook

This is the baseline for building Django backends. **Django is always built as an API** (DRF + JSON over HTTP): no server-rendered HTML, no template views, no frontend concern. Target stack: Django 6 + DRF + PostgreSQL, managed with `uv`.

Everything here is the *what* and the *why*. The deep, layer-by-layer *how* lives in companion skills — reach for them as you work:

- **`django-orm-patterns`** — models, abstract bases, managers, soft-delete queries, optimization, migrations.
- **`django-rest-framework`** — serializers, validation, auth (JWT), permissions, filtering, custom pagination, the exception handler, API docs.
- **`django-cbv-patterns`** — the view layer: when to use `ViewSet` vs `APIView` vs generics, base classes, mixins, custom `@action`s.
- **`django-testing`** — pytest + factory-boy test suite, fixtures, the TDD loop, coverage, what to assert per layer.
- **`python-tooling`** — `uv`, `ruff`, `pre-commit`, `pytest`, `pyproject.toml`.

Read those when you need detail. This file is what you keep in your head on every task.

---

## Golden rules

These are non-negotiable because each one prevents a whole class of bugs or rework. If a task seems to require breaking one, stop and surface it to the user rather than silently deviating.

1. **UUID primary keys, never autoincrement.** Sequential integer IDs leak row counts, are guessable, and collide across environments during data merges. Every model gets a `UUIDField` PK via inheritance.
2. **Soft delete, never hard delete.** Records are retired with `deleted_at` (a timestamp) and `active=False`, not removed. A row is *live* only when `deleted_at IS NULL AND active=True`. Data is an asset; deletion is almost always a mistake you discover too late.
3. **Every model carries a FK to the user that owns it.** Multi-tenant data isolation and auditability depend on knowing who a record belongs to. The only exception is genuinely global/reference data (e.g. country lists, shared catalogs) where ownership makes no business sense — and that exception must be deliberate.
4. **Reuse before you write.** Before adding any model, serializer, view, permission, filter or helper, look for an existing abstract/base to inherit from. If the pattern will repeat and no base exists, create the base — never copy-paste.
5. **Type hints on every public signature.** Python 3.13+ syntax. They are documentation that can't go stale and they make the next reader's job trivial.
6. **All code in English, no emojis.** Identifiers, comments, docstrings, commit messages — English. User-facing copy may be Spanish; code never is.
7. **A feature is not done without tests, admin registration, and API docs.** These are part of the definition of done, not optional extras.
8. **Handle errors deliberately with try/except.** Anything that can fail — external API calls, file I/O, parsing, third-party integrations — is wrapped in `try/except` that catches *specific* exceptions (never bare `except Exception` to hide problems). Translate failures into clear domain errors (a custom `APIException`) instead of letting a raw traceback reach the client, and never silently swallow an exception: log it or re-raise. Uncaught bugs should still surface as a logged 500 — error handling is for *expected* failure modes, not for muting real defects.
9. **Destructive and mutating operations run inside a transaction.** Any create/update/delete sequence that must be all-or-nothing is wrapped in `transaction.atomic()`, using savepoints (checkpoints) to roll back risky sub-steps without aborting the whole unit. A half-applied multi-step write leaves the database in a state no code expects — worse than a clean failure. Side effects that must only happen after a successful commit (emails, webhooks, cache invalidation) go through `transaction.on_commit()`.
10. **Every API response uses one consistent envelope.** Success and error responses always share the same top-level shape so the client writes a single parser. Failures are signalled by *raising* a domain exception (an `APIException` subclass) that the global exception handler turns into that same envelope — views never hand-build ad-hoc error dicts. Inconsistent response shapes are a slow tax paid on every frontend integration. Pattern and renderer in `django-rest-framework`.

---

## Project layout and file organisation

We never use single-file `models.py` / `views.py` / `serializers.py` / `admin.py`. Each of those is a **package** (a folder with `__init__.py`), because a flat file becomes a 2000-line dumping ground that nobody can navigate.

```
config/
  settings/
    base.py            # shared settings
    development.py
    staging.py
    production.py
    testing.py         # used by pytest (DJANGO_SETTINGS_MODULE)
  urls.py
  wsgi.py / asgi.py
apps/
  api/                 # domain app, registered as "apps.api"
    models/
      __init__.py      # re-exports public symbols
      abstracts/       # abstract base models live here
        __init__.py
        uuid.py
        base.py
        managers.py
      user.py
      <entity>.py
    serializers/
      __init__.py
      abstracts/       # base serializers / mixins
      <entity>.py
    views/
      __init__.py
      abstracts/       # BaseViewSet / BaseAPIView
      <entity>.py
    admin/
      __init__.py
      abstracts/       # BaseModelAdmin
      <entity>.py
    middleware/
      __init__.py
      request_context.py
    lib/               # cross-module UTILITIES only (helpers, validators, adapters)
      __init__.py
    pagination/        # custom paginator(s)
    exceptions/        # custom exception handler + custom exceptions
    tests/
      __init__.py
      conftest.py
      factories.py
      test_*.py
    migrations/        # the ONLY package that keeps Django's default flat layout
manage.py
pyproject.toml
```

Rules that make this work:

- **One class per file.** Each `Model`, `Serializer`, `ViewSet`, `APIView`, `ModelAdmin` lives in its own file named after the entity. Group only when entities are inseparable (a model and its through-table), and justify it.
- **Re-export from `__init__.py`.** Every package exposes its public symbols so callers write `from apps.api.models import Worker` without knowing the file. Keep `__init__.py` a flat list of imports with no logic.
- **Abstract/base classes go in an `abstracts/` subfolder** of their package — `models/abstracts/`, `serializers/abstracts/`, `views/abstracts/`, `admin/abstracts/`. Re-export them up through `abstracts/__init__.py` and then the package `__init__.py` so the short import form works.
- **`lib/` is for utilities, not parent classes.** Helpers, validators, formatters, third-party adapters scoped to one app. A class meant to be inherited belongs in `abstracts/`, never `lib/`.
- **Create `abstracts/` on demand** — don't pre-create empty folders. The first abstract for a package is what brings the folder into existence.

---

## Models layer (essentials)

Two abstract bases anchor every model. Full detail and query patterns: **`django-orm-patterns`**.

`UUIDPrimaryKeyModel` (`models/abstracts/uuid.py`) — replaces the default `BigAutoField` with a UUID, nothing else:

```python
import uuid
from django.db import models


class UUIDPrimaryKeyModel(models.Model):
    """Abstract base that replaces the default BigAutoField id with a UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
```

`BaseModel(UUIDPrimaryKeyModel)` (`models/abstracts/base.py`) — the standard base for all concrete domain models:

```python
from django.db import models

from .managers import ActiveManager
from .uuid import UUIDPrimaryKeyModel


class BaseModel(UUIDPrimaryKeyModel):
    """
    Abstract base for all concrete domain models.

    Provides UUID PK, created/updated timestamps, soft-delete (deleted_at),
    soft-disable (active), and an ActiveManager that hides non-live records.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    active = models.BooleanField(default=True, db_index=True)

    objects = ActiveManager()        # default manager: only live records
    all_objects = models.Manager()   # escape hatch: admin, internal, tests

    class Meta(UUIDPrimaryKeyModel.Meta):
        abstract = True
        ordering = ["-created_at"]
```

`ActiveManager` (`models/abstracts/managers.py`) filters `deleted_at__isnull=True, active=True` in `get_queryset()`. This means soft-deleted/disabled rows are invisible to normal ORM queries for free — you have to opt in via `all_objects` to see them.

Conventions:

- Every concrete model inherits from `BaseModel`. Extend Meta with `class Meta(BaseModel.Meta): ...` so `ordering` is inherited.
- **Every model gets a FK to the owning user**, e.g. `user = models.ForeignKey("api.User", on_delete=models.CASCADE, related_name="<plural>")`. Skip only for deliberate global/reference data.
- **Always extend the user model.** Use a custom `User(AbstractBaseUser, PermissionsMixin, BaseModel)` with email as `USERNAME_FIELD` and a `UserManager(BaseUserManager)` that **overrides `get_queryset()`** to apply the same `deleted_at__isnull=True, active=True` filter — otherwise `authenticate()` would resolve soft-deleted users. Set `AUTH_USER_MODEL = "api.User"`.
- Never duplicate `id`, `created_at`, `deleted_at` on a concrete model — inherit them.
- Two inheritance levels max (abstract → concrete). No multi-table inheritance without explicit justification.
- Validate at the database level too: `constraints`, `unique_together`, and `clean()` for cross-field rules.
- Migrations come **only** from `makemigrations`. Inspect the generated file before applying. Pause and confirm with the user before destructive migrations (drop column/table, type change, large backfill, index on a large table). The one legitimate hand-edit is adding a `RunPython`/`RunSQL` data backfill to an autogenerated migration.

---

## API layer (essentials)

### Views — ViewSet vs APIView

Both are valid; pick by use case (full guidance in **`django-cbv-patterns`**):

- **`ModelViewSet` / `ViewSet`** when the resource maps cleanly to CRUD and you want routers to wire the URLs. Declare `queryset`, `serializer_class`, `permission_classes`, `filterset_fields`, and `pagination_class` explicitly — never rely on hidden defaults.
- **`APIView` / generics** for endpoints that aren't a standard collection (auth flows, actions, aggregations, anything with bespoke request/response shapes).

Optimise `get_queryset()` with `select_related` / `prefetch_related` to avoid N+1. Build a `BaseViewSet` / `BaseAPIView` in `views/abstracts/` when multiple views share filtering, pagination or permission logic.

**Every `@action` on a viewset must declare an explicit `url_path`** (and a clear `url_name`). Relying on the method name for the URL couples your public API to your Python identifiers — renaming a method silently breaks the route. Example:

```python
@action(detail=True, methods=["post"], url_path="send-payroll", url_name="send-payroll")
def send_payroll(self, request: Request, pk: str | None = None) -> Response:
    ...
```

### Serializers

One serializer per file under `serializers/`, with shared mixins/bases in `serializers/abstracts/`. Use nested serializers for relationships, `validate_<field>` / `validate` for custom rules, and separate read vs write serializers when the shapes diverge. Detail in **`django-rest-framework`**.

### Custom pagination — always

Never ship the bare DRF default. A custom paginator (in `pagination/`) gives a stable, documented response envelope (count, page metadata, links) that the frontend can rely on, plus a `page_size_query_param` with a sane `max_page_size`. Set it as `DEFAULT_PAGINATION_CLASS` and reference it per-view where needed.

### Global exception handler — always

Configure a custom `EXCEPTION_HANDLER` (in `exceptions/`) so every error leaves the API in one consistent JSON shape (status code, machine-readable code, message). Inconsistent error formats are the most common source of frontend pain. Define custom `APIException` subclasses for domain errors.

### Auth — dual: JWT + API key

Two authentication paths coexist:

- **JWT** (`djangorestframework-simplejwt`, access + refresh, rotation + blacklist) for end users. Email-based login. Superusers are admin-only and rejected by the API login endpoint.
- **API key** for public/server-to-server endpoints. The key lives in an environment variable and is supplied per request in a header. A custom authentication/permission validates it, so public endpoints are reachable without a user session while still being gated.

Both are registered so an endpoint can accept either. Default `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]`; relax per-view deliberately. Implementation in `django-rest-framework`.

### Response shape

Every endpoint answers with the same envelope (success and error alike) so the frontend parses one shape. Don't hand-build error dicts in views — *raise* a domain `APIException` and let the global handler format it. Renderer + handler in `django-rest-framework`.

### API documentation — always

Document every endpoint (request/response examples, error codes, auth requirement). Prefer `drf-spectacular` (OpenAPI). Undocumented endpoints are part of "not done".

---

## Request-context middleware — always

A `RequestContextMiddleware` resolves the authenticated user (via JWT) and attaches it to `request.current_user` on every request, so any layer can read the current user without re-authenticating. It never short-circuits or raises on missing/invalid credentials — authorization stays with DRF permissions. Skip resolution for `/admin/` paths. Register it last in `MIDDLEWARE`.

---

## Admin — always

Creating a model without registering it in the Django admin is incomplete work. Admin classes live in `admin/<entity>.py`, re-exported from `admin/__init__.py`, and inherit from a shared `BaseModelAdmin` (in `admin/abstracts/`) that centralises `readonly_fields` for `created_at`/`updated_at` and soft-delete handling. Configure at minimum `list_display`, `list_filter`, `search_fields`, `ordering`; add `autocomplete_fields` for FKs to large tables.

---

## Testing — always, TDD

Full patterns (fixtures, factories, the Red-Green-Refactor loop, what to assert per layer) live in **`django-testing`**. The non-negotiable baseline:

Tests live in `apps/<app>/tests/` as a package: `conftest.py` (shared fixtures like `api_client`), `factories.py` (factory-boy factories), and `test_<area>.py` files.

- **Stack:** `pytest` + `pytest-django` + `factory-boy` + `faker` + `pytest-cov`. Config in `[tool.pytest.ini_options]`.
- **TDD loop:** Red (write the failing test, confirm it fails for the right reason) → Green (minimum code to pass) → Refactor.
- File naming `test_*.py`; function naming `test_<behaviour>` as a readable sentence.
- AAA layout (Arrange / Act / Assert), one logical assertion focus per test.
- Use `reverse("namespace:url-name")` for URLs — never hardcode paths.
- Build objects with factories in Arrange; avoid manual `Model.objects.create()` in test bodies.
- Mark DB tests with `@pytest.mark.django_db`. Query soft-deleted/inactive rows via `Model.all_objects` (the default manager hides them).
- Cover: happy path, input validation (400 + correct error keys), edge/boundary cases, authz (401/403), and side effects (records created/modified, FK links, soft-delete).
- **Coverage target ≥ 80%** on the domain app; no change drops below it.

---

## Code style and tooling

- **Type hints** on every public signature (Python 3.13+ syntax).
- **Short, intent-revealing docstrings** (Google/NumPy style) on classes and non-trivial functions. Comments explain *why*, never restate *what*.
- **Functions stay small** (target 20–30 lines).
- **Descriptive names** — full words (`index`, `element`, `error`), not `idx`/`el`/`err`.
- **English only, no emojis.**
- `ruff` handles lint + format; `pre-commit` enforces it. Full setup in **`python-tooling`**.

---

## Project-specific configuration takes precedence

This skill is the project-independent baseline. Individual projects keep their own documentation — typically files like `ARCHITECTURE.md`, `WORKFLOW.md`, `COMMANDS.md`, `DESIGN.md` (often under `docs/`) — describing stack versions, exact commands, branching/commit process, deployment and other project-specific config. When a project documents something more specific than this skill, **the project's own docs win**. Before starting work in an unfamiliar project, look for those files and read the relevant ones.

When you start a non-trivial backend task, briefly state the plan (2–3 sentences plus bullet steps) before implementing, so the direction can be corrected early.
