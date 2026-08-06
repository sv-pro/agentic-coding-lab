# SAFETY BASELINE — what each tier actually buys you

*Every artifact in this repo declares a tier. This file defines them, names the real
command behind each, and — more importantly — says where each one stops working.*

The machinery is not ours. It comes from [`ai2rules`](https://github.com/sv-pro/ai2rules),
a governance kernel that sits under a local CLI agent and decides what the agent is even
able to represent. We configure it. We do not modify it, and this repo never re-explains
its design — read [`docs/harness-architecture.md`](https://github.com/sv-pro/ai2rules/blob/main/docs/harness-architecture.md)
upstream for that.

---

## Tier 0 — Unenforced

**What it is:** advice in prose. A note that says "don't point this at a production
database" and nothing that stops you.

**What checks it:** nothing.

**When it's the right tier:** most artifacts, honestly. A slash command that reformats a
changelog does not need a manifest. Tier 0 is not a failing grade — an unlabelled tier-0
artifact pretending to be tier 2 is.

---

## Tier 1 — Overlay

**What it is:** the artifact ships rules that *add* denials and approval prompts on top
of whatever the host already permits. The agent keeps its normal capabilities; specific
dangerous shapes now stop and ask.

**How it's installed** (from an `ai2rules` checkout):

```bash
bash /path/to/ai2rules/scripts/install-governance.sh .
```

That does two things: puts the `harness` binary somewhere trusted, and drops a
`.claude/` shim plus a starter manifest into the target project, merging the
`PreToolUse` hook into `settings.json`. The default mode is **additive** — it only ever
adds deny/ask on top of your existing permissions, so it cannot lock you out of your own
project. (`--grant` flips it into a mode where the manifest also *grants*, which means
fewer prompts and a much sharper edge; that's a deliberate choice, not a default.)

**How to turn it off, instantly:**

```bash
touch .claude/gate-off     # this project, takes effect on the next tool call
touch ~/.claude/gate-off   # everywhere, panic switch
```

**Where tier 1 stops working — say this part out loud:**

- **The host hook fails open.** If the harness binary is missing, crashes, or times out,
  the tool call proceeds. This is intentional: a governance layer that bricks your editor
  when it has a bad day gets uninstalled within the hour, and an uninstalled layer
  protects nobody. But it means tier 1 is a *seatbelt*, not a *cage*.
- **It only covers the seam it's wired into.** A `PreToolUse` hook sees the host's tool
  calls. It does not see what a subprocess does after the call is allowed.
- **An approval prompt is only as good as the human reading it.** The twentieth prompt of
  the afternoon gets approved without being read. This is why tier 2 exists.

**Claiming tier 1 requires** shipping the manifest or settings fragment that does the
work, named in your `SAFETY.md` under `enforced_by`. CI checks the file is there.

---

## Tier 2 — Structural

**What it is:** the dangerous capability is not refused — it is **absent**. It does not
appear in the compiled world, so there is no action to propose, no prompt to phrase
persuasively, and nothing to talk past.

Two shapes qualify:

**a) Absent from the compiled world.** A `WorldManifest` declares the actions that exist.
An action that isn't declared cannot be built into an intent at all — this is the
`ABSENT ≠ DENY` distinction the upstream project is built on. Check a manifest against a
real call before you trust it:

```bash
harness gate --world ./world.yaml       # host-neutral: feed it a tool call, read the verdict
```

**b) Mediated by the gateway.** For MCP servers, `harness mcp-gateway` sits in front of
the upstream server and shapes what it is allowed to advertise — the agent's `tools/list`
only ever contains what the manifest permits. Unlike the host hook, **the gateway fails
closed**: if it can't decide, nothing gets through.

**Where tier 2 stops working:**

- **Scope is the manifest's, not the universe's.** A capability absent from *this* world
  is still available to any process that isn't running under it.
- **It requires actually running under the harness.** A tier-2 artifact copied into a
  project with no manifest is a tier-0 artifact with confident documentation.
- **`Bash` is a wildcard and the manifest knows it.** Shell commands are classified by
  pattern into narrower actions (network, destructive, unclassified). Pattern lists are
  finite; an unmatched command falls to `Bash_unclassified`, which asks. Read the
  classification block before assuming a class is airtight.

---

## The taint rule, which applies at every tier

The kernel tracks where data came from. Content read from a web page, a file, or a tool
result is **tainted**, and taint only ever spreads — it never washes out. The default
manifests then forbid tainted context from reaching anything that leaves the machine:
no network, no credentials, no persistent writes.

This is the part that matters most for the artifacts in this repo, because the whole
point of a useful skill is that it reads something. An artifact that ingests an issue
tracker, a web page or a colleague's PR description has, by construction, put untrusted
text into the agent's context. Under a taint-aware manifest the consequence is bounded
and visible. Without one, it isn't.

If you take one thing from this file into an artifact you write: **say what your artifact
reads, and say where that reading can end up.**

---

## Writing the `SAFETY.md`

Copy [`artifacts/_template/SAFETY.md`](../artifacts/_template/SAFETY.md). Required
fields, all checked by `scripts/check-artifacts.py`:

| Field | Meaning |
|---|---|
| `artifact` | directory name |
| `kind` | `skill` · `plugin` · `subagent` · `hook` · `command` · `mcp-server` · `recipe` |
| `hosts` | which agents this was written for |
| `tier` | `0`, `1`, or `2` — as defined above |
| `enforced_by` | path *inside the artifact directory* to the file doing the enforcing. Required at tier ≥ 1. |
| `reads` | the untrusted inputs this artifact pulls into context |
| `blast_radius` | one sentence: the worst thing that happens if it misbehaves |
| `verified` | ISO date someone actually ran it, or `never` |

`verified: never` is allowed. It just obliges the artifact's `README.md` to open with the
line `> **Unverified.**` — checked by CI, so it cannot be quietly dropped later.
