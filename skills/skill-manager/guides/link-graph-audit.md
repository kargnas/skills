# Link-graph audit and repair for medium-large skills

When a skill grows past ~20 files spread across `providers/`, `prompting/`, `workflows/`, `scripts/`, etc., two failure modes compound silently across editing sessions:

1. **Broken cross-file links** — a file gets moved (e.g. `references/foo.md` → `prompting/foo.md`) and old references in sibling files keep pointing at the dead path. The author never notices because Markdown link resolution is lazy.
2. **Orphan nodes** — a new workflow or prompting file gets added but no SKILL.md row is added to point at it. The next agent that loads the skill has no way to discover the file exists.

Both are invisible to ordinary editing but they degrade the umbrella's value over time.

## When to run

- After moving / renaming / consolidating files inside a skill
- Before declaring a multi-session refactor "done"
- During the conversation-review maintenance pass when the touched skill has many internal files
- Periodically on the user's most-edited umbrella skills

## How to run

```bash
uv run python <skills-dir>/skill-manager/scripts/audit_skill_links.py \
  <skills-dir>/<skill-name>
```

(or whatever host directory the skill lives under)

Output:

```
=== AUDIT: /path/to/skill ===

=== BROKEN LINKS (N) ===
  <src>
    raw:      providers/foo.md       ← what the source file wrote
    resolved: providers/foo.md       ← where audit tried to resolve it

=== ORPHANS (M) ===
  prompting/new-file.md              ← no inbound link from anywhere

=== SUMMARY ===
  broken: N
  orphans: M
```

## Triage rules

### Scope: what counts as a node

By default the audit treats `SKILL.md` as the canonical entry point. Curated typed folders (`guides/`, `api-references/`, `sub-skills/`, `scripts/`, ...) ARE in scope for orphan reporting: a curated file with no inbound link from SKILL.md is an ORPHAN error, because curated content must be discoverable. The `references/` folder is the exception — it is the untriaged inbox (some agent harnesses hardcode dumps there), so its files are reported under TO TRIAGE rather than ORPHANS and are excluded from the SOURCE side of reachability (an inbox file linking a curated file must NOT legitimize it). Broken links *into* `references/` are still reported.

### Index direction: prefer one-way from SKILL.md

The desired shape is a **single-direction graph rooted at SKILL.md**, not a fully bidirectional one. When closing orphans, add a row from `SKILL.md` to the leaf. Do NOT also add a back-link from the leaf to other siblings just to "balance" the graph — those reverse pointers add noise without helping discovery, and the user has explicitly pushed back on bidirectional reference soup.

If a sibling-to-sibling link genuinely helps in-context navigation (e.g. `providers/foo.md` referring to its sister `providers/bar.md` for routing fallback), keep it terse — one inline mention or one row in a small routing table. Avoid `> Index: ...` super-headers, `## Related` footers that duplicate the SKILL.md row, or "see also" sections that list every neighbouring file.

### Link copy tone

Keep cross-file references short. One sentence, one path. Long, chatty link blocks defeat the purpose. A link row's job is to say "this exists and covers X" — not to summarise the target file's content.

### Broken-link entries

| Situation | Fix |
|---|---|
| File was moved; old link still points at the old path | Patch every source listed in `raw:` to use the new path. |
| File was deleted; link is dead | Patch sources to remove or redirect the link. |
| False positive: resolved path is actually correct but audit's resolver got confused (most common with `../../` deep relatives) | Verify with `ls <resolved>` first. If the file exists, ignore the report. Common in workflows that sit two levels deep. |

### Orphan entries

| Situation | Fix |
|---|---|
| File is real and useful, but SKILL.md has no row pointing at it | Add a single concise row to the SKILL.md routing table. Description should state WHAT the file covers + WHEN to load it. |
| File is real but only ever reached from a sibling (not SKILL.md) | Acceptable if the sibling is itself indexed from SKILL.md. The audit treats SKILL.md as the canonical entry point but cross-sibling links count as inbound. |
| File is stale / abandoned | Delete it, or move it into the typed folder matching its kind (`guides/`, `api-references/`, ...) if the content has lasting value. Do NOT park it in `references/` — that inbox is for untriaged agent dumps, not a retirement home for curated files. |

### Patterns that produce false positives

Known limitations of the simple resolver:

- **Deep relative paths (`../../foo.md`)** sometimes resolve incorrectly when the source lives two levels deep. Always `ls` the resolved path before patching.
- **Backslash-escaped quotes inside code-block code (`body[\"logs\"]`)** can confuse the inline-code regex if they leak from a tool call. Use plain `body["logs"]` in SKILL.md.
- **Imports between Python modules (`from my_config import X`)** are NOT tracked. The audit only inspects Markdown-style references. A Python lib module reachable only via `from X import Y` will show as an orphan even though it is in active use. Treat that case manually.

## What this is NOT

- It does not validate that the linked content is *correct* — only that the path resolves.
- It does not enforce that every routing-table row has a body link to it — only that every file has at least one inbound reference.
- It does not run sanitization (model-ID freshness) or trigger validation — those have their own passes in skill-manager.

## Example session

On a 45-file umbrella skill (verified 2026-05-23): initial audit surfaced 4 real broken links (3 stale `references/X.md` paths after a `references/` → `prompting/` reorg, 1 mis-relative `SKILL.md` from inside a subdirectory) and 3 real orphans (a model-prompting note, a workflow doc, a verifier script). Six SKILL.md rows + four target-path patches closed all of them in a single pass.

After the user clarified that the desired graph is **one-way from SKILL.md, not bidirectional**, a follow-up pass also removed earlier-added back-links (e.g. an `> Index:` header in a workflow doc, a `## Related` footer, a sibling-link from a provider doc's detail-routing table back to a sub-workflow doc). BFS reachability from SKILL.md was preserved (44/45 nodes, 1 remaining unreachable was a Python lib module reached only via `from X import ...` which the Markdown audit does not track — see false-positives section above).
