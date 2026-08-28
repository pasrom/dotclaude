---
name: repo-publication-audit
description: 'Prepares a repository written inside a company for public release,
  or audits one that is already public. Sweeps all four provenance surfaces (working
  tree, full git history including every commit message, CI configuration, author
  and committer identities) for employer names, customer names, ticket keys, internal
  hostnames and machine paths. Redacts by keeping the technical fact and dropping
  the attribution, rewrites history with a backup and verification, and finishes
  with an outside-in audit of the published result. Use before making a repo public,
  before pushing company work to a personal remote, or to verify an already-public
  repo leaks nothing. Triggers on: publish repo, make public, open source a repo,
  publication audit, provenance audit, sanitize repo, scrub git history, leak check,
  history rewrite, filter-repo, commit identity, author email, Repo veroeffentlichen,
  oeffentlich machen, Historie bereinigen, Commits saeubern, Provenienz pruefen,
  Leak-Check.'
---

# Skill: repo-publication-audit

Prepare a repository written inside a company to be published under a different
identity, or audit one that is already public. The goal is that an outside reader,
given everything the host serves, cannot infer the employer, the customer, or the
internal project the code came from.

All commands referenced below are collected in
[references/commands.md](references/commands.md).

## Read this before touching anything

**Publishing is irreversible in the way that matters.** Rewriting history does not
unpublish what the host already served. GitHub keeps serving force-pushed-away
commits by SHA, records the force push in the public events feed, and forks and
caches may hold what was removed. After a leaky force push, deleting the
repository and creating a new one from the cleaned history can be the only
remaining fix. So the order is: audit and clean **first**, publish **once**, and
treat every pre-publication step as the last chance it actually is.

For a repo that is already public with a dirty history, do not reach for a force
push as the fix. Assume the old objects stay retrievable, weigh deleting and
recreating the repository, and treat anything already served as disclosed.

## The four surfaces

Auditing only the working tree is the standard mistake. A clean tree with a dirty
history is a common shape: the source files are fine while a commit message still
names the internal tool the code was extracted from.

| Surface | What leaks there | How to sweep it |
| --- | --- | --- |
| Working tree | README prose, LICENSE copyright holder, manifest author fields, comments, test fixtures, binary blobs (run `strings` over captures and firmware images), files `.gitignore` fails to exclude | `git ls-files` and read; grep the term list; check what `git add -A` would pick up |
| Full history | Commit messages (subject AND body), deleted file content in old diffs, dangling objects from backup tags and reflogs | `git log -p --all`, `git log --all --format=%B`, `git fsck --lost-found`, `git cat-file --batch-all-objects` |
| CI configuration | Secret names, self-hosted runner labels, internal package registries, internal URLs in workflow files, and the **log content** of completed runs (paths, usernames, hostnames) | Read every file under the CI directory; after publication, read one full job log |
| Authorship metadata | Work email in author or committer fields, a colleague's identity on a pair-programmed commit, real-name mapping to a corporate account | `git shortlog -sne --all` plus the committer variant; both fields, not just author |

## What counts as provenance

A name, obviously. But the expensive finds were subtler:

