#!/usr/bin/env python3
"""Post inline review comments to a GitLab MR via glab api.

Usage:
    echo '<json>' | python3 post_inline_comments.py <MR_IID> [--dry-run]

The JSON input must have the structure:
{
    "summary": "Overall review summary",
    "comments": [
        {"file": "path/to/file.c", "line": 42, "severity": "critical", "body": "..."},
        ...
    ]
}
"""
import json
import re
import subprocess
import sys


SEVERITY_EMOJI = {
    "critical": "\u2757",  # ❗
    "warning": "\u26A0\uFE0F",  # ⚠️
    "suggestion": "\U0001F4A1",  # 💡
}


def extract_json(text: str) -> dict | None:
    """Extract a JSON object from text that may contain non-JSON content.

    Claude sometimes outputs thinking/reasoning text before the JSON.
    This function finds the outermost {...} block containing "summary".
    """
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*\n?", "", text)

    # Find all top-level JSON objects by matching balanced braces
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                candidate = text[start : i + 1]
                try:
                    obj = json.loads(candidate)
                    if isinstance(obj, dict) and "summary" in obj:
                        return obj
                except json.JSONDecodeError:
                    continue
    return None


def get_mr_versions(mr_iid: str) -> dict:
    """Get MR diff versions to obtain the SHAs needed for position-based comments."""
    result = subprocess.run(
        ["glab", "api", f"projects/:id/merge_requests/{mr_iid}/versions"],
        capture_output=True, text=True, check=True,
    )
    versions = json.loads(result.stdout)
    if not versions:
        print("Error: No diff versions found for this MR.", file=sys.stderr)
        sys.exit(1)
    # Most recent version is first
    return versions[0]


def post_inline_comment(mr_iid: str, version: dict, comment: dict) -> bool:
    """Post a single inline comment as a new discussion."""
    severity = comment.get("severity", "suggestion")
    emoji = SEVERITY_EMOJI.get(severity, "")
    label = severity.upper()
    body = f"{emoji} **[{label}]** {comment['body']}"

    payload = json.dumps({
        "body": body,
        "position": {
            "base_sha": version["base_commit_sha"],
            "start_sha": version["start_commit_sha"],
            "head_sha": version["head_commit_sha"],
            "position_type": "text",
            "new_path": comment["file"],
            "old_path": comment["file"],
            "new_line": comment["line"],
        },
    })

    result = subprocess.run(
        ["glab", "api", f"projects/:id/merge_requests/{mr_iid}/discussions",
         "-X", "POST", "--input", "-"],
        input=payload, capture_output=True, text=True,
    )

    if result.returncode != 0:
        print(f"  Failed: {comment['file']}:{comment['line']} — {result.stderr.strip()}",
              file=sys.stderr)
        return False
    return True


def post_summary(mr_iid: str, summary: str, stats: dict) -> None:
    """Post the overall summary as a regular MR note."""
    header = "## AI Code Review"
    stat_line = (f"{stats['critical']} critical, "
                 f"{stats['warning']} warnings, "
                 f"{stats['suggestion']} suggestions")
    body = f"{header}\n\n{summary}\n\n**Inline comments:** {stat_line}"

    subprocess.run(
        ["glab", "mr", "note", str(mr_iid), "-m", body],
        check=True,
    )


def print_dry_run(summary: str, comments: list) -> None:
    """Pretty-print what would be posted without actually posting."""
    stats = {"critical": 0, "warning": 0, "suggestion": 0}

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(summary)
    print()

    if not comments:
        print("No inline comments.")
        return

    print("=" * 60)
    print(f"INLINE COMMENTS ({len(comments)})")
    print("=" * 60)
    for c in comments:
        severity = c.get("severity", "suggestion")
        stats[severity] = stats.get(severity, 0) + 1
        emoji = SEVERITY_EMOJI.get(severity, "")
        print(f"\n{emoji} [{severity.upper()}] {c['file']}:{c['line']}")
        print(f"  {c['body']}")

    print()
    print("-" * 60)
    print(f"Total: {stats['critical']} critical, {stats['warning']} warnings, "
          f"{stats['suggestion']} suggestions")
    print("(dry run — nothing was posted)")


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: echo '<json>' | {sys.argv[0]} <MR_IID> [--dry-run]", file=sys.stderr)
        sys.exit(1)

    mr_iid = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    raw = sys.stdin.read().strip()

    # Extract JSON from Claude's output — it may contain thinking text before/after
    review = extract_json(raw)
    if review is None:
        print("Error: Could not find valid JSON in Claude's output.", file=sys.stderr)
        print(f"Raw output:\n{raw[:500]}", file=sys.stderr)
        sys.exit(1)

    comments = review.get("comments", [])
    summary = review.get("summary", "No summary provided.")

    if dry_run:
        print_dry_run(summary, comments)
        return

    if not comments:
        print("No inline comments to post.")
        post_summary(mr_iid, summary, {"critical": 0, "warning": 0, "suggestion": 0})
        print(f"Summary posted to MR !{mr_iid}")
        return

    # Get MR diff version for positioning
    print(f"Fetching MR !{mr_iid} diff metadata ...")
    version = get_mr_versions(mr_iid)

    # Post each inline comment
    stats = {"critical": 0, "warning": 0, "suggestion": 0}
    posted = 0
    for c in comments:
        severity = c.get("severity", "suggestion")
        stats[severity] = stats.get(severity, 0) + 1
        print(f"  Posting [{severity}] {c['file']}:{c['line']} ...", end=" ")
        if post_inline_comment(mr_iid, version, c):
            print("OK")
            posted += 1
        else:
            print("FAILED")

    # Post summary as regular note
    post_summary(mr_iid, summary, stats)

    print(f"\nDone: {posted}/{len(comments)} inline comments + summary posted to MR !{mr_iid}")


if __name__ == "__main__":
    main()
