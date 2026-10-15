#!/usr/bin/env python3
"""
Send a plain-text reply to the bound WeChat user.

  python3 reply.py "text"        or        echo "text" | python3 reply.py

Markdown is stripped (WeChat doesn't render it); long text is split at 4000 chars.
Exit codes: 0 ok | 14 token expired (-14, re-scan QR) | 2 ret -2 / stale context (user must
send a WeChat message first) | 3 no creds | 4 no context_token | 1 other error.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import ilink  # noqa: E402

LIMIT = 4000

_FENCE = re.compile(r"^\s*(```|~~~)")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_HR = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
_QUOTE = re.compile(r"^\s{0,3}>\s?")
_BULLET = re.compile(r"^(\s*)[*+]\s+")
_IMG = re.compile(r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_LINK = re.compile(r"\[([^\]]+)\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_AUTOLINK = re.compile(r"<(https?://[^>\s]+)>")
_BOLD = re.compile(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1")
_STRIKE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~")
_ITALIC = re.compile(r"(?<![\w*])\*(?=[^\s*])([^*\n]+?)(?<=[^\s*])\*(?![\w*])")
_CODE = re.compile(r"`+([^`\n]*)`+")
_BR = re.compile(r"<br\s*/?>", re.I)


def _inline(s: str) -> str:
    s = _BR.sub("\n", s)
    s = _IMG.sub(lambda m: (f"{m.group(1)} {m.group(2)}" if m.group(1) else m.group(2)), s)
    s = _LINK.sub(lambda m: m.group(2) if m.group(1).strip() == m.group(2) else f"{m.group(1)} {m.group(2)}", s)
    s = _AUTOLINK.sub(r"\1", s)
    s = _CODE.sub(r"\1", s)
    s = _BOLD.sub(r"\2", s)
    s = _STRIKE.sub(r"\1", s)
    s = _ITALIC.sub(r"\1", s)
    return s


def strip_markdown(text: str) -> str:
    out, in_code = [], False
    for line in text.replace("\r\n", "\n").split("\n"):
        if _FENCE.match(line):
            in_code = not in_code
            continue
        if in_code:
            out.append(line)
            continue
        if _TABLE_SEP.match(line) and "-" in line:
            continue
        if _HR.match(line):
            continue
        line = _HEADING.sub("", line)
        line = _QUOTE.sub("", line)
        line = _BULLET.sub(r"\1- ", line)
        if line.strip().startswith("|") or line.count("|") >= 2:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            line = "  ".join(c for c in cells if c)
        out.append(_inline(line))
    s = "\n".join(out)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def split_text(text: str, limit: int = LIMIT) -> list:
    """Split into <= limit chunks, preferring paragraph/line/space boundaries."""
    chunks, rest = [], text
    while len(rest) > limit:
        window = rest[:limit]
        cut = max(window.rfind("\n\n"), -1)
        if cut < limit // 2:
            cut = window.rfind("\n")
        if cut < limit // 2:
            cut = window.rfind(" ")
        if cut < limit // 2:
            cut = limit
        chunks.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip("\n ")
    if rest or not chunks:
        chunks.append(rest)
    return chunks


def die(code: int, msg: str):
    print(f"reply.py: {msg}", file=sys.stderr)
    sys.exit(code)


def main(argv: list) -> int:
    raw = " ".join(argv[1:]) if len(argv) > 1 else sys.stdin.read()
    text = strip_markdown(raw)
    if not text:
        die(1, "empty message")
    creds = C.load_creds()
    if not C.creds_ok(creds):
        die(3, f"no WeChat creds at {C.CREDS}: bind first (scan the ClawBot QR).")
    user = creds["ilink_user_id"]
    ctx = C.read_json(C.CONTEXT, {}) or {}
    tok = ctx.get("context_token")
    if not tok or (ctx.get("from_user_id") and ctx.get("from_user_id") != user):
        die(4, "no context_token yet: send any message to ClawBot in WeChat first.")
    parts = split_text(text)
    for i, part in enumerate(parts, 1):
        try:
            ilink.send_text(user, tok, part, token=creds["bot_token"],
                            base_url=creds.get("base_url") or ilink.DEFAULT_BASE_URL)
        except ilink.IlinkError as e:
            sent = f" ({i-1}/{len(parts)} parts sent)" if len(parts) > 1 else ""
            if e.stale_token:
                C.set_status("expired")
                die(14, f"iLink -14: bot token expired, re-scan the QR to re-bind{sent}.")
            if e.ret == -2 or e.errcode == -2:
                die(2, "iLink ret=-2: context_token stale or reply quota used up; "
                       f"send a new message to ClawBot in WeChat, then retry{sent}.")
            die(1, f"sendmessage failed: ret={e.ret} errcode={e.errcode}{sent}")
        except Exception as e:  # noqa: BLE001
            die(1, f"sendmessage failed: {type(e).__name__} ({i-1}/{len(parts)} parts sent)")
    print(f"sent {len(parts)} part(s), {len(text)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
