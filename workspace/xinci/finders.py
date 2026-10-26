#!/usr/bin/env python3
"""找词方法第一批（2026-10-22 加，2026-10-25 升级）：在 doable.py 之前跑，产出 finder_keywords.json 给 doable --extra-file。

升级内容（2026-10-25）：
1) Google 自动补全展开：对新名字 + a–z / vs / alternative / free / ai（client=firefox）及 ds=yt，优先保留 AI/工具/网页交付意图长尾，剔除同名歌手/语法噪音。
2) Google Trends：除类目「上升最快」与 Trending RSS 外，新增一批 AI 种子词（ai tool, ai generator, ai video, ai agent, ai app, ai image, llm, mcp）的美国区 Rising 列表，只留 Breakout 或涨幅 >= 100% 且未见过的新词。
3) App Store 美区免费榜 Top100 + Hacker News：仅对近 90 天上架或 AI/工具类可网页交付 App 衍生 online / web version / alternative。
4) 前置语义预筛（classify_keyword_filter）：全链路过滤体育赛事比分、名人娱乐八卦、涉黄赌毒、大厂纯品牌导航词、词典常识及无法用简单网站交付的底层硬件/内核补丁词。

用法: python3 finders.py [--date YYYY-MM-DD] [--skip ac,trends,appstore,hn] [--dry-run]
输出: finders.json（明细）、finders.md（中文摘要）、finder_keywords.json（给 doable 的词）
"""
from __future__ import annotations
import argparse, json, re, sys, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "repo"))
UA = "Mozilla/5.0 (X11; Linux x86_64) new-term-radar finders"

TOOL_RE = re.compile(
    r"\b(generator|converter|maker|checker|editor|creator|detector|remover|downloader|translator|calculator|upscaler|"
    r"online|free|alternative|alternatives|web version|playground|demo|api|benchmark|guide|tutorial|how to|open source|"
    r"voice|model|llm|agent|mcp)\b",
    re.I,
)

AI_TECH_SIGNAL = re.compile(
    r"\b(ai|llm|gpt|claude|gemini|qwen|deepseek|kimi|mistral|llama|flux|sora|kling|runway|midjourney|viggle|suno|"
    r"udio|elevenlabs|dessa|nanbeige|nemotron|flint|voxtral|ornith|minimax|mochi|ltx|hunyuan|wan2|seedance|"
    r"mcp|agent|agents|rag|lora|comfyui|ollama|vllm|gguf|huggingface|hugging face|modelscope|openrouter|"
    r"generator|converter|maker|checker|detector|remover|upscaler|transcriber|tts|stt|ocr|voice|speech|video|"
    r"image|photo|avatar|music|sound|code|coding|prompt|harness|learnharness|benchmark|playground|open source|"
    r"self hosted|alternative|online|web version|free tool|saas|seo|directory|workflow|automation|emulator|sql|"
    r"typescript|python|vulnerability|cybersecurity|accounting)\b",
    re.I,
)

# 1. 体育赛事 / 球队对阵 / 联赛比分
SPORTS_RE = re.compile(
    r"(\b(nba|nfl|mlb|nhl|ufc|wwe|fifa|uefa|ncaa|f1|nascar|pga|atp|wta|premier league|la liga|serie a|bundesliga|"
    r"champions league|world cup|super bowl|playoffs|standings|box score|live score|highlights|matchup|predictions)\b|"
    r"\b(utsa|tulane|nebraska|oregon|palace|crystal palace|newcastle|monaco|losc|lille|golden knights|blues|"
    r"atalanta|frosinone|xelaj[uú]|municipal|lakers|warriors|celtics|knicks|yankees|dodgers|mets|chiefs|eagles|"
    r"cowboys|49ers|ravens|bills|real madrid|barcelona|arsenal|chelsea|liverpool|manchester|tottenham|juventus|"
    r"inter milan|ac milan|bayern|psg|boca juniors|river plate)\b)",
    re.I,
)

