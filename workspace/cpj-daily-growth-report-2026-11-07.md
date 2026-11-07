# China Private Journeys 每日增长战报 & 乘胜追击 Todo
**日期（Asia/Taipei）**: 2026-11-07  
**站点**: `https://chinaprivatejourneys.com`  
**Worker**: `https://china-private-journeys.zhangx2624.workers.dev`  
**巡检路由**: `CPJ每日竞品与GSC增长巡检 (cpj-gsc)` · cron 08:52 Asia/Shanghai  
**原始数据**: `/workspace/cpj-daily-2026-11-07/`

---

## 一、硬门禁表 (Hard Gates)

| 通道 | 状态 | 核心指标与详情 |
| :--- | :---: | :--- |
| **GSC** | 🟢 OK | 窗口 2026-10-08→2026-11-04；点击 **0**，展现 **0**，CTR 0%，均位 0。queries/pages 空。 |
| **Bing** | 🟢 OK | 站点已验证；有行日 11-02/11-03 点击/展现 **0**；`in_index=0`；窗口 90d。 |
| **GA4** | 🟢 OK | Property `561855861` / `G-P248GHMDLE`；窗口 2026-11-02→11-06：Direct 会话 **37** + Unassigned **1** = **38**；参与 6；转化 **0**；`form_start=1`；首页 PV **40** / enquiry PV **1**；AI 确认 **0**；organic landing **0**。 |
| **Clarity** | 🟢 OK | 项目 `z76iipo4o5` 主机仅为 **chinaprivatejourneys.com**（非 Frame）。近 3 日首页真人会话 **5**、Bot **16**、死点击 1（20%/5）、暴怒 **0**、均滚深 **35.2%**。 |
| **Cloudflare** | 🟢 OK | GraphQL 本地 token 可用。**11-06**：UV **268** / 请求 **2966** / PV **401** / 威胁 5；11-05：UV 249 / 请求 2391 / PV 200。 |
| **Email Routing** | 🟢 OK（沿用） | `submit@` → `frame-submit@agentmail.to`；AgentMail 自 11-06 后无新 CPJ 验证信。 |

---

## 二、基线对比 (Baseline Ref)
* **对比基线**: 上线日 2026-11-02 近零 + 昨日战报 2026-11-06。
* **GSC**: 点击 0 / 展现 0（相对基线与昨日 **持平**；窗口末日 11-03→**11-04**）。
* **Bing**: 仍近零（持平）。
* **GA4 会话**: 昨日窗内 Direct **34** → 今日同窗含 11-06 共 Direct **37**（+3 / +8.8%，仍几乎全 Direct）。
* **CF UV DoD**: 11-06 **268** vs 11-05 **249**（**+7.6%**，未达 20% 标红）。
* **CF 请求 DoD**: 2966 vs 2391（**+24.1%**）；**PV DoD**: 401 vs 200（**+100.5%**）——更像爬虫/探测噪声（Clarity 首页 Bot 16 vs 真人 5），勿当 SEO 因果。
* **外链 Live**: 昨日 **1** → 今日 **2**（+Addon Biz nofollow）。

---

## 二点五、红绿灯（防疲劳）

| 维度 | 状态 | 标红？ |
|---|---|---|
| GSC / Bing 搜索 | 🟢 仍近零 | **否** |
| GA4 会话 | 🟡 34→37（+8.8%，全 Direct） | 否 |
| CF UV DoD | 🟢 +7.6% | 否 |
| CF 请求/PV DoD | 🟡 请求 +24% / PV +100%（爬虫噪声） | 否（非搜索面；见归因） |
| Clarity | 🟢 CPJ Token；死点 20% 但 n=5 | 否 |
| 基建 | 🟢 合规真路径 + GEO + enquiry 200；占位符 0 | 否 |
| 索引 | 🟡 搜索仍 0；IndexNow 今日 10 URL → **200** | 备注 Todo |
| 外链 | 🟢 Live **1→2**（Addon Biz 新 Live） | 否（正向） |
| 药效账本 | 🟡 今日无到期行；下一闸 **2026-11-09**（PR#1/#2 7d） | 催办日历 |

---

## 三、涨跌归因（固定四类）

