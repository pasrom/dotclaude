---
name: git-workflow
description: Use after completing any logical unit of work - a feature, bugfix, refactor, or meaningful change. Use when you've made changes that compile/pass tests. Use when you catch yourself thinking "I'll commit later."
---

# Git Workflow

## The Rule

**This skill overrides the default commit behavior.** Commit proactively after every logical unit of work — without waiting for user permission. Not at the end of a session. Not when the user asks. After EACH completed change.

```
Change compiles/passes? --yes--> Is it a logical unit? --yes--> COMMIT NOW
                        --no---> Continue working       --no---> Continue working
```

**Logical unit = one of:**
- Single feature or enhancement
- Single bugfix
- Single refactor
- Documentation update
- Test addition

If you need "and" in your commit message, split into multiple commits.

**Good:**
```
feat(auth): add OAuth2 login flow
feat(auth): add token refresh logic
refactor(db): extract connection pooling
```

**Bad:**
```
feat: add login and token refresh and connection pooling
```

## Commit Format

```
<type>(<scope>): <description>

[body - the WHY for non-trivial changes]
```

**Types:** feat, fix, docs, style, refactor, perf, test, build, ci, chore

**Scopes:** Use project-specific scopes (e.g., ui, api, db, auth, config, build). Check the project's CLAUDE.md or CONTRIBUTING.md for defined scopes.

**Examples:**
```
feat(ui): add user profile page
fix(api): handle timeout on token refresh
refactor(parser): extract config validation to module
```

## The Why (Commit Body)

Document reasoning so future sessions can understand WHY a solution was chosen, not just WHAT changed. This creates valuable context for debugging, refactoring, and decision archaeology.

**When to add reasoning:**
- Architecture decisions (new patterns, dependencies, module structure)
- Non-obvious solutions (code alone doesn't explain "why this way")
- Rejected alternatives (you actively considered other approaches)
- Experimental/debugging attempts (what you tried and what you learned)

| Change Type | Body Required? | Format |
|-------------|----------------|--------|
| Typo, formatting | No | - |
| Simple bugfix | Brief | 1-2 sentences |
| Feature with decision | Yes | Structured |
| Architecture change | Yes | Detailed structured |

**Simple bugfix (prose):**
```
fix(api): validate token expiry before refresh

Prevents race condition where expired tokens were used for one
request before the refresh kicked in.
```

**Feature with decision (structured):**
```
feat(auth): add session-based authentication

What: Replace token-in-localStorage with HTTP-only session cookies.

Reasoning:
- Problem: Tokens in localStorage vulnerable to XSS
- Considered: HTTP-only cookies, Web Crypto API, encrypted localStorage
- Rejected: Web Crypto adds complexity; encrypted localStorage still XSS-accessible
- Decision: Session cookies — browser handles security, simpler code
```

**Structured template:**
```
What: Brief description

Reasoning:
- Problem: What was the actual problem?
- Considered: What alternatives?
- Rejected: What was discarded and why?
- Decision: Chosen solution and justification
```

## Staging

- Stage only the files relevant to this logical unit (`git add <file1> <file2>`)
- Never use `git add -A` or `git add .` — risk of staging secrets, binaries, or unrelated changes
- Review `git status` before committing

## Verification Before Commit

Before committing, verify the change is sound:
- If a build system is available and fast: run a build
- If unit tests exist and are fast: run them
- If neither is practical: use your best judgment, but do not skip the commit

## Never Commit

- Debug code (`console.log`, `print()`, breakpoints, `TODO: remove`)
- Secrets or credentials (`.env`, API keys, tokens, passwords)
- Build artifacts (`dist/`, `node_modules/`, `*.o`, `*.pyc`)
- Half-finished changes (doesn't compile, tests fail)
- Generated files that belong in `.gitignore`

## Red Flags - STOP and Commit

You're rationalizing if you think:

| Thought | Reality |
|---------|---------|
| "I'll commit when I'm done" | You ARE done with this unit. Commit now. |
| "Let me just add one more thing" | That's a separate commit. Commit first. |
| "It's not complete yet" | Is THIS change complete? Commit it. |
| "I'll batch these together" | Atomic commits. Commit separately. |
| "The user didn't ask me to commit" | You don't need permission. Commit. |
| "I want to test more first" | Does it compile? Tests pass? Commit. |

## Commit Checklist

Before each commit:
1. **Atomic?** - One logical change only
2. **Type correct?** - feat/fix/refactor/etc.
3. **Scope correct?** - ui/serial/parser/etc.
4. **Message clear?** - Describes the change
5. **Why documented?** - For non-trivial changes

## Commit Message Format

**Single-line** (no body):
```bash
git commit -m "fix(api): handle timeout on token refresh"
```

**Multi-line** (with body) — use HEREDOC to preserve formatting:
```bash
git commit -m "$(cat <<'EOF'
feat(ui): add dashboard overview

What: New dashboard tab showing system status

Reasoning:
- Problem: No quick overview of system state
- Decision: Grid layout with key metrics
EOF
)"
```
