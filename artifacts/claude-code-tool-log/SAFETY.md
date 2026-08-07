---
artifact: claude-code-tool-log
kind: hook
hosts: [claude-code]
tier: 0
reads: every tool call the host proposes, arguments included — file contents on writes, full command lines on shell calls, URLs, and every MCP tool result request
blast_radius: it writes a durable record of your work to disk, and at `--level full` that record contains whatever your commands contain, secrets included
verified: 2026-08-06
---

# Safety notes — claude-code-tool-log

## Tier 0, and necessarily so

This artifact governs nothing. It is a `PreToolUse` hook that appends a line and exits.
It does not decide, block, prompt, or alter a single call. Tier 0 is not a compromise
here — a logger that could change the outcome would be a different and much more
dangerous artifact.

## The two real risks

**1. A bad `PreToolUse` hook degrades every tool call in the session.** The hook runs
before *each* call. If it hangs, crashes in a way the host treats as a decision, or
writes to stdout, the session suffers — and the failure looks like the assistant
misbehaving rather than like a hook problem, which makes it slow to diagnose.

Three rules are therefore enforced in the code, not just documented:

| Rule | Why |
|---|---|
| Always exit `0` | Losing a log line is acceptable. Interfering with a session is not. Every path is inside one `try/except` that swallows and returns 0. |
| Never write to stdout | Claude Code reads hook stdout as a permission decision. Diagnostics go to stderr; the record goes to the file. |
| Never block | No network, no locks, append-only writes. Pair with a short `timeout` in `settings.json`. |

**2. The log is a durable record of your work.** This is the risk people
under-rate. It accumulates what you did, when, in which directory. Treat it like a shell
history file that also knows about your editor.

## What each level records

Default is `keys`, the safest useful setting. Verified 2026-08-06 by feeding synthetic
events containing a bearer token, an API query-string token, and a hardcoded password:

| `--level` | Records | Secrets in a `curl -H "Authorization: Bearer …"` |
|---|---|---|
| `keys` *(default)* | tool, timestamp, session, cwd, argument **key names**, byte size | none — verified 0 matches |
| `paths` | + `file_path` / `notebook_path` / `pattern`, URL **host only**, and `commands` | none — verified 0 matches |
| `full` | the entire `tool_input` | **all of them, verbatim** |

`--level full` is the only setting that supports exact offline replay against a candidate
manifest, and it is the only one that writes your secrets to a file. That trade is the
whole reason the levels exist; pick deliberately, and don't leave `full` on after the
run you needed it for.

**A limit found by running it for real, not by testing it — since fixed.** At `paths`,
shell classification was originally the command's first token, which is `if`, `for` or
`VAR=$(…)` often enough that about a fifth of real calls classified to nothing. Every
synthetic event used during development started with a clean command name, so the
heuristic looked sound until it met a live session. It now scans command positions
instead (`./log_tool_calls.py --self-test`), and [`log-sample.jsonl`](log-sample.jsonl) is
kept in its pre-fix state as the evidence.

**Then a second, worse bug, also found by running it.** The first fix padded bare parens
into command separators — so a `Bash` call wrapping a Python heredoc opened a "command
position" on every function call and scattered **fragments of the script** across the log:
`print`, `d['tool']:6`, `.jsonl`. That is not a classification error, it is a **redaction
failure** — `--level paths` promises not to record command content, and it was recording
it a word at a time.

Fixed, and hardened so the class of failure cannot recur silently:

| Guard | Effect |
|---|---|
| quoted spans dropped before scanning | embedded code and data are never command positions |
| everything after `<<` dropped | heredoc bodies are input, not shell |
| bare `(` no longer a separator | only `$(` and backticks open a nested command |
| every name must match `^[A-Za-z0-9_][A-Za-z0-9_.+@-]*$` | fragments and punctuation are discarded, not logged |
| at most 8 commands kept | a bad parse loses data instead of spilling the command |

The last two are the ones that matter for safety: they are a **floor on what can leak**,
independent of whether the parser is right.

What remains true: `commands` is a scanner, not a shell parser. `sh -c "…"`, `eval`,
`xargs` and aliases conceal the program that actually runs, so a census built on it
undercounts. That is a stated limit, not a bug queued for later.

## What it reads

Everything the host proposes. Native tools and MCP tools alike — an MCP call arrives as
`mcp__<server>__<tool>` and is recorded like any other, which is exactly why this sees
more than an MCP gateway can.

Note what that means for provenance: the hook observes the *proposal*, before execution.
A call that was subsequently denied by a permission rule still appears in the log. The
log is a record of intent, not of what happened.

## What is NOT bounded

- **Log growth.** No rotation, no size cap. It is one append per tool call; a busy week
  is large. Rotate it yourself.
- **Log permissions.** The file is created with your umask. If that's permissive, so is
  the log.
- **Anything after the call.** `PreToolUse` fires before execution and never learns the
  result, the exit code, or the duration.
- **Other hosts.** This is Claude Code's hook shape. Codex, Copilot and Claude Desktop do
  not have it; for those, the MCP seam is the only place to stand, which is what
  [`mcp-capability-census`](../mcp-capability-census/) is for.
