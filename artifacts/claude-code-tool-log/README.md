# claude-code-tool-log

**Log every tool call your assistant makes. One hook, one file, no infrastructure.**

Claude Code hands each proposed tool call to a `PreToolUse` hook before running it. This
reads that event, appends one JSON line, and exits. It governs nothing.

That's the whole thing. If you want a capability census and you use Claude Code, start
here — not with a gateway.

## Install

```bash
mkdir -p ~/.claude && cp log_tool_calls.py ~/.claude/log_tool_calls.py
```

Then in `~/.claude/settings.json` (user-wide) or `<project>/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "*",
        "hooks": [
          { "type": "command",
            "timeout": 5,
            "command": "python3 $HOME/.claude/log_tool_calls.py --log $HOME/claude-tool-log.jsonl" }
        ] }
    ]
  }
}
```

Start a new session — hooks are read at session start. Then work normally.

```json
{"ts":"2026-08-06T20:43:23.406+00:00","session":"s1","tool":"Bash","cwd":"/home/dev/proj",
 "keys":["command"],"bytes":97,"argv0":"curl","command_bytes":80}
```

## How much to record

```bash
--level keys    # default: which tools, when, argument NAMES only. No values.
--level paths   # + file paths, URL host, and the command's first word
--level full    # the entire tool_input, secrets included
```

Start at `keys`. It answers "which tools do I actually use, and how often" — the census
question — without writing your work to disk. Move up only when you need more, and move
back down after.

`--level full` is the only setting that supports exact replay against a candidate
manifest. It is also the only one that will write an API token into a log file. Read
[`SAFETY.md`](SAFETY.md) before turning it on.

## Why this rather than the MCP gateway

They see different things, and the difference is the point.

| | This hook | [`mcp-capability-census`](../mcp-capability-census/) |
|---|---|---|
| Sees native tools (`Bash`, `Read`, `Edit`, `WebFetch`) | **yes** | no |
| Sees MCP tools | yes, as `mcp__server__tool` | yes |
| Records arguments | yes, at your chosen level | **no** |
| Enforces anything | no | yes — fail-closed |
| Works on | Claude Code only | any client that speaks MCP |

For a census on Claude Code, this is strictly better data and a much smaller setup. The
gateway earns its place when you want *enforcement*, or when the host has no hook — which
is every host except Claude Code today.

## What it can't tell you

- **Whether the call succeeded.** `PreToolUse` fires before execution. The log records
  what was *proposed*; a call later blocked by a permission rule still appears. It is a
  record of intent, not of outcome.
- **How long anything took**, or what it returned.
- **Anything about a different host.** Claude Desktop has no hooks. Codex and Copilot
  have their own shapes.

## Rotate it

There's no rotation and no size cap — one append per tool call adds up over a week.

```bash
mv ~/claude-tool-log.jsonl ~/census/week-$(date +%G-W%V).jsonl
```
