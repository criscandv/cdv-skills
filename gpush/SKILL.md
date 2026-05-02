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

**Rules for the commit message:**

- Format: `<type>(<optional-scope>): <description>` — all lowercase except proper nouns.
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Use scope between parentheses when the change is clearly about a specific module (e.g. `feat(auth):`, `fix(api):`). Omit the scope only when the change spans many areas.
- Subject line: imperative mood, max 72 chars, no trailing period.
- Add a body **only** if the change is non-trivial: a blank line after the subject, then 1–3 short bullet points or a paragraph explaining the *why* (not the *what* — the diff already shows that).
- **NEVER** include `Co-authored-by: Claude`, `🤖 Generated with Claude`, `Generated-by:`, or any AI attribution. The commit must look exactly like the user wrote it.
- If multiple unrelated changes are staged, prefer the dominant change for `<type>` and mention secondary changes in the body.

Show the proposed message to the user before committing and ask for confirmation. If they want changes, edit and re-show.

Once approved, commit with a heredoc to preserve formatting:

```bash
git commit -m "$(cat <<'EOF'
<the approved message here>
EOF
)"
```

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
  > - `pr target=<base>` → crear PR contra otra base
  > - `merge` → merge a `<default_branch>` con --no-ff
  > - `merge target=<base>` → merge a la base indicada con --no-ff
  > - `no` → terminar"

  Route based on the answer:

  - **`no`** → finish and print confirmation.
  - **`pr`** → run `gh pr create --fill --base <default_branch>`, then print the PR URL.
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
