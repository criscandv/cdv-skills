---
name: django-rest-framework
description: Deep reference for the serialization and API-infrastructure layer of a Django REST Framework project. Use this skill whenever you build or edit serializers, validation, JWT authentication, permissions, filtering, custom pagination, the global exception handler, throttling, or OpenAPI documentation. Trigger it whenever a task involves shaping request/response JSON, validating input, controlling who can call an endpoint, paginating a list, or documenting an API — even if DRF is not named explicitly. It is the API-layer companion to django-conventions (the rules), django-orm-patterns (models) and django-cbv-patterns (views/viewsets).
---

# Django REST Framework Patterns

The serialization and cross-cutting API layer. The mandatory rules (custom pagination always, global exception handler always, API docs always, JWT auth, type hints) live in **django-conventions**. The **view** layer — `ViewSet` vs `APIView`, base view classes, `@action` — lives in **django-cbv-patterns**. This skill covers everything between the model and the view: serializers, validation, auth, permissions, filtering, pagination, error shaping and documentation.

Guiding idea: **the serializer is the boundary.** It is the one place that translates between untrusted JSON and trusted model instances. Validation, field shaping and write logic belong here, not scattered across views.

---

## Serializers

One serializer per file under `serializers/`, shared mixins/bases under `serializers/abstracts/`, re-exported through the package `__init__.py`.

### Base serializer

When several serializers share read-only audit fields, define a base in `serializers/abstracts/` instead of repeating them:

```python
from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """Shared base: exposes the audit fields as read-only everywhere."""

    class Meta:
        abstract = True
        read_only_fields = ("id", "created_at", "updated_at")
```

DRF's `ModelSerializer` does not support `abstract = True` natively, so in practice the base lists the common fields and subclasses extend `Meta.fields`. The point is one definition of "these fields are never client-writable".

### A concrete serializer

```python
from rest_framework import serializers

from apps.api.models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ("id", "number", "amount", "issued_at", "status", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_number(self, value: str) -> str:
        if len(value) < 3:
            raise serializers.ValidationError("Invoice number is too short.")
        return value

    def validate(self, data: dict) -> dict:
        if data.get("status") == "paid" and not data.get("amount"):
            raise serializers.ValidationError("A paid invoice must have an amount.")
        return data
```

- `validate_<field>` for single-field rules, `validate` for cross-field rules. Raising `serializers.ValidationError` produces a clean 400 the frontend can parse.
- **Owner is set server-side, never trusted from the client.** Don't expose the owner FK as writable; assign it in the view's `perform_create` from the authenticated user. Exposing it lets a caller create rows owned by someone else.

### Read vs write serializers

