# Importing External Skills (GitHub → local skills dir)

Use when the user wants to install a community SKILL.md (typically found via a skill-discovery search) into their local skill directory and commit it. Common phrasing: "이 스킬 추가해줘", "<skills-dir>/<name>/ 로 추가해서 커밋/푸시", "install this skill from <repo>".

## Procedure

### 1. Collision check (MUST)

Before cloning, check the target host for a name collision:

```bash
ls <skills-dir>/ | grep -i <proposed-name>
```

If a same-name skill exists, decide explicitly with the user:
- **Rename** (e.g. `write` → `translator-zh` when `translator` already exists)
- **Replace** (only if the user confirms the old one is dead)
- **Absorb** (merge content — use the merge procedure in SKILL.md)

NEVER `mv` or `cp -r` blindly into the target dir — it nests inside the existing same-named directory and produces `skills/<name>/<name>/SKILL.md`.

### 2. Shallow clone to /tmp

```bash
cd /tmp && rm -rf <repo-tmp> && git clone --depth 1 <upstream-url> <repo-tmp>
```

Inspect structure first:
```bash
ls <repo-tmp>/<path-to-skill>/
wc -l <repo-tmp>/<path-to-skill>/SKILL.md <repo-tmp>/<path-to-skill>/references/* <repo-tmp>/<path-to-skill>/guides/* 2>/dev/null
```

### 3. Copy support files into TYPED folders, rewrite SKILL.md

Upstream usually parks all support docs in one `references/` folder. Do NOT replicate that dump — classify each file by kind (read-as-guidance → `guides/`, grepped lookup data → `api-references/`) and route it there. `guides/` is the safe default for prose docs:
```bash
mkdir -p <skills-dir>/<new-name>/guides
cp /tmp/<repo-tmp>/<path>/references/*.md <skills-dir>/<new-name>/guides/
# then move any lookup/schema files into api-references/ and re-point SKILL.md links
```

Rewrite SKILL.md (do not just `cp` — frontmatter usually needs normalization):

**Frontmatter normalization checklist:**

| Field in upstream | Action |
|---|---|
| `name: <old-name>` | Replace with the chosen local name |
| `when_to_use: "..."` | **Merge into `description`** — opencode's standard frontmatter has no `when_to_use` field, it's silently dropped from trigger matching |
| `allowed-tools: [...]` | Keep only if the host (Claude Code/OpenCode/Codex) honors it; otherwise drop |
| `metadata:` | Keep, add `upstream: "<repo-url> (<path>)"` for provenance |
| First-person voice ("I can help...") | Rewrite to third-person ("Strips AI patterns...") |

Trigger keywords (CJK, synonyms, file types) MUST be inside `description` — that's what the router matches.

### 4. Git add + commit + push

```bash
cd <skills-repo> && git add skills/<new-name>/
git diff --cached --stat skills/<new-name>/   # sanity check file count
git commit -m "Add <new-name> skill from <owner>/<repo>

Source: <upstream-url> (<path>, v<version>)
- Renamed: <old> -> <new> (<reason>)
- <other frontmatter changes>
- <reference file count> reference files"
git push
```

Verify push succeeded (look for the commit hash line `xxxxx..yyyyy main -> main`).

### 5. Don't symlink unless cross-agent

If the skill should be shared across multiple hosts (Claude Code + Codex + OpenCode), follow the cross-agent pattern in SKILL.md's "Where the skill directory lives" section. For single-host import (most cases), a direct copy is correct — symlinks add complexity for no benefit.

## Common pitfalls

- **`when_to_use` orphan**: upstream uses it heavily, you copy SKILL.md verbatim, the skill never triggers because router only reads `description`. Always merge or test trigger.
- **Same-day burst commits**: a 0-star repo with 1 commit yesterday is NOT battle-tested. Check the repo's commit-history spread before importing — prefer skills iterated across 2+ distinct days.
- **Importing a repo that bundles many skills**: e.g. `tw93/Waza` has `skills/write/`, `skills/X/`, `skills/Y/`. Import only what the user asked for. If they want the full set later, that's a separate decision.
- **`description` over 1024 chars**: trigger keyword stuffing easily blows the limit. Trim or move some keywords into the body.
- **Forgetting to verify push**: `git push` can fail silently (auth, no-upstream, conflicts). Always read the last few lines of output.

## When to escalate

- Skill structure looks fundamentally wrong (no frontmatter, mixes runtime code into SKILL.md, references nested 3 deep) → don't import as-is. Either fix it locally before commit, or tell the user it needs rewrite before being useful.
- Upstream license is unclear or restrictive → flag before commit. Many agent-skill repos are MIT/Apache, but check.

## Locally-orphaned skills (non-registry locations)

Sometimes the skill you need is already on disk but invisible to the host's skill listing because it lives in a non-registry location — an external worktree, a project-local `.claude/skills/`, or a vendored skill dir inside an arbitrary repo. Before declaring a class of work uncovered, grep those locations too.

If you find a full skill system in an external location, the import procedure is:

1. Copy the external directory into the target skills dir.
2. Find any hardcoded old-worktree paths inside SKILL.md and the scripts — rewrite to the new canonical location.
3. **Do NOT rewrite hardcoded paths inside historical output/run-record files** — they are execution records, not active code paths. Leave them as-is.
4. Run a smoke test of one bundled script before declaring the import successful. External systems may require heavy local dependencies the new host lacks. Better to know on day 1.
5. Add the source path to `metadata.upstream` for provenance, so future agents know where to pull updates from.
