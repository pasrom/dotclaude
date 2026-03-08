---
name: km-weekly-summary
description: Generates a summary of all knowledge repo changes from the past week (or specified time range). Shows new documents, updates, decisions, and open items.
argument-hint: optional time range (e.g., "last 2 weeks")
---

# Skill: km-weekly-summary

Generate a summary of recent changes in the knowledge repo. Time range: $ARGUMENTS (default: last 7 days).

## Steps

1. **Determine time range:**
   - Default: last 7 days
   - Parse $ARGUMENTS for custom range (e.g., "last 2 weeks", "since 2026-03-01")

2. **Gather changes from git log:**
   - `git log --since="<date>" --name-status --pretty=format:"%h %s"`
   - Categorize: Added (A), Modified (M), Deleted (D), Renamed (R)

3. **Read frontmatter of changed files:**
   - Extract title, type, status, project, tags
   - Group by project or topic area

4. **Generate summary:**

   ### New Documents
   - List each new file with title, type, and one-line description

   ### Updated Documents
   - List each modified file with what changed (from commit messages)

   ### Decisions Made
   - List any files with `type: decision` that were added or changed to `status: accepted`

   ### Action Items (from transcripts)
   - Scan new transcripts for unchecked action items `- [ ]`

   ### Open Questions
   - Scan for "Open Questions" or "Offene Fragen" sections in new/modified files

5. **Report statistics:**
   - Total files changed
   - Breakdown by type and project
   - Contributors (from git log authors)

## Rules

- Only report on markdown content files (skip _index.md, CONVENTIONS.md, SKILL.md changes)
- Link to each mentioned file
- Keep the summary scannable — use tables and bullet points
- Respond in the language the user used
