#!/usr/bin/env bash
# ----------------------------------------------------------------------
# review.sh — Local AI-assisted code review using Claude Code CLI
#
# Usage:
#   review.sh                  # Review current branch vs main
#   review.sh develop          # Review current branch vs develop
#   review.sh --mr 42          # Review GitLab MR !42
#   review.sh --mr 42 --post   # Review MR !42 and post as comment
#   review.sh --mr 42 --inline # Review MR !42 with inline line comments
#   review.sh --mr 42 --inline --dry-run  # Preview inline comments without posting
#   review.sh --post           # Review local branch + post to its MR
#   review.sh --list           # List open MRs
#
# Prerequisites:
#   - claude CLI installed and logged in (uses existing credentials)
#   - For --mr/--post: glab CLI installed and authenticated (glab auth login)
# ----------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PROMPT_FILE="$SCRIPT_DIR/review_prompt.md"
INLINE_PROMPT_FILE="$SCRIPT_DIR/review_prompt_inline.md"
INLINE_POSTER="$SCRIPT_DIR/post_inline_comments.py"

# -- Parse arguments ---------------------------------------------------
POST_TO_GITLAB=false
INLINE_COMMENTS=false
DRY_RUN=false
BASE_BRANCH="main"
MR_IID=""
LIST_MRS=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --post)      POST_TO_GITLAB=true; shift ;;
        --inline)    INLINE_COMMENTS=true; shift ;;
        --dry-run)   DRY_RUN=true; shift ;;
        --mr)        MR_IID="$2"; shift 2 ;;
        --list)      LIST_MRS=true; shift ;;
        *)           BASE_BRANCH="$1"; shift ;;
    esac
done

# -- List MRs and exit -------------------------------------------------
if [ "$LIST_MRS" = true ]; then
    if ! command -v glab &>/dev/null; then
        echo "Error: 'glab' CLI not found. Install with: brew install glab"
        exit 1
    fi
    echo "Open Merge Requests:"
    echo ""
    glab mr list
    exit 0
fi

# -- Sanity checks -----------------------------------------------------
if ! command -v claude &>/dev/null; then
    echo "Error: 'claude' CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

cd "$REPO_ROOT"

# -- Load review prompt ------------------------------------------------
if [ "$INLINE_COMMENTS" = true ]; then
    ACTIVE_PROMPT_FILE="$INLINE_PROMPT_FILE"
else
    ACTIVE_PROMPT_FILE="$PROMPT_FILE"
fi

if [ ! -f "$ACTIVE_PROMPT_FILE" ]; then
    if [ -f "${ACTIVE_PROMPT_FILE}.example" ]; then
        echo "No custom prompt found. Copying from ${ACTIVE_PROMPT_FILE}.example ..."
        cp "${ACTIVE_PROMPT_FILE}.example" "$ACTIVE_PROMPT_FILE"
        echo "Edit $ACTIVE_PROMPT_FILE to customize for your project."
        echo ""
    else
        echo "Error: Review prompt not found at $ACTIVE_PROMPT_FILE"
        exit 1
    fi
fi

REVIEW_PROMPT="$(cat "$ACTIVE_PROMPT_FILE")"

# -- Collect diff and context ------------------------------------------
if [ -n "$MR_IID" ]; then
    # ---- GitLab MR mode ----
    if ! command -v glab &>/dev/null; then
        echo "Error: 'glab' CLI not found. Install with: brew install glab"
        exit 1
    fi

    echo "Fetching MR !$MR_IID from GitLab ..."

    MR_INFO="$(glab mr view "$MR_IID" -F json)"
    MR_TITLE="$(echo "$MR_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")"
    MR_DESC="$(echo "$MR_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('description',''))")"
    MR_SOURCE="$(echo "$MR_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['source_branch'])")"
    MR_TARGET="$(echo "$MR_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['target_branch'])")"

    DIFF="$(glab mr diff "$MR_IID" --color=never)"

    if [ -z "$DIFF" ]; then
        echo "No changes found in MR !$MR_IID."
        exit 0
    fi

    FULL_PROMPT="$(cat <<EOF
$REVIEW_PROMPT

