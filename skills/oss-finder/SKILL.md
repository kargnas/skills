---
name: oss-finder
description: "Finds battle-tested open-source repos, libraries, frameworks, CLI tools, or code on GitHub, ranked by README polish-days instead of stars. Also the shared GitHub code-search backend toolkit — rotating PAT pool, grep.app, Blackbird web index, BigQuery/GHArchive, and the code-search fallback chain. Use for 'find a library/framework/tool for X', 'battle-tested repo', GitHub-wide code search, or when `gh search code` rate-limits. Finding installable SKILL.md agent-skill packages goes to the skill-finder skill (it delegates its GitHub sweep here)."
---

# OSS Finder — GitHub repo & code discovery, ranked by polish-days

> **ONE SENTENCE:** Find battle-tested OSS on GitHub (or run any GitHub-wide code search) and rank by how many distinct days a human iterated on the target file — not by stars.

All paths below are relative to this skill's directory (the one containing this `SKILL.md`).

## Step 0 — token check before anything else (MUST)

Run this every time the skill is invoked, before launching any backend or script:

```bash
python3 scripts/gh_pool.py --check
```

| Exit | Meaning | What to do |
|---|---|---|
| `0` (`READY`) | PAT pool loaded AND `gh` CLI authenticated | Continue. |
| `1` (`SETUP NEEDED`) | PAT pool missing, and/or `gh` not logged in | **STOP. Do not run any search.** Tell the user exactly what is missing and ask whether to set it up now. Walk them through the setup below, re-run the check, and continue only on exit `0`. |

Both bundled scripts refuse to run without PATs (they print the same setup hint and exit `2`). There is no anonymous or `gh`-CLI-only path: anonymous GitHub search (60 req/h) cannot finish a single polish-day sweep.

### PAT pool setup

| Constant | Value | Purpose |
|---|---|---|
| `PAT_CONFIG_FILE` | `~/.config/kargnas/oss-finder.env` | Local GitHub PAT pool read by `scripts/gh_pool.py`. Keep it untracked. |

```bash
mkdir -p ~/.config/kargnas
cat > ~/.config/kargnas/oss-finder.env <<'EOF'
GH_PAT_1=github_pat_...
GH_PAT_2=ghp_...
EOF
chmod 600 ~/.config/kargnas/oss-finder.env
```

1. Create 1–5 PATs. Public search needs only public-repository read access (`public_repo` on classic tokens).
2. Each PAT must come from a **different GitHub account** — same-account PATs share one quota. Every account adds 30 req/min on the Search API (3 accounts ⇒ 90 req/min). Keep account-ownership notes as comments in the file, not in this skill.
3. `GH_PAT_<n>` environment variables extend the pool at runtime.
4. `gh auth login` is still required for the inline `gh search` / `gh api` steps below (5000 req/h core quota vs 60 anonymous).
5. Verify: `python3 scripts/gh_pool.py /rate_limit` prints the current PAT's quota; repeated calls rotate PATs.

## Why polish-days, not stars or install counts

| Signal | Why insufficient |
|---|---|
| Stars | Hype-driven. A trending repo gets 10k stars in a week with one commit. |
| Install / download count | Often = "bundled in a famous repo", not quality. |
| Total commit count | An AI session generates 30 commits in 1 hour. |
| **Unique edit DAYS on the target file** | A human comes back tomorrow and tweaks. AI bursts can't fake it. |

A 0-star repo with 30 polish-days is more battle-tested than an 18k-star repo with 8 polish-days. Same-UTC-day burst commits collapse to 1 polish day.

## Two search entrypoints (bundled scripts)

| Script | Target file | Ranks by | Use for |
|---|---|---|---|
| `scripts/repo_finder.py` | README.md | README polish-days (falls back to `pushed_at × stars` when README commits are unavailable) | **general repos / libraries / frameworks / CLI tools** — the headline use |
| `scripts/finder.py` | SKILL.md | SKILL.md polish-days | GitHub-wide **SKILL.md** discovery — the `skill-finder` skill delegates its sweep here, then applies skill-specific quality gates |

Both import `scripts/gh_pool.py` (the rotating PAT pool) as a sibling. All three ship in this skill's `scripts/` dir. Results are cached under `~/.cache/oss-finder/`.

## General repository search — `repo_finder.py`

Trigger phrases: "라이브러리 찾아줘", "프레임워크 추천", "CLI 도구", "library for", "framework for", "tool for X", "battle-tested X".

```bash
python3 scripts/repo_finder.py \
  --query "discord bot framework" \
  --variants "discord.js" "discordpy" \
  --language Python --min-stars 10 \
  --top 15 --workers 6
```

Smoke test: `--query "discord bot framework" --top 5` should put long-iterated frameworks such as `wechaty/wechaty`, `AstrBotDevs/AstrBot`, `koishijs/koishi` at the top — battle-tested winners, not star-leaders.

**Ranking:** README.md polish-days descending; when the commits API can't be fetched, demote to `(pushed_at recency × stars)` and mark the row `⚠️`.