1. **我方改动（药效账本）** — PR#3（`5402ca6`）/ PR#4（`08c6a50`）仍在 7d 观察窗内（复盘日 **2026-11-12**）；今日无新增长部署。GSC/Bing 仍 0，**禁止**把 CF PV/请求跳高或 GA4 Direct +3 说成单次 TDH/GEO 因果。出处：`08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`
2. **外链/目录/Referral** — 今日新 Live：**Addon Biz**（`https://www.addonbiz.com/listing/guangzhou-china-china-private-journeys/`，backlink-guard = qualified / `rel=nofollow` sidebar）。Live 累计 **2**（Brownbook Claimed + Addon Biz）。GA4 仍无 Referral/organic → 外链尚未贡献可证伪搜索/引荐。出处：`04-内容与外链/02-外链/目录站提交质量门控与证据账本（flaqai-backlink_skills）.md` · `China-Private-Journeys外链与目录执行溯源台账.md` · `Nofollow 外链也别嫌弃，对于权重提升有作用.md`
3. **SERP 日常抖动 / 算法 / 竞品** — 搜索面仍 0 曝光，无从谈 CTR 抖动。私人定制中国游位仍被 China Highlights / WildChina / Audley / Remote Lands / TourRadar 等占据；今日新观察：**WeTrip**（AI planner vs China Highlights 对比文）、**D1D1** / **ChinaGo.ai**（AI inbound planner/撮合）、**WildConcierge**（WildChina AI 前置）、价格矩阵站 **Homeground** / **China with Ease** / **china-travel.org**（BXS 报价文）。CPJ 未进竞争片段（上线第 6 天）。
4. **数据不可证伪** — GSC 28d 截止 **2026-11-04**（更新滞后）；无询盘转化 API（`form_start=1` / conversions=0）；GA4 几乎全 Direct；CF Uniques/PV 含爬虫；Brownbook `backlink-guard` 仍 403（curl 维持 Claimed，勿标 Lost）；Addon Biz 为 nofollow，短期难证 SEO 因果。

---

## 四、基建 (Infrastructure)
* **首页 / Workers / 合规真路径 / sitemap(31) / robots(AI Allows) / llms / enquiry / GEO 两页 / journey**: 均为 **200**；占位符 localhost/ShipAny/假牌照 **0**；GA4 `G-P248GHMDLE` + Clarity `z76iipo4o5`；Org JSON-LD = China Private Journeys / contact@ / Guangzhou Tianhe / enquiry-routing（非持牌旅行社）。
* **合规路径**: 真 URL `/privacy-policy` `/terms-of-service` `/refund-policy`（200）。裸 `/privacy` `/terms` `/refund` 仍 **404**（内容未缺，别名卫生待拍板）。
* **IndexNow**: 今日再提 10 URL → **HTTP 200**。
* 出处：`01-SEO基础与SOP/新站上线与周期巡检三合一SOP（五合一统计+零模板残留+外链反作弊）.md` · SaaS 站内 SEO 基建 Playbook

---

## 五、询盘漏斗 (Enquiry Funnel)
* **简漏斗（无转化 API）**: 浏览（GA4 首页 PV **40** / 会话 ~38）→ `/enquiry` **1 PV** → `form_start=1` → conversions **0**。
* Clarity：首页滚深 ~35%，死点击 1、暴怒 0 —— 询盘意图仍极薄。
* `/enquiry` 表单字段与 submit 在线；`mailto:contact@` 备用在 `/contact`。
* **归因分类**: 缺转化 API → **第（4）类**。出处：`07-工具/01-SEO工具/全自动转化漏斗监控与7天药效复盘五步法（GSC-Clarity-GA4-GEO闭环）.md`

---

## 六、外链台账摘要 (Backlinks Ledger)
* **Live (2)**: Brownbook Claimed；**Addon Biz**（今日新 · nofollow qualified）。
* **Pending**: ExactSeek；ASR（会员已激活仍非 Live）；Startup88（>6mo）；Jayde（无 listing 信）。
* **Queued**: PeerPush Coming soon（禁止 Live）。
* **Member ready / 无 listing**: ASEAN Now。
* **今日新增提交**: 1（Addon Biz）· **今日新增 Live**: **1** · 累计 Live = **2** · Lost = **0**。
* **NEED_BROWSER**: F6S / Touristlink / Cybo / Hotfrog / TinyLaunch / SideProjectors / Crunchbase / Travellerspoint / ShowMySites / Toolfio / DodoDirectory。
* **邮箱**: 一律 `submit@chinaprivatejourneys.com`（→ `frame-submit@agentmail.to`）；AgentMail 无新 CPJ 信。
* 双写已完成：`/workspace/cpj-backlink-ledger.md` + 知识库台账（git `837d9c5` 已推 origin）。

---

## 七、竞品简报 (Competitor Briefing)
* **仍占位**: China Highlights、WildChina、Audley、Remote Lands、TourRadar、Asia Odyssey、The China Guide。
* **今日新观察（截胡观察名单）**:
  * WeTrip vs China Highlights 2026 对比（AI 先出行程再人工）
  * WildChina WildConcierge AI 前置
  * D1D1 / ChinaGo.ai（AI inbound / 专家撮合）
  * Homeground / China with Ease / china-travel.org 价格与 BXS 私家团矩阵（**勿镜像竞品自称牌照到 CPJ**）
