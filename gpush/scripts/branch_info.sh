#!/usr/bin/env bash
# branch_info.sh — Emit repository state as key=value pairs for the gpush skill.
# All output goes to stdout. Errors are silenced; falsy values are emitted instead.

set -u

# Check if we're inside a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "is_repo=false"
  exit 0
fi
echo "is_repo=true"

# Detached HEAD check
if ! git symbolic-ref --quiet HEAD >/dev/null 2>&1; then
  echo "is_detached=true"
  echo "branch="
else
  echo "is_detached=false"
  branch="$(git rev-parse --abbrev-ref HEAD)"
  echo "branch=${branch}"
fi

# Remote configured?
if [ -z "$(git remote)" ]; then
  echo "has_remote=false"
else
  echo "has_remote=true"
fi

# Upstream configured for current branch?
if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  echo "has_upstream=true"
  upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}')"
  echo "upstream=${upstream}"
else
  echo "has_upstream=false"
  echo "upstream="
fi

# Working tree changes (staged + unstaged + untracked)
if [ -n "$(git status --porcelain)" ]; then
  echo "has_changes=true"
else
  echo "has_changes=false"
fi

# Ahead/behind count vs upstream (0 if no upstream)
if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  counts="$(git rev-list --left-right --count '@{u}'...HEAD 2>/dev/null || echo "0	0")"
  behind="$(echo "$counts" | awk '{print $1}')"
  ahead="$(echo "$counts" | awk '{print $2}')"
  echo "behind=${behind:-0}"
  echo "ahead=${ahead:-0}"
else
  echo "behind=0"
  echo "ahead=0"
fi

# Default branch hint (useful for PR base)
default_branch="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')"
echo "default_branch=${default_branch:-}"
