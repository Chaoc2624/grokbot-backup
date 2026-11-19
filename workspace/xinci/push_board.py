#!/usr/bin/env python3
"""merged.json + doable.json + board_keywords.json -> board radar payload (label 'YYYY-MM-DD 新词雷达'), push via /workspace/xbm/board_client.py.

keywords feed /radar/new: cap 40; 游戏最多预留 10、视频/热梗最多预留 10（不够留空）；视频有合格条目时不能被 AI 工具挤为 0。
书签X 只保留少量最高价值（最多 5）。立项通过词可补剩余名额但不能挤掉视频预留。
Derived track suffixes unblocked/online/play/alternative are dropped when a cleaner base phrase exists; `{name} AI` is kept.
"""
import argparse, json, re, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import os as _os
HERE = Path(_os.environ["XINCI_HOME"]) if _os.environ.get("XINCI_HOME") else Path(__file__).resolve().parent
from merge_board import norm
import sys
sys.path.insert(0, str(HERE))
from v2.select_keywords import select_board_keywords

SOURCE_ORDER = ("书签X", "游戏轨", "AI工具轨", "新闻轨", "热梗轨")
SOURCE_TAG = {"书签X": "【书签X】", "游戏轨": "【游戏轨】", "AI工具轨": "【AI工具轨】", "新闻轨": "【新闻轨】", "热梗轨": "【热梗轨】", "Higgsfield": "【Higgsfield】"}
NEWS_KW_CAP = 8
MEME_KW_CAP = 6
SUPP_CAPS = {"新闻轨": NEWS_KW_CAP, "热梗轨": MEME_KW_CAP}
DERIVED_SUF = re.compile(r"^(?P<base>.+?)\s+(unblocked|online|play|alternative)$", re.I)
KW_CAP = 40


def fmtv(t):
    v, kd, cpc = t.get("volume"), t.get("kd"), t.get("cpc")
    comp = t.get("verdict") or "—"
    comp = {"open": "能进", "crowded": "挤满"}.get(comp, comp)
    return f"月搜 {v if v is not None else '—'}、KD {kd if kd is not None else '—'}、CPC ${cpc if cpc is not None else '—'}、首页竞争「{comp}」（Semrush 美国库）"


def source_rank(src):
    try:
        return SOURCE_ORDER.index(src)
    except ValueError:
        return len(SOURCE_ORDER)


def is_supp_source(src):
    primary = (src or "").split("/")[0]
    return primary in SUPP_CAPS


def filter_derived(entries):
    """Drop unblocked/online/play/alternative when a cleaner base phrase exists in the same list."""
    phrases = {e.get("phrase") or "" for e in entries}
    out = []
    for e in entries:
        p = (e.get("phrase") or "").strip()
        if not p:
            continue
        m = DERIVED_SUF.match(p)
        if m and m.group("base") in phrases:
            continue
        out.append(e)
    return out


def attach_keyword(by, items, phrase, names, reason, rank, evidence="", source=""):
    """Stamp keyword_rank/keyword/reason onto a matching merged item, or append a synthetic one."""
    keys = [phrase] + list(names or [])
    tgt = next((by[norm(n)] for n in keys if n and norm(n) in by), None)
    if tgt is None:
        tgt = {
            "name": phrase,
            "desc": (evidence or reason or "")[:300],
            "source": source or "",
            "url": "",
            "first_seen": items[0]["first_seen"] if items else "",
        }
        items.append(tgt)
        by[norm(phrase)] = tgt
    # Only set rank fields once so earlier (higher-priority) keywords keep the item highlight.
    if tgt.get("keyword_rank") is None:
        tgt.update(keyword_rank=rank, keyword=phrase, reason=reason)
    return tgt


