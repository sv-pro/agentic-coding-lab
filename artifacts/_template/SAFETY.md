---
artifact: _template
kind: recipe
hosts: [claude-code]
tier: 1
enforced_by: world.yaml
reads: nothing — this is a skeleton, not a working artifact
blast_radius: none on its own; copying it without editing `world.yaml` gives an artifact a bound that was written for something else
verified: never
---

# Safety notes — template

*Copy this whole directory to `artifacts/<your-artifact>/` and rewrite every field
above. The frontmatter is checked by `scripts/check-artifacts.py`; the prose below is
checked by whoever reviews your pull request.*

## What this artifact reads

List every input that did not come from the person at the keyboard. File contents,
issue bodies, PR descriptions, web pages, MCP tool results, other agents' output.

Be exhaustive and be specific. This is the field that decides whether the artifact can
be steered by someone who is not your user, and it is the one people skip.

## What it can reach

The capabilities it needs, and what the worst version of using them looks like. Not
"it might do something bad" — name the concrete thing. *"It can run `git push`, so a
malformed instruction in a PR description could overwrite a branch."*

## What bounds it

Point at `enforced_by` and say, in one paragraph, what that file actually stops.
Then say what it doesn't. Every bound has an edge; the useful documentation is where
the edge is, not that a bound exists.

For this template, `world.yaml` is a real manifest and it does four things worth
copying:

| Proposed call | Verdict | Why |
|---|---|---|
| `Read` a file | `ALLOW` | declared, no side effect that leaves the machine |
| `Bash` running `rm -rf /tmp/x` | `ASK` → `Bash_destructive` | the kernel reclassifies destructive shell into its own action, which requires approval |
| `WebFetch` | `ABSENT` → `unknown_to_ontology` | **the manifest never declares it.** Not denied — nonexistent. Nothing to prompt about, nothing to argue past. |
| `Bash` running `curl …` with tainted context | `DENY` → `taint_invariant` | data from an untrusted channel is in play, so anything that leaves the machine is off |

The fourth row is the one that matters for real artifacts. The same `curl` from a clean
context is `ALLOW`. The verdict changes because of *where the data came from*, not
because of what the command looks like.

## How to re-run that table

```bash
./verify.sh /path/to/harness
```

Verified 2026-08-06 against `harness` 0.0.1 (both the debug and release builds of the
`ai2rules` checkout gave identical verdicts; manifest hash `8629c6be6c12`). This is a
local check, not a CI check — CI in this repo does not build the Rust harness.

## What is NOT bounded

The honest list. For this template: everything except the four rows above. It is a
skeleton with an example manifest attached, it has never been run as part of a real
workflow, and its `verified: never` says so.
