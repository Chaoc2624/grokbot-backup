# China Private Journeys 每日增长战报 & 乘胜追击 Todo
**日期（Asia/Taipei）**: 2026-11-08  
**站点**: `https://chinaprivatejourneys.com`  
**Worker**: `https://china-private-journeys.zhangx2624.workers.dev`  
**巡检路由**: `CPJ每日竞品与GSC增长巡检 (cpj-gsc)` · cron 08:52 Asia/Shanghai  
**原始数据**: `/workspace/cpj-daily-2026-11-08/`

---

## 一、硬门禁表 (Hard Gates)

| 通道 | 状态 | 核心指标与详情 |
| :--- | :---: | :--- |
| **GSC** | 🟢 OK | 窗口 2026-10-09→2026-11-05；点击 **0**，展现 **1**（昨日同口径为 0；窗口末日 11-04→**11-05**），CTR 0%，均位 1.0。queries 仍空（匿名查询）。页面行：首页展现 1 / 均位 1；`/privacy-policy` 展现 1 / 均位 2（总览展现=1，页面维或为同一次曝光/站点链接，n=1 不作拆分结论）。 |
| **Bing** | 🟢 OK | 站点已验证；有行日 11-02/11-03/**11-04** 点击/展现 **0**；`in_index=0`；11-03 `crawled_pages=5`；窗口 90d。 |
| **GA4** | 🟢 OK | Property `561855861` / `G-P248GHMDLE`；窗口 2026-11-02→11-07：Direct 会话 **43** + Unassigned **1** = **44**；参与 7；转化 **0**；`form_start=1`；首页 PV **46** / enquiry PV **1**；AI 确认 **0**；organic landing **0**。 |
| **Clarity** | 🟢 OK | 项目 `z76iipo4o5` 主机仅为 **chinaprivatejourneys.com**（非 Frame）。近 3 日首页真人会话 **5**、Bot **12**、死点击 **0**、暴怒 **0**、均滚深 **30.67%**。近 1 日首页真人 2 / Bot 4。 |
| **Cloudflare** | 🟢 OK | GraphQL 本地 token 可用。**11-07**：UV **198** / 请求 **1356** / PV **283** / 威胁 0 / 字节 15147371；11-06：UV 268 / 请求 2966 / PV 401。11-08 截至约 09:09 仅为不完整日（UV 6 / 请求 6 / PV 3），不作 DoD。 |
| **Email Routing** | 🟢 OK | `submit@` → `frame-submit@agentmail.to` 仍通（11-07 下午 To=`submit@` 的 TinyLaunch / F6S 信已入箱）。11-07 17:40 之后无新的 CPJ listing/验证信（ExactSeek / ASR / Jayde / Startup88 均无新信）。共享箱噪声：TipSeason 通讯（2026-11-08 00:07 Taipei，To 为 frame-submit 本身）；另有一封 Frame Extractor 的 TinyLaunch 通过信也落到 `submit@`（**不是** CPJ listing）。 |

---

## 二、基线对比 (Baseline Ref)
* **对比基线**: 上线日 2026-11-02 近零 + 昨日战报 2026-11-07。上线第 **7** 天。
* **GSC**: 点击 0 / 展现 **0→1**（窗口末日 11-04→**11-05**）。n=1 且查询被匿名，**不**另拉 7 日切片（无法构成可解释的 WoW 语境；更像窗口滚入 11-05 后的首次曝光）。
* **Bing**: 仍近零（持平）；多出 11-04 零流量行。
* **GA4 会话**: 昨日窗内 Direct **37** → 今日同窗含 11-07 共 Direct **43**（+6 / +16.2%，未达 20%；仍几乎全 Direct）。`form_start` 1→1；enquiry PV 1→1；首页 PV 40→46。
* **CF UV DoD**: 11-07 **198** vs 11-06 **268**（**-26.1%**）。
* **CF 请求 DoD**: 1356 vs 2966（**-54.3%**）；**PV DoD**: 283 vs 401（**-29.4%**）——与昨日 11-06 爬虫尖峰回落一致（11-05 曾为 UV 249 / 请求 2391 / PV 200）。GA4 Direct 反而上升、Clarity 首页真人 3 日仍为 5，故视为爬虫噪声回归，勿当 SEO 因果。
* **外链 Live**: 昨日下午台账 **3**（Brownbook + Addon Biz + F6S）→ 今日复验 **维持 3**。

---

## 二点五、红绿灯（防疲劳）

| 维度 | 状态 | 标红？ |
|---|---|---|
| GSC / Bing 搜索 | 🟡 谷歌首次展现 n=1；Bing 仍 0 | **否**（n=1，非可操作波动） |
| GA4 会话 | 🟢 37→43（+16.2%，全 Direct） | 否 |
| CF UV DoD | 🟡 −26.1% | 否（见归因；爬虫回落） |
| CF 请求/PV DoD | 🟡 请求 −54% / PV −29%（相对 11-06 尖峰回落） | 否（非搜索面） |
| Clarity | 🟢 CPJ Token；真人 5 持平；死点 0；Bot 16→12 | 否 |
| 基建 | 🟢 合规真路径 + GEO + enquiry 200；占位符 0 | 否 |
| 索引 | 🟡 搜索刚出现 1 次展现；IndexNow 今日 10 URL → **200** | 备注 Todo |
| 外链 | 🟢 Live **3** 维持 | 否 |
| 药效账本 | 🟡 今日无到期行；下一闸 **2026-11-09**（PR#1/#2 7d） | 催办日历 |

---

## 三、涨跌归因（固定四类）

1. **我方改动（药效账本）** — 今日无新增长部署、无 TDH/站内修改。PR#1（`9f868c6`）/ PR#2（`0506374`）7d 复盘日为 **明天 2026-11-09**；PR#3（`5402ca6`）/ PR#4（`08c6a50`）7d 为 **2026-11-12**。GSC 窗口只到 **2026-11-05**，因此 **不能**把 11-06 的 Request indexing 说成这次展现的原因；n=1 也禁止把首次展现或 CF 回落写成单次 TDH/GEO 因果。出处：`08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`
2. **外链/目录/Referral** — Live 维持 **3**：Brownbook Claimed（curl UA 仍见 Claimed×2 + 域名×13；`backlink-guard` 仍 403，勿标 Lost）；Addon Biz nofollow qualified（200，域名提及 3）；F6S `https://www.f6s.com/china-private-journeys` HTTP 200 但今日 bot 只吃到验证码拦截页（WebFetch 403，guard 在挑战 HTML 上 not found）——按 Brownbook 同类处理，**不改 Lost**。GA4 仍无 Referral/organic → 外链尚未贡献可证伪搜索/引荐。11-07 下午已入账、今日确认：TinyLaunch #30842 **Rejected**（非 SaaS，勿再交）；Touristlink / SideProjectors **Blocked**；Toolfio / DodoDirectory **Skipped**。出处：`04-内容与外链/02-外链/目录站提交质量门控与证据账本（flaqai-backlink_skills）.md` · `China-Private-Journeys外链与目录执行溯源台账.md` · `Nofollow 外链也别嫌弃，对于权重提升有作用.md`
3. **SERP 日常抖动 / 算法 / 竞品** — 谷歌仅 1 次匿名展现，无从谈 CTR 抖动。BXS / 私人中国游位仍被传统运营商与报价页占据（China with Ease 7 日 BXS from $1,699；The China Guide 9 日黄金三角；TourRadar 上的 Travel China Guide 私人 8 日与 The Dragon Trip 10 日团体团）。今日相对昨日名单的新观察：**Silk Road Travel** BXS 私人团页（from $1,490）。AI planner 集合（WeTrip / D1D1 / ChinaGo.ai / WildConcierge）仍在，无新头部名称。CPJ 未进竞争片段（上线第 7 天）。
4. **数据不可证伪** — GSC 28d 截止 **2026-11-05**（更新滞后）；展现 n=1 且查询被匿名；无询盘转化 API（`form_start=1` / conversions=0）；GA4 几乎全 Direct；CF Uniques/PV 含爬虫（11-06 尖峰后的 11-07 回落）；F6S 今日无法重读正文；Brownbook `backlink-guard` 仍 403；共享隔离箱混有 Frame Extractor / newsletter 噪声。

---

## 四、基建 (Infrastructure)
* **首页 / Workers / 合规真路径 / sitemap(31) / robots(AI Allows) / llms / enquiry / GEO 两页 / journey /de /es**: 均为 **200**；占位符 localhost/ShipAny/假牌照 **0**；GA4 `G-P248GHMDLE` + Clarity `z76iipo4o5`；Org JSON-LD = China Private Journeys / contact@ / Guangzhou Tianhe / enquiry-routing（非持牌旅行社）。
* **合规路径**: 真 URL `/privacy-policy` `/terms-of-service` `/refund-policy`（200）。裸 `/privacy` `/terms` `/refund` 仍 **404**（内容未缺，别名卫生待拍板）。
* **IndexNow**: 今日再提 10 URL → **HTTP 200**。
* 出处：`01-SEO基础与SOP/新站上线与周期巡检三合一SOP（五合一统计+零模板残留+外链反作弊）.md` · SaaS 站内 SEO 基建 Playbook

---

## 五、询盘漏斗 (Enquiry Funnel)
* **简漏斗（无转化 API）**: 浏览（GA4 首页 PV **46** / 会话 **44**）→ `/enquiry` **1 PV** → `form_start=1` → conversions **0**。
* Clarity：首页 3 日滚深 ~30.67%，死点击 0、暴怒 0；enquiry / 两篇 GEO / 12 日行程页近 3 日仅见 Bot 会话各 1 —— 询盘意图仍极薄。
* `/enquiry` 表单字段与 submit 在线；`mailto:contact@` 备用在 `/contact`。
* **归因分类**: 缺转化 API → **第（4）类**。出处：`07-工具/01-SEO工具/全自动转化漏斗监控与7天药效复盘五步法（GSC-Clarity-GA4-GEO闭环）.md`

---

## 六、外链台账摘要 (Backlinks Ledger)
* **Live (3)**: Brownbook Claimed；Addon Biz（nofollow qualified）；F6S（公开公司页；今日 bot 验证码墙，不改 Lost）。
* **Pending (4)**: ExactSeek；ASR（会员已激活仍非 Live）；Startup88（>6mo）；Jayde（无 listing 信）。
* **Queued (1)**: PeerPush Coming soon（禁止 Live）。
* **Member ready / 无 listing**: ASEAN Now。
* **Rejected**: TinyLaunch #30842（非 SaaS；**勿再交**）。
* **Blocked**: Touristlink（`submit@` 被拒）；SideProjectors（密码校验失败，停止重试）。
* **Skipped**: Toolfio；DodoDirectory（永久徽章 / 付费 / 品类不合）。
* **今日新增提交**: 0 · **今日新增 Live**: **0** · 累计 Live = **3** · Lost = **0**。
* **NEED_BROWSER（留给 14:00；已剔除拒/拦/跳过项）**: Crunchbase / Cybo / Hotfrog / Travellerspoint / ShowMySites。
* **邮箱**: 一律 `submit@chinaprivatejourneys.com`（→ `frame-submit@agentmail.to`）；无新的 CPJ listing/验证信。
* 双写：`/workspace/cpj-backlink-ledger.md` + 知识库台账。

---

## 七、竞品简报 (Competitor Briefing)
* **仍占位**: China Highlights、WildChina、Audley、Remote Lands、TourRadar、Asia Odyssey、The China Guide；价格/BXS 矩阵站 **China with Ease**（7 日 BXS from $1,699）仍靠前。
* **相对昨日的增量观察**:
  * **Silk Road Travel**（`silkroadtravel.com`）BXS 私人团页，标价 from $1,490 —— 昨日名单未单列。
  * TourRadar 继续出现 Travel China Guide 私人 8 日黄金三角（约 $2,319）与 The Dragon Trip 10 日团体团（约 $3,090）——团体产品勿与 CPJ 询盘路由对标。
  * AI planner 集合无新头部：WeTrip、D1D1、ChinaGo.ai、WildConcierge 仍在。
* **CPJ**: 竞争头词片段中 **未出现**（day 7）。策略仍只做 **上内页 + 质量外链**；不追 TDH。
* 出处：`01-SEO基础与SOP/01-上线SOP/新站上线后能做的只有两件事：上内页，加外链.md` · `04-内容与外链/01-内容策略/谷歌与ChatGPT双引擎GEO五步骤（Geektao实测）.md`

---

## 八、GSC 建议制预览 (Preview Only · 不擅自改站)

1. **优先索引健康**：首次展现出现在首页与 `/privacy-policy`（n=1、查询匿名）。持续观察 GEO 两页、`/enquiry`、journey；IndexNow 已再推；有可分诊查询之前不改 TDH。  
   → `03-站内优化/02-技术SEO/「已抓取但未编入索引」是能救的，但工作量比你想的大.md` · `新站上线后能做的只有两件事：上内页，加外链.md`
2. **印象仍近零时不动首页/旅程 TDH**：n=1 不是改 Title/H1 的理由；只登记候选；须 Halo multiSelect 拍板。  
   → `已有排名与出沙盒页面TDH修改红线（零掉词铁律与老板审批门禁）.md`
3. **询盘 CTA 钩子（非 Title/H1）**：英雄区保持极简；履约/无站内订金/规划师交接放渐进披露，改善滚深与 `form_start`（今日漏斗仍是 46 首页 PV → 1 enquiry → 1 form_start → 0 转化）。  
   → `GEO硬核参数与真人极简体验解耦铁律（渐进式披露Progressive-Disclosure）.md` · 漏斗五步法
4. **合规 URL 卫生（非 TDH）**：页脚统一 `/terms-of-service` + `/refund-policy` + `/privacy-policy`；可选短路径 301（待拍板）。  
   → `出海应用上线前6大合规避坑清单与自检Prompt.md`
5. **低 CTR 机会词（预备）**：有可识别查询后再分诊 `private China tours` / BXS private 等；今日 queries 为空，禁止臆造词包或静默上线。  
   → `Title 和 Description 要怎么写？.md` · TDH 红线
6. **目录质量门控**：晨间未发现可 curl/API、免费、无验证码、无互挂徽章的剩余目录，故未代交。Pending≠Live；旅行向验证码站进 14:00 NEED_BROWSER（已剔除 TinyLaunch / Touristlink / Toolfio / DodoDirectory / SideProjectors）。  
   → 目录站提交质量门控 · CPJ 外链台账
7. **药效账本节奏**：下一闸 **2026-11-09**（PR#1/#2）；**2026-11-12**（PR#3/#4）。Direct 流量与 CF 爬虫回落都不算 SEO 胜负。  
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

- [ ] **[multiSelect]** 在 GSC 对首页（已有 1 次展现）+ `/privacy-policy` + `/enquiry` + 两 GEO 长文 + journey 再确认 Coverage / 是否仍需 Request indexing
- [ ] **[multiSelect]** 非 TDH 卫生 PR：页脚/站内链统一 `/terms-of-service` + `/refund-policy`（可选短路径 301）
- [ ] **[multiSelect]** NEED_BROWSER 目录队列人工推进（Crunchbase / Cybo / Hotfrog / Travellerspoint / ShowMySites）；邮只用 `submit@`。**不要**再交 TinyLaunch、Touristlink、Toolfio、DodoDirectory、SideProjectors
- [ ] **[日历]** PR#1/#2 7 天药效复盘日 **2026-11-09**；PR#3/#4 7 天 **2026-11-12**
- [ ] （信息项）Live 外链 **3** 维持；GSC 首次展现 n=1；无标红 — 继续上内页+外链，不动 TDH
