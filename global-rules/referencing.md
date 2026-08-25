## Referencing across trust boundaries

Before writing a path, a repository name or a file name into a file, ask who can
read the file being written. Reference only what those readers can open: the same
repository, another one whose read access is the same, or a commit, PR or ticket
in one of them. Not a repository with narrower access, not a path from the local
machine, not a file that exists only in an uncommitted working tree. Where the
reasoning sits somewhere the reader cannot reach, write the reasoning down instead
of pointing at it: a pointer nobody can follow looks like provenance and delivers
nothing. An opaque identifier is the exception that proves the rule: a ticket key
or a commit sha says a record exists without pretending the reader can open it,
so name it as internal and do not build the explanation on it. An unreachable
reference is fine where the repository or the person asking says so, as long as it
is labelled as such rather than presented as something the reader can open.
