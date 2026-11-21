
import json, re
from pathlib import Path

raw = Path("/workspace/xinci/_xscan_raw_parts_20261121_am")
data = json.loads((raw / "flat_posts.json").read_text())
posts = data["posts"]

porn = re.compile(r"condo|nsfw|porn|onlyfans|性感|色情|🔞| Condos|CONDOS|r34|hentai|nude|18\+|sex game|erotica", re.I)
child = re.compile(r"\b(kids?|child|children|toddler|baby|little kids|family video|children's)\b|儿童|小孩|孩子", re.I)
spam_game = re.compile(r"#fyp|#FYP|royalehigh", re.I)

def is_reply_to_nothing_useful(p):
    t = p.get("text") or ""
    return t.startswith("@") and p.get("likes", 0) < 20 and p.get("views", 0) < 2000

def dump(title, rows, limit=40):
    lines = [title, f"n={len(rows)}", ""]
    for p in rows[:limit]:
        lines.append("-" * 36)
        lines.append(f"@{p.get('username')} {p.get('first_seen')} likes={p['likes']} bk={p['bookmarks']} views={p['views']} tracks={p.get('tracks')}")
        lines.append(p.get("url") or "")
        lines.append((p.get("text") or "")[:450].replace("\n", " / "))
    return "\n".join(lines)

# games
games = [p for p in posts if any(t.startswith("game") for t in p.get("tracks") or [])]
games_clean = []
for p in games:
    t = p.get("text") or ""
    if porn.search(t):
        continue
    if is_reply_to_nothing_useful(p):
        continue
    # keep if some engagement or concrete new-game signal
    if p["likes"] >= 8 or p["views"] >= 800 or re.search(r"new game|新游|爆款|trending|charts|unblocked|play now|released|just launched", t, re.I):
        games_clean.append(p)
games_clean.sort(key=lambda x: (x["likes"], x["views"]), reverse=True)

# tools: local min_faves 50 for tools1; otherwise some signal
tools = [p for p in posts if any(t.startswith("tools") for t in p.get("tracks") or [])]
tools_clean = []
for p in tools:
    t = p.get("text") or ""
    if p.get("username") == "grok":
        continue
    if is_reply_to_nothing_useful(p) and p["likes"] < 50:
        continue
    if "tools1" in (p.get("tracks") or []) and p["likes"] < 20 and p["views"] < 2000:
        # tools1 originally min_faves 50; keep medium signal too
        if p["likes"] < 8:
            continue
    if p["likes"] >= 8 or p["views"] >= 500 or re.search(r"just launched|new ai tool|上架|新上|Product Hunt|开源", t, re.I):
        tools_clean.append(p)
tools_clean.sort(key=lambda x: (x["likes"], x["views"]), reverse=True)

# video
videos = [p for p in posts if "video" in (p.get("tracks") or [])]
videos_clean = []
for p in videos:
    t = p.get("text") or ""
    if p.get("username") == "grok":
        continue
    if child.search(t) and re.search(r"capcut|template|family|kids|child", t, re.I):
        continue
    if is_reply_to_nothing_useful(p):
        continue
    if p["likes"] >= 3 or p["views"] >= 80 or re.search(r"玩法|模板|template|OpenMotion|Higgsfield|photo to video|replicate|复刻", t, re.I):
        videos_clean.append(p)
videos_clean.sort(key=lambda x: (x["likes"], x["views"]), reverse=True)

text = "\n\n".join([
    dump("===== GAMES CLEAN =====", games_clean, 35),
    dump("===== TOOLS CLEAN =====", tools_clean, 35),
    dump("===== VIDEO CLEAN =====", videos_clean, 40),
])
(raw / "tracks_candidates.txt").write_text(text, encoding="utf-8")
print(f"games raw={len(games)} clean={len(games_clean)}")
print(f"tools raw={len(tools)} clean={len(tools_clean)}")
print(f"video raw={len(videos)} clean={len(videos_clean)}")
print("wrote tracks_candidates.txt", len(text))
