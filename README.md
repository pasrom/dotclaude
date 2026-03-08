# dotclaude

My personal [Claude Code](https://docs.anthropic.com/en/docs/claude-code) configuration — skills, tools, and workflows.

## Structure

```
dotclaude/
  skills/                # Claude Code skills (SKILL.md files)
    git-workflow/        # Atomic commits with Conventional Commits
    km-init/             # Bootstrap a new knowledge repo
    km-ingest/           # Save content with auto-classification
    km-query/            # Semantic search across knowledge repo
    km-decision/         # Create Architecture Decision Records
    km-update/           # Modify existing documents
    km-transcript/       # Process meeting transcripts
    km-sort-inbox/       # Sort inbox files into proper folders
    km-review/           # Submit documents for review via PR/MR
    km-weekly-summary/   # Weekly changelog from git history
    km-archive/          # Document lifecycle management
    km-help/             # List all KM skills
  tools/                 # Standalone scripts and utilities
    ai-mr-review/        # AI-powered GitLab MR reviews using Claude
```

## Skills

### git-workflow

Enforces atomic commits after every logical unit of work using [Conventional Commits](https://www.conventionalcommits.org/) format.

### Knowledge Management (km-*)

A suite of 11 skills for AI-driven knowledge management. Works in **any Git repo** — just run `/km-init` to bootstrap a `CONVENTIONS.md` and folder structure.

**Quick start:**
```bash
# In any Git repo:
/km-init              # Creates CONVENTIONS.md, inbox/, topics/, etc.
/km-ingest <content>  # Start saving knowledge
/km-query <question>  # Search and summarize
```

| Skill | Purpose |
|-------|---------|
| `/km-init` | Bootstrap a new knowledge repo (CONVENTIONS.md + folders) |
| `/km-ingest` | Save any content with auto-classification and frontmatter |
| `/km-query` | Semantic search and summarize knowledge |
| `/km-decision` | Create Architecture Decision Records (ADRs) |
| `/km-update` | Modify existing documents with confirmation |
| `/km-transcript` | Process meeting transcripts, extract decisions and actions |
| `/km-sort-inbox` | Batch-sort inbox/ files into proper locations |
| `/km-review` | Submit document for review via PR/MR |
| `/km-weekly-summary` | Generate changelog from git history |
| `/km-archive` | Mark documents as superseded or obsolete |
| `/km-help` | Show all available KM skills with examples |

All skills are installed automatically by `./install.sh` (symlinks to `~/.claude/skills/`).

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
