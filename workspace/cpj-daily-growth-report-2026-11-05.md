# China Private Journeys 每日增长战报 & 乘胜追击 Todo
**日期（Asia/Singapore）**: 2026-11-05  
**站点**: `https://chinaprivatejourneys.com`  
**Worker**: `https://china-private-journeys.zhangx2624.workers.dev`  
**巡检路由**: `CPJ每日竞品与GSC增长巡检 (cpj-gsc)`

---

## 一、 硬门禁表 (Hard Gates)

| 通道 | 状态 | 核心指标与详情 |
| :--- | :---: | :--- |
| **GSC** | 🟢 OK | 窗口: 2026-10-06→2026-11-02；点击 0，展现 0，CTR 0%，平均排名 0；Sitemap 已提交 29，已收录 0，警告 29，最后下载 2026-11-04。 |
| **Bing** | 🟢 OK | 点击/展现 0；Sitemap 状态 Success (最后抓取 2026-11-02)；配额: 日 100 / 月 2600。 |
| **GA4** | 🟢 OK | 属性: `561855861` (G-P248GHMDLE)；窗口: 2026-11-02→2026-11-05；直接会话 30，参与会话 5，转化 0，表单开始 1；AI 确认会话 0。 |
| **Clarity** | 🔴 **RED** | **不合格原因**: CPJ 环境中的 `CLARITY_API_TOKEN` 为 Frame 项目 Token（导出仅返回 frame-extractor.app URLs，忽略 projectId 查询）。需在 Clarity 项目 `z76iipo4o5` 内部生成专用 API Token。**严禁**将 Frame 数据作为 CPJ 漏斗使用。 |
| **Cloudflare** | 🟢 OK | 通过 MCP GraphQL 获取。11-02: PV 669, UV 403, 请求 5678, 威胁 15；11-03: PV 237, UV 256, 请求 3973, 威胁 24；11-04: PV 247, UV 284, 请求 1629, 威胁 1。本地 Token 文件 `cloudflare-api-token.txt` 缺失。 |
| **Email Routing** | 🟢 OK | `submit@` → `frame-submit@agentmail.to` (已启用)；`contact@` → `zhangx2624@gmail.com` (已启用)。 |

---

## 二、 基线对比 (Baseline Ref)
* **对比基线**: 首次巡检（2026-11-04 报告）。
* **GSC**: 点击 0 / 展现 0（持平）。
* **Bing**: 排名/流量为 0（持平）。
* **GA4 会话**: 当前 30 会话 vs 上期 23 会话，环比增长 **+30.4%**。
* **Cloudflare 独立访客 (UV)**: 11-04 (284) vs 11-03 (256)，环比增长 **+10.9%**。
* **Cloudflare 页面浏览量 (PV)**: 11-04 (247) vs 11-03 (237)，环比增长 **+4.2%**。

---

## 二点五、 红绿灯（防疲劳）

| 维度 | 状态 | 标红？ |
|---|---|---|
| Clarity API | 🔴 Token 实为 Frame 项目；导出全是 frame-extractor.app | **是** |
| 本地 CF API token 文件 | 🟡 MCP 可用；`cloudflare-api-token.txt` 仍缺 | 否（有 MCP 替代） |
| GSC / Bing 搜索 | 🟢 仍近零（相对基线持平） | 否 |
| GA4 会话 | 🟡 23→30（+30.4%，全 Direct） | 备注（非搜索>20% 标红口径） |
| CF DoD | 🟢 UV +10.9% / PV +4.2%（未达 20% 标红） | 否 |
| 基建 | 🟢 合规/语种/像素 OK；PR#4 GEO 两页生产 **404**（未部署） | 备注 Todo，非基建回退 |
| 外链 | 🟡 Live=1；今日新交 0；Pending/Queued 待消化 | 否 |
| 药效账本 7d | 🟡 PR#1/#2 复盘日 **2026-11-09** | 催办日历 |

