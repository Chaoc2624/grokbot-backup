#!/usr/bin/env python3
"""新闻轨：用 Horizon 的免密钥、非 X 源补充新词雷达信号。

产出 news-YYYYMMDD.json（结构与 tracks 同形，tracks.news.items/keywords），
来源标「新闻轨」。在 track_scan.py 之后、merge_board.py 之前跑。

只启用：Google News RSS 检索、GDELT 2.0 DOC API、公开 Telegram 频道
（t.me/s/<channel> 网页）、少量通用 RSS/Atom（含 GitHub Trending RSS）。
不启用 Horizon 的 twitter、openbb、email/wechat/webhook/pages、Apify、
Playwright、Firecrawl，也不跑它的 LLM 打分 / enrichment / 简报 / 推送。
不需要新密钥或付费服务。

Portions adapted from Horizon (https://github.com/Thysrael/Horizon), MIT License.
Copyright (c) 2026 Thysrael
Adapted ideas from src/scrapers/google_news.py, gdelt.py, telegram.py, rss.py:
  Google News when:/after: time operator and RSS entry mapping;
  GDELT DOC API query construction (sourcelang/sourcecountry, timespan);
  Telegram public-channel HTML parse (tgme_widget_message, fallback hosts);
  RSS/Atom date and content extraction, 429 backoff.
This file is a standalone stdlib adapter and is not a vendor of the Horizon package.
"""
from __future__ import annotations

import argparse
import sys
import calendar
import gzip
import html as htmlmod
import json
import re
import subprocess
import time
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, quote, unquote

HERE = Path(__file__).resolve().parent
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass
STATE = HERE / "track_state"
CONFIG_PATH = HERE / "news_sources.json"
FREE_LLM = Path("/home/box/.local/bin/free-llm")
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "xinci-news-scan/1.0"
)
TG_UA = "Mozilla/5.0 (compatible; xinci-news-scan/1.0; +https://github.com/Thysrael/Horizon)"
TZ8 = timezone(timedelta(hours=8))
TIMEOUT = 35
TELEGRAM_WEB_BASES = (
    "https://t.me/s",
    "https://telegram.me/s",
    "https://telegram.dog/s",
)
GN_BASE = "https://news.google.com/rss/search"
GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

NSFW_RE = re.compile(
    r"\b(porn|nsfw|xxx|onlyfans|hentai|nude|sex|casino|gambling|betting|slots|poker)\b",
    re.I,
)
NOISE_RE = re.compile(
    r"\b(IPO|lawsuit|affair|layoffs?|earnings|stock price|game week|game-day)\b"
    r"|(路演|估值目标|遭.{0,6}攻击|数据外泄|股权限制|裁员)",
    re.I,
)
LAUNCH_RE = re.compile(
    r"\b(launch(?:es|ed)?|releasing|released|release|introduc(?:es|ing)|announc(?:es|ed|ing)"
    r"|unveil(?:s|ed|ing)?|now available|just launched|open[- ]sourc(?:e|ed)|open[- ]weight"
    r"|available on (?:steam|roblox|ollama|huggingface|github)"
    r"|new (?:ai )?tool|new (?:language )?model|new game)\b"
    r"|(发布|推出|上线|开源|现已推出|现已上线|正式发布|新品)",
    re.I,
)
PUBLISHER_SUF = re.compile(
    r"\s+[-–—|]\s+[A-Za-z0-9][^|]{1,40}$"
)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
GENERIC_NAMES = {
    "ai", "tool", "tools", "new", "app", "agent", "model", "game", "news",
    "google", "apple", "meta", "microsoft", "amazon", "openai", "anthropic",
    "steam", "roblox", "nvidia", "tesla", "github", "hugging face", "huggingface",
    "deepmind", "google deepmind", "the verge", "techcrunch", "ollama",
}
# borrowed / aligned with track_scan.ok_name headline leftovers
BAD_HEADLINE = re.compile(
    r"\b(says|could|linked to|orders|costing you|predict|reconstruct|supercharge"
    r"|affair|threatened|wind(?:ing)? down)\b",
    re.I,
)

def now_bj() -> datetime:
    return datetime.now(TZ8)


def bj_stamp(dt: datetime | None = None) -> str:
    return (dt or now_bj()).strftime("%Y-%m-%d %H:%M")


def ensure_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    s = value.strip()
    if not s:
        return None
    try:
        moment = parsedate_to_datetime(s)
        return ensure_utc(moment)
    except Exception:
        pass
    try:
        s2 = s.replace("Z", "+00:00")
        return ensure_utc(datetime.fromisoformat(s2))
    except Exception:
        return None


def parse_gdelt_seendate(value: str) -> datetime | None:
    # Horizon gdelt.py: YYYYMMDDTHHMMSSZ
    if not value:
        return None
    try:
        dt = datetime.strptime(value.strip(), "%Y%m%dT%H%M%SZ")
        return dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return parse_dt(value)


