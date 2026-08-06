---
artifact: mcp-capability-census
kind: command
hosts: [claude-desktop]
tier: 0
reads: your client's MCP config file, and each server's `tools/list` response — tool names and descriptions authored by whoever wrote that server, not by you
blast_radius: it starts every stdio MCP server named in your config, so a hostile or compromised entry there runs its command with your user's privileges
verified: 2026-08-06
---

# Safety notes — mcp-capability-census

## Tier 0, and that is the honest answer

This artifact ships no enforcement of its own. It is a discovery tool: it reads a config,
asks each server what it can do, and writes a manifest. Nothing in this directory bounds
what it does while it does that.

It is worth being clear about why a repo built around governance is shipping a tier-0
artifact first. The tiers describe what an artifact enforces **on itself**, not how useful
it is for governance. This one's *output* is what makes tier 2 reachable — you cannot
declare a surface absent until you know what the surface contains — but that's a fact
about the manifest it writes, not about the script. Labelling it tier 1 because it is
governance-adjacent would be exactly the inflation the contract exists to stop.

## The dangerous output, which is not the obvious one

`census-world.yaml` **permits everything on purpose.** No transition policies, every
capability at every trust level, and every action declared `side_effect: Read` no matter
what the tool really does. Its verdicts are meaningless by construction. Only the audit
log it produces means anything.

> **If someone mistakes it for a starter manifest and ships it, they have deployed a
> manifest that allows every tool call unconditionally** — while the presence of a
> manifest makes the project look governed.

That is the worst outcome this artifact can cause, and it is worse than anything the
script itself does. The generated file opens with a `DO NOT SHIP THIS` banner for that
reason. The manifest you actually deploy is the one you derive *from the log* after the
census, and it is a different file.

## What it reads

- **Your client's MCP config** — server names, commands, arguments, and `env` blocks.
  `env` frequently holds API tokens. The script passes them through to the servers it
  spawns (it has to, or the servers won't start) and never writes them to the census
  world. The wrapped config it emits with `--emit-config` **does** contain them, because
  it is a copy of your config — treat that file exactly as you treat the original.
- **Each server's `tools/list` response.** Tool names and descriptions are authored by
  third parties. They are quoted on the way into the YAML rather than interpolated, and
  nothing in the response is executed. But they end up in a file you will read, so a
  server can put text of its choosing in front of you.

## What it can reach

It runs `command` + `args` verbatim from your config, with your environment, as your
user. That is the same thing your MCP client does every time it starts — the script is
not granting new authority — but it means **the config file is the trust boundary.** If
you have not read every entry in it, run `--dry-run` first: that prints every command
that would be spawned and spawns none.

## What bounds it

Nothing, mechanically — hence tier 0. What it does instead is refuse a few specific
foot-guns:

- It **never overwrites your live config.** `--emit-config` writes to a separate path and
  exits with an error if that path resolves to the original. You copy it over yourself.
- It **spawns nothing under `--dry-run`**, so the config can be audited before it runs.
- It **names what it skipped.** Entries with no `command` are out of scope for this
  gateway build, which wraps stdio only — not because the transport is unreachable, but
  because interposing needs a process to substitute and there isn't one. Route such a
  server through a stdio bridge and it comes back into scope. Disabled entries are
  skipped too. Both are printed as `unobserved:` lines, because a capability distribution
  with silent gaps is worse than one with stated gaps.
- It **terminates each server** after `tools/list`, with a kill after a 5s grace period.

## What is NOT bounded

- A malicious config entry. The script trusts your config completely, by design.
- A server that hangs during startup — `--timeout` (default 20s) bounds the wait for a
  *response*, not the process lifetime before termination.
- Anything about what happens after phase 0. Running the census itself puts a gateway in
  your live tool path; that is `harness mcp-gateway`'s behaviour, not this script's, and
  the gateway is **fail-closed** — a non-ALLOW verdict is never forwarded upstream. This
  is why the census world must permit everything. A mistake in that manifest doesn't
  corrupt your data; it stops your tools working.

## How it was verified

2026-08-06, against `harness` 0.0.1 and `harness mock-jira` (7 tools) on Linux:

| Check | Result |
|---|---|
| enumerate a stdio server | 7/7 tools discovered |
| skip a remote (`url`) server | reported `unobserved`, not silently dropped |
| skip a `disabled` entry | reported `unobserved` |
| `--dry-run` | listed the command, spawned nothing |
| refuse to overwrite the live config | error, non-zero exit |
| **generated world is observe-only** | gateway exposed **7/7, 0 ABSENT**; all 7 calls `ALLOW` |

The last row is the one that matters — the same server behind the *governed* demo
manifest exposes 4 of 7 with 3 `ABSENT`. The census world does not alter the surface.

**Not verified:** any real Claude Desktop installation, macOS or Windows paths, servers
other than `mock-jira`, or any server requiring authentication to answer `tools/list`.
