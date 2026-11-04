# CPJ 每日增长战报 & 乘胜追击 Todo — 2026-11-04（Asia/Taipei）

巡检类型：**手动触发 · 等同例程 `cpj-gsc` 首次跑** · 完成于约 **17:45 Asia/Taipei** · **外链站规修订约 17:51**。  
站点：https://chinaprivatejourneys.com · 过渡 Workers：https://china-private-journeys.zhangx2624.workers.dev  
画像：线上询盘/路由平台（非持牌旅行社）；legalName/contact/fulfilment 以 `operatorFacts-confirmed-2026-11-02.json` 为准。  
**隔离邮站规（Halo/Grok总管 2026-11-04）**：目录/外链 **禁止个人 Gmail**；必须 AgentMail。临时 `submit@chinaprivatejourneys.com`→Gmail **已删除**（CF 现仅 `contact@`→Gmail）。`cpj-submit@agentmail.to` **未开通**（AgentMail **3/3 满额**）。

## 硬门禁结果

| 源 | 状态 | 说明 |
|---|---|---|
| GSC | 🟢 已实拉 | `get-performance-overview` / queries / pages · 28d 窗口 **2026-10-05→2026-11-01** |
| Bing Webmaster | 🟢 已实拉 | key 在 env；站点 verified；90d 流量行 **0**；Sitemap feed Success |
| GA4 | 🟢 已实拉 | Property **561855861** · Measurement **G-P248GHMDLE** · 窗口 2026-11-02→11-04 |
| Clarity Data Export | 🔴 **不合格** | 缺 `/home/box/secrets/china-private-journeys-analytics/clarity-api-token.txt`；项目 ID `z76iipo4o5` 仅有 tracking 备注。父壳若残留 Frame token，导出的是 **frame-extractor.app** 数据——**禁止当作 CPJ 漏斗** |
| Cloudflare | 🟢 MCP GraphQL | zone `7e545f2a…` / account `eb92c278…`；本地 `CLOUDFLARE_API_TOKEN` 文件仍缺（边缘数靠 MCP） |
| 目录隔离邮 | 🔴 **缺 CPJ AgentMail** | 满额 3/3；无 `cpj-submit@agentmail.to`；禁止个人 Gmail / 已删 submit@ |

**巡检判定：Clarity + 目录隔离邮双标红 → 硬门禁不合格项已写明。** GSC/Bing/GA4/CF 已写入基线备忘。外链段今日 **只记 NEED_BROWSER，不自动交**。

## 红绿灯（防疲劳）

| 维度 | 状态 | 标红？ |
|---|---|---|
| Clarity API | 🔴 无 CPJ `clarity-api-token.txt`；不可用 Frame token 冒充 | **是** |
| 目录/外链隔离邮 | 🔴 **缺 CPJ AgentMail**（3/3）；submit@→Gmail 已删 | **是** |
| GSC 28d | 🟢 **0 / 0 / 0% / —**（上线前窗口，预期近零） | 否（基线） |
| Bing 90d | 🟢 **0 行** clicks/impr；feed sitemap Success 2026-11-02 | 否（基线） |
| GA4 11-02..04 | 🟡 Direct **23** sessions · bounce 首页高 · `form_start`×1 · 转化 0 | 备注 |
| CF 完整日 11-03 | 🟡 Uniques **256** / PV **237** / Req **3973** / Threats **24**（vs 11-02 403/669/5678/15） | DoD 备注（\|Δ\| PV/UV>20%），非基建回退；含爬虫 |
| 基建 | 🟢 核心语种/合规/sitemap/robots/llms/IndexNow key/GA4/CF beacon/主 CTA | 短路径别名 404 见基建 |
| 索引 | 🟡 四语首页已 indexed；enquiry/about/contact/合规/行程页仍 Discovered/unknown | 催收录，非回退 |
| 外链定额 | 🔴 无合规隔离邮 → **自动交 0** · NEED_BROWSER 待邮 · 误交 ASR/Viesearch **Void** · **Live 0** | **是** |
| 药效账本 | 🟡 PR#1/#2 7d=**2026-11-09** / 14d=**2026-11-16** 待复盘 | 催办日历 |