def main():
    now = datetime.now(timezone(timedelta(hours=8)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=now.strftime("%Y-%m-%d"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    m = json.loads((HERE / "merged.json").read_text())
    if m["date"] != a.date:
        sys.exit(f"merged.json is for {m['date']}, not {a.date}; run merge_board.py --date {a.date} first")
    dj = json.loads((HERE / "doable.json").read_text()) if (HERE / "doable.json").exists() else {"terms": []}
    bk_path = HERE / "board_keywords.json"
    board_kw = json.loads(bk_path.read_text()) if bk_path.exists() else []
    if not isinstance(board_kw, list):
        board_kw = []

    items, by = [], {}
    for t in m["terms"]:
        b = t.get("board") or {}
        it = {
            "name": t["name"],
            "desc": (t["desc"] or "；".join(t["signals"]))[:300],
            "source": " / ".join(t["sources"]) + (f"（{b['source']}）" if b.get("source") else ""),
            "url": t["url"],
            "first_seen": b.get("first_seen") or a.date,
        }
        items.append(it)
        by[t["key"]] = it

    seen = set()  # norm(phrase)
    keywords = []

    def add_kw(phrase, reason, names=None, evidence="", source=""):
        p = (phrase or "").strip()
        if not p:
            return False
        k = norm(p)
        if not k or k in seen:
            return False
        if len(keywords) >= KW_CAP:
            return False
        seen.add(k)
        rank = len(keywords) + 1
        attach_keyword(by, items, p, names or [p], reason, rank, evidence=evidence, source=source)
        keywords.append({"keyword": p, "reason": reason})
        return True

    # 1) board keywords with v2 reserves (game<=10, video<=10, x<=5). Do not pad.
    filtered = filter_derived(board_kw)
    selected = select_board_keywords(filtered, cap=KW_CAP, game_reserve=10, video_reserve=10, x_max=5)

    def _src(e):
        return e.get("source") or ""

    def _add_entry(e):
        src = _src(e)
        tag = SOURCE_TAG.get(src, f"【{src}】" if src else "【其他】")
        evidence = (e.get("evidence") or "").strip()
        reason = tag + (evidence or (e.get("reason") or "").strip() or e.get("phrase", ""))
        return add_kw(e.get("phrase"), reason, names=e.get("names") or [], evidence=evidence, source=src)

    for e in selected:
        _add_entry(e)

    # 2) doable passed may fill leftover slots only; never evict reserved video/game already added
    passed = [t for t in dj.get("terms") or [] if not t.get("failed") and not t.get("unknown") and t.get("passed_立项") or (
        (not t.get("failed") and not t.get("unknown") and not t.get("nodata") and t.get("volume") is not None and t.get("kd") is not None
         and t.get("volume") >= 500 and t.get("kd") <= 31 and t.get("cpc") is not None)
    )]
    # Safer: only terms explicitly marked passed if present, else classic checks without treating None as 0
    passed = []
    for t0 in dj.get("terms") or []:
        if t0.get("failed") or t0.get("unknown") or t0.get("nodata"):
            continue
        vol, kd, cpc = t0.get("volume"), t0.get("kd"), t0.get("cpc")
        if vol is None or kd is None or cpc is None:
            continue
        if vol >= 500 and kd <= 31:
            passed.append(t0)
    passed.sort(key=lambda t0: -t0.get("score", 0))
    for t0 in passed:
        if len(keywords) >= KW_CAP:
            break
        why = fmtv(t0) + f"，信心分 {t0.get('score')}"
        if t0.get("names"):
            why += f"；来自 {'、'.join(t0['names'])}"
        add_kw(t0["phrase"], why, names=t0.get("names") or [], evidence=t0.get("evidence", ""), source=t0.get("source", ""))

        items.sort(key=lambda i: (i.get("keyword_rank") or 999))
    p = {
        "label": f"{a.date} 新词雷达",
        "run_at": now.strftime("%Y-%m-%d %H:%M"),
        "window_start": f"{a.date} 00:00",
        "window_end": f"{a.date} 23:59",
        "empty": not items,
        "items": items,
        "keywords": keywords,
    }
    out = HERE / "board_payload.json"
    out.write_text(json.dumps(p, ensure_ascii=False, indent=1))
    kw_names = [k["keyword"] for k in keywords]
    def _count(label):
        items_n = sum(1 for i in items if label in (i.get("source") or ""))
        kws_n = sum(1 for k in keywords if f"【{label}】" in (k.get("reason") or ""))
        names = [k["keyword"] for k in keywords if f"【{label}】" in (k.get("reason") or "")]
        return items_n, kws_n, names
    news_items, news_kws, news_kw_names = _count("新闻轨")
    meme_items, meme_kws, meme_kw_names = _count("热梗轨")
    print(f"label={p['label']} items={len(items)} keywords={len(keywords)} x_failed={m['our_x_failed']} news_items={news_items} news_keywords={news_kws} meme_items={meme_items} meme_keywords={meme_kws}")
    print("keywords_first15=" + json.dumps(kw_names[:15], ensure_ascii=False))
    print("news_keywords=" + json.dumps(news_kw_names, ensure_ascii=False))
    print("meme_keywords=" + json.dumps(meme_kw_names, ensure_ascii=False))
    if a.dry_run:
        print("dry-run, not pushed:", out)
        return
    r = subprocess.run(["python3", "/workspace/xbm/board_client.py", "radar", str(out)], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[-500:])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