## 三、 涨跌归因（固定四类）

1. **我方改动（药效账本）** — PR#1/#2 于 11-02 上线；今日无新部署。GSC/Bing 仍近零，**禁止**把 GA4 Direct +30% 或 CF DoD 说成单次 TDH 因果。PR#4 GEO 长文仅 OPEN 未合并，生产 404 属部署门禁，未入药效账本。7d 复盘日 **2026-11-09** / 14d **2026-11-16**。出处：`08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`
2. **外链/目录/Referral** — Live 仍仅 Brownbook Claimed；PeerPush 有 follow 链但 Coming soon≠Live；GA4 渠道仍全 Direct、AI referral 0。今日无新合规提交。出处：`04-内容与外链/02-外链/目录站提交质量门控与证据账本（flaqai-backlink_skills）.md`
3. **SERP 日常抖动 / 算法 / 竞品** — 搜索面仍 0 曝光，无从谈 CTR 抖动；私人定制游推荐位仍被 China Highlights / Travel China Guide / Asia Odyssey / WildChina / Wendy Wei 等占据，CPJ 未进列表（上线第 4 天）。
4. **数据不可证伪** — GSC 28d 窗口截止 **2026-11-02**（与今日错位，上线后增量可能尚未进 API）；Clarity 无本站导出；无询盘转化 API（form_start=1 / conversions=0）；GA4 全 Direct 无法拆自然/外链贡献；CF Uniques 含爬虫。

---

## 四、 基建 (Infrastructure)
* **核心多语言/Sitemap/Robots/LLMs/IndexNow/GA4/Clarity 像素**: `200 OK`；占位符 0；HTML 页面均已挂载 GA4 + Clarity 像素。
* **GEO 长文 PR#4**:
  * 包含 URLs: `/how-private-china-trip-enquiry-works`, `/private-beijing-xian-shanghai-journey`。
  * 生产状态: **404**。
  * PR 状态: `https://github.com/Chaoc2624/china-private-journeys/pull/4` OPEN 未合并，**deploy 严格 gatelocked 在 Halo 审批**。**严禁擅自改站/合并**。
* **Journey 页面**: `200 /journeys/beijing-xian-shanghai-12-days`。
* **索引状态**:
  * **已索引 (Indexed)**: `/`, `/de/`, `/es/`, `/fr/`, `/privacy-policy`。
  * **已发现但未索引 (Discovered - not indexed)**: `/about`, `/contact`, `/journeys/beijing-xian-shanghai-12-days`。
  * **未知/待处理 (Unknown)**: `/enquiry`, `/how-private-china-trip-enquiry-works`。

---

## 五、 询盘漏斗 (Enquiry Funnel)
* **浏览至询盘转化路径**: GA4 中 `/enquiry` 的 PV = 1（占 30 个会话的极小比例），`form_start = 1`，`conversions = 0`。
* **归因分类**: 无 Conversion API，归类为 **归因级别 4（Attribution Class 4）**。

---

## 六、 外链台账摘要 (Backlinks Ledger)
* **Live (1)**: Brownbook Claimed。
* **Pending (3)**: ExactSeek, ASR resubmit, Startup88。
* **Queued (1)**: PeerPush (Coming soon，含 follow 链接，暂非 Live)。
* **Member Ready / No Listing (1)**: ASEAN Now 注册完成。
* **Void (1)**: ASR/Viesearch 邮箱填写错误。
* **今日新增提交**: 0。
* **今日新增 Live**: 0。
* **需浏览器人工介入**: 旅游目录站存在验证码/登录墙，自动化脚本无法输入密钥。

---

## 七、 竞品简报 (Competitor Briefing)
* **监控竞品池**: China Highlights, Travel China Guide, Asia Odyssey, Catherine Lu Tours, The China Guide, WildChina, Wendy Wei Tours, Sunda Travel, TourRadar。
* **本期动态**: 竞品整体在长尾长文和私家团目的地页保持高频更新，本站正通过 PR#4（GEO 长文）布局追赶，待 Halo 审批通过后同步上线。