## 基线备忘（首次巡检写入 · 上线日 2026-11-02 近零）

| 指标 | 值 | 来源文件 |
|---|---|---|
| GSC 28d（截止 11-01） | clicks **0** · impressions **0** · CTR **0** · avg pos **0** · queries/pages 空 | `gsc-cli get-performance-overview` |
| GSC sitemap | submitted **29** · indexed（API 字段）**0** · warnings **29** · last download **2026-11-04T04:42:05Z** | `gsc-sitemaps.json` |
| URL 检查 indexed | `/` `/de/` `/es/` `/fr/` = **Submitted and indexed**（末次抓取约 11-04 UTC 早晨） | `gsc-inspect-*.json` |
| URL 检查未索引 | `/enquiry` unknown；`/about` `/contact` `/privacy-policy` `/journeys/beijing-xian-shanghai-12-days` `/de/china-rundreise-individuell` = Discovered/not indexed | 同左 |
| Bing 90d | rank-traffic / query / page / crawl rows **全部 0** | `bing-*-90d.json` |
| Bing feed | sitemap.xml · status Success · last_crawled **2026-11-02** · url_count 0（API 字段） | `bing-feeds.json` |
| Bing 配额 | daily **100** · monthly **2700** | `bing-quota.json` |
| GA4 11-02..04 | sessions **23**（全 Direct）；pages: `/` 24 PV / 20 users；`/es/` 3；`/de/` 2；`/enquiry` 1；`/es/agencia-de-viajes-a-china` 1 | `ga4-*.json` |
| GA4 行为 | desktop 18 / mobile 5；US 11 · JP 5；new 20 / returning 3；AI referrals confirmed **0** | 同左 |
| GA4 事件 | page_view 31 · session_start 23 · first_visit 20 · user_engagement 12 · scroll 5 · **form_start 1** · conversions **0** | `ga4-conversions.json` |
| CF 11-02 | PV **669** · Uniques **403** · Req **5678** · Threats **15** | `cf-graphql.json`（MCP） |
| CF 11-03（上一完整日） | PV **237** · Uniques **256** · Req **3973** · Threats **24** | 同左 |
| Clarity | **不可用（缺本站 token）** | 见缺凭据 |
| IndexNow | key 文件 200；批量 POST **HTTP 202**（9 URL） | `indexnow-curl.body` |
| Email Routing | enabled；**仅** `contact@`→Gmail；submit@ 规则 **已删** | CF MCP 17:51 复核 |

## 涨跌归因（固定四类）

1. **我方改动（药效账本）** — PR#1（9f868c6 一带）/ PR#2（0506374）于 11-02 上线；今日为首次巡检，GSC/Bing 搜索面仍近零，**禁止**把 CF DoD 或 Direct 会话说成单次 TDH 因果。7d 复盘日 **2026-11-09**。出处：`08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`
2. **外链/引荐** — 台账已建；因缺 AgentMail **今日无合规新外链**；误用已删 submit@ 的 ASR/Viesearch **Void、不计 Live**；GA4 无 referral/organic，全 Direct。出处：`目录站提交质量门控与证据账本（flaqai-backlink_skills）.md`；site-growth-operator Isolation email；`新站上线后能做的只有两件事：上内页，加外链.md`
3. **SERP 抖动 / 算法 / 竞品** — 主词战场被 GoChinaQuest、China Fantasy Travel、TourRadar、WildChina 等占据；CPJ 未进推荐列表（上线 2 天）。详见 `daily-runs/2026-11-04/competitors.md`
4. **不可证伪** — GSC 窗口截止 11-01（与上线日错位）；Clarity 无本站导出；CF Uniques 含 bot；box DNS 将 apex 解析到 `198.18.0.1` 导致 `gsc-cli bing-url-submit` URLSafety 拒绝（IndexNow 公网 API 仍 202）；`submit-url` 触发 OAuth browser disabled

## 知识库引用清单（本战报）

