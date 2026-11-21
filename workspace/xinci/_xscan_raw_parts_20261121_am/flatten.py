
import json, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
raw = Path("/workspace/xinci/_xscan_raw_parts_20261121_am")

def load_queries(*files):
    out = {}
    for f in files:
        p = raw / f
        if not p.exists():
            continue
        data = json.loads(p.read_text())
        out.update(data.get("queries") or {})
    return out

queries = load_queries("page1.json", "page2.json", "page3.json")
page1 = json.loads((raw / "page1.json").read_text())
meta = page1.get("meta") or {}

def beijing(iso):
    if not iso:
        return None
    s = iso.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return iso
    return dt.astimezone(TZ).strftime("%Y-%m-%d %H:%M")

def flatten(label, result):
    posts = (result or {}).get("data") or []
    includes = (result or {}).get("includes") or {}
    users = {u["id"]: u for u in (includes.get("users") or []) if u.get("id")}
    rows = []
    for p in posts:
        uid = p.get("author_id") or p.get("authorId")
        u = users.get(uid) or {}
        username = u.get("username") or p.get("username")
        m = p.get("public_metrics") or {}
        rows.append({
            "query": label,
            "id": p.get("id"),
            "url": p.get("url") or (f"https://x.com/{username}/status/{p.get('id')}" if username and p.get("id") else f"https://x.com/i/status/{p.get('id')}"),
            "username": username,
            "display_name": u.get("name"),
            "author_id": uid,
            "created_at": p.get("created_at"),
            "first_seen": beijing(p.get("created_at")),
            "lang": p.get("lang"),
            "likes": m.get("like_count") or 0,
            "bookmarks": m.get("bookmark_count") or 0,
            "views": m.get("impression_count") or 0,
            "replies": m.get("reply_count") or 0,
            "quotes": m.get("quote_count") or 0,
            "reposts": m.get("repost_count") or m.get("retweet_count") or 0,
            "text": p.get("text") or (p.get("note_post") or {}).get("text") or "",
        })
    return rows

all_rows = []
counts = {}
for label, rec in queries.items():
    rows = flatten(label, rec.get("result") if rec.get("ok") else None)
    base = re.sub(r"_p\d+$", "", label)
    for r in rows:
        r["track"] = base
    counts[label] = {"ok": rec.get("ok"), "n": len(rows), "error": rec.get("error")}
    all_rows.extend(rows)

by_id = {}
for r in all_rows:
    i = r["id"]
    if i not in by_id:
        r["tracks"] = [r["track"]]
        by_id[i] = r
    else:
        if r["track"] not in by_id[i]["tracks"]:
            by_id[i]["tracks"].append(r["track"])

unique = list(by_id.values())
(raw / "flat_posts.json").write_text(json.dumps({"meta": meta, "counts": counts, "posts": unique}, ensure_ascii=False, indent=2))

official = [p for p in unique if "official" in p["tracks"]]
official.sort(key=lambda x: x.get("created_at") or "", reverse=True)

intro_hi = [p for p in unique if "introducing" in p["tracks"] and (p["likes"] >= 100 or p["bookmarks"] >= 50 or p["views"] >= 20000)]
intro_hi.sort(key=lambda x: (x["likes"], x["views"]), reverse=True)
n500 = sum(1 for p in unique if "introducing" in p["tracks"] and p["likes"] >= 500)

lines = []
lines.append("COUNTS " + json.dumps(counts, ensure_ascii=False))
lines.append(f"UNIQUE {len(unique)} OFFICIAL {len(official)}")
lines.append(f"introducing likes>=500: {n500}; high-signal: {len(intro_hi)}")
lines.append("")
lines.append("===== OFFICIAL POSTS =====")
for p in official:
    lines.append("-" * 40)
    lines.append(f"@{p['username']} {p['first_seen']} likes={p['likes']} bk={p['bookmarks']} views={p['views']}")
    lines.append(p["url"])
    lines.append(p["text"][:800])
lines.append("")
lines.append("===== INTRODUCING high-signal =====")
for p in intro_hi[:40]:
    lines.append("-" * 40)
    lines.append(f"@{p['username']} {p['first_seen']} likes={p['likes']} bk={p['bookmarks']} views={p['views']}")
    lines.append(p["url"])
    lines.append(p["text"][:500])

(raw / "official_and_intro.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines[:30]))
print("... wrote official_and_intro.txt and flat_posts.json")
print("unique", len(unique), "official", len(official), "intro>=500", n500, "intro_hi", len(intro_hi))
