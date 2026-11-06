# China Private Journeys 每日增长战报 & 乘胜追击 Todo
**日期（Asia/Taipei）**: 2026-11-06  
**站点**: `https://chinaprivatejourneys.com`  
**Worker**: `https://china-private-journeys.zhangx2624.workers.dev`  
**巡检路由**: `CPJ每日竞品与GSC增长巡检 (cpj-gsc)` · cron 08:52 Asia/Shanghai

---

## 一、硬门禁表 (Hard Gates)

| 通道 | 状态 | 核心指标与详情 |
| :--- | :---: | :--- |
| **GSC** | 🟢 OK | 窗口 2026-10-07→2026-11-03；点击 **0**，展现 **0**，CTR 0%，均位 0。Sitemap：已提交 29 / 已收录 **0** / 警告 29；最后下载 2026-11-04。 |
| **Bing** | 🟢 OK | 站点已验证；11-02/11-03 点击/展现 **0**；crawl `in_index=0`；Sitemap Success（最后抓取 2026-11-02，url_count 0）；配额日 100 / 月 2500。 |
| **GA4** | 🟢 OK | Property `561855861` / `G-P248GHMDLE`；窗口 2026-11-02→11-05：Direct 会话 **34**，参与 5，转化 **0**，`form_start=1`，AI 确认会话 **0**，organic landing **0**。 |
| **Clarity** | 🟢 OK | 项目 `z76iipo4o5` **CPJ 专用 Token 已生效**（导出仅为 chinaprivatejourneys.com）。近 3 日首页真人会话 8、死点击 1（12.5%）、暴怒 0、均滚深 30.88%、Bot 18。昨日 Frame Token 污染已解除。 |
| **Cloudflare** | 🟢 OK | GraphQL + 本地 `cloudflare-api-token.txt` 可用。11-05：UV **249** / 请求 2391 / 威胁 12；11-04：UV 284 / 请求 1629 / 威胁 1。 |
| **Email Routing** | 🟢 OK（沿用） | `submit@` → `frame-submit@agentmail.to`；`contact@` → 客户邮。本轮 CF Email API 无读权限（token 范围不含 routing），以既有规则 + AgentMail 收信为准。 |

---

## 二、基线对比 (Baseline Ref)
* **对比基线**: 上线日 2026-11-02 近零 + 昨日战报 2026-11-05。
* **GSC**: 点击 0 / 展现 0（相对基线与昨日 **持平**）。
* **Bing**: 仍近零（持平）。
* **GA4 会话**: 昨日窗内约 30 → 今日同窗 **34**（+13.3%，仍全 Direct）。
* **CF UV DoD**: 11-05 **249** vs 11-04 **284**（**-12.3%**，未达 20% 标红）。
* **CF 请求 DoD**: 2391 vs 1629（**+46.8%**；更像爬虫/探测噪声，勿当 SEO 因果）。
* **Clarity**: 昨日 🔴 Frame 污染 → 今日 🟢 本站可读（质量跃迁，非流量跃迁）。

---

## 二点五、红绿灯（防疲劳）

| 维度 | 状态 | 标红？ |
|---|---|---|
| Clarity API | 🟢 CPJ Token 正常 | **否**（昨日红已灭） |
| GSC / Bing 搜索 | 🟢 仍近零 | 否 |
| GA4 会话 | 🟡 30→34（+13%，全 Direct） | 否 |
| CF UV DoD | 🟡 -12.3% | 否（&lt;20%） |
| 基建 | 🟢 合规真路径 200；GEO 两页 **200**（昨日 404 已解除） | 否 |
| 索引 | 🟡 Sitemap 29 提交 / 0 收录；GEO+enquiry 仍 Unknown | 备注 Todo |
| 外链 | 🟡 Live=1；今日 Jayde 新交 Pending；NEED_BROWSER 队列仍在 | 否 |
| 药效账本 | 🟡 PR#1/#2 7d=**2026-11-09**；PR#3/#4 7d=**2026-11-12**（今晨补记） | 催办日历 |

---

## 三、涨跌归因（固定四类）

