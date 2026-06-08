---
name: python-tooling
description: The standard Python project toolchain — uv for environments and dependencies, ruff for lint and format, pre-commit for enforcement, and pytest configuration. Use this skill whenever you set up a new Python project, add or update dependencies, configure pyproject.toml, wire ruff or pre-commit, pin a Python version, or sort out why formatting/linting/hooks behave a certain way. Trigger it whenever a task touches uv, ruff, pre-commit, virtual environments, lockfiles, or the [tool.*] sections of pyproject.toml, even if not named explicitly. It is language-tooling, not framework-specific; for Django code conventions see django-conventions and for test patterns see django-testing.
---

# Python Tooling

The baseline toolchain for any Python project: **`uv`** to manage the environment and dependencies, **`ruff`** to lint and format, **`pre-commit`** to enforce it on every commit, and **`pytest`** for tests. `pyproject.toml` is the single source of truth — no `requirements.txt`, no `setup.py`, no scattered config files.

The principle: configuration is declarative and lives in one place, and the same checks run locally, in hooks and in CI, so "works on my machine" can't diverge from the gate.

---

## uv — environments and dependencies

`uv` replaces pip/pip-tools/poetry/virtualenv with one fast tool. It manages the virtual environment, resolves and locks dependencies, and runs commands inside the environment.

### Starting and pinning

```bash
uv init                          # scaffold pyproject.toml (for a fresh project)
uv python pin 3.13               # write .python-version so everyone uses the same interpreter
uv sync                          # create .venv and install everything from the lockfile
```

`.python-version` pins the interpreter; `uv sync` reads it and `pyproject.toml` and produces a reproducible `.venv` plus `uv.lock`. Commit `pyproject.toml` and `uv.lock`; never commit `.venv`.

### Dependencies

```bash
uv add django djangorestframework        # runtime deps -> [project.dependencies]
uv add --dev pytest ruff pre-commit      # dev-only deps -> [dependency-groups.dev]
uv add --group prod gunicorn             # a named group, e.g. production-only
uv remove markdown                       # drop a dependency
uv lock --upgrade                        # re-resolve to newer compatible versions
```

Separate concerns into groups: runtime dependencies the app needs to run, `dev` for tooling (pytest, ruff, pre-commit, factory-boy), and a `prod` group for things only the deployed image needs (e.g. `gunicorn`). Install selectively with `uv sync --group prod`.

### Running commands

Always run project commands **through `uv run`** so they use the locked environment, never a globally installed tool:

```bash
uv run python manage.py migrate
uv run pytest
uv run ruff check .
```

`uv run <cmd>` ensures the environment is synced first, so there's no separate "activate the venv" step to forget.

---

## pyproject.toml — the single source of truth

A representative layout. The `[tool.*]` sections configure ruff and pytest; nothing about tooling lives outside this file.

```toml
[project]
name = "my-api"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "django>=5.1",
    "djangorestframework>=3.15",
    "python-decouple>=3.8",
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
target-version = "py313"
exclude = [".git", ".venv", "__pycache__", "migrations", "*.pyc"]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (import sorting)
    "B",   # flake8-bugbear (likely bugs)
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade (modernise syntax)
    "DJ",  # flake8-django (Django-specific lints)
    "T20", # flake8-print (no stray print())
]
ignore = [
    "E501",  # line length handled by the formatter, not the linter
    "B008",  # function calls in argument defaults (common and intentional in DRF)
]

[tool.ruff.lint.isort]
known-first-party = ["config", "apps"]

[tool.ruff.lint.per-file-ignores]
"config/settings/*.py" = ["F403", "F405"]  # settings use star-imports across env files

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.testing"
python_files = ["test_*.py"]
addopts = "--tb=short -ra"
testpaths = ["apps"]
```

Notes on the choices:

