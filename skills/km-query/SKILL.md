---
name: km-query
description: Semantically searches the knowledge repo (and optionally linked brains) and summarizes relevant information. Use @brain-name to target a specific brain, @all for all brains, or no prefix for the current repo only. Only works in repos with a CONVENTIONS.md.
argument-hint: [@brain | @all] question or topic
---

# Skill: km-query

Answer the following question based on the knowledge repo: $ARGUMENTS

## Argument parsing

Parse `$ARGUMENTS` for brain selectors:

1. Extract all tokens starting with `@` from the beginning of the arguments
2. The remaining text after `@` tokens is the query
3. Rules:
   - `@brain-name` → search only the named brain(s) in `brains/<name>/`
   - `@all` → search all brains in `brains/` plus the current repo
   - Multiple selectors: `@brain1 @brain2 query text` → search those specific brains
   - No `@` prefix → search only the current repo (original behavior, fully backward-compatible)

## Brain resolution and auto-update

Skip this section entirely if no `@` selectors are present.

For each target brain:

1. **Locate:** Check that `brains/<name>/` exists and contains a `CONVENTIONS.md`. If not, report: "Brain '<name>' not found. Use `/km-brain list` to see registered brains." and skip it.

2. **Freshness check and auto-update:**
   - Check when the brain was last fetched: `stat -f %m .git/modules/brains/<name>/FETCH_HEAD` (macOS) or `stat -c %Y` (Linux)
   - If the last fetch was **more than 15 minutes ago**, update:
     - Run: `git submodule update --remote brains/<name>`
     - If the update fails (offline, no access): use the local state silently, do not abort
   - If the last fetch was recent enough: use the local state directly

3. **Record commit hash:** `git -C brains/<name> rev-parse --short HEAD` — needed for source attribution later

## Prerequisites

For each target repo (current repo and/or resolved brains):
- Read its `CONVENTIONS.md` to understand the repo structure and frontmatter schema.

## Search strategy (per target repo, in this order)

Execute the following search for each target repo. When searching a brain, all file paths are relative to `brains/<name>/`.

1. **Frontmatter scan:**
   - Grep for relevant tags in YAML headers
   - Filter: `status: accepted` or `status: draft` (NOT `obsolete` or `superseded`, unless explicitly asked about history)

2. **Folder navigation:**
   - Identify relevant folders per CONVENTIONS.md structure
   - Read `_index.md` files for folder overviews

3. **Heading scan:**
   - Scan H1/H2 of all potentially relevant files
   - Only read files with matching headings in full

4. **Full-text search:**
   - Only if above steps don't yield enough results
   - Grep with keywords from the question

5. **Cross-references:**
   - Follow `related:` and `supersedes:` fields in found files
   - Include related projects/topics
   - Cross-references only within the same repo (do not follow links across brains)

## Response format

- **Summary** of found information (3-5 sentences)
- **Sources** with file paths and brain attribution:
  - Current repo sources: normal markdown links (as before)
  - Brain sources: `[brain-name@abc1234] path/to/file.md` (brain name + short commit hash + path within brain)
- **Recency:** When was the information last updated?
- **Gaps:** What's missing or potentially outdated?
- **Related topics:** What else might be relevant?
- If results come from multiple repos, group sources by repo

Scale response complexity to query complexity — simple questions get concise answers.

## Rules

- Respond in the language the question was asked in
- Always cite source files
- When querying brains, always include `[brain-name@commit]` attribution for every brain source
- If contradictions exist between repos: prefer the current repo over brains, prefer newer information, and mention the contradiction
- If a brain is inaccessible or has no CONVENTIONS.md: skip it silently
- If nothing found: say so honestly, do not hallucinate
