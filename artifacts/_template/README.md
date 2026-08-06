> **Unverified.** This is the artifact template, not a working artifact. Nobody has
> run it as part of a real workflow, because there is nothing to run.

# _template — copy me

The skeleton every artifact in this repo starts from.

```bash
cp -r artifacts/_template artifacts/my-artifact
cd artifacts/my-artifact
# rewrite SAFETY.md's frontmatter, then this file
```

## What each file is for

| File | Purpose |
|---|---|
| `README.md` | This page. What the artifact does, how to install it, how to use it. Written for someone who has never heard of this repo. |
| `SAFETY.md` | Machine-checked frontmatter plus the honest prose: what it reads, what it can reach, what bounds it, what doesn't. |
| `world.yaml` | The enforcement file named by `enforced_by`. Required at tier ≥ 1. Delete it if your artifact is tier 0 — and then set `tier: 0`, don't leave the claim behind. |
| `verify.sh` | Re-runs the verdict table in `SAFETY.md` against a real kernel. |

## The three things reviewers will push back on

1. **A tier you didn't earn.** Tier 2 means the dangerous capability is *absent from
   the compiled world*. If your artifact merely prompts before doing the dangerous
   thing, that is tier 1, and tier 1 is a perfectly respectable answer.
2. **A `reads:` field that says "nothing" when it doesn't.** If the artifact touches an
   issue tracker, a web page, a log file or another agent's output, it reads untrusted
   input. Say so.
3. **A blast radius written as reassurance.** "Minimal risk" is not a blast radius.
   "It can force-push to any remote the developer has credentials for" is.

## Filling in the manifest

`world.yaml` here is real and it compiles — the verdict table in
[`SAFETY.md`](SAFETY.md) came out of the actual kernel, not out of a guess. The two
edits most artifacts need:

- **Delete actions you don't need.** Deleting is the strongest edit available. An action
  that isn't declared is `ABSENT`: there is no prompt to phrase persuasively, because
  the agent cannot form the request at all. Start from too little and add back.
- **Declare your `channels`.** If your artifact ingests something, add the channel it
  arrives on with `taint: true`. An undeclared channel defaults to untrusted, which is
  safe but gives confusing verdicts — you'll see `ABSENT` where you expected `DENY`,
  because the capability was never visible in the first place.

Full definitions of the tiers, and the real commands behind each, are in
[`docs/SAFETY-BASELINE.md`](../../docs/SAFETY-BASELINE.md).
