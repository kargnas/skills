# Code-search engine fallback chain

Marketplace metadata (`npx skills find`) and repo-description search (`gh search repos`) both miss projects whose relevant logic lives DEEP inside code files, not in a title or description. When they return weak hits, add a third path: search inside code for the function names, API endpoints, or concept phrases the implementation would contain — and never stop after one engine, because each has different blind spots.

## Engines

| Engine | Strengths | Failure modes |
|---|---|---|
| `npx skills find` (Path A) | Curated, frontmatter quality, install metadata | Only sees skills.sh-indexed repos. Misses raw GitHub. |
| `gh search code` (Path B `finder.py`) | Full GitHub-wide text search, polish-day ranking, includes 0-star repos | **30 req/min hard rate limit on the Search API.** Paid plans do NOT raise it. 4-5 queries ⇒ `HTTP 403: API rate limit exceeded`. |
| `grep.app` | Free, no auth, fast, regex-friendly | Multi-word queries are AND (natural phrases return 0). Vercel security checkpoint 429s `curl`/`fetch` — drive it with a browser tool. Index is weeks-stale. |
| `sourcegraph.com` | Powerful structural queries, public code | Account-gated for high volume. |
| `searchcode.com` | Free | Lighter index. |

## Decision rule

- 1–2 keyword query, broad recall wanted → grep.app via browser.
- 3+ keyword query with specific token combinations → `gh search code` (until the rate limit).
- Before saying "nothing exists" → BOTH engines must have been tried.

## Engine-failure recovery

| Failure | Recovery |
|---|---|
| `gh search code` returns `HTTP 403: API rate limit exceeded` | Switch to grep.app immediately (or wait 60s). Do NOT report "couldn't search" — switch tools, don't give up. |
| grep.app `curl` returns the Vercel security checkpoint HTML | Navigate the browser tool to `https://grep.app/search?q=...`; the HTML page renders results without API access. |
| grep.app multi-term query returns "No results" | Drop to a single distinctive term + language filter, or use identifier-style strings authors put in code. |
| First 5 hits all look off-topic | Open the file contents of the top 2 anyway. README/frontmatter is misleading; the code file often carries the heuristic. |

## Fallback order when `gh search code` rate-limits

1. **grep.app** — browser tool → `https://grep.app/search?q=<urlencoded>&filter[lang][0]=Markdown` (Markdown filter for SKILL.md hunts; drop it for source code).
2. **sourcegraph.com** — more powerful query language, public code only.
3. **searchcode.com** — lighter index.
4. After ~60 seconds `gh search code` is available again, and steps 1–3 have produced a pre-filtered candidate set for authenticated `gh api` calls. These use the core REST quota (5000 req/h, separate from search) and are almost never the bottleneck:
   - `repos/<owner>/<repo>` (description, stars, updated_at, topics)
   - `repos/<owner>/<repo>/git/trees/HEAD?recursive=1` (full file list, one call)
   - `repos/<owner>/<repo>/contents/<path>` then `base64 -d` (read the actual SKILL.md / source)
   - `repos/<owner>/<repo>/commits?path=<file>&per_page=100` (compute polish-days deterministically)

This gives authoritative content rather than grep.app's snippet view and spends no `gh search code` calls per candidate.

## grep.app AND-semantics

grep.app treats every space as AND across the full text. `slack "needs reply"`, `slack "missed messages"`, or `slack "follow up" mention` return zero even when the topic is heavily covered, because no single file contains all those tokens. Pick the most distinctive single phrase per query (`"unanswered mentions"`, `未返信`) and run several narrow queries instead of one broad one.

## When the user pushes back ("look harder", "open 20–30 repos", "search the code too")

Do NOT defend the prior result count. That feedback means the engine was too narrow OR you stopped too soon:

1. **Switch engine** — Path A empty → `gh search code` with 5+ varied queries → rate-limited → grep.app → multi-term zeroed → single word + language/path filter.
2. **Broaden vocabulary** — natural phrases return zero; use the verbs and primitives the code itself uses (`conversations.replies unanswered`, `app_mention reply detect`, `UNANSWERED_MENTION_THRESHOLD_MS`).
3. **Open the top 5–10 hits even when descriptions look unrelated.** A demo app or SaaS scaffold can carry the exact heuristic you need.
4. **When code-only repos win, port the heuristic, don't install the package.** Deterministic regex/stdlib ports of small source files into a self-contained script beat installing a full web-app stack.

**Time budget:** allocate 5–10 minutes across ≥2 engines AND open ≥10 candidate files before concluding "nothing relevant exists".

## Borrow from repos that aren't installable skills

Many production projects are NOT packaged as `SKILL.md`. Extract their detection logic, classifier prompts, and heuristic patterns and feed them into the existing skill via `references/<source-repo-name>.md`. "Find an installable skill" and "borrow ideas from production code" are both valid outcomes of a search.

## Negative-claim guard: ALWAYS search before saying "X doesn't exist"

When the user asks "is there a clean way to do X" or "is there an official CLI / OAuth path / skill / tool for X", do NOT answer from prior belief. A "doesn't exist / no clean path / only unofficial wrappers" sentence MUST be preceded in the same turn by at least one of:

1. `npx skills find <term>` (Path A)
2. a web search against the vendor's official docs / blog
3. `gh search repos <vendor>+<thing>` for first-party repos

If none of the three ran, you have no grounds to claim absence. Run them, then answer.
