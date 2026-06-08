---
name: django-orm-patterns
description: Deep reference for the Django ORM and models layer in a DRF API. Use this skill whenever you define or query Django models — abstract base models, custom managers and querysets, soft-delete, UUID primary keys, the mandatory owner FK, select_related/prefetch_related, Q/F expressions, aggregation, constraints and indexes, transactions, and safe migrations. Trigger it whenever you write a model, a manager, a migration, or a non-trivial ORM query, even if the user does not mention the ORM by name. It is the models-layer companion to django-conventions (the rules), django-rest-framework (serialization/API) and django-cbv-patterns (views).
---

# Django ORM Patterns

The models layer for a Django REST API. The mandatory rules (UUID PK, soft-delete, owner FK, abstracts/ folders, one-class-per-file) live in **django-conventions** — this skill is the *how*: the concrete patterns for building those models and querying them efficiently.

Two principles run through everything here:

- **Inherit, don't repeat.** Timestamps, soft-delete and the UUID PK come from abstract bases. A concrete model never re-declares them.
- **Let the database do the work.** Filtering, aggregation and conditional logic belong in querysets and database functions, not in Python loops over rows.

---

## The abstract base stack

Every project starts with three files under `models/abstracts/`. Build them first; every domain model depends on them.

### `uuid.py` — UUID primary key

```python
import uuid

from django.db import models


class UUIDPrimaryKeyModel(models.Model):
    """Abstract base that replaces the default BigAutoField id with a UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
```

Its single job is swapping the PK type. Keep it free of any other field so it stays composable.

### `managers.py` — the soft-delete manager

```python
from django.db import models


class ActiveManager(models.Manager):
    """
    Default manager that restricts querysets to live records only.

    A record is live when both hold: deleted_at IS NULL (not soft-deleted)
    and active is True (not soft-disabled).
    """

    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(deleted_at__isnull=True, active=True)
```

`get_queryset()` is the chokepoint: filtering here means **every** lookup through this manager is soft-delete-aware for free. You never have to remember to add `.filter(deleted_at__isnull=True)` at call sites — and forgetting it is exactly how soft-deleted data leaks back into an API response.

### `base.py` — the standard base model

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

    objects = ActiveManager()        # default manager: live records only
    all_objects = models.Manager()   # unfiltered: admin, internal jobs, tests

    class Meta(UUIDPrimaryKeyModel.Meta):
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self) -> None:
        """Retire the record without removing the row."""
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.active = False
        self.save(update_fields=["deleted_at", "active", "updated_at"])
```

The two managers are deliberate. `objects` is what application code and the API use, so non-live rows are invisible by default. `all_objects` is the escape hatch — the admin, data-repair scripts and tests need to see everything, including retired rows. Declaring `objects` first also makes it the **default manager** Django uses for things like related-object lookups.

`deleted_at` and `active` are both indexed because they appear in the `WHERE` clause of essentially every query through `ActiveManager`.

Re-export everything through `abstracts/__init__.py` and then `models/__init__.py` so callers write `from apps.api.models import BaseModel`.

---

## Concrete models

A standard domain model inherits `BaseModel`, extends its `Meta`, and carries the owner FK:

```python
from django.db import models

from .abstracts import BaseModel


