📌 推特书签简报 · 2026-11-20 上午（10:00 档）

账号 @Chaoc2624 · 新增 23 条书签（过滤 0）。之前推过、看板上还没处理的还有 384 条，详情在看板。

### 增长
- [用 Bing Webmaster Tools 免费查看 AI 引用了哪些页面](https://x.com/ShenyuanNext/status/2122881785797447942)
  - Shenyuan Wang（@ShenyuanNext）分享免费 AEO 技巧：在必应网站管理员工具打开 AI Performance，重点看 Intents 里的 Commercial 和 Comparison；再打开 Grounding Query – Page Mapping，可看到某条查询实际引用了站点的哪些页面，便于发现引用页与搜索意图不匹配。还可看 Citation Share 及不同时间段变化。作者称这是微软第一方数据，覆盖 Copilot、Bing AI 和部分合作伙伴平台。原帖无配图。
  - 动作：打开已验证站点的 Bing Webmaster Tools → AI Performance，先看商业/比较意图查询的 Page Mapping 和 Citation Share
- [子木指 Semrush 用 Google 首选来源组件做 GEO](https://x.com/CoderJeffLee/status/2122370983470502050)
  - 写增长的子木（@CoderJeffLee）称这是让用户帮你把博客喂给 AI 的 GEO 操作，Semrush 正在这么做，并提到 HeyGen 也曾跟上。配图是 Semrush 博客文 How to Choose the Right AI SEO Tool，右侧框出 “Tells Google to show you more from Semrush in AI, Search, and Discover” 以及 “Add SEMRUSH as a preferred source on Google”。截图未给出该组件的官方设置入口。
  - 动作：先辨认这是 Google 的 preferred / follow source 类组件，再评估自己站点是否适合放同类入口
- [Geektao 补 GEO 基线：18 次提问里 10 次读同一测评站](https://x.com/geektao0319/status/2121951520350437638)
  - Geektao（@geektao0319）引用 [GoSailGlobal 的测试帖](https://x.com/GoSailGlobal/status/2121198885460914540) 并补充：问了 18 次，有 10 次 ChatGPT 都去读同一个第三方测评站，最多一次读了它 9 页；问替代品的 3 次，排第一的都是同一家，它自己写的对比页 3 次都被读到。被引用帖称 skills.sh 进了 6 篇、20 次回答里被推荐 12 次；作者站 11 月 6 日一篇没进、被推荐 0 次；用 Glasser 问了 20 道题给 ChatGPT/Gemini/Perplexity，60 个回答里 Agent Skills Hub 被推荐 0 次；公开邮箱退信后改走 GitHub，PR 被合并。Geektao 未给出自己所说测评站的域名。
  - 动作：对自己站做同类提问基线，记录模型先读哪些第三方页，再考虑能否出现在那些页里
- [子木谈 SEO 页面波动：单页竞争力撑不住站点信任](https://x.com/CoderJeffLee/status/2122132239286927503)
  - 子木发 X 长文《GSC 后台如何排查 SEO 数据变化？》，并感谢 Joker。原帖补充他对某个页面排名波动的判断：页面可能有一定竞争力，但站点的主题积累和信任还撑不住它长期排名。长文全文接口未返回。
  - 动作：排查波动时，除单页因素外，同时看站点主题积累和信任是否撑得住该词的竞争
- [阿杭称本月 Affiliate 赚了几百刀且新站出现搜索与 AI 抓取](https://x.com/Astronaut_1216/status/2122904132441043419)
  - 叫我阿杭（@Astronaut_1216）称 AI 自媒体+Affiliate 这个月已赚几百刀，新站开始有搜索流量。配图为 TOTAL UNPAID $400.4；账户余额 USD 185.74、待定佣金 USD 4.09；以及「搜索引擎和 AI 每天来读了多少次」：Meta AI 3631、Claude 2199、Amazon 225、Google 135、OAI-SearchBot 67、ChatGPT-User 15、Bing 14、Apple 7、其他 15，约 11 月 18 日附近明显拉升。站点域名未给出，未付与余额不要加总。
  - 动作：当作联盟+新站启动期案例记录；若要复现需另核其方法文

### 工具
- [开源 app-store-compliance 可在提交前按 2026 规则审查拒因](https://x.com/slashui/status/2122817482863890626)
  - 洛克船长（@slashui）称 App Store 审核周期动辄一个多月，被拒再改又要再等约一个月。仓库：https://github.com/mjmirza/app-store-compliance ，称可盘点常见拒因、按 2026 年规则检查，并支持提交前让 AI Agent 审查代码。
  - 动作：下次提交 App 前先在该仓库跑一遍合规检查
- [麦当开源「麦田」自媒体七平台发布与监控工作台](https://x.com/czzzzzzJ_/status/2122266042491642027)
  - 麦当mdldm（@czzzzzzJ_）开源「麦田」，仓库 https://github.com/CzzzzzzJ/mdldm-maitian 。用于 B站/抖音/小红书/视频号/YouTube/X 等分发与数据监控，带飞书卡片和数据大屏；作者称国内四平台只填写、不自动点发布，跑在常开 Mac 上、不存平台密码。
  - 动作：若在做多平台分发，先看仓库的 macOS 安装要求再决定是否试用
- [一个 Stripe 账号接多站时要用 metadata.site 分流 webhook](https://x.com/victor_UWer/status/2121453268588962266)
  - Victor在西雅图（@victor_UWer）提醒：一号多站时，各站 webhook 会收到账号下全部事件。做法是 Checkout Session 的 metadata 带 site 字段；处理时先读 metadata.site（正文里曾被 X 误识别成 http://metadata.site，那不是网站）；非本站返回 200 而非 4xx；各端点单独 signing secret；创建订阅时把 metadata 写到 subscription 上，以免续费发票认不出站点。
  - 动作：检查 Checkout/Subscription 是否都写了 site metadata，webhook 是否按站点过滤并返回 200
- [卡兹克分享近两月最常用的 10 条 Agent Prompt](https://x.com/Khazix0918/status/2122268349707219333)
  - 数字生命卡兹克（@Khazix0918）整理 10 条常用指令：从第一性原理找根因、先对齐偏好再出 3 版方案、先质疑问题定义、推演二阶三阶影响、跨领域找方案、先假设当前方案是错的、分析 Git 历史与可移除包袱、评估接手认知成本、复盘最慢 PR，以及把反复出现的问题沉淀成规则或 Skill。
  - 动作：按自己的工作流挑几条写成固定指令，不必一次全用
- [陈成补充 9 条常用 Agent Prompt](https://x.com/chenchengpro/status/2122321666898538758)
  - 陈成（@chenchengpro）引用卡兹克的帖，补充 9 条英文 Prompt，覆盖先分析再改、worktree 里做完再一次性提交、结果存到 ~/Downloads、让 Agent 追问、用 HTML 证明做完、做 15–30 秒宣传视频、按包体积和 UI 审 PR，以及通宵把应用做专业并自己开 PR。
  - 动作：对照卡兹克那组，按自己的仓库习惯挑几条试用
- [小晚不在发布 ChatGPT 去 AI 味写作长文](https://x.com/bbkirstry/status/2123419503417544831)
  - 小晚不在（@bbkirstry）推荐用 ChatGPT 的 Chat 模式辅助写作，长文为《ChatGPT 保姆级写作教程｜从源头解决人机感和 AI 味》。公开索引只见到开头，全文接口未返回。
  - 动作：打开原帖长文阅读完整方法
- [Nexmoe 称 UU 远程用户应装某个开源项目但未给仓库](https://x.com/nexmoe/status/2122678742824919207)
  - Nexmoe（@nexmoe）说所有 UU 远程用户都应该必装某个开源项目，原帖只附演示视频，没有写出仓库名或链接，这里不猜测项目。
  - 动作：打开原帖看视频再核对项目名；没有仓库地址前先不要按第三方推荐安装

### 羊毛
- [中国银行银联闪付首笔立减至高40元](https://x.com/donniy520/status/2122553197927551201)
  - 东逆（@donniy520）转发中国银联活动：首笔立减至高40元，时间为 2026-11-17 00:00 至 2026-12-31 23:59。适用中行在中国国内（不含港澳台）发行的银联标识卡（借记/单标信用卡 62 开头，Visa-银联双标 40/43 开头），支付方式为手机闪付。原帖未给独立活动链接。
  - 动作：若持有符合条件的卡，在 12 月 31 日前用手机闪付确认活动是否仍可用
- [日区 Google Play 订阅 Ultra 12 个月试用后续费 JP¥1,100/月](https://x.com/interjc/status/2122823614303179047)
  - Justin（@interjc）称下一年续费每月 1100，自己又上车了。截图为日区 Google AI Ultra (20 TB)+YouTube Premium：今天试用免费（Ultra 12 个月、YT Premium 1 个月）；2026-12-18 起 JP¥1,100/month；2027-11-18 起 JP¥15,600/month。页面写明 2026-12-18 前取消无需付费。「每月 1100」是日元。
  - 动作：若已订阅，在 2026-12-18 前到 Google Play 确认是否取消，以免开始按月扣款
- [作者称 Google Ultra 0元购亲测成功并已设置到期取消](https://x.com/0xzheng888/status/2122701196486185076)
  - 0x政（@0xzheng888）称 0 元购成功，可爽用 Opus 5.5 / Carbon，并提醒接口随时失效，仓库 https://github.com/gylive/google-ultra 。截图为 Ultra (30 TB)+YT Premium 试用 1 个月 US$0.00，2026-12-17 起 US$213.57/month，且 Google One 显示 Cancels on Dec 17, 2026。属灰区羊毛，步骤不转述。
  - 动作：只作记录；若已试用，核对是否已设为 12 月 17 日取消
- [搞到 Google Ultra 羊毛后反重力无法使用可先开通 Cloud Shell](https://x.com/zhuxufng154415/status/2122742533990318197)
  - BanXian（@zhuxufng154415）称很多人搞到 Ultra 后「反重力」用不了，多半是没开通，打开 https://shell.cloud.google.com 即可。未说明「反重力」的官方产品名。
  - 动作：若已有 Ultra 却打不开相关开发环境，先访问该页看是否需要开通

### 美卡
- [SecJack 称 Elios 又支持中国护照开户](https://x.com/SecJack96/status/2122293529275924768)
  - SecJack（@SecJack96）称 Elios 又支持 CN 护照。称 3% 返现为 USDC，RMB 消费损耗大约 1.5%；美元户出金无手续费，入金 USDC 1:1 美元；建议开美区，不需要地址证明，英国手机号也支持。他前一天还发过「已没有 CN 护照选项」的反馈。
  - 动作：若考虑办理，先到官方开户页确认是否仍有中国护照选项
- [昨日重现分享 Tria Card：不支持中国注册、称将推欧元 IBAN](https://x.com/zrchongxian/status/2123069958653456429)
  - 昨日重现（@zrchongxian）称 Tria Card 在日本较火、APP 有日语，不支持 CN 注册，他用菲律宾水卡和地址；邮件称将推出欧元 IBAN。有 Visa 虚拟卡和实体卡、自托管钱包，支持 Apple Pay / Google Pay，1.5% 返现。
  - 动作：只作卡片资讯记录，先核对注册限制和欧元 IBAN 是否已上线
- [Starry 分享塞浦路斯电子钱包 eCREDO 可开 CY 开头欧元 IBAN](https://x.com/hackerxiao/status/2122261278102327676)
  - Starry（@hackerxiao）称 eCREDO 可用护照+欧洲手机号开户，无需地址证明；IBAN 以 CY059170 开头；同名 SEPA 出入金免费；官方称即将推出万事达预付卡。注册链接在评论区，正文未给 URL。
  - 动作：若需要欧元 IBAN，先到评论区或官网核对开户条件
- [silence 将 ITIN tools 插件开源并另开 20 美元 VIP 群](https://x.com/silence_3650/status/2123346265735888991)
  - silence（@silence_3650）因破解和二次开发影响付费用户而开源 ITIN tools。仓库 https://github.com/mstscmsn/itin_tools ，站点 https://itin.nranote.com 。VIP 群 20USD/年，含两次英语代打电话；已购用户可免费永久进群。
  - 动作：若在办 ITIN/美卡，先看开源仓库说明；VIP 群按需自行判断
- [Starry 分享统一英国地址并用 Zilch 分期做信用](https://x.com/hackerxiao/status/2122730888484257854)
  - Starry 表示要搞英国信用：统一了 Monzo、Lloyds、Zilch 的地址，在 Zilch 打开 Alpinetrek 并优先分期，再通过支付宝买了几张美团饭票。
  - 动作：仅作英国信用玩法记录，不要照搬具体消费路径

### 身份
- [sola 称已有人按其方法通过 KYC](https://x.com/solaabbbb/status/2123280718898073936)
  - sola（@solaabbbb）称已有人按其方法通过 KYC。该帖及配图涉及加工证件用于验证，这里只作高层次记录，不转述步骤。
  - 动作：只作书签记录，不要按该帖操作
- [sola 补充 KYC 过审经验](https://x.com/solaabbbb/status/2123410015377887659)
  - sola 对前帖作几点补充，内容仍围绕海外 KYC。同样只作高层次记录。
  - 动作：只作书签记录，不要按该帖操作
