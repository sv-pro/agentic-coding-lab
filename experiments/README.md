# experiments/

Did the technique actually help?

**Nothing here yet.** The protocol is written down first, in
[`docs/EXPERIMENT-PROTOCOL.md`](../docs/EXPERIMENT-PROTOCOL.md), because deciding what
counts as a result *after* seeing the numbers is how this kind of write-up goes wrong.

## The short version of the protocol

An experiment answers six questions: the claim (falsifiable, one sentence), the setup
(agent, model, version, date), the baseline, the tasks (with the actual prompts), what
happened (raw, with the number of runs), and what would change the conclusion.

Two rules do most of the work:

- **Negative results get published.** A repo that only shows wins is a repo whose
  results carry no information, because nobody can separate selection from effect.
- **`n=1` says `n=1` in the headline.** One run of a stochastic system is a story.

## Layout

```
experiments/<short-name>/
  README.md      the six questions
  tasks/         the prompts, verbatim
  runs/          transcripts or logs, one per run
  results.md     the numbers, kept separate from the interpretation
```

## Questions worth running

Not a roadmap — a list of things this repo is positioned to answer and most write-ups
aren't:

- Does a governance overlay cost measurable wall-clock time, or only prompts?
- How many approval prompts per hour before a developer stops reading them?
- Do subagents beat one long context on multi-file refactors, and at what task size
  does the answer flip?
- Does a skill that reads an issue tracker survive a deliberately hostile issue body?
  (Run this one under a manifest.)
