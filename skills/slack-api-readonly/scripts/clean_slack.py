#!/usr/bin/env python3
"""Format Slack desktop copy-paste into clean message blocks.

Reads a Slack paste (Korean or English locale) from a file or stdin, segments it
into messages by their `  [HH:MM]` timestamps, and prints one block per message
(same shape as the slack-api-readonly scraper):

    Sender [HH:MM] first body line
    continuation lines flush left

    Next Sender [HH:MM] ...

Always-on cleaners (Slack-universal noise):
- (편집됨) / (edited) edit markers
- N개의 댓글 / N replies / N comments thread-count lines
- blank-line runs inside a body squashed; empty messages dropped

Configurable (nothing workspace-specific is hard-coded):
- --exclude NAME  drop messages whose sender contains NAME (repeatable).
                  Translation bots go here, e.g. --exclude "Translator".
- --strip REGEX   remove matches from message bodies (repeatable). Bot-specific
                  noise goes here, e.g. --strip ':robot_face:.*'.

Read-only: writes nowhere except stdout.
"""

from __future__ import annotations

import argparse
import re
import sys

# Structural anchor: Slack's desktop "copy" prefixes each message time with two
# spaces + a bracket. The double-space is load-bearing — find_sender_start walks
# back from it to isolate the sender name — so match it exactly. The meridiem is
# optional and may sit before the digits (Korean: 오전 10:30) or after them
# (English: 10:30 AM); bare 24h (15:30) also parses.
# Only the Korean form is covered by selftest; AM/PM + 24h are cheap additions.
TIME_RE = re.compile(
    r"  \[(오전|오후)?\s?(\d{1,2}):(\d{2})\s?(AM|PM)?\]", re.IGNORECASE
)

# [ \t]* not \s* — newlines are now structure (continuation lines), don't eat them
EDITED_RE = re.compile(r"[ \t]*\((?:편집됨|edited)\)[ \t]*")
# KO "3개의 댓글", EN "3 replies" / "3 comments"
COMMENT_COUNT_RE = re.compile(r"\d+개의 댓글|\d+\s+repl(?:y|ies)|\d+\s+comments?")
COMMENT_PREFIX_RE = re.compile(
    r"(?:\d+개의 댓글|\d+\s+repl(?:y|ies)|\d+\s+comments?)\s*"
)


def to_24h(pre: str | None, post: str | None, hour_str: str) -> int:
    hour = int(hour_str)
    mer = (pre or post or "").upper()
    if mer in ("오후", "PM") and hour != 12:
        hour += 12
    elif mer in ("오전", "AM") and hour == 12:
        hour = 0
    return hour


def find_sender_start(text: str, time_start: int) -> int:
    """Walk back from a timestamp to the start of the sender name."""
    window = 50  # senders are short; 50 chars back is plenty and bounds the scan
    chunk_start = max(0, time_start - window)
    chunk = text[chunk_start:time_start]
    i = len(chunk) - 1
    while i >= 0:
        ch = chunk[i]
        if ch == "\n" or ch in ".,)?!:;…":
            i += 1
            break
        i -= 1
    if i < 0:
        i = 0
    abs_start = chunk_start + i
    while abs_start < time_start and text[abs_start].isspace():
        abs_start += 1
    m = COMMENT_PREFIX_RE.match(text[abs_start:time_start])
    if m:
        abs_start += m.end()
    while abs_start < time_start and text[abs_start].isspace():
        abs_start += 1
    return abs_start


def clean_body(body: str, strip_res: list[re.Pattern]) -> str:
    body = EDITED_RE.sub(" ", body)
    for rx in strip_res:
        body = rx.sub(" ", body)
    body = COMMENT_COUNT_RE.sub("", body)
    body = re.sub(r"[ \t]+", " ", body)  # collapse spaces, keep newlines for now
    body = re.sub(r" +\n", "\n", body)   # stripped markers can leave trailing spaces
    return body.strip()


def squash_blank_lines(body: str) -> str:
    return re.sub(r"\n+", "\n", body)


def parse_paste(
    text: str, excludes: list[str], strip_res: list[re.Pattern]
) -> list[dict]:
    matches = list(TIME_RE.finditer(text))
    messages = []
    for idx, m in enumerate(matches):
        sender_start = find_sender_start(text, m.start())
        sender = text[sender_start:m.start()].strip()
        body_start = m.end()
        if idx + 1 < len(matches):
            body_end = find_sender_start(text, matches[idx + 1].start())
        else:
            body_end = len(text)
        body = squash_blank_lines(clean_body(text[body_start:body_end], strip_res))
        messages.append(
            {
                "sender": sender,
                "hour_24": to_24h(m.group(1), m.group(4), m.group(2)),
                "minute": m.group(3),
                "body": body,
            }
        )
    return [
        msg
        for msg in messages
        if msg["body"] and not any(x in msg["sender"] for x in excludes)
    ]


def render(messages: list[dict]) -> str:
    blocks = []
    for m in messages:
        lines = m["body"].split("\n")
        first = f"{m['sender']} [{m['hour_24']:02d}:{m['minute']}] {lines[0]}"
        blocks.append("\n".join([first] + lines[1:]))
    return "\n\n".join(blocks)


def selftest() -> int:
    sample = (
        "Alice  [오전 10:30]\n"
        "Hello there\n"
        "Translator  [오전 10:31]\n"
        "Alice:flag-kr: → :flag-us: (#1) Hello there\n"
        "Bob  [오후 2:05]\n"
        "Reply (편집됨)\n"
        "second line\n"
        "3개의 댓글\n"
    )
    msgs = parse_paste(sample, excludes=["Translator"], strip_res=[])
    got = render(msgs)
    # block format: Sender [HH:MM] inline first line, continuations flush,
    # blank line between messages — matches slack-api-readonly output
    expected = "Alice [10:30] Hello there\n\nBob [14:05] Reply\nsecond line"
    assert got == expected, f"got:\n{got}\nexpected:\n{expected}"
    print("selftest ok")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Clean Slack copy-paste into [HH:MM] Sender: body lines (stdout)."
    )
    p.add_argument("paste", nargs="?", help="Slack paste file (default: stdin)")
    p.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="NAME",
        help="drop messages whose sender contains NAME (repeatable)",
    )
    p.add_argument(
        "--strip",
        action="append",
        default=[],
        metavar="REGEX",
        help="remove matches from message bodies (repeatable)",
    )
    p.add_argument("--selftest", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args()

    if args.selftest:
        return selftest()

    try:
        text = open(args.paste, encoding="utf-8").read() if args.paste else sys.stdin.read()
    except OSError as exc:
        sys.exit(f"error: cannot read input: {exc}")

    if not text.strip():
        sys.exit("error: input is empty")

    try:
        strip_res = [re.compile(s) for s in args.strip]
    except re.error as exc:
        sys.exit(f"error: bad --strip regex: {exc}")

    messages = parse_paste(text, args.exclude, strip_res)
    if not messages:
        sys.exit(
            "error: no messages parsed. Check the paste has `  [HH:MM]` timestamps "
            "and that --exclude did not drop everything."
        )

    print(render(messages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
