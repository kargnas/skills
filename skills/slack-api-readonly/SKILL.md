---
name: slack-api-readonly
description: Scrape Slack read-only via Web API (user token) into markdown for LLM. Use to FETCH Slack conversation directly — by channel, thread permalink, or search — without copy-paste. Real names, mrkdwn unwrapped, emoji/reactions kept, tz configurable; --files downloads images/attachments. Stdout-only otherwise. Formats pasted Slack text with the bundled cleaner.
---

# Slack API Read-Only Scrape

Pulls Slack messages straight from the Web API and prints one markdown document
to stdout. No copy-paste, no LLM context spent on the raw conversation.

## Prerequisite: user token

Needs a Slack **user** token (`xoxp-*`) in the environment — a bot token cannot
search or read DMs. Put it in `~/.zshenv`:

```zsh
export AGENT_SLACK_USER_TOKEN=xoxp-...
```

Read scopes it uses: `channels:history` `groups:history` `im:history`
`mpim:history` `channels:read` `users:read` `users.profile:read` `search:read`
`reactions:read` `files:read` `emoji:read`.

## Usage

EXECUTE the script (do not reimplement it):

```bash
# a channel by name or ID, newest 200 msgs, threads expanded, KST
scripts/scrape_slack.py --channel eng-team > out.md

# drop a translation bot (repeatable; matches sender name substring)
scripts/scrape_slack.py --channel eng-team --exclude "Translator" > out.md

# one thread from a message permalink
scripts/scrape_slack.py --thread 'https://xxx.slack.com/archives/C0AB/p1700000000123456'

# a search query (user token only)
scripts/scrape_slack.py --search 'rollback in:#eng-team' > out.md

# narrow a channel by date + render in another timezone
scripts/scrape_slack.py --channel C0AB --since 2026-07-01 --until 2026-07-22 --tz America/New_York

# download attachments too: ./files/ next to out.md, images embed as ![name](files/…)
scripts/scrape_slack.py --channel eng-team --files > out.md

# or name the basedir yourself (keep it relative to out.md's location)
scripts/scrape_slack.py --channel eng-team --files attachments > out.md
```

Sources are mutually exclusive — pick exactly one of `--channel` / `--thread`
/ `--search`.

## Options

- `--tz IANA` — timezone for timestamps (default `Asia/Seoul`); recorded in frontmatter
- `--limit N` — max messages (default 200)
- `--since` / `--until YYYY-MM-DD` — channel-mode date window
- `--no-threads` — channel mode: don't expand thread replies
- `--title` — frontmatter title/source label
- `--exclude NAME` — drop senders containing NAME (repeatable; e.g. translation bots)
- `--files [DIR]` — download attachments into DIR (default `files`, relative to
  where the md lives — run from that dir). Images embed as `![name](DIR/…)`,
  other files link; the basedir is recorded as `files_dir` in the frontmatter,
  so md + DIR move together as a portable bundle. Without the flag, only
  `[file: name]` markers (nothing is written anywhere)

## Output

Frontmatter identifies the conversation — `channel` + `channel_type`
(`channel` / `private-channel` / `dm` / `group-dm`; DM shows the counterpart's
name, group DM lists members) or `search` for search mode — plus `captured`,
`tz`, `participants`. No H1; messages follow, grouped by `## YYYY-MM-DD` day
headers:

```
Real Name [14:11] first body line
continuation lines flush left

  ↳ Reply Name [14:12] thread replies indented, packed tight
  ↳ Other Name [14:18] consecutive same-sender messages (≤3 min apart)
    fold into one block as continuation lines
```

Mentions render as `<@Real Name>` / `<@subteam-handle>`, channels as `#name`,
links unwrapped to bare URL or label. Standard reaction emoji become unicode
(`👍×3`); custom workspace emoji keep their slug (`:acme:×1`). File
attachments append per message.

Senders whose Slack **profile timezone** (users.info — never guessed) differs
from the document tz get a dual stamp on their first message and then at most
once per hour: `Casey Morgan [11:59 KST / 21:59 CDT] …`. Same-offset zones
(Seoul vs Tokyo) are not annotated. Every abbreviation used in the body is
defined in a frontmatter `timezones:` map (`CDT: "America/Chicago"`) so
ambiguous codes can't be misread; the key is omitted when no annotation occurs.

## Pasted Slack text

Use the bundled read-only filter for Slack desktop copy-paste. It reads a file or stdin and writes only stdout.

```bash
pbpaste | scripts/clean_slack.py
scripts/clean_slack.py paste.txt > out.txt
pbpaste | scripts/clean_slack.py --exclude "Translator" --strip ':robot_face:.*'
```

The parser accepts Korean and English timestamps, removes edit markers, thread-count lines, and blank runs, and preserves multiline message bodies.

## Always-on API cleaners

- system-subtype noise (joins, topic changes, …) dropped
- empty messages dropped
- user IDs resolved to real names (cached per run)

## Self-check

```bash
scripts/scrape_slack.py --selftest   # prints "selftest ok" — no network
scripts/clean_slack.py --selftest     # prints "selftest ok" — no network
```
