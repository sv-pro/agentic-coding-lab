#!/usr/bin/env python3
"""Log every tool call Claude Code makes. A PreToolUse hook, and nothing else.

No kernel, no manifest, no gateway. Claude Code hands each proposed tool call to a
PreToolUse hook before running it; this reads that event, appends one JSON line, and
gets out of the way. It governs nothing and decides nothing.

It sees *everything* the host runs — native tools (Bash, Read, Edit, WebFetch) and MCP
tools alike — with their arguments. That is strictly more than an MCP gateway can see,
and it is why this exists alongside one.

    "hooks": {
      "PreToolUse": [
        { "matcher": "*",
          "hooks": [ { "type": "command", "timeout": 5,
                       "command": "python3 /abs/path/log_tool_calls.py --log ~/tool-log.jsonl" } ] }
      ]
    }

Three rules this file must never break, because a bad PreToolUse hook degrades every
tool call in the session:

  1. Always exit 0. Any failure to log is silent — losing a log line is acceptable,
     interfering with the developer's session is not.
  2. Never write to stdout. Claude Code reads hook stdout as a permission decision.
     Diagnostics go to stderr; the record goes to the log file.
  3. Never block. No network, no locks held across work, append-only writes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fields worth keeping at --level paths: structural, and the ones a capability census
# actually needs (which paths got touched, what kind of command ran). Values of anything
# not listed here stay out of the log.
PATH_FIELDS = ("file_path", "notebook_path", "path", "pattern")
URL_FIELDS = ("url",)

# --- shell command extraction ------------------------------------------------------
# First-token parsing does not survive real input: a live session produced `if` and
# `BEFORE=$(wc` for roughly a fifth of its shell calls, because control flow and variable
# assignment both occupy position zero without being commands. So instead of reading one
# token, walk the string and collect what sits in *command position* — the start, or just
# after a separator or a control keyword.

_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\+?=")

# Reset to a command position; these are structure, not programs.
_SEPARATORS = {";", ";;", "&&", "||", "|", "|&", "&", "(", ")", "{", "}", "\n"}

# Keywords followed by a command: step over them and keep looking (`if grep …`).
_KEYWORDS_TRANSPARENT = {"if", "then", "elif", "else", "fi", "while", "until", "do",
                         "done", "esac", "function", "time", "!", "coproc"}

# Keywords followed by *words*, not commands (`for i in a b`). Their operands must not be
# mistaken for programs, so these consume the command position instead of passing it on.
_KEYWORDS_BINDING = {"for", "case", "select", "in"}

# Real commands that reach nothing worth counting in a capability census.
_TRIVIAL = {"[", "[[", "]", "]]", "test", ":", "true", "false"}


def _tokens(command: str) -> list[str]:
    """Split on whitespace after padding shell operators so they become their own tokens.

    Not a shell parser — deliberately. `$(` degrades to `$` + `(`, which is exactly what
    we want: the `$` is ignored and the `(` opens a command position, so the contents of a
    substitution get scanned like anything else.
    """
    text = command
    for op in ("&&", "||", ";;", "|&"):
        text = text.replace(op, f" {op} ")
    for ch in (";", "|", "&", "(", ")", "{", "}", "\n"):
        text = text.replace(ch, f" {ch} ")
    return text.split()


def shell_commands(command: str) -> list[str]:
    """Every program invoked in `command`, in order, deduplicated.

    Assignments and keywords are skipped rather than reported, and a leading path is
    reduced to its basename so `/usr/bin/git` and `git` aggregate together.
    """
    found: list[str] = []
    at_command = True
    for tok in _tokens(command):
        if tok in _SEPARATORS:
            at_command = True
            continue
        if not at_command:
            continue
        if _ASSIGNMENT.match(tok) or tok in _KEYWORDS_TRANSPARENT:
            continue  # still looking for the command this belongs to
        if tok in _KEYWORDS_BINDING or tok in _TRIVIAL:
            at_command = False
            continue
        name = tok.rsplit("/", 1)[-1][:64]
        if name and name not in found:
            found.append(name)
        at_command = False
    return found


def summarize(tool_input: dict, level: str) -> dict:
    """Reduce a tool's arguments to what the chosen level permits."""
    if level == "full":
        return {"input": tool_input}

    out: dict = {"keys": sorted(tool_input), "bytes": len(json.dumps(tool_input))}
    if level == "keys":
        return out

    # level == "paths": structure, plus the shape of a command — never its full text.
    for field in PATH_FIELDS:
        if isinstance(tool_input.get(field), str):
            out[field] = tool_input[field]
    for field in URL_FIELDS:
        value = tool_input.get(field)
        if isinstance(value, str):
            # Host only. The path and query string are where the interesting secrets are.
            rest = value.split("://", 1)[-1]
            out[field] = rest.split("/", 1)[0]
    command = tool_input.get("command")
    if isinstance(command, str):
        # Which programs this call reaches, without recording what it asked them to do.
        # `commands` is the field to count; `argv0` is kept as its first element for
        # continuity with logs written before this was fixed.
        cmds = shell_commands(command)
        out["commands"] = cmds
        out["argv0"] = cmds[0] if cmds else None
        out["command_bytes"] = len(command)
    return out


# Cases 1-3 are verbatim from the live session that showed first-token parsing failing.
SELF_TEST = [
    ("BEFORE=$(wc -l < ~/log || echo 0)", ["wc", "echo"]),
    ("if [ -f ~/log ]; then echo yes; else echo no; fi", ["echo"]),
    ("cd /repo && ./scripts/check.sh", ["cd", "check.sh"]),
    ("git status --short", ["git"]),
    ('curl -H "Auth: Bearer sk-X" https://api.example.com | jq .', ["curl", "jq"]),
    ("sudo rm -rf /tmp/x", ["sudo"]),
    ("FOO=1 BAR=2 python3 run.py", ["python3"]),
    ("/usr/bin/git push", ["git"]),
    ("for i in 1 2 3; do echo $i; done", ["echo"]),
    ("python3 - <<'PY'", ["python3"]),
    ("", []),
    ("   ", []),
]


def self_test() -> int:
    failures = 0
    for command, expected in SELF_TEST:
        got = shell_commands(command)
        if got == expected:
            print(f"  ok    {command[:44]!r:48} -> {got}")
        else:
            failures += 1
            print(f"  FAIL  {command[:44]!r:48} -> {got}, want {expected}")
    print(f"\nself-test: {failures} failure(s)")
    return 1 if failures else 0


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return self_test()
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default="~/claude-tool-log.jsonl")
    ap.add_argument("--level", choices=("keys", "paths", "full"), default="keys",
                    help="how much of each tool's arguments to record (default: keys)")
    try:
        args = ap.parse_args()
        event = json.load(sys.stdin)

        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "session": event.get("session_id"),
            "tool": event.get("tool_name"),
            "cwd": event.get("cwd") or os.getcwd(),
            **summarize(event.get("tool_input") or {}, args.level),
        }

        path = Path(args.log).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:  # noqa: BLE001
        # Rule 1. A logger that can break a session is worse than no logger.
        print(f"[tool-log] skipped: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
