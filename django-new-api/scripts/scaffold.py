#!/usr/bin/env python3
"""Scaffold a Django + DRF API project that follows the house conventions.

Writes the full skeleton (settings split, abstract base models, custom user,
request-context middleware, domain exceptions + global handler, custom
pagination, standard response renderer, dual JWT/API-key auth, admin base,
tests skeleton) plus pyproject tool config and pre-commit.

It only writes files; it does not run uv/migrations. The SKILL.md drives those
steps after this script lays down the tree.

Usage:
    python scaffold.py --target /path/to/project [--app api] [--python 3.13]

The project name is taken from the target directory name unless --name is given.
Existing files are never overwritten unless --force is passed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# --------------------------------------------------------------------------- #
# File templates. Keys are paths relative to the project root; "{app}" in a key
# or value is substituted with the chosen app name, "{py}" with the python
# version (e.g. "313"), "{name}" with the project name.
# --------------------------------------------------------------------------- #

FILES: dict[str, str] = {}

FILES[".python-version"] = "{pyver}\n"

FILES[".gitignore"] = """\
.venv/
__pycache__/
*.pyc
.env
*.sqlite3
media/
.ruff_cache/
.pytest_cache/
htmlcov/
.coverage
"""

FILES[".env.example"] = """\
SECRET_KEY=change-me
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
DATABASE_URL=postgres://postgres:postgres@localhost:5432/{name}
API_KEY=change-me-public-endpoint-key
"""

FILES["pyproject.toml"] = """\
[project]
name = "{name}"
version = "0.1.0"
description = "API for {name}"
requires-python = ">={pydot}"
dependencies = [
    "django>=5.1",
    "djangorestframework>=3.15",
    "djangorestframework-simplejwt>=5.3",
    "django-cors-headers>=4.4",
    "django-filter>=24.3",
    "drf-spectacular>=0.27",
    "python-decouple>=3.8",
    "psycopg2-binary>=2.9",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-django>=4.9",
    "pytest-cov>=6.0",
    "factory-boy>=3.3",
    "faker>=33.0",
    "ruff>=0.6",
    "pre-commit>=4.0",
]
prod = [
    "gunicorn>=23.0",
]

[tool.ruff]
line-length = 120
indent-width = 4
target-version = "py{py}"
exclude = [".git", ".venv", "__pycache__", "migrations", "*.pyc"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "DJ", "T20"]
ignore = ["E501", "B008"]

[tool.ruff.lint.isort]
known-first-party = ["config", "apps"]

