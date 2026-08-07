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

[`log-sample.jsonl`](log-sample.jsonl) is a real one — 16 calls from ~100 minutes of
actual work at `--level paths`, not a fixture:

```json
{"ts":"2026-08-06T21:28:20.217+00:00","session":"<session>","tool":"Read",
 "cwd":"~/…/agentic-coding-lab","keys":["file_path","limit"],"bytes":60,
 "file_path":"~/.claude/settings.json"}
{"ts":"2026-08-07T06:51:44.916+00:00","session":"<session>","tool":"Write",
 "cwd":"~/…/agentic-coding-lab","keys":["content","file_path"],"bytes":9937,
 "file_path":"~/…/ai2rules/docs/GOVERNABILITY-INDEX.md"}
```

Note the second line: a 9,937-byte `Write` whose *content* is not in the record. That is
`--level paths` doing its job.

The sample was scrubbed before being committed — home directory to `~`, session UUID and
scratch paths to placeholders — then checked for residue. That is the same discipline this
artifact asks of you: **publish aggregates and scrubbed samples, never the raw log.**

What 16 real calls look like in aggregate:

| | |
|---|---|
| Bash | 10 |
| Write | 4 |
| Read · Edit | 1 each |

### What the real sample caught that fixtures didn't

`argv0` is meant to classify a shell call — `git`, `curl`, `rm` — without recording the
command. Across the 10 real `Bash` calls it produced: `git`×2, `echo`×2, `cd`×2, `grep`,
`python3` … and **`if`** and **`BEFORE=$(wc`**.

Shell control flow and variable assignment defeat "first token" entirely. Every synthetic
event I tested with began with a clean command name, so the heuristic looked perfect until
it met real input. **Roughly 20% of real shell calls classify to nothing useful** — plan
your analysis accordingly, and treat `argv0` as a hint rather than a category.

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
- **Reliable command classification.** `argv0` is the first token, and real shell input
  is full of `if`, `for`, and `VAR=$(…)`. About a fifth of the calls in the real sample
  classify to nothing. Use `--level full` if you need this to be exact — and read
  [`SAFETY.md`](SAFETY.md) before you do.

## Rotate it

There's no rotation and no size cap — one append per tool call adds up over a week.

```bash
mv ~/claude-tool-log.jsonl ~/census/week-$(date +%G-W%V).jsonl
```
