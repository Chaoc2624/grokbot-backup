#!/usr/bin/env python3
"""Merge the board radar (X 书签助手: /workspace/xbm/radar-YYYYMMDD-{am,pm}.json) with our report.json.
Out: merged.json, merged.md, board_keywords.json (extra input for doable.py --extra-file). Read-only on /workspace/xbm."""
import argparse, json, re, unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
XBM = Path("/workspace/xbm")
KIND = {"x": "我们X", "hf": "HF", "breakout": "GitHub", "sitemap": "竞品站"}

def norm(s):
    s = re.sub(r"[（(【\[].*?[）)】\]]", "", s or "")
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"[\W_]+", "", s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"))
    ap.add_argument("--report", default=str(HERE / "report.json"))
    a = ap.parse_args()
    d = a.date.replace("-", "")
    report = json.loads(Path(a.report).read_text())
    terms, idx = [], {}
    def get(name):
        k = norm(name)
        if not k: return None
        if k not in idx:
            idx[k] = {"name": name, "key": k, "sources": [], "desc": "", "url": "", "signals": [], "variants": []}
            terms.append(idx[k])
        return idx[k]
    # ours
    for l in report.get("leads", []):
        t = get(l["term"])
        for kd in l.get("kinds", []):
            s = KIND.get(kd, kd)
            if s not in t["sources"]: t["sources"].append(s)
        t["signals"] += l.get("signals", [])
        t["desc"] = t["desc"] or "；".join(l.get("examples", [])[:1])
        if l.get("repo"): t["url"] = t["url"] or f"https://github.com/{l['repo']}"
        t["named"] = l.get("named")
        for v in l.get("variants", []):  # map variants onto same term
            idx.setdefault(norm(v), t)
    # board
    board_runs, board_kw, dupes = [], [], []
    for half in ("am", "pm"):
        p = XBM / f"radar-{d}-{half}.json"
        if not p.exists(): continue
        run = json.loads(p.read_text()); board_runs.append(run["label"])
        for it in run.get("items", []):
            k = norm(it["name"]); existed = k in idx
            t = get(it["name"])
            if existed and "看板X" not in t["sources"]:
                dupes.append({"name": it["name"], "matched": t["name"], "ours": list(t["sources"])})
            if "看板X" not in t["sources"]: t["sources"].append("看板X")
            if not t.get("board"):
                t["board"] = {k2: it.get(k2) for k2 in ("name", "source", "url", "first_seen", "keyword_rank", "keyword", "reason")}
                t["desc"] = it.get("desc") or t["desc"]
                t["url"] = it.get("url") or t["url"]
            if it.get("keyword"): board_kw.append((it["keyword"], it["name"], it.get("reason", "")))
        for kw in run.get("keywords", []):
            board_kw.append((kw["keyword"], "", kw.get("reason", "")))
        if not any(i.get("keyword") for i in run.get("items", [])) and not run.get("keywords"):
            board_kw += [(re.sub(r"[（(【].*$", "", i["name"]).strip(), i["name"], "") for i in run.get("items", [])]
    # our free X scan (XSCAN.md): xnew-YYYYMMDD-{am,pm}.json, label 书签X
    xnew_runs = []
    for half in ("am", "pm"):
        p = HERE / f"xnew-{d}-{half}.json"
        if not p.exists(): continue
        run = json.loads(p.read_text()); xnew_runs.append(run.get("label", p.name))
        for it in run.get("items", []):
            k = norm(it["name"]); existed = k in idx
            t = get(it["name"])
            if existed and "书签X" not in t["sources"]:
                dupes.append({"name": it["name"], "matched": t["name"], "ours": list(t["sources"])})
            if "书签X" not in t["sources"]: t["sources"].append("书签X")
            if it.get("kind") == "not_model": t["not_model"] = True
            if not t["desc"] or not t.get("board"):
                t["desc"] = it.get("desc") or t["desc"]; t["url"] = t["url"] or it.get("url", "")
            t.setdefault("first_seen", it.get("first_seen"))
            if it.get("keyword"): board_kw.append((it["keyword"], it["name"], it.get("reason", ""), "书签X"))
        for kw in run.get("keywords", []):
            board_kw.append((kw["keyword"], "", kw.get("reason", ""), "书签X"))
    extra, seen = [], set()
    for e in board_kw:
        kw, nm, why = e[:3]; src = e[3] if len(e) > 3 else "看板X"
        hit = next((x for x in extra if x["phrase"].lower() == kw.lower()), None)
        if hit:
            if src not in hit["source"]: hit["source"] += "/" + src
            continue
        extra.append({"phrase": kw, "source": src, "names": [nm] if nm else [], "evidence": why})
    xs = report.get("x", {})
    x_failed = bool(xs.get("error")) or (xs.get("answered", 0) == 0)
    out = {"date": a.date, "board_runs": board_runs, "xnew_runs": xnew_runs, "our_x_failed": x_failed, "terms": terms,
           "dupes": dupes, "board_keywords": [e["phrase"] for e in extra]}
    (HERE / "merged.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (HERE / "board_keywords.json").write_text(json.dumps(extra, ensure_ascii=False, indent=1))
    L = [f"## 合并新词（{a.date}）", "", f"看板雷达：{'、'.join(board_runs) or '当天没有'}；书签X：{'、'.join(xnew_runs) or '当天没有'}；共 {len(terms)} 个词，两边重合 {len(dupes)} 个。"]
    if x_failed: L.append("⚠ 我们的 X 源今晚失败，X 部分只有看板雷达的词。")
    L.append("")
    order = sorted(terms, key=lambda t: (-len(t["sources"]), "看板X" not in t["sources"]))
    for t in order:
        link = f" [链接]({t['url']})" if t["url"] else ""
        L.append(f"- **{t['name']}**〔{' / '.join(t['sources'])}〕{(t['desc'] or '；'.join(t['signals']))[:120]}{link}")
    (HERE / "merged.md").write_text("\n".join(L) + "\n")
    print(f"merged {len(terms)} terms, dupes {len(dupes)}: {[x['name'] for x in dupes]}; board keywords: {out['board_keywords']}; our X failed: {x_failed}")

if __name__ == "__main__":
    main()
