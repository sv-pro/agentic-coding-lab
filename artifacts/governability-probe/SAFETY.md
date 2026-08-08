---
artifact: governability-probe
kind: recipe
hosts: [claude-code, claude-desktop, antigravity, codex, copilot]
tier: 0
reads: nothing directly — the procedures drive other artifacts, each with its own SAFETY.md, and your host's own configuration
blast_radius: the G5 procedure deliberately provokes an action the host considers dangerous and then makes it silently repeatable, so run it in a throwaway directory and revoke the stored approval afterwards; G2 and G3 install hooks that deny or grant, and a blanket matcher there will brick the session you are measuring from
verified: 2026-08-08
---

# Safety notes — governability-probe

## Tier 0

A set of written procedures. It enforces nothing, installs nothing, and decides nothing.
The artifacts it drives carry their own tiers — both are also tier 0, because both are
instruments.

## Coverage, stated plainly

**8 of 9 procedures have been executed** — G1, G4, G9 (Claude Code, 2026-08-06); G2, G6, G7,
G8 (Claude Code **2.1.223**, 2026-08-08); **G3 (Antigravity CLI `agy` 1.1.10**, 2026-08-08),
the first measurement here from a second host. **G5 is blocked, and G3 is still blocked on
Claude Code:** both need an action the host prompts for, and nothing prompted there.

**A note on running G3 anywhere:** it installs a hook that grants, and its deny control
installs one that blocks. Use a throwaway workspace, and confirm the hook actually fired
before believing either result — a hook that silently failed to load looks exactly like a
host that ignores hooks.

That distinction is load-bearing and is repeated on the artifact's front page. An unrun
procedure is a *hypothesis about how to measure something*. It may not work; the host may
not behave as the write-up assumes; the observable may not be observable. Treat an unrun
procedure as a proposal to be tested, and report back if it fails — a procedure that
doesn't work is a finding about the procedure.

## The one genuinely risky procedure

**G5 — "can an approval be satisfied from cache?"** requires you to:

1. get the host to propose something it considers worth interrupting you for, then
2. approve it with the *always allow* option, which makes it silently repeatable.

Step 2 is the hazard. You are deliberately installing a standing approval for a class of
action the host thought was dangerous, in order to find out whether a later "ask" can be
satisfied from it. If you do this in a real repository you have weakened that repository's
prompting for as long as the stored approval lives.

**Do it in a throwaway directory, and revoke the approval afterwards.** The README carries
the same warning inline; it is repeated here because this is the file people read when
they are deciding whether something is safe to run.

## The subtler risk: reputational, not technical

These procedures produce a **public table with vendors' names in it.** A wrong cell is a
false claim about somebody's product.

The mitigations are conventions rather than mechanisms, and they only work if followed:

- **A cell without a date and a host version is not a result.** These surfaces ship
  weekly.
- **`?` is an honest state.** "We looked and didn't find one" is not a measurement, and
  publishing it as a `no` is the failure mode this rule exists to prevent.
- **Distinguish what you ran from what you read.** The index separates `✓` observed from
  `○` documented for exactly this reason.
- **The index discloses that we build a competing thing** and every parameter is
  answerable without our tooling. If you find one that isn't, that's a bug in the index.

## What is NOT bounded

- Whether a procedure still measures what it claims after a host update.
- Whether a host's behaviour is consistent across platforms — every result so far is
  Linux, one machine, one operator.
- Anything about model behaviour. None of these procedures say a word about how good the
  assistant is, and a table of them should never be presented as if they did.
