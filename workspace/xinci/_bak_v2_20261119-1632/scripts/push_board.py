#!/usr/bin/env python3
"""merged.json + doable.json + board_keywords.json -> board radar payload (label 'YYYY-MM-DD 新词雷达'), push via /workspace/xbm/board_client.py.

keywords feed /radar/new: doable passed first, then board_keywords (书签X → 游戏轨 → AI工具轨 → 新闻轨 → 热梗轨 → others), ~40 cap.
新闻轨最多 8 个、热梗轨最多 6 个关键词，只填主轨（书签X/游戏轨/AI工具轨）用剩的名额，不挤占主轨。
Derived track suffixes unblocked/online/play/alternative are dropped when a cleaner base phrase exists; `{name} AI` is kept.
"""
import argparse, json, re, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
from merge_board import norm

SOURCE_ORDER = ("书签X", "游戏轨", "AI工具轨", "新闻轨", "热梗轨")
SOURCE_TAG = {"书签X": "【书签X】", "游戏轨": "【游戏轨】", "AI工具轨": "【AI工具轨】", "新闻轨": "【新闻轨】", "热梗轨": "【热梗轨】"}
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

    # 1) doable passed first (existing fmtv + score)
    passed = [t for t in dj.get("terms") or [] if not t.get("failed") and not t.get("unknown")]
    passed.sort(key=lambda t: -t.get("score", 0))
    for t in passed:
        why = fmtv(t) + f"，信心分 {t.get('score')}"
        if t.get("names"):
            why += f"；来自 {'、'.join(t['names'])}"
        add_kw(t["phrase"], why, names=t.get("names") or [], evidence=t.get("evidence", ""), source=t.get("source", ""))

    # 2) board_keywords：先填主轨（书签X → 游戏轨 → AI工具轨），再用剩余名额填新闻轨 / 热梗轨。
    # 不预留、不挤占主轨；新闻轨最多 8、热梗轨最多 6。主轨已满时补充轨 keywords 可能为 0，但 items 仍在列表里。
    filtered = filter_derived(board_kw)

    def _src(e):
        return e.get("source") or ""

    def _add_entry(e):
        src = _src(e)
        tag = SOURCE_TAG.get(src, f"【{src}】" if src else "【其他】")
        evidence = (e.get("evidence") or "").strip()
        reason = tag + (evidence or (e.get("reason") or "").strip() or e.get("phrase", ""))
        return add_kw(e.get("phrase"), reason, names=e.get("names") or [], evidence=evidence, source=src)

    other_list = [e for e in filtered if not is_supp_source(_src(e))]
    supp_list = [e for e in filtered if is_supp_source(_src(e))]
    other_list.sort(key=lambda e: (source_rank(_src(e)), board_kw.index(e) if e in board_kw else 0))
    supp_list.sort(key=lambda e: (source_rank(_src(e)), board_kw.index(e) if e in board_kw else 0))

    for e in other_list:
        if len(keywords) >= KW_CAP:
            break
        _add_entry(e)

    added_by = {k: 0 for k in SUPP_CAPS}
    for e in supp_list:
        if len(keywords) >= KW_CAP:
            break
        primary = _src(e).split("/")[0]
        cap = SUPP_CAPS.get(primary, 0)
        if added_by.get(primary, 0) >= cap:
            continue
        if _add_entry(e):
            added_by[primary] = added_by.get(primary, 0) + 1

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