1. `增长知识库/01-SEO基础与SOP/01-上线SOP/SaaS站内SEO基建让Google看见看懂收录（Playbook摘要）.md` → 看见/收录优先  
2. `增长知识库/01-SEO基础与SOP/01-上线SOP/新站上线后能做的只有两件事：上内页，加外链.md` → 冷启动动作面  
3. `增长知识库/03-站内优化/01-页面优化/已有排名与出沙盒页面TDH修改红线（零掉词铁律与老板审批门禁）.md` → 零曝光也不擅自改 TDH  
4. `增长知识库/03-站内优化/01-页面优化/GEO硬核参数与真人极简体验解耦铁律（渐进式披露Progressive-Disclosure）.md` → 单主 CTA  
5. `增长知识库/03-站内优化/01-页面优化/Title 和 Description 要怎么写？.md` → 有曝光后再谈 CTR 文案  
6. `增长知识库/04-内容与外链/02-外链/目录站提交质量门控与证据账本（flaqai-backlink_skills）.md` → Live≠提交成功  
7. `增长知识库/04-内容与外链/02-外链/0DR起步优先提交的12个目录站.md` + `73个高DR外链提交渠道.md` → Brownbook/ASR/ExactSeek 优先级  
8. `增长知识库/08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md` → 7/14d 日历  
9. site-growth-operator **Isolation email** → 目录只用站点 AgentMail  

## 1. 基建健康

| 检查项 | 结果 |
|---|---|
| EN/DE/FR/ES 首页 | **200**（apex + Worker） |
| 合规 | `/privacy-policy` `/terms-of-service` `/about` `/contact` `/refund-policy` `/de/impressum` **200**；短路径 `/privacy` `/terms` `/refund` **404** |
| `/enquiry` | **200**；主 CTA「Send an enquiry」 |
| `sitemap.xml` | **200** · **29** `<loc>` |
| `robots.txt` | **200** · Allow `/` · Disallow admin/settings/api/`/*?*` · Sitemap 声明 |
| `llms.txt` / `llms-full.txt` | **200** |
| IndexNow key | `/$KEY.txt` **200**（key=`9eac16ecca27195bf1af3a494e021a65`） |
| GA4 埋点 | SSR `G-P248GHMDLE` loader+config **✓** |
| Clarity 埋点 | `integrations.clarityId=z76iipo4o5` **✓**（客户端注入；API 导出另议） |
| CF Web Analytics beacon | token `3db8fc9b…` **✓** |
| www→apex | `www` **200→** apex |
| Organization JSON-LD | legalName China Private Journeys · email `contact@…` · **无牌照号** |
| 过渡 Worker | 首页/语种/合规/enquiry **200**（与 apex 对齐） |
| 缺口 | EN `/best-time-to-visit-china` **404**（DE/ES/FR 指南在 sitemap）；`/ai.txt` 404（非必须） |

## 2. 询盘漏斗简况

- L1 基建/CTA：首页 + header 主按钮 → `/enquiry`；文案明确「No payment is taken here」。  
- GA4：23 Direct sessions；`/enquiry` 1 PV；**form_start×1**；无 `generate_lead`/keyEvents。  
- Clarity：本站 Data Export **不可用** → 死点/rage/scroll **无法证伪**。  
- 合规页 contact 公开 `contact@chinaprivatejourneys.com`（联系用，**不是**目录提交邮）。

## 3. 外链 / 目录（今日动作 · 站规修订后）

**🔴 缺 CPJ AgentMail — 外链段标红。** 今日起禁止自动提交；禁止填个人 Gmail / 已删 submit@。台账：`/workspace/cpj-backlink-ledger.md`。

| 项 | 结果（合规口径） |
|---|---|
| Active Search Results | **Void / 不计**（曾误用已删 submit@ POST；确认信无法再收） |
| Viesearch | **Void / 不计**（同上 + `/plan` 付费墙边缘，未付款） |
| ExactSeek | **NEED_BROWSER**（captcha；等 AgentMail） |
| Brownbook / Startup88 / ASEAN Now | **NEED_BROWSER**（等 AgentMail） |
| PeerPush | Failed/Down HTTP 522 |
| **合规自动交** | **0** |
| **Live** | **0** |
| IndexNow | **202** · 9 URL（无邮箱，保留） |
| Bing URL Submit CLI | DNS `198.18.0.1` URLSafety 拒绝 |
| GSC `submit-url` | OAuth browser disabled（inspect 可用） |