* **CPJ**: 竞争头词片段中 **未出现**（day 6）。策略仍只做 **上内页 + 质量外链**；不追 TDH。
* 出处：`01-SEO基础与SOP/01-上线SOP/新站上线后能做的只有两件事：上内页，加外链.md` · `04-内容与外链/01-内容策略/谷歌与ChatGPT双引擎GEO五步骤（Geektao实测）.md`

---

## 八、GSC 建议制预览 (Preview Only · 不擅自改站)

1. **优先索引健康**：持续观察 GEO 两页、`/enquiry`、journey；IndexNow 已再推；有展现前不改 TDH。  
   → `03-站内优化/02-技术SEO/「已抓取但未编入索引」是能救的，但工作量比你想的大.md` · `新站上线后能做的只有两件事：上内页，加外链.md`
2. **印象=0 时不动首页/旅程 TDH**：只登记候选；须 Halo multiSelect 拍板。  
   → `已有排名与出沙盒页面TDH修改红线（零掉词铁律与老板审批门禁）.md`
3. **询盘 CTA 钩子（非 Title/H1）**：英雄区保持极简；履约/无站内订金/规划师交接放渐进披露，改善滚深与 `form_start`。  
   → `GEO硬核参数与真人极简体验解耦铁律（渐进式披露Progressive-Disclosure）.md` · 漏斗五步法
4. **合规 URL 卫生（非 TDH）**：页脚统一 `/terms-of-service` + `/refund-policy` + `/privacy-policy`；可选短路径 301（待拍板）。  
   → `出海应用上线前6大合规避坑清单与自检Prompt.md`
5. **低 CTR 机会词（预备）**：有展现后再分诊 `private China tours` / BXS private 等；离线起草，禁止静默上线。  
   → `Title 和 Description 要怎么写？.md` · TDH 红线
6. **目录质量门控**：继续免验证码可交项；Pending≠Live；旅行向验证码站进 NEED_BROWSER（今日 14:00 例程出清单）。  
   → 目录站提交质量门控 · CPJ 外链台账
7. **药效账本节奏**：下一闸 **2026-11-09**（PR#1/#2）；**2026-11-12**（PR#3/#4）。Direct 流量不算 SEO 胜。  
   → CPJ 药效复盘账本

---

## 九、知识库引用清单
1. `01-SEO基础与SOP/01-上线SOP/新站上线后能做的只有两件事：上内页，加外链.md`
2. `01-SEO基础与SOP/新站上线与周期巡检三合一SOP（五合一统计+零模板残留+外链反作弊）.md`
3. `01-SEO基础与SOP/01-上线SOP/SaaS站内SEO基建让Google看见看懂收录（Playbook摘要）.md`
4. `03-站内优化/01-页面优化/已有排名与出沙盒页面TDH修改红线（零掉词铁律与老板审批门禁）.md`
5. `03-站内优化/01-页面优化/GEO硬核参数与真人极简体验解耦铁律（渐进式披露Progressive-Disclosure）.md`
6. `03-站内优化/01-页面优化/Title 和 Description 要怎么写？.md`
7. `03-站内优化/02-技术SEO/「已抓取但未编入索引」是能救的，但工作量比你想的大.md`
8. `04-内容与外链/01-内容策略/谷歌与ChatGPT双引擎GEO五步骤（Geektao实测）.md`
9. `04-内容与外链/02-外链/目录站提交质量门控与证据账本（flaqai-backlink_skills）.md`
10. `04-内容与外链/02-外链/China-Private-Journeys外链与目录执行溯源台账.md`
11. `04-内容与外链/02-外链/Nofollow 外链也别嫌弃，对于权重提升有作用.md`
12. `06-出海建站/02-收款与合规/出海应用上线前6大合规避坑清单与自检Prompt.md`
13. `07-工具/01-SEO工具/全自动转化漏斗监控与7天药效复盘五步法（GSC-Clarity-GA4-GEO闭环）.md`
14. `08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`

---

## 十、乘胜追击 Todo (Action Items & MultiSelect)

- [ ] **[multiSelect]** 在 GSC 对 `/enquiry` + 两 GEO 长文 + journey 再确认 Request indexing / Coverage
- [ ] **[multiSelect]** 非 TDH 卫生 PR：页脚/站内链统一 `/terms-of-service` + `/refund-policy`（可选短路径 301）
- [ ] **[multiSelect]** NEED_BROWSER 目录队列人工推进（优先旅行向：Touristlink / Travellerspoint / F6S / Hotfrog…）；邮只用 `submit@`
- [ ] **[日历]** PR#1/#2 7 天药效复盘日 **2026-11-09**；PR#3/#4 7 天 **2026-11-12**
- [ ] （信息项）Live 外链 **2**（+Addon Biz nofollow）；无标红；GSC/Bing 仍 0 — 继续上内页+外链，不动 TDH
