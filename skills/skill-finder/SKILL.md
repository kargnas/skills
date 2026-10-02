---
name: skill-finder
description: "Finds and ranks installable SKILL.md agent-skill packages for a task: discovers via the `npx skills` marketplace plus a GitHub-wide sweep, then ranks by real human iteration — semantic polish-days, content depth (production vs toy signals), and optional social review — not stars or install counts. Use for skill discovery: find/search a skill, 'is there a skill for X', task-specific skill lookup, compare skills. Delegates the GitHub search itself to the oss-finder skill; finding general OSS libraries/frameworks/tools (not SKILL.md packages) also goes to oss-finder."
---

# Find Skills

> **ONE SENTENCE:** Discover installable SKILL.md packages for a task and rank by real human iteration (semantic polish-days) + content depth — not stars or install counts.

This skill owns the **skill-evaluation** workflow. The raw GitHub search that feeds it is owned by the **oss-finder** skill (backends, PAT pool, polish-day scripts), which must be installed next to this skill: `<skills-dir>/oss-finder/` where `<skills-dir>` is the directory containing this skill. skill-finder builds the query, delegates the sweep, then applies the quality gates below.

## Two discovery surfaces — launch in PARALLEL (MANDATORY)

Fire both at the start of every discovery request, concurrently (async), then union the results into one candidate pool. This is NOT a fallback chain.

| Surface | Tool | Role |
|---|---|---|
| **MARKETPLACE** | `npx skills find <query>` (Path A) | skills.sh install-count signal + install recipe |
| **GITHUB** | the **oss-finder** skill → `<skills-dir>/oss-finder/scripts/finder.py` (Path B) | GitHub-wide SKILL.md sweep, polish-day ranked, across REST + Blackbird + grep.app + PAT pool |

**Precondition not met — ASK the user, never silent-skip.** oss-finder's Step 0 (`python3 <skills-dir>/oss-finder/scripts/gh_pool.py --check`) runs before the GitHub surface launches. If it reports `SETUP NEEDED` (PAT pool missing or `gh` not logged in), relay the exact gap to the user and collect the setup before re-launching that surface — do not run Path B without it. If `npx`/network fails, report the actual error.

**VERIFY [S-PAR]:** before printing any candidate table, both surfaces launched (or paused for user input on an unmet precondition) and each surface's raw candidate count is reported. A pool from a single surface undercounts the long tail.

### [S-LAZY] Local presence ≠ skip the sweep (MUST)

