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


def fetch(url: str, timeout: int = TIMEOUT) -> tuple[int, str, str]:
    """Return (http_status, body_text, error). Does not send cookies or impersonate."""
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
        if body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return code, body.decode("utf-8", "replace"), ""
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read() or b""
            if body[:2] == b"\x1f\x8b":
                body = gzip.decompress(body)
            text = body.decode("utf-8", "replace")
        except Exception:
            text = ""
        return int(exc.code or 0), text, f"HTTPError {exc.code}: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        return 0, "", f"{type(exc).__name__}: {exc}"


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
                f"{url}: HTTP 200，页面可打开，但趋势列表未出现在 HTML（前端渲染 / 登录后才有完整榜），未调用未公开内部接口"
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
        status = "unavailable"
        direct = False
        note = "官方 Creative Center 公开页未能提供可解析的热榜数据；未把 Google News/X 或内部接口当作直采。"
    note = " ".join(page_notes + ([api_note] if api_note else []) + [note])
    cov = coverage_row(
        status,
        direct,
        "TikTok Creative Center public HTML; official Discovery API requires advertiser token",
        page_url,
        http_status=last_code,
        docs=docs,
        note=note,
        items_from_html=len(extracted),
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
    if not key:
        # Probe once to record official 403 without a key
        demo = f"{api}?{urlencode({'part': 'snippet', 'chart': 'mostPopular', 'regionCode': 'US', 'maxResults': 1})}"
        code, _text, err = fetch(demo)
        cov = coverage_row(
            "unavailable",
            False,
            "YouTube Data API v3 videos.list chart=mostPopular",
            docs,
            http_status=code,
            note=(
                f"官方接口探测 HTTP {code or 'ERR'}{(' / ' + err) if err else ''}。"
                "本机未配置 YOUTUBE_API_KEY / GOOGLE_API_KEY。"
                "官方频道 RSS 不提供 mostPopular 榜（chart= 参数返回 400）。"
                "注意：2025-07-21 起 mostPopular 来自 Music / Movies / Gaming 榜，不再等于已下线的 Trending Now 页。"
            ),
        )
        return [], cov

    items: list[dict] = []
    last_code = 0
    max_results = int(block.get("max_results") or 15)
    for region in block.get("region_codes") or ["US"]:
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
    cov = coverage_row(
        "ok" if items else "unavailable",
        bool(items),
        "YouTube Data API v3 videos.list chart=mostPopular",
        docs,
        http_status=last_code,
        key_env=used_env,
        note=(
            f"使用环境变量 {used_env} 调用官方 API，共 {len(items)} 条。"
            "榜单已不是原 Trending Now；短视频热梗未必出现。未观看视频，仅元数据。"
        ),
        item_count=len(items),
    )
    return items, cov


def probe_instagram(cfg: dict) -> tuple[list[dict], dict]:
    block = cfg.get("instagram") or {}
    docs = block.get("docs") or "https://transparency.meta.com/en-us/researchtools/meta-content-library/"
    cov = coverage_row(
        "unavailable",
        False,
        "No public no-auth Instagram trend RSS/API; Meta Content Library requires researcher review",
        docs,
        note=(
            "Instagram 没有免申请的官方热梗 RSS 或公开趋势 API。"
            "Meta Content Library / API 可查公开帖与趋势图，但须经 CASD 审核的科研权限，且仅限符合资格的研究用途。"
            "Instagram Graph API 的标签搜索需要商业账号与应用审核。"
            "本次未登录、未复制 cookies、未调用非公开接口，故无 Instagram 直采条目。"
        ),
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
        src = {
            "tiktok": "热梗轨·TikTok Creative Center",
            "youtube": "热梗轨·YouTube mostPopular",
            "instagram": "热梗轨·Instagram",
            "secondary": "热梗轨·secondary·Google Trends",
        }.get(platform, f"热梗轨·{platform}")
        if not direct:
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
            "need": "在本机或例程环境配置官方 YouTube Data API v3 密钥（环境变量 YOUTUBE_API_KEY）。",
            "plugin_note": "TubeAlfred 面向字幕/评论/频道，不是官方热门榜；本次未安装。",
        },
        {
            "platform": "instagram",
            "need": "经 Meta Research Tools / CASD 审核的 Content Library 权限，或已审核的 Instagram Graph API 商业应用。无免密钥公开趋势接口。",
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
            "Google Trends RSS 仅为 secondary/discovery，不是三平台直采。",
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
        print("  本轮无合格热梗条目（三平台直采不可用，且 secondary 过滤后为空或未通过）。")
    for e in errors[:12]:
        print("  !", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
