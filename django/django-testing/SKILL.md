---
name: django-testing
description: The testing discipline for a Django + DRF API — pytest, pytest-django, factory-boy and coverage, the test-first (TDD) loop, fixtures and factories, and what to assert at each layer (models, serializers, endpoints). Use this skill whenever you write or run tests for a Django backend, set up the test suite, add factories or fixtures, debug a failing test, or decide what a feature's tests should cover. Trigger it whenever a task involves tests, pytest, factory-boy, coverage, TDD, conftest or fixtures, even if not named explicitly. It is the testing companion to django-conventions (the rules), django-orm-patterns (models), django-rest-framework (API) and django-cbv-patterns (views).
---

# Django Testing

How we test a Django REST API. The rule is simple and non-negotiable (it lives in **django-conventions**): **a feature is not done until its tests are green.** This skill is the *how* — the stack, the layout, the test-first loop, and what to actually assert.

The mindset: tests are the executable spec. You write the test that describes the behaviour first, watch it fail for the right reason, then write the code that makes it pass. Tests that are bolted on afterwards tend to assert what the code happens to do, not what it should do.

---

## Stack and layout

`pytest` + `pytest-django` + `factory-boy` + `faker` + `pytest-cov`. Configuration lives in `pyproject.toml` (`[tool.pytest.ini_options]`, see **python-tooling**), pointing `DJANGO_SETTINGS_MODULE` at a dedicated test settings module so tests never touch dev/prod config.

Tests live in a package per app:

```
apps/<app>/tests/
  __init__.py
  conftest.py        # shared fixtures (api_client, authenticated clients, ...)
  factories.py       # factory-boy factories, one per model
  test_models.py     # model invariants: soft-delete, UUID PK, constraints
  test_<resource>.py # one file per endpoint/area
```

One file per area keeps failures easy to locate. Name files `test_*.py` and functions `test_<behaviour>` as a readable sentence (`test_user_cannot_see_another_users_invoices`).

---

## The TDD loop

1. **Red** — write the failing test and run just it; confirm it fails for the *right* reason (an assertion failure, not an import error or typo):
   ```bash
   uv run pytest apps/api/tests/test_invoice.py::test_create_invoice -vv
   ```
2. **Green** — implement the minimum production code to pass.
3. **Refactor** — clean up while the test stays green.

Each test follows **AAA**: Arrange (build data with factories), Act (one call), Assert (one logical focus). Don't assert ten unrelated things in one test — a focused test names the exact behaviour that broke.

---

## Fixtures — conftest.py

Shared setup goes in `conftest.py` so tests stay terse. The workhorse is an API client, plus authenticated variants:

```python
import pytest
from rest_framework.test import APIClient

from apps.api.tests.factories import UserFactory


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def auth_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user)
    return client
```

`force_authenticate` bypasses the JWT flow so endpoint tests don't re-test login on every case. Test the auth flow itself separately, in its own file.

---

## Factories — factories.py

factory-boy builds valid objects so tests don't hand-write `Model.objects.create(...)` with every field. Use `SubFactory` for relationships and `Sequence`/`Faker` for unique/realistic values:

```python
import factory
from factory.django import DjangoModelFactory

from apps.api.models import Invoice, User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "password123")
        if create:
            self.save()


class InvoiceFactory(DjangoModelFactory):
    class Meta:
        model = Invoice

    user = factory.SubFactory(UserFactory)
    number = factory.Sequence(lambda n: f"INV-{n}")
    amount = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
```

Arrange with factories, not inline `create()` — it keeps the *relevant* data visible in each test and the noise out.

---

## What to assert, per layer

### Models (`test_models.py`)

The data-model contract from **django-orm-patterns**:

- **Soft-delete**: after `obj.soft_delete()`, the row is gone from `Model.objects` but present in `Model.all_objects`, with `deleted_at` set and `active=False`.
- **Default manager hides non-live rows**: an `active=False` row is invisible to `Model.objects`.
- **UUID PK**: `obj.pk` is a `UUID`.
- **Constraints**: the soft-delete-aware `UniqueConstraint` rejects a duplicate live row but allows reusing a value freed by a soft-deleted row.

