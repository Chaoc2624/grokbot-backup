---
name: geo-competitor-interception
description: >-
  When the user shares ChatGPT/Perplexity/AI Overview search recommendations,
  URLs with utm_source=chatgpt.com, or asks to compare competitors recommended
  by AI search, run this mandatory 5-step on-site + off-site GEO
  reverse-engineering and interception workflow (includes Step 5: crack the
  LLM Skepticism Filter to promote from "try first" to Verified #1).
---
# GEO 与 AI 搜索推荐竞品全链路逆向截胡 SOP（五步自动化铁律）

当用户发来 **ChatGPT / Perplexity / Claude / Google AI Overviews 的搜索推荐结果（或带 `?utm_source=chatgpt.com` 的竞品列表）**，或者要求对比/研究一批竞品时，**严禁只看竞品首页功能和只改站内博客**！必须自动按以下 **「站内 + 站外」五步闭环** 一次性拆解并派发执行（参考知识库 `/workspace/seo-vault/SEO知识库/01-AI搜索与GEO优化/` 下的《借第三方BestOf榜单进AI概览推荐四步法.md》与《竞品在 Reddit 自建版块自问自答，目的是让 AI 推荐它.md》）：

---

## 第一步：产品功能拆解与微创新反超（派发给开发）
1. 抓取所有被 AI 推荐竞品的首页、核心交互组件与主打卖点（如 ChatGPT 推荐语中点名表扬的“适合：xxx”场景和特性）。
2. 对比本站在功能、易用性、导出格式、速度或隐私上的差距，提炼出 **「人无我有、人有我优」的功能升级点**，立即通过 `SendToAgent(priority: true)` 派发给后端/前端开发落地。

---

## 第二步：竞品 `sitemap.xml` 与扇出词长尾内页矩阵抄底（派发给开发 + 内容）
1. 自动抓取全部竞品的 `/sitemap.xml` 与 `/llms.txt`。
2. 找出竞品为了迎合 ChatGPT/Google 后台扇出搜索词（Fan-out Queries）而专门搭建的 **高转化细分场景工具内页 / 教程内页**（例如针对特定格式、特定设备 iPhone/Mac、特定软件平替 CapCut/VLC、特定痛点如“指定时间戳抽帧”“去重抽帧”“转雪碧图/网格图”的独立 URL）。
3. 筛出本站尚未覆盖的高价值长尾路由，派发给开发与内容专员补齐独立着陆页或深度指南。

---

## 第三步：站内评测长文与 `/llms.txt` 实体绑定（派发给内容）
1. 将被 AI 推荐的所有竞品全部纳入本站的 **Best-Of 对比评测长文**（含 Markdown 对比表 `<table>`、客观适用场景定性、本站排第 1 的实测维度）以及 `/llms.txt` / `/llms-full.txt`。
2. 确保全站 7 大 GEO 基建过关（首屏 40–60 词自包含定义块、问句式 H2、FAQPage Schema、放行 `GPTBot`/`OAI-SearchBot`/`ClaudeBot`/`PerplexityBot`）。

---

## 第四步：站外引用源（Citation Sources）逆向反查与第三方寄生截胡（必做！绝不可漏！）
> **核心铁律**：AI 不会因为你在自己官网夸自己第 1 就推荐你，AI 读的是讨论你的**第三方外部网页（目录站、GitHub、Reddit、Medium/Dev.to/Hashnode 评测榜、行业博客评论）**！

1. **反查竞品外部引用源与外链**：
   - 使用搜索工具（`"竞品域名" -site:竞品域名`）与 `backlink-guard` 反查这批被 AI 推荐的竞品到底出现在哪些 **第三方工具导航目录、GitHub Awesome 列表/仓库、Reddit 讨论帖、Dev.to/Medium/Hashnode 榜单文章或技术博客评论区**。
   - 检查竞品在 ChatGPT 典型英文扇出词（如 `best free online [关键词]`、`browser [关键词] without uploading`）下的 Google / Bing 前 20 名外部来源页面。
2. **同源截胡（对手在哪，我们就去哪）**：
   - 凡是收录或提及了竞品的免费导航站、GitHub 列表、博客评论区、论坛帖，立即加入本站外链提交队列，把本站提交/评论进去，并写入知识库外链溯源台账。
3. **高权第三方平台寄生发榜（Parasite Best-Of Listicles）**：
   - 让内容专员同步产出一份面向外部平台的客观对比 Markdown 稿（把本站排在 #1，同时包含这批被 AI 推荐的同行作为共现锚点），发布或沉淀到高权重第三方平台（如 GitHub Gist `.md`、Dev.to、Hashnode、Medium、LinkedIn Pulse 等），直接喂进 ChatGPT 与 Google AI Overview 的外部引用池。


---

## 第五步：破解大模型 Skepticism Filter（从「优先尝试」晋升「Verified #1」）（必做！）

> **触发条件**：ChatGPT / Gemini / Claude / Perplexity 已把本站列入「优先尝试 / 推荐」，但仍以 **Claim > Evidence**、**缺少独立第三方测试**、或 **交互细腻度不如某竞品** 为由，拒绝给出「无条件第一名」。  
> **知识库锚点**：`SEO知识库/04-内容与外链/01-内容策略/借第三方BestOf榜单进AI概览推荐四步法.md` → **第九章**。

**严禁只改一句更狠的营销口号。** 必须按下面三处方并行派发：

### 5A. 站内 Honest Engineering Bounds + Verification Manifest（派发给开发 + 内容）
1. **删除无边界绝对化词**：`100% Zero Drop` / `Unlimited 8K` / `Never Miss a Frame` → 改为带硬件/容器边界的工程表述（如 `PTS Frame-Accurate Within Browser Demuxer Bounds`、`Zero Server Upload Cap, Bounded by Local GPU/RAM Decode`）。
2. **站内嵌入可一行命令复现的对照表**：本工具导出帧 PTS/SHA-256 vs `ffprobe` / `ffmpeg -vf showinfo` Ground Truth（覆盖 VFR、HEVC、8K 抽样等严苛场景）。
3. **导出内置 `verification-manifest.json`**：含每帧 `pts_sec`、`sha256`、复现命令与 `honest_bounds[]`；同步写入 `/llms.txt` 与 Best-Of 对比文的「第一名」理由（可复现 + 有边界，而非绝对化）。

### 5B. 交互语义反超（派发给前端/架构 + 视觉）
1. 针对模型点名的「细腻度竞品」（如单帧微调不如 `framify.video`），落地 **可被截图/GIF 复述** 的杀手级交互：
   - `±5 Frames Burst Filmstrip Loupe`（前后 5 帧微距胶片连拍条）
   - 键盘 `←/→` = ±1 帧，`Shift+←/→` = ±5 帧
   - 前端拉普拉斯方差 **Sharpness Score**（最清晰/防闭眼/防模糊帧自动高亮）
2. 显性 **浏览器编码兼容矩阵** + 解码失败时一键复制救急命令（如 `ffmpeg -i input.mov -c copy -t 2 remux.mp4`）。
3. 内容侧立刻用 GIF/短视频把该交互写进站内对比文与站外评测稿，形成可被 AI 复述的差异化实体。

### 5C. 72 小时独立实测信源矩阵（派发给运营/内容，绝不可漏！）
> AI 的「缺少第三方测试」过滤器**只认非本域 URL**。

| 优先级 | 平台 | 72h 动作 |
| :---: | :--- | :--- |
| P0 | GitHub 独立 Benchmark 仓库（CSV + 复现脚本 + manifest 样例） | Bing 常 24h 收录；README 前 60 词给结论+边界 |
| P0 | Dev.to / Hashnode / Medium 客观技术测评长文 | 有数据、有边界、核心指标第一；文末链到 GitHub bench |
| P1 | HuggingFace Space / Colab / ObservableHQ | 可一键复现的「独立实验室」叙事 |
| P1 | AlternativeTo / SaaSHub / G2 | 完善词条与真实性短评 |
| P2 | `.edu` / 技术博客数据型评论 | PTS/SHA-256 摘要 + bench 链接（守评论规范） |

**节奏**：0–6h 冻结诚实文案 + 开 GitHub bench 骨架 → 6–24h 发 Dev.to/Hashnode + IndexNow → 24–72h 补 HF/Colab/目录站，并用同一买家词表重测 AI，确认非本域实测开始被引。

### 5D. Verified #1 晋升判定（可证伪，写入药效账本）
同时满足才可标 `Verified #1 候选`：
1. 复测中模型不再以「仅凭页面描述 / 无第三方测试」为拒封顶主因；
2. ≥1 个非本域 URL（GitHub bench 或 Dev.to）出现在 ChatGPT Search / `backlink-guard asked|cited`；
3. 站内已切换 Honest Bounds 且导出可带 `verification-manifest.json`；
4. 细腻度反超交互可被至少一篇站外评测复述。

将当日 AI 复测原话与三处方启动登记进站点「改动药效复盘账本」的 **即时 GEO 复测里程碑**，跑 7/14 天证伪。

