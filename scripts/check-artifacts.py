#!/usr/bin/env python3
"""Enforce the artifact contract.

The rule this file exists to enforce is the one in the README:

    An artifact may not describe itself as safer than it is.

Mechanism can only reach part of that. What it *can* check is that a claim comes with
the thing that backs it — a tier-1 or tier-2 artifact ships the file doing the
enforcing, and an artifact nobody has run says so on its own front page. The rest is
review.

Stdlib only, on purpose: this is a content repo and nobody should need a virtualenv to
run the lint. Run `--self-test` to check the checker, including that it actually
rejects the things it claims to reject.

    ./scripts/check-artifacts.py
    ./scripts/check-artifacts.py --self-test
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARTIFACTS = REPO / "artifacts"
TEMPLATE = ARTIFACTS / "_template"

KINDS = {"skill", "plugin", "subagent", "hook", "command", "mcp-server", "recipe"}
REQUIRED = ("artifact", "kind", "hosts", "tier", "reads", "blast_radius", "verified")
UNVERIFIED_BANNER = "> **Unverified.**"
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Read a `---` delimited block of `key: value` lines. None if absent/unterminated.

    Deliberately not YAML: the contract is a flat set of scalar fields, and a real
    parser here would be a dependency plus an invitation to nest things.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None

    fields: dict[str, str] = {}
    key = None
    for line in lines[1:end]:
        if not line.strip():
            continue
        if line[:1].isspace() and key:  # continuation of the previous value
            fields[key] += " " + line.strip()
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        fields[key] = value.strip()
    return fields


def check(artifact_dir: Path) -> list[str]:
    """Return a list of contract violations for one artifact directory."""
    name = artifact_dir.name
    problems: list[str] = []
    say = problems.append

    readme = artifact_dir / "README.md"
    safety = artifact_dir / "SAFETY.md"
    if not readme.is_file():
        say("no README.md")
    if not safety.is_file():
        say("no SAFETY.md — every artifact declares its reach")
        return problems

    fields = parse_frontmatter(safety.read_text(encoding="utf-8"))
    if fields is None:
        say("SAFETY.md has no `---` frontmatter block")
        return problems

    for key in REQUIRED:
        if not fields.get(key):
            say(f"SAFETY.md is missing a non-empty `{key}:`")
    if problems:
        return problems

    if fields["artifact"] != name:
        say(f"`artifact: {fields['artifact']}` does not match the directory name `{name}`")

    if fields["kind"] not in KINDS:
        say(f"`kind: {fields['kind']}` is not one of {sorted(KINDS)}")

    try:
        tier = int(fields["tier"])
        if tier not in (0, 1, 2):
            raise ValueError
    except ValueError:
        say(f"`tier: {fields['tier']}` must be 0, 1, or 2 — see docs/SAFETY-BASELINE.md")
        tier = None

    # The load-bearing check: a tier is a claim, and a claim ships its evidence.
    enforced_by = fields.get("enforced_by")
    if tier is not None and tier >= 1:
        if not enforced_by:
            say(f"tier {tier} claims enforcement but no `enforced_by:` names the file doing it")
        elif Path(enforced_by).is_absolute() or ".." in Path(enforced_by).parts:
            say(f"`enforced_by: {enforced_by}` must be a path inside the artifact directory")
        elif not (artifact_dir / enforced_by).is_file():
            say(f"`enforced_by: {enforced_by}` does not exist — the tier {tier} claim is unbacked")
    elif tier == 0 and enforced_by:
        say(f"`tier: 0` means unenforced, but `enforced_by: {enforced_by}` is set — pick one")

    # An artifact nobody has run has to say so where a reader will see it.
    verified = fields["verified"]
    if verified == "never":
        head = "\n".join(readme.read_text(encoding="utf-8").splitlines()[:5])
        if UNVERIFIED_BANNER not in head:
            say(f"`verified: never` requires README.md to open with `{UNVERIFIED_BANNER}`")
    elif not ISO_DATE.match(verified):
        say(f"`verified: {verified}` must be an ISO date (YYYY-MM-DD) or `never`")

    return problems


def artifact_dirs() -> list[Path]:
    if not ARTIFACTS.is_dir():
        return []
    return sorted(d for d in ARTIFACTS.iterdir() if d.is_dir() and not d.name.startswith("_"))


def run() -> int:
    dirs = artifact_dirs()
    if not dirs:
        print("no artifacts yet (artifacts/ holds only the template) — contract holds vacuously")
        return 0

    failed = 0
    for d in dirs:
        problems = check(d)
        if problems:
            failed += 1
            print(f"FAIL {d.name}")
            for p in problems:
                print(f"       {p}")
        else:
            print(f"ok   {d.name}")
    print(f"\n{len(dirs) - failed}/{len(dirs)} artifacts satisfy the contract")
    return 1 if failed else 0


# --- self-test ---------------------------------------------------------------------
# A linter that has never rejected anything is indistinguishable from one that
# accepts everything. Each case mutates a valid copy of the template and asserts the
# specific violation is caught.

MUTATIONS: list[tuple[str, str, str]] = [
    # (label, frontmatter key, the value to force it to)
    ("tier claimed without the file", "enforced_by", "missing.yaml"),
    ("tier claimed with no enforced_by", "enforced_by", ""),
    ("enforced_by escapes the directory", "enforced_by", "../../world.yaml"),
    ("bogus tier", "tier", "9"),
    ("tier 0 with enforcement claim", "tier", "0"),
    ("unknown kind", "kind", "vibes"),
    ("empty blast radius", "blast_radius", ""),
    ("undeclared reads", "reads", ""),
    ("bad verified date", "verified", "last tuesday"),
    ("name does not match the directory", "artifact", "something-else"),
]


def set_field(text: str, key: str, value: str) -> str | None:
    """Rewrite one frontmatter line to `key: value`, dropping its continuations.

    Whole-line, because substring edits leave the tail of a value behind and quietly
    turn a negative test into a passing one.
    """
    lines = text.splitlines()
    out: list[str] = []
    found = False
    skipping = False
    for line in lines:
        if line.startswith(f"{key}:"):
            out.append(f"{key}: {value}".rstrip())
            found = True
            skipping = True
            continue
        if skipping and line[:1].isspace() and line.strip():
            continue  # a wrapped continuation of the value we just replaced
        skipping = False
        out.append(line)
    return "\n".join(out) + "\n" if found else None


def self_test() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "case"

        def fresh(name: str) -> Path:
            if base.exists():
                shutil.rmtree(base)
            shutil.copytree(TEMPLATE, base)
            renamed = base.parent / name
            if renamed.exists():
                shutil.rmtree(renamed)
            base.rename(renamed)
            safety = renamed / "SAFETY.md"
            safety.write_text(
                safety.read_text(encoding="utf-8").replace("artifact: _template", f"artifact: {name}"),
                encoding="utf-8",
            )
            return renamed

        # Positive: the template as shipped must satisfy its own contract.
        good = fresh("positive")
        problems = check(good)
        if problems:
            failures += 1
            print("FAIL positive: the template violates the contract it documents")
            for p in problems:
                print(f"       {p}")
        else:
            print("ok   positive: the template satisfies the contract")
        shutil.rmtree(good)

        # Negative: each mutation must be caught.
        for label, key, value in MUTATIONS:
            d = fresh("negative")
            safety = d / "SAFETY.md"
            mutated = set_field(safety.read_text(encoding="utf-8"), key, value)
            if mutated is None:
                failures += 1
                print(f"FAIL {label}: the template has no `{key}:` line to mutate")
                shutil.rmtree(d)
                continue
            safety.write_text(mutated, encoding="utf-8")
            if check(d):
                print(f"ok   rejected: {label}")
            else:
                failures += 1
                print(f"FAIL accepted: {label} — the linter did not catch it")
            shutil.rmtree(d)

        # Negative: an unrun artifact that hides it.
        d = fresh("negative")
        readme = d / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(UNVERIFIED_BANNER, "> Totally fine."),
            encoding="utf-8",
        )
        if check(d):
            print("ok   rejected: unverified artifact without the banner")
        else:
            failures += 1
            print("FAIL accepted: unverified artifact without the banner")

    print(f"\nself-test: {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv[1:] else run())
