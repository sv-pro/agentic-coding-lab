# CHARTER — what belongs here, and what doesn't

*This repo exists inside a cluster whose documented failure mode is sprawl: eight repos
were archived in one pass because nobody could say what each was for. So the boundary
gets written down on day one, not discovered in six months.*

## The one-sentence scope

> **Techniques for getting more out of AI coding agents, each shipped with an honest
> account of what it can reach.**

## In scope

- **Artifacts.** Skills, plugins, subagents, hooks, slash commands, MCP server configs,
  prompt scaffolds — anything a developer copies into a project to change how their
  agent behaves.
- **Experiments.** Measurements of whether a technique helps: which agent, which task,
  what was compared, what happened. Negative results are first-class and are the more
  valuable half.
- **Articles.** Practitioner write-ups: how to do a thing, what went wrong, what the
  numbers said.
- **The safety half of all three.** The manifest, overlay or gateway config that bounds
  an artifact's reach, and the honest tier label when there isn't one.

## Out of scope

| Not here | Where instead | Why |
|---|---|---|
| The governance kernel, compiler, executor, gate ABI | [`ai2rules`](https://github.com/sv-pro/ai2rules) | This repo is a consumer. Changing the kernel to suit a recipe is the tail wagging the dog. |
| The thesis, the architecture, the decision record | `ai2rules/docs/THESIS.md`, `DECISIONS.md` | Two copies of an argument drift within a month. Point, don't duplicate. |
| Long-form governance essays | the ai2rules blog | The audiences differ — see the split below. |
| Detector benchmarks | [`ai-detector-bench`](https://github.com/sv-pro/ai-detector-bench) | Different instrument, different audience. |
| Anything that becomes a governance *input* | nowhere | See "the one-way rule" below. |

## The article split

Both this repo and the upstream blog publish prose, so the line has to be explicit:

- **Here:** *"How I got a subagent to do X, and what I had to fence off first."*
  Capability-first. The safety measure is a feature of the recipe. Reader wants to go
  faster today.
- **Upstream blog:** *"Why a probabilistic classifier cannot sit in a trust path."*
  Argument-first. Reader is being persuaded of a position.

A useful test: if removing the governance section would still leave a useful article,
it belongs here. If removing it leaves nothing, it belongs upstream.

## The one-way rule

**This repo may depend on `ai2rules`. `ai2rules` may never depend on this repo.**

And the sharper half: **no artifact here may become an input to a governance decision.**
A skill can be *governed by* a manifest. A skill may never *inform* what a manifest
decides — not by writing rules at runtime, not by feeding a heuristic into a verdict,
not by shipping a "trusted artifact" list the kernel consults.

The reasoning is inherited, not new. The kernel's whole claim is that a decision is a
pure function of `(intent, context, compiled world)`. Anything that lets a convenience
artifact reach into that function converts a determinstic decision into a negotiable
one, and a negotiable decision is one an attacker can negotiate with.

## The honesty rule

**An artifact may not describe itself as safer than it is.**

This is enforced mechanically as far as mechanism reaches — CI checks that a tier-1 or
tier-2 claim ships the file that does the enforcing, and that an unverified artifact
says so on its front page. Past that point it is a discipline, not a check. The
temptation this rule exists to resist is real: "hardened", "sandboxed" and "safe" are
excellent words for getting a repo starred, and using them for an overlay that fails
open would be the exact failure this cluster spends its time criticising in others.

## Kill condition

Stated up front rather than discovered later, following the same practice as the
sibling repos:

> **If this repo has no verified artifact and no published experiment by 2027-02-06,
> archive it** with a README pointer to `ai2rules`. An archived repo is a decision. A
> dormant one is a question every visitor re-asks.
