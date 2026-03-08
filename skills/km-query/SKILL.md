---
name: km-query
description: Semantically searches the entire knowledge repo and summarizes relevant information. Use when someone asks "What do we know about X?" or "What's the status of Y?". Only works in repos with a CONVENTIONS.md.
argument-hint: question or topic
---

# Skill: km-query

Answer the following question based on the knowledge repo: $ARGUMENTS

## Prerequisites

Read `CONVENTIONS.md` in the repo root to understand the repo structure and frontmatter schema.

## Search strategy (in this order)

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

## Response format

- **Summary** of found information (3-5 sentences)
- **Sources** with file paths (as markdown links)
- **Recency:** When was the information last updated?
- **Gaps:** What's missing or potentially outdated?
- **Related topics:** What else might be relevant?

Scale response complexity to query complexity — simple questions get concise answers.

## Rules

- Respond in the language the question was asked in
- Always cite source files
- If contradictions exist: prefer newer information, but mention the contradiction
- If nothing found: say so honestly, do not hallucinate
