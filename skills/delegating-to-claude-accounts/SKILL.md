---
name: delegating-to-claude-accounts
description: Use when you need to run a prompt under a DIFFERENT Claude Code account/subscription than the current session, e.g. offload a headless task to the work (claude-work) or second (claude-acc2) account, spread cost across another account's headless credit pool, or run under an isolated profile/auth. Not for same-account parallelism (use the Agent tool for that).
---

# Delegating to Claude Code accounts

## Overview

Roman runs several Claude Code accounts on one Mac. Each is a fully separate
profile selected by `CLAUDE_CONFIG_DIR` (own auth, settings, MCP, history),
invoked through a wrapper on `PATH`. To use another account from a session,
call its wrapper **headless with `-p`** — it spawns an independent `claude`
process under that subscription and prints the answer.

## Accounts

| Command | Config dir | Account |
|---|---|---|
| `claude` (default) | `~/.claude` | primary / private — usually the current session |
| `claude-work` | `~/.claude-work` | work (Firma) |
| `claude-acc2` | `~/.claude-acc2` | second personal |
| `claude-science` · `claude-bioscience` · `operon` | `~/.claude-science` | science (compiled launcher, 3 entry points → same profile) |

`claude-work` / `claude-acc2` are one-line shell wrappers in `~/.local/bin`
(`CLAUDE_CONFIG_DIR=~/.claude-… exec claude "$@"`). The science ones are a
compiled launcher symlinked from `~/.claude-science/bin/`.

## Quick reference

```bash
# One-shot answer under the work account. ALWAYS -p, ALWAYS a timeout.
timeout 180 claude-work -p "your prompt"

# Structured output (session_id, total_cost_usd, usage):
timeout 180 claude-work -p "your prompt" --output-format json

# The delegated task needs tools? -p refuses tool use by default. Either
# pipe the data in and avoid tools entirely...
git log --oneline -50 | timeout 180 claude-acc2 -p "Summarize this git log"
# ...or grant exactly what it needs:
timeout 180 claude-work -p "summarize the git log" --allowedTools "Bash(git log:*)"
```

## Gotchas

- **`-p` is mandatory.** Without it the wrapper opens the interactive TUI and
  the Bash tool hangs until timeout. Always add `timeout`.
- **Tool permissions block headless.** A bare `claude-work -p` cannot run
  Bash/Edit/etc. — it will refuse. Pipe data in, or pass `--allowedTools "…"`
  / `--permission-mode acceptEdits` (or `bypassPermissions` for full trust).
- **Billing is per account.** Since 2026-06-15, headless `-p` spends *that*
  account's separate monthly headless credit pool (then full API rates), not
  its interactive 5h/7d subscription quota. So delegating does not dodge an
  interactive rate limit; it spreads the per-account headless pool.
- **Wrapper vs. alias.** The `~/.local/bin/claude-work` *script* works in the
  non-interactive Bash tool; the zsh *alias* does not. If a wrapper isn't
  found (or a cmux/PATH shim intercepts `claude`), fall back to the explicit
  form: `CLAUDE_CONFIG_DIR=~/.claude-work claude -p "…"`.
- **Trust dialog on a new workspace.** First use of another profile in a repo
  warns "workspace not trusted" and ignores that profile's `permissions.allow`.
  Fix: set `projects["<repo-dir>"].hasTrustDialogAccepted = true` in that
  profile's `.claude.json` (e.g. `~/.claude-acc2/.claude.json`), or run
  `claude-acc2` interactively once and accept.
- **No cheap attribution.** You can't confirm *which* account answered without
  spending a token on it; trust the config dir you selected.

## When NOT to use

- **Same-account parallelism / subtasks →** use the **Agent tool** (subagents).
  It shares context, spends no extra subscription, and needs no separate auth.
- Reach for account delegation only to (a) use a *different* subscription's
  quota, or (b) genuinely isolate auth/config/MCP.
