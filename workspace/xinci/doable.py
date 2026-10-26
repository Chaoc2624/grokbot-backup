#!/usr/bin/env python3
"""可做的词 + SERP 真空期扫描 + 精确域名可注册检查: post-step for the nightly new-term-radar report.

升级功能（2026-10-25）：
1) 前置语义预筛（能否用简单网站交付）：剔除体育比分、名人八卦、大厂纯品牌导航、涉黄赌毒、词典常识及无法用简单网页交付的底层硬件/内核词。
2) SERP 真空期通道（免月搜门槛）：对新爆发候选词（建站热词、AI新品、GitHub/HF 新爆发、Trends AI 种子词 Rising、Google 补全）抓取 Google 美区前 10 自然结果；
   若论坛/社交/问答/代码仓/模型库/视频/科技资讯占比 >= 70% 且无独立产品站占坑，直接标为「🔥 真空期可抢」(is_vacuum: true)。
3) 自动查候选域名可注册状态（RDAP 只读查询，绝不注册或下单）：对可做词、真空期词、建站热词及差一项词生成 SEO 候选域名（优先 exact-match .com，兼顾 .ai / .io / .org），查询 Verisign / PIR / IdentityDigital RDAP。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE / "repo"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))

DEFAULTS = {
    "min_volume": 500,        # 月搜 >= this
    "max_kd": 31,             # Semrush KD <= this
    "min_cpc": 0.01,          # CPC must be present and >= this (USD)
    "need_open_serp": True,   # 首页竞争 must be 能进 (open)
    "database": "us",
    "max_terms": 60,
    "max_spend_usd": 0.50,
    "cache_days": 7,
    "serp_fetch": True,       # read page one ($0.002) for terms with no competition data that pass volume+CPC
    "serp_location_code": 2840,
    # 2026-10-22 筛词升级
    "kd_min_volume": 100,       # 月搜低于此不再花钱查 KD（预筛）
    "max_allintitle": 10000,    # allintitle 结果数上限
    "check_allintitle": True,   # 对过了月搜+CPC 的词查 allintitle（DataForSEO SERP，经 AIsa）
    "need_small_sites": False,  # True 时「首页小站居多」也算门槛；默认只展示
    "small_sites_min": 5,       # 首页前 10 里非大站 >= 此数算小站居多
    "tool_intent_bonus": 15,
    # 2026-10-25 真空期与域名可注册升级
    "vacuum_enabled": True,
    "vacuum_min_ratio": 0.70,
    "vacuum_max_serp_checks": 18,
    "check_domains": True,
    "domain_tlds": ["com", "ai", "io", "org"],
}
TOOL_INTENT = re.compile(
    r"\b(generator|converter|maker|checker|editor|creator|detector|remover|downloader|translator|calculator|upscaler|"
    r"playground|online|free|alternative|demo)\b",
    re.I,
)
BIG = (
    "wikipedia.org", "youtube.com", "reddit.com", "amazon.com", "github.com", "google.com", "apple.com", "microsoft.com",
    "facebook.com", "x.com", "twitter.com", "linkedin.com", "medium.com", "quora.com", "forbes.com", "nytimes.com",
    "cnn.com", "bbc.com", "theverge.com", "techcrunch.com", "instagram.com", "tiktok.com", "huggingface.co",
    "openai.com", "anthropic.com", "adobe.com", "canva.com", "zapier.com", "g2.com", "capterra.com", "pcmag.com",
    "cnet.com", "wired.com", "nvidia.com", "meta.com", "ibm.com", "aws.amazon.com", "yahoo.com", "ebay.com", "walmart.com",
)

# SERP 真空期分类白名单：论坛/社媒/问答、代码仓/模型库/开发文档、视频、综合科技媒体/博客/评测库
VACUUM_SOCIAL_FORUM = (
    "reddit.com", "x.com", "twitter.com", "news.ycombinator.com", "quora.com", "stackoverflow.com", "stackexchange.com",
    "facebook.com", "instagram.com", "tiktok.com", "linkedin.com", "threads.net", "bsky.app", "discord.com",
    "pinterest.com", "zhihu.com", "v2ex.com", "linux.do",
)
VACUUM_REPO_HUB_DOCS = (
    "github.com", "gist.github.com", "gitlab.com", "huggingface.co", "modelscope.cn", "modelscope.ai", "ollama.com",
    "lmstudio.ai", "unsloth.ai", "arxiv.org", "openreview.net", "paperswithcode.com", "kaggle.com", "pypi.org",
    "npmjs.com", "crates.io", "docs.comfy.org", "developers.cloudflare.com", "developers.redhat.com", "gofastmcp.com",
)
VACUUM_VIDEO = (
    "youtube.com", "youtu.be", "vimeo.com", "bilibili.com", "twitch.tv",
)
VACUUM_NEWS_MEDIA_BLOG = (
    "medium.com", "substack.com", "dev.to", "hashnode.dev", "hackernoon.com", "marktechpost.com", "theverge.com",
    "mashable.com", "techcrunch.com", "wired.com", "venturebeat.com", "arstechnica.com", "forbes.com", "thenewstack.io",
    "wikipedia.org", "indiatimes.com", "economictimes.indiatimes.com", "aiweekly.co", "lucumr.pocoo.org",
    "artificialanalysis.ai", "benchlm.ai", "llmbase.ai",
)
OFFICIAL_UMBRELLA_DOMAINS = (
    "block.xyz", "nvidia.com", "research.nvidia.com", "build.nvidia.com", "openmoss.ai", "openai.com", "anthropic.com",
    "deepmind.google", "blog.google", "ai.meta.com", "mistral.ai", "moonshot.cn", "kimi.ai",
)
APP_STORE_DOMAINS = (
    "apps.apple.com", "play.google.com", "chromewebstore.google.com", "marketplace.visualstudio.com",
)

# 单字易重名 AI 新品 -> 自动附加 " ai" 进行搜索与真空期检验，避免查到同名歌手或日常词
AMBIGUOUS_SINGLE_AI_NAMES = {"dessa", "flint", "spark", "sage", "moss", "mercury"}

PRICE = {"overview": 1000, "kd": 5000, "serp": 2000}   # micro-USD estimates, per keyword
OVERVIEW = "get_semrush_keyword_overview"
KD = "get_semrush_keyword_difficulty"
VERDICT_ZH = {"open": "能进", "mixed": "一般", "crowded": "挤满", None: "未查"}
KIND_ZH = {"tool": "工具", "list": "榜单", "article": "文章", "video": "视频", "forum": "论坛"}


def load_env():
    if os.environ.get("AISA_API_KEY"):
        return
    env = HERE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip().removeprefix("export ").strip(), v.strip().strip('"').strip("'"))


def config() -> dict:
    cfg = dict(DEFAULTS)
    p = HERE / "doable_config.json"
    if p.exists():
        cfg.update(json.loads(p.read_text()))
    return cfg


def semantic_prescreen(phrase: str, source: str = "", evidence: str = "") -> tuple[bool, str]:
    """调用 finders.classify_keyword_filter 执行前置语义预筛（淘汰含义不明、巨头导航、球赛八卦、涉黄赌毒、非简单网页可交付词）。"""
    try:
        from finders import classify_keyword_filter
        return classify_keyword_filter(phrase, source, evidence)
    except Exception:
        return True, ""


# ---------- collect ----------
def collect(report: dict, extra: list, cap: int, report_day: str, filtered_out: list[dict]) -> list[dict]:
    kw = report.get("keywords") or {}
    out: dict[str, dict] = {}
    seen_filtered: set[str] = set()

    def add(phrase: str, **info):
        p = " ".join((phrase or "").lower().split())
        if not p:
            return
        src = info.get("source") or "雷达"
        ev = info.get("evidence") or ""
        # 单字易歧义的 AI 新品（如 dessa -> dessa ai），确保查询指向 AI 模型而非同名歌手
        if p in AMBIGUOUS_SINGLE_AI_NAMES and ("书签" in src or "看板" in src or "AI新品" in src):
            orig_name = info.get("names") or [phrase]
            p = f"{p} ai"
            info["names"] = orig_name
        ok, reason = semantic_prescreen(p, src, ev)
        if not ok:
            if p not in seen_filtered:
                seen_filtered.add(p)
                filtered_out.append({"phrase": p, "source": src, "reason": reason})
            return
        if p not in out:
            out[p] = {"phrase": p, **info}
        else:
            # 合并标记
            if info.get("is_vacuum_candidate"):
                out[p]["is_vacuum_candidate"] = True
            if info.get("is_hot_keyword"):
                out[p]["is_hot_keyword"] = True

    # 1) 优先收集当日 AI 新品与建站热词（来自 xnew-YYYYMMDD-*.json 与 board_keywords.json）
    day_compact = report_day.replace("-", "")
    for pat in (f"xnew-{day_compact}-*.json",):
        for xp in sorted(HERE.glob(pat)):
            try:
                xd = json.loads(xp.read_text())
                for it in xd.get("items", []):
                    if it.get("kind") == "not_model":
                        continue
                    raw_kw = it.get("keyword") or it.get("name") or ""
                    is_hot = bool(it.get("keyword_rank"))
                    add(
                        raw_kw,
                        source="书签X·建站热词" if is_hot else "书签X·AI新品",
                        names=[it.get("name") or raw_kw],
                        evidence=it.get("reason") or it.get("desc") or "",
                        is_vacuum_candidate=True,
                        is_hot_keyword=is_hot,
                    )
            except Exception:
                pass

    # 2) 收集 extra（board_keywords.json + finder_keywords.json）
    for t in extra:
        if isinstance(t, dict):
            src = t.get("source") or "看板X"
            is_vac = bool(
                t.get("is_vacuum_candidate")
                or "书签" in src
                or "看板" in src
                or "Trends AI飙升" in src
                or "Google 补全" in src
                or "Hacker News" in src
            )
            add(
                t.get("phrase", ""),
                source=src,
                names=t.get("names") or [],
                evidence=t.get("evidence") or "",
                is_vacuum_candidate=is_vac,
                is_hot_keyword=("书签" in src or "看板" in src),
            )
        else:
            add(t, source="手动", names=[], evidence="", is_vacuum_candidate=True)

    # 3) 收集 report.json 里的 GitHub / HF / X 新爆发名字（named >= 0.8 且通过网页可交付语义预筛）
    for l in report.get("leads", []):
        kinds = l.get("kinds") or []
        if (l.get("named") or 0) >= 0.8 and any(k in ("breakout", "hf", "x") for k in kinds):
            lname = l.get("name") or ""
            ev = "；".join((l.get("examples") or l.get("signals") or [])[:1])
            add(
                lname,
                source="GitHub/HF 新爆发",
                names=[lname],
                evidence=ev,
                is_vacuum_candidate=True,
            )

    # 4) 收集 report.json 里的通用词（generic）
    for r in kw.get("rows", []):
        if r.get("kind") != "generic" or r.get("brand"):
            continue
        src = "🔎 相关查询" if r.get("source") == "searched" else "模型提取"
        add(
            r["phrase"],
            source=src,
            names=r.get("names") or [],
            evidence=r.get("evidence") or "",
            competition=r.get("competition"),
            radar_volume=r.get("volume"),
            decision=r.get("decision"),
            is_vacuum_candidate=False,
        )

    return list(out.values())[:cap]


# ---------- cache ----------
def load_cache(days: int) -> dict:
    p = HERE / "doable_cache.json"
    if not p.exists():
        return {}
    held = json.loads(p.read_text())
    today = date.today()
    out = {}
    for k, v in held.items():
        if k == "_domains" and isinstance(v, dict):
            out[k] = v
            continue
        if isinstance(v, dict) and v.get("day"):
            try:
                if (today - date.fromisoformat(v["day"])).days < days:
                    out[k] = v
            except Exception:
                pass
    return out


def save_cache(cache: dict):
    (HERE / "doable_cache.json").write_text(json.dumps(cache, ensure_ascii=False, indent=1))


# ---------- fetch ----------
class Budget:
    def __init__(self, cap_usd: float):
        self.cap = int(cap_usd * 1_000_000)
        self.spent = 0
        self.skipped: list[str] = []

    def allows(self, estimate: int) -> bool:
        return self.spent + estimate <= self.cap


def parse_csv(text) -> list[dict]:
    if not isinstance(text, str) or ";" not in text:
        return []
    lines = [l for l in text.replace("\r", "").split("\n") if l.strip()]
    head = lines[0].split(";")
    return [dict(zip(head, l.split(";"))) for l in lines[1:]]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fetch_semrush(phrases: list[str], cfg: dict, budget: Budget, errors: list[str]) -> dict[str, dict]:
    from radar import aisa
    got: dict[str, dict] = {p: {} for p in phrases}
    for i in range(0, len(phrases), 20):
        chunk = phrases[i:i + 20]
        if not budget.allows(PRICE["overview"] * len(chunk)):
            budget.skipped += [f"overview:{p}" for p in chunk]
            continue
        calls = [{"call_id": f"o{j}", "tool": OVERVIEW, "arguments": {"phrase": p, "database": cfg["database"]}}
                 for j, p in enumerate(chunk)]
        try:
            data, cost = aisa.call(calls)
            budget.spent += cost
        except aisa.AisaError as exc:
            errors.append(f"Semrush 概览: {exc}")
            continue
        for j, p in enumerate(chunk):
            rows = parse_csv(data.get(f"o{j}"))
            row = next((r for r in rows if r.get("Keyword", "").lower() == p), rows[0] if rows else None)
            got[p]["overview_ok"] = True
            if row:
                got[p].update(volume=int(num(row.get("Search Volume")) or 0), cpc=num(row.get("CPC")),
                              comp=num(row.get("Competition")), results=int(num(row.get("Number of Results")) or 0))
            else:
                got[p].update(volume=0, cpc=None, comp=None, nodata=True)
    kd_need = []
    for p in phrases:
        if got[p].get("overview_ok") and (got[p].get("volume") or 0) < cfg.get("kd_min_volume", 0):
            got[p].update(kd_ok=True, kd=None, kd_skipped=True)
        else:
            kd_need.append(p)
    for i in range(0, len(kd_need), 20):
        chunk = kd_need[i:i + 20]
        if not budget.allows(PRICE["kd"] * len(chunk)):
            budget.skipped += [f"kd:{p}" for p in chunk]
            continue
        try:
            data, cost = aisa.call([{"call_id": "k", "tool": KD, "arguments": {"phrase": ";".join(chunk), "database": cfg["database"]}}])
            budget.spent += cost
        except aisa.AisaError as exc:
            errors.append(f"Semrush KD: {exc}")
            continue
        kds = {r.get("Keyword", "").lower(): num(r.get("Keyword Difficulty Index")) for r in parse_csv(data.get("k"))}
        for p in chunk:
            got[p]["kd_ok"] = True
            got[p]["kd"] = None if kds.get(p) is None else int(kds[p])
    return got


def serp_check(phrase: str, cfg: dict, budget: Budget, errors: list[str]) -> dict | None:
    from radar import aisa, competition
    if not budget.allows(PRICE["serp"]):
        budget.skipped.append(f"serp:{phrase}")
        return None
    try:
        page, cost = competition.page_one(phrase, cfg["serp_location_code"])
        budget.spent += cost
    except aisa.AisaError as exc:
        errors.append(f"首页 {phrase}: {exc}")
        return None
    kinds: dict[str, int] = {}
    for x in page["results"]:
        kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
    return {
        "kinds": kinds,
        "ads": page["ads"],
        "features": page["features"],
        "top": [x["domain"] for x in page["results"][:10]],
        "items": page["results"][:10],
        "source": "serp",
    }


def allintitle(phrase: str, cfg: dict, budget: Budget, errors: list[str]):
    from radar import aisa
    if not budget.allows(PRICE["serp"] * 5):
        budget.skipped.append(f"allintitle:{phrase}")
        return None
    try:
        data, cost = aisa.call([{"call_id": "a", "tool": "post_dataforseo_serp_google_organic_live", "arguments": {"body": [{
            "keyword": f"allintitle:{phrase}", "location_code": cfg["serp_location_code"], "language_code": "en", "depth": 10}]}}])
        budget.spent += cost
    except aisa.AisaError as exc:
        errors.append(f"allintitle {phrase}: {exc}")
        return None
    res = (((data.get("a") or {}).get("tasks") or [{}])[0].get("result") or [{}])[0]
    return res.get("se_results_count")


def small_sites(serp: dict) -> int | None:
    top = serp.get("top") or []
    if not top:
        return None
    return sum(1 for d in top if not any(d == b or d.endswith("." + b) for b in BIG))


def kdroi(t: dict) -> float | None:
    if not t.get("volume") or t.get("cpc") is None:
        return None
    return round(t["volume"] * t["cpc"] / max(t.get("kd") or 1, 1), 1)


def serp_verdict(serp: dict, kd) -> str:
    """No GoAnyAPI site ratings: count forum + video results as the soft slots a new site can take."""
    soft = (serp["kinds"].get("forum", 0) + serp["kinds"].get("video", 0))
    serp["soft_weak"] = soft
    if soft >= 3 or (kd is not None and kd <= 15):
        return "open"
    if soft == 0 and (kd is None or kd >= 40):
        return "crowded"
    return "mixed"


# ---------- SERP 真空期检测（免月搜门槛） ----------
def _domain_matches(d: str, patterns: tuple[str, ...]) -> bool:
    d = (d or "").lower().removeprefix("www.")
    return any(d == p or d.endswith("." + p) for p in patterns)


def evaluate_vacuum(t: dict, serp: dict | None, cfg: dict) -> dict:
    """检查 Google 前 10 自然结果：
    若论坛/社交/问答/代码仓/模型库/视频/科技媒体占比 >= 70% 且无独立产品站占坑，则判定为 SERP 真空期可抢 (is_vacuum: True)。
    """
    if not serp:
        return {"is_vacuum": False, "vacuum_ratio": None, "vacuum_count": None, "vacuum_evidence": "未查 SERP"}
    items = serp.get("items") or [{"domain": d, "url": "", "title": "", "kind": ""} for d in (serp.get("top") or [])]
    items = items[:10]
    total = len(items)
    if total < 3:
        return {"is_vacuum": False, "vacuum_ratio": 0.0, "vacuum_count": f"0/{total}", "vacuum_evidence": "结果过少"}

    phrase = t["phrase"].lower()
    # 提取关键词里的核心品牌词根（用于识别是否已有同名独立站占坑）
    stop_tokens = {
        "ai", "llm", "mcp", "model", "tool", "app", "video", "image", "voice", "generator", "converter", "maker",
        "checker", "free", "online", "web", "version", "alternative", "review", "demo", "how", "to", "get", "use",
        "open", "source", "coding", "assistant", "pro", "flash", "bolt",
    }
    raw_tokens = [re.sub(r"[^a-z0-9]", "", w) for w in re.split(r"[\s\-_.]+", phrase)]
    core_tokens = [w for w in raw_tokens if len(w) >= 4 and w not in stop_tokens and not w.isdigit()]

    buckets = {"社媒/论坛": 0, "代码仓/模型库": 0, "视频": 0, "资讯/评测": 0}
    umbrella_cnt = 0
    dedicated_sites = []
    niche_sites = []

    for r in items:
        d = (r.get("domain") or "").lower().removeprefix("www.")
        u = (r.get("url") or "").lower()
        if not d:
            continue
        if _domain_matches(d, VACUUM_SOCIAL_FORUM):
            buckets["社媒/论坛"] += 1
        elif _domain_matches(d, VACUUM_REPO_HUB_DOCS):
            buckets["代码仓/模型库"] += 1
        elif _domain_matches(d, VACUUM_VIDEO):
            buckets["视频"] += 1
        elif _domain_matches(d, VACUUM_NEWS_MEDIA_BLOG):
            buckets["资讯/评测"] += 1
        elif _domain_matches(d, OFFICIAL_UMBRELLA_DOMAINS):
            # 官方母站的子路径发布页（如 block.xyz/dessa, build.nvidia.com/...）不算第三方独立占坑站
            umbrella_cnt += 1
        elif _domain_matches(d, APP_STORE_DOMAINS):
            dedicated_sites.append(d)
        else:
            d_base = re.sub(r"[^a-z0-9]", "", d.split(".")[0])
            # 若域名直接包含核心词根（如 everygen.ai / pavoai.com / claudecowork.com / mccarbons.com），视为独立站占坑
            if any(ct in d_base or d_base in ct for ct in core_tokens if len(ct) >= 4):
                dedicated_sites.append(d)
            # 若是根路径主页（非 /blog/ /articles/ 内页），也视为独立产品站
            elif u.rstrip("/").count("/") <= 2 and not any(x in u for x in ("/blog", "/article", "/news", "/post")):
                dedicated_sites.append(d)
            else:
                niche_sites.append(d)

    vacuum_hits = sum(buckets.values())
    ratio = round(vacuum_hits / total, 2)
    min_ratio = cfg.get("vacuum_min_ratio", 0.70)
    # 若已有独立产品站占坑，或已有 >=3 个小站博客抢占，则不算真空期
    has_competitor_site = len(dedicated_sites) > 0 or len(niche_sites) >= 3
    is_vac = (ratio >= min_ratio) and (not has_competitor_site)

    parts = [f"{k} {v}" for k, v in buckets.items() if v > 0]
    breakdown = " / ".join(parts) if parts else "常规网页"
    if is_vac:
        ev = f"前{total}里 {vacuum_hits} 条（{int(ratio*100)}%）为 {breakdown}，0 独立产品站"
    else:
        if dedicated_sites:
            ev = f"已有独立站/应用占坑（{', '.join(dict.fromkeys(dedicated_sites[:2]))}），社区占比 {vacuum_hits}/{total}"
        elif len(niche_sites) >= 3:
            ev = f"已有 {len(niche_sites)} 个垂直博客抢占（{', '.join(dict.fromkeys(niche_sites[:2]))}），社区占比 {vacuum_hits}/{total}"
        else:
            ev = f"社区/代码仓占比 {vacuum_hits}/{total}（{int(ratio*100)}% < {int(min_ratio*100)}%）"

    return {
        "is_vacuum": is_vac,
        "vacuum_ratio": ratio,
        "vacuum_count": f"{vacuum_hits}/{total}",
        "vacuum_hits": vacuum_hits,
        "vacuum_total": total,
        "vacuum_breakdown": buckets,
        "dedicated_sites": list(dict.fromkeys(dedicated_sites)),
        "vacuum_evidence": ev,
    }


def suggest_web_delivery(t: dict) -> str:
    """为真空期/可做词生成具体的独立站交付建议。"""
    p = t["phrase"].lower()
    ev = (t.get("evidence") or "").lower()
    if "dessa" in p:
        return "全双工语音对话在线试玩页 + 本地 Mac/GPU 部署与评测对比站"
    if "nanbeige" in p:
        return "33B 开源编码模型 Prompt 演练场、SWE-bench 跑分对比与 Ollama/vLLM 部署指南站"
    if "nemotron" in p:
        return "4GB 端侧小模型本地运行教程、量化包下载导航与角色对话 Demo 站"
    if "flint" in p:
        return "40B MoE 本地代码模型安装指南、硬件显存计算器与编码评测对比页"
    if "code mode mcp" in p or "mcp" in p:
        return "MCP Server 配置生成器、Claude/Cursor 接入教程与目录导航页"
    if "moss image" in p:
        return "多参考图改图在线工坊 + ComfyUI 工作流一键模板下载站"
    if "learnharness" in p:
        return "AI Agent Harness 架构交互式教程、模板库与对比导航站"
    if "kimi k3" in p:
        return "Kimi K3.1 Pro API 价格计算器、长文本评测对比与接入指南页"
    if "claude duet" in p:
        return "Claude Duet 主动型 Agent 用例模板库、等待名单攻略与对比评测页"
    if "timecapsule" in p:
        return "历史语料零幻觉 LLM 在线体验与复古问答工具站"
    if "mercury" in p or "diffusion llm" in p:
        return "Diffusion LLM 极速生成速度对比 Demo 与 API 导航页"
    if "php vulnerability" in p:
        return "PHP2Shell 漏洞在线自检清单、安全加固脚本生成与补丁指南页"
    if "alternative" in p:
        return "开源/平替方案功能对比表、价格计算器与一键迁移指南站"
    if TOOL_INTENT.search(p):
        return "单页在线生成/转换工具站（免登录即用 + 预设模板库）"
    return "垂直功能演练场 + 评测对比与快速上手指南站"


# ---------- 精确匹配域名生成与 RDAP 只读查询 ----------
def generate_candidate_domains(phrase: str, names: list[str] | None = None, tlds: list[str] | None = None) -> list[str]:
    """按 SEO 标准为候选词生成候选域名（优先 exact-match .com，兼顾 -ai / try- 及 .ai / .io / .org）。"""
    tlds = tlds or ["com", "ai", "io", "org"]
    p = phrase.lower().strip()
    # 去掉版本小数点（4.3 -> 43, 3.5 -> 35）
    p_nodot = re.sub(r"(\d)\.(\d)", r"\1\2", p)
    tokens = [re.sub(r"[^a-z0-9]", "", w) for w in re.split(r"[\s\-_/]+", p_nodot)]
    tokens = [t for t in tokens if t]
    # 去掉末尾参数规模词（如 33b, e4b, 122b, 4gb）构建精简主干
    core_tokens = [t for t in tokens if not re.match(r"^(e?\d+b|\d+gb|1017)$", t)]
    if not core_tokens:
        core_tokens = tokens

    full_slug = "".join(core_tokens)[:24]
    # 若词根以数字版本结尾（如 nanbeige43），同时提取纯字母品牌词根（nanbeige）
    alpha_root = re.sub(r"\d+$", "", core_tokens[0]) if core_tokens else ""

    stem_no_suffix = "".join(core_tokens[:-1]) if len(core_tokens) >= 2 and core_tokens[-1] in ("ai", "llm", "mcp") else ""
    bases = []
    for b in (
        full_slug,
        f"{full_slug}ai" if not full_slug.endswith("ai") else full_slug,
        stem_no_suffix,
        f"try{stem_no_suffix}" if stem_no_suffix and len(stem_no_suffix) <= 14 else "",
        f"try{core_tokens[0]}" if core_tokens and len(core_tokens[0]) <= 12 else "",
        f"{alpha_root}ai" if len(alpha_root) >= 4 and alpha_root != full_slug else "",
        alpha_root if len(alpha_root) >= 5 and alpha_root != full_slug else "",
    ):
        if b and 3 <= len(b) <= 24 and b not in bases:
            bases.append(b)

    candidates = []
    # 优先排所有候选的 .com，再排主词根的 .ai / .io / .org
    for b in bases[:3]:
        d = f"{b}.com"
        if d not in candidates:
            candidates.append(d)
    for tld in tlds:
        if tld == "com":
            continue
        for b in bases[:2]:
            # 避免 xxxai.ai 重复后缀
            if tld == "ai" and b.endswith("ai") and len(b) > 5:
                b_clean = b[:-2]
                if len(b_clean) >= 4:
                    d0 = f"{b_clean}.ai"
                    if d0 not in candidates:
                        candidates.append(d0)
            d = f"{b}.{tld}"
            if d not in candidates:
                candidates.append(d)
    return candidates[:8]


def check_rdap_domain(domain: str, domain_cache: dict) -> bool | None:
    """只读查询官方 RDAP 接口判断域名是否未注册（HTTP 404 = 可注册 True，HTTP 200 = 已注册 False）。"""
    domain = domain.lower().strip()
    today_s = date.today().isoformat()
    if domain in domain_cache and isinstance(domain_cache[domain], dict):
        cached = domain_cache[domain]
        if cached.get("available") is not None:
            return bool(cached["available"])

    tld = domain.rsplit(".", 1)[-1]
    if tld == "com":
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
    elif tld == "org":
        url = f"https://rdap.publicinterestregistry.org/rdap/domain/{domain}"
    elif tld in ("ai", "io"):
        url = f"https://rdap.identitydigital.services/rdap/domain/{domain}"
    else:
        url = f"https://rdap.org/domain/{domain}"

    avail = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (RDAP-Read-Only-Check)"})
        with urllib.request.urlopen(req, timeout=6) as r:
            if r.status == 200:
                avail = False
    except urllib.error.HTTPError as e:
        if e.code == 404:
            avail = True
    except Exception:
        avail = None

    if avail is not None:
        domain_cache[domain] = {"available": avail, "day": today_s}
    return avail


def check_domains_for_term(t: dict, cfg: dict, cache: dict):
    domain_cache = cache.setdefault("_domains", {})
    cands = generate_candidate_domains(t["phrase"], t.get("names"), cfg.get("domain_tlds"))
    checked = []
    avail_list = []
    for d in cands:
        st = check_rdap_domain(d, domain_cache)
        checked.append({"domain": d, "available": st})
        if st is True:
            avail_list.append(d)
    # .com 排最前
    avail_list.sort(key=lambda d: (not d.endswith(".com"), not d.endswith(".ai"), not d.endswith(".io"), len(d)))
    t["domains"] = checked
    t["available_domains"] = avail_list


# ---------- judge ----------
def checks(t: dict, cfg: dict) -> dict[str, bool | None]:
    vol, kd, cpc = t.get("volume"), t.get("kd"), t.get("cpc")
    c = {
        "月搜": None if vol is None else vol >= cfg["min_volume"],
        "KD": None if kd is None else kd <= cfg["max_kd"],
        "CPC": None if not t.get("overview_ok") else (cpc is not None and cpc >= cfg["min_cpc"]),
    }
    if cfg["need_open_serp"]:
        c["首页竞争"] = None if t.get("verdict") is None else t["verdict"] == "open"
    if cfg.get("check_allintitle"):
        c["allintitle"] = None if t.get("allintitle") is None else t["allintitle"] < cfg["max_allintitle"]
    if cfg.get("need_small_sites"):
        c["小站居多"] = None if t.get("small_sites") is None else t["small_sites"] >= cfg["small_sites_min"]
    return c


def score(t: dict, cfg: dict) -> int:
    """0-100 confidence: volume headroom, KD headroom, CPC, page-one openness, vacuum bonus, evidence."""
    s = 0
    vol = t.get("volume") or 0
    s += min(30, int(30 * vol / max(1, cfg["min_volume"] * 4)))
    kd = t.get("kd")
    if kd is not None:
        s += max(0, int(25 * (1 - kd / 100)))
    cpc = t.get("cpc") or 0
    s += min(15, int(cpc * 5))
    s += {"open": 20, "mixed": 8}.get(t.get("verdict"), 0)
    s += 10 if t.get("evidence") else 0
    s += cfg.get("tool_intent_bonus", 0) if t.get("tool_intent") else 0
    if t.get("is_vacuum"):
        s = max(s, int((t.get("vacuum_ratio") or 0.7) * 85))
    return min(100, s)


def fmt(v, kind):
    if v is None:
        return "—"
    if kind == "cpc":
        return f"${v:.2f}"
    if kind == "n":
        return f"{v:,}" if isinstance(v, (int, float)) else str(v)
    if kind == "vol":
        return f"{v:,}"
    return str(v)


def comp_note(t: dict) -> str:
    v = VERDICT_ZH.get(t.get("verdict"), "未查")
    c = t.get("comp_detail") or {}
    kinds = c.get("kinds") or {}
    parts = [f"{KIND_ZH.get(k, k)}{n}" for k, n in sorted(kinds.items(), key=lambda x: -x[1])]
    extra = []
    if c.get("weak") is not None:
        extra.append(f"弱站 {c['weak']}")
    elif c.get("soft_weak") is not None:
        extra.append(f"论坛/视频位 {c['soft_weak']}")
    if c.get("ads"):
        extra.append("有广告")
    detail = "、".join(parts + extra)
    return f"{v}（{detail}）" if detail else v


def domain_note(t: dict) -> str:
    av = t.get("available_domains") or []
    if av:
        return "、".join(f"`{d}` (可注册)" for d in av[:3])
    checked = t.get("domains") or []
    if checked:
        return "同名 .com/.ai 已注册"
    return "—"


def source_note(t: dict) -> str:
    bits = [t.get("source", "")]
    if t.get("names"):
        bits.append("来自 " + "、".join(t["names"]))
    s = "，".join(b for b in bits if b)
    if t.get("evidence"):
        ev = t["evidence"].replace("|", "/")
        s += f"：“{ev[:90]}{'…' if len(ev) > 90 else ''}”"
    return s


def render(
    terms: list[dict],
    vacuum_terms: list[dict],
    filtered_out: list[dict],
    cfg: dict,
    budget: Budget,
    errors: list[str],
    report_day: str,
    cached: int,
) -> tuple[str, list[dict], list[dict]]:
    passed, near, rest = [], [], []
    for t in terms:
        c = t["checks"]
        failed = [k for k, ok in c.items() if ok is False]
        unknown = [k for k, ok in c.items() if ok is None]
        t["failed"], t["unknown"] = failed, unknown
        if not failed and not unknown:
            passed.append(t)
        elif len(failed) + len(unknown) == 1:
            near.append(t)
        else:
            rest.append(t)
    key = lambda t: (not t.get("tool_intent"), -(t.get("kdroi") or 0), -t["score"])
    passed.sort(key=key)
    near.sort(key=key)
    rest.sort(key=key)

    th = (
        f"常规通道：月搜 ≥ {cfg['min_volume']:,}、KD ≤ {cfg['max_kd']}、CPC 有值"
        + ("、首页竞争「能进」" if cfg["need_open_serp"] else "")
        + (f"、allintitle < {cfg['max_allintitle']:,}" if cfg.get("check_allintitle") else "")
        + f"；真空期通道（免月搜门槛）：Google 前 10 自然结果中论坛/社交/代码仓/视频/资讯占比 ≥ {int(cfg.get('vacuum_min_ratio', 0.7)*100)}% 且无独立产品站占坑。"
    )
    L = [
        f"## 可做的词 & SERP 真空期机会（{report_day}）",
        "",
        f"规则：{th}共查 {len(terms)} 个干净候选词（前置语义预筛已自动剔除 {len(filtered_out)} 个球赛/八卦/非网页交付噪音词）。",
        "",
    ]

    # 1) SERP 真空期可抢
    L.append(f"### 🔥 真空期可抢（免月搜门槛 · SERP 社媒/代码仓 ≥70% 且无独立站）（{len(vacuum_terms)}）")
    if vacuum_terms:
        L += [
            "",
            "| 词 | 来源 | 美区月搜 | SERP 真空度 | 搜索结果证据 | 推荐可注册域名（RDAP） | 上线建议 |",
            "|---|---|---|---|---|---|---|",
        ]
        for t in vacuum_terms:
            ratio_pct = f"**{int((t.get('vacuum_ratio') or 0)*100)}%** ({t.get('vacuum_count')})"
            L.append(
                f"| **{t['phrase']}** | {t.get('source','')} | {fmt(t.get('volume'),'vol')} | {ratio_pct} | "
                f"{t.get('vacuum_evidence','')} | {domain_note(t)} | {t.get('delivery_suggestion','')} |"
            )
    else:
        L += ["", "今天没有触发 SERP 真空期的词。"]

    # 2) 全过门槛的词
    L += ["", f"### 全过门槛的词（{len(passed)}）"]
    if passed:
        L += [
            "",
            "| 词 | 月搜 | KD | CPC | KDROI | allintitle | 小站/10 | 首页竞争 | 推荐可注册域名 | 依据/来源 |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for t in passed:
            L.append(
                f"| **{t['phrase']}** | {fmt(t.get('volume'),'vol')} | {fmt(t.get('kd'),'kd')} | {fmt(t.get('cpc'),'cpc')} | "
                f"{fmt(t.get('kdroi'),'n')}{' 🛠' if t.get('tool_intent') else ''} | {fmt(t.get('allintitle'),'vol')} | "
                f"{fmt(t.get('small_sites'),'n')} | {comp_note(t)} | {domain_note(t)} | {source_note(t)} |"
            )
    else:
        L += ["", "今天没有词全过 Semrush 常规门槛。"]

    # 3) 差一点就过的词
    L += ["", f"### 差一点就过的词（{len(near)}）"]
    if near:
        L += [
            "",
            "| 词 | 月搜 | KD | CPC | KDROI | allintitle | 小站/10 | 首页竞争 | 卡在哪 | 推荐可注册域名 | 依据/来源 |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for t in near:
            why = "、".join([f"{k}没过" for k in t["failed"]] + [f"{k}没数据" for k in t["unknown"]])
            L.append(
                f"| {t['phrase']} | {fmt(t.get('volume'),'vol')} | {fmt(t.get('kd'),'kd')} | {fmt(t.get('cpc'),'cpc')} | "
                f"{fmt(t.get('kdroi'),'n')}{' 🛠' if t.get('tool_intent') else ''} | {fmt(t.get('allintitle'),'vol')} | "
                f"{fmt(t.get('small_sites'),'n')} | {comp_note(t)} | {why} | {domain_note(t)} | {source_note(t)} |"
            )
    else:
        L += ["", "没有只差一项的词。"]

    if rest:
        L += [
            "",
            "其余（两项以上没过）："
            + "；".join(
                f"{t['phrase']}（月搜 {fmt(t.get('volume'),'vol')}，KDROI {fmt(t.get('kdroi'),'n')}，KD {fmt(t.get('kd'),'kd')}，CPC {fmt(t.get('cpc'),'cpc')}；卡在 "
                + "、".join(t["failed"] + [k + "没数据" for k in t["unknown"]])
                + "）"
                for t in rest[:25]
            ),
        ]
    if filtered_out:
        L += [
            "",
            f"前置语义预筛拦截（共 {len(filtered_out)} 个）："
            + "、".join(f"`{x['phrase']}`（{x['reason']}）" for x in filtered_out[:18]),
        ]
    L += ["", f"花费：本次 AIsa 约 ${budget.spent/1e6:.3f}（上限 ${budget.cap/1e6:.2f}），{cached} 个词用了 7 天内缓存没再付费。"]
    if budget.skipped:
        L.append(f"因上限跳过 {len(budget.skipped)} 次查询。")
    if errors:
        L.append("接口问题：" + "；".join(errors))
    L.append("注：KD 用的是 Semrush 指数；域名状态通过官方 RDAP 只读查询（.com Verisign / .ai & .io IdentityDigital / .org PIR），全程只读不自动注册。")
    return "\n".join(L) + "\n", passed, near


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=str(HERE / "report.json"))
    ap.add_argument("--out", default=str(HERE / "doable.md"))
    ap.add_argument("--terms", default="", help="extra terms, ';'-separated")
    ap.add_argument("--extra-file", default="", help="JSON list of {phrase,source,names,evidence}")
    ap.add_argument("--dry-run", action="store_true", help="collect and show terms, spend nothing")
    a = ap.parse_args()
    load_env()
    cfg = config()
    report = json.loads(Path(a.report).read_text())
    report_day = datetime.fromtimestamp(Path(a.report).stat().st_mtime).strftime("%Y-%m-%d")
    extra = [t for t in a.terms.split(";") if t.strip()]
    for ef in [x for x in a.extra_file.split(",") if x.strip()]:
        if Path(ef).exists():
            extra += json.loads(Path(ef).read_text())

    filtered_out: list[dict] = []
    # 同时汇总 finders.json 已记录的被拦截噪音词，方便在日报卡片中统一展示
    fj_path = HERE / "finders.json"
    if fj_path.exists():
        try:
            for fn in json.loads(fj_path.read_text()).get("filtered_noise") or []:
                if fn.get("phrase") and not any(x["phrase"] == fn["phrase"] for x in filtered_out):
                    filtered_out.append(fn)
        except Exception:
            pass

    terms = collect(report, extra, cfg["max_terms"], report_day, filtered_out)
    if a.dry_run:
        print(json.dumps([t["phrase"] for t in terms], ensure_ascii=False))
        return

    budget, errors = Budget(cfg["max_spend_usd"]), []
    cache = load_cache(cfg["cache_days"])
    todo = [t["phrase"] for t in terms if t["phrase"] not in cache or not cache[t["phrase"]].get("overview_ok")]
    cached = len(terms) - len(todo)
    if todo:
        fetched = fetch_semrush(todo, cfg, budget, errors)
        for p, v in fetched.items():
            if v.get("overview_ok") and v.get("kd_ok"):
                existing = cache.get(p) if isinstance(cache.get(p), dict) else {}
                cache[p] = {**existing, **v, "day": date.today().isoformat()}
            terms_by = next(t for t in terms if t["phrase"] == p)
            terms_by.update(v)

    for t in terms:
        if t["phrase"] in cache and isinstance(cache[t["phrase"]], dict):
            t.update({k: v for k, v in cache[t["phrase"]].items() if k not in ("day", "serp", "allintitle")})

    # SERP 检查：常规过月搜+CPC 的词，或属于新词真空期候选池的词（免月搜门槛）
    vac_checks_used = 0
    vac_max = cfg.get("vacuum_max_serp_checks", 18)
    for t in terms:
        p = t["phrase"]
        pre = (t.get("volume") or 0) >= cfg["min_volume"] and (t.get("cpc") or 0) >= cfg["min_cpc"]
        is_vac_cand = bool(cfg.get("vacuum_enabled", True) and t.get("is_vacuum_candidate"))
        serp = (cache.get(p) or {}).get("serp") if isinstance(cache.get(p), dict) else None

        # 若需要跑真空期检验但缓存里的 serp 没有前 10 域名列表，或完全没缓存，则拉取 SERP
        need_serp = pre or (is_vac_cand and vac_checks_used < vac_max)
        if serp is None and need_serp and cfg["serp_fetch"]:
            serp = serp_check(p, cfg, budget, errors)
            if is_vac_cand and not pre:
                vac_checks_used += 1
            if serp:
                cache.setdefault(p, {"day": date.today().isoformat()})["serp"] = serp

        if serp:
            t["verdict"], t["comp_detail"] = serp_verdict(serp, t.get("kd")), serp
        else:
            comp = t.get("competition")
            if comp and comp.get("verdict"):
                t["verdict"], t["comp_detail"] = comp["verdict"], comp
            else:
                t["verdict"] = None

        # 真空期评估
        if is_vac_cand or serp:
            vac_info = evaluate_vacuum(t, serp, cfg)
            t.update(vac_info)
            p_slug = re.sub(r"[^a-z0-9]", "", p)
            if any(re.sub(r"[^a-z0-9]", "", d.split(".")[0]) == p_slug for d in (t.get("dedicated_sites") or [])):
                t["verdict"] = "mixed"
        else:
            t["is_vacuum"] = False

    for t in terms:
        t["tool_intent"] = bool(TOOL_INTENT.search(t["phrase"]))
        t["kdroi"] = kdroi(t)
        if t.get("comp_detail") and t["comp_detail"].get("top"):
            t["small_sites"] = small_sites(t["comp_detail"])
        pre = (t.get("volume") or 0) >= cfg["min_volume"] and (t.get("cpc") or 0) >= cfg["min_cpc"]
        c = cache.get(t["phrase"]) if isinstance(cache.get(t["phrase"]), dict) else {}
        if "allintitle" in c:
            t["allintitle"] = c["allintitle"]
        elif pre and cfg.get("check_allintitle"):
            t["allintitle"] = allintitle(t["phrase"], cfg, budget, errors)
            if t["allintitle"] is not None and t["phrase"] in cache:
                cache[t["phrase"]]["allintitle"] = t["allintitle"]

    for t in terms:
        t["checks"] = checks(t, cfg)
        t["score"] = score(t, cfg)
        t["delivery_suggestion"] = suggest_web_delivery(t)

    # 整理真空期列表（按建站热词/AI新品优先级 -> 真空比 -> 工具意图排序，同一母词去重保留最优代表词）
    raw_vac = [t for t in terms if t.get("is_vacuum")]
    raw_vac.sort(
        key=lambda t: (
            not bool(t.get("is_hot_keyword")),
            "AI新品" not in (t.get("source") or ""),
            -(t.get("vacuum_ratio") or 0),
            not bool(t.get("tool_intent")),
            -(t.get("volume") or 0),
        )
    )
    vacuum_terms = []
    seen_vac_root = set()
    for t in raw_vac:
        root_key = (t.get("names") or [t["phrase"]])[0].lower().strip()
        if root_key in ("ai generator", "ai video", "ai agent", "ai app", "ai image", "llm", "mcp", "ai tool"):
            root_key = t["phrase"].split()[0]
        if "flint" in root_key or "flint" in t["phrase"]:
            root_key = "flint" 
        if root_key in seen_vac_root:
            continue
        seen_vac_root.add(root_key)
        vacuum_terms.append(t)

    # 对全过词、真空期词、建站热词及前 5 个高潜力词执行 RDAP 域名可注册只读检查
    if cfg.get("check_domains", True):
        for t in terms:
            c = t["checks"]
            failed = [k for k, ok in c.items() if ok is False]
            unknown = [k for k, ok in c.items() if ok is None]
            if (
                t.get("is_vacuum")
                or t.get("is_hot_keyword")
                or "AI新品" in (t.get("source") or "")
                or (not failed and not unknown)
                or (len(failed) + len(unknown) <= 1)
            ):
                check_domains_for_term(t, cfg, cache)

    save_cache(cache)
    md, passed, near = render(terms, vacuum_terms, filtered_out, cfg, budget, errors, report_day, cached)
    Path(a.out).write_text(md)
    Path(a.out).with_suffix(".json").write_text(
        json.dumps(
            {
                "day": report_day,
                "config": cfg,
                "passed": passed,
                "vacuum_terms": vacuum_terms,
                "almost": near,
                "filtered_out": filtered_out,
                "terms": terms,
                "spent_micros": budget.spent,
                "errors": errors,
                "skipped": budget.skipped,
            },
            ensure_ascii=False,
            indent=1,
            default=str,
        )
    )
    with open(HERE / "doable.log", "a") as f:
        f.write(
            json.dumps(
                {
                    "at": datetime.now().isoformat(timespec="seconds"),
                    "report": a.report,
                    "terms": len(terms),
                    "vacuum": len(vacuum_terms),
                    "passed": len(passed),
                    "filtered_noise": len(filtered_out),
                    "queried": len(todo),
                    "cached": cached,
                    "spent_usd": round(budget.spent / 1e6, 4),
                    "errors": errors,
                    "skipped": len(budget.skipped),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    print(md)


if __name__ == "__main__":
    main()