**VERIFY:** Output shows a markdown table where the top rows are ≥🔧 iterated tier, not merely the highest-star repos. Cache lands at `~/.cache/oss-finder/repos-{slug}.json`.

## SKILL.md discovery entrypoint — `finder.py`

`skill-finder` owns the SKILL.md *evaluation* workflow ([S-DIFF] semantic-diff, depth checks, social review, report) but delegates the raw GitHub sweep here:

```bash
python3 scripts/finder.py \
  --query "{PRIMARY_TERM}" --variants {VARIANT_1} {VARIANT_2} {VARIANT_3} \
  --top 15 --max-candidates 30 --per-query 12 --workers 6
```

Pass each variant as a separate argument. Output: a polish-day-ranked SKILL.md table; cache at `~/.cache/oss-finder/{slug}.json`.

---

## Search backends — GH-API/GH-WEB/GREP-APP/PAT-POOL run in parallel (MANDATORY); BIGQUERY/GHARCHIVE opt-in

On any exhaustive discovery request, fire these backends **at the same level, in parallel (async)** as the first action. This is NOT a fallback chain — do NOT run one, check it, then try the next. Launch concurrently, union every result into one candidate pool, then rank by polish-days. Sequential search undercounts the long tail and is slow.

| Backend | Tool | Role in the pool |
|---|---|---|
| **GH-API** | `scripts/finder.py` / `repo_finder.py` (wrap the `gh search code` / repo-search sweep) | candidate pool + polish-day ranking |
| **GH-WEB** | cloakbrowser → `github.com/search` (Blackbird) | repos the REST API index cannot see |
| **GREP-APP** | headless browser → `grep.app/search` | multi-language exact-token hits |
| **PAT-POOL** | `scripts/gh_pool.py` PAT round-robin | GH-API throughput boost (≈90 req/min with 3 tokens) |

BIGQUERY (BigQuery) and GHARCHIVE (GHArchive) are NOT in the default parallel batch. Add them opt-in ONLY when the user explicitly asks for full-corpus grep or brand-new-repo (created-today) discovery.

**Precondition not met — ASK the user, never silent-skip (MUST):** if a backend lacks its key, cookie, or auth, MUST NOT drop it quietly. GH-API / PAT-POOL are covered by Step 0; the others:

| Backend | Missing precondition | Tell the user + collect |
|---|---|---|
| GH-WEB | no login cookie/profile at `~/.cloakbrowser-profiles/github/` | "GitHub login cookie missing" → ask them to log in once via cloakbrowser `headless=False` |
| GREP-APP | network or browser launch fails | report the actual error → ask whether to retry |

**VERIFY [S-PAR]:** before printing any candidate table, all applicable backends launched concurrently (or paused for user input on an unmet precondition) and each backend's raw candidate count is reported. A pool built from a single backend violates this gate.

### Candidate enumeration [S0] — folder/repo sweep

`nameWithOwner` is the CORRECT jq key — `.repository.fullName` returns `null`, do NOT use it:

```bash
for q in "{VARIANT_1}" "{VARIANT_2}" "{VARIANT_3}" "{VARIANT_4}"; do
  gh search code "$q" --filename SKILL.md --limit 100 --json repository,path \
    --jq '.[] | "\(.repository.nameWithOwner)\t\(.path)"'
done | sort -u > /tmp/pool.txt
```

(For general repos, use `gh search repos` / `repo_finder.py` instead of the `--filename` code sweep.)

**zsh GOTCHA (MUST follow):** NEVER name a shell variable `path` inside these loops. In zsh `$path` is bound to `$PATH`; assigning it wipes `$PATH` and every external command (`sort`, `wc`, `cut`, `basename`) dies with `command not found`, silently zeroing the enumeration pass. Use `pth` or `p`.

### Backend reference catalog

| Backend ID | Backend | Coverage | Freshness | Rate limit | Notes |
|---|---|---|---|---|---|
| `GH-API` | `gh search code/repos` | GitHub REST API index (SUBSET of Web UI) | near real-time | **30 req/min hard** | First serious sweep. ⚠️ **REST API uses a DIFFERENT, SMALLER index than the Web UI's Blackbird engine.** Repos visible on github.com may return 0 from the API. NEVER treat API-only results as exhaustive. |
| `GH-WEB` | cloakbrowser persistent profile → `github.com/search?q=...&type=code` | Full Blackbird index | real-time | none | **MANDATORY — always run alongside GH-API.** Uses `~/.cloakbrowser-profiles/github/`. Navigate to `https://github.com/search?q={urlencoded}&type=code`, `wait_until='domcontentloaded'`, parse `document.body.innerText`. Catches low-star repos invisible to REST. |
| `GREP-APP` | grep.app via headless browser | grep.app's own crawl | **weeks-stale** | none | Multi-language exact-token search. Curl blocked by Vercel 429 — navigate `https://grep.app/search?q=...` in a browser. |
| `PAT-POOL` | `scripts/gh_pool.py` round-robin | same as GH-API | real-time | 30 req/min × N tokens | When you need GH-API throughput but exceeded the limit. |
| `BIGQUERY` | BigQuery `bigquery-public-data:github_repos` | full public GitHub | **weekly snapshot** | pay-per-TB (~$0.30–$2/query) | Bulk pattern search. Needs `gcloud auth application-default login`. Free tier: 1 TB/month. |
| `GHARCHIVE` | GHArchive (`githubarchive.day.*` or direct `.json.gz`) | every public push/create/star event | **~1 hour lag** | none (direct .gz) or pay-per-TB | "today's brand-new repos" — the ONLY way to catch fresh repos gh Search hasn't indexed. |