When the input and output shapes diverge — nested objects on read, plain IDs on write — use two serializers and pick per action (the view's `get_serializer_class`, see django-cbv-patterns):

```python
class InvoiceReadSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = ("id", "number", "amount", "user", "created_at")


class InvoiceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ("number", "amount", "issued_at", "status")
```

This avoids the trap of a single serializer with half its fields `read_only` and the relationship logic guessing which mode it's in.

### Nested writes

Nested writable serializers need an explicit `create`/`update` — DRF won't persist nested data for you. Wrap multi-object writes in a transaction:

```python
from django.db import transaction


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "items")

    @transaction.atomic
    def create(self, validated_data: dict) -> Order:
        items = validated_data.pop("items", [])
        order = Order.objects.create(**validated_data)
        OrderItem.objects.bulk_create(
            [OrderItem(order=order, **item) for item in items]
        )
        return order
```

### SerializerMethodField with context

`SerializerMethodField` is for computed, read-only output. It can read the request from `self.context`:

```python
class InvoiceSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()

    def get_is_owner(self, obj: Invoice) -> bool:
        request = self.context.get("request")
        return bool(request and obj.user_id == request.user.id)
```

Beware N+1: if a method field touches a relation, make sure the view's queryset prefetches it.

---

## Authentication — JWT

Use `djangorestframework-simplejwt` with email-based login. Typical settings:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

SIMPLE_JWT = {
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
```

A custom token serializer lets you authenticate by email and reject accounts that shouldn't use the API (e.g. admin-only superusers) with a generic 401 — generic so it doesn't leak which accounts exist.

The default permission is `IsAuthenticated`; open specific endpoints with `AllowAny` deliberately (registration, login, public reads).

### Dual auth — API key for public endpoints

Public and server-to-server endpoints authenticate with an API key instead of a user session. The key lives in an environment variable and is sent in a request header; a custom authentication class validates it. Registering it alongside JWT lets an endpoint accept either path.

```python
# authentication/api_key.py
import hmac

from django.conf import settings
from rest_framework import authentication, exceptions


class APIKeyUser:
    """Lightweight non-persisted principal representing a valid API-key caller."""

    is_authenticated = True


class APIKeyAuthentication(authentication.BaseAuthentication):
    """Authenticate a request by a shared API key carried in the X-API-Key header.

    The expected key is read from settings (sourced from an environment variable).
    Returns a non-user principal so IsAuthenticated passes without a DB user.
    """

    keyword = "X-API-Key"

    def authenticate(self, request):
        provided = request.headers.get(self.keyword)
        if not provided:
            return None  # no key -> let other authenticators (JWT) try

        expected = settings.API_KEY
        if not expected or not hmac.compare_digest(provided, expected):
            raise exceptions.AuthenticationFailed("Invalid API key.")

        return (APIKeyUser(), None)
```

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "apps.api.authentication.APIKeyAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}
```

Key points:

- **Return `None` when the header is absent**, not an error — that lets DRF fall through to the next authenticator (JWT) so the same view can serve both authenticated users and API-key callers.
- **Compare with `hmac.compare_digest`**, never `==` — constant-time comparison avoids leaking the key through timing.
- The key comes from an env var (`API_KEY = config("API_KEY", default="")`); never hardcode it. Gate the public endpoint with a permission that accepts the API-key principal.
- **Register the class as part of the baseline, even if the project has no public endpoints yet.** Leaving `API_KEY=""` in env effectively disables the path (no header value can match an empty expected key), but keeping the authenticator in `DEFAULT_AUTHENTICATION_CLASSES` means a future public endpoint needs zero settings changes — just set the env var. Removing the class on the grounds that "we don't use it now" creates a hidden migration cost the day you do need it.
- For multiple rotating keys or per-client keys, prefer the managed `djangorestframework-api-key` package (hashed keys in the DB) over a single shared secret.

---

## Permissions

Object-level permissions enforce ownership. With the mandatory owner FK, the common rule is "you may only touch your own rows":

```python
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Allow access only to the user that owns the object."""

    def has_object_permission(self, request, view, obj) -> bool:
        return obj.user_id == request.user.id
```

Two layers matter: `has_permission` (can this user hit this endpoint at all?) and `has_object_permission` (can they touch *this* row?). Pair object permissions with a queryset already filtered to the user — permissions guard the single-object path, the queryset guards the list path. Relying on only one of them leaks data.

---

## Filtering, search, ordering

Use `django-filter` plus DRF's search/ordering backends:

```python
from django_filters import rest_framework as filters


class InvoiceFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr="gte")
    issued_after = filters.DateFilter(field_name="issued_at", lookup_expr="gte")

    class Meta:
        model = Invoice
        fields = ["status", "min_amount", "issued_after"]
```

Wire `filterset_class`, `search_fields` and `ordering_fields` on the view (see django-cbv-patterns). Keep filtering declarative here rather than parsing query params by hand in the view.

---

## Custom pagination — always

Never ship the bare DRF default. A custom paginator gives a stable, documented envelope the frontend can depend on, plus a client-tunable page size with an upper bound. Put it under `pagination/`:

```python
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data) -> Response:
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
```

Set it as the project default and override per-view only when a specific endpoint needs different behaviour:

```python
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "apps.api.pagination.StandardPagination",
    "PAGE_SIZE": 20,
}
```

`max_page_size` is not optional — without it a client can request `page_size=1000000` and exhaust memory.

---

## Errors — raise domain exceptions, handle them globally

The model for failures is: **a view (or service) `raise`s a domain exception, and a single global handler turns it into the standard error envelope.** Views never build ad-hoc error dicts and never need a `try/except` around the happy path — DRF catches the raised exception and routes it through the handler. Reserve `try/except` for *expected* failures of code that can genuinely blow up (external API calls, file I/O, parsing); catch the specific exception and re-raise it as a domain exception so the client still gets the standard shape.

### Domain exceptions

Subclass DRF's `APIException` (not bare `Exception`) so the framework's machinery handles them automatically and they carry a status code and a stable, machine-readable `default_code`:

```python
# exceptions/domain.py
from rest_framework import status
from rest_framework.exceptions import APIException


class ResourceConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The resource is in a state that conflicts with this action."
    default_code = "resource_conflict"


class IntegrationUnavailable(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "An upstream service is unavailable."
    default_code = "integration_unavailable"
```

Raise them with a specific message where the failure is detected:

```python
def mark_paid(self, request, pk=None):
    invoice = self.get_object()
    if invoice.status == "paid":
        raise ResourceConflict("This invoice is already paid.")
    ...
```

```python
# wrapping an external call that can fail
import requests


def fetch_quote(reference: str) -> dict:
    try:
        response = requests.get(f"{settings.QUOTES_URL}/{reference}", timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise IntegrationUnavailable("Could not reach the quotes provider.") from exc
    return response.json()
```

Subclassing `APIException` is the upgrade over the older "subclass `Exception` and call a `handle_exception()` helper inside every view" pattern: it removes the repetitive `try/except` boilerplate and lets the global handler do the formatting in one place.

### The global handler — one envelope for every error

```python
# exceptions/handler.py
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Normalise every handled error to the standard envelope.

    Shape: {"success": false, "message": <human-readable>, "errors": <details|null>}
    Returns None for unhandled exceptions so genuine bugs surface as a logged 500
    rather than being dressed up as a tidy error.
    """
    response = exception_handler(exc, context)
    if response is None:
        return response

    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])
        errors = None
    elif isinstance(detail, (list, str)):
        message = "Request could not be processed."
        errors = detail
    else:
        message = "Request could not be processed."
        errors = detail  # field-level validation errors keyed by field

    response.data = {"success": False, "message": message, "errors": errors}
    return response
```

```python
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "apps.api.exceptions.api_exception_handler",
}
```

This envelope is the error half of the consistent response shape below — same `success` flag, mirrored structure.

---

## Consistent response envelope — always

Every successful response shares one shape too, so the frontend reads `success`, then `data` (or `errors`). Rather than rely on each developer hand-building `Response({...})` consistently — the way that drifts into incoherence — enforce it with a **custom renderer** that wraps whatever a view returns. Developers just `return Response(data)`; the renderer does the envelope.

```python
# renderers/standard.py
from rest_framework.renderers import JSONRenderer


class StandardJSONRenderer(JSONRenderer):
    """Wrap every successful payload in {"success": true, "message": ..., "data": ...}.

    Error responses (status >= 400) are already shaped by the exception handler,
    so they pass through untouched. Views that want a message can return an
    already-enveloped dict and it is passed through as-is.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context["response"] if renderer_context else None
        status_code = getattr(response, "status_code", 200)

        if status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)

        if isinstance(data, dict) and "success" in data:
            payload = data  # already enveloped (e.g. handler output or explicit message)
        else:
            payload = {"success": True, "message": None, "data": data}

        return super().render(payload, accepted_media_type, renderer_context)
```

```python
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["apps.api.renderers.StandardJSONRenderer"],
}
```

Resulting shapes the frontend can always rely on:

```jsonc
// success — list (the paginator's envelope lands under data)
{ "success": true, "message": null, "data": { "count": 42, "results": [ ... ] } }

// success — detail
{ "success": true, "message": null, "data": { "id": "…", "number": "INV-1" } }

// success with a message — view returns Response({"success": True, "message": "Sent", "data": {...}})
{ "success": true, "message": "Payroll sent", "data": { ... } }

// error — produced by the exception handler
{ "success": false, "message": "This invoice is already paid.", "errors": null }
```

Why a renderer rather than a helper function: a helper still depends on every developer remembering to call it. A renderer is applied globally and is impossible to forget, which is exactly the coherence guarantee the API needs. If a specific endpoint must return a non-enveloped body (a file download, a third-party webhook contract), give it its own renderer explicitly.

---

## Throttling

Protect expensive or abusable endpoints with scoped rate limits:

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"user": "1000/day", "anon": "100/day", "login": "10/min"},
}
```

A tight `login` scope on the auth endpoint is the cheapest defence against credential stuffing.

---

## API documentation — always

Generate OpenAPI with `drf-spectacular`. Annotate endpoints so the schema is accurate and useful:

```python
from drf_spectacular.utils import extend_schema


