
#!/usr/bin/env python3
import json, re, unicodedata
from pathlib import Path
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
ROOT = Path("/workspace/xinci")
RAW = ROOT / "_xscan_raw_parts_20261121_am"
now = datetime.now(TZ)
run_at = now.strftime("%Y-%m-%d %H:%M")

def norm(s):
    s = re.sub(r"[（(【\[].*?[）)】\]]", "", s or "")
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"[\W_]+", "", s)

# usage receipt (already queried)
usage_today = {
    "queried_at_utc": "2026-11-21T01:59:00Z",
    "queried_at_taipei": "2026-11-21 09:59 CST (Asia/Taipei)",
    "endpoint": "https://api.aisa.one/v1/usage?start_time=<today_utc_midnight>",
    "today": {
        "date_basis": "as_of UTC midnight; usage totals.charged_micros_usd / 1e6 as today charged_usd",
        "requests": 0,
        "failed_requests": 0,
        "charged_usd": 0.0,
        "charged_micros_usd": 0,
    },
    "today_shanghai_also_zero": True,
}
(RAW / "aisa_account_today.json").write_text(json.dumps(usage_today, indent=2), encoding="utf-8")

# flatten counts
flat = json.loads((RAW / "flat_posts.json").read_text())
counts = flat.get("counts") or {}
meta = flat.get("meta") or {}
official_start = meta.get("officialStart") or "2026-11-20T01:59:52Z"
tracks_start = meta.get("tracksStart") or "2026-11-14T01:55:00Z"
end_time = meta.get("endTime") or "2026-11-21T01:58:40Z"

