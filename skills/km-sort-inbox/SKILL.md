---
name: km-sort-inbox
description: Sorts all files in inbox/ into the correct folder structure. Analyzes each file's content and moves it to the appropriate location with correct frontmatter. Only works in repos with a CONVENTIONS.md.
disable-model-invocation: true
---

# Skill: km-sort-inbox

Sort all files in `inbox/` into their proper location in the repo.

## Prerequisites

Read `CONVENTIONS.md` in the repo root for folder structure and frontmatter schema.

## Steps

1. **Scan inbox:**
   - List all files in `inbox/`
   - If empty: report "Inbox is empty." and done

2. **For each file:**
   a. Read content
   b. Determine type per CONVENTIONS.md document types
   c. Assign to folder per CONVENTIONS.md folder structure
   d. Add or fix frontmatter if missing/incomplete
   e. Move file to target folder (`git mv`)

3. **Output summary:**
   - Table: file → new location → type
   - Files that couldn't be assigned stay in inbox/

4. **Commit:** `docs: sort inbox (<N> files moved)`

## Rules

- Never delete, only move
- When in doubt, leave in inbox/ and ask
- Do not overwrite existing frontmatter, only supplement