# 2. 名人 / 政客 / 影视综艺 / 时尚八卦 / 猎奇新闻
CELEB_GOSSIP_RE = re.compile(
    r"(\b(fantasy bra|victoria'?s secret|sahara ray|annie andrews|ken kutaragi|chase young|kellen moore|wes moore|"
    r"dk metcalf|josh turek|mike rogers|ben kindel|the voice|the battles|blue bloods|peaky blinders|terminal list|"
    r"asbury park|mesh tunnel cats|shy safari|lovewarschauerstr|hc andersen|taylor swift|beyonce|kardashian|"
    r"elon musk|donald trump|kamala harris|joe biden|oscars|grammys|emmys|met gala|horoscope|zodiac|tarot)\b|"
    r"\b(age|height|weight|husband|wife|boyfriend|girlfriend|married|divorce|wedding|dating|biography|wiki|"
    r"obituary|death|died|funeral|arrested|mugshot|scandal|leaked|født)\b)",
    re.I,
)

# 3. 涉黄赌毒 / 博彩 / 违规
NSFW_GAMBLING_RE = re.compile(
    r"\b(porn|nsfw|xxx|onlyfans|hentai|nude|nudify|undress|naked|sex|camgirl|stripchat|chaturbate|erotic|escort|"
    r"casino|gambling|betting|sportsbook|slots|poker|roulette|blackjack|lottery|powerball|mega millions|jackpot|"
    r"prizepicks|draftkings|fanduel|betmgm|caesars sportsbook|cheater buster)\b",
    re.I,
)

# 4. 词典释义 / 语法同音词 / 故障状态 / 股票天气 / 线下本地服务 / Trends 共搜垃圾词
TRIVIA_OUTAGE_SPAM_RE = re.compile(
    r"(\b(meaning|definition|synonym|antonym|pronunciation|crossword|wordle|scrabble|lyrics|chords|karaoke|"
    r"weather|forecast|near me|directions|hours|menu|coupon|promo code|stock price|stocks to buy|share price|"
    r"outage|is down|server status|mcp down|atlassian status|jira mcp down|jira mcp status|atlassian mcp server status|"
    r"dessa vs detta|dessa vs denna|dessa assessment|mccarbon sa|acrt inc|acrt nj|acrt nhs|steam php|what is php|"
    r"chevron font|arial definition|wrest|krillion)\b|"
    r"\b(trending beauty hacks|viral tiktok trends|non-toxic air fryer|wellness gadgets|kitchen tech upgrades|"
    r"home fitness trends|social commerce|influencer marketing trends|healthy cooking tools|k-pop trending|"
    r"digital side hustles|streaming shows trending|aura points|minimalist lifestyle trend|what is a 401k|"
    r"what is a roth ira|email marketing for restaurants|congressional app challenge|automatic refund eligibility|"
    r"attraction lockers|mailbox rental|screen crack)\b)",
    re.I,
)

# 5. 大厂纯品牌导航词 / 传统线下与流媒体老应用
PURE_BRAND_SET = {
    "whatsapp", "firefox", "wordpress", "waymo", "google", "apple", "microsoft", "amazon", "facebook",
    "instagram", "youtube", "netflix", "spotify", "tiktok", "uber", "lyft", "doordash", "airbnb", "walmart",
    "target", "costco", "ebay", "paypal", "stripe", "openai", "anthropic", "nvidia", "meta", "ibm", "alibaba",
    "alibaba.com", "fox one", "tubi", "youtube tv", "starlink", "godot", "unreal", "venturebeat", "xai",
}

LEGACY_APP_RE = re.compile(
    r"\b(domino'?s pizza|youtube tv|tubi|fox one|mcm events|crimeradar|dispatch audio|for starlink|tv remote|"
    r"alibaba\.com|netflix game controller|waymo|reflex flexible retail|zeta|7 brew coffee|fubo|wayfair|recime|espn|messenger)\b",
    re.I,
)

# 6. 无法用简单网站交付的底层硬件/内核/固件补丁词
NON_WEB_HARDWARE_RE = re.compile(
    r"(\b(gpu-unlock|gpu unlock|gpu-unlock-ada|gpu unlock ada|sm100|hackios|xnu-kernel|hackios-xnu-kernel|"
    r"fairplay-decrypt|fairplay decrypt|snapintosh|iphone duo|galaxy z fold 8|rtx 3090 mod|vbios|kernel patch|"
    r"driver unlock)\b)",
    re.I,
)

