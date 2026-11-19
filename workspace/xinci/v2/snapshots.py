from pathlib import Path
from v2.util import HERE, today_bj, load_json, save_json, norm, bj_stamp, data_root

def snap_dir() -> Path:
    return data_root() / "track_state" / "chart_snapshots"

SNAP_DIR = HERE / "track_state" / "chart_snapshots"  # fallback only; prefer snap_dir()

def report_is_current(report: dict, today: str) -> bool:
    if not isinstance(report, dict) or not report:
        return False
    keys = ["date", "day", "generated_at", "run_at", "label", "collected_at"]
    for k in keys:
        val = report.get(k)
        if isinstance(val, str) and val.startswith(today):
            return True
    return False

def sitemap_diff(prev_urls, now_urls) -> dict:
    now_set = set(now_urls or [])
    now_count = len(now_set)
    if not prev_urls:
        return {
            "first_run": True,
            "new": [],
            "new_count": 0,
            "now_count": now_count,
            "note": "首次基线，new=0"
        }
    prev_set = set(prev_urls)
    new_items = sorted(list(now_set - prev_set))
    return {
        "first_run": False,
        "new": new_items,
        "new_count": len(new_items),
        "now_count": now_count,
    }

def scrape_status(had_error: bool, now_count: int, new_count: int) -> str:
    if had_error and now_count == 0:
        return "failed"
    if (not had_error) and new_count == 0:
        return "zero_new"
    if had_error:
        return "partial"
    return "ok"

def classify_chart_items(current_items, history_snapshots, today: str) -> list[dict]:
    current_items = current_items or []
    history_snapshots = sorted(history_snapshots or [], key=lambda x: x.get("date", ""))
    
    previous = None
    for snap in history_snapshots:
        if snap.get("date", "") < today:
            previous = snap
        else:
            break
    if previous is None and history_snapshots:
        if history_snapshots[-1].get("date", "") < today:
            previous = history_snapshots[-1]

    all_seen = set()
    for snap in history_snapshots:
        for n in snap.get("names", []):
            all_seen.add(norm(n))

    prev_names = set()
    if previous:
        for n in previous.get("names", []):
            prev_names.add(norm(n))

    result = []
    for item in current_items:
        it = dict(item)
        name = it.get("name", "")
        k = norm(name)
        
        # No prior snapshot: first baseline. Names are observed, not "first discovery".
        if not history_snapshots:
            is_first_discovery = False
            new_on_chart = False
            still_popular = False
            reheating = False
        else:
            is_first_discovery = k not in all_seen
            new_on_chart = (k not in prev_names) if previous is not None else False
            still_popular = (k in prev_names) if previous is not None else False
            reheating = (k in all_seen) and (k not in prev_names) and not is_first_discovery

        first_seen = today
        for snap in history_snapshots:
            snap_names = [norm(x) for x in snap.get("names", [])]
            if k in snap_names:
                first_seen = snap.get("date", today)
                break

        it["is_first_discovery"] = is_first_discovery
        it["new_on_chart"] = new_on_chart
        it["still_popular"] = still_popular
        it["reheating"] = reheating
        it["first_seen"] = first_seen
        result.append(it)

    return result

def write_game_snapshot(date: str, items: list, path: Path = None) -> Path:
    if path is None:
        d = snap_dir()
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"game-{date}.json"
    
    cleaned_items = []
    names = []
    for it in items or []:
        name = it.get("name", "")
        cleaned_items.append({
            "name": name,
            "url": it.get("url", ""),
            "platform": it.get("platform", ""),
            "metrics": it.get("metrics", {})
        })
        if name and name not in names:
            names.append(name)

    data = {
        "date": date,
        "timezone": "Asia/Shanghai",
        "collected_at": bj_stamp(),
        "items": cleaned_items,
        "names": names
    }
    save_json(path, data)
    return path

def load_history(dir: Path = None, prefix: str = "game-") -> list:
    d = Path(dir) if dir else snap_dir()
    if not d.exists() or not d.is_dir():
        return []
    
    history = []
    for f in sorted(d.glob(f"{prefix}*.json")):
        data = load_json(f)
        if isinstance(data, dict) and "date" in data:
            history.append(data)
    
    return sorted(history, key=lambda x: x.get("date", ""))
