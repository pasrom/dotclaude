# dotclaude

My personal [Claude Code](https://docs.anthropic.com/en/docs/claude-code) configuration — skills, tools, and workflows.

## Structure

```
dotclaude/
  skills/          # Claude Code skills (SKILL.md files)
    git-workflow/  # Atomic commits with Conventional Commits
  tools/           # Standalone scripts and utilities
    ai-mr-review/  # AI-powered GitLab MR reviews using Claude
```

## Skills

### git-workflow

Enforces atomic commits after every logical unit of work using [Conventional Commits](https://www.conventionalcommits.org/) format.

Installed automatically by `./install.sh` (symlinks to `~/.claude/skills/`).

## Tools

### ai-mr-review

AI-powered merge request code review for GitLab using Claude Code CLI. Reviews your GitLab merge requests locally or posts feedback directly as MR comments — including inline line-level comments on the diff.

**Prerequisites:**
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) — installed and logged in
- [glab](https://gitlab.com/gitlab-org/cli) — GitLab CLI, authenticated (`glab auth login`)
- Python 3

**Quick Start:**

```bash
git clone https://github.com/pasrom/dotclaude.git
cd dotclaude
./install.sh   # Symlinks skills + adds shell alias

# Then from any GitLab repo:
review --mr 42
```

**Usage:**

```bash
review.sh                          # Review current branch vs main
review.sh develop                  # Review against a different base branch
review.sh --list                   # List open merge requests
review.sh --mr 42                  # Review a specific GitLab MR
review.sh --mr 42 --post           # Review and post as MR comment
review.sh --mr 42 --inline         # Review with inline line comments
review.sh --mr 42 --inline --dry-run  # Preview inline comments
```

On first run, the script creates `review_prompt.md` from the included `.example` template. Edit it to customize the review focus for your project (these custom prompts are gitignored).

**How it works:**

1. Collects the diff — from your local branch (`git diff`) or from a GitLab MR (`glab mr diff`)
2. Sends it to Claude — via `claude --print` with a customizable review prompt
3. Displays the review — structured output with severity levels
4. Optionally posts to GitLab — as a single comment (`--post`) or as inline line comments (`--inline`)

**Authentication:** Uses your existing Claude Code CLI login and `glab auth login`. For `--post` and `--inline`, your GitLab token needs the **`api`** scope.

## License

[MIT](LICENSE)