# 7. Sitemap 逆向域名碎片或无意义单字
GIBBERISH_FRAGMENT_RE = re.compile(
    r"(^(io\.|com\.|org\.|net\.|connectors\s+io\.|api\s+|eval\s+|verifier\s+)|"
    r"^(ghost|paw|stand|banana|wrest|cae|aisi|acrt|zeta|reflex|daily pro)$|\b(best laptop|best budget smartphone)\b)",
    re.I,
)

CFG = {
    "ac_max_names": 25,
    "ac_sleep": 0.08,
    "ac_keep_per_name": 3,
    "trends_categories": [5, 13],
    "trends_seeds": ["ai tool", "ai generator", "ai video", "ai agent", "ai app", "ai image", "llm", "mcp"],
    "trends_seed_min_rise": 100,   # Breakout or >= +100%
    "trends_max_check": 15,
    "appstore_top": 100,
    "hn_min_points": 3,
    "max_keywords": 60,
}
SPENT = [0]


def classify_keyword_filter(phrase: str, source: str = "", evidence: str = "") -> tuple[bool, str]:
    """前置语义预筛：判断候选词是否干净且可用简单网站（工具/生成器/对比评测/指南/导航）交付。
    返回 (is_valid, drop_reason)。
    """
    p = " ".join((phrase or "").strip().lower().split())
    if not p or len(p) < 2 or len(p) > 65:
        return False, "长度异常或为空"
    if GIBBERISH_FRAGMENT_RE.search(p):
        return False, "含义不明/包名碎片"
    if NSFW_GAMBLING_RE.search(p):
        return False, "涉黄赌毒/博彩违规"
    if SPORTS_RE.search(p):
        return False, "体育赛事/比分噪音"
    if re.search(r"\bvs\.?\b", p) and not AI_TECH_SIGNAL.search(p):
        return False, "非科技/赛事对阵词"
    if CELEB_GOSSIP_RE.search(p):
        return False, "名人/娱乐/八卦噪音"
    if TRIVIA_OUTAGE_SPAM_RE.search(p):
        return False, "词典常识/服务故障/共搜噪音"
    if p in PURE_BRAND_SET:
        return False, "大厂纯品牌导航词"
    if LEGACY_APP_RE.search(p):
        return False, "传统线下/流媒体大厂应用"
    if NON_WEB_HARDWARE_RE.search(p):
        return False, "底层硬件/内核补丁（无法用简单网站交付）"
    return True, ""


def get(url, timeout=15, tries=2):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(1)


def norm(s):
    return " ".join(re.sub(r"[^\w\s.\-+]", " ", (s or "").lower()).split())


def aisa_call(calls):
    import doable
    doable.load_env()
    from radar import aisa
    data, cost = aisa.call(calls)
    SPENT[0] += cost
    return data


# ---------- 1) autocomplete ----------
def suggest(q, yt=False):
    url = "https://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=us&q=" + urllib.parse.quote(q)
    if yt:
        url += "&ds=yt"
    try:
        return [s.lower() for s in json.loads(get(url).decode("utf-8", "replace"))[1]]
    except Exception:
        return []