def fetch(url: str, headers: dict[str, str] | None = None, timeout: int = TIMEOUT) -> bytes:
    import urllib.request

    hdrs = {
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, application/json, text/html;q=0.9, */*;q=0.8",
        "Accept-Encoding": "gzip",
        "Accept-Language": "en-US,en;q=0.8,zh;q=0.5",
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url.replace("&amp;", "&"), headers=hdrs)
    last: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                body = res.read()
                retry_after = res.headers.get("Retry-After")
            if body[:2] == b"\x1f\x8b":
                body = gzip.decompress(body)
            return body
        except Exception as exc:  # noqa: BLE001
            last = exc
            code = getattr(exc, "code", None)
            wait = 2 * (attempt + 1)
            if code == 429:
                wait = max(wait, 15 * (attempt + 1))
                if "Retry-After" in dir(exc) or True:
                    try:
                        ra = int(getattr(getattr(exc, "headers", None), "get", lambda *_: "")("Retry-After") or 0)
                        wait = max(wait, min(ra, 60))
                    except Exception:
                        pass
            time.sleep(wait)
    raise RuntimeError(f"fetch {url}: {last}")


def fetch_text(url: str, headers: dict[str, str] | None = None, timeout: int = TIMEOUT) -> str:
    return fetch(url, headers=headers, timeout=timeout).decode("utf-8", "replace")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def strip_html(text: str) -> str:
    s = htmlmod.unescape(text or "")
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p>", "\n", s)
    s = TAG_RE.sub("", s)
    s = WS_RE.sub(" ", s).strip()
    return s


def local_tag(tag: str) -> str:
    return tag.split("}", 1)[-1].lower() if tag else ""


def xml_text(el: ET.Element, names: set[str]) -> str:
    for child in list(el):
        if local_tag(child.tag) in names:
            t = (child.text or "").strip()
            href = (child.get("href") or "").strip()
            if t:
                return t
            if href:
                return href
    return ""


def xml_link(el: ET.Element) -> str:
    alt = ""
    any_href = ""
    for child in list(el):
        if local_tag(child.tag) != "link":
            continue
        href = (child.get("href") or (child.text or "")).strip()
        rel = (child.get("rel") or "").lower()
        typ = (child.get("type") or "").lower()
        if href and rel in ("", "alternate"):
            if "atom" in typ or "rss" in typ:
                if not alt:
                    any_href = any_href or href
                continue
            return href
        if href and not any_href:
            any_href = href
        if href and rel == "alternate":
            alt = href
    return alt or any_href or xml_text(el, {"link"})


def xml_date(el: ET.Element) -> datetime | None:
    for child in list(el):
        if local_tag(child.tag) in {"pubdate", "published", "updated", "date", "dc:date", "created"}:
            dt = parse_dt((child.text or "").strip())
            if dt:
                return dt
    return None


def feed_channel_date(root: ET.Element) -> datetime | None:
    for el in root.iter():
        if local_tag(el.tag) in {"pubdate", "lastbuilddate", "updated", "date"}:
            # skip item-level: only channel / feed / rdf
            parent_ok = True
            dt = parse_dt((el.text or "").strip())
            if dt and local_tag(el.tag) in {"lastbuilddate", "pubdate", "updated"}:
                # first one is usually the channel
                return dt
    return None


def iter_feed_entries(root: ET.Element) -> list[ET.Element]:
    out = []
    for el in root.iter():
        if local_tag(el.tag) in {"item", "entry"}:
            out.append(el)
    return out


def xml_content(el: ET.Element) -> str:
    chunks: list[str] = []
    for child in list(el):
        loc = local_tag(child.tag)
        if loc in {"summary", "description", "content", "encoded", "content:encoded"}:
            raw = "".join(child.itertext()) if list(child) else (child.text or "")
            if not raw and child.text:
                raw = child.text
            if raw:
                chunks.append(raw)
    chunks.sort(key=len, reverse=True)
    return strip_html(chunks[0]) if chunks else ""


def norm_name(s: str) -> str:
    s = re.sub(r"[（(【\[].*?[）)】\]]", "", s or "")
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"[\W_]+", "", s)


def norm_url(url: str) -> str:
    if not url:
        return ""
    try:
        u = urlsplit(url.strip())
    except Exception:
        return url.strip().rstrip("/").lower()
    host = (u.hostname or "").lower()
    path = re.sub(r"/+", "/", u.path or "")
    if path.endswith("/") and path != "/":
        path = path[:-1]
    q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    return urlunsplit((u.scheme or "https", host, path, urlencode(q), ""))


def gn_time_operator(since: datetime) -> str:
    # Horizon google_news.py: when:<hours>h if <=100h else after:YYYY-MM-DD
    since_utc = ensure_utc(since)
    hours = max(1, int(((datetime.now(timezone.utc) - since_utc).total_seconds() + 3599) // 3600))
    if hours <= 100:
        return f"when:{hours}h"
    return f"after:{since_utc.strftime('%Y-%m-%d')}"


def clean_title(title: str) -> str:
    s = strip_html(title or "")
    s = re.sub(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]", "", s)
    s = s.replace("️", "").replace("‍", "")
    s = s.replace("™", "").replace("®", "").replace("©", "")
    s = PUBLISHER_SUF.sub("", s)
    s = WS_RE.sub(" ", s).strip(" -_|")
    return s


def extract_original_url(url: str, raw_html: str) -> str:
    if url and "news.google.com" in url and raw_html:
        hrefs = re.findall(r'href="(https?://[^"]+)"', raw_html)
        for h in hrefs:
            if "news.google.com" not in h and "google.com/rss" not in h:
                return htmlmod.unescape(h)
    return url


def in_window(dt: datetime | None, since: datetime, until: datetime) -> bool:
    if dt is None:
        return False
    t = ensure_utc(dt)
    return ensure_utc(since) <= t <= ensure_utc(until) + timedelta(minutes=30)


def looks_like_repo(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name or ""))


def cut_name(s: str) -> str:
    s = s.strip(" .,;:：-–—|\"'“”‘’")
    s = re.split(r"\s+(?:for|that|with|from|to|and|is|are|will|can|could)\s+", s, maxsplit=1, flags=re.I)[0]
    s = re.split(r"[,，。；;]| - ", s, maxsplit=1)[0]
    return s.strip(" .,;:：-–—|\"'“”‘’")


def extract_name(title: str, snippet: str = "", kind_hint: str = "") -> str:
    """Rule-based product/game/model name from a headline. Empty if unsure."""
    t = clean_title(title)
    if not t:
        return ""
    if looks_like_repo(t):
        # prefer product-like last segment unless generic
        last = t.split("/")[-1].replace("-", " ").replace("_", " ")
        if last.lower() not in GENERIC_NAMES and len(last) >= 3:
            # Keep owner/repo when last is generic-ish short token? keep full for uniqueness
            if last.lower() in {"skills", "blog", "docs", "app", "web", "core", "api"}:
                return t
            return t  # keep full repo path as name; keyword later may use last
        return t

    patterns = [
        r"(?i)^now available on steam\s*[-–:]\s*(.+)$",
        r"(?i)^(?:introducing|announcing)\s+(?:our\s+)?(?:smallest,\s+most efficient model:\s+)?(.+)$",
        r"(?i)\bintroduces\s+(?:a |an |its |their |the )?(.+)$",
        r"(?i)\bunveils\s+(?:a |an |its |their |the )?(.+)$",
        r"(?i)\b(?:just )?launches\s+(?:a |an |its |their |the |standalone |new )?(.+)$",
        r"(?i)\breleases\s+(?:a |an |its |their |the |new )?(.+)$",
        r"(?i)^(.+?)\s+(?:is )?now (?:widely )?available(?:\s+on\s+[\w .]+)?\s*$",
        r"(?i)^(.+?)\s+steam release(?: date)?\b",
        r"开源\s+([A-Za-z][\w .+-]{1,50}|[\u4e00-\u9fffA-Za-z0-9][\u4e00-\u9fffA-Za-z0-9 .+-]{1,40})",
        r"(?:推出|发布|上线)\s+([A-Za-z][\w .+-]{1,50}|[\u4e00-\u9fffA-Za-z0-9][\u4e00-\u9fffA-Za-z0-9 .+-]{1,40})",
        r"^([A-Za-z][\w.+-]{0,40}(?:\s+[A-Za-z0-9][\w.+-]{0,20}){0,4})\s*(?:上线|发布|开源|推出)",
        r"^([A-Za-z0-9][\w.+-]{1,40}(?:\s+[A-Za-z0-9][\w.+-]{0,24}){0,4})\s*[:：]\s+",
    ]
    for pat in patterns:
        m = re.search(pat, t)
        if m:
            name = cut_name(m.group(1))
            # trim trailing clause leftovers like "to power cost-efficient AI agents"
            name = re.sub(r"\s+(?:to|that|which)\s+.*$", "", name, flags=re.I).strip()
            if ok_name(name):
                return name

    # "X is a ..." from telegram/github trending blurbs
    blob = f"{t}. {snippet or ''}"
    m = re.search(
        r"^([A-Z][A-Za-z0-9][\w.+-]{1,40}(?:\s+[A-Z][A-Za-z0-9][\w.+-]{0,20}){0,3})\s+(?:is|are)\s+(?:a|an|the)\b",
        blob.strip(),
    )
    if m and ok_name(m.group(1)):
        return m.group(1)

    # short title that's already a product name
    if ok_name(t) and len(t.split()) <= 5 and not BAD_HEADLINE.search(t) and not t.endswith("?"):
        if not re.search(r"\b(how|why|what|after|amid|despite)\b", t, re.I):
            return t
    return ""


def ok_name(name: str, min_len: int = 2, max_words: int = 8) -> bool:
    n = (name or "").strip()
    if len(n) < min_len or len(n) > 70:
        return False
    if len(n.split()) > max_words:
        return False
    if NSFW_RE.search(n):
        return False
    if re.fullmatch(r"[\d\W_]+", n):
        return False
    if n.lower() in GENERIC_NAMES:
        return False
    if BAD_HEADLINE.search(n):
        return False
    return True


def infer_kind(title: str, snippet: str, hint: str) -> str:
    blob = f"{title} {snippet}".lower()
    if re.search(r"\b(steam|roblox|videogame|video game|now available on steam)\b|(新游戏|上线 steam)", blob):
        return "game"
    if re.search(r"\b(language model|llm|open[- ]weight|open[- ]source model|foundation model)\b|(大模型|开源模型)", blob):
        return "model"
    if re.search(r"\b(ai tool|ai agent|copilot|assistant|mcp)\b|(ai ?工具)", blob):
        return "ai_tool"
    return hint or "news"


def keep_raw(title: str, snippet: str, official: bool, dateless_ok: bool) -> bool:
    blob = f"{title} {snippet}"
    if NSFW_RE.search(blob):
        return False
    if NOISE_RE.search(blob) and not LAUNCH_RE.search(blob):
        return False
    if official or dateless_ok:
        # official blogs / daily trending: still drop obvious non-product noise
        if NOISE_RE.search(title) and not LAUNCH_RE.search(title):
            return False
        return True
    return bool(LAUNCH_RE.search(blob))


# --------------- scrapers (Horizon-adapted) ---------------

def scrape_google_news(cfg: dict, since: datetime, until: datetime, errors: list[str], pause: float) -> tuple[list[dict], int]:
    block = cfg.get("google_news") or {}
    if not block.get("enabled", True):
        return [], 0
    items: list[dict] = []
    raw_count = 0
    default_hl = block.get("language") or "en-US"
    default_gl = block.get("country") or "US"
    default_ceid = block.get("ceid") or f"{default_gl}:{default_hl}"
    cap = int(block.get("max_results_per_query") or 20)
    for q in block.get("queries") or []:
        if q.get("enabled") is False:
            continue
        base_q = (q.get("q") or "").strip()
        if not base_q:
            continue
        hl = q.get("language") or default_hl
        gl = q.get("country") or default_gl
        ceid = q.get("ceid") or f"{gl}:{hl}"
        query = f"{base_q} {gn_time_operator(since)}"
        params = urlencode({"q": query, "hl": hl, "gl": gl, "ceid": ceid})
        url = f"{GN_BASE}?{params}"
        time.sleep(pause)
        try:
            text = fetch_text(url)
            root = ET.fromstring(text)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"google_news/{q.get('id') or 'q'}: {exc}")
            continue
        got = 0
        for entry in iter_feed_entries(root):
            title = xml_text(entry, {"title"})
            link = xml_link(entry)
            raw_desc = ""
            for child in list(entry):
                if local_tag(child.tag) in {"description", "summary"}:
                    raw_desc = "".join(child.itertext()) or (child.text or "")
            published = xml_date(entry)
            if not title or not link:
                continue
            if published and not in_window(published, since, until):
                continue
            link = extract_original_url(link, raw_desc)
            raw_count += 1
            got += 1
            items.append(
                {
                    "title": title,
                    "url": link,
                    "snippet": strip_html(raw_desc),
                    "published": published,
                    "source_label": "新闻轨·Google News",
                    "platform": "google_news",
                    "query_id": q.get("id") or "",
                    "kind_hint": q.get("kind_hint") or "",
                    "official": False,
                    "dateless_ok": False,
                }
            )
            if got >= cap:
                break
    return items, raw_count


def scrape_gdelt(cfg: dict, since: datetime, until: datetime, errors: list[str], pause: float) -> tuple[list[dict], int]:
    block = cfg.get("gdelt") or {}
    if not block.get("enabled", True):
        return [], 0
    items: list[dict] = []
    raw_count = 0
    max_records = int(block.get("max_records") or 25)
    mode = block.get("mode") or "ArtList"
    timespan = block.get("timespan") or "24h"
    for q in block.get("queries") or []:
        if q.get("enabled") is False:
            continue
        query = (q.get("q") or "").strip()
        if not query:
            continue
        params = {
            "query": query,
            "mode": mode,
            "format": "json",
            "maxrecords": max_records,
            "sort": "datedesc",
            "timespan": timespan,
        }
        url = f"{GDELT_BASE}?{urlencode(params)}"
        time.sleep(max(pause, 1.5))
        text = ""
        try:
            text = fetch_text(url, timeout=45)
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError("GDELT returned a non-object body")
            articles = payload.get("articles") or []
            if not isinstance(articles, list):
                raise ValueError("GDELT returned an invalid article list")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"gdelt/{q.get('id') or 'q'}: {exc}")
            continue
        for raw in articles:
            if not isinstance(raw, dict):
                continue
            title = (raw.get("title") or "").strip()
            link = (raw.get("url") or "").strip()
            seendate = (raw.get("seendate") or "").strip()
            published = parse_gdelt_seendate(seendate)
            if not title or not link:
                continue
            if published and not in_window(published, since, until):
                continue
            raw_count += 1
            items.append(
                {
                    "title": title,
                    "url": link,
                    "snippet": "",
                    "published": published,
                    "source_label": "新闻轨·GDELT",
                    "platform": "gdelt",
                    "query_id": q.get("id") or "",
                    "kind_hint": q.get("kind_hint") or "",
                    "official": False,
                    "dateless_ok": False,
                    "domain": raw.get("domain") or "",
                }
            )
    return items, raw_count


def scrape_telegram(cfg: dict, since: datetime, until: datetime, errors: list[str], pause: float) -> tuple[list[dict], int]:
    # Horizon telegram.py: public web preview, fallback hosts, 429 retry
    block = cfg.get("telegram") or {}
    if not block.get("enabled", True):
        return [], 0
    items: list[dict] = []
    raw_count = 0
    for ch in block.get("channels") or []:
        if ch.get("enabled") is False:
            continue
        channel = (ch.get("channel") or "").strip().lstrip("@")
        if not channel:
            continue
        limit = int(ch.get("fetch_limit") or 20)
        html = ""
        last_err: Exception | None = None
        for base in TELEGRAM_WEB_BASES:
            url = f"{base}/{channel}"
            time.sleep(pause)
            try:
                html = fetch_text(url, headers={"User-Agent": TG_UA}, timeout=60)
                if "tgme_widget_message" in html or "data-post=" in html:
                    last_err = None
                    break
                last_err = RuntimeError("no public messages on preview page")
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                continue
        if last_err and not html:
            errors.append(f"telegram/@{channel}: {last_err}")
            continue
        blocks = re.split(r'<div class="tgme_widget_message_wrap[^"]*"', html)
        got = 0
        for b in blocks[1:]:
            post = re.search(r'data-post="([^"]+)"', b)
            dt_m = re.search(r'<time[^>]*datetime="([^"]+)"', b)
            text_m = re.search(
                r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', b, re.S
            )
            if not text_m:
                continue
            raw_html = text_m.group(1)
            text = strip_html(re.sub(r"(?i)<br\s*/?>", "\n", raw_html))
            text = re.sub(r"\n+", "\n", text).strip()
            if not text:
                continue
            published = parse_dt(dt_m.group(1) if dt_m else "")
            if published and not in_window(published, since, until):
                continue
            msg_id = ""
            if post:
                msg_id = post.group(1).split("/")[-1]
            msg_url = f"https://t.me/{channel}/{msg_id}" if msg_id else f"https://t.me/s/{channel}"
            canonical = msg_url
            for href in re.findall(r'href="(https?://[^"]+)"', raw_html):
                href = htmlmod.unescape(href)
                try:
                    host = (urlsplit(href).hostname or "").lower()
                except Exception:
                    continue
                if host and host not in {"t.me", "telegram.me", "telegram.dog"}:
                    canonical = href
                    break
            title = text.split("\n\n")[0].replace("\n", " ").strip()
            if len(title) > 80:
                m = re.search(r"[。！？.!?]", title[:80])
                title = title[: m.end()] if m else title[:80]
            raw_count += 1
            got += 1
            items.append(
                {
                    "title": title,
                    "url": canonical,
                    "snippet": text[:500],
                    "published": published,
                    "source_label": f"新闻轨·Telegram@{channel}",
                    "platform": "telegram",
                    "query_id": channel,
                    "kind_hint": "",
                    "official": False,
                    "dateless_ok": False,
                    "msg_url": msg_url,
                }
            )
            if got >= limit:
                break
        if got == 0 and last_err:
            errors.append(f"telegram/@{channel}: 窗口内无帖或解析失败（{last_err}）")
    return items, raw_count


def scrape_rss(cfg: dict, since: datetime, until: datetime, errors: list[str], pause: float) -> tuple[list[dict], int]:
    block = cfg.get("rss") or {}
    if not block.get("enabled", True):
        return [], 0
    items: list[dict] = []
    raw_count = 0
    for feed in block.get("feeds") or []:
        if feed.get("enabled") is False:
            continue
        url = (feed.get("url") or "").strip()
        name = feed.get("name") or feed.get("id") or url
        if not url:
            continue
        time.sleep(pause)
        try:
            text = fetch_text(url)
            root = ET.fromstring(text)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"rss/{name}: {exc}")
            continue
        feed_dt = feed_channel_date(root)
        dateless_policy = feed.get("dateless_policy") or ""
        official = bool(feed.get("official"))
        got = 0
        for entry in iter_feed_entries(root):
            title = xml_text(entry, {"title"})
            link = xml_link(entry)
            snippet = xml_content(entry)
            published = xml_date(entry)
            if published is None and dateless_policy == "feed_date":
                published = feed_dt
            if not title or not link:
                continue
            if published is not None and not in_window(published, since, until):
                continue
            if published is None:
                # no date and not a daily snapshot — skip rather than ingest history
                continue
            raw_count += 1
            got += 1
            items.append(
                {
                    "title": title,
                    "url": link,
                    "snippet": snippet[:500],
                    "published": published,
                    "source_label": f"新闻轨·RSS·{name}",
                    "platform": "rss",
                    "query_id": feed.get("id") or name,
                    "kind_hint": feed.get("kind_hint") or "",
                    "official": official,
                    "dateless_ok": dateless_policy == "feed_date",
                }
            )
        if got == 0 and not any(e.startswith(f"rss/{name}:") for e in errors):
            # not an error — empty window is fine
            pass
    return items, raw_count