[tool.ruff.lint.per-file-ignores]
"config/settings/*.py" = ["F403", "F405"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.testing"
python_files = ["test_*.py"]
addopts = "--tb=short -ra"
testpaths = ["apps"]
"""

FILES[".pre-commit-config.yaml"] = """\
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
      - id: no-commit-to-branch
        args: [--branch, main]
"""

FILES["manage.py"] = """\
#!/usr/bin/env python
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
"""

# --- config package -------------------------------------------------------- #

FILES["config/__init__.py"] = ""

FILES["config/settings/__init__.py"] = ""

FILES["config/settings/base.py"] = '''\
from datetime import timedelta
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS: list[str] = []

# API key for public / server-to-server endpoints (see apps.{app}.authentication).
API_KEY = config("API_KEY", default="")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # Local
    "apps.{app}",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.{app}.middleware.RequestContextMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {{
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        }},
    }},
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {{
    "default": {{
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="{name}"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="postgres"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }}
}}

AUTH_PASSWORD_VALIDATORS = [
    {{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"}},
    {{"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"}},
    {{"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"}},
    {{"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"}},
]

LANGUAGE_CODE = "es-ES"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "{app}.User"

REST_FRAMEWORK = {{
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "apps.{app}.authentication.APIKeyAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "apps.{app}.pagination.StandardPagination",
    "DEFAULT_RENDERER_CLASSES": ["apps.{app}.renderers.StandardJSONRenderer"],
    "EXCEPTION_HANDLER": "apps.{app}.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "PAGE_SIZE": 20,
}}

SIMPLE_JWT = {{
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}}

SPECTACULAR_SETTINGS = {{
    "TITLE": "{name} API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}}

CORS_ALLOWED_ORIGINS: list[str] = []
CORS_ALLOW_CREDENTIALS = True
'''

FILES["config/settings/development.py"] = """\
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOWED_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
"""

FILES["config/settings/staging.py"] = """\
from .base import *  # noqa: F403

DEBUG = False
"""

FILES["config/settings/production.py"] = """\
from .base import *  # noqa: F403

DEBUG = False
"""

FILES["config/settings/testing.py"] = """\
from .base import *  # noqa: F403

DEBUG = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
"""

FILES["config/urls.py"] = """\
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("v1/", include("apps.{app}.urls")),
    path("v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
"""

FILES["config/wsgi.py"] = """\
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
application = get_wsgi_application()
"""

FILES["config/asgi.py"] = """\
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
application = get_asgi_application()
"""

# --- app package ----------------------------------------------------------- #

FILES["apps/__init__.py"] = ""

FILES["apps/{app}/__init__.py"] = ""

FILES["apps/{app}/apps.py"] = """\
from django.apps import AppConfig


class {AppClass}Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.{app}"
"""

# models / abstracts
FILES["apps/{app}/models/__init__.py"] = """\
from .abstracts import ActiveManager, BaseModel, UUIDPrimaryKeyModel
from .user import User, UserManager

__all__ = ["UUIDPrimaryKeyModel", "BaseModel", "ActiveManager", "User", "UserManager"]
"""

FILES["apps/{app}/models/abstracts/__init__.py"] = """\
from .base import BaseModel
from .managers import ActiveManager
from .uuid import UUIDPrimaryKeyModel

__all__ = ["BaseModel", "ActiveManager", "UUIDPrimaryKeyModel"]
"""

FILES["apps/{app}/models/abstracts/uuid.py"] = """\
import uuid

from django.db import models


class UUIDPrimaryKeyModel(models.Model):
    \"\"\"Abstract base that replaces the default BigAutoField id with a UUID primary key.\"\"\"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
"""

FILES["apps/{app}/models/abstracts/managers.py"] = """\
from django.db import models


class ActiveManager(models.Manager):
    \"\"\"Default manager that restricts querysets to live records only.\"\"\"

    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(deleted_at__isnull=True, active=True)
"""

FILES["apps/{app}/models/abstracts/base.py"] = """\
from django.db import models
from django.utils import timezone

from .managers import ActiveManager
from .uuid import UUIDPrimaryKeyModel


class BaseModel(UUIDPrimaryKeyModel):
    \"\"\"Abstract base for all concrete domain models (UUID PK, timestamps, soft-delete).\"\"\"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    active = models.BooleanField(default=True, db_index=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta(UUIDPrimaryKeyModel.Meta):
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self) -> None:
        \"\"\"Retire the record without removing the row.\"\"\"
        self.deleted_at = timezone.now()
        self.active = False
        self.save(update_fields=["deleted_at", "active", "updated_at"])
"""

FILES["apps/{app}/models/user.py"] = """\
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from .abstracts import BaseModel


class UserManager(BaseUserManager):
    \"\"\"Keeps create_user/create_superuser and enforces the soft-delete filter.\"\"\"

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
    \"\"\"Custom user using email as the unique identifier.\"\"\"

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
"""

# serializers
FILES["apps/{app}/serializers/__init__.py"] = ""
FILES["apps/{app}/serializers/abstracts/__init__.py"] = ""

# views / abstracts
FILES["apps/{app}/views/__init__.py"] = ""
FILES["apps/{app}/views/abstracts/__init__.py"] = """\
from .base import BaseOwnedViewSet

__all__ = ["BaseOwnedViewSet"]
"""
FILES["apps/{app}/views/abstracts/base.py"] = """\
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.{app}.pagination import StandardPagination


class BaseOwnedViewSet(viewsets.ModelViewSet):
    \"\"\"Base for resources owned by the requesting user.

    Centralises permissions, pagination and owner-scoping so concrete viewsets
    only declare their model-specific bits (queryset, serializer_class).
    \"\"\"

    permission_classes = (IsAuthenticated,)
    pagination_class = StandardPagination
    owner_field = "user"

    def get_queryset(self):
        return self.queryset.filter(**{{self.owner_field: self.request.user}})

    def perform_create(self, serializer) -> None:
        serializer.save(**{{self.owner_field: self.request.user}})
"""

# admin / abstracts
FILES["apps/{app}/admin/__init__.py"] = """\
from .abstracts import BaseModelAdmin

__all__ = ["BaseModelAdmin"]
"""
FILES["apps/{app}/admin/abstracts/__init__.py"] = """\
from .base import BaseModelAdmin

__all__ = ["BaseModelAdmin"]
"""
FILES["apps/{app}/admin/abstracts/base.py"] = """\
from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    \"\"\"Shared admin base: audit fields read-only, soft-delete visible in filters.\"\"\"

    readonly_fields = ("id", "created_at", "updated_at")
    list_filter = ("active",)
    ordering = ("-created_at",)
"""

# middleware
FILES["apps/{app}/middleware/__init__.py"] = """\
from .request_context import RequestContextMiddleware

__all__ = ["RequestContextMiddleware"]
"""
FILES["apps/{app}/middleware/request_context.py"] = """\
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class RequestContextMiddleware:
    \"\"\"Populate request.current_user on every request.

    Resolves the authenticated user via JWT (if present) and attaches it to the
    request. Authorization decisions stay with DRF; this never short-circuits or
    raises on missing/invalid credentials.
    \"\"\"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self._jwt = JWTAuthentication()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.current_user = None

        if request.path.startswith("/admin/"):
            return self.get_response(request)

        user = self._resolve_user(request)
        if user is not None and getattr(user, "is_authenticated", False):
            request.current_user = user

        return self.get_response(request)

    def _resolve_user(self, request: HttpRequest):
        existing = getattr(request, "user", None)
        if existing is not None and getattr(existing, "is_authenticated", False):
            return existing
        try:
            result = self._jwt.authenticate(request)
        except (InvalidToken, TokenError):
            return None
        except Exception:
            return None
        if result is None:
            return None
        user, _token = result
        return user
"""

# authentication
FILES["apps/{app}/authentication/__init__.py"] = """\
from .api_key import APIKeyAuthentication, APIKeyUser

__all__ = ["APIKeyAuthentication", "APIKeyUser"]
"""
FILES["apps/{app}/authentication/api_key.py"] = """\
import hmac

from django.conf import settings
from rest_framework import authentication, exceptions


class APIKeyUser:
    \"\"\"Lightweight non-persisted principal representing a valid API-key caller.\"\"\"

    is_authenticated = True


class APIKeyAuthentication(authentication.BaseAuthentication):
    \"\"\"Authenticate a request by a shared API key carried in the X-API-Key header.\"\"\"

    keyword = "X-API-Key"

    def authenticate(self, request):
        provided = request.headers.get(self.keyword)
        if not provided:
            return None  # let other authenticators (JWT) try

        expected = settings.API_KEY
        if not expected or not hmac.compare_digest(provided, expected):
            raise exceptions.AuthenticationFailed("Invalid API key.")

        return (APIKeyUser(), None)
"""

# exceptions
FILES["apps/{app}/exceptions/__init__.py"] = """\
from .domain import IntegrationUnavailable, ResourceConflict
from .handler import api_exception_handler

__all__ = ["IntegrationUnavailable", "ResourceConflict", "api_exception_handler"]
"""
FILES["apps/{app}/exceptions/domain.py"] = """\
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
"""
FILES["apps/{app}/exceptions/handler.py"] = """\
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    \"\"\"Normalise every handled error to {\\"success\\": false, \\"message\\": ..., \\"errors\\": ...}.

    Returns None for unhandled exceptions so genuine bugs surface as a logged 500.
    \"\"\"
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
        errors = detail

    response.data = {"success": False, "message": message, "errors": errors}
    return response
"""

# pagination
FILES["apps/{app}/pagination/__init__.py"] = """\
from .standard import StandardPagination

__all__ = ["StandardPagination"]
"""
FILES["apps/{app}/pagination/standard.py"] = """\
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    \"\"\"Stable, documented pagination envelope with a client-tunable, bounded page size.\"\"\"

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
"""

# renderers
FILES["apps/{app}/renderers/__init__.py"] = """\
from .standard import StandardJSONRenderer

__all__ = ["StandardJSONRenderer"]
"""
FILES["apps/{app}/renderers/standard.py"] = """\
from rest_framework.renderers import JSONRenderer


class StandardJSONRenderer(JSONRenderer):
    \"\"\"Wrap every successful payload in {\\"success\\": true, \\"message\\": ..., \\"data\\": ...}.

    Error responses (status >= 400) are already shaped by the exception handler and
    pass through. Views may return an already-enveloped dict to attach a message.
    \"\"\"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context["response"] if renderer_context else None
        status_code = getattr(response, "status_code", 200)

        if status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)

        if isinstance(data, dict) and "success" in data:
            payload = data
        else:
            payload = {"success": True, "message": None, "data": data}

        return super().render(payload, accepted_media_type, renderer_context)
