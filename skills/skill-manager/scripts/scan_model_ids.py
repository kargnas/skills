#!/usr/bin/env python3
"""
Scan a skill directory for LLM model IDs and classify each one against the live models.dev catalog.

Usage:
    scan_model_ids.py <skill_directory>

Prints a markdown table with one row per match, then a last line `matches=N outdated=K unknown=U`.
Status is CURRENT (newest release in its family at the model's origin provider), OUTDATED (a newer
release exists there), or UNKNOWN (the catalog cannot place the ID in a family).
"""

import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

# Fetched on every run: any model table written into a skill is stale by the time it ships.
CATALOG_URL = "https://models.dev/api.json"


def load_catalog():
    # models.dev answers 403 to urllib's default "Python-urllib" User-Agent.
    request = urllib.request.Request(CATALOG_URL, headers={"User-Agent": "scan_model_ids"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def build_pattern(catalog):
    # IDs without a digit carry no version, so they cannot go stale, and many are ordinary
    # words that would flood the scan.
    ids = {model_id for provider in catalog.values() for model_id in provider.get("models", {})
           if re.search(r"\d", model_id)}
    # Longest first, so a full ID wins over a shorter catalog ID that is its suffix.
    alternation = "|".join(map(re.escape, sorted(ids, key=len, reverse=True)))
    # Group 1 is the catalog ID. Pinned snapshots append a date the catalog often omits
    # ("-2025-12-11", "-20251211"), so the date is matched but not used for lookup.
    # An ID is bounded by whitespace or punctuation. A sentence-ending period still ends it,
    # but a dot followed by a word character continues the token.
    return re.compile(rf"(?<![\w./-])({alternation})(?:-\d{{4}}-\d{{2}}-\d{{2}}|-\d{{8}})?(?![\w/-]|\.\w)")


def index_catalog(catalog):
    """Return the canonical IDs that re-hosts point to, and each family's origin provider."""
    canonical, votes = set(), Counter()
    for provider in catalog.values():
        for entry in provider.get("models", {}).values():
            origin_id = entry.get("canonical_model_id")
            if origin_id:
                canonical.add(origin_id)
                if entry.get("family"):
                    votes[entry["family"], origin_id.split("/", 1)[0]] += 1
    family_origin = {}
    for (family, origin), _ in votes.most_common():
        family_origin.setdefault(family, origin)
    return canonical, family_origin


def outputs(entry):
    return sorted((entry.get("modalities") or {}).get("output") or [])


def classify(catalog, index, model_id):
    """Return (origin provider, entry, newest release in its family), or None when unknown."""
    canonical, family_origin = index
    resolved = fallback = None
    for name, provider in catalog.items():
        entry = provider.get("models", {}).get(model_id)
        if not entry:
            continue
        # Re-hosts copy models under their own IDs and families, so only the origin catalog
        # (the provider that canonical_model_id points to) decides what is newest.
        origin_id = entry.get("canonical_model_id") or (
            f"{name}/{model_id}" if f"{name}/{model_id}" in canonical else None)
        if origin_id:
            origin, origin_model = origin_id.split("/", 1)
            origin_entry = catalog.get(origin, {}).get("models", {}).get(origin_model)
            if origin_entry:
                resolved = (origin, origin_entry)
                break
        # Origins drop retired IDs that re-hosts still list; the family still names the origin.
        if fallback is None and entry.get("family") in family_origin:
            fallback = (family_origin[entry["family"]], entry)
    origin, entry = resolved or fallback or (None, None)
    if not entry or not entry.get("family") or not entry.get("release_date") or origin not in catalog:
        return None
    # A newer image or audio model in the same family is not an upgrade for a text model, and
    # unversioned or "-latest" aliases are not pinned releases.
    wanted = outputs(entry)
    family = [m for m in catalog[origin]["models"].values()
              if m.get("family") == entry["family"] and m.get("release_date")
              and re.search(r"\d", m["id"]) and "latest" not in m["id"]
              and (not wanted or outputs(m) == wanted)]
    # Same-day variants ("-customtools", "-vision-exp") lose to the shorter base ID.
    newest = max(family or [entry], key=lambda m: (m["release_date"], -len(m["id"])))
    return origin, entry, newest


def cost(entry):
    price = entry.get("cost") or {}
    if "input" not in price or "output" not in price:
        return "?"
    return f"{price['input']} / {price['output']}"


def main():
    if len(sys.argv) != 2:
        print("Usage: scan_model_ids.py <skill_directory>")
        sys.exit(1)
    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)
    try:
        catalog = load_catalog()
    except OSError as error:
        print(f"Error: cannot download {CATALOG_URL}: {error}", file=sys.stderr)
        sys.exit(2)

    pattern = build_pattern(catalog)
    index = index_catalog(catalog)
    counts = {"matches": 0, "outdated": 0, "unknown": 0}
    print("| Location | ID | Status | Newest in family | Origin provider | Old $/1M in / out | Newest $/1M in / out |")
    print("|---|---|---|---|---|---|---|")
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binary assets cannot hold a model ID the skill sends
        for line_number, line in enumerate(text.splitlines(), 1):
            for match in pattern.finditer(line):
                written = match.group(0)
                location = f"{path.relative_to(root)}:{line_number}"
                counts["matches"] += 1
                result = classify(catalog, index, match.group(1))
                if result is None:
                    counts["unknown"] += 1
                    print(f"| {location} | `{written}` | UNKNOWN | - | - | - | - |")
                    continue
                origin, entry, newest = result
                status = "OUTDATED" if newest["release_date"] > entry["release_date"] else "CURRENT"
                counts["outdated"] += status == "OUTDATED"
                print(f"| {location} | `{written}` | {status} | `{newest['id']}` | {origin} | {cost(entry)} | {cost(newest)} |")
    print(" ".join(f"{name}={value}" for name, value in counts.items()))


if __name__ == "__main__":
    main()