### GH-API → GREP-APP escape hatch

When `gh search` returns `HTTP 403: API rate limit exceeded`, GREP-APP is already running in the parallel batch — rely on it. Drive grep.app with your browser tool (navigate to `https://grep.app/search?q=<url-encoded-query>`); curl is blocked by the Vercel security checkpoint (429).

**grep.app quirks:**
- Multi-keyword queries are **AND**, not OR — `slack "needs reply"` returns 0 while `slack unanswered` returns hits. Use a single distinctive token first, then narrow with sidebar facets.
- Curl/fetch is permanently blocked by Vercel; browser navigation works.
- Coverage is weeks-stale — combine with GHARCHIVE for "what's new this week".

### BIGQUERY pre-flight: ALWAYS check freshness AND dry-run before paying

1. **Stale-snapshot trap.** `bigquery-public-data.github_repos.files` looks comprehensive but its `lastModifiedTime` can be years old:
   ```bash
   bq show --format=prettyjson bigquery-public-data:github_repos.files 2>&1 | grep lastModifiedTime
   # Convert ms epoch → date. Older than 6 months = NOT a current index → use the PAT pool instead.
   ```
2. **Always dry-run for cost.**
   ```bash
   bq query --dry_run --use_legacy_sql=false --format=prettyjson < query.sql 2>&1 | grep totalBytesProcessed
   # bytes / 1e12 × $6.25/TB. Decide BEFORE running.
   ```

"Go ahead, spend it" is permission to spend, NOT permission to skip the freshness check. One-time setup: `gcloud auth login && gcloud auth application-default login`. If `bq` returns `Reauthentication failed. cannot prompt during non-interactive execution`, the user must run those two commands once interactively.

### GHARCHIVE direct usage (no GCP needed)

```bash
# All public repo-Create events for a given UTC hour (each .gz ~10-50 MB)
curl -sL "https://data.gharchive.org/$(date -u +%Y-%m-%d)-3.json.gz" | gunzip \
  | jq -c 'select(.type=="CreateEvent" and .payload.ref_type=="repository")
           | {repo:.repo.name, desc:.payload.description, actor:.actor.login, t:.created_at}'
```

### PAT-POOL — the 1000-result cap

GitHub Code Search caps each query at 1000 results (10 pages × 100). Partitioning is the only way past it — use `path × size × date-range` (or `× language`). **`stars:` filtering does NOT work in Code Search** (non-monotonic — the operator is ignored); filter by stars post-fetch via `repos/{owner}/{repo}` metadata instead.

## Blackbird web-index coverage [S2b]

**ALWAYS run a cloakbrowser Blackbird pass, even when the REST API returns many results.** The REST index is a smaller subset than the Web UI. For the setup recipe, the parse loop, and the REST-vs-Blackbird gap evidence, see [references/github-blackbird-index-gap.md](references/github-blackbird-index-gap.md).

## Code-search engine fallback chain

When `gh search code` rate-limits (30 req/min hard cap, NOT raised by paid plans), switch to grep.app / sourcegraph / the PAT pool. Full decision table: [references/code-search-fallback.md](references/code-search-fallback.md).

## Constraints

- MUST run Step 0 (`scripts/gh_pool.py --check`) before any backend or script; on `SETUP NEEDED`, MUST stop and ask the user to set up the PAT pool / `gh auth login` instead of searching without it.
- MUST launch GH-API/GH-WEB/GREP-APP/PAT-POOL in parallel (async) at the start of an exhaustive discovery request, union their results, and report each backend's raw count before any candidate table.
- MUST NOT silent-skip a backend whose key/cookie/auth is missing — tell the user what is missing and collect it.
- MUST use authenticated `gh` (5000 req/h vs 60 anonymous) and collapse same-UTC-day commits to 1 polish day.
- MUST include 0-star results in the candidate pool.
- MUST run the bundled scripts — do NOT inline `gh api` loops in conversation when the candidate set > 5.
- SHOULD include 中文 / 한국어 variants when the topic has cross-lingual community presence.
- MAY use `--cache` for repeat searches within 24h.

## Variable definitions

| Var | Meaning |
|---|---|
| `{PRIMARY_TERM}` | The user's main topic in their original language |
| `{VARIANT_N}` | One additional search variant (other language or synonym) |
| `{OWNER}/{REPO}` | A GitHub repository identifier |