class InvoiceViewSet(viewsets.ModelViewSet):
    @extend_schema(summary="List the caller's invoices", responses=InvoiceReadSerializer)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

```python
REST_FRAMEWORK = {"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"}

SPECTACULAR_SETTINGS = {
    "TITLE": "API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
```

Expose `SpectacularAPIView` (schema) and `SpectacularSwaggerView` (interactive docs). Document the auth requirement per endpoint. An undocumented endpoint is unfinished.

---

## Testing the API

Full test patterns — the DRF test client, fixtures, factory-boy, the TDD loop and what to assert per layer — live in **`django-testing`**. At the API layer, every endpoint must cover: happy path (200/201 with the exact response shape), validation (400 with the right error keys), authn/authz (401 unauthenticated, 403 touching another user's row), and the pagination envelope plus filters.

---

## Common pitfalls

- **Trusting the owner FK from the client** — set it server-side in `perform_create`.
- **One overloaded serializer** doing both read and write — split them when shapes diverge.
- **N+1 via `SerializerMethodField` / nested serializers** — prefetch in the view's queryset.
- **No `max_page_size`** — a client can request an enormous page.
- **Permissions without a filtered queryset (or vice versa)** — object permission guards the detail path, the queryset guards the list path; you need both.
- **Inconsistent error shapes** — route everything through the custom exception handler.
- **Nested writes without `create`/`update`** — DRF won't persist nested data automatically.
