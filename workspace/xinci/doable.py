#!/usr/bin/env python3
"""可做的词: post-step for the nightly new-term-radar report.

Reads report.json, takes the generic (non-branded, no ⚠) terms from the keyword table plus
any 🔎 related queries / long tails, fetches Semrush (US) volume + CPC + KD through AIsa,
checks page one (reuses report.json `competition`, else one cheap DataForSEO SERP read for
terms that already clear volume + CPC), and writes doable.md / doable.json.

Run after `python3 -m radar daily`:
    python3 /workspace/xinci/doable.py [--report PATH] [--out PATH] [--terms "a;b"] [--dry-run]

Thresholds live in doable_config.json next to this file (defaults below).
Per-keyword results are cached 7 days in doable_cache.json. Spend is capped per run.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE / "repo"
sys.path.insert(0, str(REPO))

DEFAULTS = {
    "min_volume": 500,        # 月搜 >= this
    "max_kd": 15,             # Semrush KD <= this
    "min_cpc": 0.01,          # CPC must be present and >= this (USD)
    "need_open_serp": True,   # 首页竞争 must be 能进 (open)
    "database": "us",
    "max_terms": 40,
    "max_spend_usd": 0.50,
    "cache_days": 7,
    "serp_fetch": True,       # read page one ($0.002) for terms with no competition data that pass volume+CPC
    "serp_location_code": 2840,
    # 2026-10-22 筛词升级
    "kd_min_volume": 100,       # 月搜低于此不再花钱查 KD（预筛）
    "max_allintitle": 10000,    # allintitle 结果数上限
    "check_allintitle": True,   # 对过了月搜+CPC 的词查 allintitle（DataForSEO SERP，经 AIsa）
    "need_small_sites": False,  # True 时「首页小站居多」也算门槛；默认只展示
    "small_sites_min": 5,       # 首页前 10 里非大站 >= 此数算小站居多
    "tool_intent_bonus": 15,
}
TOOL_INTENT = __import__("re").compile(r"\b(generator|converter|maker|checker|editor|creator|detector|remover|downloader|translator|calculator|upscaler)\b", __import__("re").I)
BIG = ("wikipedia.org", "youtube.com", "reddit.com", "amazon.com", "github.com", "google.com", "apple.com", "microsoft.com",
       "facebook.com", "x.com", "twitter.com", "linkedin.com", "medium.com", "quora.com", "forbes.com", "nytimes.com",
       "cnn.com", "bbc.com", "theverge.com", "techcrunch.com", "instagram.com", "tiktok.com", "huggingface.co",
       "openai.com", "anthropic.com", "adobe.com", "canva.com", "zapier.com", "g2.com", "capterra.com", "pcmag.com",
       "cnet.com", "wired.com", "nvidia.com", "meta.com", "ibm.com", "aws.amazon.com", "yahoo.com", "ebay.com", "walmart.com")
PRICE = {"overview": 1000, "kd": 5000, "serp": 2000}   # micro-USD estimates, per keyword
OVERVIEW = "get_semrush_keyword_overview"
KD = "get_semrush_keyword_difficulty"
VERDICT_ZH = {"open": "能进", "mixed": "一般", "crowded": "挤满", None: "未查"}
KIND_ZH = {"tool": "工具", "list": "榜单", "article": "文章", "video": "视频", "forum": "论坛"}


def load_env():
    if os.environ.get("AISA_API_KEY"):
        return
    env = HERE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip().removeprefix("export ").strip(), v.strip().strip('"').strip("'"))


def config() -> dict:
    cfg = dict(DEFAULTS)
    p = HERE / "doable_config.json"
    if p.exists():
        cfg.update(json.loads(p.read_text()))
    return cfg


# ---------- collect ----------
def collect(report: dict, extra: list[str], cap: int) -> list[dict]:
    kw = report.get("keywords") or {}
    out: dict[str, dict] = {}

    def add(phrase: str, **info):
        p = " ".join((phrase or "").lower().split())
        if p and p not in out:
            out[p] = {"phrase": p, **info}

    for r in kw.get("rows", []):
        if r.get("kind") != "generic" or r.get("brand"):
            continue   # names and ⚠ branded terms are left to the user
        src = "🔎 相关查询" if r.get("source") == "searched" else "模型提取"
        add(r["phrase"], source=src, names=r.get("names") or [], evidence=r.get("evidence") or "",
            competition=r.get("competition"), radar_volume=r.get("volume"), decision=r.get("decision"))
    # kw["tails"] are the name's own long tails ("photocraft download"): branded, left out.
    for t in extra:
        if isinstance(t, dict):
            add(t.get("phrase", ""), source=t.get("source") or "看板X", names=t.get("names") or [],
                evidence=t.get("evidence") or "")
        else:
            add(t, source="手动", names=[], evidence="")
    return list(out.values())[:cap]


# ---------- cache ----------
def load_cache(days: int) -> dict:
    p = HERE / "doable_cache.json"
    if not p.exists():
        return {}
    held = json.loads(p.read_text())
    today = date.today()
    return {k: v for k, v in held.items() if (today - date.fromisoformat(v["day"])).days < days}


def save_cache(cache: dict):
    (HERE / "doable_cache.json").write_text(json.dumps(cache, ensure_ascii=False, indent=1))


# ---------- fetch ----------
class Budget:
    def __init__(self, cap_usd: float):
        self.cap = int(cap_usd * 1_000_000)
        self.spent = 0
        self.skipped: list[str] = []

    def allows(self, estimate: int) -> bool:
        return self.spent + estimate <= self.cap


def parse_csv(text) -> list[dict]:
    if not isinstance(text, str) or ";" not in text:
        return []
    lines = [l for l in text.replace("\r", "").split("\n") if l.strip()]
    head = lines[0].split(";")
    return [dict(zip(head, l.split(";"))) for l in lines[1:]]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fetch_semrush(phrases: list[str], cfg: dict, budget: Budget, errors: list[str]) -> dict[str, dict]:
    from radar import aisa
    got: dict[str, dict] = {p: {} for p in phrases}
    # overview: one call per phrase, batches of 20
    for i in range(0, len(phrases), 20):
        chunk = phrases[i:i + 20]
        if not budget.allows(PRICE["overview"] * len(chunk)):
            budget.skipped += [f"overview:{p}" for p in chunk]
            continue
        calls = [{"call_id": f"o{j}", "tool": OVERVIEW, "arguments": {"phrase": p, "database": cfg["database"]}}
                 for j, p in enumerate(chunk)]
        try:
            data, cost = aisa.call(calls)
            budget.spent += cost
        except aisa.AisaError as exc:
            errors.append(f"Semrush 概览: {exc}")
            continue
        for j, p in enumerate(chunk):
            rows = parse_csv(data.get(f"o{j}"))
            row = next((r for r in rows if r.get("Keyword", "").lower() == p), rows[0] if rows else None)
            got[p]["overview_ok"] = True
            if row:
                got[p].update(volume=int(num(row.get("Search Volume")) or 0), cpc=num(row.get("CPC")),
                              comp=num(row.get("Competition")), results=int(num(row.get("Number of Results")) or 0))
            else:
                got[p].update(volume=0, cpc=None, comp=None, nodata=True)
    # KD: one call per 20 phrases, billed per phrase
    kd_need = []
    for p in phrases:
        if got[p].get("overview_ok") and (got[p].get("volume") or 0) < cfg.get("kd_min_volume", 0):
            got[p].update(kd_ok=True, kd=None, kd_skipped=True)
        else:
            kd_need.append(p)
    for i in range(0, len(kd_need), 20):
        chunk = kd_need[i:i + 20]
        if not budget.allows(PRICE["kd"] * len(chunk)):
            budget.skipped += [f"kd:{p}" for p in chunk]
            continue
        try:
            data, cost = aisa.call([{"call_id": "k", "tool": KD, "arguments": {"phrase": ";".join(chunk), "database": cfg["database"]}}])
            budget.spent += cost
        except aisa.AisaError as exc:
            errors.append(f"Semrush KD: {exc}")
            continue
        kds = {r.get("Keyword", "").lower(): num(r.get("Keyword Difficulty Index")) for r in parse_csv(data.get("k"))}
        for p in chunk:
            got[p]["kd_ok"] = True
            got[p]["kd"] = None if kds.get(p) is None else int(kds[p])
    return got


def serp_check(phrase: str, cfg: dict, budget: Budget, errors: list[str]) -> dict | None:
    from radar import aisa, competition
    if not budget.allows(PRICE["serp"]):
        budget.skipped.append(f"serp:{phrase}")
        return None
    try:
        page, cost = competition.page_one(phrase, cfg["serp_location_code"])
        budget.spent += cost
    except aisa.AisaError as exc:
        errors.append(f"首页 {phrase}: {exc}")
        return None
    kinds: dict[str, int] = {}
    for x in page["results"]:
        kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
    return {"kinds": kinds, "ads": page["ads"], "features": page["features"],
            "top": [x["domain"] for x in page["results"][:10]], "source": "serp"}


def allintitle(phrase: str, cfg: dict, budget: Budget, errors: list[str]):
    from radar import aisa
    if not budget.allows(PRICE["serp"] * 5):
        budget.skipped.append(f"allintitle:{phrase}")
        return None
    try:
        data, cost = aisa.call([{"call_id": "a", "tool": "post_dataforseo_serp_google_organic_live", "arguments": {"body": [{
            "keyword": f"allintitle:{phrase}", "location_code": cfg["serp_location_code"], "language_code": "en", "depth": 10}]}}])
        budget.spent += cost
    except aisa.AisaError as exc:
        errors.append(f"allintitle {phrase}: {exc}")
        return None
    res = (((data.get("a") or {}).get("tasks") or [{}])[0].get("result") or [{}])[0]
    return res.get("se_results_count")


def small_sites(serp: dict) -> int | None:
    top = serp.get("top") or []
    if not top:
        return None
    return sum(1 for d in top if not any(d == b or d.endswith("." + b) for b in BIG))


def kdroi(t: dict) -> float | None:
    if not t.get("volume") or t.get("cpc") is None:
        return None
    return round(t["volume"] * t["cpc"] / max(t.get("kd") or 1, 1), 1)


def serp_verdict(serp: dict, kd) -> str:
    """No GoAnyAPI site ratings: count forum + video results as the soft slots a new site can take."""
    soft = (serp["kinds"].get("forum", 0) + serp["kinds"].get("video", 0))
    serp["soft_weak"] = soft
    if soft >= 3 or (kd is not None and kd <= 15):
        return "open"
    if soft == 0 and (kd is None or kd >= 40):
        return "crowded"
    return "mixed"


# ---------- judge ----------
def checks(t: dict, cfg: dict) -> dict[str, bool | None]:
    vol, kd, cpc = t.get("volume"), t.get("kd"), t.get("cpc")
    c = {
        "月搜": None if vol is None else vol >= cfg["min_volume"],
        "KD": None if kd is None else kd <= cfg["max_kd"],
        "CPC": None if not t.get("overview_ok") else (cpc is not None and cpc >= cfg["min_cpc"]),
    }
    if cfg["need_open_serp"]:
        c["首页竞争"] = None if t.get("verdict") is None else t["verdict"] == "open"
    if cfg.get("check_allintitle"):
        c["allintitle"] = None if t.get("allintitle") is None else t["allintitle"] < cfg["max_allintitle"]
    if cfg.get("need_small_sites"):
        c["小站居多"] = None if t.get("small_sites") is None else t["small_sites"] >= cfg["small_sites_min"]
    return c


def score(t: dict, cfg: dict) -> int:
    """0-100 confidence: volume headroom, KD headroom, CPC, page-one openness, evidence."""
    s = 0
    vol = t.get("volume") or 0
    s += min(30, int(30 * vol / max(1, cfg["min_volume"] * 4)))
    kd = t.get("kd")
    if kd is not None:
        s += max(0, int(25 * (1 - kd / 100)))
    cpc = t.get("cpc") or 0
    s += min(15, int(cpc * 5))
    s += {"open": 20, "mixed": 8}.get(t.get("verdict"), 0)
    s += 10 if t.get("evidence") else 0
    s += cfg.get("tool_intent_bonus", 0) if t.get("tool_intent") else 0
    return min(100, s)


def fmt(v, kind):
    if v is None:
        return "—"
    if kind == "cpc":
        return f"${v:.2f}"
    if kind == "n":
        return f"{v:,}" if isinstance(v, (int, float)) else str(v)
    if kind == "vol":
        return f"{v:,}"
    return str(v)


def comp_note(t: dict) -> str:
    v = VERDICT_ZH.get(t.get("verdict"), "未查")
    c = t.get("comp_detail") or {}
    kinds = c.get("kinds") or {}
    parts = [f"{KIND_ZH.get(k, k)}{n}" for k, n in sorted(kinds.items(), key=lambda x: -x[1])]
    extra = []
    if c.get("weak") is not None:
        extra.append(f"弱站 {c['weak']}")
    elif c.get("soft_weak") is not None:
        extra.append(f"论坛/视频位 {c['soft_weak']}")
    if c.get("ads"):
        extra.append("有广告")
    detail = "、".join(parts + extra)
    return f"{v}（{detail}）" if detail else v


def source_note(t: dict) -> str:
    bits = [t.get("source", "")]
    if t.get("names"):
        bits.append("来自 " + "、".join(t["names"]))
    s = "，".join(b for b in bits if b)
    if t.get("evidence"):
        ev = t["evidence"].replace("|", "/")
        s += f"：“{ev[:90]}{'…' if len(ev) > 90 else ''}”"
    return s


def render(terms: list[dict], cfg: dict, budget: Budget, errors: list[str], report_day: str, cached: int) -> str:
    passed, near, rest = [], [], []
    for t in terms:
        c = t["checks"]
        failed = [k for k, ok in c.items() if ok is False]
        unknown = [k for k, ok in c.items() if ok is None]
        t["failed"], t["unknown"] = failed, unknown
        if not failed and not unknown:
            passed.append(t)
        elif len(failed) + len(unknown) == 1:
            near.append(t)
        else:
            rest.append(t)
    key = lambda t: (not t.get("tool_intent"), -(t.get("kdroi") or 0), -t["score"])
    passed.sort(key=key)
    near.sort(key=key)
    rest.sort(key=key)
    th = f"月搜 ≥ {cfg['min_volume']:,}、KD ≤ {cfg['max_kd']}、CPC 有值" + ("、首页竞争「能进」" if cfg["need_open_serp"] else "") + (f"、allintitle < {cfg['max_allintitle']:,}" if cfg.get("check_allintitle") else "") + "；按 KDROI（月搜×CPC÷KD）排序，🛠 工具意图词优先"
    L = [f"## 可做的词（{report_day}）", "", f"门槛：{th}。只看不带品牌的通用词（⚠ 品牌词留给你判断），数据来自 Semrush 美国库。共查 {len(terms)} 个词。", ""]
    L.append(f"### 全过门槛的词（{len(passed)}）")
    if passed:
        L += ["", "| 词 | 月搜 | KD | CPC | KDROI | allintitle | 小站/10 | 首页竞争 | 信心分 | 依据/来源 |", "|---|---|---|---|---|---|---|---|---|---|"]
        for t in passed:
            L.append(f"| **{t['phrase']}** | {fmt(t.get('volume'),'vol')} | {fmt(t.get('kd'),'kd')} | {fmt(t.get('cpc'),'cpc')} | {fmt(t.get('kdroi'),'n')}{' 🛠' if t.get('tool_intent') else ''} | {fmt(t.get('allintitle'),'vol')} | {fmt(t.get('small_sites'),'n')} | {comp_note(t)} | {t['score']} | {source_note(t)} |")
    else:
        L += ["", "今天没有词全过门槛。"]
    L += ["", f"### 差一点就过的词（{len(near)}）"]
    if near:
        L += ["", "| 词 | 月搜 | KD | CPC | KDROI | allintitle | 小站/10 | 首页竞争 | 卡在哪 | 依据/来源 |", "|---|---|---|---|---|---|---|---|---|---|"]
        for t in near:
            why = "、".join([f"{k}没过" for k in t["failed"]] + [f"{k}没数据" for k in t["unknown"]])
            L.append(f"| {t['phrase']} | {fmt(t.get('volume'),'vol')} | {fmt(t.get('kd'),'kd')} | {fmt(t.get('cpc'),'cpc')} | {fmt(t.get('kdroi'),'n')}{' 🛠' if t.get('tool_intent') else ''} | {fmt(t.get('allintitle'),'vol')} | {fmt(t.get('small_sites'),'n')} | {comp_note(t)} | {why} | {source_note(t)} |")
    else:
        L += ["", "没有只差一项的词。"]
    if rest:
        L += ["", "其余（两项以上没过）：" + "；".join(
            f"{t['phrase']}（月搜 {fmt(t.get('volume'),'vol')}，KDROI {fmt(t.get('kdroi'),'n')}，KD {fmt(t.get('kd'),'kd')}，CPC {fmt(t.get('cpc'),'cpc')}；卡在 " + "、".join(t['failed'] + [k + '没数据' for k in t['unknown']]) + "）" for t in rest)]
    L += ["", f"花费：本次 AIsa 约 ${budget.spent/1e6:.3f}（上限 ${budget.cap/1e6:.2f}），{cached} 个词用了 7 天内缓存没再付费。"]
    if budget.skipped:
        L.append(f"因上限跳过 {len(budget.skipped)} 次查询。")
    if errors:
        L.append("接口问题：" + "；".join(errors))
    L.append("注：KD 用的是 Semrush 指数，和雷达新词表里 DataForSEO 的 KD 口径不同，同一个词 Semrush 通常更高。")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=str(HERE / "report.json"))
    ap.add_argument("--out", default=str(HERE / "doable.md"))
    ap.add_argument("--terms", default="", help="extra terms, ';'-separated")
    ap.add_argument("--extra-file", default="", help="JSON list of {phrase,source,names,evidence} (e.g. board_keywords.json from merge_board.py)")
    ap.add_argument("--dry-run", action="store_true", help="collect and show terms, spend nothing")
    a = ap.parse_args()
    load_env()
    cfg = config()
    report = json.loads(Path(a.report).read_text())
    report_day = datetime.fromtimestamp(Path(a.report).stat().st_mtime).strftime("%Y-%m-%d")
    extra = [t for t in a.terms.split(";") if t.strip()]
    for ef in [x for x in a.extra_file.split(",") if x.strip()]:
        if Path(ef).exists():
            extra += json.loads(Path(ef).read_text())
    terms = collect(report, extra, cfg["max_terms"])
    if a.dry_run:
        print(json.dumps([t["phrase"] for t in terms], ensure_ascii=False))
        return
    budget, errors = Budget(cfg["max_spend_usd"]), []
    cache = load_cache(cfg["cache_days"])
    todo = [t["phrase"] for t in terms if t["phrase"] not in cache]
    cached = len(terms) - len(todo)
    if todo:
        fetched = fetch_semrush(todo, cfg, budget, errors)
        for p, v in fetched.items():
            if v.get("overview_ok") and v.get("kd_ok"):
                cache[p] = {**v, "day": date.today().isoformat()}
            terms_by = next(t for t in terms if t["phrase"] == p)
            terms_by.update(v)
    for t in terms:
        if t["phrase"] in cache:
            t.update({k: v for k, v in cache[t["phrase"]].items() if k not in ("day", "serp", "allintitle")})
    # page one: reuse the radar's verdict, else cached/new SERP read for terms clearing volume + CPC
    for t in terms:
        comp = t.get("competition")
        if comp and comp.get("verdict"):
            t["verdict"], t["comp_detail"] = comp["verdict"], comp
            continue
        pre = (t.get("volume") or 0) >= cfg["min_volume"] and (t.get("cpc") or 0) >= cfg["min_cpc"]
        serp = (cache.get(t["phrase"]) or {}).get("serp")
        if serp is None and pre and cfg["serp_fetch"]:
            serp = serp_check(t["phrase"], cfg, budget, errors)
            if serp and t["phrase"] in cache:
                cache[t["phrase"]]["serp"] = serp
        if serp:
            t["verdict"], t["comp_detail"] = serp_verdict(serp, t.get("kd")), serp
        else:
            t["verdict"] = None
    for t in terms:
        t["tool_intent"] = bool(TOOL_INTENT.search(t["phrase"]))
        t["kdroi"] = kdroi(t)
        if t.get("comp_detail") and t["comp_detail"].get("top"):
            t["small_sites"] = small_sites(t["comp_detail"])
        pre = (t.get("volume") or 0) >= cfg["min_volume"] and (t.get("cpc") or 0) >= cfg["min_cpc"]
        c = cache.get(t["phrase"]) or {}
        if "allintitle" in c:
            t["allintitle"] = c["allintitle"]
        elif pre and cfg.get("check_allintitle"):
            t["allintitle"] = allintitle(t["phrase"], cfg, budget, errors)
            if t["allintitle"] is not None and t["phrase"] in cache:
                cache[t["phrase"]]["allintitle"] = t["allintitle"]
    for t in terms:
        t["checks"] = checks(t, cfg)
        t["score"] = score(t, cfg)
    save_cache(cache)
    md = render(terms, cfg, budget, errors, report_day, cached)
    Path(a.out).write_text(md)
    Path(a.out).with_suffix(".json").write_text(json.dumps(
        {"day": report_day, "config": cfg, "terms": terms, "spent_micros": budget.spent, "errors": errors,
         "skipped": budget.skipped}, ensure_ascii=False, indent=1, default=str))
    with open(HERE / "doable.log", "a") as f:
        f.write(json.dumps({"at": datetime.now().isoformat(timespec="seconds"), "report": a.report, "terms": len(terms),
                            "queried": len(todo), "cached": cached, "spent_usd": round(budget.spent / 1e6, 4),
                            "errors": errors, "skipped": len(budget.skipped)}, ensure_ascii=False) + "\n")
    print(md)


if __name__ == "__main__":
    main()
