"""Shared paths/helpers for the WeChat bridge. Never logs secrets."""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timedelta, timezone

STATE_DIR = os.path.expanduser(os.environ.get("WECHAT_STATE_DIR", "~/.wechat"))
CREDS = os.environ.get("ILINK_CREDS") or os.path.join(STATE_DIR, "ilink_creds.json")
CURSOR = os.path.join(STATE_DIR, "cursor")
CONTEXT = os.path.join(STATE_DIR, "context.json")
STATUS = os.path.join(STATE_DIR, "STATUS")
SEEN = os.path.join(STATE_DIR, "seen.json")
PENDING = os.path.join(STATE_DIR, "pending.json")
LOG = os.path.join(STATE_DIR, "forwarder.log")
PIDFILE = os.path.join(STATE_DIR, "forwarder.pid")
LOCK = os.path.join(STATE_DIR, "forwarder.lock")

CST = timezone(timedelta(hours=8))


def ensure_dir() -> None:
    os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)


def write_private(path: str, data: str) -> None:
    """Atomic write, mode 600."""
    ensure_dir()
    tmp = f"{path}.tmp.{os.getpid()}"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp, path)


def write_json(path: str, obj) -> None:
    write_private(path, json.dumps(obj, ensure_ascii=False))


def read_json(path: str, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def load_creds() -> dict:
    c = read_json(CREDS, {}) or {}
    if not isinstance(c, dict):
        return {}
    # accept both spellings of the base URL key
    if not c.get("base_url") and c.get("baseurl"):
        c["base_url"] = c["baseurl"]
    return c


def creds_ok(c: dict) -> bool:
    return bool(c.get("bot_token") and c.get("ilink_user_id"))


def token_fp(token: str | None) -> str:
    """Short non-reversible fingerprint, safe to store/log."""
    return hashlib.sha256((token or "").encode()).hexdigest()[:12]


def creds_sig() -> tuple:
    try:
        st = os.stat(CREDS)
        return (st.st_mtime_ns, st.st_size, st.st_ino)
    except FileNotFoundError:
        return ()


def set_status(s: str) -> None:
    write_private(STATUS, s + "\n")


def get_status() -> str:
    try:
        with open(STATUS, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def now_iso() -> str:
    return datetime.now(CST).isoformat(timespec="seconds")


def ms_to_iso(ms) -> str:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, CST).isoformat(timespec="seconds")
    except (TypeError, ValueError, OSError):
        return now_iso()


def save_context(msg: dict) -> None:
    write_json(CONTEXT, {
        "context_token": msg.get("context_token"),
        "from_user_id": msg.get("from_user_id"),
        "message_id": str(msg.get("message_id") or ""),
        "saved_at": int(time.time()),
        "saved_at_iso": now_iso(),
    })
