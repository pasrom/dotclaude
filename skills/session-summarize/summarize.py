#!/usr/bin/env python3
"""Summarize a Claude Code session JSONL file.

Usage:
    summarize.py                          # list recent sessions
    summarize.py list                     # same
    summarize.py <session-id>             # summarize by ID (searches all projects)
    summarize.py <path/to/file.jsonl>     # summarize by path
    summarize.py --project <substr> list  # list only matching project
    summarize.py <id_or_path> --full      # include full prompts, no truncation
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# USD per million tokens (base input / output). Cache multipliers applied below.
# Source: anthropic.com/pricing — update when prices change.
PRICING = {
    "opus":   {"in": 15.00, "out": 75.00},
    "sonnet": {"in":  3.00, "out": 15.00},
    "haiku":  {"in":  0.80, "out":  4.00},
}

CACHE_WRITE_5M = 1.25
CACHE_WRITE_1H = 2.00
CACHE_READ     = 0.10


def projects_dirs() -> list[Path]:
    """Return all plausible Claude Code project roots.

    Honors CLAUDE_CONFIG_DIR but also includes the default ~/.claude/projects
    so older sessions remain discoverable even when the config dir is overridden.
    """
    dirs: list[Path] = []
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    if env:
        dirs.append(Path(env) / "projects")
    dirs.append(Path.home() / ".claude" / "projects")
    seen: set[Path] = set()
    result: list[Path] = []
    for d in dirs:
        if d in seen or not d.is_dir():
            continue
        seen.add(d)
        result.append(d)
    return result


def projects_dir() -> Path:
    """Primary projects dir (for error messages only)."""
    roots = projects_dirs()
    return roots[0] if roots else Path.home() / ".claude" / "projects"


def model_family(model: str) -> str:
    m = model.lower()
    if "opus" in m:
        return "opus"
    if "haiku" in m:
        return "haiku"
    return "sonnet"  # default, also covers sonnet + unknowns


def cost_for(family: str, tokens: dict) -> float:
    p = PRICING[family]
    inp = tokens.get("input_tokens", 0)
    out = tokens.get("output_tokens", 0)
    c5m = tokens.get("ephemeral_5m_input_tokens", 0)
    c1h = tokens.get("ephemeral_1h_input_tokens", 0)
    cr  = tokens.get("cache_read_input_tokens", 0)
    return (
        inp * p["in"]
        + out * p["out"]
        + c5m * p["in"] * CACHE_WRITE_5M
        + c1h * p["in"] * CACHE_WRITE_1H
        + cr  * p["in"] * CACHE_READ
    ) / 1_000_000


def fmt_usd(x: float) -> str:
    return f"${x:,.4f}" if x < 1 else f"${x:,.2f}"


def fmt_tok(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def find_session(arg: str) -> Path | None:
    p = Path(arg)
    if p.is_file():
        return p
    # Treat as session ID — search across all known project roots
    for root in projects_dirs():
        for proj_dir in root.iterdir():
            if not proj_dir.is_dir():
                continue
            candidate = proj_dir / f"{arg}.jsonl"
            if candidate.is_file():
                return candidate
    return None


def load_session(path: Path) -> list[dict]:
    events = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def session_stats(events: list[dict]) -> dict:
    stats = {
        "user_turns": 0,
        "assistant_turns": 0,
        "tool_calls": Counter(),
        "files_touched": set(),
        "models": Counter(),
        "usage": defaultdict(int),
        "cost_total": 0.0,
        "start": None,
        "end": None,
        "cwd": None,
        "branch": None,
        "version": None,
        "user_prompts": [],
        "last_assistant_text": "",
        "last_context_tokens": 0,
    }

    for ev in events:
        t = ev.get("type")
        ts = ev.get("timestamp")
        if ts:
            try:
                dt = parse_ts(ts)
                stats["start"] = stats["start"] or dt
                stats["end"] = dt
            except Exception:
                pass

        if "cwd" in ev and not stats["cwd"]:
            stats["cwd"] = ev["cwd"]
        if "gitBranch" in ev and not stats["branch"]:
            stats["branch"] = ev["gitBranch"]
        if "version" in ev and not stats["version"]:
            stats["version"] = ev["version"]

        if t == "user":
            msg = ev.get("message") or {}
            content = msg.get("content")
            text = ""
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                parts = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        parts.append(c.get("text", ""))
                    elif isinstance(c, dict) and c.get("type") == "tool_result":
                        continue  # skip tool results, they're not user input
                text = "\n".join(p for p in parts if p)
            if text and not text.startswith("<") and "tool_use_id" not in str(content):
                stats["user_turns"] += 1
                stats["user_prompts"].append(text.strip())

        elif t == "assistant":
            stats["assistant_turns"] += 1
            msg = ev.get("message") or {}
            model = msg.get("model", "")
            if model:
                stats["models"][model] += 1

            # Token accounting
            usage = msg.get("usage") or {}
            cache_creation = usage.get("cache_creation") or {}
            tokens = {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
                "ephemeral_5m_input_tokens": cache_creation.get("ephemeral_5m_input_tokens", 0),
                "ephemeral_1h_input_tokens": cache_creation.get("ephemeral_1h_input_tokens", 0),
            }
            for k, v in tokens.items():
                stats["usage"][k] += v

            family = model_family(model)
            stats["cost_total"] += cost_for(family, tokens)

            # Track context size on this turn (= what a cold resume would pay)
            context_size = (
                tokens["input_tokens"]
                + tokens["cache_read_input_tokens"]
                + tokens["ephemeral_5m_input_tokens"]
                + tokens["ephemeral_1h_input_tokens"]
            )
            stats["last_context_tokens"] = max(stats["last_context_tokens"], context_size)

            # Tool calls + files touched
            content = msg.get("content") or []
            assistant_text_chunks = []
            if isinstance(content, list):
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") == "tool_use":
                        name = c.get("name", "?")
                        stats["tool_calls"][name] += 1
                        inp = c.get("input") or {}
                        for key in ("file_path", "path", "notebook_path"):
                            v = inp.get(key)
                            if isinstance(v, str):
                                stats["files_touched"].add(v)
                    elif c.get("type") == "text":
                        assistant_text_chunks.append(c.get("text", ""))
            if assistant_text_chunks:
                stats["last_assistant_text"] = "\n".join(assistant_text_chunks)

    return stats


def truncate(s: str, n: int = 200) -> str:
    s = s.strip()
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"


def render_summary(path: Path, stats: dict, full: bool) -> str:
    out: list[str] = []
    rel = path.relative_to(Path.home()) if str(path).startswith(str(Path.home())) else path
    out.append(f"# Session Summary: `{path.stem}`")
    out.append("")
    out.append(f"**File:** `~/{rel}`")
    if stats["start"] and stats["end"]:
        dur = stats["end"] - stats["start"]
        out.append(f"**Time:** {stats['start'].astimezone().strftime('%Y-%m-%d %H:%M')} → {stats['end'].astimezone().strftime('%H:%M')} ({dur})")
    if stats["cwd"]:
        out.append(f"**cwd:** `{stats['cwd']}`")
    if stats["branch"]:
        out.append(f"**branch:** `{stats['branch']}`")
    if stats["version"]:
        out.append(f"**Claude Code:** {stats['version']}")
    if stats["models"]:
        models_str = ", ".join(f"{m} ({c}×)" for m, c in stats["models"].most_common())
        out.append(f"**Models:** {models_str}")
    out.append("")
    out.append(f"**Turns:** {stats['user_turns']} user / {stats['assistant_turns']} assistant")
    out.append("")

    # Token breakdown
    u = stats["usage"]
    out.append("## Token & Cost Breakdown")
    out.append("")
    out.append(f"- Input (uncached):        {fmt_tok(u['input_tokens'])}")
    out.append(f"- Output:                  {fmt_tok(u['output_tokens'])}")
    out.append(f"- Cache write (5 min):     {fmt_tok(u['ephemeral_5m_input_tokens'])}")
    out.append(f"- Cache write (1 hour):    {fmt_tok(u['ephemeral_1h_input_tokens'])}")
    out.append(f"- Cache read:              {fmt_tok(u['cache_read_input_tokens'])}")
    out.append(f"- **Estimated cost:**      {fmt_usd(stats['cost_total'])}")
    out.append("")

    if stats["last_context_tokens"]:
        # Cold-resume estimate = context size × base input price of most-used model
        top_model = stats["models"].most_common(1)[0][0] if stats["models"] else "sonnet"
        family = model_family(top_model)
        cold_cost = stats["last_context_tokens"] * PRICING[family]["in"] / 1_000_000
        out.append(f"**Peak context:** {fmt_tok(stats['last_context_tokens'])} tokens — cold resume on {family} ≈ {fmt_usd(cold_cost)}")
        out.append("")

    # Tool calls
    if stats["tool_calls"]:
        out.append("## Tool Usage")
        out.append("")
        for name, count in stats["tool_calls"].most_common():
            out.append(f"- {name}: {count}×")
        out.append("")

    # Files touched
    if stats["files_touched"]:
        out.append(f"## Files Touched ({len(stats['files_touched'])})")
        out.append("")
        for f in sorted(stats["files_touched"]):
            out.append(f"- `{f}`")
        out.append("")

    # User prompts
    if stats["user_prompts"]:
        out.append("## User Prompts")
        out.append("")
        for i, p in enumerate(stats["user_prompts"], 1):
            text = p if full else truncate(p, 300)
            out.append(f"{i}. {text}")
        out.append("")

    # Last assistant text
    if stats["last_assistant_text"]:
        out.append("## Last Assistant Message (tail)")
        out.append("")
        tail = stats["last_assistant_text"].strip()
        if not full and len(tail) > 1000:
            tail = tail[-1000:]
            tail = "…" + tail
        out.append(tail)
        out.append("")

    return "\n".join(out)


def list_sessions(project_filter: str | None, limit: int = 10) -> str:
    roots = projects_dirs()
    if not roots:
        return f"No projects dir found (tried CLAUDE_CONFIG_DIR and ~/.claude)"

    rows = []
    for base in roots:
        for proj_dir in base.iterdir():
            if not proj_dir.is_dir():
                continue
            if project_filter and project_filter not in proj_dir.name:
                continue
            for jf in proj_dir.glob("*.jsonl"):
                try:
                    mtime = datetime.fromtimestamp(jf.stat().st_mtime, tz=timezone.utc)
                    size = jf.stat().st_size
                except OSError:
                    continue
                rows.append((mtime, proj_dir.name, jf.stem, size, jf))

    rows.sort(reverse=True)
    rows = rows[:limit]

    if not rows:
        return "No sessions found."

    out = ["# Recent Sessions", ""]
    out.append("| Date | Project | Session ID | Size |")
    out.append("|------|---------|------------|------|")
    for mtime, proj, sid, size, _ in rows:
        date = mtime.astimezone().strftime("%Y-%m-%d %H:%M")
        proj_short = proj.replace("-Users-roman-", "~/").replace("-", "/")
        size_str = f"{size/1024:.0f}k" if size < 1_000_000 else f"{size/1_000_000:.1f}M"
        out.append(f"| {date} | `{proj_short}` | `{sid}` | {size_str} |")
    out.append("")
    out.append("Run `summarize.py <session-id>` for a full summary.")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    args = argv[1:]
    full = False
    if "--full" in args:
        args.remove("--full")
        full = True

    project_filter = None
    if "--project" in args:
        i = args.index("--project")
        if i + 1 < len(args):
            project_filter = args[i + 1]
            del args[i:i + 2]

    if not args or args[0] == "list":
        print(list_sessions(project_filter))
        return 0

    target = args[0]
    path = find_session(target)
    if not path:
        print(f"Session not found: {target}", file=sys.stderr)
        print(f"Searched under: {projects_dir()}", file=sys.stderr)
        return 1

    events = load_session(path)
    if not events:
        print(f"No events parsed from {path}", file=sys.stderr)
        return 1

    stats = session_stats(events)
    print(render_summary(path, stats, full))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