def autocomplete(names, filtered_log):
    out, kw = [], []
    clean_names = []
    for name in names:
        ok, reason = classify_keyword_filter(name, "Google 补全种子")
        if not ok:
            filtered_log.append({"phrase": norm(name), "source": "Google 补全种子", "reason": reason})
            continue
        if name not in clean_names:
            clean_names.append(name)

    for name in clean_names[:CFG["ac_max_names"]]:
        n = norm(name)
        if len(n) < 3:
            continue
        base = suggest(n)
        if " " not in n and not n.endswith("ai"):
            base = suggest(f"{n} ai") + base
        time.sleep(CFG["ac_sleep"])
        raw_tails = {s for s in base if s.startswith(n) and s != n}
        if not raw_tails:
            out.append({"name": name, "tails": [], "yt": []})
            continue
        suffixes = ["ai", "vs", "alternative", "free", "online", "model", "tool", *"abcdefghimoprstuvw"]
        for suf in suffixes:
            for s in suggest(f"{n} {suf}"):
                if s.startswith(n) and s != n:
                    raw_tails.add(s)
            time.sleep(CFG["ac_sleep"])
        yt_raw = [s for s in (suggest(n, yt=True) + suggest(f"{n} ai", yt=True)) if s.startswith(n) and s != n]
        yt = []
        for s in yt_raw:
            ok, _ = classify_keyword_filter(s, "Google 补全(YT)")
            if ok and s not in yt:
                yt.append(s)

        tails = []
        for s in sorted(raw_tails):
            ok, reason = classify_keyword_filter(s, f"Google 补全({name})")
            if not ok:
                filtered_log.append({"phrase": s, "source": f"Google 补全({name})", "reason": reason})
                continue
            # 单字短名（如 dessa）要求补全词带 AI/模型/语音/工具词根，防止混入同名歌手
            if " " not in n and len(n) <= 7 and not AI_TECH_SIGNAL.search(s):
                filtered_log.append({"phrase": s, "source": f"Google 补全({name})", "reason": "单字同名非AI语义"})
                continue
            tails.append(s)

        ranked = sorted(
            tails,
            key=lambda s: (
                not bool(AI_TECH_SIGNAL.search(s)),
                not bool(TOOL_RE.search(s)),
                s not in yt,
                len(s),
            ),
        )
        out.append({"name": name, "tails": tails, "yt": yt})
        for s in ranked[:CFG["ac_keep_per_name"]]:
            kw.append({
                "phrase": s,
                "source": "Google 补全",
                "names": [name],
                "is_vacuum_candidate": True,
                "evidence": f"{name} 的补全长尾（共 {len(tails)} 条有效 AI/工具长尾）",
            })
    return out, kw


# ---------- 2) trends ----------
TF = "any_dataforseo_apis_v1_dataforseo_keywords_data_g_f56cfb"


