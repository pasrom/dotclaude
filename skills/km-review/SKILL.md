---
name: km-review
description: Submits a document for review by creating a branch and merge/pull request. Use for documents that need a second pair of eyes or formal approval (e.g., ISO 26262 compliance). Only works in repos with a CONVENTIONS.md.
argument-hint: document path or name
---

# Skill: km-review

Submit a document for review: $ARGUMENTS

## Prerequisites

Read `CONVENTIONS.md` in the repo root for review conventions if defined.

## Steps

1. **Identify the document:**
   - Parse $ARGUMENTS for document name or path
   - Search if needed, confirm with user

2. **Create review branch:**
   - Branch name: `review/<document-kebab-name>`
   - Based on current main branch

3. **Make review-ready changes (if any):**
   - Ensure frontmatter is complete
   - Set `status: draft` if not already set
   - Add any missing `related:` links

4. **Commit changes on branch:**
   - `docs(<scope>): prepare <document> for review`

5. **Push and create PR/MR:**
   - Push branch to remote
   - Create pull/merge request with:
     - Title: `Review: <document title>`
     - Body: Summary of what's being reviewed, key questions for reviewer
   - If `gh` is available: use `gh pr create`
   - If `glab` is available: use `glab mr create`

6. **Report back:**
   - Link to the PR/MR
   - Suggest reviewers if known from participants field

## Rules

- Never merge the PR/MR yourself
- Keep the review branch focused on one document
- If the document references others, mention them in the PR description
