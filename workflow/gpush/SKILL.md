---
name: gpush
description: Stages all changes, creates a Conventional Commits message in English, and pushes the current branch. If on a branch other than main/develop, asks whether to open a PR with gh CLI or merge into a target branch. Use when the user runs /gpush or asks to "push", "commit and push", or "ship" their changes.
disable-model-invocation: true
allowed-tools: Bash
---

# gpush — Smart git push with PR and merge support

You are helping the user push their work to the remote repository. Follow this workflow strictly. Do **not** skip steps. Do **not** add `Co-authored-by: Claude` or any AI attribution to commit messages.

Communicate progress in Spanish (the user's preferred language). The **commit message itself must always be in English**.

## Workflow

### 1. Pre-flight checks

Run the helper script to gather repository state:

```bash
bash ~/.claude/skills/gpush/scripts/branch_info.sh
```

The script outputs key=value lines. Parse them and abort with a clear message if any of these are true:

- `is_repo=false` → "Not inside a git repository."
- `has_remote=false` → "This repo has no remote configured. Add one with `git remote add origin <url>` first."
- `is_detached=true` → "HEAD is detached. Checkout a branch before pushing."
- `has_changes=false` AND `ahead=0` → "Nothing to commit and nothing to push. Working tree is clean and up to date with the remote."

If `has_changes=false` but `ahead>0`, skip directly to the **push** step (step 4) — there are local commits to push.

Store `branch`, `has_upstream`, and `default_branch` from the output. If `default_branch` is empty, fall back to `main`.

### 2. Stage all changes

```bash
git add -A
```

Then run `git status` and show the user a brief summary if there are unexpected files (`.env`, `node_modules/`, large binaries, build artifacts). Ask for confirmation before continuing if anything looks off.

### 3. Generate the commit message

Inspect the staged diff to write a meaningful Conventional Commits message **in English**:

```bash
git diff --cached --stat
git diff --cached
```

#### Detect the type from the diff (heuristics)

Before reaching for `feat`/`fix`, check whether the diff matches one of the unambiguous cases below. In those, **don't ask** — pick the type directly:

| Diff signal | Type |
| --- | --- |
| All paths under `docs/`, all files `*.md` / `*.rst`, or only README/AGENTS/CLAUDE | `docs` |
| All paths under `tests/` or files matching `test_*.py` / `*.test.ts(x)` / `*.spec.*` | `test` |
| Only `pyproject.toml` / `uv.lock` / `package.json` / `package-lock.json` / `poetry.lock` (dep bumps, no source change) | `chore(deps)` |
| Only formatting/whitespace changes — `ruff format`/`prettier`/`black` output, no behaviour change | `style` |
| Only `.github/` / `Dockerfile` / CI config | `ci` |
| Only `Dockerfile` / build config / Makefile / `setup.cfg` build-related | `build` |
| Pure refactor: identical behaviour, only reorganisation/renames/extraction (verified by reading the diff, not assumed) | `refactor` |
| Reverts another commit (path includes "Revert" / starts from `git revert`) | `revert` |
| New user-facing capability (new endpoint, model, feature surface) | `feat` |
| Bug fix (the diff narrows a wrong behaviour) | `fix` |
| Performance improvement with no behaviour change | `perf` |

If multiple categories apply (a feature *and* its tests, a fix *and* its docs), pick the **dominant** type and mention the others in the body.

#### Pick the scope

- **Monorepo with named sub-projects** (e.g. `apps/api/...` + `apps/app/...`, or `tprealstate-api/` + `tprealstate-app/`): when **all** changed paths live under one sub-project, use it as the scope. `apps/api/views/...` → `(api)`; `serviflex-crm-app/src/...` → `(app)`. When the change spans sub-projects, omit the scope and explain in the body.
- **Single-package repo**: use a module/area name when one is obvious (`auth`, `models`, `pagination`); omit when the change is broad.
- Always lowercase, hyphenated if needed (`feat(api-key): ...`).

#### Rules

- Format: `<type>(<optional-scope>)<!?>: <description>` — all lowercase except proper nouns. The `!` (e.g. `feat(api)!: …`) marks a **breaking change** and is paired with a `BREAKING CHANGE:` footer (see below). Use it only when the public surface (API contract, exported names, env var names, CLI flags, DB schema migration that requires consumer changes) actually changes incompatibly. When uncertain, **ask the user** before adding `!`.
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Subject line: imperative mood, max 72 chars, no trailing period.
- Body **only** when the change is non-trivial: blank line after the subject, then 1–3 short bullet points or a paragraph explaining the *why* (not the *what* — the diff already shows that).
- **NEVER** include `Co-authored-by: Claude`, `🤖 Generated with Claude`, `Generated-by:`, or any AI attribution. The commit must look exactly like the user wrote it.
- If multiple unrelated changes are staged, prefer the dominant change for `<type>` and mention secondary changes in the body. When they're truly unrelated, offer the user the option to split into separate commits before continuing.

#### Footers (when applicable)

After the body, leave a blank line and add Git trailers (one per line) for things the user mentions or the context implies:

- `BREAKING CHANGE: <what breaks and the migration path>` — **mandatory** whenever the subject uses `!`.
- `Closes #<n>` / `Fixes #<n>` — when the user references an issue they intend to close, or the branch name encodes one (e.g. `feature/123-add-invoices` → `Refs #123`; only use `Closes`/`Fixes` if the user confirms it actually resolves the issue).
- `Refs #<n>` — partial work towards an issue.
- Standard trailers (`Reported-by:`, `Reviewed-by:`) — only if the user provides them.

Never invent issue numbers; only include footers when there's a concrete source for them.

#### Examples

```text
Input  (paths): apps/api/views/login.py, apps/api/serializers/auth_token.py
Output:
feat(api): add httpOnly cookie storage for refresh token

Input  (paths): docs/ARCHITECTURE.md (typo fix), docs/COMMANDS.md (clarify)
Output:
docs: clarify migration commands and fix typo
```

```text
Input  (paths): pyproject.toml + uv.lock only (django 6.0.4 -> 6.0.6)
Output:
chore(deps): bump django to 6.0.6
```

```text
Input  (paths): apps/api/tests/test_worker.py only
Output:
test(api): cover soft-delete contract on Worker
```

```text
Input  (paths): apps/api/serializers/* renamed to one-class-per-file
Output:
refactor(api): split grouped serializers into one class per file

- auth_serializers / registration_serializers / worker_serializers
  are now one file per class under serializers/
- public symbols re-exported from serializers/__init__.py so callers
  don't change
```

```text
Input  (paths): apps/api/exceptions/handler.py (new), removes old envelope shape
Output:
feat(api)!: switch error responses to {success, message, errors}

The global exception handler now wraps every handled error in the
standard envelope. Clients reading `error.detail` directly must update
to read `message` and `errors`.

BREAKING CHANGE: error response shape changed from {error: {...}} to
{success: false, message, errors}. Update API consumers.
```

#### Confirm and commit

Show the proposed message to the user before committing and ask for confirmation. If they want changes, edit and re-show.

Once approved, commit with a heredoc to preserve formatting:

```bash
git commit -m "$(cat <<'EOF'
<the approved message here>
EOF
)"
```

#### If pre-commit hooks modify files

When the repo's `.pre-commit-config.yaml` runs formatters/fixers (ruff, prettier, trailing-whitespace, end-of-file-fixer), the first commit attempt may fail with output like:

```
ruff-format..............................................................Failed
- hook id: ruff-format
- files were modified by this hook
```

This is **not** an error — the hook fixed your files. The commit didn't happen. Handle it automatically:

1. `git status` to confirm files are now modified (the hook's edits are unstaged).
2. Show the user a one-line summary: *"Pre-commit reformateó ficheros; re-stagear y reintentar."*
3. `git add -A` to re-stage the formatter's changes.
4. Retry the same commit (same message, same heredoc).
5. **Retry at most once.** If the second attempt also fails because hooks modified files again, stop and surface the output to the user — something is wrong (a hook that doesn't converge, or two hooks fighting each other) and a human needs to look.

If the commit fails for any **other** reason (lint error the hook can't auto-fix, `no-commit-to-branch` blocking a protected branch, etc.), do **not** retry — report the hook output verbatim and stop the workflow.

### 4. Push the current branch

Read `branch` and `has_upstream` from the helper output.

- If `has_upstream=true`:

```bash
  git push
```

- If `has_upstream=false`:

```bash
  git push -u origin <branch>
```

If the push fails because the remote has new commits, report the error and suggest `git pull --rebase` — do **not** force-push automatically.

### 5. Branch-specific follow-up

Read `branch` from the helper output:

- **If `branch` is `main` or `develop`:** Done. Print a short confirmation showing the commit hash and branch.

- **If `branch` is anything else:** Ask the user (in Spanish):

  > "Estás en `<branch>`. ¿Qué hago?
  > - `pr` → crear PR (base = `<default_branch>`)
  > - `pr develop` → crear PR a `develop`
  > - `pr target=<base>` → crear PR contra otra base
  > - `merge` → merge a `<default_branch>` con --no-ff
  > - `merge target=<base>` → merge a la base indicada con --no-ff
  > - `no` → terminar"

  Route based on the answer:

  - **`no`** → finish and print confirmation.
  - **`pr`** → run `gh pr create --fill --base <default_branch>`, then print the PR URL.
  - **`pr develop`** → run `gh pr create --fill --base develop`, then print the PR URL.
  - **`pr target=<base>`** → run `gh pr create --fill --base <base>`, then print the PR URL.
  - **`merge`** → run the **Merge sub-flow** below with `<default_branch>` as base.
  - **`merge target=<base>`** → run the **Merge sub-flow** below with `<base>` as base.

  If `gh` is not authenticated, the command will fail with a clear error — report it verbatim and suggest `gh auth login`.

## Merge sub-flow

Inputs: `feature_branch` (the branch the user is currently on), `base` (the merge target).

Execute these steps in order. **If any step fails, stop immediately, report the failure, and try to leave the user back on `feature_branch`.**

### M1. Fetch latest refs

```bash
git fetch origin
```

### M2. Switch to base branch

```bash
git checkout <base>
```

If checkout fails (e.g. uncommitted changes — shouldn't happen since we just committed everything, but defensive), report and abort.

### M3. Bring base up to date

```bash
git pull --ff-only
```

If this fails (base diverged from remote, or has uncommitted local commits not pushed), abort:

1. Run `git checkout <feature_branch>` to return to the original branch.
2. Tell the user: "La rama `<base>` ha divergido del remoto y no se puede actualizar con fast-forward. Sincroniza `<base>` manualmente antes de hacer merge."
3. Stop the workflow.

### M4. Merge feature branch with --no-ff

```bash
git merge --no-ff <feature_branch>
```

If conflicts appear:

1. Run `git merge --abort`.
2. Run `git checkout <feature_branch>`.
3. Tell the user: "Hay conflictos al hacer merge de `<feature_branch>` en `<base>`. Aborté el merge y te dejo en `<feature_branch>`. Resuélvelos manualmente."
4. Stop the workflow.

When the merge succeeds without conflicts, git will open an editor for the merge commit message. We want to skip that — use the default message non-interactively:

```bash
GIT_MERGE_AUTOEDIT=no git merge --no-ff <feature_branch>
```

(Use this form from the start in step M4 — it avoids the editor opening.)

### M5. Push the merged base

```bash
git push
```

If this fails, abort:

1. Run `git reset --hard origin/<base>` is **dangerous** and we will NOT do it automatically.
2. Instead, tell the user: "El merge se hizo localmente en `<base>` pero no pude pushearlo. Resuelve manualmente. Estás actualmente en `<base>`."
3. Stop the workflow without switching branches (the user needs to be on `<base>` to fix it).

### M6. Return to feature branch

```bash
git checkout <feature_branch>
```

### M7. Print summary

Show the user (in Spanish):

- Rama feature: `<feature_branch>` (pusheada)
- Base actualizada: `<base>` (con merge --no-ff)
- Hash del merge commit
- Estás de vuelta en: `<feature_branch>`

## Important constraints

- Always run `git status` before staging if you're unsure what's about to be committed; show it to the user if there are unexpected files.
- Do **not** amend, rebase, or rewrite history unless explicitly asked.
- Do **not** force push (`--force` / `--force-with-lease`) unless explicitly asked.
- Do **not** create new branches unless explicitly asked.
- Do **not** delete branches (local or remote) unless explicitly asked.
- Do **not** attempt to resolve merge conflicts automatically — always abort and hand back to the user.
