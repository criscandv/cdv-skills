---
name: django-cbv-patterns
description: Deep reference for the view layer of a Django REST Framework API — class-based views only. Use this skill whenever you create or edit an endpoint: choosing between ViewSet, APIView and generics, writing base view classes and mixins, overriding get_queryset/get_serializer_class/perform_create, adding custom @action routes, wiring routers and URLs, and applying permissions/filtering/pagination at the view. Trigger it whenever a task involves an endpoint, a route, a viewset or an APIView, even if not named explicitly. It is the view-layer companion to django-conventions (the rules), django-orm-patterns (models) and django-rest-framework (serializers/auth/pagination).
---

# Django Class-Based Views (DRF)

The view layer for a REST API. **Function-based views are not used** here beyond the truly trivial — class-based views give us inheritance, mixins and shared base classes, which is how we avoid repeating querysets, permissions and pagination across endpoints.

The rules (custom pagination always, `@action` always has `url_path`, explicit `permission_classes`/`serializer_class`/`queryset`) live in **django-conventions**. Serializers, permissions, pagination and the exception handler live in **django-rest-framework**. This skill is about the views themselves: which base to pick and how to compose them.

---

## Choosing the right view class

This is the first decision on every endpoint. Pick by how well the resource fits standard CRUD.

**`ModelViewSet`** — the default for a resource with standard CRUD over a queryset. One class gives list/retrieve/create/update/destroy, and a router generates the URLs. Reach for it first.

**`ReadOnlyModelViewSet`** — same, but list + retrieve only. For resources the API exposes but never mutates.

**`ViewSet`** (plain) — when you want router grouping and custom `@action`s but the default CRUD methods don't map to a single queryset (e.g. a resource assembled from several sources).

**Generic `APIView` subclasses** (`CreateAPIView`, `RetrieveAPIView`, `ListAPIView`, …) — for a single, focused endpoint that isn't part of a CRUD collection: registration, "me" profile, a one-off report.

**`APIView`** (plain) — for endpoints that aren't resources at all: auth/token flows, actions, aggregations, anything with a bespoke request/response shape and custom logic per HTTP method.

Rule of thumb: **collection that behaves like CRUD → ViewSet; single bespoke endpoint → APIView/generic.** When in doubt, start with the most specific class that fits and drop to a lower-level one only when the abstraction fights you.

---

## A standard ModelViewSet

```python
from rest_framework import viewsets
from rest_framework.request import Request

from apps.api.models import Invoice
from apps.api.serializers import InvoiceReadSerializer, InvoiceWriteSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    """CRUD for the authenticated user's invoices."""

    serializer_class = InvoiceReadSerializer
    filterset_fields = ("status",)
    search_fields = ("number",)
    ordering_fields = ("created_at", "amount")

    def get_queryset(self):
        """Scope every action to the caller's own rows, prefetched to avoid N+1."""
        return (
            Invoice.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("items")
        )

    def get_serializer_class(self):
        """Plain payload on write, nested representation on read."""
        if self.action in ("create", "update", "partial_update"):
            return InvoiceWriteSerializer
        return InvoiceReadSerializer

    def perform_create(self, serializer) -> None:
        """Set the owner from the authenticated user — never trust it from the client."""
        serializer.save(user=self.request.user)
```

Why each override matters:

- **`get_queryset()` scopes data per user.** This is the list-level half of ownership enforcement (object permissions are the detail-level half — see django-rest-framework). Optimise relations here so the whole endpoint benefits, not at call sites.
- **`get_serializer_class()`** lets one viewset serve different shapes for read vs write without an overloaded serializer.
- **`perform_create()` sets the owner server-side.** Exposing the owner FK as writable lets a caller create rows for someone else.

`permission_classes` and `pagination_class` are declared explicitly per the rules; if a base viewset already sets them (below), inherit instead of repeating.

---

## Custom actions — always with url_path

A `@action` adds a route to a viewset beyond standard CRUD. **Always declare `url_path` (and `url_name`)** — relying on the method name couples the public URL to your Python identifier, so a rename silently breaks the route and any reverse lookups.

```python
from rest_framework.decorators import action
from rest_framework.response import Response


class InvoiceViewSet(viewsets.ModelViewSet):
    ...

    @action(detail=True, methods=["post"], url_path="mark-paid", url_name="mark-paid")
    def mark_paid(self, request: Request, pk: str | None = None) -> Response:
        """POST /invoices/{id}/mark-paid/"""
        invoice = self.get_object()  # respects get_queryset scoping + object permissions
        if invoice.status == "paid":
            raise ResourceConflict("This invoice is already paid.")  # domain exception

        invoice.status = "paid"
        invoice.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(invoice).data)  # renderer wraps the envelope

    @action(detail=False, methods=["get"], url_path="summary", url_name="summary")
    def summary(self, request: Request) -> Response:
        """GET /invoices/summary/ — aggregate over the caller's invoices."""
        from django.db.models import Sum

        totals = self.get_queryset().aggregate(total=Sum("amount"))
        return Response(totals)
```

