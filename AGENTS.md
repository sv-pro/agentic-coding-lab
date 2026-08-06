# AGENTS.md — working in this repo

Guidance for AI coding agents (Claude Code, Codex, Antigravity, …) and humans. Read this
first. It is the cross-agent source of truth for *how to work here*; per-agent files
(`CLAUDE.md`, etc.) point here rather than duplicating it.

## What this repo is

**`agentic-coding-lab` — techniques for getting more out of AI coding agents, each
shipped with an honest account of what it can reach.** Artifacts, experiments, articles.

It is a **consumer** of [`ai2rules`](https://github.com/sv-pro/ai2rules), the governance
kernel that provides the safety half. Read [`docs/CHARTER.md`](docs/CHARTER.md) before
adding anything — the scope boundary is written down precisely because this cluster's
documented failure mode is repos that grew past their charter.

## The three rules that are not negotiable

1. **One-way dependency.** This repo may depend on, cite and configure `ai2rules`.
   `ai2rules` may never depend on this repo, and **nothing here may become an input to a
   governance decision.** An artifact is a convenience; conveniences do not get a vote
   on authority.
2. **No unearned safety claim.** An artifact may not describe itself as safer than it
   is. Tiers are defined in [`docs/SAFETY-BASELINE.md`](docs/SAFETY-BASELINE.md) and
   partially enforced by `scripts/check-artifacts.py`. The words "hardened",
   "sandboxed" and "safe" are load-bearing and get checked in review.
3. **Point, don't duplicate.** The thesis, the kernel design and the decision record
   live upstream. Link them. A second copy of an argument drifts within a month.

## Before you commit

```bash
./scripts/check-artifacts.py             # the artifact contract
./scripts/check-artifacts.py --self-test # the linter's own negative tests
```

Both run in CI. If you touch an artifact's manifest, also re-run its `verify.sh`
against a real `harness` binary and update the date in its `SAFETY.md` — CI cannot do
this, because CI does not build Rust.

## Verifying a manifest locally

You need the `harness` binary from an `ai2rules` checkout:

```bash
cd /path/to/ai2rules && cargo build --release -p cli-harness
./artifacts/<name>/verify.sh /path/to/ai2rules/target/release/harness
```

`harness gate --world <manifest>` reads one `GateRequest` on stdin and writes one
`GateResponse` on stdout. The ABI is documented upstream in
[`docs/harness-gate-abi.md`](https://github.com/sv-pro/ai2rules/blob/main/docs/harness-gate-abi.md).

## Standards

- **Honesty over polish.** Report what actually happened — the failing run, the skipped
  step, the technique that lost to the baseline. This repo's entire differentiator is
  being the place where that gets published.
- **Date everything.** Agentic tooling moves weekly. An undated claim has no shelf life.
- **Verify the real thing.** That a manifest *compiles* is not that it *decides the way
  you said*. Run the calls.
- **Never widen an artifact's reach to make a demo work.** If the recipe needs a
  capability the manifest denies, that is a finding about the recipe, and it goes in
  the write-up.
- **Decisions that close off an alternative get recorded** upstream in
  `ai2rules/DECISIONS.md`, not here. This repo holds no decision log of its own — see
  rule 3.

## Repo layout

```
artifacts/     copyable things, each with README.md + SAFETY.md
  _template/   the skeleton; carries a real, kernel-verified world.yaml
experiments/   measurements, per docs/EXPERIMENT-PROTOCOL.md
articles/      practitioner write-ups
docs/          CHARTER · SAFETY-BASELINE · EXPERIMENT-PROTOCOL
scripts/       check-artifacts.py — the contract lint, stdlib only
```

## What not to do here

- Don't add a decision log, a thesis file, or an architecture doc. Those live upstream.
- Don't vendor any part of `ai2rules`. Reference a version; don't copy code.
- Don't add a build system, a site generator, or a package. This is a content repo with
  one lint. Adding a toolchain is a decision, and decisions go upstream first.
- Don't commit an artifact you haven't run. If you must, set `verified: never` and put
  the banner on it — that path is deliberately open and deliberately visible.
