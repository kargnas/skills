# Importing Heavy / Collector-Bundled External Skill Repos

Supplements `guides/importing-external-skills.md`. Use this WHEN the community
repo bundles RUNTIME CODE (data collectors, network tools, an LLM distiller)
rather than a lone SKILL.md, and the user asks to "verify first." A community
"skill" is often a whole framework: e.g. a 10MB / 108-file engine with
Slack/Feishu/DingTalk/email auto-collectors and an LLM distiller. Blind-cloning
that into a host skills dir is wrong. Audit first, then report, then install.

## Step A — trace every outbound network destination (MUST)

Confirm collectors/tools POST/PUT only to the official APIs the skill claims, not
a third-party exfil endpoint:

```bash
grep -rnE "requests\.(post|put)|httpx\.(post|put)|urlopen|fetch\(" <repo-tmp>/tools/ <repo-tmp>/scripts/ 2>/dev/null
grep -rnE "https?://[a-z0-9.-]+" <repo-tmp>/tools/ 2>/dev/null | sort -u | head -30
```

PASS only if every host is a documented official API (one audited repo verified
clean: `open.feishu.cn/open-apis`, `api.dingtalk.com` — tokens are user-issued
app tokens hitting only those APIs). An unexplained third-party host → STOP and
report to the user; do not install.

## Step B — manifest the env vars / API keys it reads (MUST)

Record them in `metadata.env` on import (required/optional + one-line purpose):

```bash
grep -rhoE "os\.environ(\.get)?\(['\"][A-Z_]+|process\.env\.[A-Z_]+|getenv\(['\"][A-Z_]+" <repo-tmp>/ 2>/dev/null | sort -u
```

One audited repo read `OPENAI_API_KEY` (user's key → billable LLM calls) plus
its own auto-install flag. The user must be told about any billable-key use.

## Step C — slim on import, drop non-functional bloat

Marketing assets (WeChat group QR pngs, promo PDFs), multi-language READMEs,
ownership-claim txt files (`openarena-claim.txt`), and `.git` are dead weight.
Copy only what the skill needs:

```bash
rsync -a --exclude='.git' --exclude='docs/assets' --exclude='*.pdf' \
  --exclude='docs/lang' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='<ownership-claim>.txt' <repo-tmp>/ <dest>/
# example result: 10MB/108 files -> 756KB/82 files
```

## Step D — report the audit verdict BEFORE finalizing

Tell the user: (1) no-exfil result + which official hosts the collectors hit,
(2) which env keys it reads and whether any are billable, (3) what you dropped as
bloat, (4) any name collision with an existing same-class skill. Then proceed.
This follows a verify-first policy over silent install.

## Bonus — distinguish a dead shell from a real collision

An existing same-named skill dir may be an EMPTY shell (0 files), not a real
skill — one import found the pre-existing same-name dir had zero files. An empty
shell is not a true collision: remove it (`rmdir`) and proceed. Only a populated
same-name skill triggers the rename/replace/absorb decision from the main guide.
