# cdv-skills

Personal collection of [Claude Code](https://docs.claude.com/en/docs/claude-code) skills.

Skills extend Claude Code with custom workflows. Each skill lives in its own directory with a `SKILL.md` file containing instructions and metadata.

## Structure
cdv-skills/
├── install.sh          # Symlinks each skill into ~/.claude/skills/
├── gpush/              # Smart git push with PR and merge support
└── ...                 # More skills added over time

## Installation

Clone the repo and run the installer:

```bash
git clone git@github.com:<your-username>/cdv-skills.git ~/Development/cdv-skills
cd ~/Development/cdv-skills
./install.sh
```

The installer creates a symlink from each skill directory to `~/.claude/skills/<skill-name>`. Edits in the repo are reflected instantly — no reinstall needed.

## Skills

| Skill | Slash command | Description |
|-------|---------------|-------------|
| `gpush` | `/gpush` | Stages changes, writes a Conventional Commits message in English, pushes the current branch, and offers PR or merge to base. |

## Adding a new skill

1. Create a new directory at the repo root: `mkdir my-skill`
2. Add a `SKILL.md` with frontmatter (`name`, `description`, etc.) and instructions.
3. Run `./install.sh` to symlink it into `~/.claude/skills/`.
4. Commit and push.

## License

Personal use. Not licensed for redistribution.
