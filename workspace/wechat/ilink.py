"""
Minimal iLink (WeChat ClawBot) client — stdlib only, outbound HTTPS only.

Mirrors the official Tencent plugin @tencent-weixin/openclaw-weixin v2.4.9
(src/api/api.ts, src/auth/login-qr.ts, src/api/types.ts, src/messaging/send.ts).
See RESEARCH.md for sources.

Credentials (after a successful QR bind) are read from, in order:
  1. explicit kwargs (token=..., base_url=...)
  2. configure(token, base_url)
  3. JSON file $ILINK_CREDS or ~/.wechat/ilink_creds.json
     {"bot_token": "...", "base_url": "https://ilinkai.weixin.qq.com",
      "ilink_bot_id": "...@im.bot", "ilink_user_id": "...@im.wechat"}

Nothing here runs on import.
"""
from __future__ import annotations

import base64
import json
import os
import re
import secrets
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

DEFAULT_BASE_URL = "https://ilinkai.weixin.qq.com"   # accounts.ts DEFAULT_BASE_URL; QR always uses this host
CDN_BASE_URL = "https://novac2c.cdn.weixin.qq.com/c2c"  # media only, unused here
BOT_TYPE = "3"                                        # login-qr.ts DEFAULT_ILINK_BOT_TYPE
CHANNEL_VERSION = "2.4.9"                             # plugin version we mirror
ILINK_APP_ID = "bot"                                  # package.json "ilink_appid"
BOT_AGENT = "GrokBot/1.0"                             # base_info.bot_agent (observability only)

LONG_POLL_TIMEOUT_S = 35.0     # getupdates / get_qrcode_status default (server may suggest another)
API_TIMEOUT_S = 15.0           # sendmessage
CONFIG_TIMEOUT_S = 10.0        # getconfig / sendtyping
QR_TTL_S = 5 * 60              # plugin's local TTL for an issued QR (ACTIVE_LOGIN_TTL_MS)

STALE_TOKEN_ERRCODE = -14      # session-guard.ts: bot token invalid -> re-scan QR

# Message enums (types.ts)
MSG_TYPE_USER, MSG_TYPE_BOT = 1, 2
MSG_STATE_NEW, MSG_STATE_GENERATING, MSG_STATE_FINISH = 0, 1, 2
ITEM_TEXT, ITEM_IMAGE, ITEM_VOICE, ITEM_FILE, ITEM_VIDEO = 1, 2, 3, 4, 5
TYPING_ON, TYPING_CANCEL = 1, 2

_cfg: dict[str, Optional[str]] = {"token": None, "base_url": None}


class IlinkError(Exception):
    def __init__(self, msg: str, ret: Any = None, errcode: Any = None, resp: Any = None):
        super().__init__(msg)
        self.ret, self.errcode, self.resp = ret, errcode, resp

    @property
    def stale_token(self) -> bool:
        return STALE_TOKEN_ERRCODE in (self.ret, self.errcode)


# --------------------------------------------------------------------------- config

def _creds_path() -> str:
    return os.environ.get("ILINK_CREDS") or os.path.expanduser("~/.wechat/ilink_creds.json")


