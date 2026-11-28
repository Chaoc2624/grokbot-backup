
import json, re, unicodedata, shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
ROOT = Path("/workspace/xinci")
RAW = ROOT / "_xscan_raw_parts_20261122_am"
now = datetime.now(TZ)
run_at = now.strftime("%Y-%m-%d %H:%M")

def norm(s):
    s = re.sub(r"[（(【\[].*?[）)】\]]", "", s or "")
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"[\W_]+", "", s)

descs = json.loads((RAW / "descs_zh.json").read_text())
descs["codemode"] = descs["codemode"].replace("非新模型。", "不是新模型。").replace("非新模型", "不是新模型")

official_start = "2026-11-21T01:58:40Z"
tracks_start = "2026-11-15T01:55:00Z"
end_time = "2026-11-22T01:58:52Z"

def bj_from_iso(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(TZ)
    return dt.strftime("%Y-%m-%d %H:%M")

items = [
    {
        "name": "CCORE-Web-Coder-4B",
        "desc": descs["ccore"],
        "source": "@ModelScope2022",
        "url": "https://x.com/ModelScope2022/status/2123990190939308374",
        "first_seen": "2026-11-21 12:01",
        "views": 1711,
        "bookmarks": 13,
        "likes": 24,
        "kind": "model",
    },
    {
        "name": "Hy4-flash",
        "desc": descs["hy4flash"],
        "source": "@ModelScope2022",
        "url": "https://x.com/ModelScope2022/status/2122955127782834677",
        "first_seen": "2026-11-18 15:28",
        "views": 4082,
        "bookmarks": 4,
        "likes": 37,
        "kind": "model",
        "backfill": True,
    },
    {
        "name": "Code Mode",
        "desc": descs["codemode"],
        "source": "@ClaudeDevs",
        "url": "https://x.com/ClaudeDevs/status/2122801681939234950",
        "first_seen": "2026-11-18 05:18",
        "views": 2403922,
        "bookmarks": 14515,
        "likes": 12487,
        "kind": "not_model",
        "backfill": True,
    },
]

query_note = (
    "免费 x.search_posts_all，未使用付费 user-X。"
    "官方账号窗口 start_time=2026-11-21T01:58:40Z（上次成功 last_scan）；"
    "游戏/工具/视频及官方补漏 start_time=2026-11-15T01:55:00Z（近7天），end_time=2026-11-22T01:58:52Z。"
    "A 官方本窗仅 2 条（活动帖已排除），翻页后无更多；另补近7天官方账号 3 页用于查漏。"
    "B 路 min_likes:500 与工具路 min_faves:50 被 API 去掉，已改为本地过滤，本窗 likes>=500 的首发关键词帖为 0。"
    "本窗官方首发收录 CCORE-Web-Coder-4B；Hy4-flash 为已报 Hy4 的新 SKU、窗口前官方帖，已补报；"
    "Code Mode 为 Claude Code 实验功能（不是新模型），窗口前官方帖已补报，但「Code Mode」偏泛词，未列入建站热词。"
    "Gemini 4 Neon/Hydrogen、Genie 4、Stitch Loop、WeMM-Video、DaisyRose-27B、GPT-Live-1.1、GPT-6.2 Astra/Sol、"
    "Mistral Vibe Desktop、Depth Pro 2、Gemini 3.5 Transcribe 语音编辑 API、Hy4 总称均已在 reported，不重复收录。"
    "视频检索已排除儿童相关与普通 CapCut 模板/GTA 切片教程；查询种子（CapCut/AI video 等）不当作新词。"
    "有原文证据的 Higgsfield Genjutsu、Quilted fabric cave 仅作为元数据线索进入可选 x-input，未做画面核验。"
    "游戏检索大量历史事件/色情/泛讨论已剔除；未写明游戏名的自宣帖不编造名称。尚未发行的 Sandkeeper、coming soon 的 bugsbugs 不收。"
)

xnew = {
    "label": "2026-11-22 上午 书签X",
    "run_at": run_at,
    "window_start": bj_from_iso(official_start),
    "window_end": bj_from_iso(end_time),
    "empty": False,
    "query_note": query_note,
    "items": items,
    "keywords": [],
}

xnew_path = ROOT / "xnew-20261122-am.json"
xnew_path.write_text(json.dumps(xnew, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

x_input = {
    "game": [
        {"name": "Flower Survivors", "desc": descs["flower"], "url": "https://x.com/MoJz89092047/status/2124157134225199385", "source": "@MoJz89092047", "first_seen": "2026-11-21 23:05"},
        {"name": "Forty Eight", "desc": descs["forty"], "url": "https://x.com/FedoraMasterB98/status/2124048897668727123", "source": "@FedoraMasterB98", "first_seen": "2026-11-21 15:54"},
        {"name": "Classroom in Sora", "desc": descs["classroom"], "url": "https://x.com/hypohyphen/status/2123146356646936933", "source": "@hypohyphen", "first_seen": "2026-11-19 04:08"},
    ],
    "ai_tools": [
        {"name": "CCORE-Web-Coder-4B", "desc": descs["ccore"], "url": "https://x.com/ModelScope2022/status/2123990190939308374", "source": "@ModelScope2022", "first_seen": "2026-11-21 12:01"},
        {"name": "Hy4-flash", "desc": descs["hy4flash"], "url": "https://x.com/ModelScope2022/status/2122955127782834677", "source": "@ModelScope2022", "first_seen": "2026-11-18 15:28"},
        {"name": "Code Mode", "desc": descs["codemode"], "url": "https://x.com/ClaudeDevs/status/2122801681939234950", "source": "@ClaudeDevs", "first_seen": "2026-11-18 05:18"},
        {"name": "PhoText", "desc": descs["photext"], "url": "https://x.com/tao_nie23174/status/2123778714110488744", "source": "@tao_nie23174", "first_seen": "2026-11-20 22:01"},
        {"name": "Gluely", "desc": descs["gluely"], "url": "https://x.com/michaelaubry/status/2124286967924019322", "source": "@michaelaubry", "first_seen": "2026-11-22 07:40"},
        {"name": "Higgsfield Genjutsu", "desc": descs["genjutsu"], "url": "https://x.com/AbubacaryDanso/status/2124288855725486246", "source": "@AbubacaryDanso", "first_seen": "2026-11-22 07:48"},
        {"name": "Quilted fabric cave", "desc": descs["quilted"], "url": "https://x.com/tolik12308/status/2124171625151054287", "source": "@tolik12308", "first_seen": "2026-11-22 00:02"},
    ],
}
x_input_path = ROOT / "v2_run" / "x-input-20261122-am.json"
x_input_path.write_text(json.dumps(x_input, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

flat = json.loads((RAW / "flat_posts.json").read_text())
counts = flat.get("counts_pages") or {}
usage = json.loads((RAW / "aisa_account_today.json").read_text())
prior = usage.get("today_prior_usd")
if prior is None:
    prior = 0.0

raw_meta = {
    "official_posts": counts.get("official", 0),
    "official_7d_posts": counts.get("official7d", 0),
    "introducing_posts": counts.get("intro", 0) + counts.get("intro7d", 0),
    "games_posts": counts.get("game1", 0) + counts.get("game2", 0) + counts.get("game3", 0),
    "tools_posts": counts.get("tools1", 0) + counts.get("tools2", 0) + counts.get("tools3", 0),
    "video_posts": counts.get("video", 0),
    "unique_posts": flat.get("unique_posts"),
    "start_time_official": official_start,
    "start_time_tracks": tracks_start,
    "end_time": end_time,
    "namespace": "x",
    "max_results": 25,
    "today_prior_usd": prior,
    "aisa_usage_today_charged_usd": prior,
    "aisa_usage_today_requests": 0,
    "tracks_window_start_taipei": bj_from_iso(tracks_start),
    "xnew_items": len(items),
    "x_input_game": len(x_input["game"]),
    "x_input_ai_tools": len(x_input["ai_tools"]),
}
(ROOT / "v2_run" / "x-raw-meta-20261122-am.json").write_text(json.dumps(raw_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(RAW / "x-raw-meta.json").write_text(json.dumps(raw_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

state_path = ROOT / "xscan_state.json"
state = json.loads(state_path.read_text())
(RAW / "xscan_state.before.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
shutil.copy2(state_path, ROOT / "xscan_state.json.bak-pre-20261122-am")
state["last_scan"] = end_time
reported = state.get("reported") or {}
cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d")
pruned = {}
for k, v in reported.items():
    fs = (v or {}).get("first_seen") or ""
    if fs >= cutoff:
        pruned[k] = v
for it in items:
    key = norm(it["name"])
    if key and key not in pruned:
        pruned[key] = {"name": it["name"], "first_seen": it["first_seen"], "file": "xnew-20261122-am.json"}
state["reported"] = pruned
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(json.dumps({
    "run_at": run_at,
    "xnew": str(xnew_path),
    "x_input": str(x_input_path),
    "items": [it["name"] for it in items],
    "keywords": [],
    "x_input_game": [g["name"] for g in x_input["game"]],
    "x_input_ai_tools": [g["name"] for g in x_input["ai_tools"]],
    "today_prior_usd": prior,
    "reported_count": len(pruned),
    "last_scan": state["last_scan"],
    "xnew_bytes": xnew_path.stat().st_size,
}, ensure_ascii=False, indent=2))
