# GitHub REST API vs Blackbird (Web UI) code-search index gap

## The problem

GitHub's REST API `/search/code` and the Web UI's code search use **different search engines and indexes**:

| Engine | Used by | Index coverage |
|---|---|---|
| **Blackbird** | Web UI (`github.com/search?type=code`) | Full — same as what humans see |
| **Legacy (REST API v3)** | `gh search code`, `gh api /search/code` | SUBSET — misses many repos |

Repos with 0 stars, small size, and infrequent pushes are often absent from the legacy index entirely:

1. **`repo:` filter doesn't help.** `filename:SKILL.md repo:<owner>/<repo>` returns 0 via REST when the repo is not in the index — the query is fine, the repo is simply not there.
2. **Data endpoints still work.** `gh api repos/<owner>/<repo>/git/trees/HEAD` returns the tree; only the SEARCH index excludes the repo.
3. **Web search engines usually can't find it either.** Google/Bing rarely crawl file contents of low-star repos.
4. **Blackbird requires login.** The unauthenticated Web UI shows "Sign in to search code on GitHub."

So a REST-only sweep can return 0 for a repo the Web UI finds on the first page. NEVER treat API-only results as exhaustive.

## Solution: cloakbrowser + persistent GitHub profile

### One-time setup

```python
import asyncio, cloakbrowser, os

async def setup_github_profile():
    """Launch headed browser for user to log in with 2FA."""
    profile_dir = os.path.expanduser("~/.cloakbrowser-profiles/github")
    ctx = await cloakbrowser.launch_persistent_context_async(
        user_data_dir=profile_dir, headless=False, stealth_args=True,
    )
    try:
        page = await ctx.new_page()
        await page.goto("https://github.com/login", wait_until="networkidle", timeout=30000)
        # User manually completes login + 2FA in the browser window
        # Wait up to 90s for redirect to github.com (away from login/two-factor pages)
        for i in range(90):
            await page.wait_for_timeout(1000)
            url = page.url
            if "github.com" in url and "two-factor" not in url and "login" not in url:
                print(f"Logged in after {i}s: {url}")
                break
        # Keep browser open briefly so cookies persist
        await asyncio.sleep(5)
    finally:
        await ctx.close()
```

### Search function (headless, reuses saved session)

```python
import asyncio, cloakbrowser, os
from urllib.parse import quote

async def blackbird_code_search(query: str) -> list[dict]:
    """Search GitHub code using Blackbird engine via persistent login."""
    profile_dir = os.path.expanduser("~/.cloakbrowser-profiles/github")
    ctx = await cloakbrowser.launch_persistent_context_async(
        user_data_dir=profile_dir, headless=True, stealth_args=True,
    )
    try:
        page = await ctx.new_page()
        encoded = quote(f"{query} path:SKILL.md")
        url = f"https://github.com/search?q={encoded}&type=code"
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
        content = await page.evaluate("document.body.innerText")
        results = []
        for line in content.split("\n"):
            if "·" in line and "SKILL.md" in line:
                parts = line.strip().split("·")
                repo = parts[0].strip()
                path = parts[1].strip() if len(parts) > 1 else ""
                results.append({"full_name": repo, "path": path})
        return results
    finally:
        await ctx.close()
```

### Gotchas

1. **`wait_until="networkidle"` times out on GitHub search pages.** Use `"domcontentloaded"` + 3-5s explicit wait.
2. **`headless=False` is required for the initial login** (the user must complete 2FA). After the profile is saved, `headless=True` works.
3. **Profile directory lock.** If a previous cloakbrowser process crashed, a `SingletonLock` file may block new launches: `rm ~/.cloakbrowser-profiles/github/SingletonLock`.
4. **Session expiry.** GitHub sessions last ~weeks. If search returns "Sign in to search code on GitHub", re-run the headed setup flow.
5. **Run it as a standalone Python script in a terminal**, not inside a code sandbox that lacks `cloakbrowser` (`pip install cloakbrowser`).
