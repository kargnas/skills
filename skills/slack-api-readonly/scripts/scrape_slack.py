#!/usr/bin/env python3
"""Scrape Slack (read-only) into a markdown doc via the Web API.

Reads AGENT_SLACK_USER_TOKEN (a Slack *user* token, xoxp-*) and pulls messages
from ONE of three sources, printing a single markdown document to stdout:

    --channel NAME|ID     conversations.history (+ thread replies)
    --thread  PERMALINK   conversations.replies for one thread
    --search  QUERY       search.messages

Format: `Real Name [HH:MM] body` lines, thread replies as `  ↳ Name [HH:MM] …`,
consecutive same-sender messages folded into one block. Mentions render as
<@Real Name> / <@subteam-handle>; standard reaction emoji become unicode
(👍×3), custom workspace emoji keep their slug (:acme:×1). File attachments
are appended per message. Times render in --tz (default Asia/Seoul), with the tz
recorded in the frontmatter. Read-only: writes nowhere except stdout — unless
you opt in with --files [DIR] (default "files", relative to where the md will
live), which downloads attachments there, embeds images as ![name](DIR/file),
and records the basedir as files_dir in the frontmatter.

A user token is required because search.messages and private/DM history need
user scopes a bot token (xoxb) cannot hold.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

API = "https://slack.com/api/"


def ssl_context() -> ssl.SSLContext:
    """Default context, but python.org macOS builds ship with NO CA paths set
    (until Install Certificates.command is run) — fall back to certifi or the
    system bundle so verification still happens instead of failing."""
    ctx = ssl.create_default_context()
    paths = ssl.get_default_verify_paths()
    if paths.cafile is None and paths.capath is None:
        try:
            import certifi  # optional; user-site install is common
            ctx.load_verify_locations(certifi.where())
        except ImportError:
            if os.path.exists("/etc/ssl/cert.pem"):  # macOS system bundle
                ctx.load_verify_locations("/etc/ssl/cert.pem")
            # else: leave as-is; urlopen will fail loudly, which beats no verify
    return ctx


_SSL_CTX = ssl_context()
TOKEN_ENV = "AGENT_SLACK_USER_TOKEN"
# Slack system messages that are pure noise in an evidence log.
SKIP_SUBTYPES = {
    "channel_join", "channel_leave", "channel_topic", "channel_purpose",
    "channel_name", "channel_archive", "channel_unarchive", "bot_add", "bot_remove",
}


def die(msg: str) -> None:
    sys.exit(f"error: {msg}")


# ---- HTTP --------------------------------------------------------------------

def api_call(method: str, token: str, **params) -> dict:
    """GET a Slack Web API method. Dies (no silent failure) on any error."""
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(
        f"{API}{method}?{query}", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        die(f"{method}: HTTP {exc.code}")
    except urllib.error.URLError as exc:
        die(f"{method}: network error: {exc.reason}")
    if not data.get("ok"):
        err = data.get("error", "unknown")
        # Turn the most common opaque errors into an actionable hint.
        hint = {
            "not_in_channel": " (the token's user must be a member of that channel)",
            "channel_not_found": " (wrong name/ID, or no access)",
            "missing_scope": f" (token missing scope: {data.get('needed')})",
            "invalid_auth": f" (check ${TOKEN_ENV})",
            "not_authed": f" (check ${TOKEN_ENV})",
            "token_revoked": f" (${TOKEN_ENV} was revoked — reissue it)",
        }.get(err, "")
        die(f"{method}: {err}{hint}")
    return data


def paginate(method: str, token: str, limit: int | None, **params) -> list[dict]:
    """Follow cursor pagination, returning up to `limit` messages."""
    out: list[dict] = []
    cursor = None
    while True:
        page = min(200, limit - len(out)) if limit else 200
        data = api_call(method, token, limit=page, cursor=cursor, **params)
        out.extend(data.get("messages", []))
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor or (limit and len(out) >= limit):
            break
    return out[:limit] if limit else out


# ---- name + mrkdwn resolution ------------------------------------------------

_user_cache: dict[str, str] = {}
_user_tz: dict[str, str | None] = {}  # uid → IANA tz from users.info (NO guessing)
_usergroup_cache: dict[str, str] = {}
_usergroups_loaded = False


def subteam_handle(token: str, sid: str) -> str:
    """Resolve <!subteam^S…> IDs to @handles via usergroups.list (one call/run)."""
    global _usergroups_loaded
    if not _usergroups_loaded:
        _usergroups_loaded = True
        try:
            for g in api_call("usergroups.list", token)["usergroups"]:
                _usergroup_cache[g["id"]] = g.get("handle") or g.get("name") or g["id"]
        except SystemExit:
            pass  # missing usergroups:read must not kill the scrape — keep raw IDs
    return _usergroup_cache.get(sid, sid)


def user_name(token: str, uid: str) -> str:
    if uid not in _user_cache:
        try:
            u = api_call("users.info", token, user=uid)["user"]
        except SystemExit:
            # A single unresolvable uid (deleted account, foreign org member in a
            # Connect channel) must not kill a whole channel scrape — keep the raw ID.
            _user_cache[uid] = uid
            _user_tz[uid] = None
            return uid
        prof = u.get("profile", {})
        # Prefer real_name ("Jane Doe") over the login handle ("jdoe").
        _user_cache[uid] = (
            prof.get("real_name")
            or u.get("real_name")
            or prof.get("display_name")
            or u.get("name")
            or uid
        )
        # The profile's own tz setting — the only non-guessed source we accept.
        _user_tz[uid] = u.get("tz") or None
    return _user_cache[uid]


MENTION_RE = re.compile(r"<@([UW][A-Z0-9]+)(?:\|[^>]*)?>")
CHANNEL_RE = re.compile(r"<#[CG][A-Z0-9]+\|([^>]*)>")
LINK_RE = re.compile(r"<(https?://[^|>]+)(?:\|([^>]*))?>")
SPECIAL_RE = re.compile(r"<!([^|>]+)(?:\|([^>]*))?>")  # <!here>, <!subteam^ID|@handle>, <!date^...|fallback>


def unwrap(text: str, token: str) -> str:
    """Turn Slack mrkdwn entities into plain readable text."""
    # Mentions keep the <@…> shape but with the resolved real name inside —
    # still visually a mention, but greppable by name.
    text = MENTION_RE.sub(lambda m: f"<@{user_name(token, m.group(1))}>", text)
    text = CHANNEL_RE.sub(lambda m: "#" + m.group(1), text)

    def link(m):
        url, label = m.group(1), m.group(2)
        # Slack truncates long URLs into "youtu.be/…?si=…" display labels —
        # keep the real URL in that case, the label only when it's real words.
        return label if label and "…" not in label else url

    text = LINK_RE.sub(link, text)

    def special(m):
        label = m.group(2)
        if label:  # subteam labels carry "@" (<!subteam^S1|@eng>) — normalize into <@…>
            return f"<@{label.lstrip('@')}>"
        inner = m.group(1)
        if inner.startswith("subteam^"):
            return f"<@{subteam_handle(token, inner[len('subteam^'):])}>"
        return f"<@{inner}>"  # <!here>, <!channel>, …

    text = SPECIAL_RE.sub(special, text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return text.strip()


FILES_DIR: str | None = None  # set by --files; None keeps [file: name] markers
_downloaded: dict[str, str | None] = {}  # file id → local path (dedupes thread/channel repeats)


def download_file(token: str, f: dict) -> str | None:
    fid = f.get("id") or f.get("name", "file")
    if fid in _downloaded:
        return _downloaded[fid]
    url = f.get("url_private_download") or f.get("url_private")
    path = None
    if url:
        safe = re.sub(r"[^\w.\-]+", "_", f.get("name") or fid)
        path = os.path.join(FILES_DIR, f"{fid}-{safe}")  # id prefix: same-named files can't collide
        if not os.path.exists(path):
            try:
                req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
                with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as r:
                    ctype = r.headers.get("Content-Type", "")
                    # Slack serves an HTML login page instead of 403 when the token
                    # can't fetch the binary — catch that so we don't save junk.
                    if ctype.startswith("text/html") and not (f.get("mimetype") or "").startswith("text/html"):
                        raise OSError(f"got HTML (auth wall?) for {f.get('mimetype')}")
                    with open(path, "wb") as w:
                        shutil.copyfileobj(r, w)
            except (urllib.error.URLError, OSError) as exc:
                # One dead attachment must not kill a 200-message scrape; the
                # warning + inline marker keep the failure visible, not silent.
                print(f"warning: download failed: {f.get('name')}: {exc}", file=sys.stderr)
                if os.path.exists(path):
                    os.remove(path)  # drop partial write
                path = None
    _downloaded[fid] = path
    return path


def file_ref(token: str, f: dict) -> str:
    name = f.get("name") or f.get("id", "file")
    if not FILES_DIR:
        return f"[file: {name}]"
    path = download_file(token, f)
    if not path:
        return f"[file: {name} (not downloaded)]"  # external/Drive files have no url_private
    mark = "!" if (f.get("mimetype") or "").startswith("image/") else ""
    return f"{mark}[{name}]({path})"


# Common Slack default reaction slugs → unicode. Anything not here (custom
# workspace emoji like :acme:) stays in :slug: form on purpose.
EMOJI = {
    "+1": "👍", "thumbsup": "👍", "-1": "👎", "thumbsdown": "👎",
    "heavy_check_mark": "✔️", "white_check_mark": "✅", "ballot_box_with_check": "☑️",
    "x": "❌", "o": "⭕", "100": "💯", "ok_hand": "👌", "v": "✌️",
    "joy": "😂", "rolling_on_the_floor_laughing": "🤣", "smile": "😄", "smiley": "😃",
    "grin": "😁", "laughing": "😆", "sweat_smile": "😅", "blush": "😊", "wink": "😉",
    "slightly_smiling_face": "🙂", "upside_down_face": "🙃", "smiling_face_with_tear": "🥲",
    "melting_face": "🫠", "saluting_face": "🫡", "pleading_face": "🥺",
    "exploding_head": "🤯", "partying_face": "🥳", "thinking_face": "🤔",
    "face_with_rolling_eyes": "🙄", "neutral_face": "😐", "flushed": "😳",
    "cry": "😢", "sob": "😭", "disappointed": "😞", "scream": "😱", "rage": "😡",
    "heart": "❤️", "heart_eyes": "😍", "two_hearts": "💕", "broken_heart": "💔",
    "blue_heart": "💙", "yellow_heart": "💛", "green_heart": "💚", "purple_heart": "💜",
    "tada": "🎉", "confetti_ball": "🎊", "fire": "🔥", "rocket": "🚀", "sparkles": "✨",
    "star": "⭐", "zap": "⚡", "boom": "💥", "bulb": "💡", "memo": "📝",
    "eyes": "👀", "pray": "🙏", "clap": "👏", "raised_hands": "🙌", "muscle": "💪",
    "wave": "👋", "handshake": "🤝", "crossed_fingers": "🤞", "call_me_hand": "🤙",
    "point_up": "☝️", "bow": "🙇", "warning": "⚠️", "question": "❓",
    "heavy_exclamation_mark": "❗", "heavy_plus_sign": "➕", "salute": "🫡",
}


def emoji_char(name: str) -> str:
    """Unicode for standard slugs; skin-tone variants fold to the base emoji;
    unknown (= custom workspace) slugs stay as :slug:."""
    base = name.split("::")[0]
    return EMOJI.get(name) or EMOJI.get(base) or f":{name}:"


def extras(msg: dict, token: str) -> str:
    """File attachments + reactions, appended to a message body."""
    parts = [file_ref(token, f) for f in msg.get("files") or []]
    rs = msg.get("reactions") or []
    if rs:
        parts.append(" ".join(f"{emoji_char(r['name'])}×{r['count']}" for r in rs))
    return " ".join(p for p in parts if p)


def to_msg(raw: dict, token: str, tz: str) -> dict:
    dt = datetime.fromtimestamp(float(raw["ts"]), ZoneInfo(tz))
    uid = raw.get("user") or ""
    if uid[:1] in ("U", "W"):
        name = user_name(token, uid)
        utz = _user_tz.get(uid)
    else:
        name = raw.get("username") or raw.get("bot_id") or "unknown"
        utz = None  # bots carry no profile tz — never annotate, never guess
    body = " ".join(p for p in (unwrap(raw.get("text", ""), token), extras(raw, token)) if p).strip()
    ch = raw.get("channel")
    # ctx guards block-merging: search matches from different channels must not
    # fold together even when sender+time line up. History/replies have no
    # channel field → None, where adjacency already implies the same context.
    ctx = ch.get("id") if isinstance(ch, dict) else None
    return {"dt": dt, "name": name, "body": body, "reply": False, "ctx": ctx, "utz": utz}


def collect(raws: list[dict], token: str, tz: str) -> list[dict]:
    """Drop system-subtype noise and empty messages; keep the rest."""
    out = []
    for raw in raws:
        if raw.get("subtype") in SKIP_SUBTYPES:
            continue
        m = to_msg(raw, token, tz)
        if m["body"]:
            out.append(m)
    return out


# ---- sources -----------------------------------------------------------------

def conv_info(token: str, cid: str) -> dict:
    return api_call("conversations.info", token, channel=cid)["channel"]


def conv_label(token: str, c: dict) -> tuple[str, str]:
    """Frontmatter (channel, channel_type) for any conversation kind."""
    if c.get("is_im"):  # DM: the label is the counterpart's name
        return user_name(token, c["user"]), "dm"
    if c.get("is_mpim"):  # group DM: list every member (mpims are small)
        ids = api_call("conversations.members", token, channel=c["id"])["members"]
        return ", ".join(user_name(token, u) for u in ids), "group-dm"
    # is_mpim checked first — mpims also carry is_private
    kind = "private-channel" if c.get("is_private") else "channel"
    return "#" + c.get("name", c["id"]), kind


def resolve_channel(token: str, chan: str) -> dict:
    """Name or ID → full conversation object (needed for type metadata)."""
    if re.fullmatch(r"[CGD][A-Z0-9]+", chan):
        return conv_info(token, chan)
    name = chan.lstrip("#")
    cursor = None
    while True:
        data = api_call(
            "conversations.list", token, cursor=cursor, limit=1000,
            types="public_channel,private_channel,mpim,im",
        )
        for c in data["channels"]:
            if c.get("name") == name:
                return c
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            die(f"channel not found: {chan}")


def fetch_channel(token, cid, tz, limit, oldest, latest, threads) -> list[dict]:
    # history is newest-first; walk it into chronological order.
    raws = list(reversed(paginate(
        "conversations.history", token, limit, channel=cid, oldest=oldest, latest=latest
    )))
    msgs: list[dict] = []
    for raw in raws:
        if raw.get("subtype") in SKIP_SUBTYPES:
            continue
        m = to_msg(raw, token, tz)
        if m["body"]:
            msgs.append(m)
        if threads and raw.get("reply_count"):
            # One page (200 replies) per thread; paginate if threads outgrow it
            replies = api_call(
                "conversations.replies", token, channel=cid, ts=raw["ts"], limit=200
            )["messages"]
            for rep in collect(replies[1:], token, tz):  # [0] is the parent
                rep["reply"] = True
                msgs.append(rep)
    return msgs


PERMALINK_RE = re.compile(r"/archives/([CGD][A-Z0-9]+)/p(\d{10})(\d{6})")


def parse_permalink(url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(url)
    m = PERMALINK_RE.search(parsed.path)
    if not m:
        die(f"cannot parse thread permalink: {url}")
    cid, sec, micro = m.groups()
    q = urllib.parse.parse_qs(parsed.query)
    # A reply's permalink carries the parent in thread_ts / the channel in cid.
    ts = q.get("thread_ts", [f"{sec}.{micro}"])[0]
    cid = q.get("cid", [cid])[0]
    return cid, ts


def fetch_thread(token, cid, ts, tz) -> list[dict]:
    replies = api_call("conversations.replies", token, channel=cid, ts=ts, limit=200)["messages"]
    msgs = collect(replies, token, tz)
    for i, m in enumerate(msgs):
        m["reply"] = i > 0
    return msgs


def fetch_search(token, query, tz, limit) -> list[dict]:
    matches: list[dict] = []
    page = 1
    while len(matches) < (limit or 100):
        # newest-first so --limit keeps the most recent matches; reversed below
        # so the rendered doc reads chronologically (day headers stay monotonic).
        data = api_call("search.messages", token, query=query, count=100, page=page,
                        sort="timestamp", sort_dir="desc")
        block = data["messages"]
        matches.extend(block["matches"])
        if page >= block["paging"]["pages"] or not block["matches"]:
            break
        page += 1
    return collect(list(reversed(matches[:limit] if limit else matches)), token, tz)


# ---- render ------------------------------------------------------------------

# A 3-minute window folds rapid-fire same-sender messages into one
# block; raise it if people in your workspace monologue more slowly.
MERGE_GAP_S = 180
# A remote sender's local time is re-shown at most once per hour to keep noise down.
TZ_ANNOTATE_GAP_S = 3600


def tz_stamp(b: dict, stamp: str, last_anno: dict, doc_tz: str, tz_seen: dict) -> str:
    """Append ` KST / 06:03 PDT`-style annotation for senders whose profile tz
    puts them at a different wall-clock time than the document tz. Profile tz
    only (users.info) — offset-equal zones (Seoul vs Tokyo) are skipped since
    their local time is identical. Every abbreviation actually rendered is
    collected into tz_seen (abbr → IANA) for the frontmatter, because "CDT"
    alone is ambiguous (Chicago? China reads it as CST?)."""
    utz = b.get("utz")
    if not utz:
        return stamp
    try:
        zone = ZoneInfo(utz)
    except (ZoneInfoNotFoundError, ValueError):
        return stamp  # unparseable profile tz — show nothing rather than guess
    local = b["dt"].astimezone(zone)
    if local.utcoffset() == b["dt"].utcoffset():
        return stamp
    prev = last_anno.get(b["name"])
    if prev and (b["dt"] - prev).total_seconds() < TZ_ANNOTATE_GAP_S:
        return stamp
    last_anno[b["name"]] = b["dt"]
    doc_abbr = b["dt"].strftime("%Z")
    loc_abbr = local.strftime("%Z")
    tz_seen.setdefault(doc_abbr, doc_tz)
    tz_seen.setdefault(loc_abbr, utz)
    return f"{stamp} {doc_abbr} / {local.strftime('%H:%M')} {loc_abbr}"


def merge_blocks(msgs: list[dict]) -> list[dict]:
    """Fold consecutive same-sender messages (same reply role + context,
    ≤MERGE_GAP_S apart) into one block; extra messages become extra lines."""
    blocks: list[dict] = []
    for m in msgs:
        b = blocks[-1] if blocks else None
        if (b and b["name"] == m["name"] and b["reply"] == m["reply"]
                and b["ctx"] == m.get("ctx")
                and (m["dt"] - b["end"]).total_seconds() <= MERGE_GAP_S):
            b["lines"] += m["body"].split("\n")
            b["end"] = m["dt"]
        else:
            blocks.append({"name": m["name"], "dt": m["dt"], "end": m["dt"],
                           "reply": m["reply"], "ctx": m.get("ctx"),
                           "utz": m.get("utz"), "lines": m["body"].split("\n")})
    return blocks


def render(msgs: list[dict], meta: dict[str, str], tz: str) -> str:
    # Body first: it discovers which tz abbreviations actually appear, and the
    # frontmatter then defines them (CDT alone could be misread as China time).
    body: list[str] = []
    cur_day = None
    last_anno: dict[str, datetime] = {}  # per-sender last tz annotation time
    tz_seen: dict[str, str] = {}         # rendered abbr → IANA zone
    for b in merge_blocks(msgs):
        day = b["dt"].date().isoformat()
        # Replies stay under their parent's day section (threads are grouped, not
        # re-sorted), so only top-level blocks open a new ## day header.
        if not b["reply"] and day != cur_day:
            body += ["", f"## {day}"]
            cur_day = day
        # Cross-day replies keep their parent's section but show the date inline.
        stamp = b["dt"].strftime("%H:%M") if day == cur_day else b["dt"].strftime("%m-%d %H:%M")
        stamp = tz_stamp(b, stamp, last_anno, tz, tz_seen)
        if b["reply"]:
            head, cont = "  ↳ ", "    "
        else:
            head, cont = "", ""
        body.append("")  # one blank line before every message block, replies included
        body.append(f"{head}{b['name']} [{stamp}] {b['lines'][0]}")
        body += [(cont + line).rstrip() for line in b["lines"][1:]]

    participants = sorted({m["name"] for m in msgs})
    out = ["---"]
    for k, v in meta.items():
        safe = str(v).replace('"', '\\"')  # values may contain ":" — quote to keep YAML valid
        out.append(f'{k}: "{safe}"')
    out += [f"captured: {datetime.now(ZoneInfo(tz)).date()}", f"tz: {tz}"]
    if tz_seen:
        out.append("timezones:")  # define every abbreviation used in the body
        out += [f'  {abbr}: "{iana}"' for abbr, iana in tz_seen.items()]
    if FILES_DIR:
        # Attachment basedir; body links are FILES_DIR-prefixed relative paths,
        # so the md + this dir move together as a portable bundle.
        out.append(f'files_dir: "{FILES_DIR}"')
    out.append("participants:")
    out += [f'  - "{p}"' for p in participants]
    out.append("---")  # no H1 — the channel metadata already says what this is
    return "\n".join(out + body)


# ---- self-check (no network) -------------------------------------------------

def selftest() -> int:
    global _usergroups_loaded, FILES_DIR
    _user_cache.update({"U1": "Alice", "U2": "Bob"})
    _usergroup_cache["S1"] = "eng"
    _usergroups_loaded = True  # keep selftest offline
    assert parse_permalink(
        "https://x.slack.com/archives/C0AB/p1700000000123456"
    ) == ("C0AB", "1700000000.123456")
    assert parse_permalink(
        "https://x.slack.com/archives/C0AB/p1700000009000000?thread_ts=1700000000.123456&cid=C0AB"
    ) == ("C0AB", "1700000000.123456")
    assert unwrap("hi <@U1> in <#C9|general> see <http://x|here> &amp; done", "t") \
        == "hi <@Alice> in #general see here & done"
    assert unwrap("<!here> <!subteam^S1|@eng>", "t") == "<@here> <@eng>"
    assert unwrap("<!subteam^S1>", "t") == "<@eng>"  # label-less subteam resolves via cache
    assert unwrap("<https://youtu.be/abc?si=x|youtu.be/…?si=…>", "t") == "https://youtu.be/abc?si=x"
    # reactions: standard slug → unicode, skin-tone folds to base, custom keeps slug
    assert emoji_char("+1") == "👍" and emoji_char("+1::skin-tone-2") == "👍"
    assert emoji_char("acme") == ":acme:"
    assert extras({"files": [{"name": "a.png"}],
                   "reactions": [{"name": "tada", "count": 3}, {"name": "acme", "count": 1}]}, "t") \
        == "[file: a.png] 🎉×3 :acme:×1"
    # --files rendering: image embeds, doc links, external fallback (cache-seeded, offline)
    FILES_DIR = "files"
    _downloaded.update({"F9": "files/F9-a.png", "F8": "files/F8-r.pdf", "F7": None})
    assert file_ref("t", {"id": "F9", "name": "a.png", "mimetype": "image/png"}) == "![a.png](files/F9-a.png)"
    assert file_ref("t", {"id": "F8", "name": "r.pdf", "mimetype": "application/pdf"}) == "[r.pdf](files/F8-r.pdf)"
    assert file_ref("t", {"id": "F7", "name": "ext.doc"}) == "[file: ext.doc (not downloaded)]"
    fm = render([{"dt": datetime.fromtimestamp(0, ZoneInfo("UTC")), "name": "A",
                  "body": "x", "reply": False}], {"channel": "#t", "channel_type": "channel"}, "UTC")
    assert 'files_dir: "files"' in fm
    FILES_DIR = None
    assert file_ref("t", {"id": "F6", "name": "b.png"}) == "[file: b.png]"
    # zoneinfo drives tz conversion; assert the known KST/UTC offset holds.
    u = datetime.fromtimestamp(1700000000, ZoneInfo("UTC"))
    k = datetime.fromtimestamp(1700000000, ZoneInfo("Asia/Seoul"))
    assert (k.hour - u.hour) % 24 == 9
    hhmm = k.strftime("%H:%M")
    md = render(
        [{"dt": k, "name": "Alice", "body": "hello\nworld", "reply": False},
         {"dt": k, "name": "Bob", "body": "hi", "reply": True},
         # same sender within 3 min → folds into Bob's block as an extra line
         {"dt": k + timedelta(seconds=60), "name": "Bob", "body": "again", "reply": True}],
        {"channel": "#test", "channel_type": "channel"}, "Asia/Seoul",
    )
    assert "tz: Asia/Seoul" in md
    assert 'channel: "#test"' in md and 'channel_type: "channel"' in md
    assert "files_dir" not in md  # no --files → no basedir key
    assert "\n# " not in md       # no H1 — metadata carries the source
    assert f"Alice [{hhmm}] hello\nworld" in md      # first line inline, continuation flush
    assert f"  ↳ Bob [{hhmm}] hi\n    again" in md   # merged block, 4-space continuation
    assert "world\n\n  ↳ Bob" in md                  # one blank line between every block
    assert md.count("↳ Bob") == 1                    # the merge actually happened
    assert "**" not in md and "\n> " not in md       # old bold/quote format is gone
    k2 = datetime.fromtimestamp(1700000000 + 86400, ZoneInfo("Asia/Seoul"))
    md2 = render([{"dt": k, "name": "A", "body": "x", "reply": False},
                  {"dt": k2, "name": "B", "body": "y", "reply": True}],
                 {"channel": "#t"}, "Asia/Seoul")
    # cross-day reply: stays in the parent's section, shows its date inline
    assert md2.count("## ") == 1 and f"[{k2.strftime('%m-%d %H:%M')}]" in md2
    # search-mode guard: same sender+time but different channel ctx must NOT merge
    md3 = render([{"dt": k, "name": "A", "body": "x", "reply": False, "ctx": "C1"},
                  {"dt": k, "name": "A", "body": "y", "reply": False, "ctx": "C2"}],
                 {"search": "q"}, "Asia/Seoul")
    assert md3.count(f"A [{hhmm}]") == 2
    # tz annotation: profile-tz sender gets doc/local dual stamp, ≤1/hour, only
    # when the wall clock actually differs (Tokyo == Seoul offset → nothing).
    la = k.astimezone(ZoneInfo("America/Los_Angeles")).strftime("%H:%M %Z")
    mdz = render(
        [{"dt": k, "name": "Casey", "body": "hi", "reply": False, "utz": "America/Los_Angeles"},
         {"dt": k + timedelta(seconds=1800), "name": "Casey", "body": "again", "reply": False,
          "utz": "America/Los_Angeles"},
         {"dt": k + timedelta(seconds=4000), "name": "Casey", "body": "later", "reply": False,
          "utz": "America/Los_Angeles"},
         {"dt": k + timedelta(seconds=4100), "name": "Tokyo", "body": "same", "reply": False,
          "utz": "Asia/Tokyo"}],
        {"channel": "#t"}, "Asia/Seoul",
    )
    assert f"Casey [{k.strftime('%H:%M %Z')} / {la}] hi" in mdz          # first: annotated
    assert f"Casey [{(k + timedelta(seconds=1800)).strftime('%H:%M')}] again" in mdz  # <1h: bare
    assert mdz.count("/") - mdz.count("//") >= 2 and mdz.count(la.split()[-1]) == 3  # 2 annotations + 1 fm key
    assert "Tokyo [" in mdz and "Tokyo [" + (k + timedelta(seconds=4100)).strftime("%H:%M") + "] same" in mdz
    # frontmatter defines every rendered abbreviation (CDT-style ambiguity guard)
    assert "timezones:" in mdz
    assert f'  {k.strftime("%Z")}: "Asia/Seoul"' in mdz
    assert f'  {la.split()[-1]}: "America/Los_Angeles"' in mdz
    assert "timezones:" not in md  # no annotations → no key
    print("selftest ok")
    return 0


# ---- cli ---------------------------------------------------------------------

def day_to_ts(day: str, tz: str, end: bool) -> str:
    try:
        d = datetime.strptime(day, "%Y-%m-%d")
    except ValueError:
        die(f"date must be YYYY-MM-DD: {day}")
    if end:
        d = d.replace(hour=23, minute=59, second=59)
    return str(d.replace(tzinfo=ZoneInfo(tz)).timestamp())


def main() -> int:
    p = argparse.ArgumentParser(
        description="Scrape Slack (read-only) into a markdown doc (stdout)."
    )
    src = p.add_mutually_exclusive_group()  # required check deferred so --selftest works alone
    src.add_argument("--channel", help="channel name or ID")
    src.add_argument("--thread", help="a message permalink")
    src.add_argument("--search", help="search.messages query")
    p.add_argument("--tz", default="Asia/Seoul", help="IANA tz for timestamps (default Asia/Seoul)")
    p.add_argument("--limit", type=int, default=200, help="max messages (default 200)")
    p.add_argument("--since", help="channel mode: only messages on/after YYYY-MM-DD")
    p.add_argument("--until", help="channel mode: only messages on/before YYYY-MM-DD")
    p.add_argument("--title", help="extra frontmatter title key (optional)")
    p.add_argument("--exclude", action="append", default=[], metavar="NAME",
                   help="drop messages whose sender name contains NAME (repeatable); "
                        "translation bots go here")
    p.add_argument("--no-threads", action="store_true", help="channel mode: skip thread replies")
    p.add_argument("--files", nargs="?", const="files", metavar="DIR",
                   help="download attachments into DIR — relative to where the md "
                        "will live (default 'files' when the flag is given) — and "
                        "link/embed them; recorded as files_dir in frontmatter. "
                        "Without the flag: filename markers only, nothing written")
    p.add_argument("--selftest", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args()

    if args.selftest:
        return selftest()

    if not (args.channel or args.thread or args.search):
        p.error("one of the arguments --channel --thread --search is required")

    try:
        ZoneInfo(args.tz)
    except (ZoneInfoNotFoundError, ValueError):
        die(f"unknown --tz: {args.tz}")

    token = os.environ.get(TOKEN_ENV)
    if not token:
        die(f"${TOKEN_ENV} not set (put your xoxp-* user token in ~/.zshenv)")
    if not token.startswith("xoxp-"):
        die(f"${TOKEN_ENV} must be a user token (xoxp-*); got '{token[:5]}...'. "
            "A bot token cannot search or read DMs.")

    if args.files:
        global FILES_DIR
        os.makedirs(args.files, exist_ok=True)
        FILES_DIR = args.files

    oldest = day_to_ts(args.since, args.tz, False) if args.since else None
    latest = day_to_ts(args.until, args.tz, True) if args.until else None

    if args.channel:
        cobj = resolve_channel(token, args.channel)
        msgs = fetch_channel(token, cobj["id"], args.tz, args.limit, oldest, latest,
                             not args.no_threads)
        label, ctype = conv_label(token, cobj)
        meta = {"channel": label, "channel_type": ctype}
    elif args.thread:
        cid, ts = parse_permalink(args.thread)
        label, ctype = conv_label(token, conv_info(token, cid))
        msgs = fetch_thread(token, cid, ts, args.tz)
        meta = {"channel": label, "channel_type": ctype}
    else:
        msgs = fetch_search(token, args.search, args.tz, args.limit)
        meta = {"search": args.search}  # spans conversations — no single channel

    if args.title:
        meta = {"title": args.title, **meta}

    if args.exclude:
        msgs = [m for m in msgs if not any(x in m["name"] for x in args.exclude)]

    if not msgs:
        die("no messages returned (check the source, date range, --exclude, "
            "or that the user has access)")

    print(render(msgs, meta, args.tz))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
