# mcp-capability-census

**Find out what your AI client can actually do, then write it down.**

If you use MCP servers with Claude Desktop, you have a tool surface you have probably
never seen in full. This enumerates it — every server, every tool — and writes a manifest
that declares the whole thing, so you can then *record* a week of real usage without
changing what the agent is able to do.

That recording is the point. Once you know which tools got used, and which never did, you
can write a real manifest that removes the rest.

## Why this step exists at all

`harness mcp-gateway` shapes `tools/list` down to what its manifest declares. Anything the
manifest misses becomes `ABSENT` — it disappears from the client entirely. That's the
feature; it's how a capability stops existing rather than merely being denied.

But it means you can't just point the gateway at your servers and watch. A manifest that
doesn't name a tool doesn't observe that tool, it *removes* it. So phase 0 is: ask every
server what it has, and declare all of it.

You can't observe a surface you haven't declared.

## Use it

```bash
./census_enumerate.py --dry-run     # print every command that would be spawned. Spawns nothing.
./census_enumerate.py               # enumerate, write census-world.yaml
./census_enumerate.py --emit-config --harness ~/.local/bin/harness
```

Python 3, stdlib only. It finds Claude Desktop's config automatically on macOS, Windows
and Linux; `--config PATH` takes any JSON file with an `mcpServers` map.

**Run `--dry-run` first.** This script starts every stdio MCP server in your config. That's
the same thing your client does at launch, but you should see the list before it happens.

### What you get

- **`census-world.yaml`** — a manifest declaring every discovered tool, permitting all of
  it. This is a measuring instrument. **Do not ship it as a starter manifest** — it allows
  everything, while making a project look governed. Read [`SAFETY.md`](SAFETY.md) on this
  before you do anything else with it.
- **`claude_desktop_config.census.json`** (with `--emit-config`) — your config with each
  stdio server wrapped in `harness mcp-gateway`, logging to a JSONL audit file. Review it,
  then copy it over your real config yourself. The script will not do that for you.

Restart the client, work normally for a week, and the audit log fills up:

```json
{"ts_ms":1786034110838,"tool":"jira_get_issue","action":"jira_get_issue","decision":"ALLOW",
 "rule":"","manifest_hash":"73b597461eef","mode":"interactive","source":"cli","taint_in":false}
```

## What the log will and won't tell you

**Will:** which tools were called and how often, when, in what order, the verdict each
got, and how session taint progressed.

**Won't: the arguments.** They aren't recorded. So you can count calls per tool, but you
cannot replay the week against a different candidate manifest and get exact numbers — any
rule that depends on a path or a command string needs data the log doesn't hold. Plan the
analysis around tool-name granularity, or log redacted arguments upstream first.

## What stays invisible

Worth knowing before you draw conclusions from the distribution:

- **Remote (SSE/HTTP) servers.** The gateway fronts a spawned process; a server reached
  over a URL has no command to wrap. Reported as `unobserved:`, never silently dropped.
- **The client's built-in tools.** Web search, the analysis tool, file attachments — none
  of them travel over MCP, so none of them appear. On Claude Desktop the census is an
  *MCP-seam* census, and calling it a complete picture of what the agent did would be
  wrong.
- **Everything, if you're on Claude Code instead.** Claude Code's native tools (`Bash`,
  `Read`, `Edit`) don't go through MCP either. Its `PreToolUse` hook sees them, but
  `harness cc-hook` has no logging flag today — the practical source there is Claude
  Code's own session transcripts under `~/.claude/projects/`, which do record full tool
  inputs.

## Prerequisites

The `harness` binary, for the gateway step. From an
[`ai2rules`](https://github.com/sv-pro/ai2rules) checkout:

```bash
cargo build --release -p cli-harness
```

The enumerator itself needs nothing but Python 3 — you can run it before deciding whether
you want the rest.