"""

# urls / lib / migrations
FILES["apps/{app}/urls.py"] = """\
from rest_framework.routers import DefaultRouter

app_name = "{app}"

router = DefaultRouter()
# router.register(r"<resource>", <ViewSet>, basename="<resource>")

urlpatterns = [
    *router.urls,
]
"""
FILES["apps/{app}/lib/__init__.py"] = ""
FILES["apps/{app}/migrations/__init__.py"] = ""

# tests
FILES["apps/{app}/tests/__init__.py"] = ""
FILES["apps/{app}/tests/conftest.py"] = """\
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()
"""
FILES["apps/{app}/tests/factories.py"] = """\
import factory
from factory.django import DjangoModelFactory

from apps.{app}.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{{n}}@example.com")
    first_name = factory.Faker("first_name")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "password123")
        if create:
            self.save()
"""


def render(text: str, *, app: str, name: str, py: str, pydot: str, pyver: str, app_class: str) -> str:
    """Substitute placeholder tokens, then collapse doubled braces to single.

    Placeholders are written with single braces ({app}, {name}, {py}, {pydot},
    {pyver}, {AppClass}); literal braces in the generated code are written doubled
    ({{ }}) and collapsed afterwards. This avoids str.format choking on the many
    literal braces in Python/TOML bodies.
    """
    for token, value in (
        ("{app}", app),
        ("{name}", name),
        ("{pydot}", pydot),
        ("{pyver}", pyver),
        ("{AppClass}", app_class),
        ("{py}", py),
    ):
        text = text.replace(token, value)
    return text.replace("{{", "{").replace("}}", "}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a Django + DRF API project.")
    parser.add_argument("--target", required=True, help="Project root directory.")
    parser.add_argument("--app", default="api", help="Domain app name (default: api).")
    parser.add_argument("--name", default=None, help="Project name (default: target dir name).")
    parser.add_argument("--python", default="3.13", help="Python version, e.g. 3.13.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    name = args.name or target.name
    app = args.app
    pyver = args.python  # e.g. "3.13"
    pydot = pyver  # requires-python uses dotted form
    py = pyver.replace(".", "")  # ruff target-version uses "py313"
    app_class = "".join(part.capitalize() for part in app.replace("-", "_").split("_"))

    written, skipped = 0, 0
    for rel_template, content_template in FILES.items():
        rel = rel_template.format(app=app)
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not args.force:
            skipped += 1
            continue
        path.write_text(
            render(content_template, app=app, name=name, py=py, pydot=pydot, pyver=pyver, app_class=app_class)
        )
        written += 1

    print(f"Scaffolded project '{name}' (app '{app}', python {pyver}) at {target}")
    print(f"  files written: {written}, skipped (already existed): {skipped}")
    print("Next: uv sync, then makemigrations + migrate. See SKILL.md.")


if __name__ == "__main__":
    main()