def trends(state, target_date, filtered_log):
    res = {"rss": [], "rising": {}, "seed_rising": [], "fresh": [], "errors": []}
    try:
        root = ET.fromstring(get("https://trends.google.com/trending/rss?geo=US"))
        ns = {"ht": "https://trends.google.com/trending/rss"}
        for it in root.iter("item"):
            term = it.findtext("title") or ""
            ok, reason = classify_keyword_filter(term, "Trends RSS")
            if not ok:
                filtered_log.append({"phrase": norm(term), "source": "Trends RSS", "reason": reason})
                continue
            res["rss"].append({"term": term, "traffic": it.findtext("ht:approx_traffic", namespaces=ns)})
    except Exception as e:
        res["errors"].append(f"Trends RSS: {e}")

    seen = state.setdefault("trends_seen", {})

    # 2a) AI 种子词 Rising（Breakout 或涨幅 >= 100%，未见过的新词）
    seed_cache = state.setdefault("trends_seed_cache", {})
    seed_map = {}
    if target_date in seed_cache and isinstance(seed_cache[target_date], dict) and seed_cache[target_date].get("data"):
        seed_map = seed_cache[target_date]["data"]
    else:
        s_calls = [
            {
                "call_id": f"seed_{i}",
                "tool": TF,
                "arguments": {
                    "body": [{
                        "keywords": [seed],
                        "location_code": 2840,
                        "time_range": "past_7_days",
                        "type": "web",
                        "item_types": ["google_trends_queries_list"],
                    }]
                },
            }
            for i, seed in enumerate(CFG["trends_seeds"])
        ]
        try:
            s_data = aisa_call(s_calls)
            for i, seed in enumerate(CFG["trends_seeds"]):
                d = s_data.get(f"seed_{i}") or {}
                items = ((d.get("tasks") or [{}])[0].get("result") or [{}])[0].get("items") or []
                rlist = []
                for it in items:
                    for r in (it.get("data") or {}).get("rising") or []:
                        rlist.append({"query": r.get("query"), "value": r.get("value")})
                seed_map[seed] = rlist
            seed_cache[target_date] = {"data": seed_map, "cost": round(SPENT[0] / 1e6, 4)}
        except Exception as e:
            res["errors"].append(f"AI 种子词 Rising: {e}")

    seen_seed_q = set()
    for seed, rows in seed_map.items():
        for r in rows:
            q = norm(r.get("query"))
            val = r.get("value")
            if not q or q in seen_seed_q:
                continue
            is_breakout = isinstance(val, str) and "breakout" in val.lower()
            num_val = val if isinstance(val, (int, float)) else (999999 if is_breakout else 0)
            if num_val < CFG["trends_seed_min_rise"]:
                continue
            ok, reason = classify_keyword_filter(q, f"Trends种子({seed})")
            if not ok:
                filtered_log.append({"phrase": q, "source": f"Trends种子({seed})", "reason": reason})
                continue
            seen_seed_q.add(q)
            first_day = seen.get(q)
            if first_day is not None and first_day != target_date:
                continue
            seen[q] = target_date
            res["seed_rising"].append({
                "term": q,
                "seed": seed,
                "value": val,
                "first_seen": target_date,
                "is_breakout": is_breakout or num_val >= 5000,
            })

    res["seed_rising"].sort(key=lambda x: -(x["value"] if isinstance(x["value"], (int, float)) else 999999))

    # 2b) 类目上升最快（使用当日缓存避免重复扣费）
    cat_cache = state.setdefault("trends_cat_cache", {})
    if target_date in cat_cache and isinstance(cat_cache[target_date], dict) and cat_cache[target_date]:
        res["rising"] = cat_cache[target_date]
    elif target_date in cat_cache and isinstance(cat_cache[target_date], list) and cat_cache[target_date]:
        by_c = {"c5_past_day": [], "c5_past_7_days": [], "c13_past_day": [], "c13_past_7_days": []}
        for r in cat_cache[target_date]:
            k = f"c{r.get('category', 5)}_{r.get('window', 'past_7_days')}"
            by_c.setdefault(k, []).append({"query": r.get("query"), "value": r.get("value")})
        res["rising"] = by_c
    else:
        calls = []
        for cat in CFG["trends_categories"]:
            for tr in ("past_day", "past_7_days"):
                calls.append({"call_id": f"c{cat}_{tr}", "tool": TF, "arguments": {"body": [{
                    "category_code": cat, "location_code": 2840, "time_range": tr, "item_types": ["google_trends_queries_list"]}]}})
        try:
            data = aisa_call(calls)
            for c in calls:
                d = data.get(c["call_id"])
                if not d:
                    res["errors"].append(f"类目上升 {c['call_id']} 无结果"); continue
                items = ((d.get("tasks") or [{}])[0].get("result") or [{}])[0].get("items") or []
                rising = []
                for i in items:
                    rising += [{"query": r.get("query"), "value": r.get("value")} for r in ((i.get("data") or {}).get("rising") or [])]
                res["rising"][c["call_id"]] = rising
            cat_cache[target_date] = res["rising"]
        except Exception as e:
            res["errors"].append(f"类目上升: {e}")

    # 候选：类目上升词 + RSS 词（先经过语义预筛，再查 12 个月年龄）
    cand = []
    for k, rows in res["rising"].items():
        for r in rows:
            q = norm(r.get("query"))
            if not q or q in cand:
                continue
            ok, reason = classify_keyword_filter(q, f"Trends({k})")
            if not ok:
                filtered_log.append({"phrase": q, "source": f"Trends({k})", "reason": reason})
                continue
            cand.append(q)
    for r in res["rss"]:
        q = norm(r["term"])
        if q and q not in cand and AI_TECH_SIGNAL.search(q):
            cand.append(q)
    for q in cand:
        seen.setdefault(q, target_date)

    check = [q for q in cand if not state.setdefault("trends_age", {}).get(q)][:CFG["trends_max_check"]]
    calls = [{"call_id": f"a{i}", "tool": "post_dataforseo_keywords_trends_explore_live", "arguments": {"body": [{
        "keywords": check[i:i + 5], "location_code": 2840, "time_range": "past_5_years"}]}} for i in range(0, len(check), 5)]
    try:
        data = aisa_call(calls) if calls else {}
        for i, c in enumerate(calls):
            kws = c["arguments"]["body"][0]["keywords"]
            items = ((((data.get(c["call_id"]) or {}).get("tasks") or [{}])[0].get("result") or [{}])[0].get("items") or [])
            graph = next((it for it in items if it.get("type") == "dataforseo_trends_graph"), None)
            if not graph:
                continue
            cutoff = (date.today() - timedelta(days=365)).isoformat()
            for j, k in enumerate(kws):
                old = [p["values"][j] or 0 for p in graph.get("data", []) if (p.get("date_from") or "") < cutoff and p.get("values")]
                state["trends_age"][k] = "old" if old and max(old) >= 5 else "new"
    except Exception as e:
        res["errors"].append(f"Trends 年龄检查: {e}")

    week = (date.fromisoformat(target_date) - timedelta(days=7)).isoformat()
    for q in cand:
        if state["trends_age"].get(q) == "new":
            res["fresh"].append({
                "term": q,
                "first_seen": seen[q],
                "window": "1d" if seen[q] == target_date else ("7d" if seen[q] >= week else ""),
            })

    kw = []
    for sr in res["seed_rising"]:
        val_s = "Breakout" if sr.get("is_breakout") and not isinstance(sr["value"], (int, float)) else f"+{sr['value']}%"
        kw.append({
            "phrase": sr["term"],
            "source": "Trends AI飙升",
            "names": [sr["seed"]],
            "is_vacuum_candidate": True,
            "evidence": f"Trends 种子词「{sr['seed']}」飙升 {val_s}（新发现）",
        })
    for f in res["fresh"]:
        kw.append({
            "phrase": f["term"],
            "source": "Google Trends",
            "names": [],
            "is_vacuum_candidate": bool(AI_TECH_SIGNAL.search(f["term"])),
            "evidence": f"{f['window']} 上升，12 个月内新出现",
        })
    return res, kw


