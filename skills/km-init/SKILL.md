---
name: km-init
description: Bootstraps a new knowledge management repository. Creates CONVENTIONS.md, folder structure, and _index.md files. Run this once to enable all km-* skills in any Git repo.
disable-model-invocation: true
---

# Skill: km-init

Initialize this repository as a knowledge management repo.

## Steps

1. **Check prerequisites:**
   - Verify this is a Git repo (`git rev-parse --git-dir`)
   - Check if CONVENTIONS.md already exists → if yes, ask if user wants to reset or update

2. **Gather configuration from user:**
   Ask these questions:
   - What is this repo about? (one-line description)
   - What are the main topic areas? (e.g., "backend, frontend, infrastructure" or "bms, embedded, safety")
   - Who is the default author? (initials or name)
   - Primary language for content? (English/German/other)
   - Do you want a projects/ folder for time-bound work? (yes/no)

3. **Create folder structure:**
   Based on the topic areas, create:
   ```
   <repo>/
   ├── CONVENTIONS.md
   ├── inbox/           # always
   │   └── .gitkeep
   ├── topics/          # always
   │   └── .gitkeep
   ├── <topic-1>/       # per topic area
   │   └── _index.md
   ├── <topic-2>/
   │   └── _index.md
   └── projects/        # if requested
       └── _index.md
   ```

4. **Generate CONVENTIONS.md:**
   Create a CONVENTIONS.md tailored to the user's answers. Include:

   - **Frontmatter Schema** with the user's default author
   - **Document Types:** note, decision, concept, transcript, artifact, summary
   - **Status Lifecycle:** draft → accepted → superseded | obsolete
   - **Folder Structure** based on the topic areas
   - **Naming Conventions:** kebab-case.md, YYYY-MM-DD-kebab-case.md, NNN-kebab-case.md
   - **Folder Navigation:** _index.md per folder
   - **Language** per user preference
   - **Cross-References:** relative links + related: field
   - **Obsolescence:** never delete, use status
   - **Git Workflow:** Conventional Commits

5. **Generate _index.md for each folder:**
   Each with frontmatter (title, type: artifact, date, author, status: accepted, tags)
   and a brief description of the folder's purpose.

6. **Update existing files (optional):**
   If the repo already has markdown files, ask:
   "Do you want me to add YAML frontmatter to existing .md files?"
   If yes, scan and add frontmatter to all .md files.

7. **Commit:** `feat: initialize knowledge management structure`

8. **Report back:**
   Show created structure and list available km-* skills (invoke /km-help content).

## Rules

- Never overwrite existing CONVENTIONS.md without confirmation
- Keep the generated structure minimal — users can always add more folders later
- All generated content in the user's chosen language