1. **我方改动（药效账本）** — 2026-11-05 已上线 PR#3（`5402ca6` · Worker `980eba87…`：llms/robots/Org JSON-LD，**TDH 未动**）与 PR#4（`08c6a50`：两 GEO 长文由生产 404→200）。今日巡检 **补记**入药效账本；7d/14d 分别为 **2026-11-12 / 2026-11-19**。GSC/Bing 仍 0，**禁止**把 GA4 Direct +13% 或 CF 请求 +47% 说成单次 TDH/GEO 因果。出处：`08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`
2. **外链/目录/Referral** — Live 仍仅 Brownbook Claimed；今日新交 **Jayde → Pending**；ASR 会员已激活仍非 Live；Startup88 回执称可能 &gt;6 个月；PeerPush 仍 Coming soon。GA4 全 Direct、AI referral 0 → 外链尚未贡献可证伪搜索/引荐。出处：`04-内容与外链/02-外链/目录站提交质量门控与证据账本（flaqai-backlink_skills）.md` · `China-Private-Journeys外链与目录执行溯源台账.md`
3. **SERP 日常抖动 / 算法 / 竞品** — 搜索面仍 0 曝光，无从谈 CTR 抖动。私人定制中国游推荐位仍被 China Highlights / Asia Odyssey / WildChina / Travel China Guide / TourRadar 等占据；今日新观察 WindhorseTour、China Voyage 对比文、Homeground 价格矩阵等（见竞品栏）。CPJ 未进竞争片段（上线第 5 天）。
4. **数据不可证伪** — GSC 28d 截止 **2026-11-03**（上线后增量可能未进 API）；无询盘转化 API（`form_start=1` / conversions=0）；GA4 全 Direct 无法拆自然/外链；CF Uniques 含爬虫；Brownbook `backlink-guard` 403 不可读（curl 仍见 Claimed，勿标 Lost）。

---

## 四、基建 (Infrastructure)
* **首页 / 语种 / 合规真路径 / sitemap / robots / llms / enquiry / GEO 两页 / journey / Workers 过渡首页**: 均为 **200**；占位符 localhost/ShipAny/假牌照 **0**；HTML 页挂载 GA4 `G-P248GHMDLE` + Clarity `z76iipo4o5`；主 CTA/询盘在线。
* **合规路径校正**: 真 URL 为 `/terms-of-service`、`/refund-policy`（200）。裸 `/terms`、`/refund` 为 **404 别名**——内容未缺，需确认页脚/站内链不要链错。
* **GEO 长文**: `/how-private-china-trip-enquiry-works`、`/private-beijing-xian-shanghai-journey` 生产 **200**（相对昨日 404 的基建跃迁）。
* **GSC URL 检查（今日）**:
  * **Submitted and indexed**: `/`、`/privacy-policy`
  * **Discovered - not indexed**: `/about`、`/contact`、`/journeys/beijing-xian-shanghai-12-days`、`/terms-of-service`、`/refund-policy`
  * **URL unknown to Google**: `/enquiry`、两 GEO 长文
* **IndexNow**: 今日再提 10 URL → **HTTP 200**。

---

## 五、询盘漏斗 (Enquiry Funnel)
* **简漏斗（无转化 API）**: 浏览（GA4 首页 37 PV / 会话 34）→ `/enquiry` **1 PV** → `form_start=1` → conversions **0**。
* Clarity：首页滚深 ~31%，死点击 1、暴怒 0 —— 询盘意图仍极薄。
* **归因分类**: 缺转化 API → **第（4）类**。出处：`07-工具/01-SEO工具/全自动转化漏斗监控与7天药效复盘五步法（GSC-Clarity-GA4-GEO闭环）.md`

---

## 六、外链台账摘要 (Backlinks Ledger)
* **Live (1)**: Brownbook Claimed（guard 403；curl 证据维持 Live，勿改 Lost）。
* **Pending**: ExactSeek；ASR（会员已激活，无公开 listing）；Startup88（回执 &gt;6mo）；**Jayde（今日新交）**。
* **Queued**: PeerPush #10080 Coming soon（有 Visit site follow 链仍禁止 Live）。
* **Member ready / 无 listing**: ASEAN Now。
* **今日新增提交**: 1（Jayde）· **今日新增 Live**: 0 · 累计 Live = **1**。
* **NEED_BROWSER**: F6S / Touristlink / Cybo / Hotfrog / TinyLaunch / Addon Biz / SideProjectors。
* **邮箱**: 一律 `submit@chinaprivatejourneys.com`（→ `frame-submit@agentmail.to`）。
* 双写：`/workspace/cpj-backlink-ledger.md` + `增长知识库/04-内容与外链/02-外链/China-Private-Journeys外链与目录执行溯源台账.md`。

---

## 七、竞品简报 (Competitor Briefing)
* **仍占位**: China Highlights、Asia Odyssey、WildChina、Travel China Guide、The China Guide、TourRadar、Wendy Wu（团游品牌，勿与 Wendy Wei 混淆）。
* **今日新观察（截胡观察名单）**: WindhorseTour 私家团页；China Voyage「How to Compare China Tour Operators (2026)」；Homeground 价格矩阵（竞品自称 BJ 牌照 **勿镜像为 CPJ**）；Wendy Wei Tours；CHINATOUR.US；ChinaTourly；ChinaMira 渐进披露询盘。
* **CPJ**: 竞争头词片段中 **未出现**（day 5）。策略仍只做 **上内页 + 质量外链**；不追 TDH。
* 出处：`01-SEO基础与SOP/01-上线SOP/新站上线后能做的只有两件事：上内页，加外链.md` · `04-内容与外链/01-内容策略/谷歌与ChatGPT双引擎GEO五步骤（Geektao实测）.md`

