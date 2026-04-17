---
name: session-summarize
description: Read and summarize past Claude Code sessions from their JSONL files. Use when the user wants to see what happened in an old session, decide whether to resume one, or get a token/cost breakdown. Also use before expensive /resume operations to check if resuming is worth it.
argument-hint: session-id, path to jsonl, or "list" to show recent sessions
---

# Skill: session-summarize

$ARGUMENTS

## What this skill does

Claude Code stores every session as a JSONL file under `~/.claude/projects/<project-hash>/<session-id>.jsonl`. Each line is an event (user prompt, assistant message, tool call, system reminder, token usage). This skill parses those files and produces a readable summary — **without** reloading the full context (which would cost a cache miss for long sessions).

## When to use

- User asks "what did I do yesterday in Claude Code?"
- User is deciding whether to `/resume` a big session (check cost first)
- User wants a cost/token breakdown of past work
- User wants to extract key decisions or files changed from an old session

## How to use

Run the helper script. It works on any JSONL session file:

```bash
python3 ~/.claude/skills/session-summarize/summarize.py [SESSION_ID_OR_PATH]
```

### Argument forms

- **no argument or `list`** → list the 10 most recent sessions across all projects with date, cwd, turn count, and token total
- **session ID** (e.g. `b9b247ad-32ee-...`) → search all project dirs for that ID and summarize
- **absolute path** to a `.jsonl` → summarize that file directly
- **`--project <name>`** → restrict search/list to one project dir (substring match on the encoded project path)
- **`--full`** → include every user prompt verbatim (default: truncate long prompts)

### Output

The script prints a markdown summary containing:
- Session metadata: start/end time, duration, project cwd, git branch, model(s) used, Claude Code version
- Turn count (user / assistant / tool calls)
- **Token & cost breakdown** — input, output, 5m cache writes, 1h cache writes, cache reads, plus an estimated cost in USD based on current Opus/Sonnet/Haiku pricing
- All user prompts (so you can see what was asked)
- Tool-call summary grouped by tool name with counts
- Files touched (from Edit/Write/Read tool calls)
- Last assistant message excerpt (tail of the session, useful for "where did I leave off")

## Typical flow

1. User: "Was lief gestern in der Session?"
2. Run `python3 ~/.claude/skills/session-summarize/summarize.py list` to find the session
3. Run it again with the session ID to get the full summary
4. Present the summary, and — if the user is thinking about resuming — mention the estimated resume cost (same as the last turn's `cache_creation + input` tokens if resumed after cache expiry)

## Notes on cost estimation

- Prices are hardcoded from the Anthropic pricing page (USD per million tokens). Update them in `summarize.py` if they change.
- Cache-read tokens are cheap (10% of base input price); cache-write tokens are 1.25× (5m) or 2× (1h) base.
- The reported cost is what the session **actually cost**, not what a resume would cost. A resume cost estimate is printed separately: it's the size of the final context × base input price (worst case, cold cache).

## Limitations

- Tool results in the JSONL reflect what was sent to the API (may be truncated for large outputs). Original file contents on disk are not stored.
- If the user ran with a custom `CLAUDE_CONFIG_DIR`, the script falls back to `$CLAUDE_CONFIG_DIR/projects/` — honor that env var.
