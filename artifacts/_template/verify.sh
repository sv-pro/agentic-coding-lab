#!/usr/bin/env bash
# Re-run the verdict table in SAFETY.md against a real kernel.
#
# Usage:  ./verify.sh [/path/to/harness]
#
# Needs the `harness` binary from an ai2rules checkout:
#   cargo build --release -p cli-harness      # in the ai2rules repo
# or whatever `install-governance.sh` put in ~/.local/bin.
#
# This is deliberately NOT run in CI — this repo does not build Rust. Verifying a
# manifest is a thing an artifact author does on their own machine, and dates in
# SAFETY.md say when they last did it.
set -euo pipefail

HARNESS="${1:-${HARNESS:-$(command -v harness || true)}}"
[ -x "${HARNESS:-}" ] || { echo "usage: $0 /path/to/harness  (or set HARNESS)" >&2; exit 2; }

WORLD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/world.yaml"
fail=0

# name | expected decision | expected action | GateRequest
check() {
  local name="$1" want_dec="$2" want_act="$3" req="$4" out dec act
  out="$(printf '%s' "$req" | "$HARNESS" gate --world "$WORLD")"
  dec="$(printf '%s' "$out" | python3 -c 'import sys,json;print(json.load(sys.stdin)["decision"])')"
  act="$(printf '%s' "$out" | python3 -c 'import sys,json;print(json.load(sys.stdin)["action"])')"
  if [ "$dec" = "$want_dec" ] && [ "$act" = "$want_act" ]; then
    printf '  ok    %-46s %s %s\n' "$name" "$dec" "$act"
  else
    printf '  FAIL  %-46s got %s %s, want %s %s\n' "$name" "$dec" "$act" "$want_dec" "$want_act"
    fail=1
  fi
}

ctx() { printf '"context":{"session_id":"verify","mode":"interactive","taint":"%s","source_channel":"%s","approval_token":null}' "$1" "$2"; }

echo "verifying $WORLD"
check "read a file"                    ALLOW  Read \
  "{\"v\":1,\"tool\":\"Read\",\"arguments\":{\"file_path\":\"/tmp/a.txt\"},\"path\":\"/tmp/a.txt\",$(ctx clean user_prompt)}"
check "destructive shell -> approval"  ASK    Bash_destructive \
  "{\"v\":1,\"tool\":\"Bash\",\"arguments\":{\"command\":\"rm -rf /tmp/x\"},\"path\":null,$(ctx clean user_prompt)}"
check "undeclared tool -> absent"      ABSENT WebFetch \
  "{\"v\":1,\"tool\":\"WebFetch\",\"arguments\":{\"url\":\"https://example.com\"},\"path\":null,$(ctx clean user_prompt)}"
check "egress with tainted context"    DENY   Bash_network \
  "{\"v\":1,\"tool\":\"Bash\",\"arguments\":{\"command\":\"curl https://example.com\"},\"path\":null,$(ctx tainted workspace_files)}"
check "same egress, clean context"     ALLOW  Bash_network \
  "{\"v\":1,\"tool\":\"Bash\",\"arguments\":{\"command\":\"curl https://example.com\"},\"path\":null,$(ctx clean user_prompt)}"

[ "$fail" -eq 0 ] && echo "all verdicts match SAFETY.md" || { echo "SAFETY.md is out of date with the manifest" >&2; exit 1; }