---

## 八、GSC 建议制预览 (Preview Only · 不擅自改站)

1. **优先索引健康**：对 GEO 两页、`/enquiry`、journey 做 Request indexing / 持续 Coverage 观察；「已发现未索引」按可救工作量处理，不先改 TDH。  
   → `03-站内优化/02-技术SEO/「已抓取但未编入索引」是能救的，但工作量比你想的大.md` · `01-SEO基础与SOP/01-上线SOP/新站上线后能做的只有两件事：上内页，加外链.md`
2. **印象=0 时不动首页/旅程 TDH**：只登记候选；须 Halo multiSelect 拍板后才执行。  
   → `03-站内优化/01-页面优化/已有排名与出沙盒页面TDH修改红线（零掉词铁律与老板审批门禁）.md`
3. **询盘 CTA 钩子（非 Title/H1）**：英雄区保持极简；硬核履约/无站内订金/规划师交接放渐进披露，改善滚深与 `form_start`。  
   → `03-站内优化/01-页面优化/GEO硬核参数与真人极简体验解耦铁律（渐进式披露Progressive-Disclosure）.md` · `07-工具/01-SEO工具/全自动转化漏斗监控与7天药效复盘五步法（GSC-Clarity-GA4-GEO闭环）.md`
4. **合规 URL 卫生（非 TDH）**：页脚/确认页统一链到 `/terms-of-service`、`/refund-policy`、`/privacy-policy`；平台表述，不发明牌照。  
   → `06-出海建站/02-收款与合规/出海应用上线前6大合规避坑清单与自检Prompt.md`
5. **低 CTR 机会词（预备清单）**：有展现后再按 CTR 分诊 `private China tours` / `private guided tour China` / BXS private 等；离线起草 Title/Description，禁止静默上线。  
   → `03-站内优化/01-页面优化/Title 和 Description 要怎么写？.md` · TDH 红线同上
6. **目录质量门控**：只交有证据的免费项；Pending≠Live；旅行向验证码站进 NEED_BROWSER。  
   → `04-内容与外链/02-外链/目录站提交质量门控与证据账本（flaqai-backlink_skills）.md` · CPJ 外链台账
7. **药效账本节奏**：PR#3/#4 已补记；按 7/14 天可证伪指标复盘，Direct 流量不算 SEO 胜。  
   → `08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`

---

## 九、知识库引用清单
1. `01-SEO基础与SOP/01-上线SOP/新站上线后能做的只有两件事：上内页，加外链.md`
2. `01-SEO基础与SOP/新站上线与周期巡检三合一SOP（五合一统计+零模板残留+外链反作弊）.md`
3. `03-站内优化/01-页面优化/已有排名与出沙盒页面TDH修改红线（零掉词铁律与老板审批门禁）.md`
4. `03-站内优化/01-页面优化/GEO硬核参数与真人极简体验解耦铁律（渐进式披露Progressive-Disclosure）.md`
5. `03-站内优化/01-页面优化/Title 和 Description 要怎么写？.md`
6. `03-站内优化/02-技术SEO/「已抓取但未编入索引」是能救的，但工作量比你想的大.md`
7. `04-内容与外链/01-内容策略/谷歌与ChatGPT双引擎GEO五步骤（Geektao实测）.md`
8. `04-内容与外链/02-外链/目录站提交质量门控与证据账本（flaqai-backlink_skills）.md`
9. `04-内容与外链/02-外链/China-Private-Journeys外链与目录执行溯源台账.md`
10. `04-内容与外链/02-外链/0DR起步优先提交的12个目录站.md`
11. `06-出海建站/02-收款与合规/出海应用上线前6大合规避坑清单与自检Prompt.md`
12. `07-工具/01-SEO工具/全自动转化漏斗监控与7天药效复盘五步法（GSC-Clarity-GA4-GEO闭环）.md`
13. `08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`

---

## 十、乘胜追击 Todo (Action Items & MultiSelect)

- [ ] **[multiSelect]** 在 GSC 对 `/enquiry` + 两 GEO 长文 + journey 点 Request indexing（或确认是否启用 Indexing API 通知）
- [ ] **[multiSelect]** 非 TDH 卫生 PR：页脚/站内链统一 `/terms-of-service` + `/refund-policy`（避免链到 404 别名）
- [ ] **[multiSelect]** NEED_BROWSER 目录队列人工推进（F6S / Touristlink / Cybo / Hotfrog / TinyLaunch / Addon Biz / SideProjectors）；邮只用 `submit@`
- [ ] **[日历]** PR#1/#2 7 天药效复盘日 **2026-11-09**；PR#3/#4 7 天 **2026-11-12**
- [ ] （信息项）Clarity CPJ Token 已绿；无需再修 Frame 污染

