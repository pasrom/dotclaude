---
name: compact-prep
description: >-
  Prepares a long Claude Code session to survive a context compaction or a
  hard stop with nothing lost. Commits or records uncommitted work, writes
  open items into a gitignored scratch backlog, saves durable knowledge and
  decisions where a future session will find them, and ends with a short
  carry-over statement the user can paste into the continued session. Also
  states when to prepare (before context runs low, because preparing itself
  needs context) and what a compaction keeps versus loses. Not for ending
  work, which has its own checklist (push, report, hand over). Triggers on:
  prepare for compaction, compact prep, get compact ready, ready for
  compact, save everything before compacting, context almost full, running
  out of context, save state, handoff status, so you know where you were
  after compact, kompaktieren, Kompaktierung, fuers Compacten vorbereiten,
  mach dich compact ready, alles speichern fuers Compacting, compact ready
  machen, sichern vor dem Compact, Zwischenstand vor dem Compact sichern.
---

# Compact Prep

Prepare the session so that a context compaction, or a sudden end of the session,
loses nothing. Everything the continued session needs must be on disk, in the right
place, before the context is rewritten.

## When to run this

Run the ritual at the **first** of these, not the last:

- Claude Code shows its low-context warning (the "until auto-compact" notice).
- You are about to start something context-hungry: reading large logs, a multi-agent
  review fan-out, a long build-and-debug loop. Prepare first, then start it.
- The user asks for it, in any wording ("mach dich compact ready", "save everything").
- A natural milestone is reached late in a long session (PR opened, tests green).

**The trap that motivates this skill:** the preparation itself needs context. Writing
the scratch file, committing, and saving to memory all consume tokens. If you wait
until auto-compact is imminent, the preparation gets truncated along with everything
else, and the summary writes itself without your input. Early is cheap; late is
impossible.

## What a compaction keeps and what it loses

A compaction replaces the conversation with a machine-written summary and continues
the session from that summary.

Keeps, reliably:

- Everything on disk: files, git history, the scratch file you are about to write.
- What is loaded independently of the conversation: `CLAUDE.md`, auto-memory,
  settings. These are present again after the compaction without your help.

Loses, or may lose (the summary is lossy and you do not control what survives):

- Tool outputs: test results, error messages, command output, file contents you read.
- Exact values: numbers, URLs, ticket ids, commit shas, thresholds you derived.
- Rationale: why an approach was rejected, what was already tried and failed.
- Nuance in the user's instructions from early in the session.

Work with the conservative assumption: **anything that exists only in the
conversation is gone after compaction.** And there is no way to pin a region of the
context ("keep the earlier part, compact the rest" is not a thing); if a part must
survive verbatim, write it to a file.

## The ritual

In order. Skipping a step because "the summary will probably cover it" is the
failure mode this skill exists to prevent.

### 1. Commit, or record why not

- Every finished logical unit: commit it now (see the `git-workflow` skill for
  format). Do not invent a commit to bundle half-done work; that is worse than
  leaving it uncommitted.
- Every file that stays uncommitted: list it in the scratch file with one line of
  why (mid-refactor, experiment, blocked on X). An uncommitted file with no note is
  a file the continued session will misjudge: it cannot tell work-in-progress from
  leftover junk.

### 2. Open items into the scratch backlog

Every open item, deferred fix, and "do this tomorrow" goes into the gitignored
scratch file (convention below). Each item needs enough context to act on **without
the conversation**: what, where (file, function, PR), and why it is open. "Fix the
timeout thing" is useless after compaction; "raise `poll_timeout_s` in
`daemon/config.py`, 5 s races the sensor on cold boot, reproduced with
`pytest -k cold_boot`" is actionable.

### 3. Decisions and durable knowledge into the durable stores

Decisions made this session, with their rationale and rejected alternatives, go to
memory or the knowledge base (routing table below). The rationale is the part the
summary drops first and the part that prevents re-litigating the decision next week.

### 4. Carry-over statement

End with a short statement in chat, and mirror it at the top of the scratch file:

