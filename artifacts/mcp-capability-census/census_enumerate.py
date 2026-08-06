#!/usr/bin/env python3
"""Phase 0 of the capability census: discover the MCP surface, then declare it.

You cannot observe a surface you have not declared. `harness mcp-gateway` shapes
`tools/list` down to what the world manifest names, so any tool the manifest misses
disappears from the client — that is `ABSENT` doing its job, and it is the opposite of
observe-only. So before you can record a week of real usage, you need a manifest that
declares *everything* your servers expose.

This script builds that manifest by asking each server what it has.

    ./census_enumerate.py --dry-run              # what would be spawned, spawning nothing
    ./census_enumerate.py                        # enumerate, write the census world
    ./census_enumerate.py --emit-config          # ...and a gateway-wrapped client config

Stdlib only. Read SAFETY.md before running it — this script starts every MCP server in
your config, and the manifest it writes is an instrument, not a security policy.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
from datetime import date
from pathlib import Path

PROTOCOL_VERSION = "2024-11-05"

# Where each client keeps its MCP config. Claude Desktop only, for now — the format is
# shared with several other clients, so --config takes anything with an `mcpServers` map.
DEFAULT_CONFIGS = {
    "darwin": "~/Library/Application Support/Claude/claude_desktop_config.json",
    "win32": "~/AppData/Roaming/Claude/claude_desktop_config.json",
    "linux": "~/.config/Claude/claude_desktop_config.json",
}


# --- talking to one server ---------------------------------------------------------


class ServerError(Exception):
    pass


def _reader(stream, q: queue.Queue) -> None:
    """Pump stdout lines into a queue so the main thread can wait with a timeout.

    A thread rather than selectors: pipe polling differs across platforms and this has
    to work on whichever laptop the census is being run from.
    """
    try:
        for line in stream:
            q.put(line)
    except Exception:  # noqa: BLE001 - the process died; the timeout path reports it
        pass
    finally:
        q.put(None)


def list_tools(command: list[str], env: dict[str, str] | None, timeout: float) -> list[dict]:
    """Spawn one stdio MCP server, complete the handshake, return its tools."""
    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        env={**os.environ, **(env or {})},
    )
    q: queue.Queue = queue.Queue()
    threading.Thread(target=_reader, args=(proc.stdout, q), daemon=True).start()

    def send(msg: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()

    def await_id(want: int) -> dict:
        """Read until the response with this id arrives; ignore notifications and logs."""
        while True:
            line = q.get(timeout=timeout)
            if line is None:
                raise ServerError("server closed the connection before responding")
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue  # servers sometimes print banners on stdout
            if msg.get("id") == want:
                if "error" in msg:
                    raise ServerError(f"server returned an error: {msg['error']}")
                return msg.get("result", {})

    try:
        send({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "capability-census", "version": "0"},
            },
        })
        await_id(1)
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        return await_id(2).get("tools", [])
    except queue.Empty as exc:
        raise ServerError(f"no response within {timeout:g}s") from exc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


# --- emitting the manifest ---------------------------------------------------------


def yaml_str(s: str) -> str:
    """Quote a scalar. Tool names come from third-party servers; never trust their shape."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_world(surface: dict[str, list[dict]]) -> str:
    """Render a maximally permissive manifest that declares every discovered tool.

    Every design choice here is subordinate to one goal: change nothing about what the
    agent can do, so that the audit log records real behaviour rather than the effect of
    this manifest. Hence no transition policies, every capability at every trust level,
    and `side_effect: Read` on everything regardless of what the tool actually does.
    """
    total = sum(len(v) for v in surface.values())
    out: list[str] = [
        "# CENSUS WORLD — an instrument, not a policy. Generated, do not hand-edit.",
        f"# Generated {date.today().isoformat()} from {len(surface)} server(s), {total} tool(s).",
        "#",
        "# This manifest permits everything on purpose. It has no transition policies, it",
        "# grants every capability at every trust level, and it declares every action with",
        "# `side_effect: Read` no matter what the tool really does. Its verdicts are",
        "# therefore meaningless by construction — only the audit log it produces means",
        "# anything.",
        "#",
        "# DO NOT SHIP THIS AS A STARTER MANIFEST. It is the measuring instrument. The",
        "# manifest you ship is the one you derive *from the log* once the census is done.",
        "world_id: census-observe-only",
        "",
        "actors:",
        "  - { name: developer, kind: User }",
        "  - { name: agent, kind: Model }",
    ]
    for server in surface:
        out.append(f"  - {{ name: {yaml_str(server)}, kind: McpServer }}")

    out += [
        "",
        "data_classes: [Public, Workspace, Secret, Credential, Generated, External]",
        "",
        "# Everything trusted, nothing tainting: the instrument must not alter the readings.",
        "channels:",
        "  - { name: cli, trust: Trusted, taint: false }",
        "  - { name: mcp_output, trust: Trusted, taint: false }",
        "",
        "# Every capability at every trust level, so nothing can fall out via capability.",
        "capabilities:",
    ]
    acts = "[Read, Write, Patch, Command, Pty, Mcp, Web, Memory]"
    for trust in ("Trusted", "SemiTrusted", "Untrusted", "Derived"):
        out.append(f"  - {{ trust: {trust}, actions: {acts} }}")

    out += ["", "base_actions:"]
    for server, tools in surface.items():
        out.append(f"  # --- {server} ({len(tools)} tools) ---")
        for tool in sorted(tools, key=lambda t: t["name"]):
            name = tool["name"]
            out += [
                f"  - name: {yaml_str(name)}",
                "    action_type: Mcp",
                "    side_effect: Read",
                f"    backing: !McpServer {{ server: {yaml_str(server)}, tool: {yaml_str(name)} }}",
            ]

    out += [
        "",
        "# No transition_policies. Deliberate: a taint floor would deny calls, and a denied",
        "# call is a call you did not observe.",
        "",
        "budget:",
        "  max_tokens_per_session: 100000000",
        "  max_commands_per_task: 100000",
        "  command_timeout_ms: 600000",
        "",
        "observability:",
        "  redact:",
        '    - "env.*_TOKEN"',
        '    - "env.*_KEY"',
        '    - "**/.env"',
        "",
    ]
    return "\n".join(out)


