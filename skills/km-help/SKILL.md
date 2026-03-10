---
name: km-help
description: Shows all available knowledge management skills with descriptions and examples. Use when someone asks what they can do or how to use the knowledge system.
---

# Skill: km-help

Show the user all available knowledge management skills.

## Prerequisites

Check if the current repo has a `CONVENTIONS.md`. If not, explain that KM skills require a knowledge repo with CONVENTIONS.md and offer to help set one up.

## Output

Present this overview:

### Create
| Skill | Purpose | Example |
|-------|---------|---------|
| `/km-ingest` | Save any content (note, mail, idea) | `/km-ingest We decided to use LTC6813 for cell monitoring` |
| `/km-decision` | Create a formal decision record (ADR) | `/km-decision Use FlatBuffers instead of Protobuf` |
| `/km-transcript` | Process a meeting transcript | `/km-transcript <paste transcript or file path>` |

### Read
| Skill | Purpose | Example |
|-------|---------|---------|
| `/km-query` | Search and summarize knowledge (supports `@brain`) | `/km-query What do we know about thermal management?` |
| `/km-weekly-summary` | Changes from the past week | `/km-weekly-summary` or `/km-weekly-summary last 2 weeks` |

### Update
| Skill | Purpose | Example |
|-------|---------|---------|
| `/km-update` | Modify an existing document | `/km-update sensor-fusion concept: add calibration values` |
| `/km-archive` | Mark document as superseded/obsolete | `/km-archive old-concept.md superseded by new-concept.md` |

### Organize
| Skill | Purpose | Example |
|-------|---------|---------|
| `/km-sort-inbox` | Sort all inbox files into proper folders | `/km-sort-inbox` |

### Review
| Skill | Purpose | Example |
|-------|---------|---------|
| `/km-review` | Submit document for review via PR/MR | `/km-review profinet-evaluation.md` |

### Brains
| Skill | Purpose | Example |
|-------|---------|---------|
| `/km-brain add` | Link another knowledge repo as Git submodule | `/km-brain add https://gitlab.com/org/team-brain.git` |
| `/km-brain list` | Show all linked brains with commit hashes | `/km-brain list` |
| `/km-brain remove` | Unlink a brain | `/km-brain remove team-brain` |

### Tips
- Use `@brain-name` in queries to search a specific brain: `/km-query @mko What's the status of thermal management?`
- Use `@all` to search all linked brains at once: `/km-query @all Zephyr RTOS`
- Brains auto-update when queried (if older than 15 minutes)
- You don't have to use slash commands — just describe what you need in natural language
- "Save this", "remember this", "file this" work the same as `/km-ingest`
- "What do we know about X?" works the same as `/km-query`
- "Update the BMS concept" works the same as `/km-update`
- All documents are stored as Markdown with YAML frontmatter in a Git repository
- See CONVENTIONS.md in the repo root for structure rules