- **`line-length = 120`** is a deliberate, comfortable width; `E501` is left to the formatter so the linter doesn't double-flag it.
- **`I` (isort)** lets ruff sort imports — no separate isort tool. `known-first-party` keeps your own packages in their own import group.
- **`DJ`** catches Django anti-patterns (e.g. `null=True` on string fields), **`T20`** stops stray `print()` reaching production, **`UP`** keeps syntax modern for the pinned Python.
- **`migrations` excluded** because they are machine-generated and shouldn't be reformatted.
- For non-Django projects, drop the `DJ` rule and the settings/migrations specifics; everything else is general.

---

## ruff — lint and format

Ruff is both the linter and the formatter, replacing flake8 + isort + black with one fast tool.

```bash
uv run ruff check .            # lint
uv run ruff check . --fix      # lint and auto-fix what it safely can
uv run ruff format .           # format (black-compatible)
uv run ruff format . --check   # verify formatting without changing files (CI/pre-push)
```

Lint and format are distinct: `check` finds problems (unused imports, likely bugs, unsorted imports), `format` rewrites whitespace and quotes. Run both. In automation, `--check`/`--diff` variants fail without mutating files.

---

## pre-commit — enforce on every commit

`pre-commit` runs the checks automatically when someone commits, so unformatted or unlinted code can't enter history. Config lives in `.pre-commit-config.yaml` at the repo root:

```yaml
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
```

Activate it once per clone:

```bash
uv run pre-commit install              # wire the git hook
uv run pre-commit run --all-files      # run against the whole repo (first time / CI)
uv run pre-commit autoupdate           # bump hook versions
```

How it behaves and why it matters:

- The `ruff` + `ruff-format` hooks mean formatting is applied at commit time, not argued about in review.
- If a hook **modifies files**, the commit fails with "files were modified by this hook". That's expected — re-stage (`git add .`) and commit again. The failure is the hook fixing your code, not an error.
- `no-commit-to-branch --branch main` blocks direct commits to `main`, enforcing branch-based work.
- **Never bypass with `--no-verify`.** If a hook fails, fix the root cause; a green hook is the contract the rest of the team relies on.

---

## pytest — configuration

Test *patterns* (factories, fixtures, the TDD loop, what to assert) live in **django-testing**. The *config* lives here, in `[tool.pytest.ini_options]`:

- `DJANGO_SETTINGS_MODULE` points at a dedicated test settings module (e.g. `config.settings.testing`) so tests never touch dev/prod config.
- `python_files = ["test_*.py"]` and `testpaths` tell pytest where and what to collect.
- `addopts` sets default flags (`--tb=short` for readable tracebacks, `-ra` to summarise non-passing tests).

Run with coverage:

```bash
uv run pytest                                        # all tests
uv run pytest apps/api/tests/test_models.py -vv      # one file, verbose
uv run pytest --cov=apps --cov-report=term-missing   # coverage with uncovered lines
```

---

## Command cheat-sheet

```bash
# environment
uv python pin 3.13
uv sync
uv sync --group prod

# dependencies
uv add <pkg>
uv add --dev <pkg>
uv remove <pkg>
uv lock --upgrade

# run things
uv run <command>

# quality
uv run ruff check . --fix
uv run ruff format .
uv run pre-commit install
uv run pre-commit run --all-files

# tests
uv run pytest
uv run pytest --cov=apps --cov-report=term-missing
```

---

## Common pitfalls

- **Running tools outside `uv run`** — picks up a global install at a different version than the lockfile.
- **Committing `.venv`** — it's a build artifact; commit `pyproject.toml` and `uv.lock` instead.
- **Editing `requirements.txt`** — there isn't one; dependencies live in `pyproject.toml` via `uv add`.
- **`--no-verify` to skip hooks** — defeats the entire point; fix the cause.
- **Treating "files were modified by this hook" as an error** — it's the hook fixing your code; re-stage and commit again.
- **Formatting machine-generated files** (migrations) — keep them in ruff's `exclude`.
- **Linting line length** — leave `E501` to the formatter so you don't get duplicate complaints.
