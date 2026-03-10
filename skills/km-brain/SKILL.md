---
name: km-brain
description: Manages cross-repo knowledge brains as Git submodules. Add, list, or remove other knowledge repos to search across them with km-query. Only works in repos with a CONVENTIONS.md.
argument-hint: add <git-url> [name] | list | remove <name>
---

# Skill: km-brain

Manage knowledge brains in the current repo: $ARGUMENTS

## Prerequisites

- Verify this is a Git repo with a `CONVENTIONS.md` in the root. If not, tell the user this skill requires a knowledge repo.
- Parse the first word of `$ARGUMENTS` to determine the subcommand: `add`, `list`, or `remove`.
- If no subcommand or unrecognized subcommand, show usage:
  ```
  Usage: /km-brain add <git-url> [name]
         /km-brain list
         /km-brain remove <name>
  ```

## Subcommand: add

Add another knowledge brain as a Git submodule.

### Steps

1. **Parse arguments:**
   - Extract `<git-url>` (required) after `add`
   - Extract `[name]` (optional). If not provided, derive from URL: strip trailing `.git`, take the last path segment
   - Example: `https://gitlab.com/org/mko-brain.git` → name `mko-brain`

2. **Validate:**
   - Check that `brains/<name>` does not already exist
   - If it does, report: "Brain '<name>' already exists. Use `/km-brain list` to see registered brains."

3. **Create brains directory:**
   - `mkdir -p brains/`

4. **Add submodule:**
   - Run: `git submodule add <git-url> brains/<name>`
   - If this fails (no access, bad URL), report the error clearly and stop

5. **Validate brain:**
   - Check that `brains/<name>/CONVENTIONS.md` exists
   - If not: run `git rm -f brains/<name>` to undo, then report: "Not a valid knowledge brain — CONVENTIONS.md missing in <git-url>"

6. **Configure auto-recurse:**
   - Run: `git config submodule.recurse true`
   - This ensures `git pull` automatically updates all submodules

7. **Commit:**
   - Stage `.gitmodules` and `brains/<name>`
   - Commit message: `feat(brains): add <name>`

8. **Report:**
   - Brain name
   - Git URL
   - Pinned commit hash (`git -C brains/<name> rev-parse --short HEAD`)
   - Remind: "Use `/km-query @<name> <question>` to search this brain"

## Subcommand: list

List all registered knowledge brains.

### Steps

1. **Check for brains:**
   - If `brains/` directory does not exist or is empty (only `.gitkeep`), report: "No brains registered. Use `/km-brain add <git-url>` to add one."

2. **Enumerate brains:**
   - For each subdirectory in `brains/` that contains a `CONVENTIONS.md`:
     - **Name:** directory name
     - **URL:** from `.gitmodules` (`git config --file .gitmodules submodule.brains/<name>.url`)
     - **Commit:** `git -C brains/<name> rev-parse --short HEAD`
     - **Last updated:** `git -C brains/<name> log -1 --format="%ci" HEAD`

3. **Output as table:**

   | Brain | URL | Commit | Last Updated |
   |-------|-----|--------|--------------|
   | mko   | git@gitlab.com:... | a3f7c2d | 2026-03-09 14:30 |

## Subcommand: remove

Remove a registered knowledge brain.

### Steps

1. **Parse arguments:**
   - Extract `<name>` after `remove`
   - If not provided, report usage

2. **Validate:**
   - Check that `brains/<name>` exists
   - If not, report: "Brain '<name>' not found. Use `/km-brain list` to see registered brains."

3. **Confirm with user:**
   - Ask: "Remove brain '<name>'? This removes the submodule reference from this repo. The remote repository is not affected."

4. **Remove submodule:**
   - `git submodule deinit -f brains/<name>`
   - `git rm -f brains/<name>`
   - Remove leftover directory if present: `rm -rf .git/modules/brains/<name>`

5. **Commit:**
   - Commit message: `feat(brains): remove <name>`

6. **Report:** Confirm removal

## Rules

- All subcommands operate on the current repo, not on dotclaude itself
- Never modify the remote brain repository — brains are read-only from this repo's perspective
- Brain names must be unique within a repo
- Respond in the language the user used