def load_creds() -> dict:
    try:
        with open(_creds_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_creds(creds: dict) -> str:
    p = _creds_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(creds, f, ensure_ascii=False)
    return p


def configure(token: Optional[str] = None, base_url: Optional[str] = None) -> None:
    if token is not None:
        _cfg["token"] = token
    if base_url is not None:
        _cfg["base_url"] = base_url


def _resolve(token: Optional[str], base_url: Optional[str]) -> tuple[Optional[str], str]:
    c = load_creds() if (token is None or base_url is None) else {}
    tok = token or _cfg["token"] or c.get("bot_token")
    base = base_url or _cfg["base_url"] or c.get("base_url") or DEFAULT_BASE_URL
    return tok, base


# --------------------------------------------------------------------------- HTTP

def _client_version() -> str:
    ma, mi, pa = (int(x) for x in CHANNEL_VERSION.split("."))
    return str(((ma & 0xFF) << 16) | ((mi & 0xFF) << 8) | (pa & 0xFF))


def _common_headers() -> dict[str, str]:
    return {"iLink-App-Id": ILINK_APP_ID, "iLink-App-ClientVersion": _client_version()}


def _random_wechat_uin() -> str:
    """X-WECHAT-UIN: random uint32 -> decimal string -> base64 (new value per request)."""
    n = int.from_bytes(secrets.token_bytes(4), "big")
    return base64.b64encode(str(n).encode()).decode()


def _post_headers(token: Optional[str]) -> dict[str, str]:
    h = {
        "Content-Type": "application/json",
        "AuthorizationType": "ilink_bot_token",
        "X-WECHAT-UIN": _random_wechat_uin(),
        **_common_headers(),
    }
    if token and token.strip():
        h["Authorization"] = f"Bearer {token.strip()}"
    return h


def base_info() -> dict:
    return {"channel_version": CHANNEL_VERSION, "bot_agent": BOT_AGENT}


_ID_FIELDS = re.compile(r'("(?:message_id|msg_id|svr_id)"\s*:\s*)(-?\d+)')


def _parse(raw: str) -> dict:
    # uint64 ids -> strings (plugin does the same; Python ints are lossless anyway,
    # but strings keep ids stable when re-serialised/forwarded to JS).
    return json.loads(_ID_FIELDS.sub(r'\1"\2"', raw)) if raw.strip() else {}


def _url(base: str, endpoint: str) -> str:
    return urllib.parse.urljoin(base if base.endswith("/") else base + "/", endpoint)


def _post(base: str, endpoint: str, body: dict, token: Optional[str], timeout: float) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(_url(base, endpoint), data=data, method="POST",
                                 headers=_post_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return _parse(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise IlinkError(f"{endpoint} HTTP {e.code}: {e.read()[:300]!r}") from e


def _get(base: str, endpoint: str, timeout: float) -> dict:
    req = urllib.request.Request(_url(base, endpoint), method="GET", headers=_common_headers())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return _parse(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise IlinkError(f"{endpoint} HTTP {e.code}: {e.read()[:300]!r}") from e


def _is_timeout(e: BaseException) -> bool:
    return isinstance(e, (socket.timeout, TimeoutError)) or (
        isinstance(e, urllib.error.URLError) and isinstance(e.reason, (socket.timeout, TimeoutError)))


def _check(resp: dict, what: str) -> dict:
    ret, errcode = resp.get("ret"), resp.get("errcode")
    if (ret not in (None, 0)) or (errcode not in (None, 0)):
        raise IlinkError(f"{what} ret={ret} errcode={errcode} errmsg={resp.get('errmsg')}",
                         ret=ret, errcode=errcode, resp=resp)
    return resp


# --------------------------------------------------------------------------- login

def get_qr(local_token_list: Optional[list[str]] = None) -> dict:
    """
    POST {DEFAULT_BASE_URL}/ilink/bot/get_bot_qrcode?bot_type=3  body {"local_token_list": [...]}
    No auth. Returns {"qrcode": <32-char id for polling>,
                      "qrcode_img_content": "https://liteapp.weixin.qq.com/q/...?qrcode=...&bot_type=3",
                      "ret": 0}
    Render qrcode_img_content as a QR image; the same URL is the fallback link that
    opens directly in WeChat. local_token_list = up to 10 existing bot_tokens so the
    server can answer `binded_redirect` instead of creating a duplicate bot.
    """
    return _post(DEFAULT_BASE_URL, f"ilink/bot/get_bot_qrcode?bot_type={BOT_TYPE}",
                 {"local_token_list": local_token_list or []}, token=None, timeout=API_TIMEOUT_S)


def poll_qr(qrcode: str, base_url: str = DEFAULT_BASE_URL, verify_code: Optional[str] = None,
            timeout: float = LONG_POLL_TIMEOUT_S) -> dict:
    """
    ONE long-poll of GET {base}/ilink/bot/get_qrcode_status?qrcode=...[&verify_code=...]
    (no auth, only iLink-App-* headers). Client timeout -> {"status": "wait"}.

    status: wait | scaned | need_verifycode | verify_code_blocked | scaned_but_redirect
            (use redirect_host: base_url = "https://" + redirect_host) | binded_redirect
            (already bound, keep old creds) | expired (call get_qr again) | confirmed
    confirmed carries: bot_token, ilink_bot_id ("...@im.bot"), baseurl, ilink_user_id
    (the scanner's id, "...@im.wechat" -> use as the only allowed sender).
    Caller loops: sleep ~1s between polls, give up after QR_TTL_S / 3 refreshes.
    """
    ep = f"ilink/bot/get_qrcode_status?qrcode={urllib.parse.quote(qrcode)}"
    if verify_code:
        ep += f"&verify_code={urllib.parse.quote(verify_code)}"
    try:
        return _get(base_url, ep, timeout)
    except Exception as e:  # plugin treats timeouts and gateway errors as "wait"
        if _is_timeout(e) or isinstance(e, (IlinkError, urllib.error.URLError)):
            return {"status": "wait"}
        raise


def creds_from_confirmed(status_resp: dict) -> dict:
    return {
        "bot_token": status_resp.get("bot_token"),
        "ilink_bot_id": status_resp.get("ilink_bot_id"),
        "base_url": status_resp.get("baseurl") or DEFAULT_BASE_URL,
        "ilink_user_id": status_resp.get("ilink_user_id"),
        "bound_at": int(time.time()),
    }


# --------------------------------------------------------------------------- messaging

def get_updates(cursor: str = "", *, token: Optional[str] = None, base_url: Optional[str] = None,
                timeout: float = LONG_POLL_TIMEOUT_S) -> dict:
    """
    POST {base}/ilink/bot/getupdates  body {"get_updates_buf": cursor, "base_info": {...}}
    Server holds up to ~35s. Returns {"ret":0, "msgs":[WeixinMessage...], "get_updates_buf": new,
    "longpolling_timeout_ms": n?}. Persist the new get_updates_buf (only when non-empty) and
    send it next time; "" on first run. A client-side timeout returns an empty batch with the
    same cursor. Raises IlinkError on ret/errcode != 0 (check .stale_token for -14).
    """
    tok, base = _resolve(token, base_url)
    try:
        resp = _post(base, "ilink/bot/getupdates",
                     {"get_updates_buf": cursor or "", "base_info": base_info()},
                     tok, timeout + 5)
    except Exception as e:
        if _is_timeout(e):
            return {"ret": 0, "msgs": [], "get_updates_buf": cursor}
        raise
    return _check(resp, "getupdates")


def send_text(to: str, context_token: Optional[str], text: str, *, token: Optional[str] = None,
              base_url: Optional[str] = None, client_id: Optional[str] = None) -> dict:
    """
    POST {base}/ilink/bot/sendmessage
    {"msg": {"from_user_id": "", "to_user_id": to, "client_id": unique,
             "message_type": 2, "message_state": 2, "context_token": ctx,
             "item_list": [{"type": 1, "text_item": {"text": text}}]},
     "base_info": {...}}
    Returns {"message_id"?: str, "ret"?: 0}. Raises IlinkError if ret != 0
    (community-observed: ret=-2 when context_token expired / ~10-reply quota used up).
    Send plain text only; WeChat does not render Markdown.
    """
    tok, base = _resolve(token, base_url)
    msg: dict[str, Any] = {
        "from_user_id": "",
        "to_user_id": to,
        "client_id": client_id or f"grokbot-weixin:{int(time.time()*1000)}-{secrets.token_hex(4)}",
        "message_type": MSG_TYPE_BOT,
        "message_state": MSG_STATE_FINISH,
        "item_list": [{"type": ITEM_TEXT, "text_item": {"text": text}}],
    }
    if context_token:
        msg["context_token"] = context_token
    resp = _post(base, "ilink/bot/sendmessage", {"msg": msg, "base_info": base_info()}, tok, API_TIMEOUT_S)
    return _check(resp, "sendmessage")


def get_config(ilink_user_id: str, context_token: Optional[str] = None, *,
               token: Optional[str] = None, base_url: Optional[str] = None) -> dict:
    """Optional. POST ilink/bot/getconfig -> {"ret":0, "typing_ticket": "<base64>"} (for send_typing)."""
    tok, base = _resolve(token, base_url)
    body = {"ilink_user_id": ilink_user_id, "base_info": base_info()}
    if context_token:
        body["context_token"] = context_token
    return _post(base, "ilink/bot/getconfig", body, tok, CONFIG_TIMEOUT_S)


def send_typing(ilink_user_id: str, typing_ticket: str, status: int = TYPING_ON, *,
                token: Optional[str] = None, base_url: Optional[str] = None) -> dict:
    """Optional. POST ilink/bot/sendtyping {ilink_user_id, typing_ticket, status: 1 typing | 2 cancel}."""
    tok, base = _resolve(token, base_url)
    return _post(base, "ilink/bot/sendtyping",
                 {"ilink_user_id": ilink_user_id, "typing_ticket": typing_ticket,
                  "status": status, "base_info": base_info()}, tok, CONFIG_TIMEOUT_S)


# --------------------------------------------------------------------------- helpers

def message_text(msg: dict) -> str:
    """First text item; voice -> its speech-to-text; media -> placeholder (like inbound.ts)."""
    for it in msg.get("item_list") or []:
        t = it.get("type")
        if t == ITEM_TEXT and (it.get("text_item") or {}).get("text") is not None:
            return str(it["text_item"]["text"])
        if t == ITEM_VOICE and (it.get("voice_item") or {}).get("text"):
            return it["voice_item"]["text"]
        if t in (ITEM_IMAGE, ITEM_FILE, ITEM_VIDEO, ITEM_VOICE):
            return {ITEM_IMAGE: "[图片]", ITEM_VOICE: "[语音]", ITEM_FILE: "[文件]", ITEM_VIDEO: "[视频]"}[t]
    return ""


def split_text(text: str, limit: int = 4000) -> list[str]:
    """Plugin default textChunkLimit is 4000 chars per message (channel.ts)."""
    return [text[i:i + limit] for i in range(0, len(text), limit)] or [""]


__all__ = ["get_qr", "poll_qr", "creds_from_confirmed", "get_updates", "send_text",
           "get_config", "send_typing", "message_text", "split_text", "configure",
           "load_creds", "save_creds", "IlinkError", "STALE_TOKEN_ERRCODE", "QR_TTL_S"]