手动清单（停交）：`daily-runs/2026-11-04/manual-dirs.md`

## 4. 竞品 / AI 推荐位

见 `daily-runs/2026-11-04/competitors.md`。要点：private/tailor-made 词面被运营商与聚合平台占据；CPJ 差异化继续锁「enquiry-routing / 本站不收团款 / 非持牌社」，禁止发明牌照。

## 5. GSC 建议制预览（未改站）

完整预览：`daily-runs/2026-11-04/gsc-suggestions.md`  
**今日无 TDH multiSelect 提案**（零曝光 + 已拍板 Title/H1）。非 TDH 优先：催收录未索引 URL、短路径 301、补 EN best-time、enquiry 成功事件。

## 6. 合成结论

冷启动第 3 日：四语首页已被 Google 抓取并标 indexed；搜索点击/曝光与 Bing 流量仍为 **0**；真人流量信号主要来自 GA4 Direct + 1 次表单开始。增长杠杆仍是 **外链定额 + 内页收录**，但外链被 **AgentMail 满额** 挡住——开好 `cpj-submit@agentmail.to` 前只记 NEED_BROWSER。Clarity token 与 AgentMail 均为当日红灯。**未改任何 Title/meta/H1。**

## 乘胜追击 Todo

1. **【老板 · 阻断】** 腾出 AgentMail 名额或升级，开通 **`cpj-submit@agentmail.to`** 后再恢复目录提交  
2. **【老板 · 今日】** Clarity 项目 `z76iipo4o5` 生成 **Data Export API token** → `/home/box/secrets/china-private-journeys-analytics/clarity-api-token.txt`（**勿**复用 Frame token）  
3. **【可选】** 补 `CLOUDFLARE_API_TOKEN` 到 CPJ secrets  
4. AgentMail 就绪后：按 `manual-dirs.md` 浏览器交 ExactSeek / Brownbook / Startup88；ASR/Viesearch 视情况用合规邮重交；Viesearch **勿买**  
5. 非 TDH：短路径 → 正式合规 URL 的 301；评估 EN best-time 页  
6. 日历：**2026-11-09** 药效 7d；**2026-11-16** 14d  
7. 勿改 Title/meta/H1，直至 GSC 出现可证伪曝光  

## 缺凭据清单

| 缺项 | 影响 | 补法 |
|---|---|---|
| `clarity-api-token.txt`（CPJ 专用） | Clarity Data Export 硬门禁失败；漏斗不可证伪 | Clarity 项目 z76iipo4o5 → Data Export token → 写入 CPJ secrets |
| `cpj-submit@agentmail.to`（AgentMail 满 3/3） | 目录/外链无法合规提交 | 腾名额或扩容后创建 CPJ 隔离邮 |
| `CLOUDFLARE_API_TOKEN` 本地文件 | CLI/inspector 跳过 CF；今日已用 MCP 顶上 | 可选写入 CPJ secrets |
| GSC `submit-url` 非交互 OAuth | 无法 API 请求编入索引（inspect 仍可用） | 服务账号或预登录 token；短期靠 IndexNow+内链 |
| box DNS → `198.18.0.1` | `bing-url-submit` URLSafety 拒 | 环境限制；IndexNow 公网 API 可替代通知 |

## 今日外链动作结果摘要

- 站规修订后口径：**合规自动提交 0 · Live 0 · 外链段标红（缺 CPJ AgentMail）**  
- 修订前误操作（已 Void）：ASR、Viesearch 曾用已删 `submit@`——**不计 Pending/Live**  
- NEED_BROWSER 待 AgentMail：ExactSeek、Brownbook、Startup88、ASEAN Now  
- PeerPush：522 跳过  
- IndexNow：9 URL HTTP 202（保留）  

## 工件路径

- 战报：`/workspace/cpj-daily-growth-report-2026-11-04.md`  
- 台账：`/workspace/cpj-backlink-ledger.md`  
- 原始拉数：`/workspace/gsc-china-private-journeys/daily-runs/2026-11-04/`  
- 药效账本：`/workspace/seo-vault/增长知识库/08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`
