#!/usr/bin/env bash
# compact-snapshot.sh - PreCompact hook: snapshot git state to disk before a
# context compaction, so even an unprepared auto-compact leaves a trace.
#
# Mechanical only. It records what git already knows (branch, status, diff
# stat, recent commits, stashes). It does not commit, does not write memory or
# knowledge-base entries, and does not block the compaction: judgement stays
# with the model and the user (see ../SKILL.md).
#
# Contract (Claude Code hooks reference): receives JSON on stdin with
# session_id, transcript_path, cwd, hook_event_name, trigger ("manual"|"auto"),
# custom_instructions. stdout is not shown to the model. Exit code 2 would
# BLOCK the compaction, which on a reactive auto-compact fails the running
# request, so this script must always exit 0.

# No set -e: a failing sub-step must never turn into a blocking exit code.

# Read the payload from stdin without a command substitution. With fd 0 closed,
# `$(cat)` would read the substitution's own pipe and hang forever, which would
# stall the compaction this hook must never block. `read` fails instantly on a
# closed descriptor and the timeout bounds an interactive terminal.
INPUT=""
IFS= read -r -d '' -t 5 INPUT 2>/dev/null || true

json_field() {
    # $1 = field name; jq when available, crude grep fallback otherwise.
    if command -v jq >/dev/null 2>&1; then
        printf '%s' "$INPUT" | jq -r ".$1 // empty" 2>/dev/null
    else
        printf '%s' "$INPUT" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1
    fi
}

CWD="$(json_field cwd)"
TRIGGER="$(json_field trigger)"
SESSION_ID="$(json_field session_id)"
[ -n "$CWD" ] || CWD="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -n "$TRIGGER" ] || TRIGGER="unknown"

cd "$CWD" 2>/dev/null || exit 0

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
STAMP="$(date +%Y-%m-%d-%H%M%S)"

# Destination: the repo's scratch dir when the convention exists, otherwise a
# per-user fallback outside any repo. Never create docs/plans/.local/ here:
# whether a repo adopts the convention is a decision, not a side effect.
if [ -n "$REPO_ROOT" ] && [ -d "$REPO_ROOT/docs/plans/.local" ]; then
    DEST_DIR="$REPO_ROOT/docs/plans/.local"
else
    DEST_DIR="$HOME/.claude/compact-snapshots"
    mkdir -p "$DEST_DIR" 2>/dev/null || exit 0
fi
OUT="$DEST_DIR/$STAMP-compact-snapshot.md"

{
    echo "# Compact snapshot $STAMP"
    echo
    echo "- trigger: $TRIGGER"
    echo "- session: ${SESSION_ID:-unknown}"
    echo "- cwd: $CWD"
    if [ -n "$REPO_ROOT" ]; then
        echo "- repo: $REPO_ROOT"
        echo "- branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
        echo "- upstream: $(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || echo none)"
        echo
        echo "## git status"
        echo '```'
        git status --short --branch 2>/dev/null
        echo '```'
        echo
        echo "## Uncommitted changes (diff stat, unstaged + staged)"
        echo '```'
        git diff --stat 2>/dev/null
        git diff --stat --cached 2>/dev/null
        echo '```'
        echo
        echo "## Last 10 commits"
        echo '```'
        git log --oneline -10 2>/dev/null
        echo '```'
        echo
        echo "## Stashes"
        echo '```'
        git stash list 2>/dev/null
        echo '```'
    else
        echo "- repo: not a git repository"
    fi
    echo
    echo "Mechanical snapshot written by the compact-prep PreCompact hook."
    echo "Open items, reasons and decisions are NOT in here; see the session's"
    echo "own scratch notes in this directory, if any."
} > "$OUT" 2>/dev/null

exit 0
