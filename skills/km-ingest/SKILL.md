---
name: km-ingest
description: Takes any content (note, mail, idea, link, raw text) and stores it as Markdown with YAML frontmatter in the appropriate folder. Uses inbox/ for unsorted content. Only works in repos with a CONVENTIONS.md.
argument-hint: content or file path
---

# Skill: km-ingest

Ingest the following content into the knowledge repo: $ARGUMENTS

## Prerequisites

Read `CONVENTIONS.md` in the repo root. If it doesn't exist, tell the user this skill requires a knowledge repo with CONVENTIONS.md.

## Steps

1. **Analyze content:**
   - Determine type: note, decision, concept, transcript, artifact
   - Identify project (check folder names)
   - Identify topic
   - If unclear: use `inbox/`

   Heuristics for type detection:
   - Contains a decision with rationale → decision (use /km-decision instead)
   - Raw meeting content with speakers/timestamps → transcript (use /km-transcript instead)
   - Structured technical analysis or design → concept
   - If unclear → default to note

2. **Generate frontmatter** per CONVENTIONS.md schema

3. **Determine target folder:**
   - Follow the folder-to-topic mapping defined in CONVENTIONS.md
   - If no matching folder exists → `inbox/`

4. **Filename:**
   - Notes and transcripts: `YYYY-MM-DD-kebab-case-title.md`
   - Concepts: `kebab-case-title.md` (no date prefix)
   - Decisions: use /km-decision skill instead
   - Follow naming rules in CONVENTIONS.md

5. **Write file:**
   - Frontmatter + content
   - Preserve raw content, do not rephrase
   - Only minimal formatting (headings where useful)

6. **Confirm with user:**
   - Show proposed: file path, type, and tags
   - Ask "Shall I save this?" before writing and committing

7. **Commit:** `docs(<scope>): add <short description>`

8. **Report back:** file path and brief summary
