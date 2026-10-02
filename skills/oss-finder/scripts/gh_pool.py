#!/usr/bin/env python3
"""
gh_pool.py — GitHub REST helper using a rotating PAT pool.

Loads PATs from ~/.config/kargnas/oss-finder.env (one PAT per GitHub account;
3 accounts = 90 req/min on the Search API, 5000 req/h core per token).
GH_PAT_<n> environment variables extend the pool.

Usage as library:
    from gh_pool import gh_get, code_search, repo_commits

    items = code_search("filename:SKILL.md path:.agents/skills", per_page=100)
    for it in items["items"]:
        print(it["repository"]["full_name"], it["path"])

Usage as CLI:
    python3 gh_pool.py --check          # exit 0 = PAT pool + gh CLI ready, 1 = setup needed
    python3 gh_pool.py /repos/octocat/hello-world
    python3 gh_pool.py /search/code 'q=filename:SKILL.md+path:.agents/skills'
"""
from __future__ import annotations

import itertools
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote

import ssl
import urllib.request
import urllib.error

# macOS python.org builds ship without linked root CAs, so urllib's default SSL
# context fails with CERTIFICATE_VERIFY_FAILED. Use certifi's CA bundle when it
# is importable (no SSL_CERT_FILE env needed); fall back to the system default.
try:
    import certifi

    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CONTEXT = ssl.create_default_context()

PAT_CONFIG_FILE = Path.home() / ".config" / "kargnas" / "oss-finder.env"
PAT_ENV_PREFIX = "GH_PAT_"
PAT_META_SUFFIXES = ("_OWNER", "_EMAIL")

# Printed whenever the pool is empty. The scripts refuse to run without PATs
# instead of degrading to anonymous requests (60 req/h), which cannot finish a
# single polish-day sweep.
SETUP_HINT = f"""\
[oss-finder] No GitHub PATs loaded — the PAT pool is not configured.
  1. Create one PAT per GitHub account (public search needs only public-repo read access).
  2. Write them to {PAT_CONFIG_FILE} as GH_PAT_1=..., GH_PAT_2=... and chmod 600 the file.
  3. Re-run: python3 {Path(__file__).name} --check
  See SKILL.md "Step 0" for the full setup."""


def load_pats() -> list[str]:
    """Load PATs from the config file, then from GH_PAT_<n> env vars."""
    pats: list[str] = []
    if PAT_CONFIG_FILE.exists():
        for line in PAT_CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip()
            if k.startswith(PAT_ENV_PREFIX) and not k.endswith(PAT_META_SUFFIXES):
                if (v.startswith("github_pat_") or v.startswith("ghp_")) and v not in pats:
                    pats.append(v)
    # Env vars override / extend
    for k, v in os.environ.items():
        if k.startswith(PAT_ENV_PREFIX) and not k.endswith(PAT_META_SUFFIXES) and v:
            if v not in pats:
                pats.append(v)
    return pats


_PATS = load_pats()
_TOKEN_LOCK = threading.Lock()
_TOKEN_CYCLE = itertools.cycle(_PATS) if _PATS else None


def have_pats() -> bool:
    return bool(_PATS)


def pat_count() -> int:
    return len(_PATS)


def require_pats() -> None:
    """Exit with the setup hint when the pool is empty. Every entrypoint calls
    this first so a missing pool stops the run instead of silently going anonymous."""
    if not _PATS:
        print(SETUP_HINT, file=sys.stderr)
        sys.exit(2)


def check_setup() -> int:
    """`--check`: report PAT pool + gh CLI auth. Returns 0 when both are ready.

    The bundled scripts only need the pool; the inline `gh search` / `gh api`
    steps in SKILL.md need an authenticated gh CLI, so both are checked here.
    """
    ok = True
    if _PATS:
        print(f"[oss-finder] PATs loaded: {len(_PATS)} (from {PAT_CONFIG_FILE} + GH_PAT_* env)")
    else:
        print(SETUP_HINT)
        ok = False
    try:
        r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            print("[oss-finder] gh CLI: authenticated")
        else:
            print("[oss-finder] gh CLI: not authenticated — run `gh auth login` "
                  "(the inline `gh search` / `gh api` steps need it)")
            ok = False
    except FileNotFoundError:
        print("[oss-finder] gh CLI: not installed — install GitHub CLI, then run `gh auth login`")
        ok = False
    print("READY" if ok else "SETUP NEEDED")
    return 0 if ok else 1


