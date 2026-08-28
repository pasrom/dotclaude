# Commands for a repository publication audit

Contents:

1. [Term list](#1-term-list)
2. [History-wide content search](#2-history-wide-content-search)
3. [Authorship listing](#3-authorship-listing)
4. [Working tree and binaries](#4-working-tree-and-binaries)
5. [CI configuration](#5-ci-configuration)
6. [History rewrite](#6-history-rewrite)
7. [Post-rewrite verification](#7-post-rewrite-verification)
8. [Commit identity setup](#8-commit-identity-setup)
9. [Outside-in pass](#9-outside-in-pass)

All examples use invented placeholders (`examplecorp`, `globex`, `fleet-tool`,
`PROJ-`, `jane.doe@examplecorp.com`). Build the real term list per repo.

## 1. Term list

One file, one term per line, case-insensitive matching. Include:

- employer and customer names, full and partial (`examplecorp`, `excorp`),
- domains and email addresses (`examplecorp.com`, `@examplecorp`),
- internal tool and project names (`fleet-tool`, `proj-x9`),
- ticket prefixes (`PROJ-`),
- internal hostnames and machine usernames (`build01`, `/Users/jane`),
- colleague names and addresses,
- hardware fingerprints where relevant: device names, real MAC addresses,
  serial numbers.

```bash
TERMS=/tmp/terms.txt
```

## 2. History-wide content search

Every command below covers all refs, not just HEAD.

```bash
# All commit messages, subject and body
git log --all --format='%H %B' | grep -i -f "$TERMS"

# All diffs ever committed (content added or removed in any commit)
git log -p --all | grep -i -f "$TERMS"

# Every blob in every commit, by pathname context
git rev-list --all | while read -r c; do
  git grep -i -f "$TERMS" "$c" -- . && echo "^^ in commit $c"
done

# Every object in the database, reachable or not
git cat-file --batch-all-objects --batch | grep -ai -f "$TERMS"

# Dangling and unreachable objects (backup tags, reflog leftovers)
git fsck --unreachable --dangling --lost-found
git log -g --all --format='%H %gs %B' | grep -i -f "$TERMS"
```

A hit in an unreachable object still matters: `gc` has not pruned it yet and a
naive `cp -r` of the repo, or a push of a ref that still reaches it, publishes it.

## 3. Authorship listing

Check author AND committer. A rebase or cherry-pick stamps the committer field
with whoever ran it, so the committer often leaks when the author is clean.

```bash
git shortlog -sne --all                 # authors
git shortlog -sne --all --committer     # committers
git log --all --format='%an <%ae> | %cn <%ce>' | sort -u
```

Also read `.mailmap` if present: it can itself name the corporate identity.

## 4. Working tree and binaries

```bash
git ls-files | xargs grep -il -f "$TERMS"

# Files a stranger reads first, in full, not via grep:
# README*, LICENSE (copyright holder), the manifest (Cargo.toml authors,
# package.json author, pyproject.toml authors), CONTRIBUTING*, docs/.

# Binary and data files: captures, images, archives, fixtures
git ls-files -z | xargs -0 file | grep -vi text
strings tests/fixtures/capture.pcapng | grep -i -f "$TERMS"

# What would a careless `git add -A` publish?
git status --ignored --porcelain
```

Network captures deserve special attention: they embed real station names, MAC
addresses, and device identification records.

## 5. CI configuration

```bash
grep -ri -f "$TERMS" .github/ .gitlab-ci.yml .woodpecker/ 2>/dev/null

# Look manually for: secret names (secrets.EXAMPLECORP_TOKEN), self-hosted
# runner labels, internal package registries, internal URLs in comments.
```

After publication, download one completed job log and grep it too: logs print
paths, usernames, and hostnames that the workflow file does not contain.

## 6. History rewrite

Back up first, **outside the repository**, and record the tree hash for
verification. Not as an in-repo branch or tag: `filter-repo` rewrites all refs,
so an in-repo backup is either rewritten along with everything else or survives
as exactly the dangling objects the audit later flags. Backup tags left inside
the repo have been the leak in a real audit.

```bash
git bundle create ../pre-scrub.bundle --all    # delete after verification
git rev-parse HEAD^{tree} > /tmp/tree-before
```

Prefer `git filter-repo` (not filter-branch). It refuses to run on a clone with
history you might still need (use a fresh clone, or `--force` knowingly) and it
removes the `origin` remote on purpose. Fold each redaction into the commit that
introduced the text; never add a cleanup commit on top.

```bash
# Rewrite commit messages: expressions file has one `literal==>replacement` per line
git filter-repo --replace-message /tmp/msg-replacements.txt

# Rewrite blob content the same way
git filter-repo --replace-text /tmp/content-replacements.txt

# Fix identities
git filter-repo --mailmap /tmp/mailmap   # "New Name <new@email> <old@email>"
```

Then purge everything that still reaches the old objects:

```bash
# refs/original/* exists only after filter-branch; remote-tracking refs after either
git for-each-ref --format='%(refname)' refs/original refs/remotes | \
  xargs -n1 git update-ref -d
git reflog expire --expire=now --expire-unreachable=now --all
git gc --prune=now --aggressive
```

Delete the bundle backup once verification (next section) has passed. A backup
that outlives the cleanup is a copy of everything the cleanup removed.

**Do not fetch from the old remote after this.** A fetch re-imports the removed
objects. `git remote remove origin` (or repoint it to the new remote) before
anything else touches the repo.

## 7. Post-rewrite verification

```bash
# 1. Content unchanged (when only messages/identities were rewritten)
diff <(git rev-parse HEAD^{tree}) /tmp/tree-before

# 2. Old commits gone: must fail for every pre-rewrite SHA
git cat-file -t <old-sha>   # expect: "could not get object info"

# 3. Full-database term scan comes back empty
git cat-file --batch-all-objects --batch | grep -aci -f "$TERMS"   # expect 0

# 4. Outside the object database
grep -i -f "$TERMS" .git/config .git/packed-refs .git/FETCH_HEAD \
  .git/ORIG_HEAD .git/COMMIT_EDITMSG 2>/dev/null
git config --local --list          # user.email, remote URLs
ls .git/hooks .git/info
```

When content was edited (not just messages), verify the intended tree instead:
check out the final commit in a scratch clone and grep it, then spot-read the
edited files for corrupted sentences. A rewrite that rewraps text can leave a
dangling half-line.

## 8. Commit identity setup

Decided before the first commit. Conditional includes keep it automatic:

```ini
# ~/.gitconfig
[user]
    name = Jane Doe
    email = jane@personal.example
[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-work
[includeIf "hasconfig:remote.*.url:git@github.example.com:examplecorp/**"]
    path = ~/.gitconfig-work

# ~/.gitconfig-work
[user]
    email = jane.doe@examplecorp.com
```

Verify in the repo before the first commit: `git config user.email`. And pin it
locally in the published repo's clone as a guard:

```bash
git config user.email jane@personal.example
```

## 9. Outside-in pass

Work from a fresh clone and the host's public API only. Do not use the local
working copy: what the host serves is the artifact under test.

```bash
cd "$(mktemp -d)"
git clone https://github.com/janedoe/fleet-proto.git
cd fleet-proto
git log --all --format='%H%n%an <%ae>%n%cn <%ce>%n%B%n---'
git cat-file --batch-all-objects --batch | grep -aci -f "$TERMS"

# Old SHAs must not be retrievable from the host (expect 404/422)
gh api repos/janedoe/fleet-proto/commits/<old-sha>

# Surface beyond the git objects
gh api repos/janedoe/fleet-proto              # description, topics, homepage
gh api repos/janedoe/fleet-proto/branches     # bot branches pin old history
gh api repos/janedoe/fleet-proto/actions/runs # then read one full job log
gh api repos/janedoe/fleet-proto/events       # force pushes are public here
```

Then the part no command does: read the README and the prose as a stranger and
write down what can be inferred about who wrote this and why. Look at the
owner's profile and other public repos next to this one: thematic correlation
is a finding too. Classify each finding fixable or irreversible before acting;
a conspicuous post-publication rewrite can draw more attention than a low-grade
residue it removes.
