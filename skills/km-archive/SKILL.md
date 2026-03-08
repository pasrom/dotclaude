---
name: km-archive
description: Manages document lifecycle transitions. Marks documents as superseded or obsolete, sets up supersession links between old and new documents. Only works in repos with a CONVENTIONS.md.
argument-hint: document to archive and optionally its replacement
---

# Skill: km-archive

Manage the lifecycle of: $ARGUMENTS

## Prerequisites

Read `CONVENTIONS.md` in the repo root for status lifecycle rules.

## Steps

1. **Identify the document(s):**
   - Parse $ARGUMENTS for the document to archive
   - Check if a replacement document is specified

2. **Determine transition type:**
   - **Superseded:** A newer document replaces this one → set `status: superseded` + `superseded_by:`
   - **Obsolete:** No replacement, just no longer relevant → set `status: obsolete`
   - If unclear, ask the user which applies

3. **For supersession:**
   a. Set old document: `status: superseded`, add `superseded_by: <new-file.md>`
   b. Set new document: add `supersedes: <old-file.md>` to frontmatter
   c. Verify both files exist

4. **For obsolescence:**
   a. Set document: `status: obsolete`
   b. Optionally add a note at the top explaining why

5. **Update cross-references:**
   - Search for files that link to the archived document
   - Report them so the user can decide whether to update the links

6. **Commit:** `docs(<scope>): archive <document> [superseded by <new>|obsolete]`

## Rules

- NEVER delete documents — only change status
- Always confirm with the user before changing status
- Documents with `status: superseded` or `status: obsolete` are kept for history
- AI filters them out by default in /km-query but can surface them on request
