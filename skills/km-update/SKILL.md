---
name: km-update
description: Updates an existing document in the knowledge repo. Finds the document, shows current content, applies changes, and commits. Only works in repos with a CONVENTIONS.md.
argument-hint: document name and changes to make
---

# Skill: km-update

Update a document in the knowledge repo: $ARGUMENTS

## Prerequisites

Read `CONVENTIONS.md` in the repo root for frontmatter schema.

## Steps

1. **Identify the target document:**
   - Parse $ARGUMENTS for document name, path, or topic
   - Search by filename, title, or content
   - If multiple matches: show candidates and ask user to pick

2. **Show current state:**
   - Display file path, title, status, and last modified date
   - Show relevant sections that will be affected

3. **Confirm with user:**
   - "I found [file]. I'll update [section/field]. Proceed?"

4. **Apply changes:**
   - Edit the document as requested
   - Update `date:` in frontmatter to today
   - If changes are substantial (new major section, changed conclusion):
     ask if a new document should be created instead

5. **Handle supersession:**
   - If creating a replacement document: set old doc to `status: superseded`
     and add `superseded_by:` field
   - Add `supersedes:` to the new document

6. **Commit:** `docs(<scope>): update <document> — <what changed>`

## Rules

- Always show what will change before committing
- Preserve existing content unless explicitly asked to remove
- Update the date field on every edit
- For major rewrites, prefer creating a new document over overwriting