- A vendor-specific constant in a comment. A ticket key (the prefix names the
  tracker's owner). A build path like `/Users/jane/work/fleet-tool/`.
- An internal hostname, a bench device name, a real MAC address or serial number
  embedded in a test capture.
- A colleague's address in the author or committer field.
- Wording that only makes sense inside the company: "verified on the device",
  "the bench board", a count of lines compared against a private reference
  implementation. Each implies privileged access to something specific.
- A commit message citing a SHA that no longer exists after a rewrite. It
  dead-ends, but it tells a stranger the history was rebuilt, and before the
  rewrite it pointed at the leak.
- Uniform committer timestamps across spread author dates: a visible tell that
  history was rebased. Harmless on its own, conspicuous next to other residue.

Keyword search alone does not find the wording category. Read the README and the
prose of every source, test, and CI file and ask what a stranger concludes about
who wrote this and why.

## Redaction style: keep the fact, drop the attribution

Deleting the technical fact makes the code worse. Deleting the attribution costs
nothing.

| Before | After |
| --- | --- |
| `// FLEETCTL_ERR_TIMEOUT (0x2001), see PROJ-1234` | `// error 0x2001: transaction timeout` |
| `the fleet-tool valve bit refused by both channels` | `the same refused output write from both channels` |
| `spawned by fleet-tool as a subprocess` | `spawned by the consuming application as a subprocess` |
| `tested against build01.internal.example.com` | `tested against a local instance` |

Two edge cases worth knowing before they surprise you:

- **Do not redact public data.** A file may ship a complete public registry in
  which one row happens to name the employer. Trimming that one row creates a
  diffable arrow pointing exactly at what was removed, so shipping the public
  list whole is usually the safer choice.
- **Opaque identifiers.** Inside a company repo, a ticket key or internal commit
  SHA may be named as internal without pretending the reader can open it. In a
  repo published under a personal identity the calculus flips: the tie to the
  company is itself the secret, so the ticket prefix is a leak. Write the
  reasoning into the text instead of pointing at the record.

## The rewrite procedure

1. **Back up first, outside the repository** (a bundle or a second clone), and
   note the root tree hash of HEAD (`git rev-parse HEAD^{tree}`) so step 4 can
   prove the content did not change. Not an in-repo branch or tag: the rewrite
   rewrites those too, and a backup tag inside the repo keeps the
   unscrubbed objects reachable, which is exactly what the rewrite was meant to
   end.
2. **Fold redactions into the commit that introduced them**, via
   `git filter-repo` message and blob callbacks or an interactive-style rewrite.
   Never append a "remove company references" cleanup commit: its diff publishes
   exactly what it was meant to remove, permanently.
3. **Purge the leftovers.** The rewrite leaves the old objects reachable through
   backup refs, remote-tracking refs, old tags, and the reflog. Delete those
   refs, expire the reflog, and `git gc --prune=now`.
4. **Verify.** The new root tree hash equals the noted one when only messages and
   identities changed (or equals the intended tree after content edits).
   `git cat-file -t <old-sha>` fails for every pre-rewrite SHA.
   `git cat-file --batch-all-objects --batch | grep` over the full term list
   comes back empty. Also check outside the object database: `.git/config`,
   `packed-refs`, `FETCH_HEAD`, `ORIG_HEAD`, `COMMIT_EDITMSG`, hooks.
5. **Do not fetch from the old remote.** A fetch re-imports the objects you just
   removed. Remove or repoint the remote before anything else talks to it; push
   to the new remote only.

## Commit identity

Which identity goes on which remote is decided **before the first commit**, not
fixed afterwards: fixing it afterwards is a full history rewrite. Use conditional
git config includes so the work identity applies under the work directory or
work remotes and the personal identity everywhere else (snippet in
[references/commands.md](references/commands.md)). Check both author and
committer on every commit: a rebase or cherry-pick stamps the committer field
with whoever ran it.

## The outside-in pass (do not skip)

After publication, audit what the host actually serves, not the local clone.
This pass has surfaced findings after every earlier pass was declared clean:
stale SHA references in commit messages, rewrite tells in the timestamps, and a
correlation through the owner's other public repositories.

- Clone fresh into a temp directory and work only from that clone plus the
  host's public API. The local working copy is not the artifact under test.
- Confirm the old SHAs are gone from the host (fetching a removed commit by SHA
  must fail).
- Read every commit message and identity as served.
- Check the surface beyond the git objects: repo description and topics,
  releases and tags, bot-created branches and PRs, the full log of one completed
  CI run, and the owner's public profile as it reads next to this repo.
- Then read the whole thing as a stranger and ask what can be inferred. Classify
  every finding as fixable or already irreversible, and fix only the fixable:
  a conspicuous post-publication rewrite draws more attention than a LOW residue.

## Afterwards: guard rules

A clean history is re-dirtied by the next commit. Install the guards the same
day:

- A note in the repo's contributor docs or CLAUDE.md: no employer, customer, or
  internal-project references, in code or in commit messages, and which identity
  commits here.
- Local git config in the clone pinning the correct `user.email`.
- Re-run the term-list grep before any push that follows work done alongside
  internal repos.

## Situation to action

| Situation | Action |
| --- | --- |
| Repo about to go public the first time | Full four-surface audit, rewrite, verify, publish, outside-in pass |
| Repo already public, leak suspected | Outside-in pass first; treat what is served as disclosed; weigh delete-and-recreate over force push |
| One leaky commit message, not yet pushed | Fold the fix into that commit now; no cleanup commit |
| Wrong author email on unpushed commits | Rewrite now; unpushed history is the only cheap moment |
| Wrong author email on published commits | Decide whether the correlation is worth a visible rewrite; often it is already disclosed |
| New repo starting from company work | Decide commit identity before the first commit; start from a cleaned export, not a fork of the internal repo |