class Invoice(BaseModel):
    """A single invoice owned by a user."""

    user = models.ForeignKey(
        "api.User",
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    number = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    issued_at = models.DateField()

    class Meta(BaseModel.Meta):
        verbose_name = "invoice"
        verbose_name_plural = "invoices"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "number"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_live_invoice_number_per_user",
            ),
            models.CheckConstraint(
                check=models.Q(amount__gte=0),
                name="invoice_amount_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return self.number
```

Notes that matter:

- The owner FK is the default for every model. Omit it only for deliberate global/reference data.
- **Uniqueness under soft-delete is subtle.** A plain `unique_together` would block a user from ever reusing the number of a soft-deleted invoice. Scope the `UniqueConstraint` with `condition=Q(deleted_at__isnull=True)` so uniqueness applies only to live rows.
- Push invariants into the database with `CheckConstraint` / `UniqueConstraint` — they hold even against raw SQL and concurrent writes, unlike Python-side checks.

### The custom user model

The user model is special: it extends Django auth *and* the soft-delete contract.

```python
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from .abstracts import BaseModel


class UserManager(BaseUserManager):
    """Keeps create_user/create_superuser and enforces the soft-delete filter."""

    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(deleted_at__isnull=True, active=True)

    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """Custom user using email as the unique identifier."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    class Meta(BaseModel.Meta):
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email
```

`UserManager.get_queryset()` **must** replicate the soft-delete filter. Django's `authenticate()` calls the default manager — without this override a soft-deleted user could still log in. Set `AUTH_USER_MODEL = "api.User"` in settings before the first migration.

(Note `BaseModel.active` and auth's `is_active` are different switches: `active` is the soft-disable flag in the live-record contract; `is_active` is Django auth's login gate. Keep both in sync when retiring a user.)

---

## Custom querysets and managers

When query logic repeats, name it once on a `QuerySet` and expose it through a manager. `Manager.from_queryset` keeps both chainable:

```python
from django.db import models
from django.utils import timezone
from datetime import timedelta


class InvoiceQuerySet(models.QuerySet):
    def paid(self) -> "InvoiceQuerySet":
        return self.filter(status="paid")

    def for_user(self, user) -> "InvoiceQuerySet":
        return self.filter(user=user)

    def recent(self, days: int = 30) -> "InvoiceQuerySet":
        return self.filter(created_at__gte=timezone.now() - timedelta(days=days))


class InvoiceManager(models.Manager.from_queryset(InvoiceQuerySet)):
    def get_queryset(self) -> InvoiceQuerySet:
        return super().get_queryset().filter(deleted_at__isnull=True, active=True)
```

If you override `objects` on a `BaseModel` subclass like this, re-apply the soft-delete filter in `get_queryset()` — you are replacing `ActiveManager`, not extending it. Methods then chain naturally: `Invoice.objects.for_user(user).paid().recent()`.

---

## Querying efficiently

### Kill N+1 with select_related / prefetch_related

The single most common performance bug is a serializer touching a related object inside a loop, firing one query per row.

```python
# ForeignKey / OneToOne -> select_related (SQL JOIN, one query)
Invoice.objects.select_related("user")

# Reverse FK / ManyToMany -> prefetch_related (second query, joined in Python)
User.objects.prefetch_related("invoices")

# Shape the prefetched queryset
from django.db.models import Prefetch

User.objects.prefetch_related(
    Prefetch("invoices", queryset=Invoice.objects.paid(), to_attr="paid_invoices")
)
```

Set these in the view's `get_queryset()`, not at call sites, so the whole endpoint benefits. See **django-cbv-patterns**.

### Q for OR/NOT, F for field references

```python
from django.db.models import Q, F

Invoice.objects.filter(Q(status="paid") | Q(amount__gte=1000))
Invoice.objects.filter(~Q(status="draft"))

# F references a column: atomic update, no read-modify-write race
Invoice.objects.filter(pk=pk).update(views=F("views") + 1)
```

After an `F()` update on an instance, call `refresh_from_db()` before reading the field — the in-memory value is still the `F` expression, not the computed result.

### Aggregation and annotation

```python
from django.db.models import Count, Sum, Avg, Q

# Whole-queryset rollup
Invoice.objects.aggregate(total=Sum("amount"), paid=Count("id", filter=Q(status="paid")))

# Per-row computed field
User.objects.annotate(
    invoice_count=Count("invoices"),
    total_billed=Sum("invoices__amount"),
).filter(invoice_count__gt=0)
```

Prefer `Count("id", filter=Q(...))` (conditional aggregation in one pass) over multiple separate queries.

### Lean reads

```python
Invoice.objects.only("id", "number", "amount")          # load just these columns
Invoice.objects.values("id", "number")                  # dicts, not model instances
Invoice.objects.values_list("id", flat=True)            # flat list of one column
for invoice in Invoice.objects.iterator(chunk_size=1000):  # large sets, low memory
    ...
```

---

## Transactions

Wrap operations that must succeed or fail together:

```python
from django.db import transaction


@transaction.atomic
def issue_invoice(*, user, number: str, amount) -> Invoice:
    invoice = Invoice.objects.create(user=user, number=number, amount=amount)
    user.invoice_count = F("invoice_count") + 1
    user.save(update_fields=["invoice_count"])
    return invoice
```

- Use `select_for_update()` inside `atomic()` to lock rows against concurrent modification.
- For side effects that must run only after the data is durably committed (emails, webhooks, cache busting), use `transaction.on_commit(...)` so they don't fire on a rolled-back transaction.

**Destructive and multi-step writes are always transactional.** A create/update/delete that touches several rows must be all-or-nothing; a half-applied write leaves the database in a state no code expects. Wrap the unit in `atomic()` and use **savepoints (checkpoints)** to roll back a risky sub-step without aborting everything:

```python
from django.db import transaction


@transaction.atomic
def replace_order_items(*, order, new_items: list[dict]) -> None:
    """Swap an order's items, rolling back only the rebuild if it fails."""
    order.items.all().delete()  # soft-delete in our models

    checkpoint = transaction.savepoint()
    try:
        OrderItem.objects.bulk_create(
            [OrderItem(order=order, **item) for item in new_items]
        )
    except IntegrityError:
        transaction.savepoint_rollback(checkpoint)  # undo the rebuild, keep the rest
        raise
    else:
        transaction.savepoint_commit(checkpoint)
```

Nested `atomic()` blocks are themselves implemented as savepoints, so the common case — `with transaction.atomic():` inside an outer `atomic()` — already gives you partial rollback. Reach for explicit `savepoint()` only when you need to catch and recover from a sub-step rather than abort the whole transaction.

---

## Bulk operations

For many rows, avoid a query per object:

```python
Invoice.objects.bulk_create(objects, batch_size=500)
Invoice.objects.bulk_update(objects, ["status"], batch_size=500)
```

`bulk_create` does not call `save()` or send `post_save` signals — account for that if logic depends on them.

---

## Migrations — safety first

- Generate migrations **only** with `makemigrations`; never hand-author a schema migration. The one acceptable manual edit is adding a `RunPython`/`RunSQL` data backfill to an autogenerated file.
- Always `makemigrations --check --dry-run` before, and read the generated file before `migrate`.
- **Pause and confirm with the user** before destructive operations: dropping a column/table, changing a column type, large backfills, or adding an index on a large table. Offer a safer multi-step path (add nullable → backfill via `RunPython` → enforce constraint) when relevant.

---

## Debugging queries

When something is slow or fires too many queries:

```python
from django.db import connection, reset_queries

reset_queries()
list(User.objects.prefetch_related("invoices"))
print(len(connection.queries))  # how many SQL statements actually ran

print(Invoice.objects.filter(status="paid").explain(analyze=True))  # query plan
```

In tests, assert the count so a regression that reintroduces N+1 fails loudly:

```python
with self.assertNumQueries(2):
    list(serializer.data)
```

---

## Common pitfalls

- **N+1 in serializers** — the most frequent one. Optimise in the view's `get_queryset()`.
- **Forgetting the soft-delete filter on a custom manager** — overriding `objects` without re-applying `deleted_at__isnull=True, active=True` re-exposes retired rows.
- **`unique_together` ignoring soft-delete** — blocks reuse of a soft-deleted value; scope the constraint with `condition=Q(deleted_at__isnull=True)`.
- **`save()` in a loop** — use `bulk_create` / `bulk_update`.
- **Reading an `F()` field without `refresh_from_db()`** — you get the expression, not the value.
- **Unbounded `.all()`** in a response — always paginate (see django-rest-framework).