- Branch, commits ahead/pushed, working tree state, test status.
- What was achieved this session, in two or three lines.
- The immediate next step.
- Where the notes are (scratch file path, memory file, knowledge base page).

The chat copy is for the user: they verify nothing was missed, and they often paste
this exact block into the continued session as the first message. The file copy is
for you: the chat copy may not survive the compaction intact.

### Definition of done

- [ ] `git status` clean, or every dirty file listed in the scratch file with a reason.
- [ ] Open items in the scratch backlog, each actionable without the conversation.
- [ ] Decisions and their rationale in memory or the knowledge base.
- [ ] Carry-over statement given in chat and mirrored in the scratch file.
- [ ] Nothing essential exists only in the conversation.

## Where each kind of thing goes

The recurring mistake is writing session state into permanent knowledge: the
knowledge base gets polluted with "current branch is X" entries that are stale in a
day, and the actual open items get lost because nobody reads the knowledge base
looking for todos. Three destinations, three retention policies:

| What | Where | Why there |
| --- | --- | --- |
| Durable knowledge: facts that stay true beyond this task (how a subsystem works, a measured limit, a vendor quirk) | Knowledge base, if the user keeps one (`/km` here) | It is searched by topic later, independent of any session. |
| Anything a future session must not re-derive: project decisions, gotchas, "we tried X, it fails because Y" | Auto-memory (`MEMORY.md` and its topic files) | It is loaded automatically at session start, no lookup needed. |
| Session-scoped state: open items, next steps, branch status, findings not yet acted on | Gitignored scratch file in the repo | It is temporary by design and must not outlive the task or enter git history. |

One test: "is this still true and useful in a month, regardless of what happens to
this branch?" Yes: knowledge base or memory. No: scratch file.

## The scratch-file convention

- Directory: `docs/plans/.local/` inside the repository.
- Gitignore: the directory must be ignored; check, and add `docs/plans/.local/` to
  `.gitignore` if missing (that line itself is committed).
- File name: `YYYY-MM-DD-<topic>.md`, e.g. `2026-08-27-daemon-retry-backlog.md`.
  One file per task or per prep, date first so they sort. When the directory grows,
  optional subfolders `open/`, `research/`, `done/`, `deferred/` keep it navigable.
- Contents, top to bottom:
  1. State block: branch, commits ahead/pushed, working tree state, test status.
  2. Uncommitted files, each with its one-line reason.
  3. Open items, each actionable without the conversation (step 2 above).
  4. Pointers: PR/issue numbers, paths of files central to the task.
- Committed plans that are shared reference material live in `docs/plans/` proper;
  `.local/` is personal scratch only.

**Never reference `.local/` content from committed artifacts**: no `.local/` paths
or internal item ids in PR descriptions, commit messages, or code comments. Nobody
else can see those files, so the pointer looks like provenance and delivers nothing.
Inline the relevant content instead.

If the repository's own `CLAUDE.md` defines a different scratch location, that wins.

## Compact prep is not ending work

Two different rituals; do not run this one when the session is actually over.

| | Compact prep (this skill) | Ending work |
| --- | --- | --- |
| Situation | Session continues after compaction or resume | Task done or handed over |
| Commits | Commit finished units, record the rest | Everything committed |
| Push | Only what was going to be pushed anyway | Push, open/update the PR |
| Open items | Scratch backlog, for yourself | Report to the user, hand over |
| Audience of the summary | The continued session (and the user as courier) | The user and the team |

If the user says "we are done" or "mach fertig", they want the ending-work ritual:
push, report, hand over. If they say "compact ready" or "save everything", they want
this one. When unclear, ask; the difference is whether unpushed work is acceptable.

## Optional safety net: PreCompact hook

The mechanical part of step 1 and the state block can be automated so that even an
**unprepared auto-compact** leaves a trace on disk. See
[references/precompact-hook.md](references/precompact-hook.md) for the hook script
shipped with this skill, what it does and deliberately does not do, and the
`settings.json` snippet to register it. The hook is a safety net, not a replacement:
it captures git state mechanically, and no hook can write down your rationale.