def next_token() -> str | None:
    """Round-robin next PAT. Thread-safe. Returns None if no PATs."""
    if not _TOKEN_CYCLE:
        return None
    with _TOKEN_LOCK:
        return next(_TOKEN_CYCLE)


def gh_get(
    path: str,
    params: dict | None = None,
    max_retries: int = 3,
    timeout: int = 30,
) -> dict | list | None:
    """GET against api.github.com with rotating PAT auth.

    path: starts with '/' (e.g. '/repos/octocat/hello').
    params: dict of query params. Values are URL-quoted.
    Returns parsed JSON, or None on persistent failure.
    """
    url = f"https://api.github.com{path}"
    if params:
        qs = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())
        url = f"{url}?{qs}"

    for attempt in range(max_retries):
        tok = next_token()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "oss-finder-gh-pool/1.0",
        }
        if tok:
            headers["Authorization"] = f"Bearer {tok}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            remaining = e.headers.get("X-RateLimit-Remaining", "?") if e.headers else "?"
            reset = e.headers.get("X-RateLimit-Reset", "?") if e.headers else "?"
            if e.code == 403 and remaining == "0":
                # Current PAT exhausted; the next round-robin pick may have headroom.
                if attempt < max_retries - 1:
                    continue
                # All retries used; back off until reset (capped).
                sleep_s = max(1, int(reset) - int(time.time())) if reset != "?" else 60
                print(
                    f"[gh-pool] all PATs exhausted, sleeping {min(sleep_s, 60)}s",
                    file=sys.stderr,
                )
                time.sleep(min(sleep_s, 60))
                continue
            if e.code in (403, 429):
                # Secondary rate limit / abuse detection
                time.sleep(5 * (attempt + 1))
                continue
            if e.code == 422:
                # Invalid query — not retryable
                return None
            print(f"[gh-pool {e.code}] {url[:120]}", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception as e:
            print(f"[gh-pool err] {url[:120]}: {e}", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
    return None


# ---------------------------------------------------------------------------
# Convenience wrappers for common Search/Repo calls
# ---------------------------------------------------------------------------


def code_search(query: str, per_page: int = 30, page: int = 1):
    """Search code. Returns full response dict with total_count + items."""
    return gh_get("/search/code", {"q": query, "per_page": per_page, "page": page})


def repo_search(query: str, per_page: int = 30, page: int = 1):
    """Search repositories."""
    return gh_get(
        "/search/repositories", {"q": query, "per_page": per_page, "page": page}
    )


def repo_info(full_name: str):
    """GET /repos/{owner}/{repo}"""
    return gh_get(f"/repos/{full_name}")


def repo_contents(full_name: str, path: str, ref: str | None = None):
    """GET /repos/{owner}/{repo}/contents/{path}"""
    params = {"ref": ref} if ref else None
    return gh_get(f"/repos/{full_name}/contents/{path}", params)


def repo_commits(
    full_name: str,
    path: str | None = None,
    per_page: int = 100,
    page: int = 1,
):
    """GET /repos/{owner}/{repo}/commits"""
    params: dict = {"per_page": per_page, "page": page}
    if path:
        params["path"] = path
    return gh_get(f"/repos/{full_name}/commits", params)


def rate_limit():
    """GET /rate_limit — useful to check pool health."""
    return gh_get("/rate_limit")


# ---------------------------------------------------------------------------
# CLI entry: --check, or an API path with an optional querystring "k=v&k=v"
# ---------------------------------------------------------------------------


def _parse_query(s: str) -> dict:
    out = {}
    for chunk in s.split("&"):
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            out[k] = v
    return out


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--check":
        sys.exit(check_setup())
    if len(sys.argv) < 2:
        print("usage: gh_pool.py --check | <api-path> [k=v&k=v]", file=sys.stderr)
        print(f"PATs loaded: {pat_count()}", file=sys.stderr)
        sys.exit(2)
    require_pats()
    path = sys.argv[1]
    params = _parse_query(sys.argv[2]) if len(sys.argv) > 2 else None
    result = gh_get(path, params)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