# ---------- 3) app store ----------
def appstore(state, target_date, filtered_log):
    feed = json.loads(get("https://rss.marketingtools.apple.com/api/v2/us/apps/top-free/100/apps.json"))["feed"]["results"]
    hist = state.setdefault("appstore", {})
    first_run = not hist
    new, kw = [], []
    recent_cutoff = (date.fromisoformat(target_date) - timedelta(days=120)).isoformat()
    for rank, a in enumerate(feed, 1):
        aid = a["id"]
        is_new_today = (aid not in hist) or (hist[aid].get("first") == target_date)
        if is_new_today:
            hist[aid] = {"name": a["name"], "first": target_date, "release": a.get("releaseDate")}
            rel = a.get("releaseDate") or "0"
            short = norm(re.split(r"[:\-–—|•(]", a["name"])[0])
            ok, reason = classify_keyword_filter(short, "App Store")
            is_recent_or_ai = bool(AI_TECH_SIGNAL.search(a["name"]))
            deliverable = ok and is_recent_or_ai
            if not first_run or deliverable:
                new.append({
                    "name": a["name"],
                    "rank": rank,
                    "artist": a.get("artistName"),
                    "release": rel,
                    "url": a.get("url"),
                    "baseline": first_run,
                    "web_deliverable": deliverable,
                })
            if not ok:
                filtered_log.append({"phrase": short, "source": f"App Store(#{rank} {a['name']})", "reason": reason})
            elif not is_recent_or_ai:
                filtered_log.append({"phrase": short, "source": f"App Store(#{rank} {a['name']})", "reason": f"老应用重返榜单(上架 {rel})，非AI新工具"})
        hist[aid]["last"] = target_date

    for n in new:
        if not n.get("web_deliverable"):
            continue
        short = norm(re.split(r"[:\-–—|•(]", n["name"])[0])
        if "ai" in n["name"].lower() and "ai" not in short.split():
            short = f"{short} ai"
        for suf in ("online", "web version", "alternative"):
            kw.append({
                "phrase": f"{short} {suf}",
                "source": "App Store 新上榜",
                "names": [n["name"]],
                "is_vacuum_candidate": True,
                "evidence": f"美区免费榜第 {n['rank']} 名，上架 {n['release']}",
            })
    return {"first_run": first_run, "new": new, "size": len(feed)}, kw


