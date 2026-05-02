#!/usr/bin/env bash
# install.sh — Symlink each skill in this repo into ~/.claude/skills/
#
# Usage:
#   ./install.sh           Install all skills
#   ./install.sh <name>    Install only the specified skill
#
# Idempotent: re-running is safe. Existing symlinks pointing to this repo
# are left alone. Existing real directories or wrong-target symlinks are
# reported and skipped.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.claude/skills"

mkdir -p "${TARGET_DIR}"

install_skill() {
  local skill_path="$1"
  local skill_name
  skill_name="$(basename "${skill_path}")"
  local link_path="${TARGET_DIR}/${skill_name}"

  if [ ! -f "${skill_path}/SKILL.md" ]; then
    echo "  ⚠  skip ${skill_name} — no SKILL.md inside"
    return
  fi

  if [ -L "${link_path}" ]; then
    local current_target
    current_target="$(readlink "${link_path}")"
    if [ "${current_target}" = "${skill_path}" ]; then
      echo "  ✓  ${skill_name} (already linked)"
    else
      echo "  ⚠  ${skill_name} — symlink exists but points elsewhere: ${current_target}"
    fi
    return
  fi

  if [ -e "${link_path}" ]; then
    echo "  ⚠  ${skill_name} — a real file or directory exists at ${link_path}, not touching it"
    return
  fi

  ln -s "${skill_path}" "${link_path}"
  echo "  ✓  ${skill_name} → ${link_path}"
}

echo "Installing skills from: ${REPO_DIR}"
echo "Target directory:       ${TARGET_DIR}"
echo

if [ $# -ge 1 ]; then
  skill_path="${REPO_DIR}/$1"
  if [ ! -d "${skill_path}" ]; then
    echo "Error: skill directory '${skill_path}' not found" >&2
    exit 1
  fi
  install_skill "${skill_path}"
else
  for entry in "${REPO_DIR}"/*/; do
    [ -d "${entry}" ] || continue
    install_skill "${entry%/}"
  done
fi

echo
echo "Done."
