#!/usr/bin/env python3
"""
repo_finder.py — General GitHub repository search with polish-day ranking.

Sister script to finder.py. While finder.py searches for SKILL.md files,
this one searches for general repos (libraries, frameworks, tools) and
ranks them by README.md polish-day count.

Polish day = unique YYYY-MM-DD on which README.md was committed.
Same-day burst commits collapse to 1 polish day to avoid AI-generated
"30 commits in one hour" noise.

Falls back to (pushed_at + commit count) when README commits are unavailable.

Usage:
    python3 repo_finder.py --query "discord bot framework" \\
        --variants "discord.js" "discordpy" \\
        --language Python --min-stars 10 \\
        --top 15 --workers 6
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

# Sibling import — same dir as gh_pool.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gh_pool  # noqa: E402

CACHE_DIR = Path.home() / ".cache" / "oss-finder"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def slugify(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9가-힣\u4e00-\u9fff]+", "-", s.lower()).strip("-")[:60]


# ---------------------------------------------------------------------------
# GitHub API wrappers (delegate to gh_pool)
# ---------------------------------------------------------------------------


def search_repos(query: str, per_page: int = 30) -> list[dict]:
    """Search repositories. Returns list of repo metadata dicts."""
    d = gh_pool.repo_search(query, per_page=per_page)
    if not isinstance(d, dict):
        return []
    return d.get("items", [])


def repo_topics(full_name: str) -> list[str]:
    """Fetch topics for a repo. Returns empty list on failure."""
    # repo_info already returns topics in the standard endpoint
    info = gh_pool.repo_info(full_name)
    if isinstance(info, dict):
        return info.get("topics", []) or []
    return []


def get_readme_commits(full_name: str) -> list[dict]:
    """Fetch commit history for README.md (any case). Returns list of commit dicts.

    Tries README.md → README.rst → README → first README-like file from contents.
    """
    candidates = ["README.md", "README.rst", "README.MD", "readme.md", "Readme.md", "README"]
    for path in candidates:
        out: list[dict] = []
        page = 1
        while True:
            commits = gh_pool.repo_commits(full_name, path=path, per_page=100, page=page)
            if commits is None or not isinstance(commits, list):
                break
            if not commits:
                break
            for c in commits:
                try:
                    out.append({
                        "sha": c["sha"][:7],
                        "date": c["commit"]["committer"]["date"],
                        "author": (c["commit"]["author"].get("email")
                                   or c["commit"]["author"].get("name", "")),
                        "message": c["commit"]["message"].split("\n")[0][:80],
                    })
                except (KeyError, TypeError):
                    continue
            if len(commits) < 100:
                break
            page += 1
            if page > 5:
                break  # cap at 500 commits
        if out:
            return out
    return []


# ---------------------------------------------------------------------------
# Candidate dataclass + polish-day computation
# ---------------------------------------------------------------------------


@dataclass
class Candidate:
    full_name: str
    stars: int = 0
    description: str = ""
    language: str = ""
    html_url: str = ""
    pushed_at: str = ""
    topics: list[str] = field(default_factory=list)
    commits: list[dict] = field(default_factory=list)
    unique_days: int = 0
    total_commits: int = 0
    days_span: int = 0
    unique_authors: int = 0
    first_commit: str = ""
    last_commit: str = ""
    tier: str = ""
    fallback_used: bool = False

    def compute_polish(self):
        if not self.commits:
            # Fallback: derive a coarse signal from pushed_at + repo metadata.
            # We can't compute polish-days without commit history, so demote
            # to drive-by unless the pushed_at is recent AND stars > 0.
            self.fallback_used = True
            self.tier = "drive-by"
            return
        days = sorted({c["date"][:10] for c in self.commits})
        self.unique_days = len(days)
        self.total_commits = len(self.commits)
        self.unique_authors = len({c["author"] for c in self.commits if c["author"]})
        self.first_commit = days[0]
        self.last_commit = days[-1]
        try:
            d1 = datetime.fromisoformat(days[0])
            d2 = datetime.fromisoformat(days[-1])
            self.days_span = (d2 - d1).days
        except Exception:
            self.days_span = 0
        if self.unique_days >= 16:
            self.tier = "battle-tested"
        elif self.unique_days >= 6:
            self.tier = "well-polished"
        elif self.unique_days >= 2:
            self.tier = "iterated"
        else:
            self.tier = "drive-by"


TIER_RANK = {"battle-tested": 3, "well-polished": 2, "iterated": 1, "drive-by": 0}


def topic_match_score(text: str, query_terms: list[str]) -> int:
    if not text:
        return 0
    t = text.lower()
    return sum(1 for q in query_terms if q.lower() in t)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="Primary topic")
    ap.add_argument("--variants", nargs="*", default=[],
                    help="Extra search variants (synonyms, other languages)")
    ap.add_argument("--language", default="",
                    help="Filter results by GitHub language (e.g. Python, Rust)")
    ap.add_argument("--min-stars", type=int, default=0,
                    help="Drop repos under this star count")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--per-query", type=int, default=30)
    ap.add_argument("--max-candidates", type=int, default=40)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--cache", action="store_true", help="Use cache if fresh (<24h)")
    args = ap.parse_args()

    gh_pool.require_pats()

    queries = [args.query] + args.variants
    cache_path = CACHE_DIR / f"repos-{slugify(args.query)}.json"

    if args.cache and cache_path.exists():
        age_h = (time.time() - cache_path.stat().st_mtime) / 3600
        if age_h < 24:
            print(f"[cache] using {cache_path} (age {age_h:.1f}h)", file=sys.stderr)
            data = json.loads(cache_path.read_text())
            print_report(data, args.top)
            return

    # Phase 1: collect candidates via repo search across query variants.
    print(f"[1/4] searching repos across {len(queries)} variants...", file=sys.stderr)
    candidates: dict[str, dict] = {}

    for q in queries:
        # Build query with optional language + min-stars filters.
        # We deliberately run TWO sub-queries per variant: stars-desc and
        # updated-desc. Stars surfaces established libraries; updated
        # surfaces fresh/maintained ones. Polish-days will rank the union.
        filters = []
        if args.language:
            filters.append(f"language:{args.language}")
        if args.min_stars > 0:
            filters.append(f"stars:>={args.min_stars}")
        filter_str = " ".join(filters)
        for sort_q in [
            f"{q} {filter_str} sort:stars-desc".strip(),
            f"{q} {filter_str} sort:updated".strip(),
        ]:
            items = search_repos(sort_q, per_page=args.per_query)
            for it in items:
                fn = it.get("full_name")
                if not fn or fn in candidates:
                    continue
                candidates[fn] = {
                    "full_name": fn,
                    "stars": it.get("stargazers_count", 0),
                    "description": it.get("description") or "",
                    "language": it.get("language") or "",
                    "html_url": it.get("html_url", ""),
                    "pushed_at": it.get("pushed_at", ""),
                    "topics": it.get("topics", []) or [],
                }
        time.sleep(0.5)  # gentle pacing between variants

    print(f"      collected {len(candidates)} unique repos", file=sys.stderr)

    # Phase 1b: prune by description + topics match + stars
    if len(candidates) > args.max_candidates:
        def score(c):
            blob = c["description"] + " " + " ".join(c.get("topics", []))
            return (topic_match_score(blob, queries), c["stars"])
        scored = sorted(candidates.values(), key=score, reverse=True)[:args.max_candidates]
        candidates = {c["full_name"]: c for c in scored}
        print(f"      pruned to top {args.max_candidates} by topic-match + stars",
              file=sys.stderr)

    # Phase 2: build Candidate list (topics already attached from search hit).
    print(f"[2/4] building candidate list...", file=sys.stderr)
    cands: list[Candidate] = [
        Candidate(
            full_name=m["full_name"],
            stars=m["stars"],
            description=m["description"],
            language=m["language"],
            html_url=m["html_url"],
            pushed_at=m["pushed_at"],
            topics=m.get("topics", []),
        )
        for m in candidates.values()
    ]
    print(f"      {len(cands)} candidates ready for commit fetch", file=sys.stderr)

    # Phase 3: fetch README commits in parallel.
    print(f"[3/4] fetching README commit history (parallel x{args.workers})...",
          file=sys.stderr)

    def fill_commits(c: Candidate) -> Candidate:
        c.commits = get_readme_commits(c.full_name)
        c.compute_polish()
        return c

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(fill_commits, c): c for c in cands}
        completed: list[Candidate] = []
        for i, f in enumerate(as_completed(futures), 1):
            try:
                completed.append(f.result())
                if i % 5 == 0:
                    print(f"      {i}/{len(cands)}...", file=sys.stderr)
            except Exception as e:
                print(f"[commit-err] {e}", file=sys.stderr)

    cands = completed

    # Phase 4: rank by tier, polish-days, stars (matches finder.py)
    print(f"[4/4] ranking...", file=sys.stderr)
    cands.sort(
        key=lambda c: (TIER_RANK.get(c.tier, 0), c.unique_days, c.stars),
        reverse=True,
    )

    data = {
        "query": args.query,
        "variants": args.variants,
        "language": args.language,
        "min_stars": args.min_stars,
        "ts": datetime.utcnow().isoformat() + "Z",
        "candidates": [asdict(c) for c in cands],
    }
    cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"[cache] wrote {cache_path}", file=sys.stderr)

    print_report(data, args.top)


def print_report(data: dict, top: int):
    cands = data["candidates"][:top]
    if not cands:
        print("No candidates found.")
        return

    print(f"\n## Repo Finder — {data['query']}")
    if data.get("variants"):
        print(f"Variants: {data['variants']}")
    filter_bits = []
    if data.get("language"):
        filter_bits.append(f"language={data['language']}")
    if data.get("min_stars"):
        filter_bits.append(f"min_stars={data['min_stars']}")
    if filter_bits:
        print(f"Filters: {', '.join(filter_bits)}")
    print(f"Total candidates inspected: {len(data['candidates'])}\n")

    print("| Tier | Days | Commits | Span(d) | Authors | ★ | Repo | Lang | Updated |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in cands:
        tier_emoji = {
            "battle-tested": "🏆",
            "well-polished": "✨",
            "iterated": "🔧",
            "drive-by": "💨",
        }.get(c["tier"], "?")
        repo_link = f"[{c['full_name']}]({c['html_url']})"
        updated = (c.get("pushed_at") or "")[:10]
        fallback_marker = "⚠️" if c.get("fallback_used") else ""
        print(
            f"| {tier_emoji}{fallback_marker} {c['tier']} | {c['unique_days']} | "
            f"{c['total_commits']} | {c['days_span']} | {c['unique_authors']} | "
            f"{c['stars']} | {repo_link} | {c['language'] or '-'} | {updated} |"
        )

    print()
    for i, c in enumerate(cands[:3], 1):
        print(f"\n### #{i} — {c['full_name']}")
        if c["description"]:
            print(f"   {c['description']}")
        if c.get("topics"):
            print(f"   Topics: {', '.join(c['topics'][:8])}")
        if c["commits"]:
            print(f"   First README edit: {c['first_commit']}  →  Last: {c['last_commit']}")
            print(f"   {c['unique_days']} polish days across {c['days_span']}d "
                  f"({c['unique_authors']} author{'s' if c['unique_authors']!=1 else ''})")
        else:
            print(f"   ⚠️ README commit history unavailable — ranked via stars + pushed_at only")
            print(f"   Last push: {(c.get('pushed_at') or '')[:10]}, stars: {c['stars']}")


if __name__ == "__main__":
    main()
