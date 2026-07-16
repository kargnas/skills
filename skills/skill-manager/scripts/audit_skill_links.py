#!/usr/bin/env python3
"""Audit cross-file Markdown link graph inside a skill directory.

Catches two failure modes that compound silently as a skill grows:
  1. BROKEN LINKS — `path/to/x.md` mentioned in SKILL.md or a sibling that
     does not resolve to a real file. Common cause: a file was moved
     (e.g. `guides/foo.md` → `prompting/foo.md`) but the old link
     text never got patched.
  2. ORPHANS — CURATED files (under guides/, api-references/, sub-skills/,
     scripts/, etc.) reachable from nowhere except possibly themselves.
     Almost always means someone added a guide or reference file and forgot
     to add a row to the SKILL.md routing table, so the future agent has no
     way to discover it. For curated typed folders this is an ERROR: curated
     content MUST be linked from SKILL.md.
  3. TO TRIAGE — files sitting in the `references/` inbox. `references/` is
     NOT a curated folder here: it is the untriaged dump that some agent
     harnesses hardcode their writes into. Files there are EXPECTED to be
     unlinked; they await promotion into a typed folder (guides/,
     api-references/, sub-skills/) or deletion. They are reported separately
     so they never masquerade as either curated content or as orphan errors.

Both broken links and orphans are common when a skill grows past ~20 files
and edits happen across many sessions.

Usage:
    python audit_skill_links.py <skill-dir>

Defaults to the directory containing this script's parent skill if no path
is given. Treats `references/` as the inbox: its files are excluded from the
SOURCE side of the reachability check (an inbox file linking a curated file
must NOT legitimize it) and are listed under TO TRIAGE rather than ORPHANS.

Output:
    === BROKEN LINKS ===
      <src>:<line> → <target>   (resolved: <abs-or-rel>)
    === ORPHANS ===
      <file>   (curated file with zero inbound links; add a row to SKILL.md)
    === TO TRIAGE (references/ inbox) ===
      <file>   (promote into a typed folder or delete)

Exits 0 always; the report is the value. Exit code is reserved for usage
errors.

Heuristics & known false-positives:
  - The regex extracts `dir/file.ext` shapes from inline code spans and
    from explicit relative paths (`../`, `./`, `skills/<name>/`). It does
    not parse full Markdown link syntax `[txt](url)` because skills here
    use inline-code link style by convention.
  - Code-block paths like `skills/<name>/scripts/x.py` are recognized
    via the `skills/<name>/` prefix and rewritten to skill-relative.
  - Paths starting with `./` inside a deep subdir can produce false
    "broken" reports because the path-resolution branch is intentionally
    simple. Cross-check any flagged item by `ls`-ing the resolved path
    before patching.
"""
from __future__ import annotations
import os, re, sys
from collections import defaultdict
from pathlib import Path


LINK_RE = re.compile(
    r"`([A-Za-z0-9_./-]+\.(?:md|py|json|yml|yaml|safetensors|sh))(?:#[^`]+)?`"
)
PATH_RE = re.compile(
    r"(?<![\w/])"
    r"((?:\.\./|\./|skills/[a-z0-9_-]+/)?"
    r"(?:providers|prompting|workflows|local|evaluation|experiments|"
    r"scripts|catalog|prompts|templates|guides|api-references|sub-skills|"
    r"references|assets)"
    r"/[A-Za-z0-9_./-]+\.(?:md|py|json|yml|yaml))"
)

# Placeholder path shapes that appear in documentation examples, never real links.
PLACEHOLDER = {"file.md", "path/to.md", "skill.md", "jobs.json"}
# Example-config filename pattern used in docs (`config-<skill>.yml`) — never a real link.
CONFIG_EXAMPLE_SUFFIX = ".yml"
CONFIG_EXAMPLE_PREFIX = "config-"


def audit(skill_root: Path):
    all_files = set()
    for dp, _, fns in os.walk(skill_root):
        for fn in fns:
            rel = os.path.normpath(os.path.relpath(os.path.join(dp, fn), skill_root))
            all_files.add(rel)

    src_files = sorted(
        f for f in all_files
        if (f.endswith(".md") or f.endswith(".py"))
    )

    broken: list[tuple[str, str, str]] = []
    outbound: dict[str, set[str]] = defaultdict(set)

    for src in src_files:
        try:
            text = (skill_root / src).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        cands = set(LINK_RE.findall(text)) | set(PATH_RE.findall(text))
        src_dir = os.path.dirname(src)
        for raw in cands:
            t = raw.strip()
            base = os.path.basename(t)
            if t in PLACEHOLDER or (
                base.startswith(CONFIG_EXAMPLE_PREFIX) and base.endswith(CONFIG_EXAMPLE_SUFFIX)
            ):
                continue
            # Resolve path
            if t.startswith("skills/"):
                # skills/<name>/foo.md → drop skills/<name>/
                parts = t.split("/", 2)
                resolved = parts[2] if len(parts) >= 3 else t
            elif t.startswith("../") or t.startswith("./"):
                resolved = os.path.normpath(os.path.join(src_dir, t))
            elif "/" in t:
                root_cand = t
                sib_cand = os.path.normpath(os.path.join(src_dir, t)) if src_dir else t
                resolved = root_cand if root_cand in all_files else sib_cand
            else:
                resolved = os.path.normpath(os.path.join(src_dir, t)) if src_dir else t
            outbound[src].add(resolved)
            if resolved not in all_files and "*" not in resolved and not resolved.endswith("/"):
                broken.append((src, raw, resolved))

    # Build inbound (exclude self-links AND references/ inbox as a SOURCE).
    # references/ is the untriaged dump, NOT curated: an inbox file linking a
    # curated file must NOT count as making that curated file reachable.
    inbound: dict[str, set[str]] = defaultdict(set)
    for s, ts in outbound.items():
        if s.startswith("references/"):
            continue
        for t in ts:
            if t in all_files and t != s:
                inbound[t].add(s)

    # Split unreachable files into two buckets by location:
    #   - references/  → TO TRIAGE (expected; awaiting promotion or deletion)
    #   - everything else (curated typed folders) → ORPHAN (error: link from SKILL.md)
    orphans = []
    to_triage = []
    for f in src_files:
        if f == "SKILL.md":
            continue
        if f.startswith("references/"):
            to_triage.append(f)  # inbox file — promote into a typed folder or delete
            continue
        if not inbound.get(f):
            orphans.append(f)

    return broken, orphans, to_triage


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: audit_skill_links.py <skill-dir>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    broken, orphans, to_triage = audit(root)

    print(f"=== AUDIT: {root} ===")
    print()
    print(f"=== BROKEN LINKS ({len(broken)}) ===")
    for s, raw, r in broken:
        print(f"  {s}\n    raw:      {raw}\n    resolved: {r}\n")
    print(f"=== ORPHANS ({len(orphans)}) ===")
    for f in orphans:
        print(f"  {f}")
    print()
    print(f"=== TO TRIAGE (references/ inbox, {len(to_triage)}) ===")
    for f in to_triage:
        print(f"  {f}")
    print()
    print(f"=== SUMMARY ===")
    print(f"  broken: {len(broken)}")
    print(f"  orphans: {len(orphans)}")
    print(f"  to_triage: {len(to_triage)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