# --------------- existing names from today's tracks / xnew ---------------

def load_today_seen(day: str) -> tuple[set[str], set[str]]:
    names: set[str] = set()
    urls: set[str] = set()
    d = day.replace("-", "")

    def add_item(it: dict) -> None:
        n = norm_name(it.get("name") or "")
        if n:
            names.add(n)
        u = norm_url(it.get("url") or "")
        if u:
            urls.add(u)

    for p in sorted(HERE.glob(f"tracks-{d}-*.json")):
        run = load_json(p, {})
        tracks = run.get("tracks") or {}
        for block in tracks.values():
            if not isinstance(block, dict):
                continue
            for it in block.get("items") or []:
                add_item(it)
    for p in list(HERE.glob(f"xnew-{d}-*.json")) + [HERE / f"xnew-{d}.json"]:
        if not p.exists():
            continue
        run = load_json(p, {})
        for it in run.get("items") or []:
            add_item(it)
    return names, urls


def load_news_seen() -> tuple[set[str], set[str]]:
    data = load_json(STATE / "news_seen.json", {})
    if isinstance(data, list):
        return {str(x) for x in data}, set()
    names = {str(x) for x in (data.get("names") or [])}
    urls = {norm_url(str(x)) for x in (data.get("urls") or []) if x}
    return names, urls


