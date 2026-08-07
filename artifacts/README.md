# artifacts/

Things you can copy into a project: skills, plugins, subagents, hooks, slash commands,
MCP server configs, prompt scaffolds.

| Artifact | Kind | Tier | Verified |
|---|---|---|---|
| [`claude-code-tool-log`](claude-code-tool-log/) | hook | 0 — unenforced | 2026-08-06 |
| [`governability-probe`](governability-probe/) | recipe | 0 — unenforced | 2026-08-07 |
| [`mcp-capability-census`](mcp-capability-census/) | command | 0 — unenforced | 2026-08-06 |

`_template/` is the skeleton, not an artifact.

## Adding one

```bash
cp -r artifacts/_template artifacts/my-artifact
$EDITOR artifacts/my-artifact/SAFETY.md      # rewrite every frontmatter field
./scripts/check-artifacts.py                 # must pass before you open a PR
```

## The contract, in short

Each directory carries a `README.md` (what it does, for someone who's never seen this
repo) and a `SAFETY.md` (what it reads, what it can reach, what bounds it, and what
doesn't). The `SAFETY.md` frontmatter is machine-checked:

```yaml
---
artifact: my-artifact          # must match the directory name
kind: skill                    # skill | plugin | subagent | hook | command | mcp-server | recipe
hosts: [claude-code]
tier: 1                        # 0 unenforced · 1 overlay · 2 structural
enforced_by: world.yaml        # required at tier >= 1, must exist in this directory
reads: issue titles and bodies from the configured tracker
blast_radius: can run any shell command the developer can, so a crafted issue body reaches the shell
verified: 2026-08-06           # ISO date someone ran it, or `never`
---
```

`scripts/check-artifacts.py` rejects a tier claim with no file behind it, a `tier: 0`
that still names an enforcer, an out-of-directory `enforced_by`, an unknown `kind`, an
empty `reads` or `blast_radius`, a name that doesn't match its directory, and a
`verified: never` whose README doesn't open with `> **Unverified.**`. Run
`--self-test` to see it reject each of those on demand.

What it cannot check is whether your `reads:` field is *honest*. That's the review.

## Naming

Directory names are lowercase and hyphenated, and describe the job rather than the
mechanism: `triage-inbound-issues`, not `issue-mcp-wrapper`. Somebody browsing this
list is looking for a task they have, not an implementation they want.
