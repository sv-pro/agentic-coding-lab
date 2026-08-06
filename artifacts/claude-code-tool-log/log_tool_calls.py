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
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fields worth keeping at --level paths: structural, and the ones a capability census
# actually needs (which paths got touched, what kind of command ran). Values of anything
# not listed here stay out of the log.
PATH_FIELDS = ("file_path", "notebook_path", "path", "pattern")
URL_FIELDS = ("url",)


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
        # argv0 is enough to classify (git / curl / rm / npm) without recording what was
        # actually run. `--level full` is there for anyone who needs the rest.
        out["argv0"] = command.strip().split(" ", 1)[0][:64]
        out["command_bytes"] = len(command)
    return out


def main() -> int:
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
