## 推特书签简报 · 2026-11-09 上午

新增 **6** 条（过滤 0），看板收录 **6**，carryover **329**。

本档新增无港号参加八达通新户 150 港币活动的补丁、把 GSC 接入 Claude 优化已有页面、出海站上线先开各国站长后台、Capital One 风控后先不要关户、Claude KYC 与印尼驾照代办的价格对比，以及 Grok Bot 额度不够改用 OpenMausBot；过滤 0 条。

### 羊毛
- [没有香港手机号也能撸八达通新户 150 港币羊毛](https://x.com/sino_go_global/status/2119397785527361740)
  - 浪险（@sino_go_global）补充昨天那条八达通新户 150 港币活动：App 注册要香港手机号，但活动核心是新设备开卡，所以可以跳过注册、开卡、登记、消费三步走完。支付难点用两部 NFC 手机模拟拍卡。步骤：下载八达通 App 并跳过注册进入开卡；用 Apple Pay 充值（支持内地借记卡和信用卡）；登记卡号；在淘宝或拼多多消费 100 港币以上，两部手机互相拍卡完成支付。引用自己昨天的原帖，活动登记页：[octopuscards.com 登记](https://www.octopuscards.com/onlineform/promotion/general/registration/tc/step1.jsp?promotionRegRefCode=202611MO)。作者说还会再写更完整的玩法。
  - 动作：若要参加，先看活动登记页和名额，再按开卡、登记、消费三步操作

### 增长
- [把 GSC 接入 Claude，用现有页面数据补缺口拿点击](https://x.com/yaohongan2025/status/2119288301534564644)
  - 虹安（@yaohongan2025）转发 @asaio87 的长线程并说「直接把 GSC 接入 Claude Code，再按提示词优化 SEO」。原帖主张先别写新文、先别做外链：从 Search Console 按点击再按展示取出 Google 已信任的前 10 个页面，用近 3 个月数据（MCP 直连或导出 zip）交给 Claude，找出页面没写到但仍有展示的词，以及排在 10–30 名的词；按提示词决定补 H2、段落、FAQ 还是改原句，并改写首两段直接回答主问题、检查主词是否出现在标题/描述/首段。再补截图、表格和自己的数据角度，给这 10 页做内链，用 URL 检查请求重新编入索引，等 7–14 天复盘；这 10 页也是优先外链对象，每月 2–5 条即可。原帖强调 AI 是写作助手不是代笔。原线程：[asaio87](https://x.com/asaio87/status/2119171723849245031)
  - 动作：可先从 GSC 导出或接入近 3 个月前 10 页数据，按原帖提示词逐页补缺口后再请求编入索引

- [出海站上线先开各国站长后台，IndexNow 一次覆盖四家](https://x.com/GoSailGlobal/status/2119318584640094406)
  - Jason Zhu（@GoSailGlobal）写：出海站上线后第一件事不是发外链，而是去要收录的搜索引擎开站长后台。IndexNow 提交一次，Bing、Yandex、Naver、Seznam 共享；Google 和百度不收，得各交各的。分市场：美国用 Search Console + Bing Webmaster（Yahoo 和 DuckDuckGo 多数结果来自 Bing，Bing 还能从 Search Console 导入）；印尼、越南有 Search Console 即可，越南 Cốc Cốc 没有后台只有提交表单；日本是 Search Console + Bing，Yahoo! JAPAN 用 Google 引擎；韩国要注册 Naver Search Advisor，验证用的 meta 必须写在 head 里，Naver 验证时不执行 JavaScript；俄罗斯是 Yandex Webmaster，完整注册要确认手机号，地区需手动设置并过人工审核；中国是百度搜索资源平台，要大陆手机号，非实名不能交 sitemap，「快速收录」2024 年已下线、改成只给 VIP 的「快速抓取」；欧洲、英国用 Search Console + Bing，做捷克再加还在测试的 Seznam。他还澄清：Google「请求编入索引」有每日上限，Indexing API 只收招聘和直播视频页。后台也开始给 AI 数据：Search Console 有「生成式 AI 效果」，Bing 能看 Copilot 引用次数，Yandex 能看 Alice AI 引用占比。完整注册与提交步骤：[jasonzhu.ai 站长后台指南](https://jasonzhu.ai/zh/go-global/indexing)
  - 动作：新站上线后按目标市场去 Search Console、Bing，并用 IndexNow 覆盖其余四家，Google 和百度单独提交

### 美卡
- [Capital One 下卡后被风控别急着关户，先撑过第一期信报](https://x.com/DaixiXha/status/2119402348187718001)
  - daixi（@DaixiXha）的 X Article 说，最近不少人 ITIN 下号后扎堆申请 Capital One，风控变严，已下卡也可能被风控甚至关户，常见触发是用了「万人骑」地址。可先试打客服 800-227-4825（以短信通知为准），验证姓名、ITIN 尾号和卡号后四位，英文不好可要求中文翻译，也可用 Gemini 或豆包做即时口译；但作者认为电话多半仍会要美国 ID 和地址证明，别抱太大希望。重点是：信用局看不到银行内部的风控状态，只要没被关户，信报上仍是 Open、使用率为 0，第一期信报仍能用来破冰。千万不要用美国机房 IP 或非美国 IP 登网页/App，不要主动让客服关户，也不要让房东拒收卡片（拒收后关户概率极高），收到卡后扫描卡号和安全码再电话激活。等有了信报和其他美国账户、若仍解不了封，再考虑自己主动关户，以免后面爆雷。原帖：[X Article](https://x.com/i/article/2119353565822984192)
  - 动作：若 C1 已被风控，先避免关户和异常 IP 登录，激活实体卡并等待第一期信报

### 身份
- [Claude KYC：闲鱼代办印尼驾照约 1500 元，评论区有人报价 120 元](https://x.com/WeiYi88890/status/2119464527930732958)
  - 维易（@WeiYi88890）先发过：过 Claude KYC 最简单还正规的办法是闲鱼代办印尼驾照，需护照、证件照和白纸签名，驾照有效期五年，闲鱼代办大约 1500 元。本帖引用该条并配评论区截图：@aypokeflow 说「120给你搞定」，@riloong（显示名 WeilGre）称自己在印尼常驻可以代办；作者惊讶闲鱼要 1500、对方报 120，调侃「你都可以去闲鱼挣钱了」，并问这是不是住在国外的优势。帖内没有代办流程、成功案例或担保，只是价格对比和评论区报价。
  - 动作：若为 Claude KYC 考虑这条路径，先自行核实代办合规性和可靠性，不要只凭评论区报价下单

### 工具
- [Grok Bot 额度不够改用 OpenMausBot 辅助](https://x.com/geekbb/status/2119356490192650420)
  - Geek（@geekbb）写：Grok Bot 额度不够用，只好拉 OpenMausBot 打辅助，用习惯了就不回来了，并调侃「老马你确定这样做好吗」。配图是 MausBot 侧栏里「随便问问」的对话（模型显示 auto/deepseek-v4.1-flash），内容在解释 Grok Bot 产品上叫「虚拟机」、在 macOS 上实际是 OrbStack 提供的 Linux 容器（共享宿主机内核），不是 UTM/Parallels 那种真虚拟机；对比了冷启动、内存、能否换内核、GPU、隔离和快照，结论是 bot 主要用于画界面和键鼠时容器更合适，若要跑不可信代码或要更强隔离再用真虚拟机或 VPS。帖内没有 OpenMausBot 的下载或注册链接。
  - 动作：若也觉得 Grok Bot 额度紧，可先了解作者提到的 OpenMausBot；截图讲的是 Grok Bot 桌面环境，不是安装教程

### 看板
- [x.omnitools.cc](https://x.omnitools.cc)（📰 每日简报、待办书签已同步）

### X API
- 本档调用：bookmarks 1 + usage 2（+me）
- 余额：**$12.73** free（约 2027-10-06 20:22 台北时间到期），prepaid $0

### 增长批
- **2** 条（GSC + Claude 优化已有页面、出海站各国站长后台 / IndexNow）已 priority 转增长大师
