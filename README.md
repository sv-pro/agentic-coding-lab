# agentic-coding-lab

**Getting real work out of AI coding agents — and knowing what they can reach while
they do it.**

This repo is about *effectiveness*: the skills, plugins, subagents, hooks and MCP
setups that actually make an agent faster at building software, plus the experiments
that show whether they do, plus the write-ups that explain why.

The catch is that every technique which makes an agent more useful also makes it
reach further. A subagent that can run your test suite can run anything. A skill that
reads your issue tracker has just given a stranger's bug report a path into your
shell. So each artifact here ships with a plain statement of **what it can reach when
it goes wrong**, and — where it matters — a configuration that makes the bad reach
*structurally impossible* rather than merely discouraged.

That second half is not invented here. It comes from a sibling project,
[`ai2rules`](https://github.com/sv-pro/ai2rules), which is a deterministic governance
kernel for local CLI agents. This repo is its **consumer**, never its author. We
import the brakes; we don't redesign them.

## Who this is for

You already use Claude Code, Codex CLI, OpenCode, Antigravity, Cursor or similar most
days. You want the good stuff — the workflows that compress an afternoon into twenty
minutes — without the version where an agent quietly force-pushes over a colleague's
branch because a web page told it to.

You do not need to care about governance theory to use anything here. If you want the
theory, it lives upstream in [`docs/THESIS.md`](https://github.com/sv-pro/ai2rules/blob/main/docs/THESIS.md)
and this repo will not restate it.

## What's in here

| Directory | What it holds |
|---|---|
| [`artifacts/`](artifacts/) | Things you can copy into a project: skills, plugins, subagents, hooks, MCP configs, slash commands. Each one carries a `SAFETY.md`. |
| [`experiments/`](experiments/) | Did the technique actually help? Setup, what was measured, what happened — including the ones that didn't work. |
| [`articles/`](articles/) | Practitioner write-ups. Long-form governance essays stay on the upstream blog; see the [charter](docs/CHARTER.md). |
| [`docs/`](docs/) | The [charter](docs/CHARTER.md) (scope), the [safety baseline](docs/SAFETY-BASELINE.md) (the tiers), the [experiment protocol](docs/EXPERIMENT-PROTOCOL.md) (how results get reported). |

## The artifact contract

The thing that makes this repo different from a folder of prompts is one rule, and it
is checked by CI:

> **An artifact may not describe itself as safer than it is.**

Every artifact declares a tier in its `SAFETY.md`, and the tier has to be earned:

| Tier | Name | What it means |
|---|---|---|
| **0** | Unenforced | The safety note is advice. Nothing checks it. Perfectly legitimate — just labelled. |
| **1** | Overlay | Ships rules that add denials or approval prompts on top of the host's own permissions. Fails open if the harness is missing. |
| **2** | Structural | The dangerous capability is **absent** from the compiled world, or is mediated by a gateway. There is no prompt to talk past, because the action cannot be represented. |

Claiming tier 1 or 2 requires shipping the file that does the enforcing —
[`scripts/check-artifacts.py`](scripts/check-artifacts.py) verifies the file exists and
fails the build if it doesn't. An artifact nobody has actually run has to say so on
its own front page. See [`docs/SAFETY-BASELINE.md`](docs/SAFETY-BASELINE.md) for the
full definition and the commands behind each tier.

## Current state — read this before judging the repo

**Nothing ships yet.** This is the scaffolding commit: the charter, the safety
baseline, the artifact contract, the template, and the CI lint that enforces it.
`artifacts/` contains a template and no artifacts.

That is deliberate. The contract above forbids shipping an artifact that hasn't been
run, and none have been run *here* yet. The first real artifacts get added as they are
built and verified, not as placeholders.

## Open calls before this goes public

- **No LICENSE yet.** A repo whose point is that people copy things out of it needs
  one. Sibling repos in this cluster don't carry a license either, so this is a
  cluster-wide call rather than a local oversight.
- **No published artifact yet**, per the section above.

## Relationship to the rest of the cluster

```
ai2rules  ──────────────►  agentic-coding-lab
(kernel, harness, gateway)   (this repo: recipes that use it)
        ▲
        └── never depends on anything here
```

The direction is one-way and load-bearing. This repo may cite, install, configure and
depend on `ai2rules`. `ai2rules` may never depend on this repo, and **nothing produced
here may become an input to a governance decision** — an artifact is a convenience, and
conveniences do not get a vote on authority. The reasoning is the same as the rule
that keeps a text detector out of the kernel; it is recorded upstream in
[`DECISIONS.md`](https://github.com/sv-pro/ai2rules/blob/main/DECISIONS.md).
