---
name: km-transcript
description: Processes a meeting transcript. Stores it, extracts decisions, action items, and key takeaways. Accepts raw transcript text or a file path as input. Only works in repos with a CONVENTIONS.md.
argument-hint: paste transcript or file path
---

# Skill: km-transcript

Process the following meeting transcript: $ARGUMENTS

## Prerequisites

Read `CONVENTIONS.md` in the repo root for frontmatter schema and folder structure.

## Steps

1. **Read transcript:**
   - If file path: read file
   - If text: process directly

2. **Extract metadata:**
   - Date (from content or today)
   - Participants (from speaker names)
   - Project assignment (from topics discussed)
   - Estimated duration (from timestamps if available)

3. **Create transcript file:**
   - Place in the appropriate project or topic folder per CONVENTIONS.md
   - Use `inbox/` if no clear assignment

4. **Frontmatter:** per CONVENTIONS.md schema with `type: transcript`

5. **Create structured summary** (at the top, BEFORE the raw transcript):

   - ## Summary — 3-5 sentences core content
   - ## Decisions — each with rationale
   - ## Action Items — checklist with who, what, when
   - ## Open Questions — unresolved items
   - ## Raw Transcript — original text, unmodified

6. **Create separate ADRs for significant decisions:**
   - For each significant decision found, ask: "Should I create a separate Decision Record for this?"
   - If yes: follow the /km-decision skill workflow

7. **Commit:** `docs(<scope>): add meeting transcript YYYY-MM-DD`

## Rules

- ALWAYS preserve the raw transcript, never shorten or rephrase
- Summary is extraction, not interpretation
- Ambiguities in transcript: mark as open question
- Action items without clear owner: explicitly mark as "unassigned"