def save_news_seen(names: set[str], urls: set[str]) -> None:
    # keep lists stable and bounded
    name_list = sorted(names)
    url_list = sorted(u for u in urls if u)
    if len(name_list) > 8000:
        name_list = name_list[-8000:]
    if len(url_list) > 8000:
        url_list = url_list[-8000:]
    save_json(STATE / "news_seen.json", {"names": name_list, "urls": url_list})


# --------------- LLM polish ---------------

def call_free_llm(payload: list[dict], errors: list[str]) -> dict[str, dict]:
    """Ask free-llm to extract name + one-line Chinese desc. Returns id -> {name,desc,kind,keep}."""
    if not payload:
        return {}
    if not FREE_LLM.exists():
        errors.append("free-llm: 未找到 /home/box/.local/bin/free-llm，改用规则抽名")
        return {}
    tmp_in = HERE / "_news_llm_payload.json"
    tmp_out = HERE / "_news_llm_out.json"
    tmp_status = HERE / "_news_llm_status.txt"
    tmp_in.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    system = (
        "你是新词雷达新闻轨提炼器。根据输入的新闻/博客/频道条目，输出纯 JSON 对象："
        '{"items":[{"id":0,"keep":true,"name":"产品名","desc":"一句中文用途","kind":"ai_tool"}]}'
        " kind 只能是 ai_tool、game、model、news。"
    )
    prompt = (
        "要求：\n"
        "- 只保留有明确产品 / 游戏 / 模型名的条目（keep=true）；政策、融资/IPO、裁员、事故、体育、赌场、无产品名的评论丢弃（keep=false）。\n"
        "- name 是专有产品名，不要整句标题，不要出版社名。GitHub 仓库可用 owner/repo 或更常见的产品名。\n"
        "- desc 一句中文，说明是什么、做什么；游戏须写类型和已核实平台（Steam/Roblox/itch 等），未核实不要写成已上线。\n"
        "- 查不清用途就写「用途待核实」；严禁凭名字编造功能。\n"
        "- 只输出 JSON，不要 markdown 围栏，不要解释。\n"
        f"共 {len(payload)} 条，id 与输入一致。"
    )
    try:
        proc = subprocess.run(
            [
                str(FREE_LLM),
                "-s", system,
                "-p", prompt,
                "-f", str(tmp_in),
                "--json",
                "-o", str(tmp_out),
                "-q",
            ],
            capture_output=True,
            text=True,
            timeout=240,
        )
        tmp_status.write_text((proc.stderr or "") + "\n" + (proc.stdout or ""))
        if proc.returncode != 0:
            errors.append(f"free-llm: exit {proc.returncode}: {(proc.stderr or proc.stdout or '')[-300:]}")
            return {}
        raw = tmp_out.read_text() if tmp_out.exists() else (proc.stdout or "")
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()
        data = json.loads(raw)
        rows = data.get("items") if isinstance(data, dict) else data
        out: dict[str, dict] = {}
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                out[str(row.get("id"))] = row
        elif isinstance(data, dict):
            # maybe { "0": {...}, ... }
            for k, v in data.items():
                if isinstance(v, dict) and k != "items":
                    out[str(k)] = v
        return out
    except subprocess.TimeoutExpired:
        errors.append("free-llm: 超时，改用规则抽名")
        return {}
    except Exception as exc:  # noqa: BLE001
        errors.append(f"free-llm: {exc}")
        return {}


