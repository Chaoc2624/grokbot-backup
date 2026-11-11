#!/usr/bin/env python3
"""热梗轨：每天监听 TikTok / YouTube / Instagram 的热梗与 AI 视频热词（独立于新闻轨）。

产出 meme-YYYYMMDD.json，结构与 tracks 同形（tracks.meme.items/keywords），
并附 coverage / permissions_needed。在 news_scan.py 之后、merge_board.py 之前跑，
避免与新闻轨互相覆盖。

只使用官方公开方法：
  - TikTok Creative Center 公开页面（HTTP GET）；完整榜需 TikTok for Business Discovery API
  - YouTube Data API v3 videos.list?chart=mostPopular（需官方 API key）
  - Instagram：无公开免申请趋势接口；Meta Content Library 需科研审核
Secondary / discovery（必须标注，不得当作平台直采）：
  - 官方 Google Trends RSS（https://trends.google.com/trending/rss）
不调用未公开内部接口，不复制 cookies，不绕过登录 / 反爬 / 网络封禁。
不把 Google News 或 X 转述写成三平台直采。
历史种子 hotel lobby / ai raindance / ai zombie / burning bridges / Bulin47
不得当作当天趋势。短时增速若无多点快照，标「待观察」，不编造速度。
视频语义仅有元数据时标「未核实」，不声称已观看。
抽名 / 解释 / 去重若需模型，只用 /home/box/.local/bin/free-llm 或 pi。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
STATE = HERE / "track_state"
CONFIG_PATH = HERE / "meme_sources.json"
FREE_LLM = Path("/home/box/.local/bin/free-llm")
TZ8 = timezone(timedelta(hours=8))
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "xinci-meme-scan/1.0"
)
TIMEOUT = 30

try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

MEMEISH_RE = re.compile(
    r"\b(ai\s*(video|meme|dance|avatar|face|photo|selfie|reels?|shorts?|tiktok)"
    r"|viral\s*(dance|audio|meme|trend|sound)|recreate|remake|duet|trend\s*alert"
    r"|photo\s*to\s*video|image\s*to\s*video|face\s*swap|motion\s*transfer)\b"
    r"|(热梗|爆款视频|用自己的照片|复刻|AI\s*视频|AI短视频|AI变装)",
    re.I,
)
EXCLUDE_NEWS_RE = re.compile(
    r"\b(nfl|nba|mlb|premier league|champions league|earnings|stock|ipo|election"
    r"|vs\.|versus|coach|stadium|gm meetings)\b"
    r"|(股價|股價|演唱會|信用卡|古裝劇)",
    re.I,
)
SEED_DEFAULT = [
    "hotel lobby",
    "ai raindance",
    "ai zombie",
    "burning bridges",
    "bulin47",
]


def now_bj() -> datetime:
    return datetime.now(TZ8)


def bj_stamp(dt: datetime | None = None) -> str:
    return (dt or now_bj()).strftime("%Y-%m-%d %H:%M")


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        moment = parsedate_to_datetime(value.strip())
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc)
    except Exception:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            return None


def fetch_ex(url: str, timeout: int = TIMEOUT) -> tuple[int, str, str, str]:
    """Return (http_status, body_text, error, final_url). No cookies, no impersonation."""
    import gzip
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/rss+xml, application/xml, application/json, text/html;q=0.9, */*;q=0.8",
            "Accept-Encoding": "gzip",
            "Accept-Language": "en-US,en;q=0.8,zh;q=0.5",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            body = res.read()
            code = res.status
            final = res.geturl() or url
        if body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return code, body.decode("utf-8", "replace"), "", final
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read() or b""
            if body[:2] == b"\x1f\x8b":
                body = gzip.decompress(body)
            text = body.decode("utf-8", "replace")
        except Exception:
            text = ""
        final = ""
        try:
            final = exc.geturl() or url
        except Exception:
            final = url
        return int(exc.code or 0), text, f"HTTPError {exc.code}: {exc.reason}", final
    except Exception as exc:  # noqa: BLE001
        return 0, "", f"{type(exc).__name__}: {exc}", url


def fetch(url: str, timeout: int = TIMEOUT) -> tuple[int, str, str]:
    """Return (http_status, body_text, error). Does not send cookies or impersonate."""
    code, text, err, _final = fetch_ex(url, timeout=timeout)
    return code, text, err


def official_oembed(video_url: str) -> dict:
    """Official YouTube or TikTok oEmbed. Returns {} on failure. No API key."""
    from urllib.parse import quote

    u = (video_url or "").strip()
    if not u:
        return {}
    if "youtube.com" in u or "youtu.be" in u:
        endpoint = "https://www.youtube.com/oembed?format=json&url=" + quote(u, safe="")
    elif "tiktok.com" in u:
        endpoint = "https://www.tiktok.com/oembed?url=" + quote(u, safe="")
    else:
        return {}
    code, text, err = fetch(endpoint)
    if code != 200 or not text:
        return {}
    try:
        data = json.loads(text)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def parse_youtube_atom(text: str) -> list[dict]:
    import xml.etree.ElementTree as ET

    out: list[dict] = []
    try:
        root = ET.fromstring(text)
    except Exception:
        return out
    for el in root.iter():
        if local_tag(el.tag) != "entry":
            continue
        title = link = published = author = ""
        views = None
        for c in list(el):
            n = local_tag(c.tag)
            if n == "title":
                title = (c.text or "").strip()
            elif n == "link" and not link:
                link = (c.get("href") or c.text or "").strip()
            elif n == "published":
                published = (c.text or "").strip()
            elif n == "name" and not author:
                author = (c.text or "").strip()
            elif n == "author":
                for x in list(c):
                    if local_tag(x.tag) == "name":
                        author = (x.text or "").strip()
            elif n == "statistics" and c.get("views") is not None:
                try:
                    views = int(c.get("views") or 0)
                except Exception:
                    views = c.get("views")
        if title and link:
            row = {
                "title": title,
                "url": link,
                "published": published,
                "author": author,
            }
            if views is not None:
                row["views"] = views
            out.append(row)
    return out


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


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"[\W_]+", "", s)


def local_tag(tag: str) -> str:
    return tag.split("}", 1)[-1].lower() if tag else ""


def is_seed(name: str, seeds: list[str]) -> bool:
    n = norm_name(name)
    return any(n == norm_name(s) or n in norm_name(s) or norm_name(s) in n for s in seeds if s)


def coverage_row(status: str, direct: bool, method: str, source_url: str, **extra: Any) -> dict:
    row = {
        "status": status,
        "direct": direct,
        "method": method,
        "source_url": source_url,
        "collected_at": bj_stamp(),
    }
    row.update(extra)
    return row


# --------------- official probes ---------------

def probe_tiktok(cfg: dict, errors: list[str]) -> tuple[list[dict], dict]:
    block = cfg.get("tiktok") or {}
    urls = block.get("creative_center_urls") or []
    page_url = urls[0] if urls else "https://ads.tiktok.com/creative/creativeCenter/trends/hashtag"
    docs = block.get("docs") or "https://business-api.tiktok.com/portal/docs/discovery-api-overview/v1.3"
    if not block.get("enabled", True):
        return [], coverage_row("skipped", False, "disabled", page_url)

    page_notes = []
    extracted: list[dict] = []
    last_code = 0
    for url in urls:
        code, text, err = fetch(url)
        last_code = code or last_code
        if err and code == 0:
            page_notes.append(f"{url}: {err}")
            errors.append(f"tiktok creative center: {err}")
            continue
        # Official public HTML is a JS shell; do not call undocumented video/hashtag endpoints.
        has_shell = "TikTok One Creative Suite" in text or "creativeCenter" in text or "trends/hashtag" in text
        # Only accept hashtags if they appear as /tag/<name> or obvious ranked labels in HTML (SSR).
        tags = re.findall(r"https?://(?:www\.)?tiktok\.com/tag/([A-Za-z0-9_\u4e00-\u9fff]+)", text or "")
        labels = re.findall(r'data-hashtag="([^"]+)"', text or "")
        found = list(dict.fromkeys([*tags, *labels]))
        if found:
            for name in found[:10]:
                extracted.append(
                    {
                        "name": name,
                        "title": f"#{name}",
                        "url": f"https://www.tiktok.com/tag/{name}",
                        "source_url": url,
                        "published": None,
                        "snippet": "TikTok Creative Center public HTML",
                        "platform": "tiktok",
                        "coverage_type": "direct",
                        "metrics": {},
                        "kind_hint": "meme",
                    }
                )
            page_notes.append(f"{url}: HTTP {code}, extracted {len(found)} hashtag(s) from HTML")
        elif code == 200 and has_shell:
            page_notes.append(
                f"{url}: HTTP 200，官方页可打开，但热榜行未出现在静态 HTML（前端渲染）。这不等于无法访问；需父线程用浏览器读取可见 UI，未调用未公开内部接口"
            )
        elif code in {401, 403}:
            page_notes.append(f"{url}: HTTP {code}，公开页受限")
        else:
            page_notes.append(f"{url}: HTTP {code or 'ERR'} {err}".strip())

    # Official Discovery API without credentials: record auth requirement, do not invent a token.
    api = block.get("discovery_api") or ""
    api_note = ""
    if api:
        probe = f"{api}?{urlencode({'discovery_type': 'HASHTAG', 'advertiser_id': '', 'access_token': ''})}"
        code, text, err = fetch(probe)
        api_note = f"Discovery API 探测 HTTP {code or 'ERR'}" + (f"（{err}）" if err and not code else "")
        try:
            payload = json.loads(text) if text else {}
            if isinstance(payload, dict) and payload.get("message"):
                api_note += f"；业务码 {payload.get('code')}：{payload.get('message')}"
        except Exception:
            pass
        api_note += "；完整热榜需要 advertiser_id + access_token（TikTok for Business 广告账户授权）"

    if extracted:
        status = "partial"
        direct = True
        note = "仅从公开 HTML 抽到可见标签，数量可能远少于登录后的完整榜。"
    else:
        status = "needs_browser"
        direct = False
        note = "静态 HTML 无热榜行，但官方页 HTTP 200 可打开；请父线程按 parent_ui_task 读取可见榜，不要把前端渲染当成无法访问。未把 Google News/X 或内部接口当作直采。"
    note = " ".join(page_notes + ([api_note] if api_note else []) + [note])
    parent_ui_task = {
        "why": "Creative Center Trends 是官方公开页，数据在前端渲染，本环境 curl 看不到行。",
        "pages": [
            "https://ads.tiktok.com/creative/creativeCenter/trends/hashtag?countryCode=US&period=7",
            "https://ads.tiktok.com/creative/creativeCenter/trends/hashtag?countryCode=TW&period=7",
            "https://ads.tiktok.com/creative/creativeCenter/trends/video?countryCode=US&period=7",
            "https://ads.tiktok.com/creative/creativeCenter/trends/video?countryCode=TW&period=7",
        ],
        "steps": [
            "未登录打开 Hashtag 页（先 US，再 TW）；如有 cookie 横幅只接受必要项。",
            "若出现登录墙或必须登录才能看到任何标签/视频，立即停止并回报，不要登录。",
            "若未登录也能看到榜（常见是顶部少量标签），抄写可见 hashtag 名称、可见播放/发布量、时间范围（7 天）。",
            "点击页面上的 Video / 视频趋势标签（或打开上面的 trends/video 页）。",
            "对每条可见视频抄写：原始 tiktok.com/@user/video/数字ID 链接、作者、可见播放量、可见发布日；没有的字段留空，不要编。",
            "截图整个可见榜。优先挑多人复刻、可用自己照片/换脸生成的 AI 视频梗，不要泛 AI 新闻。",
        ],
        "stop_if_login": True,
    }
    cov = coverage_row(
        status,
        direct,
        "TikTok Creative Center public HTML (JS-rendered); official Discovery API requires advertiser token; official TikTok oEmbed can enrich a known public video URL",
        page_url,
        http_status=last_code,
        docs=docs,
        note=note,
        items_from_html=len(extracted),
        parent_ui_task=parent_ui_task,
    )
    return extracted, cov


def probe_youtube(cfg: dict, errors: list[str]) -> tuple[list[dict], dict]:
    block = cfg.get("youtube") or {}
    api = block.get("api_url") or "https://www.googleapis.com/youtube/v3/videos"
    docs = block.get("docs") or "https://developers.google.com/youtube/v3/docs/videos/list"
    if not block.get("enabled", True):
        return [], coverage_row("skipped", False, "disabled", api)

    key = ""
    used_env = ""
    for env_name in block.get("key_env") or ["YOUTUBE_API_KEY"]:
        val = (os.environ.get(env_name) or "").strip()
        if val:
            key, used_env = val, env_name
            break
    api_code = 0
    api_note = ""
    if not key:
        demo = f"{api}?{urlencode({'part': 'snippet', 'chart': 'mostPopular', 'regionCode': 'US', 'maxResults': 1})}"
        api_code, _text, err = fetch(demo)
        api_note = (
            f"Data API mostPopular 探测 HTTP {api_code or 'ERR'}{(' / ' + err) if err else ''}。"
            "本机未配置 YOUTUBE_API_KEY。该接口不是全站热梗搜索；2025-07-21 起 mostPopular 来自 Music/Movies/Gaming，不等于已下线的 Trending Now。"
        )

    items: list[dict] = []
    last_code = api_code
    max_results = int(block.get("max_results") or 15)
    for region in (block.get("region_codes") or ["US"]) if key else []:
        params = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": region,
            "maxResults": max_results,
            "key": key,
        }
        url = f"{api}?{urlencode(params)}"
        code, text, err = fetch(url)
        last_code = code or last_code
        if code != 200:
            errors.append(f"youtube {region}: HTTP {code} {err}")
            continue
        try:
            payload = json.loads(text)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"youtube {region}: {exc}")
            continue
        for vid in payload.get("items") or []:
            if not isinstance(vid, dict):
                continue
            vid_id = vid.get("id") or ""
            snip = vid.get("snippet") or {}
            stats = vid.get("statistics") or {}
            title = (snip.get("title") or "").strip()
            if not title or not vid_id:
                continue
            metrics = {}
            for k in ("viewCount", "likeCount", "commentCount"):
                if k in stats:
                    try:
                        metrics[k] = int(stats[k])
                    except Exception:
                        metrics[k] = stats[k]
            items.append(
                {
                    "name": title,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "source_url": docs,
                    "published": parse_dt(snip.get("publishedAt")),
                    "snippet": (snip.get("description") or "")[:300],
                    "platform": "youtube",
                    "coverage_type": "direct",
                    "metrics": metrics,
                    "kind_hint": "meme",
                    "channel": snip.get("channelTitle") or "",
                    "region": region,
                    "note": "来自 official mostPopular（Music/Movies/Gaming 榜，不等于已下线的 Trending Now）",
                }
            )
    # Official keyless path: public channel/playlist Atom RSS + oEmbed.
    # This is not a global trending chart; only latest 15 of configured public channels.
    rss_items: list[dict] = []
    rss_notes: list[str] = []
    rss_verified = False
    channel_ids = [c for c in (block.get("public_channel_ids") or []) if c]
    playlist_ids = [c for c in (block.get("public_playlist_ids") or []) if c]
    health_id = (block.get("rss_healthcheck_channel_id") or "").strip()
    feeds: list[tuple[str, str]] = []
    for cid in channel_ids:
        feeds.append((f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", "channel"))
    for pid in playlist_ids:
        feeds.append((f"https://www.youtube.com/feeds/videos.xml?playlist_id={pid}", "playlist"))
    if health_id:
        health_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={health_id}"
        code, text, err = fetch(health_url)
        parsed = parse_youtube_atom(text) if code == 200 else []
        if parsed:
            rss_verified = True
            sample = parsed[0]
            oe = official_oembed(sample.get("url") or "")
            rss_notes.append(
                f"官方 RSS 健康检查 HTTP {code}，{len(parsed)} 条；oEmbed "
                f"{'ok '+ (oe.get('title') or '')[:60] if oe else 'fail'}。"
                "健康检查频道的视频不写入热梗条目。"
            )
        else:
            rss_notes.append(f"官方 RSS 健康检查 HTTP {code or 'ERR'} {err}，entries={len(parsed)}")
    for feed_url, kind in feeds:
        code, text, err = fetch(feed_url)
        last_code = code or last_code
        parsed = parse_youtube_atom(text) if code == 200 else []
        if parsed:
            rss_verified = True
        else:
            rss_notes.append(f"{kind} RSS {feed_url}: HTTP {code or 'ERR'} {err}".strip())
            continue
        for ev in parsed:
            video_url = ev["url"]
            oe = official_oembed(video_url)
            title = (oe.get("title") or ev["title"]).strip()
            metrics = {}
            if ev.get("views") is not None:
                metrics["views"] = ev["views"]
            rss_items.append(
                {
                    "name": title,
                    "title": title,
                    "url": video_url,
                    "source_url": feed_url,
                    "published": parse_dt(ev.get("published")),
                    "snippet": f"author={oe.get('author_name') or ev.get('author') or ''}",
                    "platform": "youtube",
                    "coverage_type": "direct",
                    "source_kind": "official_rss",
                    "metrics": metrics,
                    "kind_hint": "meme",
                    "channel": oe.get("author_name") or ev.get("author") or "",
                    "note": "来自官方公开频道/播放列表 Atom RSS + oEmbed，不是全站热门榜；仅元数据，未观看视频。RSS 默认不含播放量。",
                }
            )
        rss_notes.append(f"{kind} RSS {feed_url}: HTTP {code}，{len(parsed)} 条")

    items.extend(rss_items)
    page_ui = {
        "why": "YouTube 搜索/Shorts/标签页是前端渲染，curl 的 HTML 里没有可解析的视频 URL；不要解析未文档化的 ytInitialData。",
        "pages": [
            "https://www.youtube.com/results?search_query=AI+face+swap+OR+%22photo+to+video%22+trend&sp=EgIYAQ%253D%253D",
            "https://www.youtube.com/hashtag/aivideo",
            "https://www.youtube.com/shorts/",
        ],
        "steps": [
            "未登录打开第一条搜索页（已带 Shorts 过滤 sp=EgIYAQ%253D%253D）。如出现同意/登录墙挡住结果，立即停止并回报，不要登录。",
            "抄写前 15 条可见 Shorts：原始 URL（优先 https://www.youtube.com/shorts/VIDEO_ID）、标题、频道、可见播放量、可见发布时间。没有的字段留空。",
            "在结果里优先找多人用自己照片/换脸复刻的 AI 视频梗，排除教程、工具评测、泛 AI 新闻。",
            "如有余力再打开 hashtag/aivideo 与 shorts 页，同样只读可见项并截图。",
        ],
        "stop_if_login": True,
    }
    if items:
        status = "ok" if key else "partial"
        direct = True
    elif rss_verified:
        status = "partial"
        direct = False
    else:
        status = "unavailable"
        direct = False
    method = (
        "Official YouTube channel/playlist Atom RSS + oEmbed (keyless, not a global trend chart); "
        "optional Data API v3 videos.list chart=mostPopular if YOUTUBE_API_KEY is set"
    )
    note_parts = [api_note] if api_note else []
    if used_env:
        note_parts.append(f"使用环境变量 {used_env} 调用官方 Data API，共 API 条目见上。")
    note_parts.extend(rss_notes)
    if not channel_ids and not playlist_ids:
        note_parts.append(
            "已接通官方无密钥 RSS/oEmbed 采集链路，但 meme_sources.json 的 public_channel_ids / public_playlist_ids 仍为空，"
            "故本轮没有频道直采条目。全站热梗搜索仍需 Data API key、或父线程按 parent_ui_task 读搜索页。"
        )
    note_parts.append("未观看视频，仅元数据。未把 X/新闻转述当作 YouTube 直采。")
    cov = coverage_row(
        status,
        direct,
        method,
        "https://www.youtube.com/feeds/videos.xml",
        http_status=last_code,
        key_env=used_env or "",
        docs=docs,
        note=" ".join(p for p in note_parts if p),
        item_count=len(items),
        rss_verified=rss_verified,
        rss_channels=len(channel_ids),
        parent_ui_task=page_ui,
    )
    return items, cov


def probe_instagram(cfg: dict) -> tuple[list[dict], dict]:
    block = cfg.get("instagram") or {}
    docs = block.get("docs") or "https://transparency.meta.com/en-us/researchtools/meta-content-library/"
    pages = block.get("public_pages") or [
        "https://www.instagram.com/reels/",
        "https://www.instagram.com/explore/tags/aivideo/",
    ]
    notes = []
    login_required = False
    last_code = 0
    last_final = pages[0]
    for url in pages:
        code, text, err, final = fetch_ex(url)
        last_code = code or last_code
        last_final = final or url
        low = (final or "").lower() + " " + (text or "")[:2000].lower()
        if "accounts/login" in (final or "").lower() or "/login" in (final or "").lower():
            login_required = True
            notes.append(f"{url}: HTTP {code}，已重定向到登录页 {final}。按规则停止，不登录、不复制会话。")
        elif code == 200:
            notes.append(f"{url}: HTTP 200，final={final}。静态 HTML 未见可解析的公开 reel URL。")
        else:
            notes.append(f"{url}: HTTP {code or 'ERR'} {err}")
    parent_ui_task = {
        "why": "本环境请求 Instagram Reels 已被重定向到登录页；父线程可用浏览器做只读检查，遇到登录即停。",
        "pages": pages,
        "steps": [
            "未登录打开 https://www.instagram.com/reels/ 。",
            "若跳转 accounts/login 或必须登录才能看公开 Reels，立即停止并回报，不要登录。",
            "若未登录也能看到公开 Reels，再打开 https://www.instagram.com/explore/tags/aivideo/ 与可见的音频页。",
            "抄写每条可见内容：原始 instagram.com/reel/CODE 链接、作者、可见播放/点赞、可见发布日；没有的字段留空。",
            "只收多人复刻、可用自己照片/换脸生成的 AI 视频梗。截图后结束。",
        ],
        "stop_if_login": True,
    }
    status = "login_required" if login_required else "unavailable"
    cov = coverage_row(
        status,
        False,
        "No public no-auth Instagram trend RSS/API; public reels/tag pages probed without login",
        pages[0],
        docs=docs,
        http_status=last_code,
        final_url=last_final,
        login_required=login_required,
        note=(
            " ".join(notes)
            + " Instagram 没有免申请的官方热梗 RSS。Meta Content Library 须 CASD 科研审核；Graph API 标签搜索须商业应用审核。"
            " 本次未登录、未复制 cookies、未调用非公开接口。官方 oEmbed 现也需要 Meta 应用 token，无法对未知 Reel 做无密钥补全。"
        ),
        parent_ui_task=parent_ui_task,
    )
    return [], cov


def probe_google_trends(cfg: dict, errors: list[str], seeds: list[str]) -> tuple[list[dict], dict]:
    block = cfg.get("secondary_google_trends") or {}
    feeds = block.get("feeds") or []
    if not block.get("enabled", True):
        return [], coverage_row("skipped", False, "disabled", "")
    raw_items: list[dict] = []
    last_url = feeds[0]["url"] if feeds else "https://trends.google.com/trending/rss"
    last_code = 0
    for feed in feeds:
        url = feed.get("url") or ""
        if not url:
            continue
        code, text, err = fetch(url)
        last_code = code or last_code
        last_url = url
        if code != 200:
            errors.append(f"gtrends {feed.get('id')}: HTTP {code} {err}")
            continue
        try:
            root = ET.fromstring(text)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"gtrends {feed.get('id')}: {exc}")
            continue
        for el in root.iter():
            if local_tag(el.tag) != "item":
                continue
            title = traffic = pub = link = ""
            news: list[str] = []
            for c in list(el):
                n = local_tag(c.tag)
                if n == "title":
                    title = (c.text or "").strip()
                elif n == "approx_traffic":
                    traffic = (c.text or "").strip()
                elif n == "pubdate":
                    pub = (c.text or "").strip()
                elif n == "link":
                    link = (c.text or "").strip()
                elif n == "news_item":
                    bits = [(x.text or "").strip() for x in list(c) if (x.text or "").strip()]
                    news.append(" ".join(bits))
            if not title or is_seed(title, seeds):
                continue
            snippet = " | ".join(news[:3])
            blob = f"{title} {snippet}"
            if EXCLUDE_NEWS_RE.search(blob) and not MEMEISH_RE.search(blob):
                continue
            if not MEMEISH_RE.search(blob):
                # Google search trends are mostly news/sports; only keep clear AI-video / recreation signals
                continue
            metrics = {}
            if traffic:
                metrics["approx_traffic"] = traffic
                metrics["approx_traffic_note"] = "Google Trends 官方 RSS 的约略搜索热度，不是平台播放量"
            raw_items.append(
                {
                    "name": title,
                    "title": title,
                    "url": link or url,
                    "source_url": url,
                    "published": parse_dt(pub),
                    "snippet": snippet[:400],
                    "platform": "secondary",
                    "coverage_type": "secondary",
                    "metrics": metrics,
                    "kind_hint": "meme",
                    "geo": feed.get("geo") or "",
                    "note": "Google Trends 官方 RSS 的 discovery 线索，不是 TikTok/YouTube/Instagram 直采",
                }
            )
    cov = coverage_row(
        "ok" if last_code == 200 else "unavailable",
        False,
        "Official Google Trends daily search RSS (secondary/discovery only)",
        last_url,
        http_status=last_code,
        note=(
            (block.get("note") or "官方 RSS，仅作 discovery 线索，不是三平台直采。")
            + f" 过滤后保留 {len(raw_items)} 条明显与 AI 视频/复刻梗相关的词；其余搜索热词已丢弃。"
        ),
        kept=len(raw_items),
    )
    return raw_items, cov


# --------------- existing names / seen ---------------

def load_today_seen(day: str) -> set[str]:
    names: set[str] = set()
    d = day.replace("-", "")

    def add(it: dict) -> None:
        n = norm_name(it.get("name") or "")
        if n:
            names.add(n)

    for pat in (f"tracks-{d}-*.json", f"xnew-{d}-*.json", f"news-{d}.json", f"meme-{d}.json"):
        for p in HERE.glob(pat) if "*" in pat else [HERE / pat]:
            if not p.exists():
                continue
            run = load_json(p, {})
            if "items" in run:
                for it in run.get("items") or []:
                    add(it)
            for block in (run.get("tracks") or {}).values():
                if isinstance(block, dict):
                    for it in block.get("items") or []:
                        add(it)
    return names


def load_meme_seen() -> set[str]:
    data = load_json(STATE / "meme_seen.json", {})
    if isinstance(data, list):
        return {str(x) for x in data}
    return {str(x) for x in (data.get("names") or [])}


def save_meme_seen(names: set[str]) -> None:
    lst = sorted(names)
    if len(lst) > 8000:
        lst = lst[-8000:]
    save_json(STATE / "meme_seen.json", {"names": lst})


def call_free_llm(payload: list[dict], errors: list[str]) -> dict[str, dict]:
    if not payload or not FREE_LLM.exists():
        if payload and not FREE_LLM.exists():
            errors.append("free-llm 未找到，改用规则")
        return {}
    tmp_in = HERE / "_meme_llm_payload.json"
    tmp_out = HERE / "_meme_llm_out.json"
    tmp_in.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    system = (
        "你是新词雷达热梗轨提炼器。输出纯 JSON："
        '{"items":[{"id":0,"keep":true,"name":"梗名","desc":"是什么，用户如何用自己的照片或视频复刻",'
        '"generation_feasibility":"可行/部分可行/不适用","risks":"商用或肖像或版权风险","kind":"meme"}]}'
    )
    prompt = (
        "只保留用户可能用本人照片/视频去复刻、且复刻本身也可能传播的 AI 视频或短视频热梗。"
        "不要体育、财经、一般新闻、游戏发售（除非明确是可复刻的视频梗）。"
        "hotel lobby、ai raindance、ai zombie、burning bridges、Bulin47 是历史种子，不要当成今天新爆的梗。"
        "desc 一句中文：是什么 + 用户怎么复刻；查不清就写用途待核实，禁止编造玩法或传播速度。"
        "trend 阶段不要写成「新爆」，除非输入里有多创作者复刻证据。"
        "视频都未观看，不要描述画面细节。"
        "只输出 JSON，不要 markdown 围栏。"
    )
    try:
        proc = subprocess.run(
            [str(FREE_LLM), "-s", system, "-p", prompt, "-f", str(tmp_in), "--json", "-o", str(tmp_out), "-q"],
            capture_output=True,
            text=True,
            timeout=240,
        )
        Path(HERE / "_meme_llm_status.txt").write_text((proc.stderr or "") + "\n" + (proc.stdout or ""))
        if proc.returncode != 0:
            errors.append(f"free-llm: exit {proc.returncode}: {(proc.stderr or proc.stdout or '')[-300:]}")
            return {}
        raw = tmp_out.read_text() if tmp_out.exists() else (proc.stdout or "")
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip()).strip()
        data = json.loads(raw)
        rows = data.get("items") if isinstance(data, dict) else data
        out: dict[str, dict] = {}
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and "id" in row:
                    out[str(row["id"])] = row
        return out
    except Exception as exc:  # noqa: BLE001
        errors.append(f"free-llm: {exc}")
        return {}


def to_items(raw: list[dict], llm_map: dict[str, dict], seeds: list[str]) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for i, r in enumerate(raw):
        title = (r.get("title") or r.get("name") or "").strip()
        if is_seed(title, seeds) or is_seed(r.get("name") or "", seeds):
            continue
        row = llm_map.get(str(i)) or {}
        if row.get("keep") is False and r.get("coverage_type") != "direct":
            continue
        name = (row.get("name") or r.get("name") or title).strip()
        name = re.sub(r"^#", "", name).strip()
        if not name or is_seed(name, seeds):
            continue
        key = norm_name(name)
        if not key or key in seen or len(name) > 70:
            continue
        seen.add(key)
        desc = (row.get("desc") or "").strip() or (
            (r.get("note") or r.get("snippet") or title)[:160]
        )
        published = r.get("published")
        first_seen = bj_stamp(published.astimezone(TZ8) if isinstance(published, datetime) else None)
        direct = r.get("coverage_type") == "direct"
        platform = r.get("platform") or "secondary"
        # 无多点快照、无多创作者证据时不得称「新爆」
        repl = r.get("replication_evidence") or ""
        if not repl:
            trend_stage = "待观察"
            repl = "本轮只有单次快照，未见同梗多创作者复刻证据；不能判定为新爆或给出增速。"
        else:
            trend_stage = "新发现"
        if r.get("source_kind") == "official_rss":
            src = "热梗轨·YouTube 官方RSS"
        elif platform == "tiktok":
            src = "热梗轨·TikTok Creative Center"
        elif platform == "youtube":
            src = "热梗轨·YouTube mostPopular" if direct else "热梗轨·YouTube"
        elif platform == "instagram":
            src = "热梗轨·Instagram"
        elif platform == "secondary":
            src = "热梗轨·secondary·Google Trends"
        else:
            src = f"热梗轨·{platform}"
        if not direct and platform == "secondary":
            src = "热梗轨·secondary·Google Trends"
        item = {
            "name": name,
            "desc": desc[:240],
            "url": r.get("url") or "",
            "source": src,
            "first_seen": first_seen,
            "kind": "meme",
            "platform": platform,
            "coverage_type": r.get("coverage_type") or "secondary",
            "source_url": r.get("source_url") or r.get("url") or "",
            "collected_at": bj_stamp(),
            "published_at": first_seen if published else "",
            "metrics": r.get("metrics") or {},
            "replication_evidence": repl,
            "trend_stage": trend_stage,
            "generation_feasibility": (row.get("generation_feasibility") or "待核实"),
            "risks": (row.get("risks") or "商用/肖像/版权风险待核实；未观看原视频"),
            "video_semantics": "未核实（仅元数据，未观看视频）",
            "title": title,
        }
        if r.get("note"):
            item["note"] = r["note"]
        out.append(item)
    return out


def keywords_from(items: list[dict], limit: int) -> list[dict]:
    kws: list[dict] = []
    seen: set[str] = set()
    for it in items:
        phrase = it["name"]
        key = phrase.lower()
        if key in seen:
            continue
        seen.add(key)
        stage = it.get("trend_stage") or "待观察"
        cov = "直采" if it.get("coverage_type") == "direct" else "secondary线索"
        kws.append(
            {
                "keyword": phrase,
                "reason": f"{it.get('source')} · {stage} · {cov}：{(it.get('desc') or '')[:80]}",
                "from": phrase,
            }
        )
        if len(kws) >= limit:
            break
    return kws


def main() -> int:
    ap = argparse.ArgumentParser(description="热梗轨扫描（TikTok/YouTube/Instagram 官方公开方法）")
    ap.add_argument("--date", default=now_bj().strftime("%Y-%m-%d"))
    ap.add_argument("--config", default=str(CONFIG_PATH))
    ap.add_argument("--skip", default="", help="逗号分隔: tiktok,youtube,instagram,gtrends")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    errors: list[str] = []
    seeds = list(cfg.get("seed_exclude") or SEED_DEFAULT)

    coverage: dict[str, dict] = {}
    raw: list[dict] = []

    if "tiktok" not in skip:
        items, cov = probe_tiktok(cfg, errors)
        coverage["tiktok"] = cov
        raw.extend(items)
        print(f"  tiktok: status={cov['status']} direct={cov['direct']} items={len(items)}")
    if "youtube" not in skip:
        items, cov = probe_youtube(cfg, errors)
        coverage["youtube"] = cov
        raw.extend(items)
        print(f"  youtube: status={cov['status']} direct={cov['direct']} items={len(items)}")
    if "instagram" not in skip:
        items, cov = probe_instagram(cfg)
        coverage["instagram"] = cov
        raw.extend(items)
        print(f"  instagram: status={cov['status']} direct={cov['direct']} items={len(items)}")
    if "gtrends" not in skip:
        items, cov = probe_google_trends(cfg, errors, seeds)
        coverage["secondary_google_trends"] = cov
        raw.extend(items)
        print(f"  gtrends(secondary): status={cov['status']} kept={len(items)}")

    llm_map: dict[str, dict] = {}
    if not args.no_llm and raw:
        payload = [
            {
                "id": i,
                "name": it.get("name"),
                "title": it.get("title"),
                "snippet": (it.get("snippet") or "")[:280],
                "platform": it.get("platform"),
                "coverage_type": it.get("coverage_type"),
                "url": it.get("url"),
                "metrics": it.get("metrics") or {},
            }
            for i, it in enumerate(raw)
        ]
        llm_map = call_free_llm(payload, errors)
        print(f"  llm mapped {len(llm_map)}/{len(payload)}")

    items = to_items(raw, llm_map, seeds)
    today = load_today_seen(args.date)
    seen = load_meme_seen()
    fresh: list[dict] = []
    new_seen = set(seen)
    for it in items:
        nk = norm_name(it["name"])
        if nk in today or nk in seen:
            continue
        fresh.append(it)
        new_seen.add(nk)
        if len(fresh) >= int(cfg.get("max_items") or 40):
            break
    kws = keywords_from(fresh, int(cfg.get("max_keywords") or 12))

    permissions = [
        {
            "platform": "tiktok",
            "need": "TikTok for Business 广告账户授权，调用官方 Discovery API（advertiser_id + access_token）才能稳定取得热门标签/音乐；Creative Center 登录后可见更完整 Trends。",
            "plugin_note": "目录里的 TikTok for Business 连接器面向广告投放，不是公开热梗源；本次未安装。",
        },
        {
            "platform": "youtube",
            "need": "全站热梗/搜索：配置官方 YouTube Data API v3 密钥（YOUTUBE_API_KEY）。已知公开频道的最新视频已可用官方无密钥 RSS + oEmbed；把频道 ID 写入 meme_sources.json 的 public_channel_ids 即可每日直采。搜索/Shorts 页也可由父线程按 parent_ui_task 只读抄录。",
            "plugin_note": "TubeAlfred（未安装）技能含 public search/trending/hashtags/Shorts，自称无需 YouTube API key，但连接需要 TubeAlfred 账号 API key 与 credits（https://tubealfred.com/app/api-keys），不是官方 Data API。未获用户批准付费前不安装。",
        },
        {
            "platform": "instagram",
            "need": "本环境访问 instagram.com/reels/ 会重定向到登录页。自动化直采需要经 CASD 审核的 Meta Content Library，或已审核的 Instagram Graph API 商业应用。不要登录或复制 cookies。父线程可用浏览器做只读检查，遇登录即停。",
        },
    ]

    d = args.date.replace("-", "")
    out = {
        "label": f"{args.date} 热梗轨",
        "run_at": bj_stamp(),
        "date": args.date,
        "tracks": {"meme": {"items": fresh, "keywords": kws}},
        "coverage": coverage,
        "permissions_needed": permissions,
        "errors": errors,
        "notes": [
            "新发现不等于新爆；无多点快照则趋势阶段为「待观察」。",
            "历史种子 hotel lobby / ai raindance / ai zombie / burning bridges / Bulin47 已排除，不当当天趋势。",
            "原帖营收为作者自述，不用于评分或承诺。",
            "常规 Semrush 缺数据不能判 0 搜索量。",
            "Google Trends RSS 与 X 搜索仅为 secondary/discovery，不是三平台直采。",
            "官方 YouTube RSS/oEmbed 已验证可拿到原始视频 URL；未配置的频道不会写成热梗。",
            "AIsa 目录里有社交热榜工具，但账户余额不足以支付单次调用，且部分工具带非官方/cookie 字段，本次未调用。",
        ],
    }
    out_path = HERE / f"meme-{d}.json"
    if not args.dry_run:
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
        save_meme_seen(new_seen)
    print(
        f"meme {out_path.name if not args.dry_run else '(dry)'}: "
        f"items={len(fresh)} kws={len(kws)} raw={len(raw)} errors={len(errors)}"
    )
    if fresh:
        print("  sample:", ", ".join(i["name"] for i in fresh[:8]))
    else:
        print("  本轮无合格热梗条目（已接通的官方链路本轮没有可入轨样本，或 secondary 过滤后为空）。")
    for e in errors[:12]:
        print("  !", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