def build_wrapped_config(raw: dict, servers: list[str], harness: str, world: Path, audit: Path) -> dict:
    """Return a copy of the client config with each stdio server behind the gateway."""
    wrapped = json.loads(json.dumps(raw))  # deep copy; never mutate the caller's config
    for name in servers:
        entry = wrapped["mcpServers"][name]
        upstream = [entry["command"], *entry.get("args", [])]
        entry["command"] = harness
        entry["args"] = [
            "mcp-gateway",
            "--world", str(world),
            "--audit", str(audit),
            "--", *upstream,
        ]
    return wrapped


# --- main --------------------------------------------------------------------------


def default_config_path() -> Path:
    return Path(DEFAULT_CONFIGS.get(sys.platform, DEFAULT_CONFIGS["linux"])).expanduser()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=None, help="client MCP config (default: Claude Desktop's)")
    ap.add_argument("--out-world", type=Path, default=Path("census-world.yaml"))
    ap.add_argument("--audit", type=Path, default=Path("census-audit.jsonl"), help="where the gateway should log")
    ap.add_argument("--harness", default="harness", help="path to the harness binary, for --emit-config")
    ap.add_argument("--emit-config", action="store_true", help="also write a gateway-wrapped client config")
    ap.add_argument("--out-config", type=Path, default=None, help="where to write it (default: <config>.census.json)")
    ap.add_argument("--only", action="append", default=[], metavar="NAME", help="enumerate only these servers")
    ap.add_argument("--timeout", type=float, default=20.0, help="per-server response timeout (default: 20s)")
    ap.add_argument("--dry-run", action="store_true", help="list what would be spawned, spawn nothing")
    args = ap.parse_args()

    config_path = (args.config or default_config_path()).expanduser()
    if not config_path.is_file():
        print(f"no MCP config at {config_path}\npass --config PATH", file=sys.stderr)
        return 2

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    servers = raw.get("mcpServers") or {}
    if not servers:
        print(f"{config_path} declares no mcpServers", file=sys.stderr)
        return 2

    surface: dict[str, list[dict]] = {}
    stdio_names: list[str] = []
    skipped: list[tuple[str, str]] = []

    for name, entry in servers.items():
        if args.only and name not in args.only:
            continue
        if entry.get("disabled"):
            skipped.append((name, "disabled in the config"))
            continue
        if not entry.get("command"):
            # No command means there is no process to substitute. That is a limit of this
            # gateway build, not of the approach: transport is an adapter concern, and
            # interposition needs only that the client's endpoint be redirectable. Routing
            # such a server through a stdio bridge puts it back in scope today, and an
            # HTTP-side adapter on the gateway would too.
            skipped.append((name, "no command — this gateway build wraps stdio only; route it "
                                  "through a stdio bridge to bring it into scope"))
            continue

        command = [entry["command"], *entry.get("args", [])]
        stdio_names.append(name)
        print(f"  {name}: {' '.join(command)}")
        if args.dry_run:
            continue
        try:
            tools = list_tools(command, entry.get("env"), args.timeout)
        except (ServerError, OSError) as exc:
            skipped.append((name, str(exc)))
            print(f"    ! {exc}", file=sys.stderr)
            continue
        surface[name] = tools
        print(f"    {len(tools)} tools: {', '.join(sorted(t['name'] for t in tools)) or '(none)'}")

    if args.dry_run:
        print(f"\ndry run — nothing was spawned. {len(stdio_names)} server(s) would be.")
        return 0

    if not surface:
        print("\nno server responded; nothing to declare", file=sys.stderr)
        return 1

    args.out_world.write_text(build_world(surface), encoding="utf-8")
    total = sum(len(v) for v in surface.values())
    print(f"\nwrote {args.out_world} — {total} tools across {len(surface)} server(s)")

    if args.emit_config:
        out_config = args.out_config or config_path.with_suffix(".census.json")
        if out_config.resolve() == config_path.resolve():
            print("refusing to overwrite the live config; pass a different --out-config", file=sys.stderr)
            return 1
        wrapped = build_wrapped_config(raw, list(surface), args.harness,
                                       args.out_world.resolve(), args.audit.resolve())
        out_config.write_text(json.dumps(wrapped, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out_config} — review it, then copy it over {config_path.name} yourself")

    for name, why in skipped:
        print(f"unobserved: {name} — {why}")
    if skipped:
        print("\nServers listed above are NOT in the census. Say so in the write-up:")
        print("a capability distribution with silent gaps is worse than one with stated gaps.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
