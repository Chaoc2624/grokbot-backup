#!/usr/bin/env python3
"""游戏轨 + AI工具轨：免费公开源抓取 → tracks-YYYYMMDD-{am|pm}.json

用法:
  python3 track_scan.py --mode am|pm
  python3 track_scan.py --mode pm --x-input /path/to/x_fill.json
  python3 track_scan.py --mode pm --skip steam,roblox,poki,sitemaps,ph,hn

X 查询见 XSCAN.md / TRACKS.md；本脚本不调 MCP，只吃 --x-input。
状态目录: track_state/（sitemap URL 快照 + 已见表）
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import time
import urllib.error
import urllib.request
from urllib.parse import quote
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
STATE = HERE / "track_state"
UA = "Mozilla/5.0 (X11; Linux x86_64) xinci-track-scan/1.0"
TZ8 = timezone(timedelta(hours=8))
TIMEOUT = 35

# --- X 查询（打印给例程；不在本脚本执行）---
X_QUERIES = {
    "game": [
        '(Roblox OR "roblox game" OR "steal a" OR survivors OR poki OR "unblocked games" OR itch.io) (viral OR trending OR "new game" OR exploded OR 爆款 OR 新游) -is:retweet lang:en OR lang:zh',
        '("steam charts" OR "steam top" OR "new on steam" OR "steam next fest") (game OR play) -is:retweet lang:en',
        '(游戏站 OR unblocked OR "在线玩" OR "网页游戏" OR Poki OR Roblox) (新词 OR 热词 OR 爆了 OR 日pv OR 建站) -is:retweet lang:zh',
    ],
    "ai_tools": [
        '("new ai tool" OR "ai tool launch" OR "just launched" OR "product hunt") (ai OR generator OR agent) -is:retweet lang:en min_faves:50',
        '(Toolify OR Futurepedia OR Aixploria OR "ai directory") (new OR added OR growth OR 增长) -is:retweet',
        '(AI工具站 OR "ai generator" OR "ai alternative" OR Toolify) (新上 OR 增长榜 OR 挖词 OR 热词) -is:retweet lang:zh',
    ],
}

SITEMAPS = {
    "toolify": {
        "index": "https://www.toolify.ai/sitemap.xml",
        # 与雷达 config 对齐：偏后段工具分片；首次也会拉齐快照
        "shards": r"sitemap_tools_(1[0-9]|[2-9]\d)\.xml$",
        "pause": 2.0,
        "strip_locale": True,
        "path_must": "/tool/",
    },
    "futurepedia": {
        "index": "https://www.futurepedia.io/sitemap_tools.xml",
        "shards": None,
        "pause": 1.5,
        "strip_locale": False,
        "path_must": "/tool/",
    },
    "aixploria": {
        "index": "https://www.aixploria.com/sitemap.xml",
        # 只吃近 2 个月，控量
        "shards": None,  # filled at runtime for current YYYYMM
        "pause": 1.5,
        "strip_locale": False,
        "path_must": None,
        "dynamic_shards": True,
    },
}

NSFW_RE = re.compile(
    r"\b(porn|nsfw|xxx|onlyfans|hentai|nude|sex|casino|gambling|betting|slots|poker)\b",
    re.I,
)
_LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*([^<\s\]]+)\s*(?:\]\]>)?\s*</loc>", re.I)
_LASTMOD = re.compile(
    r"<url>\s*<loc>\s*(?:<!\[CDATA\[)?\s*([^<\s\]]+)\s*(?:\]\]>)?\s*</loc>\s*"
    r"(?:<lastmod>\s*([^<]+)\s*</lastmod>)?",
    re.I | re.S,
)
LANGS = (
    "en|zh|tw|ja|ko|fr|de|es|pt|it|ru|ar|tr|vi|th|id|nl|pl|sv|da|fi|no|nb|cs|hu|ro|uk|el|he|hi|ms|fa|bn|"
    "ur|ta|te|sk|bg|hr|sr|sl|lt|lv|et|ca|tl|fil|sw"
)
_LOCALE = re.compile(rf"^(https?://[^/]+)/(?:{LANGS})(?:[-_][A-Za-z]{{2,4}})?(?=/)", re.I)


def now_bj() -> datetime:
    return datetime.now(TZ8)


def bj_stamp(dt: datetime | None = None) -> str:
    return (dt or now_bj()).strftime("%Y-%m-%d %H:%M")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url.replace("&amp;", "&"),
        headers={"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "gzip"},
    )
    last: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
                body = res.read()
            if body[:2] == b"\x1f\x8b":
                body = gzip.decompress(body)
            return body
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"fetch {url}: {last}")


def fetch_text(url: str) -> str:
    return fetch(url).decode("utf-8", "replace")


def fetch_json(url: str) -> Any:
    return json.loads(fetch_text(url))


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


def clean_game_name(name: str) -> str:
    s = name or ""
    s = re.sub(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]", "", s)  # emoji
    s = s.replace("️", "").replace("‍", "")
    s = re.sub(r"\[[^\]]*\]|\([^)]*\)|（[^）]*）", " ", s)
    s = s.replace("™", "").replace("®", "").replace("©", "")
    s = re.sub(r'["\']+', '', s)
    s = re.sub(r"\s+", " ", s).strip(" -_|")
    return s

def slug_to_name(url: str) -> str:
    path = re.sub(r"^https?://[^/]+", "", url).split("?")[0].rstrip("/")
    seg = path.split("/")[-1] if path else ""
    seg = re.sub(r"\.(html?|xml)$", "", seg, flags=re.I)
    seg = re.sub(r"[-_]+", " ", seg)
    return seg.strip()


def strip_locale(url: str) -> str:
    return _LOCALE.sub(r"\1", url)


def ok_name(name: str, min_len: int = 2, max_words: int = 8) -> bool:
    n = (name or "").strip()
    if len(n) < min_len or len(n) > 60:
        return False
    if len(n.split()) > max_words:
        return False
    if NSFW_RE.search(n):
        return False
    if re.fullmatch(r"[\d\W_]+", n):
        return False
    if re.search(r"\b(says|could|linked to|orders|costing you|predict|reconstruct|supercharge)\b", n, re.I):
        return False
    return True

def site_urls(index: str, shards: str | None, pause: float, strip: bool) -> set[str]:
    files = [index]
    if shards:
        idx = fetch_text(index)
        files = [u for u in _LOC.findall(idx) if re.search(shards, u.replace("&amp;", "&"))]
    urls: set[str] = set()
    for i, u in enumerate(files):
        if i or shards:
            time.sleep(pause)
        body = fetch_text(u)
        found = [x.replace("&amp;", "&") for x in _LOC.findall(body)]
        urls.update(found)
    return {strip_locale(u) for u in urls} if strip else urls


def aixploria_shard_re() -> str:
    """近两个 YYYYMM 的 post sitemap。"""
    now = now_bj()
    months = []
    y, m = now.year, now.month
    for _ in range(2):
        months.append(f"{y:04d}{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    alts = "|".join(months)
    return rf"sitemap-posttype-post\.({alts})\.xml$"


# ---------- Game sources ----------

def scrape_steam(errors: list[str]) -> list[dict]:
    items: list[dict] = []
    filters = {
        "topsellers": "Steam 畅销",
        "popularnew": "Steam 新热",
        "globaltopsellers": "Steam 全球畅销",
    }
    for filt, label in filters.items():
        url = f"https://store.steampowered.com/search/results/?filter={filt}&os=win&json=1"
        try:
            data = fetch_json(url)
            for it in (data.get("items") or [])[:25]:
                raw = it.get("name") or ""
                name = clean_game_name(raw)
                if not ok_name(name):
                    continue
                items.append(
                    {
                        "name": name,
                        "desc": f"{label}：{raw}",
                        "source": label,
                        "url": f"https://store.steampowered.com/search/?term={quote(name)}",
                        "kind": "game",
                        "platform": "steam",
                    }
                )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"steam:{filt}: {exc}")
        time.sleep(0.4)
    return dedupe_items(items)


def scrape_roblox(errors: list[str]) -> list[dict]:
    want = {"Top Trending", "Up-and-Coming", "Top Playing Now"}
    items: list[dict] = []
    try:
        data = fetch_json("https://apis.roblox.com/explore-api/v1/get-sorts?sessionId=1")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"roblox: {exc}")
        return items
    for sort in data.get("sorts") or []:
        label = sort.get("sortDisplayName") or ""
        if label not in want:
            continue
        for g in (sort.get("games") or [])[:25]:
            raw = g.get("name") or ""
            name = clean_game_name(raw)
            if not ok_name(name):
                continue
            uid = g.get("universeId") or g.get("rootPlaceId")
            url = f"https://www.roblox.com/games/{g.get('rootPlaceId')}" if g.get("rootPlaceId") else "https://www.roblox.com/charts"
            pc = g.get("playerCount")
            desc = f"Roblox {label}" + (f" · {pc} playing" if pc is not None else "")
            items.append(
                {
                    "name": name,
                    "desc": desc,
                    "source": f"Roblox · {label}",
                    "url": url,
                    "kind": "game",
                    "platform": "roblox",
                    "universeId": uid,
                }
            )
    return dedupe_items(items)


def scrape_poki(errors: list[str]) -> list[dict]:
    items: list[dict] = []
    try:
        html = fetch_text("https://poki.com/")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"poki: {exc}")
        return items
    slugs = []
    for m in re.finditer(r'href="/(?:[a-z]{2}/)?g/([a-z0-9][a-z0-9\-]{1,60})"', html, re.I):
        slugs.append(m.group(1).lower())
    seen = set()
    for slug in slugs:
        if slug in seen:
            continue
        seen.add(slug)
        name = slug.replace("-", " ").strip()
        if not ok_name(name):
            continue
        items.append(
            {
                "name": name,
                "desc": "Poki 首页热门",
                "source": "Poki",
                "url": f"https://poki.com/en/g/{slug}",
                "kind": "game",
                "platform": "poki",
            }
        )
        if len(items) >= 30:
            break
    return items


# ---------- AI tool sources ----------

def scrape_sitemaps(errors: list[str]) -> list[dict]:
    items: list[dict] = []
    for site, cfg in SITEMAPS.items():
        shards = cfg.get("shards")
        if cfg.get("dynamic_shards"):
            shards = aixploria_shard_re()
        path = STATE / "sitemaps" / f"{site}.json.gz"
        old = None
        if path.exists():
            try:
                old = set(json.loads(gzip.decompress(path.read_bytes()).decode("utf-8")))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"sitemap load {site}: {exc}")
                old = None
        try:
            now = site_urls(cfg["index"], shards, float(cfg.get("pause", 2)), bool(cfg.get("strip_locale")))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"sitemap {site}: {exc}")
            continue
        if not now:
            errors.append(f"sitemap {site}: no URLs")
            continue
        must = cfg.get("path_must")
        if must:
            now = {u for u in now if must in u}
        new_urls = sorted(now - old) if old is not None else []
        first = old is None
        # persist snapshot
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(json.dumps(sorted(now)).encode("utf-8"), 6))
        # first run: no "new"; still record meta via empty
        take = new_urls[:40]
        for u in take:
            name = slug_to_name(u)
            if not ok_name(name):
                continue
            items.append(
                {
                    "name": name,
                    "desc": f"{site} sitemap 新页" + ("（首跑建快照）" if first else ""),
                    "source": f"sitemap·{site}",
                    "url": u,
                    "kind": "ai_tool",
                    "platform": site,
                    "first_run": first,
                }
            )
        if first:
            # annotate in errors/info style without failing
            errors.append(f"sitemap {site}: first_run urls={len(now)} new=0 (snapshot saved)")
        else:
            errors.append(f"sitemap {site}: urls={len(now)} new={len(new_urls)}")
        time.sleep(0.5)
    return dedupe_items(items)


def scrape_producthunt(errors: list[str]) -> list[dict]:
    items: list[dict] = []
    try:
        xml = fetch_text("https://www.producthunt.com/feed")
        root = ET.fromstring(xml)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"producthunt: {exc}")
        return items
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for e in root.findall("a:entry", ns)[:40]:
        title = (e.findtext("a:title", default="", namespaces=ns) or "").strip()
        # PH titles are often "Name — tagline" or just Name
        name = re.split(r"\s+[—\-–|]\s+", title, maxsplit=1)[0].strip()
        name = clean_game_name(name)  # reuse light cleaner
        if not ok_name(name):
            continue
        link = e.find("a:link", ns)
        href = link.get("href") if link is not None else "https://www.producthunt.com/"
        summary = (e.findtext("a:summary", default="", namespaces=ns) or "")[:160]
        # soft AI filter: keep if AI-ish OR keep all PH (directory signal); prefer AI-ish
        blob = f"{title} {summary}".lower()
        ai_ish = bool(
            re.search(
                r"\b(ai|llm|gpt|agent|mcp|generator|automation|model|openai|claude)\b",
                blob,
            )
        )
        items.append(
            {
                "name": name,
                "desc": (summary or title)[:160],
                "source": "Product Hunt",
                "url": href,
                "kind": "ai_tool",
                "platform": "producthunt",
                "ai_ish": ai_ish,
            }
        )
    # prefer ai_ish, then fill
    items.sort(key=lambda x: (not x.get("ai_ish"), x["name"].lower()))
    return dedupe_items(items)[:30]


def scrape_hn(errors: list[str]) -> list[dict]:
    items: list[dict] = []
    url = "https://hnrss.org/newest?q=AI+tool"
    try:
        xml = fetch_text(url)
        root = ET.fromstring(xml)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"hn: {exc}")
        return items
    for item in root.findall("./channel/item")[:25]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        # crude name: first clause
        name = re.split(r"\s+[—\-–|:]\s+", title, maxsplit=1)[0].strip()
        name = re.sub(r"^(Show HN|Ask HN|Tell HN):\s*", "", name, flags=re.I)
        name = clean_game_name(name)
        if not ok_name(name, min_len=3, max_words=6):
            continue
        if "Show HN" not in title and "Ask HN" not in title and len(name.split()) > 4:
            continue
        items.append(
            {
                "name": name[:80],
                "desc": title[:160],
                "source": "Hacker News",
                "url": link or "https://news.ycombinator.com/",
                "kind": "ai_tool",
                "platform": "hn",
            }
        )
    return dedupe_items(items)


# ---------- helpers ----------

def dedupe_items(items: list[dict]) -> list[dict]:
    out, seen = [], set()
    for it in items:
        k = re.sub(r"[\W_]+", "", (it.get("name") or "").lower())
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


def mark_new(items: list[dict], seen_path: Path) -> list[dict]:
    """相对上次已见表打 is_new；更新 seen。"""
    prev = set(load_json(seen_path, []))
    now_keys = []
    for it in items:
        k = re.sub(r"[\W_]+", "", (it.get("name") or "").lower())
        it["is_new"] = k not in prev if prev else True
        now_keys.append(k)
    # keep last ~2000
    merged = list(dict.fromkeys(list(prev) + now_keys))[-2000:]
    save_json(seen_path, merged)
    return items


def keywords_from_game(items: list[dict], limit: int = 40) -> list[dict]:
    kws, seen = [], set()
    # prefer newly seen
    ordered = sorted(items, key=lambda x: (not x.get("is_new", True), x["name"].lower()))
    for it in ordered:
        base = it["name"].strip()
        variants = [base]
        plat = it.get("platform")
        if plat in ("roblox", "poki") or len(base.split()) <= 4:
            variants += [f"{base} unblocked", f"{base} online", f"{base} play"]
        elif plat == "steam":
            variants += [f"{base} guide", f"{base} walkthrough"]
        for v in variants:
            key = v.lower()
            if key in seen or not ok_name(v):
                continue
            seen.add(key)
            kws.append(
                {
                    "keyword": v,
                    "reason": f"{it.get('source')}: {it.get('desc','')[:80]}",
                    "from": it["name"],
                }
            )
            if len(kws) >= limit:
                return kws
    return kws


def keywords_from_tools(items: list[dict], limit: int = 40) -> list[dict]:
    kws, seen = [], set()
    # skip pure first_run noise if any slipped through with first_run True and empty new
    ordered = sorted(
        [i for i in items if not i.get("first_run")],
        key=lambda x: (not x.get("is_new", True), not x.get("ai_ish", False), x["name"].lower()),
    )
    # if everything was first_run, still allow PH/HN
    if not ordered:
        ordered = [i for i in items if i.get("platform") in ("producthunt", "hn")]
    for it in ordered:
        base = it["name"].strip()
        variants = [base, f"{base} ai", f"{base} alternative"]
        for v in variants:
            key = v.lower()
            if key in seen or not ok_name(v, max_words=6):
                continue
            # drop overly generic
            if key in {"ai", "tool", "tools", "new", "app", "agent"}:
                continue
            if len(v) > 48:
                continue
            seen.add(key)
            kws.append(
                {
                    "keyword": v,
                    "reason": f"{it.get('source')}: {it.get('desc','')[:80]}",
                    "from": it["name"],
                }
            )
            if len(kws) >= limit:
                return kws
    return kws


def load_x_input(path: Path | None, errors: list[str]) -> dict[str, list]:
    if not path:
        return {"game": [], "ai_tools": []}
    try:
        data = json.loads(path.read_text())
        return {
            "game": list(data.get("game") or []),
            "ai_tools": list(data.get("ai_tools") or data.get("ai_tool") or []),
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"x-input: {exc}")
        return {"game": [], "ai_tools": []}


def print_x_queries() -> None:
    print("=== X 查询（例程用 namespace=x 执行，结果经 --x-input 喂回）===")
    for track, qs in X_QUERIES.items():
        print(f"[{track}]")
        for q in qs:
            print(f"  {q}")
    print("===")


def main() -> int:
    ap = argparse.ArgumentParser(description="游戏轨 + AI工具轨扫描")
    ap.add_argument("--mode", choices=("am", "pm"), required=True)
    ap.add_argument("--date", default=now_bj().strftime("%Y-%m-%d"), help="北京日期 YYYY-MM-DD")
    ap.add_argument("--x-input", default="", help="可选：例程填好的 X 结果 JSON")
    ap.add_argument(
        "--skip",
        default="",
        help="逗号分隔: steam,roblox,poki,sitemaps,ph,hn",
    )
    ap.add_argument("--dry-run", action="store_true", help="不写 tracks 文件，只打印摘要")
    args = ap.parse_args()
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    errors: list[str] = []
    STATE.mkdir(parents=True, exist_ok=True)

    print_x_queries()

    game_items: list[dict] = []
    tool_items: list[dict] = []

    if "steam" not in skip:
        game_items += scrape_steam(errors)
    if "roblox" not in skip:
        game_items += scrape_roblox(errors)
    if "poki" not in skip:
        game_items += scrape_poki(errors)

    if "sitemaps" not in skip:
        tool_items += scrape_sitemaps(errors)
    if "ph" not in skip:
        tool_items += scrape_producthunt(errors)
    if "hn" not in skip:
        tool_items += scrape_hn(errors)

    x_path = Path(args.x_input) if args.x_input else None
    xfill = load_x_input(x_path, errors)
    for it in xfill["game"]:
        name = clean_game_name(it.get("name") or "")
        if not ok_name(name):
            continue
        game_items.append(
            {
                "name": name,
                "desc": it.get("desc") or "X 补源",
                "source": it.get("source") or "X·游戏",
                "url": it.get("url") or "",
                "first_seen": it.get("first_seen") or bj_stamp(),
                "kind": "game",
                "platform": "x",
            }
        )
    for it in xfill["ai_tools"]:
        name = clean_game_name(it.get("name") or "")
        if not ok_name(name):
            continue
        tool_items.append(
            {
                "name": name,
                "desc": it.get("desc") or "X 补源",
                "source": it.get("source") or "X·AI工具",
                "url": it.get("url") or "",
                "first_seen": it.get("first_seen") or bj_stamp(),
                "kind": "ai_tool",
                "platform": "x",
                "ai_ish": True,
            }
        )

    game_items = dedupe_items(game_items)
    tool_items = dedupe_items(tool_items)
    game_items = mark_new(game_items, STATE / "game_seen.json")
    tool_items = mark_new(tool_items, STATE / "ai_tools_seen.json")

    # stamp first_seen
    for it in game_items + tool_items:
        it.setdefault("first_seen", bj_stamp())

    game_kws = keywords_from_game(game_items)
    tool_kws = keywords_from_tools(tool_items)

    d = args.date.replace("-", "")
    half = args.mode
    label = f"{args.date} {'上午' if half == 'am' else '晚上'} 双轨"
    out = {
        "label": label,
        "run_at": bj_stamp(),
        "date": args.date,
        "mode": half,
        "tracks": {
            "game": {"items": game_items, "keywords": game_kws},
            "ai_tools": {"items": tool_items, "keywords": tool_kws},
        },
        "x_queries": X_QUERIES,
        "errors": errors,
    }
    # flatten mild error: only hard-fail if both tracks empty AND had fetch errors
    if not game_items and not tool_items and errors:
        out["error"] = "; ".join(errors[:5])

    out_path = HERE / f"tracks-{d}-{half}.json"
    if not args.dry_run:
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")

    print(
        f"tracks {out_path.name if not args.dry_run else '(dry)'}: "
        f"game items={len(game_items)} kws={len(game_kws)}; "
        f"ai_tools items={len(tool_items)} kws={len(tool_kws)}; "
        f"errors={len(errors)}"
    )
    if game_items:
        print("  game sample:", ", ".join(i["name"] for i in game_items[:8]))
    if tool_items:
        print("  ai_tools sample:", ", ".join(i["name"] for i in tool_items[:8]))
    for e in errors[:12]:
        print("  !", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
