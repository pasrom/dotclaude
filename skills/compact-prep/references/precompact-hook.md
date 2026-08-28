# PreCompact snapshot hook

Contents: [What it does](#what-it-does) | [What it deliberately does not do](#what-it-deliberately-does-not-do) | [Install](#install) | [Verify](#verify) | [Hook contract notes](#hook-contract-notes)

Claude Code fires a `PreCompact` hook right before a context compaction, for both
the manual `/compact` command (matcher `manual`) and automatic compaction under
context pressure (matcher `auto`). This skill ships
[`scripts/compact-snapshot.sh`](../scripts/compact-snapshot.sh) for that event, so
that even a compaction nobody prepared for leaves the git state on disk.

## What it does

On every compaction it writes one markdown file,
`<timestamp>-compact-snapshot.md`, containing:

- trigger (`manual` or `auto`), session id, working directory,
- branch, upstream, `git status --short --branch`,
- diff stat of unstaged and staged changes,
- the last 10 commits, and the stash list.

Destination: `docs/plans/.local/` in the current repository **if that directory
already exists** (the scratch convention from SKILL.md), otherwise
`~/.claude/compact-snapshots/`. It never creates `docs/plans/.local/` itself:
adopting the convention in a repo is a decision, not a hook side effect.

After a compaction, check that directory for the newest snapshot before trusting
your summary's picture of the working tree.

## What it deliberately does not do

- **No judgement.** It does not commit, does not write memory or knowledge-base
  entries, and cannot record open items, reasons, or rationale. That is the ritual
  in SKILL.md; the hook only guarantees the mechanical git facts survive.
- **No blocking.** Exit code 2 would cancel the compaction, and on a reactive
  auto-compact that fails the running request. The script always exits 0.
- **No reminder to the model.** PreCompact stdout is not injected into the
  context (verified against the hooks reference), so the hook cannot tell the
  session to run the ritual. Running the ritual early remains the model's job.

## Install

The skill directory is already symlinked to `~/.claude/skills/compact-prep/` by
dotclaude's `install.sh`. Two manual steps remain, because the installer manages
skills, not hooks:

1. Make the script executable (once, in this repo):

   ```bash
   chmod +x ~/.claude/skills/compact-prep/scripts/compact-snapshot.sh
   ```

2. Register the hook in `~/.claude/settings.json` (or the project's
   `.claude/settings.json`). No `matcher` key means it fires for both manual and
   auto compaction, which is what you want:

   ```json
   {
     "hooks": {
       "PreCompact": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "\"$HOME\"/.claude/skills/compact-prep/scripts/compact-snapshot.sh"
             }
           ]
         }
       ]
     }
   }
   ```

   Merge into an existing `hooks` object if one is already there; do not replace
   other entries.

## Verify

In any long-ish session run `/compact`, then check for a fresh
`*-compact-snapshot.md` in `docs/plans/.local/` (or `~/.claude/compact-snapshots/`).
`claude --debug` prints hook execution if it does not appear.

## The stdin read, and its limit

The hook reads its payload with a bounded `read` rather than a command
substitution. With file descriptor 0 closed, `$(cat)` reads the substitution's
own pipe and never returns, which would stall the compaction this hook must
never block.

The bound is five seconds, and it introduces a limit the original did not have:
a payload still arriving after five seconds is lost. On the bash 3.2 that ships
with macOS the partial input is discarded entirely, bash 4 and later keep the
prefix. Either way the script falls back to its defaults and exits zero, so a
slow writer costs detail in the snapshot, never the session. A real payload is
a few hundred bytes delivered at once, so the bound is not reached in practice.

## Hook contract notes

Verified against the Claude Code hooks reference (code.claude.com/docs/en/hooks)
on Claude Code v2.1.247:

- stdin JSON fields: `session_id`, `transcript_path`, `cwd`, `hook_event_name`,
  `trigger` (`"manual"` or `"auto"`), `custom_instructions` (manual only).
- stdout is observational; no PreCompact output reaches the model's context.
- Exit code 2 or `{"decision": "block"}` blocks the compaction. This script never
  uses either.
- There is no earlier "context pressure" hook: PreCompact fires when compaction
  is already starting. That is why it can only be a safety net, and why the
  SKILL.md trigger ("prepare at the first low-context warning") stands.
