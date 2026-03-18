#!/usr/bin/env bash
# ----------------------------------------------------------------------
# install.sh — Set up dotclaude skills, tools, and shell aliases
# ----------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
FORCE=false
for arg in "$@"; do
    case "$arg" in
        --force|-f) FORCE=true ;;
        --dir=*)    CLAUDE_DIR="${arg#--dir=}" ;;
    esac
done

# -- Colors ------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
skip() { echo -e "  ${YELLOW}→${NC} $1 (already exists)"; }

# -- Install skills (symlink) -----------------------------------------
echo "Installing skills..."

SKILLS_DIR="$CLAUDE_DIR/skills"
mkdir -p "$SKILLS_DIR"

for skill_dir in "$SCRIPT_DIR"/skills/*/; do
    skill_name="$(basename "$skill_dir")"
    target="$SKILLS_DIR/$skill_name"
    if [ "$FORCE" = true ] && { [ -L "$target" ] || [ -d "$target" ]; }; then
        rm -rf "$target"
    fi
    if [ -L "$target" ] || [ -d "$target" ]; then
        skip "skills/$skill_name"
    else
        ln -s "$skill_dir" "$target"
        ok "skills/$skill_name"
    fi
done

# -- Install shell alias ----------------------------------------------
echo ""
echo "Installing aliases..."

# Detect shell config file
if [ -n "${ZSH_VERSION:-}" ] || [ "$(basename "$SHELL")" = "zsh" ]; then
    RC_FILE="$HOME/.zshrc"
else
    RC_FILE="$HOME/.bashrc"
fi

ALIAS_LINE="alias review='$SCRIPT_DIR/tools/ai-mr-review/review.sh'"

if grep -qF "alias review=" "$RC_FILE" 2>/dev/null; then
    if [ "$FORCE" = true ]; then
        # Remove old alias block and re-add
        sed -i '' '/# dotclaude — AI MR review/d; /alias review=/d' "$RC_FILE"
        echo "" >> "$RC_FILE"
        echo "# dotclaude — AI MR review" >> "$RC_FILE"
        echo "$ALIAS_LINE" >> "$RC_FILE"
        ok "review alias updated in $RC_FILE"
    else
        skip "review alias in $RC_FILE"
    fi
else
    echo "" >> "$RC_FILE"
    echo "# dotclaude — AI MR review" >> "$RC_FILE"
    echo "$ALIAS_LINE" >> "$RC_FILE"
    ok "review alias added to $RC_FILE"
fi

# -- Register additionalDirectories in settings.json ------------------
echo ""
echo "Registering additionalDirectories..."

SETTINGS_FILE="$CLAUDE_DIR/settings.json"

if ! command -v jq &>/dev/null; then
    echo -e "  ${YELLOW}✗${NC} jq not found — skipping additionalDirectories update"
else
    # Create minimal settings.json if missing
    if [ ! -f "$SETTINGS_FILE" ]; then
        echo '{"permissions":{}}' > "$SETTINGS_FILE"
    fi

    UPDATED=$(jq \
        --arg dir "$SCRIPT_DIR" \
        '.permissions.additionalDirectories = ((.permissions.additionalDirectories // []) + [$dir] | unique)' \
        "$SETTINGS_FILE")

    echo "$UPDATED" > "$SETTINGS_FILE"
    ok "added $SCRIPT_DIR to permissions.additionalDirectories"
fi

# -- Create/update global CLAUDE.md -----------------------------------
echo ""
echo "Updating global CLAUDE.md..."

CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
MARKER="# dotclaude"

if [ -f "$CLAUDE_MD" ] && grep -qF "$MARKER" "$CLAUDE_MD"; then
    skip "dotclaude section in CLAUDE.md"
else
    cat >> "$CLAUDE_MD" << EOF

# dotclaude
Skills and tools are installed from: $SCRIPT_DIR
Use /km-help to see all available knowledge management skills.
EOF
    ok "dotclaude section added to CLAUDE.md"
fi

# -- Check prerequisites ----------------------------------------------
echo ""
echo "Checking prerequisites..."

for cmd in claude glab python3; do
    if command -v "$cmd" &>/dev/null; then
        ok "$cmd"
    else
        echo -e "  ${YELLOW}✗${NC} $cmd not found"
    fi
done

echo ""
echo "Done. Restart your shell or run: source $RC_FILE"
