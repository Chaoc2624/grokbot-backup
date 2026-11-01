# Frame 每日增长战报 & 乘胜追击 Todo — 2026-11-01（Asia/Shanghai）

巡检完成于 09:16。对比基线（2026-10-26）：GSC 28d 71 / 1,892 / 3.8% / 11.6；Bing 3m 297 / 7,157 / 4.15%；CF RUM 9月 760 Visits；Sitemap 37+ → **今日仍 43**。

## 红绿灯（防疲劳）
| 维度 | 状态 | 标红？ |
|---|---|---|
| 基建回退 | 🟢 占位符 0；GA4/Clarity/SSR/示例视频在线；核心页全 200 | 否 |
| Bing 3m | 🟢 293点击 / 7.3K曝光 / CTR 4.02%（vs 297/7157/4.15%，−1.3% / +≈2% / −0.13pp） | **否**（远低于 20%） |
| GSC 28d | 🟡 本轮自动化无法填 Google 密码；**今日未刷新**（同 10-30/10-31 阻断） | 阻断拉数，非站点故障 |
| CF 边缘 | 🟡 10-31 Uniques 520 vs 10-30 696（**−25.3%**）；PageViews 879（−15.2%）；Requests 21262（**+159%**，偏爬虫噪音） | 流量备注，非基建回退 |
| 漏斗 L2–L4 API | 🟡 无 GSC/GA4/Clarity 服务账号环境变量 | 无法算转化波动 |
| 竞品定价/新页 | 🟢 跟踪五站 sitemap Δ=0、仍免费、无新高价值路由 | 否 |
| SERP 情报 | 🟡 WebSearch「extract frames from video online」**我方 .app 掉出 Top5**（10-31 为 #5）；同日「video frame extractor」仍 **#2**、「frame extractor」仍 **#5**；新进 FramePeel / toframes.video | 情报备注（非价格/sitemap 级标红） |
| Dead/Rage / decode_error | 🟡 Clarity API 未接 | 无法拉 |

**今日无「价格>5% / Bing 搜索>20% / 基建回退 / 跟踪竞品高价值新页」级标红。** 需老板处理：GSC 登录。关注 SERP 主词掉出与 CF Uniques DoD。

## 1. 基建
- 核心语种首页、11 工具内页、法务、`sitemap.xml`、`llms.txt`、`llms-full.txt`、IndexNow key：**全 200**
- 占位符 `localhost:3000` / `ShipAny App` / `YourAppName`：**0**
- GA4 `G-7J7WCQ7V35`、Clarity `z3ok33tl46`、`ssr-workbench-controls`、`try-sample-video-btn`：✓
- CF RUM：`auto_install=true`（边缘注入；site_info/list 今日鉴权 10001 失败，沿用旧 tag）
- IndexNow 核心 URL 批量推送：**HTTP 200**（43 URLs）
- 已知：`/pt` `/zh` `/ru` 404；`/ko` 301→/；Markdown Accept 200 但仍 `text/html`；`/index.md` **403**（昨记 404）

## 2. 漏斗 / 边缘流量
- `daily-funnel-inspector --summarize`：**WARN**（Claude SEO runtime 未 setup；L2–L4 API 无凭据；L1 HTTP PASS；药效复盘今日无 7d/14d 到期行）
- CF GraphQL（10-31）：PV **879** / Uniques **520** / Requests **21262**（相对 10-30：−15.2% / −25.3% / +159%；高请求低 UV 偏 bot）

## 3. Bing（已截图）
文件：
- `/workspace/gsc-frame-extractor/bing-bwt-frame-extractor-3m-summary-2026-11-01.png`
- `/workspace/gsc-frame-extractor/bing-bwt-frame-extractor-3m-keywords-2026-11-01.png`  
窗口：Last 3 months；站点 `frame-extractor.app/`

高曝光低 CTR（位次 ~4–20）钩子优化候选（**改 TDH 须先报老板确认**）：
- `frame extractor`：3.1K / 84 / **2.68%** / 4.64
- `video frame extractor`：1.1K / 16 / **1.40%** / 8.17
- `extract frames from video`：32 / 0 / **0%** / 9.22
- `extractor de fotogramas`：57 / 0 / **0%** / 9.96（西语机会）

强势词：`video frame grabber` 66 / 56 / **84.85%** / 1.12

## 4. 竞品
五站 HTTP 200；sitemap 13/9/8/42/14 与 10-31 相同；仍免费、无新路由。  
WebSearch「extract frames from video online」Top5：`framepeel.com`、`frame-extractor.online`、`frameripper.com`、`toframes.video`、`framify.video` — **我方 .app 未进**（昨 #5）。  
「video frame extractor」：**frame-extractor.app #2**；「frame extractor」：**#5**。  
新观察：FramePeel（三词均 #1）、toframes.video。

## 5. 外链定额
| 项 | 结果 |
|---|---|
| 博客评论 | **30 次尝试 → Live 28 / Pending 2 / Failed 0**；小语种母语锚文本 **8**（ja2/de2/fr2/it2） |
| 目录站 | ExactSeek Failed(一日一次)；humanornot Pending(Webflow ok)；poweredbyai / brownbook / tooldirectory.ai **NEED_BROWSER**；**0 个今日新目录 Live** |
| 邮箱 | 仅 `frame-submit@agentmail.to` |
| 台账 | ledger id **149–183** 已写入 `frame-backlink-ledger.md` + 知识库溯源台账 |

Pending：`blog.alfred.edu`×2（cid 19306/19307）。无新增 Instant-Live .gov/.edu 宝典源（未 vault push）。

## 乘胜追击 Todo
1. **【老板】** 在对话里登录 Google（`zhangx2624@gmail.com`）刷 GSC 28d，否则无法判搜索异动与精品率
2. 派 computerUse 补提 3–5 个免费目录（优先 brownbook、tooldirectory.ai、poweredbyai；**跳过 viesearch**；ExactSeek 明日再试一日限额；遇付费跳过）
3. 会诊 `@SEO总参谋`：Bing 高曝光低 CTR 词 + 西语 `extractor de fotogramas` 的 title/meta 钩子方案（**改前呈报对比，未经确认不动 TDH**）
4. `@GEO内容主理人`：llms.txt 补 Markdown 链接 + `>` 摘要；跟进 `/index.md` 403；评估 FramePeel / toframes 是否纳入对比表与 llms（不动已有页 TDH）
5. 巩固「video frame extractor」#2：外链 + 内页密度，勿拆新页；持续盯主词 SERP 是否回 Top5
6. 可选：修 funnel-inspector `/seo setup` 与 Claude SEO runtime，便于 L1 drift

工件目录：`/workspace/frame-daily-runs/2026-11-01-*`
