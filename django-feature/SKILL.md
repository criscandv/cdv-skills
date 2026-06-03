---
name: django-feature
description: Build a complete vertical slice for a new entity in an existing Django + DRF API — model, admin, serializer(s), view/viewset, URL wiring, factory, tests and migration — following the house conventions and a test-first (TDD) loop. Use this skill when the user asks to add a resource, entity, endpoint, model or CRUD to an existing Django backend ("add an Invoice model with an API", "create endpoints for products", "necesito un CRUD de clientes"). This is a slash-invoked action. For starting a whole new project use django-new-api; for bringing a non-conforming project up to standard use django-normalize.
disable-model-invocation: true
---

# /django-feature — a complete vertical slice, test-first

Add one entity end to end, so it lands as a coherent, tested, documented slice rather than a half-wired model. Everything here follows **django-conventions**; the exact code per layer lives in **django-orm-patterns** (model), **django-rest-framework** (serializer/permissions/docs), **django-cbv-patterns** (view) and **django-testing** (tests). Read those for depth — this skill is the order of operations and the wiring.

Communicate progress in Spanish. All code is in English.

## The loop is test-first

A feature is **not done** until its tests are green. Work Red → Green → Refactor: write the failing test that describes the behaviour, confirm it fails for the right reason, implement the minimum to pass, then clean up. Don't write the whole slice and bolt tests on at the end — the tests are the spec.

## 1. Capture the entity spec

Before touching code, pin down (ask the user where unclear):

- **Entity name** (singular, English): e.g. `Invoice`.
- **Fields** with types and constraints (required/optional, unique, choices, max_length, decimals).
- **Relationships**: FKs/M2M to other models.
- **Owner**: which user owns a row. Default is a `user` FK to the custom user model — every model carries it unless this is deliberate global/reference data (state it explicitly if so).
- **API surface**: full CRUD (`ModelViewSet`), read-only (`ReadOnlyModelViewSet`), or bespoke (`APIView`)? Any custom `@action`s beyond CRUD?
- **Access rule**: owner-only (the usual — `BaseOwnedViewSet`), or broader?
- **Filtering / search / ordering** fields the frontend needs.

Write this down (a short spec under `specs/` if the project uses them) so the tests can be written against it.

## 2. Locate the app and confirm the baseline

Identify the target app (`apps/<app>/`). Confirm it has the abstract bases this slice depends on — `BaseModel`, `BaseOwnedViewSet`, `BaseModelAdmin`, the custom user, the pagination/renderer/handler. If any are missing, the project isn't on the baseline yet: run **django-normalize** first.

## 3. Build the slice, file by file

One class per file, re-exported from the package `__init__.py`. Create in this order; after each new file, add its import + `__all__` entry to the package `__init__.py`.

### Model — `apps/<app>/models/<entity>.py`

Inherit `BaseModel`, carry the owner FK, push invariants into the database. Remember soft-delete-aware uniqueness (`UniqueConstraint` with `condition=Q(deleted_at__isnull=True)`). See **django-orm-patterns**.

```python
from django.db import models

from .abstracts import BaseModel


class Invoice(BaseModel):
    """An invoice owned by a user."""

    user = models.ForeignKey("api.User", on_delete=models.CASCADE, related_name="invoices")
    number = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default="draft")

    class Meta(BaseModel.Meta):
        verbose_name = "invoice"
        verbose_name_plural = "invoices"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "number"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_live_invoice_number_per_user",
            ),
        ]

    def __str__(self) -> str:
        return self.number
```

Re-export: add `from .invoice import Invoice` and `"Invoice"` to `models/__init__.py`.

### Admin — `apps/<app>/admin/<entity>.py`

Mandatory. Inherit `BaseModelAdmin`; register the model. `BaseModelAdmin` handles showing the UUID `id` read-only on both the changelist and the change form, so the subclass doesn't repeat that. **Every ForeignKey on the model goes in `raw_id_fields`** — never `autocomplete_fields` or the default dropdown (see **django-conventions** for the rationale).

```python
from django.contrib import admin

from apps.api.admin.abstracts import BaseModelAdmin
from apps.api.models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(BaseModelAdmin):
    list_display = ("number", "user", "amount", "status", "created_at")
    list_filter = ("status", "active")
    search_fields = ("number",)
    raw_id_fields = ("user",)  # every FK uses raw_id_fields — never autocomplete or default dropdown
```

Re-export from `admin/__init__.py`.

### Serializer(s) — `apps/<app>/serializers/<entity>.py`

Split read vs write when shapes diverge; set the owner server-side, never from the client. Validation in `validate_<field>` / `validate`. See **django-rest-framework**.

```python
from rest_framework import serializers

from apps.api.models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ("id", "number", "amount", "status", "created_at")
        read_only_fields = ("id", "created_at")
```

Re-export from `serializers/__init__.py`.

### View — `apps/<app>/views/<entity>.py`

Pick the class per the spec (see **django-cbv-patterns**). For an owner-scoped CRUD resource, extend `BaseOwnedViewSet`: it already provides permissions, pagination and owner-scoping, so declare only `queryset` and `serializer_class`. Custom `@action`s always declare `url_path` + `url_name`; raise domain exceptions on failure and return plain data on success (the renderer envelopes it).

```python
from apps.api.models import Invoice
from apps.api.serializers import InvoiceSerializer
from apps.api.views.abstracts import BaseOwnedViewSet


class InvoiceViewSet(BaseOwnedViewSet):
    queryset = Invoice.objects.select_related("user")
    serializer_class = InvoiceSerializer
    filterset_fields = ("status",)
    search_fields = ("number",)
    ordering_fields = ("created_at", "amount")
```

Re-export from `views/__init__.py`.

### URL wiring — `apps/<app>/urls.py`

Register the viewset on the router with an explicit `basename` (required when the viewset has no static `queryset`, and good practice always):

```python
router.register(r"invoices", InvoiceViewSet, basename="invoice")
```

For an `APIView`/generic, add an explicit `path(...)` with a `name`.

### Factory — `apps/<app>/tests/factories.py`

Add a factory-boy factory so tests build instances without manual `create()`:

```python
class InvoiceFactory(DjangoModelFactory):
    class Meta:
        model = Invoice

    user = factory.SubFactory(UserFactory)
    number = factory.Sequence(lambda n: f"INV-{n}")
    amount = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
```

### Tests — `apps/<app>/tests/test_<entity>.py`

Written first in the loop. Cover: happy path (201/200 + exact response shape, remembering the `{success, data}` envelope), validation (400 + correct error keys), authn/authz (401 unauthenticated, 403 touching another user's row), filtering/pagination, and side effects including soft-delete (query via `all_objects`). Use `reverse("api:invoice-list")` — never hardcode URLs. See **django-testing**.

## 4. Migration

```bash
uv run python manage.py makemigrations <app>
# inspect apps/<app>/migrations/000X_*.py — verify the FK on_delete, constraints, indexes
uv run python manage.py migrate
```

Generate only via `makemigrations`; inspect before applying. Pause and confirm with the user before anything destructive on an existing table.

## 5. Verify before handing off

```bash
uv run python manage.py check
uv run pytest apps/<app>/tests/test_<entity>.py -vv
uv run pytest --cov=apps --cov-report=term-missing   # coverage stays >= 80%
uv run ruff check . && uv run ruff format --check .
```

## Definition of done

The slice is complete only when: tests are green, the model is registered in the admin, the endpoint is reachable through the router, the response uses the standard envelope, the OpenAPI schema picks it up (annotate non-obvious endpoints with `extend_schema`), and coverage hasn't dropped. Missing any of these means the feature is unfinished.
