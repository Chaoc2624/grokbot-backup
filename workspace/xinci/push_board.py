#!/usr/bin/env python3
"""merged.json + doable.json -> board radar payload (label 'YYYY-MM-DD 新词雷达'), push via /workspace/xbm/board_client.py."""
import argparse, json, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
from merge_board import norm

def fmtv(t):
    v, kd, cpc = t.get("volume"), t.get("kd"), t.get("cpc")
    d = t.get("comp_detail") or {}
    comp = t.get("verdict") or "—"
    comp = {"open": "能进", "crowded": "挤满"}.get(comp, comp)
    return f"月搜 {v if v is not None else '—'}、KD {kd if kd is not None else '—'}、CPC ${cpc if cpc is not None else '—'}、首页竞争「{comp}」（Semrush 美国库）"

def main():
    now = datetime.now(timezone(timedelta(hours=8)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=now.strftime("%Y-%m-%d"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    m = json.loads((HERE / "merged.json").read_text())
    if m["date"] != a.date: sys.exit(f"merged.json is for {m['date']}, not {a.date}; run merge_board.py --date {a.date} first")
    dj = json.loads((HERE / "doable.json").read_text()) if (HERE / "doable.json").exists() else {"terms": []}
    items, by = [], {}
    for t in m["terms"]:
        b = t.get("board") or {}
        it = {"name": t["name"], "desc": (t["desc"] or "；".join(t["signals"]))[:300],
              "source": " / ".join(t["sources"]) + (f"（{b['source']}）" if b.get("source") else ""),
              "url": t["url"], "first_seen": b.get("first_seen") or a.date}
        items.append(it); by[t["key"]] = it
    passed = [t for t in dj["terms"] if not t.get("failed") and not t.get("unknown")]
    passed.sort(key=lambda t: -t.get("score", 0))
    keywords = []
    for r, t in enumerate(passed, 1):
        why = fmtv(t) + f"，信心分 {t.get('score')}" + (f"；来自 {'、'.join(t['names'])}" if t.get("names") else "")
        tgt = next((by[norm(n)] for n in t.get("names", []) + [t["phrase"]] if norm(n) in by), None)
        if tgt is None:
            tgt = {"name": t["phrase"], "desc": t.get("evidence", "")[:300], "source": t.get("source", ""), "url": "", "first_seen": a.date}
            items.append(tgt)
        tgt.update(keyword_rank=r, keyword=t["phrase"], reason=why)
        keywords.append({"keyword": t["phrase"], "reason": why})
    items.sort(key=lambda i: (i.get("keyword_rank") or 999))
    p = {"label": f"{a.date} 新词雷达", "run_at": now.strftime("%Y-%m-%d %H:%M"),
         "window_start": f"{a.date} 00:00", "window_end": f"{a.date} 23:59", "empty": not items,
         "items": items, "keywords": keywords}
    out = HERE / "board_payload.json"; out.write_text(json.dumps(p, ensure_ascii=False, indent=1))
    print(f"label={p['label']} items={len(items)} keywords={[k['keyword'] for k in keywords]} x_failed={m['our_x_failed']}")
    if a.dry_run: print("dry-run, not pushed:", out); return
    r = subprocess.run(["python3", "/workspace/xbm/board_client.py", "radar", str(out)], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[-500:]); sys.exit(r.returncode)

if __name__ == "__main__":
    main()