def fallback_desc(it: dict, name: str) -> str:
    snippet = (it.get("snippet") or "").strip()
    title = clean_title(it.get("title") or "")
    if snippet and len(snippet) >= 12:
        s = snippet.split("\n")[0]
        s = WS_RE.sub(" ", s).strip()
        return s[:160]
    return title[:160] or f"{name}（用途待核实）"


def to_items(raw_items: list[dict], llm_map: dict[str, dict], errors: list[str]) -> list[dict]:
    out: list[dict] = []
    seen_n: set[str] = set()
    seen_u: set[str] = set()
    for i, raw in enumerate(raw_items):
        title = raw.get("title") or ""
        snippet = raw.get("snippet") or ""
        official = bool(raw.get("official"))
        dateless_ok = bool(raw.get("dateless_ok"))
        if not keep_raw(title, snippet, official, dateless_ok):
            continue
        row = llm_map.get(str(i)) or {}
        keep = row.get("keep")
        name = (row.get("name") or "").strip() if keep is not False else ""
        if keep is False and name:
            name = ""
        if not name:
            name = extract_name(title, snippet, raw.get("kind_hint") or "")
        name = cut_name(clean_title(name)) if name else ""
        if looks_like_repo(clean_title(title)) and not name:
            name = clean_title(title)
        if not ok_name(name):
            continue
        if keep is False and not official and not dateless_ok:
            # model said drop; honor unless official feed already had a clean name
            continue
        kind = (row.get("kind") or "").strip() or infer_kind(title, snippet, raw.get("kind_hint") or "")
        if kind not in {"ai_tool", "game", "model", "news"}:
            kind = infer_kind(title, snippet, raw.get("kind_hint") or "")
        desc = (row.get("desc") or "").strip() or fallback_desc(raw, name)
        desc = WS_RE.sub(" ", desc).strip()[:200]
        url = raw.get("url") or ""
        nk, uk = norm_name(name), norm_url(url)
        if nk in seen_n or (uk and uk in seen_u):
            continue
        seen_n.add(nk)
        if uk:
            seen_u.add(uk)
        published = raw.get("published")
        first_seen = bj_stamp(published.astimezone(TZ8) if isinstance(published, datetime) else None)
        out.append(
            {
                "name": name,
                "desc": desc,
                "url": url,
                "source": raw.get("source_label") or "新闻轨",
                "first_seen": first_seen,
                "kind": kind,
                "platform": raw.get("platform") or "",
                "title": clean_title(title),
                "is_new": True,
            }
        )
    return out


