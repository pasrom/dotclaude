# dotclaude

My personal [Claude Code](https://docs.anthropic.com/en/docs/claude-code) configuration — skills, tools, and workflows.

## Structure

```
dotclaude/
  skills/                # Claude Code skills (SKILL.md files)
    git-workflow/        # Atomic commits with Conventional Commits
    km/                  # Unified knowledge management
    comms-archive/       # Archive Outlook/Teams into the knowledge base
    datasheet-to-md/     # PDF datasheet -> clean Markdown for LLMs
    cv-extract/          # CV PDF -> JSON Resume + portrait photo
    ris-search/          # Search Austrian legal sources (RIS)
    session-summarize/   # Summarize Claude Code session transcripts
    repo-publication-audit/  # Prepare a company-internal repo for public release
  global-rules/          # Instruction blocks appended to ~/.claude/CLAUDE.md
  tools/                 # Standalone scripts and utilities
    ai-mr-review/        # AI-powered GitLab MR reviews using Claude
    tmux-claude/         # Launch Claude across repos in tmux windows
```

## Skills

### git-workflow

Enforces atomic commits after every logical unit of work using [Conventional Commits](https://www.conventionalcommits.org/) format.

### Knowledge Management (`/km`)

One skill for all knowledge management. Works in **any Git repo** — just type `/km init` to get started.

```bash
/km init                                    # Bootstrap a new knowledge repo
/km What do we know about thermal management?  # Search and summarize
/km We decided to use LTC6813               # Save content (auto-detects type)
/km update sensor-fusion: add calibration   # Modify a document
/km brain add https://gitlab.com/org/team-brain.git  # Link another brain
/km @mko PROFINET stack options             # Search a linked brain
/km @all Zephyr RTOS                        # Search all brains
/km help                                    # Show all commands
```

**Cross-repo brains:** Link other knowledge repos as Git submodules. Each brain has its own access permissions — every team member controls who can read their brain. Brains auto-update when queried (if stale >15 min) and every result includes `[brain@commit]` for full traceability.

### Other skills

- **comms-archive** — archive Outlook emails and Teams messages as a daily digest in the knowledge base (requires the Microsoft 365 MCP connector).
- **datasheet-to-md** — convert a PDF datasheet into clean, LLM-friendly Markdown with extracted images, then review it for fidelity.
- **cv-extract** — extract structured data (JSON Resume) and the portrait photo from a CV PDF.
- **ris-search** — search Austrian legal sources via the RIS (Rechtsinformationssystem).
- **session-summarize** — summarize a Claude Code session transcript, with token/cost stats.
- **repo-publication-audit**: audit and scrub a repository before, or after, publishing it. Four provenance surfaces, history rewrite with verification, commit identity per remote, and an outside-in pass on the published result.

## Install

```bash
# macOS / Linux / WSL
git clone https://github.com/pasrom/dotclaude.git
cd dotclaude
./install.sh
```

```powershell
# Windows (PowerShell)
git clone https://github.com/pasrom/dotclaude.git
cd dotclaude
.\install.ps1
```

Both scripts link `~/.claude/skills/` entries to this repo (symlinks on macOS/Linux, junctions on Windows); use `-f` to reinstall. The bash script additionally registers the `review` alias, adds this repo to `additionalDirectories`, appends a `# dotclaude` section to your global `CLAUDE.md`, and supports `--dir=<path>` for an alternate config directory (`install.ps1` does skill links only):

```bash
./install.sh --dir="$HOME/.claude-work"   # Install to alternate Claude config dir
```

## Tools

### ai-mr-review

AI-powered merge request code review for GitLab using Claude Code CLI. Reviews your GitLab merge requests locally or posts feedback directly as MR comments — including inline line-level comments on the diff.

**Prerequisites:**
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) — installed and logged in
- [glab](https://gitlab.com/gitlab-org/cli) — GitLab CLI, authenticated (`glab auth login`)
- Python 3

**Quick Start:**

```bash
# After install (see above), from any GitLab repo:
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
