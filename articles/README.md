# articles/

Practitioner write-ups: how to do a thing with an agent, what went wrong, what the
numbers said.

**Nothing here yet.**

## What belongs here vs upstream

There are two publishing surfaces in this cluster and the line is worth being strict
about, because a blurred one produces two half-audiences instead of one.

- **Here:** capability-first. *"How I got a subagent to triage inbound issues, and what
  I fenced off before pointing it at a real tracker."* The reader wants to go faster
  today; the safety half arrives as a feature of the recipe.
- **[The ai2rules blog](https://ai2rules.dev):** argument-first. *"Why a probabilistic
  classifier cannot sit in a trust path."* The reader is being persuaded of a position.

The test: if you deleted the governance section and the article were still useful, it
belongs here. If deleting it leaves nothing, it belongs upstream. See
[`docs/CHARTER.md`](../docs/CHARTER.md).

## Format

Plain markdown, one file per article, `YYYY-MM-DD-slug.md`. No build step, no site —
GitHub renders them and that is enough until it isn't. If an article outgrows that,
it probably wanted to be an experiment with a write-up attached.

## House rules

- **Date everything.** Agentic tooling changes weekly; an undated technique is a
  technique with no shelf life stated.
- **Name the version.** Which agent, which model, which host.
- **Say when it stopped working.** An article that quietly rots is worse than one with
  a "this broke in October" note at the top.
- **Don't launder an anecdote as a measurement.** If there was no baseline, say the
  word "anecdote" in the first paragraph. The [experiment
  protocol](../docs/EXPERIMENT-PROTOCOL.md) is what the other thing looks like.