def keywords_from(items: list[dict], limit: int) -> list[dict]:
    kws: list[dict] = []
    seen: set[str] = set()
    # prefer official / telegram product posts slightly by source
    def score(it: dict) -> tuple:
        src = it.get("source") or ""
        official = "RSS·" in src and any(
            n in src for n in ("Simon Willison", "Hugging Face", "OpenAI", "DeepMind", "Google AI", "Ollama", "Steam")
        )
        return (not official, 0 if it.get("kind") in {"model", "ai_tool", "game"} else 1, it["name"].lower())

    for it in sorted(items, key=score):
        base = it["name"].strip()
        # for owner/repo, also try last segment if distinctive
        variants = [base]
        if looks_like_repo(base):
            last = base.split("/")[-1].replace("-", " ")
            if ok_name(last) and last.lower() not in GENERIC_NAMES:
                variants.append(last)
        for v in variants:
            key = v.lower()
            if key in seen or not ok_name(v, max_words=6):
                continue
            if key in GENERIC_NAMES:
                continue
            if len(v) > 48:
                continue
            seen.add(key)
            kws.append(
                {
                    "keyword": v,
                    "reason": f"{it.get('source')}: {(it.get('desc') or it.get('title') or '')[:80]}",
                    "from": it["name"],
                }
            )
            if len(kws) >= limit:
                return kws
    return kws