`detail=True` builds `{prefix}/{pk}/{url_path}/`; `detail=False` builds `{prefix}/{url_path}/`. Use `self.get_object()` inside detail actions so queryset scoping and object permissions still apply.

---

## Errors and responses in views

Views don't build error dicts and don't wrap success bodies by hand — that is what drifts into incoherence across an API. The contract:

- **On failure, `raise` a domain exception** (an `APIException` subclass like `ResourceConflict`). The global exception handler turns it into the standard error envelope. No `try/except` around the happy path.
- **On success, return the plain data** (`Response(serializer.data)`); the standard renderer wraps it in the success envelope. Return an already-enveloped `Response({"success": True, "message": "...", "data": ...})` only when you want to attach a message.

The exception classes, the handler and the renderer all live in **django-rest-framework**.

## Base view classes and mixins

When several viewsets share the same permissions, pagination or queryset shape, lift it into a base in `views/abstracts/` rather than copy-pasting. This is the main reason we use CBVs at all.

```python
# views/abstracts/base.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.pagination import StandardPagination


class BaseOwnedViewSet(viewsets.ModelViewSet):
    """Base for resources owned by the requesting user.

    Centralises permissions, pagination and owner-scoping so concrete
    viewsets only declare their model-specific bits.
    """

    permission_classes = (IsAuthenticated,)
    pagination_class = StandardPagination
    owner_field = "user"

    def get_queryset(self):
        return self.queryset.filter(**{self.owner_field: self.request.user})

    def perform_create(self, serializer) -> None:
        serializer.save(**{self.owner_field: self.request.user})
```

```python
# views/invoice.py
class InvoiceViewSet(BaseOwnedViewSet):
    queryset = Invoice.objects.select_related("user").prefetch_related("items")
    serializer_class = InvoiceReadSerializer
```

A concrete viewset now declares only its `queryset` and `serializer_class`; ownership, permissions and pagination come from the base. When a concrete view needs more relations prefetched, set its own `queryset` (as above) — the base reads `self.queryset`.

For cross-cutting behaviour that isn't a full base class, use small mixins (e.g. a mixin that injects audit context, or one that adds a soft-delete `destroy`):

```python
class SoftDeleteDestroyMixin:
    """Override destroy to soft-delete instead of removing the row."""

    def perform_destroy(self, instance) -> None:
        instance.soft_delete()
```

Mixin ordering follows Python MRO: put mixins **before** the base view so their overrides take effect (`class InvoiceViewSet(SoftDeleteDestroyMixin, BaseOwnedViewSet)`).

---

## APIView for bespoke endpoints

When the endpoint isn't a CRUD resource, an `APIView` (or a generic) is clearer than bending a viewset:

```python
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.api.models import User
from apps.api.serializers import MeSerializer


class MeView(generics.RetrieveAPIView):
    """GET /auth/me/ — the authenticated user's own profile."""

    serializer_class = MeSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self) -> User:
        return self.request.user
```

```python
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


class RegistrationView(APIView):
    """POST /auth/register/ — create an account."""

    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"id": user.pk, "email": user.email}, status=201)
```

Generics (`RetrieveAPIView`, `CreateAPIView`, …) handle the boilerplate when the flow is standard; drop to plain `APIView` only when you need full control over each method.

---

## Routers and URLs

Register viewsets on a router; wire plain/generic views as explicit paths. Use a namespace so `reverse()` is unambiguous (tests rely on it):

```python
# apps/api/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.api.views import InvoiceViewSet, MeView, RegistrationView

app_name = "api"

router = DefaultRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")

urlpatterns = [
    path("auth/register/", RegistrationView.as_view(), name="register"),
    path("auth/me/", MeView.as_view(), name="me"),
    *router.urls,
]
```

`basename` drives the route names the router generates (`invoice-list`, `invoice-detail`, and for actions `invoice-mark-paid`). Always pass it explicitly when the viewset has no static `queryset` attribute, since the router can't infer it.

---

## Performance at the view layer

The view is where you control query count, because it owns the queryset that the serializer walks.

- Set `select_related` / `prefetch_related` in `get_queryset()`, shaped to what the serializer actually reads.
- For list vs detail with different needs, branch on `self.action` and `only()` the columns the list serializer uses.
- A `SerializerMethodField` or nested serializer that hits an unprefetched relation is an N+1 — the fix lives here, in the queryset, not in the serializer.

---

## Common pitfalls

- **`@action` without `url_path`** — couples the public URL to the method name; a rename breaks the route.
- **Filtering by user in the serializer or in Python** — scope in `get_queryset()` so list and detail are both protected.
- **Trusting the owner FK from the request** — set it in `perform_create`.
- **Copy-pasted permissions/pagination across viewsets** — lift them into a base in `views/abstracts/`.
- **Wrong mixin order** — mixins must precede the base view in the class definition or their overrides are shadowed.
- **N+1 from an unprefetched relation** — fix in `get_queryset()`, not by caching in the serializer.
- **Missing `basename` on a router register** — required when the viewset has no static `queryset`.