# ---------- 4) hacker news ----------
HN_Q = ["alternative", "alternative to", "open source alternative", "I hate", "frustrated with", "looking for alternative", "fed up with", "switching from"]
ALT = re.compile(r"(?:alternatives? to|replac(?:e|ement for|ing)|instead of|switch(?:ing|ed)? from|ditch(?:ing|ed)?|leav(?:e|ing))\s+([A-Z][\w.+\-]*(?:\s[A-Z][\w.+\-]*)?)|\b([A-Z][\w.+\-]*(?:\s[A-Z][\w.+\-]*)?)\s+alternatives?\b")


def hn(filtered_log):
    since = int(time.time()) - 86400 * 2
    hits, seen, kw = [], set(), []
    for q in HN_Q:
        url = ("https://hn.algolia.com/api/v1/search?tags=(story,ask_hn,show_hn)&hitsPerPage=50&query=" + urllib.parse.quote(f'"{q}"')
               + f"&numericFilters=created_at_i>{since}")
        try:
            for h in json.loads(get(url))["hits"]:
                if h["objectID"] in seen or (h.get("points") or 0) < CFG["hn_min_points"]:
                    continue
                seen.add(h["objectID"])
                hits.append({"title": h.get("title"), "points": h.get("points"), "comments": h.get("num_comments"),
                             "url": f"https://news.ycombinator.com/item?id={h['objectID']}", "query": q})
        except Exception:
            pass
        time.sleep(0.15)
    stop = {"Open-source", "Open", "Show", "Ask", "HN", "The", "A", "An", "I", "My", "Why", "How", "What", "Source", "Free", "We", "For"}
    for h in hits:
        for m in ALT.finditer(h["title"] or ""):
            prod = (m.group(1) or m.group(2) or "").strip()
            if prod and prod.split()[0] not in stop:
                kw_phrase = f"{norm(prod)} alternative"
                ok, reason = classify_keyword_filter(kw_phrase, "Hacker News", h.get("title") or "")
                if not ok:
                    filtered_log.append({"phrase": kw_phrase, "source": "Hacker News", "reason": reason})
                    continue
                h["product"] = prod
                kw.append({
                    "phrase": kw_phrase,
                    "source": "Hacker News",
                    "names": [prod],
                    "is_vacuum_candidate": True,
                    "evidence": f"HN「{h['title'][:70]}」{h['points']} 分",
                })
    hits.sort(key=lambda h: -(h["points"] or 0))
    return hits, kw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--skip", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    skip = set(x.strip() for x in a.skip.split(",") if x.strip())
    sp = HERE / "finders_state.json"
    state = json.loads(sp.read_text()) if sp.exists() else {}
    filtered_log = []

    merged = json.loads((HERE / "merged.json").read_text()) if (HERE / "merged.json").exists() else {"terms": []}
    names = []
    # 优先把当日 AI 新品与建站热词放入自动补全名字列表
    day_compact = a.date.replace("-", "")
    for p in sorted(HERE.glob(f"xnew-{day_compact}-*.json")) + sorted(HERE.glob("xnew-*.json"))[:2]:
        try:
            for it in json.loads(p.read_text()).get("items", []):
                if it.get("kind") != "not_model":
                    names.append(it.get("keyword") or it.get("name", ""))
        except Exception:
            pass
    bk = HERE / "board_keywords.json"
    if bk.exists():
        names += [k["phrase"] for k in json.loads(bk.read_text())]
    names += [t["name"] for t in merged.get("terms", [])]
    names = [n for n in dict.fromkeys(names) if n]

    out, kws, errs = {"date": a.date}, [], []
    for key, fn in (
        ("ac", lambda: autocomplete(names, filtered_log)),
        ("trends", lambda: trends(state, a.date, filtered_log)),
        ("appstore", lambda: appstore(state, a.date, filtered_log)),
        ("hn", lambda: hn(filtered_log)),
    ):
        if key in skip:
            continue
        try:
            r, k = fn()
            out[key] = r
            kws += k
        except Exception as e:
            errs.append(f"{key}: {type(e).__name__}: {e}")

    uniq = {}
    for k in kws:
        ok, reason = classify_keyword_filter(k["phrase"], k.get("source", ""), k.get("evidence", ""))
        if not ok:
            filtered_log.append({"phrase": k["phrase"], "source": k.get("source", ""), "reason": reason})
            continue
        uniq.setdefault(k["phrase"], k)

    # 每个来源轮流取，AI 飙升与工具意图词优先
    by = {}
    for k in sorted(uniq.values(), key=lambda k: (k.get("source") != "Trends AI飙升", not TOOL_RE.search(k["phrase"]))):
        by.setdefault(k["source"], []).append(k)
    kws = []
    while any(by.values()) and len(kws) < CFG["max_keywords"]:
        for src in list(by):
            if by[src] and len(kws) < CFG["max_keywords"]:
                kws.append(by[src].pop(0))

    out.update(errors=errs, spent_micros=SPENT[0], keywords=kws, filtered_noise=filtered_log)
    sp.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    (HERE / "finders.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (HERE / "finder_keywords.json").write_text(json.dumps(kws, ensure_ascii=False, indent=1))

    L = [f"## 找词方法（{a.date} · 含 Trends AI 种子词 Rising & 前置语义预筛）", ""]
    if "ac" in out:
        has = [x for x in out["ac"] if x["tails"]]
        L.append(f"- Google 补全：查了 {len(out['ac'])} 个有效名字，{len(has)} 个有 AI/工具长尾：" + "；".join(f"{x['name']}（{len(x['tails'])} 条，YT {len(x['yt'])}）" for x in has))
    if "trends" in out:
        t = out["trends"]
        sr = t.get("seed_rising") or []
        L.append(f"- Trends AI 种子词 Rising（Breakout 或 ≥+100% 新词）：共 {len(sr)} 个：" + "、".join(f"{x['term']}（{x['seed']} +{x['value']}%）" for x in sr[:15]))
        L.append(f"- Google Trends 类目/RSS：RSS {len(t['rss'])} 条，类目上升 " + "、".join(f"{k}:{len(v)}" for k, v in t["rising"].items())
                 + f"；12 个月内新出现（已剔除球赛/八卦）的 {len(t['fresh'])} 个：" + "、".join(f["term"] for f in t["fresh"]))
        if t["errors"]:
            L.append("  - 问题：" + "；".join(t["errors"]))
    if "appstore" in out:
        s = out["appstore"]
        deliverable_apps = [n for n in s["new"] if n.get("web_deliverable")]
        L.append(f"- App Store 免费榜：新上榜 {len(s['new'])} 个（可网页交付 {len(deliverable_apps)} 个）："
                 + "、".join(f"{n['name']}（#{n['rank']}{' ✅' if n.get('web_deliverable') else ' ⏭️跳过'}）" for n in s["new"]))
    if "hn" in out:
        L.append(f"- Hacker News 48 小时：{len(out['hn'])} 帖：" + "；".join(f"[{h['title']}]({h['url']}) {h['points']} 分" for h in out["hn"][:8]))
    if filtered_log:
        uniq_f = []
        seen_f = set()
        for f in filtered_log:
            if f["phrase"] not in seen_f:
                seen_f.add(f["phrase"])
                uniq_f.append(f"{f['phrase']}（{f['reason']}）")
        L.append(f"- 🧹 前置语义预筛拦截噪音词 {len(uniq_f)} 个：" + "、".join(uniq_f[:20]))
    L.append(f"- 送去 Semrush / 真空期检测的候选词 {len(kws)} 个。本步新增 AIsa 花费 ${SPENT[0]/1e6:.3f}。")
    if errs:
        L.append("- 出错：" + "；".join(errs))
    (HERE / "finders.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
