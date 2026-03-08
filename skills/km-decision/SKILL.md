---
name: km-decision
description: Creates an Architecture Decision Record (ADR) with numbered naming and structured format. Use when a technical decision needs to be documented. Only works in repos with a CONVENTIONS.md.
argument-hint: decision description
---

# Skill: km-decision

Create an Architecture Decision Record for: $ARGUMENTS

## Prerequisites

Read `CONVENTIONS.md` in the repo root for frontmatter schema and naming conventions.

## Steps

1. **Determine scope and folder:**
   - Follow folder rules in CONVENTIONS.md
   - If no decisions/ subfolder exists in the target area, create one

2. **Find next ADR number:**
   - Scan existing files with NNN- prefix in the target decisions/ folder
   - Next number = highest found + 1 (start at 001)

3. **Generate filename:** `NNN-kebab-case-topic.md`

4. **Create file with ADR template:**
   Frontmatter per CONVENTIONS.md schema with `type: decision`.

   Sections:
   - ## Context — why this decision is needed
   - ## Options — ### Option A, ### Option B (with pros/cons each)
   - ## Decision — which option was chosen
   - ## Rationale — why this option
   - ## Consequences — what follows from this decision

5. **Pre-fill context** from existing repo knowledge if available

6. **Commit:** `docs(<scope>): add ADR-NNN <topic>`

7. **Report back** with file path and ask if user wants to fill in details

## Rules

- Always use the ADR template structure
- Pre-fill what you can from existing knowledge
- Leave sections empty with placeholder text if unknown
- Link to related documents via the related: field
