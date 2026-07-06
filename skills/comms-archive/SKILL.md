---
name: comms-archive
description: Archive Outlook emails and Teams messages as a daily summary in the knowledge base. Requires Microsoft 365 MCP connector.
argument-hint: "[days back, e.g. '2' for last 2 days] (default: today)"
---

# Skill: comms-archive

$ARGUMENTS

## What This Does

Fetches Outlook emails and Teams messages via the Microsoft 365 MCP connector, filters out noise, clusters by topic, and writes a daily summary to a `comms/` folder in the current repository.

## Prerequisites

- Microsoft 365 MCP connector configured (for `outlook_email_search`, `chat_message_search`, `read_resource`)
- Repository with a `CONVENTIONS.md` (for frontmatter schema and author initials)

## Setup (first run)

If `comms/` does not exist yet:

**Show this privacy notice first and ask for explicit confirmation before proceeding:**

> **Privacy Notice:** This skill fetches emails and chat messages from Microsoft 365 and sends their content to an LLM API for summarization. This means personal data (names, email addresses, message content) of you, your colleagues, and external contacts will be processed by the LLM provider.
>
> Before using this skill, ensure:
> - Your organization permits sending workplace communications to third-party AI services
> - A Data Processing Agreement (DPA) with the LLM provider is in place if required
> - You have informed relevant stakeholders (e.g., DPO, works council) if applicable
>
> The generated summaries (containing names and decisions) will be stored in this git repository. Ensure the repository access controls are appropriate.

If the user confirms, proceed:

1. Create `comms/` and `comms/sync/`
2. Create `comms/_index.md` with frontmatter describing the folder purpose
3. Create `comms/sync/processed-ids.json` with empty arrays:
   ```json
   {"last_sync": null, "processed_emails": [], "processed_teams_messages": []}
   ```
4. Ask the user which noise filters to apply (offer defaults below) and save them to `comms/sync/filter-rules.json`

## Steps

### 1. Determine date range

- No argument: last 24 hours
- Numeric argument N: last N days
- Use `afterDateTime` accordingly

### 2. Load configuration

- Read author initials from `CONVENTIONS.md` (the default `author:` field)
- Read noise filters from `comms/sync/filter-rules.json` (if exists, otherwise use defaults)
- Read processed IDs from `comms/sync/processed-ids.json`

### 3. Fetch communications

- Outlook: `outlook_email_search` with `afterDateTime`, `limit: 50`
- Teams: `chat_message_search` with `query: '*'`, `afterDateTime`, `limit: 50`

If a source returns exactly `limit` (50) results, more likely exist for that window — note the truncation in the summary so a busy day isn't silently under-archived.

### 4. Deduplicate

Skip messages whose IDs already appear in `processed-ids.json`. This file grows unbounded; when writing it back, drop IDs older than ~30 days to keep it small.

### 5. Filter noise

Apply rules from `comms/sync/filter-rules.json`. Default rules if no config exists:

```json
{
  "exclude_senders": [],
  "exclude_subject_contains": [
    "invited to share this calendar",
    "[MASSENMAIL]"
  ],
  "exclude_subject_starts_with": [
    "Accepted:",
    "Declined:"
  ],
  "exclude_sender_and_subject": [
    {"sender": "noreply", "subject": "Verifying"}
  ],
  "exclude_sender_domains": []
}
```

Suggest additional filters to the user based on what looks like noise in the fetched messages.

### 6. Read relevant emails

For each relevant email, use `read_resource` to get full body. Strip HTML signatures, legal disclaimers, and meeting join links.

### 7. Cluster and write summary

Group messages by topic/theme. Write to `comms/YYYY-MM-DD-daily.md`.

Frontmatter (use author initials from CONVENTIONS.md):
```yaml
---
title: "Daily Communications Summary YYYY-MM-DD"
type: summary
date: YYYY-MM-DD
author: <initials from CONVENTIONS.md>
status: accepted
tags: [daily-summary, <topic-tags>]
---
```

Section format:
```markdown
## Topic Name (HIGH PRIORITY if critical)

**Sources:** Teams chat with X, Email from Y

Key facts, decisions, context.

### Action Items
- Who does what

### Upcoming Meetings
- Date/time and purpose
```

Low-value items go in `## Misc / Low Priority` at the bottom.

### 8. Update tracking

Add newly processed IDs to `comms/sync/processed-ids.json`. Update `last_sync`.

### 9. Confirm and commit

Show the user a brief overview of the topics found. Ask for confirmation before writing. Commit with: `docs(comms): daily summary YYYY-MM-DD`

## Rules

- Respond and write summaries in the user's language (detect from conversation)
- Be concise, capture decisions, action items, deadlines
- Flag HIGH PRIORITY items prominently
- If no new messages: notify user, do not create an empty file
- Never include email signatures, legal disclaimers, or meeting join links
- Always confirm before committing
