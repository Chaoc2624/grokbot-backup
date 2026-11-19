import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
p = Path("/workspace/xinci/xscan_state.json")
d = json.load(p.open())
d["last_scan"] = "2026-11-15T12:48:16Z"
cutoff = datetime.now(timezone.utc) - timedelta(days=30)
rep = d.get("reported", {})
kept = {}
dropped = 0
for k,v in rep.items():
    fs = str(v.get("first_seen") or "")
    keep = True
    try:
        dt = datetime.strptime(fs, "%Y-%m-%d %H:%M").replace(tzinfo=timezone(timedelta(hours=8)))
        if dt < cutoff:
            keep = False
    except Exception:
        keep = True
    if keep:
        kept[k] = v
    else:
        dropped += 1
d["reported"] = kept
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
print("last_scan", d["last_scan"], "reported", len(kept), "dropped", dropped)
x=json.load(open("/workspace/xinci/xnew-20261115-pm.json"))
print("xnew", x["label"], "empty", x["empty"], "window", x["window_start"], "->", x["window_end"], "run_at", x["run_at"])
