# Merge-via-Absorption Pattern

> Verified 2026-05-24 on a mobile-UX audit skill (merged two source skills into one self-contained skill via an in-session subagent delegation, 9 min wall).

A specific variant of the merge procedure where:
- The new skill ABSORBS knowledge from N source skills (rewrites in its own voice).
- The new skill is RUNTIME-INDEPENDENT — if sources are uninstalled, the new skill still works.
- Sources STAY on disk for other contexts (no deletion, no absorption-via-replacement).

This differs from the standard merge procedure in `guides/modular-architecture.md` (which assumes sources collapse into the merged skill). Use absorption when sources have OTHER consumers and you only need ONE narrow use case unified.

## When to choose absorption over standard merge

| Situation | Pick |
|---|---|
| Both source skills are general-purpose libraries with other use cases | Absorption |
| Sources are narrow variants that fully collapse into the new skill | Standard merge (delete sources) |
| Sources are external (community / upstream) and you can't modify them | Absorption (always — you can't delete what you don't own) |
| Sources are big knowledge dumps and you only want ONE workflow extracted | Absorption |

## The absorption spec template

Every absorption spec MUST include these blocks:

1. **Hard rule "READ AND ABSORB — do NOT runtime-reference"** listing each source with absolute path.
2. **A markdown table** mapping each source → (what to extract, how it appears in the merged skill). One row per source. This forces the delegate to think in terms of synthesis, not concatenation.
3. **Forbidden-strings list** for the merged skill body and references. Example: `"see ${source-name}", "consult ${source-name}", any path like ~/.agents/skills/${source-name}"`. These become the grep gate in acceptance criteria.
4. **`metadata.upstream` frontmatter requirement** — the ONLY place source-skill identifiers may appear (as GitHub URLs, for re-sync provenance).
5. **A grep self-containment acceptance gate** that runs after build:
   ```
   grep -rE "(${source-1}|${source-2}|/.agents/skills)" <new-skill-dir>/
   ```
   Must return ZERO matches except possibly `metadata.upstream` URL line of SKILL.md frontmatter.

## Why the grep gate matters

Without it, weaker delegates default to "respectful citation" mode and pepper the new skill with `see references/foo.md in <source-skill> for the WebKit bug list`. Those lines silently rot — when the source skill is later refactored, renamed, or uninstalled, the merged skill breaks. The grep gate catches this at build time, not 6 months later.

Empirically, the grep gate also catches absorption laziness: a delegate that copy-pastes whole sections from sources usually leaves the source's internal cross-references (`see ../core/X.md`) intact. Grep flags them; the delegate must rewrite into the merged skill's own structure.

## Delegate-of-choice for absorption work

In rough order of preference:

1. **The host's in-session subagent delegation tool** (Claude Code `Task`/`Agent`, or the equivalent on other hosts) with file+terminal toolsets and the full spec in the delegation context. Uses the parent session's model + auth pool — no CLI quota issues. Verified pattern: 9-min wall, 26 api_calls, completed first try after 3 CLI delegate attempts failed on auth/quota.
2. **`opencode run`** in the background — only when the parent session model is constrained AND the opencode auth pool is healthy.
3. **`codex exec`** stdin — only when both above paths are blocked.

The CLI subprocess paths (2, 3) carry the well-documented hang / quota / token-reuse failure modes. The in-session path inherits parent session auth and avoids all CLI-credential failure modes by construction.

## Acceptance criteria template for absorption skills

Every absorption-pattern delegation MUST include in the spec:

```
1. find <new-skill-dir>/ -type f | sort  ==  <exact whitelist>
2. grep -rE "(<source-1>|<source-2>|/.agents/skills)" <new-skill-dir>/  ==  0 matches (except metadata.upstream URL)
3. <main script> --help  runs cleanly
4. quick_validate.py <new-skill-dir>/  returns zero errors
5. <smoke run command>  produces <expected artifact list>
6. <domain-specific coverage check>, e.g. "grep -c rule_id <catalog>.md  >=  N"
```

The grep gate (criterion 2) is the absorption-specific gate. Without it the build superficially succeeds while leaving runtime dependencies on sources.

## What the delegate prints after completion

The spec MUST require this exact print order to stdout:

```
1. git status -s from the host repo (confirm only new-skill-dir touched)
2. find <new-skill-dir>/ -type f | sort
3. wc -l on every .md file (verifies size caps)
4. The literal string SMOKE_RUN_PASS (only if all smoke artifacts present)
5. One-paragraph summary: decisions made unprompted, trade-offs taken, open caveats
```

Step 4's `SMOKE_RUN_PASS` is a hard signal — the parent agent greps for it in the delegate's reported summary. Anything less means re-run the smoke before accepting completion.

## Known absorption pitfalls

- **Spec ambiguity → silent default to copy-paste**: weaker delegates faced with "merge X + Y" without an explicit absorption directive will concatenate. Always include the table from block 2 above.
- **Forgetting `metadata.upstream`**: provenance is the ONLY place source identity is permitted. Without it the merged skill can never be re-synced when sources update upstream.
- **Smoke run with environment-dependent prereqs**: if the smoke needs `pip install X && X install Y` (e.g. Playwright + Chromium), document the install in the spec's smoke-run criterion AND in the merged skill's prereq section. Verified case: smoke needed `pip install --break-system-packages playwright && playwright install chromium` because the host had `python3 -m pip` only on `/opt/homebrew/bin/python3`, not on the venv python. The merged skill's prereq line was correct; only the parent agent's smoke re-run had to discover the system-python path.
- **Source-skill knowledge that doesn't map cleanly to the merged skill's use case**: don't force-include it. Verified case: one source had rules for landscape phones, large-text reflow, and chart density — the merged skill absorbed those that are auto-detectable (44×44, safe-area, dvh, inputmode) and dropped those that need human judgment (chart density, semantic intent). Document the dropped knowledge briefly in the summary so future reviewers know it was a choice, not an oversight.
