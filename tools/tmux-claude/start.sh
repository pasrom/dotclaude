#!/usr/bin/env bash
# start.sh — Start Claude Code sessions in multiple repos via tmux
#
# Usage:
#   ./start.sh                  # uses repos.txt in same directory
#   ./start.sh ~/my-repos.txt   # uses custom file
#
# Repo file format (one path per line, # comments and blank lines ignored):
#   ~/git/dotclaude
#   ~/git/my-project
#   $HOME/work/other-repo

set -euo pipefail

SESSION_NAME="claude-work"
DELAY_BETWEEN=2  # seconds between launches to avoid API hammering

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOS_FILE="${1:-$SCRIPT_DIR/repos.txt}"

# --- Read repos from file ---
if [[ ! -f "$REPOS_FILE" ]]; then
    echo "Error: Repo file not found: $REPOS_FILE"
    echo "Create one with repo paths (one per line), e.g.:"
    echo "  ~/git/my-project"
    echo "  \$HOME/work/other-repo"
    exit 1
fi

REPOS=()
while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    # Expand ~ and $HOME safely (no eval)
    line="${line/#\~/$HOME}"
    line="${line//\$HOME/$HOME}"
    REPOS+=("$line")
done < "$REPOS_FILE"

if [[ ${#REPOS[@]} -eq 0 ]]; then
    echo "Error: No repos found in $REPOS_FILE"
    exit 1
fi

# --- Validate repos ---
VALID_REPOS=()
for REPO in "${REPOS[@]}"; do
    if [[ -d "$REPO" ]]; then
        VALID_REPOS+=("$REPO")
    else
        echo "Warning: $REPO does not exist, skipping."
    fi
done

if [[ ${#VALID_REPOS[@]} -eq 0 ]]; then
    echo "Error: No valid repos found."
    exit 1
fi

echo "Starting Claude in ${#VALID_REPOS[@]} repos..."

# --- Kill existing session if present ---
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

# --- Create first window ---
# Target the returned pane id (not "$SESSION:$NAME") so two repos with the same
# basename don't send keystrokes to an ambiguous window.
FIRST_REPO="${VALID_REPOS[0]}"
FIRST_NAME=$(basename "$FIRST_REPO")
FIRST_PANE=$(tmux new-session -d -s "$SESSION_NAME" -n "$FIRST_NAME" -c "$FIRST_REPO" -P -F '#{pane_id}')
tmux send-keys -t "$FIRST_PANE" "claude" Enter
echo "  Started: $FIRST_NAME"

# --- Create remaining windows ---
for ((i=1; i<${#VALID_REPOS[@]}; i++)); do
    REPO="${VALID_REPOS[$i]}"
    WIN_NAME=$(basename "$REPO")
    PANE=$(tmux new-window -t "$SESSION_NAME" -n "$WIN_NAME" -c "$REPO" -P -F '#{pane_id}')
    tmux send-keys -t "$PANE" "claude" Enter
    echo "  Started: $WIN_NAME"
    sleep "$DELAY_BETWEEN"
done

# --- tmux settings ---
# mouse on: scroll = tmux buffer, arrow keys = Claude Code navigation.
# Scope to this session so we don't flip the user's global tmux setting.
tmux set-option -t "$SESSION_NAME" mouse on

# --- Attach ---
# Select by window name, not index 0 — users with base-index 1 have no window 0.
tmux select-window -t "$SESSION_NAME:$FIRST_NAME"
echo ""
echo "Attaching to tmux session '$SESSION_NAME' (${#VALID_REPOS[@]} windows)"
echo "  Switch windows: Ctrl-b n/p    List: Ctrl-b w    Detach: Ctrl-b d"
tmux attach -t "$SESSION_NAME"