A locally-installed skill that already looks like a fit MUST NOT narrow, defer, or cancel the sweep. Local skills (whatever registries your agent reads, the session's pre-loaded list) are frozen snapshots, NOT live search results. Run both surfaces in full even when an on-disk skill seems to cover the topic — "there is already a similar one installed" is never a reason to downgrade the search.

| Rationalization | Reality |
|---|---|
| "Local already has it, done." | Local is a frozen copy; a newer, more-polished upstream may exist. Search. |
| "Running the full sweep is overkill here." | The sweep IS the job — skipping it defeats skill-finder. |
| "I'll just recommend the local one and stop." | Recommending without searching is exactly the laziness this gate blocks. |

---

## Path A — Curated marketplace (`npx skills`)

### Quick discover + install

```bash
npx skills find <query>
```

Returns lines like `vercel-labs/agent-skills@vercel-react-best-practices` with a `https://skills.sh/...` URL.

**Install-target warning:** `npx skills add ... -g` can fan out through every agent-home convention at once. Stage the upstream package in a temporary `HOME`, then copy exactly ONE selected skill dir into the user-approved target. See [references/install.md](references/install.md) for the staging recipe, the "install under a different name" step, and the collision check (`test ! -e "{target}"`).

**VERIFY:** the chosen target has `SKILL.md`, its `name:` frontmatter matches the directory name, and no command created a second install location or a registry-to-registry symlink.

### Path A query-variant retry

If the first query returns ≤3 candidates OR none has a description matching the actual workflow (vs. matching the term by accident — e.g. `braindump` returning a file-dump CLI), the query was too generic. Re-run with 2-3 synonym variants, the user-language verb (`reorder`, `consolidate`) instead of the noun-form, and a non-English variant when the workflow is culturally loaded. Stop variant-bombing after 4 marketplace queries — if nothing surfaces, Path A is genuinely empty for this niche; rely on the GitHub surface.

### Path A install-count trap

`npx skills find` orders by install count — a popularity proxy, NOT a quality proxy. Viral / SEO-friendly / generic-named skills bubble up; production-grade skills with descriptive-but-unsearchable names stay buried. When the top results have wildly different install counts, MUST fetch all top-5 skills.sh pages and judge by content depth (see [S4b]), not install count.

### Path A stale-slug / hidden-path verification

Skills.sh pages can be stale or hide the real repo path. Do NOT assume `skills.sh/<owner>/<repo>/<skill>` means the file lives at `<skill>/SKILL.md` in the repo root.

1. For each serious candidate, inspect the repo tree: `gh api repos/{owner}/{repo}/git/trees/HEAD?recursive=1 --jq '.tree[].path'` and search for the skill slug / domain tokens.
2. Fetch the actual raw SKILL.md from the discovered path, not the guessed root path.
3. If the marketplace page exists but the current tree has no matching SKILL.md, mark it `stale/404` and demote even if installs are high.

### Private-repo trap

`npx skills find` returns skills.sh results regardless of repo visibility. High-install skills can be **private repos** that fail on `npx skills add` with an auth error. Verify before recommending:

```bash
gh api repos/<owner>/<repo> --jq '.private' 2>/dev/null   # true = private (will fail install); false = public
```

If the top candidate is private, demote it and note `⛔ private repo`.

### Compare multiple marketplace skills

When the user wants comparison ("most novel / best for X"): multi-query sweep (3-5 related terms, parallel) → fetch each candidate's `https://skills.sh/<owner>/<repo>/<skill>` page → compare on differentiation, not popularity → recommend "borrow ideas, don't install" when overlap is high.

---

## Path B — GitHub-wide SKILL.md search (delegated to oss-finder)

### Step 1 [S1]: Build query variants

| Variant rule | Required? |
|---|---|
| Original English term | MUST |
| Root/stem form if the original is derived (`refactor` if user said `refactoring`) | MUST |
| 中文 equivalent | MUST when the topic has cross-lingual presence |
| 한국어 equivalent | SHOULD |
| Synonyms / alternative names | SHOULD (2-4 extra) |

**VERIFY:** ≥3 variants; ≥1 non-English for any plausibly cross-lingual topic. Morphology matters — include BOTH root and derived forms (`refactor`/`refactoring`, `deploy`/`deployment`). Hand-tuned author-style names (`humanizer-ja`, `patina`) beat translation-perfect ones (`自然な日本語生成スキル`).

### Step 2 [S2]: Run the sweep via oss-finder

```bash
OSS_ROOT="<skills-dir>/oss-finder"          # sibling of this skill's directory
python3 "$OSS_ROOT/scripts/gh_pool.py" --check   # oss-finder Step 0 — stop and ask on SETUP NEEDED
python3 "$OSS_ROOT/scripts/finder.py" \
  --query "{PRIMARY_TERM}" --variants {VARIANT_1} {VARIANT_2} {VARIANT_3} \
  --top 15 --max-candidates 30 --per-query 12 --workers 6
```

The sweep already fans out across the REST API, the Blackbird web index, grep.app, and the PAT pool (oss-finder [S-PAR]/[S2b]). Do NOT re-implement backends here — if a backend precondition is unmet, oss-finder reports it; relay to the user.

**VERIFY:** finder.py prints `[4/4] ranking...` and a markdown table; cache at `~/.cache/oss-finder/{slug}.json`. If < 5 SKILL.md candidates for a plausibly-popular topic, the variant list is too narrow → return to [S1], add variants, re-run. Do NOT rank an under-enumerated pool.

### Step 2b [S2b]: Filter to skill FOLDER-name matches

The sweep's content match is polluted (e.g. "resume" also matches resume/continue execution). Filter on the skill FOLDER, not the body:

```bash
grep -iE '/[A-Za-z0-9-]*({TOPIC_TOKEN_1}|{TOPIC_TOKEN_2})[A-Za-z0-9-]*/SKILL\.md$' /tmp/pool.txt | sort -u
```

**Workflow/agent-behavior topics** (proactive-agent, task-discovery, action-item, standup-to-tasks) predictably surface viral mega-repos that matched a generic token ("agent"/"task") by accident. Recognize the signature, treat Path A (marketplace) as primary, and judge by [S4b] depth. Full signature + build-vs-borrow rule: [references/path-b-high-star-offtopic-noise.md](references/path-b-high-star-offtopic-noise.md).

### Step 3 [S-DIFF]: Semantic-diff guard — polish-days can lie

Polish-days are a discovery heuristic, not a recommendation. Before reporting "longest polish" or using polish-days to pick a winner, inspect actual SKILL.md diffs for the top 3 candidates and compute `semantic polish-days`.

**MUST fetch per-day diffs** for each top-3 candidate:

```bash
gh api "repos/{OWNER}/{REPO}/commits?path={SKILL_PATH}&per_page=100" \
  --jq '.[] | {sha:.sha, date:(.commit.author.date|.[0:10]), msg:.commit.message}'
gh api "repos/{OWNER}/{REPO}/commits/{SHA}" \
  --jq '.files[] | select(.filename=="{SKILL_PATH}") | .patch'   # per SHA
```

**Classify each UTC day:**

| Diff content on that day | Class |
|---|---|
| Adds/changes task behavior, workflow, domain rules, examples, VERIFY steps, API usage, or concrete heuristics | ✅ semantic |
| Same UTC day has both semantic and cosmetic commits | ✅ semantic (mention mixed-day churn) |
| Frontmatter reshape only (`category`, `tags`, `allowed-tools`) | ❌ cosmetic |
| Repo-wide migration / mass formatting churn | ❌ cosmetic |
| Hero image, website, artifact plumbing | ❌ cosmetic |
| Body moved into `references/` without better agent instructions | ❌ cosmetic |

`semantic_days = count(distinct UTC days where class=✅)`. **MUST report both** numbers when `semantic_days < raw_days * 0.7`.

**IF BLOCKED** (rate-limited or >200 commits): sample the oldest 3 + median 3 + newest 3 commits, classify those 9, report `semantic polish-days (sampled 9/N)`. Do NOT skip classification.

**VERIFY:** each top-3 candidate printed a `raw=NN / semantic=MM` pair (or a sampled pair). A row with only one polish number violates [S-DIFF].

### Step 3b [S3]: Read the ranking tiers

finder.py tags each row: 🏆 battle-tested (16+ semantic days), ✨ well-polished (6-15), 🔧 iterated (2-5), 💨 drive-by (1). **VERIFY:** the top row is ≥🔧 iterated, OR the user is told no battle-tested skill exists for this topic.

### Step 3c [S-TREND]: Generational-supersession check for fast-moving tooling topics (MUST for AI-tooling topics)

Install counts AND polish-days measure MAINTENANCE, not CURRENCY. In fast-moving spaces (AI video, agent frameworks, image-gen tooling, codegen stacks) the highest-install, most-polished, official incumbent is often last season's winner, already displaced by a successor that is sitting at #2 in your own table with steep star growth and daily commits. Before crowning #1 in any tooling category younger than ~3 years:

1. Compare **initial release dates** of the top candidates. A candidate released within the last ~3-6 months that already has daily commits + rapid star growth is a generation-shift signal, not an immature also-ran.
2. Run one `web_search("{incumbent} vs {newer candidate} {current-year}")` sweep and check the DATES of comparison/tutorial content. Where recent (last 4-8 weeks) content converges is the current generation; if all the incumbent's tutorials are from early in the year and recent ones cover the successor, the trend moved.
3. Check social sentiment about **output quality**, not just DX — complaints like "looks artificial/cheap" about the incumbent outrank its install count and official status.

**VERIFY:** for any AI-tooling topic, the report names the release dates compared and the comparison-content check that was run.

### Step 4 [S4]: Confirm topic match AND content depth for top 3

**[S4a] Topic match** — search relevance ≠ content relevance. Fetch the SKILL.md head:

```bash
gh api "repos/{OWNER}/{REPO}/contents/{PATH}" --jq '.content' | base64 -d | head -60
```

Tag ✅ on-topic / ❌ off-topic-demote / ❌ stub-demote.

**[S4b] Content depth** — frontmatter alone lies. Fetch one representative reference/pattern file and compare structure.

- **Production-grade signals (any 3+ → real tool):** quantitative fire conditions; explicit exclusion conditions (legal/medical carve-outs); meaning-preservation / risk scores; before/after pairs showing genuine transformation; cross-references between patterns ("this is NOT pattern X, see Y"); versioning / pattern count in frontmatter.
- **Toy signals (any 2+ → demote regardless of stars):** patterns = regex + replacement with no fire/exclusion logic; before/after that swaps one AI word for another; external dependency disguised as a skill; CLI-flag enumeration as 80% of the body.

Tag 🏆 production-grade / ⚠️ check use-case fit / 🪀 toy-demote. For humanizer / writing-style skills, add a one-paragraph prompt-quality judgment (trigger conditions, exclusion conditions, per-language pattern packs), not just polish-days.

### Step 5 [S5]: Optional — social review check

| Situation | Run review? |
|---|---|
| Top-1 semantic polish ≥16 AND user just wants the winner | ❌ Skip |
| Top-3 within 2 polish-days of each other | ✅ Lightweight |
| User says "리뷰/후기/평가/is it actually good/real users/should I install" | ✅ Lightweight |
| User asks for full social signal / deep research | ✅ Deep (last30days) |

**Lightweight (web search, ~30s per repo)** — three parallel searches; the third matters because Reddit users use the bare skill name (often `/skillname`):

```
web_search("{owner}/{repo} site:reddit.com")
web_search("{repo-name} OR /{repo-name} site:reddit.com")
web_search("{repo-name} skill review OR opinion OR experience")
```

**False-positive guard:** only count a hit when the subreddit is dev/agent-focused (r/ClaudeAI, r/ClaudeCode, r/codex, r/AI_Agents, r/LocalLLaMA, …), OR the thread mentions claude/codex/cursor/skill/agent/MCP, OR the owner handle appears. Tag ⭐ praised / ⚠️ complaints / 🔇 silent / mixed. **Anchor test:** run the pattern against `mvanhorn/last30days-skill` first (heavily discussed) — 0 hits there means the pattern is broken.

### Step 6 [S6]: Report to user

Print the ranked table + a one-paragraph rationale for #1, mentioning in order: (1) **semantic polish-day count** AND raw count; (2) first/last edit dates; (3) cosmetic-day ratio if `semantic < raw*0.7`; (4) why it ranks above the highest-star alternative; (5) [S4a] topic tag + [S4b] depth tag; (6) if [S5] ran, one-line social summary.

**MUST NOT** present polish-days as a single number when [S-DIFF] produced two — show the semantic value first. **VERIFY:** the deliverable contains the literal substring `semantic polish-days` or `semantic=` for #1 and for any top-3 row where `semantic_days < raw_days * 0.7`.

---

## Install target policy

Community skills MUST NOT be installed with blind global fan-out. Before installing, ask the user to choose exactly one destination skills directory and install only there; never create registry-to-registry symlinks or copies. When several skills should be bundled, use the standard lifecycle: `skill-manager` first (umbrella/merge structure), then `skill-prompter` (harden wording). MUST NOT build a bundle that only works by installing every source skill and adding mutual references. See [references/install.md](references/install.md) for the staging recipe, collision check, rename-on-install, installing a raw GitHub repo via `git clone`, and the script-dependency gotchas.

---

## When no skills are found

1. Acknowledge. 2. Offer to handle the task with general capabilities. 3. Suggest creating a new skill via `skill-manager` (or `npx skills init`).

### Decision rule: when to stop searching and write your own

After exhausting Path A + the GitHub sweep + 2 query reformulations, if the top results are all adjacent-but-not-matching, generic copy-editing tools when you need contextual logic, or star-leaders that fail [S4] content inspection — STOP searching. Writing a custom skill via `skill-manager` is faster than the next 3 reformulations. The niche is genuinely yours (not just under-searched) when: the task involves the user's personal voice/language/workflow; it spans 2+ languages with user-specific rules; the right answer needs the user's memory/people files first; existing community skills assume a generic English use case.

## Constraints

- MUST launch MARKETPLACE + the oss-finder GITHUB sweep in parallel, union results, and report each surface's raw count before any candidate table.
- MUST NOT silent-skip a surface whose precondition is unmet — relay the gap (including oss-finder's `SETUP NEEDED`) and collect user input.
- MUST run [S-DIFF] for every top-3 candidate before the [S6] report whenever polish-days are used for ranking; MUST surface `semantic polish-days` when semantic diverges from raw by ≥30%.
- MUST verify topic match in [S4a] even when the polish-day score is high (a 40-day repo with the wrong content is demoted, not promoted).
- MUST delegate the raw GitHub search to oss-finder — do NOT inline `gh search code` backend loops here.
- SHOULD prefer Path A when the user explicitly mentions skills.sh, marketplace, or installable packages.
- MAY use finder.py's `--cache` for repeat searches within 24h.

## Variable definitions

| Var | Meaning |
|---|---|
| `<skills-dir>` | The directory that contains this skill's folder (and the sibling `oss-finder/`) |
| `{PRIMARY_TERM}` | The user's main topic in their original language |
| `{VARIANT_N}` | One additional search variant (other language or synonym) |
| `{OWNER}/{REPO}` | A GitHub repository identifier |
| `{PATH}` | Relative path to a `SKILL.md` inside that repo |
