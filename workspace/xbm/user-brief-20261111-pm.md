📌 推特书签简报 · 2026-11-11 晚上（22:00 档）

账号 @Chaoc2624 · 新增 2 条书签（过滤 0）。之前推过、看板上还没处理的还有 363 条，详情在看板。

### 美卡
- [富国银行 Everyday Checking 再开 500 美元开户奖励](https://x.com/HaiWaiYunJuMin/status/2120323653443428464)
  - 海外云居民（@HaiWaiYunJuMin）说，上一波富国银行 Wells Fargo Everyday Checking $500 开户奖励，有人因为信用刚建立而错过；现在活动又来了，截止日期 2027-01-12，并称这是美银里要求较低、奖励较高、也比较容易拿的一档开户奖励。配图是官方活动页截图：Limited Time Offer ends January 12, 2027；作为新支票客户开立 Everyday Checking，并在开户后 90 天内完成合计 $1,000 或以上合格直接存款（qualifying direct deposits），可获 $500 bonus。页面写从该优惠页在线申请会自动带上 bonus offer code，另外有如何避免 $15 月费的说明。原帖没有给出可点击的官方申请 URL，只有截图，不要随便用第三方申请链接。
  - 动作：若符合新支票客户条件，先对照截图里的 90 天 / $1,000 合格直接存款要求，再自行找到官方优惠页申请，并看清 $15 月费怎么免

### 增长
- [砍柴少侠开源 yan-skills 覆盖选词建站外链全链路](https://x.com/yan_ai_labs/status/2090785456774689270)
  - 砍柴少侠 YAN（@yan_ai_labs）在 2026-08-21 发长帖，开源自己做 SEO 用的一套 Agent Skills，仓库：[yan-labs/yan-skills](https://github.com/yan-labs/yan-skills)（MIT，兼容 Claude Code / Codex / Cursor）。帖里把打法写成一条链：选词、查 KD、查竞对、查搜索量和长尾 → 用 shadcn 官方模板起站，部署到 Cloudflare（Workers / D1 / R2）→ 接 Stripe、GSC、Webmaster、Ahrefs，并接入哥飞工具箱做检测 → `/rankup` 在项目里建 `.rankup` 目录长期管迭代 → `/backlink` 发外链。发帖时自述收录约 492 个免费外链平台（其中 100+ 免登录可自动发、102 个免费但要注册），另有 141 个付费外链表，称至少有几个新词站的第一批外链来自这些付费平台。他也写了 Semrush / Similarweb 自动化脚本用过共享账号平台，但明确建议买正版。本档核查：仓库还在，约 285 stars，2026-11-11 仍有 push；README 现在以 rankup（文档写 3.42.0，七段：调研→立项→建站→上线前 SEO/GEO→上线接入→外链节奏→变现监控）、backlink、opencli、imagegen、cf-cli 为主，也有 autopilot / write 等。安装：`npx skills add yan-labs/yan-skills -g --all`。外链平台数量以仓库当前目录为准，不要把共享账号当成推荐用法。
  - 动作：先按上面的命令把 skill 接到自己的 Agent，用 `/rankup` 做选词和站点体检，外链再交给 `/backlink`；数据平台用正版或自己的账号

### 看板
- [x.omnitools.cc](https://x.omnitools.cc)（📰 每日简报、待办书签已同步）

### X API
- 本档调用：bookmarks 1 + usage 1（未另走用户侧开发者接口拉对话）
- 余额：**$12.73** free（约 2027-10-06 20:22 台北时间到期），prepaid $0

### 增长批
- **1** 条已 priority 转给增长大师：yan-skills 开源 SEO/建站/外链工作流
