## 推特书签简报 · 2026-11-08 晚上

新增 **9** 条（过滤 0），看板收录 **9**，carryover **320**。

本档新增开源 eSIM-Matrix 远程切卡接码网关、ITIN 查美国信用分教程、嘉信 Visa 借记卡到账进度、Monese 开不了户、精确匹配域名 10 天登上 Google 与 LLM、Image 2.6 拼贴 B-roll 工作流、Swipt 跳过 iOS 开屏广告、Herdr/Orca/T3 Codes 对比，以及 MyGo 云音乐下线；过滤 0 条。

### 通讯
- [开源 eSIM-Matrix 把安卓备用机做成远程切卡接码网关](https://x.com/wlzh/status/2119031354482704632)
  - M.（@wlzh）介绍开源项目 eSIM-Matrix：把闲置安卓备用机做成无人值守的接码和保号网关，需自备可插拔 eUICC 芯片（9eSIM、ESTKme、eSIM.gg、SakuraSIM 等）。切卡时可让 SIM、FlClash 代理节点和虚拟定位一起切换，降低只换卡被判异地高危的风险；支持秒级远程切卡、5 分钟临时接码后自动切回、短信验证码推 Telegram、在 Telegram 里发 eSIM 二维码远程写卡，以及 90/180 天定时保号。也提供 Web 控制台和 REST API。基于 NekokoLPA2 二次开发，MIT 开源，作者称仓库 2026-11-06 新建、当时约 21 个 star、版本 v1.4.1，仍早期；并写明只供个人管理自己合法的 eSIM，严禁非法接码。仓库：[hg552/eSIM-Matrix](https://github.com/hg552/eSIM-Matrix)
  - 动作：若要自建切卡/保号网关，先看仓库说明，并只用于管理自己的合法 eSIM

### 身份
- [ITIN 查美国信用分：myEquifax 走 X 客服、myFICO 免费版要打电话](https://x.com/CardAndMiles/status/2106308341119193221)
  - 旅遊卡路哩（@CardAndMiles）的 X Article《ITIN 也能查美國信用分：myEquifax ＋ myFICO 申請教程》面向已有 ITIN、美国地址、美国门号和美卡纪录的人。结论：myEquifax 可看 Equifax 报告和 VantageScore，ITIN 用户线上验证常卡住，可用 Equifax 官方 X 文字客服完成认证、不必打电话；myFICO 免费版提供发卡行更常看的 Equifax FICO Score 8，但必须在美国客服时段打电话验证；myFICO 付费版调 Experian/TransUnion 时 ITIN 通常过不了验证，作者建议改用 Equifax 付费方案订一个月看完另两局就取消（另两局分数一年才更新一次）。原帖：[X Article](https://x.com/i/article/2106305503429263360)
  - 动作：已有 ITIN 和美国地址、门号的可先注册 myEquifax，再按教程打电话开通 myFICO 免费版

### 美卡
- [嘉信 Visa 借记卡申请约 20 天后账户已显示卡号与支票功能](https://x.com/UncleJohnnyMe/status/2118870155908587831)
  - Uncle Johnny（@UncleJohnnyMe）说 10 月 19 日申请嘉信 Visa Debit Card，等了快 20 天没有邮件通知；登录后发现账户里已经显示 Visa Debit Card，并有 Routing Number、Checking Account Number 和 Checkwriting 支票功能。他原本只想申请免境外 ATM 手续费的借记卡，现在还差确认实体卡有没有寄出，并向其他申请人打听收卡周期。
  - 动作：已申请嘉信借记卡的可以登录账户查看是否已开通；实体卡未到可继续等寄送或向客服查询

### 支付
- [Monese 现在开不了户](https://x.com/WeiYi88890/status/2119058033372541156)
  - 维易（@WeiYi88890）写：之前 N26 还没关门时都看不上 Monese，现在想开却开不了了。配图未做文字识别，帖内没有说明具体报错或关闭原因。
  - 动作：若计划开 Monese，先确认当前是否还接受新用户，并准备备选账户

### 增长
- [用精确匹配域名加实体映射 10 天登上 Google 与 LLM 第一](https://x.com/margatix/status/2119089991217262884)
  - Margatix（@margatix）复盘：在「sell your data」赛道抢下 best data labs、best data labelling、best data labelling platform 等精确匹配域名，部署与关键词词面接近的内容，并做清晰的实体映射，称 10 天内在 Google 和 LLMs 排到第 1，随后接到域名出租和七位数买断报价。判断逻辑是买卖双方找彼此难、客单价高、决策急，占住这些词价值很大。这是增长方法论复盘，不是让读者去买他们的域名。
  - 动作：若在做高客单利基站，可对照「精确匹配域名 + 词面接近内容 + 实体映射」评估是否值得试

### AI
- [用 Codex Image 2.6 做拼贴 B-roll 不必另接视频模型 API](https://x.com/gkxspace/status/2119030071302426753)
  - 余温（@gkxspace）转发狗哥笔记（@gbroai）的教程：用 Codex 的 Image 2.6 做半调纸拼贴风 B-roll，走订阅额度、不再按条调用视频模型 API。流程是先把口播译成视觉隐喻并确认，再用案例图把风格参数化后出静帧，按纸片落下、剪刀滑入等物理顺序描述动作出 GIF，最后一行 ffmpeg 转成 MP4 进剪映。作者强调不要让模型一步出 GIF。仓库：[pyang5166/gbro-collage-broll](https://github.com/pyang5166/gbro-collage-broll)
  - 动作：做口播配镜时可按「隐喻→静帧→GIF→ffmpeg 转 MP4」试用该 skill

### 工具
- [Swipt 上的 Swiplet 可跳过 iOS 国区应用开屏广告](https://x.com/sino_go_global/status/2119282919839850633)
  - 浪险（@sino_go_global）转发世界（@nek0hasekai）为 Swipt 做的第一个 Swiplet：在 iOS 上跳过国内应用开屏广告，通过无障碍树识别常见广告 SDK 并学习，下次更快跳过。作者称用 ipatool 和 unfairplay 下载并逆向了国区热门应用；也提到不少应用会给跳过按钮加约半秒延迟，所以它只能比手动点更快。项目站：[swipt.io](https://swipt.io)。这不是 App Store 官方应用。
  - 动作：若在用 iOS 且想跳过开屏广告，可先看项目站了解 Swipt/Swiplet，不要按破解或侧载步骤操作

- [对比 Herdr、Orca 与 T3 Codes 后留下 T3 Codes](https://x.com/jilaiqian/status/2119118276089245782)
  - Laiqian Ji（@jilaiqian）用西语复盘一周试用：Herdr 像给 Agent 用的 tmux，快、可定制，但缺手机连接，也受限于 Claude Code/Codex 的 harness；Orca 功能很多（产物可视化、切换订阅、手机连接、GitHub/Linear），作者觉得过于笨重；herdr-app 更漂亮还能加插件，但还早、远程 SSH 有 bug。最终留下 T3 Codes（@t3dotcodes）：手机连接、切换订阅、SSH 远程环境、终端/浏览器/diff 都有，而且打磨更好；界面更像聊天而非 TUI，作者已适应。
  - 动作：若在选 Agent 控制面板，可按作者的取舍对比这几款工具

- [MyGo 云音乐因网易云来函下线，作者称 B 站插件已能替代音乐 App](https://x.com/st7evechou/status/2118893685505159640)
  - 𝗦𝘁𝗲𝘃𝗲 𝕏（@st7evechou）引用低空飞行（@localhost_4173）的帖子说「可以卸载各大音乐 app 了，bilibili 插件杀死比赛」。被引用站点 [MyGo 云音乐](https://music.egoist.dev) 标题是「原生地，安静地下线。」，描述写着网易云音乐来函、请本站立即下线。作者没有给出所谓 B 站插件的名称或安装方式。
  - 动作：若在用 MyGo，留意站点已提示下线；B 站插件细节原文未提供，需自行再查
