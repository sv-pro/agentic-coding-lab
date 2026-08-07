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

Then work normally. No restart needed — user-level hook config is read live; a hook
added mid-session fires on the very next tool call (measured 2026-08-06, and removal
takes effect the same way).

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

### What the real sample caught, and the fix it forced

The sample was recorded when shell classification was "take the first token". Across 10
real `Bash` calls that produced `git`×2, `echo`×2, `cd`×2, `grep`, `python3` … and
**`if`** and **`BEFORE=$(wc`**.

Control flow and variable assignment both occupy position zero without being commands.
Every synthetic event used in development began with a clean command name, so the
heuristic looked perfect until it met a live session — about a fifth of real calls
classified to nothing.

**Now fixed.** The logger walks the string and collects what sits in *command position* —
the start, or just after a separator or a control keyword — skipping assignments and
keywords, unwrapping `$(…)`, and reducing `/usr/bin/git` to `git`:

| Command | `commands` |
|---|---|
| `BEFORE=$(wc -l < ~/log \|\| echo 0)` | `["wc", "echo"]` |
| `if [ -f x ]; then echo yes; fi` | `["echo"]` |
| `curl … \| jq .` | `["curl", "jq"]` |
| `for i in 1 2 3; do echo $i; done` | `["echo"]` |
| `cd /repo && ./scripts/check.sh` | `["cd", "check.sh"]` |

`commands` is the field to count — a call that runs `cd /repo && git push` reaches `git`,
and first-token parsing would have told you it reached `cd`. `argv0` is kept as its first
element so older logs stay comparable.

```bash
./log_tool_calls.py --self-test   # 12 cases, three lifted from the failing session
```

**[`log-sample.jsonl`](log-sample.jsonl) predates the fix** and is kept that way on
purpose: it is the evidence that produced it, and `if` / `BEFORE=$(wc` are visible in it.

## How much to record

```bash
--level keys    # default: which tools, when, argument NAMES only. No values.
--level paths   # + file paths, URL host, and which programs each shell call runs
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
- **Perfect command classification.** `commands` handles assignments, keywords, pipes and
  substitutions, but it is a scanner and not a shell parser. It deliberately gives up in
  three places rather than guess: **quoted spans are dropped**, **everything after a
  heredoc marker is dropped**, and a bare `(` does not open a command. So `sh -c "git
  push"`, `eval`, `xargs` and aliases all hide the program that actually runs, and a
  census built on this **undercounts**. Every extracted name must also match a strict
  command-name pattern, and at most 8 are kept — so a bad parse loses data rather than
  spilling command text into the log. Use `--level full` when you need this exact.

## Rotate it

There's no rotation and no size cap — one append per tool call adds up over a week.

```bash
mv ~/claude-tool-log.jsonl ~/census/week-$(date +%G-W%V).jsonl
```