def bj_from_iso(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(TZ)
    return dt.strftime("%Y-%m-%d %H:%M")

window_start = bj_from_iso(official_start)
window_end = bj_from_iso(end_time)
tracks_start_bj = bj_from_iso(tracks_start)

items = [
    {
        "name": "Inkling 2 Mini",
        "desc": "Thinking Machines 官方发布 Inkling 2 Mini：约 26B 参数（激活约 3.4B）的循环 Transformer 开源权重模型，官方称可在笔记本运行，AA Index 20.1，面向 agent 工作。",
        "source": "@thinkymachines",
        "url": "https://x.com/thinkymachines/status/2123871643797995872",
        "first_seen": "2026-11-21 04:10",
        "views": 877955,
        "bookmarks": 4904,
        "likes": 7876,
        "kind": "model",
        "keyword_rank": 1,
        "keyword": "Inkling 2 Mini",
        "reason": "官方首发的新 SKU（相对已报的 Inkling 2 Small），播放约 87.8 万、收藏约 4904，适合做本地部署/下载页，以及与 Qwen3.8 27B 等小模型的对比页。",
    },
    {
        "name": "WeMM-Video",
        "desc": "腾讯微信视觉（WeChat Vision）发布 WeMM-Video 开源权重模型系列，面向音画联合理解与推理，提供 2B/4B/9B/35B-A3B 规格，支持文本、图像、音频和视频输入，Apache-2.0。",
        "source": "@ModelScope2022",
        "url": "https://x.com/ModelScope2022/status/2123755394296422564",
        "first_seen": "2026-11-20 20:28",
        "views": 3366,
        "bookmarks": 55,
        "likes": 68,
        "kind": "model",
    },
    {
        "name": "Gemini 3.5 Transcribe 语音编辑 API",
        "desc": "Google 宣布把 Gemini 3.5 Transcribe 的语音编辑能力开放到 Gemini API，开发者可做「用语音编辑、改写、翻译已有文本」的体验；该能力已用于 Gboard 的 Rambler 和 macOS 上的 Gemini 应用。不是新模型。",
        "source": "@Google",
        "url": "https://x.com/Google/status/2123827048808370477",
        "first_seen": "2026-11-21 01:13",
        "views": 182590,
        "bookmarks": 294,
        "likes": 809,
        "kind": "not_model",
    },
    {
        "name": "Stitch Loop",
        "desc": "【补报】Google / Google Labs 发布实验产品 Stitch Loop：代码上线后仍持续监测产品指标，在沙箱中测试修复并提交待审批的 PR，基于 Gemini 4 Carbon 和 CodeMender。本窗之前官方首发（2026-11-18），上档漏报。",
        "source": "@Google",
        "url": "https://x.com/Google/status/2123101724047200432",
        "first_seen": "2026-11-19 01:11",
        "views": 225354,
        "bookmarks": 707,
        "likes": 1711,
        "kind": "product",
        "backfill": True,
    },
    {
        "name": "Flowtica Verso",
        "desc": "【补报】Flowtica 官方发布 Flowtica Verso：宣称全球首款带实时电子墨水屏的 MagSafe AI 会议记录配件，可记录通话与当面交谈并生成摘要和待办。本窗之前官方首发（2026-11-17），上档漏报。",
        "source": "@Flowtica_AI",
        "url": "https://x.com/Flowtica_AI/status/2122691235261383029",
        "first_seen": "2026-11-17 22:00",
        "views": 552827,
        "bookmarks": 56,
        "likes": 184,
        "kind": "product",
        "backfill": True,
        "keyword_rank": 2,
        "keyword": "Flowtica Verso",
        "reason": "官方硬件+AI 笔记新品，播放约 55.3 万，适合做 AI 会议记录/MagSafe 录音配件介绍或替代词页；需标明这是实体配件，不是纯网页工具。",
    },
]

xnew = {
    "label": "2026-11-21 上午 书签X",
    "run_at": run_at,
    "window_start": window_start,
    "window_end": window_end,
    "empty": False,
    "query_note": (
        "免费 x.search_posts_all，未使用付费 user-X。"
        f"官方账号窗口 start_time={official_start}（上次成功 last_scan）；"
        f"游戏/工具/视频补近7天 start_time={tracks_start}，end_time={end_time}。"
        "A 官方 14 条后翻页 0 条。B 路 min_likes:500 被 API 去掉，本地过滤 likes>=500 仅命中 Inkling 2 Mini 相关转述，已改用官方 @thinkymachines 首发帖。"
        "本窗 GoogleAI 回顾帖还提到 Gemini 4 Neon/Hydrogen/Carbon、Genie 4、Gemini Robotics 2.5、AlphaGenome 2，均已在 reported 中，不重复收录；Hy4 开源权重动态因 hy4 已报（2026-11-04）不重复收录。"
        "Stitch Loop、Flowtica Verso 为窗口前官方首发、上档漏报，已补报。"
        "视频检索含大量 grok 回复、K-pop/普通 CapCut 模板和儿童相关内容，已排除；未见有原文证据、可复刻的具体 AI 视频玩法，故视频词不收录，查询种子（CapCut/AI video 等）不当作新词。"
        "游戏检索大量 condo/色情及泛讨论已剔除；仅保留低互动的 TNT Incremental 2 作为发现线索进入可选 x-input。"
    ),
    "items": items,
    "keywords": [
        {"keyword": "Inkling 2 Mini", "reason": items[0]["reason"]},
        {"keyword": "Flowtica Verso", "reason": items[4]["reason"]},
    ],
}

xnew_path = ROOT / "xnew-20261121-am.json"
xnew_path.write_text(json.dumps(xnew, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

x_input = {
    "game": [
        {
            "name": "TNT Incremental 2",
            "desc": "开发者自宣 Roblox 新游戏 TNT Incremental 2 已上线，从标签看是增量/放置（incremental）类型、平台为 Roblox。互动极低（播放 52、赞 3），未做画面核验，仅作游戏轨发现线索，不是官方榜单或高互动首发。",
            "url": "https://x.com/realw1vvo/status/2123891148758634877",
            "source": "@realw1vvo",
            "first_seen": "2026-11-21 05:28",
        }
    ],
    "ai_tools": [
        {
            "name": "Inkling 2 Mini",
            "desc": items[0]["desc"],
            "url": items[0]["url"],
            "source": items[0]["source"],
            "first_seen": items[0]["first_seen"],
        },
        {
            "name": "WeMM-Video",
            "desc": items[1]["desc"],
            "url": items[1]["url"],
            "source": items[1]["source"],
            "first_seen": items[1]["first_seen"],
        },
        {
            "name": "Gemini 3.5 Transcribe 语音编辑 API",
            "desc": items[2]["desc"],
            "url": items[2]["url"],
            "source": items[2]["source"],
            "first_seen": items[2]["first_seen"],
        },
        {
            "name": "Stitch Loop",
            "desc": items[3]["desc"],
            "url": items[3]["url"],
            "source": items[3]["source"],
            "first_seen": items[3]["first_seen"],
        },
        {
            "name": "Flowtica Verso",
            "desc": items[4]["desc"],
            "url": items[4]["url"],
            "source": items[4]["source"],
            "first_seen": items[4]["first_seen"],
        },
        {
            "name": "OpenMotion",
            "desc": "X 帖称 OpenMotion 是开源的 CapCut / Claude Motion 替代，玩法是喂一段参考视频、换上自己的品牌素材和文案后复刻可改的动态设计并导出 MP4；另有帖称 OpenDesign 为其增加 DeepSeek 调用和 300 多个视频模板。互动极低，未做画面核验，仅作工具轨发现线索，不是已核验的热梗玩法。",
            "url": "https://x.com/wlzh/status/2123954192993952044",
            "source": "@wlzh",
            "first_seen": "2026-11-21 09:38",
        },
        {
            "name": "n8n Agents",
            "desc": "第三方帖称 n8n 刚上线 Agents：可给 agent 设定目标并调用已有 n8n 工作流。未见 @n8n_io 官方首发帖，n8n 为既有产品，本条只作功能更新发现线索，不是新工具名立项依据。",
            "url": "https://x.com/DataChaz/status/2123887116182835574",
            "source": "@DataChaz",
            "first_seen": "2026-11-21 05:12",
        },
    ],
}
x_input_path = ROOT / "v2_run" / "x-input-20261121-am.json"
x_input_path.write_text(json.dumps(x_input, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def count_base(prefix):
    n = 0
    for k, v in counts.items():
        if k == prefix or k.startswith(prefix + "_p"):
            n += v.get("n") or 0
    return n

raw_meta = {
    "official_posts": count_base("official"),
    "introducing_posts": count_base("introducing"),
    "games_posts": count_base("game1") + count_base("game2") + count_base("game3"),
    "tools_posts": count_base("tools1") + count_base("tools2") + count_base("tools3"),
    "video_posts": count_base("video"),
    "start_time_official": official_start,
    "start_time_tracks": tracks_start,
    "end_time": end_time,
    "namespace": "x",
    "max_results": 25,
    "today_prior_usd": 0.0,
    "aisa_usage_today_charged_usd": 0.0,
    "aisa_usage_today_requests": 0,
    "tracks_window_start_taipei": tracks_start_bj,
    "xnew_items": len(items),
    "x_input_game": len(x_input["game"]),
    "x_input_ai_tools": len(x_input["ai_tools"]),
}
(ROOT / "v2_run" / "x-raw-meta-20261121-am.json").write_text(json.dumps(raw_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# update xscan_state
state_path = ROOT / "xscan_state.json"
state = json.loads(state_path.read_text())
# backup
(RAW / "xscan_state.before.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
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
        pruned[key] = {"name": it["name"], "first_seen": it["first_seen"], "file": "xnew-20261121-am.json"}
state["reported"] = pruned
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(json.dumps({
    "run_at": run_at,
    "xnew": str(xnew_path),
    "x_input": str(x_input_path),
    "items": [it["name"] for it in items],
    "keywords": [k["keyword"] for k in xnew["keywords"]],
    "raw_meta": raw_meta,
    "reported_count": len(pruned),
    "last_scan": state["last_scan"],
}, ensure_ascii=False, indent=2))
