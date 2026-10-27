# Frame 每日增长战报 & 乘胜追击 Todo List
**日期**：2026-10-27（Asia/Shanghai） · 巡检窗 ~08:52–09:25

## 总览（防疲劳：无强制标红）
- **基建**：核心页 / 9 语种首页 / 11 工具内页 / 法务 / sitemap(43) / llms.txt / IndexNow key → **HTTP 200**；占位符 `localhost:3000`/`ShipAny`/`YourAppName` = **0**；GA4 `G-7J7WCQ7V35` + Clarity `z3ok33tl46` + SSR `ssr-workbench-controls` + sample btn OK；`Accept: text/markdown` 200。`/pt` `/zh` 404（不在 sitemap，已知）。
- **漏斗脚本**：`daily-funnel-inspector` **Overall WARN**（`L1_drift_compare` 参数 `--json` 失效）；L2–L4 云端 API 缺凭证跳过；药效账本今日无 7d/14d 到期项（下一窗 **2026-11-02 / 2026-11-09**）。
- **GSC**：本轮无实时拉取（沿用 10-26 基线 28d：点击 71 / 曝光 1,892 / CTR 3.8% / 排名 11.6）→ **无法计算 >20% 异动，不标红**。
- **Bing**：3 个月约 **294 点击 / 7.1K 曝光 / CTR 4.13%**（截图），相对基线 297/7157/4.15% **近似持平（<20%）**。
- **竞品**：五站无定价异动、sitemap 数量未增、无 RED。
- **外链定额**：评论 **31/30 ✅**（小语种 7）；目录 **2/3–5**（ASR + Uneed），其余卡在登录/付费/拒 AgentMail。

## 标红项
**无。**（无价格>5%、无已证实 GSC/Bing 点击曝光>20%、无竞品高价值新页、基建无回退。）

## WARN / 缺口
1. GSC 实时未取到 → 明日优先补拉 `sc-domain:frame-extractor.app`。
2. 漏斗 L1_drift_compare 脚本参数需修；GA4/Clarity/CF GraphQL 凭证/限额未接通 → L2–L4 定性不足。
3. 目录站今日仅 2 个闭环；Fazier（要首页反链）、Startupfa.st/BetaList（登录或付费）、Viesearch（拒 disposable）已记黑名单/跳过理由。

## 外链执行摘要
| 类型 | 结果 |
|---|---|
| 评论 | 31 条成功（ja2/de2/fr1/it2）；台账 #48–78；双写 ledger + vault |
| 目录 | ASR DR74 确认链已点；Uneed Waiting Line（截图）；目标差 1–3 个 |
| 邮箱 | 仅用 `frame-submit@agentmail.to` |

## 竞品乘胜追击 Todo（非 RED）
1. 跟进 **Live Photo / iPhone 单帧保存** 意图页（framify 已占 how-to）— 评估是否新增内页（**动 TDH 须老板+SEO总参谋确认**）。
2. 监控 **Pilko / FrameCatcher** 与 getframes* 外链源，继续同源评论截胡。
3. 保持 getframesfromvideo / framesfromvideo 意图词对比文与 `llms.txt` 同步（已有基线，无新 sitemap 变化）。

## 请老板拍板 / 知晓
- 今日战报：**无紧急标红**；评论定额完成；目录差 1–3 个明日补。
- 可选：是否授权 Fazier 免费档所需的 **首页/页脚反链徽章**（会改站点，需确认）。
- 可选：Cloudflare GraphQL / GA4 / Clarity 只读凭证接通，便于明日 L2–L4 全自动。