---

## Merge Request !$MR_IID
- **Title:** $MR_TITLE
- **Source:** $MR_SOURCE → **Target:** $MR_TARGET

### Description
$MR_DESC

## Diff
\`\`\`diff
$DIFF
\`\`\`
EOF
)"

    echo "MR !$MR_IID: $MR_TITLE"
    echo "  $MR_SOURCE → $MR_TARGET"
    echo ""

else
    # ---- Local branch mode ----
    CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    if [ "$CURRENT_BRANCH" = "$BASE_BRANCH" ]; then
        echo "Error: You are on '$BASE_BRANCH'. Switch to a feature branch first."
        exit 1
    fi

    MERGE_BASE="$(git merge-base "$BASE_BRANCH" HEAD)"
    DIFF="$(git diff "$MERGE_BASE"...HEAD)"
    STAT="$(git diff --stat "$MERGE_BASE"...HEAD)"
    LOG="$(git log --oneline "$MERGE_BASE"..HEAD)"

    if [ -z "$DIFF" ]; then
        echo "No changes found between '$BASE_BRANCH' and '$CURRENT_BRANCH'."
        exit 0
    fi

    FULL_PROMPT="$(cat <<EOF
$REVIEW_PROMPT

---

## Branch Info
- **Branch:** $CURRENT_BRANCH
- **Base:** $BASE_BRANCH
- **Commits:**
$LOG

## Changed Files
$STAT

## Diff
\`\`\`diff
$DIFF
\`\`\`
EOF
)"

    echo "Reviewing $CURRENT_BRANCH against $BASE_BRANCH ..."
    echo "Changed files:"
    echo "$STAT"
    echo ""
fi

# -- Run review --------------------------------------------------------
REVIEW_OUTPUT="$(echo "$FULL_PROMPT" | claude -p --print 2>&1)"

echo ""
echo "===== REVIEW RESULT ====="
echo ""
echo "$REVIEW_OUTPUT"

# -- Inline comments to GitLab -----------------------------------------
if [ "$INLINE_COMMENTS" = true ]; then
    if ! command -v glab &>/dev/null; then
        echo "Error: 'glab' CLI not found. Install with: brew install glab"
        exit 1
    fi

    # Determine MR IID
    if [ -z "$MR_IID" ]; then
        CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
        MR_IID="$(glab mr list --source-branch="$CURRENT_BRANCH" -F json \
            | python3 -c "import sys,json; mrs=json.load(sys.stdin); print(mrs[0]['iid'] if mrs else '')" 2>/dev/null || true)"
    fi

    if [ -z "$MR_IID" ]; then
        echo ""
        echo "Warning: No open MR found. Inline comments were NOT posted."
        exit 0
    fi

    echo ""
    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN — Inline comments that would be posted to MR !$MR_IID:"
        echo "$REVIEW_OUTPUT" | python3 "$INLINE_POSTER" "$MR_IID" --dry-run
    else
        echo "Posting inline comments to MR !$MR_IID ..."
        echo "$REVIEW_OUTPUT" | python3 "$INLINE_POSTER" "$MR_IID"
    fi
    exit 0
fi

# -- Optionally post to GitLab (single note) ---------------------------
if [ "$POST_TO_GITLAB" = true ]; then
    if ! command -v glab &>/dev/null; then
        echo "Error: 'glab' CLI not found. Install with: brew install glab"
        exit 1
    fi

    # Determine MR IID (from --mr flag or auto-detect from branch)
    if [ -z "$MR_IID" ]; then
        CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
        MR_IID="$(glab mr list --source-branch="$CURRENT_BRANCH" -F json \
            | python3 -c "import sys,json; mrs=json.load(sys.stdin); print(mrs[0]['iid'] if mrs else '')" 2>/dev/null || true)"
    fi

    if [ -z "$MR_IID" ]; then
        echo ""
        echo "Warning: No open MR found. Review was NOT posted to GitLab."
        exit 0
    fi

    # Post review as MR note
    glab mr note "$MR_IID" -m "$REVIEW_OUTPUT"

    echo ""
    echo "Review posted to MR !$MR_IID"
fi
