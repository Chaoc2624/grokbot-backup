#!/usr/bin/env python3
"""
render_card.py — 新词雷达图文卡片生成器 (1600px Retina PNG)

支持两种模式：
  1) --mode am (或 morning): 渲染 10:20 上午扫描卡片
     读取: xnew-YYYYMMDD-am.json + sources-YYYYMMDD-am.log (及 radar.db)
     输出: /workspace/xinci/card-am.png 与 /workspace/xinci/card-YYYYMMDD-am.png
  2) --mode pm (或 daily, 默认): 渲染 21:20 晚间日报卡片
     读取: merged.json / report.json, doable.json, finders.json, xnew-YYYYMMDD-{am,pm}.json, board_payload.json
     输出: /workspace/xinci/card-pm.png 与 /workspace/xinci/card-YYYYMMDD-pm.png

设计遵循 kaoda-ui v0.1.5 规范与 Halo Board 视觉风格：
  - 800px 逻辑宽度 × 2x DPR = 1600px 高清宽度，Noto Sans CJK SC 字体
  - 浅灰底色 (#f4f6f9) + 纯白分区面板 (#ffffff) + 扁平分隔行（严禁卡片套卡片）
  - 建站热词采用暖琥珀色高亮 (#fffbeb / #fde68a / #854d0e)
  - SERP 真空期可抢采用柔绿/翠青高亮与可注册域名徽章 (#ecfdf5 / #10b981 / #065f46)
"""

from __future__ import annotations
import argparse
import datetime as dt
import html
import json
import os
import pathlib
import re
import shutil
import sqlite3
from typing import Any

ROOT = pathlib.Path("/workspace/xinci")
CHROME_PATH = "/usr/bin/google-chrome"

# 常见英文开源仓库 / 信号的一句话中文简述映射（自动兜底 + 支持 card_notes.json 扩展）
ZH_DESC_OVERRIDES: dict[str, str] = {
    "xevrion/hatchzip": "原地解压超大 ZIP/7z 压缩包，边解压边缩小原包体积，省磁盘空间",
    "hatchzip": "原地解压超大 ZIP/7z 压缩包，边解压边缩小原包体积，省磁盘空间",
    "zagitta/gpu-unlock": "解锁 Nvidia RTX 3000 系消费卡 FP/BF16 吞吐率至专业卡水平",
    "gpu-unlock": "解锁 Nvidia RTX 3000 系消费卡 FP/BF16 吞吐率至专业卡水平",
    "gpu unlock": "解锁 Nvidia RTX 3000 系消费卡 FP/BF16 吞吐率至专业卡水平",
    "justaresearcher/gpu-unlock-ada": "解锁 RTX 4090 / 4070 Ti Super 张量算力固件生成工具（底层硬件补丁）",
    "gpu-unlock-ada": "解锁 RTX 4090 / 4070 Ti Super 张量算力固件生成工具（底层硬件补丁）",
    "yeqv111/mccarbon": "麦麦碳账本：基于麦当劳 MCP 的个人餐饮碳足迹估算与减排模拟器",
    "mccarbon": "麦麦碳账本：基于麦当劳 MCP 的个人餐饮碳足迹估算与减排模拟器",
    "amosblomqvist/learnharness": "面向高难度技能与知识习得的 AI Agent Harness 脚手架框架",
    "learnharness": "面向高难度技能与知识习得的 AI Agent Harness 脚手架框架",
    "nikii-w/mclife-desk": "麦门人生工作台：基于麦当劳 MCP 记录点餐日历、消费金额与热量统计",
    "mclife-desk": "麦门人生工作台：基于麦当劳 MCP 记录点餐日历、消费金额与热量统计",
    "ethanarbuckle/fairplay-decrypt": "独立密钥派生的离线 FairPlay App Store IPA 解密工具",
    "fairplay-decrypt": "独立密钥派生的离线 FairPlay App Store IPA 解密工具",
    "fairplay decrypt": "独立密钥派生的离线 FairPlay App Store IPA 解密工具",
    "gathin23/cleanyourtv": "通过 Wi-Fi 为 Android / Google TV 去广告精简系统，换成 Apple TV 风格桌面",
    "cleanyourtv": "通过 Wi-Fi 为 Android / Google TV 去广告精简系统，换成 Apple TV 风格桌面",
    "deepseek-ai/deepinfer": "DeepSeek 官方高性能大规模大模型推理框架，星标持续暴涨",
    "deepinfer": "DeepSeek 官方高性能大规模大模型推理框架，星标持续暴涨",
    "wesbos/3d-model-anything": "利用 iPhone LiDAR 与照片重建可编辑 Three.js 3D 房间并在浏览器漫游",
    "3d-model-anything": "利用 iPhone LiDAR 与照片重建可编辑 Three.js 3D 房间并在浏览器漫游",
    "pengchujin/aerial-tv": "面向小米、TCL 等国产电视的开源无广告 tvOS 风格桌面，开机自动接管",
    "aerial-tv": "面向小米、TCL 等国产电视的开源无广告 tvOS 风格桌面，开机自动接管",
    "seedds/nxnative": "将 Switch 游戏转成免签 IPA，在 iPhone / iPad / Mac 上原生运行",
    "nxnative": "将 Switch 游戏转成免签 IPA，在 iPhone / iPad / Mac 上原生运行",
    "simbasjungles/free-my-tv": "适用于 Google TV / LG / 三星电视的极速无广告桌面，支持一键还原",
    "free-my-tv": "适用于 Google TV / LG / 三星电视的极速无广告桌面，支持一键还原",
    "openai/php2shell-checker": "OpenAI 官方开源的 PHP2Shell 远程代码执行漏洞检测脚本",
    "ikow/php2shell-poc": "PHP session.upload_progress 5 条 RCE 利用链与检测规则合集",
    "oosexgang/hackios-xnu-kernel": "iOS XNU 内核安全研究与调试工具项目",
    "deepseek v4.1 flash 1017 gsq rco": "ISTA-DASLab 发布的 DeepSeek-V4.1-Flash GGUF 量化模型，新进 HF 热门榜",
    "qwen4-27b": "社区从 XPU 内核 PR 发现 Qwen4-27B 稠密模型规格线索，尚无官方权重",
}

NOISE_SOURCE_TERMS = {
    "aisi", "godot", "unreal", "wordpress", "firefox", "whatsapp", "venturebeat", "xai",
}