def main() -> int:
    ap = argparse.ArgumentParser(description="新闻轨扫描（Horizon 补充源）")
    ap.add_argument("--date", default=now_bj().strftime("%Y-%m-%d"), help="北京日期 YYYY-MM-DD")
    ap.add_argument("--config", default=str(CONFIG_PATH), help="news_sources.json 路径")
    ap.add_argument("--skip", default="", help="逗号分隔: google_news,gdelt,telegram,rss")
    ap.add_argument("--no-llm", action="store_true", help="只用规则抽名，不调用 free-llm")
    ap.add_argument("--dry-run", action="store_true", help="不写 news 文件和 seen 状态，只打印摘要")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        raise SystemExit(f"缺少配置文件: {cfg_path}")
    cfg = json.loads(cfg_path.read_text())
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    errors: list[str] = []
    source_stats: list[dict] = []

    window_hours = int(cfg.get("window_hours") or 24)
    pause = float(cfg.get("pause_sec") or 0.8)
    max_items = int(cfg.get("max_items") or 80)
    max_keywords = int(cfg.get("max_keywords") or 16)
    until = now_bj()
    since = until - timedelta(hours=window_hours)
    # compare in UTC inside scrapers
    since_utc, until_utc = since.astimezone(timezone.utc), until.astimezone(timezone.utc)

    raw: list[dict] = []
    probes = []
    if "google_news" not in skip:
        probes.append(("google_news", scrape_google_news))
    if "gdelt" not in skip:
        probes.append(("gdelt", scrape_gdelt))
    if "telegram" not in skip:
        probes.append(("telegram", scrape_telegram))
    if "rss" not in skip:
        probes.append(("rss", scrape_rss))

    for key, fn in probes:
        try:
            got, raw_count = fn(cfg, since_utc, until_utc, errors, pause)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{key}: {exc}")
            got, raw_count = [], 0
        # per-source counts
        counts: dict[str, int] = {}
        for it in got:
            counts[it.get("source_label") or key] = counts.get(it.get("source_label") or key, 0) + 1
        source_stats.append({"group": key, "raw": raw_count, "kept_window": len(got), "by_label": counts})
        print(f"  {key}: window_hits={len(got)} raw={raw_count}")
        for lab, n in counts.items():
            print(f"    {lab}: {n}")
        raw.extend(got)

    # rule prefilter before LLM to keep prompt small
    pre = []
    for it in raw:
        if keep_raw(it.get("title") or "", it.get("snippet") or "", bool(it.get("official")), bool(it.get("dateless_ok"))):
            pre.append(it)
        elif extract_name(it.get("title") or "", it.get("snippet") or ""):
            pre.append(it)
    # cap for LLM
    pre = pre[:120]

    llm_map: dict[str, dict] = {}
    if not args.no_llm and pre:
        payload = []
        for i, it in enumerate(pre):
            payload.append(
                {
                    "id": i,
                    "title": clean_title(it.get("title") or ""),
                    "snippet": (it.get("snippet") or "")[:280],
                    "url": it.get("url") or "",
                    "source": it.get("source_label") or "",
                    "kind_hint": it.get("kind_hint") or "",
                }
            )
        # reuse indices of `pre`, so to_items must use `pre` not `raw`
        llm_map = call_free_llm(payload, errors)
        print(f"  llm mapped {len(llm_map)}/{len(payload)}")

    items = to_items(pre, llm_map, errors)

    today_names, today_urls = load_today_seen(args.date)
    seen_names, seen_urls = load_news_seen()
    fresh: list[dict] = []
    new_names, new_urls = set(seen_names), set(seen_urls)
    for it in items:
        nk, uk = norm_name(it["name"]), norm_url(it.get("url") or "")
        if nk in today_names or nk in seen_names:
            continue
        if uk and (uk in today_urls or uk in seen_urls):
            continue
        fresh.append(it)
        new_names.add(nk)
        if uk:
            new_urls.add(uk)
        if len(fresh) >= max_items:
            break

    kws = keywords_from(fresh, max_keywords)
    d = args.date.replace("-", "")
    label = f"{args.date} 新闻轨"
    out = {
        "label": label,
        "run_at": bj_stamp(),
        "date": args.date,
        "window_hours": window_hours,
        "window_start": since.strftime("%Y-%m-%d %H:%M"),
        "window_end": until.strftime("%Y-%m-%d %H:%M"),
        "tracks": {"news": {"items": fresh, "keywords": kws}},
        "source_stats": source_stats,
        "errors": errors,
    }
    out_path = HERE / f"news-{d}.json"
    if not args.dry_run:
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
        save_news_seen(new_names, new_urls)

    print(
        f"news {out_path.name if not args.dry_run else '(dry)'}: "
        f"items={len(fresh)} kws={len(kws)} raw={len(raw)} pre={len(pre)} errors={len(errors)}"
    )
    if fresh:
        print("  sample:", ", ".join(i["name"] for i in fresh[:10]))
    for e in errors[:15]:
        print("  !", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
