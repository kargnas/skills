#!/usr/bin/env python3
"""
oss-finder/scripts/finder.py
Search GitHub for SKILL.md files matching a topic, rank by polish-day count.
(SKILL.md-targeted entrypoint of the oss-finder search toolkit; the skill-finder
skill delegates its GitHub-wide sweep here, then applies skill-specific gates.)

Polish day = unique YYYY-MM-DD on which SKILL.md was committed.
Same-day burst commits collapse to 1 polish day to avoid AI-generated
"30 commits in one hour" noise.
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

# Sibling import — gh_pool.py lives next to this script. Every API call fans
# out through the rotating PAT pool (3 PATs = 90 req/min on Search); the pool
# is mandatory, see gh_pool.require_pats().
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gh_pool  # noqa: E402

CACHE_DIR = Path.home() / ".cache" / "oss-finder"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def slugify(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9가-힣一-鿿]+", "-", s.lower()).strip("-")[:60]


def search_repos_raw(query: str, per_page: int = 30) -> list[dict]:
    """Search repositories via the PAT pool."""
    d = gh_pool.repo_search(query, per_page=per_page)
    return d.get("items", []) if isinstance(d, dict) else []


def search_code_skillmd(query: str, per_page: int = 30) -> list[dict]:
    """Find SKILL.md files containing the query."""
    d = gh_pool.code_search(f"filename:SKILL.md {query}", per_page=per_page)
    if not isinstance(d, dict):
        return []
    return [
        {"full_name": it["repository"]["full_name"], "path": it["path"]}
        for it in d.get("items", [])
    ]


def get_repo_info(full_name: str) -> dict | None:
    return gh_pool.repo_info(full_name)


def list_skill_paths(full_name: str) -> list[str]:
    """List all SKILL.md paths in a repo."""
    d = gh_pool.code_search(f"filename:SKILL.md repo:{full_name}", per_page=20)
    if isinstance(d, dict):
        return [it["path"] for it in d.get("items", [])]
    return []


def get_commits_for_path(full_name: str, path: str) -> list[dict]:
    """Fetch all commits touching a specific path."""
    out: list[dict] = []
    page = 1
    while True:
        commits = gh_pool.repo_commits(full_name, path=path, per_page=100, page=page)
        if not commits:
            break
        for c in commits:
            out.append({
                "sha": c["sha"][:7],
                "date": c["commit"]["committer"]["date"],
                "author": c["commit"]["author"].get("email") or c["commit"]["author"].get("name", ""),
                "message": c["commit"]["message"].split("\n")[0][:80],
            })
        if len(commits) < 100:
            break
        page += 1
        if page > 5:
            break  # cap at 500 commits
    return out


@dataclass
class Candidate:
    full_name: str
    path: str
    stars: int = 0
    description: str = ""
    language: str = ""
    html_url: str = ""
    pushed_at: str = ""
    commits: list[dict] = field(default_factory=list)
    unique_days: int = 0
    total_commits: int = 0
    days_span: int = 0
    unique_authors: int = 0
    first_commit: str = ""
    last_commit: str = ""
    tier: str = ""

    def compute_polish(self):
        if not self.commits:
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="Primary topic")
    ap.add_argument("--variants", nargs="*", default=[], help="Extra search variants (CN/KR/etc)")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--per-query", type=int, default=20)
    ap.add_argument("--cache", action="store_true", help="Use cache if fresh")
    ap.add_argument("--max-candidates", type=int, default=40)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    gh_pool.require_pats()

    queries = [args.query] + args.variants
    cache_path = CACHE_DIR / f"{slugify(args.query)}.json"

    if args.cache and cache_path.exists():
        age_h = (time.time() - cache_path.stat().st_mtime) / 3600
        if age_h < 24:
            print(f"[cache] using {cache_path} (age {age_h:.1f}h)", file=sys.stderr)
            data = json.loads(cache_path.read_text())
            print_report(data, args.top)
            return

    # Phase 1: collect candidates
    print(f"[1/4] searching repos across {len(queries)} variants...", file=sys.stderr)
    candidates: dict[str, dict] = {}  # full_name → metadata

    for q in queries:
        # repo search
        for variant_q in [
            f"{q} SKILL.md in:readme,description sort:stars-desc",
            f"{q} sort:updated",
        ]:
            items = search_repos_raw(variant_q, per_page=args.per_query)
            for it in items:
                fn = it["full_name"]
                if fn not in candidates:
                    candidates[fn] = {
                        "full_name": fn,
                        "stars": it.get("stargazers_count", 0),
                        "description": it.get("description") or "",
                        "language": it.get("language") or "",
                        "html_url": it.get("html_url", ""),
                        "pushed_at": it.get("pushed_at", ""),
                    }
        # code search
        code_items = search_code_skillmd(q, per_page=args.per_query)
        for it in code_items:
            fn = it["full_name"]
            if fn not in candidates:
                info = get_repo_info(fn) or {}
                candidates[fn] = {
                    "full_name": fn,
                    "stars": info.get("stargazers_count", 0),
                    "description": info.get("description") or "",
                    "language": info.get("language") or "",
                    "html_url": info.get("html_url", ""),
                    "pushed_at": info.get("pushed_at", ""),
                    "_hint_path": it["path"],
                }
        time.sleep(1)  # gentle pacing

    print(f"      collected {len(candidates)} unique repos", file=sys.stderr)

    if len(candidates) > args.max_candidates:
        # keep top by stars and by topic-match
        scored = sorted(
            candidates.values(),
            key=lambda c: (
                topic_match_score(c["description"], queries),
                c["stars"],
            ),
            reverse=True,
        )[: args.max_candidates]
        candidates = {c["full_name"]: c for c in scored}
        print(f"      pruned to top {args.max_candidates} by description match + stars", file=sys.stderr)

    # Phase 2: locate SKILL.md paths
    print(f"[2/4] locating SKILL.md paths...", file=sys.stderr)
    cands: list[Candidate] = []

    def locate(meta: dict) -> list[Candidate]:
        fn = meta["full_name"]
        paths = []
        if "_hint_path" in meta:
            paths.append(meta["_hint_path"])
        else:
            paths = list_skill_paths(fn)
        out = []
        if not paths:
            return out
        # pick the most relevant path: shortest path that contains a query term in dirname
        chosen = paths[0]
        best_score = -1
        for p in paths:
            score = topic_match_score(p, queries)
            if score > best_score:
                chosen = p
                best_score = score
        out.append(Candidate(
            full_name=fn,
            path=chosen,
            stars=meta["stars"],
            description=meta["description"],
            language=meta["language"],
            html_url=meta["html_url"],
            pushed_at=meta["pushed_at"],
        ))
        return out

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(locate, m) for m in candidates.values()]
        for f in as_completed(futures):
            try:
                cands.extend(f.result())
            except Exception as e:
                print(f"[locate-err] {e}", file=sys.stderr)

    print(f"      {len(cands)} candidates with SKILL.md", file=sys.stderr)

    # Phase 3: fetch commits in parallel
    print(f"[3/4] fetching commit history (parallel x{args.workers})...", file=sys.stderr)

    def fill_commits(c: Candidate) -> Candidate:
        c.commits = get_commits_for_path(c.full_name, c.path)
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

    # Phase 4: rank
    print(f"[4/4] ranking...", file=sys.stderr)
    cands.sort(
        key=lambda c: (
            TIER_RANK.get(c.tier, 0),
            c.unique_days,
            c.stars,
        ),
        reverse=True,
    )

    data = {
        "query": args.query,
        "variants": args.variants,
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

    print(f"\n## Find Skills — {data['query']}")
    print(f"Variants: {data['variants']}")
    print(f"Total candidates inspected: {len(data['candidates'])}\n")

    print("| Tier | Days | Commits | Span(d) | Authors | ★ | Repo | Path | Lang |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in cands:
        tier_emoji = {
            "battle-tested": "🏆",
            "well-polished": "✨",
            "iterated": "🔧",
            "drive-by": "💨",
        }.get(c["tier"], "?")
        repo_link = f"[{c['full_name']}]({c['html_url']})"
        path_short = c["path"] if len(c["path"]) < 50 else "..." + c["path"][-47:]
        print(
            f"| {tier_emoji} {c['tier']} | {c['unique_days']} | {c['total_commits']} | "
            f"{c['days_span']} | {c['unique_authors']} | {c['stars']} | "
            f"{repo_link} | `{path_short}` | {c['language'] or '-'} |"
        )

    print()
    for i, c in enumerate(cands[:3], 1):
        print(f"\n### #{i} — {c['full_name']}")
        if c['description']:
            print(f"   {c['description']}")
        print(f"   First edit: {c['first_commit']}  →  Last: {c['last_commit']}")
        print(f"   {c['unique_days']} polish days across {c['days_span']}d "
              f"({c['unique_authors']} author{'s' if c['unique_authors']!=1 else ''})")


if __name__ == "__main__":
    main()