def load_json(path: pathlib.Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def esc(val: Any) -> str:
    return html.escape(str(val or ""), quote=True)


def fmt_num(n: Any) -> str:
    if n is None or n == "":
        return "—"
    try:
        v = int(float(n))
    except Exception:
        return str(n)
    if v >= 10000:
        w = v / 10000.0
        return f"{w:.0f}万" if w >= 100 else f"{w:.1f}万".replace(".0万", "万")
    return f"{v:,}"


def truncate_zh(text: str, max_len: int = 44) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip("，,、；;。. ") + "…"


def load_custom_notes() -> dict[str, str]:
    custom = load_json(ROOT / "card_notes.json", {})
    merged = dict(ZH_DESC_OVERRIDES)
    if isinstance(custom, dict):
        for k, v in custom.items():
            merged[k.lower().strip()] = str(v)
    return merged


def clean_repo_desc(repo_name: str, raw_desc: str, notes_map: dict[str, str]) -> str:
    key_full = (repo_name or "").lower().strip()
    key_short = key_full.split("/")[-1]
    if key_full in notes_map:
        return truncate_zh(notes_map[key_full], 46)
    if key_short in notes_map:
        return truncate_zh(notes_map[key_short], 46)
    desc = (raw_desc or "").strip()
    zh_match = re.search(r"([\u4e00-\u9fff][^\n|]+)", desc)
    if zh_match:
        return truncate_zh(zh_match.group(1), 46)
    if not desc:
        return "GitHub 热门飙升开源项目"
    return truncate_zh(desc, 48)


def parse_sources_am(date_str: str, notes_map: dict[str, str]) -> dict[str, Any]:
    """解析 sources-YYYYMMDD-am.log 及 radar.db 中的上午源头新词。"""
    ymd = date_str.replace("-", "")
    log_path = ROOT / f"sources-{ymd}-am.log"
    if not log_path.exists():
        log_path = ROOT / "sources_am.log"

    rows: list[dict[str, Any]] = []
    tweets: dict[str, str] = {}
    spend_usd: float | None = None
    hf_count = 0

    if log_path.exists():
        txt = log_path.read_text(encoding="utf-8", errors="ignore")
        m_cost = re.findall(r"本次 AIsa 数据花费:\s*\$([0-9.]+)", txt)
        if m_cost:
            try:
                spend_usd = float(m_cost[-1])
            except Exception:
                pass

        in_tweets = False
        for line in txt.splitlines():
            if line.startswith("### 推文原文"):
                in_tweets = True
                continue
            if in_tweets:
                if line.startswith("## ") or line.startswith("本次 AIsa"):
                    in_tweets = False
                    continue
                m_tw = re.match(r"-\s*\*\*(.+?)\*\*:\s*(.+)", line.strip())
                if m_tw:
                    tweets[m_tw.group(1).strip().lower()] = m_tw.group(2).strip()

        for line in txt.splitlines():
            line_s = line.strip()
            if not line_s.startswith("|") or line_s.startswith("|---") or "名字得分" in line_s:
                continue
            parts = [p.strip() for p in line_s.strip("|").split("|")]
            if len(parts) >= 5:
                term, sig, score_s, cov, ex = re.sub(r"\*+", "", parts[0]).strip(), parts[1], parts[2], parts[3], parts[4]
                try:
                    score = float(score_s)
                except Exception:
                    score = 0.5
                is_hf = "HF" in sig or "Hugging" in sig
                if is_hf:
                    hf_count += 1
                rows.append({
                    "term": term,
                    "signal": sig,
                    "score": score,
                    "covered": cov,
                    "example": tweets.get(term.lower(), ex),
                    "is_hf": is_hf,
                })

    db_path = ROOT / "repo" / "state" / "radar.db"
    if not rows and db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.execute(
                "SELECT term, signals, notes, named FROM leads WHERE first_seen = ? ORDER BY named DESC",
                (date_str,),
            )
            for term, sigs_j, notes_j, named in cur.fetchall():
                sigs = json.loads(sigs_j or "[]")
                notes = json.loads(notes_j or "[]")
                if not any(s in ("x", "hf") for s in sigs):
                    continue
                sig_str = " · ".join(notes) if notes else ",".join(sigs)
                is_hf = "hf" in sigs
                if is_hf:
                    hf_count += 1
                rows.append({
                    "term": term,
                    "signal": sig_str,
                    "score": float(named or 0.5),
                    "covered": "—",
                    "example": notes_map.get(term.lower(), ""),
                    "is_hf": is_hf,
                })
            conn.close()
        except Exception:
            pass

    primary_rows = []
    incidental_terms = []
    for r in rows:
        t_low = r["term"].lower()
        if t_low in NOISE_SOURCE_TERMS or r["score"] < 0.65:
            incidental_terms.append(r["term"])
            continue
        desc = notes_map.get(t_low, "")
        if not desc:
            ex = r.get("example", "")
            m_auth = re.match(r"(@[A-Za-z0-9_]+):\s*(.+)", ex)
            if m_auth:
                desc = f"来源 {m_auth.group(1)}：{m_auth.group(2)}"
            else:
                desc = ex or "社区新出现的高分名字信号"
        r["zh_desc"] = truncate_zh(desc, 44)
        primary_rows.append(r)

    return {
        "primary": primary_rows[:6],
        "incidental": incidental_terms[:6],
        "hf_count": hf_count,
        "spend_usd": spend_usd,
    }


def collect_xnew_data(date_str: str, mode: str) -> dict[str, Any]:
    """读取 xnew-YYYYMMDD-{am,pm}.json 并整理建站热词、AI新品与非模型动态。"""
    ymd = date_str.replace("-", "")
    am_data = load_json(ROOT / f"xnew-{ymd}-am.json", {}) or {}
    pm_data = load_json(ROOT / f"xnew-{ymd}-pm.json", {}) or {}

    if mode == "am":
        items = list(am_data.get("items") or [])
        window_note = f"{am_data.get('window_start', '昨日 21:20')} → {am_data.get('window_end', '今日 10:20')}"
        pm_empty_fallback = False
    else:
        pm_items = list(pm_data.get("items") or [])
        am_items = list(am_data.get("items") or [])
        pm_empty_fallback = len(pm_items) == 0 and len(am_items) > 0
        seen = set()
        items = []
        for it in pm_items + am_items:
            key = (it.get("name") or "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                it_copy = dict(it)
                if it in am_items and it not in pm_items:
                    it_copy["_shift"] = "上午档首发"
                else:
                    it_copy["_shift"] = "晚间档首发"
                items.append(it_copy)
        window_note = f"{date_str} 全天汇总（含 10:20 与 21:20 两档）"

    kw_items = [it for it in items if it.get("keyword_rank")]
    kw_items.sort(key=lambda x: int(x.get("keyword_rank") or 99))

    models = [it for it in items if it.get("kind") != "not_model" and not it.get("keyword_rank")]
    not_models = [it for it in items if it.get("kind") == "not_model" and not it.get("keyword_rank")]

    return {
        "kw_items": kw_items,
        "models": models,
        "not_models": not_models,
        "all_items": items,
        "window_note": window_note,
        "pm_empty_fallback": pm_empty_fallback,
    }


def estimate_pm_spend_and_board(date_str: str, report: dict, finders: dict) -> tuple[str, str]:
    """估算晚间日报 AIsa 花费与看板同步状态。"""
    spend = 0.0
    x_cost = ((report.get("x") or {}).get("cost_micros") or 0) / 1_000_000.0
    if x_cost > 0:
        spend += max(x_cost, 0.232)
    f_cost = (finders.get("spent_micros") or 0) / 1_000_000.0
    spend += f_cost
    doable_log = ROOT / "doable.log"
    if doable_log.exists():
        m = re.findall(r'"spent_usd":\s*([0-9.]+)', doable_log.read_text(encoding="utf-8", errors="ignore"))
        if m:
            try:
                spend += float(m[-1])
            except Exception:
                pass

    spend_str = f"约 ${spend:.2f}" if spend > 0 else "—"

    bp = load_json(ROOT / "board_payload.json", {}) or {}
    bp_label = bp.get("label", "")
    bp_count = len(bp.get("items") or [])
    if date_str in bp_label and bp_count > 0:
        board_str = f"已推送 ({bp_count} 词)"
    elif bp_count > 0:
        board_str = f"已推送 ({bp_count} 词)"
    else:
        board_str = "待推送"

    return spend_str, board_str


CSS_STYLE = """
@page {
  margin: 0;
}
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
body {
  width: 800px;
  background: #f4f6f9;
  color: #111827;
  font-family: 'Noto Sans CJK SC', 'PingFang SC', 'Hiragino Sans GB', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  font-variant-numeric: tabular-nums;
}
.canvas {
  padding: 22px 26px 24px 26px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

/* 顶部总览面板 */
.hero {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px 20px 15px 20px;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 13px;
  border-bottom: 1px solid #eef0f4;
}
.brand-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-dot {
  width: 10px;
  height: 22px;
  border-radius: 4px;
  background: #1d6fe0;
  flex-shrink: 0;
}
.brand-title {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  letter-spacing: -0.01em;
  white-space: nowrap;
}
.brand-sub {
  font-size: 12.5px;
  color: #6b7280;
  white-space: nowrap;
}
.shift-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
  white-space: nowrap;
}
.shift-pm {
  background: #eaf2ff;
  color: #1a56c4;
}
.shift-am {
  background: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
}

/* 顶部指标条（扁平分栏，不嵌套卡片） */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  padding-top: 13px;
  gap: 0;
}
.stat-cell {
  padding: 0 11px;
  border-right: 1px dashed #e5e7eb;
}
.stat-cell:first-child {
  padding-left: 2px;
}
.stat-cell:last-child {
  border-right: none;
  padding-right: 2px;
}
.stat-label {
  font-size: 11.5px;
  color: #6b7280;
  margin-bottom: 3px;
  white-space: nowrap;
}
.stat-val {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.stat-val.accent-amber {
  color: #b45309;
}
.stat-val.accent-blue {
  color: #1a56c4;
}
.stat-val.accent-emerald {
  color: #047857;
}
.stat-sub {
  font-size: 11px;
  color: #6b7280;
  margin-top: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 分区容器 */
.section {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
.sec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 18px;
  background: #fafbfc;
  border-bottom: 1px solid #eef0f4;
  gap: 10px;
}
.sec-subhead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 18px;
  background: #f8fafc;
  border-top: 1px solid #eef0f4;
  border-bottom: 1px solid #eef0f4;
  font-size: 12px;
  font-weight: 700;
  color: #334155;
}
.sec-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sec-title {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
}
.sec-count {
  font-size: 11.5px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  background: #eef2f6;
  color: #475569;
  white-space: nowrap;
}
.sec-note {
  font-size: 11.5px;
  color: #6b7280;
  white-space: nowrap;
}

/* 列表行（扁平分隔，无嵌套边框卡片） */
.item-list {
  display: flex;
  flex-direction: column;
}
.item-row {
  padding: 11px 18px;
  border-bottom: 1px dashed #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.item-row:last-child {
  border-bottom: none;
}
.item-row.kw-highlight {
  background: #fffbeb;
  border-left: 4px solid #f59e0b;
  padding-left: 14px;
}
.item-row.vac-highlight {
  background: #f0fdf4;
  border-left: 4px solid #10b981;
  padding-left: 14px;
}
.row-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.row-left {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
  flex-wrap: nowrap;
}
.item-name {
  font-size: 14.5px;
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
}
.row-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.item-desc {
  font-size: 13px;
  color: #374151;
  line-height: 1.42;
}
.item-sug {
  font-size: 12.5px;
  color: #92400e;
  font-weight: 600;
  margin-top: 1px;
}
.item-sug-emerald {
  font-size: 12.5px;
  color: #065f46;
  font-weight: 600;
  margin-top: 1px;
}

/* 标签 / 徽章 (全部禁止断行) */
.pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 600;
  line-height: 1.35;
  white-space: nowrap;
  flex-shrink: 0;
}
.pill-gold {
  background: #fde68a;
  color: #854d0e;
}
.pill-emerald {
  background: #d1fae5;
  color: #065f46;
}
.pill-blue {
  background: #dbeafe;
  color: #1e40af;
}
.pill-softblue {
  background: #eaf2ff;
  color: #1a56c4;
}
.pill-red {
  background: #fee2e2;
  color: #991b1b;
}
.pill-orange {
  background: #ffedd5;
  color: #9a3412;
}
.pill-amber {
  background: #fef3c7;
  color: #92400e;
}
.pill-indigo {
  background: #e0e7ff;
  color: #3730a3;
}
.pill-purple {
  background: #f3e8ff;
  color: #6b21a8;
}
.pill-gray {
  background: #f1f5f9;
  color: #475569;
}
.domain-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
  white-space: nowrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
.metric-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  background: #f8fafc;
  color: #334155;
  border: 1px solid #e2e8f0;
  white-space: nowrap;
}
.meta-text {
  font-size: 11.5px;
  color: #6b7280;
  white-space: nowrap;
}

/* 非新模型紧凑汇总行 */
.compact-group {
  padding: 9px 18px;
  background: #fafbfc;
  border-top: 1px solid #eef0f4;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.compact-label {
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
  display: flex;
  align-items: center;
  gap: 6px;
}
.compact-items {
  display: flex;
  flex-wrap: wrap;
  gap: 5px 12px;
  font-size: 12px;
  color: #4b5563;
}
.compact-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.compact-bullet {
  color: #9ca3af;
}

/* 可做的词 / KDROI 表格 */
.kw-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
}
.kw-table th {
  text-align: left;
  padding: 8px 12px;
  font-size: 11.5px;
  font-weight: 600;
  color: #6b7280;
  background: #fcfcfd;
  border-bottom: 1px solid #eef0f4;
  white-space: nowrap;
}
.kw-table th.num, .kw-table td.num {
  text-align: right;
  white-space: nowrap;
}
.kw-table td {
  padding: 9px 12px;
  border-bottom: 1px dashed #e5e7eb;
  vertical-align: middle;
}
.kw-table tr:last-child td {
  border-bottom: none;
}
.kw-table tr.row-pass td {
  background: #f0f7ff;
}
.kw-phrase {
  font-weight: 700;
  color: #111827;
  font-size: 13.5px;
  white-space: nowrap;
}
.kw-src-sub {
  font-size: 11px;
  color: #6b7280;
  margin-top: 2px;
  white-space: nowrap;
}
.kw-dom-sub {
  font-size: 11px;
  color: #047857;
  font-weight: 600;
  margin-top: 2px;
  white-space: nowrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
.kdroi-val {
  font-weight: 700;
  color: #1a56c4;
}
.kd-ok {
  color: #1e40af;
  font-weight: 600;
}
.kd-high {
  color: #b45309;
  font-weight: 600;
}

/* 底部页脚 */
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 4px 0 4px;
  font-size: 11.5px;
  color: #6b7280;
}
"""


def build_xnew_section_html(xnew: dict[str, Any], mode: str, doable: dict[str, Any] | None = None) -> str:
    kw_items = xnew["kw_items"]
    models = xnew["models"]
    not_models = xnew["not_models"]

    # Map name/phrase -> available_domains from doable.json if present
    dom_map: dict[str, list[str]] = {}
    if doable:
        for t in (doable.get("vacuum_terms") or []) + (doable.get("terms") or []):
            av = t.get("available_domains") or []
            if av:
                dom_map[t["phrase"].lower()] = av
                for nm in t.get("names") or []:
                    dom_map[nm.lower()] = av

    sec_note = xnew["window_note"]
    if mode == "pm" and xnew.get("pm_empty_fallback"):
        sec_note = "晚间窗口无新首发 · 以下为今日全天汇总"

    rows_html: list[str] = []

    # 1. Highlighted 建站热词
    for it in kw_items:
        rank = it.get("keyword_rank", 1)
        name = esc(it.get("name"))
        kw_str = it.get("keyword") or ""
        source = esc(it.get("source") or "X")
        first_seen = esc((it.get("first_seen") or "")[-11:])
        views = it.get("views")
        bms = it.get("bookmarks")
        backfill = " · 补报" if it.get("backfill") else ""

        metrics = []
        if views:
            metrics.append(f"👁 {fmt_num(views)}")
        if bms:
            metrics.append(f"🔖 {fmt_num(bms)}")
        metric_html = f'<span class="metric-badge">{" · ".join(metrics)}</span>' if metrics else ""

        av_doms = dom_map.get((it.get("name") or "").lower()) or dom_map.get(kw_str.lower()) or []
        dom_html = f'<span class="domain-badge">🟢 {esc(" · ".join(av_doms[:2]))}</span>' if av_doms else ""

        desc = esc(truncate_zh(it.get("desc") or "", 48))
        reason = esc(truncate_zh(it.get("reason") or "", 46))
        kw_hint = f"（搜索词：{esc(kw_str)}）" if kw_str and kw_str.lower() != (it.get("name") or "").lower() else ""

        rows_html.append(f"""
        <div class="item-row kw-highlight">
          <div class="row-top">
            <div class="row-left">
              <span class="pill pill-gold">🔑 建站热词 #{rank}</span>
              <span class="item-name">{name}</span>
              <span class="pill pill-blue">书签X{backfill}</span>
              {dom_html}
            </div>
            <div class="row-right">
              {metric_html}
              <span class="meta-text">{source} · {first_seen}</span>
            </div>
          </div>
          <div class="item-desc">{desc}</div>
          <div class="item-sug">💡 建站建议{kw_hint}：{reason}</div>
        </div>
        """)

    # 2. Regular AI 新品 (model)
    for it in models:
        name = esc(it.get("name"))
        source = esc(it.get("source") or "X")
        first_seen = esc((it.get("first_seen") or "")[-11:])
        views = it.get("views")
        bms = it.get("bookmarks")
        backfill = " · 补报" if it.get("backfill") else ""

        metrics = []
        if views:
            metrics.append(f"👁 {fmt_num(views)}")
        if bms:
            metrics.append(f"🔖 {fmt_num(bms)}")
        metric_html = f'<span class="metric-badge">{" · ".join(metrics)}</span>' if metrics else ""

        av_doms = dom_map.get((it.get("name") or "").lower()) or []
        dom_html = f'<span class="domain-badge">🟢 {esc(" · ".join(av_doms[:2]))}</span>' if av_doms else ""
        desc = esc(truncate_zh(it.get("desc") or "", 50))

        rows_html.append(f"""
        <div class="item-row">
          <div class="row-top">
            <div class="row-left">
              <span class="pill pill-softblue">🚀 AI 新品{backfill}</span>
              <span class="item-name">{name}</span>
              {dom_html}
            </div>
            <div class="row-right">
              {metric_html}
              <span class="meta-text">{source} · {first_seen}</span>
            </div>
          </div>
          <div class="item-desc">{desc}</div>
        </div>
        """)

    if not rows_html:
        rows_html.append("""
        <div class="item-row">
          <div class="item-desc" style="color:#6b7280;">本窗口重点账号无新模型首发，也无达到门槛（浏览 ≥50万 或 收藏 ≥1,000）的建站热词。</div>
        </div>
        """)

    not_model_html = ""
    if not_models:
        chips = []
        for nm in not_models[:5]:
            nm_name = esc(nm.get("name"))
            nm_src = esc(nm.get("source") or "")
            chips.append(f'<span class="compact-item"><span class="compact-bullet">•</span> <strong>{nm_name}</strong> <span class="meta-text">({nm_src})</span></span>')
        not_model_html = f"""
        <div class="compact-group">
          <div class="compact-label">
            <span class="pill pill-gray">📌 其它官方动态（非新模型 {len(not_models)} 条）</span>
            <span class="meta-text">仅作背景参考，不计入建站主词</span>
          </div>
          <div class="compact-items">
            {"".join(chips)}
          </div>
        </div>
        """

    return f"""
    <div class="section">
      <div class="sec-head">
        <div class="sec-title-wrap">
          <span class="sec-title">🔥 建站热词 &amp; AI 新品</span>
          <span class="sec-count">热词 {len(kw_items)} · 新品 {len(kw_items) + len(models)}</span>
        </div>
        <div class="sec-note">{esc(sec_note)}</div>
      </div>
      <div class="item-list">
        {"".join(rows_html)}
      </div>
      {not_model_html}
    </div>
    """


def split_doable_terms(doable: dict[str, Any]) -> tuple[list[dict], list[dict], list[dict], list[dict], int, int]:
    cfg = doable.get("config") or {}
    max_kd = int(cfg.get("max_kd", doable.get("max_kd", 31)))
    min_vol = int(cfg.get("min_volume", doable.get("min_volume", 500)))
    all_rows = list(doable.get("terms") or doable.get("all") or [])
    vacuum_terms = list(doable.get("vacuum_terms") or [t for t in all_rows if t.get("is_vacuum")])
    passed = list(doable.get("passed") or [
        t for t in all_rows if not (t.get("failed") or []) and not (t.get("unknown") or []) and (t.get("volume") or 0) >= min_vol
    ])
    almost = list(doable.get("almost") or [
        t for t in all_rows if len(t.get("failed") or []) == 1 and not (t.get("unknown") or [])
    ])
    passed.sort(key=lambda x: (not bool(x.get("tool_intent")), -float(x.get("kdroi") or 0)))
    almost.sort(key=lambda x: float(x.get("kdroi") or 0), reverse=True)
    return vacuum_terms, passed, almost, all_rows, max_kd, min_vol


def build_doable_section_html(doable: dict[str, Any]) -> str:
    vacuum_terms, passed, almost, all_rows, max_kd, min_vol = split_doable_terms(doable)
    checked = doable.get("candidates_checked", len(all_rows))
    filtered_out = list(doable.get("filtered_out") or [])

    # 1. SERP 真空期可抢列表（免月搜门槛）
    vac_rows_html: list[str] = []
    for vt in vacuum_terms[:6]:
        phrase = esc(vt.get("phrase"))
        src = esc(vt.get("source") or "新词池")
        ratio_pct = int((vt.get("vacuum_ratio") or 0) * 100)
        v_cnt = esc(vt.get("vacuum_count") or "")
        vol = vt.get("volume")
        vol_badge = f"月搜 {fmt_num(vol)}" if vol else "新词月搜 0"
        ev_str = esc(vt.get("vacuum_evidence") or "")
        sug_str = esc(vt.get("delivery_suggestion") or "适合做功能演练场与接入指南站")
        av_doms = vt.get("available_domains") or []
        if av_doms:
            dom_str = " · ".join(av_doms[:3])
            dom_badge = f'<span class="domain-badge">🟢 {esc(dom_str)} 可注册</span>'
        else:
            dom_badge = '<span class="metric-badge">同名域名已注册</span>'

        vac_rows_html.append(f"""
        <div class="item-row vac-highlight">
          <div class="row-top">
            <div class="row-left">
              <span class="pill pill-emerald">🔥 真空期 {ratio_pct}% ({v_cnt})</span>
              <span class="item-name">{phrase}</span>
              <span class="pill pill-softblue">{src}</span>
              <span class="meta-text">{vol_badge}</span>
            </div>
            <div class="row-right">
              {dom_badge}
            </div>
          </div>
          <div class="item-desc">🔍 SERP 证据：{ev_str}</div>
          <div class="item-sug-emerald">🛠️ 上线建议：{sug_str}</div>
        </div>
        """)

    vac_block_html = ""
    if vac_rows_html:
        vac_block_html = f"""
        <div class="sec-subhead">
          <span>🔥 SERP 真空期可抢（免月搜门槛 · Google 前 10 自然结果 ≥70% 为社媒/代码仓 · 0 独立产品站）</span>
          <span class="meta-text">官方 RDAP 实时核验域名可注册状态</span>
        </div>
        <div class="item-list">
          {"".join(vac_rows_html)}
        </div>
        """

    # 2. Semrush 常规筛词与 KDROI 榜
    display_rows: list[tuple[str, dict[str, Any]]] = []
    seen = set()
    for r in passed:
        p = r.get("phrase")
        if p and p not in seen:
            seen.add(p)
            display_rows.append(("pass", r))
    for r in almost:
        p = r.get("phrase")
        if p and p not in seen and len(display_rows) < 5:
            seen.add(p)
            display_rows.append(("almost", r))

    high_kdroi = [r for r in all_rows if (r.get("volume") or 0) >= min_vol and (r.get("kdroi") or 0) > 40]
    high_kdroi.sort(key=lambda x: float(x.get("kdroi") or 0), reverse=True)
    for r in high_kdroi:
        p = r.get("phrase")
        if p and p not in seen and len(display_rows) < 5:
            seen.add(p)
            display_rows.append(("watch", r))

    tbody = []
    for kind, r in display_rows:
        phrase = esc(r.get("phrase"))
        tool_tag = " 🛠" if r.get("tool_intent") else ""
        src = esc(truncate_zh(r.get("source") or "雷达词池", 18))
        vol = fmt_num(r.get("volume"))
        kd = r.get("kd")
        kd_cls = "kd-ok" if (kd is not None and kd <= max_kd) else "kd-high"
        kd_str = f"{kd:g}" if isinstance(kd, (int, float)) else "—"
        cpc = r.get("cpc")
        cpc_str = f"${cpc:.2f}" if isinstance(cpc, (int, float)) else "—"
        kdroi = r.get("kdroi")
        kdroi_str = f"{kdroi:.1f}" if isinstance(kdroi, (int, float)) else "—"
        ait = r.get("allintitle")
        ait_str = fmt_num(ait) if ait is not None else "—"
        weak = r.get("small_sites") if r.get("small_sites") is not None else r.get("weak_sites")
        weak_str = f"小站 {weak}/10" if weak is not None else "—"

        fails = r.get("failed") or r.get("fails") or []
        verdict_raw = r.get("verdict") or (r.get("competition") or {}).get("verdict") or ""
        verdict_map = {"open": "能进", "mixed": "一般", "hard": "难"}
        verdict = verdict_map.get(verdict_raw, verdict_raw)
        names_hint = " · ".join((r.get("names") or [])[:1])
        if names_hint and names_hint.lower() != (r.get("phrase") or "").lower():
            src = f"{src} ({truncate_zh(names_hint, 14)})"

        av_doms = r.get("available_domains") or []
        dom_sub = f'<div class="kw-dom-sub">🟢 {esc(" · ".join(av_doms[:2]))} 可注册</div>' if av_doms else ""

        if kind == "pass":
            status_html = '<span class="pill pill-blue">✅ 全过门槛</span>'
        elif kind == "almost":
            fail_reason = fails[0] if fails else "差一项"
            if fail_reason == "首页竞争":
                fail_reason = "已有同名站占坑" if r.get("dedicated_sites") else f"首页竞争({verdict})"
            elif fail_reason.startswith("KD"):
                fail_reason = f"KD {kd_str} &gt; {max_kd}"
            status_html = f'<span class="pill pill-amber">⚡ 差1项：{esc(fail_reason)}</span>'
        else:
            status_html = f'<span class="pill pill-gray">🔎 高KDROI观察 (KD {kd_str})</span>'

        row_cls = "row-pass" if kind == "pass" else ""
        tbody.append(f"""
        <tr class="{row_cls}">
          <td>
            <div class="kw-phrase">{phrase}{tool_tag}</div>
            <div class="kw-src-sub">来源：{src}</div>
            {dom_sub}
          </td>
          <td class="num">{vol}</td>
          <td class="num"><span class="{kd_cls}">{kd_str}</span></td>
          <td class="num">{cpc_str}</td>
          <td class="num kdroi-val">{kdroi_str}</td>
          <td class="num">{ait_str} · {weak_str}</td>
          <td>{status_html}</td>
        </tr>
        """)

    if not tbody:
        tbody.append("""
        <tr>
          <td colspan="7" style="text-align:center;color:#6b7280;padding:16px;">今日候选词池暂无达到月搜门槛的词条</td>
        </tr>
        """)

    # 3. 语义预筛拦截脚注
    filter_footer_html = ""
    if filtered_out:
        sample_dropped = []
        for x in filtered_out:
            ph = x.get("phrase") or ""
            if ph and ph not in sample_dropped and any(k in ph for k in (" vs ", "bra", "gpu", "age", "domino", "youtube", "assessment", "sahara")):
                sample_dropped.append(ph)
        if len(sample_dropped) < 5:
            for x in filtered_out:
                ph = x.get("phrase") or ""
                if ph and ph not in sample_dropped:
                    sample_dropped.append(ph)
                if len(sample_dropped) >= 6:
                    break
        dropped_str = "、".join(esc(p) for p in sample_dropped[:6])
        filter_footer_html = f"""
        <div class="compact-group">
          <div class="compact-label">
            <span class="pill pill-gray">🛡️ 语义预筛前置拦截（共剔除 {len(filtered_out)} 个噪音词）</span>
            <span class="meta-text">已自动过滤赛事比分、娱乐八卦、纯大厂品牌及非网页交付词（如 {dropped_str} 等）</span>
          </div>
        </div>
        """

    return f"""
    <div class="section">
      <div class="sec-head">
        <div class="sec-title-wrap">
          <span class="sec-title">🎯 可做的词 &amp; SERP 真空期可抢</span>
          <span class="sec-count">🔥 真空期 {len(vacuum_terms)} · ✅ 全过 {len(passed)} · ⚡ 差一项 {len(almost)}（净查 {checked} 词）</span>
        </div>
        <div class="sec-note">常规门槛：月搜 ≥{min_vol} · KD ≤{max_kd} · 首页能进 · allintitle &lt;1万</div>
      </div>
      {vac_block_html}
      <div class="sec-subhead">
        <span>📊 Semrush 常规筛词与 KDROI 榜（带 🛠 为工具意图优先词）</span>
        <span class="meta-text">KDROI = 月搜 × CPC ÷ KD</span>
      </div>
      <table class="kw-table">
        <thead>
          <tr>
            <th>候选词 / 来源 / 可注册域名</th>
            <th class="num">美区月搜</th>
            <th class="num">KD</th>
            <th class="num">CPC</th>
            <th class="num">KDROI</th>
            <th class="num">allintitle · 小站</th>
            <th>筛词结论</th>
          </tr>
        </thead>
        <tbody>
          {"".join(tbody)}
        </tbody>
      </table>
      {filter_footer_html}
    </div>
    """


def build_pm_signals_section_html(
    report: dict[str, Any],
    finders: dict[str, Any],
    notes_map: dict[str, str],
) -> str:
    rows_html: list[str] = []

    # 1. GitHub 爆发 (Top 3 new + Top 2 surging)
    repos = list((report.get("breakout") or {}).get("repos") or [])
    new_repos = [r for r in repos if r.get("new")]
    new_repos.sort(key=lambda x: int(x.get("delta") or x.get("stars") or 0), reverse=True)
    surging_repos = [r for r in repos if not r.get("new")]
    surging_repos.sort(key=lambda x: int(x.get("delta") or 0), reverse=True)

    picked_repos = new_repos[:3] + surging_repos[:2]
    for r in picked_repos:
        full_repo = r.get("repo") or ""
        short_name = full_repo.split("/")[-1] if "/" in full_repo else full_repo
        is_new = bool(r.get("new"))
        stars = fmt_num(r.get("stars"))
        delta = r.get("delta")
        vel = r.get("velocity")
        if delta:
            badge_txt = f"★ {stars} (+{fmt_num(delta)}/天)"
        elif vel:
            badge_txt = f"★ {stars} (均+{fmt_num(vel)}/天)"
        else:
            badge_txt = f"★ {stars}"

        pill_cls = "pill-red" if is_new else "pill-orange"
        pill_lbl = "GitHub 🆕 新爆发" if is_new else "GitHub 🔥 持续暴涨"
        zh_desc = esc(clean_repo_desc(full_repo, r.get("description") or "", notes_map))

        rows_html.append(f"""
        <div class="item-row">
          <div class="row-top">
            <div class="row-left">
              <span class="pill {pill_cls}">{pill_lbl}</span>
              <span class="item-name">{esc(short_name)}</span>
              <span class="meta-text">({esc(full_repo)})</span>
            </div>
            <div class="row-right">
              <span class="metric-badge">{esc(badge_txt)}</span>
            </div>
          </div>
          <div class="item-desc">{zh_desc}</div>
        </div>
        """)

    # 2. Hugging Face 新进榜
    hf_terms = list((report.get("hf") or {}).get("terms") or [])
    for ht in hf_terms[:2]:
        term = ht.get("term") or ""
        notes = " · ".join(ht.get("notes") or ["HF 热门新上榜"])
        ex_list = ht.get("examples") or []
        ex0 = ex_list[0] if ex_list else ""
        if isinstance(ex0, dict):
            model_id = ex0.get("id") or term
            likes = ex0.get("likes")
            badge = f"{notes}" + (f" · ♥ {fmt_num(likes)}" if likes else "")
        else:
            ex_s = str(ex0)
            model_id = ex_s.split(" (")[0].strip() if ex_s else term
            m_lk = re.search(r"♥\s*([0-9,]+)", ex_s)
            badge = f"{notes}" + (f" · ♥ {m_lk.group(1)}" if m_lk else "")
        zh_desc = notes_map.get(term.lower(), f"Hugging Face 热门榜新上榜模型：{model_id}")

        rows_html.append(f"""
        <div class="item-row">
          <div class="row-top">
            <div class="row-left">
              <span class="pill pill-amber">HF 热门榜</span>
              <span class="item-name">{esc(model_id)}</span>
            </div>
            <div class="row-right">
              <span class="metric-badge">{esc(badge)}</span>
            </div>
          </div>
          <div class="item-desc">{esc(truncate_zh(zh_desc, 46))}</div>
        </div>
        """)

    # 3. Trends AI 种子词 Rising 飙升发现 (New!)
    seed_rising = list((finders.get("trends") or {}).get("seed_rising") or [])
    trends_fresh = list((finders.get("trends") or {}).get("fresh") or [])
    if seed_rising:
        top_sr = [f"{s.get('query')} (+{s.get('value')}%)" for s in seed_rising[:4]]
        sr_title = " · ".join(top_sr)
        rows_html.append(f"""
        <div class="item-row">
          <div class="row-top">
            <div class="row-left">
              <span class="pill pill-purple">Trends AI 种子词飙升</span>
              <span class="item-name">{esc(truncate_zh(sr_title, 44))}</span>
            </div>
            <div class="row-right">
              <span class="metric-badge">AI 飙升新词 {len(seed_rising)} 个</span>
            </div>
          </div>
          <div class="item-desc">监控 8 个 AI 种子词（ai tool / generator / video / agent / llm / mcp）美区 Rising ≥+100% 新词。</div>
        </div>
        """)

    # 4. App Store 美区免费榜（仅保留 AI/工具类）& 竞品站动向
    apps_kept = list((finders.get("appstore") or {}).get("kept_ai_apps") or [])
    apps_new = list((finders.get("appstore") or {}).get("new") or [])
    sitemap_counts = (report.get("sitemap") or {}).get("site_counts") or {}
    sm_summary = "、".join(f"{k}(+{v})" for k, v in list(sitemap_counts.items())[:2]) if sitemap_counts else "无显著批量铺页"

    if apps_kept or apps_new or sm_summary:
        if apps_kept:
            app_str = " · ".join(f"{a.get('name')} (#{a.get('rank')})" for a in apps_kept[:2])
        elif apps_new:
            app_str = " · ".join(f"{a.get('name')} (#{a.get('rank')})" for a in apps_new[:2])
        else:
            app_str = "今日无新增 AI 免费榜应用"
        rows_html.append(f"""
        <div class="item-row">
          <div class="row-top">
            <div class="row-left">
              <span class="pill pill-indigo">App Store &amp; 竞品</span>
              <span class="item-name">{esc(truncate_zh(app_str, 42))}</span>
            </div>
            <div class="row-right">
              <span class="metric-badge">AI 应用 {len(apps_kept)} 款 · 榜单新进 {len(apps_new)} 款</span>
            </div>
          </div>
          <div class="item-desc">仅对 AI/工具类新上榜 App 派生 web/alternative 词；竞品站动态：{esc(sm_summary)}。</div>
        </div>
        """)

    return f"""
    <div class="section">
      <div class="sec-head">
        <div class="sec-title-wrap">
          <span class="sec-title">📡 重点信号精选（GitHub / Trends AI 飙升 / 榜单）</span>
          <span class="sec-count">精选 {len(rows_html)} 组</span>
        </div>
        <div class="sec-note">已剔除低价值泛词与常规噪音，仅展示高增信号</div>
      </div>
      <div class="item-list">
        {"".join(rows_html)}
      </div>
    </div>
    """


def build_am_sources_section_html(src_info: dict[str, Any]) -> str:
    primary = src_info["primary"]
    incidental = src_info["incidental"]
    hf_count = src_info["hf_count"]

    rows_html: list[str] = []
    for r in primary:
        term = esc(r["term"])
        sig = esc(r["signal"])
        score = f"{r['score']:.2f}"
        pill_cls = "pill-amber" if r["is_hf"] else "pill-softblue"
        pill_lbl = "HF 热门榜" if r["is_hf"] else "X 社区新词"
        rows_html.append(f"""
        <div class="item-row">
          <div class="row-top">
            <div class="row-left">
              <span class="pill {pill_cls}">{pill_lbl}</span>
              <span class="item-name">{term}</span>
            </div>
            <div class="row-right">
              <span class="metric-badge">{sig} · 名字得分 {score}</span>
            </div>
          </div>
          <div class="item-desc">{esc(r["zh_desc"])}</div>
        </div>
        """)

    if hf_count == 0:
        rows_html.append("""
        <div class="item-row">
          <div class="row-top">
            <div class="row-left">
              <span class="pill pill-amber">HF 热门榜</span>
              <span class="item-name" style="font-weight:600;color:#4b5563;">本轮无新进榜名字</span>
            </div>
            <div class="row-right">
              <span class="meta-text">Hugging Face Trending 扫描正常</span>
            </div>
          </div>
          <div class="item-desc" style="color:#6b7280;">当前在榜模型均已在前序轮次入库覆盖。</div>
        </div>
        """)

    inc_html = ""
    if incidental:
        inc_str = "、".join(esc(x) for x in incidental)
        inc_html = f"""
        <div class="compact-group">
          <div class="compact-label">
            <span class="pill pill-gray">已过滤顺带提及的老词</span>
            <span class="meta-text">{inc_str}（非新产品，不进筛词池）</span>
          </div>
        </div>
        """

    return f"""
    <div class="section">
      <div class="sec-head">
        <div class="sec-title-wrap">
          <span class="sec-title">📡 源头新名字扫描（X 社区 &amp; Hugging Face）</span>
          <span class="sec-count">高分新名 {len(primary)} · HF {hf_count}</span>
        </div>
        <div class="sec-note">AIsa 监控 35 个 AI 重点账号 + HF 趋势榜</div>
      </div>
      <div class="item-list">
        {"".join(rows_html)}
      </div>
      {inc_html}
    </div>
    """


def render_html(mode: str, date_str: str, balance_str: str | None = None) -> str:
    notes_map = load_custom_notes()
    xnew = collect_xnew_data(date_str, mode)
    kw_count = len(xnew["kw_items"])
    model_count = kw_count + len(xnew["models"])
    not_model_count = len(xnew["not_models"])

    kw_names = "、".join(it.get("name", "") for it in xnew["kw_items"]) or "本档无达标"

    if mode == "am":
        src_info = parse_sources_am(date_str, notes_map)
        spend_val = f"${src_info['spend_usd']:.3f}" if src_info["spend_usd"] is not None else "$0.099"
        spend_sub = f"余额 {balance_str}" if balance_str else "模型判断另计"

        hero_html = f"""
        <div class="hero">
          <div class="hero-top">
            <div class="brand-wrap">
              <div class="brand-dot"></div>
              <div>
                <div class="brand-title">新词雷达 · 上午扫描简报</div>
                <div class="brand-sub">书签X AI 新品首发 + 建站热词 + X / Hugging Face 源头新名</div>
              </div>
            </div>
            <div class="shift-badge shift-am">☀️ {esc(date_str)} · 10:20 上午档</div>
          </div>
          <div class="stats-bar">
            <div class="stat-cell">
              <div class="stat-label">🔥 建站热词</div>
              <div class="stat-val accent-amber">{kw_count} 个</div>
              <div class="stat-sub">{esc(truncate_zh(kw_names, 14))}</div>
            </div>
            <div class="stat-cell">
              <div class="stat-label">🚀 AI 新品首发</div>
              <div class="stat-val accent-blue">{model_count} 个</div>
              <div class="stat-sub">另有非模型动态 {not_model_count} 条</div>
            </div>
            <div class="stat-cell">
              <div class="stat-label">📡 源头高分新名</div>
              <div class="stat-val">{len(src_info['primary'])} 个</div>
              <div class="stat-sub">HF 新上榜 {src_info['hf_count']} 个</div>
            </div>
            <div class="stat-cell">
              <div class="stat-label">🎯 真空期 &amp; 筛词</div>
              <div class="stat-val">21:20 汇总</div>
              <div class="stat-sub">晚报查 SERP + 域名</div>
            </div>
            <div class="stat-cell">
              <div class="stat-label">💰 本轮 AIsa 花费</div>
              <div class="stat-val">{esc(spend_val)}</div>
              <div class="stat-sub">{esc(spend_sub)}</div>
            </div>
          </div>
        </div>
        """

        sec1 = build_xnew_section_html(xnew, mode="am")
        sec2 = build_am_sources_section_html(src_info)
        body_sections = sec1 + sec2
        footer_left = "💡 提示：图中首发帖与仓库的可点击链接已附在随图短消息中"
        footer_right = f"新词雷达 · 北京时间 {date_str} 10:20 (UTC+8)"

    else:
        report = load_json(ROOT / "report.json", {}) or {}
        doable = load_json(ROOT / "doable.json", {}) or {}
        finders = load_json(ROOT / "finders.json", {}) or {}

        vacuum_list, passed_list, almost_list, all_doable_rows, max_kd_val, _ = split_doable_terms(doable)
        vac_cnt = len(vacuum_list)
        passed_cnt = len(passed_list)
        filtered_cnt = len(doable.get("filtered_out") or [])
        spend_str, board_str = estimate_pm_spend_and_board(date_str, report, finders)
        spend_sub = f"余额 {balance_str}" if balance_str else f"KD ≤{max_kd_val} · 含RDAP查域名"

        hero_html = f"""
        <div class="hero">
          <div class="hero-top">
            <div class="brand-wrap">
              <div class="brand-dot"></div>
              <div>
                <div class="brand-title">新词雷达 · 晚间合并日报</div>
                <div class="brand-sub">AI 新品与建站热词 · SERP 真空期与 RDAP 域名 · Semrush KDROI 筛词</div>
              </div>
            </div>
            <div class="shift-badge shift-pm">🌙 {esc(date_str)} · 21:20 晚报</div>
          </div>
          <div class="stats-bar">
            <div class="stat-cell">
              <div class="stat-label">🔥 今日建站热词</div>
              <div class="stat-val accent-amber">{kw_count} 个</div>
              <div class="stat-sub">{esc(truncate_zh(kw_names, 14))}</div>
            </div>
            <div class="stat-cell">
              <div class="stat-label">🚀 今日 AI 新品</div>
              <div class="stat-val accent-blue">{model_count} 个</div>
              <div class="stat-sub">非新模型动态 {not_model_count} 条</div>
            </div>
            <div class="stat-cell">
              <div class="stat-label">🎯 真空期 &amp; 可做词</div>
              <div class="stat-val accent-emerald">{vac_cnt} 真空 / {passed_cnt} 全过</div>
              <div class="stat-sub">净筛 {len(all_doable_rows)} 词 · 滤噪 {filtered_cnt}</div>
            </div>
            <div class="stat-cell">
              <div class="stat-label">📌 看板同步状态</div>
              <div class="stat-val">{esc(board_str)}</div>
              <div class="stat-sub">标签 {esc(date_str)} 新词雷达</div>
            </div>
            <div class="stat-cell">
              <div class="stat-label">💰 本轮 AIsa 花费</div>
              <div class="stat-val">{esc(spend_str)}</div>
              <div class="stat-sub">{esc(spend_sub)}</div>
            </div>
          </div>
        </div>
        """

        sec1 = build_xnew_section_html(xnew, mode="pm", doable=doable)
        sec2 = build_doable_section_html(doable)
        sec3 = build_pm_signals_section_html(report, finders, notes_map)
        body_sections = sec1 + sec2 + sec3
        footer_left = "💡 提示：全流程只读（RDAP 仅查可注册状态，绝不自动买域名/发帖）"
        footer_right = f"新词雷达 · 北京时间 {date_str} 21:20 (UTC+8)"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>{CSS_STYLE}</style>
</head>
<body>
  <div class="canvas" id="card-root">
    {hero_html}
    {body_sections}
    <div class="footer">
      <span>{esc(footer_left)}</span>
      <span>{esc(footer_right)}</span>
    </div>
  </div>
</body>
</html>
"""


def render_png(html_str: str, out_paths: list[pathlib.Path]) -> tuple[int, int]:
    from playwright.sync_api import sync_playwright
    from PIL import Image

    tmp_html = ROOT / ".tmp_card_render.html"
    tmp_html.write_text(html_str, encoding="utf-8")

    primary_out = out_paths[0]
    primary_out.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            viewport={"width": 800, "height": 600},
            device_scale_factor=2,
        )
        page = context.new_page()
        page.goto(f"file://{tmp_html.resolve()}", wait_until="networkidle")
        page.wait_for_timeout(150)
        locator = page.locator("#card-root")
        locator.screenshot(path=str(primary_out))
        browser.close()

    try:
        tmp_html.unlink()
    except Exception:
        pass

    for extra in out_paths[1:]:
        if extra.resolve() != primary_out.resolve():
            shutil.copyfile(primary_out, extra)

    with Image.open(primary_out) as im:
        return im.size


def main() -> None:
    ap = argparse.ArgumentParser(description="生成新词雷达图文卡片 PNG")
    ap.add_argument(
        "--mode",
        choices=["am", "pm", "morning", "daily"],
        default="pm",
        help="am/morning: 10:20 上午扫描; pm/daily: 21:20 晚间日报 (默认 pm)",
    )
    ap.add_argument(
        "--date",
        default=None,
        help="日期 YYYY-MM-DD（默认：am 取今日，pm 取 doable.json 日期或今日）",
    )
    ap.add_argument(
        "--balance",
        default=None,
        help="可选：显示 AIsa 余额（例如 '$5.99'）",
    )
    ap.add_argument(
        "--out",
        default=None,
        help="可选：额外输出的 PNG 路径",
    )
    args = ap.parse_args()

    norm_mode = "am" if args.mode in ("am", "morning") else "pm"

    if args.date:
        date_str = args.date
    else:
        if norm_mode == "pm":
            doable = load_json(ROOT / "doable.json", {}) or {}
            date_str = doable.get("day") or dt.datetime.now().strftime("%Y-%m-%d")
        else:
            date_str = dt.datetime.now().strftime("%Y-%m-%d")

    ymd = date_str.replace("-", "")
    dated_out = ROOT / f"card-{ymd}-{norm_mode}.png"
    latest_out = ROOT / f"card-{norm_mode}.png"
    out_paths = [dated_out, latest_out]
    if args.out:
        out_paths.append(pathlib.Path(args.out))

    html_str = render_html(norm_mode, date_str, balance_str=args.balance)
    w, h = render_png(html_str, out_paths)
    print(json.dumps({
        "ok": True,
        "mode": norm_mode,
        "date": date_str,
        "width_px": w,
        "height_px": h,
        "files": [str(p) for p in out_paths],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
