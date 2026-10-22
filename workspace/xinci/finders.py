#!/usr/bin/env python3
"""找词方法第一批（2026-10-22 加）：在 doable.py 之前跑，产出 finder_keywords.json 给 doable --extra-file。

1) Google 自动补全展开：今天的新名字 + a–z / vs / alternative / free（client=firefox），另查 ds=yt。
2) Google Trends：类目「上升最快」（搜索词留空，DataForSEO Trends explore 经 AIsa），1 天和 7 天窗口；
   加 trends.google.com/trending/rss?geo=US。用 past_5_years 曲线剔除 12 个月前就有热度的词。
3) App Store 美区免费榜 Top100：存历史，新上榜 App → "<app> online / web version / alternative"。
4) Hacker News（hn.algolia.com）：过去 24 小时的 alternative 和抱怨类帖子。

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
TOOL_RE = re.compile(r"\b(generator|converter|maker|checker|editor|creator|detector|remover|downloader|translator|online|free)\b", re.I)
CFG = {"ac_max_names": 25, "ac_sleep": 0.35, "ac_keep_per_name": 3, "trends_categories": [5, 13],
       "trends_max_check": 15, "appstore_top": 100, "hn_min_points": 3, "max_keywords": 60}
SPENT = [0]


def get(url, timeout=30, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3)


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


def autocomplete(names):
    out, kw = [], []
    for name in names[:CFG["ac_max_names"]]:
        n = norm(name)
        if len(n) < 3:
            continue
        base = suggest(n)
        time.sleep(CFG["ac_sleep"])
        tails = {s for s in base if s.startswith(n) and s != n}
        if not tails:            # 名字本身没补全 → 没人搜，不展开
            out.append({"name": name, "tails": [], "yt": []})
            continue
        for suf in [*"abcdefghijklmnopqrstuvwxyz", "vs", "alternative", "free"]:
            for s in suggest(f"{n} {suf}"):
                if s.startswith(n) and s != n:
                    tails.add(s)
            time.sleep(CFG["ac_sleep"])
        yt = [s for s in suggest(n, yt=True) if s.startswith(n) and s != n]
        ranked = sorted(tails, key=lambda s: (not TOOL_RE.search(s), not re.search(r"\b(vs|alternative|free)\b", s), len(s)))
        out.append({"name": name, "tails": sorted(tails), "yt": yt})
        for s in ranked[:CFG["ac_keep_per_name"]]:
            kw.append({"phrase": s, "source": "Google 补全", "names": [name], "evidence": f"{name} 的补全长尾（共 {len(tails)} 条）"})
    return out, kw


# ---------- 2) trends ----------
TF = "any_dataforseo_apis_v1_dataforseo_keywords_data_g_f56cfb"


def trends(state):
    res = {"rss": [], "rising": {}, "fresh": [], "errors": []}
    try:
        root = ET.fromstring(get("https://trends.google.com/trending/rss?geo=US"))
        ns = {"ht": "https://trends.google.com/trending/rss"}
        for it in root.iter("item"):
            res["rss"].append({"term": it.findtext("title"), "traffic": it.findtext("ht:approx_traffic", namespaces=ns)})
    except Exception as e:
        res["errors"].append(f"Trends RSS: {e}")
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
    except Exception as e:
        res["errors"].append(f"类目上升: {e}")
    # 候选：类目上升词 + RSS 词；记录首次出现，再用 5 年曲线看 12 个月前有没有热度
    seen = state.setdefault("trends_seen", {})
    today = date.today().isoformat()
    cand = []
    for k, rows in res["rising"].items():
        for r in rows:
            q = norm(r["query"])
            if q and q not in cand:
                cand.append(q)
    for r in res["rss"]:
        q = norm(r["term"])
        if q and q not in cand:
            cand.append(q)
    for q in cand:
        seen.setdefault(q, today)
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
    week = (date.today() - timedelta(days=7)).isoformat()
    for q in cand:
        if state["trends_age"].get(q) == "new":
            res["fresh"].append({"term": q, "first_seen": seen[q], "window": "1d" if seen[q] == today else ("7d" if seen[q] >= week else "")})
    kw = [{"phrase": f["term"], "source": "Google Trends", "names": [], "evidence": f"{f['window']} 上升，12 个月内新出现"} for f in res["fresh"]]
    return res, kw


# ---------- 3) app store ----------
def appstore(state):
    feed = json.loads(get("https://rss.marketingtools.apple.com/api/v2/us/apps/top-free/100/apps.json"))["feed"]["results"]
    hist = state.setdefault("appstore", {})
    first_run = not hist
    today = date.today().isoformat()
    new, kw = [], []
    for rank, a in enumerate(feed, 1):
        aid = a["id"]
        if aid not in hist:
            hist[aid] = {"name": a["name"], "first": today, "release": a.get("releaseDate")}
            recent = (a.get("releaseDate") or "0") >= (date.today() - timedelta(days=90)).isoformat()
            if not first_run or recent:
                new.append({"name": a["name"], "rank": rank, "artist": a.get("artistName"), "release": a.get("releaseDate"),
                            "url": a.get("url"), "baseline": first_run})
        hist[aid]["last"] = today
    for n in new:
        short = norm(re.split(r"[:\-–—|]", n["name"])[0])
        for suf in ("online", "web version", "alternative"):
            kw.append({"phrase": f"{short} {suf}", "source": "App Store 新上榜", "names": [n["name"]],
                       "evidence": f"美区免费榜第 {n['rank']} 名，上架 {n['release']}"})
    return {"first_run": first_run, "new": new, "size": len(feed)}, kw


# ---------- 4) hacker news ----------
HN_Q = ["alternative", "alternative to", "I hate", "frustrated with", "looking for alternative", "fed up with", "switching from"]
ALT = re.compile(r"(?:alternatives? to|replac(?:e|ement for|ing)|instead of|switch(?:ing|ed)? from|ditch(?:ing|ed)?|leav(?:e|ing))\s+([A-Z][\w.+\-]*(?:\s[A-Z][\w.+\-]*)?)|\b([A-Z][\w.+\-]*(?:\s[A-Z][\w.+\-]*)?)\s+alternatives?\b")


def hn():
    since = int(time.time()) - 86400
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
        time.sleep(0.3)
    stop = {"Open-source", "Open", "Show", "Ask", "HN", "The", "A", "An", "I", "My", "Why", "How", "What", "Open", "Source", "Free", "We"}
    for h in hits:
        for m in ALT.finditer(h["title"] or ""):
            prod = (m.group(1) or m.group(2) or "").strip()
            if prod and prod.split()[0] not in stop:
                h["product"] = prod
                kw.append({"phrase": f"{norm(prod)} alternative", "source": "Hacker News", "names": [prod],
                           "evidence": f"HN「{h['title'][:70]}」{h['points']} 分"})
    hits.sort(key=lambda h: -(h["points"] or 0))
    return hits, kw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--skip", default="")
    a = ap.parse_args()
    skip = set(a.skip.split(","))
    sp = HERE / "finders_state.json"
    state = json.loads(sp.read_text()) if sp.exists() else {}
    merged = json.loads((HERE / "merged.json").read_text()) if (HERE / "merged.json").exists() else {"terms": []}
    names = [t["name"] for t in merged.get("terms", [])]
    bk = HERE / "board_keywords.json"
    if bk.exists():
        names = [k["phrase"] for k in json.loads(bk.read_text())] + names
    names = list(dict.fromkeys(names))
    out, kws, errs = {"date": a.date}, [], []
    for key, fn in (("ac", lambda: autocomplete(names)), ("trends", lambda: trends(state)),
                    ("appstore", lambda: appstore(state)), ("hn", hn)):
        if key in skip:
            continue
        try:
            r, k = fn()
            out[key] = r; kws += k
        except Exception as e:
            errs.append(f"{key}: {type(e).__name__}: {e}")
    uniq = {}
    for k in kws:
        uniq.setdefault(k["phrase"], k)
    # 每个来源轮流取，工具意图词优先，避免补全长尾占满名额
    by = {}
    for k in sorted(uniq.values(), key=lambda k: not TOOL_RE.search(k["phrase"])):
        by.setdefault(k["source"], []).append(k)
    kws = []
    while any(by.values()) and len(kws) < CFG["max_keywords"]:
        for src in list(by):
            if by[src] and len(kws) < CFG["max_keywords"]:
                kws.append(by[src].pop(0))
    out.update(errors=errs, spent_micros=SPENT[0], keywords=kws)
    sp.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    (HERE / "finders.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (HERE / "finder_keywords.json").write_text(json.dumps(kws, ensure_ascii=False, indent=1))
    L = [f"## 找词方法（{a.date}）", ""]
    if "ac" in out:
        has = [x for x in out["ac"] if x["tails"]]
        L.append(f"- Google 补全：查了 {len(out['ac'])} 个名字，{len(has)} 个有长尾：" + "；".join(f"{x['name']}（{len(x['tails'])} 条，YT {len(x['yt'])}）" for x in has))
    if "trends" in out:
        t = out["trends"]
        L.append(f"- Google Trends：RSS {len(t['rss'])} 条，类目上升 " + "、".join(f"{k}:{len(v)}" for k, v in t["rising"].items())
                 + f"；12 个月内新出现的 {len(t['fresh'])} 个：" + "、".join(f["term"] for f in t["fresh"]))
        if t["errors"]:
            L.append("  - 问题：" + "；".join(t["errors"]))
    if "appstore" in out:
        s = out["appstore"]
        L.append(f"- App Store 免费榜：" + ("首次建档（只报 90 天内上架的）；" if s["first_run"] else "") + f"新上榜 {len(s['new'])} 个："
                 + "、".join(f"{n['name']}（#{n['rank']}）" for n in s["new"]))
    if "hn" in out:
        L.append(f"- Hacker News 24 小时：{len(out['hn'])} 帖：" + "；".join(f"[{h['title']}]({h['url']}) {h['points']} 分" for h in out["hn"][:8]))
    L.append(f"- 送去 Semrush 的候选词 {len(kws)} 个。本步 AIsa 花费 ${SPENT[0]/1e6:.3f}。")
    if errs:
        L.append("- 出错：" + "；".join(errs))
    (HERE / "finders.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
