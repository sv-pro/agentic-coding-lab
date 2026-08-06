# EXPERIMENT PROTOCOL — how a result gets reported here

*The failure mode this file exists to prevent: a write-up that says a technique "made
the agent dramatically better" with no baseline, no task list, and no way for anyone to
disagree with it.*

Agentic-coding advice is drowning in that. The differentiator available to this repo is
not better prompts — it's being the place where the numbers are checkable and the
negative results get published.

## The minimum

An experiment is a directory under `experiments/` with a `README.md` that answers six
questions. If it can't answer all six, it's an anecdote — which is fine, but it goes in
`articles/` and is labelled as one.

1. **The claim.** One sentence, falsifiable. "Splitting the task across two subagents
   reduces wall-clock time on multi-file refactors" — not "subagents are better".
2. **The setup.** Agent and version, model, host, repo, date. Agentic tooling moves
   weekly; a result without a date is a result without a meaning.
3. **The baseline.** What it's being compared against, run under the same conditions.
   A technique with no baseline has not been measured.
4. **The tasks.** Listed, with the actual prompts. Enough that a reader could re-run it.
5. **What happened.** Raw numbers or transcripts, plus how many runs. One run of a
   stochastic system is a story, not a measurement — say `n=1` when it's `n=1` rather
   than rounding it up into a trend.
6. **What would change the conclusion.** The condition under which you'd say you were
   wrong.

## The rules that keep it honest

- **Report the runs that failed.** Including the ones where the technique lost. A repo
  that only publishes wins is a repo whose results are worthless, because the reader
  can't tell selection from effect.
- **Separate what you measured from what you concluded.** They go in different
  sections. A conclusion that reaches past the measurement is the single most common way
  this kind of write-up goes wrong.
- **Name the confound you couldn't remove.** There is always one. Model non-determinism,
  task ordering, your own growing familiarity with the technique between runs.
- **Don't compare against a strawman baseline.** "Agent with my clever skill" versus
  "agent given a deliberately bad prompt" measures nothing.
- **If it's `n=1`, the headline says `n=1`.**

## Layout

```
experiments/<short-name>/
  README.md        the six questions
  tasks/           the prompts, verbatim
  runs/            transcripts or logs, one per run
  results.md       the numbers, separate from the interpretation
```

## The governance half

If the experiment involved an agent touching anything real, record what bounded it —
which manifest, which tier, or honestly `none`. Two reasons: reproducibility (a governed
run and an ungoverned run are different experiments), and because "did the governance
layer cost me anything measurable?" is itself one of the more interesting questions this
repo can answer.

If a governance layer *did* cost something — extra prompts, a blocked call that should
have been allowed, wall-clock overhead — publish that number too. Especially that one.
