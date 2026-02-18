# dotclaude

Personal Claude Code configuration repo — skills, tools, and workflows.

## Structure

- `skills/` — Claude Code skills (SKILL.md files), symlinked to `~/.claude/skills/` via `install.sh`
- `tools/` — Standalone scripts and utilities
- `install.sh` — Sets up symlinks and shell aliases (`--force` to reinstall)

## Conventions

- Language: English for code, comments, and documentation
- Shell scripts: `bash`, `set -euo pipefail`, portable (macOS + Linux)
- Skills follow Claude Code SKILL.md format (YAML frontmatter + markdown)

## Tools

### ai-mr-review

GitLab MR review tool using Claude Code CLI + glab.

Key files:
- `tools/ai-mr-review/review.sh` — Main script
- `tools/ai-mr-review/post_inline_comments.py` — Posts inline comments via GitLab Discussions API
- `tools/ai-mr-review/*.example` — Generic prompt templates (committed)
- `tools/ai-mr-review/review_prompt.md` / `review_prompt_inline.md` — Custom prompts (gitignored)