---

## 八、 GSC 建议制预览 (GSC Action Recommendations Preview)
* **建议 1**: 针对 GSC 29 个警告及未收录的核心内页，持续推进内页上线与外链引入。
  * *知识库出处*: `01-SEO基础与SOP/01-上线SOP/新站上线后能做的只有两件事：上内页，加外链.md`
* **建议 2**: 检查 SaaS 站内 SEO 基建，确保 Google 能够顺畅抓取与理解结构化数据。
  * *知识库出处*: `01-SEO基础与SOP/01-上线SOP/SaaS站内SEO基建让Google看见看懂收录（Playbook摘要）.md`
* **建议 3**: 后续如需调整已有排名页面的 TDH，必须严格执行老板审批门禁与零掉词铁律（当前阶段暂不执行，仅作建议预览）。
  * *知识库出处*: `03-站内优化/01-页面优化/已有排名与出沙盒页面TDH修改红线（零掉词铁律与老板审批门禁）.md`
* **建议 4**: 在 GEO 长文编写中贯彻硬核参数与真人极简体验解耦铁律，采用渐进式披露（Progressive Disclosure）。
  * *知识库出处*: `03-站内优化/01-页面优化/GEO硬核参数与真人极简体验解耦铁律（渐进式披露Progressive-Disclosure）.md`
* **建议 5**: 严格遵循目录站提交质量门控与证据账本规范处理外链。
  * *知识库出处*: `04-内容与外链/02-外链/目录站提交质量门控与证据账本（flaqai-backlink_skills）.md`
* **建议 6**: 按照 7 天与 14 天可证伪性追踪药效复盘账本对近期改动进行效果监控。
  * *知识库出处*: `08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`

---

## 九、 知识库引用清单 (Knowledge Base Citations)
1. `01-SEO基础与SOP/01-上线SOP/新站上线后能做的只有两件事：上内页，加外链.md`
2. `01-SEO基础与SOP/01-上线SOP/SaaS站内SEO基建让Google看见看懂收录（Playbook摘要）.md`
3. `03-站内优化/01-页面优化/已有排名与出沙盒页面TDH修改红线（零掉词铁律与老板审批门禁）.md`
4. `03-站内优化/01-页面优化/GEO硬核参数与真人极简体验解耦铁律（渐进式披露Progressive-Disclosure）.md`
5. `04-内容与外链/02-外链/目录站提交质量门控与证据账本（flaqai-backlink_skills）.md`
6. `08-案例复盘/01-站点复盘/China-Private-Journeys改动药效复盘账本（7天与14天可证伪性追踪）.md`

---

## 十、 乘胜追击 Todo (Action Items & MultiSelect)

- [ ] **[multiSelect: 拍板项] 修复 Clarity API Token 配置**
  * **动作**: 在 Clarity 项目 `z76iipo4o5` 内部重新生成专用 API Token，并更新至 CPJ 环境变量，消除数据隔离污染。
- [ ] **[multiSelect: 拍板项] 等待 Halo 审批并合并 PR#4 (GEO 长文)**
  * **动作**: 维持 PR#4 (`https://github.com/Chaoc2624/china-private-journeys/pull/4`) 当前 OPEN 状态，**绝对不擅自改站/部署**，等待 Halo 拍板后执行上线。
- [ ] **[multiSelect: 拍板项] 补充 Cloudflare 本地凭证文件**
  * **动作**: 补齐缺失的 `cloudflare-api-token.txt` 本地凭证，保障 MCP GraphQL 巡检链路完整。
- [ ] **[multiSelect: 拍板项] 人工推进外链目录突破**
  * **动作**: 针对需要浏览器登录/验证码的目录站（如 Travel directories），安排人工介入完成剩余 Pending/Queued 外链提交。