```python
import pytest

from apps.api.tests.factories import InvoiceFactory


@pytest.mark.django_db
def test_soft_delete_hides_row_from_default_manager():
    invoice = InvoiceFactory()
    invoice.soft_delete()

    assert not type(invoice).objects.filter(pk=invoice.pk).exists()
    assert type(invoice).all_objects.filter(pk=invoice.pk).exists()
```

### Serializers

Where validation lives, so test it directly when the rule is non-trivial: invalid input raises `ValidationError` with the expected field key; computed/`SerializerMethodField` output is correct; read-only fields can't be written.

### Endpoints (`test_<resource>.py`)

The bulk of the suite. For every endpoint cover:

- **Happy path** — correct status (200/201) and the exact response shape. Remember the response envelope (`{"success": true, "data": ...}`); list endpoints carry the pagination envelope under `data`.
- **Validation** — 400 with the right error keys.
- **Authentication** — 401 when unauthenticated.
- **Authorisation / ownership** — 403 (or 404) when touching another user's row. This is the test that catches the most dangerous bug class.
- **Filtering / pagination** — filters narrow results; the pagination envelope is present.
- **Side effects** — the DB actually changed (row created, FK linked, soft-deleted), checked via the ORM.

```python
import pytest
from django.urls import reverse

from apps.api.tests.factories import InvoiceFactory, UserFactory


@pytest.mark.django_db
def test_user_only_sees_their_own_invoices(auth_client, user):
    InvoiceFactory(user=user)
    InvoiceFactory(user=UserFactory())  # someone else's

    response = auth_client.get(reverse("api:invoice-list"))

    assert response.status_code == 200
    assert response.data["data"]["count"] == 1


@pytest.mark.django_db
def test_cannot_retrieve_another_users_invoice(auth_client):
    other = InvoiceFactory(user=UserFactory())

    response = auth_client.get(reverse("api:invoice-detail", args=[other.pk]))

    assert response.status_code in (403, 404)
```

Always resolve URLs with `reverse("<namespace>:<name>")` — hardcoded paths break silently when routes change, and the indirection is what lets you trust the router wiring.

---

## Key conventions

- **`@pytest.mark.django_db`** on any test that hits the database. Prefer the marker over the legacy `TestCase` base.
- **Query non-live rows via `all_objects`** — the default `objects` manager hides soft-deleted/inactive records, so a test verifying a soft-delete must use `all_objects` to see the row still exists.
- **Mock at the boundary, not the internals.** Stub external HTTP/services (the thing you don't control); don't mock your own ORM or serializers — test the real thing against a real test database.
- **Assert query count where N+1 matters.** Wrap a list endpoint in `django_assert_num_queries` (pytest-django fixture) so a regression that reintroduces N+1 fails loudly:
  ```python
  def test_invoice_list_is_constant_queries(auth_client, user, django_assert_num_queries):
      InvoiceFactory.create_batch(5, user=user)
      with django_assert_num_queries(4):
          auth_client.get(reverse("api:invoice-list"))
  ```

---

## Coverage

Target **≥ 80%** on the domain app; no change drops below it. Inspect what's uncovered, not just the number:

```bash
uv run pytest --cov=apps --cov-report=term-missing
```

`term-missing` lists the exact uncovered lines so you can see whether the gap is a real untested path (fix it) or unreachable defensive code (acceptable). Chase meaningful coverage — an authorisation branch with no test is a hole regardless of the headline percentage.

---

## Common pitfalls

- **Forgetting `@pytest.mark.django_db`** — the test errors on first DB access instead of running.
- **Asserting against `objects` when verifying a soft-delete** — the row is hidden; use `all_objects`.
- **Hardcoded URLs** — use `reverse()`.
- **Over-mocking** — mocking your own code tests the mock, not the system; mock only true external boundaries.
- **Manual `create()` in test bodies** — use factories so the relevant data stays visible and the rest is noise-free.
- **Chasing a coverage number** while leaving authz branches untested — coverage is a floor, not the goal.
- **Testing the happy path only** — the validation, auth and ownership cases are where the bugs that reach production actually live.
