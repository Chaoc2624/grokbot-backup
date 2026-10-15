#!/usr/bin/env python3
"""
WeChat (iLink / ClawBot) -> Grok Bot routine forwarder.

Outbound only: long-polls ilink getupdates and POSTs each message from the bound
user to the routine webhook. Never opens a listening port.

Webhook URL/key come ONLY from the process env (WECHAT_ROUTINE_WEBHOOK_URL /
WECHAT_ROUTINE_WEBHOOK_KEY), read at send time, never logged or written anywhere.
State lives in ~/.wechat (see common.py).
"""
from __future__ import annotations

import fcntl
import json
import logging
import logging.handlers
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import ilink  # noqa: E402
import media  # noqa: E402

ENV_URL, ENV_KEY = "WECHAT_ROUTINE_WEBHOOK_URL", "WECHAT_ROUTINE_WEBHOOK_KEY"
NO_CREDS_RECHECK_S = 30
EXPIRED_RECHECK_S = 30
SEEN_MAX = 2000
PENDING_MAX = 500

log = logging.getLogger("wechat-forwarder")


def setup_logging() -> None:
    C.ensure_dir()
    h = logging.handlers.RotatingFileHandler(C.LOG, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"))
    log.addHandler(h)
    log.setLevel(logging.INFO)
    try:
        os.chmod(C.LOG, 0o600)
    except OSError:
        pass


# --------------------------------------------------------------------------- webhook

def webhook_post(payload: dict, timeout: float = 20.0) -> int:
    """POST payload to the routine webhook. Returns HTTP status (raises on network error).
    Reads the URL/key from os.environ at call time only."""
    url, key = os.environ.get(ENV_URL, "").strip(), os.environ.get(ENV_KEY, "").strip()
    if not url or not key:
        raise RuntimeError("webhook env vars missing")
    req = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def _err_name(e: BaseException) -> str:
    """Error description that can never contain the URL or key."""
    if isinstance(e, urllib.error.URLError):
        return f"URLError({type(e.reason).__name__})"
    if isinstance(e, RuntimeError) and "env vars missing" in str(e):
        return "env vars missing (start from a Grok Bot shell)"
    return type(e).__name__


# --------------------------------------------------------------------------- core

def msg_id(m: dict) -> str:
    mid = m.get("message_id") or m.get("msg_id") or m.get("svr_id")
    if mid not in (None, "", 0, "0"):
        return str(mid)
    return f"seq:{m.get('seq')}|{m.get('from_user_id')}|{m.get('create_time_ms')}|{m.get('client_id')}"


def _caption(m: dict) -> str | None:
    for it in m.get("item_list") or []:
        if it.get("type") == ilink.ITEM_TEXT and (it.get("text_item") or {}).get("text") is not None:
            return str(it["text_item"]["text"])
    return None


def build_payload(m: dict, images: list | None = None, image_error: str | None = None) -> dict:
    text = ilink.message_text(m)
    if images is not None:  # message has image item(s): caption if any, else "[图片]"
        text = _caption(m) or text or "[图片]"
    p = {
        "source": "wechat",
        "from_user_id": m.get("from_user_id"),
        "message_id": msg_id(m),
        "text": text,
        "time": C.ms_to_iso(m.get("create_time_ms")),
    }
    if images is not None:
        p["images"] = list(images)  # absolute paths on the box (~/.wechat/media, mode 600)
        if image_error:
            p["image_error"] = image_error
    return p


class Forwarder:
    def __init__(self, get_updates=ilink.get_updates, http_post=webhook_post, sleep=time.sleep,
                 retry_delays=(1, 2, 4, 8, 16), download_images=media.download_message_images):
        self.get_updates, self.http_post, self.sleep = get_updates, http_post, sleep
        self.download_images = download_images
        self.retry_delays = retry_delays
        seen = C.read_json(C.SEEN, []) or []
        self.seen_q: deque = deque(seen[-SEEN_MAX:], maxlen=SEEN_MAX)
        self.seen = set(self.seen_q)
        self.pending: list = C.read_json(C.PENDING, []) or []
        self.pending_next_try = 0.0
        self.pending_backoff = 30.0
        self.running = True

    # -- dedupe / persistence
    def _mark_seen(self, mid: str) -> None:
        if len(self.seen_q) == self.seen_q.maxlen:
            self.seen.discard(self.seen_q[0])
        self.seen_q.append(mid)
        self.seen.add(mid)
        C.write_json(C.SEEN, list(self.seen_q))

    def _save_pending(self) -> None:
        C.write_json(C.PENDING, self.pending[-PENDING_MAX:])

    # -- message handling (whitelist + dedupe)
    def handle_msgs(self, msgs: list, allowed_user: str) -> list:
        """Returns payloads queued for the webhook."""
        queued = []
        for m in msgs or []:
            if m.get("message_type") != ilink.MSG_TYPE_USER:
                continue  # bot echoes / our own sends
            if not allowed_user or m.get("from_user_id") != allowed_user:
                log.info("dropped message from non-bound sender")  # no content, no id
                continue
            mid = msg_id(m)
            if mid in self.seen:
                continue
            if m.get("context_token"):
                C.save_context(m)
            images = err = None
            if media.image_items(m):  # only reached for the bound sender (whitelist above)
                try:
                    images, err = self.download_images(m, mid, log)
                except Exception as e:  # noqa: BLE001
                    images, err = [], f"image download failed: {type(e).__name__}"
            p = build_payload(m, images, err)
            self.pending.append(p)
            self._save_pending()
            self._mark_seen(mid)
            queued.append(p)
            log.info("queued message %s (%d chars%s)", mid, len(p["text"]),
                     f", {len(images)} image(s){', with error' if err else ''}" if images is not None else "")
        return queued

    # -- webhook with backoff
    def post_with_retry(self, payload: dict) -> bool:
        for attempt, delay in enumerate((0,) + tuple(self.retry_delays)):
            if delay:
                self.sleep(delay)
            try:
                code = self.http_post(payload)
            except Exception as e:  # noqa: BLE001
                log.warning("webhook attempt %d failed: %s", attempt + 1, _err_name(e))
                if isinstance(e, RuntimeError):
                    return False  # env missing: retrying now is pointless
                continue
            if 200 <= code < 300:
                log.info("forwarded message %s (HTTP %d)", payload.get("message_id"), code)
                return True
            log.warning("webhook attempt %d got HTTP %d", attempt + 1, code)
        return False

    def flush_pending(self, force: bool = False) -> None:
        if not self.pending or (not force and time.time() < self.pending_next_try):
            return
        while self.pending:
            if not self.post_with_retry(self.pending[0]):
                self.pending_next_try = time.time() + self.pending_backoff
                log.warning("webhook unavailable; %d message(s) pending, retry in %ds",
                            len(self.pending), int(self.pending_backoff))
                self.pending_backoff = min(self.pending_backoff * 2, 600)
                return
            self.pending.pop(0)
            self._save_pending()
        self.pending_backoff = 30.0

    # -- main loop
    def run(self) -> None:
        cur_fp = None
        cursor = ""
        lp_timeout = ilink.LONG_POLL_TIMEOUT_S
        fails = 0
        expired_sig = None
        logged_wait = False
        while self.running:
            creds = C.load_creds()
            if not C.creds_ok(creds):
                if not logged_wait:
                    log.info("no creds at %s yet; waiting for QR bind (recheck every %ds)",
                             C.CREDS, NO_CREDS_RECHECK_S)
                    logged_wait = True
                if C.get_status() != "waiting_creds":
                    C.set_status("waiting_creds")
                self.sleep(NO_CREDS_RECHECK_S)
                continue
            logged_wait = False
            sig = C.creds_sig()
            if expired_sig is not None:
                if sig == expired_sig:
                    self.sleep(EXPIRED_RECHECK_S)
                    continue
                log.info("creds file changed; resuming")
                expired_sig = None
            fp = C.token_fp(creds["bot_token"])
            if fp != cur_fp:
                saved = C.read_json(C.CURSOR, {}) or {}
                if isinstance(saved, dict) and saved.get("bot_fp") == fp:
                    cursor = saved.get("get_updates_buf") or ""
                else:
                    cursor = ""
                    if saved:  # new bot token (re-scan): old cursor/context are invalid
                        for p in (C.CURSOR, C.CONTEXT):
                            try:
                                os.remove(p)
                            except FileNotFoundError:
                                pass
                        log.info("new bot token; cleared cursor and context")
                cur_fp = fp
                log.info("polling as bot %s (token fp %s), whitelist=1 user",
                         creds.get("ilink_bot_id"), fp)
                try:
                    _ns = ilink._post(creds.get("base_url") or creds.get("baseurl") or ilink.DEFAULT_BASE_URL,
                                      "ilink/bot/msg/notifystart", {"base_info": ilink.base_info()},
                                      token=creds.get("bot_token"), timeout=10)
                    log.info("notifystart ret=%s errcode=%s", _ns.get("ret"), _ns.get("errcode"))
                except Exception as _e:
                    log.warning("notifystart failed (ignored): %s", str(_e)[:120])
            if C.get_status() != "running":
                C.set_status("running")

            self.flush_pending()
            try:
                resp = self.get_updates(cursor, token=creds["bot_token"],
                                        base_url=creds.get("base_url") or ilink.DEFAULT_BASE_URL,
                                        timeout=lp_timeout)
            except ilink.IlinkError as e:
                if e.stale_token:
                    C.set_status("expired")
                    log.error("iLink -14: bot token expired -> re-scan the QR. Polling stopped "
                              "until %s changes.", C.CREDS)
                    expired_sig = sig
                    self.sleep(60)
                    continue
                fails += 1
                log.warning("getupdates error ret=%s errcode=%s (fail %d)", e.ret, e.errcode, fails)
                self.sleep(30 if fails >= 3 else 2)
                if fails >= 3:
                    fails = 0
                continue
            except Exception as e:  # network etc.
                fails += 1
                log.warning("getupdates failed: %s (fail %d)", type(e).__name__, fails)
                self.sleep(30 if fails >= 3 else 2)
                if fails >= 3:
                    fails = 0
                continue
            fails = 0
            nb = resp.get("get_updates_buf")
            if nb and nb != cursor:
                cursor = nb
                C.write_json(C.CURSOR, {"bot_fp": fp, "get_updates_buf": cursor})
            t = resp.get("longpolling_timeout_ms")
            if isinstance(t, (int, float)) and t > 0:
                lp_timeout = max(5.0, min(t / 1000.0, 120.0))
            if self.handle_msgs(resp.get("msgs") or [], creds.get("ilink_user_id")):
                self.flush_pending(force=True)


def main() -> int:
    setup_logging()
    lockf = open(C.LOCK, "w")
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log.info("another forwarder holds the lock; exiting")
        return 0
    f = Forwarder()

    def stop(signum, _frame):
        log.info("signal %d, stopping", signum)
        C.set_status("stopped")
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    env_ok = bool(os.environ.get(ENV_URL)) and bool(os.environ.get(ENV_KEY))
    log.info("forwarder start pid=%d webhook_env=%s", os.getpid(), "present" if env_ok else "MISSING")
    f.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
